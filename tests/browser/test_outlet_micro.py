"""P3-4（CB-19）微观落点 E2E：micro rows 产物 → 出口卡需求位置 POI 精确化 + 诚实标注。

经 e2e-seam 暴露的 __emcTest 直测（稳定·不赌博 LLM 路由·仿 test_outlet_macro.py）：
- setOutletRows(rows)：设 _lastToolRows 缓存（模拟 micro zonal/rank 产物·含 place_name/place_name_source/poi_names）
- buildOutletCardForTest(diagnose, ctx, newLayerCount)：直调 _maybeBuildOutletCard → POST /outlet_card → 卡 JSON

验证 P3-4 修复（CB-19·出口闭环最后一块）：
- Gap B：rows 带 place_name（prop_cols 放行）→ 需求位置不再「暂无数据」
- Gap C：micro + poi_top_places（place_name=边界名·有 poi_names）→ 需求位置升级为首个 POI
- Gap A：limitations 按 place_name_source 动态标注（不硬编码"格内最近 POI"）
- geo_label：micro → 「微观·落点：<POI 名>」

运行：py tests/browser/test_outlet_micro.py（需 serve·起自管）
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session, open_emc


def main() -> int:
    with emc_session() as page:
        open_emc(page, url='http://localhost:8080/frontend/index.html?e2e=1', wait_ms=2500)
        page.wait_for_function("() => !!(window.__emcTest && __emcTest.buildOutletCardForTest)", timeout=45000)

        # ── 场景 1：micro + poi_top_places（place_name=边界名·有 poi_names）→ 需求位置升级为首个 POI ──
        rows1 = [{'place_name': '大南门·二马路滨江片区', 'place_name_source': 'poi_top_places',
                  'poi_names': '滨江公园、二马路老巷 等3处', 'polarity_index': -0.32,
                  'domain_top': 'urban_renewal', 'element_top': '设施',
                  'issue_label': '停车难', 'point_count': 900}]
        page.evaluate("(r) => __emcTest.setOutletRows(r)", rows1)
        card1 = page.evaluate("""() => __emcTest.buildOutletCardForTest(
          { scale: 'micro', domain_lens: ['urban_renewal'], outlet: '建议清单' },
          { question: '大南门更新需求分析' }, 0)""")
        assert card1 and isinstance(card1, list) and card1[0], f'场景1 应出卡（实际 {card1}）'
        c1 = card1[0]   # Wave 3 多卡：cards 数组首卡
        vals1 = {k: str(f.get('value')) for k, f in (c1.get('fields') or {}).items()}
        srcs1 = {k: str(f.get('source')) for k, f in (c1.get('fields') or {}).items()}
        assert '滨江公园' in vals1.get('需求位置', ''), \
            f'场景1 需求位置应升级为首个 POI（poi_names 首个·实际 {vals1.get("需求位置")}）'
        assert 'POI 落点' in srcs1.get('需求位置', ''), \
            f'场景1 需求位置 source 应标 POI 落点升级（{srcs1.get("需求位置")}）'
        assert c1['geo_label'].startswith('微观·落点'), \
            f'场景1 geo_label 应微观·落点（{c1["geo_label"]}）'
        lims1 = ' '.join(c1['limitations'])
        assert '面域代表名' in lims1, f'场景1 limitations 应标 poi_top_places 面域代表名（{lims1}）'
        print('[OK] 场景1 micro + poi_top_places → 需求位置升级为首个 POI + geo_label 微观·落点 + 诚实标注')

        # ── 场景 2：micro + poi_sjoin（已精确·格内最近 POI）→ 需求位置保持·source 标精确 ──
        rows2 = [{'place_name': '万达广场', 'place_name_source': 'poi_sjoin',
                  'poi_names': '万达广场、沃尔玛 等2处', 'polarity_index': -0.5,
                  'domain_top': 'urban_renewal', 'element_top': '服务',
                  'issue_label': '配套不足', 'point_count': 60}]
        page.evaluate("(r) => __emcTest.setOutletRows(r)", rows2)
        card2 = page.evaluate("""() => __emcTest.buildOutletCardForTest(
          { scale: 'micro', domain_lens: ['urban_renewal'], outlet: '建议清单' },
          { question: '万达广场更新需求分析' }, 0)""")   # 含「更新需求」触发词（前端 OUTLET_TRIGGER_KW 前置门）
        assert card2 and isinstance(card2, list) and card2[0], f'场景2 应出卡（实际 {card2}）'
        c2 = card2[0]
        vals2 = {k: str(f.get('value')) for k, f in (c2.get('fields') or {}).items()}
        srcs2 = {k: str(f.get('source')) for k, f in (c2.get('fields') or {}).items()}
        assert '万达广场' in vals2.get('需求位置', ''), \
            f'场景2 poi_sjoin 需求位置应保持 POI 名（{vals2.get("需求位置")}）'
        assert '精确' in srcs2.get('需求位置', ''), \
            f'场景2 poi_sjoin source 应标精确（{srcs2.get("需求位置")}）'
        lims2 = ' '.join(c2['limitations'])
        assert '精确' in lims2, f'场景2 limitations 应标精确（poi_sjoin·{lims2}）'
        print('[OK] 场景2 micro + poi_sjoin → 需求位置保持 POI 名 + source 标精确')

        # ── 场景 3：micro + 无 poi_names → 需求位置保持·source 标粗略（诚实不编造）──
        rows3 = [{'place_name': '西陵区', 'place_name_source': 'spatial_hotspot',
                  'polarity_index': -0.4, 'domain_top': 'urban_renewal',
                  'element_top': '环境', 'issue_label': '老旧', 'point_count': 30}]
        page.evaluate("(r) => __emcTest.setOutletRows(r)", rows3)
        card3 = page.evaluate("""() => __emcTest.buildOutletCardForTest(
          { scale: 'micro', domain_lens: ['urban_renewal'], outlet: '建议清单' },
          { question: '西陵区更新需求分析' }, 0)""")   # 含「更新需求」触发词
        assert card3 and isinstance(card3, list) and card3[0], f'场景3 应出卡（实际 {card3}）'
        c3 = card3[0]
        vals3 = {k: str(f.get('value')) for k, f in (c3.get('fields') or {}).items()}
        srcs3 = {k: str(f.get('source')) for k, f in (c3.get('fields') or {}).items()}
        assert '西陵区' in vals3.get('需求位置', ''), \
            f'场景3 无 poi_names 需求位置应保持（{vals3.get("需求位置")}）'
        assert '粗略' in srcs3.get('需求位置', ''), \
            f'场景3 无 poi_names source 应标粗略（{srcs3.get("需求位置")}）'
        print('[OK] 场景3 micro + 无 poi_names → 需求位置保持 + source 标粗略（诚实不编造）')

        print('[OK] PASS — P3-4 微观落点：poi_top_places 升级 / poi_sjoin 保持精确 / 无 POI 诚实粗略')
        return 0


if __name__ == '__main__':
    sys.exit(main())
