"""城市更新出向契约（v1）· 行业表单项 → 情绪地图产出字段映射。

基于住建部《城市更新规划编制导则》（建办科〔2025〕46号）+ 宁夏/新疆/大连等地方导则
+ 湖北/宜昌等真实案例。对齐 CLAUDE.md 出口抽象层（EMC 找市场·一一对应·能/不能双栏）。

情绪地图聚合产物字段（真实存在·core/spatial_analysis.py）：
polarity_index / n_positive|negative|neutral / domain_top / element_top /
place_name / topic_top / issue_label / attribution / suggestion / category_top
"""
from __future__ import annotations

DOMAIN = 'urban_renewal'

# ── 出口契约（outlet_id → 契约定义）─────────────────────────────
# field_mapping = 行业表单项 ← 情绪地图产出字段（确定性组装）
CONTRACTS = {
    'renewal_object_identify': {
        'name': '更新对象识别',
        'industry_interface': '专项规划·更新对象分布图（建办科〔2025〕46号）',
        'scales': ['macro'],
        'field_mapping': {
            '更新对象（疑似）': 'issue_label',        # 消极归因 → 疑似更新对象
            '对象分布图': '图层（极性面）',            # 图
            '空间聚集强度': 'polarity_index',         # 数
        },
        'can': '评论归因→消极聚集区（海量真实评估·反向印证更新对象）',
        'cannot': '不能测产权/建筑结构（需普查/鉴定）',
        'boundary': '情绪=市民感知维度，客观=结构维度，互补',
        'task_link': ['①既有建筑改造', '②老旧小区整治'],
    },
    'renewal_demand': {
        'name': '更新需求摸排',
        'industry_interface': '片区策划·问题清单/需求分析（宁夏导则·问题清单表）',
        'scales': ['meso', 'micro'],
        'field_mapping': {
            '问题类型': 'issue_label',              # 问题标签 → 需求类型
            '需求强度': 'polarity_index',           # 极性指数 → 优先级
            '需求位置': 'place_name + 网格/POI',     # 代表地名 → 地理定位
            '需求类型（设施/环境/服务/文化/事件）': 'domain_top/element_top',  # 4×5 归因
            '数据基础': 'point_count + 时间窗',      # N 条评论
        },
        'can': '评论归因→设施/环境/服务缺口热点·需求强度·位置·类型·数据基础（几乎全填）',
        'cannot': '不能测实际设施数量/精确面积（需普查/详规）',
        'boundary': '情绪说"哪里呼声高·缺什么"，普查说"缺多少·缺在哪地块"',
        'task_link': ['②老旧小区整治', '⑥基础设施改造', '③完整社区'],
    },
    'renewal_sequence': {
        'name': '更新时序排序',
        'industry_interface': '专项规划·更新项目实施计划表（五年行动计划清单）',
        'scales': ['meso'],
        'field_mapping': {
            '优先级排序': 'polarity_index 降序',     # 情绪强度 → 先后
            '单元特征': 'domain_top/element_top',    # 归因 → 特征
        },
        'can': '情绪强度排序 → 更新时序建议（先重后轻）',
        'cannot': '不能测资金/实施条件（需项目库评估）',
        'boundary': '情绪排序是"需求紧迫度"参考·资金/可行性另行评估',
        'task_link': ['②老旧小区整治', '④老旧街区'],
    },
    'renewal_content': {
        'name': '更新内容确定',
        'industry_interface': '片区策划·更新内容统计表（宁夏表11·大类×子类）',
        'scales': ['meso'],
        'field_mapping': {
            '更新大类（设施/环境/服务/文化/事件）': 'element_top',
            '更新内容分布': 'n_elem_* 计数',
        },
        'can': '4×5 归因分布 → 更新内容大类（设施补齐/环境提升/服务优化/文化活化）',
        'cannot': '不能定"留改拆建"具体规模（需产权/结构评估）',
        'boundary': '情绪指出"更新什么方向"，规模/方式需工程评估',
        'task_link': ['③完整社区', '⑤完善城市功能'],
    },
    'renewal_project': {
        'name': '更新项目生成',
        'industry_interface': '片区策划·更新项目统计表（宁夏表12：序号/名称/类型/规模/拆除比例/拆建比）',
        'scales': ['micro'],
        'field_mapping': {
            '项目名称': 'place_name',
            '项目类型': 'domain_top/element_top',
            '规模（参考）': 'point_count + 情绪聚集范围',
            '拆除比例/拆建比': '（不能测·需工程评估）',   # 边界·不可越界
        },
        'can': '候选更新点 + 需求强度 + 归因 → 项目库条目的"名称/类型"',
        'cannot': '不能测拆除比例/拆建比/投资（需工程/资金评估）·须守底线（拆除≤20%·拆建比≤2）',
        'boundary': '情绪产出"更新候选 + 需求"，工程规模/资金/底线另行评估',
        'task_link': ['②老旧小区整治', '⑥基础设施改造'],
    },
}

# ── 指标库（行业官方指标 → 情绪地图字段映射·能/不能双栏）────────
METRIC_MAPPINGS = {
    '设施缺口': {
        'industry': '完整社区·设施配套（建办科〔2021〕55号 6目标20项）',
        'emc_field': 'element_top=设施 + issue_label',
        'can': '评论归因→设施缺口热点（停车/电梯/养老/便民）',
        'cannot': '不能测实际设施数量/达标率（需普查）',
    },
    '需求强度': {
        'industry': '更新需求摸排·需求强度',
        'emc_field': 'polarity_index + n_negative 占比',
        'can': '空间精准需求强度',
        'cannot': '不能替代工程检测（电梯结构安全等）',
    },
    '需求位置': {
        'industry': '更新需求摸排·需求位置',
        'emc_field': 'place_name + 网格/POI 落点',
        'can': '精确到小区/栋/路',
        'cannot': '不能测精确产权/面积（需详规）',
    },
}
