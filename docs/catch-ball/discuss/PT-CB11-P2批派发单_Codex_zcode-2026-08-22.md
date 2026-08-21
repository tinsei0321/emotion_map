# PT-CB11 · P2 批派发单（Codex·两阶段·函数级规格）

> 主手：zcode。执行：Codex。分支 `EMC_harness_dsh`（main 冻结）。commit 前缀 `PT-CB11(C2):`。
> **git 政策（用户令 08-22）**：**本地仓即最新·零 pull 零 push**——直接开工；只做显式路径 commit+执行记录，push 由主手回收时统一。
> 沿 P1 派发单架构铁则八条（纯只读/惰性导入/caliber 四键/体积纪律/G-2 守卫/五判据/测试/`_safe_print` 禁 emoji）——不重复·违者退回。
> **新增模板条目（claude 审计建议·即刻生效）**：每件新工具测试默认含 **1 例空集边界**（空输入/裁剪零点→语义化拒绝·非模糊错误）。

## ⚠ 同文件并行协调（与 P1 同规则）

改动面仅限：`tools/mcp_server_emc.py` register 段（新号接 F_037 后·**F_036 号位已预留给 nearest·Phase 1 首件必须落 F_036**）+ 新函数（area_stats 之后、_dataset_meta 之前）+ build_server 注册行。**禁改**：render_spec/render_file/_dataset_meta/_layer_output_geojson/_gdf_rows/既有工具函数体。与 Kimi 在途件（A-4 徽章·api/render_routes.py+frontend）零文件交集。

---

## Phase 1（先交付·~1.5d）：补丁两件 + 薄工具两件

### ① P2-1 空集判空补丁（grid_aggregate·**B 件过审条件**·最高优）

- 位置：`grid_aggregate` stats 计算前（当前 :603 附近）。
- 规格：`row_count == 0 或 'point_count' 不在 merged.columns` → 语义化返回：
  `{'ok': False, 'hint': '聚合结果为空（点层为空或 boundary 裁剪后零点）——请换 boundary 或检查点层', 'caliber': caliber}`
- +1 用例（空点层路径·非 mock 非空 fake）。

### ② P3-3 compare_regions 同款判空

- aggregate 后 `merged 为空` → 同款语义化空集返回（勿坍缩 `_UNKNOWN_HINT`）。

### ③ nearest_analysis（**F_036**·最近邻锚定·~0.5d）

```python
@track('MOD_AIQA.F_036', track_args=False)
def nearest_analysis(layer: str = 'yichang_l2_t1', target: str = '',
                     k: int = 1, top_n: int = 10, layer_output: bool = False) -> dict:
```
- 契约源：tool_contracts `nearest`（params: target 必填=k 个最近邻的目标层·layer=锚点层·k 默认 1）。
- backing：`resolve_points(layer)`（锚点）+ `resolve_points(target) 或 resolve_boundary(target)`（目标·先点层后面层）→ `gpd.sjoin_nearest(points_anchor, targets, how='left', distance_col='dist_m')`（**注意**：sjoin_nearest 需投影 CRS 算米距——照抄 area_stats 的 EPSG:4546 投影先例）→ 每锚点取最近 k 个。
- 返回：`{pairs: [{anchor(place_name 如有), target(名称), dist_m}...]（≤top_n 行·按 dist 升序）, stats: {mean_dist, max_dist}, caliber}`。
- caliber limits：`邻近≠因果；距离为投影平面距离（<1% 级误差）；k≤5 cap`。

### ④ overlay_analysis（F_038·叠置交叉·~0.5d）

```python
@track('MOD_AIQA.F_038', track_args=False)
def overlay_analysis(layer_a: str, layer_b: str, how: str = 'intersection',
                     top_n: int = 10, layer_output: bool = False) -> dict:
```
- 契约源：tool_contracts `overlay`（how: intersection|union|difference|symmetric·默认 intersection）。
- backing：双 `resolve_boundary`（G-2 各过）→ `gpd.overlay(a, b, how=how)` → 结果面积（EPSG:4546·照抄 area_stats）。
- 返回：`{rows: [{名称对/面积_km2}]（≤top_n）, result_count, stats: {total_area_km2}, caliber}`。
- caliber limits：`面∩面运算——点层裁剪勿用（无意义）；结果要素可能 explode 多块（按面积降序 top）`。

### ⑤ 顺手三小件

- P3-4：hotspot 补 layer_output 用例 1 例。
- render_file docstring 加一句：`面文件默认 value_field=point_count 多半不适用——显式传该文件真实指标字段`。
- P3-2：render_policy `renderable_fields` 提示文案加「部分字段可能未列出」（改 mcp_server_emc 侧 hint 拼接处·**不改 core/render_policy.py**——那是 zcode 在途件）。

## Phase 2（Phase 1 回收后·~3d）：组合件两件 + guard 迁移

### ⑥ trend_analysis（F_039·时序对比·~1d）

- 数据：L2 情绪点 T1/T2/T3 三期（`core.geo_registry` 点层 yichang_l2_t1/t2/t3·先 list_point_layers 核实 id）。
- 规格：`trend_analysis(boundary: str = '', metric: str = 'polarity_index', periods: list = None)` → 各期按 boundary（可选·无则全城）聚合 → 三期对比表+方向（升/降/平·按 metric 变化）+ 变化幅度。
- **先落契约**：tool_contracts.py 增 skill `trend`（params: boundary/metric/periods·panel_source=EMC-only）——契约为先纪律。
- caliber limits：`三期=采集批次非等间隔日历期；趋势为聚合口径非个体追踪`。

### ⑦ report_assemble（F_040·综合报告组装·~1d）

- 规格：`report_assemble(question: str, results: list, sections: list = None)`——results=[各工具返回 dict]（宿主链式传入）→ 按 outlet_card 结构组装综合报告（结论段/证据段（各工具 caliber 摘要）/口径段（合并 refs 去重）/建议段）。
- backing：`ai_qa.outlet_kb.build_outlet_schema.build_outlet_schema` 组合扩展（纯确定性零 LLM·对齐 outlet_card 先例）。
- caliber limits：`组装不产生新结论——只汇总输入结果；输入无 caliber 的段落标注「口径缺失」不编造`。

### ⑧ guard 迁 server 侧（任务书 §三）

- `_guard_check(tool, args)` 前置校验函数：现有 `_reject_analysis_output` 泛化（usage 检查+步数预算占位+审批策略占位）。
- B4 白名单差集自动核对：新工具注册时自动核对 manifest usage（list_data 返回面与工具可接受输入面差集→log 警告）。

---

## DoD

- [ ] 每件：8-11 用例（含空集边界 1 例）+ 五判据一行答辩 + F 号连续（F_036/F_038/F_039/F_040）
- [ ] Phase 1 完成即 commit+执行记录（`PT-CB11-P2执行记录_Codex-2026-08-22.md`）→ 通知主手回收 → 开 Phase 2
- [ ] `python -m pytest tests/ -q`：457 绿+7 存量环境失败（不新增失败）
- [ ] 显式路径 commit（零 pull 零 push·主手回收时统一 push）

> zcode 主手 · 2026-08-22 上午 · P2 两阶段派发
