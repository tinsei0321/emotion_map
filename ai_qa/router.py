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
            '你是情绪地图分析助手。你有全部工具的自由选择权——不存在"预选工具"限制。从下方所有可用工具中选择最合适的一个。\n\n'
            '## 任务\n'
            '1. 从全部可用工具中选择**所有需要的工具**（tool_calls 数组）——如果用户请求需要多步完成（如"裁剪某区3类用地"=提取边界+3次叠置），请输出多个 tool_call，系统会自动顺序执行全部\n'
            '2. 在回复文本中输出 plans JSON（后续分析建议·可选）\n'
            '3. 在回复文本中输出 domain_lens（领域聚焦）\n\n'
            '## plans 格式\n'
            '在回复文本中输出如下 JSON（不要用 markdown 代码块）：\n'
            '{"plans":[{"rank":1,"label":"工具中文描述","tool":"工具名","params":{...},"confidence":"high|medium|low","rationale":"选择理由"},...]}\n\n'
            'rank=1 是当前 tool_call 执行的工具；rank=2+ 是后续可做的分析建议。\n\n'
            '**重要**：如果用户请求涉及多个步骤（如"剪裁出某区3类用地"=抽取边界+3次叠置+合并），**必须在 plans[] 中列出全部步骤**：\n'
            '- rank=1 填第一步的工具和参数\n'
            '- rank=2+ 填后续每一步（工具名+完整参数·引用第一步产出的图层名作为 layer_a）\n'
            '- plans 至少包含 2 项（rank=1 + 至少 1 个后续步骤）\n'
            '- 示例：用户说"裁剪西陵区商业+居住用地"→ plans: [{rank:1,tool:"extract_feature",params:{layer:"L001",where:"MC/in/西陵区",as:"西陵区范围"}}, {rank:2,tool:"overlay",params:{layer_a:"西陵区范围",layer_b:"L006",how:"intersection",as:"西陵区_商业"}}, {rank:3,tool:"overlay",params:{layer_a:"西陵区范围",layer_b:"L005",how:"intersection",as:"西陵区_居住"}}]\n\n'
            '## domain_lens\n'
            '在回复文本开头输出领域标签（选 0-2 个最匹配的）：\n'
            '[domain_lens:urban_planning] 或 [domain_lens:urban_renewal] 或 [domain_lens:urban_operation] 或 [domain_lens:urban_governance]\n'
            '判断依据：规划/用地→planning·更新/老旧/改造→renewal·运营/商圈/场馆→operation·治理/交通/停车→governance\n'
            '情绪分析类（极性/归因/排序）默认 urban_renewal。无明确领域则不输出。\n\n'
            '## 工具×数据兼容性\n'
            '选工具前先看下方「数据上下文」——确认数据类型匹配：\n'
            '- density/hotspot/rank/zonal_stats/compare_regions 需**情绪点层**（含 polarity/score 字段）\n'
            '- clip 需**点层 + 范围**（range）——**clip 仅用于裁剪点层**！面层面裁剪（如"某区内的某类用地"）必须用 overlay(how="intersection")，严禁用 clip 裁面层\n'
            '- extract_feature/overlay/merge/area_stats 需**面层**（polygon boundary）。overlay how="intersection" = 面∩面 = 空间裁剪面层的正确工具\n'
            '- buffer/nearest 需**点层 + 目标**（center/target）\n'
            '- **跨层合并多个面层**（如"合并商业+居住+公园三个图层"）：merge 只能处理单个图层内的要素·不能跨层合并。跨层合并用 overlay(how="union") 两两合并，或分别 overlay(intersection) 后 merge\n'
            '若数据不支撑所选工具，换一个合适的工具或说明缺什么数据。\n\n'
            '## 极性范围纪律（CB-09 P0-3·治意图缩窄 B006）\n'
            '- 用户说"情绪点"/"情绪分布"/"筛选情绪"等**未限定极性**的词 → 默认覆盖**全部三个极性**（积极+中性+消极）·**严禁自行缩窄**为单一极性（如"选数据最多的积极层先做"——这是错的，用户没有让你选）\n'
            '- 用户明确说了"积极"/"消极"/"中性" → 严格按指定极性操作·不扩展\n'
            '- 若三个极性是独立图层无法一次完成 → 先 merge 三个极性层再操作·或诚实告知用户并给出选项\n\n'
            '## 参数填写纪律\n'
            '- where/pre_filter 的 field **必须用「数据上下文」中列出的实际字段名**（非训练数据假设的 MC/name 等）\n'
            '- layer 参数**必须用「数据上下文」中 id:xxx 标注的值**（如 yichang_l2_t3）·非拼凑层名\n'
            '- **必填槽必须从问句抽出填入 tool_call·勿留空**（留空会被拦下追问·拖慢且打断分析）\n'
            '- **信息不足时直接说明缺什么/列出「数据上下文」所见·勿反复推理猜测**（会耗尽 token 致错误结论·如把已上传数据说成"没上传"）\n\n'
            '## 多要素提取（Hotfix R3·治"裁剪西陵+伍家岗"死循环）\n'
            '从面层提取多个要素（如"西陵区+伍家岗区""A 和 B"）：**用 where="字段/in/值1,值2" 一次提取**（in 操作符 + 逗号分隔多值）。\n'
            '示例：where="MC/in/西陵区,伍家岗区" → 一次抽出两区。**勿纠结"extract 只能单要素→要 extract×2+merge"**——in 多值一次搞定·勿进多步链死循环。\n\n'
            '## 参数提取示例（WS3 F3.1·治 buffer/overlay/compare 缺必填槽）\n'
            '- 「以X为中心周边500米」「X 附近 Y 米」→ buffer: center="X"(地名/POI), radius_m=Y\n'
            '- 「A 与 B 的情绪对比」「比较 A 和 B」→ compare_regions: boundaries=["A","B"]（≥2 个·必须数组·从问句两个地名抽·勿填单数 boundary）\n'
            '- 「A 与 B 的交集」「A ∩ B」→ overlay: layer_a="A", layer_b="B", how="intersection"\n'
            '- 「某区内某类用地」（如"西陵区内的商业用地"）→ 面∩面空间裁剪，用 overlay(layer_a=区面层, layer_b=用地面层, how="intersection")。**注意**：这是两个不同图层的空间相交，不是从一个图层里抽要素——严禁用 extract_feature！extract_feature 只在「从同一个图层里按属性抽子集」（如"从行政区划里抽西陵区"）时使用\n'
            '- 「裁剪/提取 A 和 B」「裁出西陵+伍家岗」→ 从**单个**行政区划面层中按属性抽要素：extract_feature: layer=面层, where="name字段/in/A,B"（多要素用 in·勿拆多步链）。**注意**：仅当 A 和 B 在**同一个图层**内时才用 extract_feature！如果 A 和 B 是**两个独立图层**（如"西陵区范围"和"用地_商业"），必须用 overlay(intersection)\n\n'
            '## 追问场景指引\n'
            '- 追问「分析消极/积极/中性情绪」→ 直接用 density 切换 polarity（negative/positive/neutral）·不要先 filter_attr 再 density（多余步骤）\n'
            '- 追问「换个极性看看」→ 同一工具换 polarity 参数即可·无需换工具\n\n'
            '## 推理风格\n'
            '推理过程（thinking）用生动、口语、拟人的表达，像跟同事边想边讲思路——可以带点语气词和转折的节奏感，避免"因为/所以/另外/但是"的僵硬八股。但工具选择、参数填写、字段引用仍须严谨准确（风格服务于可读，不牺牲正确性）。\n\n'
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
