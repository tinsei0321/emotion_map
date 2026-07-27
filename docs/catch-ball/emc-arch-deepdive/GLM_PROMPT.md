# GLM 评估 Prompt：EMC 架构重构方案

> 请 GLM 作为第三方大模型，对以下 EMC（Emotion Map Controller）架构重构方案进行全面评估。

---

## 背景

经 CB-04 多轮 SCAN（DeepSeek 评估 + Claude 反评价 + GLM 融合定稿），核心发现：

- EMC 管线耗时 50-95s（诊断 prompt 臃肿 30-54KB + finalStep prompt 20-44KB + while-loop 多轮超时）
- 工具 AI 入口与手动 UI 能力断层（generateHeatmapForAI 硬编码 rainbow·observation 质量差）
- 审查机制假阳性高（Flash 小模型审大模型）且大部分路径本就跳过
- 执行层 observation 不准确导致 finalStep LLM 结论与实际产出矛盾

## 重构方案

用户 + DeepSeek 经 9 个模块深度拆解讨论，产出 43 条决策的架构重构方案。

**核心文件**：
- `SUMMARY.md` — 架构全景 + 全部决策索引 + 耗时对比 + 实施优先级
- `README.md` — 逐模块会议记录 + 决策表 + 进度追踪
- `01-diagnose-agent.md` 至 `09-field-recognition.md` — 各模块详细决议

**文件路径**：`docs/catch-ball/emc-arch-deepdive/`

## 架构核心变化

```
改造前:
  用户 NL → diagnose LLM(25-45s) → while-loop(30-75s) → finalStep LLM(25-50s) → review+revise
  总耗时: 50-95s·经常超时

改造后:
  用户 NL → 0LLM字段识别(<100ms)
         → Flash填信息卡(<5s·prompt 1-3.5KB)
         → [单卡直传 | 多卡→Pro推理(5-10s·prompt 2.5-5KB)]
         → 编排器确定性派发(<10ms)
         → 工具执行(100ms-2s)
         → finalStep轻LLM(3-5s·prompt 0.6-1.3KB)
         → 代码质量防线(<20ms)
  总耗时: 8-20s·零超时
```

## 请 GLM 重点评估

1. **三阶段低耦合（0LLM→Flash→Pro）的边界划分是否合理？** Flash「只匹配填卡不推理」的定位是否正确？Pro 的触发条件（单卡跳过、多卡介入）是否合理？

2. **prompt 瘦身幅度是否过度？** Flash 从 30-54KB → 1-3.5KB、finalStep 从 20-44KB → 0.6-1.3KB——是否会影响 LLM 输出质量？是否存在遗漏的关键知识？

3. **CPD 和追问胶囊的分级设计（L1直达/L2轻判/L3走CPD）是否合理？** L2 跨工具单步跳过 Flash 直走 Pro 是否安全？

4. **旧 Review+Revise 全部删除、改为 8 条代码规则的决策是否正确？** 代码规则能否替代 LLM 审查？是否存在盲区？

5. **工具能力字典（tool_contracts.py）作为单一真相源的方案是否可行？** 派生机制是否会引入新的维护负担？

6. **整体架构是否存在未覆盖的盲区或潜在风险？** 多轮对话上下文传递、异常恢复降级链路、前后端 contracts 同步——这三个补充设计是否充分？

7. **实施优先级排序（P0-P4）是否合理？** 模块三（执行层）和模块五（删除R+R）作为 P0 是否确实是最高杠杆？

## 已知约束

- 用户坚持「保 LLM 灵活性」——所有阶段保留 LLM，不引入 0 LLM 的模板结论
- 单问深度控制在 gis_operation 级别——不深入归因/领域出口（复杂问题由 CPD 多轮拆解）
- MANIFESTO §1-11 全文从所有 LLM prompt 中移除——领域知识由 contracts 结构化数据替代
