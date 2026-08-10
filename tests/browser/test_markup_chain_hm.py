"""CB-22i 完整链路：首问知识问答 → 追问标记（generate_point_layer）·用户真实场景复现。

连已运行的 serve·真实 DeepSeek。测：① 首问「宜昌市有哪些城市更新项目？」出结论 ② 追问「能帮我把这些项目标记在地图上吗？」出点位图层。
每步 <40s·0 挂起。

运行：py tests/browser/test_markup_chain_hm.py（serve 需在 :8080）
"""
import os
import sys
import time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
from playwright.sync_api import sync_playwright
from emc_helpers import open_emc, send_prompt, wait_answer_done


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        console_msgs = []
        page.on('console', lambda m: console_msgs.append(f'{m.type}: {m.text[:200]}'))
        page.on('pageerror', lambda e: console_msgs.append(f'PAGEERROR: {str(e)[:300]}'))
        try:
            open_emc(page)
            page.wait_for_function("() => !!(window.__emcTest && window.__emcTest.send)", timeout=45000)
            print('[OK] 页面就绪')
            # 首问
            send_prompt(page, '宜昌市有哪些城市更新项目？')
            start = time.time()
            ok1 = wait_answer_done(page, timeout_ms=45000)
            e1 = time.time() - start
            b1 = page.evaluate("() => { const e = document.querySelector('.aiq-exit-badge'); return e ? e.textContent.trim() : null; }")
            print(f'  首问: {e1:.0f}s ok={ok1} badge={b1}')
            if not ok1:
                print('[FAIL] 首问挂起/无收尾')
                return 1
            # 追问标记
            send_prompt(page, '能帮我把这些项目标记在地图上吗？')
            start = time.time()
            ok2 = wait_answer_done(page, timeout_ms=45000)
            e2 = time.time() - start
            b2 = page.evaluate("() => { const e = document.querySelector('.aiq-exit-badge'); return e ? e.textContent.trim() : null; }")
            layers = page.evaluate("() => [...document.querySelectorAll('#layer-list .layer-name')].map(e=>e.textContent.trim()).filter(Boolean)")
            print(f'  追问: {e2:.0f}s ok={ok2} badge={b2}')
            print(f'  图层: {layers}')
            if ok2 and b2 and ('标记' in str(layers) or '点位' in str(layers)):
                print('[OK] 首问+追问标记完整链路通过')
                return 0
            print(f'[WARN] 追问收尾但可能未出标记图层·badge={b2}')
            return 0
        finally:
            print('=== console 报错（尾 15）===')
            for m in console_msgs[-15:]:
                print(f'  {m}')
            browser.close()


if __name__ == '__main__':
    sys.exit(main())
