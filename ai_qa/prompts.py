"""思考层 · Agent Loop prompt builder（ReAct）。

替代上一轮的 think/answer/review 三阶段。现两阶段：
- agent_step ：ReAct 每轮，输出 {thought, action} JSON（流式 reasoning + content JSON）。
- answer     ：agent 决定 answer 后，基于全部探索历史出最终结论（流式 markdown）。

改 prompt 只改本文件。
"""
from ai_qa.manifesto import MANIFESTO
from ai_qa.paradigm import (
    scale_paradigm_text, domain_outlets_text, geo_tool_catalog_text,
    DIAGNOSE_CARD_FIELDS, DATA_STRATEGY,
)


def _inject_tokens(prompt, context_tokens):
    """@关联对象 → 追加约束。"""
    if not context_tokens:
        return prompt
    refs = []
    for t in context_tokens:
        typ = t.get('type', '对象')
        label = t.get('label') or t.get('ref', {}).get('name') or '?'
        refs.append(f'{typ}:{label}')
    return prompt + '\n用户本次@关联的对象（回答/操作须围绕它们展开）：' + '、'.join(refs)


# ── agent_step 阶段：ReAct 每轮，输出 {thought, action} ──────────────────────
AGENT_TEMPLATE = """

═══════════ 本次任务 · Agent Loop 第 {round} 轮（ReAct）═══════════
你在用 Thought-Action-Observation 模式解题：每轮思考一步、做一个动作、看结果、再思考。
本轮你必须输出**严格的 JSON 对象**（仅 JSON，禁 markdown 代码块 / 前后解释），结构如下：
{{
  "thought": "这一步你在想什么（口语化、面向用户、可见，如：我先看看当前有哪些数据）",
  "action": {{
    "type": "tool", "name": "工具名", "params": {{...}}
  }}
  // 或（信息已足够时）：
  // "action": {{ "type": "answer" }}
}}

【可用工具】（action.name 只能取以下值之一，params 仅列出的键）：
- query_layers：查当前已加载的图层/数据（有什么可用）。params: {{}}
- query_zone_stats：查区域极性统计（按维度排序找区域）。params: {{ "criteria": "worst" | "best" | "domain:规划" | "domain:更新" | "domain:运营" | "domain:治理" | "element:设施" | "element:环境" | "element:服务" | "element:文化" | "element:事件", "top": 个数(默认3) }}
- query_attribution：查 4×5 归因（全局或某区域）。params: {{ "zone": "区域名" 或 空字符串(全局) }}
- query_keywords：查关键词/热门话题。params: {{ "polarity": "overall" | "positive" | "negative" }}
- ensure_zone：生成/确保聚合域（仅当无聚合层时用）。params: {{ "analysis": "square" | "zonal"(默认square), "cell_size": 米(square默认500), "polarity": "overall", "mode": "2d" | "3d"(默认2d) }}
- focus_zones：定位区域到地图（飞到+高亮）。params: {{ "names": ["区域A", "区域B"] }}
- open_attribution：展开 Overview 归因面板。params: {{}}
- inspect_zone：深读某聚合域明细。params: {{ "name": "区域名" }}
- answer：已掌握足够信息，退出 loop 出结论。params: {{}}

【Agent 规则】（严守）
1. **先 query 后操作**：拿到问题先用 query_layers / query_zone_stats / query_attribution 摸清当前有什么数据、数据说什么，再决定动作。**勿盲目 ensure_zone**（已有聚合层就复用）。
2. **数据驱动**：thought 里引用 query 拿到的真实数值/区域，勿臆造。
3. **每轮只做一个动作**（一个 tool 或 answer）。
4. **信息足够即 answer**：通常 3-6 轮；纯定义类问题（如"什么是情绪地图"）1-2 轮即可 answer，不必 query。
5. **thought 面向用户、口语化**（"我先看看有哪些数据"），不提 JSON/tool 字眼。

【已完成的探索】（历轮 thought + action + 工具观察；首轮为空）：
{tool_history}

当前数据（grounding，主窗口推送的图层摘要）：
{context}
"""


def build_agent_prompt(context: str = '', tool_history: str = '', round_n: int = 1,
                       context_tokens: list = None) -> str:
    """agent_step 阶段：ReAct 每轮，输出 {thought, action} JSON。"""
    ctx = context or '（未提供数据上下文）'
    hist = tool_history or '（首轮，尚无探索）'
    prompt = MANIFESTO + AGENT_TEMPLATE.format(round=round_n, tool_history=hist, context=ctx)
    return _inject_tokens(prompt, context_tokens)


# ── answer 阶段：基于全部探索出最终结论 ─────────────────────────────────────
FINAL_TEMPLATE = """

═══════════ 本次任务 · 最终结论 ═══════════
你已完成探索（下方"探索历史"含你历轮的 thought/action/工具观察）。现在基于掌握的全部信息，给用户最终结论。

严格遵守 MANIFESTO 第十节回答公约：数据驱动（引用数值/区域 + [ref:区域名]）、结构清晰（问题定性 → 数据证据 → 结论建议）、4×5 表达、专业用语、结论有指向（城建问题 + 可落地建议）、精炼。
结论要对齐演示逻辑链：指出有张力的区域 → 解释归因 → 指向具体城建问题与建议。

【探索历史】（你历轮的 thought + action + 工具观察）：
{tool_history}

当前数据：
{context}
"""


def build_final_prompt(context: str = '', tool_history: str = '', context_tokens: list = None) -> str:
    """answer 阶段：基于全部探索出最终结论（流式 markdown + [ref:]）。"""
    ctx = context or '（未提供数据上下文）'
    hist = tool_history or '（无探索历史）'
    prompt = MANIFESTO + FINAL_TEMPLATE.format(tool_history=hist, context=ctx)
    return _inject_tokens(prompt, context_tokens)


# ── diagnose 阶段：问题理解卡（agent_step 之前的专业认知前置步）─────────────────
DIAGNOSE_TEMPLATE = """

═══════════ 本次任务 · 问题诊断（DIAGNOSE · 专业认知前置步）═══════════
阅读用户问题，**像城市规划师那样先沿专业轴拆解**——不是语义解析后直接走管线，而是判定：
这是个什么行业视角、什么空间尺度、什么决策类型的问题，该出什么形态的结论，需要什么数据、
当前是否齐全、该用什么 GIS 方法。诊断卡会指导后续 agent loop 的工具选型与最终结论的颗粒度。

严格遵守 MANIFESTO 第十一节「尺度-方法-范式」：结论颗粒度必须匹配问题尺度（宏观禁落单点 /
微观禁泛泛）。数据盘点要诚实——缺关键数据须在 strategy 标 request_upload 或 fallback_annotated，
勿假装全知。

输出**严格 JSON 对象**（仅 JSON，禁 markdown 代码块 / 前后解释），结构如下（6 字段必填）：
{{
  "domain_lens": ["urban_planning" | "urban_renewal" | "urban_operation" | "urban_governance", ...],
  "scale": "macro" | "meso" | "micro",
  "decision_type": "评价" | "选址" | "排查" | "对比" | "监测" | "定义",
  "outlet": "报告结论" | "指标排序" | "地图定位" | "建议清单" | "预警",
  "data_plan": {{
    "needed": ["回答此问所需的数据，如『更新单元矢量』『L2 极性』"],
    "available": ["当前已有的，如『L2 T1 极性』『行政区边界』"],
    "gap": ["缺失的，如『更新紧迫度评估』"],
    "strategy": "ready" | "fallback_annotated" | "request_upload"
  }},
  "method": ["从下方 GIS 工具目录选 + 组合，如 'zonal_stats(更新单元) → rank(worst)'"]
}}

【尺度判定要点】（查下方矩阵）：
- 提到"中心城区/片区/整体/哪个区/哪类"→ 多为宏观；提到"街道/社区/更新单元/几个片区对比"→ 中观；
  提到"这条街/这个小区/这个公园/哪个点位"→ 微观。
- "定义"类问题（如"什么是情绪地图"）scale 可填 macro 但 decision_type=定义，method 可空。
【strategy 判定要点】（查下方 strategy 语义）：硬缺口（无替代）→ request_upload；
有合理替代（社区代街道、用极性近似紧迫度）→ fallback_annotated；齐全 → ready。

当前数据（grounding，主窗口推送的图层摘要；据此判断 available/gap）：
{context}
"""


def build_diagnose_prompt(context: str = '', context_tokens: list = None) -> str:
    """diagnose 阶段：输出 6 字段问题理解卡（流式 reasoning + content JSON）。

    范式知识（矩阵/出口/工具目录/卡字段）在 DIAGNOSE_TEMPLATE.format() 之后拼接——
    避免这些含花括号的文本被 str.format 误解析（见 manifesto/py 花括号警示）。
    """
    ctx = context or '（未提供数据上下文）'
    prompt = MANIFESTO + DIAGNOSE_TEMPLATE.format(context=ctx)
    # 范式知识附录（format 后拼接，花括号安全）
    prompt += '\n═══════════ 附录 · 尺度-方法-范式矩阵 ═══════════\n' + scale_paradigm_text()
    prompt += '\n\n═══════════ 附录 · 4 领域出口范式启发库 ═══════════\n' + domain_outlets_text()
    prompt += '\n\n═══════════ 附录 · GIS 操作目录（method 字段据此选型）═══════════\n' \
              + geo_tool_catalog_text()
    prompt += '\n\n═══════════ 附录 · 诊断卡字段说明 ═══════════'
    for k, v in DIAGNOSE_CARD_FIELDS.items():
        prompt += f'\n- {k}：{v}'
    prompt += '\n\n═══════════ 附录 · data_plan.strategy 语义 ═══════════'
    for k, v in DATA_STRATEGY.items():
        prompt += f'\n- {k}：{v}'
    return _inject_tokens(prompt, context_tokens)


# ── revise 阶段：审查未过，基于 draft + hints 重写 ───────────────────────────
REVISE_TEMPLATE = """

═══════════ 本次任务 · 修订重写 ═══════════
你之前的草稿未通过审查员审查（审查意见见下）。请基于审查意见修订重写，逐条修正不达标项，输出修订后的完整结论。

严格遵守 MANIFESTO 第十节回答公约：数据驱动（引用数值/区域 + [ref:区域名]）、结构清晰（问题定性 → 数据证据 → 结论建议）、4×5 表达、专业用语、结论有指向（城建问题 + 可落地建议）、精炼。

【审查意见】（六条中不达标/警告项 + 修正方向，须逐条对照修正）：
{review_hints}

【原草稿】（在此基础上改，不要推翻重写、保留正确部分）：
{draft}

【探索历史】（你历轮的 thought/action/工具观察）：
{tool_history}

当前数据：
{context}

输出修订后的完整结论（markdown + [ref:区域名]），不要解释"我改了什么"、不要前后缀解释。
"""


def build_revise_prompt(draft: str = '', review_hints: str = '', context: str = '',
                        tool_history: str = '', context_tokens: list = None) -> str:
    """revise 阶段：基于 draft + review_hints 重写（流式 markdown）。"""
    ctx = context or '（未提供数据上下文）'
    hist = tool_history or '（无探索历史）'
    prompt = MANIFESTO + REVISE_TEMPLATE.format(
        review_hints=review_hints or '（无具体意见，请按六条公约全面检查并改写）',
        draft=draft or '（空）',
        tool_history=hist,
        context=ctx,
    )
    return _inject_tokens(prompt, context_tokens)
