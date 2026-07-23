# EMC 运行时测试用例清单（C6 盲区 catalog）

> eval（`tests/eval_template_flash.py`）只测 Flash 模板路由（空 context），**运行时行为测不出**。
> 本文件登记这些 C6 盲区用例，每例：描述 / 前置 / 步骤 / 断言 / 状态。
> 可自动化的落 `tests/browser/`（Playwright），其余为手工用例。主 plan：Phase 5 筑基。

状态：✅ 已实现并跑通 ｜ 🔄 进行中 ｜ ⬜ 待实现 ｜ 🤚 手工（难自动化）

---

## 用例 1 · compare 中文地名↔preset_id 错配 ✅

- **描述**：欢迎胶囊"对比西陵区和伍家岗区的情绪与归因" → compare_regions 调 2× zonal_stats。
  修复前 LLM 把中文名"西陵区"当 preset_id 传 → 后端 `load_preset` 按 id 查无 → 400 → "仅 0/2 区"。
  修复 = `frontend/js/ai_qa/boundary-resolve.js` 把中文名解析成 `admin_district` 内 feature 的 GeoJSON dict。
- **前置**：`.env` DEEPSEEK key；`data/boundaries/presets/行政区.geojson` 在位。
- **步骤**：开 EMC → 填 `#chat-input` + 点 `#chat-send`（问句含"对比"→ select_template 路由 compare）。
- **断言**：硬=2× `POST /geo/zonal_stats` 均 200 + `rows[0].name` 含两区；软=回答文本含两区。
- **脚本**：`tests/browser/test_compare_regions.py`。
- **关联**：memory `emc-compare-skill` / `verify-real-endpoint`；plan `5-127-...shiny-tome.md` Phase 5。

---

## 用例 2 · domain_lens 等结构字段被前端压扁 ✅

- **描述**：diagnose 卡的结构字段（`domain_lens` 等）被前端压扁进 `ctx.context` 字符串丢结构，
  下游结构化用（compare/threading）须显式回传 ChatRequest（④5.108 范式），别正则抠。
- **前置**：`.env` DEEPSEEK key；注入点层；问一句触发多领域 domain_lens 的问句（如"对比规划与治理两板块的情绪"）。
- **步骤**：开 EMC → 注入点层 → 发多领域问句 → 捕 **POST `/chat` 请求体**（diagnose 产 domain_lens 后，后续 agent_step/answer 步前端须结构化回传 `domain_lens` 数组——router.py:35/46/54 `req.domain_lens`）。
- **断言**：硬=≥1 个 POST `/chat` 捕到（chat 管线跑通）；软=domain_lens 结构化回传（实测 `['urban_planning','urban_renewal']` phase=agent_step ✓；threading 代码层已核实 [api.js:31](frontend/js/ai_qa/api.js#L31) + [harness.js:384](frontend/js/ai_qa/harness.js#L384) 过滤 general——runtime 观测依赖 LLM 产非-general 多领域诊断，软断言兜底）。
- **脚本**：`tests/browser/test_domain_lens_threading.py`（emc_helpers 加 `/chat` 请求体捕获）。
- **关联**：memory `emc-domain-lens-threading`。

---

## 用例 3 · `_driftRe` 无围栏裸 JSON 边缘 ✅

- **描述**：harness.js `_driftRe` 拦「任意 ``` 围栏」→ revise；边缘 case = 草稿含裸 JSON 内联（无围栏）
  或围栏内非 action-JSON，确认不静默 strip、走 revise-失败→固定卡 通道。
- **前置**：`.env` DEEPSEEK key；构造会触发 LLM 产围栏/裸 JSON 的问句（如强求"给我 JSON 格式"）。
- **步骤**：开 EMC → 发问 → `wait_answer_done` → 读 `.aiq-answer` 文本。
- **断言**：硬=回答无裸 ``` 围栏泄漏；软=有合理兜底叙述。
- **风险**：LLM 是否产围栏非确定 → 若 flaky 降级 🤚 手工（不强求硬绿，软断言 [WARN] 兜底）。
- **脚本**：`tests/browser/test_drift_fence.py`（若可稳定触发则 ✅，否则 🤚）。
- **关联**：memory `emc-compare-skill`（_driftRe 拓宽段）。

---

## 用例 4 · 路由与空 context eval 分歧 🤚

- **描述**：`eval_template_flash` 用 `build_diagnose_prompt('')` 空 context 选模板；
  有 grounding 层时运行时路由可能与空 context eval 分歧（C6：居住用地里→zonal 非 overlay）。
- **前置**：先加载某 grounding 层（如居住用地 preset）→ 再问会落在分歧路由的问句。
- **步骤**：browser 先上载/选层 → 发问 → 对比 eval（空 context）与运行时（有层）的路由。
- **断言**：人工判运行时路由是否更贴合 grounding（eval 测不出，靠 browser）。
- **关联**：memory `emc-eval-empty-context-vs-runtime`。

---

> 加例守则：先在此 catalog 登记（状态⬜）→ 实现 `tests/browser/` 脚本 → 跑通标 ✅。
> 断言一律硬挂网络层/数据层/DOM（测真业务端点 + 真实 DOM 状态），软挂回答散文。
> **组合场景回归**（GUIDANCE §4.4）：每 Phase 新增 Playwright 用例须含 ≥1 组合场景（多事件/多状态/事件×状态×去重咬合），防 CB 三轮"修订引入新缺陷"模式重演。
> 状态分级：✅ 跑通 ｜ 🔄 进行中 ｜ ⬜ 待实现（标所属 Phase）｜ 🤚 手工（难自动化）。

---

## 用例 5 · CPD 默认折叠欢迎卡（地基行为）✅

- **描述**：F5 默认折叠胶囊（不记忆上轮展开态，用户定 2026-07-22）+ 空态欢迎卡开场。守 CPD 地基"默认折叠 + 欢迎卡"契约。
- **前置**：无需 LLM（纯 load）；清 localStorage 确保无展开态残留。
- **步骤**：开 EMC → 不发问 → 读 `#emc-panel` class + `.emc-welcome` + 输入框 placeholder。
- **断言**：硬=`#emc-panel.is-collapsed` 存在 + `.emc-welcome` 可见 + placeholder=折叠态文案。
- **脚本**：`tests/browser/test_cpd_collapsed_welcome.py`（**最稳，无 LLM，先跑验管线**）。
- **关联**：plan v1.0 §八 P0 地基行为；memory `cpd-soft-collapse`。

---

## 用例 6 · exit-badge 出口徽章渲染（地基行为）✅

- **描述**：回答完毕时 `_renderFooter` 创建 `.aiq-exit-badge`（[panel.js:378](frontend/js/ai_qa/panel.js#L378)），txt/cls 按 exit 编码——result→`分析完成`/`已生成 N 个图层`(cls=ok)；general→`纯问答`(cls=neutral)；gap/drift/ask/partial→`warn`（[:360-368](frontend/js/ai_qa/panel.js#L360)）。
- **前置**：`.env` DEEPSEEK key；`compare_points.geojson`（result 分支需点层）。
- **步骤**：开 EMC → 注入点层 → 发 result 型问句（`对比西陵区和伍家岗区的情绪与归因`）→ `wait_answer_done` → 读末条 `.aiq-exit-badge`；再发 general 型（`什么是4×5矩阵`）→ 读 badge。
- **断言**：硬=分析轮 `.aiq-exit-badge` 渲染 + cls∈{ok,warn}（exit 取决 LLM+数据非确定——compare 实测落 gap/warn）；软=general 问句路由 general→badge `纯问答`/neutral（H1 DOM 级前置，LLM 路由非确定，观测到=bonus）。
- **脚本**：`tests/browser/test_exit_badge.py`。
- **关联**：plan v1.0 §4.1 S4 信号 `.aiq-exit-badge`；general 分支 = H1 教训 DOM 级前置（为用例 11 铺路）；memory `emc-tri-state-exit-contract`。

---

## 用例 7 · 内容驱动高度自适应（地基行为）✅

- **描述**：展开态 EMC 高度 `--emc-h` 随内容驱动（`_fitEmcToContent` [panel.js:1471](frontend/js/ai_qa/panel.js#L1471)）；折叠态 `.is-collapsed` 局部覆盖 `--emc-h` 固定（[:144](frontend/js/ai_qa/panel.js#L144)）。
- **前置**：无需 LLM（注入点层触发 `layers:changed` → 高度重算）；或发长 prompt。
- **步骤**：开 EMC（折叠态）→ focus `#chat-input` 触发展开 → 读 `--emc-h` 基线 → 注入点层/发长内容 → 读 `--emc-h` → 折叠 → 读 `--emc-h`。
- **断言**：硬=展开态注入后 `--emc-h` > 基线（内容拉长）；硬=折叠态 `--emc-h` 固定（不随内容变）。
- **脚本**：`tests/browser/test_emc_height_adapt.py`。
- **关联**：plan v1.0 §八 P0 地基行为（拉长+缩回）。

---

## 用例 8 · 历史垃圾桶全清（地基行为）✅

- **描述**：`#emc-history-clear`（[panel.js:1601](frontend/js/ai_qa/panel.js#L1601)）→ `clearAllHistory()`（[:245](frontend/js/ai_qa/panel.js#L245)）清空 `_archive`，`#emc-history-list`（[:1295](frontend/js/ai_qa/panel.js#L1295)）的 `.emc-history-item` 归零（confirm dialog 二次确认）。
- **前置**：`_archive` 需有项——`page.add_init_script` 预置 localStorage `ai_qa_archive_v1` 假会话（确定性，免 LLM 归档）。
- **步骤**：预置 archive → 开 EMC → 开历史记录面板 → 读 `.emc-history-item` 计数 → 点 `#emc-history-clear` → `page.on('dialog')` accept → 重读计数。
- **断言**：硬=清后 `.emc-history-item` 计数 = 0（或仅剩当前会话项）。
- **脚本**：`tests/browser/test_history_clear.py`。
- **关联**：plan v1.0 §八 P0 地基行为（历史垃圾桶加大+全清）；用户定 2026-07-22。

---

## 用例 9 · 尺度诚实话术（P1 配套）🔄

- **描述**：问"某条街精确情绪分"（微观尺度细于数据支撑）→ 回答须含"宏观方向/非精确测量"声明 + 给替代趋势。P1 已强化 [review.py](ai_qa/review.py) `scale_paradigm_fit` desc（U7 三态：无声明→fail / 有声明无替代趋势→warn / 齐全→pass；scale_paradigm_fit 是客观项，fail→pass=false→revise）。
- **前置**：✅ desc 强化已落地（5.178）；⚠️ 灰度对比**待数据**——`DATA/ai_qa/episodes.jsonl` 63 条全宏观/GIS 操作，**微观精确问题 0 命中**，无法跑"≥10 条 fail 率对比"。待微观数据积累后补灰度（防 fail 率突增>30%）。
- **步骤**：开 EMC → 注入点层 → 发"西陵区某条街的精确情绪分是多少"→ 读回答 + 抓 review verdict。
- **断言**：软=回答含宏观声明（`宏观`/`非精确`/`趋势`类词）；硬=review `scale_paradigm_fit` verdict ∈ {fail, warn}（无声明应 fail→revise，有声明无趋势 warn）。
- **脚本**：`tests/browser/test_scale_honesty.py`（待落——需 LLM + 抓 /chat review 帧）。
- **关联**：plan v1.0 §配套 A；memory `project-design-philosophy`；U7 三态（CLAUDE.md「AI·Copilot 开发内核」无直接，见 review.py desc）。

---

## 用例 10 · A1 谓词真值（G1 配套）🔄

- **描述**：[cpd-state.js](frontend/js/ai_qa/cpd-state.js) 谓词（hasImport/hasRange/hasVisibleEmotionLayer/hasAnalysis）导出为纯函数 + 经 [e2e-seam.js](frontend/js/e2e-seam.js) 暴露 `window.__cpdPredicates`，`page.evaluate` 直读真值——把死信号/谓词盲区（`.aiq-conclusion` 死信号 / M2 无情绪层撒谎"点击深绿/深橙"）从评审发现变测试发现。
- **前置**：✅ G1 谓词导出 + e2e-seam 暴露已落地；✅ `fixtures/plain_poi.geojson`（无 polarity/score 字段，测 M2）已就位。
- **步骤**：开 EMC → 各场景（空 / 注入情绪层 / 注入无情绪层 / range 层 / dock 产图）→ `read_predicate(page, "() => window.__cpdPredicates.<pred>()")` 读各谓词。
- **断言**：硬=无情绪字段层（plain_poi）→ `hasVisibleEmotionLayer`=false（M2 演示链断点回归）；硬=情绪层 → true。
- **脚本**：`tests/browser/test_cpd_predicates.py`（G1 已就位，待跑）；helper `emc_helpers.read_predicate`。
- **关联**：GUIDANCE §1.1 A1；plan v1.0 §4.1 谓词 + §八 P0 增量；CB-CPD-03 M2。

---

## 用例 11 · H1 引擎不冻结（G1 配套）🔄

- **描述**：general 短路轮（exit=null）后引导引擎仍响应——`cpd:turn-ended` dispatch 守 `settled`（非 `exit!==undefined`）+ 单调去重 `turnId > lastProcessed`（非严格 +1），防 CB-CPD-03 H1 静默冻结。
- **前置**：✅ G1 引擎就绪（[cpd-guide.js](frontend/js/ai_qa/cpd-guide.js) + [panel.js](frontend/js/ai_qa/panel.js) finally dispatch）。
- **步骤**（确定性 dispatch 模拟，**免 LLM**）：开 EMC → 计数 `cpd:guidance` 派发 → dispatch `cpd:turn-ended` 序列：result(turnId=1) → general(exit=null·turnId=2) → 跳号 result(turnId=4) → 低 turnId(turnId=2)。
- **断言**：硬=result→general(exit=null)→跳号 result 均 `cpd:guidance` 响应（gCount 递增，不冻结）；硬=低 turnId 去重（不重复处理）。**组合场景**（事件×状态×去重咬合，H1 教训制度化）。panel.js finally `settled` dispatch 侧由代码审查 + 用例 6（exit-badge answer 路径）覆盖。
- **脚本**：`tests/browser/test_cpd_guide_no_freeze.py`（G1 已就位，待跑）。
- **关联**：plan v1.0 §4.3 H1 + §八 P0 组合场景回归；CB-CPD-03 H1；GUIDANCE §4.4。
