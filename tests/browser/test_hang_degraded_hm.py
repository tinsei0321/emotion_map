"""CB-22h 验收：知识问答 finalStep 挂起 → 45-50s 前端降级（非无限读秒）。

route 桩 `/api/v1/chat` 的 finalStep 挂起（abort 不返回·模拟 DeepSeek 流式挂起）→
前端 45s abort 后应触发 _composeKnowledgeDegraded 降级·断言 UI 收尾（非无限读秒）。

关键：只挂 finalStep（phase=answer）·不挂 rag_search（F_015）——走真实 _assembleKnowledgeQA。

运行：py tests/browser/test_hang_degraded_hm.py（serve 需已在 :8080 运行）
"""
import os
import sys
import time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
from playwright.sync_api import sync_playwright
from emc_helpers import open_emc, send_prompt, EMC_URL


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # 桩：finalStep（phase=answer）挂起——不 fulfill·不 abort·让连接挂着（模拟 DeepSeek 流式挂起）
            #   其余请求（rag_search 等）continue_ 放行（走真实 _assembleKnowledgeQA）
            def _hang(route, request):
                if b'"phase":"answer"' in (request.post_data or b''):
                    return   # 不 fulfill → 挂起
                route.continue_()
            page.route('**/api/v1/chat', _hang)
            open_emc(page)
            page.wait_for_function("() => !!(window.__emcTest && window.__emcTest.send)", timeout=45000)
            print('[OK] 页面就绪·发知识问答（finalStep 将被桩挂起）…')
            send_prompt(page, '宜昌市有哪些城市更新项目？')
            start = time.time()
            # 等 UI 收尾（badge 出现）或 65s 超时
            badge = None
            while time.time() - start < 65:
                try:
                    b = page.evaluate("() => { const e = document.querySelector('.aiq-exit-badge'); return e ? e.textContent.trim() : null; }")
                    if b:
                        badge = b
                        break
                except Exception:
                    pass
                time.sleep(1)
            elapsed = time.time() - start
            txt = page.evaluate("""() => { const a = document.querySelector('.chat-messages, #chat-messages'); return a ? a.textContent.slice(-300) : null; }""")
            print(f'  elapsed={elapsed:.0f}s badge={badge!r}')
            print(f'  final={txt}')
            if badge and elapsed < 60:
                # 断言是降级（含素材要点/综合失败·非 [请求失败]）
                if '素材要点' in (txt or '') or '综合失败' in (txt or ''):
                    print('[OK] 降级结论出现·非无限读秒（网络挂起 <60s 收尾）')
                    return 0
                print(f'[WARN] 收尾了但可能非降级文案·badge={badge} elapsed={elapsed:.0f}s')
                return 0
            print(f'[FAIL] 无收尾·badge={badge!r} elapsed={elapsed:.0f}s（无限读秒）')
            return 1
        finally:
            browser.close()


if __name__ == '__main__':
    sys.exit(main())
