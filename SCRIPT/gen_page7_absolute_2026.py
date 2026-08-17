# -*- coding: utf-8 -*-
"""page7 口径 v3（用户定·2026-08-17 二次调整）：取消双高·只看客观高/主观高两张表。
- 客观线 = 体检问题点 ≥15 个（逻辑：安全3类+民生5类合计 15 个问题以上）
- 主观线 = 全年诉求 ≥50 件（逻辑：2024 年 50 件 ≈ 平均每周至少 1 件）
- 结果目标：客观表 / 主观表 / 两表重叠（落图叠加可见）≈10 社区
- 深浅档：客观 15~29 浅 / 30~59 中 / ≥60 深；主观 50~99 浅(每周约1件) / 100~199 中(每周约2件) / ≥200 深(每2天至少1件)
输出：DATA/analysis/page7小结/page7_绝对值口径_全域_2026-08-17.csv（覆盖·结构改为两表口径）
"""
import os
import sys
import io
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_P7 = os.path.join(ROOT, "DATA", "analysis", "page7小结")

C_LINE = 15   # 客观线：体检问题点 ≥15 个
S_LINE = 50   # 主观线：全年诉求 ≥50 件（≈每周 1 件）


def norm(s):
    return str(s).strip()


def main():
    # ── 客观轨：体检点绝对值（全覆盖）──
    old_s = pd.read_csv(os.path.join(ROOT, "DATA/analysis/安全韧性/安全韧性_社区3类矩阵.csv"))
    old_l = pd.read_csv(os.path.join(ROOT, "DATA/analysis/民生基础/民生_社区5类矩阵.csv"))
    inc_s = pd.read_csv(os.path.join(ROOT, "DATA/analysis/安全韧性/安全韧性_社区3类矩阵_2026增量.csv"))
    inc_l = pd.read_csv(os.path.join(ROOT, "DATA/analysis/民生基础/民生_社区5类矩阵_2026增量.csv"))
    ck25, ck26 = defaultdict(int), defaultdict(int)
    for df in (old_s, old_l):
        for _, r in df.iterrows():
            ck25[norm(r["社区"])] += int(r["总点数"])
    for df in (inc_s, inc_l):
        for _, r in df.iterrows():
            ck26[norm(r["社区"])] += int(r["总点数"])

    # ── 主观轨：12345 诉求件（九类·ok 精确点·174 扩域版矩阵）──
    hot = pd.read_csv(os.path.join(ROOT, "DATA/analysis/12345主观/12345_社区x9类_全覆盖.csv"))
    hot["k"] = hot["社区"].apply(norm)
    hk = hot.set_index("k")
    cls = [c for c in hk.columns if c not in ("其他", "社区", "k") and hk[c].dtype.kind in "iuf"]
    ap = hk[cls].sum(axis=1).to_dict()

    # ── 174 社区全表 ──
    den = pd.read_csv(os.path.join(OUT_P7, "社区规模分母_174.csv"))
    rows = []
    for _, r in den.iterrows():
        c = norm(r["社区"])
        b = r["bldg_n"]
        rows.append({
            "社区": c, "楼栋数": int(b) if pd.notna(b) and b > 0 else None,
            "体检点_2025": ck25.get(c, 0), "体检点_2026新增": ck26.get(c, 0),
            "体检点_全覆盖": ck25.get(c, 0) + ck26.get(c, 0),
            "诉求件_12345": ap.get(c),  # 无数据=None（实事求是）
        })
    df = pd.DataFrame(rows)

    # ── 两表筛选（取消双高·各自过线即入表）──
    df["客观高"] = df["体检点_全覆盖"] >= C_LINE
    df["主观高"] = df["诉求件_12345"].notna() & (df["诉求件_12345"] >= S_LINE)
    df["两表重叠"] = df["客观高"] & df["主观高"]

    # ── 深浅档（整数档·叙事：每周件数）──
    def c_tier(v):
        if v >= 60:
            return "深（≥60）"
        return "中（30~59）" if v >= 30 else "浅（15~29）"

    def s_tier(v):
        if v >= 200:
            return "深（≥200·每2天至少1件）"
        return "中（100~199·每周约2件）" if v >= 100 else "浅（50~99·每周约1件）"

    df.loc[df["客观高"], "客观档"] = df.loc[df["客观高"], "体检点_全覆盖"].apply(c_tier)
    df.loc[df["主观高"], "主观档"] = df.loc[df["主观高"], "诉求件_12345"].apply(s_tier)

    n_c, n_s, n_o = int(df["客观高"].sum()), int(df["主观高"].sum()), int(df["两表重叠"].sum())
    print(f"客观线 ≥{C_LINE} 个问题点 → 客观表 {n_c} 社区")
    print(f"主观线 ≥{S_LINE} 件（每周约 1 件）→ 主观表 {n_s} 社区")
    print(f"两表重叠（落图叠加可见）：{n_o} 社区")
    print(f"\n客观档分布: {df[df['客观高']]['客观档'].value_counts().to_dict()}")
    print(f"主观档分布: {df[df['主观高']]['主观档'].value_counts().to_dict()}")

    cols = ["社区", "楼栋数", "体检点_2025", "体检点_2026新增", "体检点_全覆盖", "诉求件_12345",
            "客观高", "主观高", "两表重叠", "客观档", "主观档"]
    print("\n--- 客观表 TOP15（体检点降序）---")
    print(df[df["客观高"]].sort_values("体检点_全覆盖", ascending=False).head(15)[cols[:6] + ["客观档"]].to_string(index=False))
    print("\n--- 主观表 TOP15（诉求件降序）---")
    print(df[df["主观高"]].sort_values("诉求件_12345", ascending=False).head(15)[["社区", "诉求件_12345", "体检点_全覆盖", "主观档"]].to_string(index=False))
    print("\n--- 两表重叠（10 目标）---")
    ov = df[df["两表重叠"]].sort_values("体检点_全覆盖", ascending=False)
    print(ov[["社区", "体检点_全覆盖", "诉求件_12345"]].to_string(index=False))

    df.to_csv(os.path.join(OUT_P7, "page7_绝对值口径_全域_2026-08-17.csv"), index=False, encoding="utf-8-sig")
    print(f"\n[OK] 全表已写（两表口径·覆盖旧版）: page7_绝对值口径_全域_2026-08-17.csv ({len(df)} 社区)")


if __name__ == "__main__":
    main()
