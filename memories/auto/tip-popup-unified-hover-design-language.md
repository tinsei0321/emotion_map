---
name: tip-popup-unified-hover-design-language
description: 网格/柱体/地形环悬停用 tip-popup 浮动卡（自适应方位+灵动跳动），是统一悬停设计语言，未来 point/range hover 也应迁移
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 450f231f-e51a-4fd7-8f99-06d6aadcbffe
---

用户在 Task 2.7 确立了**统一的鼠标悬停提示设计语言**：聚合单元（网格/柱体/地形环）悬停 → `#tip-popup` 浮动卡（`position:fixed` 150×150 白底 4px 圆角高阴影、`pointer-events:none`），而不是原 dark maplibregl tooltip。

核心要求（`frontend/js/tip-popup.js`）：
- **自适应方位**：依指针在视口的位置（左/右/上/下 40% 阈值）选象限放卡，**不遮挡被悬停的主体**。
- **灵动跳动**：不每像素死绑指针——hysteresis（位移 >14px 才换位）+ 象限翻转 + CSS `transition: left/top 120ms ease-out` 顺滑滑动，"锚定指针但灵活跳到合适位置"。
- 内容 3 行精简（地点 reverseGeocode / 口径·L2 积极·中性·消极计数 / 边长）。

**Why**：原 terrain hover 是 dark maplibregl tooltip（与 light chrome 不一致、无归因、方位死绑指针易遮挡主体）。用户要"悬停提示类内容的统一设计语言"。

**How to apply**：本批仅 tool 层（grid/terrain）接入，已删 `bindTerrainInteractions` + dark terrain-tooltip CSS。**未来 point/range 的 hover tooltip 也应迁移到 tip-popup**（模块已设计成可扩展：`bindTipPopup(layer, lid)` + `fillContent` 按层类型分支）。新增任何悬停提示→走 tip-popup，别再造 maplibregl Popup 或 dark tooltip。关联 [[frontend-default-light-theme]] [[stand-on-giants-shoulders]]。
