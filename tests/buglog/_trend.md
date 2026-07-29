# 历史复发趋势（repro_count >= 2）

> 自动生成·recurring 为派生属性（非独立目录）。本表反映「曾反复出现的 bug」分布，
> 用于飞轮回归聚焦 + 仪表盘重复问题热力图（P2）。

| ID | 标题 | 复现 | 模块 | 状态 | 最近复现 | 根因 |
|:-:|------|:-:|:-:|:-:|:-:|------|
| B001 | 多要素裁剪失败螺旋（extract_feature 字段重命名断裂 + 单工具限制 + FC 推理死循环） | [4](resolved/B001-multi-extract-field-rename.md) | 数据识别 | [RESOLVED] | 2026-07-28 | [2026-07-28-multi-extract-reasoning-spiral.md](../../docs/catch-ball/rootcause/2026-07-28-multi-extract-reasoning-spiral.md) |
| B002 | finalStep 假结论 — "只说不做/只做一半"（复现） | [3](open/B002-finalstep-fake-conclusion-recurrence.md) | finalStep | [OPEN] | 2026-07-29 | [2026-07-28-hallucination-finalstep.md](../../docs/catch-ball/rootcause/2026-07-28-hallucination-finalstep.md) |
| B008 | 网格聚合 2D/3D 视角未解耦（新发现） | [3](open/B008-grid-aggregation-view-decoupling.md) | UI | [OPEN] | 2026-07-29 | — |
| B003 | LLM 推理螺旋 — 简单查询耗时异常（复现） | [2](open/B003-llm-reasoning-spiral-simple-query.md) | FC诊断 | [OPEN] | 2026-07-29 | [2026-07-28-multi-extract-reasoning-spiral.md](../../docs/catch-ball/rootcause/2026-07-28-multi-extract-reasoning-spiral.md) |
| B004 | finalStep 假结论 — 筛选点图层"只说不做"（复现） | [2](open/B004-finalstep-fake-conclusion-point-filter.md) | finalStep | [OPEN] | 2026-07-29 | [2026-07-28-hallucination-finalstep.md](../../docs/catch-ball/rootcause/2026-07-28-hallucination-finalstep.md) |
