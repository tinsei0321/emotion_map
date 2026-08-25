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
import geopandas as gpd
from shapely.geometry import Point, Polygon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import mcp_server_emc as mse


def _caliber_keys(caliber):
    return all(k in caliber for k in ('scale', 'semantics', 'limits', 'refs'))


def _patch_persist(monkeypatch, tmp_path):
    """PT-CB15 K2：layer_output 落盘隔离（tmp manifest + tmp 落盘目录·不写真仓）。"""
    mpath = tmp_path / 'manifest.json'
    mpath.write_text('[]', encoding='utf-8')
    monkeypatch.setattr(mse, 'MANIFEST', str(mpath))
    monkeypatch.setattr(mse, 'TMP_RENDER_DIR', str(tmp_path / 'tmp_render'))


def _assert_render_ref(out, tmp_path, tool):
    """落盘直传公共断言：geojson 键移除 + render_dataset_id + 文件落盘 + manifest 登记。"""
    assert 'geojson' not in out
    ds = out.get('render_dataset_id')
    assert ds and ds.startswith('tmp_render_')
    assert 'render_hint' in out
    files = list((tmp_path / 'tmp_render').glob(f'{tool}-*.geojson'))
    assert len(files) == 1
    fc = json.loads(files[0].read_text(encoding='utf-8'))
    assert fc.get('type') == 'FeatureCollection'
    groups = json.loads((tmp_path / 'manifest.json').read_text(encoding='utf-8'))
    ids = [it['id'] for g in groups for it in g.get('items', [])]
    assert ds in ids
    return fc


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
    inbox = tmp_path / 'DATA' / 'Export' / 'exports' / 'render_inbox'
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


# ════════════ PT-CB9R A-2 · 信号字段族 ════════════

def _fake_results(scores_dims):
    """构造 (dense_score, data_dim) 对的伪检索结果。"""
    return [{'score': 0.02, 'dense_score': s, 'source': f's{i}.md', 'type': 'note',
             'data_dim': d, 'text': 't'} for i, (s, d) in enumerate(scores_dims)]


def test_a2_signal_fields_existence_rag_query_and_kb_facts(monkeypatch):
    """A-2 ①字段存在性：rag_query 恒有 confidence/thin_result·kb_facts 同；高置信无 retry_cue。"""
    monkeypatch.setattr('tools.rag_index.search', lambda query, k: {
        'ok': True, 'count': 3,
        'results': _fake_results([(0.84, '社区'), (0.80, '小区'), (0.75, '住房')])})
    out = mse.rag_query('城市体检', k=3)
    assert out['confidence'] == '高' and out['thin_result'] is False
    assert 'retry_cue' not in out and 'coverage_hint' not in out
    assert 'caliber_ref' not in out   # 高置信且未命中口径类 → 不改道

    monkeypatch.setattr('ai_qa.outlet_kb.urban_renewal_knowledge.query_knowledge_base',
                        lambda **kw: [{'id': 'X', 'name': 'n'}])
    out2 = mse.kb_facts(keyword='体检')
    assert out2['confidence'] == '高' and out2['thin_result'] is False
    assert 'retry_cue' not in out2


def test_a2_confidence_three_tiers_and_low_emits_retry(monkeypatch):
    """A-2 ②三档判定：0.84→高 / 0.56→中 / 0.44→低；低置信发 retry_cue + caliber_ref 改道。"""
    def _run(top1):
        monkeypatch.setattr('tools.rag_index.search', lambda query, k: {
            'ok': True, 'count': 2,
            'results': _fake_results([(top1, '社区'), (top1 - 0.01, '社区')])})
        return mse.rag_query('q', k=5)   # count 2 < k 5 → thin 恒真·不影响档位判定

    assert _run(0.84)['confidence'] == '高'
    assert _run(0.56)['confidence'] == '中'
    low = _run(0.44)
    assert low['confidence'] == '低' and low['thin_result'] is True
    assert any('kb_facts' in c for c in low['retry_cue'])
    assert low['caliber_ref']['kind'] == 'low_confidence'
    assert low['caliber_ref']['suggest'] == 'kb_facts'

    # 零命中 kb_facts → 低置信 + 改道 rag_query
    monkeypatch.setattr('ai_qa.outlet_kb.urban_renewal_knowledge.query_knowledge_base',
                        lambda **kw: [])
    miss = mse.kb_facts(keyword='不存在词')
    assert miss['confidence'] == '低' and miss['thin_result'] is True
    assert miss['caliber_ref']['suggest'] == 'rag_query'


def test_a2_signals_zero_llm_deterministic(monkeypatch):
    """A-2 ③零 LLM 断言：信号派生只读结果字段+本地 json——
    禁止任何 LLM/网络调用混入党发逻辑（patch 哨兵·被调即炸）。"""
    def _boom(*a, **kw):
        raise AssertionError('信号派生不得触发 LLM/网络调用')

    monkeypatch.setattr('tools.rag_index.search', lambda query, k: {
        'ok': True, 'count': 1,
        'results': _fake_results([(0.44, '社区')])})
    # 常见 LLM 入口全部埋雷（若 _derive_* 误入任何其一即失败）
    for mod_name, attr in (('tools.rag_index', '_get_model'),
                           ('tools.rag_index', '_embed_texts')):
        monkeypatch.setattr(f'{mod_name}.{attr}', _boom)
    out1 = mse.rag_query('离题主题', k=5)
    assert out1['confidence'] == '低' and out1['retry_cue']
    # 直接调派生函数（不经过 search）亦确定性可复算——同输入同输出
    s1 = mse._derive_retrieval_signals(_fake_results([(0.56, '社区')]), 5, '社区', {'社区': 1})
    s2 = mse._derive_retrieval_signals(_fake_results([(0.56, '社区')]), 5, '社区', {'社区': 1})
    assert s1 == s2 and s1['confidence'] == '中'


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


# ════════════ PT-CB11 P1 · grid_aggregate / compare_regions / hotspot_analysis ════════════

def test_track_ids_f033_to_f035_registered():
    from core.tracker import _TRACKING_REGISTRY
    for n in range(33, 36):
        assert f'MOD_AIQA.F_{n:03d}' in _TRACKING_REGISTRY, f'F_{n:03d} 未注册'


def _fake_grid(n=25):
    return gpd.GeoDataFrame({
        'point_count': list(range(1, n + 1)),
        'score_sum': [float(i) * 2 for i in range(1, n + 1)],
        'score_mean': [float(i) / 10 for i in range(1, n + 1)],
    }, geometry=[Polygon([(111, 30), (111.01, 30), (111.01, 30.01), (111, 30.01), (111, 30)])
                  for _ in range(n)])


def test_grid_aggregate_rows_stats_and_caliber(monkeypatch):
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints(inside=3))
    monkeypatch.setattr('core.spatial_analysis.create_square_grid',
                        lambda points, cell_size, agg_cols=None: _fake_grid(25))
    out = mse.grid_aggregate(value_col='score', top_n=5)
    assert len(out['rows']) == 5 and out['row_count'] == 25 and out['truncated'] is True
    assert out['rows'][0]['point_count'] == 25
    assert 'score_sum' in out['rows'][0] and 'score_mean' in out['rows'][0]
    assert out['stats']['total_cells'] == 25 and out['stats']['max_count'] == 25
    assert _caliber_keys(out['caliber'])


def test_grid_aggregate_top_n_cap_and_layer_output(monkeypatch, tmp_path):
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints(inside=3))
    monkeypatch.setattr('core.spatial_analysis.create_square_grid',
                        lambda points, cell_size, agg_cols=None: _fake_grid(30))
    _patch_persist(monkeypatch, tmp_path)
    out = mse.grid_aggregate(top_n=99, layer_output=True)
    assert len(out['rows']) <= 20
    _assert_render_ref(out, tmp_path, 'grid_aggregate')
    assert _caliber_keys(out['caliber'])


def test_grid_aggregate_unknown_layer_and_missing_value_col(monkeypatch):
    monkeypatch.setattr('core.geo_registry.resolve_points',
                        lambda layer: (_ for _ in ()).throw(KeyError('未知')))
    assert 'list_data' in mse.grid_aggregate()['hint']
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints(inside=3))
    out = mse.grid_aggregate(value_col='missing_col')
    assert out['ok'] is False and 'value_col' in out['hint']


def test_grid_aggregate_analysis_output_boundary_rejected():
    out = mse.grid_aggregate(boundary='base_174_aggregate_area')
    assert out.get('ok') is False and 'analysis_output' in out.get('hint', '')


def _fake_region_merged():
    return pd.DataFrame({
        'name': ['西陵区', '伍家岗区'],
        'point_count': [200, 50],
        'polarity_index': [0.5, -0.8],
        'score_mean': [3.0, 2.5],
    })


def _patch_compare(monkeypatch, merged=None):
    monkeypatch.setattr('core.geo_registry.list_boundaries',
                        lambda: [{'id': 'a_district', 'label': 'A 区'},
                                 {'id': 'b_district', 'label': 'B 区'}])
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints(inside=2))
    monkeypatch.setattr('core.geo_registry.resolve_boundary',
                        lambda boundary: gpd.GeoDataFrame(
                            geometry=[Polygon([(111, 30), (111.01, 30), (111.01, 30.01), (111, 30.01), (111, 30)])]))
    monkeypatch.setattr('core.spatial_analysis.aggregate_by_polygons',
                        lambda points, polys, agg_cols=None, polygon_name_col=None:
                        merged if merged is not None else _fake_region_merged())


def test_compare_regions_happy_path_diff(monkeypatch):
    _patch_compare(monkeypatch)
    out = mse.compare_regions(['a_district', 'b_district'])
    assert out['count'] == 2 and out['truncated'] is False
    assert [r['name'] for r in out['regions']] == ['西陵区', '伍家岗区']
    assert out['diff']['point_count']['max_region'] == '西陵区'
    assert out['diff']['point_count']['ratio'] == 4.0
    assert out['diff']['polarity_index']['max_region'] == '伍家岗区'  # abs 值语义
    assert _caliber_keys(out['caliber'])


def test_compare_regions_needs_two_and_string_split(monkeypatch):
    _patch_compare(monkeypatch)
    one = mse.compare_regions(['a_district'])
    assert one['ok'] is False and '≥2' in one['hint']
    out = mse.compare_regions('a_district|b_district')
    assert out['count'] == 2


def test_compare_regions_over_five_truncates(monkeypatch):
    _patch_compare(monkeypatch)
    out = mse.compare_regions([f'd{i}' for i in range(7)])
    assert out['truncated'] is True


def test_compare_regions_analysis_output_rejected(monkeypatch):
    _patch_compare(monkeypatch)
    out = mse.compare_regions(['a_district', 'base_174_aggregate_area'])
    assert out.get('ok') is False and 'analysis_output' in out.get('hint', '')


def _fake_hotspot(n=12):
    tiers = ['hot'] * 2 + ['cold'] * 1 + ['tend_hot'] * 3 + ['ns'] * (n - 7) + ['tend_cold'] * 1
    z = [3.2, 2.1, -2.5, 1.4, 1.2, 1.1, 1.05] + [0.1] * max(0, n - 8) + [-1.3]
    return gpd.GeoDataFrame({
        'Gi_Z': z[:n], 'Gi_P': [0.01] * n, 'hotspot_tier': tiers[:n],
        'place_name': [f'点{i}' for i in range(n)],
    }, geometry=[Point(111.3 + i * 0.001, 30.7 + i * 0.001) for i in range(n)])


def test_hotspot_analysis_counts_and_priority_order(monkeypatch):
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints(inside=12))
    monkeypatch.setattr('core.spatial_analysis.hot_spot_analysis',
                        lambda gdf, value_col, invert, threshold, soft_threshold: _fake_hotspot())
    out = mse.hotspot_analysis(top_n=5)
    assert out['counts'] == {'hot': 2, 'tend_hot': 3, 'ns': 5, 'tend_cold': 1, 'cold': 1}
    assert out['rows'][0]['hotspot_tier'] == 'hot' and abs(out['rows'][0]['Gi_Z']) >= 3
    assert out['rows'][2]['hotspot_tier'] == 'cold'
    assert out['row_count'] == 12 and out['truncated'] is True
    assert _caliber_keys(out['caliber'])


def test_hotspot_analysis_unknown_layer_and_missing_value_col(monkeypatch):
    monkeypatch.setattr('core.geo_registry.resolve_points',
                        lambda layer: (_ for _ in ()).throw(KeyError('未知')))
    assert 'list_data' in mse.hotspot_analysis()['hint']
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints(inside=5))
    out = mse.hotspot_analysis(value_col='missing_col')
    assert out['ok'] is False and 'value_col' in out['hint'] and 'density' in out['hint']


# ════════════ PT-CB11 P2 · 空集补丁 + nearest/overlay + 顺手件 ════════════

def test_grid_aggregate_empty_result_semantic_reject(monkeypatch):
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints(inside=0))
    monkeypatch.setattr('core.spatial_analysis.create_square_grid',
                        lambda points, cell_size, agg_cols=None:
                        gpd.GeoDataFrame(columns=['point_count'], geometry=[]))
    out = mse.grid_aggregate()
    assert out['ok'] is False and '聚合结果为空' in out['hint']
    assert _caliber_keys(out['caliber'])


def test_grid_aggregate_missing_point_count_column_reject(monkeypatch):
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints(inside=2))
    monkeypatch.setattr('core.spatial_analysis.create_square_grid',
                        lambda points, cell_size, agg_cols=None:
                        gpd.GeoDataFrame({'score_mean': [0.1]}, geometry=[Polygon(
                            [(111, 30), (111.01, 30), (111.01, 30.01), (111, 30.01), (111, 30)])]))
    out = mse.grid_aggregate()
    assert out['ok'] is False and '聚合结果为空' in out['hint']


def test_compare_regions_empty_merge_semantic_reject(monkeypatch):
    _patch_compare(monkeypatch, merged=pd.DataFrame(columns=['name', 'point_count']))
    out = mse.compare_regions(['a_district', 'b_district'])
    assert out['ok'] is False and '聚合结果为空' in out['hint']
    assert _caliber_keys(out['caliber'])


def _nearest_layers(monkeypatch, anchors=3, pois=2):
    anchor_gdf = gpd.GeoDataFrame(
        {'place_name': [f'锚{i}' for i in range(anchors)]},
        geometry=[Point(111.30 + i * 0.01, 30.70) for i in range(anchors)])
    poi_gdf = gpd.GeoDataFrame(
        {'name': [f'POI{j}' for j in range(pois)]},
        geometry=[Point(111.301 + j * 0.02, 30.70) for j in range(pois)])

    def _resolve(layer):
        if layer == 'anchors':
            return anchor_gdf
        if layer == 'pois':
            return poi_gdf
        raise KeyError('未知')

    monkeypatch.setattr('core.geo_registry.resolve_points', _resolve)
    return anchor_gdf, poi_gdf


def test_nearest_analysis_requires_target(monkeypatch):
    out = mse.nearest_analysis(layer='anchors', target='')
    assert out['ok'] is False and 'target' in out['hint']
    assert _caliber_keys(out['caliber'])


def test_nearest_analysis_k1_pairs_sorted(monkeypatch):
    _nearest_layers(monkeypatch, anchors=3, pois=2)
    out = mse.nearest_analysis(layer='anchors', target='pois', k=1)
    assert out.get('ok') is not False and len(out['pairs']) == 3
    assert out['pairs'] == sorted(out['pairs'], key=lambda p: p['dist_m'])
    assert out['stats']['pair_count'] == 3 and out['stats']['max_dist'] >= out['stats']['mean_dist']
    assert all('POI' in p['target'] for p in out['pairs'])
    assert _caliber_keys(out['caliber'])


def test_nearest_analysis_k3_cap_and_top_n(monkeypatch):
    _nearest_layers(monkeypatch, anchors=5, pois=6)
    out = mse.nearest_analysis(layer='anchors', target='pois', k=9, top_n=99)
    assert out['stats']['pair_count'] == 5 * 5  # k cap 5
    assert len(out['pairs']) <= 20  # top_n cap 20
    assert out['truncated'] is True


def test_nearest_analysis_empty_anchor_semantic_reject(monkeypatch):
    _nearest_layers(monkeypatch, anchors=0, pois=2)
    out = mse.nearest_analysis(layer='anchors', target='pois')
    assert out['ok'] is False and '锚点层为空' in out['hint']


def test_nearest_analysis_layer_output_lines(monkeypatch):
    _nearest_layers(monkeypatch, anchors=2, pois=2)
    out = mse.nearest_analysis(layer='anchors', target='pois', k=1, layer_output=True)
    assert out['geojson']['type'] == 'FeatureCollection'
    assert all(f['geometry']['type'] == 'LineString' for f in out['geojson']['features'])
    assert _caliber_keys(out['caliber'])


def test_nearest_analysis_unknown_layer_hint(monkeypatch):
    _nearest_layers(monkeypatch)
    out = mse.nearest_analysis(layer='missing', target='pois')
    assert out['ok'] is False and 'list_data' in out['hint']


_POLY_A = Polygon([(111.30, 30.70), (111.36, 30.70), (111.36, 30.76), (111.30, 30.76), (111.30, 30.70)])
_POLY_B = Polygon([(111.33, 30.73), (111.40, 30.73), (111.40, 30.80), (111.33, 30.80), (111.33, 30.73)])
_POLY_FAR = Polygon([(112.5, 31.5), (112.6, 31.5), (112.6, 31.6), (112.5, 31.6), (112.5, 31.5)])


def _patch_overlay(monkeypatch):
    def _resolve(boundary):
        if boundary == 'poly_a':
            return gpd.GeoDataFrame({'name': ['A 面']}, geometry=[_POLY_A], crs='EPSG:4326')
        if boundary == 'poly_b':
            return gpd.GeoDataFrame({'name': ['B 面']}, geometry=[_POLY_B], crs='EPSG:4326')
        if boundary == 'poly_far':
            return gpd.GeoDataFrame({'name': ['远面']}, geometry=[_POLY_FAR], crs='EPSG:4326')
        raise KeyError('未知')

    monkeypatch.setattr('core.geo_registry.resolve_boundary', _resolve)


def test_overlay_analysis_requires_layers_and_valid_how(monkeypatch):
    _patch_overlay(monkeypatch)
    miss = mse.overlay_analysis('', 'poly_b')
    assert miss['ok'] is False and 'layer_a' in miss['hint']
    bad = mse.overlay_analysis('poly_a', 'poly_b', how='xor')
    assert bad['ok'] is False and 'how 非法' in bad['hint']
    assert _caliber_keys(bad['caliber'])


def test_overlay_analysis_intersection_rows_and_stats(monkeypatch):
    _patch_overlay(monkeypatch)
    out = mse.overlay_analysis('poly_a', 'poly_b', how='intersection')
    assert out['result_count'] == 1
    assert out['rows'][0]['name_a'] == 'A 面' and out['rows'][0]['name_b'] == 'B 面'
    assert out['stats']['total_area_km2'] > 0
    assert _caliber_keys(out['caliber'])


def test_overlay_analysis_empty_intersection_semantic_reject(monkeypatch):
    _patch_overlay(monkeypatch)
    out = mse.overlay_analysis('poly_a', 'poly_far', how='intersection')
    assert out['ok'] is False and '叠置结果为空' in out['hint']
    assert _caliber_keys(out['caliber'])


def test_overlay_analysis_union_layer_output(monkeypatch, tmp_path):
    _patch_overlay(monkeypatch)
    _patch_persist(monkeypatch, tmp_path)
    out = mse.overlay_analysis('poly_a', 'poly_b', how='union', top_n=99, layer_output=True)
    assert len(out['rows']) <= 20
    _assert_render_ref(out, tmp_path, 'overlay_analysis')
    assert _caliber_keys(out['caliber'])


def test_overlay_analysis_analysis_output_rejected(monkeypatch):
    _patch_overlay(monkeypatch)
    out = mse.overlay_analysis('base_174_aggregate_area', 'poly_b')
    assert out.get('ok') is False and 'analysis_output' in out.get('hint', '')


def test_hotspot_analysis_layer_output_geojson(monkeypatch, tmp_path):
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints(inside=12))
    monkeypatch.setattr('core.spatial_analysis.hot_spot_analysis',
                        lambda gdf, value_col, invert, threshold, soft_threshold: _fake_hotspot())
    _patch_persist(monkeypatch, tmp_path)
    out = mse.hotspot_analysis(layer_output=True)
    fc = _assert_render_ref(out, tmp_path, 'hotspot_analysis')
    assert all('value' in f['properties'] for f in fc['features'])
    assert _caliber_keys(out['caliber'])


# ════════════ PT-CB11 P2 Phase 2 · trend / report_assemble / guard ════════════

def _trend_layer(polarity_labels, scores):
    n = len(polarity_labels)
    return gpd.GeoDataFrame(
        {'score': scores, 'polarity': polarity_labels},
        geometry=[Point(111.3 + i * 0.001, 30.7) for i in range(n)])


def _patch_trend(monkeypatch, layers):
    def _resolve(layer):
        if layer in layers:
            return layers[layer]
        raise KeyError('未知')

    monkeypatch.setattr('core.geo_registry.resolve_points', _resolve)


def test_trend_analysis_citywide_direction_and_steps(monkeypatch):
    _patch_trend(monkeypatch, {
        'yichang_l2_t1': _trend_layer(['Very Negative'] * 2 + ['Negative'] * 2, [1.0] * 4),
        'yichang_l2_t2': _trend_layer(['Neutral'] * 4, [2.0] * 4),
        'yichang_l2_t3': _trend_layer(['Very Positive'] * 2 + ['Positive'] * 2, [3.0] * 4),
    })
    out = mse.trend_analysis()
    assert out['metric'] == 'polarity_index' and out['direction'] == 'up'
    assert out['delta'] == 3.0  # -1.5 -> +1.5
    assert [r['period'] for r in out['rows']] == ['T1', 'T2', 'T3']
    assert out['steps'][0]['from'] == 'T1' and out['steps'][-1]['to'] == 'T3'
    assert _caliber_keys(out['caliber'])
    sm = mse.trend_analysis(metric='score_mean')
    assert sm['delta'] == 2.0 and sm['direction'] == 'up'


def test_trend_analysis_metric_and_periods_validation(monkeypatch):
    _patch_trend(monkeypatch, {})
    bad = mse.trend_analysis(metric='bad')
    assert bad['ok'] is False and 'metric 非法' in bad['hint']
    one = mse.trend_analysis(periods=['T1'])
    assert one['ok'] is False and '≥2 期' in one['hint']
    t4 = mse.trend_analysis(periods=['T1', 'T4'])
    assert t4['ok'] is False and 'T4' in t4['hint']


def test_trend_analysis_periods_subset_and_string(monkeypatch):
    _patch_trend(monkeypatch, {
        'yichang_l2_t1': _trend_layer(['Negative'] * 4, [1.0] * 4),
        'yichang_l2_t3': _trend_layer(['Positive'] * 4, [3.0] * 4),
    })
    out = mse.trend_analysis(periods='t1|t3', metric='score_mean')
    assert out['period_count'] == 2 and out['direction'] == 'up'


def test_trend_analysis_empty_layer_semantic_reject(monkeypatch):
    _patch_trend(monkeypatch, {
        'yichang_l2_t1': _trend_layer(['Negative'] * 4, [1.0] * 4),
        'yichang_l2_t2': gpd.GeoDataFrame({'score': [], 'polarity': []}, geometry=[]),
        'yichang_l2_t3': _trend_layer(['Positive'] * 4, [3.0] * 4),
    })
    out = mse.trend_analysis()
    assert out['ok'] is False and '点层为空' in out['hint']
    assert _caliber_keys(out['caliber'])


def test_trend_analysis_boundary_aggregate_path(monkeypatch):
    _patch_trend(monkeypatch, {
        lid: _trend_layer(['Negative'] * 4, [1.0] * 4)
        for lid in ('yichang_l2_t1', 'yichang_l2_t2', 'yichang_l2_t3')
    })
    monkeypatch.setattr('core.geo_registry.resolve_boundary',
                        lambda boundary: gpd.GeoDataFrame(geometry=[Polygon(
                            [(111, 30), (111.1, 30), (111.1, 30.1), (111, 30.1), (111, 30)])]))

    def _agg(points, polys, agg_cols=None, polygon_name_col=None):
        return pd.DataFrame({'name': ['整体'], 'point_count': [4], 'score_mean': [1.0]})

    monkeypatch.setattr('core.spatial_analysis.aggregate_by_polygons', _agg)
    out = mse.trend_analysis(boundary='admin_district', metric='score_mean')
    assert out['period_count'] == 3 and all(r['score_mean'] == 1.0 for r in out['rows'])
    assert out['direction'] == 'flat'


def test_trend_analysis_boundary_guard_rejects_analysis_output():
    out = mse.trend_analysis(boundary='base_174_aggregate_area')
    assert out.get('ok') is False and 'analysis_output' in out.get('hint', '')


def test_report_assemble_empty_results_semantic_reject():
    out = mse.report_assemble(question='q', results=[])
    assert out['ok'] is False and 'results' in out['hint']
    assert _caliber_keys(out['caliber'])


def test_report_assemble_sections_refs_dedupe():
    r1 = {'rows': [], 'row_count': 3, 'caliber': {'refs': ['K-C1']}}
    r2 = {'pairs': [], 'row_count': 2, 'caliber': {'refs': ['K-C1', 'K-01']}}
    out = mse.report_assemble(question='哪里差', results=[r1, r2])
    assert set(out['sections']) == {'conclusion', 'evidence', 'caliber', 'suggestion'}
    assert out['sections']['caliber']['refs'] == ['K-C1', 'K-01']
    assert out['sections']['caliber']['missing_caliber_count'] == 0
    assert '汇总 2/2 项有效结果' in out['sections']['conclusion']
    assert isinstance(out['sections']['suggestion'], str)
    assert _caliber_keys(out['caliber'])


def test_report_assemble_missing_caliber_marked_not_fabricated():
    out = mse.report_assemble(results=[{'rows': [], 'row_count': 1}, 'garbage'])
    ev = out['sections']['evidence']
    assert ev[0]['scale'] == '口径缺失' and ev[1]['scale'] == '口径缺失'
    assert out['sections']['caliber']['missing_caliber_count'] == 2
    assert '口径缺失' in out['sections']['conclusion']
    assert out['sections']['caliber']['refs'] == []


def test_report_assemble_suggestion_from_rows_and_filter():
    r = {'rows': [{'suggestion': '补设施'}, {'suggestion': '优交通'}, {'suggestion': '第3'},
                  {'suggestion': '不取'}],
         'row_count': 4, 'caliber': {'refs': ['K-C1']}}
    out = mse.report_assemble(results=[r])
    assert out['sections']['suggestion'] == ['补设施', '优交通', '第3']  # 每结果前 3 行
    only = mse.report_assemble(results=[r], sections=['caliber'])
    assert set(only['sections']) == {'caliber'}


def test_guard_check_rejects_and_passes():
    cal = {'scale': 's', 'semantics': 'm', 'limits': 'l', 'refs': ['K-C1']}
    bad = mse._guard_check('trend_analysis', {'boundary': 'base_174_aggregate_area'}, cal)
    assert bad is not None and bad['ok'] is False and 'analysis_output' in bad['hint']
    assert mse._guard_check('trend_analysis', {'boundary': 'admin_district'}, cal) is None
    assert mse._guard_check('not_a_tool', {'boundary': 'x'}, cal) is None
    assert mse._guard_check('trend_analysis', {}, cal) is None


def test_guard_check_undeclared_tool_passes_documented_behavior():
    """PT-CB12 T1⑥：未声明工具调 _guard_check → 放行（None）。

    这是文档化行为（fail-open 到「无守卫」而非报错）：新工具漏登记 _GUARD_SPECS 不会崩，
    但也意味着无 usage 守卫——防线是 _audit_input_surfaces 启动核对（B4 差集 WARN）
    与本批全量接线约定（新带面输入工具必须同步登记 + 入口调 _guard_check）。"""
    assert mse._guard_check('brand_new_tool', {'boundary': 'base_174_aggregate_area'}) is None
    assert 'brand_new_tool' not in mse._GUARD_SPECS


def test_audit_input_surfaces_warns_on_spec_drift(monkeypatch):
    captured = []
    monkeypatch.setattr(mse, '_safe_print', lambda msg, file=None: captured.append(msg))
    original = dict(mse._GUARD_SPECS)
    drifted = dict(mse._GUARD_SPECS)
    drifted['trend_analysis'] = {'usage_params': ('not_a_param',)}
    monkeypatch.setattr(mse, '_GUARD_SPECS', drifted)
    mse._audit_input_surfaces()
    assert any('not_a_param' in m and 'WARN' in m for m in captured)
    assert any('B4 输入面核对' in m for m in captured)

    captured.clear()
    monkeypatch.setattr(mse, '_GUARD_SPECS', original)
    mse._audit_input_surfaces()
    assert not any('WARN' in m for m in captured)


# ════════════ area_stats（PT-CB11 F_037·Kimi）════════════

def _fake_area_boundary(n=3, groups=None):
    """n 个方格面（宜昌附近·EPSG:4326）：第 i 格边长 0.01*(i+1) → 面积比 1:4:9:16..."""
    geoms = []
    for i in range(n):
        x0, y0 = 111.0 + i * 0.08, 30.0
        s = 0.01 * (i + 1)
        geoms.append(Polygon([(x0, y0), (x0 + s, y0), (x0 + s, y0 + s),
                              (x0, y0 + s), (x0, y0)]))
    data = {'name': [f'单元{i}' for i in range(n)]}
    if groups:
        data['DLMC'] = groups
    return gpd.GeoDataFrame(data, geometry=geoms, crs='EPSG:4326')


def test_track_id_f037_registered():
    from core.tracker import _TRACKING_REGISTRY
    assert 'MOD_AIQA.F_037' in _TRACKING_REGISTRY


def test_area_stats_happy_path_rows_order_and_caliber(monkeypatch):
    monkeypatch.setattr('core.geo_registry.resolve_boundary',
                        lambda boundary: _fake_area_boundary(3))
    out = mse.area_stats('fake_boundary')
    assert out['row_count'] == 3 and out['truncated'] is False
    assert [r['name'] for r in out['rows']] == ['单元2', '单元1', '单元0']   # 面积降序
    # 边长比 1:2:3 → 面积比 1:4:9 → 首行占比 ≈ 9/14
    assert abs(out['rows'][0]['share_pct'] - 900 / 14) < 1.0
    assert abs(sum(r['share_pct'] for r in out['rows']) - 100.0) < 0.5
    assert out['total_km2'] > 0
    assert _caliber_keys(out['caliber'])


def test_area_stats_numeric_area_value(monkeypatch):
    """面积数值断言：0.01° 方格（111E/30N）测地约 1.067 km²——投影差须 <6%（口径卡 <1% 级的工程容差）。"""
    monkeypatch.setattr('core.geo_registry.resolve_boundary',
                        lambda boundary: _fake_area_boundary(1))
    out = mse.area_stats('fake_boundary')
    assert 1.0 <= out['rows'][0]['area_km2'] <= 1.13
    assert out['rows'][0]['share_pct'] == 100.0
    assert out['rows'][0]['area_km2'] == out['total_km2']


def test_area_stats_group_by_dissolve_share(monkeypatch):
    monkeypatch.setattr('core.geo_registry.resolve_boundary',
                        lambda boundary: _fake_area_boundary(4, groups=['甲', '甲', '乙', '乙']))
    out = mse.area_stats('fake_boundary', group_by='DLMC')
    assert out['row_count'] == 2
    assert out['rows'][0]['DLMC'] == '乙'   # 9+16=25 > 1+4=5
    assert abs(out['rows'][0]['share_pct'] - 25 / 30 * 100) < 1.0
    assert abs(sum(r['share_pct'] for r in out['rows']) - 100.0) < 0.5
    assert _caliber_keys(out['caliber'])


def test_area_stats_group_by_missing_col_semantic(monkeypatch):
    monkeypatch.setattr('core.geo_registry.resolve_boundary',
                        lambda boundary: _fake_area_boundary(3, groups=['甲', '甲', '乙']))
    out = mse.area_stats('fake_boundary', group_by='缺列')
    assert out['ok'] is False
    assert 'group_by' in out['hint'] and 'DLMC' in out['hint']   # 语义化拒绝带可用列
    assert _caliber_keys(out['caliber'])


def test_area_stats_top_n_cap_and_layer_output(monkeypatch, tmp_path):
    monkeypatch.setattr('core.geo_registry.resolve_boundary',
                        lambda boundary: _fake_area_boundary(25))
    _patch_persist(monkeypatch, tmp_path)
    out = mse.area_stats('fake_boundary', top_n=99, layer_output=True)
    assert len(out['rows']) <= 20 and out['row_count'] == 25 and out['truncated'] is True
    fc = _assert_render_ref(out, tmp_path, 'area_stats')
    assert len(fc['features']) <= 20
    assert _caliber_keys(out['caliber'])


def test_area_stats_analysis_output_rejected():
    out = mse.area_stats('base_174_aggregate_area')
    assert out.get('ok') is False and 'analysis_output' in out.get('hint', '')


def test_area_stats_unknown_boundary_hint(monkeypatch):
    monkeypatch.setattr('core.geo_registry.resolve_boundary',
                        lambda boundary: (_ for _ in ()).throw(FileNotFoundError('未知')))
    out = mse.area_stats('missing_preset')
    assert out['ok'] is False and 'list_data' in out['hint']
    assert _caliber_keys(out['caliber'])


def test_area_stats_zero_area_rejected(monkeypatch):
    geoms = [Polygon([(111.0, 30.0), (111.01, 30.0), (111.01, 30.0), (111.0, 30.0)])]   # 退化面·面积 0
    gdf = gpd.GeoDataFrame({'name': ['退化']}, geometry=geoms, crs='EPSG:4326')
    monkeypatch.setattr('core.geo_registry.resolve_boundary', lambda boundary: gdf)
    out = mse.area_stats('fake_boundary')
    assert out['ok'] is False and '面积合计为 0' in out['hint']
    assert _caliber_keys(out['caliber'])


# ════════════ PT-CB11 P2 Phase1 · nearest 修复回归（zcode 协同顺手修） ════════════

def test_nearest_polygon_target_representative_point(monkeypatch):
    """面 target 不再崩 .geometry.x——representative_point() 适配（P1 修复回归）。"""
    import geopandas as gpd
    from shapely.geometry import Point, Polygon
    anchor = gpd.GeoDataFrame({'score': [1.0]}, geometry=[Point(111.25, 30.62)], crs='EPSG:4326')
    polys = gpd.GeoDataFrame(
        {'name': ['伍家岗区']},
        geometry=[Polygon([(111.3, 30.6), (111.4, 30.6), (111.4, 30.7), (111.3, 30.6)])],
        crs='EPSG:4326')
    monkeypatch.setattr('core.geo_registry.resolve_points',
                        lambda layer: anchor if layer == 'yichang_l2_t1' else (_ for _ in ()).throw(KeyError))
    monkeypatch.setattr('core.geo_registry.resolve_boundary', lambda t: polys)
    out = mse.nearest_analysis(layer='yichang_l2_t1', target='admin_district', k=1, top_n=3)
    assert 'pairs' in out and out['pairs'][0]['target'] == '伍家岗区'
    assert out['pairs'][0]['dist_m'] > 0


def test_nearest_pair_budget_guard(monkeypatch):
    """配对规模超预算语义化拒绝（防 GB 级中间矩阵·P2 守卫）。"""
    import geopandas as gpd
    from shapely.geometry import Point
    big = gpd.GeoDataFrame({'score': [1.0] * 8000},
                           geometry=[Point(111.2 + i * 1e-5, 30.6) for i in range(8000)],
                           crs='EPSG:4326')
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: big)
    out = mse.nearest_analysis(layer='yichang_l2_t1', target='yichang_l1_t1', k=1)
    assert out.get('ok') is False and '配对规模超预算' in out['hint']


# ════════════ PT-CB16 C2-3 · scale 确定性倒推 ════════════

def _reset_call_log(monkeypatch):
    monkeypatch.setattr(mse, '_TOOL_CALL_LOG', [])


def test_infer_scale_quiet_when_brief(monkeypatch):
    """brief 声明 + 单工具少量调用 → 判对静默（None）。"""
    _reset_call_log(monkeypatch)
    mse._note_call('list_data')
    mse._note_call('zonal_stats')
    assert mse.infer_scale('brief') is None


def test_infer_scale_warns_on_undershoot(monkeypatch):
    """声明 brief 却跑了 5 件工具 4 类 → 判错软提示（含计数与文案）。"""
    _reset_call_log(monkeypatch)
    for name in ('list_data', 'zonal_stats', 'rank', 'kb_facts', 'kb_facts'):
        mse._note_call(name)
    sc = mse.infer_scale('brief')
    assert sc is not None
    assert sc['inferred'] == 'analysis' and sc['declared'] == 'brief'
    assert sc['calls'] == 5 and sc['tool_kinds'] == 4
    assert '规模接近' in sc['note']
    # 声明 analysis 同场景 → 判对静默
    assert mse.infer_scale('analysis') is None


def test_infer_scale_burst_split(monkeypatch):
    """间隔 >120s 的旧调用不计入当前段（防跨问题累计误判）。"""
    _reset_call_log(monkeypatch)
    import time as _t
    old = _t.time() - 300
    for name in ('zonal_stats', 'rank', 'grid_aggregate', 'hotspot_analysis', 'area_stats'):
        mse._TOOL_CALL_LOG.append((old, name))
        old += 10
    mse._note_call('list_data')   # 当前段仅 1 件
    assert mse.infer_scale('brief') is None


def test_outlet_card_scale_check_field(monkeypatch):
    """outlet_card：判错时挂 scale_check；判对不挂（静音条件）。"""
    _reset_call_log(monkeypatch)
    for name in ('list_data', 'zonal_stats', 'rank', 'kb_facts', 'rag_query'):
        mse._note_call(name)
    out = mse.outlet_card(question='q', result={}, diagnose={'scale': 'brief'})
    assert 'scale_check' in out and out['scale_check']['inferred'] in ('analysis', 'research')
    _reset_call_log(monkeypatch)
    out2 = mse.outlet_card(question='q', result={}, diagnose={})
    assert 'scale_check' not in out2


# ════════════ PT-CB16 C2-1 · followup_actions 两级结构 ════════════

def test_action_cues_param_level_resolved_params():
    """参数级 cue：top_n 增量携带完整参数集（resolved_params 自包含·不依赖历史）。"""
    cues = mse._action_cues('rank', {'boundary': 'b', 'layer': 'l', 'by': 'worst',
                                     'top_n': 7, 'sort_by': 'point_count'})
    assert cues and cues[0]['tool'] == 'rank'
    assert cues[0]['params']['top_n'] == 8
    # 完整性：除 top_n 外其余参数原样携带
    assert cues[0]['params']['boundary'] == 'b' and cues[0]['params']['by'] == 'worst'
    # rank 附加 by 翻转 cue
    flips = [c for c in cues if c['params'].get('by') == 'best']
    assert flips, 'rank 应有 by 翻转 cue'
    # top_n=20 到顶不出增量 cue
    cues_max = mse._action_cues('rank', {'boundary': 'b', 'top_n': 20, 'by': 'worst'})
    assert all(c['params'].get('top_n') != 21 for c in cues_max)


def test_zonal_rank_output_has_followup_actions(monkeypatch):
    """zonal/rank 输出带 followup_actions（参数级+提示级）。"""
    merged = _fake_merged(5)
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints())
    monkeypatch.setattr('core.geo_registry.resolve_boundary', lambda boundary: _FakeBoundary())
    monkeypatch.setattr('core.spatial_analysis.aggregate_by_polygons',
                        lambda points, polys, agg_cols=None, polygon_name_col=None: merged)
    out = mse.zonal_stats('admin_district', top_n=3)
    actions = out.get('followup_actions')
    assert actions and actions[0]['params']['top_n'] == 4
    assert any('cue_text' in a and 'tool' not in a for a in actions), '提示级 cue 仅 cue_text'
    out_r = mse.rank(boundary='admin_district', top_n=2)
    assert out_r['followup_actions'][0]['params']['top_n'] == 3
