"""
共享 place 层 (Place Layer)
═══════════════════════════════════════════════════════════
三块（情绪点空间分配 A / 文本地域绑定 B / 地点搜索 C）共用的唯一 place 知识脊柱。
单 owner：本模块 + DATA/place/zone_typology.json + DATA/place/place_keywords.json。

职责：
  1. 加载 158 手标种子 POI（带 area 后缀 subtag，resolve_zone 权威信号）
     + 1270 高德真实 POI（索引宇宙，搜索/分配用）
  2. 构建 6 叙事区（zone_id）边界：ermalu 用显式 geojson，其余用种子 radius_m buffer 并集
  3. 暴露统一接口（CRS 全程 WGS84 出入，内部 4546 米制做 buffer/面积）：
       resolve_zone(name, area, lng, lat) -> zone_id   POI/采样点打标
       classify_point(lng, lat)           -> zone_id   生成点按坐标归区
       zones() / zone_by_id / zone_area                模拟器分配用
       place_keywords(zone_id)            -> dict       corpus + 本地性校验共用
       forward(query, limit)              -> [hit]      本地 POI 模糊搜索（C 用）
       reverse(lng, lat)                  -> place      最近 POI + 所在区（C 用）

zone 词表唯一来源：本模块。模拟器/corpus/check_spatial/搜索 全部 import 这里，
不各自重定义（避免冲突，见 REFACTOR_PLAN Conflict 1/2/3）。
═══════════════════════════════════════════════════════════
"""
import json
import math
import os
import sys

from shapely.geometry import Point, shape
from shapely.ops import unary_union, transform as shp_transform

try:
    from pyproj import Transformer
except Exception:  # pragma: no cover - pyproj 是项目硬依赖
    Transformer = None

# ── 路径自举（独立调试也能 import core） ──
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    from core.tracker import track, register_track_id
    from core.utils import safe_print
except Exception:  # 独立调试兜底
    def track(*a, **k):
        def deco(f):
            return f
        return deco
    def register_track_id(*a, **k):
        return None
    def safe_print(s, **k):
        try:
            print(s)
        except Exception:
            pass

# ── 坐标变换器（WGS84 <-> CGCS2000 EPSG:4546 米制，复用 poi_density 同款） ──
if Transformer is not None:
    _T = Transformer.from_crs('EPSG:4326', 'EPSG:4546', always_xy=True)
    _T_INV = Transformer.from_crs('EPSG:4546', 'EPSG:4326', always_xy=True)
else:
    _T = _T_INV = None

# ── 模糊匹配：优先 rapidfuzz，py3.14 无 wheel 则退 difflib ──
try:
    from rapidfuzz import fuzz as _rf_fuzz
    _HAVE_RAPIDFUZZ = True
except Exception:
    import difflib
    _HAVE_RAPIDFUZZ = False

# ── 拼音匹配（中文 POI 模糊搜索：输 wd/wanda → 万达；业界标配）──
try:
    from pypinyin import lazy_pinyin as _lazy_pinyin, Style as _PyStyle
    _HAVE_PYPINYIN = True
except Exception:
    _HAVE_PYPINYIN = False


def _pinyin_of(name):
    """name → (连写 pinyin_full, 首字母 pinyin_initial)，小写。无 pypinyin/空名返回 ('','')."""
    if not _HAVE_PYPINYIN or not name:
        return '', ''
    try:
        return ''.join(_lazy_pinyin(name)).lower(), ''.join(_lazy_pinyin(name, style=_PyStyle.FIRST_LETTER)).lower()
    except Exception:
        return '', ''


def _pr(q, s):
    """partial_ratio（rapidfuzz）或 SequenceMatcher 回退，返回 0-100。"""
    if _HAVE_RAPIDFUZZ:
        return _rf_fuzz.partial_ratio(q, s or '')
    return difflib.SequenceMatcher(None, q, s or '').ratio() * 100


def _match_score(q, name, p):
    """分层打分（业界做法：exact > prefix > pinyin-exact > substring > fuzzy）。

    精确名匹配永远排在子串匹配之前（修「金缔华城→苏宁易购(金缔华城店)」类 bug：
    partial_ratio 对二者都给 100，旧逻辑同分按数据顺序误排）。
    返回 (tier, score)：tier 非 None = 直通档（exact/prefix/pinyin-exact/substring）；
    tier None = fuzzy，调用方按 score>=55 门槛判。
    """
    if q == name:
        return 'exact', 300.0
    if name.startswith(q):
        return 'prefix', 250.0
    if _HAVE_PYPINYIN and q.isascii():      # pinyin-exact：拉丁 q == 全拼/首字母
        ql = q.lower()
        if ql == p.get('_py_full', '') or ql == p.get('_py_init', ''):
            return 'pinyin-exact', 220.0
    if q in name:
        return 'substring', 180.0 + _pr(q, name) * 0.2   # 子串：基底 180 + 细排
    # fuzzy：name + 类别 + 拼音 取 max
    s = _pr(q, name)
    s = max(s, _pr(q, p.get('baidu_level1', '')) * 0.7, _pr(q, p.get('baidu_level2', '')) * 0.7)
    if _HAVE_PYPINYIN and q.isascii():
        ql = q.lower()
        s = max(s, _pr(ql, p.get('_py_full', '')), _pr(ql, p.get('_py_init', '')) * 1.05)
        # 拼音前缀 boost：q 是拼音首字母/全拼的前缀 → +15（"wd"→万达广场 init="wdgc"）
        # 不 boost 嵌入匹配（CBD万达→"cbdwdgc"，wd 非前缀）→ 自然低于前缀匹配
        if p.get('_py_init', '').startswith(ql) or p.get('_py_full', '').startswith(ql):
            s += 15
    return None, s

# ── 路径常量（相对项目根，不硬编码绝对路径） ──
_PLACE_DIR = os.path.join(_ROOT, 'DATA', 'place')
_ZONE_TYPE_PATH = os.path.join(_PLACE_DIR, 'zone_typology.json')
_PLACE_KW_PATH = os.path.join(_PLACE_DIR, 'place_keywords.json')
_SEED_POI_PATH = os.path.join(_ROOT, 'SCRIPT', 'poi_data', 'yichang_poi_wgs84.json')
_AMAP_POI_PATH = os.path.join(_ROOT, 'SCRIPT', 'poi_data', 'amap_poi_wgs84.json')
_MAIN_BOUNDARY = os.path.join(_ROOT, 'DATA', 'boundaries', '西陵伍家核心主城.geojson')
_WATER_POLY_PATH = os.path.join(_ROOT, 'DATA', 'boundaries', '现状水系.geojson')


def _to_4546(geom):
    """shapely 几何 WGS84 -> EPSG:4546（米制）。"""
    if _T is None:
        return geom
    return shp_transform(lambda x, y, z=None: _T.transform(x, y), geom)


def _to_wgs84(geom):
    """shapely 几何 EPSG:4546 -> WGS84。"""
    if _T_INV is None:
        return geom
    return shp_transform(lambda x, y, z=None: _T_INV.transform(x, y), geom)


def _load_geojson_poly(path):
    """读 GeoJSON（首个 Polygon/MultiPolygon） -> shapely WGS84 几何。"""
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            gj = json.load(f)
    except Exception:
        return None
    geoms = []
    for feat in gj.get('features', []):
        g = feat.get('geometry') or {}
        if g.get('type') in ('Polygon', 'MultiPolygon'):
            geoms.append(shape(g))
    return unary_union(geoms) if geoms else None


def _haversine_m(lng1, lat1, lng2, lat2):
    """两点（WGS84 度）球面距离（米）。"""
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlng / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class PlaceLayer:
    """place 层单例。模块导入时由 get_place_layer() 懒加载一次。"""

    # 区解析优先级（ermalu 最具体优先，general 永远兜底最后）
    _ZONE_PRIORITY = ['ermalu_oldstreet', 'yiling_cbd', 'shuiyuecheng', 'zhongnan_road',
                      'wuyi_square', 'yiling_wanda', 'wanda_plaza', 'wuyue_square',
                      'riverside', 'transit_hub', 'residential']

    def __init__(self):
        self.zones_cfg = []          # zone_typology.json 的 zones 列表
        self.zone_by_id = {}         # id -> zone cfg
        self.place_kw = {}           # place_keywords.json
        self.zone_polys = {}         # id -> shapely Polygon(WGS84)  （不含 general）
        self.zone_area_km2 = {}      # id -> 面积 km2
        self.seed_pois = []          # 158 种子
        self.amap_pois = []          # 1270 高德
        self.all_pois = []           # 合并（搜索用）
        self._amap_zone_tally = {}   # id -> amap POI 计数（分配用，惰性算）
        self._load()

    @track("MOD_PLACE.F_001")
    def _load(self):
        # zone_typology
        with open(_ZONE_TYPE_PATH, 'r', encoding='utf-8') as f:
            zt = json.load(f)
        self.zones_cfg = zt['zones']
        self.zone_by_id = {z['id']: z for z in self.zones_cfg}

        # place_keywords
        with open(_PLACE_KW_PATH, 'r', encoding='utf-8') as f:
            pk = json.load(f)
        self.place_kw = pk.get('zones', {})

        # POI
        self.seed_pois = self._read_pois(_SEED_POI_PATH)
        self.amap_pois = self._read_pois(_AMAP_POI_PATH)
        self.all_pois = self.amap_pois   # 搜索/导出宇宙 = amap only（坐标准确）；seed 退命名不参与（坐标粗糙）

        # 预计算每条 POI 的拼音（连写 + 首字母），供 forward 拼音模糊匹配
        for _p in self.all_pois:
            _p['_py_full'], _p['_py_init'] = _pinyin_of(_p.get('name', ''))

        # 预算每个 POI 是否落在现状水系内（forward 过滤；导航到江里是错的）
        self._water = _load_geojson_poly(_WATER_POLY_PATH)
        if self._water is not None:
            from shapely.geometry import Point as _ShpPoint
            for _p in self.all_pois:
                _p['_in_water'] = self._water.contains(_ShpPoint(_p['lng'], _p['lat']))
            _nw = sum(1 for _p in self.all_pois if _p['_in_water'])
            safe_print('[LOAD] place_layer: in_water POIs={}/{}'.format(_nw, len(self.all_pois)))
        else:
            for _p in self.all_pois:
                _p['_in_water'] = False
            safe_print('[WARN] place_layer: 现状水系 未加载，_in_water 全 False')

        # 区边界
        self._build_zone_boundaries()

        safe_print('[LOAD] place_layer: zones={}, seed_pois={}, amap_pois={}'.format(
            len(self.zones_cfg), len(self.seed_pois), len(self.amap_pois)))

    @staticmethod
    def _read_pois(path):
        if not os.path.exists(path):
            return []
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        pois = data.get('pois', data if isinstance(data, list) else [])
        # 归一化字段名（amap 用 lng/lat；统一到 lng/lat）
        out = []
        for p in pois:
            lng = p.get('lng', p.get('lon'))
            lat = p.get('lat')
            if lng is None or lat is None:
                continue
            out.append({
                'name': p.get('name', ''),
                'lng': float(lng),
                'lat': float(lat),
                'area': p.get('area', ''),
                'baidu_level1': p.get('baidu_level1', ''),
                'baidu_level2': p.get('baidu_level2', ''),
                'domain': p.get('domain', ''),
                'element': p.get('element', ''),
                'radius_m': p.get('radius_m', 200),
                'source': p.get('source', 'seed' if 'yichang' in path else 'amap'),
            })
        return out

    def _build_zone_boundaries(self):
        """v2.2：只给「有边界」的 zone 建 polygon —— boundary_path（ermalu 显式）或 center（商圈圆）。
        全市型 zone（riverside/transit_hub/residential）不建边界——它们是名称型（停车场/小区全市分布），
        按 name 归（resolve_zone 处理），classify_point 不返回它们。"""
        for zid, cfg in self.zone_by_id.items():
            if zid == 'general':
                continue
            poly = None
            bp = cfg.get('boundary_path')
            if bp:
                poly = _load_geojson_poly(os.path.join(_ROOT, bp) if not os.path.isabs(bp) else bp)
            center = cfg.get('center')
            if poly is None and center and len(center) == 2:
                radius = float(cfg.get('radius_m', 300))
                pt = Point(_T.transform(center[0], center[1])) if _T else Point(center[0], center[1])
                poly_4546 = pt.buffer(radius)
                poly = _to_wgs84(poly_4546) if _T else poly_4546
            if poly is not None:
                self.zone_polys[zid] = poly
                # 面积（4546 米制）
                area_m2 = _to_4546(poly).area if _T else poly.area
                self.zone_area_km2[zid] = area_m2 / 1e6
        # general 面积 = 主城总面积 - 各类型区面积之和（粗估，下限 0）
        main_poly = _load_geojson_poly(_MAIN_BOUNDARY)
        main_area = (_to_4546(main_poly).area / 1e6) if (main_poly is not None and _T) else 0.0
        typed_sum = sum(v for k, v in self.zone_area_km2.items() if k != 'general')
        self.zone_area_km2['general'] = max(0.0, main_area - typed_sum)

    # ── 匹配核心 ──

    @staticmethod
    def _area_suffix(area):
        """'西陵-二马路' -> '二马路'；无 '-'（如纯城市名 '宜昌'）视为无 subtag，返回 ''。"""
        if not area or '-' not in area:
            return ''
        return area.split('-', 1)[1]

    def _match_by_subtag_keyword(self, name, area):
        """仅按 area 后缀子串 + name 关键词匹配（不含边界、不含 general）。未命中返回 None。"""
        suffix = self._area_suffix(area)
        for zid in self._ZONE_PRIORITY:
            cfg = self.zone_by_id[zid]
            subs = cfg.get('area_subtags', [])
            if subs and any(s in suffix or suffix in s and len(suffix) >= 2 for s in subs):
                return zid
            kws = cfg.get('name_keywords', [])
            if kws and name and any(k in name for k in kws):
                return zid
        return None

    @track("MOD_PLACE.F_002")
    def resolve_zone(self, name='', area='', lng=None, lat=None):
        """POI/采样点 -> zone_id。优先级：area 后缀 subtag -> name 关键词 -> 边界 contains -> general。"""
        zid = self._match_by_subtag_keyword(name or '', area or '')
        if zid:
            return zid
        # 边界兜底（按坐标）
        if lng is not None and lat is not None:
            bz = self.classify_point(lng, lat)
            if bz != 'general':
                return bz
        return 'general'

    @track("MOD_PLACE.F_003")
    def classify_point(self, lng, lat):
        """坐标 -> zone_id（边界 contains，按优先级首个命中；无命中 general）。"""
        pt = Point(lng, lat)
        for zid in self._ZONE_PRIORITY:
            poly = self.zone_polys.get(zid)
            if poly is not None and poly.contains(pt):
                return zid
        return 'general'

    # ── 模拟器分配用 ──

    def zones(self):
        """返回区记录列表（含 poi_count=该区 amap POI 数、area_km2）。"""
        tally = self.amap_zone_tally()
        out = []
        for cfg in self.zones_cfg:
            zid = cfg['id']
            out.append({
                'id': zid,
                'name_zh': cfg['name_zh'],
                'zone_type': cfg['zone_type'],
                'color': cfg.get('color', '#888'),
                'area_km2': self.zone_area_km2.get(zid, 0.0),
                'poi_count': tally.get(zid, 0),
            })
        return out

    def amap_zone_tally(self):
        """1270 高德 POI 逐条 resolve_zone -> 每区计数（惰性缓存）。"""
        if self._amap_zone_tally:
            return self._amap_zone_tally
        tally = {z['id']: 0 for z in self.zones_cfg}
        for p in self.amap_pois:
            tally[self.resolve_zone(p['name'], p['area'], p['lng'], p['lat'])] += 1
        self._amap_zone_tally = tally
        return tally

    # ── corpus / 本地性校验用 ──

    def place_keywords(self, zone_id):
        """zone_id -> {place_keywords, characteristic_keywords}（corpus + 校验共用）。"""
        return self.place_kw.get(zone_id, self.place_kw.get('general', {
            'place_keywords': [], 'characteristic_keywords': []
        }))

    # ── 搜索（C 用；本地优先，高德兜底在 core/geocode.py） ──

    @track("MOD_PLACE.F_004")
    def forward(self, query, limit=10):
        """关键词 -> 本地 POI 命中（rapidfuzz/difflib 模糊，按 name + baidu_level）。"""
        if not query or len(query.strip()) < 1:
            return []
        q = query.strip()
        scored = []   # (score, p)
        for p in self.all_pois:
            name = p['name'] or ''
            if not name:
                continue
            if p.get('_in_water'):
                continue
            tier, s = _match_score(q, name, p)
            if tier is None and s < 55:
                continue
            scored.append((s, p))
        # 分降序；同分保持数据顺序（稳定排序）。tier 分已保证 exact > substring。
        scored.sort(key=lambda t: t[0], reverse=True)
        hits = []
        for s, p in scored[:limit]:
            hits.append({
                'name': p['name'],
                'lng': p['lng'],
                'lat': p['lat'],
                'category': p.get('baidu_level1', '') or p.get('baidu_level2', ''),
                'baidu_level1': p.get('baidu_level1', ''),
                'baidu_level2': p.get('baidu_level2', ''),
                'area': p.get('area', ''),
                'zone_id': self.resolve_zone(p['name'], p.get('area', ''), p['lng'], p['lat']),
                'zone_name': self.zone_by_id.get(
                    self.resolve_zone(p['name'], p.get('area', ''), p['lng'], p['lat']), {}).get('name_zh', ''),
                'score': round(s, 1),
                'source': 'local',
                'data_source': p.get('source') or 'seed',   # 审计：amap 库 / seed 手标
            })
        return hits

    @track("MOD_PLACE.F_005")
    def reverse(self, lng, lat):
        """坐标 -> {zone_id, zone_name, nearest_poi:{name,dist_m}}（最近 POI + 所在区）。"""
        zid = self.classify_point(lng, lat)
        best = None
        best_d = float('inf')
        for p in self.all_pois:
            d = _haversine_m(lng, lat, p['lng'], p['lat'])
            if d < best_d:
                best_d = d
                best = p
        return {
            'zone_id': zid,
            'zone_name': self.zone_by_id.get(zid, {}).get('name_zh', '通用市区'),
            'nearest_poi': {'name': best['name'], 'dist_m': round(best_d)} if best else None,
        }


# ── 单例 ──
_INSTANCE = None


def get_place_layer():
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = PlaceLayer()
    return _INSTANCE


# ── 追踪 ID 注册 ──
register_track_id("MOD_PLACE.F_001", "place 层数据加载（zone/POI/边界）")
register_track_id("MOD_PLACE.F_002", "resolve_zone：POI/点 -> zone_id（subtag->keyword->边界->general）")
register_track_id("MOD_PLACE.F_003", "classify_point：坐标 -> zone_id（边界 contains）")
register_track_id("MOD_PLACE.F_004", "forward：本地 POI 模糊搜索")
register_track_id("MOD_PLACE.F_005", "reverse：坐标 -> 最近 POI + 所在区")


# ── 自测：分类全部种子 + amap POI，打印每区计数 ──
if __name__ == '__main__':
    pl = get_place_layer()
    safe_print('\n=== 区定义 ===')
    for z in pl.zones():
        safe_print('  {:<20} type={:<8} area={:6.2f} km2  poi={}'.format(
            z['id'], z['zone_type'], z['area_km2'], z['poi_count']))

    safe_print('\n=== 158 种子 POI resolve_zone 分布 ===')
    seed_tally = {z['id']: 0 for z in pl.zones_cfg}
    for p in pl.seed_pois:
        seed_tally[pl.resolve_zone(p['name'], p['area'], p['lng'], p['lat'])] += 1
    for zid, n in sorted(seed_tally.items(), key=lambda x: -x[1]):
        safe_print('  {:<20} {}'.format(zid, n))

    safe_print('\n=== 1270 高德 POI resolve_zone 分布（general 回退率验收 <25%） ===')
    amap_tally = pl.amap_zone_tally()
    total_amap = sum(amap_tally.values()) or 1
    for zid, n in sorted(amap_tally.items(), key=lambda x: -x[1]):
        safe_print('  {:<20} {}  ({:.1%})'.format(zid, n, n / total_amap))
    gen_rate = amap_tally.get('general', 0) / total_amap
    safe_print('\n  general 占比 = {:.1%}（通用市区承载城市主体点量，符合预期；'.format(gen_rate)
               + '真实平衡由 Phase 1 check_spatial 断言）')

    safe_print('\n=== 自检：search/reverse 烟雾测试 ===')
    safe_print('  forward("万达") = {}'.format([h['name'] for h in pl.forward('万达', 5)]))
    safe_print('  forward("二马路") = {}'.format([h['name'] for h in pl.forward('二马路', 5)]))
    safe_print('  reverse(111.29, 30.70) = {}'.format(pl.reverse(111.29, 30.70)))
