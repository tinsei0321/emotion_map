"""PT-CB6 P · render 通道测试（render_spec / layer_output / watcher / dataset 端点）。"""
import json
import os
import queue
import sys

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, Polygon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, ROOT)

import mcp_server_emc as mse
from api import render_routes


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _fake_manifest(tmp_path, items):
    reg = tmp_path / 'manifest.json'
    _write(reg, json.dumps([{'group': 'g', 'items': items}], ensure_ascii=False))
    return str(reg)


def _patch_render_globals(monkeypatch, tmp_path, manifest_items):
    monkeypatch.setattr(mse, 'MANIFEST', _fake_manifest(tmp_path, manifest_items))
    monkeypatch.setattr(mse, 'REPO', str(tmp_path))


class _FakePoints:
    def __init__(self):
        self.columns = ['score']


class _FakeBoundary:
    pass


def _fake_merged(n=5):
    return gpd.GeoDataFrame({
        'name': [f'单元{i}' for i in range(n)],
        'point_count': list(range(1, n + 1)),
        'polarity_index': [-1.0 + i * 0.4 for i in range(n)],
        'score_mean': [0.1] * n,
        'domain_top': ['治理'] * n,
        'element_top': ['设施'] * n,
        'issue_label': ['停车'] * n,
    }, geometry=[Polygon([(111.2 + i, 30.6), (111.3 + i, 30.6),
                          (111.3 + i, 30.7), (111.2 + i, 30.6)]) for i in range(n)],
       crs='EPSG:4326')


def _patch_geo(monkeypatch, merged):
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints())
    monkeypatch.setattr('core.geo_registry.resolve_boundary', lambda boundary: _FakeBoundary())
    monkeypatch.setattr('core.spatial_analysis.aggregate_by_polygons',
                        lambda points, polys, agg_cols=None, polygon_name_col=None: merged)


# ════════════ render_spec ════════════

def test_render_spec_writes_inbox_file_with_contract(monkeypatch, tmp_path):
    _patch_render_globals(monkeypatch, tmp_path, [
        {'id': 'base_18village_area', 'label': '18村', 'file': 'a.geojson',
         'nameField': 'SQMC', 'usage': 'analysis_output'},
    ])
    # PT-CB11 B3-2：render_policy 读真 manifest——同步隔离（fake 文件不存在→降级政策校验）
    monkeypatch.setattr('core.range_selector._PRESETS_MANIFEST', mse.MANIFEST)
    monkeypatch.setattr('core.geo_registry.list_point_layers', lambda: [])
    out = mse.render_spec(kind='choropleth', name='情绪最差三区',
                          dataset_id='base_18village_area', value_field='polarity_index',
                          source_tool='rank', community_caliber=174)
    assert out['ok'] is True and out['spec_id']
    fp = out['inbox_path']
    assert os.path.isfile(fp)
    spec = json.loads(open(fp, encoding='utf-8').read())
    assert spec['spec_version'] == 1
    assert spec['kind'] == 'choropleth'
    assert spec['origin']['source_tool'] == 'rank'
    assert spec['caliber_lite']['usage'] == 'analysis_output'
    assert spec['caliber_lite']['data_nature'] == 'real'
    assert spec['caliber_lite']['community'] == 174
    assert spec['style']['scheme'] == 'community_choropleth_v1'
    assert _caliber_ok(out['caliber'])


def _caliber_ok(c):
    return all(k in c for k in ('scale', 'semantics', 'limits', 'refs'))


def test_render_spec_inline_limit_and_missing_data(monkeypatch, tmp_path):
    _patch_render_globals(monkeypatch, tmp_path, [])
    fc = {'type': 'FeatureCollection',
          'features': [{'type': 'Feature', 'geometry': Point(111, 30).__geo_interface__,
                        'properties': {}} for _ in range(61)]}
    out = mse.render_spec(kind='point', name='超限', geojson=fc)
    assert out['ok'] is False and '60' in out['hint']

    out = mse.render_spec(kind='point', name='缺数据')
    assert out['ok'] is False and '二选一' in out['hint']


def test_list_data_data_nature_and_preset_passthrough(monkeypatch, tmp_path):
    _patch_render_globals(monkeypatch, tmp_path, [
        {'id': 'demo_preset', 'label': '演示面', 'file': 'a.geojson',
         'nameField': 'name', 'usage': 'input', 'data_nature': 'demo'},
    ])
    monkeypatch.setattr('core.geo_registry.list_point_layers', lambda: [
        {'id': 'yichang_l2_t1', 'label': '演示层', 'level': 'L2',
         'fields': ['score'], 'dtypes': {'score': 'float64'}, 'crs': 'EPSG:4326',
         'available': True},
        {'id': 'checkup_12345_2024', 'label': '真实 12345', 'level': 'CHECKUP',
         'fields': ['办件编号'], 'dtypes': {}, 'crs': 'EPSG:4326',
         'available': True},
    ])
    out = mse.list_data()
    by_id = {p['id']: p for p in out['point_layers']}
    assert by_id['yichang_l2_t1']['data_nature'] == 'demo'
    assert by_id['checkup_12345_2024']['data_nature'] == 'real'
    preset = next(p for p in out['presets'] if p['id'] == 'demo_preset')
    assert preset['data_nature'] == 'demo'


def test_render_spec_scheme_registry_and_inline_nature(monkeypatch, tmp_path):
    _patch_render_globals(monkeypatch, tmp_path, [])
    out = mse.render_spec(kind='choropleth', name='未知样式', geojson={
        'type': 'FeatureCollection', 'features': []}, scheme='nope')
    assert out['ok'] is False and 'scheme 未注册' in out['hint']

    fc = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'geometry': Point(111, 30).__geo_interface__, 'properties': {}}]}
    out = mse.render_spec(kind='point', name='演示点', geojson=fc, data_nature='demo')
    assert out['ok'] is True
    spec = json.loads(open(out['inbox_path'], encoding='utf-8').read())
    assert spec['style']['scheme'] == 'point_default_v1'
    assert spec['caliber_lite']['data_nature'] == 'demo'


def test_render_spec_dataset_validation(monkeypatch, tmp_path):
    _patch_render_globals(monkeypatch, tmp_path, [
        {'id': 'base_18village_area', 'label': '18村', 'file': 'a.geojson',
         'nameField': 'SQMC', 'usage': 'analysis_output'},
    ])
    # PT-CB11 B3-2：同上——隔离真 manifest（fake 文件不存在→降级政策校验）
    monkeypatch.setattr('core.range_selector._PRESETS_MANIFEST', mse.MANIFEST)
    monkeypatch.setattr('core.geo_registry.list_point_layers', lambda: [])
    out = mse.render_spec(kind='choropleth', name='未知', dataset_id='nope')
    assert out['ok'] is False and '未知 dataset_id' in out['hint']

    out = mse.render_spec(kind='choropleth', name='结论层显示',
                          dataset_id='base_18village_area', value_field='polarity_index')
    assert out['ok'] is True
    assert out['caliber']['refs'][0] == 'G-2(显示徽标)'


# ════════════ zonal / rank layer_output ════════════

def test_zonal_layer_output_geojson_topn_and_default_no_key(monkeypatch):
    _patch_geo(monkeypatch, _fake_merged(5))
    out = mse.zonal_stats('admin_district', top_n=3, layer_output=True)
    assert out['geojson']['type'] == 'FeatureCollection'
    assert len(out['geojson']['features']) == 3
    assert 'value' in out['geojson']['features'][0]['properties']

    out_off = mse.zonal_stats('admin_district', top_n=3)
    assert 'geojson' not in out_off


def test_rank_layer_output_geojson_topn(monkeypatch):
    _patch_geo(monkeypatch, _fake_merged(5))
    out = mse.rank(boundary='admin_district', top_n=2, layer_output=True)
    assert len(out['geojson']['features']) == 2
    assert len(out['rows']) == 2


# ════════════ watcher ════════════

def test_watcher_scan_order_and_bad_json_skip(tmp_path):
    inbox = tmp_path / 'inbox'
    _write(inbox / '01.json', json.dumps(
        {'spec_version': 1, 'kind': 'point', 'origin': {'producer': 'dsh', 'source_tool': 'manual'}}))
    _write(inbox / '02.json', '{bad json')
    _write(inbox / '03.json', json.dumps(
        {'spec_version': 1, 'kind': 'choropleth', 'origin': {'producer': 'dsh', 'source_tool': 'rank'}}))

    seen = set()
    q = queue.Queue()
    backlog = []
    pushed = render_routes.scan_inbox(str(inbox), seen, q, backlog)
    assert pushed == 2
    assert q.get()['kind'] == 'point'
    assert q.get()['kind'] == 'choropleth'
    assert len(backlog) == 2


def test_scan_inbox_archives_applied_no_replay_on_restart(tmp_path):
    """PT-CB7 T16：推送成功的 spec 归档 applied/——serve 重启（seen 清零）不重放历史层。"""
    inbox = tmp_path / 'inbox'
    _write(inbox / '01.json', json.dumps(
        {'spec_version': 1, 'kind': 'point', 'origin': {'producer': 'dsh'}}))
    _write(inbox / '02.json', json.dumps(
        {'spec_version': 1, 'kind': 'choropleth', 'origin': {'producer': 'dsh'}}))

    q = queue.Queue()
    assert render_routes.scan_inbox(str(inbox), set(), q, []) == 2
    # 归档：一级目录清空，applied/ 留痕
    assert sorted(p.name for p in inbox.glob('*.json')) == []
    assert sorted(p.name for p in (inbox / 'applied').glob('*.json')) == ['01.json', '02.json']
    # 重启模拟：全新 seen 集合，无重放
    assert render_routes.scan_inbox(str(inbox), set(), queue.Queue(), []) == 0


def test_sse_fanout_broadcasts_to_all_connections():
    """PT-CB7 T21：多个地图页（SSE 连接）都能收到同一 spec（治单队列争用·F5 才见）。"""
    render_routes._SUBSCRIBERS.clear()
    q1, q2 = queue.Queue(), queue.Queue()
    with render_routes._SUB_LOCK:
        render_routes._SUBSCRIBERS.extend([q1, q2])
    spec = {'spec_version': 1, 'kind': 'point', 'spec_id': 'fanout-x',
            'origin': {'producer': 'dsh'}}
    render_routes._publish(spec)
    assert q1.get_nowait()['spec_id'] == 'fanout-x'
    assert q2.get_nowait()['spec_id'] == 'fanout-x'
    # 断开连接（finally 摘除）后不再收到广播
    with render_routes._SUB_LOCK:
        render_routes._SUBSCRIBERS.remove(q1)
    render_routes._publish({'spec_version': 1, 'kind': 'point',
                            'spec_id': 'fanout-y', 'origin': {'producer': 'dsh'}})
    assert q1.empty()
    assert q2.get_nowait()['spec_id'] == 'fanout-y'
    render_routes._SUBSCRIBERS.clear()


# ════════════ dataset 端点 ════════════

def test_render_dataset_preset_returns_fc(monkeypatch):
    gdf = gpd.GeoDataFrame({'name': ['a']}, geometry=[Point(111, 30)], crs='EPSG:4326')
    monkeypatch.setattr('core.geo_registry.list_boundaries', lambda: [{'id': 'admin_district'}])
    monkeypatch.setattr('core.geo_registry.resolve_boundary', lambda bid: gdf)
    out = render_routes.render_dataset('admin_district')
    assert out['ok'] is True
    assert out['geojson']['type'] == 'FeatureCollection'
    assert out['geojson']['features'][0]['properties']['name'] == 'a'


def test_render_dataset_unknown_returns_hint(monkeypatch):
    monkeypatch.setattr('core.geo_registry.list_boundaries', lambda: [])
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda lid: (_ for _ in ()).throw(KeyError('x')))
    out = render_routes.render_dataset('nope')
    assert out['ok'] is False
    assert 'list_data' in out['hint']


# ════════════ PT-CB7 T1 · [dsh] 图层残留自清理（前端静态契约断言） ════════════
# M2（主执行前审计）：图层列表属 JS 运行时态，pytest 面不可驱动；
# 本用例断言 render_client.js 的清理契约结构，运行时实测移交浏览器实测清单。

def test_render_client_clears_dsh_layers_before_apply():
    with open(os.path.join(ROOT, 'frontend', 'js', 'render_client.js'), encoding='utf-8') as fh:
        src = fh.read()
    # ① 图层管理真身 import 在位（state.js/map.js 直 import·shared.js 未转出）
    assert 'removeLayer' in src and 'removeLayerFromMap' in src and 'getLayers' in src
    # ② 清理函数存在：按 [dsh] 前缀遍历移除 + try/catch 包裹 + warn 不阻塞（A9）
    assert '_clearDshLayers' in src
    assert 'startsWith(PREFIX)' in src
    assert 'console.warn' in src
    # ③ 顺序契约：清理调用必须位于 _apply 体内、首个 addToolboxLayer 之前
    i_apply = src.index('async function _apply(spec)')
    i_clear = src.index('_clearDshLayers();', i_apply)
    i_add = src.index('addToolboxLayer(', i_apply)
    assert i_apply < i_clear < i_add


# ════════════ PT-CB11 B3-1/B3-2 · 渲染通道字段政策 + value_field 服务端校验 ════════════

def test_render_policy_preset_render_fields_manifest():
    """B3-1：manifest 声明字段（nameField 自动 + renderFields 显式）能查到。"""
    from core import render_policy as rp
    fields = rp.preset_render_fields('page7_12345_top20')
    assert '社区' in fields             # nameField 自动放行
    assert '诉求总量' in fields         # renderFields 显式声明
    assert rp.field_allowed('诉求总量', 'page7_12345_top20')
    assert not rp.field_allowed('办件编号', 'page7_12345_top20')   # 准标识字段默认拒
    assert rp.preset_render_fields('___nope___') == set()


def test_render_policy_dataset_field_names_reads_file():
    """B3-2 地面真相：preset 文件首要素属性 = 实际字段（top20 无 point_count·有中文指标）。"""
    from core import render_policy as rp
    actual = rp.dataset_field_names('page7_12345_top20')
    assert actual is not None
    assert '诉求总量' in actual and 'point_count' not in actual
    assert rp.dataset_field_names('___nope___') is None


def test_filter_dataset_props_extra_keys_and_quasi_id_dropped():
    fc = {'features': [{'properties': {'社区': '甲', '诉求总量': 12,
                                       '办件编号': 'X1', 'point_count': 3}}]}
    dropped = render_routes._filter_dataset_props(fc, extra_keys={'诉求总量'})
    assert fc['features'][0]['properties'] == {'社区': '甲', '诉求总量': 12, 'point_count': 3}
    assert dropped == {'办件编号'}


def test_render_dataset_endpoint_passes_preset_render_fields(monkeypatch):
    """B3-1 端点集成：preset 声明的中文指标字段随 dataset 响应透传·准标识仍剔除。"""
    gdf = gpd.GeoDataFrame(
        {'社区': ['甲'], '诉求总量': [12], '办件编号': ['X1']},
        geometry=[Polygon([(111.2, 30.6), (111.3, 30.6), (111.3, 30.7), (111.2, 30.6)])],
        crs='EPSG:4326')
    monkeypatch.setattr('core.geo_registry.list_boundaries',
                        lambda: [{'id': 'page7_12345_top20'}])
    monkeypatch.setattr('core.geo_registry.resolve_boundary', lambda bid: gdf)
    out = render_routes.render_dataset('page7_12345_top20')
    assert out['ok'] is True
    props = out['geojson']['features'][0]['properties']
    assert props['诉求总量'] == 12 and props['社区'] == '甲'
    assert '办件编号' not in props


def test_render_spec_value_field_validation(monkeypatch, tmp_path):
    """B3-2 三类语义化拒绝（dataset 错配/policy 剔除/inline 缺字段）+ 正确字段放行。"""
    gdir = tmp_path / 'presets'
    gdir.mkdir()
    fc = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature',
         'geometry': {'type': 'Polygon',
                      'coordinates': [[[111.2, 30.6], [111.25, 30.6],
                                       [111.25, 30.65], [111.2, 30.6]]]},
         'properties': {'社区': f'c{i}', '诉求总量': i + 1, '内部编号': f'N{i}'}}
        for i in range(3)]}
    (gdir / 'b3.geojson').write_text(json.dumps(fc, ensure_ascii=False), encoding='utf-8')
    items = [{'id': 'b3_preset', 'label': 'B3', 'file': 'b3.geojson',
              'nameField': '社区', 'renderFields': ['诉求总量'],
              'usage': 'analysis_output'}]
    fake_manifest = _fake_manifest(tmp_path, items)
    monkeypatch.setattr(mse, 'MANIFEST', fake_manifest)
    monkeypatch.setattr(mse, 'REPO', str(tmp_path))
    monkeypatch.setattr('core.range_selector._PRESETS_MANIFEST', fake_manifest)
    monkeypatch.setattr('core.range_selector._PRESETS_DIR', str(gdir))
    monkeypatch.setattr('core.geo_registry.list_point_layers', lambda: [])

    # ① dataset 错配：point_count 不在实际字段 → 拒绝并提示可用字段（宿主自纠）
    out = mse.render_spec(kind='choropleth', name='错配', dataset_id='b3_preset',
                          value_field='point_count')
    assert out['ok'] is False
    assert '不在 dataset' in out['hint'] and '诉求总量' in out['hint']

    # ② policy 剔除：字段在实际文件里但未被声明 → 拒绝（前端收不到=全零透明）
    out = mse.render_spec(kind='choropleth', name='未声明', dataset_id='b3_preset',
                          value_field='内部编号')
    assert out['ok'] is False and '字段政策' in out['hint']

    # ③ inline 缺字段：要素属性并集里没有 → 拒绝
    fc2 = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'geometry': {'type': 'Polygon',
                                         'coordinates': [[[111.2, 30.6], [111.25, 30.6],
                                                          [111.25, 30.65], [111.2, 30.6]]]},
         'properties': {'社区': 'x', 'point_count': 5}}]}
    out = mse.render_spec(kind='choropleth', name='inline 错', geojson=fc2,
                          value_field='nope')
    assert out['ok'] is False and 'geojson 要素属性' in out['hint']

    # ④ 正确字段放行（dataset 声明字段 / inline 存在字段）
    out = mse.render_spec(kind='choropleth', name='对', dataset_id='b3_preset',
                          value_field='诉求总量')
    assert out['ok'] is True
    out = mse.render_spec(kind='choropleth', name='inline 对', geojson=fc2,
                          value_field='point_count')
    assert out['ok'] is True


# ════════════ PT-CB11 A-4 · /version 版本徽章端点 ════════════

def test_version_endpoint_returns_commit_branch_startup():
    """A-4a：/version 含 commit/branch/startup 三字段；启动时缓存（两次调用同一对象·不每请求跑 git）。"""
    from datetime import datetime
    out = render_routes.version()
    assert {'commit', 'branch', 'startup'} <= set(out)
    assert out['commit'] and len(out['commit']) >= 7   # 仓内运行·git 可用
    assert out['branch']
    datetime.fromisoformat(out['startup'])             # ISO 时间可解析
    assert render_routes.version() is out              # 缓存契约：同一 dict·不重复 subprocess


def test_render_policy_prefix_wildcard_retired():
    """P2-2 收紧：前缀通配退役——未知 poi_*/place_* 后缀字段默认拒绝（显式枚举才放行）。"""
    from core import render_policy as rp
    assert not rp.field_allowed('poi_private_note', '')
    assert not rp.field_allowed('place_internal_id', '')
    assert not rp.field_allowed('domain_raw_dump', '')
    assert rp.field_allowed('score_sum', '')          # 聚合衍生列入枚举
    assert rp.field_allowed('polarity_score_5', '')   # 体检轨字段入枚举
