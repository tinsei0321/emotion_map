---
id: B004
title: 'finalStep 假结论 — 筛选点图层"只说不做"（复现）'
type: BUG
severity: CRIT
status: open
module: finalStep
source: 用户实测
cb: CB-09
rootcause: docs/catch-ball/rootcause/2026-07-28-hallucination-finalstep.md
case_ref: TC-23
repro_count: 2
last_repro: 2026-07-29
---

# B004 · finalStep 假结论 — 筛选点图层"只说不做"（复现）

## 标准化用例

**问句**：「将西陵区范围内的积极情绪点筛选出来单独显示。」

**数据前提**：西陵区边界（面层）+ 积极情绪点层（L010，9,922 条）

**预期行为**：
① clip 工具被选中（点层=积极情绪点，裁剪面=西陵区范围）
② 生成「西陵区积极情绪点」图层（1,247 条，点层）
③ 图层自动加载到地图
④ 结论诚实描述产出（含实际点数量）

## 已知失败模式

| # | 日期 | 表现 | 根因 |
|:---:|------|------|------|
| 1 | 07-29 | 结论称生成"西陵区积极情绪点 含 1,247 条"，实际未生成图层 | finalStep 无执行结果感知（与 B002 同根因） |

## 修复记录

| 日期 | 操作 | commit |
|------|------|------|
| — | 待修复 | — |

---

## 诊断摘要

**根因**：与 B002 完全相同的 finalStep 假结论模式。LLM 在 thinking trace 中正确规划了步骤（extract 西陵区 → clip 积极情绪点），且结论文本中具体到"1,247 条"——这个数字来自 grounding context 中积极情绪点的统计信息，被 LLM"合理推算"后写入结论。但实际 clip 工具调用未执行成功（或未被触发），最终无图层产出。

**关键模式识别**：当 LLM 的 thinking trace 中出现具体的数值/地名/图层名时，即使工具未执行，finalStep 也会把这些"推理出的信息"当作事实写入结论。这是 finalStep 假结论的核心机制——**LLM 无法区分"我推理出来的"和"实际发生的"**。

**治本方向**：CB-09 P1-1（同 B002）——finalStep context 必须包含工具执行结果的结构化摘要。
