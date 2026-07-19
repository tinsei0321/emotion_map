## CB-03 实施方案

### 背景

CB-02 已于 2026-07-19 完成 counter-evaluation（status: closed）。10 建议中 5 agree 已执行 / 3 defer / 1 partial / 1 declined。CB-02→CB-03 之间的 2 个 commit（`87979cc` + `6bdc9ac`）全部是 CB 自动化基础设施 + CB-02 counter-evaluation 内容。**项目代码（core/api/ai_qa/frontend）零变化**。

本轮的独特角度：CB-03 是首次评估 **CB 流程本身**——项目方将 catch-ball 从一个"手动第三方扫描→手动反评价"的 ad-hoc 流程，升级为带自动化命令、知识库、hook 检测的系统化工程实践。

### 步骤 1：验证 CB-02 行动 + 读取新增内容（已完成）

- ✅ 全部 6 项 CB-02 agree 行动已验证
- ✅ CB 自动化基础设施（5 组件）已完整读取
- ✅ KNOWLEDGE.md（5 章节）内容已掌握
- ✅ 项目代码零变化已确认

### 步骤 2：生成 CB-03 报告 `docs/catch-ball/SCAN_DeepSeek_03.md`

**报告结构（5 部分，继承模板 + 本轮特殊焦点）：**

#### 第〇部分：CB-02 回顾与执行评估

- **CB-02 10 条建议执行状态表**（逐条 → 结果 → 第三方核实）
- **CB-02 反评价质量评估**：
  - agree 5 项：全部核实通过，执行完整
  - partial 2 项：generate_test_data 保留理由充分（L0 raw 全管线 ≠ L1/L2 demo），trace-digest cursor 不存在→诊断 defer 合理
  - defer 3 项：geo_registry 埋点 / doc Streamlit 清理 / dev-notes 更新——均合理 defer（非紧迫）
  - decline 1 项：panel.js 拆分——合理 defer（JS 单测更高优）
- **CB-02 讨论点执行**：
  - 概念框架声明 → ✅ 已加入 AGENTS.md
  - topo_scanner 扩展 → 📋 远期，不行动
  - E2E 策略 B 优先 → 📋 对齐已有计划
  - 双模型闭环改进 → ⬜ RULES v2 待 CB-03 后更新
- **CB-02 遗漏补充**：CB-02 未涉及 KNOWLEDGE.md（当时不存在）
- **关键变化摘要**：CB 自动化 5 组件建立 + 项目代码零变化

#### 第一部分：扫描内容

- 精简扫描范围表（本回合重点：CB 自动化基础设施 + defer 项状态 + 文档体系）
- 扫描深度：L1（CB 自动化全部文件 + KNOWLEDGE.md）/ L2（defer 相关模块：geo_registry, docs）/ L3（其余）

#### 第二部分：扫描结果/评价

**本回合特殊处理**：由于项目代码零变化，8 个常规子维度简化为快速复核 + 新增专项评估：

| 子维度 | 处理方式 |
|--------|---------|
| Vibe Coding 策略 | 快速复核 + 概念框架声明的效果评估 |
| Harness 框架 | **重点**：CB 自动化作为 Harness 新组件评估（/cb command + hook detector + KNOWLEDGE.md） |
| Agent 体系 | 快速复核（无变化） |
| Skills 体系 | 快速复核（无变化） |
| 架构设计 | **重点**：CB 自动化在项目架构中的定位——是过度工程化还是合理的质量基础设施？KNOWLEDGE.md 作为"自文档化"架构的案例 |
| 代码质量 | **重点**：CB 自动化代码本身的质量评估（/cb command 设计、hook 集成方式、KNOWLEDGE 组织） |
| 推进情况 | **重点**：defer 5 项的状态更新 + 项目从"功能开发"转入"质量巩固"阶段的信号 |
| 调用消耗 | 快速复核（无变化） |

**评分**：沿用 CB-01/02 的 6 轴体系，但对每轴的趋势判断更侧重"质量体系建设"而非代码增长。

#### 第三部分：优化建议

**高优先级**（针对 CB 自动化本身）：
1. KNOWLEDGE.md 与 RULES.md 的内容边界——存在交叉（red lines、标尺纠正）。建议明确"RULES = CB 流程方法论 / KNOWLEDGE = 跨轮学习积累"
2. `/cb` command 的 step 4 "4 auto-checks" 硬编码了 4 个检查项，新增检查需改 code——建议改为可配置的检查清单

**中优先级**（defer 项重新评估）：
3. geo_registry 追踪埋点——CB-02 defer，建议在下一个开发周期纳入
4. 文档 Streamlit 过时内容——多个 doc 文件仍含过时内容

**低优先级**：
5. trace-digest cursor 诊断——hook 存在但 cursor 文件不存在
6. panel.js 拆分——技术债，低优先

#### 第四部分：讨论点

1. **CB 自动化的架构定位**：这究竟是"过度工程化"还是"合理的质量基础设施"？评估标准：ROI（投入 2 commits ~1,165 行 vs 节省的未来 CB 轮次效率）、可维护性（知识的可积累性）、团队规模适配（1 人项目是否需要这种级别的流程自动化？）

2. **KNOWLEDGE.md 的演进风险**：作为"跨轮学习积累"的载体，它是否会随着轮次增长而膨胀？CB-02 后已有 5 章节 ~71 行。预测 CB-10 时可能达 300+ 行。是否需要预设 pruning 策略？

3. **项目发展的阶段信号**：CB-01→CB-02→CB-03 三轮之间，项目代码（core/api/ai_qa/frontend）零净增长。这是"质量巩固期"的正常现象，还是"开发停滞"的预警？从 roadmap 角度分析

4. **双模型闭环的成熟度评估**：三轮 catch-ball 后，这个流程是否已经成熟？哪些方面仍需改进？（RULES v2 中"SCAN 先确认运行时假设"的落地）

#### 附录

- CB-01 vs CB-02 vs CB-03 三轴评分对比表
- CB 自动化 5 组件质量评分
- defer 项追踪表

### 步骤 3：更新 cb-journal

在 `docs/catch-ball/cb-journal.md` 追加 `## CB-03` 章节（仅有 ① SCAN 摘要，状态 open）

### 约束

- 全部写入仅限 `docs/catch-ball/`
- 零 commit / 零 push / 零副作用
- 不编辑 SCAN_DeepSeek_01.md / SCAN_DeepSeek_02.md（已归档）