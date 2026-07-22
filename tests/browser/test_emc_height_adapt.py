"""用例 7（CPD 地基行为）· 内容驱动高度自适应。

展开态 EMC 面板高度 > 折叠态（_fitEmcToContent 内容驱动 + .is-collapsed 局部覆盖）；
collapse/expand 往返基线可复现（plan v1.0 §八 P0 地基行为「拉长+缩回」）。

无需 LLM（focus/collapse 触发 setEmcCollapsed，断真实渲染高度 getBoundingClientRect）。
内容驱动拉长（chat 内容）由用例 6 的 wait_answer_done 间接覆盖，本例守 collapse 机制。

运行：py tests/browser/test_emc_height_adapt.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session


def _collapsed(page):
    return page.locator('#emc-panel').evaluate("el => el.classList.contains('is-collapsed')")


def _panel_height(page):
    return float(page.locator('#emc-panel').evaluate("el => el.getBoundingClientRect().height"))


def main() -> int:
    with emc_session() as page:
        assert _collapsed(page), '初始未默认折叠'
        h_folded = _panel_height(page)

        # focus 输入框 → 展开（panel.js:1650 focus 监听 setEmcCollapsed(false)）
        page.focus('#chat-input')
        page.wait_for_timeout(600)
        assert not _collapsed(page), 'focus 输入框后未展开'
        h_expanded = _panel_height(page)

        # 点 collapse 钮 → 再折叠（panel.js:1649 toggle）
        page.click('#chat-collapse')
        page.wait_for_timeout(600)
        assert _collapsed(page), '点 #chat-collapse 后未折叠'
        h_refolded = _panel_height(page)

        assert h_expanded > h_folded + 50, f'展开未明显变高: fold={h_folded:.0f} exp={h_expanded:.0f}'
        assert abs(h_refolded - h_folded) < 30, f'再折叠未回基线: fold={h_folded:.0f} refold={h_refolded:.0f}'

        print(f'[OK] PASS — 高度自适应 fold={h_folded:.0f} → exp={h_expanded:.0f} → refold={h_refolded:.0f}')
        return 0


if __name__ == '__main__':
    sys.exit(main())
