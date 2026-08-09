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


def build_fc_sys_prompt(context):
    """FC 诊断 system prompt（单一构造·可测试断言·防 0073990 式"简化"再次静默删除）。

    只含当前有效的纪律段：工具规则（契约 when 已上游承担）+ 极性范围纪律（B006·31e2a00 恢复）。
    plans/domain_lens/多要素提取指令不再内嵌——已被 _allToolCalls/autoExpand/契约 when 取代，
    恢复会回退旧诊断卡行为（0073990 删除原因）。← CB-10
    """
    return (
        '你是情绪地图分析助手。根据用户请求选择最合适的工具。\n'
        '- 用户说"裁剪/剪裁"面层（用地、行政区等）→ 用 overlay(intersection)。clip 仅用于点数据，对面层返回空\n'
        '- 多步骤请求（如裁剪多类用地）→ 先做第一步，系统自动补全后续\n'
        '- 参数用数据上下文中的实际字段名和图层 ID\n'
        '## 尺度判定（G1·填入诊断卡 scale 字段·防"一竿子插到底"同构结论）\n'
        '- 用户问"分布情况/整体趋势/大致哪里/覆盖"→ macro（宏观分布·粗粒度·不到归因）\n'
        '- 用户问"哪里最差/哪个区域/为什么/原因/归因/排序"→ meso（中微观·细粒度·要归因）\n'
        '- 用户问"这条街/这个点/这个小区/哪个点位/公园里"→ micro（微观落点）\n'
        '- 出口须随尺度差异化：宏观=结构性分布结论（禁归因词）·中微观=单元归因+排序·微观=落点定位。纯 GIS 操作不判 scale\n'
        '## 诊断卡标签（填入 content·系统解析 A 部）\n'
        '- 输出 [domain_lens:urban_planning|urban_renewal|urban_operation|urban_governance]（可多·判定问题领域）\n'
        '- 输出 [scale:macro|meso|micro]（情绪分析时按上方尺度判定）\n'
        '## 极性范围纪律（CB-09 P0-3·治意图缩窄 B006）\n'
        '- 用户说"情绪点"/"情绪分布"/"筛选情绪"等**未限定极性**的词 → 默认覆盖**全部三个极性**（积极+中性+消极）·**严禁自行缩窄**为单一极性（如"选数据最多的积极层先做"——这是错的，用户没有让你选）\n'
        '- 用户明确说了"积极"/"消极"/"中性" → 严格按指定极性操作·不扩展\n'
        '- 若三个极性是独立图层无法一次完成 → 先 merge 三个极性层再操作·或诚实告知用户并给出选项\n'
        f'## 数据上下文\n{context or "（无数据上下文）"}\n'
    )


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
        sys_content = build_fc_sys_prompt(req.context)
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
