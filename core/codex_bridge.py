# -*- coding: utf-8 -*-
"""codex_bridge — Codex app-server 桥（PT-CB15 SPIKE 第三/四问·Qoder）。

契约：docs/brain-adapter.md v0.1「Codex 全量形态」（恒 provenance='real'·真流式）。
链路：POST /api/v1/aiqa/codex_engine（api/aiqa_routes.py）→ 本桥 → spawn
`codex app-server --stdio`（JSON-RPC over JSONL·cwd=仓外隔离目录·防本仓 AGENTS.md 注入）
→ item/agentMessage/delta 等通知 → 映射为 SSE 事件流 → 前端 brain-adapter-codex.js。
协议依据：codex-rs/app-server/README.md（JSON-RPC 2.0 无 jsonrpc 头·stdio 默认稳定面）。
版本锚点：codex-cli 0.149.1（tests/fixtures/codex_appserver_schema/README.md）。

spike 边界（诚实标注）：单例进程无看门狗重启（进程死→下轮 ensure 重建）；并发=每请求
占一 turn（app-server 单进程串行处理 turn·并发请求排队——低频 spike 场景可接受）。
"""
import asyncio
import json
import os
import shutil
import time

from core.tracker import register_track_id

register_track_id(
    'MOD_AIQA.F_042',
    'codex_bridge ask（PT-CB15 SPIKE：Codex app-server 桥·stdio JSONL 常驻单例·'
    'item/agentMessage/delta→SSE 事件流·thread 续用支持多轮·cwd 仓外隔离）')

# cwd 隔离（派发单红线：不指向本仓·防 9-Agent 协作规范 AGENTS.md 注入 Codex 上下文）
_SPIKE_CWD = r'D:\Github\_codex_spike_cwd'

_HEARTBEAT_S = 15          # SSE 心跳周期（对齐 render SSE 先例·防反代 60s 读超时）
_TURN_TIMEOUT_S = 300      # 单 turn 看门狗（PT-CB14 实证多工具链 50-366s·取慢侧上浮）
_MAX_TOOLNAME = 60


def _resolve_codex_exe():
    """codex 可执行体解析：PATH 直 hit（.exe）→ npm 全局包 vendor 路径（Windows 下
    CreateProcess 不能直跑 npm shim .cmd——dsh BA 同源坑 P6 实证复现）。
    失败返 None（fail-closed·调用方语义化 error 事件·不 500）。"""
    exe = shutil.which('codex')
    if exe and exe.lower().endswith('.exe'):
        return exe
    npm_root = os.path.join(os.environ.get('APPDATA', ''), 'npm')
    cand = os.path.join(npm_root, 'node_modules', '@openai', 'codex', 'node_modules',
                        '@openai', 'codex-win32-x64', 'vendor',
                        'x86_64-pc-windows-msvc', 'bin', 'codex.exe')
    return cand if os.path.isfile(cand) else None


class CodexBridge:
    """codex app-server 常驻桥（模块级单例 _BRIDGE·惰性 ensure）。

    ask() 是 async generator：yield SSE 事件 dict（event ∈ delta/tool/done/error/ping）。
    thread_id 跨 ask 复用（同 thread 连续 turn/start = 多轮对话·Q4 验证面）。
    """

    def __init__(self):
        self._proc = None
        self._thread_id = None
        self._req_id = 0
        self._lock = asyncio.Lock()   # turn 串行闸（app-server 单进程·防交错）

    async def _send(self, obj):
        self._proc.stdin.write(json.dumps(obj, ensure_ascii=False).encode('utf-8') + b'\n')
        await self._proc.stdin.drain()

    async def _next_id(self):
        self._req_id += 1
        return self._req_id

    async def _request(self, method, params, want_id=None):
        """发请求并等待对应 id 的响应（中途通知丢弃——仅握手期用·通知期走 ask 流）。"""
        rid = want_id if want_id is not None else await self._next_id()
        await self._send({'method': method, 'id': rid, 'params': params})
        while True:
            line = await self._proc.stdout.readline()
            if not line:
                raise ConnectionError('app-server stdout EOF（进程退出）')
            try:
                msg = json.loads(line)
            except Exception:
                continue
            if msg.get('id') == rid:
                if 'error' in msg:
                    raise RuntimeError(f'{method} 失败: {json.dumps(msg["error"], ensure_ascii=False)[:200]}')
                return msg.get('result') or {}

    async def ensure(self):
        """惰性启动：spawn app-server → initialize 握手 → thread/start（含复用重建）。"""
        if self._proc and self._proc.returncode is None and self._thread_id:
            return
        exe = _resolve_codex_exe()
        if not exe:
            raise RuntimeError('codex.exe 未找到（npm i -g @openai/codex 后可用·双机差异注记）')
        if not os.path.isdir(_SPIKE_CWD):
            os.makedirs(_SPIKE_CWD, exist_ok=True)
        self._proc = await asyncio.create_subprocess_exec(
            exe, 'app-server', '--stdio',
            # PT-CB15 用户令（08-24）：COH 的 LLM 调用接全局 DeepSeek Flash（deepseek-chat）——
            # -c 定向覆盖只作用于本进程（用户桌面 Codex 的顶层 glm 配置不受影响）。
            # key 在仓外 ~/.codex/config.toml [model_providers.deepseek]（不入仓·见复刻清单）。
            '-c', 'model_provider="deepseek"',
            '-c', 'model="deepseek-chat"',
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,   # stderr 仅 rmcp 噪音（他 server）·弃流
            cwd=_SPIKE_CWD,
            limit=16 * 1024 * 1024)   # Q4 坑修复：单行 JSONL 上限（默认 64KB）——render_spec 大结果
            #   的 mcpToolCall.completed 单行可达数百 KB·readline 超限抛
            #   'Separator is not found, and chunk exceed the limit'（spike 第四问实测）
        await self._request('initialize', {
            'clientInfo': {'name': 'emc-codex-bridge', 'title': 'EMC Codex Bridge', 'version': '0.1.0'}})
        await self._send({'method': 'initialized', 'params': {}})
        res = await self._request('thread/start', {
            'cwd': _SPIKE_CWD, 'approvalPolicy': 'never', 'sandbox': 'read-only'})
        self._thread_id = (res.get('thread') or {}).get('id')
        if not self._thread_id:
            raise RuntimeError('thread/start 未返回 thread.id')
        # MCP 启动通知（emc ready 与否）顺带读掉——不走 _request（非请求响应流）
        # 注：startupStatus 通知会在 ask 流期间到达·ask 里透传为 tool 事件。

    async def ask(self, question, timeout_s=None):
        """跑一轮 turn·yield SSE 事件（delta/tool/done/error/ping·SSE 端点直译）。

        注：F_042 埋点在端点层（post_codex_engine F_043 链路覆盖）——track_async 装饰器
        将 async generator 包成 coroutine（__aiter__ 丢失·spike 实证）·故本函数不挂装饰器。
        """
        t0 = time.time()
        try:
            await self.ensure()
        except Exception as e:
            yield {'event': 'error', 'code': 'CODEX_BRIDGE_START',
                   'message': f'Codex 桥启动失败: {e}'}
            return
        budget = timeout_s or _TURN_TIMEOUT_S
        async with self._lock:
            rid = await self._next_id()
            try:
                await self._send({'method': 'turn/start', 'id': rid, 'params': {
                    'threadId': self._thread_id,
                    'input': [{'type': 'text', 'text': question}],
                    'approvalPolicy': 'never', 'sandbox': 'read-only'}})
            except Exception as e:
                yield {'event': 'error', 'code': 'CODEX_TURN_START',
                       'message': f'turn/start 发送失败: {e}'}
                return

            completed = False
            n_delta = 0
            _reason_sent = False
            while not completed:
                # 看门狗 + 心跳：readline 带超时（超时发 ping·总预算到发 error 收口）
                try:
                    line = await asyncio.wait_for(self._proc.stdout.readline(), _HEARTBEAT_S)
                except asyncio.TimeoutError:
                    if time.time() - t0 > budget:
                        yield {'event': 'error', 'code': 'CODEX_TURN_TIMEOUT',
                               'message': f'Codex turn 超时（{budget}s）·本轮已中止'}
                        return
                    yield {'event': 'ping', 'elapsed': round(time.time() - t0, 1)}
                    continue
                if not line:
                    yield {'event': 'error', 'code': 'CODEX_PROC_EOF',
                           'message': 'app-server 进程退出（stdout EOF）——下轮将自动重建'}
                    self._proc = None
                    self._thread_id = None
                    return
                try:
                    msg = json.loads(line)
                except Exception:
                    continue   # 非 JSON 行（噪音）容错跳过

                m = msg.get('method', '')
                p = msg.get('params') or {}
                if m == 'item/agentMessage/delta':
                    d = p.get('delta') or ''
                    if d:
                        n_delta += 1
                        yield {'event': 'delta', 'kind': 'content', 'delta': d, 'n': n_delta}
                elif m == 'item/started':
                    item = p.get('item') or {}
                    t = item.get('type', '')
                    if t == 'reasoning' and not _reason_sent:
                        _reason_sent = True   # Q4 瑕疵修复：推理占位符仅发一次（多轮 item/started 会重复·防累积污染正文）
                        yield {'event': 'delta', 'kind': 'reason',
                               'delta': '（Codex 推理中…）\n', 'n': n_delta}
                    elif t in ('mcpToolCall', 'commandExecution', 'webSearch'):
                        name = (item.get('tool') or item.get('command') or t)[:_MAX_TOOLNAME]
                        srv = item.get('server') or ''
                        yield {'event': 'tool', 'phase': 'begin', 'name': name, 'server': srv}
                elif m == 'item/completed':
                    item = p.get('item') or {}
                    t = item.get('type', '')
                    if t in ('mcpToolCall', 'commandExecution', 'webSearch'):
                        name = (item.get('tool') or item.get('command') or t)[:_MAX_TOOLNAME]
                        ok = item.get('status') == 'completed'
                        err = (item.get('error') or {}).get('message', '') if item.get('error') else ''
                        yield {'event': 'tool', 'phase': 'end', 'name': name, 'ok': ok,
                               'error': err[:120]}
                elif m == 'turn/completed':
                    turn = p.get('turn') or {}
                    status = turn.get('status') or '?'
                    if status != 'completed' and not n_delta:
                        em = ((turn.get('error') or {}).get('message')) or status
                        yield {'event': 'error', 'code': 'CODEX_TURN_FAIL', 'message': str(em)[:200]}
                    else:
                        final = ''
                        try:
                            final = turn.get('output') or ''
                        except Exception:
                            pass
                        yield {'event': 'done', 'status': status, 'n_delta': n_delta,
                               'elapsed': round(time.time() - t0, 1),
                               'final_len': len(final or '')}
                    completed = True
                elif m == 'error' or 'error' in msg:
                    yield {'event': 'error', 'code': 'CODEX_PROTOCOL',
                           'message': json.dumps(msg, ensure_ascii=False)[:200]}

    async def close(self):
        if self._proc and self._proc.returncode is None:
            try:
                self._proc.kill()
            except Exception:
                pass
        self._proc = None
        self._thread_id = None


_BRIDGE = CodexBridge()


def get_bridge():
    """模块级单例访问（端点用·跨请求保 thread=多轮）。"""
    return _BRIDGE
