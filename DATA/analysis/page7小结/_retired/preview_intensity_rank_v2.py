# -*- coding: utf-8 -*-
"""CB-33 强度排名 v2（zcode·2026-08-13 深夜）
数据更新：12345社区矩阵重做（ok精确点口径 7,656=安全1,167+民生6,487+其他2，区质心剔除，伪行已清）
体检侧：源头重建口径（928/755）——官方民生矩阵仍479缺陷未修，禁用
算法同v1：楼栋分母率化→EB收缩→4维百分位等权0.25合成
"""
import geopandas as gpd
import pandas as pd
import numpy as np
import os, warnings
warnings.filterwarnings('ignore')

BASE = r'D:\Github\emotion_map\DATA'
OUT = os.path.join(BASE, 'analysis', 'page7小结')

# ===== 1. 分子 =====
m = pd.read_csv(os.path.join(OUT, 'page7_双高社区_修正矩阵_2026-08-13.csv'),
                encoding='utf-8-sig', index_col='社区')[['体检安全', '体检民生']]
c = pd.read_csv(os.path.join(BASE, 'analysis', '12345主观', '12345_社区x9类.csv'), encoding='utf-8-sig')
assert '（范围外/未匹配）' not in c['社区'].values
cs = c[['社区', '管网安全', '出行安全', '消防安全', '环境安全']].copy()
cs['12345安全'] = cs.iloc[:, 1:].sum(axis=1)
cm = c[['社区', '噪声', '停车', '住宅', '出行', '物业']].copy()
cm['12345民生'] = cm.iloc[:, 1:].sum(axis=1)
d = m.join(cs.set_index('社区')[['12345安全']], how='outer') \
     .join(cm.set_index('社区')[['12345民生']], how='outer').fillna(0).astype(int)
print(f"并集 {len(d)} | 体检安{d['体检安全'].sum()}/民{d['体检民生'].sum()} | 12345安{d['12345安全'].sum()}/民{d['12345民生'].sum()}")

# ===== 2. 分母 =====
bld = gpd.read_file(os.path.join(BASE, 'analysis', '77项量化', 'checkup_配置_楼栋质心.geojson'))
bldg = bld.groupby('SSSQ').size().rename('bldg_n')
face = gpd.read_file(os.path.join(BASE, 'boundaries', 'presets', 'checkup_配置_社区174.geojson'))
face['area_km2'] = face.to_crs('EPSG:4546').area / 1e6
area = face.set_index('社区')['area_km2']
xq = gpd.read_file(os.path.join(BASE, 'analysis', '体检对象_小区_面.geojson'))
xq['resi_km2'] = xq.to_crs('EPSG:4546').area / 1e6
resi = xq.groupby('SSSQ')['resi_km2'].sum()
d = d.join(bldg).join(area).join(resi)
d['bldg_n'] = d['bldg_n'].fillna(0).astype(int)
d['area_km2'] = d['area_km2'].fillna(0)
d['resi_km2'] = d['resi_km2'].fillna(0)
excluded = d[d['bldg_n'] <= 0].index.tolist()
d = d[d['bldg_n'] > 0].copy()
print(f"剔除楼栋=0: {excluded} | 参与排名 {len(d)}")

# ===== 3. 率化 =====
r = pd.DataFrame(index=d.index)
r['TJ安/百栋'] = d['体检安全'] / d['bldg_n'] * 100
r['TJ民/百栋'] = d['体检民生'] / d['bldg_n'] * 100
r['热线安/千栋'] = d['12345安全'] / d['bldg_n'] * 1000
r['热线民/千栋'] = d['12345民生'] / d['bldg_n'] * 1000
denom_a = d['resi_km2'].where(d['resi_km2'] > 0.01, d['area_km2'])
r['体检点/km2'] = (d['体检安全'] + d['体检民生']) / denom_a
r['热线件/km2'] = (d['12345安全'] + d['12345民生']) / denom_a

# ===== 4. EB收缩 =====
def eb_shrink(O, D):
    r_bar = O.sum() / D.sum()
    raw = O / D
    s_w2 = (D * (raw - r_bar) ** 2).sum() / D.sum()
    v = max(s_w2 - r_bar * (1.0 / D).mean(), 1e-12)
    k = r_bar / v
    return (O + k * r_bar) / (D + k), k, r_bar

dims = [('体检安全', 100, 'TJ安EB'), ('体检民生', 100, 'TJ民EB'),
        ('12345安全', 1000, '热线安EB'), ('12345民生', 1000, '热线民EB')]
for col, bs, name in dims:
    s, k, rb = eb_shrink(d[col].astype(float), d['bldg_n'].astype(float))
    r[name] = s * bs
    print(f"EB {name}: k={k:.2f} 全局率={rb:.4f}")

# ===== 5. 合成 =====
eb_cols = [n for _, _, n in dims]
r['score'] = r[eb_cols].rank(pct=True).mean(axis=1)
r = r.sort_values('score', ascending=False)
r['rank_v2'] = range(1, len(r) + 1)

# ===== 6. 与v1对比（数据变更效应）=====
v1 = pd.read_csv(os.path.join(OUT, 'page7_强度排名预览_2026-08-13.csv'),
                 encoding='utf-8-sig', index_col='社区')
r['rank_v1'] = v1['rank_new'].reindex(r.index)
rho = r[['rank_v1', 'rank_v2']].corr(method='spearman').iloc[0, 1]
print(f"\nSpearman ρ(v1旧12345口径 vs v2 ok口径) = {rho:.3f}")

# ===== 7. 落盘 =====
out = d.join(r).sort_values('rank_v2')
out.index.name = '社区'
out.to_csv(os.path.join(OUT, 'page7_强度排名预览v2_2026-08-13.csv'), encoding='utf-8-sig')

# ===== 8. 预览 =====
pd.set_option('display.width', 220)
top = out.head(15)[['bldg_n', '体检安全', '体检民生', '12345安全', '12345民生',
                    'TJ安EB', 'TJ民EB', '热线安EB', '热线民EB', 'score', 'rank_v1']].copy()
for c in ['TJ安EB', 'TJ民EB', '热线安EB', '热线民EB']:
    top[c] = top[c].round(1)
top['score'] = top['score'].round(3)
print("\n===== v2 强度 TOP15（ok口径·EB·等权0.25）=====")
print(top.to_string())

anchors = ['港务社区', '汕头路社区', '香锦社区', '果园路社区', '宝联社区', '胜利二路社区',
           '临江溪社区', '金安岭社区', '西峡社区', '深圳路社区', '镇境山社区', '万达社区']
sub = out.reindex([a for a in anchors if a in out.index])
print("\n===== 锚点社区 v1→v2 =====")
print(sub[['rank_v1', 'rank_v2', 'bldg_n', '12345安全', '12345民生', 'score']].round(3).to_string())
print("\n升降最大TOP8:")
mv = (r['rank_v1'] - r['rank_v2']).sort_values()
print(pd.DataFrame({'升': mv.head(4), '降': mv.tail(4).iloc[::-1]}).to_string())
print(f"\n落盘: {os.path.join(OUT, 'page7_强度排名预览v2_2026-08-13.csv')}")
