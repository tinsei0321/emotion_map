# ════════════════════════════════════════════════════════════════════
# ⚠ 已废弃（2026-07）—— L1/L2 数据源统一到 sim_performance_data.py + performance_config.py。
#   本文件（ermalu/main 二分、target_total 2500）与 generate_l1_mock.py 同属旧路径，
#   仅作历史保留，勿再调用/扩展。新数据生成见 .claude/agents/sim-emotion-data.agent.md。
# ════════════════════════════════════════════════════════════════════
"""
快照叙事配置 — 3 时间点的极性/领域/要素/区占比演变
=====================================================
驱动"二马路前消极后积极"的城市更新叙事 + 季节调制 + 空间占比动态（v3.3 重平衡）。

SNAPSHOTS（对齐用户叙事 v3.3）:
  T1 (2025-02 春节)        — 二马路一期开街爆满：拥挤投诉为主（消极），年味/人多
  T2 (2025-07 暑假周末)    — 年轻人涌入：中性偏积极，夜经济/打卡
  T3 (2026-05 五一)        — 大南门建成、文旅复苏：积极为主，游客/打卡

空间重平衡（v3.3）:
  zone_caps['ermalu_oldstreet'] = 该快照二马路点量占比上限（根治 v3.2 的 47x 密度）。
  ermalu 12% 占比 -> 密度比 ~21x（原 28%/47x），仍是最热点的可见爆点，但非"好几十倍"。
  target_total 每快照主城总量；flavor 驱动 corpus 时序风味。

叙事弧硬约束(_check)：二马路 T1 消极 >= 55% -> T3 积极 >= 55%。
"""
import os
import sys
import random

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from poi_data.poi_4x5_map import DOMAIN_WEIGHTS, ELEMENT_WEIGHTS, DOMAINS, ELEMENTS


# ── 3 快照配置（v3.3：日期对齐用户叙事 + zone_caps 重平衡 + flavor）──
# polarity: 该快照该区域目标极性分布 {positive, negative, neutral}（和=1）—— 保 arc 不变
# domain_bias / element_bias: 相对基础权的乘性偏移（叙事 + 季节）
# zone_caps: 各区点量占比上限（v3.3 重平衡核心；二马路根治"好几十倍"）
# flavor: corpus 时序风味（节日/暑期/旅游/常态），驱动 sample_text 地域化文本选择
# season_topics: 季节话题（叠到 keywords）
SNAPSHOTS = {
    'T1': {
        'label': '2025-02 春节·二马路一期开街爆满',
        'date_range': ('2025-02-01', '2025-02-10'),
        'season_topics': ['春节', '年货', '开街', '人多', '拥挤'],
        'target_total': 2500,
        'zone_caps': {'ermalu_oldstreet': 0.12},   # 密度比 ~21x（原 47x）
        'ermalu_flavor': 'festival',
        'main_flavor': 'festival',
        # 二马路:开街爆满 -> 拥扰投诉为主(renewal×environment/facility)
        'ermalu_polarity': {'positive': 0.20, 'negative': 0.60, 'neutral': 0.20},
        'ermalu_domain_bias': {'urban_renewal': 2.0, 'urban_governance': 1.3,
                               'urban_operation': 0.6, 'urban_planning': 0.5},
        # 主城:春节偏治理投诉 + 年货运营（v3.3：ermalu 降权后补负面，保 arc）
        'main_polarity': {'positive': 0.36, 'negative': 0.44, 'neutral': 0.20},
        'main_domain_bias': {'urban_governance': 1.4, 'urban_operation': 1.1,
                             'urban_renewal': 0.9, 'urban_planning': 0.8},
        'element_bias': {'facility': 1.3, 'service': 1.1, 'environment': 0.9,
                         'culture': 0.8, 'event': 1.0},
        'ermalu_focus': '春节开街',
    },
    'T2': {
        'label': '2025-07 暑假周末·年轻人涌入',
        'date_range': ('2025-07-12', '2025-07-20'),
        'season_topics': ['暑假', '夜经济', '打卡', '年轻人', '冷饮'],
        'target_total': 2500,
        'zone_caps': {'ermalu_oldstreet': 0.08},   # 暑假周末二马路占比回落
        'ermalu_flavor': 'summer',
        'main_flavor': 'summer',
        # 二马路:年轻人涌入,中性偏积极(夜经济/打卡);埋网红打卡点争议
        'ermalu_polarity': {'positive': 0.40, 'negative': 0.35, 'neutral': 0.25},
        'ermalu_domain_bias': {'urban_renewal': 1.3, 'urban_operation': 1.3,
                               'urban_governance': 1.0, 'urban_planning': 0.7},
        # 主城:暑假偏运营/事件(夜经济/文旅)（v3.3：略压正面保 arc）
        'main_polarity': {'positive': 0.46, 'negative': 0.34, 'neutral': 0.20},
        'main_domain_bias': {'urban_operation': 1.4, 'urban_governance': 1.0,
                             'urban_renewal': 0.9, 'urban_planning': 0.8},
        'element_bias': {'event': 1.4, 'culture': 1.2, 'service': 1.0,
                         'environment': 0.9, 'facility': 0.8},
        'ermalu_focus': '夜经济/打卡',
    },
    'T3': {
        'label': '2026-05 五一·大南门建成文旅爆满',
        'date_range': ('2026-05-01', '2026-05-07'),
        'season_topics': ['五一', '文旅', '大南门', '游客', '打卡'],
        'target_total': 2500,
        'zone_caps': {'ermalu_oldstreet': 0.13},   # 五一旅游峰,略升但仍受控
        'ermalu_flavor': 'tourism',
        'main_flavor': 'tourism',
        # 二马路:大南门建成+文旅复苏,积极为主(operation×culture/service/event)
        'ermalu_polarity': {'positive': 0.65, 'negative': 0.20, 'neutral': 0.15},
        'ermalu_domain_bias': {'urban_operation': 1.6, 'urban_renewal': 1.2,
                               'urban_governance': 0.9, 'urban_planning': 0.7},
        # 主城:五一偏环境(绿化/滨江)+ 运营(文旅/夜经济)
        'main_polarity': {'positive': 0.55, 'negative': 0.30, 'neutral': 0.15},
        'main_domain_bias': {'urban_operation': 1.3, 'urban_governance': 1.0,
                             'urban_renewal': 1.0, 'urban_planning': 0.9},
        'element_bias': {'environment': 1.3, 'culture': 1.2, 'event': 1.2,
                         'service': 1.0, 'facility': 0.8},
        'ermalu_focus': '大南门/文旅复苏',
    },
}


def get_ermalu_target(snapshot_id, total=None):
    """二马路该快照点量 = total × zone_caps['ermalu_oldstreet']（替 v3.2 硬编码 700）。"""
    snap = SNAPSHOTS[snapshot_id]
    total = total if total is not None else snap.get('target_total', 2500)
    cap = snap.get('zone_caps', {}).get('ermalu_oldstreet', 0.12)
    return int(total * cap)


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


def pick_flavor(snapshot_id, area_type):
    """采 corpus 时序风味（festival/summer/tourism/...）。area_type ∈ {'ermalu','main'}。"""
    snap = SNAPSHOTS[snapshot_id]
    return snap['ermalu_flavor'] if area_type == 'ermalu' else snap['main_flavor']


def _check():
    """自检:极性分布和=1 + 叙事弧硬约束(T1 二马路消极>=55%, T3 积极>=55%) + zone_caps。"""
    ok = True
    for sid, snap in SNAPSHOTS.items():
        for key in ('ermalu_polarity', 'main_polarity'):
            s = sum(snap[key].values())
            if abs(s - 1.0) > 1e-9:
                print('[ERR] {} {} 极性和 = {} (!= 1.0)'.format(sid, key, round(s, 4))); ok = False
        cap = snap.get('zone_caps', {}).get('ermalu_oldstreet', 0)
        print('  {} 二马路 cap = {}% -> target {} 点'.format(sid, int(cap * 100), get_ermalu_target(sid)))
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
