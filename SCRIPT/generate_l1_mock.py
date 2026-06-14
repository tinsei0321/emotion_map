#!/usr/bin/env python3
"""
L1 模拟数据生成脚本 v2.2
========================
v2.2 变更:
  - 修复 Polygon 构建：buffer(0) 修复自交，polygonize 提取所有陆地多边形
  - 移除独立水体排除（边界已自然划分陆地/水域）
  - 密度梯度模型：沿江最密 → 核心城区密 → 北部边缘稀 → 东西两端稀
  - 参考百度热力图模式：沿江带状集聚 + 商圈点状热点 + 社区面状中密
  - 热点大量扩展沿江带 + 伍家岗东区
"""

import os, sys, random
import builtins as _bi
from collections import Counter
import pandas as pd
import numpy as np
from pyproj import Transformer

_real_print = _bi.print

def _safe_print(*args, **kwargs):
    try:
        _real_print(*args, **kwargs)
    except UnicodeEncodeError:
        _real_print(*(str(a).encode('ascii','replace').decode('ascii') for a in args), **kwargs)

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.tracker import track, TrackContext, trace_error, register_track_id

# ═══════════════ 全局配置 ═══════════════
random.seed(2606)
np.random.seed(2606)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_CSV = os.path.join(PROJECT_ROOT, 'DATA', 'raw', 'simulated_20260613_100k_raw.csv')
OUTPUT_CSV = os.path.join(PROJECT_ROOT, 'DATA', 'processed', 'simulated_l1_2000_规划范围_L1_result_csv.csv')
BOUNDARY_SHP = os.path.join(PROJECT_ROOT, 'DATA', 'boundaries', '规划范围', '规划范围.shp')
TARGET = 2000

CITY_TAGS = ['城市','城建','规划','环境','社区','民生','投诉','设施','交通','河道','噪音','公共设施','基础设施','本地新闻','城市生活']
TAG_TO_CATEGORY = {
    '城市':'城市','城建':'城建','规划':'规划','环境':'环境','社区':'社区','民生':'民生',
    '投诉':'投诉','设施':'设施','交通':'交通','河道':'环境','噪音':'环境',
    '公共设施':'设施','基础设施':'设施','本地新闻':'本地新闻','城市生活':'城市生活',
}
EMOTIONS = ['满足','期待','失望','愤怒','喜爱','怀念','好奇','中性']
URBAN_VALUES = ['high','medium','low']
YICHANG_PLACES = [
    '西陵区','伍家岗区','点军区','猇亭区','夷陵区',
    '滨江公园','东山公园','运河公园','儿童公园','磨基山公园','夷陵广场',
    '沿江大道','胜利四路','云集路','东山大道','夷陵大道',
    '发展大道','城东大道','港窑路','西陵一路','珍珠路',
    'CBD','万达广场','国贸大厦','均瑶广场','水悦城',
    '锦绣社区','白龙岗小区','绿萝路','体育场路','葛洲坝','三峡大学','长江','黄柏河','东山',
]

# ═══════════════ 密度梯度模型 ═══════════════
# 宜昌主城区特征：
#  - 长江自西北→东南穿过，沿江两岸人口最密
#  - 越往西北（山区）人口越稀，越往东南（伍家岗）相对平坦
#  - 核心商圈分布在沿江带和夷陵大道/东山大道之间
#  - 密度层：沿江带(30.690-30.720) > 核心城区(30.700-30.735) > 北部边缘(30.735-30.760) > 南部边缘(30.600-30.690)

# 密度权重函数：基于纬度（越靠江越密）和经度（中间宽两端窄）
def _density_weight(lon, lat):
    """返回 0~1 的密度权重，模拟真实人口密度梯度。
    - 纬向：lat 30.695~30.715 最高（沿江核心），向外递减
    - 经向：lon 111.31~111.37 最高（双区核心），向两端递减
    """
    # 纬向密度：以沿江带30.705为中心的高斯，sigma=0.025
    lat_score = np.exp(-((lat - 30.705) ** 2) / (2 * 0.025 ** 2))
    # 经向密度：以111.34为中心，sigma=0.04
    lon_score = np.exp(-((lon - 111.34) ** 2) / (2 * 0.04 ** 2))
    # 综合
    return lat_score * lon_score

# ═══════════════ 热点定义（密集覆盖沿江+双区核心）═══════════════
# 格式: (名称, lon, lat, 权重, sigma_deg, 类型)
# 权重越大 = 生成的点的越多
# sigma 小 = 聚簇越紧凑

HOTSPOTS = [
    # ====== 沿江带核心 (lat 30.690-30.710) — 最密集 ======
    # 西陵沿江
    ('滨江公园-镇江阁', 111.280, 30.694, 0.04, 0.003, '沿江休闲'),
    ('滨江公园-双亭', 111.290, 30.697, 0.04, 0.003, '沿江休闲'),
    ('滨江公园-屈原广场', 111.298, 30.699, 0.03, 0.003, '沿江休闲'),
    ('解放路-沿江大道口', 111.295, 30.698, 0.04, 0.002, '沿江商圈'),
    ('云集路-沿江大道口', 111.300, 30.700, 0.04, 0.002, '沿江商圈'),
    # CBD到万达沿江带
    ('CBD江边段', 111.304, 30.702, 0.05, 0.003, '沿江商圈'),
    ('万达江边段', 111.312, 30.704, 0.05, 0.003, '沿江商圈'),
    ('胜利四路江口', 111.308, 30.703, 0.03, 0.002, '沿江社区'),
    # 伍家岗沿江
    ('大公桥江段', 111.335, 30.694, 0.03, 0.004, '沿江社区'),
    ('宝塔河江段', 111.350, 30.692, 0.03, 0.004, '沿江社区'),
    ('伍家岗江段', 111.365, 30.688, 0.03, 0.005, '沿江社区'),
    ('王家河江段', 111.385, 30.680, 0.02, 0.005, '沿江社区'),
    # 西坝方向
    ('西坝岛沿江', 111.278, 30.725, 0.03, 0.008, '沿江社区'),
    ('葛洲坝沿江', 111.275, 30.738, 0.03, 0.006, '沿江社区'),

    # ====== 核心商圈 (lat 30.700-30.715) — 高密度 ======
    # 西陵商圈
    ('CBD中央商务区', 111.303, 30.704, 0.06, 0.0025, '核心商圈'),
    ('国贸大厦', 111.296, 30.702, 0.05, 0.002, '核心商圈'),
    ('均瑶广场', 111.295, 30.703, 0.04, 0.002, '核心商圈'),
    ('大洋百货', 111.301, 30.704, 0.04, 0.002, '核心商圈'),
    ('时代广场', 111.298, 30.706, 0.03, 0.002, '核心商圈'),
    ('夷陵广场', 111.290, 30.698, 0.04, 0.003, '核心商圈'),
    ('步行街', 111.293, 30.704, 0.04, 0.003, '核心商圈'),
    ('西陵一路商区', 111.292, 30.708, 0.03, 0.004, '次级商圈'),
    # 夷陵大道沿线
    ('夷陵大道-西陵段', 111.305, 30.708, 0.03, 0.005, '次级商圈'),
    ('夷陵大道-云集段', 111.310, 30.709, 0.03, 0.004, '次级商圈'),
    ('夷陵大道-胜利段', 111.315, 30.710, 0.03, 0.004, '次级商圈'),
    ('夷陵大道-港窑段', 111.325, 30.713, 0.03, 0.005, '次级商圈'),
    # 伍家岗商圈
    ('万达广场', 111.310, 30.706, 0.05, 0.0025, '核心商圈'),
    ('水悦城', 111.330, 30.718, 0.04, 0.003, '核心商圈'),
    ('中南路商圈', 111.345, 30.678, 0.04, 0.004, '核心商圈'),
    ('五一广场', 111.358, 30.670, 0.04, 0.003, '核心商圈'),
    ('桔城路商圈', 111.370, 30.668, 0.03, 0.005, '次级商圈'),
    ('杨岔路商圈', 111.338, 30.688, 0.03, 0.004, '次级商圈'),

    # ====== 居住社区 (lat 30.698-30.735) — 中高密度 ======
    # 西陵社区
    ('锦绣社区', 111.305, 30.712, 0.03, 0.003, '社区'),
    ('白龙岗', 111.310, 30.715, 0.03, 0.003, '社区'),
    ('绿萝路', 111.298, 30.715, 0.03, 0.004, '社区'),
    ('体育场路', 111.315, 30.700, 0.03, 0.003, '社区'),
    ('胜利四路社区', 111.305, 30.700, 0.03, 0.003, '社区'),
    ('西坝社区', 111.278, 30.735, 0.04, 0.006, '社区'),
    ('夜明珠', 111.290, 30.730, 0.03, 0.004, '社区'),
    ('樵湖岭', 111.285, 30.735, 0.02, 0.003, '社区'),
    ('东门外', 111.298, 30.707, 0.02, 0.003, '社区'),
    ('北门外', 111.292, 30.718, 0.02, 0.003, '社区'),
    ('翁家堰', 111.295, 30.710, 0.02, 0.003, '社区'),
    ('船闸社区', 111.280, 30.745, 0.02, 0.004, '社区'),
    # 伍家岗社区
    ('大公桥社区', 111.340, 30.692, 0.03, 0.003, '社区'),
    ('宝塔河社区', 111.355, 30.680, 0.03, 0.004, '社区'),
    ('万寿桥社区', 111.355, 30.685, 0.03, 0.003, '社区'),
    ('胜利一路社区', 111.370, 30.665, 0.03, 0.004, '社区'),
    ('张家店', 111.350, 30.675, 0.02, 0.003, '社区'),
    ('港务社区', 111.375, 30.660, 0.02, 0.003, '社区'),
    ('王家河', 111.395, 30.655, 0.02, 0.004, '社区'),
    ('合益路', 111.360, 30.655, 0.03, 0.005, '社区'),
    ('花艳社区', 111.420, 30.645, 0.02, 0.006, '社区'),
    ('白沙路', 111.385, 30.662, 0.02, 0.003, '社区'),
    ('港窑路片区', 111.322, 30.705, 0.03, 0.004, '社区'),
    ('东山花园', 111.320, 30.698, 0.02, 0.003, '社区'),
    # 沿江社区（在滨江带内侧）
    ('沿江大道东段社区', 111.318, 30.699, 0.03, 0.005, '社区'),
    ('万达周边社区', 111.314, 30.709, 0.03, 0.004, '社区'),

    # ====== 教育 (中密度) ======
    ('三峡大学', 111.318, 30.725, 0.06, 0.008, '教育'),
    ('三峡职业技术学院', 111.325, 30.710, 0.03, 0.004, '教育'),
    ('宜昌一中', 111.290, 30.712, 0.02, 0.002, '教育'),
    ('夷陵中学', 111.312, 30.695, 0.02, 0.002, '教育'),
    ('葛洲坝中学', 111.282, 30.738, 0.02, 0.003, '教育'),
    ('伍家岗小学', 111.370, 30.665, 0.02, 0.003, '教育'),

    # ====== 公园/休闲 (中密度) ======
    ('儿童公园', 111.305, 30.698, 0.03, 0.004, '公园'),
    ('运河公园', 111.310, 30.712, 0.03, 0.005, '公园'),
    ('东山公园', 111.305, 30.690, 0.02, 0.005, '公园'),

    # ====== 交通节点 (中密度) ======
    ('宜昌站', 111.312, 30.708, 0.03, 0.004, '交通'),
    ('宜昌汽车站', 111.315, 30.710, 0.02, 0.003, '交通'),

    # ====== 北部边缘稀疏点 ======
    ('石板社区', 111.305, 30.750, 0.01, 0.006, '边缘'),
    ('窑湾社区', 111.315, 30.745, 0.01, 0.006, '边缘'),
    ('开发区北', 111.330, 30.745, 0.01, 0.008, '边缘'),
    ('伍家北', 111.380, 30.730, 0.01, 0.008, '边缘'),
]

# 交通廊道（沿主干道线状分布，模拟道路沿线人口）
ROAD_CORRIDORS = [
    ('沿江大道(西→东)', 111.275, 30.694, 111.400, 30.688, 120, 0.0015),
    ('夷陵大道(西→东)', 111.285, 30.705, 111.380, 30.695, 100, 0.0015),
    ('东山大道(西→东)', 111.280, 30.712, 111.395, 30.700, 100, 0.0015),
    ('城东大道(西→东)', 111.290, 30.700, 111.410, 30.685, 70, 0.0015),
    ('胜利四路(南→北)', 111.305, 30.698, 111.315, 30.720, 40, 0.001),
    ('港窑路(南→北)', 111.322, 30.695, 111.335, 30.720, 35, 0.001),
    ('发展大道(南→北)', 111.290, 30.705, 111.340, 30.745, 40, 0.0015),
    ('西陵一路(南→北)', 111.288, 30.700, 111.310, 30.712, 25, 0.001),
    ('珍珠路(南→北)', 111.292, 30.702, 111.307, 30.714, 20, 0.001),
    ('中南路(南→北)', 111.345, 30.670, 111.350, 30.700, 25, 0.001),
]

# ═══════════════ 辅助函数 ═══════════════
def _is_valid_point(lon, lat, boundary):
    """检查点是否在边界内。"""
    from shapely.geometry import Point
    return boundary.contains(Point(lon, lat))

# ═══════════════ STEP 0: 加载边界 ═══════════════
@track("MOD_GEN.F_006", track_args=False)
def load_boundary():
    """加载 shapefile，构建有效 Polygon。"""
    import geopandas as gpd
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    _safe_print(f'[LOAD] 边界: {BOUNDARY_SHP}')
    gdf = gpd.read_file(BOUNDARY_SHP)
    gdf_wgs = gdf.to_crs('EPSG:4326')

    # 尝试 polygonize（LineString ring → Polygon）
    geom = gdf_wgs.geometry.iloc[0]
    raw_poly = None

    if geom.geom_type == 'LineString' and geom.is_ring:
        raw_poly = Polygon(geom.coords)
    elif geom.geom_type == 'Polygon' or geom.geom_type == 'MultiPolygon':
        raw_poly = geom
    else:
        from shapely.ops import polygonize
        polys = list(polygonize([geom]))
        if polys:
            raw_poly = unary_union(polys)

    if raw_poly is None:
        raise ValueError('无法构建 Polygon')

    # 修复自交
    if not raw_poly.is_valid:
        raw_poly = raw_poly.buffer(0)

    # 如果是 MultiPolygon，取最大的一块陆地
    if raw_poly.geom_type == 'MultiPolygon':
        boundary = max(raw_poly.geoms, key=lambda g: g.area)
    elif raw_poly.geom_type == 'GeometryCollection':
        polys = [g for g in raw_poly.geoms if g.geom_type == 'Polygon']
        boundary = max(polys, key=lambda g: g.area)
    else:
        boundary = raw_poly

    _safe_print(f'  类型: {boundary.geom_type}, 有效: {boundary.is_valid}')
    _safe_print(f'  面积: {boundary.area:.6f} deg²')
    _safe_print(f'  范围: lon {boundary.bounds[0]:.4f}~{boundary.bounds[2]:.4f}, lat {boundary.bounds[1]:.4f}~{boundary.bounds[3]:.4f}')
    return boundary

# ═══════════════ STEP 1: 生成空间分布 ═══════════════
@track("MOD_GEN.F_007", track_args=False)
def generate_spatial_points(boundary, n=2000):
    """
    三层叠加 + 密度权重拒绝采样：
    第1层: 热点聚簇 50% (1000)
    第2层: 交通廊道 30% (600)
    第3层: 密度梯度撒点 20% (400) — 按 _density_weight 拒绝采样

    所有点必须 boundary.contains()
    """
    from shapely.geometry import Point

    n_hot = int(n * 0.50)
    n_cor = int(n * 0.30)
    n_bg = n - n_hot - n_cor

    _safe_print(f'[SPATIAL] 热点{n_hot} | 廊道{n_cor} | 密度撒点{n_bg}')

    weights = [h[3] for h in HOTSPOTS]
    total_w = sum(weights)
    points = []
    rejected = 0
    MAX_RETRY = 500

    def gen_valid(sampler):
        nonlocal rejected
        for _ in range(MAX_RETRY):
            lon, lat, name, htype = sampler()
            if _is_valid_point(lon, lat, boundary):
                return (lon, lat, name, htype)
            rejected += 1
        return None

    # 第1层: 核心热点
    def hotspot_sampler():
        r = random.uniform(0, total_w)
        cum = 0.0
        chosen = HOTSPOTS[0]
        for h in HOTSPOTS:
            cum += h[3]
            if r <= cum:
                chosen = h
                break
        lon = np.random.normal(chosen[1], chosen[4])
        lat = np.random.normal(chosen[2], chosen[4])
        return (lon, lat, chosen[0], chosen[5])

    for _ in range(n_hot):
        pt = gen_valid(hotspot_sampler)
        if pt:
            points.append(pt)

    # 第2层: 交通廊道
    for cor in ROAD_CORRIDORS:
        name, sl, sla, el, ela, cnt, w = cor
        dx = el - sl
        dy = ela - sla
        ds = (dx*dx + dy*dy)**0.5
        if ds < 1e-9:
            continue
        ux, uy = dx/ds, dy/ds
        nx, ny = -uy, ux
        def mk_sampler():
            def s():
                t = random.random()
                blon = sl + t*dx
                blat = sla + t*dy
                off = np.random.normal(0, w)
                return (blon + off*nx, blat + off*ny, name, '交通廊道')
            return s
        sampler = mk_sampler()
        for _ in range(cnt):
            pt = gen_valid(sampler)
            if pt:
                points.append(pt)

    # 第3层: 密度梯度撒点（按 _density_weight 拒绝采样）
    bounds = boundary.bounds
    pad = 0.005
    def bg_sampler():
        # 均匀采样 → 按密度权重概率接受
        while True:
            lon = random.uniform(bounds[0]-pad, bounds[2]+pad)
            lat = random.uniform(bounds[1]-pad, bounds[3]+pad)
            if _is_valid_point(lon, lat, boundary):
                dw = _density_weight(lon, lat)
                if random.random() < dw * 3:  # 放大使采样更高效
                    return (lon, lat, '稀疏区域', '背景')

    for _ in range(n_bg):
        pt = gen_valid(bg_sampler)
        if pt:
            points.append(pt)
    # 如果不足，继续用 bg_sampler 补齐
    while len(points) < n:
        pt = gen_valid(bg_sampler)
        if pt:
            points.append(pt)
        if rejected > n * 30:
            _safe_print(f'[WARN] 重试过多({rejected})，停止')
            break

    points = points[:n]
    _safe_print(f'[SPATIAL] 最终: {len(points)} 点 (拒绝: {rejected})')
    tc = Counter(p[3] for p in points)
    for t, c in sorted(tc.items(), key=lambda x: -x[1]):
        _safe_print(f'  {t}: {c}')
    return points

# ═══════════════ STEP 2-8: 数据处理（同 v2.1）═══════════════
@track("MOD_GEN.F_001", track_args=False)
def load_and_filter(pts):
    _safe_print(f'[LOAD] {RAW_CSV}')
    if not os.path.exists(RAW_CSV):
        raise FileNotFoundError(RAW_CSV)
    df = pd.read_csv(RAW_CSV, encoding='utf-8')
    _safe_print(f'  {len(df)} 条')
    with TrackContext("MOD_GEN.D_001", input_n=len(df)):
        p = '|'.join(CITY_TAGS)
        m = df['tags'].astype(str).str.contains(p, case=False, na=False)
        df_c = df[m].copy()
        _safe_print(f'  城市相关: {len(df_c)}')
    if len(df_c) < TARGET:
        df_c = df_c.sample(n=TARGET, replace=True, random_state=2606).reset_index(drop=True)
    else:
        df_c = df_c.sample(n=TARGET, random_state=2606).reset_index(drop=True)
    df_c['lon'] = [p[0] for p in pts]
    df_c['lat'] = [p[1] for p in pts]
    df_c['spatial_hotspot'] = [p[2] for p in pts]
    df_c['spatial_type'] = [p[3] for p in pts]
    return df_c

@track("MOD_GEN.F_002", track_args=False)
def transform_coords(df):
    _safe_print('[TRANSFORM] WGS84->EPSG:4546')
    t = Transformer.from_crs('EPSG:4326', 'EPSG:4546', always_xy=True)
    xs, ys = [], []
    for _, row in df.iterrows():
        try:
            x, y = t.transform(row['lon'], row['lat'])
            xs.append(round(x, 2))
            ys.append(round(y, 2))
        except Exception:
            xs.append(None); ys.append(None)
    df['x_cgcs2000'] = xs
    df['y_cgcs2000'] = ys
    _safe_print(f'  完成: {sum(1 for v in xs if v is not None)}')
    return df

def _map_tag(t):
    if not isinstance(t, str): return '其他'
    for tag in CITY_TAGS:
        if tag in t and tag in TAG_TO_CATEGORY: return TAG_TO_CATEGORY[tag]
    return '其他'

@track("MOD_GEN.F_003", track_args=False)
def inject_l1_fields(df):
    n = len(df)
    df['id_e'] = ['e'+str(i+1).zfill(4) for i in range(n)]
    df['scope'] = '规划范围'
    df['text_length'] = df['text'].astype(str).apply(len) if 'text' in df.columns else 0
    df['location_mentioned'] = [random.choice(YICHANG_PLACES) for _ in range(n)]
    df['has_location'] = True
    df['relevance'] = 'relevant'
    df['relevance_category'] = df['tags'].apply(_map_tag)
    df['primary_emotion'] = [random.choice(EMOTIONS) for _ in range(n)]
    df['emotion_intensity'] = [random.randint(1,5) for _ in range(n)]
    df['urban_value'] = [random.choice(URBAN_VALUES) for _ in range(n)]
    df['l1_confidence'] = [round(random.uniform(0.70,0.99),2) for _ in range(n)]
    if 'comments' in df.columns: df['comments'] = ''
    _safe_print(f'[INJECT] {len(df.columns)} 列')
    return df

@track("MOD_GEN.F_008", track_args=False)
def fill_keywords(df):
    _safe_print('[KEYWORDS] jieba TF-IDF')
    try:
        import jieba.analyse
    except ImportError:
        df['keywords'] = ''
        return df
    kw = []
    for _, row in df.iterrows():
        try:
            t = str(row.get('text',''))
            if t.strip():
                ks = jieba.analyse.extract_tags(t, topK=5, withWeight=False)
                ks = [k for k in ks if len(k)>=2]
                kw.append(','.join(ks) if ks else '')
            else:
                kw.append('')
        except Exception:
            kw.append('')
    df['keywords'] = kw
    _safe_print(f'  有效: {sum(1 for k in kw if k)}/{len(df)}')
    return df

@track("MOD_GEN.F_004", track_args=False)
def export_and_stats(df):
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    EXCLUDE = {'title','ai_summary','lon_gcj02','lat_gcj02','area','comments'}
    col_order = ['id_e','scope','location_mentioned','text','keywords','text_length',
                 'relevance','relevance_category','primary_emotion','emotion_intensity',
                 'urban_value','l1_confidence','has_location','like_count','comment_count',
                 'tags','source','url','crawl_time','publish_time','lon','lat',
                 'x_cgcs2000','y_cgcs2000','spatial_hotspot','spatial_type']
    cols = [c for c in col_order if c in df.columns and c not in EXCLUDE]
    for c in df.columns:
        if c not in cols and c not in EXCLUDE: cols.append(c)
    df = df[cols]
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    _safe_print(f'[OK] CSV: {OUTPUT_CSV} ({len(df)}行 {len(df.columns)}列)')
    _safe_print('\n' + '='*50 + '\n  统计报告\n' + '='*50)
    if 'spatial_type' in df.columns:
        for t, c in df['spatial_type'].value_counts().items():
            _safe_print(f'  {t}: {c}')
    if 'lon' in df.columns:
        _safe_print(f'  lon: {df["lon"].min():.4f}~{df["lon"].max():.4f}')
        _safe_print(f'  lat: {df["lat"].min():.4f}~{df["lat"].max():.4f}')
    return OUTPUT_CSV

@track("MOD_GEN.F_009", track_args=False)
def final_check(df, boundary):
    from shapely.geometry import Point
    bad = sum(1 for _,r in df.iterrows() if not boundary.contains(Point(r['lon'],r['lat'])))
    if bad == 0:
        _safe_print(f'[CHECK] {len(df)}/{len(df)} 全部在范围内 [OK]')
    else:
        _safe_print(f'[CHECK] {bad}/{len(df)} 超出范围! [ERR]')
    return bad == 0

# ═══════════════ 主流程 ═══════════════
@track("MOD_GEN.F_005", track_args=False)
def main():
    _safe_print('='*50)
    _safe_print('  L1 模拟数据生成 v2.2')
    _safe_print(f'  边界: {BOUNDARY_SHP} | 目标: {TARGET}')
    _safe_print('='*50)
    try:
        boundary = load_boundary()
        _safe_print('[0] 边界就绪')
        pts = generate_spatial_points(boundary, TARGET)
        _safe_print(f'[1] 坐标: {len(pts)}')
        df = load_and_filter(pts)
        _safe_print(f'[2] 数据: {len(df)}')
        df = transform_coords(df)
        _safe_print('[3] 坐标转换完成')
        df = inject_l1_fields(df)
        _safe_print('[4] 字段注入完成')
        df = fill_keywords(df)
        _safe_print('[5] keywords完成')
        final_check(df, boundary)
        export_and_stats(df)
        _safe_print('[7] 导出完成')
        _safe_print('\n[OK] 全部完成！')
    except Exception as e:
        _safe_print(f'\n[ERR] {e}')
        import traceback; traceback.print_exc()
        trace_error("MOD_GEN.F_005", str(e)[:200])
        raise

# 注册
register_track_id("MOD_GEN.F_001","加载筛选")
register_track_id("MOD_GEN.F_002","坐标转换")
register_track_id("MOD_GEN.F_003","注入字段")
register_track_id("MOD_GEN.F_004","导出统计")
register_track_id("MOD_GEN.F_005","主流程")
register_track_id("MOD_GEN.F_006","加载边界")
register_track_id("MOD_GEN.F_007","空间分布生成")
register_track_id("MOD_GEN.F_008","jieba关键词")
register_track_id("MOD_GEN.F_009","最终边界校验")
register_track_id("MOD_GEN.D_001","标签筛选")

if __name__ == '__main__':
    main()