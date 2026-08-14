# -*- coding: utf-8 -*-
# CB-36 体检点数据管线审计·层次①②③ 只读盘点（不写交付物）
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import geopandas as gpd
import pandas as pd
pd.set_option("display.max_columns", None); pd.set_option("display.width", 220)

SRC = r"D:\OneDrive\2026\15_城市更新专项规划研究\1 宜昌市城市体检\3_gis数据"
ROOT = r"d:\Github\emotion_map"
QTY = os.path.join(ROOT, "DATA", "analysis", "77项量化")
SAFE = os.path.join(ROOT, "DATA", "analysis", "安全韧性")
LIVE = os.path.join(ROOT, "DATA", "analysis", "民生基础")

print("=" * 70)
print("层次① 源头 shp 全量盘点（维度/子类 → 要素数/几何类型/字段）")
print("=" * 70)
rows = []
for dp, ds, files in os.walk(SRC):
    for f in sorted(files):
        if f.lower().endswith(".shp"):
            p = os.path.join(dp, f)
            rel = os.path.relpath(dp, SRC)
            try:
                g = gpd.read_file(p)
                gt = g.geom_type.iloc[0] if len(g) else "EMPTY"
                cols = [c for c in g.columns if c != "geometry"]
                rows.append((rel, f, len(g), gt, cols, g.crs))
            except Exception as e:
                rows.append((rel, f, -1, "ERR", [str(e)[:80]], None))
total = 0
for rel, f, n, gt, cols, crs in rows:
    flag = "" if n >= 0 else " <<<ERR"
    print(f"[{rel}]")
    print(f"   {f}  要素={n} 几何={gt} crs={crs}{flag}")
    print(f"   字段={cols}")
    if n > 0:
        total += n
print(f"\n>>> 源 shp 图层总数={len(rows)}  要素总计={total}")

print("\n" + "=" * 70)
print("层次② 当前产物 checkup_qty 点数据（点数/字段/类型分布/样例）")
print("=" * 70)
targets = [f for f in sorted(os.listdir(QTY)) if f.endswith(".geojson")]
for fn in targets:
    try:
        g = gpd.read_file(os.path.join(QTY, fn))
        cols = [c for c in g.columns if c != "geometry"]
        print(f"\n[{fn}] 要素={len(g)} 几何={(g.geom_type.iloc[0] if len(g) else '?')} 字段={cols}")
        for c in cols:
            vc = g[c].value_counts()
            if 1 < len(vc) <= 25:
                print(f"   <{c}>: {vc.to_dict()}")
        if len(g):
            print("   样例[0]: " + str({k: g[k].iloc[0] for k in cols[:10]}))
    except Exception as e:
        print(f"[{fn}] ERR {e}")

print("\n" + "=" * 70)
print("层次③ 矩阵 csv 合计（对照提取点数）")
print("=" * 70)
for p in [os.path.join(SAFE, "安全韧性_社区3类矩阵.csv"), os.path.join(LIVE, "民生_社区5类矩阵.csv")]:
    df = pd.read_csv(p)
    nums = df.select_dtypes(include="number")
    print(f"\n[{os.path.basename(p)}] 行={len(df)} 列={list(df.columns)}")
    print(f"   各列合计: {nums.sum().to_dict()}")
    print(f"   数值总计: {nums.sum().sum()}")
    print(f"   前3行:\n{df.head(3).to_string()}")
