---
name: deck-gl-gridlayer-extruded-broken
description: deck.gl GridLayer extruded(3D 方柱)在 MapLibre+MapboxOverlay 不渲染，3D 改用 ColumnLayer
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 22e972fb-64fe-47c3-bbb5-efd0c7d69068
---

deck.gl@9.1.0 的 **GridLayer extruded:true（3D 方柱，内部 GridCellLayer）在 MapLibre + MapboxOverlay 环境不渲染**——canvas 在 DOM、层构造成功、数据进层（2000 点）、viewState/z-index 都对，但完全空。

但对照测试确认：**2D（extruded:false 色块）✓、ScatterplotLayer ✓、ColumnLayer（3D 圆柱）✓** 都正常渲染。问题只在 GridLayer（及可能 HexagonLayer）的 extruded 方/六边柱 shader。

**Why:** 踩坑——长时间排查（疑 cellSize 单位/viewState 同步/z-index/CDN 缺层），最后用 ScatterplotLayer→GridLayer 2D→ColumnLayer 3D 逐步对照才定位是 GridLayer extruded 特定问题。addHotpointLayer 之前搁置可能同因。

**How to apply:** **最终用户放弃 deck.gl**（ColumnLayer 圆柱/方柱效果都不及 kepler 理想），3D 网格回 **MapLibre fill-extrusion**（自创，`addPolygonPaint` grid 分支，opacity 1 实心 + 3D 去线框 + `_grid_h` 高度分位）。**不要用 deck.gl GridLayer/HexagonLayer extruded**（方/六边柱在 MapLibre+MapboxOverlay 不渲染）。若未来重试 deck.gl 3D，先用 ScatterplotLayer→ColumnLayer 对照确认渲染管线，且管理预期（光影不及 kepler）。关联 [[verify-real-endpoint]] [[stand-on-giants-shoulders]]。
