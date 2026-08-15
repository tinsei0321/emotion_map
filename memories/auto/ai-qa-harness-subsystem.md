---
name: ai-qa-harness-subsystem
description: AI 问答独立子架构 ai_qa/ + Agent Loop（ReAct）+ MANIFESTO 强化；承重约定
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 03435b43-e0c8-47cb-bf2f-ca852a5616b8
---

AI 问答独立子系统（`ai_qa/` 后端 + `frontend/js/ai_qa/` 前端）。设计圣经 `docs/ai-qa-design.md`。

**演进**：B1 萌芽骨架(5.31) → 四层线性 Harness(5.33, think→execute→answer→review) → **Agent Loop 重构(5.34, Claude Code 式 ReAct)** → **审查层接回(5.35)**。线性管线实测"思考是块状结果非动态过程 + 回答不可用"，故重构为 agent loop；5.34 暂移审查层，5.35 把 review.py 六条 checklist 接回 ReAct 管线（草稿→Flash 审查→不达标 revise 重写 1 轮）。

**Agent Loop（ReAct，当前）**：每轮 DeepSeek reasoner 输出 `{thought, action}`——reasoning_content **实时流式**（动态思考）+ thought（可见）+ action（tool/answer）。模型**自主**调工具（query_layers/query_zone_stats/query_attribution/query_keywords/ensure_zone/focus_zones/open_attribution/inspect_zone/answer），工具结果回喂 tool_history，多轮（上限8）直到 answer。前端 `harness.js orchestrate` = while loop；`stages.js agentStep/finalStep`；`tools.js TOOLS` 直调主窗口。

**MANIFESTO（ai_qa/manifesto.py）强化**：概念/数据流/4×5/逻辑闭环 + 三页架构当前焦点 + **7 大应用场景**（更新排序/微更新/城市体检/营商/活动评估/12345预警/生活圈）+ 演示逻辑链 + **回答策略 SOP**（判断问题类型→先query摸数据→数据驱动→指向城建问题）+ 工具使用指导。

**承重约定（勿破坏）**：
- **Agent loop ReAct**：模型自主调工具循环（不预设 plan）；`harness.js STAGES` 不可退回线性。
- **reasoning 实时流**：agent_step/answer 都 `with_reason=True` + `json_mode=False`（json_mode 抑制 reasoning）；思考过程靠 reasoning 连续流（动态），非块状。
- **tool_history 回喂**：每轮探索（thought+action+observation）入 tool_history，下轮 prompt 让模型看到历轮。
- **panel 直调主窗口**（5.34 还原单窗口）：panel.js/tools.js import map/state/panel/grid-tool（非跨窗口协议）；[ref:] 点击 → `TOOLS.focus_zones`。
- **localStorage 历史**：`ai_qa_history_v1` 键，panel 打开 restoreHistory。
- **V4 模型 ID 承重（曾咬一次）**：必须用 `deepseek-v4-pro`/`deepseek-v4-flash`（旧 `deepseek-reasoner`/`deepseek-chat` 2026-07-24 退役，过渡期映射到 flash 后端——曾致"key 支持 v4-pro 却实际跑 flash、质量崩"）。`llm.py _resolve_model` 别名映射（pro/flash/旧ID→V4），默认 v4-pro。**勿回旧 ID**。
- **思考深度开关**：panel 顶 Pro/Flash segmented（localStorage `ai_qa_think_mode`，默认 pro）；前端发逻辑名，后端 _resolve_model 映射。动态思考状态（轮换"正在思考/分析/计算/构思…"，随机感 + 跳动点）。
- **审查层接通（5.35）**：`review.py review_answer()` Flash+json_mode 六条 checklist 打分（✓/△/✕），`_parse_review_json` 容错（fence/尾逗号/缺 key 补全/verdict 归一/fail 强制 pass=False），失败降级 {pass:True,degraded:True} **不阻塞交付**；不达标带 revise_hints 自动 revise 重写 **1 轮不递归**。`router.py` review（非流式单帧 SSE {review:{...}}，Starlette threadpool 跑同步 gen）/revise（流式）分支；`schemas.py` phase 加 review/revise + draft/review_hints；`prompts.py` REVISE_TEMPLATE；前端 `stages.js reviewStep/reviseStep` + `harness.js` 接 finalStep→review→!pass→revise + `panel.js` 审查状态区。**REVIEW_CHECKLIST key 稳定勿改**（前端按 key 渲染）。
- **稳健性 + 体验（5.35）**：`parseAgentStep` 强化（strip fence/去尾逗号/正则二次提取 action）；解析失败**不再裸显 raw**，break loop 走 finalStep 回退一次性 answer；`[ref:区域名]` 校验存在性（`getValidRefNames` 从聚合层 features.name），臆造标 `.cite-chip-invalid` 灰显不可点；tool_history 压缩注入（params≤80/obs≤200）；Flash 模式 reason 区改"Flash·直接作答"不渲染 body（Flash 无 reasoning_content）；Pro reasoning 按轮分段折叠（`.aiq-reason-segment`，onReason 透传 round）非跨轮全堆。

旧 core/chat_context.py、core/llm_client.py、chat-panel.js、chat-orchestrator.js、chat-panel.css 已删（5.33）。5.34 待删：frontend/js/ai_qa/protocol.js、frontend/js/ai_qa_host.js、frontend/chat.html（跨窗口协议弃用）。**勿复活线性管线 / 跨窗口协议**。

关联 [[verify-with-webapp-testing-skill]]、[[view-data-conclusion-sync]]、[[maintain-revision-log]]。
