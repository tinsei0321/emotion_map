---
name: extrusion-height-maxheight
description: 3D 柱体高度算法（低位线性+pc≥3 offset+sqrt）+ L2 极性网格语义（颜色高度=该极性点数）+ maxHeight 默认2000/上限4000
metadata:
  node_type: memory
  type: project
  originSessionId: 2587ac02-97a0-4c3e-940c-c57d28996cd8
---

3D 柱体高度算法（[grid-tool.js preprocessGrid](frontend/js/grid-tool.js) 的 `heightOf`，2026-07-01 多轮迭代定稿）。heightOf 全局共用 → `_grid_h`(总热度,L1+L2综合) + `_grid_h_pos/neg/neu`(分极性,L2 极性网格，各自 max)。

**heightOf(val, maxVal)** 公式：
- `val≤0` → 0
- `val≤2` → `val×0.025`（**低位线性**：pc=1→0.025/50m, pc=2→0.05/100m，接近趴地但有区分）
- `val≥3` → `((val-2)/(maxVal-2))^0.5`（**offset=2 + sqrt γ=0.5**：pc=3→~237m 起跳, pc=max→1.0 满高；ref=max 零 clamp）

**maxHeight**（高度 = _grid_h × maxHeight）：默认 **2000m**、上限 **4000m**（`#grid-extrusion-scale` min=200/max=4000/value=2000，`DEFAULTS.maxHeight=2000`）。terrain 仍硬编码 1000（等值环，非"柱体"）。

**L2 极性网格语义**（积极/消极/中性，2026-07-01 修正曾"错误"用占比）：颜色 field + heightField **同源 = 该极性点数**（`_grid_h_pos/neg/neu`，非占比 `_grid_pos`）。`gridStyle.POLARITY_FIELD`→分极性高度；`generateGrid` heightField 按 polarity 选；`POLARITY_HF` 映射；`filterPolarityZero` 剔该极性 0 点格（不渲染空格）。综合/L1 用 `_grid_h`。popup `_cellKvRows`/tip `metricText` 极性分支显该极性点数+程度(`_polJudgment`)。

**迭代教训**（勿回退）：分位归一化抹平量级 → 幂次 p95 ref 致 ≥p95 全 clamp 等高(34=44) → ref=max 致长尾低位趴地 → γ=1.3 仍趴地 → sqrt+max 1-2 都=0 无区分 → **现：低位线性+pc≥3 offset+sqrt**。γ>1 不适合长尾数据(1→73)；kepler 感=低位可见+全程梯度+高位鹤立。调参：`HEIGHT_OFFSET`/`HEIGHT_GAMMA`/`LOW_UNIT`/`maxHeight` 一行改。

关联：[[terrain-mesh-rendering]]、[[grid-palette-tuning]]、[[generate-grid-exclusive-vs-viewmode]]。
