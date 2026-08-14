# -*- coding: utf-8 -*-
# CB-33 定夺：v1(港务168) vs v2(港务83) 矛盾 · 权威对照 + 交付物点文件交叉验证
import json, os
from collections import Counter
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
feats = pts["features"]

def in_u(g):
    return union.contains(g) or union.covers(g) or union.touches(g)

inside = [f for f in feats if in_u(shape(f["geometry"]))]
print(f"INSIDE总数 {len(inside)}")

for asp in ("安全韧性", "民生基础"):
    sub = [f for f in inside if f["properties"].get("方面") == asp]
    ok = [f for f in sub if f["properties"].get("geocode_status") == "ok"]
    city = [f for f in ok if f["properties"].get("社区")]
    vill = [f for f in ok if f["properties"].get("村")]
    region = [f for f in sub if f["properties"].get("geocode_status") == "region"]
    out = [f for f in ok if not f["properties"].get("社区") and not f["properties"].get("村")]
    uniq_c = sorted(set(f["properties"]["社区"] for f in city))
    uniq_v = sorted(set(f["properties"]["村"] for f in vill))
    print(f"\n=== {asp} ===")
    print(f"  SUB={len(sub)} OK={len(ok)} CITY={len(city)} VILL={len(vill)} REGION={len(region)} OUT={len(out)}")
    print(f"  唯一社区={len(uniq_c)} 唯一村={len(uniq_v)}")
    cc = Counter(f["properties"]["社区"] for f in city)
    print(f"  CITY总数校验={sum(cc.values())} TOP5={cc.most_common(5)}")
    # 交付物点文件交叉验证
    dp = load(os.path.join(SUBJ, f"12345_{asp}_西陵伍家点.geojson"))
    df = dp["features"]
    dc = [f for f in df if f["properties"].get("geocode_status") == "ok" and f["properties"].get("社区")]
    dcc = Counter(f["properties"]["社区"] for f in dc)
    print(f"  交付物features={len(df)} 交付物ok+社区={len(dc)} 交付物TOP5={dcc.most_common(5)}")
