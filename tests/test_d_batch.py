"""PT-CB6 D 批打磨测试（D1/D11 + D10 源码分派断言）。

新增测试上浮说明：本文件新增用例后，全量门禁由 427 passed + 2 skipped 上浮。
"""

import os
import sys

import pandas as pd
from shapely.geometry import Point

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import mcp_server_emc as mse


class _FakePoints:
    def __init__(self):
        self.columns = ['score']
        self.geometry = [Point(111.30, 30.70), Point(111.31, 30.71)]


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


def _patch_geo(monkeypatch, merged):
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints())
    monkeypatch.setattr('core.geo_registry.resolve_boundary', lambda boundary: _FakeBoundary())
    monkeypatch.setattr('core.spatial_analysis.aggregate_by_polygons',
                        lambda points, polys, agg_cols=None, polygon_name_col=None: merged)


# ════════════ D1：zonal_stats / rank sort_by ════════════

def test_zonal_stats_point_count_sort(monkeypatch):
    _patch_geo(monkeypatch, _fake_merged(25))
    out = mse.zonal_stats('admin_district', sort_by='point_count', top_n=5)
    assert out.get('rows')
    counts = [r['point_count'] for r in out['rows']]
    assert counts == sorted(counts, reverse=True), 'point_count 未按件数降序'


def test_zonal_stats_default_polarity_zero_regression(monkeypatch):
    _patch_geo(monkeypatch, _fake_merged(25))
    out = mse.zonal_stats('admin_district', top_n=5)
    assert out.get('rows')
    pis = [abs(r['polarity_index']) for r in out['rows']]
    assert pis == sorted(pis, reverse=True), '默认 polarity_index 排序退化'


def test_rank_point_count_sort(monkeypatch):
    _patch_geo(monkeypatch, _fake_merged(25))
    out = mse.rank(boundary='admin_district', sort_by='point_count', top_n=5)
    assert out.get('rows')
    counts = [r['point_count'] for r in out['rows']]
    assert counts == sorted(counts, reverse=True), 'rank point_count 未按件数降序'


def test_zonal_stats_invalid_sort_by(monkeypatch):
    _patch_geo(monkeypatch, _fake_merged(25))
    out = mse.zonal_stats('admin_district', sort_by='bad')
    assert out.get('ok') is False
    assert 'sort_by 非法' in out.get('hint', '')


# ════════════ D11：render_spec K-C1 口径校验 ════════════

def _small_fc():
    return {
        'type': 'FeatureCollection',
        'features': [{
            'type': 'Feature',
            'geometry': {'type': 'Polygon', 'coordinates': [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
            # PT-CB11 B3-2：inline choropleth 须 value_field 在属性中（默认 polarity_index）
            'properties': {'name': 'x', 'polarity_index': 0.5},
        }],
    }


def test_render_spec_dataset_mismatch_warning(monkeypatch, tmp_path):
    monkeypatch.setattr(mse, 'REPO', str(tmp_path))
    # B3-2：top10 数据无 polarity_index——用其真实指标字段 诉求总量（renderFields 已声明）
    out = mse.render_spec(kind='choropleth', name='测试', dataset_id='page7_12345_top10',
                          value_field='诉求总量', community_caliber=174)
    assert out.get('ok') is True
    assert out['caliber_lite']['community'] == 154
    assert 'community_warning' in out['caliber_lite']


def test_render_spec_inline_invalid_community_caliber(monkeypatch, tmp_path):
    monkeypatch.setattr(mse, 'REPO', str(tmp_path))
    out = mse.render_spec(kind='choropleth', name='测试', geojson=_small_fc(),
                          community_caliber=999)
    assert out.get('ok') is False
    assert 'K-C1' in out.get('hint', '')


# ════════════ D10：render_client.js 源码分派断言 ════════════

def test_render_client_d10_source_dispatch():
    path = os.path.join(ROOT, 'frontend', 'js', 'render_client.js')
    with open(path, encoding='utf-8') as f:
        src = f.read()
    # 极性分支：同源 piToNorm + polarityStops('overall')
    assert 'piToNorm' in src
    assert "polarityStops('overall')" in src
    # 计数分支：维持 _normCommunityCount + count 着色
    assert '_normCommunityCount' in src
    # PT-CB10 C2-3：断言随 F4 裁决（f75aee58·显式字面量 paint 去 _ui.tool 标记·禁 defaultPaint 借用）
    # 与 C2-3 单源化（归一公式抽 shared.js countNorm）更新——同源判据=归一/色带均引共享函数而非自写公式。
    assert 'countNorm(' in src
    assert 'countStops(' in src
    # 分派条件：polarity 子串或 score_mean
    assert "valueField.includes('polarity')" in src
