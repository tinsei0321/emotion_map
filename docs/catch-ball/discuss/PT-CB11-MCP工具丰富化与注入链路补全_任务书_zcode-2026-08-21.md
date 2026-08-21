# PT-CB11 · MCP 工具丰富化 + 注入链路补全 · 任务书（zcode 主手设计·2026-08-21 深夜）

> 依据：R61/R62 战略转向（dsh 归官方+MCP 优先）+ `会话交接_完整计划落盘_zcode-2026-08-21.md` §三 + 用户 B-3 强烈要求入计划（原话「标准图例以及 parameter 对注入图层的调整，如果不在任务计划中请加入」）+ 用户 Kimi 试实力指令。
> 性质：**任务书（plan）——按「先讨论再开工」纪律，用户拍板后开工**。分支 `EMC_harness_dsh`（main 冻结）。基线 **444 collected**（上浮须注明）。
> 宪法遵守：本批全部改动在 EMC 仓内（tools/ + api/ + frontend/ + docs/）·零 dsh 侧定制·零仓外件（双环境同步=git pull 即得）。

---

## 〇 批次定位与拆分（两批交付）

| 批 | 内容 | 量级 | 交付价值 |
|---|---|---|---|
| **P1 先行批** | B-3 注入链路治本（6 小件）+ 3 件高频工具 | ~1.5d | 用户每次落图直接感知（灰框→正常填色+图例）；方格/对比/聚集三类最常见问法 1 调用即答 |
| **P2 后批** | 5 件工具 + guard 迁 server 侧 + A-4 版本徽章（顺带） | ~3d | 工具面从 10→18 件；守卫不依赖宿主自觉 |

**拆分理由**：B-3 是用户已强烈表达的不满（每次测试都撞见），必须最先治；3 件高频工具（grid_aggregate/compare/hotspot）覆盖「800m 方格」「A 区 vs B 区」「哪里显著聚集」三类高频问法，P1 即见效。后批 5 件多为组合件（nearest/area/overlay 是薄包装，trend/report 是组合件），可从容实施。

---

## 一 B-3 注入链路治本（P1·最高优先·根因已实锤）

### 1.1 根因链（主手调查·2026-08-21 深夜·含代码行号实证）

用户症状：dsh 渲染的 choropleth 图层显示为「灰色框+无填充」；参数面板能识别但调整无效；无标准图例。

```
①数据断裂（源头）：preset 数据属性全中文（诉求总量/社区/SQMC 等）
   × MCP render_spec 的 value_field 默认 'point_count'（mcp_server_emc.py:571 附近）
   × 后端 dataset 白名单 _filter_dataset_props 只放行英文键（api/render_routes.py:58-71）
   → 过滤后 properties 只剩 {来源:2025}——即使 value_field 填中文也过不了白名单（双重断裂）
②全零归一：前端 _normCommunityCount 读不到值 → _count_norm 全 0（render_client.js:58-73）
③零值透明：paint 带 zeroIsNoData:true（render_client.js:156）→ map.js:783-785 零值特判 rgba(0,0,0,0)
   → 全部面透明 = 「无填充」
④灰描边：gridField 存在时线色恒 '#666'（map.js:841）→ 「灰色框」
⑤图例缺失：图例判定按 _ui.tool 白名单 grid/terrain/density（sidebar.js:222-223）
   → 注入层刻意不带 _ui（PT-CB8 F4 修复·带 zonal 会误入对话框）
   → 无 choropleth 色带图例，反而命中 isRange（sidebar.js:203-204）显示误导性线框图例
⑥tip 缺失：富悬停 tip 只绑 _ui.tool ∈ {grid, terrain}（map.js:650-652）→ 注入层只有层名简 tooltip
⑦面板无效：拾色器对数据驱动 fill-color 无效（fill 恒为 _gridColorExpr 表达式·map.js:810）
   ——契约本意=换色走重投递 spec（render-contract.md §七-7），但 UI 未提示用户
```

**方向裁决**：走**方向 A（render_client/后端补链）**，不走方向 B（伪造 _ui.tool 走完整 Toolbox 链路）——方向 B 会把社区面当网格层处理（panel.js 极性深读/要素按钮全错配），且 PT-CB8 F4 正是为去掉该标记，走回头路；方向 B 也不治数据断裂（挂了 _ui 照样灰框）。

### 1.2 修复件清单（6 件·约 4-5 文件·每处 1-10 行）

| # | 改动 | 文件:位置 | 规格 |
|---|---|---|---|
| B3-1 | 白名单增补（治本①） | api/render_routes.py `_filter_dataset_props`（:58-71 键表 + :138-152 过滤） | 按 preset manifest 的 nameField/value 指标字段透传（含中文字段名）；或增补中文指标键表（社区/SQMC/诉求总量/民生基础件/安全韧性件/每周约件数/排名）——执行时按 manifest 实际字段定，**禁一刀切全放行**（C1 脱敏纪律：不放行含个人信息的字段） |
| B3-2 | value_field 服务端校验（治本①·防再错配） | tools/mcp_server_emc.py render_spec（:570+） | dataset 类 spec：校验 value_field ∈ dataset 实际字段；错配返回语义化错误（含可用字段清单提示宿主自纠）——错误码模式对齐 G-2 三段式拒绝 |
| B3-3 | 图例判定改语义（治⑤） | frontend/js/sidebar.js:222-223 + :203-204 | 色带图例判据改为「paint.gridField 存在即数据驱动 choropleth」（与 map.js:810/:841 F4 修复同判据·两行）；isRange 排除带 gridField 的层（防误导·一行） |
| B3-4 | tip 绑定（治⑥） | frontend/js/map.js:652 | bindTipPopup 绑定条件加 `\|\| p.gridField`；须验证 tip-popup.js 对无 _ui 层的字段取值兼容（执行时核对·不兼容则适配） |
| B3-5 | 面板防误导（治⑦） | frontend/js/settings.js polygon 分支（:100-101） | gridField 层禁用/隐藏拾色器，附提示文案「数据驱动着色·换色请重投递 spec」 |
| B3-6 | 全零可观测（防复发） | frontend/js/render_client.js `_normCommunityCount`（:58-73） | 归一后全零时 console.warn（含 valueField 与期望提示）——下次断裂 30 秒定位 |

**验收口径（用户复测四项）**：在 3080 问「12345 诉求最密集的 5 个社区，显示在地图上」→ ①正常填色（非灰框·色带梯度可辨）②左侧标准色带图例 ③悬停显社区名+数值 ④参数面板不再给出无效拾色器。

### 1.3 分工

- **B3-1/B3-2（后端两件）**：zcode 直改（小改·含测试）。
- **B3-3~B3-6（前端四件）**：**Kimi 首件**（试实力）——视觉验收标准明确（四口径），改动面小（4 文件各 1-10 行），适合首考。

---

## 二 8 件新工具设计（P1×3 + P2×5·取号 F_033-F_040 已核连续）

> 取号依据：MCP 插座已占 F_021-F_028（七件套+render_spec）、F_029/F_030（render_routes watcher/dataset 取数）、F_031/F_032（render_file/emc_status）——**新 8 件 = F_033-F_040**。

### 2.0 通用规格（每件必带·沿 PT-CB5-T3 架构铁则）

1. **纯只读包装**：零写盘零副作用零 LLM 调用；不改既有后端文件（新增函数除外）；
2. **契约 schema 派生**：参数 enum/默认值从 `ai_qa/tool_contracts.py` 对应 skill 派生（G8·禁手写 enum）；tool_contracts 无对应件的（trend/report）新契约先落 tool_contracts.py 再派生；
3. **caliber 四键**：每工具返回必带 `{scale, semantics, limits, refs}`（refs 指口径注册表 K 卡）；
4. **体积纪律**：rows≤20 / top_n cap≤20 / layer_output 复用 `_layer_output_geojson`（200KB 硬顶·几何简化·2bebb6bc 教训：宿主工具结果缓冲区有限）；
5. **服务端守卫**：输入 layer/boundary 过 usage 检查（G-2·复用 `_reject_analysis_output`）；输出过 C1 脱敏（禁 PII 字段）；
6. **五判据一行答辩**（结构化输出/口径内建/脱敏自动/错误语义化/组合性 dataset_id 链式）——答不赢的删或改；
7. **埋点**：`register_track_id` + `@track('MOD_AIQA.F_0xx', track_args=False)`；
8. **每件测试 8-11 用例**（参照 test_mcp_server_emc.py 既有模式：正常链/守卫拒绝/边界/体积）。

### 2.1 P1 三件（高频）

#### ① grid_aggregate（F_033·方格网空间聚合·~0.5d）

- **价值**：替代 T8 脚本（PT-CB7 的 800m 方格任务）——同类问题「按 800m 方格统计」1 调用即答，dsh 建议④+R46 总纲首件。
- 输入：`{layer: str 点层id, cell_size: int = 800, agg: str = 'count' (count|mean|sum), value_field: str = '' (agg≠count 时必填), boundary: str = '' (可选裁剪 preset), top_n: int = 10 (1-20)}`
- backing 三步链：`core.geo_registry` 读点层 → `core.spatial_analysis.create_square_grid`（:806）建格 → `aggregate_by_polygons`（:237）聚合 →（boundary 给出则 gpd.clip）。
- 契约源：density 契约 mode=3d 的 `cell_size` 参数（panel_source=Grid dialog cellSize·语义同源：cell=格边长非带宽）。
- 返回：`{rows: [{cell_id, count|value, centroid}], stats: {total_cells, nonzero_cells, max}, layer_output?: geojson(≤20格·_layer_output_geojson), caliber}`。
- caliber：`{'scale': '中观（格网尺度由 cell_size 定）', 'semantics': '方格网聚合强度（规则格·非行政单元）', 'limits': '方格≠社区/行政区——勿把格结论说成社区结论；行政单元归因用 zonal_stats', 'refs': ['K-C1']}`
- 五判据：count/mean 口径内建（裸调要自己翻字段语义）✓ 结构化 rows ✓ G-2/C1 自动 ✓ 错配 value_field 语义化报错 ✓ layer→boundary→render dataset_id 链式 ✓。

#### ② compare_regions（F_034·多区域对比·~0.5d）

- **价值**：「A 区和 B 区哪个情绪更差/差多少」——≥2 区并排+差异叙述，高频问法。
- 输入：`{regions: list[str] ≥2（preset id 或名称·经 manifest 解析）, layer: str = 'yichang_l2_t1', agg_cols: list = ['score'], metrics: list = ['mean'] (mean|sum|count)}`
- backing：`aggregate_by_polygons` 逐区聚合 → 差异计算（max/min/差值/倍率）。
- 契约源：tool_contracts `compare`（skill: compare·tool: compare_regions·:155——regions ≥2 约束同源）。
- 返回：`{regions: [{name, metrics...}], diff: {max_region, min_region, gap, ratio}, caliber}`。
- caliber：`{'scale': '中观（区域对比）', 'semantics': '≥2 区域同口径并排+差异', 'limits': '区数 <2 拒绝；跨口径对比无意义（同 layer 同 agg_cols 才可比）', 'refs': ['K-C1']}`

#### ③ hotspot_analysis（F_035·Gi* 显著聚集·~0.5d）

- **价值**：「哪里显著聚集/显著冷点」——统计显著性的聚集识别，与 density（连续密度面）区分的口径卡点。
- 输入：`{layer: str 点层id, threshold: float = 1.96 (1.65|1.96|2.58=90/95/99%), top_n: int = 10}`
- backing：`core.spatial_analysis.hot_spot_analysis`（:32·Gi* 现成）+ `_classify_hotspot`（:133）。
- 契约源：tool_contracts `hotspot`（:263）。
- 返回：`{hotspots: [{cell_id/coord, gi_z, classify(hot-spot|cold-spot|not-significant)}], counts: {...}, caliber}`。
- caliber：`{'scale': '中观', 'semantics': '逐格 Gi* 统计显著冷热点分类（非连续密度面）', 'limits': '显著=统计意义非业务意义；连续热度分布用 density；阈值对应置信度须随口径输出', 'refs': ['K-C1']}`

### 2.2 P2 五件（先锁名称/取号/量级·防抢号；细则 P1 销号后函数级补发）

| # | 工具 | F 号 | 功能 | backing | 契约源 | 量级 |
|---|---|---|---|---|---|---|
| ④ | nearest_analysis | F_036 | 最近邻锚定（POI 邻近：每个社区最近的 N 个 POI/设施） | gpd.sjoin_nearest（新建·core 无现成） | tool_contracts `nearest`（:227） | 0.5d |
| ⑤ | area_stats | F_037 | 面积占比统计（单层各类面积/占比） | gdf.area 计算（最简件） | tool_contracts `area_stats`（:191） | 0.5d |
| ⑥ | overlay_analysis | F_038 | 叠置交叉（面∩面/∪/差） | gpd.overlay | tool_contracts `overlay`（:116·how 参数语义同源） | 0.5d |
| ⑦ | trend_analysis | F_039 | 时序对比（L2 情绪点 T1/T2/T3 三期） | geo_registry 点层 ×3 期聚合对比（组合件） | **新契约**（tool_contracts 增 skill: trend） | 1d |
| ⑧ | report_assemble | F_040 | 综合报告组装（多工具结果→结构化报告） | outlet_card 扩展（build_outlet_schema 组合） | outlet_card 契约扩展 | 1d |

---

## 三 guard 迁 server 侧（P2·宪法条款落实）

- **迁入内容**：原 dsh guard 插件逻辑（白名单/步数预算/审批策略）→ MCP server 工具调用前校验（服务端强制·不依赖宿主自觉）。
- **B4 白名单差集检查自动化**：新工具注册时自动核对 manifest usage（input 才可作输入）——落实 R59 裁定「B4 改 server 侧自动校验」。
- **实现位置**：tools/mcp_server_emc.py 内 `_guard_check(tool, args)` 前置校验函数（现有 `_reject_analysis_output` 泛化）。

## 四 A-4 版本徽章（P2 顺带·Kimi 原任务不变）

/version 端点 + 前端角标 + 不匹配横幅（原 PT-CB10 任务书规格引用不变·随 P2 批交付）。

---

## 五 执行矩阵

| 件 | 执行 | 时点 |
|---|---|---|
| 任务书（本件） | zcode | ✅ 已落盘 |
| B3-1/B3-2 后端 | **zcode 直改** | 用户拍板后即开工 |
| B3-3~B3-6 前端 | **Kimi（首件试实力）** | B3-1/B3-2 合入后派（Kimi 基于已治本数据测图例） |
| P1 三件工具 | **Codex 或 dsh（待用户定）** | 函数级派发单随 B-3 合入发出（规格样式沿 PT-CB5-T3） |
| P2 五件 + guard + A-4 | P1 回收验收后派 | — |

## 六 DoD（批级）

- [ ] 8 件工具全过：测试 8-11 用例/件 + 五判据答辩落执行记录 + 门禁全绿（基线 444 上浮注明）
- [ ] B-3 用户复测四口径全过（填色/图例/tip/面板）
- [ ] **契约条目产出（R22）**：render-contract.md 增「注入层图例/tip 判定 = gridField 语义（非 _ui.tool 白名单）」条目 + tool_contracts 增 trend 契约
- [ ] 追踪 ID F_033-F_040 注册连续不跳号
- [ ] 双环境同步：纯仓内改动·零仓外件·零 dsh 定制（宪法合规自查）
- [ ] 回收结果落盘 + commit push（未 push 不算完成）

## 七 需用户拍板项（三项）

1. **批次拆分**：P1=B-3+3 件高频工具先行 → P2=5 件+guard+A-4。接受/调整？
2. **Kimi 首件**：B-3 前端四件（B3-3~B3-6·视觉验收明确）——试实力合适吗？备选=area_stats（最简工具件）。
3. **P1 三件工具执行手**：Codex（稳）还是 dsh（快·PT-CB5 七件套先例）？

---

> zcode 主手 · 2026-08-21 深夜 · PT-CB11 任务书·待拍板
