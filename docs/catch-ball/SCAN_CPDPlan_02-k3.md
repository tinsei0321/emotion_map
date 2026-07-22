模型：k3

# CPD 核心 Plan · 第三方评价报告（CB-CPD-02）

> **轮次**：CB-CPD-02（v0.3 验证轮） | **日期**：2026-07-22 | **被评**：`docs/cpd-core-plan.md` **v0.3**
> **基线**：v0.2 → v0.3（CB-CPD-01 反评价后修订，26 条 agree 20 / partial 6 / disagree 0）
> **方法**：首轮建议逐条核验（RULES §1.4 闭环）+ v0.3 新增内容独立实证（真值表/事件载荷/色板/模块边界），全部判断附文件:行号。与 SCAN_CPDPlan_02-deepseek 并行独立评审（未读其全文，journal 摘要已知其两高点，本报告重合发现 = 收敛信号）。

---

## 第〇部分：CB-CPD-01 建议执行核验（K3 首轮 15 条逐条）

| 我的首轮建议 | v0.3 执行 | 核验 |
|---|---|---|
| H1 `.aiq-conclusion` 死信号→改 `.aiq-exit-badge` | §4.1 已改，且注明"顺带免疫流式误推"；§九 cpd-state.js 行同步 | ✅ 完整执行 |
| H2 exit 词表小写五值∪undefined；CONCEPT 改判 intent/skipped；drift 补行；ask 标 null | §4.1 词表修正（引 harness.js 行号）；§4.2 表 drift→retry / ask→null / gap·partial→null 三行齐 | ✅ 完整执行 |
| H3 映射 key 改特征向量真值表 | §4.2 全表重写（hasImport/hasRange/visEmotion/lastExit/streaming），首匹规则+回退同表重算 | ✅ 完整执行 |
| M1 turn-ended 竞态（finally 守卫/init 恢复/F5·切会话·abort 三用例） | §4.3 载荷 {exit,turnId,intent} + `_curTrace?.exit!==undefined` 守卫 + init 恢复 + G1 三硬用例 | ✅ 完整执行，且 turnId 去重超出我的建议 |
| M2 光环渐变 theme-var 化 | §七末条 + §九 ai_qa.css 行（`--emc-halo-*`，Light 另校准，G2/G4） | ✅ 完整执行 |
| M3 S4 地图定位 CTA 闭合交互环 | §6.4 S4·result 含 ref/focus 时次 CTA「在地图上定位该区域」+ 提前至 G2 | ✅ 完整执行（比我建议的 G3 更提前） |
| M4 尺度诚实灰度 + U7 三态分级 | §配套 A：fail/warn/pass 三态 + ≥10 条历史微观问题 >30% 调话术 | ✅ 完整执行 |
| M5 hasImport/hasAnalysis 谓词定义 | §4.1 四条谓词全定义（排除 AI 组/tool 产出；isRangeLayer 复用） | ✅ 完整执行 |
| M6 回退引导（同真值表重算） | §4.2 规则首条"回退 = 同真值表重算，无特殊路径" | ✅ 完整执行 |
| L1 P0 用例顺序（引擎用例挪 G1） | §八 P0 已改"地基行为用例"，引擎用例挪 G1，标注 v0.2 自相矛盾 | ✅ 完整执行 |
| L2 绿色摘要条定义（banner done 变体） | §6.4 采纳"banner done 变体"定义 + 点「修改」回退 | ✅ 完整执行 |
| L3 banner 主 CTA 与追问胶囊视觉分组 | §5.2 末"视觉分组不混排" | ✅ 完整执行 |
| L4 引导态不持久化 | 未明文；隐含于"init 主动恢复"（若持久化则无需恢复）。另 panel.js:25 `_emcCollapsed` 已改"F5 默认折叠不记忆"（2026-07-22 用户定），方向一致 | ⚠️ 隐含执行，建议 §六补一句明文 |
| L5 review.py docstring "六条"→"七条" | §八 P1 列入顺手修 | ✅ 完整执行 |
| L6 engage 再亮兜底 | 转 U9 观察项 | ✅ 可接受（agree 不打扰优先） |

**核验结论：15/15 执行或合理处置，无一敷衍。** 修法质量两处超出原建议：exit-badge 替代信号顺带免疫流式误推；"同真值表重算"处理回退不记历史、无状态腐烂面。**CB-CPD-01 → v0.3 闭环成立。**

---

## 总体判断

**v0.3 已达可实施质量，agree 进入 P0 测试铺底。** 三个 P0 spec 错误的修复全部正确且经我复核代码属实；特征向量真值表是本 plan 的正确架构形态；演示表现力从"功能教程"升到"诊断叙事"方向正确（S3 空间交互优先是本轮最有价值的转向）。

**但 v0.3 的新增内容自身引入了 2 个新的高优先级问题**（均不在 v0.2，是修订动作产生的）：① init 恢复的"只读 getter"方案制造 panel.js ↔ cpd-guide.js 循环 import 风险；② S4 文案动态变量"主题倾向 X×Y，排序第 N"在确定性客户端引擎中无数据源。另有 3 个中优先级文字/覆盖缺口。**全部可文档级修正，不阻塞 P0，但必须在 G1 动手前修掉 H1/H2——否则 cpd-guide.js 第一行 import 就埋雷。**

---

## 一、架构合理性

**结论：真值表架构正确、事件接缝更稳；但 init 恢复的 getter 方案引入循环 import 风险（新 H1），turnId 去重价值有限（新 L1）。**

**事件载荷与守卫——稳健。** `{exit,turnId,intent}` 载荷（§4.3）让引擎零 import 闭包变量即可得 exit 与 general 判据（intent）；`_curTrace?.exit!==undefined` 守卫精确覆盖 abort/异常路径（panel.js:1162 只在 orchestrate 成功返回后赋 exit，AbortError 走 catch → exit 保持 undefined → 不 dispatch ✓）。

**【新 H1】init 恢复的"只读 getter"方案 = 循环 import 雷。** §4.3"引擎初始化时经 panel.js 导出的只读 getter 读 _history 末条"——`_history`/`_streaming` 是 panel.js 模块闭包变量（panel.js:17/19 实证）。getter 须由 panel.js 导出 → cpd-guide.js `import { getLastTrace } from './panel.js'`；同时 panel.js `_setupCpdBar` "接引擎"须 `import { initCpdGuide } from './cpd-guide.js'` → **panel.js ↔ cpd-guide.js 循环 import**。ESM 循环引用在"顶层不立即调用"时可工作，但脆弱（打包器/加载顺序敏感，且 cpd-state.js 已被 panel.js import，依赖图更绕）。决策 2"引擎不 import panel.js 内部"的措辞与 getter 方案自相矛盾。**改法（依赖注入，单向依赖）**：
```js
// cpd-guide.js —— 零 import panel.js
export function initCpdGuide({ getLastExit, isStreaming, getHasGuidance-targets }) { /* 存参，subscribe */ }
// panel.js —— 单向 import cpd-guide.js
initCpdGuide({ getLastExit: () => _history.at(-1)?.trace?.exit ?? null, isStreaming: () => _streaming });
```
panel.js→cpd-guide.js 单向，引擎对 panel.js 零 import，与决策 2 措辞自洽。§九 panel.js 行"导出末条 trace 只读 getter"改为"init 时注入 getter"。（DS 亦指 init 模块边界措辞——收敛信号；此为具体解法。）

**【新 L1】turnId 去重防御的场景基本不存在。** panel.js:1122 `if (!text || _streaming) return;`——流式中 send 直接被拒，"快速连续 send"在当前代码下不可能；abort 后 exit=undefined 不 dispatch，正常串行轮次 turnId 单调。**去重无害但不必过度设计**；真正要补的一句：切会话/clearChat 后 `_history.length` 回退 → expectedTurnId 链断裂，**init 恢复时必须重置 expectedTurnId**（plan 未写）。一句话补进 §4.3。

## 二、功能图谱与真值表覆盖

**结论：真值表首匹逻辑自洽（streaming=false 是每个引导行的必要条件，表格本身无洞）；但两个组合未标注、优先级文字与表格矛盾。**

**【新 M2】`hasRange=false + lastExit=result` 组合落行 2（range），"深读/定位/导出"CTA 永缺席。** harness 允许无 range 直接问（默认全市范围），用户没框选也拿到 result 时，表上首匹行 2「聚焦一片城区」——S4·result 的三个 CTA 永远轮不到。叙事上"先全市后聚焦"说得通，但**刚出结论就没有深读/导出入口，演示高潮断档**。改法：行 2 细分——`hasRange=false ∧ lastExit=result` 时 range 引导**兼带**深读/导出次 CTA（与行 5 共用 CTA 组），或表下加一行注释标注此组合的有意归属。**同样 `hasRange=false + general` 落行 2**：概念问答后推"框选范围"，与行 1 概念问答后推 import 同理可接受，但都应标注。

**【新 M3】§4.2 优先级文字与表格矛盾（实现者必踩）。** 规则写"hasImport=false 优先一切 → streaming=true"——若实现者按此写 if 链，则"无数据 + 流式中"会首匹 import（流式被打扰，直接违反流式硬门）。表格本身是对的（行 1 要求 streaming=false，行 9 通配 streaming=true → null），**文字顺序应改为「streaming=true 第一优先（不打扰）→ hasImport=false → lastExit∈{gap,partial,ask}→null → drift → 其余」**。一字之差，G1 实现时必踩。

**【新 L3】`hasImport=false ∧ visEmotion=true`（纯 AI 结果层、无导入数据）→ 行 1 文案"生成第一张情绪地图"错位。** 场景：用户删除导入数据但保留 AI 产出的 grid/聚合层（visible 非 group 非 range → visEmotion=true）。此时推"第一张地图"与界面上已有的分析结果矛盾。低概率但真实。改法：行 1 文案实现时对 `visEmotion=true` 分支降级为静态（"导入数据继续分析"）或表下注释。

**谓词与覆盖——其余核验通过。** hasImport 排除 AI 组/tool 产出（§4.1）与我首轮 M5 一致；hasVisibleEmotionLayer"非 group 非 range"与层模型（state.js:252/662）相容；gap/partial/ask→null 让 `_followUps` 接手、drift→retry 与 _followUps:465-469 同语义——职责切分干净，无双 CTA。

## 三、承重边界

**结论：继续清白。v0.3 §七的 curState 措辞修正经我独立复核属实且更精确。**

- curState 进 buildContext（tools.js:455-458 实证：`引导阶段：S0·开场（用户所处进度，仅供参考，不改变工具选型）`）——v0.2"不进 LLM context"措辞错误，v0.3 改"不参与 diagnose 路由裁定"**属实且措辞精确**。diagnose prompt 模板本身未动（注入的是运行时 context 而非模板文本），承重原意（保 eval）不破。✓
- turn-ended 只读、finally 守卫、不 import 闭包（H1 修复后彻底）——harness/stages/tools/diagnose/四态出口零触。✓
- 光环 theme-var 化列入 §七+§九，承重从"声明"落为"待办"。✓
- eval 安全性复核：`eval_template_flash.py` 只测 diagnose 路由不变；v0.3 新增灰度步骤（≥10 条 episodes.jsonl 对比 fail 率 >30% 调话术）把 U7 风险从"理论"降为"可测"。✓

## 四、演示表现力

**结论：S3 空间交互优先是本轮最有价值的转向（从"打字"到"点图"）；但 v0.3 新文案与线上新色带脱节（新 M1），S4 动态变量无源（新 H2）。方向 B+，落地细节待修。**

**S3「点击地图上深红/深绿的区域」——根本性的正确转向。** 它把引导从"功能教程"（点这个按钮）变为"诊断叙事"（点这块最扎眼的颜色），直接服务演示逻辑链的"引导点击突出要素"环节，对话降级为备选 CTA——主次正确。S4 地图定位 CTA 把"结论"闭合回"视野端"（§6.4），U6 的"为引导而引导"风险在**设计层面**已解除（待 G2 实现验证）。

**【新 M1】文案"深红/深绿"与线上色带脱节。** tokens.css:25-29 实证当前色板 = 连续发散带：veryPositive `#0F6E56`（深青绿）/ veryNegative `#D85A30`（深珊瑚橙）——**"深红"不存在于渲染端**（珊瑚橙≠红），用户按文案找"深红"找不到。演示逻辑链原文的"深红/深绿"是旧五色板（#78DC32/#B92D2D）语义，色带换血后文案未同步。改法：§4.2 文案列改"**深绿/深橙**"或色名中性化（"颜色最深的两端区域"）；并加一条文案铁律——**引导文案的色名必须取自 theme var 对应端点，色带再调整时文案只改一处**（可把色名放进 deriveGuidance 的常量，从 `--geojson-color-emotion-very-*` 派生显示名）。这是"视野-数据-结论同步"在文案层的体现：文案也属于"结论端"，必须与"视野端"渲染同色。

**【新 H2】S4 文案动态变量"主题倾向 X×Y，排序第 N"客户端无源。** 主题倾向（4×5 归因）与排序位次都不是确定性客户端信号——要么 LLM 产出（违背决策 1 纯客户端）、要么正则抠答案文本（§配套 B 用例 2 刚把"正则抠 domain_lens"列为反模式，plan 不可自叛）。改法：降级为**可得的确定性变量**——区域名（`_followUps`:455 region 抽取复用，plan §4.3 已声明复用）+ 极性（exit-badge 已有 ok/warn 态）：「**{区域名}的归因已就绪——深读 / 在地图定位 / 导出**」；或纯静态文案。X×Y/N 若未来想要，应由 harness 在 turn-ended 载荷里带（diagnose.card 有 domain/element 结构化字段），那是 harness 侧的**读取**而非改动，可留 G3 评估。（DS 亦指此——收敛信号。）

**叙事化文案整体——合格。** 行 1-3（"生成第一张情绪地图"/"聚焦一片城区"/"看张力"）叙事到位；M1 修色名后文案层自洽。U6 收敛判断：**设计层面已闭环，实现验证留 G2/G4。**

## 五、分阶段合理

**结论：阶段切分保持健康，G1 调和方案（独立 ship + 光环可点）成立；P0 用例表述矛盾已修。**

- G1 调和（独立 ship + 光环 click 最小 CTA）消除了我与 DS 的分歧点——光环可点使 G1 从"会亮"变"会用"，独立 ship 价值完整。✓
- P0 地基行为用例（折叠欢迎卡/高度自适应/exit-badge/历史桶）全部可 Playwright 自动化（点击/量高/读 class），与 emc_helpers.py 基建匹配。✓
- turnId 断链重置（L1）、H1 依赖注入、M2 组合标注——建议全部列入 G1 动手前的 plan 文字修正（不单独占阶段）。

## 六、风险漏项（v0.3 新增项的风险复核）

**cpd:reset（新 L2）**：reset 仅清 lastExit + recompute → 真值表落行 4（analyze）。但"换范围"CTA 的用户意图是重新框选——引导落 analyze 与动作意图略错位。可接受（CTA 本身会开 range tab，drawer 动作即引导），建议 §4.3 补一句"reset 后若 range drawer 开启中，引导可短暂 null（用户忙，U8 同源逻辑）"。

**U8 用户忙检测（新 L4）**：方向 agree（与 engage 解除同哲学），但"3 秒"魔数无依据——dock 点击与"正在操作"的相关性窗口应取自会话遥测或干脆用"dock/param-panel is-open 状态"（确定性信号，cpd-state.js:60-63 已有 param-panel MutationObserver 可复用），比时间窗更稳。

**U9 engage 再亮**：维持"不打扰优先"，留观察——agree 此处置。

**U10 地图层引导浮层**：agree plan 的保守（浮层属另一子系统，需与 #ff9000 三端同步高亮体系统一设计，G1 不开新战线）。

---

## 分级建议清单（CB-CPD-02）

**高（G1 动手前必修，均为文档级）：**
- H1. init 恢复改**依赖注入**（panel.js→cpd-guide.js 单向 import；§4.3 与 §九"导出只读 getter"改写为"init 时注入 getter"）——消除循环 import。【维度一】
- H2. S4 文案动态变量降级：X×Y/N 无源 → 「{区域名}的归因已就绪」（复用 `_followUps`:455 抽取）或静态；若要动态值，由 turn-ended 载荷从 diagnose.card 结构字段带（读取非改 harness），留 G3。【维度四】

**中（G1/G2 携带）：**
- M1. 文案色名同步线上色带："深红/深绿"→"深绿/深橙"（或色名中性化）；色名从 `--geojson-color-emotion-very-*` 派生，一处改全站随。【维度四】
- M2. 真值表标注 `hasRange=false + result` 组合归属（range 引导兼带深读/导出次 CTA）。【维度二】
- M3. §4.2 优先级文字改为 streaming 第一优先（与表格语义对齐）。【维度二】

**低（抛光/实现注释级）：**
- L1. §4.3 补"init 恢复时重置 expectedTurnId"（切会话 _history.length 回退断链）。【维度六】
- L2. cpd:reset 后 range drawer 开启中引导短暂 null（U8 同源）。【维度六】
- L3. 纯 AI 层场景（hasImport=false ∧ visEmotion=true）行 1 文案降级或注释。【维度二】
- L4. U8 忙检测弃"3 秒"魔数，改 dock/param-panel is-open 确定性信号（复用 cpd-state.js:60-63 observer）。【维度六】
- L5. §六补"引导态不持久化"明文（L4 首轮残留）。【维度六】

---

## U 系列未决项立场（CB-CPD-02 轮）

| 项 | 立场 | 备注 |
|---|---|---|
| U1-U7 | **收敛确认** | 上轮立场全部成立，v0.3 落实无误；U6 设计层面闭环（实现验证留 G2/G4） |
| U8 用户忙检测 | **agree 方向，改确定性信号** | 弃时间窗魔数，用 is-open 状态（L4） |
| U9 engage 再亮 | **agree 留观察** | 不打扰优先正确，G4 遥测后再定 |
| U10 地图浮层 | **agree 保守** | 与 #ff9000 三端同步统一设计时再动，G1 不开战线 |

---

## 结论

**v0.3 = 可进 P0（与 DS 收敛），G1 动手前修 H1/H2 + M1-M3（全文档级，预计一次 commit 量）。** CB-CPD-01 闭环质量优秀（15/15 执行，2 处修法超建议）；本轮 5 个新发现中 2 个与 DS 独立收敛（init 模块边界 / S4 动态变量）——收敛点即高置信点，建议项目方优先处理。

**综合评级**：架构 A- / 功能 B+ / 承重 A / 演示表现力 B / 分阶段 B+ / 风险 B+ → **B+**（v0.2 轮我未给字母级，本轮起给；与 DS B+ 独立收敛）。
