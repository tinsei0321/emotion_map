# -*- coding: utf-8 -*-
"""CB-41 B013 后端语义锚：无极性点层面域聚合——不产 polarity_index、point_count 正确。

前端按 rows 是否含 polarity_index 分叉「点数/极性」着色（grid-tool gridStyle semantic /
toolbox buildZonalFc+defaultPaint semantic）。本测锁后端契约：L0 无极性聚合输出只有计数，
永不出假极性列（否则前端自动分叉失准·B013 复发）。合成数据·无外部依赖。
"""
import os
import sys

import geopandas as gpd
import pytest
from shapely.geometry import Point, box

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.spatial_analysis import aggregate_by_polygons


def _pts():
    return gpd.GeoDataFrame(
        {'v': [1, 2, 3]},
        geometry=[Point(0.1, 0.1), Point(0.2, 0.2), Point(0.8, 0.8)],
        crs='EPSG:4326',
    )


def _polys():
    return gpd.GeoDataFrame(
        {'name': ['A', 'B']},
        geometry=[box(0, 0, 0.5, 0.5), box(0.6, 0.6, 1, 1)],
        crs='EPSG:4326',
    )


def test_no_polarity_returns_count_only():
    """无极性列 → 输出无 polarity_index（前端 count 分叉依据）·point_count 归面正确。"""
    merged = aggregate_by_polygons(_pts(), _polys(), agg_cols=[], polygon_name_col='name')
    assert 'polarity_index' not in merged.columns
    by_name = merged.set_index('name')
    assert int(by_name.loc['A', 'point_count']) == 2
    assert int(by_name.loc['B', 'point_count']) == 1


def test_zero_polygon_count_filled_zero():
    """无点面域 → point_count=0（int·非 NaN）——前端零点不填色（zeroIsNoData）的数据前提。"""
    polys = gpd.GeoDataFrame(
        {'name': ['A', 'EMPTY']},
        geometry=[box(0, 0, 0.5, 0.5), box(2, 2, 3, 3)],
        crs='EPSG:4326',
    )
    merged = aggregate_by_polygons(_pts(), polys, agg_cols=[], polygon_name_col='name')
    by_name = merged.set_index('name')
    assert int(by_name.loc['EMPTY', 'point_count']) == 0
    assert int(by_name.loc['A', 'point_count']) == 2


def test_with_polarity_still_produces_index():
    """有极性列 → polarity_index 照常产出（L2 极性轨零回归·边界验证）。"""
    pts = gpd.GeoDataFrame(
        {'polarity': ['positive', 'negative']},
        geometry=[Point(0.1, 0.1), Point(0.2, 0.2)],
        crs='EPSG:4326',
    )
    merged = aggregate_by_polygons(pts, _polys(), agg_cols=[], polygon_name_col='name')
    assert 'polarity_index' in merged.columns
    assert float(merged.set_index('name').loc['A', 'polarity_index']) == 0.0  # (1-1)/2


# ── CB-41 B014：membership 值匹配混合策略（空值回退 sjoin·区级质心点丢弃）──

def _polys_named():
    return gpd.GeoDataFrame(
        {'社区': ['A社区', 'B社区']},
        geometry=[box(0, 0, 0.5, 0.5), box(0.6, 0.6, 1, 1)],
        crs='EPSG:4326',
    )


def test_membership_null_falls_back_to_sjoin():
    """membership 列存在但值缺失（异构属性 NaN）→ 几何 sjoin 回退，不得静默丢点（B014 主断言）。"""
    pts = gpd.GeoDataFrame(
        {'社区': ['A社区', None, 'B社区']},   # 第 2 点几何在 A 内但 membership 空
        geometry=[Point(0.1, 0.1), Point(0.2, 0.2), Point(0.8, 0.8)],
        crs='EPSG:4326',
    )
    merged = aggregate_by_polygons(pts, _polys_named(), agg_cols=[], polygon_name_col=None)
    by = merged.set_index('社区')
    assert int(by.loc['A社区', 'point_count']) == 2   # 值匹配 1 + 空值 sjoin 回退 1
    assert int(by.loc['B社区', 'point_count']) == 1


def test_membership_value_wins_over_geometry():
    """membership 有值 → 值匹配优先于几何（CB-23 语义不变：区级质心点不误配）。"""
    pts = gpd.GeoDataFrame(
        {'社区': ['A社区']},                       # 几何落在 B 面内·但值声明 A
        geometry=[Point(0.8, 0.8)],
        crs='EPSG:4326',
    )
    merged = aggregate_by_polygons(pts, _polys_named(), agg_cols=[], polygon_name_col=None)
    by = merged.set_index('社区')
    assert int(by.loc['A社区', 'point_count']) == 1
    assert int(by.loc['B社区', 'point_count']) == 0


def test_membership_null_region_point_dropped():
    """membership 空 + geocode_status=region → 丢弃（质心坐标无定位意义·CB-23 保护延续）。"""
    pts = gpd.GeoDataFrame(
        {'社区': [None, None], 'geocode_status': ['region', 'ok']},
        geometry=[Point(0.1, 0.1), Point(0.2, 0.2)],
        crs='EPSG:4326',
    )
    merged = aggregate_by_polygons(pts, _polys_named(), agg_cols=[], polygon_name_col=None)
    by = merged.set_index('社区')
    assert int(by.loc['A社区', 'point_count']) == 1   # 仅 ok 点计入；region 点被丢弃
    assert int(merged.point_count.sum()) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-q'])
