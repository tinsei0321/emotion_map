"""EMC browser 测试辅助（Playwright sync）。
复用 frontend/serve.py 链路（with_server.py 起 :8080，serve.py 自起后端 :8000 + /api 反代）。
提供：开页 → 发问 → 抓 /geo 网络调用 → 等回答完成。供 tests/browser/ 下各用例复用。
"""
from playwright.sync_api import sync_playwright, Page

EMC_URL = 'http://localhost:8080/frontend/index.html?e2e=1'   # ?e2e=1 → index.html dynamic-load e2e-seam.js（注入 fixture 点层；main.js 零 test 代码）
GEO_BASE = '/api/v1/geo/'


def open_emc(page: Page, url: str = EMC_URL, wait_ms: int = 1500) -> None:
    """开 EMC 主页 + 等 EMC 面板挂载。

    不用 networkidle/domcontentloaded（地图瓦片持续加载 + head 脚本阻塞致 goto 假超时）；
    用 commit（导航收到响应即返）+ 等 #chat-input 挂载（真正判定 EMC 就绪）。
    不在此 focus 输入框——聚焦会展开 EMC 改变左栏状态、影响后续 #lp-upload 触发 filechooser；
    折叠态展开交由 send_prompt 的 fill 自然触发（panel.js focus 监听 setEmcCollapsed(false)）。
    """
    page.goto(url, wait_until='commit')
    page.wait_for_selector('#chat-input', timeout=30000)   # EMC 面板挂载
    page.wait_for_selector('#lp-upload', timeout=15000)     # 左栏侧栏 init 完成（change 监听已绑）
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
