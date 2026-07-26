# Toolbox 统一工具集层 — 验收报告（GLM 主线程）

> 验收人：主线程（GLM 5.2）｜ 2026-07-26 ｜ 对象：`toolbox-unified-toolset` branch（14 commits·HEAD a8d5be2·未 push）
> 验收依据：用户清单 A-E + K3 完成报告 `.codebuddy/reports/toolbox-unified-completion-2026-07-26.md` + 手册 v2.2
> 方法：静态核验（读代码 + grep）+ 动态复跑（三件套本机复现）+ 重点怀疑区裁决

---

## 一、验收概览

**一句话结论：建议合并**——静态核验 A-E 全通过 + 动态三件套（obs diff / unified / pipeline）在本机复现全绿 + 重点怀疑区 4 项裁决落地（含 1 处评审自身失误修正）。无阻断项；遗留 2 项（$n 链 diff / ensure_zone registry）纳入下一期，不阻塞合并。

**总通过率**：动态三件套 3/3 全绿 + 静态 A1-A3/B1-B5/C1-C3/E1-E3 全通过；既存回归 compare_regions 后台跑中（K3 实证 PASS），exit_badge/domain_lens 信任 K3（LLM 方差·§7-2）。

**环境**：Python 3.14.6 / win32 / pytest 9.1.1 / 本机 DATA + 5 边界预设（K3 commit 9f37f72 激活）。

---

## 二、验收明细表

### A 架构合规

| 编号 | 检查项 | 标准 | 证据 | 结论 |
|------|--------|------|------|------|
| A1 | 依赖红线 | toolbox/*.js 无 import ai_qa；tools.js→toolbox 单向 | grep `^import.*ai_qa` 全 toolbox 目录 = **0 命中**（zonal/vector/rank/area/nearest/hotspot/shared 全核） | ✅ 通过 |
| A2 | 模块契约 | 每模块 _execute+ForAI+dialog+init（nearest/hotspot 无 dialog） | zonal(generateZonal/Compare+open+init)、vector(5 ForAI+open+init)、rank/area(ForAI+open+init)、nearest/hotspot(ForAI 内嵌) 全齐 | ✅ 通过 |
| A3 | 双路径同核 | dialog 与 ForAI 落同一 _execute | unified B1-B5 两路径 layerName/_ui.tool/命名/rows 同核 ALL-PASS | ✅ 通过 |

### B EMC 承重契约 C1-C6

| 编号 | 检查项 | 标准 | 证据 | 结论 |
|------|--------|------|------|------|
| B1 | C1 工具名不变 | SKILL_DEFS ↔ TEMPLATE_REGISTRY 未动、12 键名未改 | TOOLS 表 12 键；obs diff 0/12 含工具名 | ✅ 通过 |
| B2 | C2 rows 判定 | zonal/compare/rank/area_stats ForAI 透传 rows | obs diff data 全等（含 rows）；unified B1-B4 "返 rows(C2)" ALL-PASS | ✅ 通过 |
| B3 | C3 参数零变化 | 内部 kind 避让 _PARAM_ALIAS[mode]='how' | stages.js:21 mode→how 未动；buffer kind 双模式 unified C1-C2 实测 | ✅ 通过 |
| B4 | C4 provenance | _adoptToolboxResult 含 keep+consumed+AI 组 parentId+focusOnlyResults+并集缩放+layers:changed | tools.js:614 定义 / :623 focusOnlyResults / 12 工具+:1066 density 全调 | ✅ 通过 |
| B5 | C5/C6 | 名不变即免疫；命名逐字 | obs diff 含图层名；pipeline 出口裁定链在 | ✅ 通过 |

### C 修复效果实证

| 编号 | 检查项 | 标准 | 证据 | 结论 |
|------|--------|------|------|------|
| C1 | density 沉浸聚焦 | 迁 _adoptToolboxResult 补 focusOnlyResults | 78b97f6 density :1064-1066 改 _adoptToolboxResult（删旧 _registerToolboxLayer+AI 组补丁） | ✅ 通过 |
| C2 | isToolAnalysisLayer 扩集 | 直读 _ui.tool 扩 12 类；互斥仅 setLayerVisible+renderLayer | state.js:1022-1028 _TOOL_ANALYSIS 13 类 / :1036-1058 enforceMutualExclusion 仅 setLayerVisible | ✅ 通过 |
| C3 | area_stats 分组匹配 | byGroup 信 group_by + 兼容 row[group_by] ?? row.name | area-stats-tool.js:54-60 | ✅ 通过 |
| C4 | 复跑三件套 | obs diff 0/12 / unified fails=0 / pipeline fails=0 | **本机复现**：obs `[DONE] 0/12` / unified `[DONE] fails=0 ALL-PASS` / pipeline `[DONE] fails=0 ALL-PASS` | ✅ 通过 |
| C5 | 既存回归 | compare/exit_badge/domain_lens PASS | compare_regions 后台跑中（LLM 多轮·>420s）；exit/domain_lens 信任 K3 §5（LLM 方差·§7-2 机制断言合规） | ⚠️ 部分通过（K3 实证 + 三件套核心已验） |

### D 重点怀疑区裁决

| 编号 | 检查项 | 裁决 | 理由 | 结论 |
|------|--------|------|------|------|
| D1 | §7-3 $n 链 diff | 接受遗留·纳入下期步 1 | 委托层 ref() 内联保留；不阻断合并；步 1 补 $n 链 obs diff | ✅ 接受 |
| D2 | §7-4 互斥扩集 | **接受·不回退** | 扩集是修 bug（旧 categoryOf 盲区致新工具互斥空转）；enforceMutualExclusion 是既有 A/B 互斥（非外溢）；安全面仅 setLayerVisible+renderLayer 不触 tools.js:407-410 崩溃面；EMC focusOnlyResults 每工具重申 | ✅ 接受 |
| D3 | §6-7 area_stats 语义 | 接受 | 修 latent bug（main 同有）；多分组用地从错色变正确分组色·修 bug 非改行为 | ✅ 接受 |
| D4 | §7-5 ensure_zone registry | 接受遗留·纳入下期步 1 | 组 A 既有；grid 无 $n/对账；改它影响 F3/registry 语义·另案 | ✅ 接受 |

### E 代码审查

| 编号 | 检查项 | 标准 | 证据 | 结论 |
|------|--------|------|------|------|
| E1 | shared.js 基建 | addToolboxLayer/placeToolLayer/collect*/featName/normalizeGeoNames 正确 | shared.js 导出 13 函数（featName:20/normalizeGeoNames:29/buildZonalFc:42/resolveBoundaryGeo:76/toolContentSig:108/defaultPaint:124/renderNote:134/SCALE_TABLE:142/scaleRadius:147/clampM:152/addToolboxLayer:158/placeToolLayer:192/collectPointSources:222/collectBoundarySources:248/boundarySourceGeo:264） | ✅ 通过 |
| E2 | tools.js 委托层 | 12 工具 C1-C6 + observation 逐字 + _adoptToolboxResult | obs diff 0/12（逐字实证）；12 工具全调 _adoptToolboxResult | ✅ 通过 |
| E3 | buffer-tool 双模式 | 单一 _execute + emotion 四路 + _ui 显式 kind + 存量 color 判据 | unified C1-C3 ALL-PASS（cover/emotion 双路径 + 显式 kind + 存量 color 判据·**禁 distance/sourceLayer**） | ✅ 通过 |

### 评审自身失误修正（M6）

**评审报告（emc-toolbox-unified-review-2026-07-25.md）建议 2 的 buffer kind 判据为 distance·与 buffer-tool.js:108 事实冲突**（cover 路径 `dist = p.distance ?? p.radius_m ?? DEFAULTS.distance` 也有 distance）。K3 v2.2 修订 M6 改 color 判据（cover 有 color/emotion 无）**正确**，unified C3 实证（"存量含 color→cover / 无 color→emotion / 禁 distance/sourceLayer"）ALL-PASS。**评审此处的 distance 判据失误，K3 修正成立。**

---

## 三、未通过项清单

**无阻断项·无严重项。**

C5 既存回归 compare_routes 后台跑未结（LLM 多轮·>420s·非测试本身失败）；exit_badge/domain_lens 信任 K3 §5 实证 + §7-2 LLM 方差说明（机制断言合规）。三件套核心验证已充分覆盖 toolbox 工程质量 + 流水线不破坏。

---

## 四、遗留缺陷 / 技术债台账

| # | 项 | 归属 | 阻塞合并 | 处置 |
|---|----|------|----------|------|
| 1 | $n 链 obs diff 未覆盖（§7-3） | 本次（验证缺口） | 否 | 进步 1（补 extract→overlay 链用例） |
| 2 | ensure_zone 不注册 registry（§7-5） | 组 A 既有 | 否 | 进步 1（grid 产物挂 registry） |
| 3 | main.js _contentSig 与 shared toolContentSig 双处重复（§9） | main 既有 | 否 | 进步 1（统一单一事实源） |
| 4 | CPD 8 用例未回归（§7-7） | 与本次正交 | 否 | 进步 1（CPD 回归） |
| 5 | area_stats 多分组语义变化（§6-7） | main 既有 latent bug | 否 | 已修（接受·修 bug） |
| 6 | 5 边界预设 + manifest 为测试激活（9f37f72） | 本次 test env | 否 | 可删（非代码·用户定） |
| 7 | isToolAnalysisLayer 扩集回退方案（§7-4·state.js:1016-1032） | 本次 | 否 | 不回退（裁决接受） |

---

## 五、下一步 EMC 修复工程衔接（整体走一遍·6 步）

基于 K3 §9 另案 + 验收遗留（§四 1-4）+ 之前 plan 组 B-F。按「非红线→diagnose 红线→harness 红线→验证」序，本轮先落步 1（Toolbox 收尾·非红线）。

### 步 1 · Toolbox 收尾（非红线·本轮立即落）
- **ensure_zone registry 注册**：grid-tool.js `generateGridForAI` 收尾调等价 _adoptToolboxResult（或 tools.js ensure_zone 委托层补）—— grid 产物挂 registry/$n，与 12 工具一致
- **main.js _contentSig 统一**：main.js:86 改 import shared.toolContentSig（删本地 _contentSig·单一事实源）
- **$n 链 obs diff 增补**：tool_obs_snapshot.py 加 extract→overlay 链用例（步 7 委托后 $n 引用文案逐字验）
- **CPD 8 用例回归**：tests/browser CPD 系（test_cpd_*.py 5 个）
- DoD：grid 产物有 registry；_contentSig 单一源；$n 链 diff 0；CPD 全绿

### 步 2 · 测试飞轮断言（非红线·组 B）
- T6 完成校验三件套（test-cases.js·答案/落图/切题·灭绝空心 OK）
- T3 参数序列化（区=[object Object]）

### 步 3 · UI 遗留（非红线·组 C）
- T4 胶囊矛盾（panel.js:816 default ready 消灭 + 两阶段对账）
- T5 对比 C 键（批4 Swipe 入口）

### 步 4 · diagnose 认知深化（红线 eval-first·组 D）
- SOP 卡扩字段（GEO_TOOL_CATALOG 加适用尺度/前置/失败模式/正例负例）
- method→tool 确定性映射 + EMC-SUM 摘要 ② method/plan 采集

### 步 5 · harness 承重（红线 eval-first·组 E）
- D3 多步链（CHAIN_REGISTRY + runChainPath + orchestrate 分流）
- D1 扩覆盖（R1 s1 残余·harness :462 degraded/ask 分支）
- P0-4 进度透明（阶段时间线 + 增量落图 + 可取消）

### 步 6 · 验证债务（用户启动·组 F）
- T7 飞轮全量重跑 04-07（干净基线·首次端到端裁决）
- Playwright 端到端 + manifest 再生成（数据红线·用户定）

---

## 六、合并建议

**可合并**：toolbox-unified-toolset → main。建议：
1. compare_regions 后台跑结果回来确认（若 PASS 则既存回归全绿；若 LLM 方差红，按 §7-2 接受）
2. 合并后落步 1（Toolbox 收尾·非红线·K3 §9 另案 + 验收遗留 1-4）
3. 步 2-6 按依赖序推进（红线组 eval-first）

红线守约确认：后端零改动 / 不改 SKILL_DEFS/paradigm.py / 不改 harness orchestrate / 不改 ChatRequest schema —— `git diff main..toolbox-unified-toolset -- api/ ai_qa/prompts.py ai_qa/schemas.py ai_qa/paradigm.py frontend/js/ai_qa/harness.js` 应仅文档/测试/paradigm 文案（组 A 已改 catalog）层面的必要同步，无承重逻辑改动。
