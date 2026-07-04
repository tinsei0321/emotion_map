"""
演示数据叙事配置（百度锚定版）— performance_config
=================================================
3 快照 × 3 级 area_type 的极性弧 + 4×5 区域×时间倾斜。供 sim_performance_data.py。

【2026-07 演示调参（业内同行 demo）】
  - 演示对象 = 业内同行 → 4×5 整体略偏【规划/更新】（硬件板块），但保四域基本平衡、倾向仅微弱。
  - T1 偏硬件（规划/更新 facility/environment），T3 偏软件（运营/治理 event/service/culture）。
    ⇒ SNAPSHOT_TIME_DOMAIN/ELEMENT_MOD 已据此反转（旧版 T1 治理↑/T3 运营↑ 与本演示诉求相反）。
  - 极性弧：T1 消极 > 积极（春节开街扰扰 + 老旧/交通问题），T3 积极 > 消极（大南门建成 + 文旅复苏）。
  - 防 4×5 一家独大：core 的 operation bias 由 1.6 降至 1.25（避免某桶 count 远超他桶、矩阵失梯度）。
  - 新增 venue（奥体/体育场路场馆）+ park_plaza（公园广场）两叙事片区，补全运营/更新板块的落点。

area_type 三级（按边界嵌套，互斥优先级 unit > core > central_outer；注：sim 实际产 core/central_outer/outside_cc）：
  unit          指定单元/社区（更新单元 ∪ 二马路）—— 更新/治理问题密集，强极性弧（T1消极→T3积极）
  core          核心主城热流区（西陵伍家 ∖ unit）—— 四域较均衡，温和弧；演示核心落点区
  central_outer 中心城区外围（中心城区 ∖ 西陵伍家）—— 规划/更新/治理较均匀，慢变

4×5 双层倾斜（贴近真实，非均匀，不空格）：
  层1 POI 锚定（80%）—— 点最近 POI 的 domain/element 经 AMAP_L1_TO_4X5 派生（区域 POI 组成天然分化）
  层2 背景_bias（20%）—— 本配置的 AREA_TYPE_DOMAIN_BIAS × SNAPSHOT_TIME_MOD（乘性叠 DOMAIN_WEIGHTS 基础权）
所有合成权重钳 ≥0.05 底权（20 格全有计数；倾斜是偏好非清零）。

叙事弧硬约束：T1 unit 消极≥55% → T3 unit 积极≥55%。
scale=0.639 点/value-unit（固化，全域~34k/快照）。
"""
import os
import sys
import random

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from poi_data.poi_4x5_map import DOMAIN_WEIGHTS, ELEMENT_WEIGHTS, DOMAINS, ELEMENTS

AREA_TYPES = ('unit', 'core', 'central_outer')

# ═══ 叙事片区 narrative_zone（在 area_type 之上的地层语义层，驱极性弧 + 4×5 + 文本）═══
# 8 片区（2026-07 增 venue/park_plaza）：
#   riverside   滨江带（长江水体 ∩ 中心城区 buffer ~400m）—— 25km 滨江绿廊全线贯通、夜经济/灯会/步道三线；
#               全程积极主导（江景/公园/晨跑/骑行/节日庆典），留少量 neutral(盼绿道延伸) + negative(噪音/停车) 保真实。
#   residential 老旧小区（POI 商务住宅密集）—— 西陵/伍家岗老小区改造、加装电梯"一拖二"、物业缺失；
#               T1 消极（电梯难/破旧/物业差）→ T3 中性期盼（焕新）。
#   traffic     主干道/路口（POI 交通设施服务）—— 东山大道/胜利三路/云集路带状地形拥堵、施工绕行、红绿灯长；全程消极。
#   commercial  商圈（POI 餐饮/购物/住宿）—— 夷陵广场/国贸/九州商贸中心；停车难/业态调整，混合偏消极→期盼升级。
#   ermawu      二马路历史街区（大南门二马路滨江片区 polygon）—— 1877 百年老街"修旧如旧"2025 焕新；中性(盼开街)→积极(网红打卡/夜经济)。
#   venue       大型活动场馆（POI 体育休闲服务：奥体中心/体育场路体育场馆）—— 赛事/演唱会聚集；
#               T1 中性偏消极(筹备/施工) → T3 积极(活动办得好)，混消极(停车/拥堵/噪音)。
#   park_plaza  公园广场（POI 风景名胜：滨江公园大广场/儿童公园/夷陵广场等）—— 绿地+公共活动空间；
#               全程积极偏多(体验好/活动多)，温和递进。
#   general     其余 —— 回退 area_type 级极性/倾斜（core/central_outer）。
# 极性弧硬约束：riverside 全程积极≥60%；residential T1 消极≥55%→T3 中性+积极≥65%；traffic 全程消极≥55%；ermawu T3 积极≥55%。
NARRATIVE_ZONES = ('riverside', 'residential', 'traffic', 'commercial', 'ermawu', 'venue', 'park_plaza', 'general')

# 叙事片区 domain 倾斜乘子（叠在 area_type bias 之上；general=1.0 纯回退）
NARRATIVE_DOMAIN_BIAS = {
    'riverside':   {'urban_operation': 1.5, 'urban_planning': 1.3, 'urban_governance': 0.85, 'urban_renewal': 0.75},
    'residential': {'urban_renewal': 1.9, 'urban_governance': 1.3, 'urban_planning': 1.1, 'urban_operation': 0.75},
    'traffic':     {'urban_governance': 1.9, 'urban_planning': 1.2, 'urban_operation': 1.0, 'urban_renewal': 0.8},
    'commercial':  {'urban_operation': 1.6, 'urban_governance': 1.2, 'urban_planning': 1.0, 'urban_renewal': 0.85},
    'ermawu':      {'urban_renewal': 1.6, 'urban_operation': 1.5, 'urban_planning': 1.0, 'urban_governance': 0.9},
    'venue':       {'urban_operation': 1.7, 'urban_governance': 1.3, 'urban_planning': 1.0, 'urban_renewal': 0.85},   # 场馆：运营(活动)+治理(人流)
    'park_plaza':  {'urban_renewal': 1.4, 'urban_planning': 1.4, 'urban_operation': 1.1, 'urban_governance': 0.95},   # 公园广场：更新+规划(绿地系统)
    'general':     {'urban_operation': 1.0, 'urban_planning': 1.0, 'urban_governance': 1.0, 'urban_renewal': 1.0},
}
# 叙事片区 element 倾斜乘子
NARRATIVE_ELEMENT_BIAS = {
    'riverside':   {'environment': 1.6, 'culture': 1.4, 'event': 1.3, 'facility': 0.8, 'service': 0.7},
    'residential': {'facility': 1.7, 'service': 1.4, 'environment': 1.2, 'culture': 0.7, 'event': 0.6},
    'traffic':     {'event': 1.6, 'facility': 1.4, 'service': 0.9, 'environment': 0.8, 'culture': 0.6},
    'commercial':  {'service': 1.6, 'culture': 1.2, 'event': 1.1, 'facility': 1.0, 'environment': 0.8},
    'ermawu':      {'culture': 1.7, 'event': 1.5, 'facility': 1.0, 'service': 0.9, 'environment': 0.8},
    'venue':       {'event': 1.8, 'facility': 1.4, 'service': 1.0, 'culture': 0.9, 'environment': 0.7},   # 场馆：事件(赛事/演唱会)
    'park_plaza':  {'environment': 1.7, 'facility': 1.3, 'culture': 1.2, 'service': 1.0, 'event': 0.8},   # 公园广场：环境
    'general':     {'facility': 1.0, 'environment': 1.0, 'service': 1.0, 'culture': 1.0, 'event': 1.0},
}
# POI baidu_level1 类别 → 叙事片区（几何优先 riverside/ermawu 之后用此判定 residential/traffic/commercial/venue/park_plaza）
POI_NARRATIVE_ZONE = {
    '商务住宅': 'residential',
    '交通设施服务': 'traffic',
    '餐饮服务': 'commercial', '购物服务': 'commercial', '住宿服务': 'commercial',
    '体育休闲服务': 'venue',        # 奥体中心 / 体育场路体育场馆 / 大型活动场馆
    '风景名胜': 'park_plaza',       # 滨江公园大广场 / 儿童公园 / 夷陵广场 等公园广场
}

# ── 区域 domain 倾斜（相对 DOMAIN_WEIGHTS 基础权的乘子）──
# 2026-07：core operation 由 1.6→1.25（防 4×5 单桶 count 一家独大致矩阵失梯度）；整体略提 planning/renewal（业内同行 demo）。
AREA_TYPE_DOMAIN_BIAS = {
    'unit':          {'urban_renewal': 1.7, 'urban_governance': 1.4, 'urban_planning': 1.2, 'urban_operation': 0.85},
    'core':          {'urban_operation': 1.25, 'urban_governance': 1.2, 'urban_planning': 1.15, 'urban_renewal': 1.1},
    'central_outer': {'urban_planning': 1.3, 'urban_renewal': 1.2, 'urban_governance': 1.15, 'urban_operation': 1.0},
}
# ── 区域 element 倾斜 ──
AREA_TYPE_ELEMENT_BIAS = {
    'unit':          {'facility': 1.4, 'service': 1.2, 'environment': 1.0, 'culture': 0.85, 'event': 0.7},
    'core':          {'service': 1.15, 'event': 1.2, 'culture': 1.1, 'facility': 1.0, 'environment': 0.95},
    'central_outer': {'facility': 1.2, 'environment': 1.2, 'service': 1.1, 'culture': 0.95, 'event': 0.85},
}
# ── 快照时间调制（叠在区域 bias 上，乘性）──
# 2026-07 反转：T1 偏硬件（规划/更新），T3 偏软件（运营/治理）。旧版 T1 治理↑/T3 运营↑ 与本演示诉求相反，已废。
SNAPSHOT_TIME_DOMAIN_MOD = {
    'T1': {'urban_planning': 1.3, 'urban_renewal': 1.25, 'urban_governance': 1.0, 'urban_operation': 0.85},   # 春节：规划/更新↑（硬件）
    'T2': {'urban_planning': 1.0, 'urban_renewal': 1.0, 'urban_operation': 1.15, 'urban_governance': 1.0},    # 暑假：均衡略运营（夜经济）
    'T3': {'urban_operation': 1.3, 'urban_governance': 1.2, 'urban_renewal': 1.0, 'urban_planning': 0.9},     # 五一：运营/治理↑（软件：文旅/人流治理）
}
SNAPSHOT_TIME_ELEMENT_MOD = {
    'T1': {'facility': 1.3, 'environment': 1.2, 'service': 1.0, 'culture': 0.9, 'event': 0.9},    # 硬件要素
    'T2': {'event': 1.3, 'culture': 1.1, 'service': 1.1, 'facility': 0.95, 'environment': 0.95},
    'T3': {'culture': 1.3, 'event': 1.25, 'service': 1.15, 'environment': 1.0, 'facility': 0.85}, # 软件/事件要素
}

_W_FLOOR = 0.05   # 合成权重底权（防 4×5 任一格清零；DOMAIN_WEIGHTS 本身 0.1–0.45，底权须远小于之，否则压平倾斜）

# ── 3 快照（日期对齐用户叙事；polarity 按 area_type 三级）──
# 2026-07：T1 central_outer 微调 neg>pos（强化"T1 消极>积极"故事性）。
SNAPSHOTS = {
    'T1': {
        'label': '2025-02 春节·二马路一期开街爆满',
        'date_range': ('2025-02-01', '2025-02-10'),
        'season_topics': ['春节', '年货', '开街', '人多', '拥挤'],
        'snap_factor': 1.0,
        'flavor': 'festival',
        'polarity': {
            'unit':          {'positive': 0.20, 'negative': 0.60, 'neutral': 0.20},   # 开街扰扰投诉为主（强弧起点）
            'core':          {'positive': 0.30, 'negative': 0.55, 'neutral': 0.15},   # 春节治理投诉偏重（core 弧加强，全域可见）
            'central_outer': {'positive': 0.38, 'negative': 0.42, 'neutral': 0.20},   # 外围消极略多（保 T1 消极>积极）
        },
    },
    'T2': {
        'label': '2025-07 暑假周末·年轻人涌入',
        'date_range': ('2025-07-12', '2025-07-20'),
        'season_topics': ['暑假', '夜经济', '打卡', '年轻人', '冷饮'],
        'snap_factor': 0.95,
        'flavor': 'summer',
        'polarity': {
            'unit':          {'positive': 0.40, 'negative': 0.35, 'neutral': 0.25},
            'core':          {'positive': 0.46, 'negative': 0.34, 'neutral': 0.20},
            'central_outer': {'positive': 0.45, 'negative': 0.35, 'neutral': 0.20},
        },
    },
    'T3': {
        'label': '2026-05 五一·大南门建成文旅爆满',
        'date_range': ('2026-05-01', '2026-05-07'),
        'season_topics': ['五一', '文旅', '大南门', '游客', '打卡'],
        'snap_factor': 1.05,
        'flavor': 'tourism',
        'polarity': {
            'unit':          {'positive': 0.65, 'negative': 0.20, 'neutral': 0.15},   # 大南门建成+文旅复苏（强弧终点）
            'core':          {'positive': 0.62, 'negative': 0.25, 'neutral': 0.13},   # 五一文旅积极为主（core 弧加强）
            'central_outer': {'positive': 0.50, 'negative': 0.33, 'neutral': 0.17},
        },
    },
}


# ── 叙事片区极性弧（3 快照 × 7 片区；新闻锚定，非均匀，留 neutral/negative 保真实）──
# riverside 全程积极主导（~65-78%，留 ~15% neutral 期盼 + ~10% negative 噪音/停车）；
# residential T1 消极(电梯难/物业差/破旧)→T3 中性+积极(焕新)；traffic 全程消极(带状地形拥堵)；
# commercial 混合偏消极→期盼；ermawu T1 中性(施工/盼开街)→T3 积极(网红打卡/夜经济)。
# venue T1 中性偏消极(筹备)→T3 积极(赛事/演唱会)；park_plaza 全程积极偏多(温和递进)。
NARRATIVE_POLARITY = {
    'T1': {   # 2025-02 春节·二马路一期开街爆满
        'riverside':   {'positive': 0.55, 'negative': 0.20, 'neutral': 0.25},   # 降积极（配合 buffer 缩小）保 T1 总盘消极>积极；仍积极主导
        'residential': {'positive': 0.18, 'negative': 0.55, 'neutral': 0.27},
        'traffic':     {'positive': 0.10, 'negative': 0.65, 'neutral': 0.25},
        'commercial':  {'positive': 0.25, 'negative': 0.45, 'neutral': 0.30},
        'ermawu':      {'positive': 0.30, 'negative': 0.30, 'neutral': 0.40},
        'venue':       {'positive': 0.28, 'negative': 0.32, 'neutral': 0.40},   # 筹备期中性偏消极
        'park_plaza':  {'positive': 0.48, 'negative': 0.17, 'neutral': 0.35},   # 春节公园广场活动积极
    },
    'T2': {   # 2025-07 暑假周末·年轻人涌入
        'riverside':   {'positive': 0.66, 'negative': 0.12, 'neutral': 0.22},   # 微降（配合 buffer 缩小）靠 T2 三色基本持平
        'residential': {'positive': 0.30, 'negative': 0.40, 'neutral': 0.30},
        'traffic':     {'positive': 0.12, 'negative': 0.60, 'neutral': 0.28},
        'commercial':  {'positive': 0.32, 'negative': 0.38, 'neutral': 0.30},
        'ermawu':      {'positive': 0.45, 'negative': 0.25, 'neutral': 0.30},
        'venue':       {'positive': 0.45, 'negative': 0.23, 'neutral': 0.32},   # 暑期赛事积极
        'park_plaza':  {'positive': 0.56, 'negative': 0.14, 'neutral': 0.30},
    },
    'T3': {   # 2026-05 五一·大南门建成文旅爆满（riverside 不动，T3 要积极多）
        'riverside':   {'positive': 0.78, 'negative': 0.07, 'neutral': 0.15},
        'residential': {'positive': 0.42, 'negative': 0.28, 'neutral': 0.30},
        'traffic':     {'positive': 0.15, 'negative': 0.58, 'neutral': 0.27},
        'commercial':  {'positive': 0.38, 'negative': 0.35, 'neutral': 0.27},
        'ermawu':      {'positive': 0.60, 'negative': 0.18, 'neutral': 0.22},
        'venue':       {'positive': 0.55, 'negative': 0.23, 'neutral': 0.22},   # 五一演唱会/赛事积极
        'park_plaza':  {'positive': 0.62, 'negative': 0.13, 'neutral': 0.25},   # 文旅积极
    },
}


def pick_polarity(snapshot_id, area_type, narrative_zone='general', rng=random):
    """采目标极性（positive/negative/neutral）。
    narrative_zone != 'general' → 用 NARRATIVE_POLARITY 叙事弧；否则回退 area_type 级分布。"""
    if narrative_zone and narrative_zone != 'general':
        dist = NARRATIVE_POLARITY[snapshot_id].get(narrative_zone)
        if dist:
            keys = list(dist.keys())
            return rng.choices(keys, weights=[dist[k] for k in keys], k=1)[0]
    dist = SNAPSHOTS[snapshot_id]['polarity'][area_type]
    keys = list(dist.keys())
    return rng.choices(keys, weights=[dist[k] for k in keys], k=1)[0]


def _compose_weights(base, area_bias, time_mod):
    """base × area_bias × time_mod，钳 ≥ _W_FLOOR。返回 {key: weight}。"""
    out = {}
    for k, bw in base.items():
        w = float(bw) * area_bias.get(k, 1.0) * time_mod.get(k, 1.0)
        out[k] = max(w, _W_FLOOR)
    return out


def pick_domain_element(snapshot_id, area_type, narrative_zone='general', rng=random):
    """采 (domain, element)：基础权 × area_type bias × 叙事片区 bias × 时间调制，独立采样，底权≥_W_FLOOR。

    narrative_zone 叠加倾斜（riverside→operation/environment/culture、residential→renewal/facility、
    traffic→governance/event、commercial→operation/service、ermawu→renewal/culture、
    venue→operation/event、park_plaza→renewal·planning/environment）；general=1.0 纯回退。
    domain 与 element 边际独立采样（deep 4×5 交叉留 L3/L4）。"""
    nz_dom = NARRATIVE_DOMAIN_BIAS.get(narrative_zone or 'general', NARRATIVE_DOMAIN_BIAS['general'])
    nz_elm = NARRATIVE_ELEMENT_BIAS.get(narrative_zone or 'general', NARRATIVE_ELEMENT_BIAS['general'])
    dom_w = _compose_weights(DOMAIN_WEIGHTS, AREA_TYPE_DOMAIN_BIAS[area_type], SNAPSHOT_TIME_DOMAIN_MOD[snapshot_id])
    dom_w = {k: max(v * nz_dom.get(k, 1.0), _W_FLOOR) for k, v in dom_w.items()}
    elm_w = _compose_weights(ELEMENT_WEIGHTS, AREA_TYPE_ELEMENT_BIAS[area_type], SNAPSHOT_TIME_ELEMENT_MOD[snapshot_id])
    elm_w = {k: max(v * nz_elm.get(k, 1.0), _W_FLOOR) for k, v in elm_w.items()}
    dom = rng.choices(list(dom_w.keys()), weights=list(dom_w.values()), k=1)[0]
    elm = rng.choices(list(elm_w.keys()), weights=list(elm_w.values()), k=1)[0]
    return dom, elm


def snapshot_flavor(snapshot_id):
    return SNAPSHOTS[snapshot_id]['flavor']


def _check():
    """自检：极性和=1 + 叙事弧 + domain 合成权重展示 + 演示采样。"""
    ok = True
    for sid, snap in SNAPSHOTS.items():
        for at, dist in snap['polarity'].items():
            s = sum(dist.values())
            if abs(s - 1.0) > 1e-9:
                print('[ERR] {} {} 极性和={}'.format(sid, at, round(s, 4))); ok = False
    for sid in NARRATIVE_POLARITY:
        for nz, dist in NARRATIVE_POLARITY[sid].items():
            s = sum(dist.values())
            if abs(s - 1.0) > 1e-9:
                print('[ERR] {} {} 叙事极性和={}'.format(sid, nz, round(s, 4))); ok = False
    t1u_neg = SNAPSHOTS['T1']['polarity']['unit']['negative']
    t3u_pos = SNAPSHOTS['T3']['polarity']['unit']['positive']
    if t1u_neg < 0.55: print('[ERR] T1 unit 消极 {} < 55%'.format(t1u_neg)); ok = False
    if t3u_pos < 0.55: print('[ERR] T3 unit 积极 {} < 55%'.format(t3u_pos)); ok = False
    if ok:
        print('[OK] 极性和=1.0；叙事弧 T1 unit 消极 {}% → T3 积极 {}%；片区数={}'.format(
            int(t1u_neg * 100), int(t3u_pos * 100), len(NARRATIVE_ZONES)))
    # 合成 domain 权重展示（验证倾斜方向：T1 偏规划/更新、T3 偏运营/治理）
    rng = random.Random(2606)
    print('\n=== domain 合成权重（区域×时间；T1 应偏 planning/renewal，T3 应偏 operation/governance） ===')
    for sid in ('T1', 'T3'):
        for at in AREA_TYPES:
            w = _compose_weights(DOMAIN_WEIGHTS, AREA_TYPE_DOMAIN_BIAS[at], SNAPSHOT_TIME_DOMAIN_MOD[sid])
            tot = sum(w.values())
            print('  {} {}: {}'.format(sid, at, {k.replace('urban_', ''): round(w[k] / tot, 2) for k in DOMAINS}))
    # 演示采样：T1/T3 各 area_type domain 分布
    print('\n=== 演示采样（各 2000 次） ===')
    for sid in ('T1', 'T3'):
        for at in ('unit', 'core', 'central_outer'):
            from collections import Counter
            c = Counter(pick_domain_element(sid, at, rng)[0] for _ in range(2000))
            print('  {} {}: {}'.format(sid, at, {k.replace('urban_', ''): v for k, v in c.most_common()}))
    return ok


if __name__ == '__main__':
    _check()
