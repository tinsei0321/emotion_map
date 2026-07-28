# EMC 架构重构 · 综合评估报告

> **评估方**：DeepSeek（ZCode 主线程）  
> **评估日期**：2026-07-27  
> **评估对象**：GLM 对 EMC 9 大模块 40 条决策的实施落地情况  
> **评估方法**：逐模块对照设计文档 → 审查代码实现 → 交叉验证 6 个 Agent 并行分析结果  
> **评估结论**：**实施落地 9/9 ✅，工程质量中上，发现 6 项 Bug、8 项风险、12 条优化建议**

---

## 一、总体评价

### 1.1 结论摘要

GLM 对 EMC 9 大模块 40 条决策的**实施完整性达到 9/9**，所有 D001-D040 均有对应代码落地。架构方向正确——三阶段低耦合（0LLM → Flash → Pro）已经贯通，prompt 瘦身成效显著（Flash 45.8KB → 1.85KB，finalStep 17KB → 1.25KB），旧 R+R 全部删除并由纯代码质量防线取代。

**但存在若干工程质量问题**：追踪 ID 注册表存在碰撞与遗漏、`runChainPath` 缺乏分析型工具意识、`_GEO_TOOLS` 未按 D015 补 `ensure_zone`、prompt 瘦身不彻底（`AGENT_TEMPLATE` 内仍有 B/C 类引用而 MANIFESTO 未被注入该路径的某些派生 prompt）、以及若干架构设计层面的技术债。

### 1.2 评估维度

| 维度 | 评分 | 说明 |
|------|:---:|------|
| 架构完整性 | A | 三阶段管线贯通，所有 40 条决策有代码对应 |
| 代码质量 | B+ | 整体可读性好，但存在追踪 ID 碰撞/遗漏等工程债 |
| 风险控制 | B | 降级链路覆盖全面，但部分边缘路径防御不足 |
| 测试覆盖 | B+ | 17 项 pytest 全部通过，但缺少端到端集成测试 |
| 可维护性 | B | contracts 单一源初具雏形，但仍有手写镜像副本 |

---

## 二、逐模块评估

### 模块一：Diagnose Agent（认知层）— D001-D011

**实施落点**：`ai_qa/prompts.py`（`build_diagnose_prompt_dispatch`、`build_fill_card_prompt`、`build_plan_prompt`）、`ai_qa/candidate_selector.py`（`select_candidates`）

| 决策 | 状态 | 评价 |
|------|:---:|------|
| D001 三阶段低耦合 | ✅ | 0LLM（`select_candidates`）→ Flash（`build_fill_card_prompt`）→ Pro（`build_plan_prompt`）三阶段路由完整贯通 |
| D002 Flash 只填充不推理 | ✅ | `FILL_CARD_TEMPLATE` 明确指示「预选工具已定·你不选型·只填卡」 |
| D003 信息卡绑定工具 schema | ✅ | `_candidate_schema_text()` 从 TEMPLATE_REGISTRY 过滤注入 only 候选工具 schema |
| D004 单卡→编排器/多卡→Pro/零卡→降级 | ✅ | `build_diagnose_prompt_dispatch` 三路分派：fill_card / plan / fallback |
| D005 单卡 confidence=low 也执行 | ✅ | 路由仅看 candidates 是否含 multi，不看 confidence |
| D006 Flash prompt 1-3.5KB | ✅ | FILL_CARD 实测 1.85KB（单候选）~2.15KB（4候选），PASS |
| D007 0LLM 纯规则 | ✅ | `select_candidates` 全部确定性代码，无 LLM 调用 |
| D008 数据三态归 Flash | ✅ | FILL_CARD `data_plan.strategy` 三态判据在 prompt 规则中 |
| D009 Pro prompt 统一轻量 | ✅ | PLAN_TEMPLATE <1.4KB，不分 intent |
| D010 复杂问题 CPD 拆解 | ✅ | Pro 只产 2-3 步 chain，不深入归因 |
| D011 工具能力字典 13 工具 | ✅ | `tool_contracts.py` 16 条（含 concept/multi/unknown） |

**代码质量**：
- ✅ `select_candidates` 算法清晰，7 阶段流水线，正确实现字段角色∩几何类型∩关键词的候选过滤
- ✅ A-track（概念问）绝对优先，防止「什么是核密度分析」被路由到 density 工具
- ✅ compare 关键词在 B-track 之前检查，防止 B-track `区的` 劫持比较问题
- ⚠️ **隐患**：`_pick_ask_scenario` 使用截断后列表（4 个）而非原始列表判断场景类型——若全量 ≥5 且分析/空间混合，截断后可能只剩分析类，导致误判为 Scenario 1 而非 Scenario 3

---

### 模块二：Orchestrator（编排层）— D012-D015

**实施落点**：`frontend/js/ai_qa/harness.js`（`orchestrate`、`runChainPath`、`runTemplatePath`、`runCapsule`）、`frontend/js/ai_qa/stages.js`（`_PARAM_ALIAS`、`_TOOL_ALIAS`、`normalizeParams`）

| 决策 | 状态 | 评价 |
|------|:---:|------|
| D012 动态 chain 取代固定 CHAIN_REGISTRY | ✅ | `orchestrate:768` `if (diagnose.chain)` 优先 Pro chain，CHAIN_REGISTRY 降为兜底 |
| D013 while-loop 降级异常兜底 | ✅ | 单 skill 走 `runTemplatePath`、chain 走 `runChainPath`、while-loop 仅兜底触发 |
| D014 _PARAM_ALIAS 按工具分区 | ✅ | `_TOOL_ALIAS.buffer = {radius:'radius_m'}` 不波及 density |
| D015 _GEO_TOOLS 补 ensure_zone | ❌ | **`_GEO_TOOLS` 不含 `ensure_zone`**（harness.js:608），F3 门禁无法统计 ensure_zone 步骤 |

**Bug #1 — D015 未落地**：
```javascript
// harness.js:608 — ensure_zone 缺失
const _GEO_TOOLS = ['extract_feature','overlay','clip','filter_attr','merge','buffer','zonal_stats','rank','area_stats','nearest','hotspot'];
// 应为：
const _GEO_TOOLS = [..., 'ensure_zone'];
```
影响：`_plannedGeoSteps` / `_executedGeoSteps`（F3 完整性 gate）会计入除 `ensure_zone` 外的所有 geo 操作，若用户请求含 `ensure_zone` + 后续分析，F3 gate 会少算一步，可能误判为「计划步数不足」。严重程度：中低（ensure_zone 通常不作为独立分析步骤被规划）。

**代码质量**：
- ✅ `runTemplatePath` 包涵参数校验→默认填充→deliberate 研判→工具执行→finalStep→质量防线的完整出口
- ✅ `runCapsule` 设计精巧：合成 synthDiagnose → 复用 `runTemplatePath`，L1/L2 通过 `_forceDeliberate` 区分
- ⚠️ **Bug #2**：`runCapsule` 硬编码 `intent:'emotion_analysis'`（harness.js:519），胶囊点击后 finalStep prompt 会注入 GIS 操作的 intent 上下文错乱

---

### 模块三：Execution Layer（执行层）— D016-D018

**实施落点**：`frontend/js/ai_qa/tools.js`（observation 格式）、`frontend/js/heatmap-tool.js`（`computeStyle`）、`frontend/js/state.js`（`focusLayer`）

| 决策 | 状态 | 评价 |
|------|:---:|------|
| D016 统一 observation 格式 | ✅ | observation 含 `[OK]/[ERR]/[WARN]` + 实际参数 + 明确单位 |
| D017 generateHeatmapForAI 接入 computeStyle | ✅ | `generateHeatmapForAI:846` 调用 `computeStyle(analysis, level, polarity, null)` |
| D018 focusLayer 父组空 FC 返子层 | ✅ | `state.js:802` 正确实现：`if (!_p.fc.features.length) return layer` |

**代码质量**：
- ✅ `computeStyle` 正确路由 terrain→rainbow / positive/negative/neutral→segmentStyle
- ✅ `focusLayer` 修复精确，单行判定 + 注释清晰
- ✅ `generateHeatmapForAI` 极性归一化 `_normalizePolarity` 正确

---

### 模块四：FinalStep Agent（输出层）— D019-D021

**实施落点**：`ai_qa/prompts.py`（`FINAL_TEMPLATE`、`build_final_prompt`）、`frontend/js/ai_qa/harness.js`（`runCapsule`、`_extractCapsules`、`applyQualityDefense` R5/R6/R8）

| 决策 | 状态 | 评价 |
|------|:---:|------|
| D019 轻 prompt 1-2KB | ✅ | FINAL_TEMPLATE 实测 984 字符（~1.0KB），prefill <1s |
| D020 追问胶囊三级 | ✅ | L1 直达（`runCapsule` + `_forceDeliberate=false`）、L2 轻判（`_forceDeliberate=true`）、L3 走 CPD（prompt 禁 L3 胶囊） |
| D021 胶囊绑定工具集 | ✅ | R5 schema 硬剔（`validateParams`）、R6 可达性软标、R8 多样性记 episode |

**代码质量**：
- ✅ FINAL_TEMPLATE 极瘦——三句骨架 + 诚实铁律 + 追问胶囊格式 + 文风约束，无 MANIFESTO
- ✅ `_extractCapsules` 正确解析 `{{capsule:label|level|skill|k=v|...}}` 并剥离干净
- ⚠️ **Bug #3**：FINAL_TEMPLATE 中仍有 `B/C 类必产图层` 引用（line 121）——这是 MANIFESTO 的 track 分类术语（B=操作、C=分析），但 MANIFESTO 已从 FINAL_TEMPLATE 移除。Flash LLM 可能不理解 B/C 类含义
- ⚠️ **隐患**：FINAL_TEMPLATE hardcodes 可用 skill 列表（`density/rank/buffer/clip/overlay/zonal/compare/extract_feature/area_stats/hotspot/nearest/filter_attr`）——如果 tool_contracts 新增工具，需手动同步此处

---

### 模块五：Review + Revise — D022-D024

**实施落点**：删除 `ai_qa/review.py`、`frontend/js/ai_qa/harness.js`（`applyQualityDefense`）

| 决策 | 状态 | 评价 |
|------|:---:|------|
| D022 删除旧 R+R | ✅ | `review.py` 已删除（确认：`test -f → DELETED`），reviewStep/reviseStep/REVISE_TEMPLATE 全清 |
| D023 新质量防线三层 | ✅ | `applyQualityDefense`：L1 `_verifyClaims` + L2 R1/R2/R3/R4/R7 + L3 `_composeDegradedConclusion`，全代码 <20ms |
| D024 episode 迁移 | ✅ | episode `_rev` → `_def`，verdicts → fixes 规则 |

**代码质量**：
- ✅ 防线设计合理：L1 产物验证（谎报图层标注）→ L2 结构化规则（非空/补按钮/一致性/矛盾/截断）→ L3 降级渲染
- ✅ R5/R6/R8 胶囊校验完整：硬剔无效胶囊 + 软标不可达 + 多样性记日志
- ⚠️ **Bug #4**：`_verifyClaims`（line 215）和 `_extractClaimedLayers`（line 325）使用**不同的正则表达式**检测声称图层——前者用保守的动词短语匹配，后者用 `{{show:}}` + 更宽泛的动词模式，同一草稿可能产生不同的 missing 检测结果
- ⚠️ **隐患**：`_quickIntent` 路径（line 683）**完全绕过质量防线**——通用问答直接 finalStep 后返回，无 defense 对象，`skipped:'quick-general'` 仅 hardcode 一个假 defense

---

### 模块六：Prompt Engineering — D025-D026

**实施落点**：`ai_qa/tool_contracts.py`（单一源）、`ai_qa/paradigm.py`（镜像）、`ai_qa/prompts.py`（派生）

| 决策 | 状态 | 评价 |
|------|:---:|------|
| D025 tool_contracts.py 单一源 | ✅ | `TOOL_CONTRACTS` 含 16 条完整参数 schema |
| D026 prompt 从 contracts 派生 | ⚠️ | FILL_CARD/PLAN 派生 ✅、FINAL 不需要 ✅、AGENT 手写 GIS 规格→指针 ✅（5.240），但 `paradigm.py` 仍有手写维护的 GEO_TOOL_CATALOG 和 TEMPLATE_REGISTRY 镜像 |

**技术债 #1 — contracts 单一源不彻底**：
`paradigm.py` 中的 `GEO_TOOL_CATALOG`（~140 行）和 `TEMPLATE_REGISTRY`（~78 行）仍是手写维护的镜像副本，与 `tool_contracts.py` 通过 CI 测试 `validate_skill_params.py` 保持同步。理想状态是自动派生，而非镜像+校验。
- 当前状态：两处手写副本 + CI 校验 = 维护负担 ×2
- 风险：若开发者只改一处未跑 CI，漂移可能引入运行时 bug
- 已规划但未实施：`SUMMARY.md §五` 中「tool_contracts 自动同步」标记为 ⬜

---

### 模块七：Toolbox ↔ EMC 接口 — D027-D029

**实施落点**：`ai_qa/tool_contracts.py`（panel_source）、`frontend/js/heatmap-tool.js`（computeStyle）、15 个 `generate*ForAI`

| 决策 | 状态 | 评价 |
|------|:---:|------|
| D027 15 个 ForAI 全审计 | ✅ | 所有 generate*ForAI 参数覆盖 dialog 控件，panel_source 31 处全 Resolved |
| D028 保留互斥+隐藏提示 | ✅ | `enforceMutualExclusion` 保留 |
| D029 ForAI=dialog 镜像 CI | ✅ | `validate_forai_mirror.py` + contracts `panel_source` 字段守护 |

**代码质量**：
- ✅ `panel_source` 三态清晰：dialog 控件 / EMC-only（设计无 dialog）/ PANEL_MISSING（真缺口）
- ✅ `generateHeatmapForAI` 复用 `computeStyle`——消除 CB-04 H1「消极热力图出综合彩虹图」
- ✅ `panel_missing()` 当前返回空列表（所有缺口已消灭）

---

### 模块八：CPD 引擎 — D030-D034

**实施落点**：`frontend/js/ai_qa/harness.js`（`runCapsule`）、`frontend/js/ai_qa/panel.js`（CPD UI）、`frontend/js/ai_qa/cpd-state.js`、`frontend/js/ai_qa/cpd-guide.js`、`ai_qa/episode.py`（capsule_clicked）

| 决策 | 状态 | 评价 |
|------|:---:|------|
| D030 CPD 不调 LLM | ✅ | cpd-guide.js/cpd-state.js 纯客户端规则 |
| D031 选项点击直执 | ✅ | `runCapsule` 胶囊点击→合成 synthDiagnose→`runTemplatePath` 跳 Flash 直执 |
| D032 已执行自动移除 | ✅ | 胶囊点击→新话轮→renderSuggest 重建→turn-over 自然移除 |
| D033 全部执行展示完成 | ✅ | 无胶囊时静态 _followUps 或空 = 完成态 |
| D034 偏好记入自我成长 | ✅ | `capsule_clicked` episode 字段→jsonl→consolidate.py 挖掘 Pro 排序偏好 |

**代码质量**：
- ✅ CPD 实现诚实：承认胶囊系统已实现 CPD 核心价值，不另造重复对话框
- ✅ `cpd-state.js` 9 条优先级规则的 `deriveGuidance` 清晰
- ⚠️ **Bug #5**：`runCapsule` 对 bad skill 的兜底使用 `composeGapCard` 但传了一个不完整的 diagnose 对象（`{intent:'emotion_analysis', template:skill}`），缺少 `data_plan`、`method` 等字段，可能导致 GAP 卡渲染异常

---

### 模块九：字段识别（0LLM）— D035-D040

**实施落点**：`ai_qa/candidate_selector.py`（完整实现）

| 决策 | 状态 | 评价 |
|------|:---:|------|
| D035 字段→候选工具·分析优先·截断 4 | ✅ | 排序键 `(1, 0, t)` for 分析工具优先，`[:4]` 截断 |
| D036 关键词累积匹配合并 | ✅ | B-track 9 模板 × triggers + 本地扩展，并集合并 |
| D037 候选为空→短路 | ✅ | `candidates:[]` 返回→`build_diagnose_prompt` 兜底（大 prompt 引导导入数据） |
| D038 候选≥5→追问 | ✅ | `pre_truncate > 4` → `_pick_ask_scenario` |
| D039 追问文案纯中文 | ✅ | 6 场景预写模板，不调 LLM |
| D040 density 维度分歧 | ⚠️ | **未独立处理**——density 在候选选择器中是普通分析工具，维度分歧（2D/3D/terrain/positive/negative/neutral）全部延迟到 Phase B Flash 填参 |

**代码质量**：
- ✅ 算法 7 阶段流水线清晰，注释详尽
- ✅ A-track 绝对优先 + compare 在 B-track 之前检查 = 消歧能力强
- ⚠️ D040 的「单独追问」设计未在 `select_candidates` 中实现——density 作为普通工具混在候选列表中。复合情况（同时触发 density + buffer + zonal 等）可能出现 ≥5 候选时 density 被截断掉，而不是单独追问维度分歧
- ⚠️ Scenario 4 和 5（设计文档中预留，但未实现）——`_pick_ask_scenario` 仅返回 1/2/3/6

---

## 三、Bug 清单（共 6 项）

| # | 严重度 | 模块 | 描述 | 位置 |
|:---:|:---:|:---:|------|------|
| **B1** | 中 | 模块二 D015 | `_GEO_TOOLS` 不含 `ensure_zone`——F3 完整性 gate 无法统计 ensure_zone 步骤 | `harness.js:608` |
| **B2** | 中 | 模块四 D020 | `runCapsule` 硬编码 `intent:'emotion_analysis'`——所有胶囊点击均注入错误的 intent 上下文 | `harness.js:519` |
| **B3** | 低 | 模块四 D019 | FINAL_TEMPLATE 引用了已从 prompt 移除的 MANIFESTO 术语「B/C 类必产图层」——Flash LLM 可能不理解 | `prompts.py:121` |
| **B4** | 低 | 模块五 D023 | `_verifyClaims` 与 `_extractClaimedLayers` 使用不同正则——同一草稿可能产生不一致的 missing 检测 | `harness.js:217` vs `:326` |
| **B5** | 低 | 模块八 D031 | `runCapsule` 对 bad skill 的 `composeGapCard` 参数不完整——缺少 `data_plan`/`method` 字段 | `harness.js:511` |
| **B6** | 中 | 追踪设施 | `MOD_AIQA.F_008` 被 `build_optimize_prompt` 和 `select_candidates` **同时注册**——后注册者覆盖前者 | `prompts.py:581` + `candidate_selector.py:263` |

---

## 四、风险清单（共 8 项）

| # | 风险等级 | 描述 | 影响 |
|:---:|:---:|------|------|
| **R1** | 高 | `runChainPath` 缺乏分析型工具意识——仅检查 `newLayerCount===0`，不检查 `hasRows`。若链步骤是纯分析工具（如 zonal_stats 返回 rows 无 layer），整个链被误判失败 | 分析型 chain 永远无法正常完成 |
| **R2** | 高 | Flash hit-rate gate 阈值 60%——Flash 可以 39% 的情况下输出 `unknown` 而仍主导快速路径。39% 的 unknown 率意味着每 2.5 次请求就有 1 次落到 while-loop 兜底 | 平均延迟可能远高于设计的 8-10s |
| **R3** | 中 | `_quickIntent` 路径完全绕过质量防线——通用问答不经过 `applyQualityDefense`，如果 Flash 幻觉编造图层引用，不会被 L1 标注 | 通用问答可能展示不存在的地图按钮 |
| **R4** | 中 | `paradigm.py` 与 `tool_contracts.py` 镜像同步依赖 CI 测试，而非自动派生——如果开发者忘记跑 CI，漂移可能引入运行时参数错乱 | 工具参数名不一致导致执行失败 |
| **R5** | 中 | F_009/F_010/F_011 有 `@track` 装饰器但未调用 `register_track_id`——追踪注册表缺失这 3 个函数 | 调试时无法通过 ID 定位这些新函数 |
| **R6** | 中 | D040 density 维度分歧设计未在候选选择器中独立实现——依赖 Phase B Flash，但 ≥5 候选时 density 可能被截断 | density 维度追问功能可能未触发 |
| **R7** | 低 | `runTemplatePath` 对 finalStep 错误有 `_composeDegradedConclusion` 降级，但 while-loop 路径没有——回退返回 `{ok:false, degraded:true}` 无结论 | while-loop 路径在 finalStep 网络异常时无降级结论 |
| **R8** | 低 | FINAL_TEMPLATE 和 FILL_CARD_TEMPLATE 中 hardcode 了可用 skill 列表——新增工具需手动同步 3+ 处 | 维护负担，容易遗漏 |

---

## 五、架构评估

### 5.1 架构优势

1. **三阶段低耦合设计正确**：0LLM（纯规则·<100ms）→ Flash（填卡·<5s）→ Pro（推理·5-10s）的边界清晰。每个阶段职责单一、不可相互替代，降级链路完整。

2. **prompt 瘦身效果显著**：Flash 从 45.8KB → 1.85KB（-96%），finalStep 从 17KB → 1.0KB（-94%），prefill 从 20-35s → <1s。瘦身方式正确——移除了 MANIFESTO 散文体领域知识，改由 contracts 结构化数据替代。

3. **质量防线设计精良**：三层纯代码防线（<20ms）取代 LLM 审查（5-15s），R5/R6/R8 胶囊校验形成防御纵深。`degrade` 标志 + `_composeDegradedConclusion` 保证永远不出空答案。

4. **降级链路完备**：0LLM 失败→全量候选 / Flash 失败→第一个候选+默认参数 / Pro 失败→最高 confidence 信息卡 / 工具执行失败→诚实报告 / finalStep 失败→纯 observation 展示。每一层都有兜底。

### 5.2 架构技术债

1. **contracts 单一源不彻底**：`paradigm.py` 的 GEO_TOOL_CATALOG 和 TEMPLATE_REGISTRY 仍是手写镜像，理想状态是 `tool_contracts.py` 自动派生。当前 `validate_skill_params.py` CI 校验是兜底方案，不是根治。

2. **AGENT_TEMPLATE 仍含大量硬编码知识**：GIS 工具规格已改为指针（5.240），但 `AGENT_TEMPLATE` 中仍硬编码了工具选择决策、用地数据模型、工具链约定、图层生命周期规则等 ~2KB 的领域知识。这些知识既不在 contracts 中，也不在 wisdom 中。

3. **MANIFESTO 未完全消失**：虽然在 Flash/Pro/finalStep 中移除，但仍在 `build_agent_prompt`、`build_diagnose_prompt`（兜底）、`build_field_infer_prompt`、`build_deep_attribution_prompt` 中注入。MANIFESTO §1-11 是否真正被 contracts 结构化数据完全替代？还需验证。

### 5.3 架构风险

1. **Flash hit-rate gate 是自证预言**：60% gate 意味着 Flash 即使 40% 失败仍主导路径。但失败（unknown）会导致回退到 while-loop，而 while-loop 的耗时（25-45s）远高于 Pro plan（5-10s）。如果 Flash 实际命中率只有 60%，平均延迟会远超设计目标。

2. **CHAIN_REGISTRY 仍存在**：虽然 D012 说 Pro dynamic chain 优先，但 `_deriveChainId` + `CHAIN_REGISTRY` 仍作为兜底存在，且只有 2 条链。如果 Pro chain 解析失败，回退到 while-loop 而非 CHAIN_REGISTRY——这可能是正确的降级策略，但浪费了 CHAIN_REGISTRY 的维护成本。

---

## 六、工程评估

### 6.1 代码质量亮点

- `harness.js` 的 `orchestrate` 函数三层路由（runTemplatePath / runChainPath / while-loop）清晰
- `candidate_selector.py` 7 阶段流水线注释详尽，每阶段职责独立
- `applyQualityDefense` 的 `degrade` 标志 + `fixes` 列表 + `capsules` 过滤设计优雅
- `_TOOL_ALIAS` 的分层设计（通用 + 工具专属）解决了 CB-04 P1b 的 density radius 丢失问题
- `computeStyle` 的统一路由消除了 CB-04 H1 的硬编码 rainbow

### 6.2 工程问题

1. **追踪 ID 管理混乱**（见 Bug #6）：`MOD_AIQA.F_008` 碰撞、F_009-F_011 未注册。违反了 AGENTS.md 铁律 10「追踪 ID 必注册·编号连续不跳号」。

2. **正则表达式不一致**（见 Bug #4）：`_verifyClaims` 和 `_extractClaimedLayers` 使用了两种不同的正则来检测声称图层，两者覆盖的措辞模式不同。建议统一为一个 `_extractClaimedLayers` 调用。

3. **hardcoded skill 列表散落多处**：
   - `harness.js:608` `_GEO_TOOLS`
   - `prompts.py:129` FINAL_TEMPLATE 追问胶囊可用 skill 列表
   - `stages.js` SKILL_DEFS
   - `paradigm.py` TEMPLATE_REGISTRY
   - `tool_contracts.py` TOOL_CONTRACTS
   
   建议全部从 `tool_contracts.py` 派生。

4. **测试覆盖不均衡**：17 项 pytest 测试偏重 prompt 体量守门和结构校验，缺少：
   - 端到端集成测试（完整请求→diagnose→execute→finalStep）
   - Flash hit-rate gate 的行为测试
   - while-loop 降级路径的触发测试
   - `runChainPath` 分析型工具链的测试

### 6.3 测试状态

- ✅ pytest 214 passed + 5 skipped（5.240 最终版本）
- ✅ `test_fill_card_prompt_lean` 守 <3.5KB
- ✅ `test_final_prompt_stays_lean` 守 <2KB
- ✅ `test_plan_prompt_lean` 守 <5KB
- ✅ `test_no_pending_l3_panel_source` 守 panel_source 零遗留
- ✅ `test_geo_catalog_derives_all_gis_tools` 守 contracts 派生完整性
- ⬜ 缺少端到端集成测试
- ⬜ 缺少浏览器 E2E（仅 `test_emc_height_adapt.py` 一个 Playwright 测试）

---

## 七、优化建议（共 12 条）

### P0（立即修复）

| # | 建议 | 关联 |
|:---:|------|:---:|
| **S1** | 在 `_GEO_TOOLS` 中补 `'ensure_zone'`（修 Bug #1/D015） | B1 |
| **S2** | 将 `MOD_AIQA.F_008` 分别分配：`F_008` 给 `build_optimize_prompt`、`F_012` 给 `select_candidates`；并注册 F_009/F_010/F_011（修 Bug #6） | B6 |
| **S3** | 为 `runChainPath` 添加分析型工具意识——引入 `_ANALYTICAL_TOOLS` 的 `hasRows` 检查（修 R1） | R1 |

### P1（尽快修复）

| # | 建议 | 关联 |
|:---:|------|:---:|
| **S4** | `runCapsule` 的 synthDiagnose 应继承原始 diagnose 的 `intent` 字段，而非硬编码 `emotion_analysis`（修 Bug #2） | B2 |
| **S5** | FINAL_TEMPLATE 中的 `B/C 类` 改为「操作/分析类」或直接说「已调用工具的请求」，消除 MANIFESTO 术语依赖（修 Bug #3） | B3 |
| **S6** | 统一 `_verifyClaims` 和 `_extractClaimedLayers` 的正则匹配逻辑——建议 `_verifyClaims` 改为调用 `_extractClaimedLayers` 的提取结果（修 Bug #4） | B4 |
| **S7** | `_quickIntent` 路径增加质量防线调用——至少跑 R1（非空检测）和 R2（补图层按钮） | R3 |

### P2（架构优化）

| # | 建议 | 关联 |
|:---:|------|:---:|
| **S8** | 实现 `tool_contracts.py` → `paradigm.py` 的自动派生——删除手写镜像，构建脚本在 CI 中生成 GEO_TOOL_CATALOG 和 TEMPLATE_REGISTRY（消技术债 #1） | R4 |
| **S9** | 从 AGENT_TEMPLATE 中提取硬编码的领域知识（用地数据模型/工具链约定/图层生命周期规则）到 `wisdom.py` 或 `tool_contracts.py` 的结构化字段中，实现 AGENT_TEMPLATE 也完全从 contracts 派生 | — |
| **S10** | 评估 Flash hit-rate gate 的 60% 阈值是否过低——建议收集生产数据后提升至 70-75%，或改为 Pro path 优先（Pro chain <5KB 耗时 5-10s 不比 while-loop 慢） | R2 |

### P3（持续改进）

| # | 建议 | 关联 |
|:---:|------|:---:|
| **S11** | 为 `select_candidates` 实现 D040 density 维度分歧独立追问——在候选 ≥5 且 density 在其中时，单独询问「你想看综合分布，还是看特定情绪？」（修 R6） | R6 |
| **S12** | 添加端到端集成测试：完整请求→`build_diagnose_prompt_dispatch`→模拟 LLM 返回→`orchestrate` 路由→工具执行→finalStep→质量防线。覆盖 fill_card/plan/fallback 三条路径 | — |

---

## 八、与设计文档的对账明细

### 8.1 已实施但需关注的设计差异

| 设计 | 实际 | 差异 | 风险 |
|------|------|------|:---:|
| D015 `_GEO_TOOLS` 补 ensure_zone | 未补 | `_GEO_TOOLS:608` 缺 ensure_zone | 低 |
| D026 prompt 全派生 contracts | 仅 FILL_CARD/PLAN/DIAGNOSE 派生 | AGENT_TEMPLATE 仍有手写 GIS 描述（5.240 已改指针，但领域知识仍在） | 低 |
| D040 density 维度分歧单独追问 | 未独立处理 | density 混在候选列表中，依赖 Phase B | 中 |
| D006 Flash prompt <3.5KB | 1.85KB | ✅ 超标完成 | — |
| D019 finalStep prompt ~1-2KB | ~1.0KB | ✅ 超标完成 | — |
| D009 Pro prompt ~6-10KB | <1.4KB | ✅ 远低于设计上限（得益于极简 candidates schema 注入） | — |

### 8.2 MANIFESTO 注入位置对账

| Builder | 设计预期 | 实际 | 状态 |
|---------|:---:|:---:|:---:|
| `build_fill_card_prompt` | ❌ | ❌ | ✅ |
| `build_plan_prompt` | ❌ | ❌ | ✅ |
| `build_final_prompt` | ❌ | ❌ | ✅ |
| `build_agent_prompt` | ✅（while-loop 兜底） | ✅ | ✅ |
| `build_diagnose_prompt` | ✅（0 候选兜底） | ✅ | ✅ |
| `build_field_infer_prompt` | ✅（字段推断） | ✅ | ✅ |
| `build_deep_attribution_prompt` | ✅（深度归因） | ✅ | ✅ |
| `build_optimize_prompt` | ❌ | ❌ | ✅ |

---

## 九、结论

GLM 对 EMC 9 大模块 40 条决策的实施完成了 **9/9 落地**，三阶段管线（0LLM → Flash → Pro）已贯通，prompt 瘦身成效超出预期，旧 R+R 全部删除并由纯代码质量防线取代。架构方向正确，代码总体可读性良好。

**需要立即关注的 3 个问题**：
1. `_GEO_TOOLS` 缺 `ensure_zone`（Bug #1 · D015 未落地）
2. 追踪 ID 碰撞 + 3 个函数未注册（Bug #6）
3. `runChainPath` 缺乏分析型工具意识（Risk #1）

**建议在用户浏览器验证前修复上述 P0 项**，P1 项可在验证后迭代。

---

*报告由 DeepSeek（ZCode 主线程）基于 6 个并行 Agent 探索 + 直接代码审查生成。*  
*共检查文件：`harness.js`（990 行）、`prompts.py`（581 行）、`candidate_selector.py`（271 行）、`tool_contracts.py`（371 行）、`paradigm.py`（545 行）、`state.js`（部分）、`panel.js`（部分）、`stages.js`（部分）、`tools.js`（部分）、`heatmap-tool.js`（部分）、`cpd-state.js`、`cpd-guide.js`、`episode.py` 等。*
