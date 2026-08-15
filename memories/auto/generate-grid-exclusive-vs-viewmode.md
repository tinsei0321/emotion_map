---
name: generate-grid-exclusive-vs-viewmode
description: Grid 两个独立场景——generateGrid 独占清场 vs setViewMode 视图按钮配对切换；勿耦合
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3540e2cb-de7a-41ff-9b4b-943098af252f
---

Grid 工具的两条**独立**逻辑，分属不同用户动作，改动时**勿互相耦合**（曾因此破坏独占）：

1. **`generateGrid` 独占（清场）**——用户**生成新网格**时，新建态必须**关闭其他所有可见层**（不只 grid 层），让新图独占视野（仿 heatmap `generateHeatmap`）。编辑态（要素按钮）则**原地更新当前层、不关他层**（layer id 稳定）。代码 [grid-tool.js:364-378](frontend/js/grid-tool.js#L364-L378)。

2. **`setViewMode` 配对（视图按钮）**——用户点左下 `btnView` **切换 2D↔3D**：只动 `paint._ui.tool==='grid'` 的**可见 grid 层**，按 `gridSig`（analysis|level|source|cellSize|polarity|polygonLayer，**不含 mode**）找配对 target 层；无配对则用**同 fc 生成独立层**（3D→fill-extrusion 柱 / 2D→fill 色块，fc 共享不重跑后端）。支持多 grid 层 / 2D+3D 混合共存。代码 [map.js:104-133](frontend/js/map.js#L104-L133)。

**Why:** 上一轮为支持视图按钮「多图层共存」，误把 `generateGrid` 新建态改成「跳过其他 grid 层」→ 破坏了独占语义（用户报「生成新网格没关其他图层」）。用户明确「不要再犯，两个场景独立」。memory: `spatial-aggregation-numeric-coerce` 同期。参见 [[kde-loadbearing-logic]]（独占显示同源）。

**How to apply:** 改 `generateGrid` 任何分支 → 核对新建态仍关**全量可见层**；改 `setViewMode` → 核对只动 grid 层 + gridSig 不含 mode。两边各改各的，别为一边动另一边。
