---
name: design-language-consistency-iron-rule
description: 同按钮/feature 跨场景必须一致的交互与设计语言（用户铁律，多次强调）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0ee8d3df-960a-48b5-a6d6-91c6e4b6aba3
---

用户多次强调：**同一个按钮、feature 在不同场景 / 功能区 / 窗口 / 位置下都必须保持一样的设计语言和交互逻辑**，否则会混乱。原话："设计语言一定要保持一致……要不然会很混乱。"

**Why:** 这是演示产品，一致性 = 专业感 + 可学习性。不一致（例如某组的要素按钮能 toggle-close、另一组不能）会被用户立即察觉并判定为 bug——本轮 Issue 2（网络聚合组 heatmap 要素按钮缺 toggle-close，与 L 数据/范围组不一致）正是因此被报。

**How to apply:**
- 新增或改一个交互时，先 grep 所有同类按钮 / 入口，统一行为。例：要素按钮 toggle-close——point/line/range 走 settings popover toggle（`isOpen && openSettingsLayerId===id`），heatmap/grid/buffer/terrain 走 `isToolPanelEditing`（param-panel 开 + 激活 tab + `{tab}-dialog.editLayerId===id`），**同模式**。
- 跨入口的同动作（Toolbox 工具按钮 vs 图层行要素按钮 vs 左下角按钮）走同一 open 函数、同参数集（如 heatmap 要素按钮转调 `openHeatmapDialog(id)`，与 Toolbox 同入口）。
- 改一处交互前先问：别处同类是否要同步？**默认同步**，不要只补被报的那一处。
- 单源化是达成一致的手段：色板 `PRESET_COLORS` 单源在 state.js、悬停卡统一 [[tip-popup-unified-hover-design-language]]、要素按钮统一 [[tool-layer-convention]]。

相关：本轮工具要素按钮 toggle-close（sidebar.js `isToolPanelEditing`）、范围层 split-pill（range-presets.js 主按钮 + "+"）。
