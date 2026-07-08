"""GIS 工具箱 /api/v1/geo/* 端点测试（Phase B 验收）。

覆盖 plan 验收项 5 要求的 filter_attr / clip / merge / area_stats / zonal_stats / rank。
依赖真实演示数据（DATA/performance/yichang_L2_* + DATA/boundaries/presets/admin_district）；
数据缺失则整组 skip（CI 无数据环境不报红）。
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app
from core.config import PERFORMANCE_DIR

client = TestClient(app)

_L2 = 'yichang_l2_t1'
_L2_FILE = os.path.join(PERFORMANCE_DIR, 'yichang_L2_T1_L2_result_csv.csv')

# 整组依赖真实数据；缺失即 skip
pytestmark = pytest.mark.skipif(
    not os.path.isfile(_L2_FILE),
    reason='演示数据 yichang_L2_T1 不存在',
)


def _boundary_available(bid: str) -> bool:
    r = client.get('/api/v1/geo/catalog')
    if r.status_code != 200:
        return False
    return any(b['id'] == bid and b['available'] for b in r.json().get('boundaries', []))


def test_catalog_lists_layers_boundaries_tools():
    r = client.get('/api/v1/geo/catalog')
    assert r.status_code == 200
    d = r.json()
    assert any(l['id'] == _L2 and l['available'] for l in d['point_layers'])
    assert len(d['tools']) >= 10          # 10 个 GIS 原子操作
    tool_names = {t['name'] for t in d['tools']}
    assert {'zonal_stats', 'clip', 'filter_attr', 'area_stats', 'merge'} <= tool_names


def test_zonal_stats_returns_sorted_units_with_attribution():
    """验收核心：按行政区聚合 → 排序 + 4×5 归因（宏观结论主干）。"""
    if not _boundary_available('admin_district'):
        pytest.skip('admin_district preset 不可用')
    r = client.post('/api/v1/geo/zonal_stats',
                    json={'layer': _L2, 'boundary': 'admin_district', 'top_n': 5})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['count'] <= 5
    assert d['sort_by'] in ('polarity_index', 'point_count')
    assert d['rows'], '应至少返回一个单元'
    row = d['rows'][0]
    for k in ('name', 'polarity_index', 'point_count', 'domain_top'):
        assert k in row
    # |pi| 应降序（张力大的在前）
    pis = [abs(rw['polarity_index']) for rw in d['rows'] if rw.get('polarity_index') is not None]
    assert pis == sorted(pis, reverse=True)


def test_clip_filters_points_within_range():
    if not _boundary_available('admin_district'):
        pytest.skip('admin_district preset 不可用')
    r = client.post('/api/v1/geo/clip', json={'layer': _L2, 'range': 'admin_district'})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['count'] > 0
    assert 0 < d['count'] < 20000         # 裁剪后应少于全量


def test_filter_attr_by_domain():
    r = client.post('/api/v1/geo/filter_attr',
                    json={'layer': _L2,
                          'pre_filter': {'field': 'domain', 'op': 'eq', 'value': 'urban_governance'}})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['count'] > 0


def test_area_stats_returns_shares():
    if not _boundary_available('admin_district'):
        pytest.skip('admin_district preset 不可用')
    r = client.post('/api/v1/geo/area_stats',
                    json={'boundary': 'admin_district', 'group_by': 'name'})
    assert r.status_code == 200, r.text
    rows = r.json()['rows']
    assert rows
    shares = [rw['share'] for rw in rows if rw.get('share') is not None]
    assert 0.9 < sum(shares) <= 1.0 + 1e-6   # 占比和≈1


def test_merge_dissolves_all():
    if not _boundary_available('admin_district'):
        pytest.skip('admin_district preset 不可用')
    r = client.post('/api/v1/geo/merge', json={'boundary': 'admin_district'})   # by 空=unary_union
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['count'] >= 1
    feat0 = d['geojson']['features'][0]
    assert 'area_km2' in feat0['properties']


def test_rank_worst_via_boundary():
    if not _boundary_available('admin_district'):
        pytest.skip('admin_district preset 不可用')
    r = client.post('/api/v1/geo/rank',
                    json={'layer': _L2, 'boundary': 'admin_district', 'by': 'worst', 'top_n': 3})
    assert r.status_code == 200, r.text
    rows = r.json()['rows']
    assert len(rows) <= 3
    pis = [rw['polarity_index'] for rw in rows if rw.get('polarity_index') is not None]
    assert pis == sorted(pis)                # worst=最负在前（升序）


def test_zonal_stats_pre_filter_combines():
    """复合入参：范围内 + 属性切片 一次完成（避免大数据中转）。"""
    if not _boundary_available('admin_district'):
        pytest.skip('admin_district preset 不可用')
    r = client.post('/api/v1/geo/zonal_stats', json={
        'layer': _L2, 'boundary': 'admin_district', 'range': 'admin_district',
        'pre_filter': {'field': 'domain', 'op': 'eq', 'value': 'urban_renewal'},
        'top_n': 3,
    })
    assert r.status_code == 200, r.text
    rows = r.json()['rows']
    if rows:
        # 过滤后只剩 renewal 域，domain_top 应为 renewal（或空）
        assert all(rw.get('domain_top') in ('urban_renewal', '', None) for rw in rows)
