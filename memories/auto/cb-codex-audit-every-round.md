---
name: cb-codex-audit-every-round
description: 每轮工作完成都要主动让 codex 审计——主动提示用户 + 给可复制 prompt（代码块包裹）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 39bfd82d-8d26-4166-80e7-aaa1fc2ce3b9
  modified: 2026-08-11T06:18:14.319Z
---

每轮工作完成后，主动提示用户「该让 codex 审计了」并给可复制 prompt（代码块包裹）。不要等用户要求。

**Why**：2026-08-11 用户强调「每轮的工作都要让 codex 对你进行审计，你要主动提示我，并给我 prompt」——codex 是第三方独立评估方，对每轮交付做 agree/disagree/partial 审计，保障质量与方向。这是本轮工作流固定的节奏。

**How to apply**：
- 每完成一个工作单元（如后端扩展 / fact 转换 / RAG 重建 / 适配器），主动说「本轮可让 codex 审计」+ 给 prompt。
- prompt 含：本轮改了什么（commit/文件）+ 待审计焦点 + 要求（agree/disagree/partial + 证据 + 定稿建议）+ 只读本地不 git（[[cb-third-party-no-git]]）。
- 接收方按用户分工提示（codex/zcode/两组·[[cb-roles-rename-zcode]]）；除非用户指定，评估=codex。
- 评估回收后：反评价 → 定稿 → 进 cb-journal/_cb-index。

关联：[[cb-third-party-no-git]]（评估方不 git）· [[cb-roles-rename-zcode]]（分工）· [[cb-prompt-copyable]]（prompt 代码块）
