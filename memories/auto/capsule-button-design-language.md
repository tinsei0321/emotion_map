---
name: capsule-button-design-language
description: Capsule/chip button style — no border + shadow + blue-when-selected + grey-on-hover + compact; reuse for option selectors (line-style/color/analysis-type)
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6a072729-2ee2-4ea9-96e5-56a1f87fac7a
---

胶囊按钮设计语言（用于线型/色板/分析类型等"多选一选项"选择器）：**无线框 + 阴影 + 选中蓝(蓝底白字) + 悬停灰 + 尺寸紧凑 + 规整对齐**。

具体（CSS）：`border:none` + `box-shadow:0 1px 2px rgba(0,0,0,.10)` + `border-radius:6px`；默认白底深灰字（`--geojson-color-text-secondary`）；`:hover` 背景变灰（`--geojson-color-gray-200`）；`.is-sel` 蓝底白字（`--geojson-color-chrome-active-fill` + `--geojson-color-text-inverse`）+ 蓝调阴影；`flex:1` 等宽对齐、内容居中、padding 紧凑（~5-6px）。范本：`frontend/css/settings.css` 的 `.linestyle-cap`。

**Why:** 用户要选项胶囊有套一致语言，靠阴影浮起、选中蓝填充——区别于"细线框次要按钮"（revision-log §4.7：白底+深灰字+细线框+悬停灰，不填充）和"圆形色板 swatch"（圆形+边框+选中阴影环）。

**How to apply:** 新建线型/色板/分析类型等选项胶囊时套用此语言（复用 `.linestyle-cap` 或同构 class），不要用边框；选中态一律蓝底白字（项目激活态 token）。关联 [[tool-layer-convention]]（要素按钮开弹窗，弹窗内选项用胶囊）。
