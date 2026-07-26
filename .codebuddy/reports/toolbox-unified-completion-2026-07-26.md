# Toolbox 统一工具集层 — 完成报告（交 GLM 验收）

> 执行人：CodeBuddy（K3）｜ 2026-07-26 ｜ 分支：`toolbox-unified-toolset`（未 push，main 领先 0）
> 执行依据：`.codebuddy/plans/toolbox-unified-toolset-execution.md` v2.2（用户拍板 D1-D6 + 评审建议 1 接受）
> 改动面：12 commits · 32 files · +44946/−464（基线 JSON 占 ~42k 行·非代码；代码净增约 2.6k 行）
> 验收对象：本报告 §5 验证证据均可复跑；§6/§7 为自报偏差与建议重点怀疑区。

---

## 1. 一句话总述

EMC 内联在 `ai_qa/tools.js` 的 9 个 GIS 工具 + Buffer 情绪聚合已收敛为 `frontend/js/toolbox/` 下同层级独立模块（每模块 = 单一 `_execute` 核 + ForAI 程序化入口 + 可选 UI dialog），Toolbox 面板新增 4 个入口（Zonal/面积/Rank/矢量组），Buffer 原地合一双模式，tools.js 瘦身为 LLM 委托层——**两条触发路径（EMC 对话 / Toolbox 手动）调用同一批模块，图层产出一致；12 工具 observation 逐字零漂移**。

## 2. 交付总账（12 commits，分支时序）

| Commit | 内容 |
|--------|------|
| `85255e1` | docs：v2.2 修订响应表（接受建议 1 focusOnlyResults；修正评审修订 2 判据 distance→color·附 buffer-tool.js:121 实测） |
| `529a03b` | 步 1：`toolbox/shared.js` 基建（7 函数自 tools.js 逐字迁移 + addToolboxLayer/placeToolLayer）+ api.js geoPost + tools.js 抽取 re-export + addResultLayer 拆分 |
| `c21212a` | 步 2：Buffer 合一 `kind:'cover'\|'emotion'` 单一 _execute；emotion 中心四路（搜索/取点/要素/坐标）；generateBufferForAI；编辑回填显式 kind + 存量 color 判据 |
| `d521d9a` | 步 3：zonal（聚合/对比）+ area-stats 模块 + 三步向导 dialog |
| `f708977` | 步 4：rank + vector 五操作合一模块 + dialog |
| `547405b` | 步 5：nearest/hotspot 纯内嵌 ForAI |
| `6639ed0` | 步 6：Toolbox +4 入口接线（tool-row/pp-tab/sidebar 分派/main init/param-panel 白名单泛化/pp-tabs flex-wrap） |
| `5256ae7` | 步 7 前置：observation 快照基线设施（tool_obs_snapshot.py）+ 12 工具基线 JSON |
| `7f4c9af` | 步 7：tools.js 12 工具全部改薄委托 + `_adoptToolboxResult`（C4 全项·focusOnlyResults 保留）+ 删 geoFetch/5 合成器；**快照 diff 0/12** |
| `e95354a` | 步 8：统一验证（E2E/流水线/既存用例）+ architecture-pattern.md 新节 + todo.md 日志 |
| `9f37f72` | test env：5 边界预设激活（presets/ + manifest·非代码·可删） |
| `78b97f6` | bugfix：density 沉浸聚焦 + isToolAnalysisLayer 扩集 + MC 系/分组匹配三处数据修复 |

## 3. 架构成果

```
触发层   路径一 EMC: ai_qa/tools.js（薄委托：guard/参数归一/ref() $n/resolveBoundaryInput 预解析/
                    observation 逐字/_adoptToolboxResult 簿记）
         路径二 UI : index.html 7 tool-row → param-panel 7 pp-tab dialog（三步向导）
工具集层（同层级·模块间互不 import）
  frontend/js/         heatmap-tool.js · grid-tool.js · buffer-tool.js（原地·buffer 双模式）
  frontend/js/toolbox/ shared.js（唯一共享基建：geoPost 转发/defaultPaint/renderNote/尺度表/
                       buildZonalFc/resolveBoundaryGeo/toolContentSig/addToolboxLayer/
                       placeToolLayer/collectPointSources/collectBoundarySources/featName/normalizeGeoNames）
                       zonal-tool.js · area-stats-tool.js · rank-tool.js · vector-tool.js（五操作）
                       nearest-tool.js · hotspot-tool.js（纯内嵌无 UI）
后端     /api/v1/spatial/*（heatmap/grid/buffer-cover·零改动）· /api/v1/geo/*（其余·经 api.js geoPost）
```

依赖红线（已守）：`ai_qa/tools.js → toolbox/* + js/三工具` 单向；toolbox 严禁 import ai_qa/*；shared.js↔sidebar 为既有循环模式（函数级运行时调用·TDZ 安全·已验证无 console 报错）。

## 4. EMC 流水线承重契约（C1-C6）落账

| 契约 | 落法 | 证据 |
|------|------|------|
| C1 工具名不变 | TOOLS 12 键名一字未改，只换内部实现 | tools.js TOOLS 表；pipeline 用例过 |
| C2 rows 判定 | zonal/compare/rank/area_stats 的 ForAI 透传 rows，data.rows 非空 | obs diff 的 data 全等比对（含 rows） |
| C3 参数面零变化 | LLM schema 未动；内部字段用 `kind` 避让 `_PARAM_ALIAS[mode]='how'` | stages.js 未动；Buffer kind 双模式实测 |
| C4 provenance | `_adoptToolboxResult` = _registerToolboxLayer + keep + consumed 清理 + AI 组 parentId + **focusOnlyResults** + 并集缩放 + layers:changed 补发 | pipeline $n 链（extract→overlay）过 |
| C5 F3 gate | 工具名不变即免疫 | 同上 |
| C6 命名语义 | 现状命名逐字沿用（obs diff 内含图层名比对）；新 UI 路径同名同核 | diff + E2E 两路径命名比对全过 |

## 5. 验证证据矩阵（均可复跑）

| Gate | 命令 | 结果 |
|------|------|------|
| 静态 | `node --input-type=module --check` 全部改动文件 + IDE lint | 0 错 |
| **obs 快照 diff（演示链命门）** | `py tests/browser/tool_obs_snapshot.py --diff` | **0/12 不一致**（基线 `tests/reports/toolbox-obs-baseline.json`；observation 逐字 + data 剔 layerId 全等） |
| 统一 E2E | `py tests/browser/test_toolbox_unified.py` | **fails=0 ALL-PASS**：7 tool-row 开 pane；zonal 聚合/对比、area-stats、rank、vector overlay UI×ForAI 两路径同核（kind/_ui.tool/命名/rows）；nearest/hotspot 内嵌 ForAI；Buffer cover/emotion 双模式两路径 + 编辑回填（显式 kind）+ 存量无 kind color 判据回填；无 console 报错 |
| 流水线回归 | `py tests/browser/test_toolbox_pipeline.py` | **fails=0 ALL-PASS**：回答无 [ERR]；geo 200×2（zonal_stats 单技能快路径 + extract_feature→overlay ReAct 多步链实测）；出口裁定在 |
| 既存用例 | `test_compare_regions.py` / `test_exit_badge.py` / `test_domain_lens_threading.py` | 全 PASS（exit_badge 首跑因 LLM/超时方差失败，复跑过 + diag 实证 badge 渲染正常·非回归） |

## 6. 修出的 bug 清单（过程修 4 + 遗留修 3）

| # | Bug | 性质 | 修复 |
|---|-----|------|------|
| 1 | `placeToolLayer` 空 fc 时 `L.id` 崩（0 命中 filter/clip/overlay） | 本次新写代码缺陷·步 7 自查 | shared.js 空守卫（镜像 addResultLayer :474） |
| 2 | `e2e-seam.js loadRange` 用未定义 `safe` → ReferenceError | **既存 seam bug**（loadRange 从未被用例踩到） | safe 提升模块级 |
| 3 | zonal-tool 对比胶囊对 MC 系面域全显「要素 N」+ 聚合合成空名模糊命中首行 | 新 UI 路径缺陷 + main 既有 fuzzy 放大器 | featName/normalizeGeoNames（后上移 shared）+ buildZonalFc 空名禁 fuzzy |
| 4 | `DATA/boundaries/presets/manifest.json` 缺失 → load_preset 全不可用（既存 compare 用例本机必败根因） | 环境/数据 | 激活 5 预设 + manifest（test env commit） |
| 5 | density 委托产物无沉浸聚焦 | **组 A 遗留**（v2.2 另案） | density 迁移 _adoptToolboxResult（78b97f6） |
| 6 | isToolAnalysisLayer 只认 4 类 → 新工具互斥空转 + Overview 焦点盲区（zonal 结果不可追随） | 设计缺口（评审标注待议·用户拍板修） | 直读 _ui.tool + 扩 12 类（78b97f6） |
| 7 | **area_stats 分组 rows 不回显 group 字段**（组值在 row.name）→ byGroup 恒 false → 空名放大器成唯一匹配路径（多分组用地统计必错色） | **latent 数据 bug·main 同有** | byGroup 信 group_by + 组值兼容 row[group_by] ?? row.name（78b97f6） |

## 7. 自报偏差 / 限制 / 风险（请 GLM 重点验收）

1. **环境依赖**：全部运行时验证在本机（Windows + 本机 DATA）完成；`DATA/boundaries/presets/` 是我为测试激活的（commit `9f37f72` 已注明可删）。请在你们环境复跑 §5 三件套确认可移植性。
2. **LLM 方差**：pipeline 用例按「机制断言」（无 [ERR]/geo 200/出口裁定）而非固定端点——同问句 diagnose 可 ready 也可 gap-ask，均合规。既存 exit_badge 有同类方差（已实证非回归）。若你们要求固定端点断言，需要 mock LLM 或接受偶红。
3. **observation diff 基线覆盖面**：12 工具 × 1 组固定入参（成功路径为主）；未覆盖 [ERR] 文案路径（如无效 preset/空结果）与 $n 引用文案路径。委托层对 $n/命名引用经 ref() 内联保留，但未逐字验证——**建议验收补一组 $n 链 diff**。
4. **isToolAnalysisLayer 扩集的行为外溢**（78b97f6）：手动开新工具层现在会关情绪点层与其他分析层（§3.3③ 本意）；EMC 结果也会被手动开层关（focusOnlyResults 在下一 EMC 工具重申）。若评审认为「EMC 结果应对手动互斥免疫」，需回退此项——请重点裁决。
5. **ensure_zone 不注册 registry**（组 A 既有·本次未动）：grid 产物无 $n/对账条目，与 density/12 工具不一致——记录在案未修（改它影响 F3/registry 语义，建议另案）。
6. **area_stats 修复改变产物语义**（78b97f6-#7）：多分组用地的面积着色从「全特征首行色」变为正确分组色——这是修 bug 不是改行为，但若有演示截图依赖旧（错）色，需知悉。
7. **既有用例未全量回归**：tests/browser 11 个用例跑了 3 个最相关的（compare/exit_badge/domain_lens）+ 新增 2 个；CPD 系 8 个未跑（与本次改动面正交·harness/panel 未动）。
8. **未做**：归因占位按钮（手册明确不做）；`MOD_LOADER` 等 9 个 ⬜ 模块埋点（AGENTS.md 标注低优先勿擅自加）；`main.js _contentSig` 与 shared toolContentSig 双处重复（手册登记不动 main.js）。

## 8. GLM 验收建议（按序）

1. 读执行手册 v2.2 + 本报告 §3/§4，对照抽核：tools.js 任一委托工具的 observation 与 git main 版逐字 diff（抽查 ≥3 工具）。
2. 复跑 §5 三件套（obs diff / unified / pipeline）——预期 0/12 + 2×ALL-PASS；任一红即阻断。
3. 重点怀疑区：§7-3（$n 链）、§7-4（互斥外溢）、§6-7（area_stats 语义变化）——按你们的判断决定是否接受。
4. 代码审查重点：`frontend/js/toolbox/shared.js`（基建正确性）、`tools.js` 委托层（C1-C6）、`buffer-tool.js`（双模式单一核）。
5. 真实数据用户验收：跑一遍演示链（EMC 问「西陵区情绪最差社区」→ 深读归因；Toolbox 手动 zonal/Buffer emotion），确认效果满足预期后合并 main + push。

## 9. 遗留另案（不阻塞·登记）

- ensure_zone registry 注册缺口（§7-5）；main.js `_contentSig` 双处重复；CPD 8 用例未回归；$n 链 obs diff 增补（§7-3）；isToolAnalysisLayer 扩集若被否决的回退方案（state.js:1016-1032 单点回退即可）。
