---
name: poi-library-is-place-layer
description: 项目无 SQL 数据库；POI「库」= core/place_layer.py 单 owner 内存库（4 JSON 装载，喂 /place/search + reverse）
metadata: 
  node_type: memory
  type: reference
  originSessionId: ab9ecdfe-67aa-400a-9932-8d2c86b24a90
  modified: 2026-07-21T12:18:08.383Z
---

情绪地图项目**无 SQL 数据库**（`db.py` 已于 CB-1 退役 commit 8cea41a）。POI「库」= [core/place_layer.py](../../../../../d/Github/emotion_map/core/place_layer.py) 单 owner 内存 POI 库（单例 `get_place_layer()`，模块导入懒加载一次）。

**装载源**（4 个 JSON，字段 `lng/lat/name/area/baidu_level1/baidu_level2/domain/element/radius_m/source`）：
- `SCRIPT/poi_data/amap_poi_wgs84.json`（1270 真实高德·西陵伍家核心主城）
- `SCRIPT/poi_data/amap_poi_centralcity_wgs84.json`（中心城区；2026-07-21 起为真实 3220 POI，`source='amap_cc'`，由 `ingest_centralcity_poi.py` 产出；原是 `sim_centralcity_poi.py` 的 sim_cc fallback）
- `SCRIPT/poi_data/yichang_poi_wgs84.json`（158 手标种子）/ `landmarks_wgs84.json`（手标地标）
- `all_pois = amap_pois + landmark_pois`（seed 退命名不参与）→ 喂 `/api/v1/place/search`（`forward()`）+ `reverse()`

**入库新数据**：写转换脚本（字段映射 + 4×5 派生 + `source` 标识）→ 覆写上述 JSON 之一，**place_layer 零代码改动**自动装载（`_AMAP_POI_CC_PATH` 直指文件）。`_read_pois` 加载期 drop 未知字段（如 poi_id）。新 POI GeoJSON schema（name/address/category/keyword/district）与 place_layer schema 不同，需映射（category→baidu_level1 保真、keyword→baidu_level2、district→area）+ 4×5 派生（高德 13 大类走 `poi_4x5_map.AMAP_L1_TO_4X5`；自定义短大类写专属 `_CAT_TO_4X5`）。

**搜索后端链**：前端 `search-bar.js searchPlaces()` → `/api/v1/place/search` → `core/geocode.py search_place()` → `place_layer.forward()`（本地主）+ 高德 place/text 兜底（AMAP_KEY 有时）。boundary preset 走 `core/range_selector.py` manifest（`DATA/boundaries/presets/manifest.json`），`geo_registry.list_boundaries()` 暴露给 EMC/geo 工具。

2026-07-21：all_pois 4497（1270+3220+landmark）。详见 [[cpd-soft-collapse]] 同期。
