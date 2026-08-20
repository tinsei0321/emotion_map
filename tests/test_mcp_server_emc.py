"""PT-CB5 T3 · MCP 七件标准插座测试（直接调用函数·不起 stdio）。

覆盖：
1. F_021-F_027 全部注册（F_023 为 kb_facts 预留·真实签名不符待主手裁决）；
2. 每工具 happy path 返回 caliber 四键；
3. list_data：不含样例原值、analysis_output 带 usage 标记、demo 默认不列；
4. rag_query：k 夹取、索引未构建 ok=False 不抛、synthesize deferred_v2；
5. zonal/rank：rows ≤ 20、row_count ≥ len(rows)；
6. outlet_card：空入参 cards=[] 不崩；
7. buffer：小几何返回 buffer_fc、大几何 fc_omitted；
8. 未知层 id 返回语义化 hint。
"""
import json
import os
import sys

import pandas as pd
import pytest
from shapely.geometry import Point, Polygon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import mcp_server_emc as mse


def _caliber_keys(caliber):
    return all(k in caliber for k in ('scale', 'semantics', 'limits', 'refs'))


class _FakePoints:
    def __init__(self, inside=2, outside=0):
        self.columns = ['score']
        self.geometry = (
            [Point(111.30 + i * 0.001, 30.70 + i * 0.001) for i in range(inside)]
            + [Point(111.9, 30.9) for _ in range(outside)]
        )


class _FakeBoundary:
    def __init__(self):
        self.__geo_interface__ = {'type': 'FeatureCollection', 'features': []}


def _fake_merged(n=25):
    return pd.DataFrame({
        'name': [f'单元{i}' for i in range(n)],
        'point_count': list(range(1, n + 1)),
        'polarity_index': [-1.0 + i * 0.05 for i in range(n)],
        'score_mean': [0.1] * n,
        'domain_top': ['治理'] * n,
        'element_top': ['设施'] * n,
        'issue_label': ['停车'] * n,
    })


def _small_buffer_fc(features=1):
    poly = Polygon([(111.29, 30.69), (111.32, 30.69), (111.32, 30.72), (111.29, 30.72), (111.29, 30.69)])
    return {'type': 'FeatureCollection',
            'features': [{'type': 'Feature', 'geometry': poly.__geo_interface__,
                          'properties': {}} for _ in range(features)]}


# ════════════ 追踪注册 ════════════

def test_track_ids_f021_to_f027_registered():
    from core.tracker import _TRACKING_REGISTRY
    for n in range(21, 28):
        assert f'MOD_AIQA.F_{n:03d}' in _TRACKING_REGISTRY, f'F_{n:03d} 未注册'


# ════════════ list_data ════════════

def test_list_data_available_set_hides_samples_and_usage(monkeypatch):
    """F1：点层=available（resolve 可解析）集，不再按 level 过滤；仍不含样例值。"""
    fake = [
        {'id': 'yichang_l2_t1', 'label': '演示层', 'level': 'L2',
         'fields': ['score'], 'samples': {'score': '9.9'},
         'dtypes': {'score': 'float64'}, 'crs': 'EPSG:4326',
         'available': True},
        {'id': 'checkup_12345_2024', 'label': '真实 12345', 'level': 'CHECKUP',
         'fields': ['办件编号'], 'samples': {'办件编号': '0000'},
         'dtypes': {'办件编号': 'object'}, 'crs': 'EPSG:4326',
         'available': True},
        {'id': 'missing_layer', 'label': '缺文件层', 'level': 'L2',
         'fields': [], 'dtypes': {}, 'crs': 'EPSG:4326',
         'available': False},
    ]
    monkeypatch.setattr('core.geo_registry.list_point_layers', lambda: fake)

    out = mse.list_data()
    assert [p['id'] for p in out['point_layers']] == ['yichang_l2_t1', 'checkup_12345_2024']
    assert all('samples' not in p for p in out['point_layers'])
    assert all(p['usage'] == 'input' for p in out['point_layers'])
    assert _caliber_keys(out['caliber'])
    assert any(p['usage'] == 'analysis_output' for p in out['presets'])

    out_demo = mse.list_data(include_demo=True)
    assert [p['id'] for p in out_demo['point_layers']] == ['yichang_l2_t1', 'checkup_12345_2024']


def test_list_data_real_registry_includes_yichang_l2_t1():
    """F1 回归：真实注册表清单必须含 yichang_l2_t1 等 resolve 可解析层。"""
    from core.geo_registry import list_point_layers
    expected = {p['id'] for p in list_point_layers() if p.get('available')}

    out = mse.list_data()
    assert 'yichang_l2_t1' in {p['id'] for p in out['point_layers']}
    assert {p['id'] for p in out['point_layers']} == expected


def test_list_data_render_section_contract():
    """PT-CB7 T10: list_data must carry the render capability section (schemes/paradigm/tip fields/limits)."""
    out = mse.list_data()
    r = out['render']
    assert set(r['schemes']) == {'community_choropleth_v1', 'point_default_v1', 'boundary_fill_v1'}
    assert 'dataset_id' in r['paradigm'] and 'render-contract' in r['paradigm']
    assert r['tip_required_fields'] == ['name']
    assert r['limits'] == {'inline_features_max': 60, 'zonal_top_n_max': 20}


def test_render_scheme_vocabulary_and_contract_pointer():
    """PT-CB7 T10: MCP scheme vocabulary includes boundary_fill_v1 (aligned with render_client);
    render_spec/list_data docstrings point to the render contract doc."""
    assert 'boundary_fill_v1' in mse.SCHEMES
    assert 'render-contract' in (mse.render_spec.__doc__ or '')
    assert 'render-contract' in (mse.list_data.__doc__ or '')


# ════ PT-CB7 T18: render_file ════

def _fc_points(n):
    return {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [111.2 + i * 0.001, 30.6]},
         'properties': {'name': f'p{i}', 'point_count': i + 1}} for i in range(n)]}


def _fc_polys(n):
    return {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature',
         'geometry': {'type': 'Polygon', 'coordinates': [
             [[111.2 + i * 0.01, 30.6], [111.21 + i * 0.01, 30.6],
              [111.21 + i * 0.01, 30.61], [111.2 + i * 0.01, 30.6]]]},
         'properties': {'name': f'u{i}', 'point_count': i + 1}} for i in range(n)]}


def test_render_file_small_inline(monkeypatch, tmp_path):
    """≤60 要素走内联：spec 落收件箱，mode=inline。"""
    monkeypatch.setattr(mse, 'REPO', str(tmp_path))
    src = tmp_path / 'DATA' / 'out'
    src.mkdir(parents=True)
    f = src / 'my_layer.geojson'
    f.write_text(json.dumps(_fc_points(3)), encoding='utf-8')

    out = mse.render_file(file='DATA/out/my_layer.geojson')
    assert out['ok'] is True and out['mode'] == 'inline'
    inbox = tmp_path / 'DATA' / 'exports' / 'render_inbox'
    assert len(list(inbox.glob('*.json'))) == 1


def test_render_file_large_auto_register_and_reuse(monkeypatch, tmp_path):
    """>60 要素自动登记临时 dataset（同源复用 id）→ dataset_id 引用。"""
    monkeypatch.setattr(mse, 'REPO', str(tmp_path))
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps([{'group': 'g', 'items': []}], ensure_ascii=False), encoding='utf-8')
    monkeypatch.setattr(mse, 'MANIFEST', str(manifest))
    src = tmp_path / 'DATA'
    src.mkdir(parents=True)
    f = src / 'big.geojson'
    f.write_text(json.dumps(_fc_polys(70)), encoding='utf-8')

    out1 = mse.render_file(file='DATA/big.geojson')
    assert out1['ok'] is True and out1['mode'] == 'dataset'
    ds_id = out1['dataset_id']
    assert ds_id.startswith('tmp_render_')
    groups = json.loads(manifest.read_text(encoding='utf-8'))
    tmp_group = next(g for g in groups if g['group'] == mse.TMP_RENDER_GROUP)
    assert len(tmp_group['items']) == 1 and tmp_group['items'][0]['usage'] == 'analysis_output'

    out2 = mse.render_file(file='DATA/big.geojson')
    assert out2['ok'] is True and out2['dataset_id'] == ds_id
    groups = json.loads(manifest.read_text(encoding='utf-8'))
    tmp_group = next(g for g in groups if g['group'] == mse.TMP_RENDER_GROUP)
    assert len(tmp_group['items']) == 1  # 同源复用，不重复登记


def test_render_file_path_whitelist(monkeypatch, tmp_path):
    """路径白名单：仓外绝对路径拒绝（防穿越）。"""
    monkeypatch.setattr(mse, 'REPO', str(tmp_path))
    outside = tmp_path.parent / 'outside.geojson'
    out = mse.render_file(file=str(outside))
    assert out['ok'] is False and '白名单' in out['hint']


# ════════════ rag_query ════════════

def test_rag_query_clamp_dim_counts_and_deferred_synthesize(monkeypatch):
    captured = {}

    def fake_search(query, k):
        captured['k'] = k
        return {'ok': True, 'count': 1,
                'results': [{'score': 0.9, 'source': 's.md', 'type': 'fact',
                             'data_dim': '社区', 'text': '素材文本'}]}

    monkeypatch.setattr('tools.rag_index.search', fake_search)
    out = mse.rag_query('社区体检', k=99, synthesize=True)
    assert captured['k'] == 10
    assert out['ok'] is True
    assert out['synthesize'] == 'deferred_v2'
    assert 'guidance' in out
    assert out['dim_counts'] == {'社区': 1}
    assert _caliber_keys(out['caliber'])


def test_rag_query_index_missing_no_raise(monkeypatch):
    monkeypatch.setattr('tools.rag_index.search',
                        lambda query, k: {'ok': False, 'error': '未构建'})
    out = mse.rag_query('任意问题')
    assert out['ok'] is False
    assert 'py tools/rag_index.py --build' in out['hint']
    assert _caliber_keys(out['caliber'])


def test_kb_facts_true_signature_mapping(monkeypatch):
    """主手裁决：kb_facts 直映真身签名（query/keyword/topic/limit），domain 作废。"""
    captured = {}

    def fake(query='', city='宜昌', topic=None, keyword=None, limit=5):
        captured.update(query=query, topic=topic, keyword=keyword, limit=limit)
        return [{'id': 'CHK-1', 'name': '体检事实', 'detail': 'd',
                 'year': '2025', 'source': 's.md', 'topic': 'issue'}]

    monkeypatch.setattr('ai_qa.outlet_kb.urban_renewal_knowledge.query_knowledge_base', fake)
    out = mse.kb_facts(query='体检', keyword='安全', topic='issue', limit=99)
    assert captured['limit'] == 20
    assert captured['topic'] == 'issue' and captured['keyword'] == '安全'
    assert out['count'] == 1 and out['facts'][0]['id'] == 'CHK-1'
    assert _caliber_keys(out['caliber'])


# ════════════ outlet_card ════════════

def test_outlet_card_empty_inputs_no_crash():
    out = mse.outlet_card()
    assert out['cards'] == []
    assert out['card'] is None
    assert _caliber_keys(out['caliber'])


# ════════════ zonal_stats / rank ════════════

def _patch_geo(monkeypatch, merged):
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints())
    monkeypatch.setattr('core.geo_registry.resolve_boundary', lambda boundary: _FakeBoundary())
    monkeypatch.setattr('core.spatial_analysis.aggregate_by_polygons',
                        lambda points, polys, agg_cols=None, polygon_name_col=None: merged)


def test_zonal_stats_rows_cap_row_count_and_caliber(monkeypatch):
    _patch_geo(monkeypatch, _fake_merged(25))
    out = mse.zonal_stats('admin_district', top_n=20)
    assert len(out['rows']) <= 20
    assert out['row_count'] == 25 >= len(out['rows'])
    assert out['truncated'] is True
    assert _caliber_keys(out['caliber'])


def test_zonal_stats_unknown_layer_hint(monkeypatch):
    monkeypatch.setattr('core.geo_registry.resolve_points',
                        lambda layer: (_ for _ in ()).throw(KeyError('未知')))
    out = mse.zonal_stats('admin_district')
    assert out['ok'] is False
    assert 'list_data' in out['hint']
    assert _caliber_keys(out['caliber'])


def test_rank_worst_best_rows_and_caliber(monkeypatch):
    _patch_geo(monkeypatch, _fake_merged(25))
    worst = mse.rank(by='worst', boundary='admin_district', top_n=5)
    best = mse.rank(by='best', boundary='admin_district', top_n=5)
    assert len(worst['rows']) == 5 and worst['row_count'] == 25
    assert len(best['rows']) == 5
    assert worst['rows'][0]['polarity_index'] <= best['rows'][0]['polarity_index']
    assert _caliber_keys(worst['caliber'])
    assert _caliber_keys(best['caliber'])


# ════════════ buffer ════════════

def _patch_buffer(monkeypatch, fc, area=1.234):
    monkeypatch.setattr('core.geo_registry.resolve_boundary', lambda center: _FakeBoundary())
    monkeypatch.setattr('core.buffer_analysis.create_buffer',
                        lambda geojson_fc, distance_m, dissolve, target_crs='EPSG:4546': (fc, area))
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints(inside=2, outside=1))


def test_buffer_small_fc_returns_geometry_and_point_count(monkeypatch):
    _patch_buffer(monkeypatch, _small_buffer_fc(1))
    out = mse.buffer('admin_district')
    assert out['area_km2'] == 1.234
    assert out['point_count'] == 2
    assert 'buffer_fc' in out
    assert _caliber_keys(out['caliber'])


def test_buffer_large_fc_omitted(monkeypatch):
    _patch_buffer(monkeypatch, _small_buffer_fc(6))
    out = mse.buffer('admin_district')
    assert out.get('fc_omitted') is True
    assert 'buffer_fc' not in out
    assert _caliber_keys(out['caliber'])


def test_analysis_output_rejected_three_tools():
    """PT-CB5 审计发现即修：结论层（usage=analysis_output）禁作空间操作输入——三工具服务端强制。"""
    import tools.mcp_server_emc as m
    for fn, kw in [(m.zonal_stats, {'boundary': 'base_174_aggregate_area'}),
                   (m.rank, {'boundary': 'base_18village_area'}),
                   (m.buffer, {'center': 'page7_dual_high'})]:
        r = fn(layer='yichang_l2_t1', **kw)
        assert r.get('ok') is False and 'analysis_output' in r.get('hint', ''), f'{fn.__name__} 未拒绝结论层: {str(r)[:80]}'
    r = m.zonal_stats(boundary='admin_district', layer='yichang_l2_t1', top_n=3)
    assert r.get('rows'), '正常 input 层被误伤'
