---
name: cb-third-party-no-git
description: CB 第三方评估方（Codex/zcode组）权限口径——只读项目数据与代码·禁 git·评估意见必须落盘 docs/catch-ball/（禁只回聊天文字）·commit 由 claude组唯一执行
metadata:
  node_type: memory
  type: feedback
  originSessionId: 796baacf-fac2-4b70-98a4-79a01270824d
  modified: 2026-08-13T01:23:45.072Z
---

给第三方小组（Codex / zcode组）的 CB prompt 权限口径（三句话·勿省略勿矛盾）：

1. **只读项目数据与代码**（不读之外不动任何项目文件）
2. **禁一切 git 操作**（pull/commit/push/fetch 全禁·claude组唯一 git 写者）
3. **评估意见必须落盘**为 `docs/catch-ball/discuss/`（讨论类）或 `scan/`（SCAN 类）下 .md 文件，**禁止只回聊天文字**——不落文件 claude组 无法交流

**Why**：
- 2026-08-11 我给 codex 的 prompt 写了「git pull 对齐最新」——错（评估方不能 pull，读本地已检出文件即可）。
- 2026-08-13 我给两组 prompt 写了「不落文件」——错（与 RULES.md §5.1「可新建文件 docs/catch-ball/」矛盾，两组只回了聊天文字、无法交流）。「只读」本义 = 只读项目数据/代码/不动 git，**不包括禁止落评估意见文件**。已固化 RULES.md §5.1.1「评估意见落文件义务（2026-08-13 起·强制）」：每次讨论/评估必须落盘 .md·命名 `CB{NN}-{主题}_评估_{组名}-{YYYY-MM-DD}.md`·落文件 ≠ git。

**How to apply**：给第三方小组的 prompt 权限句固定为「只读项目数据与代码·禁 git·评估意见落盘 docs/catch-ball/discuss/（或 scan/）·命名 CB{NN}-{主题}_评估_{组名}-{日期}.md·commit 由 claude组统一执行」——不再写「不落文件」、不再写任何 git 指令。

关联：[[session-handoff]]（交接卡红线·CB 机制）· [[cb-workflow-reminder]]（每阶段标注已过 CB）· [[cb-prompt-copyable]]（prompt 用代码块包裹）· [[cb-roles-rename-zcode]]
