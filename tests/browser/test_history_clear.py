"""用例 8（CPD 地基行为）· 历史垃圾桶全清。

#emc-history-clear（panel.js:1601）→ clearAllHistory()（:245）清空 _archive，
#emc-history-list（:1295）的 .emc-history-item 归零（confirm dialog 二次确认）。

预设 localStorage ai_qa_archive_v1 假会话（add_init_script，确定性，免 LLM 归档）。

运行：py tests/browser/test_history_clear.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session, open_emc

ARCHIVE_KEY = 'ai_qa_archive_v1'
FAKE_ARCHIVE = [
    {'id': 's_e2e_1', 'title': 'e2e 假会话一', 'history': [], 'createdAt': 1700000000000},
    {'id': 's_e2e_2', 'title': 'e2e 假会话二', 'history': [], 'createdAt': 1700000001000},
]


def main() -> int:
    with emc_session(open=False) as page:
        # 导航前注入假 archive（loadArchive 读 localStorage → 切历史视图时 renderHistoryList 渲染）
        page.add_init_script(
            f"localStorage.setItem({ARCHIVE_KEY!r}, {json.dumps(FAKE_ARCHIVE, ensure_ascii=False)!r})")
        open_emc(page)
        # 折叠态藏 head（含 #chat-history）→ 先 focus 输入框展开，再点 #chat-history 切历史视图
        page.focus('#chat-input')
        page.wait_for_timeout(500)
        page.locator('#chat-history').click()
        page.wait_for_selector('#emc-history-list .emc-history-item', timeout=10000)

        n0 = page.locator('#emc-history-list .emc-history-item').count()
        assert n0 >= 2, f'预置 archive 未渲染出历史项（得 {n0}，期 ≥2）'

        # accept confirm dialog + force-click 清空钮（clearAllHistory → _archive=[] → 重渲染归零）
        page.on('dialog', lambda d: d.accept())
        page.locator('#emc-history-clear').click(force=True)
        page.wait_for_timeout(600)

        n1 = page.locator('#emc-history-list .emc-history-item').count()
        assert n1 == 0, f'清空后历史项未归零（得 {n1}，期 0）'

        print(f'[OK] PASS — 历史全清 {n0} → {n1}')
        return 0


if __name__ == '__main__':
    sys.exit(main())
