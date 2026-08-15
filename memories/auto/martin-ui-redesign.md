---
name: martin-ui-redesign
description: "Martin nav architecture (ADR-016, B0-B5) — three-zone left panel, floating param panel, capsule options, brand-blue single-source; load-bearing conventions"
metadata: 
  node_type: memory
  type: project
  originSessionId: 1d87c3d5-ae52-4f1d-aae6-7bae33b9ce36
---

`frontend/` 主界面导航架构（ADR-016，2026-06，控制台 α v0.1）。在 geojson.io 1:1 外壳（顶栏+三栏+底图）内，把内部导航范式从"加法手风琴 + 各自 `<dialog>` 模态"收敛为 Martin/kepler.gl 式编辑器架构。文档化于 spec §3.4 + ui-redesign-plan Phase 4。

**承重约定（改前端导航前必读，勿破）**：

- **左栏三区 = tab 互斥，不是手风琴**：Range/Layers/Toolbox 经 `setActiveTab` 同步 pane 显隐。`showLayerManager` 等已改调 `setActiveTab('layers')`——结构性改动必须 grep 旧 `.lp-section[data-section=...]` 消费方再动。
- **参数栏随动（B6 复核零改动）**：`#param-panel` absolute `left:var(--left-w)`，紧贴 `#left-panel` 右缘、不可拖宽、默认隐藏。左下按钮簇锚 `#map`（absolute left:10px），`#map` flex 天然跟随左栏（Δcluster=Δlp，gap 恒 18=gutter8+offset10）——动 flex 前先想清楚。
- **apply 链零改**：点/线/面 + 核密度 + Buffer 三组参数 `<dialog>`→`<div>` 但 id 全保留；`applyPaint`/`generateHeatmap`/`generateBuffer` + 读值选择器不动；开关经 `openParamPanel()/closeParamPanel()` + `param-panel:closed` 事件（settings 清 `_layerId` 并转发 `layer-settings:closed` 保 sidebar `.is-active` 同步）。
- **品牌蓝单源 `#4285F4`**（`--geojson-color-brand-primary`/`chrome-active-fill`/`brand-selected`）；深灰 `#384555`（`--geojson-color-card-fill`）= 文字/图标色，**非底色**。半透明蓝走 `color-mix(in srgb, var(--geojson-color-brand-primary) N%, transparent)`——勿写死 `rgba(0,122,252)`/`#007afc`（旧蓝，B5 已清退；`--geojson-brand` 是未定义幽灵 token，B5 改走真 token）。
- **胶囊选项集设计语言**（线型/色板/分析类型复用）：无线框+阴影+选中蓝底白字+悬停灰+`--geojson-radius-md` 6px。见 [[capsule-button-design-language]]。
- **`.swatch` 调色板 = 圆角矩形**（`--geojson-radius-md`）；`.ov-swatch`/`.stat-cell .swatch` 是图例小圆点，保留圆形。

**内容色（非 chrome token，勿 token 化）**：`PRESET_COLORS` 用户选色调色板、arch-diagram 七色彩虹 `--lc`。

关联：[[three-page-architecture]]（控制台 α 定位）、[[kde-loadbearing-logic]]（核密度承重逻辑）、[[frontend-default-light-theme]]（chrome 白底）。
