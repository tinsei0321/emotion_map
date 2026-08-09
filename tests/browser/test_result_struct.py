"""出口三段式·结果结构化纯函数直测（CB-18 S-3 补证·Codex 建议）。

经 e2e-seam 暴露的 window.__emcTest.buildResultStruct 直测真实 JS 逻辑（非 Python 复刻）：
- P0-1/P0-4：观点提取——draft 含 `> **观点：**` → insight 有值（整块捕获）；无标记 → null 不显卡（W3 保守化）
- P0-2：4 要点——method/data/result/conclusion 四段确定性组装（不解析 draft markdown）
- P2-1：结论段带地点——rows 带 place_name → 学术句式含地名（按尺度）
- P1-5/P2：scale 三档 → 宏观/中观/微观标注（_scaleCN）
- P0-3：三路径都出卡由 harness.js 三处 _dispatchResultStruct 接线保证（:705/:819/:1962）·
    buildResultStruct 是共享纯函数——此处直测其确定性，接线由回归期浏览器抽验（S-5）补 DOM 断言

无需 LLM（纯函数·无副作用），与 test_r7_truncation 同级稳定。

运行：py tests/browser/test_result_struct.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session


def _rs(page, arg):
    """调 buildResultStruct（真实 JS 逻辑·确定性纯函数）。"""
    return page.evaluate("(arg) => window.__emcTest.buildResultStruct(arg)", arg)


def _draft(with_insight, extra=''):
    base = '**方法：** zonal_stats 聚合。\n**数据：** ermawu_l3l4_t3。\n**结果：** 生成图层。'
    if with_insight:
        return '> **观点：**西陵区消极面以"老旧破败 + 停车难"为主·治理优先级应高于伍家岗。\n\n' + base + extra
    return base + extra


def main() -> int:
    with emc_session() as page:
        page.wait_for_function("() => !!(window.__emcTest && window.__emcTest.buildResultStruct)", timeout=45000)

        # ── P0-1：观点提取——有标记 → insight 有值（整块捕获）──
        r1 = _rs(page, {
            'question': '西陵区哪些区域情绪最差？', 'draft': _draft(True),
            'diagnose': {'method': ['zonal_stats'], 'data_plan': ['ermawu_l3l4_t3']},
            'registryText': 'zonal 图层', 'scale': 'macro', 'rows': [],
        })
        assert r1['insight'] and '西陵区' in r1['insight'], f'P0-1 应提取观点（insight={r1["insight"]!r}）'
        assert r1['points'], 'P0-1 应有 4 要点'

        # ── P0-4：无观点不显卡——无标记 → insight null（W3 保守化·不取动作描述当观点）──
        r2 = _rs(page, {'question': '西陵区情绪', 'draft': _draft(False), 'diagnose': {}, 'rows': []})
        assert r2['insight'] is None, f'P0-4 无观点标记应 null（insight={r2["insight"]!r}）'

        # ── P0-2：4 要点四段结构——method/data/result/conclusion 键齐全且确定性组装 ──
        r3 = _rs(page, {
            'question': '西陵区哪些区域情绪最差？', 'draft': _draft(True),
            'diagnose': {'method': ['zonal_stats', 'rank'], 'data_plan': {'available': ['ermawu_l3l4_t3']}},
            'registryText': '西陵区情绪聚合', 'toolHistory': [{}, {}],
            'scale': 'macro', 'rows': [{'name': '西陵区', 'polarity_index': -0.6, 'point_count': 300}],
        })
        p3 = r3['points']
        for k in ('method', 'data', 'result', 'conclusion'):
            assert k in p3, f'P0-2 4 要点应含 {k}（keys={list(p3)}）'
        assert 'zonal_stats' in p3['method'], f'P0-2 method 应含方法（{p3["method"]!r}）'
        assert 'ermawu_l3l4_t3' in p3['data'], f'P0-2 data 应含数据（{p3["data"]!r}）'
        assert '西陵区情绪聚合' in p3['result'], f'P0-2 result 应含 registry（{p3["result"]!r}）'

        # ── P2-1：结论段带地点——rows 带 place_name → 学术句式含地名 ──
        r4 = _rs(page, {
            'question': '西陵区哪些区域情绪最差？', 'draft': _draft(True),
            'diagnose': {'method': ['zonal_stats']}, 'scale': 'macro',
            'rows': [{'place_name': '大南门', 'polarity_index': -0.6, 'point_count': 300, 'issue_label': '停车难'}],
        })
        c4 = r4['points']['conclusion']
        assert '大南门' in c4 and '-0.6' in c4 and '300' in c4, f'P2-1 结论应含地名+数值（{c4!r}）'
        assert '停车难' in c4, f'P2-1 结论应含归因（{c4!r}）'

        # ── P1-5/P2：scale 三档 → 宏观/中观/微观标注 ──
        for scale, cn in [('macro', '宏观'), ('meso', '中观'), ('micro', '微观')]:
            r = _rs(page, {'question': 'q', 'draft': _draft(True), 'diagnose': {}, 'scale': scale,
                           'rows': [{'name': 'X', 'polarity_index': -0.1, 'point_count': 5}]})
            assert cn in r['points']['conclusion'], f'scale={scale} 结论应含 {cn}（{r["points"]["conclusion"]!r}）'

        # ── 边界：rows 缺 place_name → 诚实降级「关注区域」（不编造地名）──
        r5 = _rs(page, {'question': 'q', 'draft': _draft(True), 'diagnose': {}, 'scale': 'macro',
                        'rows': [{'polarity_index': -0.4, 'point_count': 50}]})
        assert '关注区域' in r5['points']['conclusion'], f'P2-1 无地名应降级"关注区域"（{r5["points"]["conclusion"]!r}）'

        print('[OK] PASS — 出口三段式 result-struct：观点提取/无观点不显卡/4 要点/结论带地点/scale 三档/无地名降级')
        return 0


if __name__ == '__main__':
    sys.exit(main())
