# -*- coding: utf-8 -*-
"""codex_bridge — Codex app-server 桥（PT-CB15 SPIKE→转正批·Qoder）。

契约：docs/brain-adapter.md v0.1「Codex 全量形态」（恒 provenance='real'·真流式）。
链路：POST /api/v1/aiqa/codex_engine（api/aiqa_routes.py）→ 本桥 → spawn
`codex app-server --stdio`（JSON-RPC over JSONL·cwd=仓外隔离目录·防本仓 AGENTS.md 注入）
→ item/agentMessage/delta 等通知 → 映射为 SSE 事件流 → 前端 brain-adapter-codex.js。
协议依据：codex-rs/app-server/README.md（JSON-RPC 2.0 无 jsonrpc 头·stdio 默认稳定面）。
版本锚点：codex-cli 0.149.1（tests/fixtures/codex_appserver_schema/README.md）。

SSE 帧分隔约定（P2-11）：事件帧 = `event: <名>\ndata: <JSON>\n\n`（LF·双换行分帧）；
解析端须兼容 CRLF（\r\n\r\n）——见 brain-adapter-codex.js 归一化。

转正批修复（PT-CB15 PROMOTE）：
  P1-1（Z-01）看门狗「有流量即续命」——预算检查移到每行到达即查（不止静默分支）；
  P2-1（Z-02）tool begin/end 透传 item.id（前端配对用）；
  P2-2 cwd 改 {REPO} 同级推导（去硬编码盘符·仍仓外隔离）；
  P2-3（Z-04）codex.exe 多候选探测（PATH→APPDATA npm→npm root -g·glob 多 triplet）；
  P2-4（B-4）model/provider 读环境变量（CODEX_MODEL_PROVIDER/CODEX_MODEL·默认 deepseek+deepseek-chat）；
  P2-5（Z-05/B-5）stderr 环形缓冲末 4KB·error 事件随带（诊断面不再弃流）；
  P3（Z-07）握手 wait_for 30s；Z-08（_reason_sent 每 turn 重置——ask 局部变量天然满足·验证在案）。

spike 边界（诚实标注·转正保留）：并发=每请求占一 turn（app-server 单进程串行处理
turn·并发请求排队——低频场景可接受）；进程死→下轮 ensure 自动重建。
"""
import asyncio
import glob
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from core.tracker import register_track_id

register_track_id(
    'MOD_AIQA.F_042',
    'codex_bridge ask（PT-CB15 SPIKE→转正：Codex app-server 桥·stdio JSONL 常驻单例·'
    'item/agentMessage/delta→SSE 事件流·thread 续用支持多轮·cwd 仓外隔离·'
    '每行预算看门狗+stderr 诊断面+item.id 配对）')

# P2-2：cwd 隔离目录 = {REPO} 的同级目录（仓外·防本仓 9-Agent 协作规范 AGENTS.md 注入 Codex 上下文）。
# 原硬编码盘符已废（三组全抓）——双机/换盘自适应·复刻清单登记。
_REPO_ROOT = Path(__file__).resolve().parents[1]
_CODEX_CWD = str(_REPO_ROOT.parent / '_codex_cwd')

_HEARTBEAT_S = 15          # SSE 心跳周期（对齐 render SSE 先例·防反代 60s 读超时）
_TURN_TIMEOUT_S = 300      # 单 turn 看门狗（PT-CB14 实证多工具链 50-366s·取慢侧上浮）
_HANDSHAKE_TMO_S = 30      # P3（Z-07）：握手请求响应超时
_STDERR_KEEP = 4096        # P2-5：stderr 环形缓冲保留末 4KB
_MAX_TOOLNAME = 60


def _resolve_codex_exe():
    """codex 可执行体解析（P2-3·多候选探测）：

    1) PATH 直 hit（排除 .cmd/.bat npm shim——Windows CreateProcess 不能直跑·dsh BA 同源坑）；
    2) APPDATA/npm 默认全局目录的 vendor 路径（glob 全部平台 triplet·不限 win32-x64）；
    3) `npm root -g` 命令（覆盖 nvm/自定义 prefix 安装）。
    全败返 None（fail-closed·调用方语义化 error 事件·不 500）。
    """
    exe = shutil.which('codex')
    if exe and not exe.lower().endswith(('.cmd', '.bat')):
        return exe
    roots = []
    appdata_npm = os.path.join(os.environ.get('APPDATA', ''), 'npm',
                               'node_modules', '@openai', 'codex')
    if os.path.isdir(appdata_npm):
        roots.append(appdata_npm)
    try:
        out = subprocess.run(['npm', 'root', '-g'], capture_output=True,
                             text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            roots.append(os.path.join(out.stdout.strip(), '@openai', 'codex'))
    except Exception:
        pass   # npm 不在 PATH——候选 1/2 仍有机会
    for root in roots:
        pattern = os.path.join(root, 'node_modules', '@openai', 'codex-*',
                               'vendor', '*', 'bin', 'codex.exe')
        for cand in glob.glob(pattern):
            if os.path.isfile(cand):
                return cand
    return None


class CodexBridge:
    """codex app-server 常驻桥（模块级单例 _BRIDGE·惰性 ensure）。

    ask() 是 async generator：yield SSE 事件 dict（event ∈ delta/tool/done/error/ping）。
    thread_id 跨 ask 复用（同 thread 连续 turn/start = 多轮对话·Q4 验证面）。
    """

    def __init__(self):
        self._proc = None
        self._thread_id = None
        self._req_id = 0
        self._lock = asyncio.Lock()        # turn 串行闸（app-server 单进程·防交错）
        self._stderr_buf = bytearray()     # P2-5：stderr 环形缓冲（末 4KB）
        self._stderr_task = None

    async def _drain_stderr(self):
        """P2-5：后台抽 stderr 进环形缓冲（原 DEVNULL 弃流·error 时无诊断面——Z-05/B-5）。"""
        proc = self._proc
        try:
            while True:
                chunk = await proc.stderr.read(2048)
                if not chunk:
                    break
                self._stderr_buf.extend(chunk)
                if len(self._stderr_buf) > _STDERR_KEEP:
                    del self._stderr_buf[:len(self._stderr_buf) - _STDERR_KEEP]
        except Exception:
            pass   # 进程退出/管道关闭——缓冲保留到 error 事件消费

    def _stderr_tail(self):
        return self._stderr_buf[-_STDERR_KEEP:].decode('utf-8', 'replace')

    async def _send(self, obj):
        self._proc.stdin.write(json.dumps(obj, ensure_ascii=False).encode('utf-8') + b'\n')
        await self._proc.stdin.drain()

    async def _next_id(self):
        self._req_id += 1
        return self._req_id

    async def _request(self, method, params, want_id=None):
        """发请求并等待对应 id 的响应（中途通知丢弃——仅握手期用·通知期走 ask 流）。

        P3（Z-07）：readline 挂 30s 超时——app-server 无响应时语义化报错·不死等。
        """
        rid = want_id if want_id is not None else await self._next_id()
        await self._send({'method': method, 'id': rid, 'params': params})
        while True:
            try:
                line = await asyncio.wait_for(self._proc.stdout.readline(), _HANDSHAKE_TMO_S)
            except asyncio.TimeoutError:
                raise RuntimeError(f'{method} 握手超时（{_HANDSHAKE_TMO_S}s 无响应）')
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
        if self._stderr_task:   # 重建前收旧诊断任务
            self._stderr_task.cancel()
            self._stderr_task = None
        exe = _resolve_codex_exe()
        if not exe:
            raise RuntimeError('codex.exe 未找到（npm i -g @openai/codex 后可用·双机差异注记）')
        if not os.path.isdir(_CODEX_CWD):
            os.makedirs(_CODEX_CWD, exist_ok=True)
        # P2-4：model/provider 读环境变量（默认 deepseek+deepseek-chat·用户令 08-24）。
        # -c 定向覆盖只作用于本进程（用户桌面 Codex 的顶层配置不受影响）。
        provider = os.environ.get('CODEX_MODEL_PROVIDER', 'deepseek')
        model = os.environ.get('CODEX_MODEL', 'deepseek-chat')
        self._stderr_buf = bytearray()
        self._proc = await asyncio.create_subprocess_exec(
            exe, 'app-server', '--stdio',
            '-c', f'model_provider="{provider}"',
            '-c', f'model="{model}"',
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,   # P2-5：抽进环形缓冲（末 4KB·随 error 事件携带）
            cwd=_CODEX_CWD,
            limit=16 * 1024 * 1024)   # Q4 坑修复：单行 JSONL 上限（默认 64KB）——render_spec 大结果
            #   的 mcpToolCall.completed 单行可达数百 KB·readline 超限抛
            #   'Separator is not found, and chunk exceed the limit'（spike 第四问实测）
        self._stderr_task = asyncio.create_task(self._drain_stderr())
        await self._request('initialize', {
            'clientInfo': {'name': 'emc-codex-bridge', 'title': 'EMC Codex Bridge', 'version': '0.1.0'}})
        await self._send({'method': 'initialized', 'params': {}})
        res = await self._request('thread/start', {
            'cwd': _CODEX_CWD, 'approvalPolicy': 'never', 'sandbox': 'read-only'})
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
                       'message': f'turn/start 发送失败: {e}', 'stderr_tail': self._stderr_tail()}
                return

            completed = False
            n_delta = 0
            _reason_sent = False   # Z-08：ask 局部变量·每 turn 天然重置（在案验证·无需代码改动）
            while not completed:
                # 看门狗 + 心跳：readline 带超时（超时发 ping·总预算到发 error 收口）
                try:
                    line = await asyncio.wait_for(self._proc.stdout.readline(), _HEARTBEAT_S)
                except asyncio.TimeoutError:
                    if time.time() - t0 > budget:
                        yield {'event': 'error', 'code': 'CODEX_TURN_TIMEOUT',
                               'message': f'Codex turn 超时（{budget}s）·本轮已中止',
                               'stderr_tail': self._stderr_tail()}
                        return
                    yield {'event': 'ping', 'elapsed': round(time.time() - t0, 1)}
                    continue
                except ValueError as e:   # 纵深防御：readline 超单行上限（已有 16MB limit·兜底不 500）
                    yield {'event': 'error', 'code': 'CODEX_LINE_LIMIT',
                           'message': f'JSONL 单行超限: {e}', 'stderr_tail': self._stderr_tail()}
                    return
                if not line:
                    yield {'event': 'error', 'code': 'CODEX_PROC_EOF',
                           'message': 'app-server 进程退出（stdout EOF）——下轮将自动重建',
                           'stderr_tail': self._stderr_tail()}
                    self._proc = None
                    self._thread_id = None
                    return
                # P1-1（Z-01）：看门狗「有流量即续命」——预算检查在**每行到达即查**，
                # 不止静默超时分支：持续吐行（哪怕合法事件）也必在预算到达时收口。
                if time.time() - t0 > budget:
                    yield {'event': 'error', 'code': 'CODEX_TURN_TIMEOUT',
                           'message': f'Codex turn 超时（{budget}s·有流量仍超预算）·本轮已中止',
                           'stderr_tail': self._stderr_tail()}
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
                        # P2-1（Z-02）：透传 item.id——前端 begin/end 复用同 id 配对（防并行工具错配）
                        yield {'event': 'tool', 'phase': 'begin', 'name': name, 'server': srv,
                               'item_id': item.get('id') or ''}
                elif m == 'item/completed':
                    item = p.get('item') or {}
                    t = item.get('type', '')
                    if t in ('mcpToolCall', 'commandExecution', 'webSearch'):
                        name = (item.get('tool') or item.get('command') or t)[:_MAX_TOOLNAME]
                        ok = item.get('status') == 'completed'
                        err = (item.get('error') or {}).get('message', '') if item.get('error') else ''
                        yield {'event': 'tool', 'phase': 'end', 'name': name, 'ok': ok,
                               'error': err[:120], 'item_id': item.get('id') or ''}
                elif m == 'turn/completed':
                    turn = p.get('turn') or {}
                    status = turn.get('status') or '?'
                    if status != 'completed' and not n_delta:
                        em = ((turn.get('error') or {}).get('message')) or status
                        yield {'event': 'error', 'code': 'CODEX_TURN_FAIL', 'message': str(em)[:200],
                               'stderr_tail': self._stderr_tail()}
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
                           'message': json.dumps(msg, ensure_ascii=False)[:200],
                           'stderr_tail': self._stderr_tail()}

    async def close(self):
        if self._stderr_task:
            self._stderr_task.cancel()
            self._stderr_task = None
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
