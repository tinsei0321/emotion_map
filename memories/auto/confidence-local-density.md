---
name: confidence-local-density
description: l1_confidence 空间自相关须用局部点密度分位；amap POI weight 恒 1.0 无梯度不能用
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 763f315e-5f99-4d75-9826-b918ac7c6bfa
---

`l1_confidence` 空间自相关（拉开 `_grid_h` 高低）必须用**局部点密度分位**作信号，不能用 POI weight。

**Why**：amap POI 缓存的 `weight` 恒为 1.0（无梯度），按 weight 分级 → 所有点同档 → conf 全挤 0.74+，无张力（实测首版 `<0.6` 格 = 0，全图 mean 0.74，张力失败）。

**How to apply**：`SCRIPT/generate_l1_mock.py inject_fields` 开头用 numpy 把 pts snap 到 ~250m 格（`floor(lon/0.0025)`）数密度 → 分位归一 `dens_norm(0~1)` → `_spatial_confidence(area_tag, dens_norm)`：ermalu `0.80+0.18·d`、main `0.45+0.45·d`。改后 conf 落 0.42–0.97、heat(count×conf) 对比 ~50×。dens_norm 是真正的 Tobler 空间自相关信号，比 POI weight 可靠。见 [[symmetric-norm-stretch]]。
