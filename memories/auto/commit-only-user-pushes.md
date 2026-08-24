---
name: commit-only-user-pushes
description: 只 commit 不 push，用户手动 push（覆盖 CLAUDE.md commit+push 组合规则）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 41a5ee74-402f-460b-9c2e-84071b7ce5aa
---

用户明确：以后 Claude 只负责 commit，push 由用户手动。**覆盖 CLAUDE.md「commit + push 为组合操作（push 已非红线，commit 通过即推）」规则**。

**Why:** 用户网络 push 频繁失败（github 连接重置），且想自己控制 push 时机。

**How to apply:** commit 命令不带 `&& git push`；commit message 仍规范（简洁英文 + Co-Authored-By）；commit 后告知用户"已 commit（hash），待你 push"。revision-log/todo 同步照常（commit 含文档）。关联 [[maintain-revision-log]]、[[todo-revision-log-sync]]。
