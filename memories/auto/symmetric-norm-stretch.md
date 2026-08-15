---
name: symmetric-norm-stretch
description: _grid_norm/_norm 对称拉伸是 L2 综合张力根因；grid 前端与 terrain 后端必须同步同公式
metadata: 
  node_type: memory
  type: reference
  originSessionId: 763f315e-5f99-4d75-9826-b918ac7c6bfa
---

L2 综合配色的张力根因：极性归一化用**对称分位拉伸**，而非线性 `(pi+2)/4`。

公式：`norm = 0.5 + sign(pi)·min(1, |pi|/p95)·0.5`（p95 = |polarity_index| 95 分位）。

线性 `(pi+2)/4` 只到 terrain-9 中段（pi 聚集 0 附近）= 无张力。对称拉伸让极值铺满深红/深绿。实测 |pi|>1.2 的格约占一半 → 拉伸后大量格到 0/1 两端。

**必须 grid 前端与 terrain 后端同步**（两处同公式），否则「综合」配色不一致：
- 前端 `frontend/js/grid-tool.js preprocessGrid`：两遍（Pass1 收 pi 算 p95、Pass2 并入 `_grid_h` 第二循环赋 `_grid_norm`）
- 后端 `core/spatial_analysis.py create_terrain_mesh`：循环后两遍赋 `_norm`（单极性地形 pi 同号 → norm 单侧 [0,0.5] 或 [0.5,1]，正常）

L1 `_grid_h`（密度×置信度分位桶）是高度张力，与此（颜色张力）正交。见 [[emotion-map-logic-chain]]。
