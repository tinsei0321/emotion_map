"""
地理编码 (Geocoding) — 地点搜索 + 逆地理编码
═══════════════════════════════════════════════════════════
本地 place_layer 主 + 高德 API 兜底（混合源）。

职责：
  search_place(query, limit)   关键词 → POI 命中（本地 forward 主 + 高德 place/text 兜底）
  geocode_address(address)     地址 → 坐标 WGS84（高德 geo 正向）
  reverse_geocode(lng, lat)    坐标 WGS84 → {zone, nearest_poi, 街道}（本地 reverse 主 + 高德 regeo 兜底）
  _amap_request(endpoint, p)   统一高德请求：注入 key + 重试 + 强制 CRS

本地优先保证搜索↔情绪点对应 + 断网可用；高德补全覆盖本地未命中的地址/新 POI。

红线（贯穿全程）：
  1. AMAP_KEY 只在服务端读 .env，绝不进前端 JS
     （高德 Web 服务 Key = IP 白名单，进 JS 会被拦/泄露；前端只走 /api/ 反代）。
  2. 高德返回 GCJ-02，每个坐标一律 gcj02_to_wgs84（漏转 = 50-500m 静默偏移）。
     反向（regeo 送坐标）入参先 wgs84_to_gcj02。

模块 ID: MOD_GEOCODE（F_001-F_004, D_001-D_002）
═══════════════════════════════════════════════════════════
"""
import os
import sys
import time
import json
import functools

# ── 路径自举（独立调试也能 import core） ──
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    import requests
except Exception:  # pragma: no cover - requests 是项目硬依赖
    requests = None

try:
    from core.tracker import track, register_track_id, TrackContext
    from core.utils import safe_print as _safe_print
    from core.coord_transform import gcj02_to_wgs84, wgs84_to_gcj02
    from core.place_layer import get_place_layer
except Exception:  # 独立调试兜底
    def track(*a, **k):
        def deco(f):
            return f
        return deco

    def register_track_id(*a, **k):
        return None

    class TrackContext:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _safe_print(s, **k):
        try:
            print(s)
        except Exception:
            pass

    gcj02_to_wgs84 = wgs84_to_gcj02 = None
    get_place_layer = None


# ── 配置 ──
AMAP_BASE = 'https://restapi.amap.com/v3'
AMAP_CITY = '宜昌'            # 搜索/编码限定城市
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2          # 指数退避基数（秒），镜像 relevance_filter
REQUEST_TIMEOUT = 20          # 单次请求超时（秒）
_LOCAL_MIN_HITS = 3           # 本地命中 ≥ 此数 → 不调高德
_REVERSE_DIST_M = 500         # 最近 POI 超此距离 → 高德 regeo 补街道


def _load_env():
    """从项目根 .env 加载环境变量（不覆盖已有）。镜像 pull_amap_poi._load_env。"""
    env_path = os.path.join(_ROOT, '.env')
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass


# 模块导入即加载 .env —— api/main.py 不加载 .env，AMAP_KEY 由此处兜底（红线 #1）。
_load_env()
AMAP_KEY = os.environ.get('AMAP_KEY', '')

if not AMAP_KEY:
    _safe_print('[WARN] MOD_GEOCODE: AMAP_KEY missing, amap fallback disabled (local-only)')


def _amap_enabled():
    """高德兜底是否可用（Key + requests 双就绪）。"""
    return bool(AMAP_KEY and requests is not None)


# ── 高德请求层 ──

@functools.lru_cache(maxsize=256)
def _amap_fetch(endpoint, params_key):
    """实际发起高德请求（被 lru_cache 包裹；params_key = json(sort_keys)）。

    返回解析后的 dict（status='1' 成功），失败/不可用返回 None。
    纯 HTTP 层，不做 CRS 转换（方向由调用方处理）。
    """
    if not _amap_enabled():
        return None
    params = json.loads(params_key)
    params['key'] = AMAP_KEY
    params.setdefault('output', 'json')
    url = '{}/{}'.format(AMAP_BASE, endpoint.lstrip('/'))
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except Exception as e:
            if attempt < MAX_RETRIES:
                _safe_print('[AMAP][WARN] {} 异常 {}，{}/{} 重试'.format(
                    endpoint, e, attempt, MAX_RETRIES))
                time.sleep(RETRY_DELAY_BASE ** attempt)
                continue
            _safe_print('[AMAP][ERR] {} 放弃: {}'.format(endpoint, e))
            return None

        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == '1':
                return data
            _safe_print('[AMAP][WARN] {} status={} {}'.format(
                endpoint, data.get('status'), data.get('info')))
            return None  # 业务错（key 非法/参数错）—— 重试无益，直接返回
        if resp.status_code in (429, 500, 502, 503, 504):
            w = RETRY_DELAY_BASE ** attempt
            _safe_print('[AMAP][WARN] {} HTTP {}，{}/{} 重试，等 {}s'.format(
                endpoint, resp.status_code, attempt, MAX_RETRIES, w))
            time.sleep(w)
            continue
        _safe_print('[AMAP][ERR] {} HTTP {} 不重试'.format(endpoint, resp.status_code))
        return None
    return None


@track("MOD_GEOCODE.F_004")
def _amap_request(endpoint, params):
    """统一高德请求入口：注入 key + 重试 + 缓存。

    params 取值需为 JSON 可序列化（str/int/float）。返回 dict 或 None。
    """
    key = json.dumps(params, sort_keys=True, ensure_ascii=False)
    return _amap_fetch(endpoint, key)


def _gcj_loc_to_wgs(loc_str):
    """高德 location 'lng,lat'(GCJ-02) → (lng, lat) WGS84。红线 #2 单点转换。"""
    try:
        lon_s, lat_s = str(loc_str).split(',')
        glon, glat = float(lon_s), float(lat_s)
    except Exception:
        return None
    if gcj02_to_wgs84 is None:
        return (glon, glat)
    return gcj02_to_wgs84(glon, glat)


# ── 公开接口 ──

@track("MOD_GEOCODE.F_001")
def search_place(query, limit=10):
    """关键词 → POI 命中列表。本地 place_layer.forward 主 + 高德 place/text 兜底。

    返回 [{name, lng, lat, category, zone_id, zone_name, address, score, source}]，
    坐标一律 WGS84；source='local'(含 zone) | 'amap'(含 address)。
    """
    if not query or not query.strip():
        return []
    q = query.strip()
    pl = get_place_layer() if get_place_layer else None
    local_hits = pl.forward(q, limit) if pl else []

    with TrackContext("MOD_GEOCODE.D_001", local_n=len(local_hits), amap_on=_amap_enabled()):
        if len(local_hits) >= _LOCAL_MIN_HITS or not _amap_enabled():
            return local_hits[:limit]

    # 本地命中不足且高德可用 → place/text 补全
    data = _amap_request('place/text', {
        'keywords': q, 'city': AMAP_CITY, 'citylimit': 'true',
        'offset': max(limit, 20), 'page': 1, 'extensions': 'base',
    })
    amap_hits = []
    seen = {(h.get('name', ''), round(h.get('lng', 0), 5)) for h in local_hits}
    for poi in ((data or {}).get('pois')) or []:
        wgs = _gcj_loc_to_wgs(poi.get('location'))  # 红线 #2
        if not wgs:
            continue
        name = poi.get('name', '') or ''
        key = (name, round(wgs[0], 5))
        if key in seen:
            continue
        seen.add(key)
        amap_hits.append({
            'name': name,
            'lng': wgs[0], 'lat': wgs[1],
            'category': (poi.get('type') or '').split(';')[0],
            'zone_id': '', 'zone_name': '',
            'address': poi.get('address', '') or '',
            'score': 0.0,
            'source': 'amap',
            'data_source': 'amap-api',   # 审计：高德 place/text API 补全（非本地库）
        })
        if len(local_hits) + len(amap_hits) >= limit:
            break
    return (local_hits + amap_hits)[:limit]


@track("MOD_GEOCODE.F_002")
def geocode_address(address):
    """地址 → 坐标（WGS84）。高德 geo 正向；红线 #2 GCJ-02→WGS84。

    返回 {lng, lat, formatted_address, source} 或 None。
    """
    if not address or not address.strip() or not _amap_enabled():
        return None
    data = _amap_request('geocode/geo', {
        'address': address.strip(), 'city': AMAP_CITY,
    })
    geos = (data or {}).get('geocodes') or []
    if not geos:
        return None
    wgs = _gcj_loc_to_wgs(geos[0].get('location'))  # 红线 #2
    if not wgs:
        return None
    return {
        'lng': wgs[0], 'lat': wgs[1],
        'formatted_address': geos[0].get('formatted_address', '') or '',
        'source': 'amap',
    }


@track("MOD_GEOCODE.F_003")
def reverse_geocode(lng, lat):
    """坐标(WGS84) → {zone_id, zone_name, nearest_poi, formatted_address, source}。

    本地 place_layer.reverse 主（瞬时）；最近 POI 距离 > _REVERSE_DIST_M 且高德可用
    → regeo 补街道地址。红线 #2：送高德的坐标先 WGS84→GCJ-02。
    """
    pl = get_place_layer() if get_place_layer else None
    base = pl.reverse(lng, lat) if pl else {
        'zone_id': '', 'zone_name': '', 'nearest_poi': None}

    near = base.get('nearest_poi') or {}
    need_amap = (
        _amap_enabled()
        and near.get('dist_m', 1e9) > _REVERSE_DIST_M
    )
    addr = ''
    with TrackContext("MOD_GEOCODE.D_002", amap_regeo=need_amap):
        if need_amap:
            glon, glat = wgs84_to_gcj02(lng, lat) if wgs84_to_gcj02 else (lng, lat)
            data = _amap_request('geocode/regeo', {
                'location': '{:.6f},{:.6f}'.format(glon, glat),
                'extensions': 'base',
            })
            addr = (((data or {}).get('regeocode') or {}).get('formatted_address')) or ''

    out = dict(base)
    out['formatted_address'] = addr
    out['source'] = 'mixed' if addr else 'local'
    return out


# ── 追踪 ID 注册（@track 只记日志，注册表须手动同步，见 core/CLAUDE.md 铁律 10） ──
register_track_id("MOD_GEOCODE.F_001", "search_place 本地+高德 POI 搜索")
register_track_id("MOD_GEOCODE.F_002", "geocode_address 高德正向地理编码")
register_track_id("MOD_GEOCODE.F_003", "reverse_geocode 本地+高德逆地理编码")
register_track_id("MOD_GEOCODE.F_004", "_amap_request 高德统一请求（注入 key+重试+缓存）")
register_track_id("MOD_GEOCODE.D_001", "搜索源选择：本地命中阈值 vs 高德兜底")
register_track_id("MOD_GEOCODE.D_002", "CRS 转换：regeo 入参 WGS84→GCJ-02")
