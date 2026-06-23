"""
快照叙事配置 — 3 时间点的极性/领域/要素演变
=============================================
驱动"二马路前消极后积极"的城市更新叙事 + 季节调制 + 空间焦点漂移。

SNAPSHOTS:
  T1 (2025-01 冬·春节前) — 二马路改造初期:消极为主(施工扰民/环境差)
  T2 (2025-09 秋·国庆)   — 二马路过渡:中性偏积极(初见成效),埋舆情生命周期
  T3 (2026-04 春·汛前)   — 二马路焕新完成:积极为主(文创/文旅/市集)

叙事弧硬约束(plan 验证项):二马路 T1 消极 >= 55% -> T3 积极 >= 55%。
"""
import os
import sys
import random

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from poi_data.poi_4x5_map import DOMAIN_WEIGHTS, ELEMENT_WEIGHTS, DOMAINS, ELEMENTS


# ── 3 快照配置 ──
# polarity: 该快照该区域目标极性分布 {positive, negative, neutral}（和=1）
# domain_bias: 相对基础 DOMAIN_WEIGHTS 的乘性偏移（叙事 + 季节）
# element_bias: 相对基础 ELEMENT_WEIGHTS 的乘性偏移
# season_topics: 季节话题（Phase B 叠到 keywords/text）
SNAPSHOTS = {
    'T1': {
        'label': '2025-01 冬·春节前',
        'date_range': ('2025-01-05', '2025-01-25'),
        'season_topics': ['春节', '年货', '春运', '年夜饭'],
        # 二马路:改造初期消极为主(renewal×environment/facility 投诉)
        'ermalu_polarity': {'positive': 0.20, 'negative': 0.60, 'neutral': 0.20},
        'ermalu_domain_bias': {'urban_renewal': 2.0, 'urban_governance': 1.3,
                               'urban_operation': 0.6, 'urban_planning': 0.5},
        # 主城:冬偏治理投诉 + 春节运营(年货)
        'main_polarity': {'positive': 0.45, 'negative': 0.35, 'neutral': 0.20},
        'main_domain_bias': {'urban_governance': 1.4, 'urban_operation': 1.1,
                             'urban_renewal': 0.9, 'urban_planning': 0.8},
        'element_bias': {'facility': 1.3, 'service': 1.1, 'environment': 0.9,
                         'culture': 0.8, 'event': 1.0},
        'ermalu_focus': '施工区',   # 二马路焦点(T1 在改造施工段)
    },
    'T2': {
        'label': '2025-09 秋·国庆',
        'date_range': ('2025-09-15', '2025-10-05'),
        'season_topics': ['国庆', '银杏', '文创', '打卡'],
        # 二马路:过渡,中性偏积极(初见成效);埋网红打卡点争议(生命周期事件)
        'ermalu_polarity': {'positive': 0.40, 'negative': 0.35, 'neutral': 0.25},
        'ermalu_domain_bias': {'urban_renewal': 1.3, 'urban_operation': 1.3,
                               'urban_governance': 1.0, 'urban_planning': 0.7},
        # 主城:国庆偏运营/事件(文旅/节庆)
        'main_polarity': {'positive': 0.50, 'negative': 0.30, 'neutral': 0.20},
        'main_domain_bias': {'urban_operation': 1.4, 'urban_governance': 1.0,
                             'urban_renewal': 0.9, 'urban_planning': 0.8},
        'element_bias': {'event': 1.4, 'culture': 1.2, 'service': 1.0,
                         'environment': 0.9, 'facility': 0.8},
        'ermalu_focus': '文创市集',
    },
    'T3': {
        'label': '2026-04 春·汛前',
        'date_range': ('2026-04-10', '2026-04-30'),
        'season_topics': ['夜经济', '文旅复苏', '踏青', '防汛'],
        # 二马路:焕新完成积极为主(operation×culture/service/event)
        'ermalu_polarity': {'positive': 0.65, 'negative': 0.20, 'neutral': 0.15},
        'ermalu_domain_bias': {'urban_operation': 1.6, 'urban_renewal': 1.2,
                               'urban_governance': 0.9, 'urban_planning': 0.7},
        # 主城:春偏环境(绿化/滨江)+ 运营(夜经济)
        'main_polarity': {'positive': 0.55, 'negative': 0.30, 'neutral': 0.15},
        'main_domain_bias': {'urban_operation': 1.3, 'urban_governance': 1.0,
                             'urban_renewal': 1.0, 'urban_planning': 0.9},
        'element_bias': {'environment': 1.3, 'culture': 1.2, 'event': 1.2,
                         'service': 1.0, 'facility': 0.8},
        'ermalu_focus': '文旅复苏',
    },
}


def _weighted_pick(weights_dict, rng):
    """按权重字典采样一个 key。负权重钳到 0.01 防 ValueError。"""
    keys = list(weights_dict.keys())
    weights = [max(float(weights_dict[k]), 0.01) for k in keys]
    return rng.choices(keys, weights=weights, k=1)[0]


def pick_polarity(snapshot_id, area_type, rng=random):
    """采目标极性。area_type ∈ {'ermalu','main'}。返回 positive/negative/neutral。"""
    snap = SNAPSHOTS[snapshot_id]
    dist = snap['ermalu_polarity'] if area_type == 'ermalu' else snap['main_polarity']
    return _weighted_pick(dist, rng)


def pick_domain_element(snapshot_id, area_type, rng=random):
    """采 (domain, element)。叙事 + 季节调制驱动。
    area_type ∈ {'ermalu','main'}:二马路偏 renewal,主城按基础 + 季节。
    domain 与 element 独立采样(边际权重),deep 4x5 交叉分析留 L3/L4。"""
    snap = SNAPSHOTS[snapshot_id]
    dom_bias = snap['ermalu_domain_bias'] if area_type == 'ermalu' else snap['main_domain_bias']
    elem_bias = snap['element_bias']
    dom_weights = {d: DOMAIN_WEIGHTS[d] * dom_bias.get(d, 1.0) for d in DOMAINS}
    elem_weights = {e: ELEMENT_WEIGHTS[e] * elem_bias.get(e, 1.0) for e in ELEMENTS}
    return _weighted_pick(dom_weights, rng), _weighted_pick(elem_weights, rng)


def _check():
    """自检:极性分布和=1 + 叙事弧硬约束(T1 二马路消极>=55%, T3 积极>=55%)。"""
    ok = True
    for sid, snap in SNAPSHOTS.items():
        for key in ('ermalu_polarity', 'main_polarity'):
            s = sum(snap[key].values())
            if abs(s - 1.0) > 1e-9:
                print('[ERR] {} {} 极性和 = {} (!= 1.0)'.format(sid, key, round(s, 4))); ok = False
    # 叙事弧
    t1_neg = SNAPSHOTS['T1']['ermalu_polarity']['negative']
    t3_pos = SNAPSHOTS['T3']['ermalu_polarity']['positive']
    if t1_neg < 0.55:
        print('[ERR] T1 二马路消极 = {} (< 55%)'.format(t1_neg)); ok = False
    if t3_pos < 0.55:
        print('[ERR] T3 二马路积极 = {} (< 55%)'.format(t3_pos)); ok = False
    if ok:
        print('[OK] 极性和均 = 1.0;叙事弧 T1 二马路消极 {}% -> T3 积极 {}%'.format(
            int(t1_neg * 100), int(t3_pos * 100)))
    # 演示采样分布(T1/T3 二马路 domain)
    rng = random.Random(2606)
    for sid in ('T1', 'T3'):
        from collections import Counter
        c = Counter(pick_domain_element(sid, 'ermalu', rng)[0] for _ in range(2000))
        print('  {} 二马路 domain 采样: {}'.format(
            sid, {k.replace('urban_', ''): v for k, v in c.most_common()}))
    return ok


if __name__ == '__main__':
    _check()
