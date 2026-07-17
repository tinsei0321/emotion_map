"""大南门·二马路历史文化街区 L3+L4 模拟配置（ABSA aspect + 政策→项目种子 + T1-T3 归因深化弧）。

策略差异（vs L1/L2 通用城市 sim）：
- L1/L2 = 整体 polarity 弧 + 规则 4×5 单格；本 sim = **ABSA aspect 级**（每点带 aspect +
  per-aspect polarity）+ **政策→项目种子**（policy_seed/project_seed/matrix_multi）+ 归因深化弧。
- 要素占比：文化/事件显著高于 L1/L2（历史街区特性）。
- 资讯素材源：DATA/sim/research/ermawu.md（web-search 实采：1877/2025-01-25 开街/修旧如旧最小干预
  不大规模拆除搬迁/20 小区 44 栋/日均 1.5 万·五一 10 万+）。

逆推校验（CLAUDE.md 数据模拟方法论）：每 aspect 须答「属哪个矩阵块(domain×element)？落哪 policy/project？」。
"""
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ════════════ 空间参数（Sim-1 buffer 科学化）════════════
BOUNDARY_PATH = os.path.join(_HERE, os.pardir, 'DATA', 'boundaries', '大南门二马路滨江片区.geojson')
BUFFER_M = 200              # 外扩缓冲（人发帖 GPS 抖动+邻近性，100-400m 合理；守 core/coord_transform 米制）
BUFFER_DENSITY_RATIO = 0.4  # buffer 区点密度 = 核心 ×0.4（tapered，街心密外围稀）
TARGET_CRS = 'EPSG:4546'    # 米制精确 buffer（宜昌 CM 111E）

# ════════════ 每快照点量（聚焦区密度高于城市 sim）════════════
POINT_COUNT = {'T1': 700, 'T2': 800, 'T3': 900}   # T1→T3 升温（开街扰扰→文旅爆满）

# ════════════ ABSA aspect 分类法（Sim-4，10 aspect；每 aspect 落 element+domain+policy/project）════════════
# texts 三极（pos/neg/neu），源自 emotion_corpus ermawu + DATA/sim/research/ermawu.md 实采口碑。
ASPECTS = {
    '修旧如旧': {
        'element': '文化', 'domain': 'urban_renewal', 'blind_spot': False,
        'policy_seed': '防止大拆大建通知;关于持续推进城市更新行动的意见',
        'project_seed': '历史街区/历史文化街区保护更新',
        'matrix_multi': [('urban_renewal', '文化', '主'), ('urban_operation', '文化', '次')],
        'pos': ['二马路修旧如旧，百年老街焕发新生', '保留原貌真有味道，修新如旧做得好',
                '老建筑修得讲究，最小干预看出功夫', '不变拆真改，原汁原味加分'],
        'neg': [], 'neu': [],
    },
    '烟火气保留': {
        'element': '文化', 'domain': 'urban_renewal', 'blind_spot': False,
        'policy_seed': '防止大拆大建通知(留改拆·留底线)',
        'project_seed': '历史街区保护更新;社区营造',
        'matrix_multi': [('urban_renewal', '文化', '主'), ('urban_renewal', '环境', '次')],
        'pos': ['既有文化味更有烟火气，难得', '老味道还在，没变味', '原住民留着，街区还活着'],
        'neg': ['烟火气没了，商业化太重', '老味道流失，可惜', '原住民迁走，没了生活气'],
        'neu': ['烟火气这东西见仁见智'],
    },
    '网红打卡': {
        'element': '文化', 'domain': 'urban_operation', 'blind_spot': False,
        'policy_seed': '城市更新"十五五"规划(文脉保护传承)',
        'project_seed': '文旅IP打造;文化消费场景',
        'matrix_multi': [('urban_operation', '文化', '主'), ('urban_operation', '事件', '次')],
        'pos': ['二马路成了网红打卡地，年轻人多', '"宜昌"打卡墙出片，复古花墙绝了',
                '下沉广场水景配老街，拍照绝佳', '小众免费出片，本地人私藏'],
        'neg': [], 'neu': ['打卡墙前要排队'],
    },
    '夜经济': {
        # 注：二马路本体偏文化打卡；夜经济偏周边（西坝/陶珠路夜市）——文本体现"周边"
        'element': '事件', 'domain': 'urban_operation', 'blind_spot': True,   # 瞬时人流聚集=官方盲区
        'policy_seed': '城市更新"十五五"规划(生活圈扩围;夜经济)',
        'project_seed': '一刻钟便民生活圈建设;夜经济品牌培育',
        'matrix_multi': [('urban_operation', '事件', '主'), ('urban_governance', '事件', '次')],
        'pos': ['周边夜市烟火升腾，烧烤烤鱼小吃全有', '夜幕降临热闹起来，有活力',
                '夜经济让老街活了'],
        'neg': ['夜市噪音扰民，周边住户受不了', '夜经济周边停车更难'],
        'neu': ['夜经济还在培育'],
    },
    '业态丰富度': {
        'element': '服务', 'domain': 'urban_operation', 'blind_spot': False,
        'policy_seed': '关于持续推进城市更新行动的意见(业态引导)',
        'project_seed': '业态多元化引导;业态调整',
        'matrix_multi': [('urban_operation', '服务', '主'), ('urban_renewal', '服务', '次')],
        'pos': ['文创老店+特色美食，业态丰富', '业态有调性，不低端'],
        'neg': ['业态都同质化了，走哪都一样', '连锁店太多，没特色', '业态单一，逛一次就够'],
        'neu': ['业态还在调整中'],
    },
    '文旅活力': {
        # 含 T1 "盼开街"（中性期盼）→ T3 文旅爆满（积极），polarity 随 T 升温
        'element': '事件', 'domain': 'urban_operation', 'blind_spot': True,   # 节假日瞬时人流=官方盲区
        'policy_seed': '城市更新"十五五"规划(文脉保护;文旅)',
        'project_seed': '文旅品牌;节假日活动组织',
        'matrix_multi': [('urban_operation', '事件', '主'), ('urban_operation', '文化', '次')],
        'pos': ['五一日均1.5万人，百年老街出圈了', '文旅复苏，老街活了', '开街后人气回来了，热闹得像过年'],
        'neg': ['人太多挤得慌，根本走不动', '五一10万人，体验拉胯'],
        'neu': ['盼着开街呢，老街改造进度有点慢', '期待焕新效果'],
    },
    '施工扰民': {
        'element': '环境', 'domain': 'urban_governance', 'blind_spot': False,
        'policy_seed': '城市体检评估管理办法(施工期扰民)',
        'project_seed': '老旧小区改造;施工组织优化',
        'matrix_multi': [('urban_governance', '环境', '主'), ('urban_renewal', '设施', '次')],
        'pos': [], 'neu': ['施工快收尾了，忍忍'],
        'neg': ['改造还在施工，吵得受不了', '施工绕行太麻烦', '施工期灰尘大'],
    },
    '垃圾秩序': {
        'element': '环境', 'domain': 'urban_governance', 'blind_spot': False,
        'policy_seed': '城市更新行动意见(市容治理)',
        'project_seed': '市容环境治理;垃圾分类',
        'matrix_multi': [('urban_governance', '环境', '主'), ('urban_governance', '服务', '次')],
        'pos': ['开街后保洁跟上了'],
        'neg': ['开街垃圾满地没人扫', '人多秩序乱，占道', '节假日保洁跟不上'],
        'neu': [],
    },
    '回迁安置': {
        'element': '服务', 'domain': 'urban_renewal', 'blind_spot': False,
        'policy_seed': '防止大拆大建通知(不大规模搬迁原住民)',
        'project_seed': '回迁安置;原住民保留',
        'matrix_multi': [('urban_renewal', '服务', '主'), ('urban_governance', '服务', '次')],
        'pos': ['回迁满意，原样回来住着踏实', '不大规模搬迁是对的，老街坊还在'],
        'neg': ['回迁安置拖很久', '回迁户型不满意'],
        'neu': ['回迁政策还在等落实'],
    },
    '停车难': {
        'element': '设施', 'domain': 'urban_governance', 'blind_spot': False,
        'policy_seed': '完整社区(配套设施补齐);一刻钟生活圈',
        'project_seed': '停车设施补齐;配套完善',
        'matrix_multi': [('urban_governance', '设施', '主'), ('urban_planning', '设施', '次')],
        'pos': [], 'neu': ['停车勉强能找'],
        'neg': ['停车太难，绕三圈找不到', '节假日停车地狱', '配套停车跟不上热度'],
    },
}

# ════════════ T1→T3 归因深化弧（aspect 分布权重，和=1）════════════
# T1=施工扰民/盼开街(文旅活力中性)/垃圾秩序 主（消极+中性）→
# T2=网红打卡/夜经济+烟火气担忧(混合) →
# T3=修旧如旧好评/文旅活力爆满(积极峰值)+回迁满意（文化/事件主导，混停车/同质化消极保真实）
T_ASPECT_WEIGHTS = {
    'T1': {'施工扰民': 0.26, '文旅活力': 0.20, '垃圾秩序': 0.14, '烟火气保留': 0.12,
           '业态丰富度': 0.10, '回迁安置': 0.08, '停车难': 0.06, '修旧如旧': 0.04,
           '网红打卡': 0.00, '夜经济': 0.00},
    'T2': {'网红打卡': 0.20, '夜经济': 0.16, '烟火气保留': 0.16, '业态丰富度': 0.14,
           '修旧如旧': 0.12, '文旅活力': 0.10, '垃圾秩序': 0.06, '停车难': 0.04,
           '施工扰民': 0.02, '回迁安置': 0.00},
    'T3': {'修旧如旧': 0.22, '文旅活力': 0.20, '网红打卡': 0.16, '烟火气保留': 0.10,
           '回迁安置': 0.10, '业态丰富度': 0.08, '夜经济': 0.06, '停车难': 0.04,
           '垃圾秩序': 0.03, '施工扰民': 0.01},
}

# 每 aspect 在各 T 的极性分布（pos/neg/neu 和=1；驱动 aspect_polarity + 整体 polarity）
# 弧：多数 aspect 随 T 由 neg/neu→pos 升温；施工扰民 T1 全 neg→T3 消失；修旧如旧 T3 全 pos。
T_ASPECT_POLARITY = {
    '修旧如旧':  {'T1': (0.4, 0.0, 0.6), 'T2': (0.85, 0.0, 0.15), 'T3': (0.95, 0.0, 0.05)},
    '烟火气保留': {'T1': (0.2, 0.5, 0.3), 'T2': (0.35, 0.45, 0.20), 'T3': (0.55, 0.30, 0.15)},
    '网红打卡':  {'T1': (0.0, 0.0, 0.0), 'T2': (0.90, 0.0, 0.10), 'T3': (0.92, 0.0, 0.08)},
    '夜经济':   {'T1': (0.0, 0.0, 0.0), 'T2': (0.70, 0.20, 0.10), 'T3': (0.75, 0.18, 0.07)},
    '业态丰富度': {'T1': (0.10, 0.60, 0.30), 'T2': (0.30, 0.50, 0.20), 'T3': (0.40, 0.45, 0.15)},
    '文旅活力':  {'T1': (0.05, 0.20, 0.75), 'T2': (0.60, 0.10, 0.30), 'T3': (0.80, 0.15, 0.05)},
    '施工扰民':  {'T1': (0.0, 0.85, 0.15), 'T2': (0.0, 0.70, 0.30), 'T3': (0.0, 0.60, 0.40)},
    '垃圾秩序':  {'T1': (0.05, 0.80, 0.15), 'T2': (0.10, 0.70, 0.20), 'T3': (0.20, 0.65, 0.15)},
    '回迁安置':  {'T1': (0.05, 0.55, 0.40), 'T2': (0.15, 0.50, 0.35), 'T3': (0.55, 0.25, 0.20)},
    '停车难':   {'T1': (0.0, 0.85, 0.15), 'T2': (0.0, 0.88, 0.12), 'T3': (0.0, 0.92, 0.08)},
}

# 快照元数据（标签/日期，与既有 sim T1=2025-02 春节开街 / T3=2026-05 五一 一致）
SNAPSHOTS = {
    'T1': {'label': '2025-02 春节·二马路一期开街爆满', 'date_range': ('2025-02-01', '2025-02-10')},
    'T2': {'label': '2025-07 暑假·年轻人涌入打卡', 'date_range': ('2025-07-01', '2025-07-31')},
    'T3': {'label': '2026-05 五一·大南门建成文旅爆满', 'date_range': ('2026-05-01', '2026-05-07')},
}

OUTPUT_DIR = os.path.join(_HERE, os.pardir, 'DATA', 'processed')


def _check():
    """配置自检：aspect 权重和=1；每 aspect 三极和=1；policy/project 非空。"""
    for t, w in T_ASPECT_WEIGHTS.items():
        s = sum(w.values())
        assert abs(s - 1.0) < 1e-6, f'{t} aspect 权重和={s} ≠ 1'
        for a in w:
            assert a in ASPECTS, f'{t} 含未知 aspect {a}'
    for a, pol in T_ASPECT_POLARITY.items():
        for t, (p, n, nu) in pol.items():
            # 只校验在该 T 有非零权重的 aspect（权重 0 的 aspect 不出现，极性无意义）
            if T_ASPECT_WEIGHTS[t].get(a, 0) > 0:
                assert abs(p + n + nu - 1.0) < 1e-6, f'{a}/{t} 极性和={p+n+nu} ≠ 1'
    for a, info in ASPECTS.items():
        assert info['policy_seed'] and info['project_seed'], f'{a} 缺 policy/project seed'
        assert info['matrix_multi'], f'{a} 缺 matrix_multi'
    # 每 aspect 至少在某个 T 有权重
    for a in ASPECTS:
        assert any(a in w for w in T_ASPECT_WEIGHTS.values()), f'{a} 在任何 T 都无权重'
    print(f'[OK] ermawu_l3l4_config 自检通过 | {len(ASPECTS)} aspects | T1/T2/T3 权重+极性和均=1')


if __name__ == '__main__':
    _check()
