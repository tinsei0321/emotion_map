---
name: auto-update-progress-docs
description: "用户说\"更新进度\"时自动同步 todo/emc-fix-progress/revision-log 三文档"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f1fad2d4-15b8-4af6-aa1b-e176fe5287f0
  modified: 2026-07-28T06:10:36.338Z
---

用户说「更新进度」时，自动识别并同步以下文档（保持最新状态）：

1. **[docs/todo.md](docs/todo.md)** — 当日段（倒序）·当前状态 + 计划 + 遗留。
2. **[docs/emc-fix-progress.md](docs/emc-fix-progress.md)** — §一 矩阵（9 模块实施状态）+ §四 时序（版本表）+ 顶部「更新」戳。
3. **[docs/revision-log.md](docs/revision-log.md)** — §5 顶部「最新动态」+ 新条目。

**Why**: 用户多次发现文档滞后于代码·要求自动同步。三文档是监控 + 交接的核心载体。

**How to apply**: 每次完成 commit + push 后·或用户说「更新进度」时·检查三文档是否反映最新 commit 状态。尤其注意：
- 版本号 / commit hash 一致。
- 架构版本标注（当前 v3.1·v1→v2→v3 转型线）。
- emc-fix-progress §一 矩阵的「实施」列反映当前版本。
- todo 当日段在最顶部。
