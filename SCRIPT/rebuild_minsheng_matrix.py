# -*- coding: utf-8 -*-
# CB-33 修复：重建 民生_社区5类矩阵.csv（物业街面 278 点 sjoin 入矩阵，92→? 社区，合计 479→757）。
import json
import os
from collections import defaultdict

import pandas as pd
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q77 = os.path.join(ROOT, "DATA", "analysis", "77项量化")
COMM174 = os.path.join(ROOT, "DATA", "boundaries", "presets", "checkup_配置_社区174.geojson")
OUT = os.path.join(ROOT, "DATA", "analysis", "民生基础", "民生_社区5类矩阵.csv")

CLASSES = [
    ("公服设施", "checkup_qty_民生_公服设施_问题类.geojson"),
    ("住房", "checkup_qty_民生_住房.geojson"),
    ("停车设施", "checkup_qty_民生_停车设施.geojson"),
    ("交通设施", "checkup_qty_民生_交通设施.geojson"),
    ("物业街面", "checkup_qty_民生_物业街面.geojson"),
]


def load_gj(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    with open(COMM174, encoding="utf-8") as f:
        comm = json.load(f)
    key = None
    for f0 in comm["features"]:
        for k, v in f0["properties"].items():
            if v:
                key = k
                break
        if key:
            break
    geoms = [shape(f["geometry"]) for f in comm["features"]]
    names = [f["properties"].get(key) for f in comm["features"]]
    tree = STRtree(geoms)

    def comm_of(pt):
        for gi in tree.query(pt):
            g = geoms[gi]
            if g.contains(pt) or g.covers(pt):
                return names[gi]
        return None

    mat = defaultdict(lambda: defaultdict(int))
    totals = {}
    for cname, fname in CLASSES:
        gj = load_gj(os.path.join(Q77, fname))
        n_in = 0
        for f in gj["features"]:
            lon, lat = f["geometry"]["coordinates"]
            c = comm_of(Point(lon, lat))
            if c:
                mat[c][cname] += 1
                n_in += 1
        totals[cname] = (len(gj["features"]), n_in)
        print(f"  {cname}: 总 {len(gj['features'])} 点, 命中社区 {n_in}")

    rows = []
    for c, cls in mat.items():
        total = sum(cls.values())
        rows.append({
            "社区": c,
            "公服设施": cls.get("公服设施", 0),
            "住房": cls.get("住房", 0),
            "停车设施": cls.get("停车设施", 0),
            "交通设施": cls.get("交通设施", 0),
            "物业街面": cls.get("物业街面", 0),
            "总点数": total,
        })
    df = pd.DataFrame(rows)
    grand = df["总点数"].sum()
    df["总占比%"] = (df["总点数"] / grand * 100).round(2)
    df["覆盖类数"] = (df[["公服设施", "住房", "停车设施", "交通设施", "物业街面"]] > 0).sum(axis=1)
    df = df.sort_values("总点数", ascending=False).reset_index(drop=True)
    df["排序"] = df.index + 1
    df["严重度"] = df["总占比%"].apply(lambda p: "严重" if p >= 5 else ("较严重" if p >= 3 else "一般"))
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"重建完成: {len(df)} 社区, 合计 {grand} 点")
    print(f"各类合计: {df[['公服设施','住房','停车设施','交通设施','物业街面']].sum().to_dict()}")


if __name__ == "__main__":
    main()
