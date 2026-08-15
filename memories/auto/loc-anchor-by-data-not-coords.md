---
name: loc-anchor-by-data-not-coords
description: 地点类 tip/标记必须按数据（点层 POI/地名）锚定，禁止猜坐标——曾致奥体错位致命错
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fed1d60a-02fb-4599-aa2e-975832ec5441
---

地图上地点 tip / 标记 / 聚合域高亮，锚定坐标必须**来自用户加载的数据**（点层 POI 的 area_seed/spatial_hotspot/坐标），**禁止我在副本/代码里硬编码猜测 lngLat**。

**Why**：5.27 前副本硬编码奥体=(111.20,30.60) 是我猜的，实际(111.226,30.705)，偏 0.06/0.1 → tip 指到错误聚合域。用户 POI 数据准确，我猜坐标=致命错（"错误很多""不能再犯"）。

**How to apply**：
- 副本只存**地名**（`locs:[name]`），不存 lngLat。
- 锚定时去 grid 源点层（`layer.paint._ui.source = group:gid`→children 合并 fc）按 `area_seed`/`spatial_hotspot` `includes(name)` 找真实 POI → `m.geometry.coordinates` → 最近 cell._center（`_resolveLocAnchors` in [panel.js](frontend/js/panel.js)）。
- 数据无该 POI → **跳过 tip**（不显示 > 错误显示）。
- 新地名先用 `area_seed` 实测确认存在再用（`py` 一次性 grep）。

关联 [[paint-inplace-swap-view]]（视图切换）、[[view-data-conclusion-sync]]（视野-数据同步铁律）。
