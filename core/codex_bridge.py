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
  P2-4（B-4）model/provider/reasoning_effort 读环境变量（CODEX_MODEL_PROVIDER/CODEX_MODEL/CODEX_REASONING_EFFORT·
  默认 deepseek+deepseek-v4-flash+high·官方最新规则：弃用 deepseek-chat 旧别名·规范名 v4-flash·默认思考模式）；
  P2-5（Z-05/B-5）stderr 环形缓冲末 4KB·error 事件随带（诊断面不再弃流）；
  P3（Z-07）握手 wait_for 30s；Z-08（_reason_sent 每 turn 重置——ask 局部变量天然满足·验证在案）；
  2026-08-26 配置隔离：harness 独立 CODEX_HOME 自愈——与桌面 Codex 工具彻底分离（共享
  ~/.codex 被桌面应用改写致冲突反复）；模型锁定 deepseek-v4-flash 全局不可切换（用户令·
  P2-4 环境变量切换退役）；models.json Deferred 补丁自动化；emc required 迁出桌面配置。

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

register_track_id(
    'MOD_AIQA.F_045',
    'codex_bridge _ensure_harness_home（2026-08-26 配置隔离：harness 自备 CODEX_HOME 自愈生成——'
    '与桌面 Codex 工具彻底分离·锁定 deepseek-v4-flash 全局不可切换·'
    'models.json Deferred 补丁自动化·密钥运行时复制不进仓）')

# P2-2：cwd 隔离目录 = {REPO} 的同级目录（仓外·防本仓 9-Agent 协作规范 AGENTS.md 注入 Codex 上下文）。
# 原硬编码盘符已废（三组全抓）——双机/换盘自适应·复刻清单登记。
_REPO_ROOT = Path(__file__).resolve().parents[1]
_CODEX_CWD = str(_REPO_ROOT.parent / '_codex_cwd')

# 配置隔离：harness 自备 CODEX_HOME（_codex_cwd/.codex·机器生成自愈）——与桌面 Codex 工具的
# ~/.codex 配置彻底分离：桌面应用升级/model 切换会持续改写共享配置（曾致冲突反复），
# 且 emc MCP required=true 放桌面配置会让桌面工具在 8600 未起时全部工具调用快速失败。
# 隔离后：桌面配置禁放 [mcp_servers.emc]·harness 配置永不被桌面改写。
_CODEX_HOME = str(Path(_CODEX_CWD) / '.codex')
_DESKTOP_CODEX_HOME = str(Path.home() / '.codex')

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


def _load_desktop_config():
    """读桌面 Codex 配置（仅提取 [model_providers.*]·密钥运行时复制·不进仓）。"""
    path = os.path.join(_DESKTOP_CODEX_HOME, 'config.toml')
    if not os.path.isfile(path):
        return {}
    try:
        import tomllib
        with open(path, 'rb') as f:
            return tomllib.load(f)
    except Exception:
        return {}


def _fallback_providers():
    """桌面配置无 providers 时退环境变量 DEEPSEEK_API_KEY（L1 管线同源·若无返 None）。"""
    key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not key:
        return None
    return {'deepseek': {'name': 'deepseek',
                         'base_url': 'https://api.deepseek.com/',
                         'wire_api': 'responses',
                         'experimental_bearer_token': key}}


def _harness_config_text(providers):
    """harness config.toml 文本（机器生成·每次自愈重写）。

    模型锁定 deepseek-v4-flash（用户令 2026-08-26：全局不可切换·P2-4 环境变量切换退役）；
    emc MCP required=true 迁入本配置（fail-fast 保留·桌面配置摘除后不再误伤桌面工具）。
    """
    catalog = _CODEX_HOME.replace('\\', '/') + '/models.json'
    lines = [
        '# EMC Codex Harness 专用配置（机器生成·勿手改·每次桥启动自愈重写）',
        '# 配置隔离：本文件与桌面 ~/.codex/config.toml 互不影响（见 docs/codex-harness-ops.md 纪律 3）',
        'model = "deepseek-v4-flash"',
        'model_provider = "deepseek"',
        'model_reasoning_effort = "high"',
        'model_catalog_json = "%s"' % catalog,
        '',
        '[mcp_servers.emc]',
        'url = "http://127.0.0.1:8600/mcp"',
        'startup_timeout_sec = 60',
        'tool_timeout_sec = 120',
        'required = true',
        'default_tools_approval_mode = "approve"',
        '',
    ]
    for name, pv in (providers or {}).items():
        lines.append('[model_providers.%s]' % name)
        for k, v in pv.items():
            if isinstance(v, bool):
                lines.append('%s = %s' % (k, 'true' if v else 'false'))
            elif isinstance(v, str):
                lines.append('%s = %s' % (k, json.dumps(v, ensure_ascii=False)))
            else:
                lines.append('%s = %s' % (k, json.dumps(v)))
        lines.append('')
    return '\n'.join(lines)


def _patch_models_json(path):
    """防 Deferred 工具陷阱（ops 纪律·配置隔离起自动化）：deepseek 系模型若
    supports_search_tool=true 且 tool_mode=null，Codex 会把全部 MCP 工具设 Deferred，
    emc 工具在模型工具面中静默消失。强制置 false（幂等·每次自愈）。"""
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return
    changed = False
    for m in data.get('models', []):
        if str(m.get('slug') or '').startswith('deepseek') \
                and m.get('supports_search_tool') is not False:
            m['supports_search_tool'] = False
            changed = True
    if changed:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def _ensure_harness_home():
    """配置隔离（MOD_AIQA.F_045）：自愈生成 harness 独立 CODEX_HOME（{REPO}/../_codex_cwd/.codex）。

    1) config.toml 每次重写（机器生成·锁定 flash + emc required）——桌面应用升级/model
       切换改写的是 ~/.codex，本文件不受影响；
    2) models.json：源（桌面版）缺失/更新时复制，并强制 deepseek 系
       supports_search_tool=false（Deferred 陷阱补丁）；
    3) auth.json：缺失时从桌面复制（不改写）。
    桌面 providers 缺失且无 DEEPSEEK_API_KEY → RuntimeError（fail-closed·语义化）。
    """
    home = Path(_CODEX_HOME)
    home.mkdir(parents=True, exist_ok=True)

    providers = _load_desktop_config().get('model_providers')
    if not providers:
        providers = _fallback_providers()
    if not providers:
        raise RuntimeError('桌面 ~/.codex/config.toml 无 model_providers 且未设 '
                           'DEEPSEEK_API_KEY——harness 无法启动')
    (home / 'config.toml').write_text(_harness_config_text(providers), encoding='utf-8')

    src_models = os.path.join(_DESKTOP_CODEX_HOME, 'models.json')
    dst_models = home / 'models.json'
    if os.path.isfile(src_models) and (
            not dst_models.exists()
            or os.path.getmtime(src_models) > dst_models.stat().st_mtime):
        shutil.copyfile(src_models, dst_models)
    _patch_models_json(dst_models)

    src_auth = os.path.join(_DESKTOP_CODEX_HOME, 'auth.json')
    dst_auth = home / 'auth.json'
    if os.path.isfile(src_auth) and not dst_auth.exists():
        shutil.copyfile(src_auth, dst_auth)
    return _CODEX_HOME


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
        self._active_turn_id = None        # P0-A：当前 turn id（供非正常收口时 interrupt）

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

    async def _interrupt_turn(self):
        """P0-A：非正常收口时通知 app-server 中断当前 turn（best-effort·失败仅静默）。"""
        tid = getattr(self, '_active_turn_id', None)
        if not tid or not self._proc or self._proc.returncode is not None:
            return
        try:
            rid = await self._next_id()
            await self._send({'method': 'turn/interrupt', 'id': rid, 'params': {
                'threadId': self._thread_id, 'turnId': tid}})
        except Exception:
            pass

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
        # 配置隔离：harness 自备 CODEX_HOME（配置隔离桌面工具·锁定 deepseek-v4-flash·
        #   详见 _ensure_harness_home）——P2-4 的 -c 环境变量切换已退役（全局 flash 不可切换）。
        try:
            _ensure_harness_home()
        except Exception as e:
            raise RuntimeError(f'harness CODEX_HOME 自愈失败: {e}')
        if not os.path.isdir(_CODEX_CWD):
            os.makedirs(_CODEX_CWD, exist_ok=True)
        self._stderr_buf = bytearray()
        env = dict(os.environ)
        env['CODEX_HOME'] = _CODEX_HOME
        self._proc = await asyncio.create_subprocess_exec(
            exe, 'app-server', '--stdio',
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,   # P2-5：抽进环形缓冲（末 4KB·随 error 事件携带）
            cwd=_CODEX_CWD,
            env=env,
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
                        await self._interrupt_turn()
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
                    await self._interrupt_turn()
                    yield {'event': 'error', 'code': 'CODEX_PROC_EOF',
                           'message': 'app-server 进程退出（stdout EOF）——下轮将自动重建',
                           'stderr_tail': self._stderr_tail()}
                    self._proc = None
                    self._thread_id = None
                    return
                # P1-1（Z-01）：看门狗「有流量即续命」——预算检查在**每行到达即查**，
                # 不止静默超时分支：持续吐行（哪怕合法事件）也必在预算到达时收口。
                if time.time() - t0 > budget:
                    await self._interrupt_turn()
                    yield {'event': 'error', 'code': 'CODEX_TURN_TIMEOUT',
                           'message': f'Codex turn 超时（{budget}s·有流量仍超预算）·本轮已中止',
                           'stderr_tail': self._stderr_tail()}
                    return
                try:
                    msg = json.loads(line)
                except Exception:
                    continue   # 非 JSON 行（噪音）容错跳过

                if msg.get('id') == rid:
                    result = msg.get('result') or {}
                    turn = result.get('turn') or {}
                    self._active_turn_id = turn.get('id') or self._active_turn_id
                    continue

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
