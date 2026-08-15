---
name: ui-visibility-mutex-proactive-check
description: UI 改动须主动检查同区域多组件显隐互斥，勿待用户报冲突
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e6777171-ecd1-4dbb-9427-77a442be1217
  modified: 2026-07-23T04:44:58.090Z
---

UI 改动后须**主动检查同一显显隐区域的多个组件是否互斥一致**，勿待用户报冲突。

EMC 同一会话区有 3 个"引导用户开口"的组件：空态欢迎卡 `.emc-welcome`、CPD 引导内容 `#aiq-suggest`（方向/细化/examples 胶囊）、答案后追问 `_followUps`。它们**不能同时显示**（否则"上面引导下面还在欢迎"冲突）。

**Why**：用户在 5.185 批评"你要自己发现这种逻辑冲突的问题"——我在加 CPD 方向级联（Step 1b）时，没注意到它与既有欢迎卡（`renderEmptyState`·`_history` 空时显）在同一区域同时显示，导致冲突暴露给用户。同区域多组件缺协调 = 典型遗漏。

**How to apply**：改任何一个显隐组件（欢迎卡/引导胶囊/追问/步骤卡）时——
1. **grep 同区域同职责的其他组件**（如新增引导胶囊 → 查 `renderEmptyState`/`_followUps`/`.emc-welcome` 是否冲突）。
2. **建互斥规则**：用一个标志位（如 `_guidanceExamplesShown`）统一协调，`renderEmptyState` 条件加 `!flag`，引导调度末尾 `renderEmptyState()` 同步。
3. **Playwright/肉眼验三态切换**：空态（欢迎）→ 引导态（胶囊）→ 答案态（追问），确认两两互斥、切换一致。

关联 [[design-language-consistency-iron-rule]]（跨场景一致交互）、[[tool-no-auto-overview]]（工具生成不抢刷 Overview）。
