# -*- coding: utf-8 -*-
"""停车位不足小区分析：量化体检「停车泊位缺口数」点 → 小区面聚合 → 地图图层。

口径：
- 点层：DATA/boundaries/presets/checkup_qty_民生_停车设施.geojson（2025 体检·274 点·3 指标）
- 仅取 指标 == 停车泊位缺口数（个） 的点（= 停车位不足的直接量化记录）
- 面层：DATA/boundaries/presets/checkup_配置_小区.geojson（1562 小区面·XQMC）
- 输出：有缺口的 小区面 + 缺口点数/缺口总量，按缺口数降序
"""
import json
import sys
from pathlib import Path

try:
    from shapely.geometry import shape
    from shapely.strtree import STRtree
except ImportError:
    sys.exit("[ERR] missing shapely")

REPO = Path(__file__).resolve().parents[1]
PT_FILE = REPO / "DATA" / "boundaries" / "presets" / "checkup_qty_民生_停车设施.geojson"
XQ_FILE = REPO / "DATA" / "boundaries" / "presets" / "checkup_配置_小区.geojson"
OUT_FILE = REPO / "DATA" / "analysis" / "停车位不足_小区_2026-08-21.geojson"

INDICATOR = "停车泊位缺口数（个）"


def load_geojson(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    pts = load_geojson(PT_FILE)["features"]
    sel = [p for p in pts if p["properties"].get("指标") == INDICATOR]
    print(f"[LOAD] parking points total={len(pts)} selected(缺口数)={len(sel)}")

    # 点坐标 → shapely
    from shapely.geometry import Point
    pt_geoms = [Point(p["geometry"]["coordinates"]) for p in sel]

    xq = load_geojson(XQ_FILE)["features"]
    print(f"[LOAD] xiaoqu polygons={len(xq)}")

    # 小区面 → STRtree 空间索引
    xq_geoms = [shape(f["geometry"]) for f in xq]
    tree = STRtree(xq_geoms)

    # 每个缺口点归属小区（取首个命中）
    assign = {}
    for i, g in enumerate(pt_geoms):
        cand = tree.query(g)
        for c in cand:
            if xq_geoms[c].covers(g):
                assign.setdefault(c, []).append(i)
                break
    matched = sum(len(v) for v in assign.values())
    print(f"[JOIN] matched={matched}/{len(sel)}")

    # 聚合
    rows = []
    for c, idxs in assign.items():
        f = xq[c]
        rows.append({
            "XQMC": f["properties"].get("XQMC", ""),
            "SSSQ": f["properties"].get("SSSQ", ""),
            "SSJD": f["properties"].get("SSJD", ""),
            "geom_idx": c,
            "n": len(idxs),
        })
    rows.sort(key=lambda r: -r["n"])

    features = []
    for r in rows:
        props = {
            "name": r["XQMC"],
            "XQMC": r["XQMC"],
            "SSSQ": r["SSSQ"],
            "SSJD": r["SSJD"],
            "point_count": r["n"],
            "指标": INDICATOR,
        }
        features.append({
            "type": "Feature",
            "properties": props,
            "geometry": xq[r["geom_idx"]]["geometry"],
        })

    out = {"type": "FeatureCollection", "name": "停车位不足小区", "features": features}
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"[OK] written {OUT_FILE} features={len(features)}")

    print("\nTOP 15 小区（停车泊位缺口记录数）:")
    for r in rows[:15]:
        print(f"  {r['n']:>2}  {r['XQMC']} ({r['SSJD']}/{r['SSSQ']})")
    # 社区级汇总（对照既有占比表）
    from collections import Counter
    comm = Counter()
    for r in rows:
        comm[r["SSSQ"]] += r["n"]
    print("\nTOP 10 社区:")
    for name, n in comm.most_common(10):
        print(f"  {n:>2}  {name}")


if __name__ == "__main__":
    main()
