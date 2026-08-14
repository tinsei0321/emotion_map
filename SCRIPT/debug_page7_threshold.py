# -*- coding: utf-8 -*-
# page7 分层阈值 28.57/146.67 溯源（p75 反推）。
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "DATA", "analysis")


def main():
    den = pd.read_csv(os.path.join(A, "page7小结", "社区规模分母_174.csv"), encoding="utf-8-sig", index_col=0)
    safe = pd.read_csv(os.path.join(A, "安全韧性", "安全韧性_社区3类矩阵.csv"), encoding="utf-8-sig", index_col=0)
    minm = pd.read_csv(os.path.join(A, "民生基础", "民生_社区5类矩阵.csv"), encoding="utf-8-sig", index_col=0)
    c9 = pd.read_csv(os.path.join(A, "12345主观", "12345_社区x9类.csv"), encoding="utf-8-sig", index_col=0)

    bld = den["bldg_n"]
    tj = safe["总点数"].reindex(bld.index).fillna(0) + minm["总点数"].reindex(bld.index).fillna(0)
    subj = c9[["管网安全", "出行安全", "消防安全", "环境安全", "噪声", "停车", "住宅", "出行", "物业"]].sum(axis=1)
    df = pd.DataFrame({"bldg": bld, "tj": tj, "subj": subj}).fillna(0)
    df = df[df["bldg"] > 0]
    df["obj_den"] = df["tj"] / df["bldg"] * 100
    df["sub_den"] = df["subj"] / df["bldg"] * 100

    print(f"楼栋>0 社区 {len(df)}")
    print(f"客观密度 p50/p75/p80/p90 = {df.obj_den.quantile(.5):.2f}/{df.obj_den.quantile(.75):.2f}/{df.obj_den.quantile(.8):.2f}/{df.obj_den.quantile(.9):.2f}")
    print(f"主观密度 p50/p75/p80/p90 = {df.sub_den.quantile(.5):.2f}/{df.sub_den.quantile(.75):.2f}/{df.sub_den.quantile(.8):.2f}/{df.sub_den.quantile(.9):.2f}")
    # 28.57 / 146.67 的分位数
    print(f"客观 28.57 处于全样本分位 = {(df.obj_den < 28.57).mean()*100:.0f}%")
    print(f"主观 146.67 处于全样本分位 = {(df.sub_den < 146.67).mean()*100:.0f}%")
    dfo = df[df.tj > 0]
    dfs = df[df.subj > 0]
    dfo2 = df[(df.tj > 0) & (df.subj > 0)]
    print(f"有体检点 {len(dfo)} 客观p75={dfo.obj_den.quantile(.75):.2f}")
    print(f"有诉求 {len(dfs)} 主观p75={dfs.sub_den.quantile(.75):.2f}")
    print(f"双覆盖(体检+诉求) {len(dfo2)} 客观p75={dfo2.obj_den.quantile(.75):.2f} 主观p75={dfo2.sub_den.quantile(.75):.2f}")

    # 用 28.57/146.67 切
    dh = df[(df.obj_den >= 28.57) & (df.sub_den >= 146.67)]
    print(f"\n阈值 28.57/146.67 → 双高 {len(dh)} 个: {sorted(dh.index)}")
    oh = df[(df.obj_den >= 28.57) & (df.sub_den < 146.67)]
    print(f"客观高 {len(oh)} 个")
    sh = df[(df.obj_den < 28.57) & (df.sub_den >= 146.67)]
    print(f"主观高 {len(sh)} 个")
    # 28.57 / 146.67 是否正好是某社区密度
    exact_obj = df[abs(df.obj_den - 28.57) < 0.01]
    exact_sub = df[abs(df.sub_den - 146.67) < 0.01]
    print(f"\n客观密度≈28.57 的社区: {[(i, round(v,2)) for i,v in exact_obj.obj_den.items()]}")
    print(f"主观密度≈146.67 的社区: {[(i, round(v,2)) for i,v in exact_sub.sub_den.items()]}")


if __name__ == "__main__":
    main()
