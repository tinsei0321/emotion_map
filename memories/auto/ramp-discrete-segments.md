---
name: ramp-discrete-segments
description: 色带一律离散分段（.hm-style-seg），禁止 linear-gradient 连续渐变
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 22e972fb-64fe-47c3-bbb5-efd0c7d69068
---

全站色带（色板预览 / 图例 / Overview / 工具弹窗）一律用**离散分段**渲染（`<span class="hm-style-seg">` 等宽色块拼成 `.hm-style-bar`），**禁止 linear-gradient 连续渐变**。

**Why:** 设计语言一致性——用户多次强调"其他内容都是渐变颜色段，这里也要沿用"。我在 grid 色板预览用过 linear-gradient 被纠正。

**How to apply:** 渲染色带用 `rampDisplaySegs(rampKey, ramp)`（frontend/js/state.js）拿离散色段数组 → `<span class="hm-style-seg" style="background:c">` × N 嵌 `<span class="hm-style-bar">`，复用 CSS（frontend/css/dialog.css `.hm-style-seg`/`.hm-style-bar`）。参考 heatmap-tool.js `renderStylePreview`（约 :325）。grid/legend/overview/任何新工具的色带都按此。关联 [[select-cascade-progressive]]（同属 UI 一致性规则）。
