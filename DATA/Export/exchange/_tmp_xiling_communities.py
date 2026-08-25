# -*- coding: utf-8 -*-
"""临时脚本：判定 174 社区中哪些属于西陵区（质心/代表点落在西陵区面内）。"""
import json
from shapely.geometry import shape

COUNTY = r"D:\Github\emotion_map\DATA\boundaries\presets\admin_county_official.geojson"
COMM = r"D:\Github\emotion_map\DATA\boundaries\presets\checkup_配置_社区.geojson"

with open(COUNTY, encoding="utf-8") as f:
    counties = json.load(f)
xiling = None
for feat in counties["features"]:
    if feat["properties"].get("MC") == "西陵区":
        xiling = shape(feat["geometry"])
if xiling is None:
    print("[ERR] 西陵区 not found")
    raise SystemExit(1)
print("[OK] xiling area (m2, 4326 degrees approx):", xiling.area)

with open(COMM, encoding="utf-8") as f:
    comms = json.load(f)

inside, outside = [], []
for feat in comms["features"]:
    name = feat["properties"].get("社区")
    geom = shape(feat["geometry"])
    # 代表点法 + 交集面积占比法双判
    rep = geom.representative_point()
    inter = geom.intersection(xiling)
    share = inter.area / geom.area if geom.area > 0 else 0.0
    if rep.within(xiling) or share >= 0.5:
        inside.append((name, round(share, 3)))
    else:
        outside.append((name, round(share, 3)))

print("total communities:", len(comms["features"]))
print("xiling inside count:", len(inside))
inside.sort(key=lambda t: -t[1])
print("--- inside ---")
for n, s in inside:
    print(n, s)
print("--- outside (share>0.2) ---")
for n, s in outside:
    if s > 0.2:
        print(n, s)
