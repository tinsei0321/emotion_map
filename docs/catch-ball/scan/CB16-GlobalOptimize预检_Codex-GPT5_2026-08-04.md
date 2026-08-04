# CB-16 全局优化 + 发版快照 + 时间轴重规划 实施预检（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）
> **时间**：2026-08-04 | **分支**：`fix/emc-buglog` @ `dc88f35`（③w2·先讨论再实施）
> **范围**：只读评估 · 不改代码 · 不 commit
> **验证手段**：代码/数据逐项核验 + 内联断言（沙箱无 pytest/无 serve，未装依赖保只读；B3 快照与 link_checkup 为 claude组 运行项）

---

## 结论先行

**草案可行 · 无 P0。** 4 子项方向均正确，但需修正 3 项事实（P1）+ 3 项建议（P1/P2）：

- **【P1】L4 标 ✅ 属过度声称**：CLAUDE.md 原行「L4 框架已预留待实现」+ 出口卡 limitation「归因=规则查表（DEMO·L4 深度归因待接入）」与草案「L4 ✅」自相矛盾。L3 ✅ 属实（`SCRIPT/multimodal_analysis.py` v1.0 在仓·Vision/OCR/Audio 可插拔）；L4 建议标 **🔄（部分）**——4×5 归因规则查表 + ermawu L3L4 ABSA 数据在·全量深度归因待扩（守「预留当已实现→偏高 8 折」标尺）。
- **【P1】记忆 GC 标注不准确**：`global-time-axis`/`batch4-swipe-compare` **均已实现**（`frontend/js/` 下 time-bar.js/time-source.js/timeline.js 三件套 + map.js `_mapB/_enterCompare` 在仓）——标「设计稿·待落地」会误导后续会话低估现状。应标「已实现·manifest 404 待修复（③w2）」/「已实现·3D compare polish 待办」。
- **【P1】CPD-L03 文件路径失效**：全仓无 `test-cases.js`，'changyi' 已零引用（根因确已修）；实际用例在 `tests/emc_test_cases.md`（board 驱动·CPD-L03 见于 tests/reports）。硬断言落点须先定位实际执行处（test-board / test_cpd_predicates.py）。
- **【P1】validate 同步须含全字段**：内联实测漂移 = 7 工具 `when` DIFF + `extract_feature`（params/contributes）+ `merge`（params/yields/contributes）——只同步 when 仍会红。
- **【P1 建议】时间轴候选 1 直接做优先于候选 2**（见下）·写 manifest 描述符**不属数据红线**（DATA/raw 才是；DATA/performance 已入库·.gitignore:11 注明）。

---

## 一、逐子项核验

### 1. 全局优化 —— 对路（P1 修正×2）

- **CLAUDE.md 状态行**：L3 ✅（multimodal_analysis v1.0）/ 空间分析 ✅（`core/spatial_analysis.py` + `buffer_analysis.py`·MOD_SPATIAL ✅）/ UI 优化 ✅（design tokens + frontend）均属实；**L4 建议 🔄**（见结论）；L0→L1 补「L0 走购买·sim 当下充分」✓（对齐 KNOWLEDGE 红线）。
- **todo 归档**：5 日段确认在 todo.md（07-28 :349 / 07-29 :307 / 08-01 :212 / 08-02×2 :180/:124）；`todo-archive/` 已归档至 07-26，缺 07-27_08-02 ✓；重复节确认（`### ⏸️ CB-15 数据认知` 连排两行）✓。
- **emc-fix-progress**：:4/:27（2026-08-01·CB-10·220 passed）vs :29（v3.5·32 passed）自相矛盾确认；更新至 CB-16/276 正确。
- **Streamlit 死段**：spec 13 处 / arch 18 处（草案 12+18 接近）；两文件 header 均已声明退役——清理属文档卫生 P2，须保留退役声明 + `MOD_APP` 模块表引用（AGENTS.md 仍引用 retired）。
- **decisions.md**：全仓无 ADR-017+（停于 ADR-016）确认；补 3 条 ADR（Streamlit 退役 / v2/v3 FC 转型 / 出口抽象层）比冻结声明更有审计价值（信息已在 revision-log·建议轻量 3 条）。
- **记忆 GC**：`push-not-redline`（07-04·commit 通过即推）vs `commit-only-user-pushes`（后·覆盖前·用户手动推）冲突确认——且 CLAUDE.md「Git 规范：每天下班前提交并推送」三方不一致，**需用户拍板**（草案已标注 ✓）；`extrusion-height-maxheight.md` 在 MEMORY.md:28/29 重复索引确认 → 合并 ✓；**global-time-axis/batch4 标注修正**（见结论）。

### 2. 发版快照 —— 对路

- 用户定「先快照非冲达标」→ B3 快照 = 基线测量·不修 PRM 才能量化后续修复收益，**正确**。
- B3 定义 25 例（flywheel_audit docstring）·草案「23/26·88.5%」以**本次实际快照为准**（本次跑的就是基线）；`EMOTION_TRACE_SESSION=B3-<批>` 带批号 ✓（RULES trace 取证）；link_checkup 20 例（10 类×≥2·需 DEEPSEEK_API_KEY + serve）✓；pytest 276 全量回归 ✓。
- 不建议连带修 PRM——污染基线；快照后单独一轮量化修复收益。

### 3. 时间轴重规划 —— 候选 1 治本·候选 2 临时

- **根因确认**：`_time_manifest.json` 仅在 `DATA/old_data_processed/`；代码指 `/DATA/performance/_time_manifest.json` → 404。且 manifest 内 3 条 sourceTemplate 已失联（xiling_wujia_L1/L2 → 数据在 old_data_processed；ermawu_l3l4 → 数据在 performance·指向 processed）。
- **候选 1 对路**：geo_registry `_POINT_LAYERS`（9 层：yichang L1/L2 + ermawu L3L4）单一权威 + 扫 performance 现场组装——**天然剔除 xiling_wujia 旧数据**（registry 已不含）。需处理三细节：
  ① **模板中缀差异**：L2 文件 `yichang_L2_T1_L2_result_geojson.geojson`（有 `_L2_`）vs L1 `yichang_L1_T1_result_geojson.geojson`（无）——不能单 pattern 通用，须按前缀分别拼；
  ② **L1 双扩展名特判**：杂散文件 `yichang_L1_T1_result_csv.csv.geojson` 存在——扫描只收 `*_result_geojson.geojson` 排除之（草案特判即此·需测试覆盖）；
  ③ **兼容 `_templateRegex`**：派生 sourceTemplate 须唯一 `{slice}`（time-source.js:31-39）；file-first + API fallback 顺序合理（保留未来购买数据自带 manifest 的扩展位）·文档注明双源优先级。
- **候选 2**：写描述符到 DATA/performance——`DATA/raw` 不可改是硬红线；`DATA/performance` 是已入库的演示产物目录，**写 manifest 非改原始数据·不属数据红线**（time-source.js:22 注释说法过严）。但手写清单正是本次根因（漂移源）→ 仅作临时解封·建议由 sim_performance_data 同源产出或直接候选 1（1 端点 + fallback ~2 文件·零写盘）。

### 4. backlog 收尾 —— 3 项均本次应做（优先级见下）

- validate_skill_params：内联实测漂移清单确认（7 工具 when + extract_feature/merge 全字段）·contracts=单一真相源·改 paradigm 镜像 + 前端 SKILL_DEFS 一并核 ✓。
- renewal 卡 perceptible_metrics domain 门控：`_build_card:230` 无条件调用确认·改动小 ✓。
- CPD-L03 硬断言：根因已修（changyi 零引用）·防回归合理；**文件路径修正**（见结论）。

---

## 二、7 问速答

1. **范围合理**：无重大遗漏/过度；记忆 GC 三处标注需修正（L4 / global-time-axis / batch4）·push 冲突裁决需用户拍板（草案已标）。
2. **先快照对**：不修 PRM 才能量化修复收益·基线以实际快照为准；建议快照最后跑（B3 上限 120min·反映文档/修复后现状）。
3. **候选 1 对路**：治本且零数据写盘·L1/L2 中缀差异 + 杂散双扩展名文件需特判；候选 2 不属数据红线但仅临时·建议直接候选 1。
4. **backlog 3 项均应做**：validate drift（P1·CI 长红）> renewal 门控（P1）> CPD-L03 断言（P2）；MOD_PLACE/F_002 不进本次 ✓。
5. **测试基本够**：时间轴补派生 manifest 与文件扫描一致性 / L1-L2 模板逐文件命中 / 杂散文件排除 / file-first 分支 / loadSlice 端到端；validate 补全字段核对 + SKILL_DEFS。
6. **承重零触碰**：时间轴只新增端点 + time-source fallback·不碰 diagnose/harness/ChatRequest·geo 问答既有端点不动；paradigm 同步属 prompt 镜像（FC 工具描述·以 contracts 为准·改后须关键用例验证）·不碰 diagnose prompt 本体。
7. **4 子项均要**：优先级 3（时间轴治本·P1）> 1（文档/记忆一致性·P1）> 2（快照·用户定）> 4（validate P1·renewal P1·CPD-L03 P2）；建议文档+时间轴+backlog 先落地·快照最后跑。

---

## 三、优先级

| 级别 | 项 |
|---:|---|
| **P1 修正** | CLAUDE.md L4 标 🔄 非 ✅（同步改出口卡 limitation 或留注释）· 记忆 GC 中 global-time-axis/batch4 标「已实现+待修/待 polish」 · CPD-L03 断言落点定位（非 test-cases.js） |
| **P1 建议** | validate 同步含 extract_feature/merge 全字段（params/yields/contributes）· 时间轴候选 1 直接做（含 L1/L2 模板特判 + 杂散文件排除测试） |
| **P2** | Streamlit 死段清理保留退役声明与 MOD_APP 引用 · ADR-017~019 轻量补录 · todo-archive 归档 · 快照产物（trace 会话 + JSON）存档 |

---

## 四、判定

- **草案可行 · 无 P0**。方向正确（文档一致性 / 快照基线 / 同源 manifest / backlog 收尾），落地路径清晰。
- **P1 修正 ×3 + P1 建议 ×2 + P2 ×3**（如上）。
- **独立判断**：基于代码/数据逐项核验 + 内联断言（validate 漂移清单 / manifest 内容 / DATA 文件命名 / todo 日段 / 记忆文件），未参考 glm组 本轮报告。

---

## 附录：核验证据

| 依据 | 结论 |
|---|---|
| `DATA/old_data_processed/_time_manifest.json` | 4 数据集·3 条 sourceTemplate 失联（xiling_wujia×2→old dir·ermawu→processed 非 performance）·yichang_L2 已指向 performance |
| `DATA/performance/` 实际文件 | L1 无 `_L2_` 中缀 / L2 有 · 杂散 `yichang_L1_T1_result_csv.csv.geojson` · ermawu_l3l4×3 在 |
| `frontend/js/time-source.js:22` | MANIFEST_URL 指 performance·无 fallback（fetch 失败 → manifest null） |
| 内联 validate 对比 | 7 工具 when DIFF + extract_feature/merge params/yields/contributes DIFF |
| `todo-archive/` + todo.md | 归档至 07-26·缺 07-27_08-02；5 日段在 todo.md · ⏸️ CB-15 重复节确认 |
| 记忆目录 | push 双记忆冲突确认 · MEMORY.md:28/29 extrusion 重复索引 · time-bar/timeline/time-source 三件套 + mapB 在仓（global-time-axis/batch4 已实现） |
| `SCRIPT/multimodal_analysis.py` | L3 多模态引擎 v1.0（Vision/OCR/Audio·可插拔·API 依赖）在仓 |
| `core/field_dictionary.py` | 4×5 归因领域/要素 self_produced 字段在（L4 规则层）·深度归因待扩（出口卡 limitation 同述） |

*登记：docs/catch-ball/scan/（RULES 4.1 命名）。本报告只读评估·未改代码·未 commit。*
