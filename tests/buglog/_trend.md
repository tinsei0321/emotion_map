# 历史复发趋势（repro_count >= 2）

> 自动生成·recurring 为派生属性（非独立目录）。本表反映「曾反复出现的 bug」分布，
> 用于飞轮回归聚焦 + 仪表盘重复问题热力图（P2）。

| ID | 标题 | 复现 | 模块 | 状态 | 最近复现 | 根因 |
|:-:|------|:-:|:-:|:-:|:-:|------|
| B001 | 多要素裁剪失败螺旋（extract_feature 字段重命名断裂 + 单工具限制 + FC 推理死循环） | [4](resolved/B001-multi-extract-field-rename.md) | 数据识别 | [RESOLVED] | 2026-07-28 | [2026-07-28-multi-extract-reasoning-spiral.md](../../docs/catch-ball/rootcause/2026-07-28-multi-extract-reasoning-spiral.md) |
