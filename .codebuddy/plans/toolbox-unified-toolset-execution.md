# Toolbox 统一工具集层 — 执行手册（GLM 5.2 组）

> v2.2 | 2026-07-25 | 状态：据主线程评审修订（评审报告：`.codebuddy/reports/emc-toolbox-unified-review-2026-07-25.md`；逐条响应：`.codebuddy/reports/emc-toolbox-v22-revision-response-2026-07-25.md`）
> 上游：plan `toolbox-unified-toolset`（用户已确认 D1-D6；评审建议 1 focusOnlyResults 经 K3 技术复核接受落版·**待用户最终确认**，否决则按响应表回退指引处理）
> 本手册 = 唯一执行依据。遇与本手册冲突的临场判断，停下来问，不要自创分支。

### v2.1 → v2.2 修订日志

| # | 位置 | 变更 | 依据 |
|---|------|------|------|
| M1 | §0 一句话任务 | 「产出完全一致」→「图层产出一致；EMC 元数据仅对话路径补」 | 评审修订 3（D-②） |
| M2 | §1 依赖红线 | 补循环依赖既有模式说明 + TDZ 禁令 | 评审修订 5（D-①） |
| M3 | §2 C4 | `_adoptToolboxResult` 组成补 consumed 清理 + focusOnlyResults | 建议 1 |
| M4 | §3.2 去向表 | focusOnlyResults 行说明明确「:411 定义 + :515 调用保留」 | 建议 1（消 §3.2↔§3.3③ 自相矛盾） |
| M5 | §3.3③ | 「废弃 focusOnlyResults」推翻 →「互斥/聚焦分工·差异化保留」 | 建议 1（K3 接受·证据 tools.js:407-410/:515 + density :1284-1319 实证） |
| M6 | §4.3 | Buffer 兼容推断改「color 判据」+ 新产物显式 kind | 评审修订 2（D-④ 真 bug）；**评审原文 distance 判据与 buffer-tool.js:121 事实冲突，本版修正** |
| M7 | §5.1 / §5.7 | §5.1 补循环注；§5.7 补显式 kind 写入 | 修订 5 / 修订 2 |
| M8 | §6 步 3/4/5 | 批注步 3/4 可并行、步 5 可与步 7 首批合并（编号保留） | 评审修订 7（可选·部分接受） |
| M9 | §6 步 7 | 模板补 focusOnlyResults + observation 快照基线方法 + density 不迁移注 + buffer 显式 kind | 建议 1 / 修订 6 / 修订 2 |
| M10 | §6 步 8 | 加硬 gate：12 工具 observation 快照 diff 全通过 | 评审修订 6（F 验证缺口） |
| M11 | §7 纪律 1 | 补 paradigm GEO_TOOL_CATALOG 无需同步的论证 | 评审修订 4（D-③·部分接受：张力真实，解法为「论证无需改」而非「同步」） |

---

## 0. 一句话任务

把 EMC 内联在 `frontend/js/ai_qa/tools.js` 的 9 个 GIS 工具 + Buffer 情绪聚合，收敛为 `frontend/js/toolbox/` 下同层级独立模块（每模块 = 单一执行核 + ForAI 程序化入口 + 可选 UI 对话框），Toolbox 面板新增 4 个入口（Zonal/面积/Rank/矢量组），Buffer 原地合一双模式，EMC tools.js 瘦身为 LLM 适配层——**两条触发路径（EMC 对话 / Toolbox 手动）调用同一批模块，图层产出一致（同一 _execute 核）；EMC 元数据（registry/$n/provenance/沉浸聚焦）仅 EMC 对话路径由委托层补**（v2.2 修订：原「产出完全一致」表述误导——手动路径产物无 EMC registry/$n，评审 D-②）。

### 已冻结决策（用户拍板，勿改）

| # | 决策 | 内容 |
|---|------|------|
| D1 | 目录 | 新模块放 `frontend/js/toolbox/`；**heatmap-tool/grid-tool/buffer-tool 留 `frontend/js/` 原位不动**（引用面已穷尽，零 import 改动） |
| D2 | UI 入口 | +4 个：zonal（聚合/对比双模式）、area-stats、rank、vector（五操作）。nearest/hotspot 纯内嵌无 UI。归因占位不动 |
| D3 | Buffer | 原地合一 `kind:'cover'|'emotion'`；emotion 中心输入**四路**：地点搜索/地图取点/图层要素/手输坐标 |
| D4 | 字段避让 | Buffer 模式字段用 **`kind`**，禁用 `mode`（stages.js `_PARAM_ALIAS` 有 `mode→how`，会撞 overlay） |
| D5 | 验证节奏 | 8 步全做完，最后统一 playwright E2E；中间仅静态断链检查 |
| D6 | EMC 契约 | 流水线 6 条契约全保（见 §2） |

---

## 1. 目标架构

```
触发层
  路径一 EMC: ai_qa/tools.js（薄适配：参数归一/observation 文案/registry 簿记）
  路径二 UI : index.html tool-row → param-panel pp-pane 对话框
                │  都调 generateXxxForAI(opts) / 同一 _execute 核
工具集层（同层级、高内聚低耦合、模块间互不 import）
  frontend/js/         heatmap-tool.js · grid-tool.js · buffer-tool.js（原地，buffer 增强）
  frontend/js/toolbox/ shared.js（唯一共享基建）
                       zonal-tool.js · area-stats-tool.js · rank-tool.js · vector-tool.js
                       nearest-tool.js（内嵌）· hotspot-tool.js（内嵌）
                │
后端  /api/v1/spatial/*（heatmap/grid/buffer-cover，现状不动）
      /api/v1/geo/*（其余全部，经 api.js geoPost）
```

**依赖红线（单向）**：`ai_qa/tools.js → toolbox/* + js/三工具`；`toolbox/* → shared.js + state/map/sidebar/import/api/landuse_colors/grid-tool`；**toolbox 模块严禁 import `ai_qa/*`**；`shared.js` 可 import `grid-tool.js`（piToNorm/polarityStops）。

**循环依赖说明（v2.2 补·评审 D-①）**：`shared.js` import `sidebar.js`（renderLayerList :343 / refreshLegend :163）是**既有模式**——grid-tool.js:12 / heatmap-tool.js:12 / buffer-tool.js:7 均如此（sidebar.js:7-9 反向 import 三工具，`sidebar ↔ tool-module` 循环早已存在）。安全依据：renderLayerList/refreshLegend 均为 `export function` 提升声明（sidebar.js:343/:163），ES module 循环下仅作运行时调用，不触 TDZ。**红线补充：严禁 sidebar.js 顶层 const 求值依赖 toolbox/shared export（TDZ 风险）；toolbox 模块对 sidebar 的调用仅限函数级运行时调用。**

---

## 2. EMC 计划与执行流水线 — 6 条承重契约

机制：`diagnoseStep`（LLM 产意图卡）→ single 技能走 `runTemplatePath`（0 轮 agentStep 直调 `TOOLS[tool]`），multi/unknown 走 ReAct while-loop（`harness.js:527-614`）；observation 注入 toolHistory → `finalStep` 出结论。

| # | 契约 | 位置 | 执行约束 |
|---|------|------|----------|
| C1 | TOOLS 工具名不变 | `stages.js:35-54` SKILL_DEFS ↔ 后端 `paradigm.py` TEMPLATE_REGISTRY | 12 个工具名（zonal_stats/compare_regions/rank/area_stats/nearest/overlay/clip/extract_feature/merge/filter_attr/hotspot/buffer）一字不改，只换内部实现 |
| C2 | 返回 `{observation, data:{rows?, layerId?}}` | `harness.js:379` `_ANALYTICAL_TOOLS` | zonal_stats/compare_regions/rank/area_stats 成功判定认 `data.rows` 非空 → ForAI 必须回传 rows 且委托层透传 |
| C3 | 参数 schema 不变 + 别名避让 | `stages.js:10-22` `_PARAM_ALIAS` | LLM 参数面零变化；新增内部字段禁止用 `mode`/`how`，用 `kind` |
| C4 | setToolContext provenance | `harness.js:321,597` | harness 已注入；`_adoptToolboxResult`（= `_registerToolboxLayer` + consumed 清理 + AI 组 parentId + **focusOnlyResults** + layers:changed 补发·v2.2）照常在委托层调用，$n 引用/registry 对账/沉浸聚焦不断 |
| C5 | _GEO_TOOLS F3 完整性 gate | `harness.js:378-397` | 按工具名比对计划/已执行步数——工具名不变即免疫 |
| C6 | 图层命名语义 | `harness.js:218-242` `_verifyClaims` | 「名=内容/范围/要素名，勿工程前缀」（如「滨江公园·500m」「西陵区·伍家岗区」），现状命名逐字保留 |

---

## 3. 代码地图（已全部核实，行号为当前值）

### 3.1 引用面（D1 不移动的凭据，执行后须保持不变）

| 模块 | 被谁 import（符号） |
|------|---------------------|
| `js/heatmap-tool.js` | `main.js:17`（initHeatmapTool）、`sidebar.js:7`（openHeatmapDialog）、`ai_qa/tools.js:9`（generateHeatmapForAI/generateTerrainForAI） |
| `js/grid-tool.js` | `main.js:19`、`panel.js:15`（POLARITY_GRID/polarityStops）、`range-presets.js:11`（openGridDialog）、`sidebar.js:9`、`timeline.js:17`（piToNorm）、`ai_qa/tools.js:8`（generateGridForAI/piToNorm/polarityStops） |
| `js/buffer-tool.js` | `main.js:18`、`sidebar.js:8` |
| `ai_qa/tools.js` | `harness.js:7`（TOOLS/setToolContext/formatRegistry/deriveAvailable）、`ai_qa/panel.js:3`（buildContext/TOOLS/resetStepResults/resetCurrentResults/cleanupConsumedResults/getFig） |

**tools.js 导出面（必须全部保留签名）**：getGeoCatalog, invalidateGeoCatalog, getWisdom, getFieldCard, resetStepResults, getFig, clearFigCache, setToolContext, resetCurrentResults, addResultLayer, getArtifacts, formatRegistry, cleanupConsumedResults, deriveAvailable, buildContext, pickVisiblePointLayer, TOOLS。

### 3.2 tools.js 函数去向表

| 函数（行号） | 去向 | 说明 |
|--------------|------|------|
| `geoFetch` :164 | **删** | 由 `api.js geoPost` 取代；`ref()` 预处理移到委托层内联 |
| `ref` :141 | 留 tools.js | run_python inputs 与委托层 $n 预解析仍用 |
| `_buildZonalFc` :218 | → `toolbox/shared.js` | zonal/rank 共用（依赖 piToNorm） |
| `_zonalToLayer` :245 / `_compareToLayer` :254 | → `toolbox/zonal-tool.js` | 改为模块内部函数，落图改调 `addToolboxLayer` |
| `_resolveBoundaryGeo` :271（+`_presetGeoCache` :268） | → `toolbox/shared.js` | 依赖 resolveBoundaryInput——**反向问题见 §3.3 注意 ①** |
| `_rankToLayer` :300 | → `toolbox/rank-tool.js` | 同上 |
| `_areaStatsToLayer` :333 | → `toolbox/area-stats-tool.js` | 同上 |
| `_nearestToLayer` :362 | → `toolbox/nearest-tool.js` | 同上 |
| `fitToFeature` :377 | 留 tools.js | query/focus 类工具用 |
| `_aiGroup` :390 / `_unionBBox` :396 / `focusOnlyResults` :411 | 留 tools.js | EMC 簿记；focusOnlyResults **保留**：:411 定义 + addResultLayer :515 调用均不动（§3.3③ v2.2） |
| `_toolContentSig` :425 | → `toolbox/shared.js` | addToolboxLayer 去重用；tools.js re-export（注：main.js 有同语义 `_contentSig`，注释已标"待统一"，本次不动 main.js） |
| `_defaultPaint` :440 / `_renderNote` :449 | → `toolbox/shared.js` | defaultPaint 依赖 polarityStops（grid-tool） |
| `_SCALE_TABLE` :456 / `_scaleRadius` :461 / `_clampM` :466 | → `toolbox/shared.js` | tools.js re-export（委托层尺度钳制仍用） |
| `addResultLayer` :473 | **留 tools.js，内部重构** | 拆为 `addToolboxLayer`（shared.js，通用落图）+ EMC 簿记（registry/$n/keep/consumed/focusOnlyResults）。签名与行为零回归 |
| `getArtifacts` :522 → `_registerToolboxLayer` :817 | 留 tools.js | EMC registry/$n 全留 |
| hotspot class→极性重映射（TOOLS.hotspot :1256-1266） | → `toolbox/hotspot-tool.js` | `_CLS_POL` 映射随迁 |
| TOOLS :828-1359 | 留 tools.js | 12 个 GIS 工具改委托（§6 步 7）；query_*/ensure_zone/open_attribution/inspect_zone/deep_read_attribution/run_python/density 逻辑不动 |

### 3.3 注意两点

**① `_resolveBoundaryGeo` 的反向依赖**：:276 调用 `resolveBoundaryInput`（`ai_qa/boundary-resolve.js`）。决策：shared.js **不 import ai_qa/**。做法——`_resolveBoundaryGeo` 拆两半：
- shared.js `resolveBoundaryGeo(input, {resolveName}?)`：preset_id/label/GeoJSON 三路（:280-293 逻辑 + 缓存）；`resolveName` 回调可选注入。
- tools.js 委托层：中文要素名先经 `resolveBoundaryInput`（ai_qa 原地不动）解析成 GeoJSON/preset_id，再传给模块。模块内不再碰中文名解析。

**② `addToolboxLayer` 与 `addResultLayer` 分工**（消重关键）：

```js
// toolbox/shared.js — 通用落图（无 EMC 簿记）
export function addToolboxLayer({ name, kind = 'polygon', fc, paint }) {
  // = 现 addResultLayer 的：签名去重(:475-478) + landuseLayerPaint(:486-490)
  // + addLayer/renderLayer + 落图自检 _renderState(:506-511)
  // + renderLayerList/refreshLegend/reorderAllZ + fitBoundsTo + layers:changed
  // 不含：_ui.tool 注入/AI 组/registry/$n/keep/consumed/focusOnlyResults
  // 返回 L（layer 对象）或 null
}
// tools.js addResultLayer = addToolboxLayer 调用 + 原有 EMC 簿记全部保留（:491-502,513-516）
```

**③ 互斥与聚焦分工（v2.2 改写·推翻 v2.1「废弃 focusOnlyResults」）**：
- toolbox 各模块 `_execute` 落图后调 `enforceMutualExclusion(L.id)`（state.js，与 grid-tool/buffer-tool 一致，手动场景同类独占显示）。
- **focusOnlyResults 保留**（tools.js:411 定义 + addResultLayer :515 调用不动）；EMC 委托层 `_adoptToolboxResult` 在 `_registerToolboxLayer`（推送 `_curResultIds` :823）之后调用它——维持 EMC 回答「沉浸聚焦本轮」。
- 两路径**图层产出一致、聚焦行为差异化**（产品本意：EMC 对话 = 沉浸聚焦本轮结果；Toolbox 手动 = 同类互斥）。
- 证据（K3 复核实测）：tools.js:407-410 注释明确「AI 结果是 R-group（enforceMutualExclusion 不动它），故不走互斥，直关」——互斥语义替代不了直关；且组 A 已委托的 density（:1284-1319）未调 focusOnlyResults，证明「委托即丢聚焦」是实证风险而非理论推演。
- tools.js `_adoptToolboxResult` 另保留 consumed 清理（addResultLayer :481-483 逻辑提取）。

### 3.4 UI 接线点（行号当前值）

| 位置 | 现状 | 改动 |
|------|------|------|
| `index.html:143-164` | tool-list 4 行 | tool-buffer 行（:154-158）后插 4 个 tool-row：`tool-zonal`/`tool-area-stats`/`tool-rank`/`tool-vector`（SVG 图标+tool-name+tool-info，镜像现有行） |
| `index.html:385-389` | pp-tabs 3 个 | buffer tab 后插 4 个：`data-pp-tab` = `zonal`/`area-stats`/`rank`/`vector`，文案 面域/面积/排序/矢量 |
| `index.html:584-690` | grid pp-pane | 其后插 4 个 pp-pane：`data-pp-pane` 同 tab 名，内裹 `zonal-dialog`/`area-stats-dialog`/`rank-dialog`/`vector-dialog`（`.app-dialog.hm-dialog` 三步向导骨架） |
| `index.html:509-581` | buffer-dialog | ①参数区顶部加模式胶囊；emotion 参数区（中心输入四路+半径+点层下拉）新 hm-group，显隐切换镜像 `grid-tool constrainParams` |
| `sidebar.js:15-23` | isToolPanelEditing | tab 映射扩：`{zonal:'zonal', area_stats:'area-stats', rank:'rank', overlay/clip/extract_feature/merge/filter_attr:'vector'}`（**约定：pp-tab 名 + `-dialog` = dialog id**） |
| `sidebar.js:448-451` | 要素按钮分派 | 扩：`_ui.tool==='zonal'`→openZonalDialog(id)；`'area_stats'`→openAreaStatsDialog(id)；`'rank'`→openRankDialog(id)；五 vector 操作名→openVectorDialog(id) |
| `sidebar.js:821-826` | tool-* 接线 | +4 行 click 接线（归因占位 :824-826 不动） |
| `param-panel.js:64` | outside-click 白名单硬编码 3 id | 改 `.closest('.tool-row')` 泛化 |
| `main.js:316-318` | init 三工具 | 后插 `initZonalTool(); initAreaStatsTool(); initRankTool(); initVectorTool();` + :17-19 同款 import |
| `css/param-panel.css` | .pp-tabs | 7 页签 flex-wrap 排布验证不溢出（面板 460px） |

---

## 4. 契约附录（所有模块必须遵守）

### 4.1 ForAI 返回契约（与 generateGridForAI 同构）

```js
// 每个模块导出，EMC 委托的唯一接口
export async function generateXxxForAI(opts = {})
// → Promise<{ layerId, layerName, featureCount, fc, rows?, ...toolSpecific }>
// opts 公共：as?(图层名覆盖), silent?=true(不发 toast), editLayerId?(原地更新)
// 失败：throw Error（委托层 catch → '[ERR] 工具名 失败：msg'）
```

### 4.2 模块骨架（单一执行核）

```js
// 每模块三段式（UI 与 ForAI 共用 _execute，杜绝 grid-tool 式双实现债）
async function _execute(params, { editLayerId = '', silent = true } = {}) {
  // 1. geoPost 调后端 → 2. 合成 fc/rows → 3. addToolboxLayer 落图
  // 4. enforceMutualExclusion → 5. 返回契约对象（含 rows）
}
export function openXxxDialog(layerId)  // 编辑态从 paint._ui 回填；openParamPanel('tab名')
export function initXxxTool()           // dialog 事件绑定（仅一次）
export async function generateXxxForAI(opts)  // = _execute(opts, {silent:opts.silent??true})
```

### 4.3 paint._ui 契约（编辑态闭环）

| 工具 | `_ui.tool` | `_ui` 附加字段 |
|------|-----------|----------------|
| zonal 聚合 | `'zonal'` | `mode:'aggregate'`, boundary, source, level, pre_filter? |
| zonal 对比 | `'zonal'` | `mode:'compare'`, boundaries[], source, level |
| 面积统计 | `'area_stats'` | boundary, group_by |
| rank | `'rank'` | by, top_n, boundary?, source |
| overlay/clip/extract/merge/filter | 各操作名 | op 参数全集（layer_a/layer_b/how、range、where、by、pre_filter） |
| buffer | `'buffer'` | **kind:'cover'\|'emotion'** + cover:{sourceLayer,distance,dissolve,color...} / emotion:{center,radius_m,layer} |
| nearest | `'nearest'` | target, k（line 层·无编辑入口） |
| hotspot | `'hotspot'` | value_col, invert（point 层·走 settings popover） |

**Buffer 编辑兼容推断（v2.2 修正）**：新产物一律**显式写 `kind`**（cover = buffer-tool DEFAULTS 增 `kind:'cover'`；emotion = `generateBufferForAI`/EMC 委托层显式 `kind:'emotion'`），不靠推断。**存量产物推断**（组 A 期及更早·无 `kind`）：有 `color` 字段 → `'cover'`（cover 路径 _ui 必含 color，buffer-tool.js:121-122）；否则 → `'emotion'`（EMC emotion 路径 _ui 无 color，tools.js:1205）。**禁用 distance / sourceLayer 作判据**——distance 两路径均必有（buffer-tool.js:121 vs tools.js:1205），sourceLayer cover 必有而 emotion 条件性有（tools.js:1206-1207，即评审 D-④ 误判源）。（注：评审修订 2 原文以 distance 为判据，与 buffer-tool.js:121 事实冲突，本版修正为 color 判据·详见响应表。）

### 4.4 命名契约（C6 红线，逐字沿用现状）

聚合·{boundary} / 对比·{b1·b2} / Top{N}·{最差|最好}·{scope} / 面积·{boundary}[·按{group_by}] / 最近邻·{target} / {对象}·{radius}m / {howCN}·{A}与{B} / {as 或 值/字段名}（filter/clip/extract/merge 勿工程前缀）

### 4.5 observation 契约（C2）

委托层用 ForAI 返回的 rows + 现 `_fmtRow`(:196) 拼文案，**逐字等于现状**（含 `_renderNote(getLayer(layerId))` 后缀，density :1315 范式）。表格型工具 data 必须含 rows；落图型 data 必须含 layerId。

---

## 5. 新模块规格

### 5.1 `toolbox/shared.js`（基建，第一步必须先落）

```js
export async function geoPost(path, body)          // POST /api/v1/geo/{path}，detail 错误抛出（风格同 api.js runBuffer；**也同步加入 js/api.js 导出**，供不带 shared 的场景）
export function defaultPaint(tool, kind)           // 自 tools.js:440（import polarityStops from '../grid-tool.js'）
export function renderNote(L)                      // 自 tools.js:449
export const SCALE_TABLE / scaleRadius(hint) / clampM(v)   // 自 tools.js:456-466
export async function resolveBoundaryGeo(input)    // 自 tools.js:271 去掉 resolveBoundaryInput 分支（§3.3①）+ _presetGeoCache
export function buildZonalFc(rows, boundary)       // 自 tools.js:218（import piToNorm from '../grid-tool.js'）
export function toolContentSig(fc)                 // 自 tools.js:425
export function addToolboxLayer({name, kind, fc, paint})   // §3.3②
```
import 来源：`../state.js`、`../map.js`、`../sidebar.js`（renderLayerList/refreshLegend——既有循环模式，安全依据与 TDZ 禁令见 §1 依赖红线补注）、`../import.js`（fcBBox）、`../landuse_colors.js`（landuseLayerPaint）、`../api.js`（fetchRangePresets/fetchRangePreset）、`../grid-tool.js`。

### 5.2 `toolbox/zonal-tool.js`

- ForAI：`generateZonalForAI({layer, boundary, range?, pre_filter?, top_n?, as?, silent?})`、`generateCompareForAI({layer, boundaries[], pre_filter?, as?, silent?})`（≤4 区，逐区 geoPost('zonal_stats') 循环，现状 tools.js:1041-1050 逻辑随迁）
- dialog：①模式 2 卡（面域聚合/多区对比）②点层下拉（镜像 grid collectSources 简化版）+ boundary 下拉（已载 Range 面层 + fetchRangePresets 合并）+ 对比模式要素多选胶囊（≤4）+ 可选 pre_filter 三段（字段/操作/值）③红绿 choropleth 色带预览（polarityStops('overall')）
- 落图：`_ui.tool='zonal'`、paint=defaultPaint('zonal','polygon')、rows 注入要素 properties（_buildZonalFc 现状）

### 5.3 `toolbox/area-stats-tool.js`

- ForAI：`generateAreaStatsForAI({boundary, group_by?, as?, silent?})`
- dialog：①说明卡 ②boundary 下拉（同 zonal）+ group_by 字段下拉（读 boundary fc properties，默认 DLMC/name）③用地国标色自动着色提示（landuseLayerPaint 已由 addToolboxLayer 消费）+ 占比条预览
- `_ui.tool='area_stats'`，rows 的 area_km2/share 注入 properties（:346-350 现状）

### 5.4 `toolbox/rank-tool.js`

- ForAI：`generateRankForAI({layer?, by='worst', top_n=5, boundary?, range?, pre_filter?, as?, silent?})`（by 含 `domain:xxx`，中文映射 _DOMAIN_CN2EN 留 tools.js 委托层）
- dialog：①排序维度卡（情绪最差/情绪最好）+ Top N 滑块 3-10 ②点层+可选 boundary+可选范围 ③高亮色带预览
- `_ui.tool='rank'`，Top N 过滤+_grid_norm 补全（:315-321 现状）

### 5.5 `toolbox/vector-tool.js`（五操作合一）

- ForAI：`generateOverlayForAI({layer_a, layer_b, how='intersection', as?})`、`generateClipForAI({layer, range, pre_filter?, as?, keep?})`、`generateExtractForAI({layer, where?, as?})`、`generateMergeForAI({boundary, by?, as?})`、`generateFilterForAI({layer, pre_filter, as?, keep?})`
- dialog：①操作 5 卡（叠置/裁剪/抽取/合并/筛选）②参数区按操作显隐（镜像 constrainParams：叠置=图层A/B 下拉+交并差对称差胶囊；裁剪=目标点层+范围下拉；抽取=面层+where 三段；合并=面层+可选 by 字段；筛选=点层+pre_filter 三段）③取色器（settings.js `renderColorPicker` 同源）+填充透明度
- `_ui.tool` = 各操作名（overlay/clip/extract_feature/merge/filter_attr），编辑分派全路由 openVectorDialog，dialog 按 `_ui` 参数回填操作卡
- **extract 字段预校验**（:1121-1135 getFieldCard 逻辑）属 LLM 恢复链，**留 tools.js 委托层**，模块不做

### 5.6 `toolbox/nearest-tool.js` / `hotspot-tool.js`（纯内嵌）

- `generateNearestForAI({layer?, target, k=1, as?})` → LineString 连线层（#ff9000，:362-375 现状），`_ui.tool='nearest'`
- `generateHotspotForAI({layer?, value_col='score', invert=true, range?, pre_filter?, as?})` → class→极性重映射点层（:1256-1266 现状），`_ui.tool='hotspot'`
- 无 dialog、无 init、无 tool-row

### 5.7 `js/buffer-tool.js` 原地增强

- DEFAULTS 增 `kind:'cover'`；`_execute(params,{editLayerId,silent})` 重构现状 generateBuffer（cover 路径逻辑零改）
- emotion 路径：`geoPost('buffer', {center, radius_m:clampM(...), layer?, agg_cols?, range?, pre_filter?})`，圈内 point_count/polarity_index 入 properties（现状 tools.js:1198-1210）
- dialog ①参数区顶部模式胶囊（覆盖范围/圈内情绪）；emotion 参数区：
  - 中心输入四路（同一 hm-group，胶囊切换输入方式）：
    a. 地点搜索（input + 下拉候选，`searchPlaces` from api.js，选中得 {lng,lat,name}）
    b. 地图取点（按钮进入取点态，map.once('click') 取 lngLat，Esc 取消；参考 draw-tool.js 交互挂载方式）
    c. 图层要素（面层/点层下拉 → 要素下拉；点取 coordinates，面取质心 `polyCentroid` from district-stats.js）
    d. 手输坐标（lng/lat 两个 number input）
  - 半径（沿用距离控件）+ 情绪点层下拉（可见点层）
- `generateBufferForAI({kind, ...})`；EMC 委托固定 `kind:'emotion'`；**两种模式产物 `_ui` 均显式写 `kind`**（§4.3：cover 由 DEFAULTS 默认、emotion 由 _execute 写入）
- 编辑回填按 §4.3（新产物读 kind·存量走 color 判据）；生成按钮文案 调整/生成（现状已有）

---

## 6. 八步实施手册（顺序执行，每步完成判定 = DoD）

### 步 1 toolbox-foundation（基建）
- 建 `frontend/js/toolbox/shared.js`（§5.1）；`js/api.js` +`geoPost`
- tools.js：被抽函数改 `import ... from '../toolbox/shared.js'` 并 **re-export 同名**（导出面 §3.1 不变）；`_defaultPaint/_renderNote/_scaleRadius/_clampM/_buildZonalFc/_resolveBoundaryGeo/_toolContentSig` 原定义删除
- `addResultLayer` 内部拆 addToolboxLayer（§3.3②），行为零回归
- **DoD**：页面打开无 console 报错；EMC 跑 zonal_stats/buffer/rank 各一次产物与改前一致；grep 无重复定义

### 步 2 buffer-unify（Buffer 合一）
- 按 §5.7 改造；index.html buffer-dialog 加模式胶囊 + emotion 参数区
- **DoD**：cover 现状零回归（整层缓冲/编辑回填）；emotion 四路中心输入均产出聚合圈（point_count 入属性）；`generateBufferForAI` 双模式返契约；`_ui.kind` 显式写入正确，且存量无 kind 产物按 §4.3 color 判据正确回填

### 步 3 zonal-area-tools（与步 4 模块互不依赖·可并行）
- zonal-tool.js（§5.2）+ area-stats-tool.js（§5.3）+ index.html 两 pp-pane + sidebar/main 接线（可暂挂临时按钮验证）
- **DoD**：dialog 生成 choropleth 层 + rows 正确；编辑重开回填；ForAI 返 rows

### 步 4 rank-vector-tools（与步 3 可并行）
- rank-tool.js（§5.4）+ vector-tool.js（§5.5）+ UI 接线
- **DoD**：rank Top N 高亮层；vector 五操作各自产出正确 + 编辑回填

### 步 5 embedded-tools（纯内嵌无 UI·可与步 7 首批 nearest/hotspot 合并执行，编号/DoD 不变）
- nearest-tool.js + hotspot-tool.js（§5.6）
- **DoD**：ForAI 产出连线层/冷热点层；无 UI 残留

### 步 6 ui-wiring（收尾接线）
- index.html 4 tool-row（:154-158 后）+ 4 pp-tab（:388 后）；param-panel.js:64 泛化 `.tool-row`；sidebar :15-23/:448-451/:821-826 扩展；main.js :316-318 后注册
- **DoD**：7 个 tool-row 全开对应 pp-pane；7 页签 flex-wrap 不溢出；要素按钮分派全通

### 步 7 emc-delegate（tools.js 委托，最敏感步）

**前置：observation 快照基线（v2.2·修订 6·开工前必做）**——对 12 工具以固定入参各执行一次（playwright `page.evaluate` 直调 `TOOLS.xxx(params)`），抓 `{observation, data}` 存 `tests/reports/toolbox-obs-baseline.json`（data 剔除 layerId/时间戳等易变字段）；每工具委托后同入参重跑，observation 逐字 + data 稳定字段 diff 全等才过本工具 DoD。

逐工具改（建议顺序：nearest → hotspot → rank → area_stats → merge → clip → filter_attr → extract_feature → overlay → zonal_stats → compare_regions → buffer），每工具：

```js
async xxx(params = {}) {
  // 1. 现状 guard/参数归一/字段预校验/resolvePointLayer/resolveBoundaryInput 全保留
  // 2. 调 generateXxxForAI（ref() $n 预解析后的值传入）
  // 3. _adoptToolboxResult(layerId, fc, name)（新助手 = _registerToolboxLayer + consumed 清理
  //    + AI 组 parentId + focusOnlyResults（沉浸聚焦·v2.2）+ layers:changed 补发）
  // 4. rows + _fmtRow 拼现状 observation（逐字）+ renderNote(getLayer(layerId))
  // 5. data 透传 {rows, layerId, ...现状字段}
}
```
- 删 geoFetch、被迁合成器（_zonalToLayer 等）；`_adoptToolboxResult` 提取 density :1305-1311 范式
- **density 本身不迁移到新助手**（v2.2 注）：其现状（:1284-1319）未调 focusOnlyResults，迁移 = 引入未评审的行为变更，另案处理
- **buffer 委托额外**：产物 `_ui` 显式 `kind:'emotion'`（§4.3·修订 2），不再依赖推断
- **DoD（逐工具）**：observation 快照 diff 全等（前置基线·演示链命门）；registry/$n/深读链（query_zone_stats/inspect_zone/deep_read_attribution 依赖 activeAnalysis）正常；EMC 产物沉浸聚焦行为与改前一致（focusOnlyResults 生效）

### 步 8 e2e-verify-docs
- **硬 gate（v2.2·修订 6）**：12 工具 TOOLS 返 observation 改前/后快照 diff 全通过（基线 `tests/reports/toolbox-obs-baseline.json`·步 7 前置方法）——演示链命门，任一 diff 不过则步 8 不通过
- playwright：7 tool-row 开 pane；每工具 UI 生成 + evaluate 直调 ForAI 各一遍比对（kind/_ui.tool/命名）；Buffer 双模式+回填（含存量无 kind 层 color 判据回填）；无 console 报错
- EMC 流水线回归：单技能快路径（问「西陵区情绪最差的是哪些社区」类）+ ReAct 多步（「裁出西陵区再叠置商业用地」类）；rows 判定/$n/对账/F3 不破；`tests/browser` 既有用例回归
- 文档：`docs/architecture-pattern.md` 加「Toolbox 统一工具集层」节 + `docs/todo.md` 日志

---

## 7. 执行纪律

1. **编码铁律**（AGENTS.md）：禁 emoji（用 [OK]/[ERR]）；不动后端；不改 SKILL_DEFS/paradigm.py；不改 heatmap/grid 现状逻辑。**paradigm 补注（v2.2·修订 4）**：GEO_TOOL_CATALOG **无需**为 buffer 双模式同步——`kind` 是模块内部 API（§5.7 generateBufferForAI），LLM 契约面零变化（C3 参数面不变 + 委托层固定 `kind:'emotion'`），catalog :220-226 的 emotion 描述与 LLM 实际可用行为一致、无漂移；若未来决策向 LLM 暴露 cover 模式，届时再走 catalog 同步并需用户拍板。
2. **SOP 级别 = 严格**（多文件+控制流+核心链）：步 7 每工具改完自审一遍 C1-C6；步 8 全量验证
3. **上下文管理**：引用搜索用 code-explorer 子代理；每轮聚焦一个文件；tools.js 委托按 §6 步 7 顺序小批进行
4. **commit 策略**：每步一个 commit（`toolbox: step N ...`），步 7 可按工具再拆；不 push 除非用户要求
5. **禁止事项**：不创建新设计体系/CSS 框架；不动归因占位；不扩 isAnalysis 集合（rank/area_stats 不进，防 activeAnalysis 语义漂移）；不给 nearest/hotspot 加 UI
6. **临场不确定**：后端 /geo/buffer 的 center 接收格式（字符串/GeoJSON/{lng,lat}）实施步 2 时先读 `api/` 路由确认，再定 UI 提交格式——这是唯一允许的后端阅读点，不改后端代码
