---
name: maplibre-query-array-stringify
description: MapLibre map.queryRenderedFeatures 返回的 properties 只支持标量，数组/对象字段会被序列化成字符串
metadata: 
  node_type: memory
  type: reference
  originSessionId: 450f231f-e51a-4fd7-8f99-06d6aadcbffe
---

MapLibre GL 的 `map.queryRenderedFeatures()` 返回的 `feature.properties` 经过 worker 序列化传输，**只保留标量值**（string/number/boolean）。数组/对象类型的 property 会被 `JSON.stringify` 成字符串。

实测（Task 2.7）：source data 里 `properties._center = [111.28, 30.70]`（数组），但 `queryRenderedFeatures` 返回的同一 feature `_center = "[111.35,30.74]"`（字符串）。后端 geojson 直接持有的 fc 不受影响，仅 queryRenderedFeatures 的返回值被转。

**影响**：前端从 queryRenderedFeatures 拿 feature 后读数组类 property（如 `_center`/`keywords`）会拿到字符串 → `c[0]` 取到 `"["` 而非 lng → 后续 reverseGeocode/逻辑必败。

**How to apply**：读 queryRenderedFeatures feature 的数组类 property 时**必类型校验**（`Array.isArray(p._center) && p._center.length === 2`），字符串则回退用 geometry 重新算（bbox 质心等）。或干脆**不依赖数组 property**，从 geometry 现算。关联 [[js-chinese-identifier-trap]]。
