# -*- coding: utf-8 -*-
# CB-33 终验：类9×分级 交叉表（对照md表B）+ 各类9唯一社区数（对照md表A"涉及社区"）+ 各类9社区TOP3（对照md正文"主要集中在"）
import json, os
from collections import Counter, defaultdict
from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS = os.path.join(ROOT, "DATA", "analysis")
SUBJ = os.path.join(ANALYSIS, "12345主观")

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

rng = load(os.path.join(ANALYSIS, "12345_西陵+伍家岗.geojson"))
union = unary_union([shape(f["geometry"]) for f in rng["features"]])
pts = load(os.path.join(SUBJ, "12345_有坐标点.geojson"))
inside = [f for f in pts["features"] if (union.contains(shape(f["geometry"])) or union.covers(shape(f["geometry"])) or union.touches(shape(f["geometry"])))]

for asp in ("安全韧性", "民生基础"):
    sub = [f for f in inside if f["properties"].get("方面") == asp]
    print(f"\n========== {asp} 表B真相（类9 × 社区/村/区级/外）==========")
    for c9 in sorted(set(f["properties"].get("类9") for f in sub)):
        s = [f for f in sub if f["properties"].get("类9") == c9]
        ci = [f for f in s if f["properties"].get("geocode_status") == "ok" and f["properties"].get("社区")]
        cv = [f for f in s if f["properties"].get("geocode_status") == "ok" and f["properties"].get("村")]
        cr = [f for f in s if f["properties"].get("geocode_status") == "region"]
        co = [f for f in s if f["properties"].get("geocode_status") == "ok" and not f["properties"].get("社区") and not f["properties"].get("村")]
        uniqc = len(set(f["properties"]["社区"] for f in ci))
        print(f"  {c9}: 总{len(s)} | 社区{len(ci)} 村{len(cv)} 区级{len(cr)} 外{len(co)} | 涉及社区{uniqc}")
        # 该类9 社区TOP3（md正文"主要集中在"对照）
        c9c = Counter(f["properties"]["社区"] for f in ci)
        top3 = "、".join(f"{n}{v}" for n, v in c9c.most_common(3))
        print(f"      社区TOP3: {top3}")
    # 合计行
    ci_all = [f for f in sub if f["properties"].get("geocode_status") == "ok" and f["properties"].get("社区")]
    cv_all = [f for f in sub if f["properties"].get("geocode_status") == "ok" and f["properties"].get("村")]
    cr_all = [f for f in sub if f["properties"].get("geocode_status") == "region"]
    co_all = [f for f in sub if f["properties"].get("geocode_status") == "ok" and not f["properties"].get("社区") and not f["properties"].get("村")]
    print(f"  合计: 社区{len(ci_all)} 村{len(cv_all)} 区级{len(cr_all)} 外{len(co_all)} 总{len(sub)}")
