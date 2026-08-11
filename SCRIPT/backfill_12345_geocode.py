# -*- coding: utf-8 -*-
"""12345 中转版 geocode 回填：12345_geocode_cache.json → 中转版 lon/lat。

策略（CB-23·2026-08-11）：
- content/office 高/中置信行：place_name 匹配缓存（干净地名 geocode）→ 回填 lon/lat
- region 兜底行：region 质心（缓存 REGION:*）
- 未命中/无坐标：lon/lat 留空（诚实标注·不强填）

产出：12345_情绪地图中转版.csv 回填 lon/lat（新增 geocode_status 列）
用法：py SCRIPT/backfill_12345_geocode.py
"""
import json
import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

ZX = r"D:/OneDrive/2026/15_城市更新专项规划研究/1 宜昌市城市体检/EMC数据中转站/06_主观数据治理"
RAW_CSV = os.path.join(ZX, '12345_情绪地图中转版.csv')
CACHE = os.path.join(ZX, '12345_geocode_cache.json')


def main():
    cache = json.load(open(CACHE, encoding='utf-8'))
    df = pd.read_csv(RAW_CSV, encoding='utf-8-sig')
    # 坐标索引：place_name → (lon,lat)·REGION:区 → 区质心
    loc = {}
    for k, v in cache.items():
        if v:  # 命中或 region
            if isinstance(v, dict) and v.get('region'):
                loc[k] = (v['lon'], v['lat'])  # REGION:区
            else:
                loc[k] = (v['lon'], v['lat'])
    # 回填
    filled = 0
    for i, r in df.iterrows():
        p = str(r['place_name']) if pd.notna(r['place_name']) else ''
        if p in loc:
            df.at[i, 'lon'] = loc[p][0]
            df.at[i, 'lat'] = loc[p][1]
            df.at[i, 'geocode_status'] = 'ok'
            filled += 1
        else:
            df.at[i, 'geocode_status'] = 'miss'
    # region 兜底（place_source=region·用 REGION:区）
    for i, r in df.iterrows():
        if r['place_source'] == 'region' and r['lon'] == '' or (pd.isna(r['lon']) if hasattr(r['lon'], '__iter__') else not r['lon']):
            reg = r['region']
            key = f"REGION:{reg}"
            if key in loc:
                df.at[i, 'lon'] = loc[key][0]
                df.at[i, 'lat'] = loc[key][1]
                df.at[i, 'geocode_status'] = 'region'
                filled += 1
    df.to_csv(RAW_CSV, index=False, encoding='utf-8-sig')
    print(f"[OK] 回填 {filled}/{len(df)} 行 lon/lat·落 {RAW_CSV}")
    print("geocode_status 分布:", df['geocode_status'].value_counts().to_dict())


if __name__ == '__main__':
    main()
