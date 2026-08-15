---
name: terrain-mesh-rendering
description: 情绪地形 L2 3D = KDE 等值面 mesh（matplotlib contourpy）→ MapLibre fill-extrusion 分层，勿回退 deck.gl
metadata: 
  node_type: memory
  type: project
  originSessionId: 2587ac02-97a0-4c3e-940c-c57d28996cd8
---

情绪地形（L2 3D）的渲染链与算法（feature/kde-l2-3d，2026-06-29 落地）：

**后端** `core/spatial_analysis.py:create_terrain_mesh`（`@track MOD_SPATIAL.F_007`，路由 `POST /api/v1/spatial/terrain`）：
- 点→EPSG:4546→加权 `histogram2d`（权重=emotion_intensity，1~5 归一）→纯 numpy 可分离高斯卷积（`_convolve_separable`，不引 scipy）→分位 levels。
- 等值面：`contourpy` `contour_generator(..., line_type=Separate).lines(L)` 每级取环（"z≥L" 峰区边界，无空洞歧义）→ Polygon。
- `_level=(L-Lmin)/(Lmax-Lmin)` 归一化 0~1（**不是 L/zmax**——quantile 远小于峰值会压扁高度）；features 按 `_level` 升序（fill-extrusion 低先画、高压顶免 z-fighting）。
- 依赖 `matplotlib`（contourpy 随附，requirements 已加）。

**前端**：heatmap-tool `generateTerrain` → `runTerrain` → `addLayer({kind:'polygon', _ui:{tool:'terrain',mode:'3d'}})`。map.js `addPolygonPaint` 把 `tool==='grid'||'terrain'` 共用 fill-extrusion 管线（`_gridColorExpr` + `heightField` + `maxHeight`）。

**算法语义（混合）**：高度恒为 `_level`（密度×强度=地形高程）；颜色=综合 `_norm`(polarity_index→terrain-9) / 极性 `_level`(green-3/red-3/blue-3)。综合=红/绿高地（消极/积极浓集），极性=该极性密度峰。

**承重勿动**：
- deck.gl GridLayer extruded 在 MapLibre 不渲染（见 [[deck-gl-gridlayer-extruded-broken]]），terrain 也走 fill-extrusion，勿试 deck.gl。
- 环按 `_level` 升序输出是 z-fighting 关键，勿打乱顺序。
- `bindTerrainInteractions`（map.js）绑 extrusion 层 mouseenter → 段落式 `.terrain-tooltip` popup。
- 生成 terrain 不 dispatch `layer:selected`（工具层不自动弹 Overview，见 [[tool-no-auto-overview]]）。
- terrain categoryOf='terrain'（独立组卡 CATEGORY_LABEL '情绪地形'）。
