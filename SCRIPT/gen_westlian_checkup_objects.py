# -*- coding: utf-8 -*-
# CB-33 追加：生成「体检对象_西陵+伍家岗」面范围 = 174 城市社区中属于西陵+伍家岗的部分。
import json
import os

from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRESETS = os.path.join(ROOT, "DATA", "boundaries", "presets")
COMM = os.path.join(PRESETS, "checkup_配置_社区.geojson")
XLWJ = os.path.join(ROOT, "DATA", "analysis", "12345_西陵+伍家岗.geojson")
OUT = os.path.join(PRESETS, "体检对象_西陵+伍家岗.geojson")


def main():
    with open(COMM, encoding="utf-8") as f:
        comm = json.load(f)
    with open(XLWJ, encoding="utf-8") as f:
        rng = json.load(f)
    union = unary_union([shape(f["geometry"]) for f in rng["features"]])

    kept = []
    for f in comm["features"]:
        g = shape(f["geometry"])
        # 质心在 union 内，或与 union 交叠面积 > 50%（兜住南津关/上导堤等西陵区边界社区）
        if union.contains(g.centroid) or union.covers(g.centroid):
            kept.append(f)
        elif not g.is_empty and g.area > 0 and g.intersection(union).area / g.area > 0.5:
            kept.append(f)
    print(f"174 社区中命中西陵+伍家岗：{len(kept)} 个")

    out = {"type": "FeatureCollection", "features": kept}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"[OK] {os.path.basename(OUT)} ({len(kept)} features)")


if __name__ == "__main__":
    main()
