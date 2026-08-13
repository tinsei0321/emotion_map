# -*- coding: utf-8 -*-
# CB-33 修正：范围层语义改为「社区级面」，非行政区合并。
# ① 12345_西陵+伍家岗 = 有 12345 落点（ok 精确点）的西陵+伍家岗社区
# ② 体检对象_西陵+伍家岗 = 174 体检对象社区中属于西陵+伍家岗区的社区（已由 gen_westlian_checkup_objects.py 生成，此处只复核计数）
import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRESETS = os.path.join(ROOT, "DATA", "boundaries", "presets")
ANALYSIS = os.path.join(ROOT, "DATA", "analysis")
COMM174 = os.path.join(PRESETS, "checkup_配置_社区.geojson")
MAT_12345 = os.path.join(ANALYSIS, "12345主观", "12345_社区x9类_西陵伍家.csv")
OUT_12345 = os.path.join(ANALYSIS, "12345_西陵+伍家岗.geojson")
OBJ_XLWJ = os.path.join(PRESETS, "体检对象_西陵+伍家岗.geojson")


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
    by_name = {f["properties"].get(key): f for f in comm["features"]}

    # ① 有 12345 ok 落点的社区
    mat = pd.read_csv(MAT_12345, encoding="utf-8-sig", index_col=0)
    names_12345 = list(mat.index)
    feats_12345 = [by_name[n] for n in names_12345 if n in by_name]
    with open(OUT_12345, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": feats_12345}, f, ensure_ascii=False)
    print(f"① 有 12345 落点的西陵+伍家岗社区：{len(feats_12345)} 个")
    missing = [n for n in names_12345 if n not in by_name]
    if missing:
        print(f"   未在 174 社区面中找到：{missing}")

    # ② 174 体检对象中属于西陵+伍家岗的社区（复核）
    with open(OBJ_XLWJ, encoding="utf-8") as f:
        obj = json.load(f)
    print(f"② 174 体检对象中属于西陵+伍家岗的社区：{len(obj['features'])} 个")
    print(f"   差异（体检对象有但无 12345 落点）≈ {len(obj['features']) - len(feats_12345)} 个")


if __name__ == "__main__":
    main()
