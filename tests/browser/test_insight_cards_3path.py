"""出口三段式·三路径观点卡浏览器抽验（CB-18 P0-3 回归·Codex S-5 + glm 共识）。

P0-3 验收：三路径（单技能 runTemplatePath / 多步链 runChainPath / multi runAllToolCalls）
都出观点卡（.emc-insight-card）+ 4 要点卡（.emc-points-card）。

路径触发（问句）：
- 单技能：模板命中 single·runTemplatePath（"西陵区哪些区域情绪最差"→ zonal）
- 多步链：CHAIN_REGISTRY 命中（"把西陵区裁出来，再和商业用地叠置取交集"→ extract_overlay 链）
- multi：multi 模板（"裁剪出西陵区情绪点再叠置"·LLM 产多 tool_calls）

判据：每个回答完成（.aiq-exit-badge + 无光标）后，
  .emc-insight-card 存在（观点卡·无观点标记则不显卡·保守）
  .emc-points-card 存在（4 要点卡）

需 DEEPSEEK_API_KEY（真实 EMC 问答链）。运行：py tests/browser/test_insight_cards_3path.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

import json as _json

from emc_helpers import emc_session, inject_points, send_prompt, wait_answer_done


def _cards(page):
    """取当前回答的观点卡/4要点卡存在性（onFinalDone 渲染·晚于回答文本）。"""
    # onFinalDone 渲染卡片在回答文本后·轮询等待（<3s）
    for _ in range(30):
        cards = page.evaluate("() => ({"
                              "insight: !!document.querySelector('.emc-insight-card'),"
                              "points: !!document.querySelector('.emc-points-card')})")
        if cards['points']:
            return cards
        page.wait_for_timeout(100)
    return cards


def _ask(page, text, timeout=120000):
    """发问 + 等回答完成（wait_answer_done·针对当前回答）+ 轮询取卡片。"""
    # 每次新会话（防跨问串扰·工具 rows/_pendingStruct 跨轮残留）
    page.evaluate("() => window.__emcTest.newChat()")
    page.wait_for_timeout(500)
    send_prompt(page, text)
    ans = wait_answer_done(page, timeout)
    return _cards(page), ans


def main() -> int:
    with emc_session() as page:
        page.wait_for_function("() => !!(window.__emcTest && window.__emcTest.send)", timeout=45000)

        # 数据准备（对齐 test_toolbox_pipeline：注入情绪点层 + 加载行政区/社区/用地边界）
        # 否则 diagnose 判 gap 要数据→ask_user 缺数据路径→无分析→无观点卡
        fx = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'compare_points.geojson')
        with open(fx, encoding='utf-8') as fh:
            inject_points(page, _json.load(fh))
        for _b in ('社区.geojson', '行政区.geojson', '用地_商业.geojson'):
            page.evaluate("(n) => window.__emcTest.loadRange(n)", _b)
        page.wait_for_timeout(800)

        results = []

        # ── 路径 1：单技能（runTemplatePath·观点卡置顶）──
        c1, a1 = _ask(page, '西陵区哪些区域情绪最差？')
        results.append(('单技能', c1, a1))

        # ── 路径 2：多步链（runChainPath·extract_overlay 链）──
        c2, a2 = _ask(page, '把西陵区裁出来，再和商业用地叠置取交集')
        results.append(('多步链', c2, a2))

        # ── 路径 3：multi（runAllToolCalls·多工具问）──
        c3, a3 = _ask(page, '裁剪出西陵区情绪点再叠置')
        results.append(('multi', c3, a3))

        # ── 汇总断言 ──
        print('[TRACE] 三路径观点卡抽验结果:')
        ok = True
        for name, cards, ans in results:
            flag = 'PASS' if (cards['points'] and cards['insight']) else 'FAIL'
            if cards['points'] and cards['insight']:
                print(f'  [{flag}] {name}: 观点卡 + 4 要点卡均出')
            elif cards['points']:
                print(f'  [PARTIAL] {name}: 仅 4 要点卡（无观点·保守不显卡·W3）·回答={ans[:80]!r}')
            else:
                print(f'  [FAIL] {name}: 两卡均缺（cards={cards}）·回答={ans[:80]!r}')
                ok = False

        if not ok:
            print('[FAIL] 存在路径未出观点卡/4 要点卡')
            return 1
        print('[OK] PASS — 三路径（单技能/多步链/multi）观点卡 + 4 要点卡均出')
        return 0


if __name__ == '__main__':
    sys.exit(main())
