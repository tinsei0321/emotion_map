# Toolbox 统一工具集层执行手册 — 技术评审报告

> 评审人：主线程（GLM 5.2）｜ 2026-07-25 ｜ 对象：`.codebuddy/plans/toolbox-unified-toolset-execution.md` v2.1（K3 产出）
> 基线：commit d78d0a8 + 组 A 完成（emc-toolset-completion-2026-07-25.md）
> 方法：静态评审（手册声明 vs 实际代码），抽核 ≥ 30%（§3.2 去向表 20 函数 + §3.4 接线点 + §3.1 引用面 + §2 契约 6 条）
> 边界：D1-D6 用户已拍板（变更建议单列·不改）；后端零改动 / 不改 SKILL_DEFS/paradigm.py 是红线（不接受推翻）

---

## 〇、一句话总评

**中风险**——按原手册直接执行会在**步 7-8 暴露 1 个体验退化（focusOnlyResults 废弃致 EMC 图面不聚焦）+ 1 个编辑态 bug（buffer sourceLayer 误判 cover）+ 1 处契约表述误导（两路径"完全一致"）**；但事实核验扎实（§3 代码地图抽核 30%+ 全对）、契约 C1-C6 全成立、架构整体合理，**修订 6 条后可降至低风险执行**。

---

## 一、逐维度结论

### A. 事实核验 — **通过**

抽核手册 §3 代码地图（行号/引用面/去向表）vs 实际代码：

| 核验项 | 手册声明 | 实际 | 结论 |
|--------|---------|------|------|
| §3.2 去向表 20 函数行号 | geoFetch:164 / ref:141 / _buildZonalFc:218 / _zonalToLayer:245 / _compareToLayer:254 / _resolveBoundaryGeo:271 / _rankToLayer:300 / _areaStatsToLayer:333 / _nearestToLayer:362 / fitToFeature:377 / _aiGroup:390 / _unionBBox:396 / focusOnlyResults:411 / _toolContentSig:425 / _defaultPaint:440 / _renderNote:449 / _SCALE_TABLE:456 / _clampM:466 / addResultLayer:473 / _registerToolboxLayer:817 | 逐一对齐，偏差 ≤ 1 行 | ✅ 全对 |
| §3.2 TOOLS 行号 | TOOLS:828-1359 / hotspot:1256-1266 | `export const TOOLS = {` :828 / `_CLS_POL` :1257 / ensure_zone:901 / density:1284 / run_python:1324 | ✅ 对（hotspot 偏差 1 行·可忽略） |
| §3.4 index.html 接线点 | tool-list:143-164 / tool-buffer:154-158 / pp-tabs:385-389 / buffer-dialog:509-581 / grid pp-pane:584-690 | tool-list:143 / tool-buffer:154 / pp-tabs:385 / buffer-dialog:509 / grid-pane:584 | ✅ 全对 |
| §3.4 sidebar 接线点 | isToolPanelEditing:15-23 / 要素按钮:448-451 / tool-*:821-826 | isToolPanelEditing:15 / _ui.tool 分派:448-451 / tool-*:821-823 | ✅ 全对 |
| §3.4 main.js / param-panel | import:17-19 / init:316-318 / param-panel:64 | import:17-19 / init:316-318 | ✅ 全对 |
| §3.1 引用面（D1 不动凭据） | main/sidebar import heatmap/grid/buffer-tool | main.js:17-19 / sidebar.js:7-9 | ✅ 凭据成立 |

**结论**：手册 §3「已全部核实」声明**属实**，行号精度高。这是手册的强项——执行时按行号定位可靠。

### B. 契约真实性 — **通过**（C3/C2 重点核验为真约束）

| 契约 | 手册声明 | 实际核验 | 结论 |
|------|---------|----------|------|
| C1 工具名不变 | stages.js:35-54 SKILL_DEFS ↔ paradigm TEMPLATE_REGISTRY | SKILL_DEFS :35 确认；12 工具名 | ✅ |
| C2 rows 判定 | harness.js:379 _ANALYTICAL_TOOLS | `Set(['zonal_stats','compare_regions','rank','area_stats'])` :379；`hasRows` :341 认 rows 非空 | ✅ **真约束**（ForAI 必须回传 rows） |
| C3 mode→how 别名 | stages.js:10-22 _PARAM_ALIAS | `_PARAM_ALIAS[mode]='how'` :21 确认；overlay 用 `how` 参数 | ✅ **真约束**（D4 用 `kind` 避让正确·若 buffer 用 `mode` 会撞 overlay 的 how） |
| C4 setToolContext | harness.js:321,597 | runTemplatePath :321 / while-loop :597 两处注入 | ✅ |
| C5 F3 gate | harness.js:378-397 _GEO_TOOLS | `_GEO_TOOLS` :378 = 11 工具名；按名比对 | ✅ 工具名不变即免疫 |
| C6 _verifyClaims | harness.js:218-242 | _verifyClaims :218；:368/:696/:710/:733 多处调用 | ✅ 命名语义约束成立 |

**结论**：6 条契约全部成立，C3（mode 别名）是 D4 kind 决策的真实依据。

### C. 架构合理性 — **存疑（2 点）**

**C-① shared.js 抽取范围基本合理，但 import 来源 7 个偏多**（§5.1 末）：state/map/sidebar/import/landuse_colors/api/grid-tool。shared.js 成为「大杂烩基建」，其中 `sidebar.js`（renderLayerList/refreshLegend）构成循环（见 D-①）。defaultPaint 依赖 polarityStops（grid-tool）、buildZonalFc 依赖 piToNorm（grid-tool）—— 与既有 heatmap/grid-tool 模式一致（它们也 import sidebar·见 D-①），延续可接受，但应在手册点明。

**C-② focusOnlyResults 废弃论证不足**（§3.3③）：手册说「EMC 的 focusOnlyResults 差异废弃，两路径统一向 Toolbox 语义（enforceMutualExclusion）看齐」。但二者语义不同：
- `enforceMutualExclusion`（state.js）：**同类层互斥**（新 heatmap 替换旧 heatmap）。
- `focusOnlyResults`（tools.js:411）：**关所有其他层**（沉浸聚焦本轮结果·EMC 回答场景特有·tools.js:515 在 addResultLayer 内调用）。

废弃 focusOnlyResults → EMC 回答产出图层时，其他数据层不关 → 图面叠层混乱（用户问「西陵区情绪」→ 出图，但之前载入的伍家岗点层/范围层都还在）。**这是 EMC 体验退化**，手册把它当「消重/统一」利好，未论证体验影响。详见「决策变更建议 1」。

**手册自相矛盾**：§3.2 去向表说「focusOnlyResults :411 留 tools.js」，§3.3③ 说「废弃」——去留不清。

### D. 风险盲区（手册自认之外·4 点）

**D-① 循环依赖（既有模式·手册未说明）**：
- 现状：grid-tool.js:12 / heatmap-tool.js:12 都 `import { renderLayerList, refreshLegend, showLayerManager } from './sidebar.js'`；sidebar.js:7-9 import grid/heatmap/buffer-tool（openXxxDialog）。
- 即现状已有 **sidebar → tool-module → sidebar** 循环。
- 手册让 shared.js 也 import sidebar（renderLayerList）→ 延续既有模式。
- **实际不崩**（ES module 函数提升 + 运行时调用，renderLayerList 是 hoisted function declaration），但手册 §1 依赖红线只说「toolbox 禁 import ai_qa」，**未识别/未说明此循环**。
- 风险：若后续有人改 sidebar.js 顶层 const 求值依赖 toolbox export，会触发 TDZ。手册应显式标注「循环是既有模式，shared.js 延续，仅限函数级调用安全」。

**D-② 两路径「产出完全一致」表述误导（§0）**：
- §0 一句话任务说「两条触发路径调用同一批模块，产出完全一致」。
- 但 §3.3② 明确 addToolboxLayer（手动 + ForAI 通用）**不含** registry/$n/consumed/focusOnlyResults；EMC 元数据由委托层 `_adoptToolboxResult` 补。
- 即：Toolbox 手动路径产物**无 EMC registry/$n**；EMC 对话路径才有。
- 后果：用户手动生成层后，EMC 用 `$n` 引用或 registry 查询时，手动层不在 registry → 引用失败。
- 这可能是设计意图（手动层非 EMC 产出），但 §0「完全一致」表述不准，易误导执行者。

**D-③ paradigm GEO_TOOL_CATALOG 与实现漂移（§7 红线张力）**：
- 组 A 完成报告 §三已改 paradigm.py:213-240/:251（GEO_TOOL_CATALOG：rank/area_stats/nearest yields 补成图 + density params 对齐）。
- 手册 §7 纪律「不改 SKILL_DEFS/paradigm.py」——但本工程改 buffer 为双模式（`kind:'cover'|'emotion'`），catalog 的 buffer 条目（yields/params）需同步描述，否则 LLM 看到的工具描述与实际实现漂移。
- 手册红线「不改 paradigm.py」与本工程 buffer 实现演化**有张力**，未处理。

**D-④ buffer 编辑态兼容推断 bug（§4.3·真 bug）**：
- 组 A EMC buffer 产物 `_ui={tool:'buffer', distance, dissolve, lineWidth, fillOpacity, lineStyle}`（tools.js:1205）—— **无 kind**。
- :1206-1207：若 `_vl.sourceKey` 是 `layer:` 前缀或 `params.layer` 命中 → `_ui.sourceLayer = ...`。
- 手册 §4.3 兼容推断「`_ui.kind` 缺失时——有 `sourceLayer` → 'cover'；否则 → 'emotion'」。
- **碰撞**：EMC buffer 走 emotion 路径（圈内聚合·agg_cols :1194），但其 `_ui` 在 :1206 命中时会带 `sourceLayer` → 推断 **cover**（错！）→ 编辑态开 cover 面板（整层缓冲）而非 emotion 面板（圈内情绪）→ 参数回填错 + 用户重生成得到完全不同的 buffer。
- 这是真 bug，非理论风险。修法见修订清单 2。

### E. 实施顺序 — **存疑（2 点）**

**E-① 步 5（embedded nearest/hotspot）+ 步 7（emc-delegate）可合并**：nearest/hotspot 纯内嵌（无 dialog/init/tool-row·§5.6），步 5 做 ForAI + 步 7 做委托，两步对同一模块做两次——合并为「步 7 nearest/hotspot 委托时一并落 ForAI」省一轮。

**E-② 步 3（zonal/area）+ 步 4（rank/vector）可并行**：四个独立模块（zonal-tool/area-stats-tool/rank-tool/vector-tool），无相互依赖，手册串行排不必要。

**E-③ 步 7 observation 逐字比对方法缺失**：步 7 DoD 说「observation 与改前逐字比对一致（演示链命门）」——但未给方法。12 工具逐条手比不可行，需快照 diff（改前/后 evaluate ForAI 各工具返 observation 字符串→JSON→diff）。手册应明确此方法。

### F. 验证充分性 — **存疑**

**步 8 E2E 不兜步 7 委托回归**：
- 步 8 跑「7 tool-row 开 pane + 每工具 UI 生成 + ForAI 直调 + Buffer 双模式 + EMC 流水线代表性问句」。
- 但「代表性问句」不覆盖 12 工具逐条 observation。若某工具委托后 `_fmtRow`（:196）或 `_renderNote`（:449）后缀丢失，步 8 代表性问句可能漏检。
- 演示链命门（observation 逐字）需**逐工具快照比对**，手册步 8 未列。
- 建议步 8 加「12 工具 ForAI 返 observation 改前/后 diff 全通过」硬 gate（配合 E-③ 方法）。

---

## 二、决策变更建议（1 项·交用户复核·不直接改）

### 建议 1：保留 focusOnlyResults（推翻 §3.3③「废弃」决策）

**手册决策**：§3.3③「EMC 的 focusOnlyResults 差异废弃，两路径统一向 Toolbox 语义（enforceMutualExclusion）看齐」。

**变更建议**：**保留 focusOnlyResults**，EMC 委托层 `_adoptToolboxResult` 照旧调用；toolbox 模块 ForAI 落图调 enforceMutualExclusion（手动场景独占）；EMC 委托层在 addResultLayer/addToolboxLayer 之上叠 focusOnlyResults（EMC 场景沉浸聚焦）。

**证据**：
1. 语义不同（C-②）：enforceMutualExclusion = 同类层互斥；focusOnlyResults = 关所有其他层。后者是 EMC「回答聚焦本轮」的产品语义，前者替代不了。
2. 调用点：focusOnlyResults 在 addResultLayer :515 调用——**每个 EMC 工具产出都走**。废弃 = 所有 EMC 工具产出后不再沉浸聚焦。
3. 体验退化实证：EMC 问「西陵区情绪」→ 出图层，若不 focusOnlyResults，之前载入的伍家岗点层/范围层/其他结果层都还在 → 图面叠层，用户难辨「这次回答的层是哪个」。
4. 手册自相矛盾：§3.2 说 focusOnlyResults :411 留 tools.js，§3.3③ 说废弃——执行者无所适从。

**「统一工具集」的本意**应是「两路径产出的**图层**一致」（同一 _execute 核 + 同一 ForAI），而非「**聚焦行为**统一」。EMC 对话场景的沉浸聚焦是 AI 体验设计，不应为「统一」牺牲。

**若用户认可**：§3.3③ 改为「toolbox 模块 ForAI 落图调 enforceMutualExclusion；EMC 委托层 _adoptToolboxResult 保留 focusOnlyResults 调用（EMC 沉浸聚焦·与 Toolbox 手动场景差异化·产品本意）」。

---

## 三、手册修订清单（逐条·汇总后由用户定夺再落版）

| # | 位置 | 改成什么 | 为什么 |
|---|------|----------|--------|
| 1 | §3.3③ + §3.2 focusOnlyResults | 配合「建议 1」：保留 focusOnlyResults；§3.2 明确「:411 定义留 + :515 addResultLayer 内调用保留」；§3.3③ 删「废弃」改「差异化保留」 | C-② 体验退化 + 手册自相矛盾 |
| 2 | §4.3 buffer 编辑兼容推断 | EMC buffer 委托层（步 7）产物 `_ui` 显式写 `kind:'emotion'`（不靠推断）；推断逻辑补「有 `distance` 字段且无 `kind` → emotion」（distance 是 EMC emotion 路径必有·cover 路径无） | D-④ 真 bug：sourceLayer 误判 cover |
| 3 | §0 一句话任务 | 「产出完全一致」→「**图层产出一致**（同一 _execute 核）；EMC 元数据（registry/$n/provenance/沉浸聚焦）仅 EMC 对话路径补」 | D-② 表述误导 |
| 4 | §7 纪律「不改 paradigm.py」 | 补例外：「GEO_TOOL_CATALOG 的 buffer 条目 yields/params 同步双模式 kind 描述（与实现同步·避 LLM 描述漂移）」—— 或明确「catalog 描述同步交后续组 D SOP 卡批次」 | D-③ 红线与实现演化张力 |
| 5 | §1 + §5.1 循环依赖 | 补说明：「shared.js import sidebar（renderLayerList/refreshLegend）是**既有模式**（grid-tool:12/heatmap-tool:12 同），ES module 函数提升下运行时调用安全；严禁 sidebar.js 顶层 const 求值依赖 toolbox export（TDZ 风险）」 | D-① 未识别循环 |
| 6 | §6 步 8 验证 | 加硬 gate：「12 工具 ForAI 返 observation 改前/后 JSON diff 全通过（步 7 委托逐工具 snapshot 比对·演示链命门）」 | F + E-③ 验证缺口 |
| 7（可选） | §6 步 5 + 步 7 | nearest/hotspot 合并进步 7（无 UI·省一轮）；步 3/4 并行批 | E-① E-② 省时 |

---

## 四、不改手册原文件确认

本报告为评审意见，**未修改** `.codebuddy/plans/toolbox-unified-toolset-execution.md`。修订清单 7 条 + 决策变更建议 1 项，汇总交用户定夺后由 K3 落版。

## 五、边界守约

- D1-D6（用户拍板决策）：未直接改；建议 1（focusOnlyResults）以「决策变更建议」单列交复核。
- 后端零改动 / 不改 SKILL_DEFS/paradigm.py 红线：未推翻；修订 4 是「catalog 文案同步」（GEO_TOOL_CATALOG 非 SKILL_DEFS·组 A 已改过·属文案对齐非红线破例），或明确交后续组。

## 附：抽核覆盖度

- §3.2 去向表：20 函数行号 + TOOLS/hotspot（全核）
- §3.4 接线点：index.html 5 锚点 + sidebar 3 段 + main 2 段 + param-panel（全核）
- §3.1 引用面：3 模块 import（全核）
- §2 契约：6 条全核（C2/C3 重点）
- §3.3 分工：addToolboxLayer/addResultLayer（核 addResultLayer :473/:515 + focusOnlyResults）
- buffer _ui 字段：tools.js:1205-1207（核编辑态兼容）
- 循环依赖：grid-tool.js:12 / heatmap-tool.js:12 / sidebar.js:343（核既有模式）

**总抽核 > 30%**，重点 §3.2 去向表 + §3.4 接线点 + C2/C3 契约（用户指定）全覆盖。
