---
name: timeline-must-be-data-driven
description: 时间轴必须按上传数据的时间点驱动，不能硬编码 T1/T2/T3
metadata: 
  node_type: memory
  type: project
  originSessionId: e81be54e-ab00-45f0-9b55-72776c707366
---

时间轴（timeline.js）当前硬编码 T1/T2/T3 三个时间点跑动画——即使用户只上传了一个时间点的 L2 数据，时间轴仍能跑出 3 个点（因为后台有模拟快照 `_snaps.T.T1/T2/T3`，scaffold 复用 layer.fc.features）。

**问题**：换一组数据就会出错（时间点与数据不匹配）；未来真实数据会有多个时间点、甚至以 日/周/月 为单位的周期性数据，不是固定 3 点。

**Why**：用户 07月07日 指出——时间轴必须依据实际上传/加载的数据来跑，时间点集合从数据推导（按数据的时间字段/快照数量），而非固定 3 点。

**How to apply**：重新设计 timeline 时，时间点 = 数据驱动（扫已载层的快照/时间字段生成时间轴刻度）；模拟期可保留 T1/T2/T3 作为 demo 数据，但机制要通用。**当前状态：待办（用户说先记录、后做）**。

关联：[[three-page-architecture]]（控制台·时间轴是其中一环）、[[paint-inplace-swap-view]]（时间轴就地 patch KPI）。
