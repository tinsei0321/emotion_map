# -*- coding: utf-8 -*-
"""12345 热线方格网空间聚合（PT-CB7 T8 参数化模板·可复现）。

用法：
  py SCRIPT/gen_12345_grid_800m.py                       # 默认口径=原 800m 复现
  py SCRIPT/gen_12345_grid_800m.py --grid-size 500       # 改格尺寸
  py SCRIPT/gen_12345_grid_800m.py --source <geojson>    # 换源数据（须含 geocode_status）
  py SCRIPT/gen_12345_grid_800m.py --region-caliber xw_174 --out-dir <dir>

口径（默认）：
- 源数据 = DATA/analysis/12345主观/12345_有坐标点.geojson（治理后有坐标点）
- 仅取 geocode_status == 'ok' 的精确坐标点（区级质心 region 点不参与网格聚合）
- 聚合 = core.spatial_analysis.create_square_grid(cell_size=<grid_size>, unit='m')
  （EPSG:4546 量度，snap-to-grid 仅生成有点的格，结果回 EPSG:4326）
- region_caliber：xw_174（默认·西陵伍家+174社区双范围）/ none（不做区域统计）

产出（默认落 DATA/exports/12345_<N>m方格/）：
- 12345_<N>m方格聚合.geojson / _统计.csv / summary.json（含 caliber_compare 口径对照段）
- render_inbox/<spec_id>.json（前端 choropleth spec·重跑前先自清本脚本旧 spec）

输出 schema 清理（PT-CB7 T8）：core.create_square_grid 会自附 poi_names/place_name 等
下钻链字段（CB-16 Wave 2 有意设计），本脚本输出前删除（12345 交付不需要），
其出处在口径对照段声明；render_inbox spec 用裁剪后的 fc。
"""
import argparse
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
DEFAULT_SOURCE = os.path.join(ROOT, "DATA", "analysis", "12345主观", "12345_有坐标点.geojson")
INBOX = os.path.join(ROOT, "DATA", "exports", "render_inbox")
XW = os.path.join(ROOT, "DATA", "analysis", "西陵伍家_合并范围.geojson")
COMM174 = os.path.join(ROOT, "DATA", "boundaries", "presets", "checkup_配置_社区174.geojson")
SPEC_SOURCE_TOOL = "gen_12345_grid_800m"   # 同时作 render_inbox 自清标记

# core.create_square_grid 自附的下钻链字段（CB-16 Wave 2）——本交付不需要·输出前删除
_CORE_DROP_COLS = ["poi_names", "poi_count", "place_name", "place_name_source",
                   "topic_top"]

# 口径对照锚点（只读引用 _口径注册表.md·禁改卡 ID 体系）：
#   K-01 12345 管理口径（市域全量 42,871）· K-02 board 双口径（全量 49,192/8,046）
FULL_COUNT_K01 = 42871
FULL_COUNT_K02 = 49192

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


def _clean_inbox_specs():
    """PT-CB7 T8：重跑前删除本脚本产生的旧 render_inbox spec（治多 spec 残留·CB 评估 R2）。"""
    removed = 0
    for fn in os.listdir(INBOX) if os.path.isdir(INBOX) else []:
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(INBOX, fn), encoding="utf-8") as fh:
                spec = json.load(fh)
        except (OSError, ValueError):
            continue
        if (spec.get("origin") or {}).get("source_tool") == SPEC_SOURCE_TOOL:
            os.remove(os.path.join(INBOX, fn))
            removed += 1
    if removed:
        _safe_print(f"[OK] render_inbox 自清旧 spec {removed} 份")


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="12345 热线方格网聚合（参数化模板）")
    ap.add_argument("--grid-size", type=int, default=800, help="方格边长（米·默认 800）")
    ap.add_argument("--source", default=DEFAULT_SOURCE,
                    help="源点 geojson 路径（须含 geocode_status 字段）")
    ap.add_argument("--region-caliber", choices=["xw_174", "none"], default="xw_174",
                    help="区域统计口径：xw_174=西陵伍家+174社区（默认）/ none=不做")
    ap.add_argument("--out-dir", default="",
                    help="输出目录（默认 DATA/exports/12345_<N>m方格）")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    n = args.grid_size
    out_dir = args.out_dir or os.path.join(ROOT, "DATA", "exports", f"12345_{n}m方格")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(INBOX, exist_ok=True)

    # ── 源点：治理后有坐标点，仅精确坐标 ok ──
    src = load_gj(args.source)
    feats = [f for f in src["features"] if f["properties"].get("geocode_status") == "ok"]
    pts = gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")
    src_total = len(src["features"])
    _safe_print(f"[OK] 12345 ok 精确点 {len(pts)}（源含坐标点总数 {src_total}）")

    # ── Nm 方格聚合（核心）──
    grid = create_square_grid(pts, cell_size=n, unit="m")
    _safe_print(f"[OK] {n}m 网格数 {len(grid)}，覆盖点数 {int(grid['point_count'].sum())}，最大格 {int(grid['point_count'].max())}")

    # ── 点 → 格归属（用于分类计数）──
    # 与 create_square_grid 内部一致：在 EPSG:4546 米制下做 within，避免回投影后边界点漂移漏配
    _pts_m = pts.to_crs("EPSG:4546")
    _grid_m = grid[["geometry", "cell_id"]].to_crs("EPSG:4546")
    joined = gpd.sjoin(_pts_m, _grid_m, how="left", predicate="within")
    miss = int(joined["cell_id"].isna().sum())
    if miss:
        _safe_print(f"[WARN] {miss} 点未落入网格（不应发生）")
    joined = joined[joined["cell_id"].notna()].copy()

    # 点级区域归属：西陵伍家合并范围 / 174社区范围（EPSG:4546 量度·region-caliber 可选）
    use_region = args.region_caliber == "xw_174"
    if use_region:
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
    else:
        joined["in_xw_pt"] = False
        joined["in_174_pt"] = False

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

    # 区域标识：西陵伍家合并范围 / 174社区范围（按格质心·region-caliber 可选）
    if use_region:
        with open(XW, encoding="utf-8") as f:
            xw = json.load(f)
        xw_geom = unary_union([shape(feature["geometry"]) for feature in xw["features"]])
        with open(COMM174, encoding="utf-8") as f:
            c174 = json.load(f)
        c174_geom = unary_union([shape(feature["geometry"]) for feature in c174["features"]])
        cents = grid.geometry.centroid
        grid["in_xw"] = cents.within(xw_geom) | cents.covers(xw_geom)
        grid["in_174"] = cents.within(c174_geom) | cents.covers(c174_geom)
    else:
        grid["in_xw"] = False
        grid["in_174"] = False

    # 主导类9 / 主导方面
    cls_cols = [f"n_{c}" for c in CLASS9]
    grid["top_class9"] = grid[cls_cols].idxmax(axis=1).str.replace("n_", "", regex=False)
    grid["top_class9_count"] = grid[cls_cols].max(axis=1)
    asp_cols = [f"n_{c}" for c in ASPECTS]
    grid["top_aspect"] = grid[asp_cols].idxmax(axis=1).str.replace("n_", "", regex=False)

    # 输出 schema 清理：删除 core 自附的下钻链字段（出处见口径对照段）
    grid = grid.drop(columns=[c for c in _CORE_DROP_COLS if c in grid.columns])

    # 输出 GeoJSON（保留中文）
    out_gj = os.path.join(out_dir, f"12345_{n}m方格聚合.geojson")
    fc = json.loads(grid.to_json())
    with open(out_gj, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)
    _safe_print(f"[OK] {out_gj}（{len(fc['features'])} 格）")

    # 输出 CSV
    out_csv = os.path.join(out_dir, f"12345_{n}m方格聚合_统计.csv")
    grid.drop(columns=["geometry"]).to_csv(out_csv, index=False, encoding="utf-8-sig")
    _safe_print(f"[OK] {out_csv}")

    # 输出 render_inbox spec（前端 choropleth·先自清旧 spec）
    _clean_inbox_specs()
    spec_id = f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
    spec = {
        "spec_version": 1,
        "spec_id": spec_id,
        "kind": "choropleth",
        "data": {"geojson": fc},
        "style": {"scheme": "community_choropleth_v1", "value_field": "point_count"},
        "ui": {"name": f"12345热线{n}m方格聚合（ok精确点）", "zoom_to": True},
        "origin": {"producer": "dsh", "source_tool": SPEC_SOURCE_TOOL},
        "caliber_lite": {
            "usage": "input",
            "data_nature": "real",
            "note": f"12345 2024 ok 精确点 {n}m 方格聚合（create_square_grid·仅有点的格）",
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
    # 口径对照段（PT-CB7 T8/T9：所有数据类交付必带·注册表卡 ID 只读引用）
    ok_n = int(grid["point_count"].sum())
    summary["caliber_compare"] = {
        "this_result": f"12345 2024 geocode_status=ok 精确坐标点 {ok_n} 件（{n}m 方格聚合）",
        "source_total_with_coords": int(src_total),
        "landing_rate_vs_source": round(ok_n / src_total * 100, 1) if src_total else None,
        "full_k01": {"count": FULL_COUNT_K01, "note": "K-01 12345 管理口径·市域全量（含无坐标/region 点）"},
        "full_k02": {"count": FULL_COUNT_K02, "note": "K-02 board 双口径·全量（含客观轨）"},
        "subset_declaration": "本结果 = ok 精确落点子集，非全量；地理落点可得性与诉求类型相关（子集偏差声明）",
        "registry_ref": "docs/urban-renewal-plan/00-宜昌专项/_口径注册表.md K-01/K-02",
        "dropped_core_fields": _CORE_DROP_COLS,
        "dropped_fields_note": "poi_names/place_name 等为 core.create_square_grid 自附下钻链字段（CB-16 Wave 2），本交付不需要已删除",
        "region_caliber": args.region_caliber,
    }
    summary_path = os.path.join(out_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    _safe_print(f"[OK] {summary_path}")
    _safe_print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
