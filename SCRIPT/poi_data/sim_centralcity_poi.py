#!/usr/bin/env python3
"""
中心城区 POI 模拟生成（fallback：AMAP_KEY 缺失时用）
====================================================
真实高德 POI 仅覆西陵伍家（1270 条，pull_amap_poi.py 产出）。中心城区其余无 POI，
而 4×5 归因 + popup nearest_poi 依赖 POI。AMAP_KEY 未配置时走本 fallback：

  - 位置 = 百度热力点真实坐标（central_city ∖ 西陵伍家，value 加权采样 → 真实聚集）
  - 类别 = 从现有 1270 真实高德 POI 的 baidu_level1 分布采样（统计真实）
            + central_outer 调制（人居/公服略加权）
  - domain/element = 经 AMAP_L1_TO_4X5 单源派生（与真实高德同源，4×5 归因一致）
  - name = 类别 × 区名 合成（核心区沿用真实高德名，外围 sim 名——popup 主要流量在核心）
  - area = 点落区行政区划名（9 区 MC 字段）

输出 schema 与 pull_amap_poi.py 完全一致（{pois:[{lng,lat,name,weight,radius_m,
baidu_level1,baidu_level2,area,domain,element,source}]}）→ place_layer 零改接入。
AMAP_KEY 到位后跑 pull_amap_poi.py（中心城区模式）替换本文件即可，引擎无感。
"""
import os
import sys
import json
import random
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

from shapely.geometry import Point, shape
from shapely.ops import unary_union

from poi_data.poi_4x5_map import AMAP_L1_TO_4X5   # 高德大类→4×5 单源

# ── 路径 ──
BAIDU_FILE = os.path.join(_ROOT, 'DATA', 'baidu-heatpoints', '宜昌市_2026041215.geojson')
CC_BOUNDARY = os.path.join(_ROOT, 'DATA', 'boundaries', '中心城区行政区划_1623.geojson')
XLWJ_BOUNDARY = os.path.join(_ROOT, 'DATA', 'boundaries', '西陵伍家核心主城.geojson')
WATER_BOUNDARY = os.path.join(_ROOT, 'DATA', 'boundaries', '现状水系.geojson')   # 水域屏蔽（POI 不落江/湖）
REAL_POI_FILE = os.path.join(_HERE, 'amap_poi_wgs84.json')          # 1270 真实高德（学类别分布）
OUT_FILE = os.path.join(_HERE, 'amap_poi_centralcity_wgs84.json')   # 本脚本产出

TARGET_N = 2600            # central_outer（中心城区∖西陵伍家）目标 POI 数
SEED = 2606

# central_outer 类别调制（外围人居/公服/通勤略加权；商业略降——外围商圈密度低于核心）
OUTER_CAT_BOOST = {
    '商务住宅': 1.6, '生活服务': 1.3, '科教文化服务': 1.4, '交通设施服务': 1.3,
    '风景名胜': 1.2, '政府机构及社会团体': 1.2,
    '餐饮服务': 0.8, '购物服务': 0.85, '住宿服务': 0.9, '休闲娱乐': 0.8,
}

# 名称合成池（按高德大类；外围 popup 流量低，合成名足够）
NAME_POOL = {
    '餐饮服务': ['老字号', '私家菜馆', '火锅店', '烧烤', '面馆', '茶饮', '小吃街'],
    '购物服务': ['便利店', '超市', '购物中心', '专卖店', '农贸市场'],
    '生活服务': ['理发店', '家政', '维修点', '中介', '照相馆'],
    '休闲娱乐': ['棋牌室', 'KTV', '网咖', '游乐场'],
    '体育休闲服务': ['健身房', '体育馆', '羽毛球馆', '游泳馆'],
    '住宿服务': ['商务酒店', '快捷酒店', '宾馆', '民宿'],
    '风景名胜': ['公园', '广场', '景区', '纪念馆', '湿地'],
    '商务住宅': ['花园小区', '雅苑', '公寓', '华庭', '景园', '人家'],
    '政府机构及社会团体': ['街道办', '社区居委会', '政务中心', '派出所'],
    '科教文化服务': ['小学', '中学', '幼儿园', '图书馆', '培训中心', '学院'],
    '交通设施服务': ['公交站', '停车场', '加油站', '客运站', '充电站'],
    '金融保险服务': ['银行', '储蓄所', '保险', 'ATM'],
    '公司企业': ['写字楼', '产业园', '公司', '商办'],
}


def _load_polys(path):
    """读 GeoJSON → (union_poly, [(name, poly), ...])。name 取 properties.MC。"""
    gj = json.load(open(path, encoding='utf-8'))
    polys = []
    names = []
    for f in gj.get('features', []):
        g = f.get('geometry') or {}
        if g.get('type') in ('Polygon', 'MultiPolygon'):
            polys.append(shape(g))
            names.append((f.get('properties') or {}).get('MC', '') or '')
    return unary_union(polys) if polys else None, list(zip(names, polys))


def _resolve_district(lng, lat, districts):
    """点 → 区名（9 区 contains；未命中 ''）。"""
    pt = Point(lng, lat)
    for name, poly in districts:
        if poly.contains(pt):
            return name
    return ''


def main():
    rng = random.Random(SEED)

    # 边界
    cc_union, districts = _load_polys(CC_BOUNDARY)
    xlwj_gj = json.load(open(XLWJ_BOUNDARY, encoding='utf-8'))
    xlwj = unary_union([shape(f['geometry']) for f in xlwj_gj['features']
                        if (f.get('geometry') or {}).get('type') in ('Polygon', 'MultiPolygon')])
    print('[LOAD] 中心城区 {} 区 | 西陵伍家 ∩'.format(len(districts)))

    # 百度热力点 → central_outer 候选（中心城区 ∖ 西陵伍家，value 加权）
    bj = json.load(open(BAIDU_FILE, encoding='utf-8'))
    cands = []   # [(lng, lat, value)]
    for f in bj['features']:
        c = f['geometry']['coordinates']
        v = int(f['properties'].get('value', 0))
        pt = Point(c[0], c[1])
        if cc_union.contains(pt) and not xlwj.contains(pt):
            cands.append((c[0], c[1], v))
    print('[BAIDU] central_outer 候选热力点 {} (value 合计 {})'.format(len(cands), sum(c[2] for c in cands)))
    if not cands:
        print('[ERR] central_outer 无候选热力点'); sys.exit(2)

    # value 加权采样 TARGET_N 个位置（允许重复采样→同热力点散多 POI，jitter 区分）
    weights = [max(c[2], 1) for c in cands]
    picks = rng.choices(cands, weights=weights, k=TARGET_N)

    # 类别分布（学自真实 1270）
    real = json.load(open(REAL_POI_FILE, encoding='utf-8')).get('pois', [])
    cat_dist = Counter(p.get('baidu_level1', '') for p in real if p.get('baidu_level1'))
    cats = list(cat_dist.keys())
    base_w = [cat_dist[c] for c in cats]
    # central_outer 调制
    outer_w = [base_w[i] * OUTER_CAT_BOOST.get(cats[i], 1.0) for i in range(len(cats))]
    print('[CAT] 真实类别分布 {} 类 → central_outer 调制后采样'.format(len(cats)))

    out = []
    for i, (lng, lat, _v) in enumerate(picks):
        cat = rng.choices(cats, weights=outer_w, k=1)[0]
        domain, element = AMAP_L1_TO_4X5.get(cat, ('urban_operation', 'service'))
        district = _resolve_district(lng, lat, districts) or '宜昌'
        name = '{}·{}{:03d}'.format(rng.choice(NAME_POOL.get(cat, ['点位'])), district, i)
        # 微 jitter（POI 不完全重合；~30m）
        jlng = lng + rng.uniform(-0.0003, 0.0003)
        jlat = lat + rng.uniform(-0.0003, 0.0003)
        out.append({
            'lng': round(jlng, 7), 'lat': round(jlat, 7),
            'name': name, 'weight': 1.0, 'radius_m': 400,
            'baidu_level1': cat, 'baidu_level2': cat,
            'area': district, 'domain': domain, 'element': element,
            'source': 'sim_cc',   # 审计标识：中心城区 sim（vs 核心 amap）
        })

    # 水域屏蔽（POI 不落江/湖；与真实高德 _in_water 过滤一致，免 popup "最近 POI 在江里"）
    water = _load_polys(WATER_BOUNDARY)[0] if os.path.exists(WATER_BOUNDARY) else None
    if water is not None:
        before = len(out)
        out = [p for p in out if not water.contains(Point(p['lng'], p['lat']))]
        print('[WATER] 屏蔽落水 POI {} -> {}'.format(before, len(out)))

    json.dump({'pois': out}, open(OUT_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # 统计
    cat_out = Counter(p['baidu_level1'] for p in out)
    dom_out = Counter(p['domain'] for p in out)
    print('[OK] {} POI -> {}'.format(len(out), OUT_FILE))
    print('  类别 top6:', cat_out.most_common(6))
    print('  domain:', dict(dom_out))
    print('  覆盖 bbox: lng[{:.4f},{:.4f}] lat[{:.4f},{:.4f}]'.format(
        min(p['lng'] for p in out), max(p['lng'] for p in out),
        min(p['lat'] for p in out), max(p['lat'] for p in out)))


if __name__ == '__main__':
    main()
