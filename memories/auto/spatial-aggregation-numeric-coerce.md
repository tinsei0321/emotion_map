---
name: spatial-aggregation-numeric-coerce
description: 后端聚合 groupby mean 前必须 pd.to_numeric(coerce)；外部数据 str 化崩 500，合成 float 测不出
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3540e2cb-de7a-41ff-9b4b-943098af252f
---

后端空间聚合三函数——`create_square_grid` / `create_hex_grid` / `aggregate_by_polygons`——对数值列（`score`/`l1_confidence`/`emotion_intensity`，aggregate 为 `agg_cols`）**groupby mean 之前必须 `pd.to_numeric(errors='coerce')` 强转**。代码 [spatial_analysis.py:233/325/415](core/spatial_analysis.py)。

**Why:** 外部数据（用户上载 CSV / 编辑层 / 经 GeoJSON 文本中转）的数值列会被**序列化成 str**。pandas 对 str 列直接 `mean()` 抛 `TypeError: dtype 'str' does not support operation 'mean'` → `routes.py` 兜底 500 → 前端 `runGrid` 解析失败显「Failed to fetch」/错误 toast。而 `DATA/processed/` 内置数据是纯 float，**pytest 合成数据完全测不出**这条路径。

**How to apply:** ① 任何新增聚合统计列 → groupby 前 `pd.to_numeric(col, errors='coerce')`（非数值→NaN，mean 自动跳过，优雅降级）；② **验证必须用 str 化数据打真实 POST 端点**（`/api/v1/spatial/grid` body 含 `"score":"0.72"` → 期望 200 + `score_mean` 数值），不能只 curl `/health` 或用纯 float——参见 [[verify-real-endpoint]]；③ 运行中后端改了 `spatial_analysis.py` 需重启 `serve.py`（uvicorn 无 `--reload`）。同期 memory: `generate-grid-exclusive-vs-viewmode`。
