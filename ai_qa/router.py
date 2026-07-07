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
from ai_qa.prompts import build_agent_prompt, build_final_prompt

router = APIRouter()


@router.post("/chat")
async def chat_route(req: ChatRequest):
    """AI 问答 agent loop（agent_step/answer 都走 SSE 流式）。"""
    from ai_qa.llm import LLMClient, LLMError

    if req.phase == 'answer':
        sys_content = build_final_prompt(req.context or '', req.tool_history or '', req.context_tokens)
    else:   # agent_step
        sys_content = build_agent_prompt(
            req.context or '', req.tool_history or '', req.round_n or 1, req.context_tokens)

    messages = [{'role': 'system', 'content': sys_content}] + list(req.messages or [])
    try:
        cli = LLMClient(model=req.model) if req.model else LLMClient()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'LLM 客户端初始化失败: {e}')

    def gen():
        try:
            for kind, tok in cli.chat(messages, stream=True, with_reason=True, json_mode=False):
                key = 'reason' if kind == 'reason' else 'token'
                yield f'data: {json.dumps({key: tok}, ensure_ascii=False)}\n\n'
            yield 'data: [DONE]\n\n'
        except LLMError as e:
            yield f'data: {json.dumps({"error": str(e)}, ensure_ascii=False)}\n\n'
        except Exception as e:
            yield f'data: {json.dumps({"error": f"问答失败: {e}"}, ensure_ascii=False)}\n\n'

    return StreamingResponse(gen(), media_type='text/event-stream')
