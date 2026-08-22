# EMC · RAG 重建的业界对照评估与 Harness 接轨设计（zcode 主手·2026-08-22）

> 用户令：RAG 重构「参考业界经典优秀做法适配我的资产和形态」+「考虑与 Harness 接轨·发挥整体优势」。本文=专业评估（研究件·对 PT-CB9 v1.1 计划的对照评审与增补建议·**待拍板后并入 v1.2**）。
> 业界输入（2026-08 检索核实）：[Anthropic Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval)·[2026 RAG 全景](https://aishwaryasrinivasan.substack.com/p/all-you-need-to-know-about-rag-in)·[企业级 RAG 实践](https://techplustrends.com/enterprise-rag-implementation-best-practices-2026/)·[RAG 技术对比/自适应路由](https://blog.starmorph.com/blog/rag-techniques-compared-best-practices-guide)·[混合检索+重排实操](https://community.wolfram.com/groups/-/m/t/3635386)·[高级 RAG 规则](https://inexture.ai/blog/advanced-rag-techniques-for-reliable-ai-architecture/)·[late chunking 对照研究](https://arxiv.org/html/2504.19754v1)。

---

## 一 业界经典图谱（2026 现状·按流水线位置）

| 环节 | 业界标准做法 | 效果证据 | 对小语料适用性 |
|---|---|---|---|
| **入库** | Contextual Retrieval（Anthropic）：embedding 前给每 chunk 前置 LLM 生成的上下文短注（文档标题+定位） | 检索失败率 -49%（叠加重排 -67%·[官方](https://www.anthropic.com/engineering/contextual-retrieval)） | **高**——一次性 LLM 成本在小语料（<1k chunk）完全可负担·本土可用 DeepSeek API 离线生成 |
| **治理** | 元数据统一管理（status/时间/谱系）+ 源归因持续追踪 + 入库去重 | [企业实践](https://techplustrends.com/enterprise-rag-implementation-best-practices-2026/)列为一等公民 | **高**——EMC 口径卡天然是强元数据资产 |
| **检索一阶段** | Hybrid（BM25+稠密）+ RRF 融合·overfetch（top100） | [共识标准](https://community.wolfram.com/groups/-/m/t/3635386) | **高**（v1.1 已计划） |
| **检索二阶段** | Cross-encoder 重排（top100→top5） | 精度主升档·2026 标配 | **中**——小语料收益边际递减·但本地 bge-reranker 可负担·列为可选项 |
| **路由** | Adaptive RAG：query 分类器分流（精确型→直查/叙述型→RAG/复杂型→多跳） | [2026 新兴最佳实践](https://blog.starmorph.com/blog/rag-techniques-compared-best-practices-guide) | **高**——EMC 已有天然双工具（kb_facts=精确/rag_query=叙述）·缺的是显式路由契约 |
| **评测** | 黄金集+Recall@k+nDCG·门禁进 CI·持续回归 | 业界共识 | **高**（v1.1 已计划·方向正确） |
| **不采用** | GraphRAG/ColBERT/late-chunking/agentic 多跳检索 | 各有场景 | **明确不采**——大语料/复杂推理专用·EMC 小语料+口径型问答用不上·引入=纯复杂度 |

## 二 EMC 资产形态盘点（适配的出发点）

| 资产/约束 | 事实 | 对设计的含义 |
|---|---|---|
| 语料规模 | 蒸馏笔记 282 段（39 份 md 上游）+fact/concept/case 库 ≈ **<1k chunk** | 小语料：治理>暴力检索；重排是可选项非必选项 |
| 语言与模型 | 中文·本地 BGE（sentence-transformers·预热 15s） | 中文 BM25 用 jieba（已锁版）；稠密维持 bge 系 |
| **口径卡体系**（独有优势） | K 卡/G 卡/口径注册表=结构化权威源·带时效性（压旧口径） | **元数据优先**：精确口径问题应直查注册表（kb_facts 面）·不该走向量召回碰运气 |
| 双消费者 | ①MCP rag_query（外脑 dsh/Codex）②自持对话框 ai_qa（壳阶段） | 检索核心单一权威源·两契约面共享 |
| 时效语义 | 口径有「未作废但已过时」态 | status 元数据过滤（业界 temporal filtering 的 EMC 落地） |
| 同源冗余 | 39 md ↔ 282 段蒸馏同源 | 入库谱系标注+去重（v1.1 C-D 已列·业界同判） |

## 三 对 PT-CB9 v1.1 的对照评审

**已对齐业界**（无需改）：Hybrid+RRF（泳道②）/黄金集+门禁进 CI（P0·[业界共识](https://inexture.ai/blog/advanced-rag-techniques-for-reliable-ai-architecture/)）/入库谱系去重（C-D）/契约先行（P0-6 loader 契约=业界「单一事实源」）。

**建议吸收三项**（v1.2 增补·按性价比排序）：

| # | 增补 | 业界依据 | EMC 落法 | 量级 |
|---|---|---|---|---|
| **A1 上下文化前注** | [Anthropic Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval)（-49% 失败率） | 小语料一次性成本可负担 | 入库时用 DeepSeek API 为每 chunk 生成 1-2 句上下文前注（文档名+小节定位+口径状态）存 meta·embedding/BM25 都吃前注文本；索引构建脚本一次性步骤+可重建 | 0.5d |
| **A2 显式路由契约** | [Adaptive RAG](https://blog.starmorph.com/blog/rag-techniques-compared-best-practices-guide) | EMC 双工具已在·缺契约 | rag_query 描述+两工具契约里写明分工：**精确名词/口径数字→kb_facts（注册表直查）·叙述/方法/对比→rag_query**；rag_query 命中口径类时返回附注「精确值请以 kb_facts 为准」——宿主自纠路由 | 0.2d（契约层） |
| **A3 可选重排档** | 2026 两段式标配（[综述](https://aishwaryasrinivasan.substack.com/p/all-you-need-to-know-about-rag-in)） | 小语料收益边际但便宜 | 泳道②加 `rerank=False` 默认参数位：hybrid top20 → 本地 bge-reranker 精排 top5；黄金集上 A/B 实证后定默认值（消融纪律已有） | 0.5d（含 A/B） |

**明确不做**：GraphRAG/多跳/agentic 检索/late-chunking（大语料专用·EMC 引入=纯复杂度）；云端 embedding（本地纪律）。

## 四 Harness 接轨设计（「整体优势」的四个抓手）

> 定位：RAG 是 EMC 平台的**知识服务**·两个契约面（MCP 对外脑 / ai_qa 对自持壳）·一个检索核心。接轨≠改造 harness·是把 EMC 侧契约做厚到「宿主白拿优势」。

### H1 · followup_cue 契约化（最高价值·半成品接线）

- 现状：CB-22 已建 followup_cue 机制·测试问题排档件 P4「追问机制=把已有半成品接线补完」（08-21 入档）。
- 设计：**rag_query 返回增加 `followup_cues: [2-3 条可追问方向]`**（确定性生成：由命中 chunk 的 dim/相邻小节/口径关联派生·零 LLM）。宿主 agent loop 拿到 cues 自然链式追问——** harness 的编排优势被 EMC 的知识结构喂养**·这正是「整体优势」：EMC 知道知识地图的相邻节点·宿主擅长决定走哪条边。
- 壳阶段对接：cue 直接渲染成对话框「追问建议」chips（ACP `tool.end` 事件携带）。

### H2 · ACP 事件对接（检索过程可见）

- ACP v1（`docs/acp-contract-v1.md`）`tool.begin/end` 事件族在 rag_query 的最小载荷约定：begin={query 摘要}·end={命中数/口径 refs/数据维度}——壳阶段对话框显示「查知识库·命中 3 条·口径 K-C1」（3080 体验的 EMC 原生版）。
- 现成落点：rag_query 返回结构已带 count/data_dim/caliber——事件化只是包一层·零重构。

### H3 · 双消费者单一检索核心

- MCP `rag_query` 与自持 ai_qa diagnose 调**同一检索函数**（现状即如此·维持并写成契约红线）——换脑零知识质量损失·壳阶段零迁移。
- 防漂移断言：两入口返回结构 diff=0 进门禁（tests 一条·0.1d）。

### H4 · 检索核心的 harness 无关纪律

- 禁在检索核心里假设宿主行为（过滤器原则）：同义词扩展=EMC 确定性词表（计划已有）；**语义改写/多轮指代消解留给宿主大脑**（那是 LLM 强项·EMC 不抢）——分工写进契约注释。

## 五 修订汇总（v1.2 增补清单·待拍板）

| 项 | 来源 | 并入 | 量级 |
|---|---|---|---|
| A1 上下文化前注 | 业界·Anthropic | 泳道①入库流程 | +0.5d |
| A2 显式路由契约 | 业界·Adaptive RAG | 泳道②契约层+两工具描述 | +0.2d |
| A3 可选重排档（A/B 定默认） | 业界·两段式标配 | 泳道②参数位 | +0.5d |
| H1 followup_cue 契约化 | CB-22 半成品+P4 排档 | 泳道②返回结构 | +0.3d |
| H2 ACP tool 事件载荷约定 | ACP v1 | 契约文档注记 | +0.1d |
| H3 双入口防漂移断言 | 单一权威源纪律 | P0 门禁 | +0.1d |

v1.1 骨架（P0→①→②→③泳道与全部验收）**不动**；以上六项按表并入对应泳道任务书。Q-A（门禁快档）/Q-B（验收封顶）维持推荐项执行。

---

> zcode 主手 · 2026-08-22 · 业界对照评估+接轨设计·待用户拍板后出 v1.2 并开工
