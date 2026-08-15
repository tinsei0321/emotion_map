# -*- coding: utf-8 -*-
# CB-37 评审核验：双密度分布 + p81阈值 + 高社区计数 + 社区总数(120/130/118口径厘清)
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pandas as pd
import numpy as np

ROOT = r"d:\Github\emotion_map"
SAFE = os.path.join(ROOT, "DATA/analysis/安全韧性/安全韧性_社区3类矩阵.csv")
LIVE = os.path.join(ROOT, "DATA/analysis/民生基础/民生_社区5类矩阵.csv")
HOT = os.path.join(ROOT, "DATA/analysis/12345主观/12345_社区x9类_西陵伍家.csv")
DEN = os.path.join(ROOT, "DATA/analysis/page7小结/社区规模分母_174.csv")

safe = pd.read_csv(SAFE); live = pd.read_csv(LIVE)
hot = pd.read_csv(HOT); den = pd.read_csv(DEN)
print("安全矩阵", safe.shape, list(safe.columns))
print("民生矩阵", live.shape, list(live.columns))
print("12345csv", hot.shape, list(hot.columns))
print("楼栋分母", den.shape, list(den.columns))
print("楼栋分母样例:", den.head(3).to_dict("records"))

def norm(s):
    return str(s).replace("社区", "").strip()

safe["k"] = safe["社区"].apply(norm)
live["k"] = live["社区"].apply(norm)
hot["k"] = hot["社区"].apply(norm) if "社区" in hot.columns else hot.iloc[:, 0].apply(norm)

# 体检点(安全3类+民生5类)
sp = safe.set_index("k")[["市政管网", "安全消防", "住房"]].sum(axis=1)
lp = live.set_index("k")[["公服设施", "住房", "停车设施", "交通设施", "物业街面"]].sum(axis=1)
ck = sp.add(lp, fill_value=0)

# 诉求件(剔其他)
hotk = hot.set_index("k")
othercols = {"其他", "社区", "k"}
cls = [c for c in hotk.columns if c not in othercols and hotk[c].dtype.kind in "iuf"]
print("\n12345诉求列(剔其他):", cls)
ap = hotk[cls].sum(axis=1)

# 楼栋分母：探测社区列+楼栋列
dcol_community = "社区" if "社区" in den.columns else den.columns[0]
dcols_num = [c for c in den.columns if den[c].dtype.kind in "iuf"]
print(f"楼栋分母 社区列={dcol_community} 数值列={dcols_num}")
dcol_ld = "bldg_n"  # 楼栋数列(非area_km2面积)
den["k"] = den[dcol_community].apply(norm)
dn = den.set_index("k")[dcol_ld]

# 合并（以西陵+伍家体检对象范围为准 = ck 并集 社区）
allk = sorted(set(ck.index) | set(ap.index))
df = pd.DataFrame({"体检点": ck, "诉求件": ap, "楼栋": dn}).reindex(allk)
df["楼栋"] = df["楼栋"].fillna(0)
df = df[df["楼栋"] > 0].copy()  # 有楼栋的社区
df["体检密度"] = (df["体检点"] / df["楼栋"] * 100).round(1)
df["诉求密度"] = (df["诉求件"] / df["楼栋"] * 100).round(1)
df = df.fillna(0)

print(f"\n>>> 有楼栋社区总数(体检+诉求并集) = {len(df)}")
print(f"   有体检点社区={ (df['体检点']>0).sum() }  有诉求件社区={ (df['诉求件']>0).sum() }")

# p81 阈值（前19%）
p81c = np.percentile(df["体检密度"], 81)
p81s = np.percentile(df["诉求密度"], 81)
print(f"\n>>> p81阈值: 体检密度≥{p81c:.2f}  诉求密度≥{p81s:.2f}")

df["类"] = "其他"
df.loc[(df["体检密度"] >= p81c) & (df["诉求密度"] >= p81s), "类"] = "双高"
df.loc[(df["体检密度"] >= p81c) & (df["诉求密度"] < p81s), "类"] = "客观高"
df.loc[(df["体检密度"] < p81c) & (df["诉求密度"] >= p81s), "类"] = "主观高"
cnt = df["类"].value_counts().to_dict()
print(f">>> 分类计数: {cnt}")
print(f"   高社区合计(双高+客观高+主观高) = {cnt.get('双高',0)+cnt.get('客观高',0)+cnt.get('主观高',0)}")

print("\n--- 客观高 TOP12 (体检密度降序) ---")
print(df[df["类"] == "客观高"].sort_values("体检密度", ascending=False).head(12)[["体检点", "体检密度", "诉求件", "诉求密度", "楼栋"]].to_string())
print("\n--- 主观高 TOP12 (诉求密度降序) ---")
print(df[df["类"] == "主观高"].sort_values("诉求密度", ascending=False).head(12)[["诉求件", "诉求密度", "体检点", "体检密度", "楼栋"]].to_string())
print("\n--- 双高 ---")
print(df[df["类"] == "双高"][["体检点", "体检密度", "诉求件", "诉求密度", "楼栋"]].to_string())
