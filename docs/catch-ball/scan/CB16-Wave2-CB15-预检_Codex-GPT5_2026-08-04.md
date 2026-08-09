# CB-16 Wave 2 / CB-15 数据认知实施预检（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）  
> **时间**：2026-08-04 | **分支**：`fix/emc-buglog` @ `386a23d`  
> **方法**：现状声明逐条实测核验（place_layer 加载路径/_read_pois 格式/place_name 逻辑/聚合产物）+ 性能与语义推演  
> **范围**：只读评估 · 不改代码 · 不 commit

---

## 结论摘要（先行）

**草案方向正确（下钻链最小闭环五件套成立），但 claude组 探索有一处关键事实错误必须修正（P0），另有 2 个 P1 设计点。**

- **【P0·事实修正】3220 接入的前提不成立**：place_layer 的 `_load()`（`place_layer.py:215-230`）只读 `SCRIPT/poi_data/` 下四文件（157 种子 + 1270 amap + CC缺失 + 7 地标），**不读 `DATA/POI/yichang_pois_wgs84.geojson`**（3220 仍是孤岛）；且 `_read_pois`（`:257-283`）只认 `data['pois']` 键或裸 list——**3220 是 GeoJSON FeatureCollection（features+geometry），即使加路径也会静默返回 []**。接入需三件套：① 新增 FC 读取器（geometry.coordinates → lng/lat + properties 映射）或预转换 ② 加加载路径 ③ 字段映射（3220 有 `category`（中文：住宅/小区）无 `baidu_level1/2/domain/element`——需映射 category→类别字段或扩展 place_layer，domain/element 由评论侧携带、POI 侧可空）。
- **【P1】place_name 语义分层**：POI 优先适合**网格级**（真实数据 hotspot/area_seed 恒空·POI 是唯一真源）；但 **polygon 级（aggregate_by_polygons）建议保留"边界名"语义**（place_name=单元名·POI 作 top_places 增强）——否则大南门 zonal 的 place_name 会从「大南门·二马路滨江片区」变成「xx小区」（语义退化）。且 sim 数据会被 POI 名覆盖（无单测守护·demo 展示变化需知晓）。
- **【P1】/grid/pois 配 cell_id**：`create_square_grid` 现无稳定格 id（CB-15 P0 已定项）——本轮顺带加 `cell_id = origin_x_origin_y`（4546 米制），/grid/pois 参数双收（cell_id 或质心坐标回算）。
- **边界合规**：P0 范围清晰、无越界；place_layer/geocode 只增不改；契约三处同步 + 连续追踪 ID 守则。

---

## 一、现状核验（对 claude组 探索的修正）

| 探索声明 | 实测核验 |
|---|---|
| place_name 只读点侧 spatial_hotspot/area_seed（真实数据恒空·glm 发现属实） | ✅ `spatial_analysis.py:585-597` 确认（`_place_mode`：hotspot 众数→area_seed 兜底） |
| PlaceLayer/get_place_layer/_read_pois/reverse 已存在 | ✅ 确认 |
| reverse_geocode 本地 reverse 主 + 高德 regeo 兜底 | ✅ 确认（`geocode.py:263`） |
| **place_layer 的 _load 已读 3220（DATA/POI/yichang_pois_wgs84.geojson·来源=amap）** | ❌ **不成立**：`_load` 只读 SCRIPT/poi_data/ 四文件；3220 未在任何加载路径 |
| 3220 孤岛 | ✅ 确认（与 CB-15 预检一致） |
| **额外发现**：`_read_pois` 格式 | 只认 `data['pois']` 或 list——3220 是 FeatureCollection（features+geometry）→ 加路径也返回 []（静默） |

---

## 二、七问逐答

### 1. place_name 双源融合对路；性能用"格原点查找"更优

- **方案对路**：POI 优先（真实数据唯一真源）→ hotspot → area_seed（sim 兼容），与 glm 致命发现闭环。
- **性能**：3220 POI × N 格 sjoin（geopandas rtree）毫秒级可接受；但**更优实现 = 纯 numpy 格原点查找**——`create_square_grid` 的格是 4546 方格（`floor(x/cs)*cs`），POI 坐标同样 floor → 查 `origin → cell` 映射，O(P) 无空间索引、确定性、零依赖。聚合期用此法建 poi_names；/grid/pois 按需重查可复用同一映射（缓存）。
- **语义分层（P1）**：网格级 POI 优先 ✓；polygon 级（zonal）保留边界名 + POI 作 top_places——避免"大南门 zonal place_name → xx小区"退化。统一 POI 优先对 sim 数据是展示名变化（无单测守护），需知晓。

### 2. poi_names：结构化 JSON 数组 + top-N（10-20）

- **推荐 JSON 数组**（非逗号串）：下游（前端渲染/出口卡/未来 lookup_place）可直接消费；逗号串是展示形态。
- **top-N**：400m 格密集区 POI 可达数十个，列内 cap **10-20**（建议 10·配合 /grid/pois 全量）；空格空串/[]。
- 防配额爆：列内 top-N + 全量按需走 /grid/pois ✓ 双层范式成立。

### 3. /grid/pois：参数双收 + 返回 rows 风格结构

- **请求参数**：`cell_id`（推荐本轮加·origin 键）**或** `centroid`（质心坐标·前端点击自然带 geometry）——双收，前端点击/LLM 均可用。
- **返回**：`{count, pois: [{name, category, domain, element, lng, lat}]}`（3220 的 domain/element 空·由评论侧补——P1 归因落点再接入）。
- 与 zonal/rank rows 结构兼容（rows 风格·确定性组装）。
- **LLM 用法**：P1 lookup_place 之前，本轮前端点击先用（悬停试探/点击锁定范式）；可选轻量工具（"这格有什么地点"）——非必须，防范围膨胀。

### 4. 3220 接入：不能"复用 place_layer"了事——需显式三件套（P0）

- 加 FC 读取器（或预转换脚本）+ 加路径 + 字段映射（category→类别·baidu_level 缺省）。
- **去重规则需明确**：3220 与 1270 高德重叠（poi_id 同源）——建议 `poi_id` 去重、1270 优先（保 baidu_level 类别 + zone 归属），3220 补 1270 未覆盖（中心城区外围）。或 3220 为主 + 1270 类别回填——需定一条，写进测试。
- 独立"问答管线可见的 POI 消费层"（lookup_place 工具 + buildContext 注入）属 P1，本轮 sjoin 用 place_layer 数据即可。

### 5. 承重零触碰 + 回归评估

- 不碰 diagnose/harness/ChatRequest ✓；place_layer/geocode 只增不改 ✓。
- **回归**：place_name 改动在 `_attach_4x5_attrs`（zonal/grid/hex 共用）——实测**单测无真实聚合 place_name 断言**（test_outlet_schema 的 ermawu 用例是 mock result·不受影响）；B3 PRM/RST 不断言 place_name。**回归风险主要在 demo 展示语义**（sim place_name 被 POI 覆盖）。建议：新增 place_name 融合单测（POI 优先/hotspot fallback/area_seed 兜底三路径）+ 全量 pytest 回归。

### 6. 测试方案够；补 3 个边界用例

- 单测：place_name 三路径融合 · poi_names top-N/空 · /grid/pois 参数（cell_id/centroid）与返回结构 ✓。
- 建议补：① 3220 去重用例（poi_id 重叠）② sim fallback 兼容（hotspot 非空时行为）③ 空 POI 格（poi_names 空·不崩）。
- E2E（ermawu + 3220 sjoin 出地点清单）✓。

### 7. 边界无越界 ✓

- 本波 P0 五件套与 P1/P2 后置清晰；无承重触碰；契约三处同步 + 连续追踪 ID 守则（新端点/工具注册新 F_*）。

---

## 三、风险与优先级

| 级别 | 项 | 处理 |
|---:|---|---|
| **P0** | 3220 接入前提修正：FC 读取器/路径/字段映射（现状"已读"不成立 + `_read_pois` 解析不了 FC） | 三件套 + 单测（load 后 count=3220·reverse 命中） |
| **P1** | place_name 语义分层（网格 POI 优先 vs polygon 保留边界名） | 按聚合形态分支·防大南门 zonal 语义退化 |
| **P1** | /grid/pois 配 cell_id（顺带本轮加·CB-15 P0 定项） | 参数双收 + 聚合输出加列 |
| **P2** | poi_names JSON 数组 + top-N 定值（10） | 列内 top-N + 全量按需 |
| **P2** | 3220 去重规则明确 | poi_id 去重 + 测试 |
| **P2** | sim demo place_name 展示变化 | 知晓·验证时肉眼确认 |

---

## 四、判定

- **草案可行**：下钻链最小闭环五件套方向正确，双层触发范式（聚合带 top-N + 按需 /grid/pois）与 CB-15 共识一致。
- **P0 修正 1 项**：3220 接入前提（加 FC 读取 + 路径 + 字段映射）——"复用 place_layer（已读）"不成立。
- **P1 设计 2 项**：place_name 语义分层（polygon 保留边界名）；cell_id 配 /grid/pois。
- **P2 细节 3 项**：poi_names 结构化+top-N；3220 去重；sim 展示变化知晓。
- **边界合规**：零承重触碰，P1/P2 后置清晰。

---

*本报告为 Codex 组独立评估；现状核验基于当前工作树实测（place_layer 加载路径/_read_pois 格式/place_name 逻辑/测试依赖），未参考其他组报告。*
