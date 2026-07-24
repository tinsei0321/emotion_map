# 测试飞轮机制评估报告 · 2026-07-24

> 评估人：K3 | 分支 `main` | 方法：**静态审查**（代码事实 + 历史报告 + 测试生态对照；应用户指示跳过大规模实测）
> 对象：测试飞轮 v4（`?test=1` 抽屉 + 270 例 + Prompt 池 + 报告 + 投票反馈）及其与测试生态的连贯性
> 证据：全部挂代码行号 / 历史报告样本；飞轮代码一行未改。

---

## 〇、总评

| 维度 | 评分(10) | 一句话 |
|---|---|---|
| 机制设计（运行器/状态机/落盘） | 7.0 | 串行 runner + 状态机 + 自动报告骨架完整，但**结果态是模块闭包、无外部可观测面** |
| 方法有效性（断言信号链） | 4.5 | **核心信号断链**：template 断言结构性失效（ChatRequest 无 diagnose 字段），参数断言恒 pass |
| 流程连贯性（与测试生态） | 4.0 | 五套测试资产并存、无单一事实源；谓词用例两处重复；eval 与飞轮各自为政 |
| Prompt 预设（池质量与原则对齐） | 5.5 | 八原则立得好，但**全正模式零负例**、时序/POI 扩展无落地、词表三处硬编码漂移 |
| 报告与反馈处理 | 4.5 | 报告无元数据/无 JSON/无历史 diff；投票数据不落盘；**闭环在"报告"处断裂，不回流 prompt 池** |
| 执行效率 | 5.0 | 每例重复 loadCSV+loadRange（~1.1s×225）、串行无分层、无失败聚类 |

**总评 5.1/10**：飞轮的"轮"（跑→报告）成型了，但"飞"不起来——**闭环三处断裂**（信号断链 / 反馈不落盘 / 失败不回流），且断言体系对"意图转译"这一核心被测对象的观测是半盲的。好消息：断链点都已精准定位，修复均为小切口。

---

## 一、机制事实清单（以代码为准）

### 1.1 架构与数据流

```
index.html?test=1 ──dynamic-import──► e2e-seam.js（fetch 拦截 _testFetchLog + __emcTest seam + __cpdPredicates）
                                   └─► test-board.js（runner）
                                         │ 配置弹窗（模式/类别/slider/超时）
                                         ▼
                                    test-cases.js CASES 270 例（8 类）
                                         │ llmRun：loadCSV+loadRange → t.send(q) → waitAnswer(90s)
                                         │ 抓 sig = {tools(geo url), template(chatPhases body.diagnose.template), params, newLayers}
                                         ▼
                                    _results（模块闭包·外部不可达）→ _buildMarkdown() → POST /_test/report
                                         │                                    └─► serve.py:239 → tests/reports/report-*.md（入 git）
                                         └─ 行内投票 V/X（userVote·仅内存）/ 重跑 R / 跳答案 chatIdx
```

### 1.2 用例集构成（270 例）

| 类别 | 数量 | llm | 断言性质 |
|---|---|---|---|
| CPD导游 | 15 | 3 | no-llm=DOM 态硬断言；llm=hint 文案包含 |
| UI渲染 | 15 | 3 | no-llm=DOM 存在性；llm=badge 渲染（恒 pass+人工 review） |
| 引擎谓词 | 10 | 0 | `__cpdPredicates` 真值硬断言 |
| 意图识别 | 100 | 100 | `tmplOk \|\| toolOk` 软断言（概念型只断非误 GAP） |
| 工具选择 | 100 | 100 | 硬断言目标工具触发 |
| 参数正确性 | 10 | 10 | **恒 pass，仅靠人工 review**（expect* 定义未接断言） |
| 成果范式 | 10 | 5 | no-llm=DOM 存在性；llm=恒 pass+人工 review |
| Smart交流 | 10 | 4 | 多为恒 pass+人工 review |

### 1.3 测试生态并存现状

| 资产 | 覆盖 | 事实源 |
|---|---|---|
| pytest 17 文件（207 例） | 后端纯函数/管道 | `tests/` |
| Playwright 6 脚本 | 运行时行为（catalog 11 例） | `docs/emc-test-cases.md` + `tests/browser/` |
| diagnose eval | Flash 模板路由（空 context，19 例） | `tests/eval_template_flash.py` |
| **飞轮 270 例** | 意图/工具转译 + CPD/UI 行为 | `test-cases.js`（无 catalog 登记） |
| 命中率遥测 | template 命中 localStorage + 80% gate | `harness.js:7-9,455,497-499`（无文档） |

---

## 二、三维度不足清单（每条挂证据）

### 2.1 连贯性（最弱维度）

**C1【H】template 断言信号结构性断链——意图识别 100 例的核心观测半盲。**
飞轮抓 template 的链路：`e2e-seam.js:56-59 chatPhases()` 读 `/chat` 请求体 `body.diagnose.template`。但 `ai_qa/schemas.py:11-22` ChatRequest **无 diagnose 字段**——diagnose 卡只以两种形式下沉：① `harness.js:457` 压扁成一行摘要进 `ctx.context` 字符串；② `harness.js:448-452` 仅 `domain_lens` 数组平铺回传。`api.js` 全文无 diagnose。**后果**：`sig.template` 恒为 null → `_assertIntent`（test-cases.js:168-170）的 `tmplOk` 永 false，意图断言退化为只剩 `toolOk` 单腿；`report-2026-07-23-02-llm.md` 全列 `tpl=?` 即此断链的实锤（当时归因于 _fill bug，修复后 `report-03` 的 TOL-001 仍 `tpl=?` 证明根因未除）。

**C2【H】词表三处硬编码漂移——diagnose prompt 内部自相矛盾。**
- `ai_qa/prompts.py:190` 卡说明词表 = 14 id（density/rank/buffer/clip/overlay/zonal/nearest/hotspot/area_stats/merge/extract_feature/concept/multi/unknown）——**缺 compare、filter_attr**；
- `ai_qa/paradigm.py:454,470` 决策树却教 Flash「对比→compare」、B 赛道 9 原型含 filter_attr；
- 飞轮 `expectTmpl`（test-cases.js:148-158）第三处硬编码。
三处无单源，任一处演进即静默漂移（`paradigm.py:420` 注释自承"JS normalizeCard 强制执行有意延后"）。

**C3【M】谓词用例两处重复建设。** 飞轮 PRED-01~10（test-cases.js:113-123）与 `tests/browser/test_cpd_predicates.py`（catalog 用例 10）覆盖同一组 `__cpdPredicates` 真值，断言逻辑平行演进，无共享 fixture 约定（飞轮用内联 fc，Playwright 用 `fixtures/plain_poi.geojson`）。

**C4【M】飞轮用例无 catalog 登记。** `docs/emc-test-cases.md`（11 例）是运行时行为测试的登记处（"先登记→实现→跑通"守则 :60），飞轮 270 例整体缺席——生态内最大的用例库反而没有事实源入口。

**C5【M】eval 与飞轮测同一对象、口径不一。** `eval_template_flash.py` 19 例期望词表无 compare/filter_attr 例（:40-61），且是空 context 单轮；飞轮是有 grounding 的运行时多轮。两处"模板命中率"数字不可比，却都隐含指导同一个 80% gate（eval :4-5 / harness.js `_tplHitRateReady`）。

### 2.2 覆盖度

**V1【H】全正模式零负例——八原则的反模式无一落地。** `emc-prompt-design-principles.md` 明确定义反模式：范围外地名（原则 8"滨江公园"）、微观精确（原则 4"某条街精确分"）、缺要素（原则 1）、无拓扑（原则 2）。但 INTENT_TYPES/TOOL_TARGETS 全是正模式模板，**没有一条用例验证系统对坏问题的拒绝/降级行为**（误 GAP 只在断言里当被罚项，从未当被测目标）。负例恰是"尺度诚实"（review.py U7 三态）和 GAP 出口契约的回归网——目前这两块承重逻辑零运行时覆盖。

**V2【H】参数正确性断言恒 pass。** PARAM_DATA 定义了 expectCell/expectRadius/expectBoundary（test-cases.js:262-271），断言函数（:276-279）却只返 `{pass:true, review}`——**期望参数从未与 `sig.params` 比对**。`llmRun` 的 `_extractParams`（:48-59）明明已抓到 cell/radius/boundary。这是 10 例的覆盖假象。

**V3【M】时序 T1-T3 零用例。** 原则 5 要求"时间轴相关用例必须有明确时态要求"，POINTS 资产有 L2-T1/T2/T3（test-assets.js:20-22），但无一例用 T2/T3 或问"演变"。

**V4【M】POI 缓冲扩展零用例。** 原则 8 注明确扩展了"以已载 POI 点为中心周边 N 米"分析类型，TOOL_TARGETS buffer 类（:218）仍只有"二马路片区"固定面中心。

**V5【M】成果范式/Smart 交流多为恒 pass。** RST-L01~L04、SMT-L01~L04 断言均 `{pass:true, review}`——把判断推给人工 review，但这些 review 提示（"是否产聚合层+着色？"）对应的 `sig.newLayers` 等信号已在手，可硬化（如 RST-L04 断 `density` 且 `newLayers>0`）。

**V6【L】no-llm 例的 DOM 存在性断言偏浅。** UI-01~08、RST-01~05 只断元素存在（`!!querySelector`），不断行为（如 UI-09 折叠展开切换才是行为断言，占少数）。

### 2.3 执行效率

**E1【M】每 llm 例重复装载数据。** `llmRun`（test-cases.js:18-25）默认每例 `loadCSV('L2-T1') + w(800) + loadRange('行政区') + w(300)` ≈ 1.1s+网络/解析 × 225 例 ≈ **4 分钟纯浪费**，且图层持续累积（`newLayers` 靠差值计算，层数膨胀拖慢后期例）。无"批级 setup 一次、例间 newChat 复位"的分层（pytest 的 class-scoped fixture 概念）。

**E2【M】slider 头部切片抽样偏斜。** `cases.slice(0, limit)`（test-board.js:144）+ CASES 固定排序（CPD/UI/PRED 在前）→ slider=25 时全是 no-llm 例，"跑 25 例抽验 llm"的直觉操作实际 0 llm 覆盖。无按类别分层抽样。

**E3【M】无失败聚类与趋势。** 报告是平铺表格 + 待复查列表，同根因失败（如"未触发 density"×N）不聚合；无跨 run 对比（本次 vs 上次 pass 率 diff），回归/改进不可见。

**E4【L】串行+固定 sleep 的保守节奏。** 每例前 w(300)+例间 w(500)（test-board.js:169,179），no-llm 例本可毫秒级连跑；统一 90s 超时对 concept 型（10s 可答）过宽、对复杂 multi 型可能偏紧。

**E5【L】手动存报告 confirm() 阻塞。** test-board.js:296 的覆盖确认是浏览器模态对话框，打断"跑完即走"的无人值守场景。

### 2.4 报告与反馈处理（闭环断裂点）

**R1【H】投票数据不落盘——人工反馈进不了任何持久层。** `userVote` 只写 `_results` 内存（test-board.js:129），`_buildMarkdown` 虽把投票渲进表格（:253,263），但**重跑/F5 即失**；更关键的是投票（自动判定的纠偏信号）没有任何机制回流为"该例断言应修 / prompt 应调"的待办——飞轮的"人工反馈→迭代"环是断的。

**R2【H】失败不回流 prompt 池。** 现有演进流程（handoff：跑 LLM 例→收断言失败→**人工**调 INTENT/TOOL 池）全靠人肉读报告。报告里没有"失败例的原始问句 + 实发工具 + 期望工具"的结构化三元组（obs 截断 60 字符 :270），无法直接转成 prompt 池修订 diff。

**R3【M】报告无 run 元数据。** 无 commit hash / 飞轮版本 / 模式与类别配置以外的环境信息（模型版本、后端版本、数据版本）——跨日报告无法定位"哪版代码的变化导致 pass 率变化"。

**R4【M】无机器可读输出。** 仅 markdown 表格，无 JSONL/JSON 原始记录——无法做趋势图、无法被脚本消费（本次审计驱动就不得不绕路抓 DOM+fetchLog）。

**R5【M】命中率遥测孤岛。** `harness.js:7-9` 已有 template 命中率 localStorage 累积 + 80% gate（:497-499 控制 runTemplatePath 启用）——**这是现成的闭环半成品**，但数据滞留浏览器 localStorage，与飞轮报告、eval 结果零连通，三方各算各的命中率。

**R6【L】报告命名粒度。** `report-<date>-<NN>-<type>.md` 的 type 只取 mode（llm/no-llm），同日同类多份靠编号区分，无法从文件名看出类别范围。

---

## 三、业界对照

| 实践 | 飞轮现状 | 差距 |
|---|---|---|
| **测试金字塔**（unit≫integration≫e2e） | 270 例中 225 例挂在最贵的 llm e2e 层；no-llm 仅 45 例且多为 DOM 存在性 | 倒金字塔。意图/工具断言的大量场景可下沉为"diagnose 单轮 eval"（扩 eval_template_flash 词表例）——成本降两个数量级 |
| **契约测试**（consumer-driven contract） | ChatRequest schema 是飞轮与被测系统的隐式契约，断链（C1）两年无人发现 | 缺契约断言：飞轮启动时应自检"我依赖的字段在请求体里真实存在"（schema probe 用例） |
| **LLM eval 分层**（DeepEval/RAGAS 式：路由 eval / 工具选择 eval / 端到端 eval 分离） | 意图识别把"路由对"与"端到端跑通"混在一例 | 拆层：路由层只跑 diagnose 单轮（快、便宜、可大样本）；e2e 层只留代表例 |
| **蜕变测试**（metamorphic testing，治 LLM 无 oracle） | 无 | 同义改写不变式：同一意图的 N 种问法应路由同一 template——正是 prompt 池模板×变量的天然断言，零额外成本 |
| **黄金数据集 + 版本化**（promptfoo 式） | prompt 池即黄金集，但无版本/diff/趋势 | 池变更应与报告 commit 联动，pass 率按池版本切片 |
| **flaky 管理**（quarantine + 重试标记） | 无 flaky 概念；LLM 不确定性失败与真回归混在 ERR 里 | 引入"重跑一次翻转=flaky 标记"，报告分列真失败 vs flaky |
| **反馈闭环**（annotation→dataset 回流，LangSmith 式） | 投票不落盘、失败不回流（R1/R2） | 投票 BAD 的例应自动生成"待修断言/待调 prompt"条目进 catalog |

---

## 四、优化清单（H/M/L 分级 · 仅建议，待逐项拍板）

### H 级（闭环断链，先修）

| # | 优化项 | 落点 | 工作量 | 承重冲突 |
|---|---|---|---|---|
| H1 | **接通 template 信号**：ChatRequest 增 `diagnose` 可选字段（结构化回传，同 domain_lens 范式），harness post-diagnose 各 phase 回传；飞轮 chatPhases 即通 | schemas.py + harness.js + api.js | 小 | **触 ChatRequest schema——需拍板**（不改 diagnose prompt 本身，eval 不破） |
| H2 | **词表单源化**：后端 template 词表收口 `paradigm.py`（prompts.py:190 说明从 TEMPLATE_REGISTRY 渲染，补齐 compare/filter_attr）；飞轮 expectTmpl 从 `/_test/template-registry` 端点（或构建期导出 JSON）动态拉取，消灭第三处硬编码 | paradigm.py + prompts.py + serve.py + test-cases.js | 中 | 无（prompts.py:190 是说明文本非路由逻辑，但建议跑 eval 确认） |
| H3 | **参数断言硬化**：PARAMS 断言接 `_extractParams` 已抓的 sig.params 与 expect* 比对（cell/radius/boundary 容差匹配），10 例从"恒 pass"变真断言 | test-cases.js:276-279 | 小 | 无 |
| H4 | **反馈闭环落地**：① 投票随报告落盘（_buildMarkdown 已含，补 JSON 同构输出）；② 报告增"失败三元组"段（问句/实发工具/期望工具，obs 不截断）；③ 投票 BAD 自动生成 catalog 待办条目（`docs/emc-test-cases.md` 追加区或独立 `flywheel-backlog.md`） | test-board.js + serve.py | 中 | 无 |
| H5 | **机器可读报告**：`/_test/report` 同步落 `report-*.json`（每例 pass/stage/obs/template/tools/params/durationSolo + run 元数据 commit/时间/配置） | test-board.js + serve.py | 小 | 无 |

### M 级（覆盖与效率）

| # | 优化项 | 落点 | 工作量 |
|---|---|---|---|
| M1 | **负例池**（详见 §五 Prompt 专章 P1） | test-cases.js 新增 NEG 类 | 中 |
| M2 | **批级 setup 分层**：llmRun 增 `opts.shared`——批首例装载 CSV+range，后续例仅 newChat 复位；层数膨胀用例间清理（srcName 标记删除） | test-cases.js + e2e-seam.js | 中 |
| M3 | **分层抽样**：slider 截取改"按选中类别等比取样"，或弹窗加"每类 N 例"模式 | test-board.js:144 | 小 |
| M4 | **失败聚类 + 跨 run diff**：报告头部增"按 obs 根因聚类 Top N"+ 与上一同型报告的 pass 率差（serve.py 读同日/近日报告） | test-board.js + serve.py | 中 |
| M5 | **时序与 POI 用例补全**（详见 §五 P2/P3） | test-cases.js | 小 |
| M6 | **flaky 标记**：单例失败自动重跑 1 次，翻转则标 flaky 分列统计 | test-board.js | 小 |
| M7 | **生态收口**：飞轮 270 例在 `docs/emc-test-cases.md` 登记入口（一节索引）；PRED 谓词用例与 Playwright 版明确分工（飞轮=快速冒烟，Playwright=组合场景回归），删重复 | docs + test-cases.js | 小 |
| M8 | **遥测连通**：harness localStorage 命中率随报告 dump（飞轮已能读 localStorage），报告增"template 命中率（运行时累积）"段，与 eval 数字并列对照 | test-board.js | 小 |

### L 级（体验抛光）

| # | 优化项 | 落点 |
|---|---|---|
| L1 | no-llm 例去固定 sleep（w(300/500) 按 type 跳过） | test-board.js |
| L2 | 超时按类别分档（concept 30s / 单工具 60s / multi 120s） | test-cases.js |
| L3 | 手动存报告改非模态（toast 内按钮确认，不阻塞） | test-board.js:296 |
| L4 | 报告文件名加类别段（`report-<date>-<NN>-llm-intent.md`） | serve.py:259 |
| L5 | no-llm DOM 存在性断言升级为行为断言（点击→状态变化） | test-cases.js |

---

## 五、Prompt 预设调整专章（强化闭环反馈与迭代能力）

> 现状：八原则（`emc-prompt-design-principles.md`）是**生产侧**质量基准，立得完整；缺口在**反馈侧**——池子只进（人工加模板）不出（失败不回流）、只正不负、词表无源。以下 5 项调整按"闭环贡献"排序。

### P1【H】负例池：让"拒绝坏问题"成为被测目标

八原则的每条反模式转成一类负例用例，断言系统的**降级行为**而非产出：

| 负例类（对应原则） | 样例 prompt | 期望断言（硬） |
|---|---|---|
| 范围外地名（原则 8） | 「滨江公园周边 500 米情绪」 | exit=gap/ask，**不**触发 geo 调用；回答含"范围外/无法定位" |
| 微观精确（原则 4） | 「夷陵广场某条街的精确情绪分」 | 回答含"宏观/非精确"声明（尺度诚实 U7 回归网）；review scale_paradigm_fit ∈ {warn,pass} |
| 缺要素（原则 1） | 「情绪归因」 | diagnose data_plan.strategy≠ready 或 ask 出口（缺参追问） |
| 无拓扑（原则 2） | 「哪些区域情绪最差」 | ask/gap，不硬答 |
| 臆造 POI（原则 8 注） | 「奥体中心周边情绪」（未载 POI） | gap 卡含"需要什么数据"，不编造坐标 |

**闭环价值**：负例是 prompt 池的"免疫系统"——每次 diagnose/review 层改动，负例池防"为了过正例而乱答"的退化。建议 20-30 例起步，类别名 `负例防御`。

### P2【M】时序变体：把 T1-T3 资产用起来

新增意图类「时序演变」（expectTmpl=['compare','zonal','multi']）：
- 「西陵区 T1→T3 情绪变化趋势」「哪片区域从 T1 消极到 T3 好转」「对比 T1 与 T3 的消极占比」
- llmRun opts 支持 `csv:['L2-T1','L2-T3']` 双层装载（test-assets 已备）。
**闭环价值**：时序是产品演示链（时光叙事 F5）的预埋测试面。

### P3【M】POI 缓冲变体：对齐原则 8 注

buffer 类从"二马路片区固定面"扩到"已载数据 POI 点"：
- 「以 spatial_hotspot 值 X 为中心周边 500m 情绪分布」（X 从 L2 CSV 字段实取，test-assets 增 POI 语义清单）
- 断言 buffer 触发 + center 参数非空。
**闭环价值**：覆盖 buffer 技能的 POI 分支（paradigm.py:126），该分支现零运行时验证。

### P4【H】词表单源 + 断言随源演进（配合 H2）

prompt 池的 expectTmpl/expectTools 不再手写，改为**从后端注册表派生**：
```
serve.py 增 GET /_test/template-registry → paradigm.TEMPLATE_REGISTRY 序列化
test-cases.js 启动时 fetch → 生成 expect 映射（skill→tool 从注册表 required_slots/tool 字段）
```
**闭环价值**：后端加技能 → 飞轮期望自动扩，词表漂移（C2）从机制上消灭；这也是"契约测试"的落地——飞轮启动先校验注册表与本地假设一致，不一致**先报契约错**再跑例。

### P5【H】失败回流机制：报告 → 池修订的传送带

把"人工读报告调池"升级为半自动：
1. 报告 JSON（H5）中每失败例带 `{q, expectTools, actualTools, template, obs}` 结构化五元组；
2. 新增 `flywheel-backlog.md`（或 catalog 分区）：投票 BAD / 自动失败例自动追加一行待办（问句 + 失败模式 + 建议动作：调池/修断言/报 bug）；
3. 调池后重跑该例（重跑 R 已有），pass 则 backlog 勾销——**"失败→待办→修订→重跑→销账"五环闭合**，这才是飞轮的"飞"。
4. 进阶（可选）：同义改写蜕变断言——每个正例模板自动生成 2 条同义问法，断言同 template 路由，pass 率直接度量"池的泛化覆盖"，指导补模板方向。

### Prompt 池维护纪律（写入 principles 文档）

- 每条模板至少 1 条负例镜像（防过拟合正例）；
- 池变更 commit 必须附最近一次报告 JSON 的 pass 率切片（池版本↔效果可溯）；
- 新增模板先过检查清单（principles §三 6 项）+ 负例审查，再入池。

---

## 六、落地路线建议（若拍板，按此序）

1. **第一批（信号修复，1 次会话）**：H1 接通 template 信号 + H3 参数断言硬化 + H5 JSON 报告 → 飞轮核心观测从半盲变全明。
2. **第二批（闭环成形）**：H4 反馈落盘+backlog + H2 词表单源 + M8 遥测连通 → 五环闭合。
3. **第三批（覆盖扩边）**：P1 负例池 + M2 批级 setup + M3 分层抽样 + M5 时序/POI → 覆盖与效率双升。
4. **第四批（生态收口）**：M7 catalog 登记 + M4 聚类 diff + L 级抛光。

每批结束跑 no-llm 全量 + llm 抽样验证，报告入 `tests/reports/` 留痕。

---

## 附：本次评估留痕

- 实测驱动 `tests/browser/flywheel_audit.py` 已建（三路采集设计：DOM 行态 / `_testFetchLog` bodyKeys 验断链 / 报告 diff），因用户指示跳过实测未跑通全程；后续拍板实施 H 级修复后可直接用其收基线。
- 环境备注：本机 Playwright chromium 需 `py -m playwright install chromium`（cdn 直连较慢，可配 `PLAYWRIGHT_DOWNLOAD_HOST` 镜像）。
- 引用行号以 2026-07-24 `main`（f953f6c）为准。
