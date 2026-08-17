# -*- coding: utf-8 -*-
"""page7 口径变更：绝对值（弃"每百栋"密度）·全域统一口径（用户定·2026-08-17）。
- 客观轨 = 体检问题点绝对值（全覆盖 = 2025西陵伍家 + 2026新区补充·174社区全域）
- 主观轨 = 12345 诉求件绝对值（九类剔其他·不变·仅西陵伍家118社区有数据·实事求是无数据不参与主观阈值）
- 三类分色：客观 p81@174全域 · 主观 p81@118有数据域 · 双高=两线都过
- 深浅分档：单轨高内分位3档（分位数法·CB-37 建议沿用）
输出：DATA/analysis/page7小结/page7_绝对值口径_全域_2026-08-17.csv + 控制台报告
"""
import os
import sys
import io
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_P7 = os.path.join(ROOT, "DATA", "analysis", "page7小结")


def norm(s):
    return str(s).strip()


def main():
    # ── 客观轨：体检点绝对值（2025 部分 + 2026 增量 → 全覆盖）──
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

    # ── 主观轨：12345 诉求件（九类·ok 精确点·174 全覆盖扩域版 2026-08-17）──
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
            "诉求件_12345": ap.get(c),  # 无数据=None（新区·实事求是）
        })
    df = pd.DataFrame(rows)

    # ── 阈值：客观 p81@174全域 · 主观 p81@118有数据域 ──
    p81_c = np.percentile(df["体检点_全覆盖"], 81)
    ap_vals = df["诉求件_12345"].dropna()
    p81_s = np.percentile(ap_vals, 81)
    print(f"客观绝对值 p81@174全域 = {p81_c:.2f} 点")
    print(f"主观绝对值 p81@{len(ap_vals)}有数据域（174扩域版矩阵）= {p81_s:.2f} 件")

    df["客观过线"] = df["体检点_全覆盖"] >= p81_c
    df["主观过线"] = df["诉求件_12345"].notna() & (df["诉求件_12345"] >= p81_s)
    df["三类"] = "其他"
    df.loc[df["客观过线"] & df["主观过线"], "三类"] = "双高"
    df.loc[df["客观过线"] & ~df["主观过线"], "三类"] = "客观高"
    df.loc[~df["客观过线"] & df["主观过线"], "三类"] = "主观高"

    # ── 深浅分档：单轨高内分位3档（浅/中/深）──
    for cls_name, val_col, tier_col in [("客观高", "体检点_全覆盖", "客观档"),
                                         ("主观高", "诉求件_12345", "主观档")]:
        sub = df[df["三类"] == cls_name]
        if len(sub) == 0:
            continue
        q33, q67 = sub[val_col].quantile([1 / 3, 2 / 3])
        df.loc[df["三类"] == cls_name, tier_col] = df.loc[df["三类"] == cls_name, val_col].apply(
            lambda v: "深" if v >= q67 else ("中" if v >= q33 else "浅"))
        print(f"{cls_name} 分档阈值: 浅<{q33:.1f}≤中<{q67:.1f}≤深")

    cnt = df["三类"].value_counts().to_dict()
    print(f"\n三类计数: {cnt}  高社区合计 = {cnt.get('双高',0)+cnt.get('客观高',0)+cnt.get('主观高',0)}")

    cols_show = ["社区", "楼栋数", "体检点_2025", "体检点_2026新增", "体检点_全覆盖", "诉求件_12345"]
    print("\n--- 双高（绝对值两线都过·全列）---")
    print(df[df["三类"] == "双高"].sort_values("体检点_全覆盖", ascending=False)[cols_show].to_string(index=False))
    print("\n--- 客观高 TOP15（体检点绝对值降序）---")
    print(df[df["三类"] == "客观高"].sort_values("体检点_全覆盖", ascending=False).head(15)[cols_show + ["客观档"]].to_string(index=False))
    print("\n--- 主观高 TOP15（诉求件绝对值降序）---")
    print(df[df["三类"] == "主观高"].sort_values("诉求件_12345", ascending=False).head(15)[cols_show + ["主观档"]].to_string(index=False))

    df.to_csv(os.path.join(OUT_P7, "page7_绝对值口径_全域_2026-08-17.csv"), index=False, encoding="utf-8-sig")
    print(f"\n[OK] 全表已写: page7_绝对值口径_全域_2026-08-17.csv ({len(df)} 社区)")

    # ── 步行道双数据（千米总量 + 处数精准到社区）──
    print("\n--- 步行道：处数（精准到社区·2025+2026+合计）---")
    wl = pd.read_csv(os.path.join(ROOT, "DATA/analysis/民生基础/民生_社区5类矩阵.csv"))[["社区", "交通设施"]].rename(columns={"交通设施": "2025处"})
    wl26 = inc_l[["社区", "交通设施"]].rename(columns={"交通设施": "2026新增处"})
    m = wl.merge(wl26, on="社区", how="outer").fillna(0)
    m["合计处"] = m["2025处"] + m["2026新增处"]
    m = m[m["合计处"] > 0].sort_values("合计处", ascending=False)
    print(m.to_string(index=False))
    print(f"处数合计: {int(m['合计处'].sum())}（2025 {int(m['2025处'].sum())} + 2026 {int(m['2026新增处'].sum())}）")
    print("千米总量: 仅 2025 报告值 2.09 千米（西陵伍家）·2026 无长度值（11 处不占千米）——按真实数据如实呈现")


if __name__ == "__main__":
    main()
