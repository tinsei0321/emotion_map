---
name: topo-sync-discipline
description: 新子系统 → 加 revision-log §0 分支 + topo_scanner 语义边（auto-in-topology），防拓扑图漂移
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7eba1cd7-80b4-4a74-92f4-5a5c6807de5e
  modified: 2026-07-19T05:47:41.124Z
---

新增任何子系统（如 CB 闭环、未来运维/安全模块等）时，须同步更新动态拓扑图（topology.html ← `core/topo_scanner.py`），避免拓扑图与项目态漂移：

1. **§0 任务树加分支**：`docs/revision-log.md` §0 加该子系统分支（组件 + 状态 emoji）→ `_parse_revision_tasks` 解析 → roadmap 视图显该子系统。
2. **topo_scanner `_add_semantic_links` 加语义边**：若子系统组件关系非 import 驱动（如 .md 文件间引用），在 `_add_semantic_links` 加该子系统的 relation 边（仿 cb-flow / doc-of / test-of 模式，type 自命名）。
3. **登记 `docs/context-map.md`**（守记忆共享通则）。

**Why**：用户在 CB-03 后要求"动态拓扑图加入 CB 机制"——拓扑图是项目的自文档化视图（topo_scanner 实时扫），新子系统不入图 = 拓扑与项目态漂移、误导新人/第三方。

**How to apply**：新建子系统时（不只 CB），过这三步。CB 闭环为首例（CB-03 收尾落地，cb-flow 边 + §0 Catch-Ball 分支）。关联 [[context-coherence-discipline]]、[[cb-knowledge-base]]。
