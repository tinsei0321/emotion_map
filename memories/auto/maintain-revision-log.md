---
name: maintain-revision-log
description: "After every commit, append a row to docs/revision-log.md; translate user intent into professional wording"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 37c73a6f-6b0f-40d8-a99f-fb15b12069c5
---

每次 commit 后，在 `docs/revision-log.md` 第 5 节对应板块追加一行（日期 | commit | 用户意图 | 文件）。

**Why:** 用户（非程序员）要一份能回顾"我提过什么要求、为什么、怎么落地"的修订记录，按架构/功能板块归纳。revision-log.md 是用户意图视角，与 dev-notes.md(技术心得)、todo.md(每日任务) 三分互补。

**How to apply:**
- 用户意图须**专业化精炼转译**，不照抄口语原文（例："那个颜色不对" → "L2 中性色板应与急/盼胶囊蓝色系呼应"）。
- 跨板块的设计主线变更（新全局交互范式/术语调整），同步更新 revision-log 第 4 节"设计意图脉络"和第 2 节术语表。
- 一个完整需求（可能跨多 commit）合并为一条；纯 bug 修复可并入相邻条目。
- 术语铁律：类型=大类(喜怒哀乐愁急盼,固定7) / 表现=小类(动态归纳)；栏=浅蓝填充 / 选项=粗蓝框+浅灰填充。见 [[chinese-all-deliverables]]。
- **任务树全程维护**：revision-log 第 7 节"任务路线图"是树状任务跟踪（主线批1-5 + 子分支 + 临时分支 + 状态⬜🔄✅⏸❌）。产生新分支（修 bug 发现新任务 / 某批分前置 / 新需求）→ 立即追加对应节点 + 更新状态，不靠会话记忆。会话分段/新会话读此即接上全部任务。配合 [[token-saving-workstyle]]。
- **任务树平衡规范**：同级任务重要性视觉平衡（看起来差不多重）；不平衡时增/减分级层次——叶（最小子任务，如 1a/1b）收敛进详细摘要（不进树），后续/活跃模块补第二级子项（Range→缓冲区/叠加/聚合 等）。保持树清晰、准确、像一棵平衡生长的树。
