# -*- coding: utf-8 -*-
# CB-36 0值社区回查：源安全耐久Polygon sjoin vs checkup_qty点sjoin · 诊断"真实无隐患"vs"面转点错配"
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import geopandas as gpd
import pandas as pd

SRC = r"D:\OneDrive\2026\15_城市更新专项规划研究\1 宜昌市城市体检\3_gis数据"
ROOT = r"d:\Github\emotion_map"
QTY = os.path.join(ROOT, "DATA", "analysis", "77项量化")
COMM_P = os.path.join(ROOT, "DATA", "boundaries", "presets", "checkup_配置_社区174.geojson")
SAFE_M = os.path.join(ROOT, "DATA", "analysis", "安全韧性", "安全韧性_社区3类矩阵.csv")
LIVE_M = os.path.join(ROOT, "DATA", "analysis", "民生基础", "民生_社区5类矩阵.csv")

ZEROS = ["营盘路", "桥北", "万达", "建设", "岳湾路", "伍临路"]

comm = gpd.read_file(COMM_P)
print(f"社区面 crs={comm.crs} 数={len(comm)} 字段={list(comm.columns)}")
# 探测社区名列
namecol = None
for c in comm.columns:
    if c == "geometry": continue
    vals = comm[c].astype(str)
    if vals.str.contains("社区").any():
        namecol = c; break
if not namecol:
    namecol = [c for c in comm.columns if c != "geometry"][0]
print(f"社区名列={namecol}  样例={comm[namecol].head(3).tolist()}")

# 矩阵里搜 0 值社区
print("\n" + "=" * 60)
print("A. 矩阵 csv 中 0 值社区的点数")
print("=" * 60)
for tag, mp in [("安全", SAFE_M), ("民生", LIVE_M)]:
    df = pd.read_csv(mp)
    df_n = df[df["社区"].astype(str).apply(lambda s: any(z in s for z in ZEROS))]
    print(f"\n[{tag}矩阵] 命中0值社区清单的行:")
    if len(df_n):
        print(df_n[["社区"] + [c for c in df.columns if c != "社区"]].to_string())
    else:
        print("  (无——这些社区不在该矩阵的社区清单中，即 sjoin 命中0/未进表)")

# 源安全耐久4类 Polygon 合并
print("\n" + "=" * 60)
print("B. 源头安全耐久 Polygon sjoin 社区（原始楼栋面归属）")
print("=" * 60)
safe_src = [
    ("结构隐患", os.path.join(SRC, r"1城市体检——住房维度\安全耐久\存在结构安全隐患的住宅数量_Polygon\存在结构安全隐患的住宅.shp")),
    ("围护隐患", os.path.join(SRC, r"1城市体检——住房维度\安全耐久\存在围护安全隐患的住宅数量_Polygon\存在围护安全隐患的住宅.shp")),
    ("楼道隐患", os.path.join(SRC, r"1城市体检——住房维度\安全耐久\存在楼道安全隐患的住宅数量_Polygon\存在楼道安全隐患的住宅.shp")),
    ("燃气隐患", os.path.join(SRC, r"1城市体检——住房维度\安全耐久\存在燃气安全隐患的住宅数量_Polygon\存在燃气安全隐患的住宅.shp")),
    ("管线破损", os.path.join(SRC, r"1城市体检——住房维度\功能完备\存在管线管道破损的住宅数量_Polygon\存在管线管道破损的住宅.shp")),
]
frames = []
for tag, p in safe_src:
    g = gpd.read_file(p)
    g = g.to_crs(comm.crs)
    g["隐患类型"] = tag
    frames.append(g[["隐患类型", "geometry"]])
src_all = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=comm.crs)
print(f"源安全图斑总数={len(src_all)}（结构42+围护454+楼道240+燃气6+管线186=928）")
sj_src = gpd.sjoin(src_all, comm[[namecol, "geometry"]], how="left", predicate="intersects")
# 一个面可能 intersects 多社区，取 contains 优先
sj_c = gpd.sjoin(src_all, comm[[namecol, "geometry"]], how="left", predicate="within")
print("\n  [源面·contains/intersects 社区] 0值社区命中:")
for z in ZEROS:
    h_i = sj_src[sj_src[namecol].astype(str).str.contains(z, na=False)]
    print(f"    {z}: intersects命中 {len(h_i)} 面  类型={h_i['隐患类型'].value_counts().to_dict() if len(h_i) else '-'}")
print("\n  [源面·within 社区（完全在内）] 0值社区命中:")
for z in ZEROS:
    h_w = sj_c[sj_c[namecol].astype(str).str.contains(z, na=False)]
    print(f"    {z}: within命中 {len(h_w)} 面")

# checkup_qty 点 sjoin 社区
print("\n" + "=" * 60)
print("C. checkup_qty_安全_合并 点 sjoin 社区（点归属·当前管线口径）")
print("=" * 60)
qty = gpd.read_file(os.path.join(QTY, "checkup_qty_安全_合并.geojson")).to_crs(comm.crs)
sj_q = gpd.sjoin(qty[[c for c in qty.columns if c != "index_right"]], comm[[namecol, "geometry"]], how="left", predicate="within")
miss = sj_q[sj_q[namecol].isna()]
print(f"点总数={len(qty)}  未命中社区(范围外)={len(miss)}")
print("\n  [点·within 社区] 0值社区命中:")
for z in ZEROS:
    h = sj_q[sj_q[namecol].astype(str).str.contains(z, na=False)]
    print(f"    {z}: 点命中 {len(h)}  指标={h['指标'].value_counts().to_dict() if len(h) else '-'}")
