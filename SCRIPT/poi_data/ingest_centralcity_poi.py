#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中心城区真实 POI 入库（一次性转换脚本）
═══════════════════════════════════════════════════════════
读 DATA/POI/yichang_pois_wgs84.geojson（3220 真实高德 POI·WGS84，新爬取）
→ 落 SCRIPT/poi_data/amap_poi_centralcity_wgs84.json（place_layer `_read_pois` 期望格式）

替代 sim_centralcity_poi.py 的 sim_cc fallback 产出——真实数据到位后，sim 生成器转为
dormant（仅 AMAP_KEY 永久缺失时才回退重跑）。place_layer 经 `_AMAP_POI_CC_PATH` 自动装载，
零代码改动。

字段映射（新 geojson schema → place_layer schema）：
  coordinates        → lng / lat
  category（短大类） → baidu_level1（保真·搜索 fuzzy 用）
  keyword（细分）    → baidu_level2
  district           → area
  poi_id             → poi_id（文件留存·审计；_read_pois 加载期 drop，无碍）
  category → 4×5     → domain / element（经本脚本 _CAT_TO_4X5，新文件 10 类专属映射）
  source             → 'amap_cc'（真实中心城区·区别于 'amap' 核心 / 'sim_cc' fallback）

去重：按 poi_id 文件内去重（防爬取重复）。与 1270 核心主城（amap_poi_wgs84.json，无 poi_id）
的地理重叠暂不去重——核心 POI 密度本就高于外围，双计对 demo 的「真实平衡」可接受；
若需精确，可后续加空间去重。

用法：
    py SCRIPT/poi_data/ingest_centralcity_poi.py
═══════════════════════════════════════════════════════════
"""
import os
import sys
import json
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPT = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_SCRIPT)
for _p in (_ROOT, _SCRIPT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

try:
    from core.utils import safe_print as _safe_print
except Exception:
    def _safe_print(s, **k):
        try:
            print(s)
        except Exception:
            pass

# ── 路径 ──
SRC = os.path.join(_ROOT, 'DATA', 'POI', 'yichang_pois_wgs84.geojson')
OUT = os.path.join(_HERE, 'amap_poi_centralcity_wgs84.json')
CORE_1270 = os.path.join(_HERE, 'amap_poi_wgs84.json')   # 1270 核心主城（仅统计参考·不去重）

# ── 新文件 10 类短大类 → 4×5（domain, element）专属映射 ──
# 与 poi_4x5_map.AMAP_L1_TO_4X5（高德 13 大类）平行——本表是新爬取文件自定义短类别的单源；
# 设计哲学对齐 DOMAIN_WEIGHTS（operation 偏重符合主城商业餐饮密度，医疗/政府/交通落治理保平衡）。
_CAT_TO_4X5 = {
    '餐饮': ('urban_operation', 'service'),     # 餐厅
    '住宅': ('urban_renewal', 'service'),        # 住宅小区 → 更新·服务（居住/物业焦点）
    '医疗': ('urban_governance', 'service'),     # 医院 → 治理·服务（公共医疗）
    '商业': ('urban_operation', 'service'),      # 商场/购物
    '办公': ('urban_operation', 'service'),      # 写字楼
    '教育': ('urban_operation', 'culture'),      # 学校/大学 → 运营·文化
    '政府': ('urban_governance', 'service'),     # 政府机构
    '酒店': ('urban_operation', 'service'),      # 住宿
    '交通': ('urban_governance', 'facility'),    # 火车站/公交 → 治理·设施
    '公园': ('urban_operation', 'environment'),  # 公园/绿地 → 运营·环境
}
_DEFAULT_4X5 = ('urban_operation', 'service')


def main():
    if not os.path.exists(SRC):
        _safe_print('[ERR] 源文件不存在: {}'.format(SRC))
        sys.exit(2)

    gj = json.load(open(SRC, encoding='utf-8'))
    feats = gj.get('features', [])
    _safe_print('[LOAD] 源 POI = {} 条 ({})'.format(len(feats), SRC))

    seen_pid = set()       # poi_id 文件内去重
    out = []
    miss_cat = 0
    miss_pid = 0
    for ft in feats:
        p = ft.get('properties') or {}
        c = ft.get('geometry', {}).get('coordinates') or []
        if len(c) < 2:
            continue
        lng, lat = c[0], c[1]
        if lng is None or lat is None:
            continue
        pid = p.get('poi_id')
        if pid:
            if pid in seen_pid:
                continue
            seen_pid.add(pid)
        else:
            miss_pid += 1
        cat = p.get('category', '') or ''
        domain, element = _CAT_TO_4X5.get(cat, _DEFAULT_4X5)
        if cat not in _CAT_TO_4X5:
            miss_cat += 1
        out.append({
            'lng': float(lng),
            'lat': float(lat),
            'name': p.get('name', ''),
            'weight': 1.0,
            'radius_m': 400,
            'baidu_level1': cat,                 # 保真短大类（搜索 fuzzy 用真实类别）
            'baidu_level2': p.get('keyword', '') or cat,
            'area': p.get('district', '') or '宜昌',
            'domain': domain,
            'element': element,
            'source': 'amap_cc',                 # 真实中心城区（vs 核心 amap / fallback sim_cc）
            'poi_id': pid or '',                 # 文件留存审计；place_layer 加载期 drop
        })

    json.dump({'pois': out}, open(OUT, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    # ── 统计 ──
    cat_c = Counter(p['baidu_level1'] for p in out)
    dom_c = Counter(p['domain'] for p in out)
    dist_c = Counter(p['area'] for p in out)
    n_core = 0
    if os.path.exists(CORE_1270):
        try:
            n_core = len(json.load(open(CORE_1270, encoding='utf-8')).get('pois', []))
        except Exception:
            pass

    _safe_print('[OK] {} POI -> {}'.format(len(out), OUT))
    _safe_print('  去重 drop（poi_id 重复）: {}'.format(len(feats) - len(out)))
    _safe_print('  无 poi_id（保留·无法去重）: {}'.format(miss_pid))
    _safe_print('  类别未命中 _CAT_TO_4X5（落默认 operation×service）: {}'.format(miss_cat))
    _safe_print('  类别分布: {}'.format(dict(cat_c.most_common())))
    _safe_print('  domain: {}'.format(dict(dom_c.most_common())))
    _safe_print('  district top: {}'.format(dist_c.most_common(6)))
    if n_core:
        _safe_print('  合并预期: 1270 核心 + {} CC = {} 总（all_pois 不去重，核心密度本就高，双计可接受）'.format(
            len(out), n_core + len(out)))
    _safe_print('  覆盖 bbox: lng[{:.4f},{:.4f}] lat[{:.4f},{:.4f}]'.format(
        min(p['lng'] for p in out), max(p['lng'] for p in out),
        min(p['lat'] for p in out), max(p['lat'] for p in out)))


if __name__ == '__main__':
    main()
