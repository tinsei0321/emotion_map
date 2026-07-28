# 模块八：CPD 引擎 — v2 改良混合架构

> **状态**：✅ 已决议（v2）  
> **日期**：2026-07-28  
> **关联决策**：D054（v2）·D030-D034（v1·全部保留）

---

## 一、v1 → v2 变更

| 维度 | v1 | v2 |
|------|------|------|
| plans[] 来源 | Pro LLM 独立产出 | **function call content 字段附带** |
| plans[] 格式 | `{rank,label,tool,params,confidence,rationale}` | **完全相同** |
| CPD 展示逻辑 | rank=2+ 选项 | **不变** |
| CPD 执行逻辑 | 点击→直执→移除 | **不变** |
| 跨轮复用 | plans 存 turnHistory | **不变** |

**唯一改动**：数据源从 `proResult.plans` 改为 `llmResponse.content.plans`。

## 二、决策

| ID | 决策 |
|----|------|
| D054 | CPD plans[] 数据源改为 function call content·格式不变 |
| D030-D034 | v1 决策全部保留（不调LLM/直执/移除/完成/偏好） |

---

*关联文档：README.md·01-diagnose-agent.md（v2）*
