#!/usr/bin/env python3
"""
演示数据最终版生成引擎（百度热力点锚定）— sim_performance_data
================================================================
替 generate_l1_mock（POI-anchored，仅西陵伍家）。本引擎以百度热力点真实密度为底座，
全域去聚合散点 → L1；中心城区子集 → L2。3 快照 T1/T2/T3 叙事弧 + 4×5 区域×时间倾斜。

核心（详 plan 3-curious-bachman.md）：
  - 空间生成：每热力点 N=Poisson(value×scale×snap_factor)，jitter ~80m。scale=0.639（固化）
    → 全域~34k / 中心城区~17k / 西陵伍家~10.8k 每快照（依 value 比例）
  - area_type 三级（边界嵌套，互斥 unit>core>central_outer）驱 4×5 倾斜 + 极性弧
  - 4×5 双层：层1 最近 POI(<150m, 80%概率) 继承 domain/element（AMAP_L1_TO_4X5）；
            层2 背景点 performance_config 区域 bias × 时间调制
  - 极性：performance_config 三级弧 + POI lean 翻转 + 锚点迁移（重点叙事区 T1消极→T3积极）
  - 中心城区外点 = 纯热度点（text/polarity 空，不进 L2；hotness=value×密度 显全域热度）
  - L2 = L1∩中心城区 → run_analysis_task（SnowNLP，校验池锚定极性）

输出 DATA/performance/yichang_L1_{T1,T2,T3}_* + yichang_L2_{T1,T2,T3}_*（schema 与旧 L1/L2 一致，前端零改）。
"""
import os
import sys
import math
import json
import random
from collections import Counter

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
sys.path.insert(0, _PARENT)
sys.path.insert(0, _HERE)

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from shapely.geometry import Point, shape
from shapely.ops import unary_union

from core.tracker import track, TrackContext, trace_error, register_track_id
from core.utils import safe_print
from performance_config import SNAPSHOTS, pick_polarity, pick_domain_element, pick_topic, snapshot_flavor, AREA_TYPES, POI_NARRATIVE_ZONE, NARRATIVE_ZONES
from emotion_text_pool import load_pool, sample_text
from poi_data.poi_4x5_map import DOMAIN_CN, ELEMENT_CN, DOMAINS, ELEMENTS
from core.place_layer import get_place_layer

random.seed(2606)
np.random.seed(2606)

# ═══════════════ 配置 ═══════════════
PROJECT_ROOT = _PARENT
BAIDU_FILE = os.path.join(PROJECT_ROOT, 'DATA', 'baidu-heatpoints', '宜昌市_2026041215.geojson')
B_CC = os.path.join(PROJECT_ROOT, 'DATA', 'boundaries', '中心城区行政区划_1623.geojson')
B_CORE = os.path.join(PROJECT_ROOT, 'DATA', 'boundaries', '西陵伍家核心主城.geojson')
B_ERMALU = os.path.join(PROJECT_ROOT, 'DATA', 'boundaries', '大南门二马路滨江片区.geojson')
B_WATER = os.path.join(PROJECT_ROOT, 'DATA', 'boundaries', '现状水系.geojson')
RIVER_BUFFER_DEG = 0.0018   # 滨江带向陆缓冲 ~200m（降 riverside 占比：原 400m 致滨江占 cc ~48% 点不真实，且全程积极主导压过 T1 消极弧）
# 注：更新单元(150 面)为 Task3 zonal 聚合用，不参与 area_type 分层（其覆盖全域会把 core/central_outer 吞进 unit）。
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'DATA', 'performance')
SCOPE = 'yichang'

SCALE = 0.639            # 点/value-unit（固化：全域~34k/快照）
JITTER_DEG = 0.0008      # 散点 jitter ~80m（度）
POI_SNAP_M = 150         # 最近 POI 吸附半径（米）
POI_INHERIT_P = 0.80     # 有最近 POI 时继承 domain/element 的概率（层1）
LEAN_FLIP_P = 0.18       # POI lean 与基础极性相反时翻向 lean 的概率

VALUE_P95 = None         # 运行时算（百度 value 95 分位 → emotion_intensity 归一化）

SOURCE_WEIGHTS = {'dianping': 0.30, 'meituan': 0.25, 'xiaohongshu': 0.20, 'weibo': 0.15, '12345': 0.10}
EMOTION_BY_POLARITY = {'positive': ['满足', '喜爱', '期待'], 'negative': ['失望', '愤怒'], 'neutral': ['中性', '好奇']}
URBAN_VALUES = ['high', 'medium', 'low']

# POI 类别 → 极性倾向（局部纹理；叠在区域 arc 之上）
POI_POLARITY_LEAN = {
    '风景名胜': 'positive', '体育休闲服务': 'positive', '休闲娱乐': 'positive',
    '餐饮服务': 'positive', '购物服务': 'positive', '住宿服务': 'positive',
    '交通设施服务': 'negative', '政府机构及社会团体': 'negative',
    '商务住宅': 'negative', '金融保险服务': 'negative',
    '生活服务': None, '科教文化服务': None, '公司企业': None,
}

# 重点叙事区锚点（T1 消极 → T3 积极；坐标为真实地标）
ANCHORS = [
    {'name': '二马路老街', 'lng': 111.2955, 'lat': 30.7035},
    {'name': '解放路', 'lng': 111.2980, 'lat': 30.7045},
    {'name': '夷陵广场CBD', 'lng': 111.2905, 'lat': 30.7050},
    {'name': '儿童公园', 'lng': 111.2855, 'lat': 30.7060},
    {'name': '市委市政府', 'lng': 111.2900, 'lat': 30.7090},
    {'name': '大南门', 'lng': 111.2900, 'lat': 30.7000},
    {'name': '滨江公园', 'lng': 111.2900, 'lat': 30.7150},
]
ANCHOR_RADIUS_DEG = 0.0010   # ~110m（锚点迁移强制极性半径）
ANCHOR_ZONE_DEG = 0.0025     # ~250m（重点叙事区 unit 层归类半径——二马路/夷陵广场等"指定单元-社区"）
ANCHOR_SCHEDULE = {'T1': 'negative', 'T2': 'neutral', 'T3': 'positive'}

L1_COLUMNS = [
    'id_e', 'scope', 'source', 'created_at', 'publish_time', 'text', 'keywords', 'text_length',
    'domain', 'element', 'primary_emotion', 'emotion_intensity', 'polarity_hint', 'intensity',
    'urban_value', 'l1_confidence', 'has_location', 'location_mentioned',
    'relevance', 'relevance_category', 'like_count', 'comment_count', 'tags', 'url',
    'time_label', 'area_seed', 'area_tag', 'zone', 'narrative_zone', 'topic',
    'lon', 'lat', 'x_cgcs2000', 'y_cgcs2000', 'spatial_hotspot', 'spatial_type',
]


# ═══════════════ 邻近 POI 网格索引（零依赖，替 scipy.cKDTree）═══════════════
class _POIGrid:
    """POI 按 lng/lat 分桶（0.005°≈500m 格），最近邻查询只搜本格+8 邻格。"""
    def __init__(self, pois, cell=0.005):
        self.cell = cell
        self.buckets = {}
        for p in pois:
            k = (int(p['lng'] / cell), int(p['lat'] / cell))
            self.buckets.setdefault(k, []).append(p)

    def nearest(self, lng, lat, max_deg):
        cx, cy = int(lng / self.cell), int(lat / self.cell)
        best, best_d = None, max_deg ** 2
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for p in self.buckets.get((cx + dx, cy + dy), []):
                    d = (p['lng'] - lng) ** 2 + (p['lat'] - lat) ** 2
                    if d < best_d:
                        best_d, best = d, p
        return best


# ═══════════════ STEP 0: 加载 ═══════════════
# 点军江南关键地标（高德 POI 未覆盖江南；WGS84 单一真源 = poi_data/landmarks_wgs84.json）
# 奥体（venue 演唱会/楚超赛事）/ 卷桥河湿地公园（park_plaza 周末露营爆满）/ 江南URD（residential 生态新城核心住宅）
# search 与 sim 共享同一份：place_layer._load() 已把 landmark_pois 并入 all_pois（搜索/分配宇宙），
# 本模块仅读同一 json 构 _LANDMARKS（_nearest_landmark 几何强制 zone+poi 用）。
_LANDMARK_POI_PATH = os.path.join(_HERE, 'poi_data', 'landmarks_wgs84.json')


def _load_landmarks():
    """读 landmarks_wgs84.json → list[dict]（含 narrative_zone/domain/element 等全字段）。"""
    with open(_LANDMARK_POI_PATH, 'r', encoding='utf-8') as f:
        return json.load(f).get('pois', [])


# 点军江南地标几何判定（需求5：百度热力点在点军稀疏，POI 150m 吸附不足 → 500m 几何强制 zone+poi）
# 从 landmarks_wgs84.json 构建（WGS84，无需 GCJ→WGS）；_nearest_landmark 强制 zone/domain/element/name 落位。
_LANDMARKS = [
    {'lng': lm['lng'], 'lat': lm['lat'], 'zone': lm['narrative_zone'],
     'domain': lm['domain'], 'element': lm['element'], 'l1': lm['baidu_level1'], 'name': lm['name']}
    for lm in _load_landmarks()
]
_LANDMARK_RADIUS_DEG = 0.005   # ~500m 矩形

# 核心商圈（需求4：停车难强制落夷陵广场/CBD/万达/国贸/儿童公园核心商圈；坐标 GCJ-02→WGS-84）
from core.coord_transform import gcj02_to_wgs84 as _gcj2wgs
_CORE_CENTER_GCJ = (111.2905, 30.7050)   # 夷陵广场CBD（与 ANCHORS 同源；600m 覆盖 CBD/万达/国贸/儿童公园）
_CORE_CENTER_GCJ = (111.2905, 30.7050)   # 夷陵广场CBD（与 ANCHORS 同源；600m 覆盖 CBD/万达/国贸/儿童公园）
_CORE_RADIUS_DEG = 0.006   # ~600m
_CORE_LNG, _CORE_LAT = _gcj2wgs(_CORE_CENTER_GCJ[0], _CORE_CENTER_GCJ[1])


def _in_core_commercial(lng, lat):
    """核心商圈 600m 内（夷陵广场周边）—— 停车难强制落位。"""
    return abs(lng - _CORE_LNG) < _CORE_RADIUS_DEG and abs(lat - _CORE_LAT) < _CORE_RADIUS_DEG


# 中南路（伍家岗商圈）停车难第二锚点：扩散停车难聚集（CBD 单点 bbox 过紧致关键词点击 zoom 过低）
_ZHONGNAN_LNG, _ZHONGNAN_LAT = 111.325, 30.682   # WGS84（zone_typology 同源）


def _in_zhongnan(lng, lat):
    """中南路 600m 内（伍家岗商圈）—— 停车难第二锚点：拉大 top-N bbox，防 zoom 过低。"""
    return abs(lng - _ZHONGNAN_LNG) < _CORE_RADIUS_DEG and abs(lat - _ZHONGNAN_LAT) < _CORE_RADIUS_DEG


# 占道停车专属评论（60%治理 / 20%设施 / 20%环境 三主题；替通用 sample_text，让占道停车有具象叙事）
# 落位解读：占道停车本质是「治理」问题（执法/管理/市容秩序 60%），兼有「设施」配套不足（规划视角 20%）
# 与「环境」人行/市容影响（20%）。_zhandao_assign 据此重映射 (domain, element) + 主题评论，让 4×5 矩阵把占道停车主要归到治理行。
_ZHANDAO_TEXT = {
    'governance': [   # 60% 治理：执法/管理/市容秩序
        '城管贴条治标不治本，这条路天天占道双排停',
        '占道经营叠占道停车，管理部门到下班点就没人',
        '人行道被电动车占满，城管的执法呢',
        '违规占道停车屡禁不止，执法力度远远不够',
        '消防通道都敢占道停，出了事谁负责',
        '这条街占道停车泛滥，根本见不到贴条',
    ],
    'facility': [     # 20% 设施（规划配套）：停车供给不足
        '车位太少只能占道停，停车场规划跟不上',
        '没地方停车才占道，配套车位严重不足',
        '附近停车场全满了，被迫占道停路面',
        '商业街车位配建不够，车全挤到路面上',
    ],
    'environment': [  # 20% 环境：人行/市容/无障碍
        '人行道被占道停车占满，行人只能走机动车道',
        '绿化带都被占道车压秃了，市容全无',
        '推婴儿车根本过不去，占道停车太自私',
        '盲道全被占道停车占了，无障碍形同虚设',
    ],
}


def _zhandao_assign(rng):
    """占道停车 60%治理 / 20%设施 / 20%环境 → (domain, element, text)。
    60% 归 urban_governance（element 在 facility/environment 间均分）；20% 规划×设施；20% 更新×环境。"""
    r = rng.random()
    if r < 0.60:   # 治理：执法/管理/市容秩序
        return 'urban_governance', rng.choice(['facility', 'environment']), rng.choice(_ZHANDAO_TEXT['governance'])
    if r < 0.80:   # 设施：停车配套不足（规划视角）
        return 'urban_planning', 'facility', rng.choice(_ZHANDAO_TEXT['facility'])
    return 'urban_renewal', 'environment', rng.choice(_ZHANDAO_TEXT['environment'])   # 环境：人行/市容


# 点军江南地标正向专属关键词（奥体楚超/卷桥河露营/江南绿肺）——点军生态+赛事先天优势
_DIANJUN_TOPIC = {'宜昌奥体中心': '楚超', '卷桥河湿地公园': '卷桥河露营', '江南URD': '江南绿肺'}
_DIANJUN_TEXT = {
    '楚超': [           # 奥体楚超足球赛 / 演唱会（T3 五一文旅爆满峰值）
        '奥体楚超赛事现场氛围超燃，球迷全程高歌',
        '看了场楚超德比，进球那一刻全场沸腾',
        '奥体演唱会音效赞，几万人大合唱太震撼',
        '楚超终于让奥体有了大赛氛围，点军也热闹了',
        '带孩子看楚超，现场气氛比电视强太多',
    ],
    '卷桥河露营': [     # 卷桥河湿地公园周末露营（点军生态先天优势）
        '卷桥河周末露营爆满，帐篷沿着草地连成片',
        '湿地空气清新，带娃亲近自然的好地方',
        '江风配夕阳，卷桥河堪称露营天花板',
        '卷桥河生态环境真好，白鹭都回来了',
        '周末去卷桥河搭帐篷，空气比江北好太多',
    ],
    '江南绿肺': [       # 点军江南生态新城 / 丘陵绿地
        '江南这块绿肺是点军的先天优势',
        '江南URD依山傍水，生态新城名副其实',
        '点军空气比江北好太多，天然氧吧',
        '江南丘陵绿地连片，是城市稀缺的生态资源',
        '住江南最大的幸福就是推窗见绿',
    ],
}


# T2 暑假·城建施工中期连锁反应评论（道路开挖/施工噪音/交通不便/老旧改造）——浅红消极基调
_T2_CONSTRUCTION_TEXT = {
    ('urban_planning', 'facility'): [    # 道路开挖 / 修路修桥
        '这条路挖了半年了，修路修桥天天绕行',
        '道路开挖围挡到处都是，骑车都过不去',
        '修路围挡换了一茬又一茬，到底什么时候完工',
        '主干道半幅施工，早晚高峰堵得怀疑人生',
    ],
    ('urban_renewal', 'environment'): [   # 施工噪音 / 扬尘（老旧小区改造）
        '小区改造施工噪音早上六点就开始',
        '拆房子扬尘满天飞，窗户都不敢开',
        '施工到半夜，老人孩子根本睡不着',
        '装修噪音加工地噪音，双倍折磨',
    ],
    ('urban_governance', 'event'): [      # 施工致交通不便 / 绕行拥堵
        '施工封路公交改道，出行太不方便了',
        '绕行三公里才到地铁口，都是修路害的',
        '工程车辆进进出出，路口堵成一锅粥',
        '单行道因施工改道，外卖小哥天天迷路',
    ],
    ('urban_renewal', 'facility'): [      # 老旧小区改造施工
        '老旧小区改造脚手架搭了大半年',
        '管网改造挖了填、填了挖，反复折腾',
        '改造施工占道，停车更是难上加难',
    ],
}


def _nearest_landmark(lng, lat):
    """点军地标 500m 内 → 返回地标 dict（强制 zone/domain/element/name）；无则 None。
    让矩阵块指向奥体/卷桥河/江南URD（zone + place_name 都对齐）。"""
    for lm in _LANDMARKS:
        if abs(lng - lm['lng']) < _LANDMARK_RADIUS_DEG and abs(lat - lm['lat']) < _LANDMARK_RADIUS_DEG:
            return lm
    return None


@track("MOD_PERF.F_001", track_args=False)
def load_assets():
    bj = json.load(open(BAIDU_FILE, encoding='utf-8'))
    heats = []
    for f in bj['features']:
        c = f['geometry']['coordinates']
        v = int(f['properties'].get('value', 0))
        if v > 0:
            heats.append((c[0], c[1], v))
    global VALUE_P95
    VALUE_P95 = max(1, int(np.percentile([h[2] for h in heats], 95)))
    pool = load_pool()
    pl = get_place_layer()
    # 点军江南关键地标已由 place_layer._load() 从 landmarks_wgs84.json 并入 all_pois（search+sim 同源）
    poigrid = _POIGrid(pl.all_pois)
    safe_print('[LOAD] 百度热力点 {} (value p95={}) | 文本池 {} | POI {}'.format(
        len(heats), VALUE_P95, len(pool), len(pl.all_pois)))
    return heats, pool, pl, poigrid


def _load_union(path):
    if not path or not os.path.exists(path):
        return None
    gj = json.load(open(path, encoding='utf-8'))
    gs = [shape(f['geometry']) for f in gj.get('features', [])
          if (f.get('geometry') or {}).get('type') in ('Polygon', 'MultiPolygon')]
    return unary_union(gs) if gs else None


@track("MOD_PERF.F_006", track_args=False)
def load_boundaries():
    cc = _load_union(B_CC)
    core = _load_union(B_CORE)
    # 叙事片区几何：riverside = 长江水体 ∩ cc buffer ~400m；ermawu = 大南门二马路滨江片区 polygon
    riverside_poly, ermawu_poly = None, None
    water = _load_union(B_WATER)
    if water is not None and cc is not None:
        riverside_poly = water.buffer(RIVER_BUFFER_DEG).intersection(cc)
    ermawu_poly = _load_union(B_ERMALU)
    safe_print('[LOAD] cc/core 就绪 | riverside {} m² | ermawu {}'.format(
        '有' if riverside_poly else '无', '有' if ermawu_poly else '无'))
    return cc, core, riverside_poly, ermawu_poly


def classify_area_type(lng, lat, cc, core):
    """core > central_outer > outside_cc（2 级 area_type，驱 4×5 全局倾斜）。
    core = 西陵伍家核心主城（operation/governance 偏多）；central_outer = 中心城区 ∖ 西陵伍家
    （planning/renewal/governance 较均匀）；outside_cc = 市域内中心城区外（纯热度点，不入 L2）。
    注："指定单元-社区"的 renewal 倾斜由 Task3 聚合时 POI 组成自然给出（住宅 POI→renewal），
    不在此全局分层（更新单元 150 面覆盖全域，无法作子集边界）。锚点仅用于极性弧（apply_anchors）。"""
    pt = Point(lng, lat)
    if core is not None and core.contains(pt):
        return 'core'
    if cc is not None and cc.contains(pt):
        return 'central_outer'
    return 'outside_cc'


def classify_narrative_zone(lng, lat, poi, riverside_poly, ermawu_poly):
    """叙事片区（地层语义）：ermawu > riverside（几何优先，二马路滨江片区先于泛滨江带，
    避免二马路被泛滨江积极吞掉）> POI 类别 residential/traffic/commercial > general。
    poi 为最近 POI（dict，含 baidu_level1）；几何为 None 时跳过该层。"""
    pt = Point(lng, lat)
    if ermawu_poly is not None and ermawu_poly.contains(pt):
        return 'ermawu'
    if riverside_poly is not None and riverside_poly.contains(pt):
        return 'riverside'
    cat = (poi or {}).get('baidu_level1', '') if isinstance(poi, dict) else ''
    z = POI_NARRATIVE_ZONE.get(cat)
    if z:
        return z
    return 'general'


# ═══════════════ STEP 1: 百度去聚合散点 ═══════════════
def _poisson(mu, rng):
    """Poisson(μ) 采样（零依赖）：μ<30 Knuth 乘积法；μ≥30 正态近似（百度 value 大端）。"""
    if mu >= 30:
        return max(0, int(rng.gauss(mu, math.sqrt(mu))))
    L = math.exp(-mu); k = 0; p = 1.0
    while p > L:
        k += 1; p *= rng.random()
    return k - 1


@track("MOD_PERF.F_010", track_args=False)
def generate_from_heatfield(heats, cc, core, snapshot_id, rng):
    """每热力点 N=Poisson(value×scale×snap_factor)，jitter ~80m，area_type 分类。
    返回 [{'lng','lat','area_type','value'}]。"""
    snap_factor = SNAPSHOTS[snapshot_id]['snap_factor']
    lam = SCALE * snap_factor
    coslat = math.cos(math.radians(30.7))
    out = []
    for hlng, hlat, v in heats:
        for _ in range(_poisson(lam * v, rng)):
            r = JITTER_DEG * math.sqrt(rng.random())   # 圆盘均匀 jitter
            a = rng.uniform(0, 2 * math.pi)
            lng = hlng + r * math.cos(a) / coslat
            lat = hlat + r * math.sin(a)
            at = classify_area_type(lng, lat, cc, core)
            out.append({'lng': lng, 'lat': lat, 'area_type': at, 'value': v})
    by_at = Counter(p['area_type'] for p in out)
    safe_print('[SPATIAL] {} 散点 {} | area_type {} | scale={}×sf={}'.format(
        snapshot_id, len(out), dict(by_at), SCALE, snap_factor))
    return out


# ═══════════════ STEP 2: 注入字段 ═══════════════
def _spatial_confidence(area_type, dens_norm, rng):
    """l1_confidence 空间自相关：密集区高置信。unit 整体偏高（重点区）。"""
    base = {'unit': 0.78, 'core': 0.55, 'central_outer': 0.45}[area_type] + 0.20 * dens_norm
    return round(min(0.99, max(0.40, base + rng.uniform(-0.03, 0.03))), 3)


def _seed_domain_element(snapshot_id, area_type, narrative_zone, poi, rng):
    """层1(80% 有 POI)：继承 POI 的 domain/element；层2：performance_config 区域 × 叙事片区 bias。"""
    if poi and rng.random() < POI_INHERIT_P:
        d, e = poi.get('domain'), poi.get('element')
        if d and e:
            return d, e
    return pick_domain_element(snapshot_id, area_type, narrative_zone, rng)


def _pick_polarity_clustered(snapshot_id, area_type, narrative_zone, poi, rng, domain=None, element=None):
    """叙事片区 arc + 桶覆盖（BUCKET_POLARITY_MOD，驱归因矩阵趋势）+ 仅 general 区叠 POI lean 翻转。
    domain/element 用于桶覆盖；叙事片区极性比已含 neutral/negative 噪声，叠 lean 仅在 general 区。"""
    base = pick_polarity(snapshot_id, area_type, narrative_zone, domain=domain, element=element, rng=rng)
    if narrative_zone == 'general':
        lean = POI_POLARITY_LEAN.get(poi.get('baidu_level1', '')) if poi else None
        if lean and lean != base and rng.random() < LEAN_FLIP_P:
            return lean
    return base


@track("MOD_PERF.F_003", track_args=False)
def inject_fields(pts, snapshot_id, pool, pl, poigrid, rng, riverside_poly=None, ermawu_poly=None):
    snap = SNAPSHOTS[snapshot_id]
    d0, d1 = snap['date_range']
    flavor = snapshot_flavor(snapshot_id)
    # 局部点密度分位（空间自相关信号）
    _lons = np.array([p['lng'] for p in pts]); _lats = np.array([p['lat'] for p in pts])
    _gx = np.floor(_lons / 0.0025).astype(np.int64); _gy = np.floor(_lats / 0.0025).astype(np.int64)
    _cc = Counter(zip(_gx.tolist(), _gy.tolist()))
    _dens = np.array([_cc[(int(x), int(y))] for x, y in zip(_gx, _gy)], dtype=float)
    _dens_norm = (_dens - _dens.min()) / ((_dens.max() - _dens.min()) + 1e-9)
    rows = []
    for i, p in enumerate(pts):
        at = p['area_type']
        in_cc = at != 'outside_cc'   # outside_cc = 市域内中心城区外（纯热度点，不入 L2）
        # 中心城区内：POI 吸附 + 全字段；外：纯热度点
        if in_cc:
            poi = poigrid.nearest(p['lng'], p['lat'], POI_SNAP_M / 111000.0)
            nz = classify_narrative_zone(p['lng'], p['lat'], poi, riverside_poly, ermawu_poly)
            lm = _nearest_landmark(p['lng'], p['lat'])   # 点军地标优先（需求5：500m 内强制 zone+poi+地名）
            if lm:
                poi = {'name': lm['name'], 'domain': lm['domain'], 'element': lm['element'], 'baidu_level1': lm['l1'], 'area': '点军区'}
                nz = lm['zone']
            domain, element = _seed_domain_element(snapshot_id, at, nz, poi, rng)
            polarity = _pick_polarity_clustered(snapshot_id, at, nz, poi, rng, domain=domain, element=element)
            topic = pick_topic(polarity, nz, element, rng)
            # 需求4：核心商圈（夷陵广场周边 600m）+ 中南路（伍家岗）negative 点强制停车难（双锚点扩散聚集）
            if polarity == 'negative' and (_in_core_commercial(p['lng'], p['lat']) or _in_zhongnan(p['lng'], p['lat'])):
                topic = '停车难'
            zone = pl.resolve_zone((poi or {}).get('name', ''), (poi or {}).get('area', ''), p['lng'], p['lat'])
            if topic == '占道停车':
                # 占道停车 60%治理/20%设施/20%环境 → 重映射 domain/element + 专属评论（替通用 sample_text）
                domain, element, text = _zhandao_assign(rng)
            else:
                text = sample_text(polarity, element, pool, rng, zone=nz, flavor=flavor)
            # 点军地标正向 → 专属关键词（楚超/卷桥河露营/江南绿肺）+ 专属评论
            if polarity == 'positive':
                lm = _nearest_landmark(p['lng'], p['lat'])
                if lm and lm['name'] in _DIANJUN_TOPIC:
                    topic = _DIANJUN_TOPIC[lm['name']]
                    text = rng.choice(_DIANJUN_TEXT[topic])
            # T2 施工中期连锁反应 → 建设类消极评论（道路开挖/施工噪音/交通不便，浅红基调）
            if snapshot_id == 'T2' and polarity == 'negative' and (domain, element) in _T2_CONSTRUCTION_TEXT:
                text = rng.choice(_T2_CONSTRUCTION_TEXT[(domain, element)])
            emo_inten = (p['value'] / VALUE_P95)
            emo_inten = max(0.1, min(1.0, emo_inten * (1.4 if polarity in ('positive', 'negative') else 0.7)))
            rows.append({
                'lon': p['lng'], 'lat': p['lat'], 'area_tag': at, 'zone': zone, 'narrative_zone': nz, 'topic': topic,
                'area_seed': (poi or {}).get('name', '') or snap['label'],
                'spatial_hotspot': (poi or {}).get('name', ''),
                'spatial_type': (poi or {}).get('baidu_level1', '') or at,
                'domain': domain, 'element': element, 'polarity_hint': polarity,
                'primary_emotion': rng.choice(EMOTION_BY_POLARITY[polarity]),
                'emotion_intensity': round(emo_inten, 3),
                'intensity': round(rng.uniform(0.6, 1.0) if polarity != 'neutral' else rng.uniform(0.2, 0.5), 2),
                'text': text, 'text_length': len(text),
                'source': rng.choices(list(SOURCE_WEIGHTS), weights=list(SOURCE_WEIGHTS.values()), k=1)[0],
                'created_at': _random_dt(d0, d1, rng),
                'urban_value': rng.choice(URBAN_VALUES),
                'l1_confidence': _spatial_confidence(at, float(_dens_norm[i]), rng),
                'has_location': True, 'location_mentioned': (poi or {}).get('area', '') or '宜昌',
                'relevance': 'relevant', 'relevance_category': (poi or {}).get('baidu_level1', '城市生活'),
                'like_count': int(rng.expovariate(1 / 8)), 'comment_count': int(rng.expovariate(1 / 3)),
                'tags': (poi or {}).get('baidu_level2', ''), 'url': '',
            })
        else:
            # 外中心城区纯热度点（text/polarity 空；hotness=value×密度）
            rows.append({
                'lon': p['lng'], 'lat': p['lat'], 'area_tag': 'outside_cc', 'zone': 'general',
                'area_seed': '', 'spatial_hotspot': '', 'spatial_type': 'background',
                'domain': '', 'element': '', 'polarity_hint': '',
                'primary_emotion': '', 'emotion_intensity': round(max(0.1, min(1.0, p['value'] / VALUE_P95)), 3),
                'intensity': 0.0, 'text': '', 'text_length': 0,
                'source': rng.choices(list(SOURCE_WEIGHTS), weights=list(SOURCE_WEIGHTS.values()), k=1)[0],
                'created_at': _random_dt(d0, d1, rng), 'urban_value': '',
                'l1_confidence': _spatial_confidence('central_outer', float(_dens_norm[i]), rng),
                'has_location': True, 'location_mentioned': '宜昌',
                'relevance': '', 'relevance_category': '', 'like_count': 0, 'comment_count': 0,
                'tags': '', 'url': '',
            })
    return pd.DataFrame(rows)


# ═══════════════ STEP 3: 重点叙事区锚点迁移 ═══════════════
@track("MOD_PERF.F_011", track_args=False)
def apply_anchors(df, snapshot_id, pool, rng):
    forced = ANCHOR_SCHEDULE[snapshot_id]
    n_total = 0
    for a in ANCHORS:
        ap = Point(a['lng'], a['lat'])
        for idx in df.index:
            if ap.distance(Point(df.at[idx, 'lon'], df.at[idx, 'lat'])) < ANCHOR_RADIUS_DEG:
                df.at[idx, 'polarity_hint'] = forced
                df.at[idx, 'text'] = sample_text(forced, df.at[idx, 'element'], pool, rng,
                                                 zone=df.at[idx, 'zone'], flavor=snapshot_flavor(snapshot_id))
                df.at[idx, 'primary_emotion'] = rng.choice(EMOTION_BY_POLARITY[forced])
                df.at[idx, 'area_seed'] = a['name'] + '@锚点'
                n_total += 1
    safe_print('[ANCHOR] {} 强制 {} 极性，影响 {} 点'.format(snapshot_id, forced, n_total))
    return df


# ═══════════════ STEP 4-6: 坐标/keywords/导出/校验（复用 generate_l1_mock 模式）═══════════════
def _random_dt(d0, d1, rng):
    from datetime import datetime, timedelta
    t0 = datetime.strptime(d0, '%Y-%m-%d'); t1 = datetime.strptime(d1, '%Y-%m-%d')
    return (t0 + timedelta(seconds=rng.randint(0, int((t1 - t0).total_seconds())))).strftime('%Y-%m-%dT%H:%M:%S+08:00')


@track("MOD_PERF.F_002", track_args=False)
def transform_coords(df):
    from pyproj import Transformer
    t = Transformer.from_crs('EPSG:4326', 'EPSG:4546', always_xy=True)
    xs, ys = [], []
    for lon, lat in zip(df['lon'], df['lat']):
        try:
            x, y = t.transform(lon, lat); xs.append(round(x, 2)); ys.append(round(y, 2))
        except Exception:
            xs.append(None); ys.append(None)
    df['x_cgcs2000'] = xs; df['y_cgcs2000'] = ys
    return df


@track("MOD_PERF.F_008", track_args=False)
def fill_keywords(df, season_topics):
    try:
        import jieba.analyse
    except ImportError:
        df['keywords'] = ''; return df
    kw = []
    for txt in df['text'].astype(str):
        if not txt or txt == 'nan':
            kw.append(''); continue
        ks = [k for k in jieba.analyse.extract_tags(txt, topK=5, withWeight=False) if len(k) >= 2]
        kw.append(','.join(ks) if ks else '')
    df['keywords'] = kw
    for i in df.index:
        if random.random() < 0.30 and season_topics and df.at[i, 'text']:
            cur = df.at[i, 'keywords']
            df.at[i, 'keywords'] = (cur + ',' if cur else '') + random.choice(season_topics)
    return df


@track("MOD_PERF.F_004", track_args=False)
def export_l1(df, snapshot_id):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    n = len(df); df = df.copy()
    df.insert(0, 'id_e', ['e{}'.format(str(j + 1).zfill(5)) for j in range(n)])
    df['scope'] = SCOPE; df['time_label'] = snapshot_id; df['publish_time'] = df['created_at']
    df = df[[c for c in L1_COLUMNS if c in df.columns]]
    base = '{}_L1_{}_result'.format(SCOPE, snapshot_id)
    csv_path = os.path.join(OUTPUT_DIR, base + '_csv.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8')
    feats = [{'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [r['lon'], r['lat']]},
              'properties': {k: v for k, v in r.items() if k not in ('lon', 'lat')}}
             for _, r in df.iterrows()]
    geo_path = os.path.join(OUTPUT_DIR, base + '_geojson.geojson')
    json.dump({'type': 'FeatureCollection', 'features': feats}, open(geo_path, 'w', encoding='utf-8'), ensure_ascii=False)
    safe_print('[OK] {} L1 {} 点 -> CSV + GeoJSON'.format(snapshot_id, n))
    return csv_path


@track("MOD_PERF.F_009", track_args=False)
def validate_45(df, snapshot_id):
    """4×5 自检：20 格非空 + 区域倾斜方向 + 极性弧 + narrative_zone 落地。"""
    cc = df[df['area_tag'] != 'outside_cc']
    # 防回归：narrative_zone 由 inject_fields 注入（L1_COLUMNS 锁定），缺失即叙事弧未落地。
    # 历史：commit 8eb5185 改引擎加 narrative_zone 但未重生产出入库，旧产出无此字段、validate 静默跳过 → 脱节无人察觉。
    if 'narrative_zone' not in df.columns:
        safe_print('[ERR] {} narrative_zone 字段缺失 — inject_fields 未注入，narrative 弧未落地；'
                   '请勿提交，先排查 inject_fields / L1_COLUMNS'.format(snapshot_id))
        return False
    # 20 格非空
    cells = cc.groupby(['domain', 'element']).size()
    empty = [(d, e) for d in DOMAINS for e in ELEMENTS if (d, e) not in cells.index or cells.get((d, e), 0) == 0]
    # 区域倾斜：unit renewal+governance 占比 > core operation 占比 > central_outer
    def _dom_share(at):
        sub = cc[cc['area_tag'] == at]
        return (sub['domain'].value_counts(normalize=True).to_dict()) if len(sub) else {}
    pol = Counter(cc['polarity_hint'])
    safe_print('[CHECK] {} cc {} 点 | 4×5 空格 {}/20 | polarity {}'.format(
        snapshot_id, len(cc), len(empty), dict(pol)))
    for at in AREA_TYPES:
        safe_print('       {}: {}'.format(at, {k.replace('urban_', ''): round(v, 2) for k, v in _dom_share(at).items()}))
    # 叙事片区 breakdown（narrative_zone：点数 + 极性占比 + domain top2，验 riverside 积极/residential 弧/traffic 消极/ermawu 弧）
    if 'narrative_zone' in cc.columns:
        safe_print('       [narrative]')
        for nz in NARRATIVE_ZONES:
            sub = cc[cc['narrative_zone'] == nz]
            if not len(sub):
                continue
            pol_share = {k: round(v, 2) for k, v in sub['polarity_hint'].value_counts(normalize=True).items()}
            dom_top = sub['domain'].value_counts(normalize=True).head(2).to_dict()
            safe_print('         {}: {} 点 | pol {} | dom {}'.format(
                nz, len(sub), pol_share, {k.replace('urban_', ''): round(v, 2) for k, v in dom_top.items()}))
    if empty:
        safe_print('[WARN] 空格: {}'.format(empty[:5]))
    return len(empty) == 0


# ═══════════════ STEP 7: L1∩中心城区 → L2 ═══════════════
@track("MOD_PERF.F_012", track_args=False)
def run_l2(snapshot_id):
    from emotion_analysis_v1 import run_analysis_task
    # 取 L1 全量，过滤到中心城区子集（area_tag != outside_cc 且有 text）
    df = pd.read_csv(os.path.join(OUTPUT_DIR, '{}_L1_{}_result_csv.csv'.format(SCOPE, snapshot_id)), encoding='utf-8')
    cc_df = df[(df['area_tag'] != 'outside_cc') & df['text'].notna() & (df['text'].astype(str).str.strip() != '')].copy()
    cc_csv = os.path.join(OUTPUT_DIR, '_tmp_{}_cc.csv'.format(snapshot_id))
    cc_df.to_csv(cc_csv, index=False, encoding='utf-8')
    safe_print('[L2] {} cc 子集 {} 点 -> SnowNLP'.format(snapshot_id, len(cc_df)))
    res = run_analysis_task(file_path=cc_csv, engine_type='snownlp',
                            output_name='{}_L2_{}'.format(SCOPE, snapshot_id))
    if os.path.exists(cc_csv):
        os.remove(cc_csv)
    # run_analysis_task 默认输出到 DATA/processed → 移到 DATA/performance
    _move_l2_output(snapshot_id)
    if res.get('success'):
        safe_print('[L2] {} OK | {} 点 | score_mean {:.3f} | {}'.format(
            snapshot_id, res['n_points'], res.get('score_mean', 0), res.get('polarity_stats')))
    else:
        safe_print('[L2][ERR] {} {}'.format(snapshot_id, res.get('message')))
    return res


def _move_l2_output(snapshot_id):
    """run_analysis_task 写 DATA/processed/{name}_L2_result_*（export 追加 _L2_result）；移到 DATA/performance。"""
    import shutil
    src_dir = os.path.join(PROJECT_ROOT, 'DATA', 'processed')
    name = '{}_L2_{}'.format(SCOPE, snapshot_id)   # yichang_L2_T1 → 文件 yichang_L2_T1_L2_result_csv.csv
    for suf in ('_csv.csv', '_geojson.geojson'):
        src = os.path.join(src_dir, name + '_L2_result' + suf)
        dst = os.path.join(OUTPUT_DIR, name + '_L2_result' + suf)
        if os.path.exists(src):
            shutil.move(src, dst)
        elif os.path.exists(dst):
            pass   # 已在 performance
        else:
            safe_print('[L2][WARN] {} 未找到 {}'.format(snapshot_id, name + '_L2_result' + suf))


# ═══════════════ 主流程 ═══════════════
@track("MOD_PERF.F_005", track_args=False)
def main():
    safe_print('=' * 60)
    safe_print('  演示数据最终版生成（百度锚定）— scale={} 全域~34k/快照'.format(SCALE))
    safe_print('  3 快照 T1/T2/T3 | area_type unit/core/central_outer | 4×5 区域×时间倾斜')
    safe_print('=' * 60)
    try:
        heats, pool, pl, poigrid = load_assets()
        cc, core, riverside_poly, ermawu_poly = load_boundaries()
        for sid in ('T1', 'T2', 'T3'):
            snap = SNAPSHOTS[sid]
            safe_print('\n--- {} {} ---'.format(sid, snap['label']))
            rng = random.Random(2606 + ord(sid[1]))
            pts = generate_from_heatfield(heats, cc, core, sid, rng)
            df = inject_fields(pts, sid, pool, pl, poigrid, rng, riverside_poly, ermawu_poly)
            # apply_anchors 已停用：叙事弧现由 narrative_zone + NARRATIVE_POLARITY 驱动
            # （apply_anchors 强制全锚点 T1=negative，与 riverside 全程积极 / ermawu T1 中性冲突）。
            df = transform_coords(df)
            df = fill_keywords(df, snap['season_topics'])
            validate_45(df, sid)
            export_l1(df, sid)
        # L1→L2（中心城区子集）
        safe_print('\n=== L1 → L2（中心城区子集）===')
        for sid in ('T1', 'T2', 'T3'):
            run_l2(sid)
        safe_print('\n[OK] 全部完成 → {}'.format(OUTPUT_DIR))
    except Exception as e:
        safe_print('\n[ERR] {}'.format(e))
        import traceback; traceback.print_exc()
        trace_error("MOD_PERF.F_005", str(e)[:200])
        raise


# ── 追踪 ID 注册 ──
for _id, _desc in [
    ("MOD_PERF.F_001", "加载百度热力点 + 文本池 + POI"),
    ("MOD_PERF.F_002", "坐标转换 WGS84->4546"),
    ("MOD_PERF.F_003", "注入字段（4×5 双层 + 极性 + 文本）"),
    ("MOD_PERF.F_004", "导出 L1 CSV + GeoJSON"),
    ("MOD_PERF.F_005", "主流程 3 快照循环"),
    ("MOD_PERF.F_006", "加载边界 cc/core/unit"),
    ("MOD_PERF.F_008", "jieba keywords + 季节话题"),
    ("MOD_PERF.F_009", "4×5 + 区域倾斜自检"),
    ("MOD_PERF.F_010", "百度去聚合散点（Poisson + jitter）"),
    ("MOD_PERF.F_011", "重点叙事区锚点迁移"),
    ("MOD_PERF.F_012", "L1∩中心城区 -> L2"),
]:
    register_track_id(_id, _desc)

if __name__ == '__main__':
    main()
