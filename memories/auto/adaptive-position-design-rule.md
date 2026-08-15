---
name: adaptive-position-design-rule
description: 抽屉/弹窗/浮层 left 随其锚点（EMC/抽屉）右沿自适应，勿硬编码固定 left
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ab9ecdfe-67aa-400a-9932-8d2c86b24a90
  modified: 2026-07-21T14:54:34.660Z
---

用户两次强调「**记住，这是设计常识**」「**你要记住'自适应位置'的设计逻辑**」：凡浮层（抽屉、弹窗、popover、dock）的位置必须**随其锚点元素动态计算**，不能写死固定 `left`。

**Why**：锚点（如 EMC 浮窗）可被用户拖宽/移动；若弹层写死 `left:320px`，锚点变宽后弹层与锚点重叠错位（CPD 2b 就因 `#param-panel { left: var(--left-w) }` 锚旧左栏、抽屉化后错位 → ④ 待修）。

**How to apply**：
- 弹层 `left` = `锚点.getBoundingClientRect().right + gap`（JS 设，非 CSS 固定值）。
- 调用时机：弹层打开时 + 锚点 resize（ResizeObserver）+ 锚点拖动时。
- 多级浮层链式自适应：EMC → 抽屉（positionDrawer）→ param-panel/要素按钮弹层（跟随抽屉右沿）。
- 落地：cpd-state.js `positionDrawer()`（抽屉跟随 EMC 右沿）是范式；param-panel/要素按钮弹层同模式扩展（④）。
- 纵向同理（top 跟随），注意 offset parent 差异（#map vs #app-main）——用 viewport 坐标 getBoundingClientRect 换算。

关联 [[cpd-soft-collapse]]、[[design-language-consistency-iron-rule]]、[[apply-design-sense-no-bounce]]。
