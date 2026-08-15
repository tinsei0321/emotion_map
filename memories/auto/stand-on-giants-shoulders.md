---
name: stand-on-giants-shoulders
description: 站在巨人肩膀上——优先业界成熟库/规范，避免重复造轮子；主动提醒
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 22e972fb-64fe-47c3-bbb5-efd0c7d69068
---

优先用业界成熟库/规范/做法，**避免重复造轮子**。用户是初学开发者，不熟悉业界方案——要我**主动提醒 + 提优化意见**，时刻站在巨人肩膀上。

**Why:** 用户多次强调。例：3D 网格本来自己写 MapLibre fill-extrusion + 后端聚合 + 归一化（造轮子，效果差），业界成熟方案是 deck.gl（kepler 同款，自动聚合+光影+分位色，效果 kepler 级）。

**How to apply:** 遇到可视化/分析/通用需求，**先查业界成熟库**（deck.gl/kepler/turf/mapbox/等）能否直接用，再自己写。给方案时主动说"业界做法是 X，避免自己造 Y"。CDN/依赖能复用就复用（本项目 deck.gl CDN 已引入，零新依赖）。不要因为"不熟悉"就跳过业界方案——帮用户引入并说明。关联 [[deck-gl-gridlayer-extruded-broken]]。
