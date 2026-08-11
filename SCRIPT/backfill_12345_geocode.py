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
    # CB-23 P1-2：过滤离群坐标（超出宜昌范围 111-112/30-31 的 geocode 误匹配 → 置空·标 miss）
    _YICHANG = lambda lon, lat: (111.0 <= lon <= 112.0) and (30.0 <= lat <= 31.0)
    # 回填
    filled = 0
    for i, r in df.iterrows():
        p = str(r['place_name']) if pd.notna(r['place_name']) else ''
        if p in loc:
            _lon, _lat = loc[p][0], loc[p][1]
            if _YICHANG(_lon, _lat):  # P1-2：离群坐标置空·标 miss
                df.at[i, 'lon'] = _lon
                df.at[i, 'lat'] = _lat
                df.at[i, 'geocode_status'] = 'ok'
                filled += 1
            else:
                df.at[i, 'lon'] = float('nan')
                df.at[i, 'lat'] = float('nan')
                df.at[i, 'geocode_status'] = 'miss'
        else:
            df.at[i, 'lon'] = float('nan')
            df.at[i, 'lat'] = float('nan')
            df.at[i, 'geocode_status'] = 'miss'
    # region 兜底（place_source=region·用 REGION:区·修复 2026-08-11：原判断 lon=='' 对 float 空串失效）
    for i, r in df.iterrows():
        lon_v = df.at[i, 'lon']
        empty = (pd.isna(lon_v)) or (isinstance(lon_v, str) and lon_v.strip() == '') or (not lon_v)
        if r['place_source'] == 'region' and empty:
            reg = r['region']
            key = f"REGION:{reg}"
            # 兼容：place_name 可能是区名（西陵区）或 REGION:区
            if key in loc:
                df.at[i, 'lon'] = loc[key][0]
                df.at[i, 'lat'] = loc[key][1]
                df.at[i, 'geocode_status'] = 'region'
                filled += 1
            elif str(r['place_name']) in loc:
                df.at[i, 'lon'] = loc[str(r['place_name'])][0]
                df.at[i, 'lat'] = loc[str(r['place_name'])][1]
                df.at[i, 'geocode_status'] = 'region'
                filled += 1
    df.to_csv(RAW_CSV, index=False, encoding='utf-8-sig')
    print(f"[OK] 回填 {filled}/{len(df)} 行 lon/lat·落 {RAW_CSV}")
    print("geocode_status 分布:", df['geocode_status'].value_counts().to_dict())


if __name__ == '__main__':
    main()
