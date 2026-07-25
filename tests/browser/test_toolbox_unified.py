"""用例 12 · Toolbox 统一工具集层 E2E（手册 v2.2 §6 步 8）。

覆盖：
A. 7 tool-row 开 pane（新增 zonal/area-stats/rank/vector 4 入口 + heatmap/grid/buffer 回归）
B. 两路径比对：每工具 UI 生成一遍 + evaluate 直调 ForAI 一遍（kind/_ui.tool/命名 = 同一 _execute 核）
C. Buffer 双模式（cover/emotion）+ 编辑回填（新产物显式 kind；存量无 kind 按 color 判据·§4.3）
D. 无 console 报错（allowlist：资源 404/net/tile 噪音）

运行（自管 serve.py：起 :8080 + 自起后端 :8000，跑完同停）：
    py tests/browser/test_toolbox_unified.py
前置：DATA/boundaries/presets/ 已激活（行政区/用地_* 文件在）；.env DEEPSEEK_API_KEY 本用例非必需（不走 /chat）。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session

FAILS = []


def check(name, cond, detail=''):
    if cond:
        print(f'[OK] {name}')
    else:
        FAILS.append(name)
        print(f'[FAIL] {name} {detail}')


CONSOLE_ALLOW = ('Failed to load resource', 'net::', 'favicon', 'tile', '404', 'WebGL', 'GroupMarkerNotSet')


def ui_of(page, layer_id):
    return page.evaluate("(id) => { const l = window.__emcTest.getLayers().find((x) => x.id === id); return (l && l.paint && l.paint._ui) || null; }", layer_id)


def layer_by_name(page, name):
    return page.evaluate("(nm) => { const l = window.__emcTest.getLayers().find((x) => x.name === nm); return l ? { id: l.id, kind: l.kind, name: l.name } : null; }", name)


def pt_fc(page):
    return page.evaluate("() => { const l = window.__emcTest.getLayers().find((x) => x.kind === 'point' && x.visible !== false && x.colorMode && String(x.colorMode).startsWith('l2-')); return l ? l.fc : null; }")


def boundary_fc(page, fname):
    return page.evaluate("(n) => fetch('/DATA/boundaries/' + n).then((r) => r.json())", fname)


def click_tool(page, tool_id):
    """evaluate click（左栏折叠态下 tool-row 物理不可见，Playwright 原生 click 会等可见性超时）。"""
    page.evaluate("(id) => document.getElementById(id).click()", f'tool-{tool_id}')


def open_tool(page, tool_id, tab):
    click_tool(page, tool_id)
    page.wait_for_timeout(400)
    active = page.evaluate("() => document.querySelector('.pp-tab.is-active')?.dataset.ppTab || ''")
    pane_visible = page.evaluate(f"() => !document.querySelector('.pp-pane[data-pp-pane=\"{tab}\"]').hidden")
    check(f'A. tool-row {tool_id} 开 pane（tab={tab}）', active == tab and pane_visible, f'active={active} pane={pane_visible}')


def main() -> int:
    sys.stdout.reconfigure(encoding='utf-8')
    with emc_session() as page:
        console_errs = []

        def on_console(msg):
            if msg.type == 'error' and not any(a in (msg.text or '') for a in CONSOLE_ALLOW):
                console_errs.append(msg.text[:200])
        page.on('console', on_console)

        # ── 数据：L2 点层 + 行政区/用地_商业 Range 面层 ──
        r = page.evaluate("() => window.__emcTest.loadCSV('yichang_L2_T1_L2_result_csv.csv')")
        assert r and r.get('ok'), f'loadCSV 失败: {r}'
        page.evaluate("() => window.__emcTest.loadRange('行政区.geojson')")
        page.evaluate("() => window.__emcTest.loadRange('用地_商业.geojson')")
        page.wait_for_timeout(1000)

        # ── A. 7 tool-row 开 pane（先切左栏到 Toolbox 页·evaluate click 免折叠态可见性依赖）──
        page.evaluate("() => { const t = document.querySelector('.lp-tab[data-tab=\"toolbox\"]'); if (t) t.click(); }")
        page.wait_for_function("() => !document.querySelector('.lp-pane[data-pane=\"toolbox\"]').hidden", timeout=5000)
        open_tool(page, 'heatmap', 'heatmap')
        open_tool(page, 'grid', 'grid')
        open_tool(page, 'buffer', 'buffer')
        open_tool(page, 'zonal', 'zonal')
        open_tool(page, 'area-stats', 'area-stats')
        open_tool(page, 'rank', 'rank')
        open_tool(page, 'vector', 'vector')

        admin = boundary_fc(page, '行政区.geojson')
        commercial = boundary_fc(page, '用地_商业.geojson')
        pts = pt_fc(page)
        assert pts, '无可见 l2-* 点层'
        xiling = {'type': 'FeatureCollection', 'features': [f for f in admin['features'] if (f.get('properties') or {}).get('MC') == '西陵区']}
        wujiagang = {'type': 'FeatureCollection', 'features': [f for f in admin['features'] if (f.get('properties') or {}).get('MC') == '伍家岗区']}

        # ── B1. zonal 聚合：UI 生成 vs ForAI ──
        open_tool(page, 'zonal', 'zonal')
        page.wait_for_function("() => document.querySelectorAll('#zonal-boundary option').length > 1", timeout=10000)
        page.select_option('#zonal-boundary', label='行政区')
        page.click('#zonal-generate')
        page.wait_for_function("() => window.__emcTest.getLayers().some((l) => l.name === '聚合·行政区')", timeout=30000)
        ui_layer = layer_by_name(page, '聚合·行政区')
        ui_zonal = ui_of(page, ui_layer['id']) if ui_layer else None
        r_ai = page.evaluate("(args) => window.__emcTest.TOOLS ? import('./js/toolbox/zonal-tool.js').then((m) => m.generateZonalForAI(args)) : null",
                             {'layer': pts, 'boundary': admin, 'boundaryLabel': '行政区'})
        ai_zonal = ui_of(page, r_ai['layerId']) if r_ai and r_ai.get('layerId') else None
        check('B1. zonal 聚合 UI 产出 _ui（tool/mode）', bool(ui_zonal) and ui_zonal.get('tool') == 'zonal' and ui_zonal.get('mode') == 'aggregate', str(ui_zonal))
        check('B1. zonal 聚合两路径同核（layerName/_ui.tool/命名）', bool(r_ai) and r_ai.get('layerName') == '聚合·行政区' and bool(ai_zonal) and ai_zonal.get('tool') == 'zonal', str(r_ai and r_ai.get('layerName')))
        check('B1. zonal 聚合 ForAI 返 rows（C2）', bool(r_ai) and bool(r_ai.get('rows')), '')

        # ── B2. zonal 对比：UI（胶囊选 2 要素）vs ForAI ──
        click_tool(page, 'zonal')
        page.wait_for_function("() => document.querySelectorAll('#zonal-boundary option').length > 1", timeout=10000)
        page.click('#zonal-mode .buf-cap[data-mode="compare"]')
        page.select_option('#zonal-boundary', label='行政区')
        page.wait_for_function("() => document.querySelectorAll('#zonal-features .zonal-feat').length >= 2", timeout=10000)
        feats_caps = page.query_selector_all('#zonal-features .zonal-feat')
        names2 = []
        for c in feats_caps:
            nm = c.get_attribute('data-name')
            if nm in ('西陵区', '伍家岗区'):
                names2.append(nm)
        for c in feats_caps:
            if c.get_attribute('data-name') in names2:
                c.click()
        page.click('#zonal-generate')
        page.wait_for_function("() => window.__emcTest.getLayers().some((l) => l.name.startsWith('对比·'))", timeout=30000)
        ui_cmp = layer_by_name(page, '对比·西陵区·伍家岗区')
        ui_cmp_ui = ui_of(page, ui_cmp['id']) if ui_cmp else None   # 先捕获 _ui：后续 ForAI 同名去重会替换该层
        r_cmp = page.evaluate("(args) => import('./js/toolbox/zonal-tool.js').then((m) => m.generateCompareForAI(args))",
                              {'layer': pts, 'boundaries': [{'label': '西陵区', 'geo': xiling}, {'label': '伍家岗区', 'geo': wujiagang}]})
        check('B2. zonal 对比 UI 产出（对比·西陵区·伍家岗区·_ui.mode=compare）', bool(ui_cmp_ui) and ui_cmp_ui.get('mode') == 'compare', str(ui_cmp_ui))
        check('B2. zonal 对比两路径同核（layerName/okCount=2）', bool(r_cmp) and r_cmp.get('layerName') == '对比·西陵区·伍家岗区' and r_cmp.get('okCount') == 2, str(r_cmp and r_cmp.get('layerName')))

        # ── B3. area-stats：UI vs ForAI ──
        click_tool(page, 'area-stats')
        page.wait_for_function("() => document.querySelectorAll('#as-boundary option').length > 1", timeout=10000)
        page.select_option('#as-boundary', label='用地_商业')
        page.wait_for_timeout(600)
        gb = page.evaluate("() => document.querySelector('#as-group-by').value")
        if gb != 'DLMC':
            page.select_option('#as-group-by', value='DLMC')
        page.click('#as-generate')
        page.wait_for_function("() => window.__emcTest.getLayers().some((l) => l.name.startsWith('面积·用地_商业'))", timeout=30000)
        ui_as = layer_by_name(page, '面积·用地_商业·按DLMC')
        ui_as_ui = ui_of(page, ui_as['id']) if ui_as else None   # 先捕获 _ui：后续 ForAI 同名去重会替换该层
        r_as = page.evaluate("(args) => import('./js/toolbox/area-stats-tool.js').then((m) => m.generateAreaStatsForAI(args))",
                             {'boundary': commercial, 'boundaryLabel': '用地_商业', 'group_by': 'DLMC'})
        check('B3. area-stats UI 产出（面积·用地_商业·按DLMC·_ui.tool=area_stats）', bool(ui_as_ui) and ui_as_ui.get('tool') == 'area_stats', str(ui_as_ui))
        check('B3. area-stats 两路径同核 + rows（C2）', bool(r_as) and r_as.get('layerName') == '面积·用地_商业·按DLMC' and bool(r_as.get('rows')), str(r_as and r_as.get('layerName')))

        # ── B4. rank：UI vs ForAI ──
        click_tool(page, 'rank')
        page.wait_for_function("() => document.querySelectorAll('#rank-boundary option').length > 1", timeout=10000)
        page.select_option('#rank-boundary', label='行政区')
        page.click('#rank-generate')
        page.wait_for_function("() => window.__emcTest.getLayers().some((l) => l.name.startsWith('Top5·最差·'))", timeout=30000)
        ui_rk = layer_by_name(page, 'Top5·最差·行政区')
        ui_rk_ui = ui_of(page, ui_rk['id']) if ui_rk else None   # 先捕获 _ui：后续 ForAI 同名去重会替换该层
        r_rk = page.evaluate("(args) => import('./js/toolbox/rank-tool.js').then((m) => m.generateRankForAI(args))",
                             {'layer': pts, 'by': 'worst', 'top_n': 5, 'boundary': admin, 'boundaryLabel': '行政区'})
        check('B4. rank UI 产出（Top5·最差·行政区·_ui.tool=rank）', bool(ui_rk_ui) and ui_rk_ui.get('tool') == 'rank', str(ui_rk_ui))
        check('B4. rank 两路径同核 + rows（C2）', bool(r_rk) and r_rk.get('layerName') == 'Top5·最差·行政区' and bool(r_rk.get('rows')), str(r_rk and r_rk.get('layerName')))

        # ── B5. vector overlay：UI vs ForAI ──
        click_tool(page, 'vector')
        page.wait_for_function("() => document.querySelectorAll('#vec-layer-a option').length > 1", timeout=10000)
        page.select_option('#vec-layer-a', label='用地_商业')
        page.select_option('#vec-layer-b', label='行政区')
        page.click('#vec-generate')
        page.wait_for_function("() => window.__emcTest.getLayers().some((l) => l.name.startsWith('交·'))", timeout=30000)
        ui_ov = layer_by_name(page, '交·用地_商业与行政区')
        ui_ov_ui = ui_of(page, ui_ov['id']) if ui_ov else None   # 先捕获 _ui：后续 ForAI 同名去重会替换该层
        r_ov = page.evaluate("(args) => import('./js/toolbox/vector-tool.js').then((m) => m.generateOverlayForAI(args))",
                             {'layer_a': commercial, 'layer_b': admin, 'layer_a_label': '用地_商业', 'layer_b_label': '行政区', 'how': 'intersection'})
        check('B5. vector overlay UI 产出（交·用地_商业与行政区·_ui.tool=overlay）', bool(ui_ov_ui) and ui_ov_ui.get('tool') == 'overlay', str(ui_ov_ui))
        check('B5. vector overlay 两路径同核', bool(r_ov) and r_ov.get('layerName') == '交·用地_商业与行政区', str(r_ov and r_ov.get('layerName')))

        # ── B6. embedded nearest/hotspot（ForAI·无 UI）──
        r_nr = page.evaluate("(args) => import('./js/toolbox/nearest-tool.js').then((m) => m.generateNearestForAI(args))",
                             {'layer': pts, 'target': {'type': 'FeatureCollection', 'features': [boundary_fc(page, '用地_公园广场.geojson')['features'][0]]}, 'targetLabel': '公园', 'k': 2})
        check('B6. nearest ForAI 产出（连线层·_ui.tool=nearest）', bool(r_nr) and r_nr.get('layerId') and (ui_of(page, r_nr['layerId']) or {}).get('tool') == 'nearest', str(r_nr and r_nr.get('layerId')))
        r_hs = page.evaluate("(args) => import('./js/toolbox/hotspot-tool.js').then((m) => m.generateHotspotForAI(args))",
                             {'layer': pts})
        check('B6. hotspot ForAI 产出（点层·_ui.tool=hotspot + tally）', bool(r_hs) and r_hs.get('layerId') and (ui_of(page, r_hs['layerId']) or {}).get('tool') == 'hotspot' and bool(r_hs.get('tally')), str(r_hs and r_hs.get('layerId')))

        # ── C1. buffer cover：UI vs ForAI + 编辑回填（显式 kind）──
        click_tool(page, 'buffer')
        page.wait_for_timeout(400)
        cover_kind = page.evaluate("() => document.querySelector('#buf-kind .buf-cap.is-sel')?.dataset.kind")
        page.wait_for_function("() => [...document.querySelectorAll('#buf-layer option')].some((o) => o.text === '行政区')", timeout=10000)
        page.evaluate("() => { const s = document.querySelector('#buf-layer'); const opt = [...s.options].find((o) => o.text === '行政区'); if (opt) s.value = opt.value; }")
        page.click('#buf-generate')
        page.wait_for_function("() => window.__emcTest.getLayers().some((l) => (l.name || '').startsWith('缓冲 · 1000m'))", timeout=30000)
        ui_bc = page.evaluate("() => { const l = window.__emcTest.getLayers().find((x) => (x.name || '').startsWith('缓冲 · 1000m')); return l ? { id: l.id, name: l.name } : null; }")
        commercial_layer_id = page.evaluate("() => { const l = window.__emcTest.getLayers().find((x) => x.name === '用地_商业'); return l ? l.id : null; }")
        check('C1. 用地_商业 Range 层在列（cover ForAI 源）', bool(commercial_layer_id), '')
        r_bc = page.evaluate("(args) => import('./js/buffer-tool.js').then((m) => m.generateBufferForAI(args))",
                             {'kind': 'cover', 'sourceLayer': commercial_layer_id, 'distance': 800, 'dissolve': False, 'color': '#4FC3F7', 'lineWidth': 1, 'lineStyle': 'solid', 'fillOpacity': 0.15})
        check('C1. buffer cover 默认模式胶囊 = cover', cover_kind == 'cover', str(cover_kind))
        check('C1. buffer cover UI 产出 _ui.kind=cover', bool(ui_bc) and (ui_of(page, ui_bc['id']) or {}).get('kind') == 'cover', str(ui_bc))
        check('C1. buffer cover ForAI 产出 _ui.kind=cover', bool(r_bc) and r_bc.get('layerId') and (ui_of(page, r_bc['layerId']) or {}).get('kind') == 'cover', str(r_bc and r_bc.get('layerId')))

        # ── C2. buffer emotion：UI 四路（手输坐标）vs ForAI + 回填 ──
        click_tool(page, 'buffer')
        page.wait_for_timeout(300)
        page.click('#buf-kind .buf-cap[data-kind="emotion"]')
        page.click('#buf-center-mode .buf-cap[data-cmode="coord"]')
        page.fill('#buf-center-lng', '111.286')
        page.fill('#buf-center-lat', '30.701')
        page.evaluate("() => { const s = document.querySelector('#buf-emo-layer'); if (s && s.options.length) s.selectedIndex = 0; }")
        page.click('#buf-generate')
        page.wait_for_function("() => window.__emcTest.getLayers().some((l) => (l.name || '').includes('坐标(111.286,30.701)'))", timeout=30000)
        ui_be = page.evaluate("() => { const l = window.__emcTest.getLayers().find((x) => (x.name || '').includes('坐标(111.286,30.701)')); return l ? { id: l.id, name: l.name } : null; }")
        r_be = page.evaluate("(args) => import('./js/buffer-tool.js').then((m) => m.generateBufferForAI(args))",
                             {'kind': 'emotion', 'center': {'name': '坐标(111.286,30.701)', 'lng': 111.286, 'lat': 30.701}, 'radius': 500, 'layer': pts})
        check('C2. buffer emotion UI 产出 _ui.kind=emotion + 圈内聚合属性', bool(ui_be) and (ui_of(page, ui_be['id']) or {}).get('kind') == 'emotion', str(ui_be))
        check('C2. buffer emotion ForAI（point_count 入属性·aggregated）', bool(r_be) and r_be.get('layerId') and r_be.get('aggregated') and r_be.get('pointCount') is not None, str(r_be and {k: r_be.get(k) for k in ('layerId', 'aggregated', 'pointCount')} if r_be else None))
        # 编辑回填：点击 emotion 层的要素按钮 → dialog 回填 emotion 模式
        if ui_be:
            page.evaluate("(id) => { const btn = document.querySelector(`[data-feat=\"${id}\"]`); if (btn) btn.click(); }", ui_be['id'])
            page.wait_for_timeout(500)
            backfill = page.evaluate("() => document.querySelector('#buf-kind .buf-cap.is-sel')?.dataset.kind")
            check('C2. buffer emotion 编辑回填胶囊 = emotion（显式 kind）', backfill == 'emotion', str(backfill))
            page.keyboard.press('Escape')
            page.wait_for_timeout(300)

        # ── C3. 存量无 kind 产物：color 判据回填（§4.3 v2.2）──
        tiny_fc = {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'name': 't'}, 'geometry': {'type': 'Polygon', 'coordinates': [[[111.2, 30.6], [111.3, 30.6], [111.3, 30.7], [111.2, 30.7], [111.2, 30.6]]]}}]}
        legacy_cover = page.evaluate("(a) => window.__emcTest.addTestLayer('legacy-cover', 'polygon', a.fc, { color: '#4FC3F7', fillOn: true, fillOpacity: 0.15, lineWidth: 1, _ui: { tool: 'buffer', sourceLayer: 'x', distance: 300, dissolve: false, color: '#4FC3F7', lineWidth: 1, lineStyle: 'solid', fillOpacity: 0.15 } })", {'fc': tiny_fc})
        legacy_emo = page.evaluate("(a) => window.__emcTest.addTestLayer('legacy-emo', 'polygon', a.fc, { fillOn: true, fillOpacity: 0.2, lineWidth: 2, _ui: { tool: 'buffer', distance: 500, dissolve: false, lineWidth: 2, fillOpacity: 0.2, lineStyle: 'solid' } })", {'fc': tiny_fc})
        page.evaluate("(id) => { const btn = document.querySelector(`[data-feat=\"${id}\"]`); if (btn) btn.click(); }", legacy_cover)
        page.wait_for_timeout(500)
        k1 = page.evaluate("() => document.querySelector('#buf-kind .buf-cap.is-sel')?.dataset.kind")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
        page.evaluate("(id) => { const btn = document.querySelector(`[data-feat=\"${id}\"]`); if (btn) btn.click(); }", legacy_emo)
        page.wait_for_timeout(500)
        k2 = page.evaluate("() => document.querySelector('#buf-kind .buf-cap.is-sel')?.dataset.kind")
        page.keyboard.press('Escape')
        check('C3. 存量含 color → 回填 cover（color 判据）', k1 == 'cover', str(k1))
        check('C3. 存量无 color → 回填 emotion（color 判据·禁 distance/sourceLayer）', k2 == 'emotion', str(k2))

        # ── D. console 报错 ──
        check('D. 无 console 报错（allowlist 外）', not console_errs, ' | '.join(console_errs[:3]))

    print(f"\n[DONE] fails={len(FAILS)} {'ALL-PASS' if not FAILS else FAILS}")
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
