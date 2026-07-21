# CPD 核心引导 Plan · Catch-Ball 评价专轨

> **机制 = 复用项目 Catch-Ball 闭环**（不另造）。被评 artifact = [docs/cpd-core-plan.md](cpd-core-plan.md)；协议权威 = [docs/catch-ball/RULES.md](catch-ball/RULES.md)；承重红线 = [docs/catch-ball/KNOWLEDGE.md](catch-ball/KNOWLEDGE.md) §1（diagnose 永不动 / 四态出口 / tracker 连续 = 正好覆盖 CPD 承重）。
> 当前：**Round 0 初稿已建**（cpd-core-plan.md v0.1），待 CB-CPD-01 第三方首评。2026-07-22 凌晨收工，换环境后续。

---

## 一、为什么复用 CB（不另造框架）

项目已有成熟的 Catch-Ball 多轮第三方评价闭环（revision-log：CB-01/02/03 跑过，DeepSeek 扫描 + Claude 反评价）。其核心设施完全适配 plan 评价：
- **反评价标尺**（RULES §3.2）：`agree / disagree / partial`——逐条据证据，不表演性同意。
- **承重红线**（RULES §3.3 + KNOWLEDGE §1）：diagnose 永不动 / 四态出口契约 / tracker 编号连续——**正是 CPD 不可碰的边界**，第三方评价撞这些 = 自动 `disagree`。
- **四节 journal**（RULES §4.2）：① SCAN 摘要 ② 反评价 ③ 行动 ④ 状态/新发现。
- **双模型闭环**（RULES §1.4）：SCAN → 反评价+行动 → 下一轮 SCAN 对比验证。

→ plan 评价只是"被评对象从【整个项目】收窄到【一份 plan 文档】"，机制原样复用。

---

## 二、本专轨相对 CB 主轨的差异（仅这几点）

| 项 | CB 主轨（whole-project） | CPD plan 专轨（本） |
|---|---|---|
| 被评 artifact | 整个项目代码/文档 | `docs/cpd-core-plan.md` 单文档 |
| 第三方评价文件名 | `SCAN_DeepSeek_{NN}.md`（已到 03） | `SCAN_CPDPlan_{NN}.md`（新系列，从 01 起） |
| journal 章节 | `## CB-01/02/03` | `## CB-CPD-01/02/…`（同文件 [cb-journal.md](catch-ball/cb-journal.md) 追加） |
| 评价维度 | RULES §2 六轴评分（架构/代码/测试/Harness/文档/调用） | 见 §四（plan 专项六维，不套代码六轴） |
| 协议/标尺/红线/权限 | RULES 原样 | **RULES 原样**（不改 RULES） |

> 不新建 journal 文件——CPD plan 反评价直接 append 到 `docs/catch-ball/cb-journal.md`（`## CB-CPD-{N}` 章），与主轨共存、互不干扰（章名前缀区分）。

---

## 三、每轮怎么跑（映射 RULES §3 流程）

1. **取材**：`docs/cpd-core-plan.md` 当前版 + 上轮 `## CB-CPD-(N-1)` 遗留未决项。
2. **喂第三方**：§五评价 prompt 模板 + plan 全文 → 第三方大模型（DeepSeek/ChatGPT/Gemini 等）。
3. **第三方产出** → 存 `docs/catch-ball/SCAN_CPDPlan_{NN}.md`（只读，不覆写；首章回顾上轮建议执行——RULES §1.4）。
4. **主线程反评价**（主线程跑，不派 subagent——承重）：逐条 `agree/disagree/partial` + 证据 + 采纳动作；撞承重红线一律 `disagree`（RULES §3.3）。
5. **修订 plan**：更新 `cpd-core-plan.md`（bump v0.x），diff 记 journal。
6. **append journal**：`docs/catch-ball/cb-journal.md` 加 `## CB-CPD-{N}` 四节。
7. **收敛**：连续 2 轮第三方无新实质分歧 → plan 定稿 v1.0 → 进 Phase G1。

> 触发：可走 `/cb` 命令（若 skill 支持指定 artifact），或手动——用户把第三方评价贴进对话 / 存成 SCAN_CPDPlan_{NN}.md 后，主线程按本节反评价。

---

## 四、plan 专项评价维度（替代 RULES §2 六轴）

> 第三方按这六维评（每条：结论 + 理由 + 改法）；主线程反评价同维对照。

| 维度 | 关键问 |
|---|---|
| **架构合理性** | 两路径（主动引导 vs 对话分析）分工是否干净？唯一接缝 `cpd:turn-ended` 是否真零侵入 harness？`deriveGuidance` 确定性派生有无漏态/竞态？ |
| **功能图谱完备** | 是否漏情绪地图某项能力？状态→动作映射漏信号（ask 出口 / 空 import 有 range / 多轮续作）？ |
| **承重边界** | 设计有无"暗渡陈仓"实际触碰不可改部分（读 exit 是否隐含改 harness）？→ 撞红线 = disagree |
| **UX 一致性** | 符合软折叠基调 + theme var + 自适应位置？折叠态光环/文案与展开态 banner 是否一套设计语言？ |
| **分阶段合理** | G1 是否真能独立 ship 闭环？阶段切分有无依赖倒置？ |
| **风险漏项** | 状态回退 / 引导 vs 追问胶囊打架 / 流式中误推 / localStorage 脏态 / engage 解除时机 |

---

## 五、评价 prompt 模板（喂第三方大模型）

> 复制下框 + `docs/cpd-core-plan.md` 全文，粘贴给第三方。

```
你是资深前端架构师 + 产品设计师，评审一份"情境式渐进披露(CPD)"核心引导逻辑的实施计划。请站在【架构合理性 + 产品体验 + 工程承重】三角给严苛、具体的评价。

【产品背景】
- "情绪地图"= 城市情绪空间分析平台（MapLibre GL JS 前端）。EMC = EmotionMap Copilot，AI 问答浮窗，已是分析主控。
- CPD 理念（设计系统 §4）："此时此刻需要什么 = 出现对应提示"，EMC 按任务进度奉上"恰好那一个动作"。
- 六步状态机：S0 开场 → S1 选范围 → S2 载图层 → S3 跑分析 → S4 读结论 → S5 收尾。

【不可违背的工程承重（违背=硬伤）】
- diagnose prompt 永不能改（保 LLM eval）；四态出口(EXIT_RESULT/GAP/PARTIAL/CONCEPT+ask) 不能改；harness.js/stages.js/tools.js 不能改。
- curState 必须纯客户端推导（不进 LLM context）。
- EMC 颜色必须走 CSS theme var，禁硬编码 hex/rgba。
- 浮层位置必须随锚点自适应，禁写死 left。
- 基调"软折叠"（控件始终可达，非严格隐身）。

【计划全文】
<粘贴 docs/cpd-core-plan.md 全文>

【请按六维评价，每条给：结论 + 具体理由 + (若不认同)改法】
1. 架构合理性：两路径分工是否干净？cpd:turn-ended 接缝是否真零侵入？deriveGuidance 有无漏态/竞态？
2. 功能图谱完备：漏了某项能力？状态→动作漏信号(ask 出口/空import有range/续作)？
3. 承重边界：有无暗触不可改部分(读 exit 是否隐含改 harness)？
4. UX 一致性：软折叠基调 + theme var + 自适应位置？折叠/展开一套设计语言？
5. 分阶段合理：G1 真能独立 ship？阶段依赖倒置？
6. 风险漏项：状态回退/引导 vs 追问胶囊打架/流式误推/localStorage 脏态？

直接给评价，不要客套。
```

---

## 六、未决项（跨轮追踪，初始 = plan §十一）

- [ ] U1 引导呈现 = UI nudge（非对话消息）是否认同？
- [ ] U2 MVP 先行(G1 独立 ship) vs 全量，分阶段是否合理？
- [ ] U3 S4·ask 出口引导引擎如何介入？
- [ ] U4 timeline/compare/search 编排深度是否漏？
- [ ] U5 banner 与空态欢迎卡 融合 vs 并存？

---

## 七、轮次状态

- **CB-CPD-00 · 2026-07-22 凌晨**：初稿 v0.1 建（cpd-core-plan.md）+ 本专轨指南建（复用 CB）。⏳ 待第三方首评（CB-CPD-01）。

> 轮次反评价正文落 [cb-journal.md](catch-ball/cb-journal.md) `## CB-CPD-{N}` 章（不在此文件重复），本文件只作专轨指南 + 未决项索引。
