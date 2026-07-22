"""EMC browser 测试辅助（Playwright sync）。
复用 frontend/serve.py 链路（with_server.py 起 :8080，serve.py 自起后端 :8000 + /api 反代）。
提供：开页 → 发问 → 抓 /geo 网络调用 → 等回答完成。供 tests/browser/ 下各用例复用。
"""
import contextlib
import json
import os
import subprocess
import time
import urllib.request

from playwright.sync_api import sync_playwright, Page

EMC_URL = 'http://localhost:8080/frontend/index.html?e2e=1'   # ?e2e=1 → index.html dynamic-load e2e-seam.js（注入 fixture 点层；main.js 零 test 代码）
GEO_BASE = '/api/v1/geo/'
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))   # tests/browser/lib/ → repo root


def _wait_health(port: int, timeout: int = 90) -> bool:
    """等 serve.py + 后端就绪（/api/v1/health 通）。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/api/v1/health', timeout=2).read()
            return True
        except Exception:
            time.sleep(1)
    return False


@contextlib.contextmanager
def emc_session(port: int = 8080, headless: bool = True, open: bool = True):
    """一键自管：起 serve.py（自起后端 :8000 + /api 反代）+ 等 health + 起 chromium + open_emc。

    yield 已 open 的 page；退出同停 serve + browser。复用 test_compare_regions 的稳定手动流程
    （不用 with_server.py：该包装下 main.js 模体加载时序异常）。新用例复用本上下文，勿各自重抄。
    """
    serve = subprocess.Popen(['py', 'frontend/serve.py', str(port)], cwd=REPO)
    try:
        if not _wait_health(port):
            raise RuntimeError(f'serve.py 后端未就绪（port {port}，查 DEEPSEEK_API_KEY / uvicorn 启动）')
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            try:
                if open:
                    open_emc(page)
                yield page
            finally:
                browser.close()
    finally:
        # 杀进程树（serve.py 自起 uvicorn :8000 子进程；仅 terminate 父进程会留 uvicorn 孤儿占端口，
        # 跨测试级联冲突 → Windows 用 taskkill /T 杀全树）。
        try:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(serve.pid)], capture_output=True)
            else:
                serve.terminate()
            serve.wait(timeout=10)
        except Exception:
            try:
                serve.kill()
            except Exception:
                pass


def open_emc(page: Page, url: str = EMC_URL, wait_ms: int = 1500) -> None:
    """开 EMC 主页 + 等 EMC 面板挂载。

    不用 networkidle/domcontentloaded（地图瓦片持续加载 + head 脚本阻塞致 goto 假超时）；
    用 commit（导航收到响应即返）+ 等 #chat-input 挂载（真正判定 EMC 就绪）。
    不在此 focus 输入框——聚焦会展开 EMC 改变左栏状态、影响后续 #lp-upload 触发 filechooser；
    折叠态展开交由 send_prompt 的 fill 自然触发（panel.js focus 监听 setEmcCollapsed(false)）。
    """
    page.goto(url, wait_until='commit')
    page.wait_for_selector('#chat-input', timeout=30000)   # EMC 面板挂载
    page.wait_for_selector('#lp-upload', timeout=15000, state='attached')     # 左栏侧栏 init 完成（change 监听绑在 attach，非可见态——左栏折叠时按钮 hidden 但监听已就绪）
    page.wait_for_timeout(wait_ms)   # 等左栏/图层工具栏就绪


def send_prompt(page: Page, text: str) -> None:
    """填 #chat-input + 点 #chat-send（等价欢迎胶囊点击 → send(text)）。"""
    page.fill('#chat-input', text)
    page.click('#chat-send')


def inject_points(page: Page, fc: dict) -> None:
    """经 E2E test seam（?e2e=1 → window.__emcTest.loadPoints）注入点层 fixture（确定性）。

    地图空启动（main.js "No seed sample"），compare/zonal 需可见点层。
    不走 Import 对话框（file_chooser/set_input_files 均受 UI 时序影响 flaky）；
    直接调 e2e-seam.js 暴露的 loadPoints（复用 Import 点层装载逻辑）。fc = GeoJSON dict。
    """
    page.wait_for_function("() => !!window.__emcTest", timeout=45000)   # seam 就绪（main 模块加载后；冷启动 main.js 加载较慢）
    # 直接注入：loadPoints 容忍地图底图未加载（addLayer 入 state 即可被 zonal_stats 用，不依赖地图渲染）。
    res = page.evaluate("(fc) => window.__emcTest.loadPoints(fc)", fc)
    if not (res and res.get('ok')):
        raise AssertionError(f'注入点层失败: {res}')
    page.wait_for_function(
        "() => /积极|消极|中性/.test(document.querySelector('#left-panel')?.innerText || '')",
        timeout=15000)
    page.wait_for_timeout(800)   # 渲染稳定


class GeoCapture:
    """捕获 POST /api/v1/geo/<path> 的响应（status + body）。

    用 page.on('response') 收 response 对象；body 在 wait_calls 里现取（避 event 内阻塞）。
    """

    def __init__(self, page: Page):
        self.page = page
        self._resps = []   # [{path, resp}]
        page.on('response', self._on_resp)

    def _on_resp(self, resp):
        try:
            url = resp.url
            method = resp.request.method
        except Exception:
            return
        if method != 'POST':
            return
        idx = url.find(GEO_BASE)
        if idx < 0:
            return
        path = url[idx + len(GEO_BASE):].split('?')[0]
        self._resps.append({'path': path, 'resp': resp})

    def _read(self, entry):
        """取一条的 status + body（body 取不到返 None，wait_calls 会重试）。"""
        resp = entry['resp']
        out = {'path': entry['path'], 'status': None, 'body': None}
        try:
            out['status'] = resp.status   # Playwright Python: status 是属性（非方法）
        except Exception:
            pass
        try:
            out['body'] = resp.json()
        except Exception:
            out['body'] = None
        return out

    def wait_calls(self, path: str, expected: int, timeout_ms: int = 60000) -> list:
        """等到 path 收到 >= expected 个响应（每个已读到 body 或确认无 body）。

        返 [{path, status, body}]（仅 path 匹配的）。超时抛 AssertionError。
        """
        import time
        deadline = time.time() + timeout_ms / 1000
        while time.time() < deadline:
            matched = [self._read(e) for e in self._resps if e['path'] == path]
            # 已读到的（body 非 None 或 status 非 2xx 无 body）算 settled
            settled = [m for m in matched if m['body'] is not None or (m['status'] and m['status'] >= 400)]
            if len(settled) >= expected:
                return settled[:expected]
            self.page.wait_for_timeout(300)
        raise AssertionError(
            f'等待 POST {GEO_BASE}{path} × {expected} 超时（仅收到 {len(matched)} 个）')

    def all(self, path: str = None) -> list:
        """取当前已捕获（path 可选筛）。"""
        out = []
        for e in self._resps:
            if path and e['path'] != path:
                continue
            out.append(self._read(e))
        return out


def wait_answer_done(page: Page, timeout_ms: int = 60000) -> str:
    """等 EMC 回答完成：流式光标 .chat-cursor 消失 + 最后一个 .aiq-answer 有内容。

    返回答文本（.aiq-answer innerText）。超时返当前文本（供软断言）。
    """
    js = ("() => { const all=document.querySelectorAll('.aiq-answer'); "
          "const el=all[all.length-1]; const cur=document.querySelector('.chat-cursor'); "
          "return (all.length>0 && el && el.innerText.trim().length>0 && !cur); }")
    try:
        page.wait_for_function(js, timeout=timeout_ms)   # 仅等条件成立（返回 JSHandle 不用作字符串）
    except Exception:
        pass
    els = page.locator('.aiq-answer')
    return els.last.inner_text(timeout=5000) if els.count() else ''


# ── A1 谓词测试范式（GUIDANCE §1.1；G1 谓词导出后启用，P0 先就位） ──────────────
def read_predicate(page: Page, expr: str):
    """读客户端谓词真值（A1 谓词级测试基建）。

    expr = page.evaluate 求值的 JS（函数体或表达式），返回布尔/可强转布尔。
    例（G1 谓词就绪后）：read_predicate(page, "() => window.__cpdPredicates.hasVisibleEmotionLayer()")。
    把死信号/谓词盲区从评审发现变测试发现——P0 建范式，谓词 cpd-state.js 导出后用例 10 直接用。
    """
    return page.evaluate(expr)


def wait_predicate(page: Page, expr: str, expected=True, timeout_ms: int = 10000):
    """轮询直到谓词 == expected（状态变化有延迟，如注入点层后情绪性判定）。超时返当前值。"""
    deadline = time.time() + timeout_ms / 1000
    val = None
    while time.time() < deadline:
        try:
            val = page.evaluate(expr)
        except Exception:
            val = None
        if bool(val) == expected:
            return val
        page.wait_for_timeout(200)
    return val


# ── /chat 请求体捕获（用例 2 domain_lens threading） ─────────────────────────────
class ChatRequestCapture:
    """捕获 POST /api/v1/chat 请求体（解析 domain_lens 等结构字段 threading）。

    用 page.on('request') 收请求；post_data JSON 解析在 all() 现取。
    用例 2：diagnose 产 domain_lens 后，后续 step 前端须结构化回传 ChatRequest.domain_lens
    （非压扁进 context）——断言 ≥1 个 /chat 请求体 domain_lens 为非空数组。
    """

    CHAT_PATH = '/api/v1/chat'

    def __init__(self, page: Page):
        self.page = page
        self._reqs = []
        page.on('request', self._on_req)

    def _on_req(self, req):
        try:
            if req.method != 'POST' or self.CHAT_PATH not in req.url:
                return
        except Exception:
            return
        self._reqs.append(req)

    def _read(self, req):
        payload = None
        try:
            pd = req.post_data
            payload = json.loads(pd) if pd else None
        except Exception:
            payload = None
        return {
            'phase': (payload or {}).get('phase'),
            'domain_lens': (payload or {}).get('domain_lens'),
            'payload': payload,
        }

    def all(self):
        return [self._read(r) for r in self._reqs]

    def wait_domain_lens(self, timeout_ms: int = 60000):
        """等到至少一个 /chat 请求体携带非空 domain_lens 数组（结构化回传证据）。超时返 None。"""
        deadline = time.time() + timeout_ms / 1000
        while time.time() < deadline:
            for r in self.all():
                dl = r.get('domain_lens')
                if isinstance(dl, list) and dl:
                    return r
            self.page.wait_for_timeout(300)
        return None
