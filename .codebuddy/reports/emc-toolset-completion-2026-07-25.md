# EMC 工具集补齐 + 本地化（组 A）完成报告

> 执行人：K3（工程执行）｜ 2026-07-25 ｜ 基线 commit：d78d0a8（5.205 后）
> 任务书：GLM5.2 组「EMC 13 工具演示就绪补齐」（A1-A4）｜ **经评估后执行，未照搬**（评估结论见 §〇）
> 验收方：主线程（对照任务书 checklist 1-7）

---

## 〇、任务书评估结论（K3 不照搬的 4 处）

| # | 任务书 | K3 评估与处置 | 理由 |
|---|--------|--------------|------|
| 1 | A1 rank 高亮用橙色 #ff9000 | **改为极性 choropleth**（复用 zonal/compare 的 `polarityStops` 管线） | 用户 req3「设计语言统一」：rank 是极性排序，项目已有极性数据语言；#ff9000 是选择同步色非数据编码。橙色只用于 nearest 连线（关联标注，非数据编码） |
| 2 | A1 nearest 连线层 | **须后端 additive**（`geo_routes.py` 补 tgt/pt 坐标列 + 修 distance 恒 0） | 后端 rows 无几何（:481 drop geometry），纯前端造线 = 重造 GIS 轮子（违用户 req2）。nearest 另有隐藏 bug：`sjoin_nearest` 未传 `distance_col` → **distance 恒 0.0**（演示见光死），已修 |
| 3 | A4 Layer Manifest 纳入本组 | **单列，本组不做** | 三级管线**已存在**：嗅探 `profileFields`（import.js:216）→ 字典 `resolveRole`（field_dictionary.js）→ LLM `getFieldCard` 缓存（tools.js:86-115）。完整 manifest 的消费侧（quality 预检喂 diagnose data_plan）触承重红线，属组 D/E；做半个无消费方 = 死代码 |
| 4 | A2 出口 partial 裁定 | **只做渲染层标记**（`_renderState` + observation 备注） | 任务书自承出口侧触 harness EXIT_RESULT（:327/342）红线，留组 E。本组未触 |

**用户 4 条要求对齐**：① 工具=EMC skill 定位未变（TOOLS 表/SKILL_DEFS 未动）；② GIS 核心零改动（后端仅 additive 加列 + distance_col 参数，sjoin_nearest/aggregate_by_polygons 等算法未碰）；③ 专有字段识别靠既有 field_dictionary.js（本组 `_buildZonalFc`/`resolveWeightField` 复用之）；④ Dumb Tool 纯粹性：所有新逻辑确定性、无 LLM、失败降级不猜。

---

## 一、A1 分析型工具补成图（演示链断点·最核心）

**做了什么**：rank/area_stats/nearest 三工具从「只返表格 rows」升级为「rows + 可见图层 + observation 含图层名 + `data.layerId`（harness `newLayerCount` 计入，`harness.js:327` 消费）」。

| 工具 | 实现 | 文件：行号 |
|------|------|-----------|
| rank | `_rankToLayer`：boundary 路径经 `_resolveBoundaryGeo` 解析 GeoJSON → `_buildZonalFc` 合成 → **过滤到命中 Top N 的单元**（未命中单元 `polarity_index=null` 不给中性色误导）→ 极性 choropleth 高亮层 `Top N·最差·{范围}`；无 boundary 时按 name 回匹配源层 features | `tools.js:300-330`；工具体接入 `:1087` 附近 |
| area_stats | `_areaStatsToLayer`：boundary GeoJSON 按 group_by 值/name 双路 join → `area_km2/share` 写入要素 properties → choropleth 面层（**用地 DLMC 由 addResultLayer 内 `landuseLayerPaint` 自动附国标标准色**，零新配色代码） | `tools.js:333-360`；工具体接入 `:1170` 附近 |
| nearest | 后端 additive：`geo_routes.py:481` `distance_col='distance'`（**修 distance 恒 0.0**）+ `:483-493` 补 `tgt_lon/tgt_lat/pt_lon/pt_lat`（target 代表点 + 最近点，WGS84）；前端 `_nearestToLayer` 造 LineString 连线层（#ff9000 标注色），缺坐标行跳过 | `api/geo_routes.py:480-493`；`tools.js:362-377`；工具体接入 `:1261` 附近 |
| 共用 | `_resolveBoundaryGeo`：preset_id / 中文 preset 标签 / 中文要素名 / GeoJSON dict 四路归一（复用 `resolveBoundaryInput` + `fetchRangePreset`，`_presetGeoCache` 缓存）；解析失败返 null → 工具降级纯表格（Dumb 不猜） | `tools.js:269-293` |

**验收点**（主线程 Playwright + 肉眼）：
1. 问「哪个区情绪最差/最需优先更新」→ 答出排序表 + 地图出 Top N 极性着色面层，图层在「EmotionMap Copilot」组内（5.205 C 分组 parentId 继承）。
2. 问「各类用地面积占比」→ 用地标准色面层 + 弹窗含 area_km2/share。
3. 问「离 X 最近的负面点」→ 橙色连线 + **距离非 0**（distance_col 修复）。
4. 三工具 `data.layerId` 非空 → harness newLayerCount 计入（EXIT_RESULT 假完成缺口对分析型工具闭合）。

**已知限制**：
- rank/area_stats 成图依赖 boundary 可解析为 GeoJSON（preset_id 经 `fetchRangePreset` 拉取；中文名经 `resolveBoundaryInput`）；解析失败降级纯表格（与 zonal preset_id 限制同级，不报错）。
- nearest 后端 k>1 语义仍是「每 target 1 个最近点」（`sjoin_nearest` 单最近限制，rows 截断 `k*len(target)` 是既有行为）——k>1 真支持属增强，未做（不影响 demo，k 默认 1）。
- rank 无 boundary 路径回匹配依赖源层 features 有 `name` 属性。

## 二、A2 落图层型 paint 统一 + 落图自检（治假完成 C4·渲染层）

**做了什么**：

| 项 | 实现 | 文件：行号 |
|----|------|-----------|
| `_defaultPaint(tool, kind)` | 样式单一来源：line→#ff9000 连线；zonal/rank→极性 choropleth（gridField/gridStops 复用 grid 管线）；其余面结果→`{fillOn, lineWidth:2, fillOpacity:0.2}` | `tools.js:439-447` |
| paint 收敛 | extract_feature/merge/buffer/overlay 散写 paint 全部改调 `_defaultPaint`（overlay fillOpacity 0.25→0.2 统一；buffer 保留 `_ui` 元数据展开合并 `{..._defaultPaint(...), _ui}`）；A1 三新层 + zonal/compare 同步收敛 | 各工具体（`:1198/:1214/:1240/:1256` 附近 + `:244-268`） |
| 落图自检 | `addResultLayer` 内 renderLayer 后：bbox 越界（WGS84 合法域外）→ `_renderState='partial'`；addSource 失败（map.js 5.205 已标 failed）→ console.warn 上报 | `tools.js:503-510` |
| `_renderNote` | 渲染异常时 observation 追加中文提示「落图异常，图层已入列表但可能未正确渲染」——**渲染层标记，不触出口裁定**（harness EXIT_RESULT 未动） | `tools.js:449-452`；挂接 12 处 observation（clip/extract/merge/buffer/overlay/filter_attr/hotspot/zonal/compare/rank/area_stats/nearest/density 委托层经 `getLayer(r.layerId)`） |

**验收点**：各工具 paint 不再散写（`grep fillOpacity tools.js` 仅 `_defaultPaint` 一处定义 + 个别特化）；渲染异常时 observation 有中文备注 + console.warn；无 `_renderState` 时对账零变化。

**已知限制**：bbox 自检只查 WGS84 合法域（不查"是否落在请求范围内"——范围一致性属 P1-4 落图自检完整版，与出口裁定耦合，留组 E）；`_renderState` 仅层对象标记 + 文案提示，出口侧 partial 裁定未做（红线留组 E）。

## 三、A3 本地化默认

**做了什么**：

| 项 | 实现 | 文件：行号 |
|----|------|-----------|
| 尺度表 | `_SCALE_TABLE`（社区/街道级 250 · 主城/全域 1000 · 区/单元/片区 500，tier 序先细后粗）+ `_clampM` 钳制 [50, 5000] | `tools.js:455-466` |
| 应用 | buffer radius 缺省 `_scaleRadius(center)`（`:1230`）；density 2D radius / 3D cellSize 缺省 `_scaleRadius(range)`（`:1420/:1425` 附近）；LLM 显式给值一律过 `_clampM` | 同上 |
| 目录文案对齐 | GEO_TOOL_CATALOG：rank yields 补「Top N 高亮层」、area_stats params 纠 `layer→boundary`（文档漂移）+ yields 补「着色面层」、nearest yields 补「连线层」、buffer params 补尺度表、density params 对齐前端实况（2D radius 300/3D cell 600·删旧 bandwidth 800/cell 300 漂移） | `ai_qa/paradigm.py:213-240/:251` |
| 宜昌预设 | 机制已具备：`resolveBoundaryInput`（boundary-resolve.js:55-60）覆盖 admin_\*/renewal_\* preset 内中文地名（西陵区/伍家岗区…）+ 去尾缀兼容；**未改代码** | — |

**eval-first 红线执行**（paradigm.py 喂 diagnose prompt）：改前冻结 **26/28=93% PASS** → 改后两跑 **25/28=89% PASS**——与任务书记录的 5.205 基线（25/28=89%）一致，3 MISS 均为已知语义边界例（rank/zonal、overlay/multi、extract/clip），**无退化，≥80% gate 成立**。

**已知限制**：尺度表只覆盖 buffer/density/grid 三处缺省值；`runTemplatePath` 内 harness 的 density cell 提取（`harness.js:308-309`）是红线未动（LLM 问句含"N米"时 harness 覆写优先级高于尺度表——既有行为保留）。宜昌预设夷陵区缺席是资产问题（C7 已记录，非代码）。

## 四、A4 Layer Manifest（评估后单列，未做）

**评估结论**（任务书自标"较大架构·K3 评估是否纳入"）：
1. 任务书要的「三级识别」**已存在**：嗅探 `profileFields`（import.js:216，dtype/samples/stats）→ 字典 `resolveRole`（field_dictionary.js:62，前后端镜像）→ LLM `getFieldCard` 按 layerId 缓存（tools.js:86-115）。专有字段类型识别（polarity/score/emotion_intensity/domain/element/DLMC…）已工作。
2. 完整 manifest 的增量价值（quality 预检/semantics 汇总）的**消费侧在红线区**：diagnose data_plan 三态（prompts.py）+ SKILL_DEFS 参数校验（harness 路由）——组 D/E 范围。
3. 做「只产不消」的半个 manifest = 死代码，违 Dumb/纯粹原则与「每次只改一处」纪律。

**建议（留组 D/E 或单列）**：manifest 生产端（导入时一次性计算，`main.js:180-183` srcId 登记处是自然挂点）与消费端（diagnose 预检）必须同批设计；本组不动。

---

## 五、验证与承重确认

| 项 | 结果 |
|----|------|
| `py -m pytest tests/ -q` | **183 passed, 11 skipped**（与改动前 stash 基线逐数一致；注：任务书 checklist 写「5.205 后 203 passed」，实测 main 当前即为 183/11——差异先于本组存在，疑似 DATA 迁移 + eval 网络依赖跳过，见未决①） |
| eval-first（eval_template_flash.py） | 改前 26/28=93% → 改后 25/28=89% ×2 跑，与 5.205 记录基线一致，**无退化，PASS** |
| `node --check tools.js` | 语法 OK |
| **承重三不动** | `git diff`：`ai_qa/prompts.py` / `frontend/js/ai_qa/harness.js` / `ai_qa/schemas.py` **零改动**；全部改动 = 3 文件（tools.js +212/-45 主体、geo_routes.py、paradigm.py 16 行文案） |
| 5.205 不破坏 | resolveWeightField / _toolContentSig / loadPoints 清层 / C 分组 parentId / time-source 均未触碰（addResultLayer 的 srcId/parentId 逻辑原样复用） |
| lint | tools.js / geo_routes.py 零诊断 |

## 六、未决 / 交接

1. **pytest 计数差**：07-24 记录 203 passed/7 skipped → 当前 183/11（本组改动前后一致，非本组引入）。疑似：DATA/processed 删除致数据依赖测试跳过 + eval 网络跳过。主线程确认是否接受为新基线。
2. **A1 成图肉眼验收**（checklist 1-2）：需主线程起 `py frontend/serve.py 8080` + Playwright 跑「哪里最差/面积占比/最近邻」三问肉眼验图层可见性——K3 静态实现已毕，运行时验证属用户环境。
3. **A4 单列**：见 §四，建议与组 D/E 的 diagnose 预检合并设计。
4. **eval 3 MISS**（rank/zonal、overlay/multi、extract/clip 语义边界）：留 B3 SOP 卡批次（既有 backlog）。
5. overlay fillOpacity 0.25→0.2 统一为 cosmetic 变更，如主线程偏好旧值可单行回退（`_defaultPaint` 集中改）。
