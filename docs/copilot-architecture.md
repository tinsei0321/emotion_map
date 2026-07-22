# Copilot 通用架构（Smart Agent, Dumb Tool）

> 版本：v1（2026-07-22）· 把 EMC 已验证的 AI·Copilot 架构抽象成可复用框架，供本项目后续模块与未来新项目。
> 关系（single-source）：本文 = **通用抽象层**（内核 + 四层骨架 + 三铁律 + 落地模板）；[`docs/ai-qa-design.md`](ai-qa-design.md) = **情绪地图实现细节**（四层 SOP + Review + 独立子架构 + 三态出口落地）。两者双向链接，不重复。
> 内核已入 [`CLAUDE.md`](../CLAUDE.md)「AI·Copilot 开发内核」顶层节（全量注入明规则）。

---

## 一、内核：Smart Agent, Dumb Tool

> 一句话：**把"聪明"只放在两端（理解 + 表达），把"执行"做成最笨最稳的中间件。灵活来自 Agent，稳定来自 Tool，编排器机械接线。**

出处（产品侧原话）：「让 Agent 充分发挥灵活性（Smart），通过 skill/tool 执行计划，由于'执行'足够简单、纯粹（Dumb），保证结果即灵活又稳定。」

### 三角色

| 角色 | 职责 | 特性 |
|---|---|---|
| **Smart Agent** | 意图理解 Agent（NL→意图+计划）+ 结果输出 Agent（结果→优化呈现+审查） | LLM 驱动、**负责"想"**：理解模糊性、生成计划、推理校验、审查重写、优化表达。灵活、处理不确定 |
| **Dumb Tool** | Skill/Toolbox 标准化工具组 | **负责"做"、不思考**：功能单一、参数契约、纯执行、制式化产出。稳定、可测、可组合、零惊喜 |
| **Orchestrator 编排器** | Smart↔Dumb 翻译官 + 传菜员 | **确定性协调（不靠 LLM）**：把计划翻成执行参数、派发任务、回收制式结果、裁定终态。机械接线，让互不认识的 Agent/Tool 协作且互不干扰 |

### 四条推论铁律（内核的具体化，指导日常开发）

1. **Tool 越 dumb 越好**——单一职责 + 参数契约 + 纯函数式（输入参数→制式产出）+ **不内嵌 LLM 推理**。dumb = 可测、可组合、可复用、零惊喜。Tool 一旦"聪明"（内嵌推理/动态决策）就丧失稳定性，违背内核。
2. **Agent 聪明只在两端**——意图理解（入口）+ 结果输出（出口）。中间执行交 dumb tool，**避免"Agent 边想边做"的低效与不稳**（纯 ReAct 反复推理-执行的陷阱）。
3. **编排器确定性**——协调是机械的（分流/派发/回收/裁定），不是智能的。编排器不调 LLM、不推理；只按规则接线。
4. **计划-执行分离**——先计划（Smart 产意图+method+data_plan），后执行（Dumb 按 plan 跑 tool，可 0 LLM 轮）。同类型任务不重复推理（plan 可复用/缓存/命中率门控）。

### 价值（为什么是内核）

- **灵活 + 稳定兼得**：灵活集中 Smart 两端（LLM 擅长），稳定集中 Dumb 中间（确定性擅长），不互污染。
- **可测性**：Dumb tool 纯函数式 → 单测易；Smart agent → eval/运行时抽验。两端各自验证，互不纠缠。
- **可扩展**：加能力 = 加 dumb tool（参数契约）+ 编排器登记；Smart 不需改（它本就"聪明"能组合）。
- **抗退化**：内核给"新功能该放哪层"明确判据——**会推理→Smart，纯执行→Dumb，协调→编排器**。防止"大杂烩 panel.js"式坍塌。

---

## 二、四层可复用骨架（内核的架构化）

```
自然语言输入
   │
   ▼
【认知层 · Smart 意图理解 Agent】  NL → 结构化意图卡（intent/domain/scale/decision_type/data_plan/method）
   │   └ 数据自检：硬缺口→请求上传短路；软缺口→降级标注；齐全→ready
   ▼
【编排层 · Orchestrator 确定性】  意图 → 任务分流 + 派发 + 回收 + 终态裁定（不调 LLM）
   │   ├ 纯问答 → 短路（0 工具）
   │   ├ 单技能 → plan-once-execute（0 中间 LLM 轮，纯参数化执行）
   │   └ 多技能/未知 → ReAct 兜底（有界多轮）
   ▼
【执行层 · Dumb Skill/Tool 标准化】  参数契约 + 纯执行 + 制式化产出（rows/图层/统计）
   │   └ 工作流 = 参数化设计：只执行不思考，数据是参数
   ▼
【输出层 · Smart 结果输出 Agent】  意图 + 制式结果 → LLM 推理-校验-审查 → 终态呈现
   │   └ 审查层（checklist）→ 不达标 revise 1 轮
   ▼
结果展示层（排版 + 可点引用 + 三端同步）
```

### 各层职责契约

| 层 | 输入 | 输出 | 必须 | 禁止 |
|---|---|---|---|---|
| 认知层（Smart） | NL + 上下文 + grounding | 结构化意图卡 | LLM 推理、数据自检 | 改执行逻辑 |
| 编排层（Orchestrator） | 意图卡 | 任务序列 + 终态 | 确定性分流/裁定 | 调 LLM、推理 |
| 执行层（Dumb） | 参数 | 制式结果 | 纯执行、参数校验 | 内嵌 LLM、动态决策 |
| 输出层（Smart） | 意图 + 结果 | 呈现文本 + 审查 | LLM 优化、审查 | 臆造数据、裸输代码 |

---

## 三、三条可复用铁律（已验证，强约束）

### 铁律 A · 三态出口契约（编排器裁定终态，代码强制非模型自觉）

每次问答**必**落到且仅落到三种干净终态之一，由**编排器代码**裁定：

| 终态 | 触发 | 出口形态 | 绝不允许 |
|---|---|---|---|
| **做成（RESULT）** | 需工具类意图 且 有成功结果/新产出 | 数据驱动结论 + 可点操作 | 计划文、代码块、空话 |
| **缺数据（GAP）** | 数据硬缺口 或 零成功结果 | 确定性"缺数据卡"（不走 LLM） | 编造、假装做成 |
| **纯问答（CONCEPT）** | 通用/定义类意图 | 直接简洁答 | 硬塞领域框架 |

> 最高杠杆：需工具类意图零成功时**禁止**走叙述型输出，直接 GAP——杀死"只说不做"。
> EMC 落地：`harness.orchestrate` 三态出口 + `composeGapCard`（GAP 不走 LLM）+ `_exitBadge` 终态徽章。

### 铁律 B · 抗格式漂移（永不裸输原始 token）

LLM 输出非约定 schema 是常态，非异常。防线：
1. **解析归一**（`parseAgentStep`）：归一 drift schema（action 字符串/`{tool,params}`/fenced）+ 入参别名规整 + 纯叙述返 `{narrated:true}` 哨兵。
2. **叙述修复通道**：`narrated` 时纠偏重发 ≤1 轮，仍不成 → GAP。
3. **永不裸输**（`onDegraded`）：固定降级卡，忽略传入 raw 文本——代码块泄漏的最终保险。

### 铁律 C · 标准化数据契约（数据库层）

- 执行层 I/O 全走标准化端点（EMC = `/api/v1/geo/*`），返**属性表 rows**给 LLM（不灌全量 GeoJSON）。
- 数据缓存与单一权威源（EMC = `geo_registry` lazy 缓存 L1/L2×T1-T3）。
- grounding 经 `buildContext` 注入认知层（标注"仅供参考，不改变工具选型"）。

---

## 四、EMC 现状 ↔ 通用术语对照

| 通用术语（本文） | EMC 实现（[`ai-qa-design.md`](ai-qa-design.md)） |
|---|---|
| Smart·意图理解 Agent | `diagnoseStep`（6 字段 diagnose 卡）+ `_quickIntent`（本地预判） |
| Orchestrator 编排器 | `harness.orchestrate`（分流 + 三态出口裁定） |
| Dumb·Skill/Toolbox | `SKILL_DEFS`(`{tool,category,slots,defaults}`+`validateParams`) + `TOOLS`(10 geo 工具) |
| Smart·结果输出 Agent | `finalStep`/answer（Pro）+ Review（Flash 七条）+ Revise |
| 数据库层 | `/api/v1/geo/*` + `geo_registry` + `buildContext` |
| plan-once-execute | `runTemplatePath`（P1 单技能，0 agentStep LLM 轮） |
| ReAct 兜底 | while-loop（multi/unknown，有界 8 轮） |
| 三态出口 | result/gap/partial/ask/drift + general 短路 |

> **结论**：EMC 现状 = Smart Agent/Dumb Tool 内核的成熟实现（经 CB 三轮 + 三态出口承重 + 抗漂移注入测试验证），**不需推倒重来**。本框架是把它命名/抽象化，供复用。

---

## 五、领域驱动策略（可插拔，按需启用）

内核支持两种"领域"形态，按**领域间工具/数据异构度**选择：

| 形态 | 适用 | 实现 | EMC 取舍 |
|---|---|---|---|
| **领域加权（轻）** | 领域共享同一套 dumb tool + 数据，仅"视角"不同 | domain_lens 注入认知/输出层（行业语境附录加权 Smart） | ✅ **EMC 采用**（四领域共享 geo 工具 + L2 数据 + 4×5 矩阵，domain_lens 注入已覆盖） |
| **领域 Agent 拆分（重）** | 领域间工具/数据真正异构 | 编排器把目标拆成多 domain·Agent 任务，各领域独立工作模式/数据类型，并行派发回收 | ❌ EMC 不做（过度工程：共享 tool/数据下拆分 → 协调成本 > 隔离收益，且违背"Tool dumb 可组合") |

> 启用领域 Agent 拆分的判据：领域间 dumb tool 集合或数据源**真正不重叠**时才值得拆；否则用领域加权。

---

## 六、落地模板清单（供新项目复用 Copilot 内核）

### 目录骨架（前后端同构）

```
后端 <module>/
├── manifesto.py    知识层·领域宪法（喂模型懂业务）
├── prompts.py      认知/输出层 prompt（diagnose/answer/revise）
├── review.py       审查层 checklist + 审查员配置
├── paradigm.py     尺度-范式矩阵 + 工具目录（认知层单源真理）
├── schemas.py      ChatRequest（phase + 结构化字段）
├── router.py       /chat 路由（SSE 流式 + review 非流式）
└── llm.py          LLMClient（provider-agnostic）

前端 js/<module>/
├── harness.js      编排层·orchestrate + 三态出口 + Review 闭环
├── stages.js       认知/执行/输出/审查阶段函数 + SKILL_DEFS 标准化契约
├── tools.js        执行层·TOOLS（标准化 dumb tool）
├── panel.js        展示层·UI（形态无关）
└── api.js          LLM 调用（SSE）
```

### 接入清单（新项目 Copilot 化步骤）

1. **知识层**：写 `manifesto`（领域宪法）+ `paradigm`（工具目录/尺度矩阵）。
2. **认知层**：`diagnoseStep` 产意图卡（intent/scale/decision_type/data_plan/method）+ 数据自检三态。
3. **执行层**：每个能力做成 dumb tool（`SKILL_DEFS` 参数契约 + `validateParams` + 纯执行）——**会推理的绝不放这层**。
4. **编排层**：`orchestrate` 确定性分流（短路/plan-once-execute/ReAct 兜底）+ 三态出口代码裁定。
5. **输出层**：`answer`(Smart) + `review`(checklist) + `revise`(≤1 轮) + 抗漂移三防线。
6. **验证**：dumb tool 单测 + diagnose eval（空 context 路由）+ 运行时 browser e2e（真端点）。

### 可插拔扩展点

- **加 Stage**：`harness STAGES` 插项（reflect 深闭环 / 知识库 RAG / 规则库校验）。
- **换形态**：协议化后形态可插拔（浮窗↔独立窗↔侧栏↔移动端），核心 `harness/tools/panel` 不变。
- **换知识层/审查标准/tool/provider**：各单文件。
- **领域驱动**：按 §五 选加权或拆分。

---

## 七、与 CPD 的关系（客户端确定性编排器）

CPD 引擎（[`cpd-core-plan.md`](cpd-core-plan.md) v1.0 `deriveGuidance`）= **客户端确定性编排器**：
- 纯函数从特征向量推导"此刻唯一动作"——**铁律3 同源（不调 LLM、不推理）**。
- 引导（Smart 端的轻量"意图→动作"映射）+ 复用既有 dumb entry（openImport/openHeatmapDialog 等）——**铁律1/2 同源（执行交 dumb entry）**。
- CPD 实现天然遵循本内核；本文为 CPD 提供"编排器"理念参照。

---

## 八、演进与不做

- **本次已做**：内核沉淀（CLAUDE.md + 本文 + memory）+ harness 注释对齐（Smart 计划/Dumb 执行/编排器裁定术语显式化）。
- **远期（列演进位，本次不做）**：① 中途打断/流式中改提问（与 SSE + 三态出口耦合，ROI 中低）；② `ai_qa/` 抽独立可引用内核包（待 EMC 稳定）；③ 领域 Agent 拆分（按 §五 判据，情绪地图不需要）。
- **不做**：推倒重来 harness/diagnose/三态出口（内核已实现，承重）。
