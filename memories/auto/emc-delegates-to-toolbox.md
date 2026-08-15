---
name: emc-delegates-to-toolbox
description: EMC 不自造 GIS，委托主 Toolbox 程序化入口（heatmap/grid/terrain）+ Layers 可见数据纪律 + run_python 收口
metadata: 
  node_type: memory
  type: project
  originSessionId: 61d030d1-352d-4aa5-86d8-8d6434c2d807
---

EMC（情绪地图 AI 问答）的工作机制铁律（2026-07-14 重构 5.92-5.94 确立）：**不自造并行 GIS，委托主前端 Toolbox 的程序化入口**。

- **tool=委托 Toolbox**：EMC 分析能力调主 Toolbox 工具的程序化入口——`generateGridForAI`（grid-tool.js，3D 网格聚合，已存在）、`generateHeatmapForAI`+`generateTerrainForAI`（heatmap-tool.js，本轮新增 2D 彩虹/3D 等值面）。EMC `TOOLS.density` 按模式路由（2d→heatmap / 3d→grid / terrain→terrain）。**勿在 EMC 自造 `/api/v1/geo/density` 式并行 geo 端点 + 自造色带**（DENSITY_RAMP 已退场）。新增分析能力优先扩 Toolbox 工具+`*ForAI` 入口，仿 `generateGridForAI` 模板（silent:true、返 {layerId,layerName,featureCount,fc}）。
- **param=Layers 可见层**：EMC 只用 `getLayers().filter(visible)` 的层（`pickVisiblePointLayer`）；registry 未显示层（如 `yichang_l2_t1`）一律禁用——只传 L1·T1 绝不跑 L2。`buildContext` 不注 catalog 全量。
- **run_python 收口**：harness gate 拦截 run_python（`ctx.allowCodeViz=true` 才放行，用户显式要自定义可视化）；缺工具→EXIT_GAP 缺工具卡引导后续开发，不临场写代码。

**Why**：用户报 EMC 产出"半成品图"+ 自造 density（kde_raster+DENSITY_RAMP）与主 Toolbox（heatmap rainbow/grid terrain-9）分叉，图面/色段/2D-3D 全不对齐；且数据默认用 registry 缓存致"只传 L1 跑 L2"用错数据。三 Explore agent 实测全证实。用户定位=参数化设计（tool=成熟gis+本地化，design=标准图层+本地化token）。

**How to apply**：改 EMC 分析行为时守此三铁律——① 委托 Toolbox 不自造（套固定 HEATMAP_RAMPS 色段+2D/3D 切换）② 只用 Layers 可见层 ③ 不临场写 python。委托 Toolbox 的图层经 `addLayer` 入 getLayers 但绕过 addResultLayer，须调 `_registerToolboxLayer` 补 _registry/_stepResults（$n 引用+provenance+5.74 对账）。关联 [[stand-on-giants-shoulders]] [[emc-tri-state-exit-contract]] [[view-data-conclusion-sync]]。
