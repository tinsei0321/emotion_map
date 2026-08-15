---
name: plan-requires-cb-preflight
description: 每次 plan/实施草案也要进完整 CB 流程（预检→SCAN→反评价→实施→检查→通过后 push），先验后推
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e859413b-2997-4df9-8850-b7105f8d5d98
  modified: 2026-08-04T11:12:32.468Z
---

用户 2026-08-04 两次强调：不只修复工作，**每次 plan/实施草案也要走完整 CB 流程**——写草案 → 发起预检（请 Codex/glm 两组进讨论，不是自己走一遍记录）→ 等两组 SCAN → 反评价 → 实施 → 发起实施后检查 → 两组 SCAN → 通过后才 push。先验后推。

**Why:** 用户把 CB 机制视为所有工作的质量门禁（不只 bug 修复）。plan 也是产出，须两组独立评估后才能动手/推送。证据：ExitPlanMode 被拒（"老规矩，plan也要进cb"）+ 消息重申（"都要进cb，然后再push"）。

**How to apply:** 任何实现任务开始前，先把实施草案写成 CB 请求文档（`docs/catch-ball/_handoff/CB{NN}-{topic}预检*.md`·模板见 ③w/③z）→ 登记 cb-journal → push 给两组同步 → 等 SCAN → 反评价 → 实施 → 发实施后检查 → 通过后 push。**发起文档可 push**（给两组看·同 0c9ba95/0862f09 模式）；**实施代码走先验后推**（两组检查通过才 push）。**评估方（Codex/glm）不 git pull/push**——同一本地工作区只读本地文件，请求文档第一步写「读本地文件·无需 git pull/push」。已入 KNOWLEDGE.md §7。关联 [[cb-knowledge-base]]、[[no-handoff-on-routine-commit]]。
