# -*- coding: utf-8 -*-
"""PT-CB11 K3 · A-4 版本徽章验收（隔离栈 8090/8009·不动用户 8080/8000）。

口径：①左下角 v<commit7> 角标可见（A-4b）②commit 不匹配 → 黄底硬刷新横幅（A-4c）
      ③横幅点击关闭 ④/version 经反代可达（前置 curl 已验）。
产出：_tmp/kimi_a4_1_badge.png / kimi_a4_2_banner.png + stdout JSON 摘要。
"""
import json
import sys

from playwright.sync_api import sync_playwright

OUT = 'D:/Github/emotion_map/_tmp'
BASE = 'http://127.0.0.1:8090/frontend/index.html'


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1400, 'height': 900})
        page.goto(BASE, wait_until='domcontentloaded')
        page.wait_for_timeout(12000)   # 底图+模块加载+version fetch

        badge = page.locator('#emc-version-badge')
        badge_ok = badge.count() > 0 and badge.is_visible()
        badge_text = badge.inner_text() if badge_ok else ''
        badge_title = badge.get_attribute('title') if badge_ok else ''
        page.screenshot(path=f'{OUT}/kimi_a4_1_badge.png')

        # A-4c：伪造旧 commit → 刷新 → 应出横幅；点击 → 关闭
        page.evaluate("localStorage.setItem('emc_version_commit', 'oldfake0')")
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(8000)
        banner = page.locator('#emc-version-banner')
        banner_ok = banner.count() > 0 and banner.is_visible()
        banner_text = banner.inner_text() if banner_ok else ''
        page.screenshot(path=f'{OUT}/kimi_a4_2_banner.png')
        if banner_ok:
            banner.click()
            page.wait_for_timeout(500)
        banner_closed = page.locator('#emc-version-banner').count() == 0
        # 横幅关闭后记录已更新 → 再刷新不应再出
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(6000)
        banner_reappear = page.locator('#emc-version-banner').count() > 0
        browser.close()

    print(json.dumps({
        'badge_visible': badge_ok, 'badge_text': badge_text, 'badge_title': badge_title,
        'banner_on_mismatch': banner_ok, 'banner_text': banner_text,
        'banner_click_closes': banner_closed, 'banner_no_reappear': not banner_reappear,
    }, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    sys.exit(main())
