# PT-CB11 · P1 三件工具派发单（Codex·函数级规格·zcode 主手设计）

> 执行：Codex（用户拍板 2026-08-21 深夜）。沿 PT-CB5-T3 派发单范式：**精确到函数级，零判断执行**；与真身签名不符处停手记「待主手裁决」。
> 分支 `EMC_harness_dsh`（main 冻结）。commit 前缀 `PT-CB11(C1):`。基线 **444 collected**（上浮注明）。
> 开工前 `git pull origin EMC_harness_dsh`（基线 ≥ 80b6e088）。依据：任务书 `PT-CB11-MCP工具丰富化与注入链路补全_任务书_zcode-2026-08-21.md`。

---

## 〇 架构铁则（沿 T3 批·重申）

1. 纯只读包装：零写盘零副作用零 LLM 调用；**不改任何既有函数体**；
2. 重依赖惰性导入：geopandas 等只在函数体内 import；
3. `print` 全走 `_safe_print`；代码禁 emoji；
4. caliber 四键必带（refs 指口径注册表）；
5. 体积纪律：rows ≤20 / top_n cap 20 / layer_output 复用 `_layer_output_geojson`（200KB 硬顶）；
6. 守卫：boundary/layer 过 `_reject_analysis_output`（G-2）·未知 id → `_UNKNOWN_HINT`；
7. 五判据逐工具一行答辩（结构化/口径内建/脱敏自动/错误语义化/组合性）——写进执行记录；
8. 测试：`tests/test_mcp_server_emc.py` 新增 8-11 用例（monkeypatch 范式沿 `test_zonal_stats_rows_cap_row_count_and_caliber`）。

## ⚠ 同文件并行协调（必读）

zcode 正在并行改 `tools/mcp_server_emc.py`（B3-2：render_spec 增 value_field 校验）+ 新增 `core/render_policy.py`。你的改动面**仅限**：

- 模块顶部 `register_track_id` 段：新增 F_033/F_034/F_035 三行（接 F_032 行之后）；
- 新增三个工具函数：建议放在 `rank`（:485 起）与 `_dataset_meta`（:540 起）之间；
- `build_server()`（:757 起）内 `@server.tool()` 注册三处。

**禁改**：render_spec / render_file / _dataset_meta / _layer_output_geojson / _gdf_rows / zonal_stats / buffer / rank 的函数体。合并冲突预期仅 register 段数行——后到者 rebase。

---

## ① grid_aggregate（F_033 · 方格网空间聚合）

```python
register_track_id('MOD_AIQA.F_033', 'MCP grid_aggregate（方格网空间聚合·参数化替代 T8 脚本）')

@track('MOD_AIQA.F_033', track_args=False)
def grid_aggregate(layer: str = 'yichang_l2_t1', cell_size: int = 800,
                   value_col: str = '', boundary: str = '',
                   top_n: int = 10, layer_output: bool = False) -> dict:
    """方格网空间聚合：点层按固定边长方格统计（中观·规则格）。
    参数：cell_size 格边长米（默认 800·语义同 Grid dialog cellSize=格边长非带宽）；value_col 空=只计数·给值则同时算 _sum/_mean；boundary 可选 preset 裁剪；top_n 1-20；layer_output=True 增 geojson。
    限制：方格≠行政单元——社区级结论用 zonal_stats；geopandas 冷启动 10-20s。"""
```

backing 链（参照 zonal_stats :390-440 的实现范式）：

1. `from core.geo_registry import resolve_points, resolve_boundary` → `points = resolve_points(layer)`（未知 → `_UNKNOWN_HINT` 拒绝）；
2. boundary 给出时：`_reject_analysis_output(boundary, 'boundary', CALIBERS['grid_aggregate'])` → `polys = resolve_boundary(boundary)` → `import geopandas as gpd; points = gpd.clip(points, polys.unary_union)`；
3. `from core.spatial_analysis import create_square_grid` → `merged = create_square_grid(points, cell_size, agg_cols=([value_col] if value_col else []))`
   —— **先读真身（core/spatial_analysis.py:806）核对签名与返回列名**（point_count/_sum/_mean 以实测为准·不符停手记待主手裁决）；
4. value_col 给出且 `f'{value_col}_mean'` 在列 → 按其降序；否则按 point_count 降序；
5. `rows = _gdf_rows(merged.head(top_n), [value_col] if value_col else None)`；
6. stats：`{total_cells, nonzero_cells(int((merged['point_count']>0).sum()), max_count}`；
7. layer_output → `_layer_output_geojson(merged, top_n, sort_col)`。

返回：`{rows, stats, row_count, truncated, caliber}`（+ geojson）。

caliber：`{'scale': '中观（规则方格·边长 cell_size m）', 'semantics': '方格网聚合强度（规则格·非行政单元）', 'limits': '方格≠社区/行政区——勿把格结论说成社区结论；行政单元归因用 zonal_stats', 'refs': ['K-C1']}`

## ② compare_regions（F_034 · ≥2 区域对比）

```python
register_track_id('MOD_AIQA.F_034', 'MCP compare_regions（≥2 区域同口径并排+差异·契约 boundaries 参数）')

@track('MOD_AIQA.F_034', track_args=False)
def compare_regions(boundaries: list, layer: str = 'yichang_l2_t1',
                    agg_cols: list = None) -> dict:
    """区域对比：≥2 个 boundary preset 同口径并排聚合+差异方向（谁更高/差多少/几倍）。
    参数：boundaries 必填 list（≥2·≤5·超5截断标注）；agg_cols 默认 ['score']（沿 zonal_stats）；layer 默认 yichang_l2_t1。
    限制：跨 layer/agg_cols 的对比无意义；单区归因用 zonal_stats。"""
```

backing 链：

1. boundaries 规整：list 或 'a|b'/'a,b' 分隔 str → list；`len < 2` → 语义化拒绝（hint 含「compare 需 ≥2 区·对齐契约 failure_modes」）；
2. 逐区：`_reject_analysis_output(b, 'boundary', ...)` → `polys = resolve_boundary(b)` → `g = polys.dissolve()`（多要素 preset 并一面）→ name 列：从 `list_boundaries()` 查 label（缺省用 b 本身）→ `g['name'] = label`；各区 g 用 `pd.concat` 合并；
3. `merged = aggregate_by_polygons(points, combined, agg_cols=cols, polygon_name_col='name')` → 每区一行；
4. `rows = _gdf_rows(merged)`；
5. diff（对 point_count 及存在的数值列 polarity_index/score_mean/`{c}_mean`）：`{metric: {max_region, min_region, gap, ratio}}`——ratio=min 为 0 → None（诚实不除零）；polarity_index 的 max/min 按 **abs 值**语义（对齐 zonal_stats :424 的 abs key）。

返回：`{regions: rows, count, truncated, diff, caliber}`。

caliber：`{'scale': '宏观/中观（区域对比）', 'semantics': '≥2 区域同口径并排+差异方向', 'limits': '区数 2-5；同 layer 同 agg_cols 才可比；单区归因用 zonal_stats', 'refs': ['K-C1']}`

## ③ hotspot_analysis（F_035 · Gi* 逐点显著聚集）

```python
register_track_id('MOD_AIQA.F_035', 'MCP hotspot_analysis（Gi* 逐点显著聚集·五档分类）')

@track('MOD_AIQA.F_035', track_args=False)
def hotspot_analysis(layer: str = 'yichang_l2_t1', value_col: str = 'score',
                     invert: bool = True, threshold: float = 1.96,
                     soft_threshold: float = 1.0, top_n: int = 10,
                     layer_output: bool = False) -> dict:
    """显著聚集识别：逐点 Gi* Z-score 五档分类（hot/tend_hot/ns/tend_cold/cold）。
    参数：value_col 默认 score；invert=True 负面为热（契约默认）；threshold 1.96=95%（1.65=90/2.58=99）；soft_threshold 1.0=倾向档；top_n 1-20。
    限制：显著=统计显著性非业务重要性；连续密度面用 density；score 为 U 形离散分布·ns 占多属正常（P1 修正口径）。"""
```

backing 链：

1. `points = resolve_points(layer)`（未知 → 拒绝）；`value_col not in points.columns` → 语义化拒绝（hint 列出可用数值列·对齐契约 failure_modes「与 density 混」防呆）；
2. `from core.spatial_analysis import hot_spot_analysis, _classify_hotspot` → 按真身签名调用（hot_spot_analysis(gdf, value_col, invert, threshold, soft_threshold)·core/spatial_analysis.py:32；返回的 Z 列名与分类列**以实测为准**·不符停手）；
3. counts：五档计数 dict；
4. top_n rows：显著优先（hot 先于 cold·按 |Z| 降序）——行含 place_name（如有）/Z/分类；
5. layer_output → `_layer_output_geojson(points_with_z, top_n, Z列)`。

返回：`{counts, rows, row_count, truncated, caliber}`（+ geojson）。

caliber：`{'scale': '微观（逐点 Gi*）', 'semantics': '逐点 Gi* Z-score 五档显著聚集分类', 'limits': '显著=统计显著性非业务重要性；连续热度分布用 density；threshold 对应置信度（1.65→90%/1.96→95%/2.58→99%）', 'refs': ['K-C1']}`

---

## 测试与 DoD

- [ ] 三工具各 8-11 用例：正常链（monkeypatch resolve_points/resolve_boundary）+ 守卫拒绝（analysis_output boundary/未知 layer/compare <2 区/value_col 缺列）+ cap（top_n 20）+ layer_output 体积；
- [ ] F_033-F_035 注册连续（`test_track_ids_f021_to_f027_registered` 范式扩展断言）；
- [ ] `python -m pytest tests/ -q` 全绿（基线 444 上浮注明）；
- [ ] 五判据逐工具一行答辩 + 执行记录落盘 `docs/catch-ball/discuss/PT-CB11-P1三件执行记录_Codex-2026-08-21.md`；
- [ ] 显式路径 commit（禁 add -A）·push 由用户/主手统一或经授权。

> zcode 主手 · 2026-08-21 深夜 · PT-CB11 P1 工具件派发
