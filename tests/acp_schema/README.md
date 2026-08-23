# tests/acp_schema · ACP 事件 schema 校验器（壳阶段 S6 · dsh · 2026-08-23）

> 权威源：`docs/acp-contract-v1.md`（EMC 契约·只定义不实现）。本目录=契约的机器可校验面（JSON Schema draft 2020-12 + pytest 桩）。
> 依赖：`jsonschema>=4.0`（requirements.txt 已声明·双机重建可复现）。
> 纪律：禁 emoji·零新追踪 ID（纯测试资产·不进 tracker 注册面）。

## 一 覆盖面（五族事件 + 三状态对象）

| 文件 | 对象 | 契约出处 |
|---|---|---|
| `schemas/msg_delta.schema.json` | 消息增量（正文/思考链分 kind·逐 token） | §二 |
| `schemas/tool_begin.schema.json` | 工具条目开始（名/参摘要） | §二 |
| `schemas/tool_end.schema.json` | 工具条目结束（果摘要/口径标签） | §二 |
| `schemas/error.schema.json` | 错误（语义化错误码+hint） | §二 |
| `schemas/approval_req.schema.json` | 审批请求（写面放行·可选族） | §二 |
| `schemas/session.schema.json` | 会话状态对象（open\|sealed\|closed） | §三 |
| `schemas/turn.schema.json` | 轮状态对象（thinking\|acting\|sealing\|done） | §三 |
| `schemas/toolcall.schema.json` | 工具调用状态对象（begin\|end\|error） | §三 |

校验桩：`test_acp_schema.py`——①schema 齐全性（无孤儿文件）②每份过 draft 2020-12 metaschema ③合法样例通过断言 ④故坏样例失败断言（错误定位到字段）。

## 二 版本注记位（S2 v1.1 增补未定稿·预留）

> **依赖注记（用户令）**：S2 的 v1.1 增补（kind 子类型/provenance/载荷结构）未定稿——本目录先按 v1 骨架建；S2 落地后**补 schema 增量**并回填本表（各 schema `$comment` 已留版本注记位·改动不得修历史语义）。

| # | v1.1 待补增量（S2 在途方向·未定稿） | 涉及 schema | 落地动作 |
|---|---|---|---|
| 1 | `msg.delta.provenance: 'real'\|'synthesized'`（缺省 real·dsh 降级形态诚实性标记） | msg_delta（可能扩全族） | S2 定稿后加字段+enum·补样例 |
| 2 | `tool.end` 载荷结构模式：工具特定摘要对象+必带 caliber 摘要（scale/refs）·按工具注册（沿 `ai_qa/tool_contracts.py` 单一权威源模式） | tool_end（caliber 内层由宽松收紧为必带） | S2 定稿后改 caliber required 面·按工具注册载荷 schema |
| 3 | `followup_cue` = tool.end 载荷字段（过程通道·渲染语义归前端内容通道·过程-内容分层红线） | tool_end | S2 定稿后补字段 |
| 4 | `approval.req` 接线注记：首个真实消费者=RAG 支柱二 kb_inbox 写入（三级审批） | approval_req | 接线落地后按实补 action 枚举/载荷 |
| 5 | 共享不变量清单（契约 §六·S9）：ACP 事件语义为五不变量之首——本目录 schema 即该不变量的机器守护 | 全部 | 垂域②试点前本目录应零改动（改了=抽象划线错·早发现早便宜） |

## 三 用法

```text
py -m pytest tests/acp_schema/ -q        # 定向
py -m pytest tests/ -q                   # 全量门禁
```

新增事件族/状态对象：在 `schemas/` 加 `<name>.schema.json` + 在 `test_acp_schema.py` 的 `FAMILIES`/`VALID`/`INVALID` 登记（齐全性测试自动纳入）。

> dsh · 2026-08-23 · S6 交付·待主手回收（S2 落地后 schema 增量补件由主手排）
