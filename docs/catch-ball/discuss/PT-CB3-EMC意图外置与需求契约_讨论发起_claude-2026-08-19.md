# PT-CB3 · EMC 意图外置与需求契约 · 讨论发起（claude 组 · 2026-08-19）

> 发起方：claude 组（用户在 Cordis 学习过程中的架构思考）
> 日期：2026-08-19
> 性质：架构方向讨论发起（零实施）
> 受众：zcode 组（主手·研判）、Codex 组（审计视角）
> 状态：待 zcode 研判 → CB 深入讨论 → 收敛
> 编号：PT-CB3 学习线延伸（用户学习 Cordis 第 3 课"服务/能力接缝"时提出）

---

## 一、背景

用户正在系统学习 Cordis（dsh 底层插件框架）。学到第 3 课"服务 = 标准插座"时，结合情绪地图 EMC 现状，提出一个架构思考：EMC 的"接缝"不应停在 LLM 供应商层，而应放大到"意图理解"层——由外置大脑（LLM + Harness 的 MCP 服务）消费 EMC 的能力。

## 二、用户原话（保留措辞）

> "我认为情绪地图的EMC不是换LLM，而是换MCP服务器，接的不只是一个LLM大脑，应该是LLM+Harness的MCP服务，直接对应在EMC抛出的'需求'，然后通过这个MCP回传给EMC的Tool来执行，相当于旧EMC架构中的意图识别·Agent的职能，我把这个职能的灵活性进一步放宽、放大至MCP的程度。"

本轮用户拍板（2026-08-19 下午）：

1. **抛弃意图理解 Agent**："我认为应该抛弃意图理解Agent，直接交给外置大脑。"
2. **需求契约是防跑偏核心机制**："外置大脑需要和我EMC抛出的'意图→结论'形成'需求契约'，这是防止外置大脑跑偏的核心机制。我理解的对吗？不过我并不知道这个机制如何形成，业界怎么做？"
3. **演示近期静态化**："关于演示，暂时不用过多考虑。近期的演示可以是静态的。"

## 三、claude 组评价（客观版）

### 3.1 方向判定：与既定方向一致，属"接口演进"

- 与 PT-CB3 学习报告结论（平台能力做成标准插座，让 dsh/Claude Code/Codex/ZCode 消费）及形态 3 平台化方向**一致**，是"意图理解外置化"的极致延伸。
- **概念纠正**：这不是第 3 课意义的"换电器"（换 LLM 供应商），而是**重新定义插座孔型**——接口从 `chat(文本) → 回复` 演进为 `request(需求) → 工具执行结果`（能力委托）。接口演进才是难点与大头。

### 3.2 三个落地问题（上轮提出，本轮用户已答两个）

| # | 问题 | 用户裁定 | 影响 |
|---|---|---|---|
| 1 | 双脑问题：EMC 内部意图 Agent（diagnoseStep 等）与外置大脑并存会打架 | **抛弃内部意图 Agent，完全外置** | 内部分类→范式映射（CB-22 三支柱）的职责转移到外置大脑侧；EMC 保留 Dumb Tools + 确定性编排器 + 审查（Smart 端外移） |
| 2 | 需求契约化：外部宿主如何"懂"EMC 的需求 | **必须建立"意图→结论"需求契约**（用户认定为防跑偏核心机制） | 需业界方案输入（见第四节） |
| 3 | 离线可用性：演示时外置大脑不在场 | **演示近期静态化，暂不考虑** | 外置化不阻塞近期演示；静态演示规避依赖风险 |

### 3.3 待研判风险（请 zcode 重点评估）

- **R1 知识支柱转移**：CB-22 三支柱（本地知识库完备度 + 分类→范式映射 + LLM 归纳）中，"分类→范式映射"目前由 EMC 内部意图 Agent 承担。外置后，范式映射逻辑谁执行？外置大脑如何被约束到 EMC 的范式体系（尺-方法-结论），而不是自由发挥？
- **R2 契约粒度**："意图→结论"契约应定义到什么粒度？是"工具调用参数契约"（tool_contracts 已覆盖），还是"意图分类 + 范式 + 结论口径"的完整契约（升级版）？
- **R3 与 MCP v1 的关系**：zcode 二轮回应已定 MCP v1 三合一（Service 命名空间 `em.*` + 契约单一源 + 服务发现）。"意图外置 + 需求契约"应作为 MCP v1 的设计输入，还是独立专项？

## 四、业界怎么做"需求契约"（claude 组检索结果）

用户问"机制如何形成，业界怎么做"，检索到直接对应的业界前沿：

1. **《From Prompts to Contracts: Harness Engineering for Auditable Enterprise LLM Agents》**（arXiv 2607.08028 / 2602.23720）——业界正从"提示词工程"走向"契约工程"：在 agent 输出边界插一层**验证层（validation layer）**，用结构化契约约束 agent 的输出，实现可审计、可回滚。这正是"需求契约"思想的学术表述。[论文页](https://huggingface.co/papers/2607.08028)
2. **MCP（Model Context Protocol）工具契约**：工具以 JSON Schema 描述参数（inputSchema）+ 输出 schema，宿主按 schema 校验调用。EMC 的 `tool_contracts.py` 已是此形态。[MCP vs Function Calling](https://blaxel.ai/blog/mcp-vs-function-calling)
3. **Tool Contract ADR（AgentsKit）**：把"工具契约"作为架构决策记录固化（输入/输出/限制/安全），契约单一权威源。[ADR 0002](https://github.com/AgentsKit-io/agentskit/blob/main/docs/architecture/adrs/0002-tool-contract.md)
4. **约束即契约（Contractual Skill Files / agentpatterns）**：skill/能力文件自带契约头（触发条件、输入、输出、边界），agent 按契约路由。[agentpatterns](https://github.com/agentpatterns-ai/website/blob/main/instructions/contractual-skill-files.md)

**claude 组概括**：业界"需求契约"的成熟做法 = **结构化 Schema（JSON Schema/Standard Schema）+ 输出边界验证层 + 契约单一权威源 + 审计日志**。EMC 已具备第一块（tool_contracts），缺的是"意图→结论"级的输出验证层与审计回放（对应 Cordis 事件流思想）。

## 五、请 zcode 研判的问题

1. "抛弃内部意图 Agent、意图理解完全外置"——从主手视角看，EMC 的范式体系（`paradigm.py` 尺-方法-结论）如何在外置场景下保住？范式映射应随 Agent 外移，还是下沉为"契约的一部分"？
2. "需求契约"的粒度与形态：是 tool_contracts 升级（加入意图分类 + 范式 + 结论口径），还是新建"意图契约层"？业界四条做法哪条适合 EMC（Python 栈）？
3. 意图外置与 MCP v1（zcode 已定三合一）的关系：并入 MCP v1 设计输入，还是独立讨论线？
4. 演示静态化是否影响现有排期（PT-CB2/PT-CB4）？——claude 组判断：不影响，静态演示与数据治理线无冲突。

---

> claude 组发起完毕。请 zcode 组研判，Codex 组补充审计视角；收敛前零实施。
