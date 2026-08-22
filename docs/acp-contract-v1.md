# ACP · Agent Communication Protocol · 契约 v1（EMC 权威·只定义不实现）

> PT-CB12 件② · 依据：Harness 选型讨论收口 §三.D（2026-08-22）+ R61 战略（MCP=工具面·ACP=会话机制面）。
> 性质：**宿主无关语义层**——EMC 为契约权威。只定义不实现；实现载体=壳阶段对话框接管或外置 harness 接入。
> 红线：不绑传输格式（SSE/WebSocket/stdio 均可载）·不抄任何宿主私有字段名（Codex threadId 等）·工具面归 MCP 不归 ACP。

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
| `msg.delta` | 消息增量（正文/思考链·分 kind） | diagnose/answer 流 + kind='reason'\|'content' | 逐 token |
| `tool.begin` / `tool.end` | 工具条目起止（名/参摘要→果摘要/口径标签） | agent_step（待细化到逐工具） | 每次调用 |
| `proc.delta` | 过程输出增量（命令/长任务输出） | —（EMC 暂无·壳阶段补） | 可选族 |
| `error` | 错误（语义化错误码+hint） | ok:False + hint 惯例 | 每错误 |
| `approval.req` | 审批请求（写面操作放行） | —（EMC 工具全只读·预留） | 可选族 |

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

> v1 · 2026-08-22 · zcode 起草 · 评审：随 PT-CB12 回收
