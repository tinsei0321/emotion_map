---
name: view-data-conclusion-sync
description: Overview=互动指挥台；视野/数据/结论三端同步；橙色高亮 + sticky 锁定设计语言
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b93ee6eb-6608-430a-8fe9-09999cc75872
---

Overview 不是只读报表，是**互动指挥台**。演示铁律「视野-数据-结论 同步性」（已入 CLAUDE.md 演示逻辑链）：地图视野、Overview 数据、归因结论三端，任何一端 hover/click 另两端即时联动。

**同步高亮设计语言**（全 Overview 统一）：
- 基础设施在 [tip-popup.js](frontend/js/tip-popup.js)：`highlightCellSet(features,layer)` / `clearHighlightCellSet()` / `toggleStickyHighlight(features,layer,key)` / `resetHighlightCellSet()`，独立于 `showCellHover`（地图直接悬停单格）。
- 叠加层 `cell-hl-set` / `cell-hl-set-layer`：3D = fill-extrusion **橙 #ff9000 / opacity 1.0**（高度同原柱，覆盖不拔高）；2D = line 橙外轮廓。
- **悬停=试探**（瞬时，mouseleave 回 sticky 或清）；**点击=锁定 sticky**（再点同项释放、点异项切换）。`_stickySet` 跨 hover 保留。
- 触发源（panel.js delegated on `#overview-pane`）：饼图 slice → 该极性**主导**格（`_dominantPolarityOf`/`_cellsByPolarity`）；4×5 矩阵格 → domain×element 桶（`_cellsByBucket`）；关键词 → top-N 最强聚集（`_topKeywordCells` + `fitBoundsTo` bbox）。

**Why**：演示要"图面张力→引导点击→交互分析→识别问题"贯通；只读 Overview 断了交互环。**How to apply**：新增 Overview 数据元素（图表/列表）必须接同一套 hover/click→highlightCellSet；地图直接悬停单格仍走 showCellHover（不混淆）。换色/改 sticky 模型先改 tip-popup 这一处。

关联：[[tip-popup-unified-hover-design-language]] [[emotion-map-logic-chain]] [[design-language-consistency-iron-rule]]
