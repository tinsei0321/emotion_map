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


def rebalance():
    """v3.3 重平衡核对：二马路占比 / 密度比 / 落水系 / 本地性 / score arc 硬断言。
    根治 v3.2 二马路 28%/47x 失衡的回归守门。"""
    from collections import Counter
    import csv as _csv
    from core.place_layer import get_place_layer
    pl = get_place_layer()
    poly = gpd.read_file(MAIN).to_crs('EPSG:4326').geometry.union_all()
    water = gpd.read_file(WATER).to_crs('EPSG:4326').geometry.union_all() if os.path.exists(WATER) else None
    main_land = shp_transform(_T.transform, poly).area / 1e6

    # 扁平本地性关键词（命中任意 = 本地相关）
    kws = set()
    for zid in pl.zone_by_id:
        pk = pl.place_keywords(zid)
        kws.update(pk.get('place_keywords', [])); kws.update(pk.get('characteristic_keywords', []))
    kws = {k for k in kws if len(k) >= 2}

    ermalu_area = pl.zone_area_km2.get('ermalu_oldstreet') or 0.6
    fails, arc = [], {}
    for sid in ('T1', 'T2', 'T3'):
        f = os.path.join(PROC, 'xiling_wujia_L2_{}_L2_result_geojson.geojson'.format(sid))
        if not os.path.exists(f):
            safe_print('[{}] L2 GeoJSON 不存在，跳过'.format(sid)); continue
        feats = json.load(open(f, encoding='utf-8'))['features']
        n = len(feats)
        arr = np.array([ft['geometry']['coordinates'] for ft in feats])
        zc = Counter(ft['properties'].get('zone', '') for ft in feats)
        ermalu_n = zc.get('ermalu_oldstreet', 0)
        e_share = ermalu_n / n
        density_ratio = ((e_share / ermalu_area) / ((1 - e_share) / (main_land - ermalu_area))) if e_share < 1 else 0
        in_water = sum(1 for lo, la in arr if water is not None and water.contains(Point(lo, la)))
        texts = [ft['properties'].get('text', '') for ft in feats]
        zones = [ft['properties'].get('zone', '') for ft in feats]
        hit = sum(1 for t in texts if any(k in t for k in kws))
        fi = [i for i, z in enumerate(zones) if z and z != 'general']
        fh = sum(1 for i in fi if any(k in texts[i] for k in kws))
        csv_f = os.path.join(PROC, 'xiling_wujia_L2_{}_L2_result_csv.csv'.format(sid))
        sm = None
        if os.path.exists(csv_f):
            ss = [float(r['score']) for r in _csv.DictReader(open(csv_f, encoding='utf-8')) if r.get('score')]
            sm = sum(ss) / len(ss) if ss else None; arc[sid] = sm
        safe_print('[{}] 二马路 {}/{} ({:.0%}) 密度比 {:.0f}x | 落水 {:.1%} | 本地性 {:.0%}(重点 {:.0%}) | score {:.3f}'.format(
            sid, ermalu_n, n, e_share, density_ratio, in_water / n, hit / n, (fh / len(fi) if fi else 0), sm or 0))
        if e_share > 0.20:
            fails.append('{} 二马路占比 {:.0%} > 20%'.format(sid, e_share))
        if density_ratio > 30:
            fails.append('{} 密度比 {:.0f}x > 30'.format(sid, density_ratio))
        if in_water / n > 0.005:
            fails.append('{} 落水 {:.1%} > 0.5%'.format(sid, in_water / n))
        if hit / n < 0.55:
            fails.append('{} 本地性 {:.0%} < 55%'.format(sid, hit / n))

    for sid, (lo, hi) in {'T1': (0.43, 0.48), 'T2': (0.54, 0.59), 'T3': (0.61, 0.65)}.items():
        if sid in arc and not (lo <= arc[sid] <= hi):
            fails.append('{} score {:.3f} 不在 [{},{}]'.format(sid, arc[sid], lo, hi))
    safe_print('\n{}'.format('[OK] v3.3 全部断言通过' if not fails else '[FAIL] ' + ' | '.join(fails)))
    return not fails


if __name__ == '__main__':
    if '--rebalance' in sys.argv:
        sys.exit(0 if rebalance() else 1)
    main()
