---
name: timestamp-no-weekday
description: "todo/revision-log/handoff 时间戳只写\"MM月DD日 HH:MM\"（24h），不写星期几——反复算错"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9fe6a469-6f33-49eb-a04a-560a09add4f6
---

todo.md / revision-log.md / session-handoff.md 的时间戳一律 `MM月DD日 HH:MM`（24 小时制），**不写星期几**。

**Why**：星期几心算易错（2026-07-06 实为周一，我反复误写"周日"），用户多次纠正。日期+时间已满足"准确时间"要求，星期几是冗余信息。

**How to apply**：
- 日期分段标题（todo `## 📅 YYYY-MM-DD`）：直接 `## 📅 2026-07-06`，不带 `（周X）`。
- revision-log 5.x 小节标题：`（07月06日 13:25）`，不带星期。
- handoff「最后更新」行：`07月06日 13:25`。
- 确需星期：用代码/工具算（如 `date +%A`），勿心算。

关联 [[time-format-date-hm]]（时间戳写"MM月DD日 HH:MM"格式的原始约束）。
