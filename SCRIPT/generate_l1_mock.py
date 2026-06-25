#!/usr/bin/env python3
"""
L1 模拟数据生成 v3.1 — 3 快照 × 西陵伍家+二马路（任务一）
=====================================================
v3.1 变更（任务一，空间生成重做）:
  - 空间生成换「核密度曲面 + 密度引导采样」（POI 投影 4546 -> histogram2d
    -> 可分离高斯卷积 -> 按 P 采样），替 v3.0 的 POI 锚点高斯聚类
  - 解决 v3.0 离散光斑（388 点/格）+ 伍家空白 + 75% 网格空
  - 仅改 generate_zone_points；Phase A + v3.0 非空间部分全复用
v3.0 变更（任务一）:
  - 3 快照（T1 2025-01 / T2 2025-09 / T3 2026-04），二马路叙事弧（前消极后积极）
  - 158 真实 POI 种子作锚点（+ 既有的密度梯度背景填充）
  - 二马路片区（0.6km²）+ 150m 向外 buffer 加密（600-800 点，主城总量内的高密度份额）
  - 校验文本池（SnowNLP 预筛）锚定极性 + 叙事权重（snapshot_config）驱动 domain/element
  - 重点区域埋点（6 固定 POI，极性迁移表 T1 消极→T3 积极）
  - 输出 WGS84 GeoJSON（MapLibre 可渲染）+ CSV
吸收 docs/minimax-workspace 资产，扩展自 v2.2。L1→L2（Step7）见文末 run_l2()。
"""

import os
import sys
import random
import json
from collections import Counter

import pandas as pd
import numpy as np

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
sys.path.insert(0, _PARENT)   # for core.*
sys.path.insert(0, _HERE)     # for snapshot_config / emotion_text_pool / poi_data

from core.tracker import track, TrackContext, trace_error, register_track_id
from core.utils import safe_print
from snapshot_config import SNAPSHOTS, pick_polarity, pick_domain_element, get_ermalu_target, pick_flavor
from emotion_text_pool import load_pool, sample_text
from poi_data.poi_4x5_map import DOMAIN_CN, ELEMENT_CN
from core.place_layer import get_place_layer

random.seed(2606)
np.random.seed(2606)

# ═══════════════ 全局配置 ═══════════════
PROJECT_ROOT = _PARENT
BOUNDARY_MAIN = os.path.join(PROJECT_ROOT, 'DATA', 'boundaries', '西陵伍家核心主城.geojson')
BOUNDARY_ERMALU = os.path.join(PROJECT_ROOT, 'DATA', 'boundaries', '大南门二马路滨江片区.geojson')
BOUNDARY_WATER = os.path.join(PROJECT_ROOT, 'DATA', 'boundaries', '现状水系.geojson')   # 长江+主城水域，扣江得陆域掩膜
POI_SEEDS_FILE = os.path.join(_HERE, 'poi_data', 'yichang_poi_wgs84.json')
POI_AMAP_FILE = os.path.join(_HERE, 'poi_data', 'amap_poi_wgs84.json')   # 阶段2：高德真实 POI 缓存（pull_amap_poi.py 产出）
USE_AMAP_POI = os.environ.get('USE_AMAP_POI', '1') != '0'                # v3.3：默认用 1270 高德真实 POI（真实密度）
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'DATA', 'processed')
SCOPE = 'xiling_wujia'

ERMALU_BUFFER_M = 150        # 二马路向外缓冲（情绪/POI 定位 fuzziness）
TARGET_TOTAL_DEFAULT = 2500  # 默认主城每快照总量（可被 snapshot_config.target_total 覆盖）
ANCHOR_COUNT = 6             # 重点区域埋点 POI 数
ANCHOR_RADIUS_DEG = 0.0008   # ~88m，埋点影响半径

SOURCE_WEIGHTS = {'dianping': 0.30, 'meituan': 0.25, 'xiaohongshu': 0.20, 'weibo': 0.15, '12345': 0.10}
EMOTION_BY_POLARITY = {
    'positive': ['满足', '喜爱', '期待'],
    'negative': ['失望', '愤怒'],
    'neutral': ['中性', '好奇'],
}
URBAN_VALUES = ['high', 'medium', 'low']
ANCHOR_SCHEDULE = {'T1': 'negative', 'T2': 'neutral', 'T3': 'positive'}

L1_COLUMNS = [
    'id_e', 'scope', 'source', 'created_at', 'publish_time', 'text', 'keywords', 'text_length',
    'domain', 'element', 'primary_emotion', 'emotion_intensity', 'polarity_hint', 'intensity',
    'urban_value', 'l1_confidence', 'has_location', 'location_mentioned',
    'relevance', 'relevance_category', 'like_count', 'comment_count', 'tags', 'url',
    'time_label', 'area_seed', 'area_tag', 'zone',
    'lon', 'lat', 'x_cgcs2000', 'y_cgcs2000', 'spatial_hotspot', 'spatial_type',
]


# ═══════════════ 密度梯度（沿用 v2.2，背景填充用）═══════════════
def _density_weight(lon, lat):
    """沿江带最密 -> 核心城区 -> 边缘稀。背景点按此拒绝采样。"""
    lat_score = np.exp(-((lat - 30.705) ** 2) / (2 * 0.025 ** 2))
    lon_score = np.exp(-((lon - 111.34) ** 2) / (2 * 0.04 ** 2))
    return float(lat_score * lon_score)


# ═══════════════ STEP 0: 加载资产 + 边界 ═══════════════
@track("MOD_GEN.F_001", track_args=False)
def load_assets():
    """加载 POI 种子 + 文本池。
    POI 源：默认 158 种子；USE_AMAP_POI=1 且高德缓存存在时换高德真实 POI（阶段2）。"""
    use_amap = USE_AMAP_POI and os.path.exists(POI_AMAP_FILE)
    path = POI_AMAP_FILE if use_amap else POI_SEEDS_FILE
    data = json.load(open(path, encoding='utf-8'))
    pois = data.get('pois', [])
    pool = load_pool()
    safe_print('[LOAD] POI 源 {} | {} 条 | 文本池 {} 格'.format(
        'amap(高德)' if use_amap else 'seeds(158)', len(pois), len(pool)))
    return pois, pool


@track("MOD_GEN.F_006", track_args=False)
def load_boundaries():
    """加载主城 + 二马路边界（WGS84），扣水系（长江+河沟塘）得陆域掩膜；二马路 +150m buffer。
    返回 (main_land, ermalu_buf_land, ermalu_land) —— 均已扣水域，contains() 自然避江。"""
    import geopandas as gpd
    from shapely.geometry import Point
    main = gpd.read_file(BOUNDARY_MAIN).to_crs('EPSG:4326').geometry.union_all()
    ermalu = gpd.read_file(BOUNDARY_ERMALU).to_crs('EPSG:4326').geometry.union_all()
    # 二马路 + buffer（4546 米制 buffer，回 WGS84）
    ermalu_buf = (
        gpd.GeoDataFrame({'geometry': [ermalu]}, crs='EPSG:4326')
        .to_crs('EPSG:4546')
        .buffer(ERMALU_BUFFER_M)
        .to_crs('EPSG:4326')
        .geometry.iloc[0]
    )
    # 扣水系（长江水面 + 内部河沟塘）—— 解决点落江
    water = None
    if os.path.exists(BOUNDARY_WATER):
        water = gpd.read_file(BOUNDARY_WATER).to_crs('EPSG:4326').geometry.union_all()
        main = main.difference(water)
        ermalu = ermalu.difference(water)
        ermalu_buf = ermalu_buf.difference(water)
    _km2 = lambda g: gpd.GeoDataFrame({'geometry': [g]}, crs='EPSG:4326').to_crs('EPSG:4546').geometry.iloc[0].area / 1e6
    safe_print('[LOAD] 主城陆域 {:.2f} km2 | 二马路陆域 {:.3f} | 二马路+buffer {:.3f}{}'.format(
        _km2(main), _km2(ermalu), _km2(ermalu_buf), ' (已扣水系)' if water is not None else ''))
    return main, ermalu_buf, ermalu


def _split_poi_seeds(pois, ermalu_poly):
    """按是否在二马路多边形内，分二马路 / 主城两类 POI 种子。"""
    from shapely.geometry import Point
    ermalu_seeds, main_seeds = [], []
    for p in pois:
        (ermalu_seeds if ermalu_poly.contains(Point(p['lng'], p['lat'])) else main_seeds).append(p)
    safe_print('[POI] 二马路锚点 {} | 主城锚点 {}'.format(len(ermalu_seeds), len(main_seeds)))
    return ermalu_seeds, main_seeds


# ═══════════════ STEP 1: 空间生成（核密度曲面 + 密度引导采样，v3.1）═══════════════
@track("MOD_GEN.F_010", track_args=False)
def generate_zone_points(zone_poly, seeds, n, rng, area_tag):
    """在 zone_poly 内生成 n 点。v3.1：POI 核密度曲面 -> 密度引导采样
    （替 v3.0 的 POI 锚点高斯聚类，消离散光斑 + 伍家空白）。无种子时退化为
    区域内均匀。返回 (pts, tries)，pts 同契约 [{'lon','lat','seed','area_tag'}, ...]。"""
    from shapely.geometry import Point
    if seeds:
        from poi_data.poi_density import DensityField
        df = DensityField(seeds, zone_poly)
        pts = df.sample(n, rng, area_tag)
        return pts, len(pts)
    # 无 POI 种子 -> 区域内均匀采样（密度引导不可用）
    safe_print('[SPATIAL][WARN] {} 无 POI 种子，退化为均匀采样'.format(area_tag))
    out = []
    b = zone_poly.bounds
    pad = 0.003
    tries = 0
    max_tries = max(n * 100, 8000)
    while len(out) < n and tries < max_tries:
        tries += 1
        lon = rng.uniform(b[0] - pad, b[2] + pad)
        lat = rng.uniform(b[1] - pad, b[3] + pad)
        if zone_poly.contains(Point(lon, lat)):
            out.append({'lon': lon, 'lat': lat, 'seed': None, 'area_tag': area_tag})
    return out, tries


def generate_snapshot_spatial(main_poly, ermalu_buf, ermalu_seeds, main_seeds, rng, snapshot_id):
    """主城一套：二马路按 zone_caps 占比（v3.3 替硬编码 700）+ 主城其余按 POI 密度。"""
    snap = SNAPSHOTS[snapshot_id]
    total = snap.get('target_total', TARGET_TOTAL_DEFAULT)
    ermalu_n = get_ermalu_target(snapshot_id, total)
    main_minus_ermalu = main_poly.difference(ermalu_buf)
    e_pts, e_tries = generate_zone_points(ermalu_buf, ermalu_seeds, ermalu_n, rng, 'ermalu')
    n_main = total - len(e_pts)
    m_pts, m_tries = generate_zone_points(main_minus_ermalu, main_seeds, n_main, rng, 'main')
    safe_print('[SPATIAL] {} 二马路 {}/{} ({:.0%}) (拒 {}) | 主城 {} (拒 {})'.format(
        snapshot_id, len(e_pts), total, len(e_pts) / total, e_tries, len(m_pts), m_tries))
    return e_pts + m_pts


# ═══════════════ STEP 2: 注入字段（叙事 + 文本池）═══════════════
@track("MOD_GEN.F_003", track_args=False)
def inject_fields(pts, snapshot_id, pool, rng):
    """每点赋 domain/element/polarity_hint/text/created_at/source/area_seed 等。
    domain/element/polarity 由 snapshot_config 叙事驱动；text 由校验池采样。"""
    snap = SNAPSHOTS[snapshot_id]
    d0, d1 = snap['date_range']
    pl = get_place_layer()
    rows = []
    for i, p in enumerate(pts):
        area_tag = p['area_tag']
        _seed_p = p.get('seed') or {}
        zone = pl.resolve_zone(_seed_p.get('name', ''), _seed_p.get('area', ''), p['lon'], p['lat'])   # name 优先（全市型 zone 按名归）→ 边界 → general
        polarity = pick_polarity(snapshot_id, area_tag, rng)
        domain, element = pick_domain_element(snapshot_id, area_tag, rng)
        flavor = pick_flavor(snapshot_id, area_tag)
        text = sample_text(polarity, element, pool, rng, zone=zone, flavor=flavor)
        seed = p.get('seed') or {}
        rows.append({
            'lon': p['lon'],
            'lat': p['lat'],
            'area_tag': area_tag,
            'zone': zone,
            'area_seed': seed.get('name', '') or (snap['ermalu_focus'] if area_tag == 'ermalu' else '背景'),
            'spatial_hotspot': seed.get('name', ''),
            'spatial_type': seed.get('baidu_level1', '') or ('ermalu' if area_tag == 'ermalu' else 'background'),
            'domain': domain,
            'element': element,
            'polarity_hint': polarity,
            'primary_emotion': rng.choice(EMOTION_BY_POLARITY[polarity]),
            'emotion_intensity': rng.randint(4, 5) if polarity in ('positive', 'negative') else rng.randint(1, 3),
            'intensity': round(rng.uniform(0.6, 1.0) if polarity != 'neutral' else rng.uniform(0.2, 0.5), 2),
            'text': text,
            'text_length': len(text),
            'source': rng.choices(list(SOURCE_WEIGHTS), weights=list(SOURCE_WEIGHTS.values()), k=1)[0],
            'created_at': _random_dt(d0, d1, rng),
            'urban_value': rng.choice(URBAN_VALUES),
            'l1_confidence': round(rng.uniform(0.78, 0.99), 2),
            'has_location': True,
            'location_mentioned': seed.get('area', '') or '宜昌',
            'relevance': 'relevant',
            'relevance_category': seed.get('baidu_level1', '城市生活'),
            'like_count': int(rng.expovariate(1 / 8)),
            'comment_count': int(rng.expovariate(1 / 3)),
            'tags': seed.get('baidu_level2', ''),
            'url': '',
        })
    df = pd.DataFrame(rows)
    return df


def _random_dt(d0, d1, rng):
    """d0/d1 (YYYY-MM-DD) 间随机 ISO 时间。"""
    from datetime import datetime, timedelta
    t0 = datetime.strptime(d0, '%Y-%m-%d')
    t1 = datetime.strptime(d1, '%Y-%m-%d')
    dt = t0 + timedelta(seconds=rng.randint(0, int((t1 - t0).total_seconds())))
    return dt.strftime('%Y-%m-%dT%H:%M:%S+08:00')


# ═══════════════ STEP 3: 重点区域埋点（极性迁移）═══════════════
@track("MOD_GEN.F_011", track_args=False)
def select_anchors(ermalu_seeds, rng):
    """选 ANCHOR_COUNT 个二马路 POI（最高 weight）作埋点。"""
    ranked = sorted(ermalu_seeds, key=lambda s: -float(s.get('weight', 1.0)))
    chosen = ranked[:min(ANCHOR_COUNT, len(ranked))]
    for a in chosen:
        safe_print('  [ANCHOR] {} ({}) w={}'.format(a.get('name'), a.get('area'), a.get('weight')))
    return chosen


@track("MOD_GEN.F_011", track_args=False)
def apply_anchors(df, snapshot_id, anchors, pool, rng):
    """埋点 POI 半径内点强制极性 = ANCHOR_SCHEDULE[snapshot]，重采样文本。
    返回 (df, 埋点点位 mask) 供迁移表统计。"""
    from shapely.geometry import Point
    forced = ANCHOR_SCHEDULE[snapshot_id]
    mask = pd.Series(False, index=df.index)
    for a in anchors:
        ap = Point(a['lng'], a['lat'])
        near = df.apply(lambda r: ap.distance(Point(r['lon'], r['lat'])) < ANCHOR_RADIUS_DEG, axis=1)
        for idx in df.index[near]:
            df.at[idx, 'polarity_hint'] = forced
            df.at[idx, 'text'] = sample_text(forced, df.at[idx, 'element'], pool, rng, zone=df.at[idx, 'zone'])
            df.at[idx, 'primary_emotion'] = rng.choice(EMOTION_BY_POLARITY[forced])
            df.at[idx, 'area_seed'] = (a.get('name', '') or 'anchor') + '@埋点'
            mask[idx] = True
    safe_print('[ANCHOR] {} 强制 {} 极性，影响 {} 点'.format(snapshot_id, forced, int(mask.sum())))
    return df, mask, anchors


# ═══════════════ STEP 4: 坐标转换 WGS84 -> 4546 ═══════════════
@track("MOD_GEN.F_002", track_args=False)
def transform_coords(df):
    from pyproj import Transformer
    t = Transformer.from_crs('EPSG:4326', 'EPSG:4546', always_xy=True)
    xs, ys = [], []
    for lon, lat in zip(df['lon'], df['lat']):
        try:
            x, y = t.transform(lon, lat)
            xs.append(round(x, 2)); ys.append(round(y, 2))
        except Exception:
            xs.append(None); ys.append(None)
    df['x_cgcs2000'] = xs
    df['y_cgcs2000'] = ys
    return df


# ═══════════════ STEP 5: keywords（jieba + 季节话题）═══════════════
@track("MOD_GEN.F_008", track_args=False)
def fill_keywords(df, season_topics):
    try:
        import jieba.analyse
    except ImportError:
        df['keywords'] = ''
        return df
    kw = []
    for txt in df['text'].astype(str):
        ks = jieba.analyse.extract_tags(txt, topK=5, withWeight=False)
        ks = [k for k in ks if len(k) >= 2]
        kw.append(','.join(ks) if ks else '')
    df['keywords'] = kw
    # 30% 叠季节话题
    for i in df.index:
        if random.random() < 0.30 and season_topics:
            cur = df.at[i, 'keywords']
            add = random.choice(season_topics)
            df.at[i, 'keywords'] = (cur + ',' if cur else '') + add
    return df


# ═══════════════ STEP 6: 输出 CSV + GeoJSON（WGS84）═══════════════
@track("MOD_GEN.F_004", track_args=False)
def export_l1(df, snapshot_id):
    """输出 L1 CSV + WGS84 GeoJSON（MapLibre 可渲染）。"""
    from shapely.geometry import Point
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    n = len(df)
    df = df.copy()
    df.insert(0, 'id_e', ['e{}'.format(str(j + 1).zfill(4)) for j in range(n)])
    df['scope'] = SCOPE
    df['time_label'] = snapshot_id
    df['publish_time'] = df['created_at']
    df = df[[c for c in L1_COLUMNS if c in df.columns]]

    base = '{}_L1_{}_result'.format(SCOPE, snapshot_id)
    csv_path = os.path.join(OUTPUT_DIR, base + '_csv.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8')

    # GeoJSON：geometry = WGS84 Point
    feats = []
    for _, r in df.iterrows():
        props = {k: v for k, v in r.items() if k not in ('lon', 'lat')}
        feats.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [r['lon'], r['lat']]},
            'properties': props,
        })
    gj = {'type': 'FeatureCollection', 'features': feats}
    geo_path = os.path.join(OUTPUT_DIR, base + '_geojson.geojson')
    json.dump(gj, open(geo_path, 'w', encoding='utf-8'), ensure_ascii=False)

    safe_print('[OK] {} {} 点 -> CSV + GeoJSON'.format(snapshot_id, n))
    return csv_path, geo_path


# ═══════════════ STEP 7: 校验（边界 + 叙事弧）═══════════════
@track("MOD_GEN.F_009", track_args=False)
def validate_snapshot(df, snapshot_id, main_poly, ermalu_buf):
    from shapely.geometry import Point
    bad = sum(1 for _, r in df.iterrows() if not main_poly.contains(Point(r['lon'], r['lat'])))
    in_erm = sum(1 for _, r in df.iterrows() if ermalu_buf.contains(Point(r['lon'], r['lat'])))
    pol = Counter(df['polarity_hint'])
    safe_print('[CHECK] {} 越界 {}/{} | 二马路(buffer) {} | 极性 {}'.format(
        snapshot_id, bad, len(df), in_erm, dict(pol)))
    return bad == 0


# ═══════════════ 主流程（3 快照循环）══════════════
@track("MOD_GEN.F_005", track_args=False)
def main():
    safe_print('=' * 56)
    safe_print('  L1 模拟数据生成 v3.1 — 3 快照 × 西陵伍家+二马路')
    safe_print('  空间生成：核密度曲面 + 密度引导采样（替 v3.0 锚点聚类）')
    safe_print('  主城目标 {} | 二马路 cap T1={}/T2={}/T3={} | buffer {}m'.format(
        TARGET_TOTAL_DEFAULT, get_ermalu_target('T1'), get_ermalu_target('T2'),
        get_ermalu_target('T3'), ERMALU_BUFFER_M))
    safe_print('=' * 56)
    try:
        pois, pool = load_assets()
        main_poly, ermalu_buf, ermalu_poly = load_boundaries()
        ermalu_seeds, main_seeds = _split_poi_seeds(pois, ermalu_poly)
        anchors = select_anchors(ermalu_seeds, random)
        anchor_rows = []   # 迁移表
        for sid in ('T1', 'T2', 'T3'):
            snap = SNAPSHOTS[sid]
            safe_print('\n--- {} {} ---'.format(sid, snap['label']))
            rng = random.Random(2606 + ord(sid[1]))   # 每快照可复现
            pts = generate_snapshot_spatial(main_poly, ermalu_buf, ermalu_seeds, main_seeds, rng, sid)
            df = inject_fields(pts, sid, pool, rng)
            df, mask, _ = apply_anchors(df, sid, anchors, pool, rng)
            df = transform_coords(df)
            df = fill_keywords(df, snap['season_topics'])
            validate_snapshot(df, sid, main_poly, ermalu_buf)
            export_l1(df, sid)
            # 迁移表：埋点点位极性
            for a in anchors:
                from shapely.geometry import Point
                ap = Point(a['lng'], a['lat'])
                near_pol = [df.at[i, 'polarity_hint']
                            for i in df.index
                            if ap.distance(Point(df.at[i, 'lon'], df.at[i, 'lat'])) < ANCHOR_RADIUS_DEG]
                anchor_rows.append({'anchor': a.get('name', ''), 'snapshot': sid,
                                    'n': len(near_pol),
                                    'positive': near_pol.count('positive'),
                                    'negative': near_pol.count('negative'),
                                    'neutral': near_pol.count('neutral')})
        # 极性迁移表
        mig = pd.DataFrame(anchor_rows)
        mig_path = os.path.join(OUTPUT_DIR, '{}_anchor_polarity_migration.csv'.format(SCOPE))
        mig.to_csv(mig_path, index=False, encoding='utf-8-sig')
        safe_print('\n[OK] 极性迁移表 -> {}'.format(mig_path))
        # Step 7: L1 -> L2（SnowNLP，校验池锚定极性）
        run_l2()
        safe_print('\n[OK] v3.0 全部完成（L1 + L2）！')
    except Exception as e:
        safe_print('\n[ERR] {}'.format(e))
        import traceback; traceback.print_exc()
        trace_error("MOD_GEN.F_005", str(e)[:200])
        raise


# ═══════════════ Step 7：L1→L2 管线 ═══════════════
@track("MOD_GEN.F_012", track_args=False)
def run_l2():
    """L1 CSV -> emotion_analysis_v1.run_analysis_task() -> L2（score/polarity/emotion_type）。
    校验池保证 L2 极性 = 目标 polarity_hint（确定性）；真实 SnowNLP 分提供可信数值。
    返回 {sid: result_dict}。"""
    from emotion_analysis_v1 import run_analysis_task
    stats = {}
    for sid in ('T1', 'T2', 'T3'):
        csv_in = os.path.join(OUTPUT_DIR, '{}_L1_{}_result_csv.csv'.format(SCOPE, sid))
        if not os.path.exists(csv_in):
            safe_print('[L2][WARN] {} L1 不存在，跳过'.format(sid))
            continue
        safe_print('[L2] {} SnowNLP 分析中...'.format(sid))
        res = run_analysis_task(file_path=csv_in, engine_type='snownlp',
                                output_name='{}_L2_{}'.format(SCOPE, sid))
        if res.get('success'):
            stats[sid] = res
            safe_print('[L2] {} OK | {} 点 | score_mean {:.3f} | {}'.format(
                sid, res['n_points'], res.get('score_mean', 0), res.get('polarity_stats')))
        else:
            safe_print('[L2][ERR] {} {}'.format(sid, res.get('message')))
    return stats


# ── 追踪 ID 注册 ──
register_track_id("MOD_GEN.F_001", "加载 POI 种子 + 文本池")
register_track_id("MOD_GEN.F_002", "坐标转换 WGS84->4546")
register_track_id("MOD_GEN.F_003", "注入字段（叙事 + 文本池）")
register_track_id("MOD_GEN.F_004", "导出 L1 CSV + GeoJSON")
register_track_id("MOD_GEN.F_005", "主流程 3 快照循环")
register_track_id("MOD_GEN.F_006", "加载边界 + 二马路 buffer")
register_track_id("MOD_GEN.F_008", "jieba keywords + 季节话题")
register_track_id("MOD_GEN.F_009", "快照校验（边界 + 极性）")
register_track_id("MOD_GEN.F_010", "空间生成（核密度曲面 + 密度引导采样 v3.1）")
register_track_id("MOD_GEN.F_011", "重点区域埋点（极性迁移）")
register_track_id("MOD_GEN.F_012", "L1->L2 管线（待接）")
register_track_id("MOD_GEN.D_001", "标签筛选（v2.2 保留）")

if __name__ == '__main__':
    main()
