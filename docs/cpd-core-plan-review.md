# CPD 核心引导 Plan · Catch-Ball 评价专轨（v2）

> **机制 = 复用项目 Catch-Ball 闭环**（不另造）。被评 artifact = [docs/cpd-core-plan.md](cpd-core-plan.md)；协议权威 = [docs/catch-ball/RULES.md](catch-ball/RULES.md)；承重红线 = [docs/catch-ball/KNOWLEDGE.md](catch-ball/KNOWLEDGE.md) §1（diagnose 永不动 / 四态出口 / tracker 连续 = 正好覆盖 CPD 承重）。
>
> **v2 变更（2026-07-22）**：对齐 CB 机制优化——
> - RULES §2.1 六轴 → **七轴**，新增「演示表现力」10%（对齐 CLAUDE.md「演示逻辑链」北极星）；
> - KNOWLEDGE §2 语境卡片补"演示逻辑链是项目北极星"，防未来 SCAN 用纯工程标尺低估 UI 债；
> - 本专轨 §四 plan 专项维度同步：原「UX 一致性」**升格**为「演示表现力」（含演示逻辑链落地度对齐）。
>
> 当前：**Round 0 初稿已建**（cpd-core-plan.md v0.1），待 CB-CPD-01 第三方首评。

---

## 一、为什么复用 CB（不另造框架）

项目已有成熟的 Catch-Ball 多轮第三方评价闭环（revision-log：CB-01/02/03 跑过，DeepSeek 扫描 + Claude 反评价）。其核心设施完全适配 plan 评价：
- **反评价标尺**（RULES §3.2）：`agree / disagree / partial`——逐条据证据，不表演性同意。
- **承重红线**（RULES §3.3 + KNOWLEDGE §1）：diagnose 永不动 / 四态出口契约 / tracker 编号连续——**正是 CPD 不可碰的边界**，第三方评价撞这些 = 自动 `disagree`。
- **四节 journal**（RULES §4.2）：① SCAN 摘要 ② 反评价 ③ 行动 ④ 状态/新发现。
- **双模型闭环**（RULES §1.4）：SCAN → 反评价+行动 → 下一轮 SCAN 对比验证。
- **七轴评分**（RULES §2.1 v2）：含「演示表现力」——CPD 作为引导/UX 强化方案，正是该轴的主战场。

→ plan 评价只是"被评对象从【整个项目】收窄到【一份 plan 文档】"，机制原样复用。

---

## 二、本专轨相对 CB 主轨的差异（仅这几点）

| 项 | CB 主轨（whole-project） | CPD plan 专轨（本） |
|---|---|---|
| 被评 artifact | 整个项目代码/文档 | `docs/cpd-core-plan.md` 单文档 |
| 第三方评价文件名 | `SCAN_DeepSeek_{NN}.md`（已到 03） | `SCAN_CPDPlan_{NN}-{model}.md`（新系列，从 01 起；{model}=模型短名 deepseek/k3/gemini 等，同轮多模型不冲突） |
| journal 章节 | `## CB-01/02/03` | `## CB-CPD-01/02/…`（同文件 [cb-journal.md](catch-ball/cb-journal.md) 追加） |
| 评价维度 | RULES §2.1 七轴评分（架构/代码/测试/Harness/文档/调用/**演示表现力**） | 见 §四（plan 专项六维，维度 4 = 演示表现力，对齐第七轴） |
| 协议/标尺/红线/权限 | RULES 原样 | **RULES 原样**（不改 RULES） |

> 不新建 journal 文件——CPD plan 反评价直接 append 到 `docs/catch-ball/cb-journal.md`（`## CB-CPD-{N}` 章），与主轨共存、互不干扰（章名前缀区分）。

---

## 三、每轮怎么跑（映射 RULES §3 流程）

1. **取材**：`docs/cpd-core-plan.md` 当前版 + 上轮 `## CB-CPD-(N-1)` 遗留未决项。
2. **喂第三方**：§五 prompt 模板（自包含 CB 协议/纪律/本轮/语境）+ 【必读文件】路径清单（模型有文件权则自读）**或** plan 全文（无文件权则粘贴）→ 第三方大模型（DeepSeek/K3/Gemini 等）。
3. **第三方产出** → 存 `docs/catch-ball/SCAN_CPDPlan_{NN}-{model}.md`（{model}=模型短名；同轮喂多模型各存一份不混淆；只读不覆写；首章回顾上轮建议执行——RULES §1.4）。
4. **主线程反评价**（主线程跑，不派 subagent——承重）：逐条 `agree/disagree/partial` + 证据 + 采纳动作；撞承重红线一律 `disagree`（RULES §3.3）。
5. **修订 plan**：更新 `cpd-core-plan.md`（bump v0.x），diff 记 journal。
6. **append journal**：`docs/catch-ball/cb-journal.md` 加 `## CB-CPD-{N}` 四节。
7. **收敛**：连续 2 轮第三方无新实质分歧 → plan 定稿 v1.0 → 进 Phase G1。

> 触发：可走 `/cb` 命令（若 skill 支持指定 artifact），或手动——用户把第三方评价贴进对话 / 存成 SCAN_CPDPlan_{NN}.md 后，主线程按本节反评价。

---

## 四、plan 专项评价维度（v2 · 对齐 RULES 第七轴 + 演示逻辑链）

> 第三方按这六维评（每条：结论 + 理由 + 改法）；主线程反评价同维对照。
> **维度 4「演示表现力」= 本专轨核心增量**，直接对齐 CLAUDE.md「演示逻辑链」三环（表现力/有用性/交互）+ 视野-数据-结论同步性铁律，对应 RULES §2.1 第七轴。

| 维度 | 关键问 |
|---|---|
| **1 架构合理性** | 两路径（主动引导 vs 对话分析）分工是否干净？唯一接缝 `cpd:turn-ended` 是否真零侵入 harness？`deriveGuidance` 确定性派生有无漏态/竞态？ |
| **2 功能图谱完备** | 是否漏情绪地图某项能力？状态→动作映射漏信号（ask 出口 / 空 import 有 range / 多轮续作）？ |
| **3 承重边界** | 设计有无"暗渡陈仓"实际触碰不可改部分（读 exit 是否隐含改 harness）？→ 撞红线 = disagree |
| **4 演示表现力**（核心·对齐第七轴） | 引导是否服务演示链 `张力图面→引导点击→交互分析→定位关注区+主题倾向+排序优先级`？折叠态光环/文案与展开态 banner 是否**一套设计语言**（软折叠基调 + theme var + 自适应位置）？引导 nudge 是否**增强**"突出要素可见性"与"视野-数据-结论同步"，而非打断演示节奏或沦为装饰？CPD 把 curState 从"反映"升"编排"，是否真正提升了演示张力与宏观诊断信号的有用性？ |
| **5 分阶段合理** | G1 是否真能独立 ship 闭环？阶段切分有无依赖倒置？ |
| **6 风险漏项** | 状态回退 / 引导 vs 追问胶囊打架 / 流式中误推 / localStorage 脏态 / engage 解除时机 |

> **v1→v2 维度演进**：v1 六维中的「UX 一致性」并入 v2 维度 4「演示表现力」并**升格**（从"配色/间距一致性"扩展到"演示逻辑链落地度 + 设计语言 + 同步性"），对齐 RULES 第七轴。其余五维保留。

---

## 五、评价 prompt 模板（喂第三方大模型）

> **两种喂法**：① 模型有项目文件访问权（**推荐**）→ 喂 prompt + 【必读文件】路径清单，模型自读（能引文件/行号，评价更准、省粘贴）；② 无文件权 → 喂 prompt + 手动粘贴 `docs/cpd-core-plan.md` 全文（prompt 已自包含 CB 协议/纪律/本轮/语境，无需另传 RULES/KNOWLEDGE）。**每轮喂前更新【本轮轮次】块**（轮次号 / v0.x 变更 / 未决项当前态）。

```
你是 Catch-Ball（CB）第三方**中立**评测方（资深前端架构师 + 产品设计师 + 信息可视化专家），评审一份 CPD 核心 plan。

【CB 协议 · 你的角色与纪律】
项目方用"多轮第三方评测 + 项目方反评价"闭环迭代改进 plan。你是中立、证据驱动的批评者：
- 不背书、不辩护、不客套；每条判断附具体理由 + 可执行改法（尽量引 plan 章节/文件行）。
- 建设性：发现问题必带改进建议，按影响分高/中/低优先级。
- 承重红线：下列【不可违背】部分若被建议触碰，项目方会 disagree（拒）——别浪费篇幅建议改承重，聚焦承重之外的改进。
- 站在【架构合理性 + 演示表现力 + 工程承重】三角评价；演示表现力与架构/代码同等承重（项目北极星），勿当装饰、勿用纯工程标尺盲视 UI 债。

【必读文件】（若有项目文件访问权，优先自读——能引文件/行号、评价更准；若无访问权跳过本块，由用户粘贴 plan 全文）
- docs/cpd-core-plan.md（被评 plan v0.2 全文）
- docs/cpd-core-plan-review.md（本专轨规则：维度/承重/未决项）+ docs/catch-ball/{RULES.md,KNOWLEDGE.md}（CB 协议/红线/语境）
- CLAUDE.md（产品本质/演示逻辑链/承重铁律）
- 承重实证（按需深读）：ai_qa/review.py（scale_paradigm_fit 现状·§配套 A 落点）/ frontend/js/ai_qa/{panel.js,cpd-state.js,harness.js,tools.js}（引导落点·四态出口·微观工具 nearest/buffer/inspect_zone）
- 测试现状（§配套 B）：docs/emc-test-cases.md / tests/browser/

【本轮轮次】CB-CPD-01（首评）。被评 = docs/cpd-core-plan.md **v0.2**（单份 plan 文档，非整个项目）。
v0.2 相对 v0.1 新增：① 决策 4 + §配套 A「尺度诚实」（落 review.py scale_paradigm_fit，要求微观精确问题声明"宏观方向非精确测量"+ 给替代趋势）；② §配套 B「测试加固」P0 最高优（扩 emc-test-cases + tests/browser）；③ §八优先级重排（P0 测试 / P1 尺度 / P2 引导引擎 G1-G4）。
未决项（收敛参考，非必答）：U1 引导=UI nudge 非对话消息 / U2 MVP 分阶段 / U3 ask 出口引导 / U4 timeline·compare·search 编排深度 / U5 banner vs 欢迎卡 / U6 引导是否真服务演示逻辑链 / U7 尺度诚实话术分寸。

【项目语境】（文档推断不出的运行时事实，勿基于理论模型误判）
- 不派 subagent（用户全局铁律）：plan 里 Agent/SOP 是概念框架非运行时；调用次数优化靠"会话切分+精准读"，非 SOP spawn 合并。
- 前端 JS 零单测 = 项目自认**唯一真短板**（非数据、非架构）；§配套 B 测试加固即针对此。
- 演示逻辑链 = 北极星（见下），UI/UX 与架构/代码同等承重。

【产品背景】
- "情绪地图"= 城市情绪空间分析平台（MapLibre GL JS 前端）。EMC = EmotionMap Copilot，AI 问答浮窗，已是分析主控。
- CPD 理念（设计系统 §4）："此时此刻需要什么 = 出现对应提示"，EMC 按任务进度奉上"恰好那一个动作"。
- 六步状态机：S0 开场 → S1 选范围 → S2 载图层 → S3 跑分析 → S4 读结论 → S5 收尾。

【演示逻辑链 = 项目北极星（评价须覆盖其落地度）】
张力图面（深红/深绿、对称拉伸、色带、密度对比）→ 引导点击突出要素 → 交互分析张力原因
→ 定位关注区 + 主题倾向 + 排序优先级（宏观诊断信号，非精确微观识别）。
三环：表现力环（张力图面）/ 有用性环（宏观定位+排序）/ 交互环（点击→分析→归因）。
铁律：视野(地图) ↔ 数据(Overview) ↔ 结论(归因) 三端 hover/click 即时同步高亮（橙色 #ff9000）。

【不可违背的工程承重（违背=硬伤）】
- diagnose prompt 永不能改（保 LLM eval）；四态出口(EXIT_RESULT/GAP/PARTIAL/CONCEPT+ask) 不能改；harness.js/stages.js/tools.js 不能改。
- curState 必须纯客户端推导（不进 LLM context）。
- EMC 颜色必须走 CSS theme var，禁硬编码 hex/rgba。
- 浮层位置必须随锚点自适应，禁写死 left。
- 基调"软折叠"（控件始终可达，非严格隐身）。

【被评 plan】docs/cpd-core-plan.md v0.2 —— 有文件权请自读（见上【必读文件】）；无文件权则由用户粘贴全文于下：
<若需粘贴，贴此处>

【请按六维评价，每条给：结论 + 具体理由 + (若不认同)改法】
1. 架构合理性：两路径分工是否干净？cpd:turn-ended 接缝是否真零侵入？deriveGuidance 有无漏态/竞态？
2. 功能图谱完备：漏了某项能力？状态→动作漏信号(ask 出口/空import有range/续作)？
3. 承重边界：有无暗触不可改部分(读 exit 是否隐含改 harness)？
4. 演示表现力（重点）：引导是否服务演示逻辑链（张力→点击→分析→宏观诊断）？折叠/展开是否一套设计语言
   （软折叠+theme var+自适应位置）？nudge 增强"突出要素可见性"与"视野-数据-结论同步"，还是打断节奏/沦为装饰？
   curState 从"反映"升"编排"是否真提升演示张力与宏观诊断有用性？
5. 分阶段合理：G1 真能独立 ship？阶段依赖倒置？
6. 风险漏项：状态回退/引导 vs 追问胶囊打架/流式误推/localStorage 脏态？

【报告署名】报告**首行**写"模型：{你的模型短名}"（如 deepseek / k3 / gemini / chatgpt / qwen / doubao / glm）——同轮可能喂多个模型，署名便于区分（文件将存为 SCAN_CPDPlan_{NN}-{model}.md）。

直接给评价，不要客套。
```

---

## 六、未决项（跨轮追踪，初始 = plan §十一）

- [ ] U1 引导呈现 = UI nudge（非对话消息）是否认同？
- [ ] U2 MVP 先行(G1 独立 ship) vs 全量，分阶段是否合理？
- [ ] U3 S4·ask 出口引导引擎如何介入？
- [ ] U4 timeline/compare/search 编排深度是否漏？
- [ ] U5 banner 与空态欢迎卡 融合 vs 并存？
- [ ] U6（v2 新增）CPD 引导是否真服务演示逻辑链、增强宏观诊断有用性，而非"为引导而引导"的装饰？

---

## 七、轮次状态

- **CB-CPD-00 · 2026-07-22 凌晨**：初稿 v0.1 建（cpd-core-plan.md）+ 专轨 v1 建（复用 CB）。⏳ 待第三方首评。
- **CB-CPD-00b · 2026-07-22**：CB 机制优化——RULES §2.1 六轴→七轴（加「演示表现力」10%）、§2.3 八维→九维；KNOWLEDGE §2 补"演示逻辑链北极星"语境；**本专轨升 v2**（维度 4 升格演示表现力 + U6）。机制层动作，不动 plan 正文。
- **CB-CPD-00c · 2026-07-22**：cpd-core-plan.md v0.1 → **v0.2**——吸收两条 EMC 思路建议（① 决策 4 + §配套 A「尺度诚实」落 `review.py` `scale_paradigm_fit` desc；② §配套 B「测试加固」P0 最高优 + §八优先级重排 P0 测试 / P1 尺度 / P2 引擎）；加 U7（尺度诚实话术分寸）。**v0.2 作为 CB-CPD-01 被评 artifact 就绪**，待第三方首评。
- **CB-CPD-01 · 2026-07-22**：DeepSeek + K3 双模型首评 v0.2。反评价 26 条（agree 20 / partial 6 / disagree 0，4 承重证据 grep/read 核实）→ plan v0.2→**v0.3**（九点修订：§4.1 信号修正 / §4.2 特征向量真值表 / §4.3 调度强化 / §七 curState 措辞 / §九 光环 theme-var / §八 分阶段修正 / §配套A 灰度+U7 三态 / §六 6.4 演示链 / U8-U10）。正文见 [cb-journal.md](catch-ball/cb-journal.md) `## CB-CPD-01`。待 CB-CPD-02 验证修订落地 + 演示表现力升维。

> 轮次反评价正文落 [cb-journal.md](catch-ball/cb-journal.md) `## CB-CPD-{N}` 章（不在此文件重复），本文件只作专轨指南 + 未决项索引。
