# -*- coding: utf-8 -*-
"""停车泊位缺口点 -> 社区聚合 -> 社区面 geojson（出图用）
数据源：checkup_qty_民生_停车设施（274点·3项指标）+ checkup_配置_社区174（社区面）
产物：DATA/analysis/民生基础/停车泊位缺口_社区面.geojson
"""
import json
import sys
from collections import Counter, defaultdict

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

BASE = r"D:\Github\emotion_map\DATA"
PARK = BASE + r"\boundaries\presets\checkup_qty_民生_停车设施.geojson"
COMM = BASE + r"\boundaries\presets\checkup_配置_社区174.geojson"
OUT = BASE + r"\analysis\民生基础\停车泊位缺口_社区面.geojson"

TARGET = "停车泊位缺口数（个）"


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    with open(PARK, encoding="utf-8") as f:
        park = json.load(f)
    with open(COMM, encoding="utf-8") as f:
        comm = json.load(f)

    items = Counter(f["properties"].get("指标", "") for f in park["features"])
    print("停车设施层指标分布:", dict(items))

    props0 = comm["features"][0]["properties"]
    name_col = "社区" if "社区" in props0 else "NAME"
    print("社区要素数:", len(comm["features"]), "| 名称字段:", name_col)

    pts = [f for f in park["features"] if f["properties"].get("指标") == TARGET]
    print("停车泊位缺口点数:", len(pts))

    geoms = [shape(f["geometry"]) for f in comm["features"]]
    tree = STRtree(geoms)
    cnt = defaultdict(int)
    unmatched = 0
    for f in pts:
        p = Point(f["geometry"]["coordinates"])
        hit = None
        for i in tree.query(p):
            if geoms[i].contains(p):
                hit = i
                break
        if hit is None:
            unmatched += 1
            continue
        cnt[hit] += 1

    print("未匹配到社区的点数:", unmatched)
    print("覆盖社区数:", len(cnt))
    print("---- 社区排名（停车泊位缺口点）----")
    rows = sorted(cnt.items(), key=lambda kv: -kv[1])
    for i, n in rows:
        name = comm["features"][i]["properties"].get(name_col)
        print(f"{n}\t{name}")

    feats = []
    for i, n in rows:
        f0 = comm["features"][i]
        feats.append({
            "type": "Feature",
            "geometry": f0["geometry"],
            "properties": {
                "name": f0["properties"].get(name_col),
                "point_count": n,
            },
        })
    out = {"type": "FeatureCollection", "features": feats}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print("已写出:", OUT, "| 要素数:", len(feats))


if __name__ == "__main__":
    main()
