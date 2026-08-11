"""城市体检出向契约（v1）· 行业表单项 → 情绪地图产出字段映射。

基于住建部城市体检四维度（住房→小区→街区→城区）+ 8 大领域指标 + 社会满意度调查
（广州 6.5 万份/上海 5.4 万份·样本 0.6‰~1.5‰·≥1500 份）+ 各城特色（广州 81 项/
东莞城中村 16 项/南沙青年 14 项）。

情绪地图聚合产物字段（真实存在·core/spatial_analysis.py）：
polarity_index / n_positive|negative|neutral / domain_top / element_top /
place_name / topic_top / issue_label / attribution / suggestion
"""
from __future__ import annotations

# CB-16 glm：诊断卡 domain_lens 枚举只有 urban_planning/renewal/operation/governance
# （stages.js:418）·'urban_checkup' 不在枚举 → 体检类契约永远不触发（S6 不可出卡）
# → domain 改用 'urban_governance'（城市体检 ≈ 城市治理·最小改动·4 枚举中最接近）
DOMAIN = 'urban_governance'

# ── 出口契约 ──────────────────────────────────────────────────
CONTRACTS = {
    'checkup_satisfaction': {
        'name': '社会满意度调查升级',
        'industry_interface': '城市体检·社会满意度调查（4 尺度问卷·住房/小区/街区/城区）',
        'scales': ['macro', 'meso', 'micro'],
        'field_mapping': {
            # CB-16 ③z2 P2（Codex/glm）：prose → 真实字段（防空卡）·对齐 Wave 1 checkup_dimension
            #   '/' = 优先取前者（_build_card split('/')[0]）·element_top 优先（中文要素·贴近"8 领域"语义）
            '满意度（4 尺度）': 'polarity_index',                # 评论情绪 → 自动满意率（极性=满意度代理·非问卷率）
            '8 领域情绪值': 'element_top/domain_top + polarity_index',   # 4×5 归因 → 领域情绪
            '不满意项定位': 'issue_label + place_name',         # 老旧小区/停车等
        },
        'can': '海量评论全量聚合 → 自动满意率（替代/补充小样本问卷）·空间精准',
        'cannot': '不能测"知晓率/使用率/行为"（需结构化问卷）',
        'boundary': '情绪=市民感知（主观），问卷=行为，可互验',
        'task_link': ['体检·社会满意度调查'],
        'data_status': '诚实边界（CB-23）：当前数据源 = 双轨索引代理（12345 分类汇总·12345 五类 525 处 ↔ 12 条体检指标）·真实问卷明细待补（中转站仅 0.2 万份总量）·问卷到位前标注代理·不宣称问卷口径',
    },
    'checkup_dimension': {
        'name': '体检四维度诊断',
        'industry_interface': '城市体检·住房/小区/街区/城区四维度（61 项基础指标）',
        'scales': ['micro', 'meso', 'macro'],
        'field_mapping': {
            # CB-16 Wave 1（两组预检）：prose → 真实聚合字段（∈_EMC_FIELDS 白名单）
            #   [scale=xxx] 限定：仅填匹配 diagnose.scale 的维度·其余"需对应尺度分析"（Codex P1·防 macro 值入 micro/meso 槽）
            '住房维度': 'issue_label + place_name [scale=micro]',
            '小区维度': 'domain_top/element_top + polarity_index [scale=meso]',
            '街区维度': 'issue_label + polarity_index [scale=meso]',
            '城区维度': 'polarity_index + domain_top [scale=macro]',
        },
        'can': '四维度情绪画像（主观感受维度）·对齐体检四层级',
        'cannot': '不能测客观达标（绿地率/设施数量/结构安全）',
        'boundary': '情绪=主观感受·客观指标=硬件达标·互补',
        'task_link': ['体检·四维度全覆盖'],
    },
    # CB-23 阶段2' 客观轨契约：客观指标（官方结构化）→ 图/数/表/观点·不产情绪字段
    'checkup_objective': {
        'name': '城市体检客观指标分析（客观轨）',
        'industry_interface': '城市体检·客观指标（可量化/可评价类·官方结构化数据）→ 两板块（安全韧性底线/民生基础需求）',
        'scales': ['macro', 'meso'],
        'field_mapping': {
            '指标数值': 'indicator_value（缺口数/隐患栋数/覆盖率）',
            '空间落位': 'region（行政区/街道/社区）',
            '统计表': 'stat_table（zonal 聚合·{col}_sum 总量口径）',
            '图': 'chart_type（加权密度/柱状/热力·非情绪色带）',
            '观点': '宏观诊断信号（定位关注区+排序·禁精确归因）',
        },
        'can': '官方客观指标（停车/学位/结构隐患/覆盖率）直接落图落表·真实数据·两板块分析',
        'cannot': '不能产情绪字段（polarity/4×5 归因）·不替代主观轨',
        'boundary': '客观轨=官方数据直读·主观轨=12345/双轨索引代理·两轨对照为桥',
        'task_link': ['两板块分析·安全韧性底线/民生基础需求'],
    },
}

# ── CB-23 阶段2' 两板块映射（Codex 审计 P1-3：移出 CONTRACTS 防空卡）──
# 静态指标域清单（供报告/问答引用·非行业表单项→EMC 字段映射·build_outlet_schema 消费会渲染空卡）
# 数值为 2025 年静态快照·引用前对照 口径不一致清单_18项（Codex P2-6：year/source 标注防漂移）
PANEL_MAPPING = {
    'checkup_two_panels': {
        'name': '两板块映射（安全韧性底线/民生基础需求）',
        'industry_interface': '专项规划修编·三张清单·体检问题清单（00-01:51）·板块=工作分类（非官方术语）·指标域=建科〔2023〕75号',
        'year': 2025,
        'source': '03-08 摘要·口径不一致清单_18项·受控源 A/B 级',
        'panels': {
            '安全韧性底线': '结构隐患42/围护454/楼道240/燃气6/管线186 + 250栋危旧房 + 50年建筑380 + 消防站覆盖20.59%',
            '民生基础需求': '停车140点2.99万/学位31点6603/充电桩84/托育34/幼儿园11/养老2 + 中学56.10%/菜市场57.84%覆盖',
        },
        'can': '两板块指标域×图层×数据一一对应·报告板块来源可溯（专项规划分类×建科75号）',
        'cannot': '不能将板块名当官方术语·250栋≠54栋结构隐患（口径不可等同）',
        'boundary': '板块=工作分类·报告标注来源·口径对照 18 项实表',
        'task_link': ['两板块分析报告'],
    },
}

# ── 指标库（官方三类 → 情绪地图字段·能/不能双栏）─────────────
# 官方（建科〔2023〕75号）：可量化（~55-65%）/ 可感知（~15-20%）/ 可评价（~15-25%）
# 情绪地图核心对接口 = 可感知 + 可评价（合计 30-45% 涉及市民感受维度）

# 可感知指标全量罗列（官方居民问卷满意度型·情绪地图核心对接口）
METRIC_MAPPINGS = {
    '公园绿地步行可达性感知': {
        'industry': '体检·可感知（街区维度）·居民问卷',
        'emc_field': 'element_top=环境 + topic_top（公园/绿地/散步）',
        'can': '评论"去公园方便吗"→绿地可达情绪',
        'cannot': '不能测绿地面积/服务半径（需 GIS）',
    },
    '养老托育覆盖满意度': {
        'industry': '体检·可感知（小区维度）·居民问卷',
        'emc_field': 'element_top=设施 + issue_label（养老/托育）',
        'can': '养老/托育设施情绪评价',
        'cannot': '不能测设施配建数量（需普查）',
    },
    '内涝积水感受': {
        'industry': '体检·可感知（城区维度）·居民问卷',
        'emc_field': 'topic_top（积水/内涝/淹）+ polarity_index',
        'can': '暴雨后"积水/内涝"评论情绪·实时',
        'cannot': '不能测排水能力（需工程数据）',
    },
    '15分钟生活圈覆盖满意度': {
        'industry': '体检·可感知/可评价（城区维度）·问卷+空间',
        'emc_field': 'element_top=设施 + topic_top（生活圈/买菜/便民）',
        'can': '生活圈便利情绪（购物/就医/办事）',
        'cannot': '不能测设施服务半径（需 GIS 分析）',
    },
    '小区环境品质感知': {
        'industry': '体检·可感知（小区维度）·居民问卷',
        'emc_field': 'element_top=环境 + issue_label（绿化/卫生/秩序）',
        'can': '小区绿化/卫生/秩序情绪评价',
        'cannot': '不能测绿化率/卫生达标（需巡查）',
    },
    '停车泊位缺口（居民感知）': {
        'industry': '体检·可感知（小区维度）·居民问卷',
        'emc_field': 'topic_top（停车难/没车位）+ polarity_index',
        'can': '停车难情绪热点（南京大数据互补）',
        'cannot': '不能测泊位缺口数（需普查）',
    },
    '物业管理评价': {
        'industry': '体检·可感知（小区维度）·居民问卷',
        'emc_field': 'element_top=服务 + issue_label（物业）',
        'can': '物业服务质量情绪评价',
        'cannot': '不能测物业达标率（需评价体系）',
    },
    '老旧街区改造需求感知': {
        'industry': '体检·可感知（街区维度）·居民问卷',
        'emc_field': 'element_top=设施/环境 + issue_label（老旧/破旧）',
        'can': '改造呼声情绪（老旧街区改造需求）',
        'cannot': '不能测改造必要性（需结构鉴定）',
    },
    '商圈活力/烟火气': {
        'industry': '体检·可感知（城区维度）·居民问卷',
        'emc_field': 'element_top=服务/文化 + topic_top（商圈/人气/烟火气）',
        'can': '商圈人气/活力情绪（上海低分项）',
        'cannot': '不能测商业营业额（需经济数据）',
    },
    '宜居宜业宜游感知': {
        'industry': '体检·可感知（城区维度）·居民问卷',
        'emc_field': 'polarity_index + domain_top 综合',
        'can': '整体宜居情绪（满意度替代问卷）',
        'cannot': '不能测综合评分结构（需问卷设计）',
    },
    # 可评价指标（综合评价·复合型·情绪地图增强）
    '城镇房屋基础信息数字化率': {
        'industry': '体检·可评价（城区维度）·统计+信息化',
        'emc_field': '（客观·情绪地图补使用感受）',
        'can': '数字化率客观·情绪地图补居民使用感受',
        'cannot': '不能测数字化率本身（需信息化统计）',
    },
    '15分钟社区生活圈综合评估': {
        'industry': '体检·可评价（城区维度）·空间分析+满意度',
        'emc_field': 'element_top=设施 + 满意度情绪值',
        'can': '空间分析客观 + 情绪补满意度',
        'cannot': '不能测设施布局（需 GIS）',
    },
    '城市人居环境质量综合评价': {
        'industry': '体检·可评价（城区维度）·多源融合',
        'emc_field': 'polarity_index + 4×5 归因综合',
        'can': '多源融合补感知维度（情绪=市民感受源）',
        'cannot': '不能测客观指标（需遥感/统计）',
    },
    # 可量化指标（情绪地图不替代·作客观基线）
    '生态宜居': {
        'industry': '体检·可量化（生态宜居/绿地率/空气/水）',
        'emc_field': 'element_top=环境 + polarity_index',
        'can': '绿地/水体/环境情绪评价（作基线补充）',
        'cannot': '不能测绿地率/水质（需遥感/监测）',
    },
    '健康舒适': {
        'industry': '体检·可量化（设施完善/生活便利）',
        'emc_field': 'element_top=设施 + issue_label',
        'can': '设施满意度情绪值（社区/养老/便民）',
        'cannot': '不能测设施达标数量',
    },
    '交通便捷': {
        'industry': '体检·可量化（通勤/停车/路网）',
        'emc_field': 'element_top=设施/事件 + topic_top（停车/堵车）',
        'can': '交通/停车情绪热点（南京大数据互补）',
        'cannot': '不能测路网密度/通行流量（需交通数据）',
    },
    '风貌特色': {
        'industry': '体检·可量化（风貌/景观）',
        'emc_field': 'element_top=环境/文化 + issue_label',
        'can': '风貌/景观情绪评价',
        'cannot': '不能测风貌达标（需风貌评估）',
    },
    '多元包容': {
        'industry': '体检·可量化（历史文化/包容性）',
        'emc_field': 'element_top=文化 + issue_label',
        'can': '历史文化街区"烟火气/记忆"情绪指标',
        'cannot': '不能测历史建筑保护等级（需文物普查）',
    },
}
