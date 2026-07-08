"""L2 沉淀智慧 · 答问范式范例与 do/dont（人审策展，周期更新）。

三层知识闭环的中层：
- L1 = MANIFESTO（稳定身份/公约，整段注入，本文件不重复其内容）；
- L2 = 本文件（半稳定·人审策展的"答问智慧"：scale×domain 维度的 do/dont + 正例结构）；
- L3 = DATA/ai_qa/episodes.jsonl（每次问答自动 append，被 ai_qa/consolidate.py 挖掘提议 L2）。

自成长闭环：捕获(L3) → 沉淀(consolidate 提议 → 人审改本文件) → 注入(buildContext 取 wisdom_text 进 ctx.context)。

**人审是 L2 不腐烂的前提**：自动写入只进 L3，不直接进 L2；L2 恒小高信噪比 → v1 可整段注入，
当条目 > ~12 条时切 retrieve_wisdom(scale, domains) 按 diagnose 卡检索（v2）。
改 L2 = 改本文件（数据，非逻辑）；单源真理在此，运行时经 buildContext 注入。
"""


# ════════════ WISDOM 种子（从 revision-log 5.36-5.38 验收硬测 + MANIFESTO 场景提炼）════════════
# 字段：id / scale(macro|meso|micro|*) / domains([] = 全域) / scenario / do / dont / exemplar
# 注：内嵌引文一律用中文全角 “”，避免与 Python 字符串定界符冲突（同 manifesto.py 习惯）。
WISDOM = [
    {
        "id": "renewal-macro-priority",
        "scale": "macro",
        "domains": ["urban_renewal"],
        "scenario": "更新优先级排序（“中心城区哪里最需优先更新”类）",
        "do": "zonal_stats(更新单元) + rank(worst) → 出“哪类单元系统性落后”的结构判断 + Top3 归因 + 时序建议",
        "dont": "落单点坐标 / 只报“得分最低的格”——宏观问禁落单点（MANIFESTO 第十一节）",
        "exemplar": "结论分 3 层：①系统性落后的单元类型（如“老旧居住型更新单元”）②Top3 单元名 + 4×5 归因（更新×环境=物业脏乱 等）③建议优先时序与资源配置",
    },
    {
        "id": "park-micro-locate",
        "scale": "micro",
        "domains": ["urban_operation", "urban_governance"],
        "scenario": "具体范围落点（“这个公园里哪里最差”类）",
        "do": "clip(公园/街区几何) + rank(50-100m 网格 worst) → 具体落点（可飞到地图）",
        "dont": "泛泛“整体偏负面”——微观问禁泛泛（MANIFESTO 第十一节）",
        "exemplar": "结论落点：“XX 公园南侧入口 50m 网格聚集负面（极性 -1.2，12 点），归因 运营×环境=噪音脏乱”，附 [ref:区域名] 供点击定位",
    },
    {
        "id": "governance-hotspot",
        "scale": "macro",
        "domains": ["urban_governance"],
        "scenario": "12345/投诉聚集预警",
        "do": "hotspot(负面为热) + filter_attr(domain=治理) → 显著热点聚集区 + 关键词，出口=预警",
        "dont": "只报投诉数量不落空间 / 不做聚集显著性",
        "exemplar": "“治理域负面显著热点聚集于 XX 路与 YY 路交叉口周边（Gi* Z>2.5），关键词：噪音/占道/停车；建议优先巡查”",
    },
    {
        "id": "meso-unit-compare",
        "scale": "meso",
        "domains": ["urban_renewal", "urban_planning"],
        "scenario": "几个街道/社区/更新单元对比",
        "do": "zonal_stats(街道/社区 boundary) + rank(by=worst/best) → 单元级排序 + 各自 4×5 归因 + 单元针对性建议",
        "dont": "混到单点 / 泛到整城——中观要“单元级”颗粒度",
        "exemplar": "“对比 3 个更新单元：A 最差（极性 -0.8，更新×设施=配套不足），B 次之（...），C 最好（...）；A 建议优先补短板设施”",
    },
    {
        "id": "define-concept",
        "scale": "macro",
        "domains": [],
        "scenario": "概念定义类（“什么是情绪地图/极性指数/4×5”等）",
        "do": "1-2 轮直接 answer，不调 geo 工具；引 MANIFESTO 概念，给定义+用途+示例",
        "dont": "盲目 query/ensure_zone 浪费轮次；定义类 decision_type=定义",
        "exemplar": "直接答：“情绪地图是…”（引第一节）+“它用于…”（引第五/六节），2-3 句精炼",
    },
    {
        "id": "data-gap-honest",
        "scale": "*",
        "domains": [],
        "scenario": "数据缺口（DIAGNOSE 判 strategy ≠ ready）",
        "do": "硬缺口(request_upload)→出“请求上传”卡不硬答；软缺口(fallback_annotated)→降级作答 + 答案尾标口径局限",
        "dont": "假装全知 / 用情绪数据冒充专业紧迫度等它没有的维度",
        "exemplar": "“本结论为情绪视角的更新优先级（非综合紧迫度评估），缺：更新紧迫度评估。建议上传 XX 数据后重提。”",
    },
]


def retrieve_wisdom(scale=None, domains=None):
    """按 diagnose 卡的 scale + domains 检索命中条目。

    匹配规则：scale 精确匹配或条目 scale='*'；domains 任一交集或条目 domains 为空（全域）。
    v1（人审·L2 恒小）可不用此函数直接整段；v2（L2 > ~12 条）harness 按 diagnose 卡调此检索。
    """
    scale = (scale or '').strip().lower()
    doms = set(domains or [])
    out = []
    for w in WISDOM:
        ws = (w.get('scale') or '').strip().lower()
        if scale and ws not in ('', '*', scale):
            continue
        wd = set(w.get('domains') or [])
        if wd and doms and not (wd & doms):
            continue
        out.append(w)
    return out


def wisdom_text(entries=None):
    """渲染 wisdom 为 prompt 可读文本（注入 ctx.context）。

    entries 为空列表 → 返回空串（不注入）。默认渲染全量（v1 wholesale）。
    """
    entries = WISDOM if entries is None else entries
    if not entries:
        return ''
    lines = ['【答问智慧（人审策展 · 范式范例）】按问题 scale×domain 对号入座：']
    for w in entries:
        dom = '/'.join(w.get('domains') or []) or '全域'
        lines.append(
            f"- [{w.get('scale')}/{dom}] {w.get('scenario')}\n"
            f"    ✓ do：{w.get('do')}\n"
            f"    ✕ dont：{w.get('dont')}\n"
            f"    ▸ 正例：{w.get('exemplar')}"
        )
    return '\n'.join(lines)
