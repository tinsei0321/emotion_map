# GLM 最终评估 Prompt

> 将以下内容连同 `docs/catch-ball/emc-arch-deepdive/` 文件夹全部文件提交给 GLM 评估。

---

## 背景

EMC（Emotion Map Controller）是城市情绪地图平台的 AI 助手。经多轮 CB（Catch-Ball）评估 + 代码审计 + 业界对标 + DeepSeek V4 function calling 实测，产出了 v2 改良混合架构。

**核心变化**：从 v1 三阶段设计（0LLM→Flash填信息卡→Pro推理）修订为 v2 单次 LLM + function calling + 契约 Schema。废弃信息卡概念。

## 需要提交给 GLM 的文件清单

| 文件 | 内容 | 优先级 |
|------|------|:---:|
| `SUMMARY.md` | v2 架构全景 + 68 条决策 + 耗时对比 + 实施优先级 | **必读** |
| `01-diagnose-agent.md` | 模块一 v2 完整设计（function calling + 契约 Schema） | **必读** |
| `02-orchestrator.md` | 模块二 v2（消费 tool_calls + 参数校验） | **必读** |
| `06-prompt-engineering.md` | 模块六 v2（contracts 派生 + fallback） | **必读** |
| `09-field-recognition.md` | 模块九 v2 简化（全注入·废弃筛选） | **必读** |
| `SCAN_ArchReview_deepseek_2026-07-28.md` | 架构评审报告（7 个缺陷 + 修复状态） | **必读** |
| `VERIFY_DeepSeekFC.md` | DeepSeek V4 实测结果（3 个关键发现） | **必读** |
| `SCAN_PostImpl_deepseek_2026-07-28.md` | 代码审计（v1 实现率 0% 的诊断） | 选读 |
| `README.md` | 会议记录 + 全部决策索引 | 选读 |
| `03/04/05/07/08-*.md` | 无需适配的模块（保留 v1） | 选读 |

## 实测验证的 3 个关键事实

1. **content + tool_calls 并存**：DeepSeek V4 支持在 function calling 响应中同时返回 tool_calls（执行指令）和 content（plans[] JSON）。v2 的 plans[] 机制可行。
2. **strict 不强制**：`deepseek-chat` 模型的 `strict: true` 不在服务端验证——LLM 可输出 enum 外的值。已加 D062 代码层校验兜底。
3. **13 工具全注入**：7.4KB / 2.7s——完全可接受。废弃 tools_hint 子集选择，全注入更简单。

## 请 GLM 评估的 8 个问题

1. **单次 LLM + function calling 的架构选型**是否正确？对比 v1 三阶段（0LLM→Flash→Pro），v2 的 tradeoff 是否合理？是否存在 v1 能做而 v2 做不到的场景？

2. **契约 Schema 作为参数约束机制**（contracts → JSON Schema → function calling tools 参数 + 代码层校验兜底）是否足够保证出图的制式化/标准化/本地化？strict 实测不强制是否是重大风险？

3. **废弃信息卡、改用契约 Schema + function calling** 是否正确？信息卡有什么契约 Schema 覆盖不到的价值吗？

4. **全注入 13 工具（废弃 tools_hint）**是否合理？13 工具全注入 7.4KB/2.7s 是否会导致复杂场景下 LLM 选择质量下降？

5. **plans[] 在 content 字段附带产出 + ctx.plans 三方共享**的设计是否可靠？CPD 多轮引导（用户点选项→直执→移除）的跨轮状态管理（D065 数据变化检测 + D068 ctx.plans）是否充分？

6. **68 条决策中有无遗漏或矛盾**？特别是 D062（代码校验）/D063（全注入）/D065（数据变化检测）/D066（fallback 派生）/D067（plans 校验）/D068（ctx.plans）这 7 条实测后新增的决策。

7. **实施优先级（P0: contracts 派生 + function calling + 编排器适配）**是否合理？有无更优的实施顺序？

8. **整体评估**：v2 改良混合架构是否已达到可落地实现的状态？还有哪些必须在实现前解决的架构级问题（非落地细节）？

## 约束条件

- 用户坚持「保 LLM 灵活性」——所有阶段保留 LLM，不引入纯模板结论
- 单问深度控制在 gis_operation 级别——复杂问题由 CPD 多轮拆解
- 出图必须使用情绪地图专用工具（Toolbox generate*ForAI），保证制式化/本地化
- DeepSeek V4 为唯一 LLM provider（原生支持 function calling）

## GLM 的产出要求

请输出一份结构化评估报告，包含：
- **逐条回应 8 个问题**（agree/disagree/partial + 理由）
- **新增风险或遗漏**（如果有）
- **落地前的 Blockers**（如果有·区分架构级 vs 实现级）
- **一句话总评**
