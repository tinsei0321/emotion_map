"""AI 问答路由 /chat（挂载到 api/main.py，prefix=/api/v1 → /api/v1/chat）。

两阶段（ReAct agent loop）：
- agent_step → SSE 流式：Pro(reasoner) reasoning_content(思考链) + content(JSON {thought,action})。
- answer     → SSE 流式：Pro reasoning + content(最终结论 markdown + [ref:])。

不用 json_mode（抑制 reasoning）；靠 prompt 强约束 + 前端 parseAgentStep 容错解析。
SSE 帧：{"token": tok}=正文 / {"reason": tok}=思考链 / {"error": ...} / [DONE]。
"""
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ai_qa.schemas import ChatRequest
from ai_qa.prompts import (
    build_agent_prompt, build_final_prompt, build_diagnose_prompt, build_revise_prompt,
)

router = APIRouter()


@router.post("/chat")
async def chat_route(req: ChatRequest):
    """AI 问答 agent loop（agent_step/answer/revise 走 SSE 流式；review 非流式单帧）。"""
    from ai_qa.llm import LLMError, chat_with_fallback, _tier_of

    # review 阶段：非流式调 Flash 审查员，结果作单帧 SSE 返回（Starlette threadpool 跑同步 gen）
    if req.phase == 'review':
        from ai_qa.review import review_answer

        def gen_review():
            try:
                result = review_answer(
                    req.draft or '', req.context or '',
                    req.tool_history or '', req.context_tokens, req.domain_lens)
            except Exception as e:
                result = {'pass': True, 'degraded': True, 'degraded_reason': f'审查异常: {e}'}
            yield f'data: {json.dumps({"review": result}, ensure_ascii=False)}\n\n'
            yield 'data: [DONE]\n\n'

        return StreamingResponse(gen_review(), media_type='text/event-stream')

    if req.phase == 'revise':
        sys_content = build_revise_prompt(
            req.draft or '', req.review_hints or '',
            req.context or '', req.tool_history or '', req.context_tokens, req.domain_lens)
    elif req.phase == 'answer':
        sys_content = build_final_prompt(req.context or '', req.tool_history or '', req.context_tokens, req.domain_lens)
    elif req.phase == 'diagnose':
        # 问题诊断（专业认知前置步）：流式 reason + content JSON 卡（不用 json_mode，同 agent_step）
        sys_content = build_diagnose_prompt(req.context or '', req.context_tokens)
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
