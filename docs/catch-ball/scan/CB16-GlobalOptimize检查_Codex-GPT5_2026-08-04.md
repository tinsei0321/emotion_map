# CB-16 全局优化 + backlog 收尾 实施后检查（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）
> **时间**：2026-08-04 | **分支**：`fix/emc-buglog` @ `833fbf9`（③w3·先验后推未推）
> **范围**：只读评估 · 不改代码 · 不 commit
> **验证手段**：代码逐行核验 + 内联测试直跑（validate 4 项全过）+ 历史 B3 审计横向对比（16 份 audit-B3 JSON）

---

## 结论先行

**实施通过 · 可推 · 无 P0/P1 需修项。** 三项实施（validate 同步 / renewal 门控 / 全局优化）均正确落地。**RST-L06 根因判定：claude组 的「paradigm density.when 文本变化」假设在架构上不成立**——实时 FC 路径不消费 paradigm 目录；回归更可能是 FC 输出方差（历史 16 次 B3 中同用例多次 PASS/FAIL 翻转·本次 22/26 在方差区间内）。建议：**保留 paradigm 同步**·补 2 项 P1 验证（eval 回归 + RST-L06 复跑）。

---

## 一、核验结果

### ① validate_skill_params drift 修复 —— 正确

- `_sync_geo_catalog_guard_fields()`（paradigm.py:324-344）：导入时用 `derive_geo_catalog()` 对齐 when/params/yields/contributes 4 字段·scale/preconditions/failure_modes/examples 保留手写 ✓（内联实测 4 字段全等·手写字段保留）。
- **幂等**：模块级 import 每进程一次·值覆盖非累加（reload 同结果）✓；contracts 不可用时静默 fallback ✓。
- **红线**：不碰 diagnose prompt 结构本体（FC sys prompt 构造函数未动）；但同步**改变了 `build_diagnose_prompt` 附录文本**（prompts.py:120/256 消费 geo_tool_catalog_text·Flash eval / fallback 路径可见）→ 需 eval 回归确认命中率不退化（P1）。
- **实测**：内联直跑 validate_skill_params 全部 4 个 test 函数 PASS（geo_catalog / template_registry / skill_defs_mirror / panel_source）·「4 passed（原 1 failed）」属实 ✓。

### ② renewal 卡 domain 门控 —— 正确

- `_build_card`（build_outlet_schema.py:267-269）：`(contract.get('domain') or '') == 'urban_governance'` 才挂 perceptible_metrics ✓——仅 checkup_satisfaction/checkup_dimension 两体检契约命中·renewal/其他域卡不挂·无遗漏（可感知指标只应挂体检卡）✓。
- 测试 `test_wave3_renewal_no_perceptible_gate` 断言 `'perceptible_metrics' not in card` ✓；前端 renderOutletCard 对缺失 key 安全（`card.perceptible_metrics || []`）✓。

### ③ 全局优化 —— 正确

- CLAUDE.md：L3 ✅（multimodal_analysis v1.0 + sim_ermawu_l3l4）·**L4 🔄**（规则底已实现·深度归因待扩——采纳预检 P1 修正）·空间分析 ✅ · UI ✅ · L0→L1 补「L0 走购买·sim 充分」✓。
- todo 归档：`2026-07-27_2026-08-02.md` 含 5 日段（07-28/29·08-01·08-02×2）✓；todo.md 现仅 08-04/08-03 两段·重复「⏸️ CB-15」节已删（现仅 :55 一处）✓。
- decisions.md：ADR-017~019 内容与实现/历史一致（Streamlit 退役 / v2/v3 FC 转型 / 出口抽象层）+ 索引同步 ✓。
- 记忆 GC：extrusion 重复索引已合并（MEMORY.md 单条）✓；push 冲突裁决 = 删 `commit-only-user-pushes` 保留 `push-not-redline`（与 ③z3b「已推」一致·但建议确认用户拍板记录·P2）；global-time-axis/batch4 未误标「设计稿·待落地」（保留架构描述——两者已实现·预检修正被正确采纳）✓。

---

## 二、B3 快照回归分析（RST-L06）

### 根因判定：paradigm 同步假设不成立 · 方差为主

**架构证据（LLM 可见性）**：
1. 实时 FC 阶段（router.py:60-66 fc_diagnose）只用 `build_fc_sys_prompt`（router.py:25-58·**无 GIS 目录附录**）+ `contracts_to_tools_schema()`（tool_contracts.py:433·when 来自 contracts·本次未改）。
2. `geo_tool_catalog_text()` 仅被 `prompts.py:120/256`（build_diagnose_prompt）消费——**实时 FC 路径不消费 paradigm**。
3. 因此 paradigm 同步对本轮 B3 的 LLM 可见文本 = 零变化。

**确定性链逻辑未被关闭**：运行时 `ai_qa_template_stats_v1={"hits":1,"misses":0}`（样本<10·冷启动恒放行）→ `_tplHitRateReady()`=true；`_hasSeq` 正则对问句「先裁剪西陵区情绪点，再生成热力图」必匹配；`clip_density` 触发器（stages.js:79）必命中——链前置应触发。链逻辑代码在 833fbf9 未改动。

**方差证据（16 份历史审计横比）**：

| 运行 | RST-L06 | PRM-03 | PRM-04 | PRM-07 | pass/total |
|---|---|---|---|---|---|
| 08-03 09:01（基线 23/26） | **PASS**（clip+density·1→2层） | PASS（ask_user） | PASS | PASS | 23/26 |
| 08-03 13:13 | **PASS** | PASS | PASS | FAIL（龙泉≠小溪塔） | 23/26 |
| 08-03 15:28 | **PASS** | PASS | PASS | FAIL（法定功能区） | 25/26 |
| 08-04 21:09（本次） | **FAIL**（tpl=clip·tools 空·1→0层） | FAIL（radius[ERR]） | FAIL（radius[ERR]） | FAIL（法定功能区） | 22/26 |

- 同一代码路径 RST-L06 08-03 连续 3 次 PASS·本次单次 FAIL；PRM-03/04 08-03 三次全 PASS（正确 ask_user）·本次 FAIL——**同用例跨运行 PASS/FAIL 翻转**是 LLM 方差特征（B3 历史 spread 13/25→25/26）。
- 本次报告「计划命中=13/23≈56%」→ FC 输出整体方差偏高（gate 冷启动未拦截）。
- **结论**：RST-L06 FAIL = FC 诊断输出未产出可执行链/多工具（degraded 或仅单 clip 无 boundary）→ 落单工具/ReAct 无产出；与 paradigm 文本无因果。PRM-03/04/07 = 已知瓶颈（buffer 参数填充 F3.1 / 法定功能区 CB-14）的方差回归·非本次引入（请求判断方向正确·补 nuance：08-03 基线这三项恰好全 PASS）。

### 修法建议

- **保留 paradigm 同步**（正确方向·消除手写镜像漂移类）·**不退回手写**（手写即漂移源）。
- **P1**：补 eval 回归——同步改变了 build_diagnose_prompt 附录文本（Flash eval / fallback 消费）·跑 eval_template_flash 命中率确认 80% gate 不退化（这是同步的真正残余风险）。
- **P1**：RST-L06 复跑（单跑 ×3 或整 B3）确认方差；若复发→抓 FC 响应定位（degraded/general 误标/缺 boundary）。
- **P2**：audit 每例保留 fetch 证据——本次 `chat_phases={}`·/chat 请求体零捕获（只 1 条 /geo），无法看 RST-L06 实际 tool_calls；`_testFetchLog` 应每例留存。

---

## 三、6 问速答

1. **同步思路对路**：导入时派生对齐·幂等·不叠 patch；不碰 diagnose 结构红线·但改附录文本 → 补 eval 回归（P1）。
2. **RST-L06 根因**：paradigm 假设不成立（FC 路径不消费 paradigm·架构证据）→ 方差为主·复跑实证；同步应保留。
3. **renewal 门控正确**：仅体检域挂·无遗漏·测试与前端兼容均 ✓。
4. **全局优化准确**：ADR 内容/归档/重复节/记忆 GC 均核验通过；push 裁决建议留用户确认记录（P2）。
5. **PRM-03/04/07**：历史审计确认多次 PASS/FAIL 翻转·已知瓶颈方差·非本次引入 ✓。
6. **承重零触碰**：commit 仅 paradigm/outlet_build/tests/docs/CLAUDE·diagnose/harness/ChatRequest 未动；paradigm 同步影响 eval 附录文本（P1 验证）·FC sys prompt 与工具 schema 未动。

---

## 四、优先级

| 级别 | 项 |
|---:|---|
| **P1 验证** | eval_template_flash 命中率回归（同步改附录文本）· RST-L06 复跑 ×3 确认方差 |
| **P2** | audit 每例保留 /chat fetch 证据（tool_calls 可回溯）· push 裁决用户确认记录 · （可选）`_hasSeq` 链前置硬化（不依赖 FC 非 degraded） |

---

## 五、判定 + 修正声明

- **判定：实施通过 · 可推**。validate 4 项实测全过·门控/文档/归档正确·B3 快照 84.6% 在历史方差区间内。
- **修正声明**：③w2 预检时我说「CPD-L03 文件路径失效（无 test-cases.js）」——**不准确**：`frontend/js/test-cases.js` 存在且 CSV 已改名 yichang（:17 注释 CB-13 实锤）·CPD-L03 硬断言落点应在该处。特此更正。
- **独立判断**：基于代码核验 + 内联测试 + 16 份历史 audit 横比，未参考 glm组 本轮报告。

---

## 附录：关键证据

| 依据 | 结论 |
|---|---|
| router.py:60-66 fc_diagnose | 只用 build_fc_sys_prompt + contracts_to_tools_schema·无 paradigm 目录 |
| prompts.py:120/256 | geo_tool_catalog_text 仅进 build_diagnose_prompt（eval/fallback 路径） |
| audit-B3-210952 localStorage | `ai_qa_template_stats_v1={"hits":1,"misses":0}`·冷启动 gate 恒放行 |
| stages.js:79 CHAIN_REGISTRY | clip_density 触发器对「先裁剪…再热力图」必匹配 |
| 16 份 audit-B3 横比 | RST-L06 08-03×3 PASS / 本次 FAIL·PRM-03/04 同型翻转·spread 13→25 |
| validate_skill_params 内联 | 4 个 test 函数全 PASS（原 1 failed 已消） |
| frontend/js/test-cases.js:17 | CSV=yichang（xiling_wujia 改名·CB-13 实锤）·CPD-L03 断言落点 |

*登记：docs/catch-ball/scan/（RULES 4.1 命名）。本报告只读评估·未改代码·未 commit。*
