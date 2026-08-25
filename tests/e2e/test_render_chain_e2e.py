# -*- coding: utf-8 -*-
"""PT-CB16 C1 · E2E 渲染链路测试骨架（分析→落盘→投递→watcher→dataset 端点）。

分层（R8 纪律·验证忌与实现同构）：
  A 级（HTTP 层·fastapi TestClient）：真实路由进出，不函数直调 dataset 端点；
  B 级（真实数据·integration 标记）：真实 193 层 + 真实点层跑黄金问题，
    断言口径/要素数/顶点保真率 100%（坐标子集比对·PT-CB15 验证方法论固化）。

浏览器级（hello 协议 + 刷新无复活）见 tests/browser/ptcb16_render_e2e.py（隔离栈手跑）。

跑法：py -m pytest tests/e2e/ -q（B 级需真实数据与 geopandas·约 20-40s 冷启动）
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, ROOT)

import mcp_server_emc as mse  # noqa: E402
from api import render_routes  # noqa: E402


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _fake_manifest(tmp_path, items):
    reg = tmp_path / 'manifest.json'
    _write(reg, json.dumps([{'group': 'g', 'items': items}], ensure_ascii=False))
    return str(reg)


def _patch_chain(monkeypatch, tmp_path, manifest_items):
    """全链隔离：tmp manifest（mse+render_policy+range_selector 三侧）+ tmp REPO + tmp 落盘目录。"""
    monkeypatch.setattr(mse, 'MANIFEST', _fake_manifest(tmp_path, manifest_items))
    monkeypatch.setattr(mse, 'REPO', str(tmp_path))
    monkeypatch.setattr(mse, 'TMP_RENDER_DIR', str(tmp_path / 'tmp_render'))
    monkeypatch.setattr('core.range_selector._PRESETS_MANIFEST', mse.MANIFEST)
    # _PRESETS_DIR 决定 resolve 的文件根——tmp_render 登记的 rel 路径以 tmp manifest 所在目录为基准
    monkeypatch.setattr('core.range_selector._PRESETS_DIR', str(tmp_path))
    monkeypatch.setattr('core.geo_registry.list_point_layers', lambda: [])


class _FakePoints:
    def __init__(self):
        self.columns = ['score']


class _FakeBoundary:
    pass


def _fake_merged(n=5):
    import geopandas as gpd
    from shapely.geometry import Polygon
    return gpd.GeoDataFrame({
        'name': [f'单元{i}' for i in range(n)],
        'point_count': list(range(1, n + 1)),
        'polarity_index': [-1.0 + i * 0.4 for i in range(n)],
    }, geometry=[Polygon([(111.2 + i, 30.6), (111.3 + i, 30.6),
                          (111.3 + i, 30.7), (111.2 + i, 30.6)]) for i in range(n)],
       crs='EPSG:4326')


# ════════════ A 级 · HTTP 链路（mock 数据·真实路由） ════════════

def test_chain_analysis_to_dataset_endpoint_http(monkeypatch, tmp_path):
    """zonal(layer_output)→render_spec(dataset_id)→scan_inbox 消费→HTTP dataset 端点取数（政策过滤后）。"""
    fastapi = pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient

    _patch_chain(monkeypatch, tmp_path, [])
    import core.geo_registry as _gr
    _orig_resolve_boundary = _gr.resolve_boundary   # 端点步需真实解析落盘文件·mock 只罩分析步
    merged = _fake_merged(5)
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints())
    monkeypatch.setattr('core.geo_registry.resolve_boundary', lambda boundary: _FakeBoundary())
    monkeypatch.setattr('core.spatial_analysis.aggregate_by_polygons',
                        lambda points, polys, agg_cols=None, polygon_name_col=None: merged)

    # ① 分析 → render_dataset_id
    out = mse.zonal_stats('admin_district', top_n=3, layer_output=True)
    ds = out.get('render_dataset_id')
    assert ds and 'geojson' not in out

    # ② 投递 → inbox spec 落盘（隔离 REPO 下）
    spec = mse.render_spec(kind='choropleth', name='链测TOP3', dataset_id=ds,
                           value_field='point_count', source_tool='zonal_stats')
    assert spec['ok'] is True
    inbox = tmp_path / 'DATA' / 'Export' / 'exports' / 'render_inbox'
    specs = list(inbox.glob('*.json'))
    assert len(specs) == 1

    # ③ watcher 消费（scan_inbox 真实函数·文件层）
    import queue
    q = queue.Queue()
    pushed = render_routes.scan_inbox(str(inbox), set(), q, [])
    assert pushed == 1 and (inbox / 'applied' / specs[0].name).exists()

    # ④ HTTP 层取数（TestClient·真实路由·真实 resolve——R8：验证层与被验实现不同构）
    monkeypatch.setattr('core.geo_registry.resolve_boundary', _orig_resolve_boundary)
    app = fastapi.FastAPI()
    app.include_router(render_routes.router, prefix='/api/v1')
    client = TestClient(app)
    r = client.get(f'/api/v1/render/dataset/{ds}')
    assert r.status_code == 200
    body = r.json()
    assert body['ok'] is True and body['count'] == 3
    props = body['geojson']['features'][0]['properties']
    assert 'point_count' in props and 'value' in props, 'renderFields 声明字段应透传'


def test_chain_inline_thinned_warns_but_renders(monkeypatch, tmp_path):
    """内联抽稀档：软警告在场且不阻断（K4 链路验证）。"""
    _patch_chain(monkeypatch, tmp_path, [])
    thin = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature',
         'geometry': {'type': 'Polygon',
                      'coordinates': [[[111.2, 30.6], [111.3, 30.6], [111.3, 30.7], [111.2, 30.6]]]},
         'properties': {'name': 'x', 'point_count': 5}}]}
    out = mse.render_spec(kind='choropleth', name='抽稀链测', geojson=thin,
                          value_field='point_count')
    assert out['ok'] is True
    assert '疑似被压缩' in (out.get('caliber_lite') or {}).get('note', '')


# ════════════ B 级 · 黄金问题（真实数据·integration） ════════════
# 注意：测的是「正确工具链的产物」（口径/要素数/顶点保真），不测模型选择行为。
# 黄金问题①「12345 诉求最多 7 个社区」：期望 7 要素·口径文本无「两个方面」·顶点 100% 保真。


def _ring_coords(feature):
    out = set()

    def walk(c):
        if isinstance(c[0], (int, float)):
            out.add((round(c[0], 6), round(c[1], 6)))
            return
        for x in c:
            walk(x)
    walk(feature.get('geometry', {}).get('coordinates', []))
    return out


@pytest.mark.integration
def test_golden_top7_real_data_fidelity(tmp_path, monkeypatch):
    """黄金问题①：193 真实边界 + 真实点层 → TOP7 图层顶点 100% 源顶点子集（保真）。"""
    pytest.importorskip('geopandas')
    # 真实 manifest 复制到 tmp（防登记写污染真仓）——各条目 file 改绝对路径
    #（原相对路径以真 manifest 目录为基准·复制到 tmp 后会断·Windows join 遇绝对路径直取后者）
    real_dir = os.path.join(ROOT, 'DATA', 'REGISTRY', 'presets')
    real_manifest = os.path.join(real_dir, 'manifest.json')
    groups = json.load(open(real_manifest, encoding='utf-8'))
    for g in groups:
        for it in g.get('items', []):
            f = it.get('file')
            if f and not os.path.isabs(f):
                it['file'] = os.path.normpath(os.path.join(real_dir, f))
    tmp_manifest = tmp_path / 'manifest.json'
    tmp_manifest.write_text(json.dumps(groups, ensure_ascii=False, indent=2), encoding='utf-8')
    monkeypatch.setattr(mse, 'MANIFEST', str(tmp_manifest))
    monkeypatch.setattr(mse, 'TMP_RENDER_DIR', str(tmp_path / 'tmp_render'))
    monkeypatch.setattr('core.range_selector._PRESETS_MANIFEST', str(tmp_manifest))
    monkeypatch.setattr('core.range_selector._PRESETS_DIR', str(tmp_path))

    out = mse.zonal_stats(boundary='base_community_area',
                          layer='subj_12345_safety_community_point',
                          top_n=7, layer_output=True, sort_by='point_count')
    ds = out.get('render_dataset_id')
    assert ds, f'落盘失败: {out.get("render_hint")}'

    from core.geo_registry import resolve_boundary
    g = resolve_boundary(ds)
    assert len(g) == 7, 'TOP7 应 7 要素'
    # 保真比对：落盘文件顶点 ⊆ 193 权威源顶点
    files = list((tmp_path / 'tmp_render').glob('zonal_stats-*.geojson'))
    assert len(files) == 1
    out_fc = json.loads(files[0].read_text(encoding='utf-8'))
    src = json.load(open(os.path.join(ROOT, 'DATA', 'AUTHORITY', 'boundaries_社区村_193.geojson'),
                         encoding='utf-8'))
    src_pool = set()
    for f in src['features']:
        src_pool |= _ring_coords(f)
    total, hit = 0, 0
    for f in out_fc['features']:
        for pt in _ring_coords(f):
            total += 1
            if pt in src_pool:
                hit += 1
    assert total > 0 and hit == total, f'顶点保真率应 100%（{hit}/{total}）——转录抽稀回归'
    # 平均顶点数下限（源 66-1066·防「保真但只剩几点」的新型抽稀）
    avg = total / len(out_fc['features'])
    assert avg >= 30, f'面均顶点 {avg:.0f} 过低——保真率之外的量级防线'
