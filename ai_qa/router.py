"""AI 问答路由 /chat（挂载到 api/main.py，prefix=/api/v1 → 总路径 /api/v1/chat）。

三阶段（req.phase）：
- think   → SSE 流式：Pro(reasoner) 的 reasoning_content(思考链, kind=reason) + content(JSON {framing,mapping,steps[]}, kind=token)。
             不用 json_mode（会抑制 reasoning_content）；靠 prompt 强约束 + 前端 parseThink 容错解析。
- answer  → SSE 流式：Pro 的 reasoning(可选) + content(结论 markdown + [ref:])。可带 review_feedback 修订。
- review  → 非流式 JSON：Flash(json_mode) → {pass, checks[], revise_hints}。前端 reviewChat 用 fetch.json()。

SSE 帧：{"token": tok}=正文增量 / {"reason": tok}=思考链(Pro) / {"error": ...} / [DONE]。
"""
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ai_qa.schemas import ChatRequest
from ai_qa.prompts import build_think_prompt, build_answer_prompt, build_review_prompt
from ai_qa.review import REVIEWER_MODEL

router = APIRouter()


def _parse_json_loose(raw: str) -> dict:
    """容错解析 JSON（取首个 {...} 到末个 ...}）。

    review 输出兜底：解析失败 → {pass:False, checks:[], revise_hints:指出解析失败}，
    让前端审查状态区能渲染（不至于卡住），并触发 revise。
    """
    if not raw:
        return {'pass': False, 'checks': [], 'revise_hints': '审查输出为空'}
    s = raw.find('{')
    e = raw.rfind('}')
    if s < 0 or e < 0 or e <= s:
        return {'pass': False, 'checks': [], 'revise_hints': '审查输出非 JSON：' + raw[:200]}
    try:
        obj = json.loads(raw[s:e + 1])
        if not isinstance(obj.get('checks'), list):
            obj['checks'] = []
        if 'pass' not in obj:
            obj['pass'] = False
        if 'revise_hints' not in obj:
            obj['revise_hints'] = ''
        return obj
    except Exception:
        return {'pass': False, 'checks': [], 'revise_hints': '审查输出解析失败：' + raw[:200]}


def _last_user_question(messages) -> str:
    """取最后一条 user 消息内容（review prompt 用作"用户问题"上下文）。"""
    for m in reversed(messages or []):
        if isinstance(m, dict) and m.get('role') == 'user':
            return m.get('content', '') or ''
    return ''


@router.post("/chat")
async def chat_route(req: ChatRequest):
    """AI 问答（think/answer 走 SSE 流式；review 走非流式 JSON）。"""
    from ai_qa.llm import LLMClient, LLMError

    observation = req.observation or req.execution_result or ''

    # ── review 阶段：非流式 JSON（Flash json_mode）──
    if req.phase == 'review':
        question = _last_user_question(req.messages)
        sys_msg = {'role': 'system', 'content': build_review_prompt(
            req.context or '', req.draft_answer or '', observation, question)}
        try:
            cli = LLMClient(model=REVIEWER_MODEL)
            full = ''
            for tok in cli.chat([sys_msg], stream=False, with_reason=False,
                                json_mode=True, temperature=0.1, max_tokens=1200):
                full = tok   # stream=False → yield 一次完整 content
            return _parse_json_loose(full)
        except LLMError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'审查失败: {e}')

    # ── think / answer 阶段：SSE 流式（Pro，带思考链）──
    if req.phase == 'think':
        sys_content = build_think_prompt(req.context or '', req.context_tokens)
    else:   # answer
        sys_content = build_answer_prompt(
            req.context or '', observation, req.context_tokens, req.review_feedback or '')

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
