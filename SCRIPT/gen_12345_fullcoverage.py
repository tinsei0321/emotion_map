# -*- coding: utf-8 -*-
"""12345 主观轨扩域重算：按 174 社区全覆盖范围内的落点重新梳理（用户定·2026-08-17）。
- 范围 = 体检全覆盖范围_174社区合并面（点落在任一社区面内即计入·sjoin 归属·与体检管线同口径）
- 输出：分方面落图点 geojson ×2 + 社区x9类矩阵_全覆盖 csv + page4/page6 口径统计打印
"""
import json
import os
import sys
import io
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pandas as pd
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBJ = os.path.join(ROOT, "DATA", "analysis", "12345主观")
PRESETS = os.path.join(ROOT, "DATA", "boundaries", "presets")
XW = os.path.join(ROOT, "DATA", "analysis", "西陵伍家_合并范围.geojson")


def load_gj(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_gj(path, features):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, ensure_ascii=False)
    print(f"[OK] {os.path.basename(path)} ({len(features)} features)")


def main():
    # ── 社区174 空间索引 ──
    comm = load_gj(os.path.join(PRESETS, "checkup_配置_社区174.geojson"))
    cgeoms = [shape(f["geometry"]) for f in comm["features"]]
    cnames = [f["properties"]["社区"] for f in comm["features"]]
    tree = STRtree(cgeoms)

    def comm_of(pt):
        for gi in tree.query(pt):
            if cgeoms[gi].contains(pt) or cgeoms[gi].covers(pt):
                return cnames[gi]
        return None

    # 旧范围（西陵伍家）用于对比增量
    xw = load_gj(XW)
    from shapely.ops import unary_union
    xwg = unary_union([shape(f["geometry"]) for f in xw["features"]])

    pts = load_gj(os.path.join(SUBJ, "12345_有坐标点.geojson"))
    feats = pts["features"]
    print(f"总有坐标点 {len(feats)}")

    inside = []
    for f in feats:
        p = shape(f["geometry"])
        c = comm_of(p)
        if c:
            props = dict(f["properties"])
            props["社区_sjoin"] = c
            props["属新区"] = not (xwg.contains(p) or xwg.covers(p))
            f2 = dict(f)
            f2["properties"] = props
            inside.append(f2)
    n_new = sum(1 for f in inside if f["properties"]["属新区"])
    print(f"174 社区范围内 {len(inside)} 点（其中新区增量 {n_new}·原西陵伍家 {len(inside) - n_new}）")

    # 分方面输出 + 统计
    def event3(t):
        return t if t in ("投诉", "求助", "建议") else "其他"

    # 口径分离（沿旧管线惯例）：
    # - 图斑总数/类9件数 = 范围内全部点（含区级 region 点）
    # - 社区矩阵/TOP/涉及社区 = 仅 geocode_status=='ok' 且 sjoin 命中（区级点落区质心社区会畸高·不进）
    rows_mat = []
    for asp in ("安全韧性", "民生基础"):
        sub = [f for f in inside if f["properties"].get("方面") == asp]
        sub_ok = [f for f in sub if f["properties"].get("geocode_status") == "ok"]
        save_gj(os.path.join(SUBJ, f"12345_{asp}_全覆盖点.geojson"), sub)
        c9 = Counter(f["properties"].get("类9") for f in sub)
        ev = Counter(event3(f["properties"].get("事件")) for f in sub)
        n_region = sum(1 for f in sub if f["properties"].get("geocode_status") == "region")
        newcom = [f for f in sub if f["properties"]["属新区"]]
        print(f"\n=== {asp} ===")
        print(f"  总图斑 {len(sub)}（含区级 {n_region}）·新区增量 {len(newcom)}")
        print(f"  类9(全量): {dict(c9)}")
        print(f"  事件: {dict(ev)}")
        # TOP10 社区（ok 精确点·sjoin 归属）
        cc = Counter(f["properties"]["社区_sjoin"] for f in sub_ok)
        c9c = defaultdict(Counter)
        for f in sub_ok:
            c9c[f["properties"]["社区_sjoin"]][f["properties"]["类9"]] += 1
        print("  社区 TOP10（ok 精确点）:")
        for i, (name, n) in enumerate(cc.most_common(10), 1):
            det = "、".join(f"{k}{v}" for k, v in c9c[name].most_common(3))
            print(f"    {i}. {name}: {n} ({n / len(sub_ok) * 100:.1f}%)  [{det}]")
        # 类9 拆解
        print("  类9 拆解（涉及社区·ok 精确点）:")
        for c9name in sorted(set(f["properties"]["类9"] for f in sub)):
            s_all = [f for f in sub if f["properties"]["类9"] == c9name]
            s_ok = [f for f in sub_ok if f["properties"]["类9"] == c9name]
            newcom_s = [f for f in s_all if f["properties"]["属新区"]]
            c9cc = Counter(f["properties"]["社区_sjoin"] for f in s_ok)
            top = "、".join(f"{n}{v}" for n, v in c9cc.most_common(5))
            print(f"    {c9name}: {len(s_all)} 件（区级 {len(s_all) - len(s_ok)}·新区 {len(newcom_s)}）·涉及 {len(c9cc)} 社区·TOP5: {top}")
        rows_mat.extend({"社区": f["properties"]["社区_sjoin"], "类9": f["properties"]["类9"],
                         "方面": f["properties"]["方面"], "属新区": f["properties"]["属新区"]} for f in sub_ok)

    # 社区x9类矩阵（全覆盖·ok 精确点·sjoin 归属）
    df = pd.DataFrame(rows_mat)
    mat = pd.crosstab(df["社区"], df["类9"])
    mat.to_csv(os.path.join(SUBJ, "12345_社区x9类_全覆盖.csv"), encoding="utf-8-sig")
    print(f"\n[OK] 12345_社区x9类_全覆盖.csv -> {len(mat)} 社区（ok 精确点 {len(df)}·旧西陵伍家版 118 社区）")
    # 新区社区单独列（增量可区分）
    new_communities = sorted(set(df[df["属新区"]]["社区"]))
    print(f"新区有落点社区 {len(new_communities)}: {new_communities}")


if __name__ == "__main__":
    main()
