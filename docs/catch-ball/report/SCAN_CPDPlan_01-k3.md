模型：k3

# CPD 核心 Plan · 第三方评价报告（CB-CPD-01）

> **轮次**：CB-CPD-01（首评） | **日期**：2026-07-22 | **被评**：`docs/cpd-core-plan.md` v0.2（单文档）
> **方法**：全文精读 plan + 承重实证（cpd-state.js / panel.js / harness.js / tools.js / state.js / review.py / manifesto.py / eval_template_flash.py / emc-test-cases.md / tests/browser/），全部判断附文件:行号。
> **立场**：中立第三方，不背书。本轮未发现撞承重红线的建议项；但发现 2 个 P0 级 spec 错误——plan 对"已就绪地基"的两处事实陈述与代码不符。

---

## 总体判断

plan 的**方向与承重纪律是合格的**：纯客户端确定性引擎（决策 1）、两路径分工（决策 2）、软折叠基调（决策 3）、尺度诚实落 review 层而非 diagnose（决策 4）——四个决策都踩在正确落点上，禁改清单（§七）逐条核实无虚言。P0 测试铺底的重排也正确回应了"前端零单测 = 唯一真短板"。

**但 §4 引导状态机是全 plan 最弱一节**：它声称复用的信号源（`.aiq-conclusion`）在代码中不存在生产者（死信号），它使用的 exit 词表（RESULT/GAP/PARTIAL/CONCEPT）与 harness 实际返回值（小写五值 + general 短路无 exit 字段）不匹配，它的映射表以 curState 为 key 而 curState 的派生逻辑（cpd-state.js:27-35）使表中两行永不可达。**这三者不修，G1 实现时 deriveGuidance 写出来就是错的，且错得静默（不报错，只是引导永不触发或触发错分支）。** 好在修正成本低——都是 spec 层的词表/信号定义问题，不是架构推翻。

---

## 一、架构合理性

**结论：方向正确，接缝干净，但 deriveGuidance 的信号规范有三个 P0 错误 + 一个状态概念混淆。**

**两路径分工（决策 2）——干净。** 主动引导（UI nudge）与对话分析（harness）零耦合，唯一接缝是 panel.js `send()` 末尾 dispatch `cpd:turn-ended`。实证：send() 结构（panel.js:1120-1197）finally 段（1181-1196）有明确插入点；panel.js 不在禁改清单（禁改 = harness.js/stages.js/tools.js）。**接缝"零侵入"harness 属实**——读 `_curTrace.exit`（1162 行赋值后）不写 harness。

**deriveGuidance 漏态/竞态——三个 P0：**

1. **【P0】`.aiq-conclusion` 是死信号。** cpd-state.js:29 `document.querySelectorAll('#chat-messages .aiq-conclusion')` ——全前端 JS **无任何位置创建该类名元素**（grep 实证：仅 ai_qa.css:523-530 样式定义 + cpd-state.js 自身引用）。后果：deriveState() 的 `concl` 恒为 0 → **curState 永远到不了 S4**，实际只有 S0/S2/S3 三态。plan §4.1 把它列为"已订阅信号"、§4.2 把 S4 作映射表 key 行——**S4 引导分支（RESULT→export 等）依赖的 curState 信号在现实中不可达**。改法（二选一，推荐 b）：
   a. stampDone/_renderFooter 时给 shell 元素加 `aiq-conclusion` class（补生产者）；
   b. **改用已存在的 `.aiq-exit-badge`**（panel.js:378 `b.className = 'aiq-exit-badge '` 确实创建，回答完毕即出现）作 S4 信号——零新增、语义更准（exit-badge 只在"完毕"时出现，流式中不存在，顺带缓解"流式误推"）。

2. **【P0】exit 词表与 harness 实际返回值不匹配。** plan §4.1/§4.2 用大写 RESULT/GAP/PARTIAL/CONCEPT；harness.js 实际返回小写 `'result'/'gap'/'partial'/'ask'/'drift'`（272/292/307/476/568/608/620/644 行实证）。更关键的是 **general 短路路径（harness.js:372/412）根本不返回 exit 字段**（undefined）——plan 的 "exit=CONCEPT(general)" 行**永远不会触发**；真实存在的 `'drift'`（格式漂移/谎报拦截，568/580 行）在映射表**完全缺席**。改法：§4.1 信号规范写死为——读 `trace.exit`（小写五值 ∪ undefined）；CONCEPT 分支改判 `trace.diagnose.intent==='general' || trace.review.skipped∈{'general','quick-general'}`（与 `_followUps` panel.js:478 同源同判，plan §5.2 自称"复用 _followUps 映射"就该连它的判据一起复用）；drift 补映射行（→重试/缩小范围，同 _followUps:465-469）。

3. **【P0】映射表 key 与 curState 派生逻辑矛盾，两行永不可达。** cpd-state.js:27-35 deriveState：**任何**可见层（不分层型）→ S2。因此"S0 有 import"不可能（import 后 vis≥1→S2）；"S1 有 range 无可见情绪层"也不可能（range 层可见→S2，S1 根本不由 deriveState 产出——文件头注释自己也承认"S1 range-only 不自动判"）。§4.2 表以 curState 为 key 是**结构性错误**。改法：deriveGuidance 的 key 改为**特征信号向量** `(hasImport, hasRange, hasVisibleEmotionLayer, hasAnalysis, lastExit, streaming)`，§4.2 表重写为特征向量真值表；curState 仅作进度点显示输入。plan §九"cpd-state.js 导出 hasImport/hasRange/hasAnalysis 辅助（不改 deriveState）"已指向这个方向——§4.2 表与之对齐即可，是文档矛盾非设计推翻。

**竞态（中）**：① dispatch 放 finally 段 → abort/请求失败也触发 turn-ended，引擎须处理 `exit===undefined`（建议：失败不 dispatch 或 dispatch 标 ok:false）；② restoreHistory（panel.js:1257-1268）/ switchSession / clearChat **均不 dispatch** → F5 刷新、切会话后引导如何初始化？plan §4.1 说"读 _history 末条 trace"但没说是 init 时读还是仅事件驱动。改法：G1 验收加三条硬用例——F5 刷新后引导正确恢复 / 切换会话后引导正确 / abort 后不误推（引擎 init 时主动读 _history 末条 trace.exit 一次）。

---

## 二、功能图谱完备

**结论：§三图谱本身完备且诚实（归因工具标"待开发"、search 标"独立"都对），漏项不在图谱在信号——见 P0-2/3。另有两个谓词定义缺口。**

- **ask 出口**：plan 把它留给 U3 是诚实的，但 §4.2 表至少应标一行 `exit='ask' → null（不介入）`——ask 时选项胶囊已在答案区内（_followUps:464 实证"底部不再重复追问"），再推引导 = 双 CTA 打架。**我的立场：U3 收敛为 null 不介入**，写进表里防实现时自由发挥。
- **空 import 有 range**：plan G3 列为边界 case（有自觉），但 §4.2 表结构表达不了它（range 层可见→curState=S2→表上落在"S2 analyze"行，与"无 import 应先导数据"矛盾）。**这正是 P0-3 的实例**——特征向量真值表重写后自然解决（hasImport=false 优先于一切 → import 引导）。
- **多轮续作**：`ctx.resume`（panel.js:1150-1153）使上轮 GAP 后用户说"已上传"直接续跑——续作成功后 turn-ended 带新 exit，闭环成立。无漏。
- **谓词缺口（低）**：`hasImport = 有 point 层` 会误判——EMC 分析产出层（grid 格网/AI 组）也可能含 point；`hasAnalysis = grid/zonal 聚合层` 未定义判定谓词（state.js 层模型 kind∈{point,line,polygon,group,heatmap}，grid 靠 paint._ui.tool 或组归属识别，state.js:300/662-663/870 实证）。改法：§4.1 补谓词定义——hasImport = 存在**非 AI 组、非 tool 产出**的 point 层；hasAnalysis = 存在 `paint._ui.tool∈{grid,zonal,heatmap}` 或归属 'EmotionMap Copilot' 组的层（isRangeLayer 已有 state.js:662 可复用，hasRange 无歧义）。

---

## 三、承重边界

**结论：无暗触。逐条核实禁改清单，plan 清白；尺度诚实的 eval 安全性已实证。**

- diagnose 不动 ✓：plan §决策 1/§七声明，尺度诚实落 review.py `scale_paradigm_fit` 的 desc（审查层 Flash prompt），**非** diagnose prompt。实证 `tests/eval_template_flash.py` 全文——只喂问题给 diagnose、解析 template 字段（64-79 行），不 import review.py、不触 REVIEW_CHECKLIST。**"改 desc 不破 eval"属实**。
- 四态出口不动 ✓：引擎只读 `trace.exit`，不写。harness.js/stages.js/tools.js 不动 ✓：唯一代码触点是 panel.js send() dispatch CustomEvent + cpd-state.js 加导出——均不在禁改清单。
- curState 纯客户端 ✓、软折叠 ✓（§6.2 engage 解除而非锁死）、自适应位置 ✓（banner 复用 relayoutFloats/positionFloatingPanels，cpd-state.js:81-97 实证机制存在）。
- **一个事实核查顺手项（零风险）**：review.py:1 docstring 与 ai_qa/__init__.py:11 仍写"六条"，实际 REVIEW_CHECKLIST 已 7 条（review.py:18-54，REVIEW_TEMPLATE:63 已写"七条"）。plan"保七条稳定"表述正确，注释漂移顺手修。
- **尺度诚实机制成立但有灰度缺口（中）**：review.py:93 pass 判定——客观项（含 scale_paradigm_fit）任一 fail → pass=false → revise 1 轮。desc 强化后，Flash 对"微观精确问题"的 fail 率必然上升 → **revise 触发率、时延、token 消耗都会涨，且 revise 仅 1 轮，若重写后仍无声明则按 fail 交付**（用户看到的就是"没有声明的答案"+ 审查 fail 标记）。U7 阈值的实际后果比 plan 写的重。改法：P1 加灰度步骤——改 desc 后取 ≥10 条历史微观问题（episodes.jsonl 有料）跑 review_answer() 对比新旧 fail 率，突增 >30% 则先调话术再上；U7 建议收敛为三态分级（无声明=fail / 有声明无替代趋势=warn / 齐全=pass）——现有 verdict 三态天然支持，warn 不触发 revise，正好做"轻提醒"档。

---

## 四、演示表现力（重点）

**结论：折叠/展开是一套设计语言（光环→banner 同一 guidance 对象驱动），软折叠+自适应位置落实有实证；但 theme var 承重被既有光环实现违反，且引导链路只服务演示逻辑链的"前链路"，交互环未闭合——这是 U6 的实质答案。**

**设计语言一致性——成立。** 折叠态（.has-guidance 光环 + placeholder 文案）与展开态（.emc-guide-banner）由同一 `guidance` 对象驱动（§6.2/6.3），engage 解除机制（CTA 点击/输入聚焦/动作完成→光环停而非控件锁死）忠实执行软折叠基调。banner 位置复用 relayoutFloats（cpd-state.js:97）不写死 left。**"一套语言"属实。**

**theme var 承重——被既有实现违反（中）。** plan §七声明"EMC 颜色全走 theme var"，§九复用".has-guidance CSS 已就绪"——但该钩子本体是硬编码 hex 渐变：`ai_qa.css:431 linear-gradient(115deg,#4796E3,#7B5DFC,#BF4AD6,#D96570,#4FC3F7,...)` + `:456 background-color:#ececec`。G4"主题同步（Light/Dark）"未把光环渐变 theme-var 化列入文件清单（§九 ai_qa.css 行只提 .emc-guide-banner）。改法：§九 ai_qa.css 行补"光环渐变抽 `--emc-halo-*` theme var（Light 模式另校准）"，落 G2 或 G4。

**引导是否服务演示逻辑链——服务"前链路"，交互环未闭合（中，U6 实质）。** plan 全部引导动作指向**数据装载链路**（import→range→layers→analyze→export），把用户领到"有数据可问"。但演示逻辑链的第一环是"张力图面→**引导点击突出要素**"，交互环是"点击→分析→归因"——plan 没有任何 nudge 指向地图要素/Overview/网格点击。结论落地后，"视野(地图)↔数据(Overview)↔结论(归因)"三端同步全靠用户自发点击。改法（低成本闭合）：G3 加一条——S4·RESULT 且结论含 `[ref:区域]`/`{{focus:}}` 时（_followUps:455 已有同款 region 抽取），banner 次 CTA 加"**在地图上定位该区域**"（复用现有 focus/popup 机制），把引导环从"结论"闭合回"视野端"。这一条不做，CPD 对演示逻辑链的贡献止步于"装载自动化"；做了，才真正覆盖"定位关注区"这一宏观诊断信号。**这是对 U6 的回答：当前设计是"为引导而引导"的风险真实存在，闭合交互环后风险解除。**

**curState 从"反映"升"编排"是否提升演示张力——机制上成立，前提是 P0 三修。** 引导的本质是把"用户找按钮"的认知成本转为"系统给路径"，对演示节奏（尤其陌生观众前的现场演示）是实质提升：演示者零学习成本走完 import→分析→结论全链。但该价值完全依赖 deriveGuidance 触发正确——P0 三错不修，引导在最需要它的 S4 结论时刻（演示高潮）静默缺席。

---

## 五、分阶段合理

**结论：P0→P1→P2 重排正确，G1 可独立 ship；但 P0 用例清单有一处顺序表述矛盾，G3 引入前文未定义的 UI 概念。**

- **重排方向对**：测试铺底（P0）回应"前端零单测 = 唯一真短板"，且 tests/browser/lib/emc_helpers.py 已存在（实证），test_compare_regions.py 已跑通（用例 1 ✅），基建不是从零起——P0 工作量估计可信。尺度诚实（P1）是 review.py 一处 desc + 灰度，小工作穿插合理。
- **G1 能独立 ship（agree U2）**：折叠态光环 + placeholder + S0/S2/S4 引导即成最小闭环（清 localStorage→光环亮→导入→文案变→出结论→文案变 export），不依赖 G2 banner。依赖顺序 G1→G2→G3→G4 无倒置。
- **顺序表述矛盾（低）**：§八 P0 描述把"引擎状态转移（S0→S1→S2→S4）"列入 P0 新增用例——但 P0 阶段引擎不存在，测不了状态转移；§配套 B 又写对（"CPD 引擎行为（P2 随实现补）"）。改法：P0 改为"地基行为用例（折叠欢迎卡/高度自适应/exit-badge/历史桶）"，引擎状态转移用例挪入 G1 条目——与"TDD-lite 每 G 补用例"对齐。
- **G3 概念未定义（低）**："绿色摘要条（已完成步骤折叠）"首现于 §八 G3 描述，§六渐进披露细则全文无此 UI 元素的定义/样式/退场规则。改法：§六 6.1 表补一行或 6.3 补一段定义（它其实是"已完成步骤的 guidance 残留态"，建议与 banner 统一为同一组件的 done 变体，避免又造一个视觉方言）。

---

## 六、风险漏项

**结论：plan 自列的四项（流式误推/引导 vs 追问胶囊/状态回退/localStorage）命中其三，但各缺一层；另有两项未列。**

1. **流式误推——plan 有对策但信号选错。** §4.2 "S3 非流式不打扰"+ G3"流式中不推"，方向对；但若按 P0-1 改法 a（加 aiq-conclusion 生产者）且生产者在流式中途创建元素 → MutationObserver 触发 recompute → S3 提前跳 S4 误推 export。改法 b（`.aiq-exit-badge`）天然免疫（badge 只在完毕时创建）。**这是最稳的修法**。另引擎可直接读 `_streaming`（panel.js:1135/1193 有现成标志位）作硬门，双保险。
2. **引导 vs 追问胶囊——G2"合并同源"方向对，动作语义需分组（低）。** banner 主 CTA 是 UI 动作（开抽屉/导出），次追问胶囊点击是 `send(text)` 发对话（renderSuggest panel.js:508 实证）——两种动作语义混排用户分不清"点了发消息 vs 点了开面板"。改法：banner 内保持两套视觉语言——主 CTA 用按钮、追问沿用 aiq-suggest-chip 胶囊，分组不混排。
3. **状态回退——plan 未覆盖"用户逆行"（中）。** 用户按引导走到 S2 后删了图层/清了 range → layers:changed 触发 recompute → 引擎应回推 S0/S1 引导。plan 只字未提"回退引导"。特征向量真值表天然覆盖（hasImport/hasRange 变 false 即回推），但 §4.2/§六应明确一句"回退 = 同一真值表重算，无特殊路径"，防实现时漏。
4. **localStorage 脏态——plan 未提引导态持久化策略（低）。** _emcCollapsed（COLLAPSE_KEY）已持久化；引导态若也持久化，刷新后可能"光环亮着但引导已过期"。建议：**引导态不持久化**，每次加载由引擎 init 重算（信号全客户端可重推）。一句话写进 §六即可。
5. **engage 解除的"再亮"条件（低）**：§6.2.3 "engage 解除后下一状态变化再决定重亮"——若用户解除后状态长期不变（如对着 S0 import 光环点了 EMC 但不导入），光环永久熄灭，引导消失。可接受（不打扰优先），但建议加"会话内首次 engage 后 N 分钟未动作 → 轻量再亮一次"的兜底，或至少 U 系列留个观察项。

---

## 分级建议清单

**高（G1 前必修，否则引擎写出来即错）：**
- H1. 修 S4 信号：`.aiq-conclusion` 死信号 → 改用 `.aiq-exit-badge`（panel.js:378 已创建）作 deriveState 的 S4 判据。【维度一·P0-1】
- H2. 修 exit 词表：信号规范写死小写五值 ∪ undefined；CONCEPT 改判 intent/skipped；drift 补映射行；ask 标 null 入表。【维度一/二·P0-2】
- H3. §4.2 映射表重写：key 从 curState 改为特征信号向量真值表（hasImport/hasRange/hasVisibleEmotionLayer/hasAnalysis/lastExit/streaming）。【维度一·P0-3】

**中（G1/G2 携带）：**
- M1. turn-ended 竞态三用例入 G1 验收：F5 刷新恢复 / 切会话 / abort 不误推；引擎 init 主动读 _history 末条 trace.exit。【维度一】
- M2. 光环渐变 theme-var 化入 §九 ai_qa.css 行（G2/G4）。【维度四】
- M3. G3 加"在地图上定位该区域"次 CTA（S4·RESULT 含 ref/focus 时），闭合交互环——U6 的实质解法。【维度四】
- M4. P1 尺度诚实加灰度步骤：≥10 条历史微观问题对比新旧 desc fail 率，>30% 先调话术；U7 收敛为三态分级（无声明=fail/有声明无替代=warn/齐全=pass）。【维度三】
- M5. §4.1 补 hasImport/hasAnalysis 谓词定义（排除 AI 组/tool 产出层）。【维度二】
- M6. 补"回退引导"一句（同一真值表重算，无特殊路径）。【维度六】

**低（抛光期）：**
- L1. P0 用例清单顺序修正（地基行为 vs 引擎行为分开）。【维度五】
- L2. G3"绿色摘要条"定义补入 §六（建议作 banner 的 done 变体）。【维度五】
- L3. banner 内主 CTA（UI 动作）与追问胶囊（对话动作）视觉分组。【维度六】
- L4. 引导态不持久化写进 §六。【维度六】
- L5. review.py:1 / ai_qa/__init__.py:11 "六条"→"七条"注释漂移顺手修。【维度三】
- L6. engage 解除后再亮兜底（或留观察项）。【维度六】

---

## U 系列未决项立场（收敛参考）

| 项 | 立场 | 一句话理由 |
|---|---|---|
| U1 引导=UI nudge | **agree** | 对话消息污染 _history/LLM context，UI nudge 零副作用，且与 harness 零耦合的唯一干净方式 |
| U2 MVP 分阶段 | **agree** | G1 折叠态引导即可独立闭环，不依赖 banner |
| U3 ask 出口引导 | **收敛为 null 不介入** | ask 时选项胶囊已在答案区内（_followUps:464），再推 = 双 CTA 打架；写入映射表防自由发挥 |
| U4 timeline/compare/search | **agree 当前深度** | search 独立正确；timeline/compare 轻编排入 G3 合理 |
| U5 banner vs 欢迎卡 | **融合** | §6.3 方案（无对话融合/有对话置顶）已对，agree |
| U6 引导是否真服务演示链 | **partial——当前只服务前链路** | 引导停在"装载自动化"，交互环（点击要素→分析）未闭合；M3"定位到地图"CTA 做了才闭环 |
| U7 尺度诚实话术分寸 | **三态分级** | 无声明=fail（触发 revise）/有声明无替代=warn（轻提醒）/齐全=pass；配合 M4 灰度防 revise 率飙升 |

---

## 附录 · 关键证据索引

| 发现 | 证据 |
|---|---|
| `.aiq-conclusion` 死信号 | cpd-state.js:29 查询；全前端仅 ai_qa.css:523-530 有该类名，无任何 JS 创建 |
| `.aiq-exit-badge` 可作替代 | panel.js:378 `b.className='aiq-exit-badge '+...` 回答完毕时创建 |
| exit 实际词表 | harness.js:272/292/307/476/568/580/608/620/644（'result'/'gap'/'partial'/'ask'/'drift'） |
| general 短路无 exit 字段 | harness.js:372/412 return 对象无 exit key |
| deriveState 不分层型 | cpd-state.js:27-35（任何可见层→S2；S1/S5 不自动判） |
| _followUps 判据（应同源） | panel.js:457-496（exit+skipped+intent 三判据；drift/ask 已处理） |
| send() 接缝插入点 | panel.js:1160-1196（orchestrate 后 1162 赋 exit；finally 1181+） |
| restoreHistory 不 dispatch | panel.js:1257-1268 |
| 光环硬编码 hex | ai_qa.css:431（linear-gradient 七色 hex）/ :456（#ececec） |
| theme 切换基建已存在 | panel.js:1571-1577（data-theme）+ ai_qa.css:317/483+（[data-theme="light"] 覆写） |
| 软折叠/自适应机制已存在 | cpd-state.js:71-97（positionDrawer/positionFloatingPanels/relayoutFloats） |
| eval 只测 diagnose | tests/eval_template_flash.py:40-79（喂问题→解析 template 字段，不触 review） |
| review pass 判定（revise 杠杆） | review.py:93（客观项 fail→pass=false）；_OBJECTIVE 含 scale_paradigm_fit（173 行） |
| 微观工具存在（§配套 A 前提） | tools.js:656（inspect_zone）/ 890-903（buffer）/ 923-934（nearest） |
| MANIFESTO 十一节存在 | manifesto.py:80-86（尺度-方法-范式，仅约束 intent=C） |
| 测试基建 | tests/browser/lib/emc_helpers.py 存在；test_compare_regions.py 跑通；emc-test-cases.md 4 例（1✅/2⬜/1🤚） |
| Ctrl+Shift+G 测试代码待删 | panel.js:1550-1562 |
| cpd:focus-tab/openImport 已就绪 | sidebar.js:784-797 / :140 |
