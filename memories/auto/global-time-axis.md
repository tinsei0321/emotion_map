---
name: global-time-axis
description: 全局时间轴架构已实现（time-bar+timeline+time-source 三分·manifest 驱动）——⚠️ manifest 404 待修复（③w2 专题后置）
metadata: 
  node_type: memory
  type: project
  originSessionId: b4313e60-747e-46a0-a954-91863e5ac9d0
  modified: 2026-08-04T12:58:29.280Z
---

时间轴推倒重做（A0-A4，2026-07-20）：T1/T2/T3 烧死文件名 → 全局时间维度（global temporal axis）。**已实现**（time-bar.js/timeline.js/time-source.js 三件套在仓）。manifest 单一权威源原指 `DATA/processed/_time_manifest.json`——**⚠️ ③w2 发现路径已失效**：数据 R100 迁移到 `DATA/performance/`，代码已改指 `/DATA/performance/_time_manifest.json`，但手写 manifest 从未落到新位置（留 `old_data_processed/`）→ **manifest 404·时间轴当前不可用（静默降级）**。用户定**开专题重规划**（候选：geo_registry 同源派生 manifest）。

**三分架构**：
- `time-bar.js`（UI）：底部圆按钮 + Martin 风卡片（粒度胶囊 + 阶段停点/日历 + 滑动条 + play）。用户交互入口。
- `timeline.js`（**headless 引擎**，A3 改造）：grid 演进 rAF lerp + snap-to-grid 重聚合。**无自带 UI**，由 time-bar 驱动（导出 `bindGrid/unbindGrid/renderSlice/play/stop/isBound`）。旧侧栏 `#timeline-wrap` widget retired。
- `time-source.js`（数据 + 控制器）：manifest 加载 + `loadSlice` + `applyTime`（点层换源）。Track A GeoJSON / Track B MVT 接缝（换后端上层零改动）。

**关键 gotcha — applyTime silent 机制（A4）**：applyTime 末尾 dispatch `layers:changed` → refreshOverview → setOverview 读焦点层 fc。**grid 焦点时** grid.fc 不随 renderSlice 更新（只改 map source data）→ dispatch 会用旧 fc **抢刷** `_renderFrame` 画的正确 Overview。修法：`applyTime(period, key, silent = gridBound())`——grid 绑定时 silent（不 dispatch，Overview 由 timeline._renderFrame 驱动）；点焦点时 dispatch（refreshOverview 读点层新 fc 追随）。

**播放语义**：grid 平滑 lerp（T1→T2→T3 柱体/色演进 = 张力来源），点层片边界离散换源（点不可 lerp）。grid 焦点 `_renderFrame` 已 paint OverallKpi（按 Overview 当前 sub-Tab）。

**grid 层 datasetId**：grid-tool 生成 grid 时设 `L.srcName = 源 srcName`；`bindGrid` 补调 `tagLayer(layer)` 按 srcName 经 matchDataset 拿 datasetId（grid 生成时未打标）。

承重：paint-inplace-swap-view（换源走 setData 不重建层）/ tool-no-auto-overview（不抢焦点）/ 四态·diagnose 不碰 / snap-to-grid 算法保留只改组织。详见 plan `07-19-cb-lovely-quiche.md` + revision-log 5.140-5.142。关联 [[paint-inplace-swap-view]] [[tool-no-auto-overview]] [[emc-tri-state-exit-contract]]。
