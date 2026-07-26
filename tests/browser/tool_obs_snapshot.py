"""tool_obs_snapshot.py — 12 GIS 工具 observation 快照（手册 v2.2 步 7 前置·修订 6/E-③）。

用法：
  py tests/browser/tool_obs_snapshot.py --save    采集基线 → tests/reports/toolbox-obs-baseline.json
  py tests/browser/tool_obs_snapshot.py --diff    与基线比对（observation 逐字 + data 稳定字段），任一不等退出码 1

说明：固定入参直调 window.__emcTest.TOOLS.xxx（绕 LLM 流水线，确定性）；
点层 = loadCSV(yichang_L2_T1) 首个可见 l2-* 子层 fc（send-in·现状 resolvePointLayer 显式 layer 路径）；
边界 = DATA/boundaries send-in GeoJSON（presets 目录为空·preset 路径在本机不可用，两径同一入参故 diff 有效）。
data 剔除 layerId（易变）；余字段全量比对（json sort_keys）。
"""
import json
import os
import sys

from lib.emc_helpers import emc_session

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, 'tests', 'reports', 'toolbox-obs-baseline.json')

SNAPSHOT_JS = r"""
async () => {
  const T = window.__emcTest.TOOLS;
  const gj = async (n) => fetch('/DATA/boundaries/' + n).then((r) => r.json());
  const [admin, commercial, park] = await Promise.all([gj('行政区.geojson'), gj('用地_商业.geojson'), gj('用地_公园广场.geojson')]);
  const one = (fc, pred) => ({ type: 'FeatureCollection', features: fc.features.filter(pred) });
  const xiling = one(admin, (f) => (f.properties || {}).MC === '西陵区');
  const wujiagang = one(admin, (f) => (f.properties || {}).MC === '伍家岗区');
  const ptL = window.__emcTest.getLayers().find((l) => l.kind === 'point' && l.visible !== false && l.colorMode && String(l.colorMode).startsWith('l2-'));
  const ptFc = ptL ? ptL.fc : null;
  const centerPt = { type: 'FeatureCollection', features: [{ type: 'Feature', properties: { name: '滨江公园' }, geometry: { type: 'Point', coordinates: [111.286, 30.701] } }] };
  const cases = [
    ['nearest', { layer: ptFc, target: one(park, (f, i) => i === 0), k: 2 }],
    ['hotspot', { layer: ptFc }],
    ['rank', { layer: ptFc, boundary: admin, top_n: 3 }],
    ['area_stats', { boundary: commercial, group_by: 'DLMC' }],
    ['merge', { boundary: commercial }],
    ['clip', { layer: ptFc, range: xiling }],
    ['filter_attr', { layer: ptFc, pre_filter: { field: 'polarity', op: 'eq', value: 'Positive' } }],
    ['extract_feature', { layer: admin, where: { field: 'name', op: 'eq', value: '西陵区' } }],   // send-in FC 经后端 nameField 推断改 name 列（MC→name），过滤须用改名后字段
    ['overlay', { layer_a: commercial, layer_b: xiling, how: 'intersection' }],
    ['zonal_stats', { layer: ptFc, boundary: admin }],
    ['compare_regions', { layer: ptFc, boundaries: [xiling, wujiagang] }],
    ['buffer', { center: centerPt, radius_m: 500, layer: ptFc }],
  ];
  const out = {};
  window.__emcTest.resetToolState();
  for (const [tool, params] of cases) {
    try {
      const r = await T[tool](params);
      const data = { ...(r.data || {}) };
      delete data.layerId;
      out[tool] = { observation: r.observation, data };
    } catch (e) {
      out[tool] = { observation: '[THROW] ' + String((e && e.message) || e), data: null };
    }
  }
  return out;
}
"""


def run_snapshot(page):
    r = page.evaluate("() => window.__emcTest.loadCSV('yichang_L2_T1_L2_result_csv.csv')")
    if not (r and r.get('ok')):
        raise AssertionError(f'loadCSV 失败: {r}')
    page.wait_for_function(
        "() => /积极|消极|中性/.test(document.querySelector('#left-panel')?.innerText || '')",
        timeout=15000)
    page.wait_for_timeout(800)
    return page.evaluate(SNAPSHOT_JS)


def main():
    sys.stdout.reconfigure(encoding='utf-8')   # observation 含 km² 等字符，GBK 控制台直打会炸
    mode = sys.argv[1] if len(sys.argv) > 1 else '--save'
    with emc_session() as page:
        snap = run_snapshot(page)
    if mode == '--save':
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, 'w', encoding='utf-8') as f:
            json.dump(snap, f, ensure_ascii=False, indent=1)
        print(f'[OK] baseline saved: {OUT}（{len(snap)} 工具）')
        for tool, v in snap.items():
            obs = (v.get('observation') or '').replace('\n', ' | ')[:100]
            print(f'  {tool}: {obs}')
        return 0
    with open(OUT, encoding='utf-8') as f:
        base = json.load(f)
    bad = 0
    for tool, cur in snap.items():
        exp = base.get(tool)
        ok_obs = bool(exp) and exp.get('observation') == cur.get('observation')
        ok_data = bool(exp) and json.dumps(exp.get('data'), sort_keys=True, ensure_ascii=False) == \
            json.dumps(cur.get('data'), sort_keys=True, ensure_ascii=False)
        if ok_obs and ok_data:
            print(f'[OK] {tool}')
        else:
            bad += 1
            print(f'[DIFF] {tool}: observation={"SAME" if ok_obs else "DIFF"} data={"SAME" if ok_data else "DIFF"}')
            if exp and not ok_obs:
                print('  exp:', (exp.get('observation') or '')[:220].replace('\n', ' | '))
                print('  cur:', (cur.get('observation') or '')[:220].replace('\n', ' | '))
    print(f'[DONE] {bad}/{len(snap)} 工具不一致')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
