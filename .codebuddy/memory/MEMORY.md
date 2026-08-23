# MEMORY.md — 长期记忆

## 工具与 harness 架构（稳定事实）
- CodeBuddy 与 WorkBuddy **同源（腾讯平台）**，底层 harness/引擎同一套。
- **主手执行 = zcode**。CodeBuddy/WorkBuddy 是平台外壳，非独立执行引擎（勿误判为包裹 Kimi 的薄壳）。
- catch-ball 中 Kimi/OPUS 等是特殊派发的外部评估/执行对象，不代表 WorkBuddy 平台本质。
- 任务结果差异来自 zcode 主手拆解 + 仓库领域栈（契约/口径/追踪纪律），不来自选哪个腾讯平台外壳。
- 双环境（家/办公室）同步纪律见 AGENTS.md「双环境同步机制」+ `docs/catch-ball/_handoff/HOME.md`、`OFFICE.md`。
