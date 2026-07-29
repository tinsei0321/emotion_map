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
        from ai_qa.tool_contracts import contracts_to_tools_schema, validate_tool_call
        tools = contracts_to_tools_schema()
        _q = (req.messages or [{}])[-1].get('content', '') if req.messages else ''
        # v3 C2：system prompt 含「数据×工具兼容性」提示（让 LLM 避开数据不支撑的工具）
        # v3 C3：system prompt 含 domain_lens 产出指令（A+B 混合的 A 部·LLM 自主判领域）
        sys_content = (
            '你是情绪地图分析助手。根据用户请求选择最合适的工具。\n'
            '- 用户说"裁剪/剪裁"面层（用地、行政区等）→ 用 overlay(intersection)。clip 仅用于点数据，对面层返回空\n'
            '- 多步骤请求（如裁剪多类用地）→ 先做第一步，系统自动补全后续\n'
            '- 参数用数据上下文中的实际字段名和图层 ID\n'
            f'## 数据上下文\n{req.context or "（无数据上下文）"}\n'
        )
        messages = [{'role': 'system', 'content': sys_content}] + list(req.messages or [])
        # Hotfix R2 S7：FC 流式（SSE）——诊断思考渐进可见（yield reason → 前端 onReason 实时渲染）。
        # 替代旧 JSONResponse（非流式·用户感"卡住"）。实测 V4 flash FC stream 吐 17 reason + 11 tool_call delta。
        import json as _json
        from ai_qa.llm import chat_with_tools_stream_fallback

        def _fc_gen():
            try:
                for kind, tok in chat_with_tools_stream_fallback(messages, tools, tier='flash'):
                    if kind == 'reason':
                        yield f'data: {_json.dumps({"reason": tok}, ensure_ascii=False)}\n\n'   # 渐进思考
                    elif kind == 'done':
                        result = tok
                        tc = (result.get('tool_calls') or [{}])[0]
                        _fixes = []
                        if tc and tc.get('function'):   # v3 H6：后端 validate_tool_call 兜底（D062）
                            try:
                                _args = _json.loads(tc['function'].get('arguments', '{}'))
                                _v = validate_tool_call(tc['function']['name'], _args)
                                if _v['fixes']:
                                    tc['function']['arguments'] = _json.dumps(_v['params'], ensure_ascii=False)
                                    _fixes = _v['fixes']
                            except Exception:
                                pass   # validate 失败不阻塞·tool_calls 原样回
                        # CB-09：如果 LLM 没输出 content（plans 为空），从 tool_calls 自建最小 plan
                        _plans = result.get('content')
                        if not _plans and tc and tc.get('function'):
                            try:
                                _name = tc['function']['name']
                                _args = _json.loads(tc['function'].get('arguments', '{}'))
                                _plans = _json.dumps({"plans": [{"rank": 1, "label": _name, "tool": _name, "params": _args, "confidence": "high", "rationale": "auto-from-tool-call"}]}, ensure_ascii=False)
                            except Exception:
                                _plans = result.get('content')
                        yield f'data: {_json.dumps({"tool_calls": result.get("tool_calls"), "plans": _plans, "usage": result.get("usage"), "fixes": _fixes}, ensure_ascii=False)}\n\n'
                yield 'data: [DONE]\n\n'
            except LLMError as e:
                yield f'data: {_json.dumps({"error": str(e)}, ensure_ascii=False)}\n\n'
            except (KeyboardInterrupt, SystemExit):
                raise   # CB-05 CR2：不吞系统退出信号
            except Exception as e:
                yield f'data: {_json.dumps({"error": f"FC 诊断失败: {e}"}, ensure_ascii=False)}\n\n'

        return StreamingResponse(_fc_gen(), media_type='text/event-stream')

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
