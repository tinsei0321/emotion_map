# -*- coding: utf-8 -*-
# CB-33 调整：page4/page6 全篇去掉「村」相关内容 → 点数据/图斑排除村点。
# 输出：重写 12345_{方面}_西陵伍家点.geojson（无村）+ 打印无村统计。
import json
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS = os.path.join(ROOT, "DATA", "analysis")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    for asp in ("安全韧性", "民生基础"):
        src = os.path.join(ANALYSIS, f"12345_{asp}_西陵伍家点.geojson")
        gj = load(src)
        feats = gj["features"]
        # 去村：排除 geocode_status=='ok' 且 村 非空的点
        kept = [f for f in feats if not (f["properties"].get("geocode_status") == "ok" and f["properties"].get("村"))]
        with open(src, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": kept}, f, ensure_ascii=False)

        ok = [f for f in kept if f["properties"].get("geocode_status") == "ok"]
        city = [f for f in ok if f["properties"].get("社区")]
        region = [f for f in kept if f["properties"].get("geocode_status") == "region"]
        outside = [f for f in ok if not f["properties"].get("社区")]
        print(f"=== {asp}（去村）===")
        print(f"总图斑 {len(kept)} = 精确社区 {len(city)} + 区级 {len(region)} + 范围外 {len(outside)}")
        print(f"唯一社区 {len(set(f['properties']['社区'] for f in city))}")

        c9 = Counter(f["properties"]["类9"] for f in kept)
        tot = len(kept)
        print("类9（件数 / 占比）:")
        for k in sorted(c9):
            print(f"  {k}: {c9[k]} ({c9[k]/tot*100:.1f}%)")

        # 类9 拆解（社区 / 区级+范围外）
        print("类9 拆解（社区 / 区级+范围外 / 合计 / 涉及社区）:")
        for k in sorted(c9):
            s = [f for f in kept if f["properties"]["类9"] == k]
            c_city = [f for f in s if f["properties"].get("geocode_status") == "ok" and f["properties"].get("社区")]
            c_reg = [f for f in s if not (f["properties"].get("geocode_status") == "ok" and f["properties"].get("社区"))]
            print(f"  {k}: {len(c_city)} / {len(c_reg)} / {len(s)} / 涉及{len(set(f['properties']['社区'] for f in c_city))}")

        # 社区 TOP10
        cc = Counter(f["properties"]["社区"] for f in city)
        print("社区 TOP10:")
        for i, (n, c) in enumerate(cc.most_common(10), 1):
            print(f"  {i}. {n}: {c} ({c/len(city)*100:.1f}%)")
        print()


if __name__ == "__main__":
    main()
