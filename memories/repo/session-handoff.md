# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月22日（**CPD 核心 plan 初稿 v0.1 + CB 评价专轨搭建完毕；凌晨收工，待换环境跑 CB-CPD-01 第三方首评**）| 分支 `cpd`

---

## 当前节点：CPD 核心 plan 初稿就绪 + 多轮评价机制（复用 CB）搭好；下一步 = 第三方首评

### 本会话做了什么（分支 cpd）
开 **CPD 核心引导逻辑** 详细 plan（进 plan 模式，自读自规划，未派 subagent——承重）。产出三件套：

1. **`docs/cpd-core-plan.md`**（v0.1 初稿，被评 artifact）——EMC 从被动反映升主动编排的完整设计：
   - 核心 = 新增确定性引导引擎 `cpd-guide.js`：`deriveGuidance()` 从 curState + 特征存在性(hasImport/hasRange/hasAnalysis) + 上轮 exit 算出"此刻唯一动作"。
   - **两路径分工**：主动引导（新·UI nudge）/ 对话分析（harness **原样不动**）；唯一接缝 = `cpd:turn-ended {exit}` 客户端事件（panel.js send() 末尾 dispatch）作结论回灌。
   - 覆盖：功能图谱（逐项标 已由EMC引导/裸按钮/待编排）/ 状态机 S0-S4 映射 / 对话→功能桥 / 渐进披露细则（.has-guidance 耦合 + engage 解除）/ 承重边界 / 分阶段 G1-G4 / 关键文件 / 验证。
2. **`docs/cpd-core-plan-review.md`**（评价专轨指南）——**复用项目 Catch-Ball 闭环**（不另造）：被评 artifact = cpd-core-plan.md；协议走 `docs/catch-ball/RULES.md`（反评价标尺 agree/disagree/partial + 承重红线）；第三方评价存 `docs/catch-ball/SCAN_CPDPlan_{NN}.md`；反评价 append `docs/catch-ball/cb-journal.md` `## CB-CPD-{N}` 章。含评价 prompt 模板 + plan 专项六维 + 未决项 U1-U5。
3. plan 副本亦存 `~/.claude/plans/cpd-cpd-ui-graceful-lake.md`（plan 模式产物）；repo 内 `docs/cpd-core-plan.md` 为权威。

### 关键设计决策（plan §二）
- **引导 = 纯客户端确定性引擎，不进 LLM**（保 diagnose eval + 四态出口不动）。
- **两路径 clean 分工**：引导是 UI nudge（非对话消息）；对话走 harness 不改。
- **软折叠基调**（非严格隐身，chip 始终可达）。

### 下一步（换环境，9 点后）
1. **跑 CB-CPD-01 第三方首评**：用 `docs/cpd-core-plan-review.md` §五 prompt 模板 + cpd-core-plan.md 全文喂第三方大模型（DeepSeek/ChatGPT/Gemini）。
2. 第三方评价存 `docs/catch-ball/SCAN_CPDPlan_01.md`（只读）。
3. 主线程按 CB RULES §3 反评价（agree/disagree/partial，撞红线 disagree）→ 修订 plan（bump v0.x）→ append `cb-journal.md` `## CB-CPD-01`。
4. 连续 2 轮无新实质分歧 → plan 定稿 v1.0 → 进 **Phase G1**（建 cpd-guide.js + 折叠态耦合，删 Ctrl+Shift+G 测试）。
5. 新会话 prompt 见下方。

### 承重（必守）
- **调用次数优先**（全局唯一权威）：默认主线程 + 会话切分首选 + subagent 仅大宗隔离。**不派 Explore/Plan subagent**（直接自己读/grep/规划，覆盖 plan mode 默认）。
- **diagnose prompt 永不动**（保 eval）→ curState/引导纯客户端推导；四态出口(EXIT_RESULT/GAP/PARTIAL/CONCEPT)/tracker 签名/网格算法/paint-inplace 不动。
- **CPD plan 评价走 CB**（用户定）：复用 RULES/cb-journal/KNOWLEDGE，不另造框架。
- **EMC 颜色全走 theme var**，严禁硬编码 hex/rgba（memory `apply-design-sense-no-bounce` §5）。
- **自适应位置铁律**：浮层 left 随锚点动态算（memory `adaptive-position-design-rule`）。
- **设计决策先自判别甩用户**（memory `apply-design-sense-no-bounce`）。
- 批4 grid 镜像 bug + diag 日志(b13eb62)→ main 遗留，CPD 期间不动。
- 只 commit 不 push（用户手动 push）；**本次收工例外已 push**。

### 关键文件
- **`docs/cpd-core-plan.md`**（CPD 核心 plan v0.1，被评 artifact，权威）
- **`docs/cpd-core-plan-review.md`**（CB 评价专轨指南 + prompt 模板 + 未决项）
- `docs/catch-ball/RULES.md` / `cb-journal.md` / `KNOWLEDGE.md`（CB 机制，复用）
- `docs/design-system.md` §4（CPD 状态机 S0-S5 single source of truth）
- `frontend/js/ai_qa/cpd-state.js`（curState 推导 + 自适应位置）
- `frontend/js/ai_qa/harness.js`（五步+四态出口——**不动**）
- `frontend/js/ai_qa/panel.js`（_setupCpdBar + _fitCollapsedText + .has-guidance 钩子，G1 改）
- `frontend/js/sidebar.js`（cpd:focus-tab 抽屉桥，G2 复用）

---

## 新会话 prompt（CPD 核心 plan 第三方评价，复制即用）

```
接续 cpd 分支 CPD 核心引导 plan 的多轮第三方评价（Catch-Ball 专轨）。
读：docs/cpd-core-plan.md（初稿 v0.1，被评 artifact）+ docs/cpd-core-plan-review.md（CB 评价专轨指南 + prompt 模板 + 未决项）+ docs/catch-ball/RULES.md（CB 协议权威）。
我会把第三方大模型的评价贴给你（或存成 docs/catch-ball/SCAN_CPDPlan_01.md）→ 你按 review.md §三 + RULES §3 反评价（agree/disagree/partial，撞承重红线 disagree，不派 subagent）→ 修订 plan(bump v0.x) → append docs/catch-ball/cb-journal.md `## CB-CPD-01` 四节。
承重：调用次数优先 / 不派 subagent / 只 commit 不 push / diagnose 与四态出口不动。
```
