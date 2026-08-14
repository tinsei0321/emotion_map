# -*- coding: utf-8 -*-
"""生成 page7 三类重点社区的面范围（剪裁自 130 社区面），供三类点分别聚合后仅保留重点社区。"""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "DATA", "boundaries", "presets")
OUT = P

CATEGORIES = {
    "双高": ["营盘路社区", "宝联社区", "汕头路社区", "胜利四路社区", "胜利二路社区"],
    "问题指标高": ["深圳路社区", "西峡社区", "金安岭社区", "镇境山社区", "幸福路社区", "新隆康路社区", "果园路社区", "桥北社区"],
    "诉求呼声高": ["朝阳路社区", "万达社区", "港务社区", "建设社区", "岳湾路社区", "大学路社区", "伍临路社区"],
}


def main():
    src = glob.glob(os.path.join(P, "*西陵*.geojson"))
    if not src:
        raise FileNotFoundError("体检对象_西陵+伍家岗.geojson")
    with open(src[0], encoding="utf-8") as f:
        fc = json.load(f)

    name_col = "社区"
    all_names = [ft["properties"].get(name_col) for ft in fc["features"]]
    print(f"源面数: {len(fc['features'])}，唯一社区名: {len(set(all_names))}")

    for cat, names in CATEGORIES.items():
        missing = [n for n in names if n not in all_names]
        feats = [ft for ft in fc["features"] if ft["properties"].get(name_col) in names]
        if missing:
            print(f"[WARN] {cat} 缺失社区面: {missing}")
        out = os.path.join(OUT, f"page7_{cat}社区面.geojson")
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": feats}, f, ensure_ascii=False)
        print(f"[OK] {cat}: {len(feats)} 面 → {os.path.basename(out)}")


if __name__ == "__main__":
    main()
