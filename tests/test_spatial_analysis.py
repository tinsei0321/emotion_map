"""空间聚合分析测试 — 方格/六边形网格 + 面域聚合 + API 端点（P0 后端地基）。

覆盖：
  - create_square_grid（固定方格，F_006）：结构/计数/CRS/极性指数/格大小反比/非法入参。
  - create_hex_grid（H3）：h3 已装时的基本聚合。
  - aggregate_by_polygons（指定单元）：点×面域 → 每面统计。
  - /api/v1/spatial/aggregate + /spatial/grid 端点（FastAPI TestClient）。
"""
import json
import random

import pytest
import geopandas as gpd
from shapely.geometry import Point, box

from core.spatial_analysis import (
    create_square_grid, create_hex_grid, aggregate_by_polygons,
    aggregate_by_boundary_id,
)


POL5 = ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']


# ── 合成数据 ──

def _synth_points(n=100, seed=42):
    """合成 n 个情绪点 GeoDataFrame（宜昌附近 WGS84，带 score/polarity）。"""
    random.seed(seed)
    rows = [{
        'geometry': Point(111.20 + random.random() * 0.10,
                          30.65 + random.random() * 0.10),
        'score': round(random.random(), 3),
        'polarity': random.choice(POL5),
    } for _ in range(n)]
    return gpd.GeoDataFrame(rows, crs='EPSG:4326')


def _synth_points_fc(n=100, seed=42):
    """合成 GeoJSON FeatureCollection（端点测试用）。"""
    return json.loads(_synth_points(n, seed).to_json())


def _two_polys_fc():
    """两个面域（西/东区）覆盖点 bbox，带 name 列。"""
    gdf = gpd.GeoDataFrame(
        {'name': ['西区', '东区']},
        geometry=[box(111.20, 30.65, 111.25, 30.75),
                  box(111.25, 30.65, 111.30, 30.75)],
        crs='EPSG:4326',
    )
    return json.loads(gdf.to_json())


# ═══ create_square_grid ═══

def test_create_square_grid_basic():
    grid = create_square_grid(_synth_points(100), cell_size=200, unit='m')
    assert len(grid) > 0
    assert grid.crs.to_string() == 'EPSG:4326'
    assert (grid.geometry.geom_type == 'Polygon').all()
    for col in ['point_count', 'score_mean', 'polarity_index',
                'n_very_positive', 'n_very_negative']:
        assert col in grid.columns
    assert int(grid['point_count'].sum()) == 100            # 所有点都被分配
    assert grid['polarity_index'].between(-2, 2).all()


def test_create_square_grid_cell_size_inverse():
    """格越大 → 格数越少。"""
    pts = _synth_points(100)
    assert len(create_square_grid(pts, cell_size=1, unit='km')) \
        < len(create_square_grid(pts, cell_size=200, unit='m'))


def test_create_square_grid_km_unit():
    grid = create_square_grid(_synth_points(50), cell_size=1, unit='km')
    assert len(grid) > 0
    assert int(grid['point_count'].sum()) == 50


def test_create_square_grid_invalid_size():
    with pytest.raises(ValueError):
        create_square_grid(_synth_points(10), cell_size=0)


# ═══ create_hex_grid（h3 已装）═══

def test_create_hex_grid_basic():
    grid = create_hex_grid(_synth_points(100), resolution=9)
    assert len(grid) > 0
    assert grid.crs.to_string() == 'EPSG:4326'
    assert (grid.geometry.geom_type == 'Polygon').all()
    assert 'point_count' in grid.columns
    assert int(grid['point_count'].sum()) == 100


# ═══ aggregate_by_polygons ═══

def test_aggregate_by_polygons_smoke():
    pts = _synth_points(100)
    polys = gpd.GeoDataFrame(
        {'name': ['西区', '东区']},
        geometry=[box(111.20, 30.65, 111.25, 30.75),
                  box(111.25, 30.65, 111.30, 30.75)],
        crs='EPSG:4326',
    )
    merged = aggregate_by_polygons(pts, polys, polygon_name_col='name')
    assert len(merged) == 2
    assert int(merged['point_count'].sum()) > 0
    assert merged['polarity_index'].between(-2, 2).all()
    assert 'name' in merged.columns


# ═══ aggregate_by_boundary_id（⑤③ membership 分组·非 sjoin）════

def test_aggregate_by_boundary_id_smoke():
    """⑤③：点带 zone role(area_tag) → 直接 groupby 出每区 stats + 4×5 归因；无列 raises。"""
    pts = _synth_points(60).copy()
    pts['area_tag'] = (['A'] * 40 + ['B'] * 20)   # 60 点归属两区
    pts['domain'] = (['urban_operation'] * 30 + ['urban_renewal'] * 30)   # 验 _attach_4x5_attrs 复用
    r = aggregate_by_boundary_id(pts)
    assert len(r) == 2
    assert set(r['zone']) == {'A', 'B'}
    assert int(r['point_count'].sum()) == 60
    assert r['score_mean'].between(0, 1).all()
    assert r['polarity_index'].between(-2, 2).all()
    assert 'domain_top' in r.columns          # _attach_4x5_attrs 复用生效
    assert r['domain_top'].isin(['urban_operation', 'urban_renewal']).all()
    # 无 zone role 列 → raises（graceful）
    with pytest.raises(ValueError):
        aggregate_by_boundary_id(_synth_points(10))


# ═══ API 端点（TestClient）═══

def _client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


def test_aggregate_endpoint():
    c = _client()
    r = c.post('/api/v1/spatial/aggregate', json={
        'points_geojson': _synth_points_fc(100),
        'polygons_geojson': _two_polys_fc(),
        'name_col': 'name',
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['success'] is True
    assert body['feature_count'] == 2
    assert body['geojson']['type'] == 'FeatureCollection'
    props = body['geojson']['features'][0]['properties']
    assert 'point_count' in props and 'polarity_index' in props


def test_grid_endpoint_square():
    c = _client()
    r = c.post('/api/v1/spatial/grid', json={
        'geojson': _synth_points_fc(100),
        'grid_type': 'square', 'cell_size': 200, 'unit': 'm',
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['success'] is True
    assert body['feature_count'] > 0
    props = body['geojson']['features'][0]['properties']
    assert 'point_count' in props and 'score_mean' in props


def test_grid_endpoint_hex():
    c = _client()
    r = c.post('/api/v1/spatial/grid', json={
        'geojson': _synth_points_fc(100),
        'grid_type': 'hex', 'resolution': 9,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['success'] is True
    assert body['feature_count'] > 0


def test_grid_endpoint_bad_type():
    c = _client()
    r = c.post('/api/v1/spatial/grid', json={
        'geojson': _synth_points_fc(10),
        'grid_type': 'triangle',
    })
    assert r.status_code == 400


# ═══════ CB-16 Wave 2 / CB-15 数据认知（P0·下钻链最小闭环）═══════

def _client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


def test_place_layer_3220_integrated():
    """P0·3220 POI 接入：place_layer.all_pois 含 3220（合并后 ~4310·去重）·reverse 覆盖扩大。

    CB-16 Wave 2 两组 P0 阻塞修正：place_layer 原只读 SCRIPT/poi_data 四文件（1270+7）·
    不读 DATA/POI/yichang_pois_wgs84.geojson（3220 FC·geometry 坐标）→ 加 _read_pois_geojson 适配层。
    """
    from core.place_layer import get_place_layer
    pl = get_place_layer()
    assert pl is not None
    assert len(pl.yichang_pois) == 3220, f'yichang_pois 应 3220（实际 {len(pl.yichang_pois)}）'
    # 合并后 all_pois = 1270 + 7 + 3220 - 去重（1270/3220 同源 poi_id 重叠）
    assert len(pl.all_pois) >= 3000, f'all_pois 应 ≥3000（含 3220 接入·实际 {len(pl.all_pois)}）'
    # 3220 字段映射（geometry→lng/lat·category→baidu_level1）
    yp = pl.yichang_pois[0]
    assert abs(yp['lng']) > 100, f'3220 lng 应从 geometry 提取（实际 {yp["lng"]}）'
    assert isinstance(yp.get('baidu_level1'), str)
    # reverse 覆盖扩大（西陵区中心·poi_count > 0）
    r = pl.reverse(111.286, 30.708)
    assert (r.get('poi_count') or 0) > 0, f'reverse 应命中 POI（poi_count={r.get("poi_count")}）'


def test_grid_pois_endpoint_centroid():
    """③·grid_pois 端点（质心坐标 + cell_size）→ 格内 POI 清单。"""
    c = _client()
    r = c.post('/api/v1/geo/grid_pois', json={'cell_lng': 111.286, 'cell_lat': 30.708, 'cell_size': 200})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['success'] is True
    assert body['cell_id'] and body['cell_id'].startswith('grid_200_'), f'cell_id 确定性（{body["cell_id"]}）'
    assert isinstance(body['pois'], list) and body['count'] == len(body['pois'])
    if body['pois']:
        p = body['pois'][0]
        for k in ('name', 'category', 'lng', 'lat'):
            assert k in p, f'POI 缺字段 {k}（{p}）'


def test_grid_pois_endpoint_cell_id():
    """③·grid_pois 端点（cell_id 复用·确定性一致）。"""
    c = _client()
    r1 = c.post('/api/v1/geo/grid_pois', json={'cell_lng': 111.286, 'cell_lat': 30.708, 'cell_size': 200})
    cid = r1.json()['cell_id']
    r2 = c.post('/api/v1/geo/grid_pois', json={'cell_id': cid})
    assert r2.status_code == 200, r2.text
    assert r2.json()['count'] == r1.json()['count'], 'cell_id 路径应复用同一格·POI 数一致'


def test_grid_pois_endpoint_requires_param():
    """③·grid_pois 缺参数 → 400。"""
    c = _client()
    r = c.post('/api/v1/geo/grid_pois', json={})
    assert r.status_code == 400


def test_aggregate_poi_attrs_polygon():
    """①·aggregate_by_polygons 产物含 poi_names/poi_count（polygon 模式·POI top_places 增强）。"""
    # 宜昌附近合成点 + 单面覆盖
    pts = _synth_points(60)
    poly = gpd.GeoDataFrame(
        {'name': ['测试区']}, geometry=[box(111.20, 30.65, 111.30, 30.75)], crs='EPSG:4326')
    merged = aggregate_by_polygons(pts, poly, agg_cols=['score'], polygon_name_col='name')
    assert 'poi_names' in merged.columns or 'place_name_source' in merged.columns, \
        f'聚合应含 POI 属性列（{list(merged.columns)}）'
