# ACP · Agent Communication Protocol · 契约 v1.1（EMC 权威·只定义不实现）

> PT-CB12 件②起草 v1（2026-08-22）· **SHELL(S129) S2 升 v1.1**（2026-08-23·依据壳阶段联合任务书 v1.0 §一.4：Q4 四项增补+provenance 字段+载荷结构模式）。
> 依据：Harness 选型讨论收口 §三.D（2026-08-22）+ R61 战略（MCP=工具面·ACP=会话机制面）。
> 性质：**宿主无关语义层**——EMC 为契约权威。只定义不实现；实现载体=壳阶段对话框接管或外置 harness 接入。
> 红线：不绑传输格式（SSE/WebSocket/stdio 均可载）·不抄任何宿主私有字段名（Codex threadId 等）·工具面归 MCP 不归 ACP·**过程-内容分层（v1.1 新增红线：ACP 事件只承载过程可见性，内容渲染语义走 markdown+内联模板通道·两通道代码层显式分界）**。

## 一 四动词（会话生命周期·最小集）

| 动词 | 语义 | EMC 现状对应 |
|---|---|---|
| `open` | 开启会话（携上下文/意图） | /api/v1/chat 会话建立 |
| `step` | 推进一轮（模型思考/工具调用/出图） | agent_step 阶段 |
| `seal` | 定稿出口（答案/图层/报告） | answer + outlet_card |
| `close` | 关闭会话（留痕归档） | 会话历史 |

## 二 五族事件（过程流·宿主无关语义）

| 事件族 | 语义 | EMC 自持词表（第一候选） | 粒度下限 |
|---|---|---|---|
| `msg.delta` | 消息增量（分 `kind`：正文 `content` / 思考链 `reason`；分 `provenance`：真流 `real` / 桩事件 `synthesized`） | diagnose/answer 流 + kind='reason'\|'content' | 逐 token |
| `tool.begin` / `tool.end` | 工具条目起止（begin：名/参摘要 → end：**载荷结构模式**见 §五-2） | agent_step（待细化到逐工具） | 每次调用 |
| `proc.delta` | 过程输出增量（命令/长任务输出） | —（EMC 暂无·壳阶段补） | 可选族 |
| `error` | 错误（语义化错误码+hint） | ok:False + hint 惯例 | 每错误 |
| `approval.req` | 审批请求（写面操作放行·见 §五-4） | —（轻循环默认全放行·接线点已登记） | 可选族 |

## 三 状态对象（最小字段）

```
session: { id, topic?, opened_at, status: open|sealed|closed }
turn:    { id, session_id, intent?, status: thinking|acting|sealing|done }
toolcall:{ id, turn_id, verb(MCP tool name), status: begin|end|error, caliber? }
```

## 四 附录 · 宿主映射（参照·非依赖）

| ACP 语义 | Codex v2 Notification（参照） | dsh 现状 |
|---|---|---|
| msg.delta | AgentMessageDeltaNotification | web 私有协议（禁依赖） |
| tool.begin/end | ItemStarted/ItemCompleted | 私有·无官方面 |
| proc.delta | CommandExecOutputDeltaNotification | 无 |
| error | ErrorNotification | — |
| approval.req | ItemGuardianApprovalReview* | — |

（映射样例 dump 待 Codex 试点期补·见收口裁决 §三.D）

## 五 v1.1 增补详述（S2 · 2026-08-23）

### 5-1 msg.delta 子类型与来源标记

- `kind: 'reason' | 'content'`——思考链与正文分型（EMC 既有两态成文化·前端可分样式渲染）。
- `provenance: 'real' | 'synthesized'`（缺省 `real`）——**降级形态诚实性标记**：BrainAdapter 的 dsh 降级形态（headless 调用+壳侧进度桩事件）所发 msg.delta **必带 `provenance='synthesized'`**，前端对其渲染为「步进进度」而非「思考流」样式——防用户把模拟进度当真流式思考。轻循环引擎/全量形态恒为 `real`。

### 5-2 tool.end 载荷结构模式（非固定字段集）

载荷 = **工具特定摘要对象 + 必带 caliber 摘要（scale/refs）**；各工具的载荷 schema **按工具注册**（沿 `ai_qa/tool_contracts.py` 单一权威源模式·与铁律 11 契约三处同步同律）。示例：

| 工具 | 载荷摘要字段（除 caliber 外） |
|---|---|
| rag_query | `count` / `dim_counts` / `top_dim` / `elapsed_ms`（PT-CB11 已落地四字段） |
| zonal_stats | `row_count` / `sort_by` |
| render_spec | `spec_id` / `mode`（inline\|dataset） |

**设计理由**：写死单一字段集会让异构工具的事件载荷无处安放；模式条款保证「必带口径摘要」的统一性，字段面留工具自治。

### 5-3 followup_cue 渲染语义（过程通道）

`followup_cue` 是 `tool.end` 载荷字段（**过程通道**——契约只管「字段存在与语义」：确定性派生的追问线索·零 LLM）。「cue → 对话框追问 chips → 点击回填输入框」的**交互实现属前端内容通道**，契约不管（过程-内容分层红线）。实现参照：`tools/mcp_server_emc.py` `_derive_followup_cues`（三张小表 `ai_qa/rag_cues.json`）。

### 5-4 approval.req 接线注记

壳阶段轻循环引擎下**默认全放行**（当前工具面全只读·无审批需求）。**接线点登记：`approval.req` 的首个真实消费者 = RAG 支柱二 kb_inbox 写入**（RAG 方向 CB 收敛已裁三级审批：字段级自动/人审抽检/全人审）——将来写入面工具上线时直接消费本事件族，不另起审批语义。

## 六 附录 · 垂域共享不变量清单（S9 · 2026-08-23）

> 用途：垂直域抽象层（Vertical Profile·六件套见 `docs/vertical-profile.md`）的平台/垂域分界契约——**换垂域时以下五项必须零改动**。此清单是垂域②试点（城市体检医生 Agent）的核心观察项：**有一项要改 = 抽象层划线错了·早发现早便宜**。

| # | 不变量 | 真身载体 |
|---|---|---|
| 1 | ACP 事件语义（四动词+五族事件+v1.1 增补字段） | 本契约 |
| 2 | MCP 工具签名（18 件·F_021-F_040 注册面） | `tools/mcp_server_emc.py` build_server |
| 3 | 渲染契约结构（render spec 七段：spec_version/spec_id/kind/data/style/ui/origin/caliber_lite） | `docs/render-contract.md` |
| 4 | 治理字段 schema（status/lineage/X-01·rag loader 契约三字段） | `tools/rag_index.py` |
| 5 | 四态出口契约（EXIT_RESULT/GAP/CONCEPT/PARTIAL） | `ai_qa/manifesto.py` §八 |

> v1.1 · 2026-08-23 · zcode 起草 v1 + Qoder 增补（SHELL(S129) S2/S9）·评审：zcode 审读收敛
