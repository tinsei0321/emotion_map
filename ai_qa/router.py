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
    from ai_qa.llm import LLMError, chat_with_fallback, _tier_of, LLMClient

    # ═══ v2 function calling diagnose（5.243·D041）═══
    # 非流式 JSON 响应——FC 2-3s 一次返完整 tool_calls + plans[]
    if req.phase == 'fc_diagnose':
        from ai_qa.tool_contracts import contracts_to_tools_schema
        tools = contracts_to_tools_schema()
        # system prompt：极简——接地上下文 + 指令（无 MANIFESTO·无 industry_kb·D046）
        _q = (req.messages or [{}])[-1].get('content', '') if req.messages else ''
        sys_content = (
            '你是情绪地图分析助手。根据用户问题选择一个工具并填写参数。\n\n'
            '## 任务\n'
            '1. 从可用工具中选择最优先执行的一个（tool_call）\n'
            '2. 在回复文本中输出 plans JSON（后续分析建议）\n\n'
            '## plans 格式\n'
            '在回复文本中输出如下 JSON（不要用 markdown 代码块）：\n'
            '{"plans":[{"rank":1,"label":"工具中文描述","tool":"工具名","params":{...},"confidence":"high|medium|low","rationale":"选择理由"},...]}\n\n'
            'rank=1 是当前 tool_call 执行的工具；rank=2+ 是后续可做的分析建议。\n'
            '每个 plan 的 tool 必须是可用工具之一，params 必须符合该工具参数 schema。\n\n'
            f'## 数据上下文\n{req.context or "（无数据上下文）"}\n'
        )
        messages = [{'role': 'system', 'content': sys_content}] + list(req.messages or [])
        try:
            client = LLMClient(model='flash')   # FC 用 Flash（快·2-3s）
            result = client.chat_with_tools(messages, tools)
            return JSONResponse({
                'tool_calls': result.get('tool_calls'),
                'plans': result.get('content'),
                'usage': result.get('usage'),
            })
        except LLMError as e:
            return JSONResponse({'error': str(e), 'tool_calls': None, 'plans': None}, status_code=502)
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
