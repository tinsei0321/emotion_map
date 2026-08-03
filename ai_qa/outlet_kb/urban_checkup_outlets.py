"""城市体检出向契约（v1）· 行业表单项 → 情绪地图产出字段映射。

基于住建部城市体检四维度（住房→小区→街区→城区）+ 8 大领域指标 + 社会满意度调查
（广州 6.5 万份/上海 5.4 万份·样本 0.6‰~1.5‰·≥1500 份）+ 各城特色（广州 81 项/
东莞城中村 16 项/南沙青年 14 项）。

情绪地图聚合产物字段（真实存在·core/spatial_analysis.py）：
polarity_index / n_positive|negative|neutral / domain_top / element_top /
place_name / topic_top / issue_label / attribution / suggestion
"""
from __future__ import annotations

DOMAIN = 'urban_checkup'

# ── 出口契约 ──────────────────────────────────────────────────
CONTRACTS = {
    'checkup_satisfaction': {
        'name': '社会满意度调查升级',
        'industry_interface': '城市体检·社会满意度调查（4 尺度问卷·住房/小区/街区/城区）',
        'scales': ['macro', 'meso', 'micro'],
        'field_mapping': {
            '满意度（4 尺度）': '评论情绪 → 自动满意率',   # 替代问卷
            '8 领域情绪值': '4×5 归因 → 领域情绪',        # 生态宜居等
            '不满意项定位': 'issue_label + place_name',   # 老旧小区/停车等
        },
        'can': '海量评论全量聚合 → 自动满意率（替代/补充小样本问卷）·空间精准',
        'cannot': '不能测"知晓率/使用率/行为"（需结构化问卷）',
        'boundary': '情绪=市民感知（主观），问卷=行为，可互验',
        'task_link': ['体检·社会满意度调查'],
    },
    'checkup_dimension': {
        'name': '体检四维度诊断',
        'industry_interface': '城市体检·住房/小区/街区/城区四维度（61 项基础指标）',
        'scales': ['micro', 'meso', 'macro'],
        'field_mapping': {
            '住房维度': 'micro 网格/POI 归因（建筑/居住情绪）',
            '小区维度': 'meso 社区单元 zonal（设施/服务/环境）',
            '街区维度': 'meso 街道单元 zonal（功能/活力/风貌）',
            '城区维度': 'macro 行政区/片区面（整体发展质量）',
        },
        'can': '四维度情绪画像（主观感受维度）·对齐体检四层级',
        'cannot': '不能测客观达标（绿地率/设施数量/结构安全）',
        'boundary': '情绪=主观感受·客观指标=硬件达标·互补',
        'task_link': ['体检·四维度全覆盖'],
    },
}

# ── 指标库（8 大领域 → 情绪地图字段·能/不能双栏）─────────────
METRIC_MAPPINGS = {
    '生态宜居': {
        'industry': '体检·生态宜居（绿地率/空气/水）',
        'emc_field': 'element_top=环境 + polarity_index',
        'can': '绿地/水体/环境情绪评价',
        'cannot': '不能测绿地率/水质（需遥感/监测）',
    },
    '健康舒适': {
        'industry': '体检·健康舒适（设施完善/生活便利）',
        'emc_field': 'element_top=设施 + issue_label',
        'can': '设施满意度情绪值（社区/养老/便民）',
        'cannot': '不能测设施达标数量',
    },
    '交通便捷': {
        'industry': '体检·交通便捷（通勤/停车/路网）',
        'emc_field': 'element_top=设施/事件 + topic_top（停车/堵车）',
        'can': '交通/停车情绪热点（南京大数据互补）',
        'cannot': '不能测路网密度/通行流量（需交通数据）',
    },
    '风貌特色': {
        'industry': '体检·风貌特色（风貌/景观）',
        'emc_field': 'element_top=环境/文化 + issue_label',
        'can': '风貌/景观情绪评价',
        'cannot': '不能测风貌达标（需风貌评估）',
    },
    '多元包容': {
        'industry': '体检·多元包容（历史文化/包容性）',
        'emc_field': 'element_top=文化 + issue_label',
        'can': '历史文化街区"烟火气/记忆"情绪指标',
        'cannot': '不能测历史建筑保护等级（需文物普查）',
    },
}
