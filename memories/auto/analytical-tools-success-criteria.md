---
name: analytical-tools-success-criteria
description: 分析型工具(zonal/compare/rank/area_stats)成功=rows非空，非产图层；勿用 newLayerCount 误判 GAP
metadata: 
  node_type: memory
  type: project
  originSessionId: e6777171-ecd1-4dbb-9427-77a442be1217
  modified: 2026-07-23T05:47:16.147Z
---

EMC 工具分两类，**成功判定标准不同**（v1.4/5.189 修过的长期 bug 根因）：

- **操作型**（clip/buffer/overlay/filter/extract/merge/hotspot）：产地图图层 → 成功 = `data.layerId` 存在（newLayerCount>0）。
- **分析型**（`zonal_stats`/`compare_regions`/`rank`/`area_stats`）：返 `data.rows`（统计表），**不产图层、无 layerId** → 成功 = rows 非空。

**曾踩坑**：runTemplatePath 成功判定只认 `newLayerCount>0`（[harness.js:289](frontend/js/ai_qa/harness.js#L289)）→ 分析型工具即使 rows 非空、数据齐全，也被 `newLayerCount===0` **误判 → EXIT_GAP**（"未产出图层"）。这是用户长期"数据齐全却喊缺数据"的根因。

**修法（v1.4）**：`_ANALYTICAL_TOOLS` 集 + `hasRows = analytical && r.data.rows.length>0`；成功 = `!failed && (newLayerCount>0 || hasRows)`。

**How to apply**：新增工具时先归类（操作型产图层 / 分析型返表格）；分析型工具若要可视化，前端合成 polygon（zonal 的 `_zonalToLayer`：rows+boundary→`piToNorm` 注 `_grid_norm`→`addResultLayer _ui.tool='zonal'` 复用 grid choropleth）。勿再纯靠 newLayerCount 判成功。

关联 [[emc-tri-state-exit-contract]]（四态出口）、[[emc-delegates-to-toolbox]]（EMC 委托 Toolbox）。
