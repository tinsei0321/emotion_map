---
name: tool-layer-convention
description: 工具生成的图层 → 独立组卡片 + 要素按钮开本工具弹窗（镜像 HeatMap H 按钮）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 026d020e-7f61-4e7a-8a41-0c5ad930537c
---

工具（HeatMap / Buffer / 未来 Toolbox 工具）生成的图层，统一两条规则（用户 2026-06-22 明确要求"记住"）：

1. **独立组卡片**：每个工具的输出层在 Layers 里自成一组（`categoryOf` 加该工具的 category，如 `buffer:'缓冲分析'`），设计语言 + 双击折叠/展开与其他组卡一致。改三处：`CATEGORY_LABEL` 加标签、`_groupOrder` 加序、`categoryOf` 加判据（`paint._ui.tool==='xxx'`，先于 range 兜底）。
2. **要素按钮 = 本工具弹窗**：层的要素按钮（kind marker 字母，HeatMap='H' / Buffer='B'）点击 → 开该工具的生成弹窗（**不是**通用 settings popover），且**编辑态回填当前层参数 + 原地更新**（layer id 稳定，"继续编辑"语义）。改三处：`hintChip` 加字母、`renderLayerList` 要素按钮 click 路由加该工具分支 → `openXxxDialog(id)`、`openXxxDialog(layerId)` 读 `paint._ui` seed 回填 + `dlg.dataset.editLayerId` + generate 时原地更新（`layer.fc=...; layer.paint=...; removeLayerFromMap+renderLayer`，不 addLayer 新建）。

**Why**：工具产出层管理一致 + 可二次编辑（改参数重生成，不删旧新建——删旧新建曾导致热力图消失/眼睛救不回，见 revision-log 4.6 / [[kde-loadbearing-logic]] 的稳定性原则）。

**How to apply**：新增任何 Toolbox 工具时，同时落地这 6 个点（3 组卡 + 3 弹窗）。HeatMap（H / heatmap）+ Buffer（B / buffer）是范例。判据统一 `layer.paint._ui.tool`。
