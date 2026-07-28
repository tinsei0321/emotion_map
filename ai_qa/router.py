"""AI 问答路由 /chat（挂载到 api/main.py，prefix=/api/v1 → /api/v1/chat）。

两阶段（ReAct agent loop）：
- agent_step → SSE 流式：Pro(reasoner) reasoning_content(思考链) + content(JSON {thought,action})。
- answer     → SSE 流式：Pro reasoning + content(最终结论 markdown + [ref:])。

不用 json_mode（抑制 reasoning）；靠 prompt 强约束 + 前端 parseAgentStep 容错解析。
SSE 帧：{"token": tok}=正文 / {"reason": tok}=思考链 / {"error": ...} / [DONE]。

v2（5.243）：fc_diagnose phase → function calling 非流式 JSON 响应（替代旧 diagnose SSE）。
"""
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from ai_qa.schemas import ChatRequest
from ai_qa.prompts import (
    build_agent_prompt, build_final_prompt, build_diagnose_prompt, build_optimize_prompt,
    build_diagnose_prompt_dispatch,
)

router = APIRouter()


@router.post("/chat")
async def chat_route(req: ChatRequest):
    """AI 问答 agent loop（diagnose/agent_step/answer/optimize 走 SSE 流式；fc_diagnose 走 JSON）。"""
    from ai_qa.llm import LLMError, chat_with_fallback, chat_with_tools_fallback, _tier_of, LLMClient

    # ═══ v2/v3 function calling diagnose（5.243·D041·v3 C1/C2/C3 修复）═══
    # 非流式 JSON 响应——FC 2-3s 一次返完整 tool_calls + plans[]
    if req.phase == 'fc_diagnose':
        from ai_qa.tool_contracts import contracts_to_tools_schema
        tools = contracts_to_tools_schema()
        _q = (req.messages or [{}])[-1].get('content', '') if req.messages else ''
        # v3 C2：system prompt 含「数据×工具兼容性」提示（让 LLM 避开数据不支撑的工具）
        # v3 C3：system prompt 含 domain_lens 产出指令（A+B 混合的 A 部·LLM 自主判领域）
        sys_content = (
            '你是情绪地图分析助手。根据用户问题选择一个工具并填写参数。\n\n'
            '## 任务\n'
            '1. 从可用工具中选择最优先执行的一个（tool_call）\n'
            '2. 在回复文本中输出 plans JSON（后续分析建议）\n'
            '3. 在回复文本中输出 domain_lens（领域聚焦）\n\n'
            '## plans 格式\n'
            '在回复文本中输出如下 JSON（不要用 markdown 代码块）：\n'
            '{"plans":[{"rank":1,"label":"工具中文描述","tool":"工具名","params":{...},"confidence":"high|medium|low","rationale":"选择理由"},...]}\n\n'
            'rank=1 是当前 tool_call 执行的工具；rank=2+ 是后续可做的分析建议。\n\n'
            '## domain_lens\n'
            '在回复文本开头输出领域标签（选 0-2 个最匹配的）：\n'
            '[domain_lens:urban_planning] 或 [domain_lens:urban_renewal] 或 [domain_lens:urban_operation] 或 [domain_lens:urban_governance]\n'
            '判断依据：规划/用地→planning·更新/老旧/改造→renewal·运营/商圈/场馆→operation·治理/交通/停车→governance\n'
            '情绪分析类（极性/归因/排序）默认 urban_renewal。无明确领域则不输出。\n\n'
            '## 工具×数据兼容性\n'
            '选工具前先看下方「数据上下文」——确认数据类型匹配：\n'
            '- density/hotspot/rank/zonal_stats/compare_regions 需**情绪点层**（含 polarity/score 字段）\n'
            '- clip 需**点层 + 范围**（range）\n'
            '- extract_feature/overlay/merge/area_stats 需**面层**（polygon boundary）\n'
            '- buffer/nearest 需**点层 + 目标**（center/target）\n'
            '若数据不支撑所选工具，换一个合适的工具或说明缺什么数据。\n\n'
            '## 参数填写纪律\n'
            '- where/pre_filter 的 field **必须用「数据上下文」中列出的实际字段名**（非训练数据假设的 MC/name 等）\n'
            '- layer 参数**必须用「数据上下文」中 id:xxx 标注的值**（如 yichang_l2_t3）·非拼凑层名\n'
            '- **必填槽必须从问句抽出填入 tool_call·勿留空**（留空会被拦下追问·拖慢且打断分析）\n\n'
            '## 参数提取示例（WS3 F3.1·治 buffer/overlay/compare 缺必填槽）\n'
            '- 「以X为中心周边500米」「X 附近 Y 米」→ buffer: center="X"(地名/POI), radius_m=Y\n'
            '- 「A 与 B 的情绪对比」「比较 A 和 B」→ compare_regions: boundaries=["A","B"]（≥2 个·必须数组·从问句两个地名抽·勿填单数 boundary）\n'
            '- 「A 与 B 的交集」「A ∩ B」→ overlay: layer_a="A", layer_b="B", how="intersection"\n'
            '- 「某区内某类用地」→ extract_feature: layer=区面层(preset_id), where={field/op/value}\n\n'
            '## 追问场景指引\n'
            '- 追问「分析消极/积极/中性情绪」→ 直接用 density 切换 polarity（negative/positive/neutral）·不要先 filter_attr 再 density（多余步骤）\n'
            '- 追问「换个极性看看」→ 同一工具换 polarity 参数即可·无需换工具\n\n'
            f'## 数据上下文\n{req.context or "（无数据上下文）"}\n'
        )
        messages = [{'role': 'system', 'content': sys_content}] + list(req.messages or [])
        try:
            # v3 C1 修复：走 provider fallback（DeepSeek→Ark→讯飞·非单点 LLMClient）
            result = chat_with_tools_fallback(messages, tools, tier='flash')
            # v3 H6 修复：后端调 validate_tool_call（D062·strict 不强制→代码兜底）·前端信赖后端不重复校验
            from ai_qa.tool_contracts import validate_tool_call
            tc = (result.get('tool_calls') or [{}])[0]
            if tc and tc.get('function'):
                import json as _json
                _args = _json.loads(tc['function'].get('arguments', '{}'))
                _v = validate_tool_call(tc['function']['name'], _args)
                if _v['fixes']:
                    tc['function']['arguments'] = _json.dumps(_v['params'], ensure_ascii=False)
                    result.setdefault('_fc_fixes', _v['fixes'])   # 供前端日志
            return JSONResponse({
                'tool_calls': result.get('tool_calls'),
                'plans': result.get('content'),
                'usage': result.get('usage'),
                'fixes': result.get('_fc_fixes', []),   # v3.1 BR2：传回参数修正日志（供前端可观测）
            })
        except LLMError as e:
            return JSONResponse({'error': str(e), 'tool_calls': None, 'plans': None}, status_code=502)
        except (KeyboardInterrupt, SystemExit):
            raise   # CB-05 CR2：不吞系统退出信号
        except Exception as e:
            return JSONResponse({'error': f'FC 诊断失败: {e}', 'tool_calls': None, 'plans': None}, status_code=502)

    # ═══ 旧 SSE phases（diagnose/agent_step/answer/optimize）═══
    # CB-09 D022：删旧 review/revise 阶段（LLM 审查+重写）→ 前端 harness.applyQualityDefense 代码防线取代。
    if req.phase == 'answer':
        sys_content = build_final_prompt(req.context or '', req.tool_history or '', req.context_tokens, req.domain_lens)
    elif req.phase == 'diagnose':
        # 问题诊断（专业认知前置步）：流式 reason + content JSON 卡（不用 json_mode，同 agent_step）
        # CB-09 D006（5.236）Phase B：select_candidates 预选 → 单/少候选走极瘦填卡（<3.5KB·<5s）
        # CB-09 D009+D012（5.237）Phase C：复合 → Pro 计划（产 chain·<5KB·5-10s）·0 候选走大 prompt 兜底
        _q = (req.messages or [{}])[-1].get('content', '') if req.messages else ''
        sys_content, _diag_path, _diag_model = build_diagnose_prompt_dispatch(_q, req.context or '', req.context_tokens, req.layer_meta)
        if _diag_model:
            req.model = _diag_model   # 复合 → pro（下方 tier=_tier_of(req.model) 在分支后算·自动生效）
    elif req.phase == 'optimize':
        # Prompt 优化（5.215）：Flash 把用户 NL 优化成具体/实操/逻辑清晰 prompt（不增维度·梳理已有要素）
        _ui = (req.messages or [{}])[-1].get('content', '') if req.messages else ''
        sys_content = build_optimize_prompt(req.context or '', _ui)
    else:   # agent_step
        sys_content = build_agent_prompt(
            req.context or '', req.tool_history or '', req.round_n or 1, req.context_tokens, req.domain_lens)

    messages = [{'role': 'system', 'content': sys_content}] + list(req.messages or [])
    tier = _tier_of(req.model)

    def gen():
        try:
            for kind, tok in chat_with_fallback(messages, tier=tier, stream=True, with_reason=True, json_mode=False):
                if kind == 'usage':
                    yield f'data: {json.dumps({"usage": tok}, ensure_ascii=False)}\n\n'
                else:
                    key = 'reason' if kind == 'reason' else 'token'
                    yield f'data: {json.dumps({key: tok}, ensure_ascii=False)}\n\n'
            yield 'data: [DONE]\n\n'
        except LLMError as e:
            yield f'data: {json.dumps({"error": str(e)}, ensure_ascii=False)}\n\n'
        except Exception as e:
            yield f'data: {json.dumps({"error": f"问答失败: {e}"}, ensure_ascii=False)}\n\n'

    return StreamingResponse(gen(), media_type='text/event-stream')
