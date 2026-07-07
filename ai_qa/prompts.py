"""思考层 · 三阶段 SOP prompt builder。

每个阶段 = MANIFESTO（知识层前缀）+ 阶段指令 + 数据。阶段：
- think  ：规划解题路径，输出 {framing, mapping, steps[]} JSON（JSON mode）。
- answer ：基于执行观察出结论（流式 markdown + [ref:]）；可带 review_feedback 修订。
- review ：审查 draft_answer（Flash，json_mode → {pass, checks[], revise_hints}）。

改 prompt 只改本文件（思考层独立，可扩展性设计）。
"""
from ai_qa.manifesto import MANIFESTO
from ai_qa.review import REVIEW_CHECKLIST


def _inject_tokens(prompt, context_tokens):
    """@关联对象 → 追加"回答/操作须围绕它们"约束（think/answer 共用）。"""
    if not context_tokens:
        return prompt
    refs = []
    for t in context_tokens:
        typ = t.get('type', '对象')
        label = t.get('label') or t.get('ref', {}).get('name') or '?'
        refs.append(f'{typ}:{label}')
    return prompt + '\n用户本次@关联的对象（回答/操作须围绕它们展开）：' + '、'.join(refs)


# ── think 阶段：规划解题路径 JSON ─────────────────────────────────────────────
THINK_TEMPLATE = """

═══════════ 本次任务 · 规划解题路径（THINK 阶段）═══════════
用户用自然语言提问。你要规划一个**端到端的执行计划**，让前端编排器自动操作地图、得出结论。

你必须输出**严格的 JSON 对象**（仅 JSON，禁止 markdown 代码块 / 前后解释文字），结构如下：
{{
  "framing": "问题定性：这个问题落在数据流闭环的哪一环（极性评价 / 归因分析 / 空间定位 / 关键词挖掘 / 更新建议 / 概念定义），1-2 句，面向用户口语化。",
  "mapping": "框架映射：回答它需要走数据流的哪几段（范围? 点? 聚合域? 极性? 4×5归因? 关键词? 落图建议?），并简述依据。",
  "steps": [
    {{"id": "s1", "tool": "工具名", "label": "步骤显示名", "params": {{...}}}},
    {{"id": "s2", "tool": "...", "label": "...", "params": {{...}}}}
  ]
}}

【可用 tool】（steps[].tool 只能取以下值之一，params 仅列出的键）：
- ensure_zone：确保有聚合域（无则按问题选标准/指定单元生成；有则复用，是后续定位/归因的数据基础）。
  params: {{"analysis": "square" | "zonal"（默认 square）, "cell_size": 米（square 默认 500）, "polarity": "overall", "mode": "2d" | "3d"（默认 2d）}}
- rank_zones：在聚合域里按维度排序找区域并定位（地图飞到 + 高亮）。
  params: {{"criteria": "worst" | "best" | "domain:规划" | "domain:更新" | "domain:运营" | "domain:治理" | "element:设施" | "element:环境" | "element:服务" | "element:文化" | "element:事件" | "keyword"（默认 worst）, "top": 个数（默认 3）}}
- open_attribution：展开 Overview 归因面板（4×5 矩阵 + 关键词）。params: {{}}
- inspect_zone：深读某聚合域的极性/归因/关键词明细。params: {{"name": "区域名"}}
- conclude：触发最终结论生成（**必须**作为 steps 的最后一个步骤）。params: {{}}

【规划规则】
1. 步骤要"端到端"覆盖用户问题：典型链 = （若无聚合域）ensure_zone → rank_zones → open_attribution → conclude。
2. 看"当前数据"判断起点：
   - 若已含"当前分析层：xxx（N 个聚合单元）"→ **跳过 ensure_zone**，直接 rank_zones。
   - 若为"暂无聚合层"但有点层 → 先 ensure_zone。
   - 若完全无点层数据 → 仍按问题意图给 steps，但 framing 注明数据不足（编排器会降级处理）。
3. steps 必须以 {{"tool":"conclude"}} 结尾；纯定义类问题（如"什么是情绪地图"）可只给 conclude。
4. 仅用上述 tool 名与合法 params 键值，**禁止臆造区域名**（区域由 rank_zones 按数据动态找，不在 plan 里写死）。
5. framing/mapping 要口语化、面向用户、对齐情绪地图框架（"我先聚合数据，再找出情绪最差的区域，然后分析其归因"），不要提 JSON/tool 字眼。

示例（用户问"哪些区域情绪最差？为什么？"，当前无聚合层）：
{{"framing":"这是极性评价 + 归因问题——先找出情绪最差的区域，再分析其背后的治理要素归因。","mapping":"需走数据流的：聚合域 → 极性评价（找最差）→ 4×5 归因（为什么差）→ 落图建议。","steps":[{{"id":"s1","tool":"ensure_zone","label":"生成综合聚合层","params":{{"analysis":"square","cell_size":500,"polarity":"overall","mode":"2d"}}}},{{"id":"s2","tool":"rank_zones","label":"定位情绪最差区域","params":{{"criteria":"worst","top":3}}}},{{"id":"s3","tool":"open_attribution","label":"展开归因分析","params":{{}}}},{{"id":"s4","tool":"conclude","label":"输出结论与建议","params":{{}}}}]}}

当前数据：
{context}
"""


def build_think_prompt(context: str = '', context_tokens: list = None) -> str:
    """think 阶段：教 LLM 输出 {framing, mapping, steps[]} JSON。"""
    ctx = context or '（未提供数据上下文——按问题意图给计划，framing 注明数据可能不足）'
    prompt = MANIFESTO + THINK_TEMPLATE.format(context=ctx)
    return _inject_tokens(prompt, context_tokens)


# ── answer 阶段：基于执行观察出结论 ───────────────────────────────────────────
ANSWER_TEMPLATE = """

═══════════ 本次任务 · 出结论（ANSWER 阶段）═══════════
前端编排器已按计划执行了若干操作（生成聚合域 / 定位区域 / 展开归因），下方"执行观察"是它逐步收集的真实数据。请基于执行观察回答用户问题。
{revise_block}

严格遵守 MANIFESTO 第六节回答公约（数据驱动 / [ref:] / 结构清晰 / 4×5 / 专业用语 / 结论有指向 / 精炼）。

当前数据：
{context}

执行观察（前端编排器逐步收集）：
{observation}
"""

ANSWER_REVISE_BLOCK = """
**注意：上一稿未通过审查层审查，审查意见如下，请据此修订重写（保持结论指向性，补足不达标项）：**
{review_feedback}
"""


def build_answer_prompt(context: str = '', observation: str = '', context_tokens: list = None,
                        review_feedback: str = '') -> str:
    """answer 阶段：基于执行观察出结论（流式 markdown + [ref:]）；可带审查意见修订。"""
    ctx = context or '（未提供数据上下文）'
    obs = observation or '（无执行观察——按当前数据作答）'
    revise_block = ANSWER_REVISE_BLOCK.format(review_feedback=review_feedback) if review_feedback else ''
    prompt = MANIFESTO + ANSWER_TEMPLATE.format(revise_block=revise_block, context=ctx, observation=obs)
    return _inject_tokens(prompt, context_tokens)


# ── review 阶段：审查 draft_answer ────────────────────────────────────────────
def _checklist_text() -> str:
    """六条 checklist 文字（review prompt 内嵌）。"""
    lines = []
    for i, c in enumerate(REVIEW_CHECKLIST, 1):
        lines.append(f"{i}. {c['name']}（{c['key']}）：{c['desc']}")
    return '\n'.join(lines)


REVIEW_TEMPLATE = """

═══════════ 本次任务 · 审查（REVIEW 阶段）═══════════
你现在的角色是**审查员**（与出稿角色切割）。下方"待审初稿"是出稿模型对用户问题的回答。
按下方六条 checklist **严格审查**，判定是否达标。

【六条 checklist】
{checklist}

你必须输出**严格的 JSON 对象**（仅 JSON，禁止 markdown 代码块 / 前后解释文字），结构如下：
{{
  "pass": true 或 false,
  "checks": [
    {{"key": "layout", "name": "排版易读", "pass": true 或 false, "note": "具体问题（若 pass=false 必填）"}},
    ...（六条全列，顺序同上）
  ],
  "revise_hints": "若 pass=false，给可操作的修订要点（逐条对应不达标项，出稿模型据此重写）；pass=true 则为空字符串"
}}

【判定标准】
- 六条 checks 全部 pass=true 时，整体 pass 才为 true；任一条 false → pass=false 并在 revise_hints 给修订要点。
- **严苛审查**：默认倾向发现问题。初稿若确无显著缺陷（六条均达标）才判 pass=true。
- note 要具体、可操作（指出哪句哪段、缺什么），不要泛泛"不够好"。

用户问题：{question}

当前数据：
{context}

执行观察：
{observation}

待审初稿：
{draft_answer}
"""


def build_review_prompt(context: str = '', draft_answer: str = '', observation: str = '',
                        question: str = '') -> str:
    """review 阶段：审查员按六条 checklist 审查初稿（Flash，json_mode）。"""
    ctx = context or '（无）'
    obs = observation or '（无）'
    q = question or '（未提供）'
    draft = draft_answer or '（空初稿——直接判 pass=false，revise_hints 指出无内容）'
    prompt = MANIFESTO + REVIEW_TEMPLATE.format(
        checklist=_checklist_text(), question=q, context=ctx, observation=obs, draft_answer=draft,
    )
    return prompt
