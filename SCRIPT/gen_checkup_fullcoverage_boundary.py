# -*- coding: utf-8 -*-
"""生成城市体检全覆盖范围面：174 社区合并成单一面（dissolve·无社区间分界线）。
输出：DATA/analysis/77项量化/体检全覆盖范围_174社区合并面.geojson
处理：微缝隙填充（interiors <1000m² 剔除）·MultiPolygon 保留为单要素。
"""
import json
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from shapely.geometry import shape, mapping, MultiPolygon, Polygon
from shapely.ops import unary_union, transform
import pyproj

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "DATA", "boundaries", "presets", "checkup_配置_社区174.geojson")
OUT = os.path.join(ROOT, "DATA", "analysis", "77项量化", "体检全覆盖范围_174社区合并面.geojson")

with open(SRC, encoding="utf-8") as f:
    d = json.load(f)
geoms = [shape(x["geometry"]) for x in d["features"]]
print(f"输入: {len(geoms)} 社区面")

merged = unary_union(geoms)

# 统一清理阈值：5,000 m²（微缝洞填充 + 尘埃部分剔除·显示干净）
THRESH_M2 = 5000


def fill_small_holes(g):
    if isinstance(g, MultiPolygon):
        return MultiPolygon([fill_small_holes(p) for p in g.geoms])
    if not g.interiors:
        return g
    tr = pyproj.Transformer.from_crs(4326, 4546, always_xy=True).transform
    new_interiors = []
    for r in g.interiors:
        hole_m = transform(tr, Polygon(r))
        if hole_m.area >= THRESH_M2:
            new_interiors.append(r)
    if len(new_interiors) != len(g.interiors):
        return Polygon(g.exterior, new_interiors)
    return g


n_interiors_before = len(merged.interiors) if merged.geom_type == "Polygon" else sum(len(p.interiors) for p in merged.geoms)
merged2 = fill_small_holes(merged)
n_interiors_after = len(merged2.interiors) if merged2.geom_type == "Polygon" else sum(len(p.interiors) for p in merged2.geoms)

# 尘埃部分剔除（<5,000 m²·合计 <0.01% 领土·纯显示清理）
tr_f = pyproj.Transformer.from_crs(4326, 4546, always_xy=True).transform
if isinstance(merged2, MultiPolygon):
    kept = [p for p in merged2.geoms if transform(tr_f, p).area >= THRESH_M2]
    dropped = len(merged2.geoms) - len(kept)
    merged2 = kept[0] if len(kept) == 1 else MultiPolygon(kept)
    print(f"尘埃部分剔除: {dropped} 个（<{THRESH_M2} m²）")

n_parts = 1 if merged2.geom_type == "Polygon" else len(merged2.geoms)
print(f"合并后: {merged2.geom_type}·{n_parts} 部分（跨长江两岸为多部分属正常）")
print(f"内部洞: {n_interiors_before} → {n_interiors_after}（<1000m² 微缝已填）")

# 面积（4546 投影·km²）
tr = pyproj.Transformer.from_crs(4326, 4546, always_xy=True).transform
area_km2 = transform(tr, merged2).area / 1e6

feat = {
    "type": "Feature",
    "properties": {
        "名称": "城市体检全覆盖范围",
        "社区数": 174,
        "构成": "西陵+伍家岗(2025) + 夷陵/点军/猇亭(2026补充)",
        "面积_km2": round(area_km2, 2),
        "说明": "174社区dissolve合并·无社区间分界线·内部微缝已填充",
    },
    "geometry": mapping(merged2),
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"type": "FeatureCollection", "features": [feat]}, f, ensure_ascii=False)
print(f"[OK] 已写: {OUT}（面积 {area_km2:.2f} km²）")
