# EMC Harness 机制分析报告：与 codex 原生 Harness 的对照（2026-08-26）

> 触发：用户实测「西陵区 12345 top3 社区」问题（cdh 226s·思维链反常规·出图范围不符）后提出架构性质疑。
> 结论先行：**你的理解正确**——EMC 跑的就是 codex 原生 Harness，EMC 定制契约落在工具面/指令面/呈现面三层，**但不在编排层**；「思维链奇怪 + 慢 + 出图不符」三者各有明确机制根因（下述）。

## 一 机制对照：EMC Harness = codex 原生引擎 + 三层定制，缺第四层

链路全貌（?engine=codex）：

```
前端面板 → POST /api/v1/aiqa/codex_engine（api/aiqa_routes.py L207·question 原样转发）
  → core/codex_bridge.py spawn「codex app-server --stdio」（codex 官方 CLI 原版引擎·0.149.1）
  → 原生 agent loop（turn/start·approvalPolicy=never·sandbox=read-only·cwd=_codex_cwd）
  → 模型自主调 emc MCP（8600·18 个 dumb 工具）→ SSE 真流式回前端
```

| 层 | 内容 | 归属 |
|---|---|---|
| 引擎层 | app-server 原版 turn 循环/agent loop/沙箱/MCP 协议 | **codex 原生·100% 未改** |
| 指令面 | `_codex_cwd/AGENTS.md`（= docs/cdh/AGENTS.md 同步版）：身份纪律/数据纪律/回答范式 | EMC 定制（提示层） |
| 工具面 | emc MCP 18 工具：list_data/zonal_stats/rank/aggregate_export/render_spec…（参数契约+caliber 守卫） | EMC 定制（dumb tool 层） |
| 呈现面 | brain-adapter-codex.js：SSE 事件流→ACP 事件（只翻译不编排） | EMC 定制（展示层） |
| ~~编排层~~ | **不存在**——没有「意图分类→参数映射→工具链」的确定性编排 | **EMC 在 codex 引擎下跳过了自己的编排层** |

代码级证据：
- docs/brain-adapter.md L5 红线：「**编排权在引擎层**——Adapter 是翻译层非编排层（壳不经 Adapter 调度 MCP 工具）」
- brain-adapter-codex.js 头注释：「编排权：引擎层（Codex agent loop）——本适配器是翻译层非编排层（契约红线·不调 MCP 工具）」
- post_codex_engine（aiqa_routes.py L207-232）：question 原样透传，无前置指令拼接、无参数注入

**这就是与 dsh 的最大差异**：dsh 时代（3080 外接）思维链 = EMC 自己的 harness.js 四阶段（diagnose→plan→run→final）+ 确定性意图分类 → 60s 一把梭；?engine=codex 时前端**直接跑 runCodexEngine，完全跳过 harness.js**——意图理解、尺度判定、模板映射全部交给 codex 原生 agent loop（模型自主决策）。你的 EMC「意图 harness」在 codex 引擎下没有参与。

## 二 你的案例拆解：226s 思维链的每一步是什么驱动的

| 思维链步骤（你看到的） | 实际机制 | 时间占比 |
|---|---|---|
| 「先查可用的数据层和边界清单」 | AGENTS.md 纪律 1：**第一步必须直接调用 list_data**（指令面强制） | 低 |
| 「看一下分析口径文档，确认西陵区+社区级正确做法」 | 纪律 6 口径要求 + codex 原生 plan-then-act（模型自主决定查文档） | 中 |
| 「并行跑两个聚合——区级总量 + 社区级 top20」 | zonal_stats ×2（**geopandas 冷启动 10-20s ×2**） | 中 |
| 「用 POI 证据核实属于西陵区的社区」 | 模型自主加一轮核实（overlay/nearest 类调用） | 中 |
| 「确认出图方案的写法，再看渲染契约文档」 | AGENTS.md 纪律 5：出图前读 docs/render-contract.md | 中 |
| 「环境里命令行工具不可用」 | 模型试了一次 shell 被只读沙箱拦（纪律 4 已明令禁止，仍试一次） | 低 |
| render_spec 出图 | 用 zonal_stats layer_output 的 top20 全量 dataset | 低 |

**「奇怪」的真相**：你看到的行为不是 EMC 硬编码的，是 **AGENTS.md 纪律 + codex 原生自主决策**的合力——模型每一步自己决定做什么（读文档/核实/试 shell），这正是原生 agent loop 的形态。226s = 7-9 次 LLM 往返（每次含模型推理 + API 延迟）+ 2 次冷启动 + **reasoning_effort=high**（harness 配置锁定·每次工具决策前深度推理）。dsh 60s vs cdh 226s 不是"cdh 变弱"，是**确定性管线 vs 自主 agent 的架构性代价**。

## 三 出图不符的根因：工具契约缺口（代码级·不是模型不听话）

你要求西陵区 top3 面图层，但代码里**没有任何工具能产出它**：

- zonal_stats（mcp_server_emc.py L763-818）：`boundary` 是单个边界 id（如 193 社区）；`layer_output=True` 产出的 fc = `_layer_output_fc(merged, top_n, sort_col)` = **全量排序前 N**——没有「区域过滤」参数
- render_spec（L1732）：kind/name/dataset_id/…——**无 clip/filter 参数**
- overlay_analysis 是两图层求交（无「裁剪后聚合出图」原子能力）

→ 模型在现有契约下的最优解 = 全量 top20 聚合出图 + 文字里挑西陵 3 个。**答案对了、图必然是宽的**——这是 dumb tool 契约的缺口（缺「子区域过滤聚合」能力），不是模型执行错误。

## 四 是否充分发挥 Harness——诚实评价

**用对了（四验证全过）**：真流式逐字 / 只读沙箱防脚本污染 / 工具契约守卫（caliber·拒绝语义化） / 身份纪律生效（EMC 身份·三段式·口径声明·followup 接话）。

**代价（三个缺口）**：
1. **无确定性快路径**——常见任务（如本案例）也走全自主 agent loop，226s 且不可预测；
2. **出图范围无强校验**——答案范围 ≠ 图层范围没有任何守卫（图宽于答无约束）；
3. **速度不可控**——reasoning_effort=high 全局锁定，简单任务也被深度推理拖慢。

**定位差异（架构取舍，非 bug）**：dsh = 确定性管线（快/死板/60s）；cdh = 通用 agent（慢/灵活/226s）。EMC 当前把它们当互斥引擎——实际应互补。

## 五 改进建议

**短期（可立刻落地）**：
1. **降 reasoning_effort**（high→low/medium·harness config 一行）——预计 226s→90-120s；
2. **AGENTS.md 精简**：删「出图前读渲染契约文档」等重往返纪律（关键契约直接写进 render_spec 工具描述）；纪律 4 加强（禁试 shell）；
3. **治出图不符**：zonal_stats/aggregate_export 加 `region` 过滤参数（如 boundary 组合「base_community_area ∩ 西陵区」）——dumb tool 契约扩展，一个参数解决。

**中期**：
4. **快路径共存**：复用 light 引擎意图分类（select_template）→ 常见任务走模板化工具链（60s 级），codex agent 留作自由模式——恢复 dsh 的「确定性 + 快」，保留 codex 的「灵活」；
5. **出图一致性守卫**：render_spec 增加必填 scope 声明（与答案范围强校验，不符拒绝）。

---
> claude · 2026-08-26 · 证据：brain-adapter.md L5 / brain-adapter-codex.js 头注 / aiqa_routes.py L207-232 / mcp_server_emc.py L763-818·L1732 / codex_bridge.py ensure() / docs/cdh/AGENTS.md 全文
