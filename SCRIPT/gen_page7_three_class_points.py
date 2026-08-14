# -*- coding: utf-8 -*-
# page7 三类社区图 · 三类点数据导出（双高 / 问题指标高 / 诉求呼声高），每份含体检点+诉求点，供自行聚合。
import json
import os
from collections import defaultdict

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "DATA", "analysis")
OUT = os.path.join(A, "page7小结")

COMM = os.path.join(ROOT, "DATA", "boundaries", "presets", "checkup_配置_社区174.geojson")
TJ_FILES = [
    ("体检", "安全", os.path.join(A, "77项量化", "checkup_qty_安全_合并.geojson")),
    ("体检", "民生", os.path.join(A, "77项量化", "checkup_qty_民生_合并.geojson")),
]
SUB_FILES = [
    ("诉求", "安全", os.path.join(A, "12345主观", "12345_安全韧性_社区点.geojson")),
    ("诉求", "民生", os.path.join(A, "12345主观", "12345_民生基础_社区点.geojson")),
]

CATEGORIES = {
    "双高": ["营盘路社区", "宝联社区", "汕头路社区", "胜利四路社区", "胜利二路社区"],
    "问题指标高": ["深圳路社区", "西峡社区", "金安岭社区", "镇境山社区", "幸福路社区", "新隆康路社区", "果园路社区", "桥北社区"],
    "诉求呼声高": ["朝阳路社区", "万达社区", "港务社区", "建设社区", "岳湾路社区", "大学路社区", "伍临路社区"],
}


def load_gj(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    # 社区面 + STRtree（精确点面内）
    comm = load_gj(COMM)
    key = None
    for f in comm["features"]:
        for k, v in f["properties"].items():
            if v:
                key = k
                break
        if key:
            break
    geoms = [shape(f["geometry"]) for f in comm["features"]]
    names = [f["properties"].get(key) for f in comm["features"]]
    tree = STRtree(geoms)

    def comm_of(lon, lat):
        pt = Point(lon, lat)
        for gi in tree.query(pt):
            if geoms[gi].contains(pt) or geoms[gi].covers(pt):
                return names[gi]
        return None

    # 体检点（sjoin 社区）+ 诉求点（已有社区字段）
    pts = []  # {社区, 类型(体检/诉求), 方面(安全/民生), 类/指标, geometry}
    for typ, asp, path in TJ_FILES:
        gj = load_gj(path)
        for f in gj["features"]:
            lon, lat = f["geometry"]["coordinates"]
            c = comm_of(lon, lat)
            if not c:
                continue
            pts.append({
                "社区": c, "类型": typ, "方面": asp,
                "类": f["properties"].get("中类") or f["properties"].get("指标"),
                "lon": lon, "lat": lat,
            })
    for typ, asp, path in SUB_FILES:
        gj = load_gj(path)
        for f in gj["features"]:
            p = f["properties"]
            c = p.get("社区")
            if not c:
                continue
            lon, lat = f["geometry"]["coordinates"]
            pts.append({
                "社区": c, "类型": typ, "方面": asp,
                "类": p.get("类9"),
                "lon": lon, "lat": lat,
            })

    # 按三类分组
    by_cat = defaultdict(list)
    for p in pts:
        c = p["社区"]
        for cat, names in CATEGORIES.items():
            if c in names:
                by_cat[cat].append(p)
                break

    for cat, names in CATEGORIES.items():
        feats = []
        for p in by_cat[cat]:
            feats.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
                "properties": {
                    "社区": p["社区"], "类型": p["类型"], "方面": p["方面"], "类": p["类"], "层": cat,
                },
            })
        out = os.path.join(OUT, f"page7_{cat}点.geojson")
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": feats}, f, ensure_ascii=False)
        # 统计
        n_tj = sum(1 for p in by_cat[cat] if p["类型"] == "体检")
        n_sub = sum(1 for p in by_cat[cat] if p["类型"] == "诉求")
        print(f"[OK] page7_{cat}点.geojson：{len(feats)} 点（体检 {n_tj} / 诉求 {n_sub}）· {len(names)} 社区")


if __name__ == "__main__":
    main()
