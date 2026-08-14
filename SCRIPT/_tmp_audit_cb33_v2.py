# -*- coding: utf-8 -*-
# CB-33 补验：唯一社区/村数 + 环境安全聚集社区TOP + TOP10主要问题明细
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

# 非安全/民生方面 = 13,392 - 13,389 = 3
other = [f for f in inside if f["properties"].get("方面") not in ("安全韧性", "民生基础")]
print(f"inside 总 {len(inside)} | 非安全/民生方面 {len(other)} 点:")
for f in other:
    p = f["properties"]
    print(f"  方面={p.get('方面')} 类9={p.get('类9')} 事件={p.get('事件')} geocode={p.get('geocode_status')}")

for asp, decl_c, decl_v in (("安全韧性", 92, 8), ("民生基础", 112, 7)):
    sub = [f for f in inside if f["properties"].get("方面") == asp]
    ok = [f for f in sub if f["properties"].get("geocode_status") == "ok"]
    city = [f for f in ok if f["properties"].get("社区")]
    vill = [f for f in ok if f["properties"].get("村")]
    uniq_c = set(f["properties"]["社区"] for f in city)
    uniq_v = set(f["properties"]["村"] for f in vill)
    print(f"\n=== {asp} 唯一社区 {len(uniq_c)}(声明{decl_c}) 唯一村 {len(uniq_v)}(声明{decl_v}) ===")
    # 各类9 社区TOP5（验证环境安全聚集 3 vs 5）
    c9c = defaultdict(Counter)
    for f in city:
        c9c[f["properties"]["类9"]][f["properties"]["社区"]] += 1
    for c9n in sorted(c9c):
        top5 = c9c[c9n].most_common(5)
        print(f"  [{c9n}] 社区TOP5: " + " ".join(f"{n}{v}" for n, v in top5))
    # TOP10社区 类9明细（验证md"主要问题"列）
    cc = Counter(f["properties"]["社区"] for f in city)
    print("  TOP10社区 类9明细:")
    for name, cnt in cc.most_common(10):
        det = Counter(f["properties"]["类9"] for f in city if f["properties"]["社区"] == name)
        print(f"    {name}({cnt}): " + " ".join(f"{k}{v}" for k, v in det.most_common()))
