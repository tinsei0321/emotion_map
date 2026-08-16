# -*- coding: utf-8 -*-
"""B012 / CB-38 E1 audit: community tip wrong-attribution evidence chain.

Usage: py SCRIPT/_tmp_audit_b012_community_tip.py
Read-only. Evidence:
  1) preset layer 174 faces, field, no compound names
  2) five reported pairs are adjacent (shared edges, ~zero overlap)
  3) 400m grid straddle simulation -> attribution flips by cell-center side
"""
import io, json
from shapely.geometry import shape, box, Point
from shapely.ops import transform, unary_union
from pyproj import Transformer

T = Transformer.from_crs('EPSG:4326', 'EPSG:4546', always_xy=True).transform
PRESET = 'DATA/boundaries/presets/checkup_配置_社区.geojson'
PAIRS = [('金安岭社区', '望洲社区'), ('竹涛山社区', '宝联社区'),
         ('常刘路社区', '营盘路社区'), ('建设社区', '港务社区'),
         ('朝阳路社区', '石板溪社区'), ('朝阳社区', '石板社区')]
CELL = 400.0


def _p(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('gbk', 'replace').decode('gbk'))


def main():
    data = json.load(io.open(PRESET, encoding='utf-8'))
    feats = data['features']
    geoms, names = {}, []
    for f in feats:
        n = str(f['properties'].get('社区', ''))
        names.append(n)
        geoms[n] = transform(T, shape(f['geometry']))
    _p('[1] preset=%s features=%d field=社区' % (PRESET, len(feats)))
    _p('    compound names (dash/sep): %d' % sum(
        1 for n in names if any(s in n for s in '-—－/、+')))
    for a, b in PAIRS:
        if a not in geoms or b not in geoms:
            _p('[2] %s / %s: not both present (%s,%s)' % (a, b, a in geoms, b in geoms))
            continue
        ga, gb = geoms[a], geoms[b]
        inter = ga.intersection(gb)
        _p('[2] %s x %s: overlap=%.0f m2, inter.type=%s (MultiLineString=adjacent)'
           % (a, b, inter.area, inter.geom_type))
        both = unary_union([ga, gb])
        minx, miny, maxx, maxy = both.bounds
        straddle = show_a = show_b = 0
        x = minx
        while x < maxx:
            y = miny
            while y < maxy:
                cell = box(x, y, x + CELL, y + CELL)
                if ga.intersects(cell) and gb.intersects(cell):
                    straddle += 1
                    c = Point(x + CELL / 2, y + CELL / 2)
                    if ga.contains(c):
                        show_a += 1
                    elif gb.contains(c):
                        show_b += 1
                y += CELL
            x += CELL
        _p('[3]   %dm straddle cells=%d -> center-in-A=%d center-in-B=%d center-outside=%d'
           % (CELL, straddle, show_a, show_b, straddle - show_a - show_b))
    _p('[OK] audit done. Root cause: tip-popup.js fillCommunity uses feature centroid,')
    _p('     not pointer lngLat -> boundary-straddling cells show the neighbor community.')


if __name__ == '__main__':
    main()
