"""审查层 · REVIEW_CHECKLIST 六条 + 审查员模型配置。

Draft Answer 出稿后，审查员（默认 Flash，省 token、快）按六条 checklist 审查；
不达标（pass=False）带 revise_hints 让出稿模型重写（最多 1 轮，router 控制）。

六条来自用户对"最终回答质量"的硬要求：
排版易读 / 结构清晰 / 内容精炼 / 语句专业（规划行业用语）/ 数据驱动 / 结论有指向性。
"""

# 六条审查标准（顺序即审查顺序；key 稳定勿改，前端审查状态区按 key 渲染 ✓/△/✕）。
REVIEW_CHECKLIST = [
    {
        'key': 'layout',
        'name': '排版易读',
        'desc': '关键信息（数值、区域名、结论）是否凸显；是否分点/分段清晰、层次分明，便于快速抓重点。',
    },
    {
        'key': 'structure',
        'name': '结构清晰',
        'desc': '是否有"问题定性 → 数据证据 → 结论建议"的体系化结构（而非流水账式罗列）。',
    },
    {
        'key': 'concise',
        'name': '内容精炼',
        'desc': '无废话、恭维、不专业或无意义的话；信息密度高，每句都有价值。',
    },
    {
        'key': 'professional',
        'name': '语句专业',
        'desc': '贴合城市规划行业用语，专业名词与常规说法准确（如"城市更新单元/15分钟生活圈/极性指数/归因矩阵"），不口语化、不外行。',
    },
    {
        'key': 'data_driven',
        'name': '数据驱动',
        'desc': '每个判断都有具体数值与区域支撑，引用区域标注 [ref:区域名]；不臆造、不空泛。',
    },
    {
        'key': 'actionable',
        'name': '结论有指向性',
        'desc': '必须有明确结论，且分析内容指向具体的城建问题与可落地建议（更新时序/资源配置/优先片区），有"出口"而非开放讨论。',
    },
]

# 审查员模型：默认 Flash（checklist 式审查够用、省 token、快）；env REVIEWER_MODEL 覆盖（如切 Pro 审）。
import os
REVIEWER_MODEL = os.environ.get('REVIEWER_MODEL', 'deepseek-chat')
