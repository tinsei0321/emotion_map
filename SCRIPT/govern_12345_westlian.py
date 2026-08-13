# -*- coding: utf-8 -*-
# CB-32 紧急修改：page4/page6 的 12345 数据改为「命中体检对象 = 西陵区+伍家岗区」。
# 流程：读西陵+伍家范围 -> 筛选落在范围内的有坐标点 -> 区级点视作精准点合并 -> 重算 page4/page6 口径。
# 输出：12345_西陵+伍家岗.geojson（范围层）+ 分方面西陵伍家点 + 社区/村矩阵 + 统计打印。
import json
import os
from collections import Counter, defaultdict

import pandas as pd
from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS = os.path.join(ROOT, "DATA", "analysis")
SUBJ = os.path.join(ANALYSIS, "12345主观")

RANGE_SRC = os.path.join(ANALYSIS, "西陵伍家_合并范围.geojson")
PTS_SRC = os.path.join(SUBJ, "12345_有坐标点.geojson")
COMM174 = os.path.join(ROOT, "DATA", "boundaries", "presets", "checkup_配置_社区174.geojson")

def load_gj(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_gj(path, features):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, ensure_ascii=False)
    print(f"[OK] {os.path.basename(path)} ({len(features)} features)")


def main():
    rng = load_gj(RANGE_SRC)
    polys = [shape(f["geometry"]) for f in rng["features"]]
    # 合并为单一多边形（西陵+伍家）
    union = unary_union(polys)

    pts = load_gj(PTS_SRC)
    feats = pts["features"]
    print(f"总有坐标点 {len(feats)}")

    # 空间过滤：落在西陵+伍家范围内
    inside = []
    for f in feats:
        p = shape(f["geometry"])
        if union.contains(p) or union.covers(p) or union.touches(p):
            inside.append(f)
    print(f"西陵+伍家范围内 {len(inside)} 点（区级点视作精准合并）")

    # 事件三分类
    def event3(t):
        if t == "投诉":
            return "投诉"
        if t in ("求助", "咨询"):
            return "求助"
        if t == "建议":
            return "建议"
        return "其他"

    # 分方面输出
    by_aspect = defaultdict(list)
    for f in inside:
        asp = f["properties"].get("方面")
        by_aspect[asp].append(f)

    for asp, fsub in by_aspect.items():
        name = f"12345_{asp}_西陵伍家点.geojson"
        save_gj(os.path.join(SUBJ, name), fsub)
        # 类9 分布（全部点，含区级合并）
        c9 = Counter(f["properties"].get("类9") for f in fsub)
        ev = Counter(event3(f["properties"].get("事件")) for f in fsub)
        ok_c = sum(1 for f in fsub if f["properties"].get("geocode_status") == "ok" and f["properties"].get("社区"))
        ok_v = sum(1 for f in fsub if f["properties"].get("geocode_status") == "ok" and f["properties"].get("村"))
        region = sum(1 for f in fsub if f["properties"].get("geocode_status") == "region")
        print(f"\n=== {asp} ===")
        print(f"  总图斑(含区级合并) {len(fsub)} = 精确社区 {ok_c} + 精确村 {ok_v} + 区级 {region}")
        print(f"  类9: {dict(c9)}")
        print(f"  事件: {dict(ev)}")

    # 社区 / 村矩阵（ok 点·西陵+伍家内）
    ok_in = [f for f in inside if f["properties"].get("geocode_status") == "ok"]
    city = [f for f in ok_in if f["properties"].get("社区")]
    vill = [f for f in ok_in if f["properties"].get("村")]
    print(f"\n[OK] 西陵+伍家内 ok 点 {len(ok_in)}：命中社区 {len(city)} / 命中村 {len(vill)}")

    def matrix(feats, key, path):
        rows = []
        for f in feats:
            rows.append({key: f["properties"][key], "类9": f["properties"]["类9"], "方面": f["properties"]["方面"]})
        df = pd.DataFrame(rows)
        mat = pd.crosstab(df[key], df["类9"])
        mat.to_csv(path, encoding="utf-8-sig")
        print(f"[OK] {os.path.basename(path)} -> {len(mat)} 行")
        return mat

    matrix(city, "社区", os.path.join(SUBJ, "12345_社区x9类_西陵伍家.csv"))
    matrix(vill, "村", os.path.join(SUBJ, "12345_村x9类_西陵伍家.csv"))

    # 分方面 社区/村 TOP 表（用于 page4/page6 重写）
    print("\n========== 分方面 TOP（ok 点·社区/村口径） ==========")
    for asp in ("安全韧性", "民生基础"):
        sub = [f for f in inside if f["properties"].get("方面") == asp]
        ok = [f for f in sub if f["properties"].get("geocode_status") == "ok"]
        city = [f for f in ok if f["properties"].get("社区")]
        vill = [f for f in ok if f["properties"].get("村")]
        print(f"\n### {asp} ###")
        print(f"总图斑 {len(sub)} = 精确社区 {len(city)} + 精确村 {len(vill)} + 区级 {sum(1 for f in sub if f['properties'].get('geocode_status')=='region')} + 范围外 {sum(1 for f in ok if not f['properties'].get('社区') and not f['properties'].get('村'))}")
        print(f"唯一社区 {len(set(f['properties']['社区'] for f in city))} · 唯一村 {len(set(f['properties']['村'] for f in vill))}")
        cc = Counter(f["properties"]["社区"] for f in city)
        c9 = defaultdict(Counter)
        for f in city:
            c9[f["properties"]["社区"]][f["properties"]["类9"]] += 1
        total_city = len(city)
        print("社区 TOP10:")
        for i, (name, n) in enumerate(cc.most_common(10), 1):
            det = "、".join(f"{k}{v}" for k, v in c9[name].most_common(3))
            print(f"  {i}. {name}: {n} ({n/total_city*100:.1f}%)  [{det}]")
        vc = Counter(f["properties"]["村"] for f in vill)
        print("村 TOP:")
        for i, (name, n) in enumerate(vc.most_common(10), 1):
            print(f"  {i}. {name}: {n}")
        # 类9 分级拆解（精确社区/精确村/区级/涉及社区数）
        print("类9 拆解:")
        for c9name in sorted(set(f["properties"]["类9"] for f in sub)):
            s = [f for f in sub if f["properties"]["类9"] == c9name]
            c_city = [f for f in s if f["properties"].get("geocode_status") == "ok" and f["properties"].get("社区")]
            c_vill = [f for f in s if f["properties"].get("geocode_status") == "ok" and f["properties"].get("村")]
            c_reg = [f for f in s if f["properties"].get("geocode_status") == "region"]
            c_out = [f for f in s if f["properties"].get("geocode_status") == "ok" and not f["properties"].get("社区") and not f["properties"].get("村")]
            print(f"  {c9name}: 总{len(s)} = 社区{len(c_city)} 村{len(c_vill)} 区级{len(c_reg)} 范围外{len(c_out)} | 涉及社区{len(set(f['properties']['社区'] for f in c_city))}")
        # 每类9 top3 社区（明细「主要集中在」用）
        c9c = defaultdict(Counter)
        for f in city:
            c9c[f["properties"]["类9"]][f["properties"]["社区"]] += 1
        print("类9 TOP3 社区:")
        for c9name in sorted(c9c):
            top = "、".join(f"{n}{v}" for n, v in c9c[c9name].most_common(3))
            print(f"  {c9name}: {top}")
        print("类9 TOP5 社区:")
        for c9name in sorted(c9c):
            top = "、".join(n for n, _ in c9c[c9name].most_common(5))
            print(f"  {c9name}: {top}")


if __name__ == "__main__":
    main()
