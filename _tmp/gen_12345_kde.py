# -*- coding: utf-8 -*-
"""EMC 出图（③档运行产物）：12345 中心城区投诉点 → 核密度（KDE）等值面。

- 数据：DATA/boundaries/presets/checkup_12345_中心城区.geojson（9421 点·2024·WGS84·manifest id=checkup_12345_center·usage=input）
- 引擎：core.spatial_analysis.create_terrain_mesh（F_007·加权高斯 KDE→分位等值线环·与前端 heatmap 同源 Gaussian KDE）
- 输出：DATA/exports/12345_kde/（运行产物·可重算·不入库）
- 用途：render_file 直入口出图（kind=choropleth·value_field=level_raw 密度 sequential）
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import geopandas as gpd  # noqa: E402
from core.spatial_analysis import create_terrain_mesh  # noqa: E402

SRC = os.path.join(REPO, 'DATA', 'boundaries', 'presets', 'checkup_12345_中心城区.geojson')
OUT_DIR = os.path.join(REPO, 'DATA', 'exports', '12345_kde')
OUT = os.path.join(OUT_DIR, '12345_中心城区_核密度_KDE等值面.geojson')

BANDWIDTH_M = 250.0   # 高斯带宽（主城 200-300m 惯例）
CELL_M = 60.0         # 栅格边长
N_LEVELS = 7          # 等值面层数（分位 25%→97%）


def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('gbk', 'replace').decode('gbk'))


def main():
    pts = gpd.read_file(SRC)
    if pts.crs is None:
        pts = pts.set_crs('EPSG:4326')
    else:
        pts = pts.to_crs('EPSG:4326')
    safe_print(f'[LOAD] 12345 点: {len(pts)} · crs={pts.crs} · 列={list(pts.columns)}')

    mesh = create_terrain_mesh(
        pts, polarity='overall',
        bandwidth_m=BANDWIDTH_M, cell_m=CELL_M, n_levels=N_LEVELS,
    )
    safe_print(f'[OK] KDE 等值面环: {len(mesh)} · crs={mesh.crs}')

    # tip 契约：properties 必带 name（render-contract §二）→ 按 _level 分位命名层级
    n = len(mesh)
    mesh = mesh.sort_values('_level', ascending=True)
    mesh['name'] = [f'12345核密度·L{i + 1}/{n}' for i in range(n)]
    mesh['name'] = mesh['name'].astype(str)

    os.makedirs(OUT_DIR, exist_ok=True)
    mesh.to_file(OUT, driver='GeoJSON', encoding='utf-8')
    size_mb = os.path.getsize(OUT) / 1024 / 1024
    safe_print(f'[SAVE] {OUT} · {size_mb:.2f} MB')

    cols = ['name', 'level_raw', '_level', 'point_count', 'polarity_index',
            'score_mean', 'emotion_intensity_mean']
    sample = mesh[cols].head(3).to_dict('records')
    safe_print('[SAMPLE] ' + json.dumps(sample, ensure_ascii=False))


if __name__ == '__main__':
    main()
