---
name: discuss-archive-index
description: CB 讨论归档已立（主题卷宗制·按内容不按时间）——查 CB 结论先 discuss/_INDEX.md，过程稿在 archive/<卷宗>/，权威口径认注册表/CLAUDE.md/总账
metadata: 
  node_type: memory
  type: project
  originSessionId: fb8b3318-4b05-4023-b4e0-70918d220a89
  modified: 2026-08-22T06:11:28.094Z
---

discuss/ 讨论稿归档机制 2026-08-22 立（用户交办·主题卷宗制）：**按内容（卷宗）切不按时间切**，与 todo 周归档互补。结论稿（定稿/终审/拍板版）常驻 `discuss/` 顶层；过程稿随主题生命周期终结（定稿+实施完+零待办）`git mv` 下沉 `docs/catch-ball/discuss/archive/<卷宗>/`。卷一「城市体检专项」已归 134 件（CB23 系 + CB24-37 + 散件）。触发 = 每轮 CB 收官时收敛方顺手归当轮过程稿（四步：git mv → _INDEX 更新 → _DIGEST 补行 → 全仓 grep 同步引用）。

**在途保护**：EMC×dsh（卷四）/RAG（卷五）相关永不自动归档（用户明示·归档清单必带排除表）。

**消费路径**：查 CB 结论 → `docs/catch-ball/discuss/_INDEX.md`（活跃索引：在途组+常驻结论）；查过程细节 → 对应卷宗 `_DIGEST.md` 导览后进卷宗全文；**权威口径永远认口径注册表/CLAUDE.md/总账——digest 只导览不背书（防双头）**。批二~四（PT 系/CB-38~41/早期 CB09-21）待用户触发·不自动跑。CB 蒸馏总库见 [[cb-knowledge-base]]。
