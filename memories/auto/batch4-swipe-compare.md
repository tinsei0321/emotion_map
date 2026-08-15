---
name: batch4-swipe-compare
description: 批4 时间对比已实现（双 map Swipe 卷帘·grid-only mirror）——⚠️ 依赖 manifest·404 时与时间轴同不可用（③w2 专题后置）；3D compare polish 待办
metadata: 
  node_type: memory
  type: project
  originSessionId: b4313e60-747e-46a0-a954-91863e5ac9d0
  modified: 2026-08-04T12:58:40.798Z
---

批4 时间对比（宏观 thesis 5.148 首落地·治前 vs 治后 grid 演变）= **Swipe 卷帘**（单地图架构下双 map 实例各 clip 一半——MapLibre 不支持层屏幕裁剪，双 map 是唯一路径）。**已实现**（map.js `_mapB/_enterCompare` + time-bar compare toggle + timeline.renderSliceToMap 在仓）。**⚠️ ③w2 发现：依赖 manifest slices·manifest 404 时与时间轴一起不可用（静默降级）**——用户定开专题重规划时间轴，compare 一并待续。**待办**：mapB 底图/暗 overlay 在 3D compare 的视觉同步（polish·2D 不影响）。

**架构**：
- `map`（mapA，既有）+ `_mapB`（[map.js](frontend/js/map.js) 第二实例，同 basemap，lazy 建于 `_enterCompare`）同位叠加 `#map`。
- manual 双向 sync（mapA↔mapB `move`→`jumpTo`，`_syncing` 防反馈环）。
- clip divider（`_setDivider`→mapB `clip-path: inset(0 0 0 pct%)`；clip-path 同时切视觉+事件，左半事件穿透到 mapA）。
- `_mirrorLayersToMapB`：**grid-only**（`_focusedGridId` 找焦点 grid，只镜像 `lyr-{gridId}`+子层；points/range 不上 mapB 避免片不一致）。**非侵入**——读 mapA.getStyle() 复制，不动 renderLayer（承重 mapA 路径零改动）。
- A/B 时间：mapA=片A（既有 renderSlice），mapB=片B（`timeline.renderSliceToMap(mapB, key)` 纯 setData grid source）。

**cycle 约束（关键）**：timeline→map（import updateGridSourceData），故 **map 不能 import timeline** → grid A/B 由 **time-bar 编排**（time-bar import timeline + map.getMapB）。map↔time-bar 经事件解耦：`compare:mapBready`（mirror 完，time-bar 设片B）/ `compare:exit`。

**time-bar compare-aware**：`_activeSliceKey()`（compare 显 B / 否则 A）+ `_pick` compare-aware + 「对比」toggle 按钮（卡片头）+ A/B 地图角标（A 蓝 / B 橙）。进 compare = `'c'` 键或「对比」按钮。

承重：**mapA 路径 + paint-inplace-swap-view 零改动**；mapB 是只读跟随（mirror 结构 + renderSliceToMap 片B 数据）；compare 是 toggle 不改默认单 map 体验。**待办**：mapB 底图/暗 overlay 在 3D compare 的视觉同步（polish；2D compare 不影响）。详见 plan §批4 + revision-log 5.149-5.153。关联 [[global-time-axis]] [[paint-inplace-swap-view]]。
