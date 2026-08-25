# -*- coding: utf-8 -*-
"""CB-32 page7 双高社区·双变量主图渲染（zcode·2026-08-13）
红轴=安全量分位 × 蓝轴=民生量分位；双高(p75双阈值)=深品红+粗边框+标名(top10)；
体检独证隐患4社区独立符号；底层叠体检点(方块)+12345点(圆点)。
数据：修正后双高矩阵（民生矩阵物业街面278已修复）。
"""
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, FancyBboxPatch
import os, warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

BASE = r'D:\Github\emotion_map\DATA\analysis'
OUT  = os.path.join(BASE, 'page7小结')
os.makedirs(OUT, exist_ok=True)

# ===== 1. 双高修正矩阵 =====
m = pd.read_csv(os.path.join(OUT, 'page7_双高社区_修正矩阵_2026-08-13.csv'),
                encoding='utf-8-sig', index_col=0)
st75, lt75 = np.percentile(m['安全量'], 75), np.percentile(m['民生量'], 75)
st50, lt50 = np.percentile(m['安全量'], 50), np.percentile(m['民生量'], 50)
m['双高'] = (m['安全量'] >= st75) & (m['民生量'] >= lt75)
dual = m[m['双高']].sort_values('合计', ascending=False)
print(f"双高 {len(dual)} | p75 阈值 安全{st75:.0f}/民生{lt75:.0f}")

# ===== 2. 社区面 + 合并 =====
face = gpd.read_file(r'D:\Github\emotion_map\DATA\boundaries\presets\checkup_配置_社区174.geojson')
fg = face.merge(m, left_on='社区', right_index=True, how='left')
fg['安全量'] = fg['安全量'].fillna(-1)   # 未入并集(无任何问题点) → bin 0
fg['民生量'] = fg['民生量'].fillna(-1)

def sbin(v):  return 0 if v < 0 else (1 if v < st50 else (2 if v < st75 else 3))
def lbin(v):  return 0 if v < 0 else (1 if v < lt50 else (2 if v < lt75 else 3))
fg['sb'], fg['lb'] = fg['安全量'].map(sbin), fg['民生量'].map(lbin)

# 双变量混色：白底 + 红分量(安全) + 蓝分量(民生)；3档=0/0.45/0.9
R = np.array([0.82, 0.20, 0.20]); B = np.array([0.20, 0.28, 0.85]); W = np.array([0.97, 0.97, 0.97])
def bcolor(sr, lr):
    lv = {0: 0.0, 1: 0.4, 2: 0.65, 3: 1.0}
    u, v = lv[sr], lv[lr]
    c = (1 - max(u, v)) * W + u * R * 0.85 + v * B * 0.85
    return tuple(np.clip(c, 0, 1))
fg['color'] = [bcolor(a, b) for a, b in zip(fg['sb'], fg['lb'])]

# ===== 3. 点图层 =====
p_saf = gpd.read_file(os.path.join(BASE, '77项量化/checkup_qty_安全_合并.geojson'))
p_liv = gpd.read_file(os.path.join(BASE, '77项量化/checkup_qty_民生_合并.geojson'))
p_123 = gpd.read_file(os.path.join(BASE, '12345主观/12345_有坐标点.geojson'))
p_123 = p_123[p_123['社区'].notna() & (p_123['社区'] != '')]   # 只叠城市社区内点
print(f"叠加点：体检安全{len(p_saf)} 体检民生{len(p_liv)} 12345城市社区{len(p_123)}")

# ===== 4. 绘图 =====
fig, ax = plt.subplots(figsize=(15, 13), dpi=200)
fg.plot(ax=ax, color=fg['color'], edgecolor='white', linewidth=0.5, zorder=2)

# 双高粗边框
fg[fg['双高'] == True].boundary.plot(ax=ax, color='#4a148c', linewidth=2.2, zorder=4)

# 12345 点（圆·灰·半透明·光栅化）
p_123.plot(ax=ax, marker='o', color='#555555', markersize=2.5, alpha=0.18,
           linewidths=0, rasterized=True, zorder=5)
# 体检点（方块：安全红/民生蓝）
p_saf.plot(ax=ax, marker='s', color='#d73027', markersize=9, alpha=0.55,
           linewidths=0.3, edgecolors='#7f0000', rasterized=True, zorder=6)
p_liv.plot(ax=ax, marker='s', color='#4575b4', markersize=9, alpha=0.55,
           linewidths=0.3, edgecolors='#08306b', rasterized=True, zorder=6)

# 双高 top10 标名
rep = fg.set_index('社区')
top10 = dual.head(10).index.tolist()
for i, nm in enumerate(top10, 1):
    c = rep.loc[nm].geometry.representative_point()
    ax.annotate(f"{i}.{nm.replace('社区','')}", (c.x, c.y), fontsize=9.5, fontweight='bold',
                color='#1a0033', ha='center', va='center', zorder=8,
                bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='#4a148c', alpha=0.85, lw=0.7))

# 体检独证隐患4社区：红五角星 + 虚线边框
SOLO = ['西峡社区', '深圳路社区', '金安岭社区', '镇境山社区']
fg_solo = fg[fg['社区'].isin(SOLO)]
fg_solo.boundary.plot(ax=ax, color='#b30000', linewidth=2.0, linestyle=(0, (4, 2)), zorder=7)
for nm in SOLO:
    c = rep.loc[nm].geometry.representative_point()
    ax.scatter([c.x], [c.y], marker='*', s=260, c='#b30000', edgecolors='white',
               linewidths=0.8, zorder=9)
    ax.annotate(f"★{nm.replace('社区','')}", (c.x, c.y), xytext=(0, -13),
                textcoords='offset points', fontsize=9, fontweight='bold', color='#b30000',
                ha='center', zorder=9)

ax.set_axis_off()

# ===== 5. 图例 =====
lg_x0, lg_y0 = 0.012, 0.985
ax.text(lg_x0, lg_y0, '安全韧性问题 × 民生基础需求 · 双高社区分布',
        transform=ax.transAxes, fontsize=17, fontweight='bold', va='top', color='#1a1a2e')
ax.text(lg_x0, lg_y0 - 0.022, '色 = 双变量分位（红→安全量高 · 蓝→民生量高 · 品红=双高 p75×p75）'
        f'｜双高 {len(dual)}/160 社区（占 174 城市社区 {len(dual)/174*100:.1f}%）',
        transform=ax.transAxes, fontsize=10.5, va='top', color='#444444')

# 3×3 双变量色卡
cell = 0.030
bx, by = lg_x0 + 0.002, lg_y0 - 0.055
labels_s = ['<p50', 'p50–75', '≥p75']; labels_l = ['<p50', 'p50–75', '≥p75']
for i in range(3):
    for j in range(3):
        ax.add_patch(FancyBboxPatch((bx + j*cell*1.15, by - i*cell*1.15), cell, cell,
                     boxstyle='round,pad=0.001', transform=ax.transAxes,
                     fc=bcolor(1+j, 3-i), ec='white', lw=1, zorder=20, clip_on=False))
ax.text(bx - 0.004, by - cell*0.6, '民生\n→高', transform=ax.transAxes, fontsize=8.5,
        ha='right', va='center', color='#08306b')
ax.text(bx + cell*1.7/2, by + cell*0.35, '安全 → 高', transform=ax.transAxes, fontsize=8.5,
        ha='center', va='bottom', color='#7f0000')
ax.text(bx + cell*1.15*2 + cell/2, by - cell*1.15*2 - 0.012,
        f'双高象限（≥p75×≥p75·{len(dual)} 社区）', transform=ax.transAxes, fontsize=9,
        ha='center', color='#4a148c', fontweight='bold')

legend_items = [
    Line2D([0],[0], marker='o', color='w', markerfacecolor='#555555', alpha=0.6, markersize=7,
           label='12345 诉求点（社区内·半透明）'),
    Line2D([0],[0], marker='s', color='w', markerfacecolor='#d73027', markeredgecolor='#7f0000',
           markersize=8, label='体检·安全问题点（928）'),
    Line2D([0],[0], marker='s', color='w', markerfacecolor='#4575b4', markeredgecolor='#08306b',
           markersize=8, label='体检·民生问题点（757）'),
    Line2D([0],[0], marker='*', color='w', markerfacecolor='#b30000', markeredgecolor='white',
           markersize=14, label='体检独证·结构隐患社区（热线少诉）'),
    Patch(fc='none', ec='#4a148c', lw=2, label='双高社区边界（粗紫）'),
    Patch(fc='none', ec='#b30000', lw=2, ls='--', label='体检独证社区边界（红虚线）'),
]
ax.legend(handles=legend_items, loc='lower left', fontsize=9.5, frameon=True,
          framealpha=0.92, edgecolor='#cccccc', borderpad=0.9)

# 右下角双高榜
tx = 0.985
ax.text(tx, 0.045, '双高社区 TOP10（合计降序）', transform=ax.transAxes, fontsize=10.5,
        fontweight='bold', ha='right', color='#1a0033')
for i, nm in enumerate(top10, 1):
    r = dual.loc[nm]
    ax.text(tx, 0.045 - i*0.0175, f"{i:>2}. {nm.replace('社区','')}  安{r['安全量']} · 民{r['民生量']} · 计{r['合计']}",
            transform=ax.transAxes, fontsize=9, ha='right',
            color='#333333' if i > 8 else '#1a0033')
ax.text(tx, 0.045 - 12.5*0.0175,
        '注：体检独证 = 西峡/深圳路/金安岭/镇境山（结构/围护/燃气隐患集中，12345 少诉）\n'
        '数据：体检落图928+757 · 12345社区内点 · 民生矩阵已修复物业街面278点（zcode复核版）',
        transform=ax.transAxes, fontsize=7.8, ha='right', color='#888888', va='top')

out_png = os.path.join(OUT, 'page7_双高社区_双变量主图.png')
plt.savefig(out_png, dpi=200, bbox_inches='tight', facecolor='white', pad_inches=0.15)
plt.close()
print('已输出:', out_png)

# 附：修正双高矩阵落盘（供 Codex 总表）
m.reset_index().rename(columns={'index': '社区'}).to_csv(
    os.path.join(OUT, 'page7_双高社区_修正矩阵_2026-08-13.csv'), index=False, encoding='utf-8-sig')
print('已输出: page7_双高社区_修正矩阵_2026-08-13.csv')
