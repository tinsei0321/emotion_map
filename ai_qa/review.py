"""审查层 · REVIEW_CHECKLIST 六条 + review_answer() 审查执行。

Draft Answer 出稿后，审查员（默认 Flash，省 token、快）按六条 checklist 审查；
不达标（pass=False）带 revise_hints 让出稿模型重写（最多 1 轮，router 控制）。

六条来自用户对"最终回答质量"的硬要求：
排版易读 / 结构清晰 / 内容精炼 / 语句专业（规划行业用语）/ 数据驱动 / 结论有指向性。
"""
import os
import json
from typing import Optional, List

from ai_qa.llm import LLMError, chat_with_fallback, _tier_of
from ai_qa.manifesto import MANIFESTO

# 六条审查标准（顺序即审查顺序；key 稳定勿改，前端审查状态区按 key 渲染 ✓/△/✕）。
REVIEW_CHECKLIST = [
    {
        'key': 'layout',
        'name': '排版易读',
        'desc': '关键信息（数值、区域名、结论）是否凸显；是否分点/分段清晰、层次分明，便于快速抓重点。',
    },
    {
        'key': 'structure',
        'name': '图层优先结构',
        'desc': '是否有"产出图层 → 解题逻辑一句话 → 简短结论 → 可操作按钮"的结构（图层为主出口、文字为注脚）；而非纯文字报告流水账。',
    },
    {
        'key': 'concise',
        'name': '简短直接',
        'desc': '回答简短（结论 ≤ 几句，复杂问题才展开）；无废话、恭维、铺垫；信息密度高。**超长报告（啰嗦堆砌、为分析而分析）判 fail**。',
    },
    {
        'key': 'professional',
        'name': '通俗+专业',
        'desc': '专业词紧跟通俗解释（如"极性指数(=情绪正负评分)"）；语句简单清晰直接，**不写学术八股、不堆术语**；贴近用户能懂的表达。',
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
    {
        'key': 'scale_paradigm_fit',
        'name': '尺度范式匹配',
        'desc': '结论颗粒度是否匹配问题尺度（查 MANIFESTO 第十一节）——宏观禁落单点、微观禁泛泛、中观落单元级。**仅 emotion_analysis（复杂归因）查此项；简单问题 / 纯 GIS 操作（intent=B）不查**。',
    },
]

# 审查员模型：默认 Flash（checklist 式审查够用、省 token、快）；env REVIEWER_MODEL 覆盖（如切 Pro 审）。
# 别名经 llm._resolve_model 映射到 V4 真实 ID（'flash' → deepseek-v4-flash）。
REVIEWER_MODEL = os.environ.get('REVIEWER_MODEL', 'flash')


REVIEW_TEMPLATE = """
═══════════ 审查员任务 ═══════════
你是「宜昌市情绪地图」控制台回答审查员。按下列七条 checklist 审查助手草稿答案，输出严格 JSON。

【七条审查标准】（逐条评 verdict：pass=达标 / warn=小瑕疵 / fail=不达标）
{checklist}

【当前数据上下文】（grounding）
{context}

【探索历史】（助手历轮 thought/action/工具观察）
{tool_history}

【待审查草稿】
{draft}

【输出要求】
输出**严格 JSON 对象**（仅 JSON，禁 markdown 代码块 / 前后解释），结构如下：
{{
  "pass": true | false,
  "scores": [
    {{"key": "layout", "name": "排版易读", "verdict": "pass" | "warn" | "fail", "comment": "一句话说明问题或留空"}},
    {{"key": "structure", "name": "结构清晰", "verdict": "...", "comment": "..."}},
    {{"key": "concise", "name": "内容精炼", "verdict": "...", "comment": "..."}},
    {{"key": "professional", "name": "语句专业", "verdict": "...", "comment": "..."}},
    {{"key": "data_driven", "name": "数据驱动", "verdict": "...", "comment": "..."}},
    {{"key": "actionable", "name": "结论有指向性", "verdict": "...", "comment": "..."}},
    {{"key": "scale_paradigm_fit", "name": "尺度范式匹配", "verdict": "...", "comment": "..."}}
  ],
  "revise_hints": "pass=false 时必填：列出 fail/warn 项 + 具体可执行的修正方向（指出哪句哪段怎么改）；pass=true 可空字符串"
}}

【pass 判定】**客观质量项**（data_driven / actionable / scale_paradigm_fit / professional）任一 fail → pass=false；**主观项**（layout / concise / structure）只标 warn，**不轻易 fail**（排版/精炼是主观感受，不强制重写）。仅有 warn 可 pass=true。
【revise_hints 要求】pass=false 时必须具体可执行（如"第2段缺数值支撑，补极性指数与区域名"），而非泛泛"需改进"。
"""


def _build_review_prompt(draft: str, context: str, tool_history: str,
                         context_tokens: Optional[List[dict]] = None) -> str:
    """构造审查员 system prompt。

    前置 MANIFESTO（含第十一节尺度-方法-范式）——审查员需行业语境才能判准
    professional/actionable/scale_paradigm_fit；此前漏拼致判定偏松。
    """
    checklist_str = '\n'.join(
        f"- {c['key']}（{c['name']}）：{c['desc']}" for c in REVIEW_CHECKLIST
    )
    prompt = MANIFESTO + REVIEW_TEMPLATE.format(
        checklist=checklist_str,
        draft=draft or '（空）',
        context=context or '（未提供数据上下文）',
        tool_history=tool_history or '（无探索历史）',
    )
    if context_tokens:
        refs = '、'.join(
            f"{t.get('type', '对象')}:{t.get('label') or t.get('ref', {}).get('name') or '?'}"
            for t in context_tokens
        )
        prompt += '\n用户本次@关联的对象（审查时关注是否围绕它们展开）：' + refs
    return prompt


def _parse_review_json(raw: str) -> dict:
    """容错解析审查员 JSON 输出；失败降级 {pass:True, degraded:True}。"""
    if not raw or not raw.strip():
        return {'pass': True, 'degraded': True, 'degraded_reason': '审查员空输出'}
    s = raw.find('{')
    e = raw.rfind('}')
    if s < 0 or e < 0 or e <= s:
        return {'pass': True, 'degraded': True, 'degraded_reason': '审查员输出无 JSON'}
    candidate = raw[s:e + 1]
    obj = None
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError:
        try:
            cleaned = candidate.replace(',}', '}').replace(',]', ']')
            obj = json.loads(cleaned)
        except Exception:
            return {'pass': True, 'degraded': True, 'degraded_reason': '审查员 JSON 解析失败'}
    if not isinstance(obj, dict):
        return {'pass': True, 'degraded': True, 'degraded_reason': '审查员 JSON 非对象'}

    # 规范化 scores：补全缺失 key、verdict 归一
    raw_scores = obj.get('scores') or []
    by_key = {}
    if isinstance(raw_scores, list):
        for item in raw_scores:
            if not isinstance(item, dict):
                continue
            key = str(item.get('key') or '').strip()
            if not key:
                continue
            verdict = str(item.get('verdict', '')).lower().strip()
            if verdict not in ('pass', 'warn', 'fail'):
                verdict = 'warn'
            by_key[key] = {
                'key': key,
                'name': item.get('name', key),
                'verdict': verdict,
                'comment': str(item.get('comment', '') or ''),
            }
    for c in REVIEW_CHECKLIST:
        if c['key'] not in by_key:
            by_key[c['key']] = {'key': c['key'], 'name': c['name'], 'verdict': 'warn', 'comment': ''}
    scores = [by_key[c['key']] for c in REVIEW_CHECKLIST]

    pass_flag = bool(obj.get('pass', True))
    # 后端兜底：客观质量项 fail 才强制 pass=false；主观项(layout/concise/structure) fail 降为 warn（不强制重写）
    _OBJECTIVE = {'data_driven', 'actionable', 'scale_paradigm_fit', 'professional', 'concise'}
    for sc in scores:
        if sc['verdict'] == 'fail' and sc['key'] not in _OBJECTIVE:
            sc['verdict'] = 'warn'
    if any(sc['verdict'] == 'fail' for sc in scores):
        pass_flag = False

    return {
        'pass': pass_flag,
        'scores': scores,
        'revise_hints': str(obj.get('revise_hints', '') or ''),
    }


def review_answer(draft: str, context: str = '', tool_history: str = '',
                  context_tokens: Optional[List[dict]] = None) -> dict:
    """审查 draft，返回 {pass, scores, revise_hints, degraded?}。

    用 Flash + json_mode 拿结构化结果；初始化/调用/解析任一失败均降级
    {pass:True, degraded:True}（跳过审查，不阻塞交付）。
    """
    sys_prompt = _build_review_prompt(draft, context, tool_history, context_tokens)
    messages = [
        {'role': 'system', 'content': sys_prompt},
        {'role': 'user', 'content': '请审查上文草稿并输出 JSON。'},
    ]
    try:
        gen = chat_with_fallback(messages, tier=_tier_of(REVIEWER_MODEL), stream=False,
                                 json_mode=True, with_reason=False,
                                 temperature=0.2, max_tokens=1200)
        raw = next(gen)
    except LLMError as e:
        return {'pass': True, 'degraded': True, 'degraded_reason': str(e)}
    except Exception as e:
        return {'pass': True, 'degraded': True, 'degraded_reason': f'审查员异常: {e}'}

    result = _parse_review_json(raw)
    if result.get('degraded'):
        result['degraded_reason'] = result.get('degraded_reason') or '审查员输出解析失败'
    return result
