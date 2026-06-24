#!/usr/bin/env python3
"""v3.2 空间生成质量核对 — 落水系 / 网格填充 / 行政区占比 / 带状跨度。
核对四大病灶反面：落水系≈0、伍家>20%、沿江带（lat跨>=lon跨）。"""
import os
import sys
import json

import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import transform as shp_transform
from pyproj import Transformer

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)
from core.utils import safe_print
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

_T = Transformer.from_crs('EPSG:4326', 'EPSG:4546', always_xy=True)
PROC = os.path.join(_ROOT, 'DATA', 'processed')
MAIN = os.path.join(_ROOT, 'DATA', 'boundaries', '西陵伍家核心主城.geojson')
WATER = os.path.join(_ROOT, 'DATA', 'boundaries', '现状水系.geojson')


def grid_stats(pts_lonlat, poly_wgs, cell=100):
    """米制网格统计（仅边界内格）：返回 (max/格, 填充率)。"""
    proj = shp_transform(_T.transform, poly_wgs)
    x, y = _T.transform(pts_lonlat[:, 0], pts_lonlat[:, 1])
    xmin, ymin, xmax, ymax = proj.bounds
    xe = np.arange(xmin, xmax + cell, cell)
    ye = np.arange(ymin, ymax + cell, cell)
    H, _, _ = np.histogram2d(x, y, bins=[xe, ye])
    cx = (xe[:-1] + xe[1:]) / 2
    cy = (ye[:-1] + ye[1:]) / 2
    inside = np.zeros(H.shape, bool)
    for i, ix in enumerate(cx):
        for j, jy in enumerate(cy):
            inside[i, j] = proj.contains(Point(ix, jy))
    H_in = H[inside]
    return H_in.max(), (H_in > 0).mean()


def main():
    poly = gpd.read_file(MAIN).to_crs('EPSG:4326').geometry.union_all()
    water = gpd.read_file(WATER).to_crs('EPSG:4326').geometry.union_all() if os.path.exists(WATER) else None
    safe_print('[BOUNDARY] 主城 {:.2f} km2 | {} | 水系 {}'.format(
        shp_transform(_T.transform, poly).area / 1e6, poly.geom_type,
        '已加载' if water else '缺失'))

    LON_MID = (poly.bounds[0] + poly.bounds[2]) / 2   # 行政区粗分代理
    for sid in ('T1', 'T2', 'T3'):
        f = os.path.join(PROC, 'xiling_wujia_L2_{}_L2_result_geojson.geojson'.format(sid))
        if not os.path.exists(f):
            safe_print('[{}] L2 GeoJSON 不存在'.format(sid))
            continue
        gj = json.load(open(f, encoding='utf-8'))
        arr = np.array([ft['geometry']['coordinates'] for ft in gj['features']])
        lon, lat = arr[:, 0], arr[:, 1]
        for cell in (200, 500):
            mx, fl = grid_stats(arr, poly, cell)
            safe_print('[{}] {}m | {} 点 | 填充 {:.1%} | max/格 {}'.format(
                sid, cell, len(arr), fl, int(mx)))
        in_water = sum(1 for lo, la in zip(lon, lat) if water is not None and water.contains(Point(lo, la)))
        ls, ts = lon.max() - lon.min(), lat.max() - lat.min()
        safe_print('[{}] 形态 | 落水系 {}({:.2%}) | 西陵侧{:.1%} 伍家侧{:.1%} | lon跨{:.3f} lat跨{:.3f} {}'.format(
            sid, in_water, in_water / len(arr), (lon < LON_MID).mean(), (lon >= LON_MID).mean(),
            ls, ts, '(沿江带)' if ts >= ls else '(东西宽)'))


if __name__ == '__main__':
    main()
