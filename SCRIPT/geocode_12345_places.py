# -*- coding: utf-8 -*-
"""12345 治理版 geocode 回填 lon/lat（清洗后地点词 → 高德·分批防配额）。

策略（CB-23 项目/12345 落位·2026-08-11）：
- 优先：中心城区 + 高置信地点词（唯一词 ~13415·分批 <7k/批·避高德每日 1 万配额）
- region 兜底：区级（用区质心·6922 行·12%）
- 县市/低置信：暂缓（非两板块中心城区重点）
- 断点续跑：已 geocode 缓存 json·重复跑只补未命中

产出：06/12345_geocode_cache.json（唯一地点词 → lon/lat）+ 中转版回填 lon/lat
用法：py SCRIPT/geocode_12345_places.py [--batch 0|1|all] [--reset]
"""
import json
import os
import re
import sys
import time

import pandas as pd
import requests

sys.stdout.reconfigure(encoding='utf-8')

ZX = r"D:/OneDrive/2026/15_城市更新专项规划研究/1 宜昌市城市体检/EMC数据中转站/06_主观数据治理"
RAW_CSV = os.path.join(ZX, '12345_情绪地图中转版.csv')
CACHE = os.path.join(ZX, '12345_geocode_cache.json')

# 高德 key
_KEY = None
for line in open('.env', encoding='utf-8'):
    if line.startswith('AMAP_KEY='):
        _KEY = line.split('=', 1)[1].strip()
        break

# 区质心（region 兜底·宜昌 4 区 + 夷陵/高新·WGS84 近似）
REGION_CENTROID = {
    '西陵区': (111.287, 30.700), '伍家岗区': (111.333, 30.655),
    '点军区': (111.268, 30.670), '猇亭区': (111.408, 30.578),
    '夷陵区': (111.326, 30.770), '高新区': (111.305, 30.690),
    '当阳市': (111.790, 30.821), '宜都市': (111.456, 30.386),
    '枝江市': (111.759, 30.426), '秭归县': (110.977, 30.825),
    '长阳土家族自治县': (111.198, 30.472), '五峰土家族自治县': (110.674, 30.200),
    '兴山县': (110.752, 31.348), '远安县': (111.640, 31.060),
}

_BATCH = sys.argv[sys.argv.index('--batch') + 1] if '--batch' in sys.argv else 'all'
_RESET = '--reset' in sys.argv


def load_cache():
    if _RESET or not os.path.isfile(CACHE):
        return {}
    try:
        return json.load(open(CACHE, encoding='utf-8'))
    except Exception:
        return {}


def geocode(addr):
    """高德 geocode·返回 (lon,lat) 或 None。"""
    try:
        r = requests.get('https://restapi.amap.com/v3/geocode/geo',
                         params={'key': _KEY, 'address': addr, 'city': '宜昌'}, timeout=8)
        js = r.json()
        if js.get('status') == '1' and js.get('geocodes'):
            loc = js['geocodes'][0]['location'].split(',')
            return (round(float(loc[0]), 6), round(float(loc[1]), 6))
    except Exception:
        pass
    return None


# 噪声过滤（CB-23 实测 49% → 需过滤·66% 干净地名可 geocode）
_TIME_RE = re.compile(r'\d{4}年|\d{1,2}月\d{1,2}日|\d{1,2}:\d{2}|\d{4}-\d{2}|\d{10}')
_TEL_RE = re.compile(r'1\d{10}|电话|反映|138|139')
_SPEECH_RE = re.compile(r'我是|反映|经过|在|于|本人|咨询|进入|旁边|来电|接到')


def is_clean_place(p):
    """干净地名：<15 字·无时间戳/电话/口语前缀。"""
    if not p or len(p) > 15 or len(p) < 2:
        return False
    if _TIME_RE.search(p) or _TEL_RE.search(p) or _SPEECH_RE.search(p):
        return False
    return True


def main():
    df = pd.read_csv(RAW_CSV, encoding='utf-8-sig')
    cache = load_cache()
    # 待 geocode：中心城区 content/office 高/中置信·只保留干净地名（噪声过滤·提命中率）
    sel = df[(df['region_scope'] == '中心城区') & (df['place_source'].isin(['content', 'office']))]
    places = sorted({p for p in sel['place_name'].dropna().unique() if is_clean_place(p)})
    todo = [p for p in places if p not in cache]
    print(f"[LOAD] 中心城区干净地名 {len(places)} 唯一词·已缓存 {len(cache)}·待 {len(todo)}")
    if _BATCH == '0':
        todo = todo[:6000]
    elif _BATCH == '1':
        todo = todo[6000:12000]
    print(f"[BATCH {_BATCH}] geocode {len(todo)} 个")
    hit = 0
    for i, p in enumerate(todo):
        if not p or p in cache:
            continue
        loc = geocode(p)
        if loc:
            cache[p] = {'lon': loc[0], 'lat': loc[1]}
            hit += 1
        else:
            cache[p] = None  # 未命中·缓存防重试
        if (i + 1) % 50 == 0:
            json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
            print(f"  ...{i + 1}/{len(todo)}·命中 {hit}")
        time.sleep(0.08)
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f"[DONE] 本批 {len(todo)}·命中 {hit} = {hit / max(len(todo), 1):.0%}·缓存 {len(cache)}")
    # region 兜底回填区质心
    region_hit = 0
    for _, r in df[df['place_source'] == 'region'].iterrows():
        reg = r['region']
        if reg in REGION_CENTROID:
            cache.setdefault(f"REGION:{reg}", {'lon': REGION_CENTROID[reg][0], 'lat': REGION_CENTROID[reg][1], 'region': True})
            region_hit += 1
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f"[OK] region 兜底 {region_hit} 行区质心·缓存总 {len(cache)}")


if __name__ == '__main__':
    main()
