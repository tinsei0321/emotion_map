---
name: paint-inplace-swap-view
description: "View-switching features (极性深读/时间轴) swap paint on the existing layer in-place, NOT hidden layers; backup _overallPaint to restore"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9fe6a469-6f33-49eb-a04a-560a09add4f6
---

「视图切换」类功能（极性深读切极性、未来时间轴切时间点）一律用**paint 就地切换**，不要注册隐藏图层。

**Why**：原设想「后台生成 3 个极性图层不显示在 Layers」会在 `renderLayerList`/`enforceMutualExclusion`/`refreshOverview`/funnel 计数处处加 `_panelHidden` 排除（易漏且与承重冲突）；隐藏层 `setLayerVisible` 会触发 refreshOverview 抢焦点，破坏当前 Overview 视图。paint 切换零新图层、不碰 _layers、Range 自动保留。

**How to apply**：
- 综合 grid 的 fc 经 `preprocessGrid` 已算好分极性字段（`_grid_h_pos/neg/neu` 高度 + `_grid_n_pos/neg/neu` 计数），切极性 = 改该层 `paint.gridField/gridStops/heightField` + 加 `paint._polarityFilter=['>',['get','_grid_n_<pol>'],0]`（藏零计数格）+ `renderLayer` 重敷。
- 生成时备份 `paint._ui._overallPaint = {gridField, gridStops, heightField}` 作还原锚点（[grid-tool.js generateGrid](frontend/js/grid-tool.js)）。
- `map.js addPolygonPaint/addHitLayer` 透传 filter 须**条件展开**（`...(filter?{filter}:{})`）——MapLibre addLayer 拒绝 `filter:undefined`，会 throw `array expected, undefined found`。
- 颜色+高度同源切（gridField = heightField = `_grid_h_<pol>`），否则色与柱高不一致。
- 离开视图（activateOvTab('layer')/换层/删层）→ `_clearPolarityView` 读 _overallPaint 还原 + delete filter + renderLayer。

时间轴（任务2）同理：切时间点 = setData 新 fc + paint 切，不注册 T1/T2/T3 三个隐藏层。关联 [[generate-grid-exclusive-vs-viewmode]]（paint 切换与 setViewMode 2D/3D 独立、勿耦合）。
