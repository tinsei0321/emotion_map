# CB 讨论 · RAG 开发方向（Agentic RAG 特性对照与前沿范式选型）· 发起（zcode·2026-08-23·今日收敛）

> **用户令（原话）**：「目前情绪地图项目的RAG是否拥有 Agentic RAG 的特性，如果没有请重新思考RAG重构的方向，目前最前沿的RAG是什么？Agentic RAG？LLM Wiki？还有什么？请讨论组一起查阅相关论文和知识，今天需要明确RAG的开发方向。」
> 参与组：**zcode（发起+收敛）+ Kimi + Qoder**（用户令）。今日收敛·用户终裁。
> 前置：执行线派发已撤销（PT-CB9R 挂起·壳阶段评审挂起）——方向定后统一改道。

## 一 2026 前沿图谱（主手核查·源附）

| 范式 | 核心机制 | 适用场景 | 代表源 |
|---|---|---|---|
| **Pipeline RAG**（经典） | 检索一次→生成 | 简单问答 | — |
| **Agentic RAG** | **agent 控制检索循环**：规划子查询→路由工具→评估→修订再检（retrieve-evaluate-revise loop） | 复杂/多源任务 | [Neo4j](https://neo4j.com/blog/agentic-ai/what-is-agentic-rag)·[Lyzr 2026](https://lyzr.ai/blog/agentic-rag)·[A-RAG 论文](https://arxiv.org/html/2602.03442v1)·[Agentic GraphRAG 综述 SSRN](https://papers.ssrn.com) |
| **GraphRAG** | 知识图谱结构+多跳遍历 | 关系型/多跳问题 | [对比文](https://medium.com/@Micheal-Lanham/pipeline-rag-vs-agentic-rag-vs-knowledge-graph-rag-what-actually-works-and-when-47a26649a457)（EMC 已裁定小语料不采） |
| **Self-RAG / CRAG** | 自反思 token / **检索质量评估器+纠正回路**（检不好→重写/换源） | 高可靠性问答 | [Towards AI 对比](https://pub.towardsai.net)·[模式文](https://elegantsoftwaresolutions.com) |
| **Adaptive RAG** | 按问题复杂度动态选策略（_no-retrieve / single / iterative_） | 混合负载 | [变体综述](https://www.linkedin.com)（EMC 的 A2 路由=其基础形态） |
| **LLM Wiki / agent 记忆** | **agent 自维护知识库**（读写自己的 markdown wiki·Karpathy 式）；STORM=多视角提问合成维基文章；MemGPT/Letta=OS 式分层记忆 | 知识复利/长期积累 | [STORM 论文](https://arxiv.org/abs/2402.14207)·[llm-wiki-agent](https://github.com/SamurAIGPT/llm-wiki-agent)·[Karpathy LLM wiki 作 agent 记忆](https://aaif.io/blog/karpathys-llm-wiki-as-agent-memory)·[Letta/MemGPT](https://www.letta.com/blog/agent-memory/)·[记忆基准](https://arxiv.org/html/2602.16313v1) |

## 二 EMC RAG 的 Agentic 特性对照（主手开场评估·请两组挑战）

| Agentic RAG 特性 | EMC 现状 | 判定 |
|---|---|---|
| 查询路由（router） | **A2 已有**：精确→kb_facts / 叙述→rag_query（工具契约层） | ✅ 基础形态 |
| 迭代检索循环（plan→retrieve→evaluate→revise） | **无内生**——但外置 Harness 的 agent loop 天然承担（dsh 可连调 rag_query→kb_facts→zonal）；followup_cues 正是喂养该循环的设计 | ◐ **归属外脑**（架构裁定：大脑永远外置） |
| 检索质量自评（CRAG evaluator） | 无（质量判据在离线门禁·非运行时） | ❌ 候选增量 |
| 多跳/子查询分解 | 无内生（同上归外脑） | ◐ |
| 知识自维护（LLM Wiki 式读写） | **雏形**：知识提交五步流程（人审）+B2 校准三原则（OPUS-5 吸收）+治理字段/谱系（status/lineage/X-01）——**人审写入管线已建·agent 写入未开** | ◐ 半步 |
| 工具化检索（retrieval as tool） | **已达标**：rag_query/kb_facts=MCP 工具·供任意 agent 消费 | ✅ |

**开场结论**：EMC RAG = 「**Agentic-ready 检索服务**」——为 agent 消费设计的插座（路由/线索/口径/治理四件套已建）·但**自身不是 agent**（无内生循环/自评/自维护）。这符合架构裁定（大脑外置）——**但正是本次要讨论的边界**。

## 三 核心张力与三个候选方向（讨论靶）

**张力**：用户之问暗示可能想让 RAG 更「主动」——与「大脑永远外置」的既定裁定存在边界张力。三个方向：

| 方向 | 内容 | 与裁定关系 | 代价 |
|---|---|---|---|
| **A 服务深化** | 维持外置：RAG 补 CRAG 式检索质量自评（低置信→返回「建议换 kb_facts/细化问题」线索）+ 多路召回增强——agent 循环仍归 Harness | 完全相容 | 小 |
| **B 轻内置 agent** | EMC RAG 内置 retrieval agent（查询改写/多跳分解/自评循环·一个 MCP 工具内闭环） | **边界案例**：工具内 agent≠壳内大脑·可辩护（工具自治≠编排权转移）但需用户确认 | 中 |
| **C LLM Wiki 化** | 知识库升级「受治理的 agent-writable wiki」：Harness/分析工具的结论经治理管线（B2 三原则+谱系+人审位）**回写知识库**——知识复利闭环（Karpathy 式+EMC 治理特色） | 相容（写入走管线非自由写·口径纪律不破） | 中大 |

**主手开场倾向**：**A 立即 + C 规划 + B 缓议**——A 是无争议增量；C 是用户「语料会长厚」+学习回路的自然终局（但要治理护栏先行）；B 与 A 功能重叠且触裁定边界·除非 C 需要否则不引入。

## 四 讨论议题（D1-D5·两组逐条表态）

- **D1**：特性对照表（§二）判定是否成立——尤其「迭代循环归属外脑」的边界论证。
- **D2**：方向 A/B/C 采否与组合——B 的裁定边界你怎么看（工具内 agent 算不算把大脑搬回来）？
- **D3**：若 C（wiki 化）：治理管线设计原则——agent 写入的**审批位**（全自动/人审抽检/白名单源自动）？与 X-01/口径注册表的关系？
- **D4**：若 A：CRAG 自评的轻量实现面（返回结构加 confidence/retry_cue 就够·还是要真跑二次检索）？
- **D5**：对已收口的 96.7% 体系的影响——任何方向不得零退化违例（红线确认）。

## 五 今日流程与分工

1. **zcode 开场**（本件·已完成）→ 2. **Kimi+Qoder 各自查阅论文/知识并回应**（今日内·落盘 `RAG方向讨论回应_{组}-2026-08-23.md`·带源）→ 3. **zcode 收敛**（今日·裁决表）→ 4. **用户终裁** → 5. 改道执行（PT-CB9R/壳阶段按新方向重排）。
- 回应要求：一句话结论+D1-D5 逐条（agree/disagree/partial+证据）+**至少 2 个本报告未覆盖的前沿范式或论文**（补盲）+四档裁决（对 A/B/C 及子项）。
- 纪律：查阅须真读（链接/论文名附上）·零实施零 git 写（回应文件除外）·中文结论先行。

> zcode 主手 · 2026-08-23 · RAG 方向 CB 发起·今日收敛
