# -*- coding: utf-8 -*-
"""12345 热线 800m 方格网空间聚合（可复现）。

口径：
- 源数据 = DATA/analysis/12345主观/12345_有坐标点.geojson（治理后有坐标点）
- 仅取 geocode_status == 'ok' 的精确坐标点（区级质心 region 点不参与网格聚合）
- 聚合 = core.spatial_analysis.create_square_grid(cell_size=800, unit='m')
  （EPSG:4546 量度 800m，snap-to-grid 仅生成有点的格，结果回 EPSG:4326）

产出：
- DATA/exports/12345_800m方格/12345_800m方格聚合.geojson
- DATA/exports/12345_800m方格/12345_800m方格聚合_统计.csv
- DATA/exports/12345_800m方格/12345_800m方格聚合_分析.md
- DATA/exports/render_inbox/<spec_id>.json（前端 choropleth spec）
"""
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
from shapely.ops import unary_union

from core.spatial_analysis import create_square_grid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBJ = os.path.join(ROOT, "DATA", "analysis", "12345主观")
OUT_DIR = os.path.join(ROOT, "DATA", "exports", "12345_800m方格")
INBOX = os.path.join(ROOT, "DATA", "exports", "render_inbox")
XW = os.path.join(ROOT, "DATA", "analysis", "西陵伍家_合并范围.geojson")
COMM174 = os.path.join(ROOT, "DATA", "boundaries", "presets", "checkup_配置_社区174.geojson")

ASPECTS = ["民生基础", "安全韧性"]
CLASS9 = ["噪声", "住宅", "物业", "停车", "出行", "管网安全", "出行安全", "消防安全", "环境安全", "其他"]
EVENTS = ["投诉", "求助", "建议", "其他"]


def _safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("gbk", "replace").decode("gbk"))


def load_gj(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(INBOX, exist_ok=True)

    # ── 源点：治理后有坐标点，仅精确坐标 ok ──
    src = load_gj(os.path.join(SUBJ, "12345_有坐标点.geojson"))
    feats = [f for f in src["features"] if f["properties"].get("geocode_status") == "ok"]
    pts = gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")
    _safe_print(f"[OK] 12345 ok 精确点 {len(pts)}")

    # ── 800m 方格聚合（核心）──
    grid = create_square_grid(pts, cell_size=800, unit="m")
    _safe_print(f"[OK] 800m 网格数 {len(grid)}，覆盖点数 {int(grid['point_count'].sum())}，最大格 {int(grid['point_count'].max())}")

    # ── 点 → 格归属（用于分类计数）──
    # 与 create_square_grid 内部一致：在 EPSG:4546 米制下做 within，避免回投影后边界点漂移漏配
    _pts_m = pts.to_crs("EPSG:4546")
    _grid_m = grid[["geometry", "cell_id"]].to_crs("EPSG:4546")
    joined = gpd.sjoin(_pts_m, _grid_m, how="left", predicate="within")
    miss = int(joined["cell_id"].isna().sum())
    if miss:
        _safe_print(f"[WARN] {miss} 点未落入网格（不应发生）")
    joined = joined[joined["cell_id"].notna()].copy()

    # 点级区域归属：西陵伍家合并范围 / 174社区范围（EPSG:4546 量度）
    with open(XW, encoding="utf-8") as f:
        xw = json.load(f)
    xw_geom_4326 = unary_union([shape(feature["geometry"]) for feature in xw["features"]])
    xw_geom = gpd.GeoSeries([xw_geom_4326], crs="EPSG:4326").to_crs("EPSG:4546").iloc[0]
    with open(COMM174, encoding="utf-8") as f:
        c174 = json.load(f)
    c174_geom_4326 = unary_union([shape(feature["geometry"]) for feature in c174["features"]])
    c174_geom = gpd.GeoSeries([c174_geom_4326], crs="EPSG:4326").to_crs("EPSG:4546").iloc[0]
    joined["in_xw_pt"] = joined.geometry.within(xw_geom) | joined.geometry.covers(xw_geom)
    joined["in_174_pt"] = joined.geometry.within(c174_geom) | joined.geometry.covers(c174_geom)

    # 方面计数
    asp = joined.groupby("cell_id")["方面"].value_counts().unstack(fill_value=0)
    for c in ASPECTS:
        if c not in asp.columns:
            asp[c] = 0
    asp = asp[ASPECTS].rename(columns={c: f"n_{c}" for c in ASPECTS})

    # 类9计数
    cls = joined.groupby("cell_id")["类9"].value_counts().unstack(fill_value=0)
    for c in CLASS9:
        if c not in cls.columns:
            cls[c] = 0
    cls = cls[CLASS9].rename(columns={c: f"n_{c}" for c in CLASS9})

    # 事件计数（存在才统计；列名用 n_ev_* 避免与类9的 n_其他 冲突）
    ev = None
    if "事件" in joined.columns:
        ev = joined.groupby("cell_id")["事件"].value_counts().unstack(fill_value=0)
        for c in EVENTS:
            if c not in ev.columns:
                ev[c] = 0
        ev = ev[EVENTS].rename(columns={c: f"n_ev_{c}" for c in EVENTS})

    # 主社区（众数）
    if "社区" in joined.columns:
        comm = joined.dropna(subset=["社区"]).groupby("cell_id")["社区"].agg(
            lambda s: s.value_counts().index[0] if len(s) else ""
        ).rename("top_community")
    else:
        comm = pd.Series(dtype=str, name="top_community")

    # 点级区域计数（按格汇总）
    reg = joined.groupby("cell_id")[["in_xw_pt", "in_174_pt"]].sum().astype(int)
    reg = reg.rename(columns={"in_xw_pt": "n_in_xw", "in_174_pt": "n_in_174"})

    # 合并
    grid = grid.merge(asp, left_on="cell_id", right_index=True, how="left")
    grid = grid.merge(cls, left_on="cell_id", right_index=True, how="left")
    if ev is not None:
        grid = grid.merge(ev, left_on="cell_id", right_index=True, how="left")
    if len(comm):
        grid = grid.merge(comm, left_on="cell_id", right_index=True, how="left")
    else:
        grid["top_community"] = ""
    grid = grid.merge(reg, left_on="cell_id", right_index=True, how="left")

    count_cols = (
        [f"n_{c}" for c in ASPECTS]
        + [f"n_{c}" for c in CLASS9]
        + ([f"n_ev_{c}" for c in EVENTS] if ev is not None else [])
        + ["n_in_xw", "n_in_174"]
    )
    for c in count_cols:
        if c not in grid.columns:
            grid[c] = 0
        grid[c] = pd.to_numeric(grid[c], errors="coerce").fillna(0).astype(int)

    # 区域标识：西陵伍家合并范围 / 174社区范围（按格质心）
    with open(XW, encoding="utf-8") as f:
        xw = json.load(f)
    xw_geom = unary_union([shape(feature["geometry"]) for feature in xw["features"]])
    with open(COMM174, encoding="utf-8") as f:
        c174 = json.load(f)
    c174_geom = unary_union([shape(feature["geometry"]) for feature in c174["features"]])
    cents = grid.geometry.centroid
    grid["in_xw"] = cents.within(xw_geom) | cents.covers(xw_geom)
    grid["in_174"] = cents.within(c174_geom) | cents.covers(c174_geom)

    # 主导类9 / 主导方面
    cls_cols = [f"n_{c}" for c in CLASS9]
    grid["top_class9"] = grid[cls_cols].idxmax(axis=1).str.replace("n_", "", regex=False)
    grid["top_class9_count"] = grid[cls_cols].max(axis=1)
    asp_cols = [f"n_{c}" for c in ASPECTS]
    grid["top_aspect"] = grid[asp_cols].idxmax(axis=1).str.replace("n_", "", regex=False)

    # 输出 GeoJSON（保留中文）
    out_gj = os.path.join(OUT_DIR, "12345_800m方格聚合.geojson")
    fc = json.loads(grid.to_json())
    with open(out_gj, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)
    _safe_print(f"[OK] {out_gj}（{len(fc['features'])} 格）")

    # 输出 CSV
    out_csv = os.path.join(OUT_DIR, "12345_800m方格聚合_统计.csv")
    grid.drop(columns=["geometry"]).to_csv(out_csv, index=False, encoding="utf-8-sig")
    _safe_print(f"[OK] {out_csv}")

    # 输出 render_inbox spec（前端 choropleth）
    spec_id = f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
    spec = {
        "spec_version": 1,
        "spec_id": spec_id,
        "kind": "choropleth",
        "data": {"geojson": fc},
        "style": {"scheme": "community_choropleth_v1", "value_field": "point_count"},
        "ui": {"name": "12345热线800m方格聚合（ok精确点）", "zoom_to": True},
        "origin": {"producer": "dsh", "source_tool": "gen_12345_grid_800m"},
        "caliber_lite": {
            "usage": "input",
            "data_nature": "real",
            "note": "12345 2024 ok 精确点 800m 方格聚合（create_square_grid·仅有点的格）",
        },
    }
    spec_path = os.path.join(INBOX, f"{spec_id}.json")
    with open(spec_path, "w", encoding="utf-8", newline="") as f:
        json.dump(spec, f, ensure_ascii=False)
    _safe_print(f"[OK] {spec_path}")

    # ── 统计摘要（供分析 md）──
    summary = {
        "total_points": int(grid["point_count"].sum()),
        "grid_count": int(len(grid)),
        "max_count": int(grid["point_count"].max()),
        "mean_count": round(float(grid["point_count"].mean()), 1),
        "in_xw_grids": int(grid["in_xw"].sum()),
        "in_xw_points": int(grid["n_in_xw"].sum()),
        "in_174_grids": int(grid["in_174"].sum()),
        "in_174_points": int(grid["n_in_174"].sum()),
        "top10": [],
    }
    top10 = grid.nlargest(10, "point_count")
    for _, r in top10.iterrows():
        summary["top10"].append({
            "cell_id": r["cell_id"],
            "point_count": int(r["point_count"]),
            "top_class9": r["top_class9"],
            "top_aspect": r["top_aspect"],
            "top_community": r.get("top_community", ""),
            "in_xw": bool(r["in_xw"]),
            "lon": round(float(r.geometry.centroid.x), 5),
            "lat": round(float(r.geometry.centroid.y), 5),
        })
    summary["class9"] = {c: int(grid[f"n_{c}"].sum()) for c in CLASS9}
    summary["aspect"] = {c: int(grid[f"n_{c}"].sum()) for c in ASPECTS}
    if ev is not None:
        summary["event"] = {c: int(grid[f"n_ev_{c}"].sum()) for c in EVENTS}
    summary_path = os.path.join(OUT_DIR, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    _safe_print(f"[OK] {summary_path}")
    _safe_print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
