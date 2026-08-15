---
name: token-saving-workstyle
description: subagent 规则已更新——2026-08-04 起可以派 subagent（全局 CLAUDE.md「调用次数优先」已移除）；并行优先·subagent 按需
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-08-04T12:26:49.467Z
  originSessionId: e859413b-2997-4df9-8850-b7105f8d5d98
---

**subagent 规则更新（2026-08-04）**：用户明确「不派 subagent 的规则过时了」→ 全局 `~/.claude/CLAUDE.md`「工作方式」段已改（移除「调动次数优先·不派 subagent」→ 改为「并行优先·subagent 按需」）。

**新规则**：
- 大范围探索 / 并行独立任务 / 需隔离上下文的重活 → 可派 Explore / general-purpose / Plan agent（多个并行一条消息）
- 单点查询 / 小改动 → 自己直接读，不派
- 会话切分 + 批量并行 + 合并修改 仍有效（省往返·不是成本红线）

**Why**：旧版「调用次数优先（非 token）」主张不派 subagent 是当时用户选择；2026-08-04 用户推翻——可派了。本条目记录这个转变，避免与旧全局规则混淆。

**How to apply**：默认并行优先；该派就派（Explore 扫文件 / general-purpose 跑多步），不该派（单点读）自己读。关联 [[plan-requires-cb-preflight]]、[[context-coherence-discipline]]。
