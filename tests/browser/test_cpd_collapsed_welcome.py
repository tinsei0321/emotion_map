"""用例 5（CPD 地基行为）· 默认折叠欢迎卡。

F5 默认折叠胶囊（不记忆上轮展开态·用户定 2026-07-22）+ 空态欢迎卡开场。
守 CPD 地基"默认折叠 + 欢迎卡"契约（plan v1.0 §八 P0 地基行为）。

无需 LLM（纯 load）——最稳，先跑验 serve + Playwright 管线。

运行：py tests/browser/test_cpd_collapsed_welcome.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session


def main() -> int:
    with emc_session() as page:
        collapsed = page.locator('#emc-panel').evaluate("el => el.classList.contains('is-collapsed')")
        assert collapsed, 'EMC 未默认折叠（#emc-panel 缺 is-collapsed）'

        welcome = page.locator('.emc-welcome')
        assert welcome.count() >= 1, '空态欢迎卡 .emc-welcome 未渲染'

        ph = page.evaluate("document.getElementById('chat-input').placeholder")
        assert ph and ph.strip(), f'折叠态 placeholder 为空: {ph!r}'

        print(f'[OK] PASS — #emc-panel.is-collapsed + .emc-welcome 可见 + placeholder="{ph[:30]}"')
        return 0


if __name__ == '__main__':
    sys.exit(main())
