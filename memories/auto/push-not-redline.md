---
name: push-not-redline
description: git push 已从红线解除，commit+push 为组合操作，commit 通过即推
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5c57f310-265b-4d4b-9087-aac8a5a9568f
---

git push 不再是红线操作。commit + push 是组合操作——commit 通过即推，不再单独询问。

**Why:** 用户 2026-07-04 明确申明。配额按调动次数计，每次 commit 后再单独确认 push 是多余往返；日常开发提交直接推到远端即可。

**How to apply:** commit 后直接 `git push`，视为同一动作。rebase / reset --hard / 强制推送仍属红线，需先问（见项目 CLAUDE.md 红线段，已同步移除 git push）。同类政策更新风格见 [[no-handoff-on-routine-commit]]。
