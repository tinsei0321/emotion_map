"""Wave 1（macro 出口）E2E：rows 产物 → 出口卡片出卡（.outlet-card·字段非空）。

经 e2e-seam 暴露的 __emcTest 直测（稳定·不赌博 LLM 路由·与 test_r7_truncation 同模式）：
- setOutletRows(rows)：设 _lastToolRows 缓存（模拟 macro zonal/rank 产物·含 issue_label/polarity_index）
- buildOutletCardForTest(diagnose, ctx, newLayerCount)：直调 _maybeBuildOutletCard（门放宽·newLayerCount=0 也出卡）→ POST 后端 /outlet_card → 卡 JSON

验证 Wave 1 修复（CB-16 两组预检反评价）：
- ② 门放宽：newLayerCount=0 + rows 非空 → 出卡（旧逻辑直接 return·不出卡）
- ① _extract_emc_value 统一收 rows：卡字段取到 rows 值（更新对象 ← issue_label·非"暂无数据"）
- ④ checkup_dimension scale 限定：macro 问句 → 城区维度填值·其余"需对应尺度分析"

运行：py tests/browser/test_outlet_macro.py（需 serve·起自管）
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session, open_emc


def main() -> int:
    with emc_session() as page:
        open_emc(page, url='http://localhost:8080/frontend/index.html?e2e=1', wait_ms=2500)
        page.wait_for_function("() => !!(window.__emcTest && __emcTest.buildOutletCardForTest)", timeout=45000)

        # ── 场景 1：macro rows 产物 → renewal_object_identify 出卡（newLayerCount=0·门放宽）──
        # P3-4（CB-19）：rows 带 place_name/place_name_source（prop_cols 放行）→ 出口卡可读到地点（Gap B 端到端链路）
        rows = [
            {'name': '西陵区', 'place_name': '滨江公园', 'place_name_source': 'poi_sjoin',
             'polarity_index': -0.42, 'domain_top': 'urban_renewal',
             'element_top': '环境', 'issue_label': '老旧破败', 'point_count': 300},
            {'name': '伍家岗区', 'place_name': '万达广场', 'place_name_source': 'poi_sjoin',
             'polarity_index': -0.21, 'domain_top': 'urban_renewal',
             'element_top': '设施', 'issue_label': '停车难', 'point_count': 200},
        ]
        page.evaluate("(r) => __emcTest.setOutletRows(r)", rows)
        card1 = page.evaluate("""() => __emcTest.buildOutletCardForTest(
          { scale: 'macro', domain_lens: ['urban_renewal'], outlet: '生成图层' },
          { question: '宜昌城区哪些区域更新优先' }, 0)""")
        assert card1 and isinstance(card1, list) and card1[0], \
            f'场景1 应命中 renewal_object_identify（newLayerCount=0 也出卡·门放宽）·实际 {card1}'
        c1 = card1[0]   # Wave 3 多卡：cards 数组首卡
        assert c1.get('outlet_id') == 'renewal_object_identify', \
            f'场景1 应命中 renewal_object_identify（实际 {c1.get("outlet_id")}）'
        vals1 = {k: str(f.get('value')) for k, f in (c1.get('fields') or {}).items()}
        assert '老旧破败' in vals1.get('更新对象（疑似）', ''), \
            f'场景1 更新对象应取 rows issue_label（{vals1}）'
        assert any(v != '暂无数据' for v in vals1.values()), f'场景1 字段不应全降级（{vals1}）'
        assert c1['data_base']['N'] == 2 and c1['data_base']['total_points'] == 500, \
            f'场景1 data_base 应为单元数+总评论数（{c1["data_base"]}）'
        # P3-4：limitations 读 place_name_source（poi_sjoin → 精确标注·Gap A 端到端）
        lims1 = ' '.join(c1['limitations'])
        assert '精确' in lims1, f'场景1 limitations 应标 poi_sjoin 精确（{lims1}）'
        print(f'[OK] 场景1 macro rows → renewal_object_identify 出卡（newLayerCount=0·门放宽）+ 字段非空 + data_base 单元数 + 地点标注精确')

        # ── 场景 2：checkup_dimension scale 限定（macro 问句 → 城区维度填值·其余需对应尺度）──
        rows2 = [{'name': '宜昌城区', 'polarity_index': 0.15, 'domain_top': 'urban_governance',
                  'element_top': '环境', 'issue_label': '绿量不足', 'point_count': 1000}]
        page.evaluate("(r) => __emcTest.setOutletRows(r)", rows2)
        card2 = page.evaluate("""() => __emcTest.buildOutletCardForTest(
          { scale: 'macro', domain_lens: ['urban_governance'], outlet: '报告结论' },
          { question: '中心城区城市体检评估' }, 0)""")
        assert card2 and isinstance(card2, list) and card2[0], \
            f'场景2 应命中 checkup_dimension（实际 {card2}）'
        c2 = card2[0]
        assert c2.get('outlet_id') == 'checkup_dimension', \
            f'场景2 应命中 checkup_dimension（实际 {c2.get("outlet_id")}）'
        vals2 = {k: str(f.get('value')) for k, f in (c2.get('fields') or {}).items()}
        assert '0.15' in vals2.get('城区维度', ''), f'场景2 城区维度应取 polarity_index（{vals2}）'
        assert '需对应尺度分析' in vals2.get('住房维度', ''), f'场景2 住房维度应标需对应尺度分析（{vals2}）'
        print('[OK] 场景2 checkup_dimension scale 限定：城区填值·住房/小区/街区需对应尺度')

        print('[OK] PASS — Wave 1 macro 出口：rows 门放宽出卡 + 字段非空 + scale 限定')
        return 0


if __name__ == '__main__':
    sys.exit(main())
