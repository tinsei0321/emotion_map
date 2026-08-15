---
name: no-handoff-on-routine-commit
description: "平时 commit 只更 revision-log 工作记录；交接卡 session-handoff.md 只在用户说\"交接\"时才覆写"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0687e08b-697c-4787-bbff-23129d0e9ddd
---

用户原话：«我只有说"交接"的时候才会交接，平时只是普通 commit + 工作记录»（2026-06-24，v3.2 commit 时我误更了交接卡被纠正）。

**Why:** 交接卡 `memories/repo/session-handoff.md` 是换机/换会话的**单节点快照**，频繁改动会失去快照意义；平时工作记录走 `docs/revision-log.md`（§5 追加一行 + ★任务树状态）。

**How to apply:** 每次 commit 默认**只更新 revision-log**（§5 加行 + 任务树），**不要碰交接卡**。只有用户明确说"交接"/"换机"/"handoff"时，才覆写交接卡「当前节点」。已误更的交接卡用 `git checkout -- memories/repo/session-handoff.md` 还原。关联 [[maintain-revision-log]] [[session-handoff]]。
