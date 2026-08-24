---
name: cb-workflow-reminder
description: "用户会忘记本轮是否经过 CB 流程——Claude 须主动提醒该轮是\"提交两组 prompt\"还是\"在我这继续推进\""
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 00016925-05d5-4757-a236-aac40310c879
  modified: 2026-08-05T06:16:20.967Z
---

用户的工作流痛点：有时忘记本轮是否经过了 CB 流程（第三方 Codex/glm组 评估）。

**Why**: CB 流程 = 计划/执行都要进两组评估（提交 prompt → 回收回应 → 反评价收敛 → 拍板 → 执行 → 审计）。用户需要随时知道当前处于哪个环节，否则会混淆"该发两组 prompt"vs"该继续推进"。

**How to apply**:
- 每个任务阶段开始时/推进中，**主动一句话标注当前 CB 状态**：
  - 已过 CB（评估已回收并收敛）→ "进入执行阶段·在我这继续推进·无需提交两组"
  - 需进 CB（计划/执行完成）→ "下一步需提交两组 prompt（评估/审计）"
- 尤其用户在说"继续"时，先明确"这轮是继续执行（已过 CB）还是要发两组"。
- 交接给用户的关键 prompt 用代码块呈现（VSCode hover 可复制）。
- 关联：[[cb-knowledge-base]]（CB 记忆库）、[[cb-prompt-copyable]]（prompt 可点击复制）。
