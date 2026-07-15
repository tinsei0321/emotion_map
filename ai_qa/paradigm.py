"""专业认知层 · 尺度-方法-范式 参考表 + GIS 操作目录（DIAGNOSE 选型依据）。

纯数据（dict/list），供 manifesto.py / prompts.build_diagnose_prompt 渲染进 prompt，教模型：
1) 任何问题先沿「行业视角 × 尺度 × 决策类型 × 出口」拆解，而非语义解析后直接走固定管线；
2) 结论颗粒度必须匹配问题尺度（宏观禁落单点 / 微观禁泛泛）—— 这是城市规划系统性思维的核心；
3) 从 GIS 工具目录自动选型 + 组合（Data+Skill+Agent+Harness 的 "Skill" 层）。

改范式 = 改本文件（数据，非逻辑）。运行时强制靠 prompts.build_diagnose_prompt +
review.REVIEW_CHECKLIST 的 scale_paradigm_fit；方法论镜像沉淀于
.claude/skills/emotion-scale-paradigm/（供开发维护演进）。
"""

# ════════════ 表1 · 尺度-方法-范式矩阵（结论颗粒度硬约束）════════════
# 情绪地图的专业认知皇冠：分析的"尺度感"决定结论的"形态"。尺度错位 = 答非所问。
SCALE_PARADIGM = [
    {
        'scale': 'macro',
        'name': '宏观',
        'geo_objects': '城区 / 片区 / 组团（10²–10³ km²，如中心城区 1623 km²、各行政区）',
        'method': '大尺度聚合（1000m 网格 / 行政区 zonal）+ 排序 + 类型化/结构化归纳',
        'paradigm': '产出宏观聚合图层（如行政区极性面）+ 体系化结论：哪类空间 / 哪些街道 / 哪类用地系统性落后或领先',
        'forbidden': '禁止落到单一坐标 / 单一网格（用微观结论答宏观问）',
        'typical_q': '"中心城区整体情绪如何？哪里好哪里坏？""哪个片区最需优先更新？"',
        'city_checkup_level': '城区（城市）',  # 对齐住建部 2024 城市体检四层级（住房→小区→街区→城区）
        'method_templates': ['zonal_stats(admin_district)→4×5归因+排序', 'area_stats(用地结构)'],
    },
    {
        'scale': 'meso',
        'name': '中观',
        'geo_objects': '街道 / 社区 / 更新单元（1–50 km²）',
        'method': '单元 zonal 聚合（边界 preset）+ 4×5 归因 + 单元间排序',
        'paradigm': '产出单元聚合图层 + 单元级结论：哪个单元最差/最好 + 归因（domain×element）+ 单元针对性建议',
        'forbidden': '不混到单点、也不泛到整城',
        'typical_q': '"这几个街道里哪个最需更新？""某社区的 4×5 归因偏哪一格？"',
        'city_checkup_level': '街区/小区（社区）',
        'method_templates': ['zonal_stats(street/renewal_unit)→4×5归因', 'buffer(15min生活圈)'],
    },
    {
        'scale': 'micro',
        'name': '微观',
        'geo_objects': '街 / 小区 / 公园 / POI / 网格（10⁻²–1 km²）',
        'method': '50–100m 精细网格聚合 + 热点聚集（Gi*）+ 具体落点',
        'paradigm': '产出精细网格/热点图层 + 落点结论：哪个具体网格 / 聚集区 / POI + 精确定位（可飞到地图）',
        'forbidden': '禁止泛泛而谈（用宏观结论答微观问）',
        'typical_q': '"这个公园里哪里情绪最差？""这条街上哪个点位被吐槽最多？"',
        'city_checkup_level': '住房/小区',
        'method_templates': ['hotspot(Gi*冷热点)', 'nearest(设施锚定)', '精细网格 50-100m'],
    },
]


def scale_paradigm_text() -> str:
    """渲染表1为模型可读文本（注入 MANIFESTO/diagnose prompt）。"""
    lines = []
    for s in SCALE_PARADIGM:
        lines.append(
            f"- [{s['name']}/{s['scale']}] 对象：{s['geo_objects']}\n"
            f"    方法：{s['method']}\n"
            f"    出口范式：{s['paradigm']}\n"
            f"    禁止：{s['forbidden']}\n"
            f"    典型问：{s['typical_q']}\n"
            f"    城市体检层级：{s.get('city_checkup_level', '—')}（对齐住建部四层级：住房→小区→街区→城区）\n"
            f"    默认方法模板：{' / '.join(s.get('method_templates', []))}"
        )
    return '\n'.join(lines)


# ════════════ 表2 · 4 领域 × 出口范式启发库（DIAGNOSE 选型参考，可扩）════════════
DOMAIN_OUTLETS = {
    'urban_planning': {
        'name': '城市规划·设计',
        'framework': '国土空间规划（五级三类四体系/三区三线/多规合一）+ 城市设计/景观设计/修建性详规（设计全谱）',
        'outlets': [
            '选址研判（设施缺口 × 情绪，中观）',
            '15 分钟生活圈品质评价（中观单元）',
            '用地类型情绪对比（宏观结构）',
        ],
    },
    'urban_renewal': {
        'name': '城市更新',
        'framework': '城市更新行动（留改拆/防止大拆大建：拆≤20%）+ 完整社区/15min 生活圈 + 城市体检四层级',
        'outlets': [
            '更新时序排序 / 优先级（中观，按更新单元）',
            '微更新点位识别（微观，老旧小区 100m 网格）',
            '片区更新系统性诊断（宏观结构）',
        ],
    },
    'urban_operation': {
        'name': '城市运营',
        'framework': '城市生命线安全工程（燃气/桥梁/供水…）+ 运管服平台（国-省-市三级）+ 一网统管',
        'outlets': [
            '场馆 / 商圈活动复盘（事件前后情绪对比）',
            '舆情监测预警（负面聚集热点）',
            '商圈业态口碑对比（中观）',
        ],
    },
    'urban_governance': {
        'name': '城市治理',
        'framework': '人民城市 + 网格化管理（主动/精细）+ 12345 接诉即办（三率：响应/解决/满意）',
        'outlets': [
            '12345 / 投诉热点预警（负面聚集 + 关键词）',
            '交通 / 停车拥堵点排查（微观落点）',
            '跨单元治理压力对比（中观排序）',
        ],
    },
}


def domain_outlets_text() -> str:
    lines = []
    for d, info in DOMAIN_OUTLETS.items():
        lines.append(f"- {info['name']}（{d}）｜官方框架：{info.get('framework', '—')}\n    出口范式：" + ' / '.join(info['outlets']))
    return '\n'.join(lines)


# ════════════ 表2b · B 赛道操作范式树（gis_operation · Load→Transform→Analyze pipeline）════════════
# B 赛道（纯 GIS 操作，出口=图层，不受 manifesto§11 尺度范式约束）的操作原型分类。
# 汲取 GeoLLM-Engine 的 Load-Filter-Plot 范式：B 操作本质 = 加载层 → 空间变换 → 落图分析。
# **list 顺序 = select_template 关键词匹配优先级**（先具体/不易混，后泛）——歧义裁断的单一真相源。
# template 字段=理想技能 id；B_TRACK 9 原型均已登记 single 技能（B1+B1.5）。
B_TRACK_PARADIGM = [
    {'archetype': '缓冲影响', 'stage': 'Transform', 'voice': '我画设施周边半径范围并聚合圈内情绪',
     'triggers': ['周边', '附近', '半径', '缓冲', '米内', '公里内'],
     'template': 'buffer'},
    {'archetype': '邻近锚定', 'stage': 'Transform', 'voice': '我找离某设施/POI 最近的点',
     'triggers': ['最近', '邻近', '最近邻'],
     'template': 'nearest'},
    {'archetype': '密度分布', 'stage': 'Analyze', 'voice': '我用核密度看聚集强度连续分布',
     'triggers': ['核密度', '密度分析', '聚集强度', '热力分布', '密度', '集中'],
     'template': 'density'},
    {'archetype': '聚集识别', 'stage': 'Analyze', 'voice': '我用 Gi* 识别显著冷热点聚集',
     'triggers': ['聚集', '热点', '冷热', '显著聚集'],
     'template': 'hotspot'},
    {'archetype': '叠置交叉', 'stage': 'Transform', 'voice': '我叠两个图层找复合关系区',
     'triggers': ['交集', '叠置', '叠加', '用地里', '用地中', '两图', '里的'],
     'template': 'overlay'},
    {'archetype': '合并上卷', 'stage': 'Transform', 'voice': '我合并多面成片区或同类用地 dissolve',
     'triggers': ['合并', '合成', 'dissolve', '并成'],
     'template': 'merge'},
    {'archetype': '范围裁取', 'stage': 'Transform', 'voice': '我按范围（某区/公园/单元）裁出目标',
     'triggers': ['范围内', '区的', '区内的', '片区'],
     'template': 'clip'},
    {'archetype': '要素抽取', 'stage': 'Load', 'voice': '我从面边界按属性抽单要素为独立面',
     'triggers': ['抽某', '裁出某', '单独裁出', '提取某'],
     'template': 'extract_feature'},
    {'archetype': '属性筛选', 'stage': 'Load', 'voice': '我按字段属性切片子集',
     'triggers': ['按字段', '用地类', '属性筛选', '筛选某类'],
     'template': 'filter_attr'},
]


def b_track_paradigm_text() -> str:
    """渲染 B 赛道范式树（注入 diagnose prompt，教 Flash B 操作选型）。list 顺序即匹配优先级。"""
    _single = {s['skill'] for s in TEMPLATE_REGISTRY if s.get('category') == 'single'}
    lines = []
    for a in B_TRACK_PARADIGM:
        pending = '（技能待 B1 建，现落 multi 多步）' if a['template'] not in _single else ''
        lines.append(
            f"- [{a['stage']}] {a['archetype']}（template={a['template']}）{a['voice']}{pending}\n"
            f"    触发词：{' / '.join(a['triggers'])}"
        )
    return '\n'.join(lines)


# ════════════ 表3 · GIS 操作目录（AI 自动选用 = Skill+Agent 层）════════════
# 每项：何时用 / 入参 / 产出 / 对结论范式的贡献。DIAGNOSE 的 method 字段据此组合。
# 后端实现见 api/geo_routes.py（复用 core/spatial_analysis + range_selector，GeoPandas）。
GEO_TOOL_CATALOG = [
    {
        'name': 'filter_attr',
        'when': '按属性筛选：用地类型 / 极性 / domain / element / 时点',
        'params': 'layer, field, op(eq|in|gt|lt), value',
        'yields': '子集（点或聚合）',
        'contributes': '聚焦切片（"商业用地"/"T1 负面"/"治理域"），支撑类型化结论',
    },
    {
        'name': 'extract_feature',
        'when': '从面边界按属性抽单要素为独立面图层（把某区/某公园/某单元单独裁出来显示）',
        'params': 'layer(preset_id|geojson), where(field/op/value，field 见 catalog name_field)',
        'yields': '面子集 GeoJSON（自动落地图）',
        'contributes': '纯 GIS 操作出口：用户要"裁出西陵区"等几何产物时用此，不走情绪归因',
    },
    {
        'name': 'clip',
        'when': '按几何裁剪：某行政区/某公园/某街道范围内的点',
        'params': 'layer, range(preset_id | geojson), pre_filter?',
        'yields': '范围内的点子集（自动落地图）',
        'contributes': '限定空间范围取点（"西陵区内的情绪点"），支撑中/微观落点',
    },
    {
        'name': 'merge',
        'when': '合并 / dissolve：把多个面域合成一个片区，或同类用地合并',
        'params': 'layer, by(字段) | all',
        'yields': '合并后的面域',
        'contributes': '上卷到更大尺度（几街道→一片区），支撑宏观结构结论',
    },
    {
        'name': 'area_stats',
        'when': '面积统计：各类用地面积占比、单元面积、单位面积情绪密度',
        'params': 'layer, group_by(字段)',
        'yields': '面积 + 占比 + 密度',
        'contributes': '量化"占比""密度"，让结论从计数升级为强度/结构判断',
    },
    {
        'name': 'zonal_stats',
        'when': '面域聚合统计：按更新单元/街道/社区把点聚合成单元指标（宏观/中观核心）',
        'params': 'layer, boundary(preset_id | geojson), metrics, top_n',
        'yields': '每单元 point_count/极性/4×5 归因 + 排序',
        'contributes': '产出"哪个单元最差 + 归因"，宏观/中观结论的主干',
    },
    {
        'name': 'rank',
        'when': '排序：按极性/domain/element 找 Top N 最差/最好',
        'params': 'layer, by(polarity|domain|element), top_n, range',
        'yields': '排序后的 Top N 单元',
        'contributes': '给出"最需优先…"的明确排序，结论有指向性',
    },
    {
        'name': 'buffer',
        'when': '缓冲区：某设施/POI 周边半径内的情绪（地铁站 500m、奥体 1km）',
        'params': 'layer, center(POI | geojson), radius_m',
        'yields': '缓冲面域 + 范围内聚合',
        'contributes': '回答"某设施影响范围"，支撑设施评估/选址',
    },
    {
        'name': 'overlay',
        'when': '叠置分析：交集/并集/差集（商业用地 ∩ 更新单元、规划范围 − 已更新）',
        'params': 'layer_a, layer_b, how(intersection|union|difference|symmetric)',
        'yields': '叠置结果面域',
        'contributes': '跨图层交叉（用地 × 更新），识别复合问题区',
    },
    {
        'name': 'nearest',
        'when': '最近邻：离某类 POI/设施最近的负面点，或 POI 锚定',
        'params': 'layer, target(POI 类型 | geojson), k',
        'yields': '邻近配对 + 距离',
        'contributes': '锚定"问题点离什么设施近"，支撑归因落点',
    },
    {
        'name': 'hotspot',
        'when': 'Gi* 热点：负面/正面情绪在空间上显著聚集的冷热点',
        'params': 'layer, value_col(score), invert(负面为热)',
        'yields': '每点 Gi* Z-score + hot/cold 分类',
        'contributes': '识别"聚集在哪"，支撑预警/排查类出口',
    },
    {
        'name': 'density',
        'when': '核密度(KDE)栅格：用户说"核密度/密度分析/聚集强度/热力分布"时首选——产连续密度面',
        'params': 'layer, bandwidth_m(默认800), cell_size_m(默认300), value_col?(加权), range?, as?, keep?',
        'yields': '规则方格面网格，每格 density + _level(0..1) + _band(0..4 离散分段)，自动落地图',
        'contributes': '"核密度分析"的标准出口=新图层（离散分段色带，对称拉伸）；区别于 hotspot(逐点Gi*)与 ensure_zone(情绪网格聚合)',
    },
]


def geo_tool_catalog_text() -> str:
    lines = []
    for t in GEO_TOOL_CATALOG:
        lines.append(
            f"- {t['name']}：{t['when']}\n"
            f"    入参：{t['params']} → 产出：{t['yields']}\n"
            f"    贡献：{t['contributes']}"
        )
    return '\n'.join(lines)


# ════════════ 表3c · 技能模板目录（P1 编排层 · 站在巨人肩膀上）════════════
# 每个「技能」= 1-2 个成熟 geo 工具 + 规划常识默认 + 拟人化口吻。diagnose 选 template → harness runTemplatePath 填 params 确定性执行（p^N→p²）。
# 少而精（7 命名技能 + 2 兜底），结构可生长：追加一条 dict 即新增技能（P2+ 加 nearest/hotspot/area_stats/merge/extract_feature）。
# 前端 stages.js SKILL_DEFS 镜像 required_slots/optional_defaults/tool/category（仿 field_dictionary 两份字典，改须同步）。
TEMPLATE_REGISTRY = [
    {'skill': 'concept', 'name': '概念问答', 'category': 'concept',
     'voice': '我直接讲解概念，不动地图', 'triggers': '什么是/含义/区别/定义',
     'tool': None, 'required_slots': [], 'optional_defaults': {},
     'planning_common': '通用问答，不走空间分析（harness 走 general 短路）'},
    {'skill': 'density', 'name': '分布热度分析', 'category': 'single',
     'voice': '我用热力图(2D彩虹)/网格聚合(3D)看清情绪点分布热度', 'triggers': '哪里最集中/热点/聚集/分布/密度',
     'tool': 'density', 'required_slots': [],
     'optional_defaults': {'mode': '2d', 'radius': 300, 'weightField': 'emotion_intensity', 'cell_size': 600, 'polarity': 'overall'},
     'planning_common': '委托主 Toolbox（固定 HEATMAP_RAMPS 色段，可切 2D/3D）：2D=彩虹热力图(radius 步行尺度)；3D=网格聚合(cell 400~1000m)。数据走 Layers 可见层（未显示层禁用）'},
    {'skill': 'rank', 'name': '排序评价', 'category': 'single',
     'voice': '我按极性给区域排序找最差/最好', 'triggers': '哪个最需更新/最差/最好/排名',
     'tool': 'rank', 'required_slots': [],
     'optional_defaults': {'by': 'polarity', 'top_n': 5},
     'planning_common': 'Top 5 聚焦最突出要素；by 默认极性'},
    {'skill': 'buffer', 'name': '缓冲影响圈', 'category': 'single',
     'voice': '我画设施影响范围并聚合圈内情绪', 'triggers': '周边/附近/范围内/地铁站X米',
     'tool': 'buffer', 'required_slots': ['center'],
     'optional_defaults': {'radius_m': 500, 'agg_cols': ['score']},
     'planning_common': '半径：5min步行≈300m/10min≈500m/15min≈1000m；地铁站500m/小学500m/社区医院800m/综合医院1500m'},
    {'skill': 'clip', 'name': '范围裁取', 'category': 'single',
     'voice': '我按范围（某区/公园/单元边界）裁出范围内的目标', 'triggers': '某区的/某范围内的/XX区内的/范围内的（"某区内的YY"优先 clip 取范围内目标，而非 overlay）',
     'tool': 'clip', 'required_slots': ['range'],
     'optional_defaults': {},
     'planning_common': 'range 用 preset_id（行政区/单元）或 geojson；点层走可见层选源（不硬默认）'},
    {'skill': 'overlay', 'name': '叠置交叉', 'category': 'single',
     'voice': '我叠两个图层找复合问题区', 'triggers': '居住用地里情绪差的/两图交集',
     'tool': 'overlay', 'required_slots': ['layer_a', 'layer_b'],
     'optional_defaults': {'how': 'intersection'},
     'planning_common': 'how：intersection 交/union 并/difference 差'},
    {'skill': 'zonal', 'name': '单元归因', 'category': 'single',
     'voice': '我按行政/规划单元聚合情绪并给 4×5 归因', 'triggers': '这几个街道/社区的归因/单元评价',
     'tool': 'zonal_stats', 'required_slots': ['boundary'],
     'optional_defaults': {'agg_cols': ['score']},
     'planning_common': 'boundary=preset_id（街道/社区/更新单元）；点层走可见层选源（不硬默认）；C 赛道情绪主干'},
    {'skill': 'extract_feature', 'name': '要素抽取', 'category': 'single',
     'voice': '我从面边界按属性抽单要素为独立面（裁出某区/某单元/某类用地）', 'triggers': '抽某/裁出某/单独裁出/提取某',
     'tool': 'extract_feature', 'required_slots': ['layer'],
     'optional_defaults': {},
     'planning_common': 'layer=preset_id（行政区/单元/用地层）；where=field/op/value 抽特定要素；产面子图层自动落图'},
    {'skill': 'area_stats', 'name': '面积占比统计', 'category': 'single',
     'voice': '我统计各类用地/各单元面积占比', 'triggers': '面积占比/各类用地占比/单元面积/用地结构',
     'tool': 'area_stats', 'required_slots': ['boundary'],
     'optional_defaults': {},
     'planning_common': 'boundary=preset_id；group_by=字段（如 name/用地类）；出口=占比表（结论支撑，非主图层）'},
    {'skill': 'merge', 'name': '合并上卷', 'category': 'single',
     'voice': '我合并/dissolve 多面成片区或同类用地', 'triggers': '合并/合成/并成/dissolve/合成片区',
     'tool': 'merge', 'required_slots': ['boundary'],
     'optional_defaults': {},
     'planning_common': 'boundary=preset_id；by=字段|空=全部合并；产合并面图层自动落图（上卷到更大尺度）'},
    {'skill': 'nearest', 'name': '最近邻锚定', 'category': 'single',
     'voice': '我找离某设施/POI 最近的点（锚定问题点离什么设施近）', 'triggers': '最近/邻近/最近邻/离X最近',
     'tool': 'nearest', 'required_slots': ['target'],
     'optional_defaults': {'k': 1},
     'planning_common': 'target=preset_id|geojson（设施/POI）；点层走可见层选源（不硬默认）；k=近邻数'},
    {'skill': 'hotspot', 'name': '聚集识别(Gi*)', 'category': 'single',
     'voice': '我用 Gi* 识别负面/正面情绪显著聚集的冷热点', 'triggers': '聚集/热点/冷热/显著聚集/聚集区',
     'tool': 'hotspot', 'required_slots': [],
     'optional_defaults': {'value_col': 'score'},
     'planning_common': '点层走可见层选源（不硬默认）；value_col=score（invert 由工具默认：负面为热）；产 hot/cold/ns 点图层'},
    {'skill': 'filter_attr', 'name': '属性筛选', 'category': 'single',
     'voice': '我按字段属性筛子集（用地/极性/domain/element/时点）', 'triggers': '按字段/用地类/属性筛选/筛选某类/只看',
     'tool': 'filter_attr', 'required_slots': ['pre_filter'],
     'optional_defaults': {},
     'planning_common': 'pre_filter=field/op/value（如 domain/eq/urban_renewal、polarity/eq/negative）；点层走可见层选源；产点子集图层'},
    {'skill': 'multi', 'name': '多步组合', 'category': 'multi',
     'voice': '这个问题要组合几步工具，我按固定链做', 'triggers': '多目标/复合问/并排序/并…再…/且…（一句话含多个动作，如"裁出来并排序"）',
     'tool': None, 'chain': ['clip', 'zonal_stats'], 'required_slots': [], 'optional_defaults': {},
     'planning_common': '固定工具链，首轮直接执行不重选（进 while-loop 受 cap）'},
    {'skill': 'unknown', 'name': '自由探索', 'category': 'unknown',
     'voice': '这个问题我没现成技能，小心探索', 'triggers': '兜底',
     'tool': None, 'required_slots': [], 'optional_defaults': {},
     'planning_common': 'MAX_ROUNDS cap 4，受约束 ReAct（进 while-loop）'},
]


def template_registry_text() -> str:
    """渲染技能目录为模型可读文本（拟人化口吻，注入 diagnose prompt 的 template 字段选型附录）。
    纯函数 f-string、不 .format()，故 voice/planning_common 内花括号安全。"""
    lines = []
    for s in TEMPLATE_REGISTRY:
        _tool = s['tool'] or ('无（' + s['category'] + '类）')
        _slots = s['required_slots'] or '无'
        _def = s['optional_defaults'] or '无'
        lines.append(
            f"- 技能 {s['skill']}（{s['name']}，category={s['category']}）：{s['voice']}\n"
            f"    触发：{s['triggers']}\n"
            f"    工具：{_tool}；必填槽：{_slots}；默认：{_def}\n"
            f"    规划常识：{s['planning_common']}"
        )
    return '\n'.join(lines)


# ════════════ 表3b · 代码执行目录（run_python，geo 工具兜底）════════════
# geo 工具覆盖不到的灵活分析/出图走 run_python（沙箱执行，三道底线加固）。
# 后端实现见 api/run_routes.py（POST /run → sandbox.run_sandbox）。
CODE_EXEC_CATALOG = [
    {
        'name': 'run_python',
        'when': 'geo 工具覆盖不到的灵活分析/出图（自定义统计、特殊可视化、pandas 复杂变换）。常规柱/折/饼图走 zonal_stats/rank + 结论里 {chart:bar|...}，勿用此',
        'params': 'code(Python 源码), inputs=[{layer,as}]?(取已加载图层注入；as 变量名须与代码内一致), timeout?。字段名以 buildContext 的 field=dtype:role:sample 为准，勿臆造（先 query_layers 看字段再写代码）',
        'yields': 'stdout + 图片（matplotlib savefig 自动捕获，结论里用 {fig:fig1} 引用）。失败时观察指明"[sandbox] 数据没注入"还是代码错',
        'contributes': '兜底能力——geo 工具够用时优先 geo；需自由代码/自定义图时用此。可 import：pandas/numpy/geopandas/shapely/scipy/matplotlib/esda/libpysal/h3 + 标准库（os/sys 等被禁）',
    },
]


def code_exec_catalog_text() -> str:
    lines = []
    for t in CODE_EXEC_CATALOG:
        lines.append(
            f"- {t['name']}：{t['when']}\n"
            f"    入参：{t['params']} → 产出：{t['yields']}\n"
            f"    贡献：{t['contributes']}"
        )
    return '\n'.join(lines)


# ════════════ DIAGNOSE 问题理解卡（8 字段，DIAGNOSE 阶段强制输出）════════════
DIAGNOSE_CARD_FIELDS = {
    'intent': '意图（最高优先级）：general(通用问答) | gis_operation(纯GIS/数据操作) | emotion_analysis(情绪分析)',
    'domain_lens': '行业视角：urban_planning/urban_renewal/urban_operation/urban_governance/general（可多选；general 对应 intent=general/gis_operation）',
    'scale': '空间尺度：macro | meso | micro（决定结论颗粒度，查表1；仅 emotion_analysis 受约束）',
    'decision_type': '决策类型：评价 | 选址 | 排查 | 对比 | 监测 | 定义 | 操作 | 通用问答',
    'outlet': '出口形态（默认=生成图层，地图交互优先）：生成图层 | 地图定位 | 指标排序 | 报告结论（仅复杂归因）| 建议清单 | 预警 | 执行操作',
    'data_plan': '数据盘点：{needed[], available[], gap[], strategy: ready|fallback_annotated|request_upload}',
    'template': '技能选型（必填·P1 编排层）：从技能目录选 id——general 概念问填 concept；gis_operation 填 density/rank/buffer/clip/overlay 之一；emotion_analysis 填 zonal/rank；真复合/无现成技能填 multi/unknown',
    'params': '技能入参：按所选技能 required_slots 填必填槽（如 buffer 的 center、clip 的 range、overlay 的 layer_a/layer_b），可空槽由系统补 optional_defaults；concept/multi/unknown 留空 {}',
}

# strategy 语义（数据自检 loop）：
DATA_STRATEGY = {
    'ready': '数据齐全，直接作答',
    'fallback_annotated': '软缺口：有合理替代（如社区代街道），降级作答 + 显著标注口径与局限',
    'request_upload': '硬缺口：关键数据无替代（如更新紧迫度），输出"请求上传"卡，该问不硬答',
}


# ════════════ 选型真相源：select_template（track + card → template）════════════
# 把「赛道 → 范式 → template」选型规则收口为一个可测纯函数（单一真相源）。
# 渲染进 diagnose prompt（select_template_text）→ Flash 按结构化决策树选型（A1 协同：从「凭语感」升级到「按范式」）。
# 汲取 GeoLLM-Engine intent={q,工具序列,...} 思路：track+scale 定义「期望 template（隐含工具序列）」作基准。
# Python-only；JS normalizeCard 强制执行有意延后（涉承重，另开 plan）。
_SINGLE_SKILL_IDS = {s['skill'] for s in TEMPLATE_REGISTRY if s.get('category') == 'single'}
# = {density, rank, buffer, clip, overlay, zonal}（B1 加技能后自动扩）


def select_template(track, card=None, question=''):
    """单一真相源：track + diagnose card（+可选原始问句）→ canonical template id。

    track ∈ {'A','B','C'}（A 通用/B 纯GIS操作/C 情绪分析）；card = diagnose 卡字段
    （scale/domain_lens/decision_type/outlet/...）；question = 可选原始问句（B 赛道关键词匹配用，card 不含问句）。
    返 template id（与 TEMPLATE_REGISTRY 对齐：concept/density/rank/buffer/clip/overlay/zonal/multi/unknown）。

    判定：
    - A → concept
    - B → 按 B_TRACK_PARADIGM（顺序即优先级）关键词匹配 question → 命中原型 template；
          未登记技能→ multi；识别不到→multi（B_TRACK 9 原型均已登记 single）
    - C → scale=micro→rank（落点排序）；macro/meso→zonal（单元归因）
    """
    card = card or {}
    if track == 'A':
        return 'concept'
    if track == 'B':
        q = str(question or card.get('question') or '')
        for arch in B_TRACK_PARADIGM:   # list 顺序 = 匹配优先级
            if any(t in q for t in arch['triggers']):
                tpl = arch['template']
                return tpl if tpl in _SINGLE_SKILL_IDS else 'multi'   # 未建技能→降级 multi
        return 'multi'   # B 操作识别不到具体原型→多步兜底
    if track == 'C':
        scale = str(card.get('scale', '')).lower()
        if scale == 'micro':
            return 'rank'
        return 'zonal'   # macro/meso → 单元归因
    return 'unknown'


def select_template_text() -> str:
    """渲染选型决策树（单一真相源）为可读文本，注入 diagnose prompt——Flash 据此结构化选型。"""
    return (
        '【选型决策树·单一真相源】track + scale + 问句关键词 → template：\n'
        '- track=A（通用问答/概念/定义）→ template=concept\n'
        '- track=B（纯 GIS 操作）：按问句关键词匹配【B 赛道操作范式树】（顺序即优先级，先具体后泛）'
        '→ 命中原型的 template（B_TRACK 9 原型均已登记 single 技能：buffer/nearest/density/hotspot/overlay/merge/clip/extract_feature/filter_attr）；'
        '识别不到任何原型、或真复合≥2 动作→multi。\n'
        '- track=C（情绪分析）：scale=macro/meso→zonal（行政/规划单元归因）；'
        'scale=micro→rank（落点排序）；真复合归因（多目标）→multi。\n'
        '**单一空间关系就是 single，禁选 multi/unknown**（仅真复合≥2 动作才 multi）。'
        '结论颗粒度须匹配城市体检层级（macro=城区/meso=街区·小区/micro=住房·POI）。'
    )
