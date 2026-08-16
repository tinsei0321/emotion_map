# -*- coding: utf-8 -*-
"""CB-33 强度排名·预览版（zcode·2026-08-13）
算法：楼栋分母率化 → 经验贝叶斯收缩(Poisson-Gamma矩估计) → 4维百分位等权合成
分子：修正矩阵口径（体检安928/体检民755/热线安1491/热线民8394）
"""
import geopandas as gpd
import pandas as pd
import numpy as np
import os, warnings
warnings.filterwarnings('ignore')

BASE = r'D:\Github\emotion_map\DATA'
OUT = os.path.join(BASE, 'analysis', 'page7小结')
os.makedirs(OUT, exist_ok=True)

# ===== 1. 分子（修正矩阵·160社区）=====
m = pd.read_csv(os.path.join(OUT, 'page7_双高社区_修正矩阵_2026-08-13.csv'),
                encoding='utf-8-sig', index_col='社区')
m = m[['体检安全', '体检民生', '12345安全', '12345民生']]
assert (m['体检安全'].sum(), m['体检民生'].sum(), m['12345安全'].sum(), m['12345民生'].sum()) == (928, 755, 1491, 8394)

# ===== 2. 分母 =====
# 2a 楼栋数（SSSQ聚合）
bld = gpd.read_file(os.path.join(BASE, 'analysis', '77项量化', 'checkup_配置_楼栋质心.geojson'))
bldg = bld.groupby('SSSQ').size().rename('bldg_n')
# 2b 行政面积（EPSG:4546 投影）
face = gpd.read_file(os.path.join(BASE, 'boundaries', 'presets', 'checkup_配置_社区174.geojson'))
face['area_km2'] = face.to_crs('EPSG:4546').area / 1e6
area = face.set_index('社区')['area_km2']
# 2c 居住用地面积（小区面投影聚合）
xq = gpd.read_file(os.path.join(BASE, 'analysis', '体检对象_小区_面.geojson'))
xq['resi_km2'] = xq.to_crs('EPSG:4546').area / 1e6
resi = xq.groupby('SSSQ')['resi_km2'].sum()

d = m.join(bldg).join(area).join(resi)
d['bldg_n'] = d['bldg_n'].fillna(0).astype(int)
d['area_km2'] = d['area_km2'].fillna(0)
d['resi_km2'] = d['resi_km2'].fillna(0)
n_nobldg = (d['bldg_n'] == 0).sum()
print(f"矩阵 {len(m)} 社区 | 楼栋缺失(=0): {n_nobldg} | 行政面积缺失: {(d['area_km2']==0).sum()} | 居住用地为0: {(d['resi_km2']==0).sum()}")

# 分母表落盘
den = face.set_index('社区')[['area_km2']].join(bldg).join(resi)
den.to_csv(os.path.join(OUT, '社区规模分母_174.csv'), encoding='utf-8-sig')

# ===== 3. 率化（主口径·楼栋）=====
# 剔除楼栋=0 的社区（分母无效，不参与率排名，单独标注）
excluded = d[d['bldg_n'] <= 0].index.tolist()
d = d[d['bldg_n'] > 0].copy()
print(f"剔除楼栋=0社区 {len(excluded)} 个: {excluded}（不参与强度排名）")

r = pd.DataFrame(index=d.index)
r['TJ安/百栋'] = d['体检安全'] / d['bldg_n'] * 100
r['TJ民/百栋'] = d['体检民生'] / d['bldg_n'] * 100
r['热线安/千栋'] = d['12345安全'] / d['bldg_n'] * 1000
r['热线民/千栋'] = d['12345民生'] / d['bldg_n'] * 1000
# 面积口径（并列呈现·居住用地优先，0则用行政面积）
denom_a = d['resi_km2'].where(d['resi_km2'] > 0.01, d['area_km2'])
r['体检点/km2'] = (d['体检安全'] + d['体检民生']) / denom_a
r['热线件/km2'] = (d['12345安全'] + d['12345民生']) / denom_a

# ===== 4. 经验贝叶斯收缩（Poisson-Gamma·矩估计）=====
def eb_shrink(O, D):
    """s_i=(O_i+k·r̄)/(D_i+k)；k=r̄/v；v=max(0, s_w²-r̄·mean(1/D_i))（要求 D>0 全体）"""
    assert (D > 0).all(), "存在 D<=0，需先剔除"
    r_bar = O.sum() / D.sum()
    raw = O / D
    s_w2 = (D * (raw - r_bar) ** 2).sum() / D.sum()
    v = max(s_w2 - r_bar * (1.0 / D).mean(), 1e-12)
    k = r_bar / v
    s = (O + k * r_bar) / (D + k)
    return s, k, r_bar

dims = [('体检安全', 100, 'TJ安EB'), ('体检民生', 100, 'TJ民EB'),
        ('12345安全', 1000, '热线安EB'), ('12345民生', 1000, '热线民EB')]
eb_params = {}
for col, base, name in dims:
    s, k, rb = eb_shrink(d[col].astype(float), d['bldg_n'].astype(float))
    r[name] = s * base
    eb_params[name] = (round(k, 1), round(rb, 6))
print("EB参数(k, 全局率):", {n: p for n, p in eb_params.items()})

# ===== 5. 合成（EB后4维→百分位→等权0.25）=====
eb_cols = [n for _, _, n in dims]
pct = r[eb_cols].rank(pct=True)
r['score'] = pct.mean(axis=1)
r = r.sort_values('score', ascending=False)
r['rank_new'] = range(1, len(r) + 1)

# ===== 6. 新旧对比 =====
sig = pd.read_csv(os.path.join(BASE, 'analysis', 'page7_sigao_candidates.csv'),
                  encoding='utf-8-sig', index_col='community')
r['rank_old'] = sig['rank'].reindex(r.index)
r['Δ(old-new)'] = r['rank_old'] - r['rank_new']
rho = r[['rank_old', 'rank_new']].corr(method='spearman').iloc[0, 1]
print(f"\nSpearman ρ(旧绝对量排名 vs 新强度排名) = {rho:.3f}")

# ===== 7. 落盘 =====
out = d.join(r).sort_values('rank_new')
out.index.name = '社区'
out.to_csv(os.path.join(OUT, 'page7_强度排名预览_2026-08-13.csv'), encoding='utf-8-sig')

# ===== 8. 终端预览 =====
pd.set_option('display.width', 200)
cols = ['bldg_n', '体检安全', '体检民生', '12345安全', '12345民生', 'TJ安EB', 'TJ民EB', '热线安EB', '热线民EB', 'score']
top20 = out.head(20)[cols].copy()
for c in ['TJ安EB', 'TJ民EB', '热线安EB', '热线民EB']:
    top20[c] = top20[c].round(2)
top20['score'] = top20['score'].round(3)
print("\n===== 强度排名 TOP20（EB收缩后·等权0.25×4）=====")
print(top20.to_string())

anchors = ['港务社区', '宝联社区', '东星社区', '西峡社区', '深圳路社区', '金安岭社区', '镇境山社区', '汕头路社区', '香锦社区', '果园路社区']
print("\n===== 锚点社区新旧对比 =====")
print(out.loc[[a for a in anchors if a in out.index],
              ['rank_old', 'rank_new', 'Δ(old-new)', 'bldg_n', 'score']].to_string())
print(f"\n已落盘: {os.path.join(OUT, 'page7_强度排名预览_2026-08-13.csv')}")
