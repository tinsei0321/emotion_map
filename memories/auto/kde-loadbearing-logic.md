---
name: kde-loadbearing-logic
description: KDE dialog load-bearing logic — cascade-exclude + exclusive-hide; do not break
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 37c73a6f-6b0f-40d8-a99f-fb15b12069c5
---

核密度分析弹窗的两条**底层逻辑**，改动时必须保持，不可破坏：

1. **联动排除（cascade-exclude）**：各选择栏（分析类型/数据层级/特性/类型/表现）互相联动，**无对应字段的层级/选项自动排除**。
   - 类型细分（积极/消极/中性）= L2 专属字段 → 选中即锁 L2，L1 不可选。
   - L1/L3/L4 无情绪分类字段 → 类型/表现胶囊禁用（不显示兜底假值）。

2. **独占显示（exclusive-hide）**：生成新热力图时隐藏其他所有图层，让新图独占视野。必须保留 `dispatch layers:changed` 让侧栏眼睛状态同步（否则眼睛表象"无效"）。

**Why:** 用户两次因这两条被破坏而报 bug——独占显示一度被误删（"关闭其他图层失效"）、neutral 没锁 L2（"选中性出现 L1"），明确要求"不要再犯同样错误，底层逻辑一路保持"。

**How to apply:** 改 KDE 弹窗任何选择栏联动 / generateHeatmap 时，逐条核对这两条。规范已写入 [revision-log.md](docs/revision-log.md) 4.10 第 9/10 条。见 [[maintain-revision-log]]。
