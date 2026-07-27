# ════════════ Toolbox 工具参数契约 · 单一权威源（CB-04 L2）════════════
#
# 消灭"density 参数契约四处分裂"（prompts.py / paradigm GEO_TOOL_CATALOG / TEMPLATE_REGISTRY / 前端 SKILL_DEFS+TOOLS 各一份不一致·
# 致"消极热力图出综合彩虹图"·CB-04 根因①）。每工具的参数契约只写一次于此：
#   - paradigm.py GEO_TOOL_CATALOG / TEMPLATE_REGISTRY → derive_geo_catalog() / derive_template_registry() 派生
#   - 前端 stages.js SKILL_DEFS.optional_defaults + _PARAM_ALIAS → 镜像（开发时同步·validate_skill_params 校验）
#   - prompts.py 工具段 → 手写（eval 安全）但须与 contracts 一致（validate 守护）
#
# 最高纪律（CLAUDE.md 第 5 条 / AGENTS.md 铁律 11）：
#   - EMC 分析图复用 Toolbox 参数面板（dialog）已有色板/参数，不造新内容
#   - ForAI 入口 = dialog 镜像（复用 computeStyle/terrainRampOf，不自带默认）
#   - panel_source = Toolbox dialog 控件来源；'PANEL_MISSING' = 参数面板缺→提醒开发者补齐+标准化+本地化，EMC 不自行造
#
# params 结构化 schema：
#   {name, type, enum?, default, required, alias[], hint?, panel_source?}
#   - default is None = 无默认（可选·缺省由工具自处理）
#   - panel_source = Toolbox dialog 控件来源 / 'EMC-only'（无 Toolbox dialog·AI 执行·设计如此）/ 'PANEL_MISSING'（真缺口·提醒补 dialog）；L3 5.238 全Resolved（旧 pending 标记已清）

# ── 参数契约清单（skill 顺序对齐 TEMPLATE_REGISTRY）──
TOOL_CONTRACTS = [
    {
        'skill': 'concept', 'tool': None, 'category': 'concept', 'name_cn': '概念问答',
        'voice': '我直接讲解概念，不动地图', 'triggers_str': '什么是/含义/区别/定义',
        'when': None,  # concept 无 GIS catalog 项
        'required_slots': [], 'planning_common': '通用问答，不走空间分析（harness 走 general 短路）',
        'params': [],
    },
    {
        'skill': 'density', 'tool': 'density', 'category': 'single', 'name_cn': '分布热度分析',
        'voice': '我用热力图(2D彩虹)/网格聚合(3D)看清情绪点分布热度', 'triggers_str': '哪里最集中/热点/聚集/分布/密度',
        'when': '核密度(KDE)/热力图：用户说"核密度/密度分析/聚集强度/热力分布/密集/集聚/哪里最集中/热力图/情绪热度分布"时首选——产连续密度面（=热力聚合，非逐点 Gi*）',
        'params_str': 'layer, polarity?(overall|positive|negative|neutral·默认overall·=极性筛点+着色), analysis?(terrain|positive|negative|neutral·色板主驱动·缺省由polarity推), mode?(2d|3d|terrain·默认2d), radius?(2D热力带宽·默认300), cell_size?(3D网格边长·默认600)（尺度表同buffer：社区250/区500/主城1000）, weightField?(加权·默认emotion_intensity), level?(L1|L2|L3|L4), range?, as?, keep?',
        'yields': '连续密度面——2D 彩虹热力图 / 3D 网格聚合 / 3D KDE 等值面地形（委托 Toolbox 标准色段·对称拉伸），自动落地图',
        'contributes': '"密度/密集/热力"类的标准出口=新热力图层（彩虹色带·最直观的分布可视化）；区别于 hotspot(逐点 Gi*·冷热点分类)与 zonal_stats(情绪网格聚合·归因排序)',
        'scale': '全尺度（连续密度面）', 'preconditions': '点层（+可选加权 value_col）',
        'failure_modes': '与 hotspot 混——density=连续密度面/热力图（聚合强度）；要逐点显著冷热分类用 hotspot',
        'examples': '正:核密度分析 / 正:哪里最集中 / 误:显著冷热点分类(→hotspot)',
        'required_slots': [],
        'planning_common': '委托主 Toolbox（固定 HEATMAP_RAMPS 色段·ForAI=dialog 镜像）：2D 综合彩虹热力图(radius 步行尺度)/3D 网格聚合(cell 400~1000m)/3D KDE 地形。**极性细分（CB-04）**：综合/总体→polarity=overall（彩虹·analysis=terrain）；积极/消极/中性→polarity=positive/negative/neutral（对应 segment 色板·只筛该极性点）。数据走 Layers 可见层（未显示层禁用）',
        'params': [
            {'name': 'layer', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '默认 L2 可见层', 'panel_source': 'Heatmap dialog #hm-level'},
            {'name': 'polarity', 'type': 'enum', 'enum': ['overall', 'positive', 'negative', 'neutral'], 'default': 'overall', 'required': False, 'alias': [], 'hint': '极性筛点+着色（综合=彩虹·极性=对应色板）', 'panel_source': 'Heatmap dialog #hm-subset / ANALYSIS_TIERS'},
            {'name': 'analysis', 'type': 'enum', 'enum': ['terrain', 'positive', 'negative', 'neutral'], 'default': None, 'required': False, 'alias': [], 'hint': '色板主驱动·缺省由 polarity 推', 'panel_source': 'Heatmap dialog ANALYSIS_PRESETS'},
            {'name': 'mode', 'type': 'enum', 'enum': ['2d', '3d', 'terrain'], 'default': '2d', 'required': False, 'alias': [], 'hint': '2D 彩虹/3D 网格/3D 地形', 'panel_source': 'Heatmap dialog 生成按钮 dim'},
            {'name': 'radius', 'type': 'int', 'default': 300, 'required': False, 'alias': ['bandwidth_m'], 'hint': '2D 热力带宽（尺度表：社区250/区500/主城1000）', 'panel_source': 'Heatmap dialog #hm-radius'},
            {'name': 'cell_size', 'type': 'int', 'default': 600, 'required': False, 'alias': ['cell_size_m'], 'hint': '3D 网格边长', 'panel_source': 'Grid dialog cellSize'},
            {'name': 'weightField', 'type': 'str', 'default': 'emotion_intensity', 'required': False, 'alias': ['value_col'], 'hint': '加权字段', 'panel_source': 'Heatmap dialog #hm-weight-field'},
            {'name': 'level', 'type': 'enum', 'enum': ['L1', 'L2', 'L3', 'L4'], 'default': None, 'required': False, 'alias': [], 'hint': '数据层级', 'panel_source': 'Heatmap dialog #hm-level'},
            {'name': 'range', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '范围 preset/geojson', 'panel_source': '通用 range'},
            {'name': 'as', 'type': 'str', 'default': None, 'required': False, 'alias': ['output', 'output_layer', 'layer_name', 'named', 'name'], 'hint': '图层名·现实内容', 'panel_source': '通用 as'},
            {'name': 'keep', 'type': 'bool', 'default': None, 'required': False, 'alias': [], 'hint': 'true=保留免清理', 'panel_source': '通用 keep'},
        ],
    },
    {
        'skill': 'rank', 'tool': 'rank', 'category': 'single', 'name_cn': '排序评价',
        'voice': '我按极性给区域排序找最差/最好', 'triggers_str': '哪个最需更新/最差/最好/排名',
        'when': '排序：按极性/domain/element 找 Top N 最差/最好',
        'params_str': 'layer, by(polarity|domain|element), top_n, range, boundary?',
        'yields': '排序后的 Top N 单元 + Top N 高亮层（极性 choropleth·自动落地图）',
        'contributes': '给出"最需优先…"的明确排序，结论有指向性且以图说话',
        'scale': '中观/微观（排序落点）', 'preconditions': 'boundary 或点层 + by 维度',
        'failure_modes': '误用于宏观整体归纳（整城/中心城区整体如何，**无排序意图**）→ zonal；含"排序/最差/最好/Top/哪个点位最差"=有排序意图→rank，勿因含"最差"就退 multi、也勿把"各区排序"当整体归纳',
        'examples': '正:最差的5个区 / 正:这个公园哪个点位最差 / 误:中心城区整体如何(→zonal)',
        'required_slots': [],
        'planning_common': 'Top 5 聚焦最突出要素；by=worst(最差)/best(最好)/domain:X/element:X（CB-04 修：旧默认 polarity 非有效值·[geo_routes:376] 抛错）',
        'params': [
            {'name': 'by', 'type': 'enum', 'enum': ['worst', 'best', 'domain:X', 'element:X'], 'default': 'worst', 'required': False, 'alias': ['sort', 'sort_by', 'criteria'], 'hint': '排序维度', 'panel_source': 'Rank dialog #rank-by'},
            {'name': 'top_n', 'type': 'int', 'default': 5, 'required': False, 'alias': ['top', 'limit', 'n'], 'hint': 'Top N', 'panel_source': 'Rank dialog topN'},
            {'name': 'layer', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '默认 L2', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'boundary', 'type': 'source', 'default': None, 'required': False, 'alias': ['zone', 'region'], 'hint': 'preset_id', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'range', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '可选先裁剪', 'panel_source': '通用 range'},
            {'name': 'pre_filter', 'type': 'str', 'default': None, 'required': False, 'alias': [], 'hint': 'field/op/value', 'panel_source': '通用 pre_filter'},
        ],
    },
    {
        'skill': 'buffer', 'tool': 'buffer', 'category': 'single', 'name_cn': '缓冲影响圈',
        'voice': '我画设施影响范围并聚合圈内情绪', 'triggers_str': '周边/附近/范围内/地铁站X米',
        'when': '缓冲区：某设施/POI 周边半径内的情绪（地铁站 500m、奥体 1km）',
        'params_str': 'layer, center(POI | geojson), radius_m(默认 500·尺度表：社区/街道 250·行政区/片区 500·主城/全域 1000)',
        'yields': '缓冲面域 + 范围内聚合', 'contributes': '回答"某设施影响范围"，支撑设施评估/选址',
        'scale': '中观（设施影响圈）', 'preconditions': 'center POI/geojson',
        'failure_modes': '误用于面要素裁剪——要某区范围内用 clip/overlay；半径按尺度表（社区250/区500/主城1000）',
        'examples': None,
        'required_slots': ['center'],
        'planning_common': '半径：5min步行≈300m/10min≈500m/15min≈1000m；地铁站500m/小学500m/社区医院800m/综合医院1500m',
        'params': [
            {'name': 'center', 'type': 'source', 'default': None, 'required': True, 'alias': ['point', 'center_point'], 'hint': 'POI preset|geojson', 'panel_source': 'Buffer dialog center'},
            {'name': 'radius_m', 'type': 'int', 'default': 500, 'required': False, 'alias': ['radius', 'radius_meters', 'buffer_radius', 'distance'], 'hint': '半径米（尺度表）', 'panel_source': 'Buffer dialog radius'},
            {'name': 'agg_cols', 'type': 'list', 'default': ['score'], 'required': False, 'alias': [], 'hint': '聚合列', 'panel_source': 'Buffer dialog #buf-emotion-params'},
            {'name': 'layer', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '默认 L2', 'panel_source': 'Buffer dialog #buf-layer'},
        ],
    },
    {
        'skill': 'clip', 'tool': 'clip', 'category': 'single', 'name_cn': '范围裁取',
        'voice': '我按范围（某区/公园/单元边界）裁出范围内的目标', 'triggers_str': '某区的/某范围内的/XX区内的/范围内的（"某区内的YY"优先 clip 取范围内目标，而非 overlay）',
        'when': '按几何裁剪：某行政区/某公园/某街道范围内的点',
        'params_str': 'layer, range(preset_id | geojson), pre_filter?',
        'yields': '范围内的点子集（自动落地图）', 'contributes': '限定空间范围取点（"西陵区内的情绪点"），支撑中/微观落点',
        'scale': '中观/微观（范围内取**点**）', 'preconditions': 'range preset/geojson + 点层',
        'failure_modes': '误用于面∩面——clip 只切点，面层会报错；面∩面/面∪面用 overlay',
        'examples': '正:西陵区的情绪点 / 正:公园范围内的点 / 误:商业∩居住用地(→overlay)',
        'required_slots': ['range'],
        'planning_common': 'range 用 preset_id（行政区/单元）或 geojson；点层走可见层选源（不硬默认）',
        'params': [
            {'name': 'range', 'type': 'source', 'default': None, 'required': True, 'alias': [], 'hint': 'preset_id|geojson', 'panel_source': 'Range popup'},
            {'name': 'layer', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '默认 L2', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'pre_filter', 'type': 'str', 'default': None, 'required': False, 'alias': [], 'hint': 'field/op/value', 'panel_source': '通用 pre_filter'},
            {'name': 'as', 'type': 'str', 'default': None, 'required': False, 'alias': ['output', 'output_layer', 'layer_name', 'named', 'name'], 'hint': '图层名', 'panel_source': '通用 as'},
            {'name': 'keep', 'type': 'bool', 'default': None, 'required': False, 'alias': [], 'hint': '保留免清理', 'panel_source': '通用 keep'},
        ],
    },
    {
        'skill': 'overlay', 'tool': 'overlay', 'category': 'single', 'name_cn': '叠置交叉',
        'voice': '我叠两个图层找复合问题区', 'triggers_str': '居住用地里情绪差的/两图交集',
        'when': '叠置分析：交集/并集/差集（商业用地 ∩ 更新单元、规划范围 − 已更新）',
        'params_str': 'layer_a, layer_b, how(intersection|union|difference|symmetric)',
        'yields': '叠置结果面域', 'contributes': '跨图层交叉（用地 × 更新），识别复合问题区',
        'scale': '中观（跨图层面）', 'preconditions': '两图层面（layer_a/layer_b）',
        'failure_modes': '误用于取点——范围内取点用 clip；误用于抽单要素（→extract）；"A 内的 B"（面∩面）是单一空间关系，用 overlay 勿选 multi',
        'examples': '正:商业∩更新单元 / 正:居住用地里情绪差的 / 误:西陵区的点(→clip)',
        'required_slots': ['layer_a', 'layer_b'],
        'planning_common': 'how：intersection 交/union 并/difference 差',
        'params': [
            {'name': 'layer_a', 'type': 'source', 'default': None, 'required': True, 'alias': [], 'hint': 'preset_id', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'layer_b', 'type': 'source', 'default': None, 'required': True, 'alias': [], 'hint': 'preset_id', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'how', 'type': 'enum', 'enum': ['intersection', 'union', 'difference', 'symmetric_difference'], 'default': 'intersection', 'required': False, 'alias': ['mode'], 'hint': '叠置方式', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'as', 'type': 'str', 'default': None, 'required': False, 'alias': ['output', 'output_layer', 'layer_name', 'named', 'name'], 'hint': '图层名', 'panel_source': '通用 as'},
            {'name': 'keep', 'type': 'bool', 'default': None, 'required': False, 'alias': [], 'hint': '保留免清理', 'panel_source': '通用 keep'},
        ],
    },
    {
        'skill': 'zonal', 'tool': 'zonal_stats', 'category': 'single', 'name_cn': '单元归因',
        'voice': '我按行政/规划单元聚合情绪并给 4×5 归因', 'triggers_str': '这几个街道/社区的归因/单元评价',
        'when': '面域聚合统计：按更新单元/街道/社区把点聚合成单元指标（宏观/中观核心）',
        'params_str': 'layer, boundary(preset_id | geojson), metrics, top_n',
        'yields': '每单元 point_count/极性/4×5 归因 + 排序', 'contributes': '产出"哪个单元最差 + 归因"，宏观/中观结论的主干',
        'scale': '宏观/中观（单元聚合主干）', 'preconditions': 'boundary preset + 点层',
        'failure_modes': '误用于单点定位——micro 落点用 rank/hotspot；误用于纯面积结构（→area_stats）',
        'examples': '正:各街道情绪归因 / 正:更新单元排序 / 误:这个公园哪个点最差(→rank micro)',
        'required_slots': ['boundary'],
        'planning_common': 'boundary=preset_id（街道/社区/更新单元）；点层走可见层选源（不硬默认）；C 赛道情绪主干',
        'params': [
            {'name': 'boundary', 'type': 'source', 'default': None, 'required': True, 'alias': ['zone', 'region'], 'hint': 'preset_id', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'agg_cols', 'type': 'list', 'default': ['score'], 'required': False, 'alias': [], 'hint': '聚合列', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'layer', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '默认 yichang_l2_t1', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'range', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '可选先裁剪', 'panel_source': '通用 range'},
            {'name': 'pre_filter', 'type': 'str', 'default': None, 'required': False, 'alias': [], 'hint': 'field/op/value', 'panel_source': '通用 pre_filter'},
            {'name': 'top_n', 'type': 'int', 'default': None, 'required': False, 'alias': ['top', 'limit', 'n'], 'hint': 'Top N', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
        ],
    },
    {
        'skill': 'compare', 'tool': 'compare_regions', 'category': 'single', 'name_cn': '区域对比',
        'voice': '我并排对比 ≥2 个区域（区/街道/单元）的情绪与归因，给差异方向（谁更消极/差在哪）', 'triggers_str': '对比/比较/VS/哪个更/谁更/两地/A与B',
        'when': '区域对比：≥2 个区/街道/单元并排对比情绪与归因，给差异方向',
        'params_str': 'layer, boundaries(≥2 个 preset_id·数组或 | ，分隔), range?',
        'yields': '并排对比 + 差异叙述', 'contributes': '"谁更消极/差在哪"的对比结论（C 赛道对比主干）',
        'scale': '宏观/中观（区域对比）', 'preconditions': '≥2 个 boundary preset',
        'failure_modes': '误用于单区归因——单区用 zonal/rank；compare 需 ≥2 区',
        'examples': '正:西陵vs伍家岗 / 正:这两个区谁更差 / 误:西陵区归因(→zonal)',
        'required_slots': ['boundaries'],
        'planning_common': 'boundaries=≥2 个 preset_id（行政区/街道/单元，数组或 | ，分隔）；复用 zonal_stats 逐区聚合（不造 geo 端点，守委托 Toolbox 红线）；出口=并排对比+差异叙述。C 赛道对比主干——decision_type=对比 时优先级高于单区 zonal/rank',
        'params': [
            {'name': 'boundaries', 'type': 'list', 'default': None, 'required': True, 'alias': ['regions', 'areas'], 'hint': '≥2 个 preset_id', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'agg_cols', 'type': 'list', 'default': ['score', 'polarity_index'], 'required': False, 'alias': [], 'hint': '聚合列', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'layer', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '默认 L2', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'range', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '可选', 'panel_source': '通用 range'},
        ],
    },
    {
        'skill': 'extract_feature', 'tool': 'extract_feature', 'category': 'single', 'name_cn': '要素抽取',
        'voice': '我从面边界按属性抽单要素为独立面（裁出某区/某单元/某类用地）', 'triggers_str': '抽某/裁出某/单独裁出/提取某',
        'when': '从面边界按属性抽单要素为独立面图层（把某区/某公园/某单元单独裁出来显示）',
        'params_str': 'layer(preset_id|geojson), where(field/op/value，field 见 catalog name_field)',
        'yields': '面子集 GeoJSON（自动落地图）', 'contributes': '纯 GIS 操作出口：用户要"裁出西陵区"等几何产物时用此，不走情绪归因',
        'scale': '宏观/中观（面要素）', 'preconditions': '面边界层（preset）+ name_field（field/op/value）',
        'failure_modes': '误用于"某区内的某类用地"——它只抽单要素，跨层交集要走 extract+overlay 链；误用于取点（→clip）',
        'examples': '正:裁出西陵区 / 正:抽出滨江公园 / 误:西陵区的商业用地(→extract+overlay 链)',
        'required_slots': ['layer'],
        'planning_common': 'layer=preset_id（行政区/单元/用地层）；where=field/op/value 抽特定要素；产面子图层自动落图',
        'params': [
            {'name': 'layer', 'type': 'source', 'default': None, 'required': True, 'alias': [], 'hint': 'preset_id', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'where', 'type': 'str', 'default': None, 'required': False, 'alias': [], 'hint': 'field/op/value', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'as', 'type': 'str', 'default': None, 'required': False, 'alias': ['output', 'output_layer', 'layer_name', 'named', 'name'], 'hint': '图层名', 'panel_source': '通用 as'},
            {'name': 'keep', 'type': 'bool', 'default': None, 'required': False, 'alias': [], 'hint': '保留免清理', 'panel_source': '通用 keep'},
        ],
    },
    {
        'skill': 'area_stats', 'tool': 'area_stats', 'category': 'single', 'name_cn': '面积占比统计',
        'voice': '我统计各类用地/各单元面积占比', 'triggers_str': '面积占比/各类用地占比/单元面积/用地结构',
        'when': '面积统计：各类用地面积占比、单元面积、单位面积情绪密度',
        'params_str': 'boundary(preset_id | geojson), group_by(字段·如 DLMC)',
        'yields': '面积 + 占比 + 着色面层（choropleth·用地自动附国标标准色，自动落地图）', 'contributes': '量化"占比""密度"，让结论从计数升级为强度/结构判断',
        'scale': '宏观/中观（面积结构）', 'preconditions': 'boundary preset + group_by 字段',
        'failure_modes': '误用于情绪归因——它只算面积占比；要情绪极性/4×5 归因用 zonal_stats/rank',
        'examples': '正:各区用地面积占比 / 正:用地结构 / 误:哪区情绪最差(→rank/zonal)',
        'required_slots': ['boundary'],
        'planning_common': 'boundary=preset_id；group_by=字段（如 name/用地类）；出口=占比表（结论支撑，非主图层）',
        'params': [
            {'name': 'boundary', 'type': 'source', 'default': None, 'required': True, 'alias': ['zone', 'region'], 'hint': 'preset_id', 'panel_source': 'Area-stats dialog boundary'},
            {'name': 'group_by', 'type': 'str', 'default': None, 'required': False, 'alias': ['by'], 'hint': '分组字段', 'panel_source': 'Area-stats dialog group_by'},
        ],
    },
    {
        'skill': 'merge', 'tool': 'merge', 'category': 'single', 'name_cn': '合并上卷',
        'voice': '我合并/dissolve 多面成片区或同类用地', 'triggers_str': '合并/合成/并成/dissolve/合成片区',
        'when': '合并 / dissolve：把多个面域合成一个片区，或同类用地合并',
        'params_str': 'layer, by(字段) | all',
        'yields': '合并后的面域', 'contributes': '上卷到更大尺度（几街道→一片区），支撑宏观结构结论',
        'scale': '宏观（上卷片区）', 'preconditions': '面边界层',
        'failure_modes': '误用于取子集——要某子区用 extract/clip，非 merge',
        'examples': None,
        'required_slots': ['boundary'],
        'planning_common': 'boundary=preset_id；by=字段|空=全部合并；产合并面图层自动落图（上卷到更大尺度）',
        'params': [
            {'name': 'boundary', 'type': 'source', 'default': None, 'required': True, 'alias': ['zone', 'region'], 'hint': 'preset_id', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'by', 'type': 'str', 'default': None, 'required': False, 'alias': ['sort', 'sort_by', 'criteria'], 'hint': '字段|空=全部', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'as', 'type': 'str', 'default': None, 'required': False, 'alias': ['output', 'output_layer', 'layer_name', 'named', 'name'], 'hint': '图层名', 'panel_source': '通用 as'},
            {'name': 'keep', 'type': 'bool', 'default': None, 'required': False, 'alias': [], 'hint': '保留免清理', 'panel_source': '通用 keep'},
        ],
    },
    {
        'skill': 'nearest', 'tool': 'nearest', 'category': 'single', 'name_cn': '最近邻锚定',
        'voice': '我找离某设施/POI 最近的点（锚定问题点离什么设施近）', 'triggers_str': '最近/邻近/最近邻/离X最近',
        'when': '最近邻：离某类 POI/设施最近的负面点，或 POI 锚定',
        'params_str': 'layer, target(POI 类型 | geojson), k',
        'yields': '邻近配对 + 距离 + 连线层（target→最近点·自动落地图）', 'contributes': '锚定"问题点离什么设施近"，支撑归因落点',
        'scale': '微观（POI 锚定）', 'preconditions': 'target POI/geojson + 点层',
        'failure_modes': '误用于面范围——要设施周边范围用 buffer，要区内点用 clip；"离X最近"是单一邻近关系，勿选 multi',
        'examples': None,
        'required_slots': ['target'],
        'planning_common': 'target=preset_id|geojson（设施/POI）；点层走可见层选源（不硬默认）；k=近邻数',
        'params': [
            {'name': 'target', 'type': 'source', 'default': None, 'required': True, 'alias': ['target_layer', 'target_poi'], 'hint': 'preset_id|geojson', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'k', 'type': 'int', 'default': 1, 'required': False, 'alias': [], 'hint': '近邻数', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'layer', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '点层', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
        ],
    },
    {
        'skill': 'hotspot', 'tool': 'hotspot', 'category': 'single', 'name_cn': '聚集识别(Gi*)',
        'voice': '我用 Gi* 识别负面/正面情绪显著聚集的冷热点', 'triggers_str': '聚集/热点/冷热/显著聚集/聚集区',
        'when': 'Gi* 热点：负面/正面情绪在空间上显著聚集的冷热点',
        'params_str': 'layer, value_col(score), invert(负面为热)',
        'yields': '每点 Gi* Z-score + hot/cold 分类', 'contributes': '识别"聚集在哪"，支撑预警/排查类出口',
        'scale': '微观（Gi* 逐点聚集）', 'preconditions': '点层 + value_col',
        'failure_modes': '与 density 混——hotspot=逐点 Gi* 冷热点分类（每点 hot/cold/ns）；要连续密度面/热力图用 density',
        'examples': '正:显著负面聚集区 / 正:冷热点识别 / 误:情绪热度连续分布(→density)',
        'required_slots': [],
        'planning_common': '点层走可见层选源（不硬默认）；value_col=score（invert 由工具默认：负面为热）；产 hot/cold/ns 点图层',
        'params': [
            {'name': 'value_col', 'type': 'str', 'default': 'score', 'required': False, 'alias': ['value', 'column', 'field_name'], 'hint': '计量列', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'invert', 'type': 'bool', 'default': None, 'required': False, 'alias': ['inverse'], 'hint': 'true=负面为热', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'layer', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '默认 L2', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'range', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '可选', 'panel_source': '通用 range'},
            {'name': 'as', 'type': 'str', 'default': None, 'required': False, 'alias': ['output', 'output_layer', 'layer_name', 'named', 'name'], 'hint': '图层名', 'panel_source': '通用 as'},
            {'name': 'keep', 'type': 'bool', 'default': None, 'required': False, 'alias': [], 'hint': '保留免清理', 'panel_source': '通用 keep'},
        ],
    },
    {
        'skill': 'filter_attr', 'tool': 'filter_attr', 'category': 'single', 'name_cn': '属性筛选',
        'voice': '我按字段属性筛子集（用地/极性/domain/element/时点）', 'triggers_str': '按字段/用地类/属性筛选/筛选某类/只看',
        'when': '按属性筛选：用地类型 / 极性 / domain / element / 时点',
        'params_str': 'layer, field, op(eq|in|gt|lt), value',
        'yields': '子集（点或聚合）', 'contributes': '聚焦切片（"商业用地"/"T1 负面"/"治理域"），支撑类型化结论',
        'scale': '全尺度（属性切片，不限空间范围）', 'preconditions': '点层已加载 + field/op/value 已知（先 query_layers 看字段）',
        'failure_modes': '误当空间裁剪——它只按属性不按几何；要"某范围内"用 clip',
        'examples': None,
        'required_slots': ['pre_filter'],
        'planning_common': 'pre_filter=field/op/value（如 domain/eq/urban_renewal、polarity/eq/negative）；点层走可见层选源；产点子集图层',
        'params': [
            {'name': 'pre_filter', 'type': 'str', 'default': None, 'required': True, 'alias': [], 'hint': 'field/op/value', 'panel_source': '通用 pre_filter'},
            {'name': 'layer', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '默认 L2', 'panel_source': 'EMC-only（无 Toolbox dialog·AI 执行）'},
            {'name': 'range', 'type': 'source', 'default': None, 'required': False, 'alias': [], 'hint': '可选', 'panel_source': '通用 range'},
            {'name': 'as', 'type': 'str', 'default': None, 'required': False, 'alias': ['output', 'output_layer', 'layer_name', 'named', 'name'], 'hint': '图层名', 'panel_source': '通用 as'},
            {'name': 'keep', 'type': 'bool', 'default': None, 'required': False, 'alias': [], 'hint': '保留免清理', 'panel_source': '通用 keep'},
        ],
    },
    {
        'skill': 'multi', 'tool': None, 'category': 'multi', 'name_cn': '多步组合',
        'voice': '这个问题要组合几步工具，我按固定链做', 'triggers_str': '多目标/复合问/并排序/并…再…/且…（一句话含多个动作，如"裁出来并排序"）',
        'when': None,  # multi 无 GIS catalog 项
        'required_slots': [], 'planning_common': '固定工具链，首轮直接执行不重选（进 while-loop 受 cap）',
        'chain': ['clip', 'zonal_stats'],
        'params': [],
    },
    {
        'skill': 'unknown', 'tool': None, 'category': 'unknown', 'name_cn': '自由探索',
        'voice': '这个问题我没现成技能，小心探索', 'triggers_str': '兜底',
        'when': None,  # unknown 无 GIS catalog 项
        'required_slots': [], 'planning_common': 'MAX_ROUNDS cap 4，受约束 ReAct（进 while-loop）',
        'params': [],
    },
]


# ── 派生函数（paradigm.py 调·保 GEO_TOOL_CATALOG/TEMPLATE_REGISTRY 文本等价）──

def derive_geo_catalog():
    """派生 GEO_TOOL_CATALOG（仅 GIS 工具·有 when 的）。params 用 params_str 原文（保 eval 等价）。"""
    out = []
    for c in TOOL_CONTRACTS:
        if not c.get('when'):
            continue
        out.append({
            'name': c.get('tool') or c['skill'],
            'when': c['when'],
            'params': c.get('params_str', ''),
            'yields': c.get('yields', ''),
            'contributes': c.get('contributes', ''),
            'scale': c.get('scale', '—'),
            'preconditions': c.get('preconditions', '—'),
            'failure_modes': c.get('failure_modes', '—'),
            'examples': c.get('examples'),
        })
    return out


def _derive_defaults(params):
    """params 结构化 → optional_defaults dict（仅 default 非 None 的·镜像 SKILL_DEFS）。"""
    return {p['name']: p['default'] for p in params if p.get('default') is not None}


def derive_template_registry():
    """派生 TEMPLATE_REGISTRY（全部技能·保 voice/triggers/planning_common/optional_defaults 等价）。
    注：optional_defaults 从 params 结构化派生（CB-04 单一源），与旧手写 dict 等价。"""
    out = []
    for c in TOOL_CONTRACTS:
        item = {
            'skill': c['skill'], 'name': c['name_cn'], 'category': c['category'],
            'voice': c['voice'], 'triggers': c.get('triggers_str', ''),
            'tool': c.get('tool'), 'required_slots': list(c.get('required_slots', [])),
            'optional_defaults': _derive_defaults(c.get('params', [])),
            'planning_common': c.get('planning_common', ''),
        }
        if 'chain' in c:
            item['chain'] = list(c['chain'])
        out.append(item)
    return out


def all_aliases():
    """聚合所有工具的参数别名（供前端 _PARAM_ALIAS 镜像 + validate 校验）。
    返回 {alias: canonical}。工具专属别名（如 density.bandwidth_m→radius）按工具隔离由前端 _TOOL_ALIAS 处理，
    本函数只返通用别名（跨工具的 output→as / top→top_n 等）。"""
    canon_map = {}  # 收集每参数的 canonical name + 其 alias
    for c in TOOL_CONTRACTS:
        for p in c.get('params', []):
            name = p['name']
            for a in p.get('alias', []):
                canon_map[a] = name
    return canon_map


def panel_missing():
    """L3（5.238 全Resolved）：列出 panel_source='PANEL_MISSING' 的**真缺口**参数（提醒开发者补 dialog）。
    'EMC-only'（设计无 Toolbox dialog·AI 执行）不计缺失；旧 pending 标记已全消灭（5.238）。"""
    out = []
    for c in TOOL_CONTRACTS:
        for p in c.get('params', []):
            src = p.get('panel_source', '')
            if 'PANEL_MISSING' in src:
                out.append({'skill': c['skill'], 'param': p['name'], 'panel_source': src})
    return out


if __name__ == '__main__':
    # 自检：派生输出行数 + panel_missing 清单
    geo = derive_geo_catalog()
    tpl = derive_template_registry()
    pm = panel_missing()
    print(f'[OK] TOOL_CONTRACTS={len(TOOL_CONTRACTS)} → GEO_TOOL_CATALOG={len(geo)}, TEMPLATE_REGISTRY={len(tpl)}')
    print(f'[L3] panel 真缺口(PANEL_MISSING)={len(pm)} 项（EMC-only 不计·L3 5.238 全Resolved）')
