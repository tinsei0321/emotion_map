# -*- coding: utf-8 -*-
"""PT-CB15 PROMOTE P2-7：codex_bridge 解析层单测（monkeypatch subprocess·离线）。

覆盖（派发单口径）：
- JSONL 坏行（非 JSON 噪音）容错跳过；
- 超长行（readline 抛 ValueError·16MB limit 纵深防御）→ CODEX_LINE_LIMIT；
- stdout EOF → CODEX_PROC_EOF + proc 状态重置；
- tool begin/end item.id 配对透传（P2-1）；
- P1-1（Z-01）看门狗「有流量即续命」——高频行流（每 50ms 一行）预算仍触发；
- 静默超时路径（心跳 ping + 预算收口）不变；
- codex.exe 解析失败 → CODEX_BRIDGE_START（fail-closed 不 500）。
"""
import asyncio
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.codex_bridge import CodexBridge   # noqa: E402


class FakeStdin:
    def write(self, data):
        pass

    async def drain(self):
        pass


class FakeStdout:
    """预置行队列（bytes/异常对象/延迟秒数）·async readline 逐条吐。"""

    def __init__(self, items, interval=0.0):
        self._items = list(items)
        self._interval = interval

    async def readline(self):
        if self._interval:
            await asyncio.sleep(self._interval)
        if not self._items:
            return b''
        it = self._items.pop(0)
        if isinstance(it, BaseException):
            raise it
        if isinstance(it, type) and issubclass(it, BaseException):
            raise it()
        return it


class FakeProc:
    def __init__(self, items, interval=0.0):
        self.stdout = FakeStdout(items, interval)
        self.stdin = FakeStdin()
        self.returncode = None


def _bridge_with(proc):
    br = CodexBridge()
    br._proc = proc
    br._thread_id = 'fake-thread'
    return br


async def _noop_ensure(self):
    pass


async def _collect(br, q='测试问题', tmo=None):
    out = []
    async for e in br.ask(q, timeout_s=tmo):
        out.append(e)
    return out


def _run(coro):
    return asyncio.run(coro)


def _jline(method, params):
    return (json.dumps({'method': method, 'params': params}) + '\n').encode('utf-8')


# ── 1. 完整事件流解析（delta + tool 配对 + done）──────────────────────
def test_bridge_parse_events(monkeypatch):
    monkeypatch.setattr(CodexBridge, 'ensure', _noop_ensure)
    lines = [
        _jline('item/started', {'item': {'type': 'mcpToolCall', 'id': 'call_1',
                                          'tool': 'rank', 'server': 'emc'}}),
        _jline('item/completed', {'item': {'type': 'mcpToolCall', 'id': 'call_1',
                                            'tool': 'rank', 'status': 'completed'}}),
        _jline('item/agentMessage/delta', {'delta': '宜'}),
        _jline('item/agentMessage/delta', {'delta': '昌'}),
        _jline('turn/completed', {'turn': {'status': 'completed'}}),
    ]
    br = _bridge_with(FakeProc(lines))
    evts = _run(_collect(br))
    kinds = [(e['event'], e.get('phase', '')) for e in evts]
    assert ('tool', 'begin') in kinds and ('tool', 'end') in kinds
    begin = next(e for e in evts if e['event'] == 'tool' and e['phase'] == 'begin')
    end = next(e for e in evts if e['event'] == 'tool' and e['phase'] == 'end')
    # P2-1：begin/end 透传同一 item_id（前端配对依据）
    assert begin['item_id'] == 'call_1' and end['item_id'] == 'call_1'
    assert end['ok'] is True
    deltas = [e for e in evts if e['event'] == 'delta']
    assert [d['delta'] for d in deltas] == ['宜', '昌']
    assert [d['n'] for d in deltas] == [1, 2]   # wire n 单调
    done = evts[-1]
    assert done['event'] == 'done' and done['status'] == 'completed' and done['n_delta'] == 2


# ── 2. 坏行容错（非 JSON 噪音跳过·不崩不中断）──────────────────────
def test_bridge_bad_line_skipped(monkeypatch):
    monkeypatch.setattr(CodexBridge, 'ensure', _noop_ensure)
    lines = [
        b'2026-08-24T12:00:00Z ERROR rmcp noise line\n',   # rmcp 噪音（真实形态）
        _jline('item/agentMessage/delta', {'delta': 'OK'}),
        b'\x80\x81 not utf8 json either\n',
        _jline('turn/completed', {'turn': {'status': 'completed'}}),
    ]
    br = _bridge_with(FakeProc(lines))
    evts = _run(_collect(br))
    assert any(e['event'] == 'delta' and e['delta'] == 'OK' for e in evts)
    assert evts[-1]['event'] == 'done'
    assert not any(e['event'] == 'error' for e in evts)


# ── 3. 超长行（readline ValueError）→ CODEX_LINE_LIMIT ──────────────
def test_bridge_line_limit(monkeypatch):
    monkeypatch.setattr(CodexBridge, 'ensure', _noop_ensure)
    lines = [ValueError('Separator is not found, and chunk exceed the limit')]
    br = _bridge_with(FakeProc(lines))
    evts = _run(_collect(br))
    assert len(evts) == 1
    assert evts[0]['event'] == 'error' and evts[0]['code'] == 'CODEX_LINE_LIMIT'


# ── 4. stdout EOF → CODEX_PROC_EOF + proc/thread 重置 ──────────────
def test_bridge_proc_eof(monkeypatch):
    monkeypatch.setattr(CodexBridge, 'ensure', _noop_ensure)
    br = _bridge_with(FakeProc([]))   # 空队列 = 立即 EOF
    evts = _run(_collect(br))
    assert evts[-1]['event'] == 'error' and evts[-1]['code'] == 'CODEX_PROC_EOF'
    assert br._proc is None and br._thread_id is None   # 重置→下轮 ensure 重建


# ── 5. P1-1（Z-01）：高频行流——有流量也必在预算到达时收口 ──────────
def test_bridge_highfreq_budget_still_triggers(monkeypatch):
    monkeypatch.setattr(CodexBridge, 'ensure', _noop_ensure)
    # 每 50ms 一行合法 delta（持续有流量·旧逻辑只查静默分支会永不超时）
    lines = [_jline('item/agentMessage/delta', {'delta': 'x'})] * 40
    br = _bridge_with(FakeProc(lines, interval=0.05))
    evts = _run(_collect(br, tmo=0.15))   # 短预算注入（测试加速）
    deltas = [e for e in evts if e['event'] == 'delta']
    assert len(deltas) >= 1, '高频行流应在超时前产出部分事件'
    assert evts[-1]['event'] == 'error' and evts[-1]['code'] == 'CODEX_TURN_TIMEOUT'
    assert '超预算' in evts[-1]['message'] or '超时' in evts[-1]['message']


# ── 6. 静默超时路径（心跳 ping + 预算收口·语义不变）───────────────
def test_bridge_silence_budget(monkeypatch):
    monkeypatch.setattr(CodexBridge, 'ensure', _noop_ensure)

    class AlwaysTimeout(FakeStdout):
        async def readline(self):
            raise asyncio.TimeoutError()

    br = _bridge_with(FakeProc([]))
    br._proc.stdout = AlwaysTimeout([])
    evts = _run(_collect(br, tmo=0.25))
    assert any(e['event'] == 'ping' for e in evts), '静默期应发心跳 ping'
    assert evts[-1]['event'] == 'error' and evts[-1]['code'] == 'CODEX_TURN_TIMEOUT'


# ── 7. codex.exe 解析失败 → CODEX_BRIDGE_START（fail-closed）──────
def test_bridge_start_fail(monkeypatch):
    import core.codex_bridge as cb
    monkeypatch.setattr(cb, '_resolve_codex_exe', lambda: None)
    br = CodexBridge()   # 真实 ensure（解析失败即抛）
    evts = _run(_collect(br))
    assert len(evts) == 1
    assert evts[0]['event'] == 'error' and evts[0]['code'] == 'CODEX_BRIDGE_START'


# ── 8. 配置隔离：harness CODEX_HOME 自愈——config 锁定 flash + emc required + providers 复制 ──
def test_harness_home_config_generation(monkeypatch, tmp_path):
    import core.codex_bridge as cb
    monkeypatch.setattr(cb, '_CODEX_HOME', str(tmp_path / '.codex'))
    monkeypatch.setattr(cb, '_DESKTOP_CODEX_HOME', str(tmp_path / 'desktop'))
    (tmp_path / 'desktop').mkdir()
    (tmp_path / 'desktop' / 'config.toml').write_text(
        '[model_providers.deepseek]\n'
        'name = "deepseek"\n'
        'base_url = "https://api.deepseek.com/"\n'
        'wire_api = "responses"\n'
        'experimental_bearer_token = "sk-test"\n', encoding='utf-8')
    out = cb._ensure_harness_home()
    assert out == str(tmp_path / '.codex')
    cfg = (tmp_path / '.codex' / 'config.toml').read_text(encoding='utf-8')
    # 锁定 deepseek-v4-flash（用户令：全局不可切换）
    assert 'model = "deepseek-v4-flash"' in cfg
    assert 'model_provider = "deepseek"' in cfg
    assert 'model_reasoning_effort = "high"' in cfg
    # emc MCP required 迁入 harness 配置（fail-fast 保留）
    assert '[mcp_servers.emc]' in cfg
    assert 'required = true' in cfg
    assert 'url = "http://127.0.0.1:8600/mcp"' in cfg
    # 桌面 providers（密钥）运行时复制·不进仓
    assert '[model_providers.deepseek]' in cfg
    assert 'experimental_bearer_token = "sk-test"' in cfg
    # 桌面配置不受影响（隔离铁律）
    assert '[mcp_servers.emc]' not in (tmp_path / 'desktop' / 'config.toml').read_text(
        encoding='utf-8')


# ── 9. 配置隔离：models.json Deferred 补丁（deepseek 系 supports_search_tool=false）──
def test_harness_models_json_patch(tmp_path):
    import core.codex_bridge as cb
    models = {'models': [
        {'slug': 'deepseek-v4-flash', 'supports_search_tool': True, 'tool_mode': None},
        {'slug': 'deepseek-v4-pro', 'supports_search_tool': None, 'tool_mode': None},
        {'slug': 'glm-5.3', 'supports_search_tool': None, 'tool_mode': None},
    ]}
    p = tmp_path / 'models.json'
    p.write_text(json.dumps(models), encoding='utf-8')
    cb._patch_models_json(str(p))
    data = json.loads(p.read_text(encoding='utf-8'))
    flags = {m['slug']: m.get('supports_search_tool') for m in data['models']}
    assert flags['deepseek-v4-flash'] is False, 'deepseek 系必须置 False（防 Deferred 工具陷阱）'
    assert flags['deepseek-v4-pro'] is False
    assert flags['glm-5.3'] is None, '非 deepseek 模型不动'
