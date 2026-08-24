# -*- coding: utf-8 -*-
"""停车泊位缺口点 -> 小区面聚合：找停车位不足的小区 TOP 并出图 geojson。

数据源：
- 点：DATA/boundaries/presets/checkup_qty_民生_停车设施.geojson（274点·3项指标）
- 面：DATA/boundaries/presets/checkup_配置_小区.geojson（1562小区·XQMC）

口径：指标含「缺口」= 停车泊位缺口数（停车位不足）。
"""
import collections
import json
import sys
from pathlib import Path

import geopandas as gpd

BASE = Path(__file__).resolve().parent.parent.parent / "DATA" / "boundaries" / "presets"
OUT_DIR = Path(__file__).resolve().parent

pts = gpd.read_file(BASE / "checkup_qty_民生_停车设施.geojson")
print("[pts]", len(pts), "cols:", list(pts.columns), "crs:", pts.crs)

ind_col = None
for c in pts.columns:
    if c in ("指标", "项目", "项", "indicator"):
        ind_col = c
        break
if ind_col:
    print("[指标 counts]", collections.Counter(pts[ind_col].astype(str).tolist()))
print("[pts sample]", json.dumps(pts.iloc[0].drop("geometry", errors="ignore").to_dict(), ensure_ascii=False, default=str))

# 选「停车泊位缺口」指标（名称含 缺口/泊位）
if ind_col:
    s = pts[ind_col].astype(str)
    gap = pts[s.str.contains("缺口|泊位", na=False)].copy()
else:
    gap = pts.copy()
print("[gap rows]", len(gap))

bld = gpd.read_file(BASE / "checkup_配置_小区.geojson")
print("[bld]", len(bld), "cols:", list(bld.columns), "crs:", bld.crs)

name_col = "XQMC" if "XQMC" in bld.columns else bld.columns[0]
print("[bld sample]", json.dumps(bld.iloc[0].drop("geometry", errors="ignore").to_dict(), ensure_ascii=False, default=str))

if bld.crs is None:
    bld = bld.set_crs("EPSG:4326")
if gap.crs != bld.crs:
    gap = gap.to_crs(bld.crs)

join = gpd.sjoin(gap, bld, how="left", predicate="within")
joined = join[join["index_right"].notna()]
print("[sjoin within matched]", len(joined), "/", len(gap))
if len(joined) < 0.5 * len(gap):
    join2 = gpd.sjoin(gap, bld, how="left", predicate="intersects")
    joined = join2[join2["index_right"].notna()]
    print("[sjoin intersects matched]", len(joined), "/", len(gap))

agg = joined.groupby(name_col).size().reset_index(name="gap_count").sort_values("gap_count", ascending=False)
print("[top by gap_count]")
print(agg.head(25).to_string(index=False))

m = bld.merge(agg, on=name_col, how="inner").sort_values("gap_count", ascending=False)
out = m[[name_col, "gap_count", "geometry"]].copy()
out = out.rename(columns={name_col: "name"})
out["point_count"] = out["gap_count"]
out["indicator"] = "parking_gap"
out = out.to_crs("EPSG:4326")

out_path = OUT_DIR / "停车泊位缺口_小区.geojson"
out.to_file(out_path, driver="GeoJSON", encoding="utf-8")
print("[saved]", out_path, "features:", len(out))
print("[top10]", [(r["name"], r["gap_count"]) for _, r in out.head(10).iterrows()])
