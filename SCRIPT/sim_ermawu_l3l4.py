#!/usr/bin/env python3
"""大南门·二马路历史文化街区 L3+L4 演示数据生成器（standalone，不复用城市 sim 引擎）。

策略（vs L1/L2 通用城市 sim）：ABSA aspect 级 + 政策→项目种子 + 归因深化弧（详见 ermawu_l3l4_config）。
空间（Sim-1 buffer 科学化）：boundary polygon 外扩 BUFFER_M(200m) + tapered 密度（核心密、buffer 稀），
  EPSG:4546 米制精确 buffer。人发帖坐标必溢出 boundary 线（GPS 抖动+邻近性）。
资讯素材：DATA/sim/research/ermawu.md（web-search 实采）。

输出：DATA/processed/ermawu_l3l4_{T1,T2,T3}_result_{geojson,csv}（独立集，不覆盖 yichang_L1/L2）。
跑：py SCRIPT/sim_ermawu_l3l4.py
"""
import os
import sys
import json
import random
import datetime as _dt

import numpy as np
from shapely.geometry import Point, shape, mapping
from shapely.ops import transform as shp_transform

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
sys.path.insert(0, _PARENT)
sys.path.insert(0, _HERE)
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from pyproj import Transformer
from core.tracker import track, register_track_id
from core.utils import safe_print
from ermawu_l3l4_config import (
    BOUNDARY_PATH, BUFFER_M, BUFFER_DENSITY_RATIO, TARGET_CRS,
    POINT_COUNT, ASPECTS, T_ASPECT_WEIGHTS, T_ASPECT_POLARITY, SNAPSHOTS, OUTPUT_DIR,
)

random.seed(2606)
np.random.seed(2606)

_WGS84 = 'EPSG:4326'
_TO_M = Transformer.from_crs(_WGS84, TARGET_CRS, always_xy=True)
_TO_WGS = Transformer.from_crs(TARGET_CRS, _WGS84, always_xy=True)

# 极性映射（aspect_polarity → L2 5 级英文 + score 区间 + emotion_type）
_POL_MAP = {
    'pos': {'levels': ['Positive', 'Very Positive'], 'score': (0.62, 0.96), 'emo': ['喜', '乐']},
    'neg': {'levels': ['Negative', 'Very Negative'], 'score': (0.04, 0.40), 'emo': ['怒', '哀', '愁']},
    'neu': {'levels': ['Neutral'], 'score': (0.40, 0.60), 'emo': ['盼', '急']},
}


def _to_metric(geom_wgs):
    """WGS84 shapely geometry → metric(4546)。"""
    return shp_transform(lambda x, y, z=None: _TO_M.transform(x, y), geom_wgs)


def _pts_to_wgs(pts_m):
    """metric (x,y) list → WGS84 (lon,lat) list。"""
    return [(_TO_WGS.transform(x, y)[0], _TO_WGS.transform(x, y)[1]) for (x, y) in pts_m]


def _sample_pts(core_m, buffered_m, n):
    """rejection sample n 点（metric）within buffered_m；tapered（core 全留，buffer-only 留 BUFFER_DENSITY_RATIO）。"""
    minx, miny, maxx, maxy = buffered_m.bounds
    out, tries = [], 0
    while len(out) < n and tries < n * 80:
        tries += 1
        x, y = random.uniform(minx, maxx), random.uniform(miny, maxy)
        p = Point(x, y)
        if not buffered_m.contains(p):
            continue
        if not core_m.contains(p) and random.random() > BUFFER_DENSITY_RATIO:
            continue   # buffer 区密度衰减
        out.append((x, y))
    return out


def _pick_aspect_polarity(t):
    """按 T 的 aspect 权重抽 aspect → 按 aspect×T 极性分布抽 polarity（pos/neg/neu）。"""
    aspects = list(T_ASPECT_WEIGHTS[t].keys())
    weights = list(T_ASPECT_WEIGHTS[t].values())
    aspect = random.choices(aspects, weights=weights, k=1)[0]
    p, n, nu = T_ASPECT_POLARITY[aspect][t]
    pol = random.choices(['pos', 'neg', 'neu'], weights=[p, n, nu], k=1)[0]
    return aspect, pol


def _pick_text(aspect, pol):
    """从 aspect 池按极性取文本；该极性空池 → 回退 neu → 回退任意非空。"""
    info = ASPECTS[aspect]
    pool = info.get(pol, []) or []
    if not pool:
        pool = info.get('neu', []) or []
    if not pool:
        for k in ('pos', 'neg', 'neu'):
            if info.get(k):
                pool = info[k]; break
    return random.choice(pool) if pool else f'{aspect}评论'


def _rand_date(t):
    """T 内随机日期（YYYY-MM-DD）。"""
    lo, hi = SNAPSHOTS[t]['date_range']
    d0 = _dt.date.fromisoformat(lo); d1 = _dt.date.fromisoformat(hi)
    return str(d0 + _dt.timedelta(days=random.randint(0, (d1 - d0).days)))


def _build_props(t, aspect, pol, pt_idx):
    """构一个点的全部属性（L2 既有列 + L3 + L4 新列）。"""
    info = ASPECTS[aspect]
    text = _pick_text(aspect, pol)
    pm = _POL_MAP[pol]
    polarity = random.choice(pm['levels'])
    score = round(random.uniform(*pm['score']), 3)
    # emotion_intensity：负极性略高（情绪更强烈）
    ei = round(random.uniform(0.5, 0.95) if pol == 'neg' else random.uniform(0.3, 0.8), 3)
    # semantic_target：观点对象（细化 target_type）
    return {
        # —— L2 既有列 ——
        'id_e': f'ermawu_{t}_{pt_idx:05d}', 'scope': 'ermawu', 'source': 'sim_ermawu_l3l4',
        'text': text, 'keywords': aspect,
        'domain': info['domain'], 'element': info['element'],
        'score': score, 'polarity': polarity, 'polarity_hint': pol,
        'emotion_intensity': ei, 'l1_confidence': round(random.uniform(0.72, 0.95), 3),
        'l2_confidence': round(random.uniform(0.70, 0.92), 3),
        'emotion_type': random.choice(pm['emo']), 'category': '历史街区',
        'timestamp': _rand_date(t), 'time_label': SNAPSHOTS[t]['label'],
        'urban_value': round(random.uniform(0.4, 0.9), 3),
        'target_type': 'aspect', 'target_detail': aspect,
        'area_tag': 'ermawu', 'zone': 'ermawu', 'has_location': 1, 'relevance': 1,
        # —— L3 语义（ABSA）——
        'aspect_primary': aspect, 'aspect_polarity': pol,
        'aspects_json': json.dumps([aspect], ensure_ascii=False),
        'semantic_target': aspect,
        # —— L4 归因种子 ——
        'policy_seed': info['policy_seed'], 'project_seed': info['project_seed'],
        'matrix_multi': json.dumps(info['matrix_multi'], ensure_ascii=False),
        'attribution_confidence': round(random.uniform(0.68, 0.95), 3),
        'blind_spot': 1 if info['blind_spot'] else 0,
    }


@track("MOD_PERF.F_013", track_args=False)
def generate():
    """生成 T1/T2/T3 三快照 ermawu L3+L4 数据 → DATA/processed/ermawu_l3l4_{T}_result_{geojson,csv}。"""
    import csv
    core_wgs = _load_boundary()
    core_m = _to_metric(core_wgs)
    buffered_m = core_m.buffer(BUFFER_M)
    safe_print(f'[LOAD] boundary core_m area={core_m.area/1e6:.3f} km² | buffered(+{BUFFER_M}m) area={buffered_m.area/1e6:.3f} km²')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    summary = {}
    for t in ('T1', 'T2', 'T3'):
        n = POINT_COUNT[t]
        pts_m = _sample_pts(core_m, buffered_m, n)
        pts_wgs = _pts_to_wgs(pts_m)
        feats = []
        for i, (lon, lat) in enumerate(pts_wgs):
            aspect, pol = _pick_aspect_polarity(t)
            props = _build_props(t, aspect, pol, i)
            feats.append({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [round(lon, 6), round(lat, 6)]}, 'properties': props})
        fc = {'type': 'FeatureCollection', 'features': feats}
        # geojson
        gj_path = os.path.join(OUTPUT_DIR, f'ermawu_l3l4_{t}_result_geojson.geojson')
        with open(gj_path, 'w', encoding='utf-8') as f:
            json.dump(fc, f, ensure_ascii=False)
        # csv（同列）
        csv_path = os.path.join(OUTPUT_DIR, f'ermawu_l3l4_{t}_result_csv.csv')
        cols = list(feats[0]['properties'].keys()) if feats else []
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            w.writerow(cols)
            for ft in feats:
                w.writerow([ft['properties'].get(c, '') for c in cols])
        summary[t] = (len(feats), gj_path, csv_path)
        safe_print(f'[GEN] {t} {SNAPSHOTS[t]["label"]} → {len(feats)} 点 | {os.path.basename(gj_path)} + {os.path.basename(csv_path)}')
    _validate_aspects(summary)
    return summary


def _load_boundary():
    d = json.load(open(BOUNDARY_PATH, encoding='utf-8'))
    feats = d.get('features', [])
    if not feats:
        raise ValueError('boundary 无 features')
    return shape(feats[0]['geometry'])


def _validate_aspects(summary):
    """内置校验：aspect 覆盖 + policy→project 闭合 + T1→T3 弧方向（pos 占比升 / 文化事件主导）。"""
    from collections import Counter
    safe_print('\n=== validate_aspects ===')
    for t in ('T1', 'T2', 'T3'):
        n, gj, _ = summary[t]
        fc = json.load(open(gj, encoding='utf-8'))
        feats = fc['features']
        asp = Counter(f['properties']['aspect_primary'] for f in feats)
        pol = Counter(f['properties']['aspect_polarity'] for f in feats)
        pos_ratio = pol.get('pos', 0) / max(1, len(feats))
        # 文化/事件占比（历史街区特性）
        ce = sum(1 for f in feats if f['properties']['element'] in ('文化', '事件'))
        # policy→project 闭合抽查
        closed = sum(1 for f in feats if f['properties']['policy_seed'] and f['properties']['project_seed'])
        safe_print(f'  {t}: n={len(feats)} | pos率={pos_ratio:.2f} | 文化/事件占比={ce/len(feats):.2f} | policy→project闭合={closed}/{len(feats)}')
        safe_print(f'      aspect 分布 top: {dict(asp.most_common(5))}')
    # 弧方向：T1 pos率 < T3 pos率
    fc1 = json.load(open(summary['T1'][1], encoding='utf-8')); fc3 = json.load(open(summary['T3'][1], encoding='utf-8'))
    pos1 = sum(1 for f in fc1['features'] if f['properties']['aspect_polarity'] == 'pos') / len(fc1['features'])
    pos3 = sum(1 for f in fc3['features'] if f['properties']['aspect_polarity'] == 'pos') / len(fc3['features'])
    safe_print(f'  弧方向 T1 pos率={pos1:.2f} → T3 pos率={pos3:.2f} {"[OK 升温]" if pos3 > pos1 else "[WARN 未升温]"}')


register_track_id("MOD_PERF.F_013", "大南门·二马路 L3+L4 sim 生成器（ABSA aspect + 政策→项目种子 + buffer 科学化）")


if __name__ == '__main__':
    safe_print('═══ ermawu L3+L4 sim 生成器（standalone）═══')
    generate()
    safe_print('═══ done ═══')
