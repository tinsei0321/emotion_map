#!/usr/bin/env python3
"""
高德真实 POI 拉取（v3.2 数据源）
================================
用 types=typecode 按类型精准拉（替中文名 keywords 全文搜——后者 POI 名称不含类目名，
全宜昌餐饮只返回 25 粒，伍家 POI 漏拉严重）。typecode 按类型拉全类，伍家餐厅/住宅都会到。

约束（SCRIPT/CLAUDE.md）：
  - 读 .env / os.environ['AMAP_KEY']，无则报错退出（不静默跳过）
  - 高德返回 GCJ-02 -> WGS84（复用 core.coord_transform.gcj02_to_wgs84）
  - 主城边界过滤
typecode 依据高德官方分类（050000 餐饮 / 060000 购物 / ...，WebSearch 核对）。
"""
import os
import sys
import json
import time
import urllib.request
import urllib.parse

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

import geopandas as gpd
from shapely.geometry import Point

from core.coord_transform import gcj02_to_wgs84
from core.utils import safe_print
from poi_data.poi_4x5_map import AMAP_L1_TO_4X5   # 高德→4×5 单一权威源（domain/element 经此派生，勿硬编码）

AMAP_URL = 'https://restapi.amap.com/v3/place/text'
CITY = '宜昌'
# (typecode, 中文名) —— 高德 POI 大类 typecode；domain/element 经 AMAP_L1_TO_4X5 派生（单源，值不变）
AMAP_TYPES = [
    (tc, cn) + AMAP_L1_TO_4X5.get(cn, ('urban_operation', 'service'))
    for tc, cn in [
        ('050000', '餐饮服务'),
        ('060000', '购物服务'),
        ('070000', '生活服务'),
        ('080000', '休闲娱乐'),
        ('090000', '体育休闲服务'),
        ('100000', '住宿服务'),
        ('110000', '风景名胜'),
        ('120000', '商务住宅'),          # 住宅小区/写字楼
        ('130000', '政府机构及社会团体'),
        ('140000', '科教文化服务'),     # 学校/图书馆
        ('150000', '交通设施服务'),
        ('160000', '金融保险服务'),
        ('170000', '公司企业'),
    ]
]
PAGE_SIZE = 25
MAX_PAGES = 50          # types 精准，count=该类真实总数，50 页(1250)多数够
SLEEP_S = 0.15

BOUNDARY_MAIN = os.path.join(_ROOT, 'DATA', 'boundaries', '西陵伍家核心主城.geojson')
OUT_FILE = os.path.join(_HERE, 'amap_poi_wgs84.json')


def _load_env():
    """从项目根 .env 加载环境变量（不覆盖已有）。"""
    env_path = os.path.join(_ROOT, '.env')
    if os.path.exists(env_path):
        for line in open(env_path, encoding='utf-8'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())


def _fetch_page(typecode, page):
    """按 typecode 拉一页。返回 (pois, count)；count<0 表出错。"""
    q = urllib.parse.urlencode({
        'key': os.environ['AMAP_KEY'],
        'types': typecode,
        'city': CITY, 'citylimit': 'true',
        'offset': PAGE_SIZE, 'page': page, 'output': 'json',
    })
    try:
        with urllib.request.urlopen(AMAP_URL + '?' + q, timeout=20) as r:
            data = json.loads(r.read().decode('utf-8'))
    except Exception as e:
        safe_print('[AMAP][ERR] {} p{} fetch: {}'.format(typecode, page, e))
        return [], -1
    if data.get('status') != '1':
        safe_print('[AMAP][ERR] {} p{} status={} {}'.format(
            typecode, page, data.get('status'), data.get('info')))
        return [], -1
    return data.get('pois') or [], int(data.get('count', 0))


def pull():
    _load_env()
    if not os.environ.get('AMAP_KEY'):
        safe_print('[AMAP][ERR] 无 AMAP_KEY。set AMAP_KEY=<key> 后重跑（不静默跳过）。')
        sys.exit(2)

    main_poly = gpd.read_file(BOUNDARY_MAIN).to_crs('EPSG:4326').geometry.union_all()
    out_pois = []
    seen = set()
    for typecode, cn, domain, element in AMAP_TYPES:
        cat_n = 0
        for page in range(1, MAX_PAGES + 1):
            pois, count = _fetch_page(typecode, page)
            if count < 0:
                break
            for p in pois:
                loc = p.get('location', '')
                if ',' not in loc:
                    continue
                glng, glat = (float(v) for v in loc.split(','))
                wlng, wlat = gcj02_to_wgs84(glng, glat)   # GCJ-02 -> WGS84
                if not main_poly.contains(Point(wlng, wlat)):
                    continue
                pid = p.get('id') or '{}_{:.6f}_{:.6f}'.format(cn, wlng, wlat)
                if pid in seen:
                    continue
                seen.add(pid)
                out_pois.append({
                    'lng': wlng, 'lat': wlat,
                    'name': p.get('name', ''),
                    'weight': 1.0, 'radius_m': 400,
                    'baidu_level1': cn,
                    'baidu_level2': (p.get('type') or cn).split(';')[-1].split('|')[-1],
                    'area': CITY,
                    'domain': domain, 'element': element,
                    'source': 'amap',
                })
                cat_n += 1
            if page * PAGE_SIZE >= count or len(pois) < PAGE_SIZE:
                break
            time.sleep(SLEEP_S)
        safe_print('[AMAP] {}({}) -> {} POI'.format(cn, typecode, cat_n))
        time.sleep(SLEEP_S)
    json.dump({'pois': out_pois}, open(OUT_FILE, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    safe_print('[AMAP][OK] 共 {} POI -> {}'.format(len(out_pois), OUT_FILE))
    safe_print('  下一步：set USE_AMAP_POI=1 && py SCRIPT/generate_l1_mock.py')


if __name__ == '__main__':
    pull()
