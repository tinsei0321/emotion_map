---
name: tool-no-auto-overview
description: 工具生成图层（grid/heatmap/buffer/terrain）不自动弹 Overview/Table——只 selectLayer+layers:changed，不 dispatch layer:selected
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2587ac02-97a0-4c3e-940c-c57d28996cd8
---

工具生成/调整图层时**不要自动弹开 Overview/Table 窗口**（用户需求 2026-06-29）。

**根因**：main.js `layer:selected` 监听 → `openRightPanel() + activateTab('overview')`。grid/heatmap/buffer 生成时曾 dispatch 它 → 强制弹右栏 Overview。

**规约**：工具生成处（grid-tool `generateGrid`、heatmap-tool `generateHeatmap`/`generateTerrain`、buffer-tool `generateBuffer`）只做 `selectLayer(id)` + dispatch `layers:changed`（后者只刷新列表/图例/Overview 内容，不弹右栏、不切 tab）。**不 dispatch `layer:selected`**。

**保留**：用户点图层行（sidebar `selectLayerRow`）仍 dispatch `layer:selected` → 正常弹 Overview（不变）。

**Why**：调参/生成是高频操作，每次弹 Overview 打断流；Overview 留给主动点击查看。
**How to apply**：新工具生成分支照此规约；`selectLayer` 让 Overview 内容跟随选中层（面板已开时刷新），但不强制弹。
