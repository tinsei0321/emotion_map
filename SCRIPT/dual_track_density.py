# -*- coding: utf-8 -*-
"""双轨密度完整版：体检全量问题（安全韧性+民生） + 12345 投诉 → 双轨密度面 + 双高区。

管线（CB-23 补强·2026-08-11）：
1. 客观轨·体检全量问题：安全韧性 5 类面（质心化）+ 民生 6 类点 → 合并点 → 1km 网格密度（point_count）
2. 主观轨·12345 投诉：checkup_12345_2024（high+medium 子集·中心城区）→ 1km 网格密度
3. 双轨叠加：两密度面 p75 高格 → 500m buffer 叠加 → 双高区（趋势聚拢核心）
4. 项目聚拢量化：183 项目 → 落双高区比例

用法：py SCRIPT/dual_track_density.py
"""
import json
import os
import sys

import geopandas as gpd
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.spatial_analysis import create_square_grid

ZX = r"D:/OneDrive/2026/15_城市更新专项规划研究/1 宜昌市城市体检/EMC数据中转站"
SPATIAL = os.path.join(ZX, "02_空间数据集")
CELL = 1000  # 1km 网格

# ── 安全韧性 5 类面（质心化·权 1）──
SAFETY_FACES = [
    "存在结构安全隐患的住宅", "存在围护安全隐患的住宅", "存在楼道安全隐患的住宅",
    "存在燃气安全隐患的住宅", "存在管线管道破损的住宅",
]
# ── 民生 6 类点（含缺口数值列）──
LIVELIHOOD_POINTS = [
    ("停车泊位缺口", "停车泊"), ("小学学位缺口", "小学学"), ("新能源汽车充电桩缺口", "新能源"),
    ("未达标配建养老服务设施小区", None), ("未达标配建婴幼儿照护服务设施的小区", None),
    ("未达标配建幼儿园的小区", None),
]


def _centroids(name):
    """面层 → 质心点（EPSG:4546 centroid 防地理CRS警告）。"""
    d = json.load(open(f"{SPATIAL}/住房维度_面层/体检_住房_{name}.geojson", encoding="utf-8"))
    face = gpd.GeoDataFrame.from_features(d["features"], crs="EPSG:4326")
    c = face.copy()
    c.geometry = face.geometry.to_crs("EPSG:4546").centroid.to_crs("EPSG:4326")
    return c


def _points(name, val_col=None):
    """点层 CSV → GeoDataFrame（含缺口数值列·可 sum）。"""
    df = pd.read_csv(f"{SPATIAL}/小区维度_点层/体检_小区_{name}.csv", encoding="utf-8-sig")
    if val_col and val_col in df.columns:
        df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
    df = df.dropna(subset=["lon", "lat"])
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")


def main():
    # ── 1. 客观轨·体检全量问题点 ──
    pts = []
    for name in SAFETY_FACES:
        c = _centroids(name)
        c["_weight"] = 1.0
        pts.append(c[["geometry", "_weight"]])
    for name, vc in LIVELIHOOD_POINTS:
        p = _points(name, vc)
        p["_weight"] = 1.0
        pts.append(p[["geometry", "_weight"]])
    checkup_pts = gpd.GeoDataFrame(pd.concat(pts, ignore_index=True), crs="EPSG:4326")
    print(f"[体检] 全量问题点: {len(checkup_pts)}（安全5面质心 + 民生6点）")

    # 体检密度面（1km 网格）
    g_obj = create_square_grid(checkup_pts, cell_size=CELL, agg_cols=["_weight"])
    print(f"[体检] 1km 网格 {len(g_obj)}·point_count 范围 {g_obj['point_count'].min()}-{g_obj['point_count'].max()}")

    # ── 2. 主观轨·12345 密度 ──
    t = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "DATA", "performance", "checkup_12345_2024.csv"), encoding="utf-8-sig")
    sub = t[(t["region_scope"] == "中心城区") & (t["place_confidence"].isin(["high", "medium"]))].dropna(subset=["lon", "lat"])
    g45 = gpd.GeoDataFrame(sub, geometry=gpd.points_from_xy(sub.lon, sub.lat), crs="EPSG:4326")
    print(f"[12345] 中心城区 high+medium: {len(g45)}")
    g_subj = create_square_grid(g45, cell_size=CELL, agg_cols=["score"])
    print(f"[12345] 1km 网格 {len(g_subj)}·point_count 范围 {g_subj['point_count'].min()}-{g_subj['point_count'].max()}")

    # ── 3. 双轨叠加 → 双高区（两轨均 >p75·500m buffer）──
    obj_high = g_obj[g_obj["point_count"] >= g_obj["point_count"].quantile(0.75)].copy()
    subj_high = g_subj[g_subj["point_count"] >= g_subj["point_count"].quantile(0.75)].copy()
    obj_high.geometry = obj_high.geometry.to_crs("EPSG:4546").centroid.to_crs("EPSG:4326")
    subj_high.geometry = subj_high.geometry.to_crs("EPSG:4546").centroid.to_crs("EPSG:4326")
    subj_buf = gpd.GeoDataFrame(subj_high, geometry=subj_high.geometry.buffer(500))
    dual = gpd.sjoin(obj_high, subj_buf, how="inner", predicate="intersects")
    print(f"[双轨] 体检高格 {len(obj_high)}·12345 高格 {len(subj_high)}·双高格 {len(dual)}")

    # ── 4. 项目聚拢量化（183 项目 → 落双高区比例）──
    from core.range_selector import load_preset
    pp = load_preset("checkup_project_point")["geojson"]
    pl = load_preset("checkup_project_line")["geojson"]
    pt = gpd.GeoDataFrame.from_features(pp["features"], crs="EPSG:4326")
    ln = gpd.GeoDataFrame.from_features(pl["features"], crs="EPSG:4326")
    ln_c = ln.copy()
    ln_c.geometry = ln.geometry.to_crs("EPSG:4546").centroid.to_crs("EPSG:4326")
    proj = gpd.GeoDataFrame(pd.concat([pt[["XMMC", "XZQ", "TZE", "geometry"]], ln_c[["XMMC", "XZQ", "TZE", "geometry"]]]), crs="EPSG:4326")
    proj = proj.drop_duplicates(subset="XMMC")
    # 双高区 union → buffer（投影 4546 buffer 防地理CRS警告）
    dual_gdf = gpd.GeoDataFrame(dual, geometry=dual.geometry, crs="EPSG:4326")
    dual_4546 = dual_gdf.to_crs("EPSG:4546")
    dual_union = dual_4546.dissolve().buffer(500).to_crs("EPSG:4326")
    in_dual = gpd.sjoin(proj, gpd.GeoDataFrame(geometry=dual_union, crs="EPSG:4326"), how="inner", predicate="intersects")
    pct = len(in_dual) / len(proj)
    print(f"[项目] {len(proj)} 项目·落双高区 {len(in_dual)} = {pct:.0%}（双轨双高区=最急难愁盼·项目聚拢核心）")

    # ── 输出摘要 ──
    out = {
        "体检问题点": len(checkup_pts), "体检网格": len(g_obj),
        "12345密度点": len(g45), "12345网格": len(g_subj),
        "体检高格": len(obj_high), "12345高格": len(subj_high),
        "双高格": len(dual),
        "项目数": len(proj), "项目落双高区": len(in_dual),
        "项目落双高区率": round(pct, 3),
    }
    out_path = os.path.join(ZX, "06_主观数据治理", "双轨密度结果.json")
    json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[OK] 结果落 {out_path}")


if __name__ == "__main__":
    main()
