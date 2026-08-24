---
name: excel-sync-for-ppt-tables
description: 图数表出图——PPT 表格 Excel 由 Codex 组负责制作·正式文件 DATA/analysis/图数表出图_PPT表格汇总.xlsx（每 page 一个 sheet·表间空行·无颜色填充）·claude组 通知与验收
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1fa86586-57ed-40af-b5a3-3d4d770f8375
  modified: 2026-08-13T01:48:40.323Z
---

PPT 图数表出图工作流（2026-08-13 用户定）：md 表格内容要同步到 Excel 方便粘贴 PPT；**Excel 制作任务固定由 Codex 组负责**（三版对比后用户选定 Codex 版；RULES.md §5.1.2 固化分工）。

**Why**：md 表格无法直接粘贴进 PPT；用户对比 claude/codex/zcode 三版后选 Codex 版为正式做法。

**How to apply**：
- 正式文件唯一位置：`DATA/analysis/图数表出图_PPT表格汇总.xlsx`（Codex 负责写·权限例外见 RULES §5.1.2）
- 结构：每个 sheet 对应一个 page（sheet 名 pageN）·page 下各表纵向排列、表间空 2 行·每表前一行表名
- 排版：简单专业——表头加粗 + 细边框 + 列宽自适应 + 同值列合并单元格；禁止颜色填充
- 范围：只做 PPT 用数据表（图数据源/文件索引等工作用表不做）
- **claude组 职责**：每完成一个 page 的 md → 发 prompt 通知 Codex 补对应 sheet（prompt 含：数据源 md 路径+该页表格清单）→ Codex 落盘后验收（sheet 名/表格齐全/数字与 md 一致）
- 推进节奏：逐个 page（page1 已完成·Codex 版在位）

关联：[[cb-third-party-no-git]]（Codex 权限口径）· [[chinese-all-deliverables]]
