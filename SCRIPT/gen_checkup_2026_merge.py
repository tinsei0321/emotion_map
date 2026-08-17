# -*- coding: utf-8 -*-
"""生成全覆盖合并点数据（2025 西陵伍家 + 2026 补充·单一文件供落图直接加载）。
- 2025 features 补 来源:"2025体检"；2026 保留 "2026补充"（可区分）
- 原 2025/2026 分类文件均不动
输出：DATA/analysis/77项量化/checkup_qty_安全_合并_全覆盖.geojson (1350)
      DATA/analysis/77项量化/checkup_qty_民生_合并_全覆盖.geojson (946)
      DATA/analysis/77项量化/checkup_qty_合并_全覆盖.geojson (2296)
"""
import json
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

Q77 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "DATA", "analysis", "77项量化")


def load(name):
    with open(os.path.join(Q77, "checkup_qty_" + name + ".geojson"), encoding="utf-8") as f:
        return json.load(f)["features"]


def main():
    pairs = [
        ("安全_合并", ["2026_安全_住房", "2026_安全_安全消防", "2026_安全_市政管网"], "安全_合并_全覆盖"),
        ("民生_合并", ["2026_民生_住房", "2026_民生_公服设施", "2026_民生_停车设施",
                    "2026_民生_交通设施", "2026_民生_物业街面"], "民生_合并_全覆盖"),
    ]
    all_feats = []
    for old, news, out in pairs:
        f25 = load(old)
        f26 = []
        for n in news:
            f26.extend(load(n))
        for x in f25:
            x["properties"].setdefault("来源", "2025体检")
        for x in f26:
            x["properties"].setdefault("来源", "2026补充")
        feats = f25 + f26
        all_feats.extend(feats)
        with open(os.path.join(Q77, f"checkup_qty_{out}.geojson"), "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": feats}, f, ensure_ascii=False)
        n26 = sum(1 for x in feats if x["properties"].get("来源") == "2026补充")
        print(f"[OK] {out}: {len(feats)} 点 = 2025 {len(feats) - n26} + 2026 {n26}")
    with open(os.path.join(Q77, "checkup_qty_合并_全覆盖.geojson"), "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": all_feats}, f, ensure_ascii=False)
    print(f"[OK] 合并_全覆盖: {len(all_feats)} 点")
    # 校验：指标分布
    from collections import Counter
    c = Counter(x["properties"]["指标"] for x in all_feats)
    src = Counter(x["properties"].get("来源") for x in all_feats)
    print(f"来源分布: {dict(src)}")
    for k, v in c.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
