# EMC 架构与运行机制第三方评估报告

> **评估方**：DeepSeek（第三方 LLM）  
> **评估日期**：2026-07-27  
> **评估对象**：Emotion Map Controller (EMC) 架构与运行机制  
> **触发用例**：用户测试「生成 L2 消极点的热力图」时，实际生成「综合彩虹图」而非极性图  
> **评估框架**：CB 机制（对照 `docs/copilot-architecture.md`「Smart Agent, Dumb Tool」内核 + 四层骨架 + 三铁律）  
> **评估范围**：EMC 全链路（Diagnose → Orchestrate → Execute → Output） + Toolbox 全量 AI 入口（14 个 `generate*ForAI`）+ Smart 层参数契约（TEMPLATE_REGISTRY / SKILL_DEFS / prompts）  
> **审计深度**：L1（全量阅读 `frontend/js/toolbox/*`、`frontend/js/ai_qa/tools.js`、`frontend/js/ai_qa/stages.js`、`ai_qa/paradigm.py`、`ai_qa/prompts.py`）

---

## 一、用例复现与根因链追踪

### 1.1 触发用例

| 项目 | 内容 |
|------|------|
| **用户输入** | 「生成 L2 消极点的热力图」 |
| **期望产出** | Toolbox「类型细分」→ `analysis=negative` → `polarity=N` → 消极极性热力图（红色系色带，如 `red-3` 或 `negative` ramp） |
| **实际产出** | 「综合彩虹图」（`rampKey='rainbow'`），数据虽正确过滤为消极点，但视觉表达不区分极性 |

### 1.2 根因链追踪（全链路 5 步）

#### Step 1: Flash Diagnose（认知层）— 部分正常

- **触发词匹配**：`B_TRACK_PARADIGM` 的 density 触发词为 `['核密度', '密度分析', '聚集强度', '热力分布', '密度', '集中']`（`paradigm.py:131`）。**「热力图」≠「热力分布」**，字符串包含关系不成立。Flash 靠语义联想而非关键词命中，路由稳定性存疑。
- **极性参数提取**：`prompts.py:85` 中 density 工具参数列表**未包含 `polarity`/`analysis`**。Flash 即使理解了「消极」的含义，也没有结构化槽位来承载。只能依赖 `SKILL_DEFS` 的 `optional_defaults.polarity: 'overall'` 兜底。

**评级**：⚠️ density prompt 未暴露极性/分析类型参数槽位，NL 意图无法完整结构化传递。

#### Step 2: Orchestrator 编排层 — 正常

`runTemplatePath` 正确派发 `TOOLS['density'](params)`，编排层不做语义转换（符合铁律 3）。

#### Step 3: EMC 执行层（tools.js density）— ⚠️ 半盲委托

`tools.js:1137-1142` 调用 `generateHeatmapForAI` 时传了 `polarity` 但未传 `rampKey`/`analysis`。无极性→色带映射逻辑。

#### Step 4: Toolbox 执行层（generateHeatmapForAI）— 🔴 能力断层

`heatmap-tool.js:818` 硬编码 `rampKey: 'rainbow'`，完全不调用手动 UI 的核心路由函数 `computeStyle()`（`heatmap-tool.js:93-109`）。`computeStyle` 正确实现了 `analysis → rampKey` 的路由，但 AI 入口完全绕过了它。

**断层对比**：

| 维度 | Toolbox UI 路径（手动） | Toolbox AI 入口（generateHeatmapForAI） |
|------|------------------------|----------------------------------------|
| 分析类型 | `ANALYSIS_PRESETS` 四选一 | ❌ 无 `analysis` 参数 |
| 色带选择 | `computeStyle()` 自动推导 | ❌ 硬编码 `rampKey='rainbow'` |
| 大类/小类筛选 | `macroFilter` + `typeChips` | ❌ 无（`filterFc` 传 `null`） |
| 分段默认参数 | `SEGMENT_DEFAULTS[analysis]` 按极性差异化 | ❌ 仅 `DEFAULTS` 统一值 |

#### Step 5: 输出层 — N/A（问题在执行层已发生，无纠正机会）

### 1.3 根因一句话

> EMC `density` 工具 → `generateHeatmapForAI` 委托链路中，**极性→色带映射逻辑完全缺失**，且 Toolbox AI 入口未实现与手动 UI 对等的 `computeStyle` 路由能力。

---

## 二、系统性 Toolbox AI 入口审计（全量 14 个 generate*ForAI）

为判断此次问题是个案还是系统性问题，对全部 14 个 Toolbox AI 程序化入口进行了逐函数审计，对照手动 UI 能力。

### 2.1 审计总表

| # | AI 入口函数 | 文件 | 参数契约完整度 | 与手动 UI 对等度 | 关键缺口 |
|---|-----------|------|:---:|:---:|------|
| 1 | `generateHeatmapForAI` | `heatmap-tool.js:817` | 🔴 40% | 🔴 30% | 缺 `analysis`/`computeStyle`/`rampKey` 路由 |
| 2 | `generateTerrainForAI` | `heatmap-tool.js:863` | 🟡 70% | 🟡 70% | `polarity`→`rampKey` 已正确映射（`terrainRampOf`），基本合格 |
| 3 | `generateGridForAI` | `grid-tool.js:397` | 🟡 75% | 🟡 75% | `polarity` 已有默认路由，缺 `maxHeight`/`extrusionOpacity` AI 通道 |
| 4 | `generateZonalForAI` | `toolbox/zonal-tool.js` | ✅ 85% | ✅ 85% | 参数较完整，色带自动路由(`polarityStops`) |
| 5 | `generateCompareForAI` | `toolbox/zonal-tool.js` | 🟡 75% | ✅ 85% | prompt 未暴露，SKILL_DEFS 失步 |
| 6 | `generateRankForAI` | `toolbox/rank-tool.js` | ✅ 85% | ✅ 85% | `by` 默认值 'polarity' 无效（应为 'worst'） |
| 7 | `generateAreaStatsForAI` | `toolbox/area-stats-tool.js` | ✅ 85% | ✅ 85% | `group_by` 未入 SKILL_DEFS |
| 8 | `generateOverlayForAI` | `toolbox/vector-tool.js` | ✅ 80% | ✅ 80% | `as`/`keep` 未入 SKILL_DEFS |
| 9 | `generateClipForAI` | `toolbox/vector-tool.js` | ✅ 85% | ✅ 85% | `layer`/`pre_filter` 未入 SKILL_DEFS |
| 10 | `generateExtractForAI` | `toolbox/vector-tool.js` | 🟡 75% | ✅ 80% | `where` 未入 SKILL_DEFS optional_defaults |
| 11 | `generateMergeForAI` | `toolbox/vector-tool.js` | 🟡 75% | ✅ 80% | `by` 未入 SKILL_DEFS |
| 12 | `generateFilterForAI` | `toolbox/vector-tool.js` | ✅ 80% | ✅ 80% | 参数基本对齐 |
| 13 | `generateNearestForAI` | `toolbox/nearest-tool.js` | ✅ 85% | ✅ 85% | `layer` 未入 SKILL_DEFS |
| 14 | `generateHotspotForAI` | `toolbox/hotspot-tool.js` | ✅ 85% | ✅ 85% | `invert` 默认逻辑脆弱 |

### 2.2 严重程度分级

**🔴 P0 — 功能缺陷（直接影响用户可见产出）：**

| # | 函数 | 问题 | 影响 |
|---|------|------|------|
| **H1** | `generateHeatmapForAI` | `rampKey` 硬编码 `'rainbow'`，无 `analysis` 维度 | 所有 EMC 触发的热力图都是综合彩虹图，无法产出极性细分图 |
| **H2** | `tools.js` density 工具 | 调用 `generateHeatmapForAI` 时未传 `rampKey`/`analysis` | 即使 H1 修了，EMC 侧也不传这些参数 |
| **R1** | `generateRankForAI` | `by: 'polarity'` 不是有效值（后端接受 `'worst'`/`'best'`/`'domain:X'`/`'element:X'`） | Flash 按默认值 `by='polarity'` 调用 rank 时，后端走 else 分支降级为 worst-first，碰巧工作但语义错误 |

**⚠️ P1 — 参数契约缺口（影响 AI 表达完整意图的能力）：**

| # | 问题 | 涉及文件 |
|---|------|---------|
| **P1a** | density prompt 参数名与代码不一致：prompt 写 `bandwidth_m`/`cell_size_m`/`value_col`，代码读 `radius`/`cell_size`/`weightField` | `prompts.py:85` vs `tools.js:1138-1141` |
| **P1b** | `_PARAM_ALIAS` 全局映射 `radius→radius_m` 与 density 工具冲突——density 读 `params.radius`，被 normalizeParams 重命名为 `radius_m` 后丢失 | `stages.js:12` vs `tools.js:1140` |
| **P1c** | `compare_regions` 完全不在 AGENT_TEMPLATE 的可用工具列表中 | `prompts.py:68-86` |
| **P1d** | `compare` 的 SKILL_DEFS.optional_defaults 与 paradigm.py 不一致：paradigm 有 `agg_cols`，SKILL_DEFS 无 | `paradigm.py:359` vs `stages.js:45` |
| **P1e** | 8 个工具的 SKILL_DEFS 缺少 `layer` 参数（zonal/rank/clip/buffer/nearest/hotspot/filter_attr/density） | `stages.js:35-53` |
| **P1f** | 6 个工具的 SKILL_DEFS 缺少 `as`/`keep` 通用参数 | `stages.js:35-53` |

**⚠️ P2 — 路由稳定性 / 知识完整性：**

| # | 问题 | 涉及文件 |
|---|------|---------|
| **P2a** | `B_TRACK_PARADIGM` density 触发词缺少「热力图」 | `paradigm.py:131` |
| **P2b** | `TEMPLATE_REGISTRY` density `planning_common` 未描述极性细分能力 | `paradigm.py:330` |
| **P2c** | `select_template()` 不感知极性维度 | `paradigm.py:479-513` |
| **P2d** | `generateGridForAI` / `generateTerrainForAI` 的 `maxHeight`/`extrusionOpacity`/`levels` 等高级参数无 AI 通道 | `grid-tool.js:423` / `heatmap-tool.js:864` |
| **P2e** | 多个工具的 `pre_filter` 格式（`field/op/value` 字符串）未在任何 SKILL_DEFS 中描述 | 跨文件 |

---

## 三、Smart 层 ← → Dumb 层参数契约对照（系统性问题分析）

### 3.1 契约断层的三个维度

对各工具的三层参数定义（SKILL_DEFS / Prompt 描述 / 实际代码入参）进行交叉比对后，发现契约断层表现为三种模式：

#### 模式 A：Skill 定义 < 代码能力（最常见）

13/14 个工具存在此问题。SKILL_DEFS 只暴露了部分参数，导致 Flash 在 diagnose 阶段无法通过参数化表达完整意图。例如：

```
density:
  SKILL_DEFS:  { mode, radius, weightField, cell_size, polarity }      (5 个)
  代码实际接受: { mode, level, polarity, radius, opacity, intensity,     (10+ 个)
                weightField, weightCurve, intensityMin, rampKey, ... }
```

#### 模式 B：Prompt 描述 ≠ 代码入参（参数名漂移）

只影响 density 工具，但影响严重：

```
prompts.py 写的:  bandwidth_m, cell_size_m, value_col
代码实际读的:     radius,      cell_size,   weightField
```

Flash 按 prompt 写 `{"bandwidth_m": 800}` → normalizeParams 不识别此别名 → 参数被忽略 → 代码用默认值 300。**Flash 遵守 prompt 指引反而导致参数丢失。**

#### 模式 C：全局副作用（_PARAM_ALIAS 误伤）

`stages.js:12` 的全局别名 `radius → radius_m` 是为 buffer 工具设计的，但 `normalizeParams` 对所有工具生效。density 工具读 `params.radius`，被别名重写为 `params.radius_m` 后丢失。

### 3.2 契约断层的根因

1. **SKILL_DEFS 是后期追加的**：`SKILL_DEFS` 作为 P1 编排层在 Toolbox 后引入，参数定义时保守（只放最常用参数），未与 Toolbox 代码全量对齐
2. **Prompt 与代码独立演进**：`prompts.py` 中的工具描述是手工维护的，与工具实际签名的同步依赖人工
3. **缺少契约校验层**：没有自动化测试验证「SKILL_DEFS declared params ⊆ Toolbox actually accepted params」和「Prompt described params ⊆ Toolbox actually accepted params」

---

## 四、实操修复计划（Phased Implementation Plan）

### Phase 0：紧急修复（🔴 P0，1 个会话，2 文件）

**目标**：让「生成 L2 消极点的热力图」产出极性正确的热力图。

#### Task 0.1：`generateHeatmapForAI` 增加 analysis 参数 + computeStyle 路由

**文件**：`frontend/js/heatmap-tool.js:817-856`

**改动**：

```javascript
// Before (line 817-818):
export async function generateHeatmapForAI(opts = {}) {
  const p = { radius: 200, opacity: 0.7, intensity: 0.6,
              weightField: 'emotion_intensity', weightCurve: 'linear',
              intensityMin: 0, rampKey: 'rainbow', silent: true, ...opts };

// After:
export async function generateHeatmapForAI(opts = {}) {
  const p = { analysis: 'terrain', level: 'L2', polarity: 'ALL',
              radius: 200, opacity: 0.7, intensity: 0.6,
              weightField: 'emotion_intensity', weightCurve: 'linear',
              intensityMin: 0, silent: true, ...opts };
  // 使用与手动 UI 相同的 computeStyle 自动推导 rampKey/rampStops
  const style = computeStyle(p.analysis, p.level, p.polarity, null);
  const rampKey = style.ramp;
  const rampStops = style.rampStops;
  // 移除原有的 opts.rampKey 覆盖（computeStyle 为权威源）
```

同时修改 `_ui` 写入（line 844）：`analysisKey` 改用 `p.analysis` 而非硬编码 `'terrain'`。

**验证**：
- 浏览器 console 调用 `generateHeatmapForAI({analysis:'negative', polarity:'N'})` 输出 `rampKey='negative'` 的热力图
- 调用 `generateHeatmapForAI({polarity:'N'})`（不传 analysis）自动推导 `analysis='negative'`

#### Task 0.2：`tools.js` density 工具补传 analysis / 极性→analysis 自动推导

**文件**：`frontend/js/ai_qa/tools.js:1121-1154`

**改动**（在 line 1136 前插入极性→analysis 映射）：

```javascript
// 极性 → analysis 映射（与 Toolbox ANALYSIS_PRESETS 对齐）
const _POL_TO_ANALYSIS = { P: 'positive', N: 'negative', O: 'neutral', ALL: 'terrain', overall: 'terrain' };
const _analysis = params.analysis || _POL_TO_ANALYSIS[params.polarity] || 'terrain';
```

然后在 `generateHeatmapForAI` 调用中传入 `analysis: _analysis`。

**验证**：
- EMC 输入「生成 L2 消极点的热力图」→ 产出使用 `negative` ramp 的热力图
- EMC 输入「做热力图」（无极性词）→ 产出 `rainbow` 综合彩虹图（保持向后兼容）

#### Task 0.3：修复 `_PARAM_ALIAS` 对 density 的误伤

**文件**：`frontend/js/ai_qa/stages.js:12`

**改动**：将全局 `radius → radius_m` 映射改为仅对 buffer 工具生效。

**方案 A（推荐·最小改动）**：在 `tools.js` density 工具中同时读 `params.radius_m || params.radius`：

```javascript
// tools.js:1140
radius: _clampM(Number(params.radius_m || params.radius) || _scaleRadius(params.range) || 300),
```

**方案 B**：让 `normalizeParams` 支持按工具区分别名（结构性更好但改动大）。

**验证**：EMC 输入「做热力图，半径 500」→ 产出 500m 半径的热力图（当前因别名丢失，始终 300m）。

---

### Phase 1：参数契约补全（⚠️ P1，1-2 个会话，3 文件）

**目标**：让 Flash 能够通过 diagnose card 表达全部 Toolbox 支持的参数。

#### Task 1.1：`prompts.py` density 工具描述修复

**文件**：`ai_qa/prompts.py:85-86`

**改动**：将 density 工具描述中的参数名对齐代码实际签名：

```
Before:
density：核密度(KDE)栅格...params: {"bandwidth_m": 800, "cell_size_m": 300,
  "value_col": "...", "layer": "...", "range": "...", "as": "...", "keep": "..."}

After:
density：核密度(KDE)/热力图...params: {"mode": "2d|3d|terrain", "analysis": "terrain|positive|negative|neutral",
  "polarity": "ALL|P|N|O", "level": "L1|L2|L3|L4", "radius": 300,
  "weightField": "emotion_intensity", "cell_size": 600, "layer": "...", "range": "...",
  "as": "...", "keep": "..."}
  **polarity/analysis 说明**：综合/总体→analysis=terrain/polarity=ALL；积极→analysis=positive/polarity=P；
  消极→analysis=negative/polarity=N；中性→analysis=neutral/polarity=O。
```

#### Task 1.2：`SKILL_DEFS` density 参数补全 + 其他工具补 `layer`/`as`/`keep`

**文件**：`frontend/js/ai_qa/stages.js:37`

**改动**：

```javascript
density: { tool: 'density', category: 'single', required_slots: [],
  optional_defaults: { mode: '2d', analysis: 'terrain', polarity: 'overall',
    radius: 300, weightField: 'emotion_intensity', cell_size: 600,
    level: 'L2' } },
```

同时为其他工具补通用参数（以 zonal 为例）：

```javascript
zonal: { tool: 'zonal_stats', category: 'single', required_slots: ['boundary'],
  optional_defaults: { agg_cols: ['score'], layer: null, as: null, keep: false } },
```

#### Task 1.3：`TEMPLATE_REGISTRY` density 知识描述更新

**文件**：`ai_qa/paradigm.py:326-330`

**改动**：`planning_common` 增加极性细分能力描述：

```python
'planning_common': '委托主 Toolbox（固定 HEATMAP_RAMPS 色段，可切 2D/3D）：2D=彩虹热力图(radius 步行尺度)；3D=网格聚合(cell 400~1000m)。'
                    '综合/总体→analysis=terrain(彩虹)；积极/消极/中性→analysis=positive/negative/neutral(对应色带)。'
                    '数据走 Layers 可见层（未显示层禁用）'
```

#### Task 1.4：修复 `compare_regions` prompt 缺失

**文件**：`ai_qa/prompts.py:68-86`

**改动**：在 AGENT_TEMPLATE 工具列表中加入 `compare_regions`。

#### Task 1.5：修复 `compare` SKILL_DEFS 与 paradigm.py 不一致

**文件**：`frontend/js/ai_qa/stages.js:45`

**改动**：

```javascript
compare: { tool: 'compare_regions', category: 'single', required_slots: ['boundaries'],
  optional_defaults: { agg_cols: ['score', 'polarity_index'] } },
```

#### Task 1.6：修复 `rank` by 默认值

**文件**：`ai_qa/paradigm.py:334`

**改动**：`'by': 'polarity'` → `'by': 'worst'`（对齐后端有效值和 prompt 文档）

---

### Phase 2：路由稳定性 / 知识完整性（⚠️ P2，1 个会话，2 文件）

#### Task 2.1：B_TRACK_PARADIGM 触发词补全

**文件**：`ai_qa/paradigm.py:131`

**改动**：

```python
'triggers': ['核密度', '密度分析', '聚集强度', '热力分布', '热力图', '热力', '密度', '集中'],
```

#### Task 2.2：`select_template()` 增加极性维度感知

**文件**：`ai_qa/paradigm.py:479-513`

**改动**：在 B 赛道 density 匹配后，进一步检查 `card.params` 中的 `polarity` 或 `analysis` 字段，返回时附带极性信息（不影响当前 template ID 选择，但增强 Flash 的诊断精度）。

**注**：此改动较低优先——当前架构下极性细分通过 params 传递而非独立 template，保持单一 `density` 技能 + 增强参数化是正确方向。

#### Task 2.3：`generateGridForAI` / `generateTerrainForAI` 高级参数暴露

**文件**：`ai_qa/paradigm.py:326-330`、`frontend/js/ai_qa/stages.js:37`

**改动**：在 SKILL_DEFS density 中增加 `maxHeight`/`extrusionOpacity`/`levels` 等高级参数（默认不填，手动 UI 的高级参数，AI 可选传）。

---

### Phase 3：防护机制（1 个会话，1 新文件 + 1 现有文件）

#### Task 3.1：参数契约一致性校验脚本

**新建文件**：`tests/validate_skill_params.py`

**功能**：自动化校验
1. SKILL_DEFS 中每个 skill 的 `optional_defaults` 声明的参数 ⊆ 对应 `generate*ForAI` 实际接受的参数
2. `prompts.py` 中每个工具的 params 描述 ⊆ 实际代码接受的参数
3. `_PARAM_ALIAS` 不与任何工具的 params 产生误伤（交叉验证）

**集成**：加入 `tests/` 目录，可被 `python -m pytest tests/ -q` 执行。

#### Task 3.2：AGENTS.md 添加 Toolbox AI 入口开发规范

**文件**：`AGENTS.md`（编码铁律区域）

**新增铁律（建议 11）**：
> **Toolbox AI 入口与手动 UI 同构**：每新增/修改 `generate*ForAI` 函数须同步更新：(1) `SKILL_DEFS` 参数声明；(2) `prompts.py` 工具描述；(3) `TEMPLATE_REGISTRY` 知识描述。三者参数集合须为 AI 入口实际参数的**超集**（可少不可多，可漏不可错）。

---

### Phase 实施优先级总表

| Phase | 任务数 | 文件数 | 预计会话 | 影响面 |
|-------|:---:|:---:|:---:|------|
| **Phase 0** 紧急修复 | 3 | 2 | 1 | 直接修复触发用例 + 同类问题 |
| **Phase 1** 参数补全 | 6 | 3 | 1-2 | Flash 意图表达完整度显著提升 |
| **Phase 2** 路由稳定 | 3 | 2 | 1 | 边界 case 覆盖 + 高级参数 |
| **Phase 3** 防护 | 2 | 2 | 1 | 防回归 |

---

## 五、架构评估（对照 Smart Agent / Dumb Tool 内核）

### 5.1 总体评分

| 维度 | 评分 | 趋势 | 说明 |
|------|:---:|:---:|------|
| 认知层（Smart·意图理解） | ⚠️ 6/10 | → | diagnose 结构完整，但 density 工具文档未暴露全部参数槽位 |
| 编排层（Orchestrator·确定性） | ✅ 9/10 | → | 分流/派发/三态出口机制成熟，铁律 3 合规 |
| **执行层（Dumb·Tool）** | **🔴 4/10** | ↓ | **系统性参数契约不完整**——14 个 AI 入口中 1 个功能缺陷、6 个参数缺口 |
| 输出层（Smart·结果呈现） | ✅ 8/10 | → | finalStep + Review + Revise 机制健全 |
| **整体** | **⚠️ 6.5/10** | → | 架构骨架正确，但执行层存在系统性参数契约问题 |

### 5.2 核心诊断

此次触发用例暴露了一个**系统性问题**而非孤立 bug：

> **Dumb Tool 的参数契约不完整**是 EMC-Toolbox 集成中的系统性短板。`generateHeatmapForAI` 是最严重的案例（硬编码 `rampKey`），但 14 个 AI 入口中有 7 个存在不同程度的参数契约缺口，3 个存在 prompt 文档与代码不一致。

**这不是「Smart Agent 不够 Smart」的问题，而是「Dumb Tool 不够完整」的问题。** Dumb 的正确含义是「不内嵌推理、纯执行」，而非「功能子集」。AI 入口的能力应为手动 UI 的**超集或等集**，而非真子集。

### 5.3 「Smart Agent, Dumb Tool」落地评估

对照 `docs/copilot-architecture.md` 四铁律：

| 铁律 | 合规状态 | 关键发现 |
|------|:---:|------|
| 1. Tool 越 dumb 越好 | ⚠️ | Tool 够 dumb（无 LLM 内嵌），但 dumb ≠ 残缺。参数契约不完整导致「能做一种」而非「能做全」 |
| 2. Agent 聪明只在两端 | ✅ | Smart 在 diagnose + finalStep，Dumb 在 tools，边界正确 |
| 3. 编排器确定性 | ✅ | `runTemplatePath` 纯参数化执行，0 中间 LLM 轮 |
| 4. 计划-执行分离 | ⚠️ | 流程正确，但 Skill 粒度粗致「计划」无法区分综合/细分 |

---

## 六、总结

### 6.1 架构健康度

EMC 的**架构骨架是健康的**——四层分离清晰、Smart/Dumb 边界明确、三态出口成熟、抗漂移防线完善。CPD 编排引擎与 EMC 正交解耦，设计合理。

### 6.2 核心问题

此次暴露的问题**不是架构问题，而是接口完整性问题**：

> Toolbox 的 14 个 AI 程序化入口（`generate*ForAI`）在追求「Dumb」的过程中，**参数契约系统性不完整**——最严重的是 `generateHeatmapForAI` 硬编码 `rampKey='rainbow'` 完全绕过手动 UI 的 `computeStyle` 路由，其余 6 个入口存在不同程度的参数缺口。

### 6.3 一句话诊断

> **Smart Agent 想得对，Dumb Tool 做不到——不是因为 Tool 不够 Dumb，而是因为 Tool 的参数契约不够完整。**

修复方向明确且分阶段可执行：Phase 0 紧急修 `generateHeatmapForAI` + `tools.js` density 委托（2 文件 / 1 会话），Phase 1 系统性补全参数契约（3 文件 / 1-2 会话），Phase 2 路由稳定性增强（2 文件 / 1 会话），Phase 3 自动化防护（2 文件 / 1 会话）。

---

*审计覆盖：`frontend/js/heatmap-tool.js`(全量)、`frontend/js/grid-tool.js`(全量)、`frontend/js/toolbox/zonal-tool.js`(全量)、`frontend/js/toolbox/area-stats-tool.js`(全量)、`frontend/js/toolbox/rank-tool.js`(全量)、`frontend/js/toolbox/vector-tool.js`(全量)、`frontend/js/toolbox/nearest-tool.js`(全量)、`frontend/js/toolbox/hotspot-tool.js`(全量)、`frontend/js/buffer-tool.js`(全量)、`frontend/js/ai_qa/tools.js`(density 工具段全量)、`frontend/js/ai_qa/stages.js`(SKILL_DEFS + normalizeParams 全量)、`ai_qa/paradigm.py`(TEMPLATE_REGISTRY + B_TRACK_PARADIGM + select_template 全量)、`ai_qa/prompts.py`(AGENT_TEMPLATE 工具列表段全量)、`api/geo_routes.py`(Pydantic 请求模型全量)*
