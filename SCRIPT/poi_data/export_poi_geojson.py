#!/usr/bin/env py
# -*- coding: utf-8 -*-
"""
导出本地 POI 为 GeoJSON 供肉眼核查位置准确性（Search v2 · item 5）
═══════════════════════════════════════════════════════════
读 place_layer.all_pois（1270 高德 POI，WGS84）+ classify_point 打 zone_id/zone_name
→ DATA/place/pois_wgs84.geojson（Point FeatureCollection，EPSG:4326）。

用户 Import 后可按 zone_id / baidu_level1 配色，核查各"点"位置是否准确（回答
"如何判断地点显示是否准确"——把全部 POI 摊到地图上肉眼对齐底图）。

用法：
    py SCRIPT/poi_data/export_poi_geojson.py
═══════════════════════════════════════════════════════════
"""
import os
import sys
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.place_layer import get_place_layer
from core.utils import safe_print as _safe_print

OUT = os.path.join(_ROOT, 'DATA', 'place', 'pois_wgs84.geojson')


def main():
    pl = get_place_layer()
    feats = []
    for p in pl.all_pois:
        lng, lat = p.get('lng'), p.get('lat')
        if lng is None or lat is None:
            continue
        zid = pl.resolve_zone(p.get('name', ''), p.get('area', ''), lng, lat)   # name 优先（全市型 zone 按名归）→ 边界 → general
        zname = pl.zone_by_id.get(zid, {}).get('name_zh', '')
        feats.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [lng, lat]},
            'properties': {
                'name': p.get('name', ''),
                'zone_id': zid,
                'zone_name': zname,
                'baidu_level1': p.get('baidu_level1', ''),
                'baidu_level2': p.get('baidu_level2', ''),
                'area': p.get('area', ''),
                'source': p.get('source', ''),
                'in_water': bool(p.get('_in_water', False)),
            },
        })
    fc = {'type': 'FeatureCollection', 'features': feats}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(fc, f, ensure_ascii=False, separators=(',', ':'))
    # 按 zone / category 统计，便于用户判断分布
    by_zone = {}
    by_cat = {}
    for ft in feats:
        p = ft['properties']
        by_zone[p['zone_name'] or '(无)'] = by_zone.get(p['zone_name'] or '(无)', 0) + 1
        by_cat[p['baidu_level1'] or '(无)'] = by_cat.get(p['baidu_level1'] or '(无)', 0) + 1
    _n_water = sum(1 for ft in feats if ft['properties']['in_water'])
    _safe_print('[OK] {} POI → {}（其中 {} 落水已标记 in_water）'.format(len(feats), OUT, _n_water))
    _safe_print('[STAT] by zone: ' + ', '.join('{}={}'.format(k, v) for k, v in sorted(by_zone.items(), key=lambda x: -x[1])))
    _safe_print('[STAT] top categories: ' + ', '.join('{}={}'.format(k, v) for k, v in sorted(by_cat.items(), key=lambda x: -x[1])[:6]))


if __name__ == '__main__':
    main()
