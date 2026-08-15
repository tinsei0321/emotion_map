---
name: smart-agent-dumb-tool
description: AI·Copilot 开发内核——聪明只在两端(理解+表达)，执行做最笨最稳中间件；新功能判据会推理→Smart/纯执行→Dumb/协调→编排器
metadata: 
  node_type: memory
  type: feedback
  originSessionId: de71ce91-41e0-4b33-ae62-ab9868fc457e
  modified: 2026-07-22T14:34:18.698Z
---

**Smart Agent, Dumb Tool** = AI·Copilot 开发内核（用户定 2026-07-22，已入 CLAUDE.md 顶层节 + docs/copilot-architecture.md）。一句话：聪明只放两端（理解+表达），执行做最笨最稳的中间件——灵活来自 Agent，稳定来自 Tool，编排器机械接线。

**三角色**：
- **Smart Agent**（意图理解 Agent + 结果输出 Agent）：LLM 驱动，负责"想"。EMC = diagnoseStep + finalStep/answer + Review。
- **Dumb Tool**（Skill/Toolbox 标准化工具组）：负责"做"、不思考（单一职责+参数契约+纯执行+制式产出）。EMC = SKILL_DEFS + TOOLS。
- **Orchestrator 编排器**：确定性翻译官+传菜员，**不调 LLM、不推理**，只接线（分流/派发/回收/裁定终态）。EMC = harness.orchestrate + 三态出口代码裁定。

**四铁律**：① Tool 越 dumb 越好（不内嵌 LLM 推理，一聪明就失稳）；② Agent 聪明只在两端（避免"边想边做"纯 ReAct 陷阱）；③ 编排器确定性（协调机械不智能，三态出口代码裁定非模型自觉）；④ 计划-执行分离（先 Smart 产 plan，后 Dumb 跑 tool 可 0 LLM 轮）。

**新功能判据（抗退化核心）**：会推理→Smart，纯执行→Dumb，协调→编排器。三者不清即"大杂烩 panel.js"坍塌信号。

**Why**：灵活+稳定兼得（灵活集中 Smart 两端、稳定集中 Dumb 中间）+ 可测（Dumb 单测/Smart eval）+ 可扩展（加能力=加 dumb tool+编排器登记）。
**How to apply**：写/改 Copilot 任何 Agent/Tool/编排时先对照内核判层；Tool 想内嵌推理→停下改走 Smart 或编排器；EMC 现状已是此内核成熟实现（CB 三轮+三态出口承重验证）**勿推倒重来**。关联 [[emc-delegates-to-toolbox]]（委托 Toolbox 不自造=Dumb 原则体现）、[[emc-tri-state-exit-contract]]（编排器确定性裁定）、[[emotion-map-logic-chain]]。
