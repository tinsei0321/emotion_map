# 会话交接卡

> 换机/新会话后读取此文件恢复上下文。**单份当前快照**——每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：2026-07-02 收工 | 分支 `main`（单分支工作流）

## 上一节点（07-02 晚）—— 演示数据最终版 + 本周四件套 + 收尾交互

**A. 演示数据最终版（百度热力点锚定 L1/L2）+ 地点层扩中心城区 + 模拟 agent**（plan `3-curious-bachman.md`，最大块）：
- **Task2 地点层扩中心城区（AMAP_KEY 缺→fallback）**：核验 POI 仅覆西陵伍家 + `.env` 不存在。[`sim_centralcity_poi.py`](SCRIPT/poi_data/sim_centralcity_poi.py) 百度热力点真实位置（central_outer，value 加权）+ 类别学自 1270 真实高德分布 + **水域屏蔽** → 2499 sim POI（schema 同真实高德）；[`place_layer.py`](core/place_layer.py) 双源合并（1270 核心 + 2499 sim = 3769）。
- **Task1 引擎** [`sim_performance_data.py`](SCRIPT/sim_performance_data.py) + [`performance_config.py`](SCRIPT/performance_config.py)：**百度去聚合** `N=Poisson(value×scale×snap_factor)` + 80m jitter，**scale=0.639 固化**（全域~34k/中心城区~17k/西陵伍家~10.8k 每快照）；**area_type 2 级**（core=西陵伍家 operation/governance / central_outer=外围 planning+renewal+governance；简化自 3 级，因更新单元 150 面覆盖全域无法作子集）；**4×5 双层倾斜** POI 继承 80% + 区域 bias×时间调制（0 空格，底权≥0.05）；**极性弧** core T1 neg55%→T3 pos62% + 7 锚点迁移（二马路/夷陵广场/儿童公园/市委/大南门/解放路/滨江）；外中心城区=纯热度点（不入 L2）；L2=L1∩cc→SnowNLP。产出 `DATA/performance/yichang_L1/L2_T1-T3`（L1 34列/L2 41列，schema 兼容前端零改）。
- **Task1c/1d**：[`api/routes.py`](api/routes.py)+[`config.py`](core/config.py) `PERFORMANCE_DIR` 合并扫入 `/data` 下拉；[`.claude/agents/sim-emotion-data.agent.md`](.claude/agents/sim-emotion-data.agent.md) 操作手册（调参食谱+AMAP_KEY 切真实高德路径）。
- **验证**：3 轮迭代（修 area_type 分化 + L2 `_L2_result` 移盘 + sim POI 水域屏蔽）；L1 34k/L2 17k、4×5 0 空格、score 弧 0.44→0.54→0.62；pytest 115 passed/1 预先存在（test_capabilities）**零回归**。

**B. 本周四件套（用户初始实现 + 我补全/修 bug）**：
1. **天地图·影像无注记底图** `tianditu-img-nolabel`（`apps/static/tianditu_img_nolabel.json`）+ popover 第 6 格 + `setBasemap` 背景。（校正：初版误加矢量 `tianditu-vec-base`→改影像）
2. **图层行单击/双击**：`selectLayerRow` 单击 `openRightPanel()`（弹 Overview/Table）；`.layer-row` dblclick→`fitToLayer`（递归 walk 全坐标 bbox）。
3. **要素色板→色段取色器**：[`RANGE_GRADIENTS`](frontend/js/state.js) 11 条；抽 [`renderColorPicker`](frontend/js/settings.js) **离散色段**（复用参数面板 `hm-style-bar`/`hm-style-seg`）共享 settings+buffer——点色段取预设色（不让自由调色）、去圆角色块+去文字标签。
4. **Range 线宽**：默认 2→1px；hover `baseW+3`→`baseW+1`（默认 1→2px）；`baseW` live 读 `paint.lineWidth`。

**C. 收尾交互**：
- **Range popup 收起反转**：`classifyMapClick` 重分 `range-outline`(line/hit) / `range-fill`(面域)；handler outline→开/保持、fill+blank→收起（用户要求"非轮廓线即收起，含面域"）。
- **放大镜外环统一加载器**：[`geocode-loader.js`](frontend/js/geocode-loader.js) 泛化 `track(kind,p)`+`trackGeneration`，分色（geocode 蓝/generation 青/完成统一橙 `#F5A623` 替原绿，stroke-width=4 不变）；search-bar 按 snapshot.color inline 设环色 + 去 is-collapsed 限制；生成 4 处接入（grid runGrid/runAggregate、buffer runBuffer、heatmap runTerrain）。以后新读取加 `KIND_COLORS` 一行即可。

## 当前状态
- 分支 `main`，HEAD = 本次 commit（演示数据最终版 + 四件套 + 收尾）。**已 push**。
- `.gitignore` 新增：`DATA/baidu-heatpoints/`（购买）、`DATA/performance/`（~197MB 生成，引擎可复现）、`amap_poi_centralcity_wgs84.json`（生成）。**数据未入库**——本地有；换机需重跑 `py SCRIPT/poi_data/sim_centralcity_poi.py && py SCRIPT/sim_performance_data.py` 复现（需本地百度数据 `DATA/baidu-heatpoints/`）。
- 新增 2 边界入库：`DATA/boundaries/中心城区行政区划_1623.geojson` + `城市更新单元划分.geojson`（公开规划数据）。
- pytest 115 passed / 1 预先存在（`test_capabilities`，06-25 已记"与本阶段无关"）；JS node --check 全过。
- **未 F5 实测**：演示数据导入 + 四件套视觉 + 收尾交互全待肉眼验 ← **新会话优先项**。

## 承重（本会话新增，勿破）
1. **演示数据引擎单源 [`sim_performance_data.py`](SCRIPT/sim_performance_data.py)**：百度去聚合 `scale=0.639` 固化（改要重算全域点量）；area_type **2 级**（core/central_outer，非 3 级——更新单元 150 面覆盖全域不可用）；4×5 双层（POI 继承 80% + 区域 bias）；外中心城区=纯热度点不入 L2；L2=L1∩cc。调参在 [`performance_config.py`](SCRIPT/performance_config.py)（SNAPSHOTS/AREA_TYPE_*_BIAS/SNAPSHOT_TIME_*_MOD）。agent 手册 `.claude/agents/sim-emotion-data.agent.md`。
2. **AMAP_KEY 缺 → sim POI fallback**：[`sim_centralcity_poi.py`](SCRIPT/poi_data/sim_centralcity_poi.py) 百度位置+真实类别分布+水域屏蔽 → `amap_poi_centralcity_wgs84.json`。key 到位后跑 `pull_amap_poi.py`（扩边界）一键切真实高德，引擎无感（schema 一致）。[`place_layer`](core/place_layer.py) 双源 `_AMAP_POI_PATH`+`_AMAP_POI_CC_PATH`。
3. **`PERFORMANCE_DIR`**（[`config.py`](core/config.py)）：[`/data`](api/routes.py) 端点合并扫 DATA/processed + DATA/performance 入下拉；前端按 scope/time_label 加载（零改）。
4. **放大镜外环统一加载器 [`geocode-loader.js`](frontend/js/geocode-loader.js)**：`track(kind,p)` 按 `KIND_COLORS`(geocode 蓝/generation 青) + `DONE_COLOR` 橙分色；多 kind 按 `KIND_PRIORITY` 取色。search-bar 类名 `is-ring-loading/done/fade`（非 is-geo-*），环色 inline。新读取：加 KIND_COLORS 一行 + track(kind,p)。stroke-width=4 不变。
5. **Range popup 收起反转**：`classifyMapClick` 返 `range-outline`(line/hit) / `range-fill`(面域 fill)；outline→showRangePopup（开/保持），fill+blank→collapseRangePopup。删了 `isRangePopupExpanded`（原 hit 带 toggle 死码）。
6. **色段取色器 `renderColorPicker`**（settings.js，settings+buffer 共享）：**离散色段**非渐变（复用 hm-style-bar/segs），点色段取预设色；去 swatch+文字。`.grad-list .hm-style-bar` 须 `flex:0 0 auto`（纵向容器内 flex:1 会压高度→横杠 bug）。
7. **Range 线宽**：默认 1px，hover +1（→2px），baseW live 读 paint.lineWidth。
8. **影像无注记底图** `tianditu-img-nolabel` → `tianditu_img_nolabel.json`（仅 img 无 cia）。
9. **图层行**：单击 `selectLayerRow`+`openRightPanel`（弹右栏）；双击 `fitToLayer`（递归 walk 全坐标）。区别于 `layer:selected` 事件仍不自动弹栏（承重④不变）。

## 承重（前会话，仍有效）
- **PRESET_COLORS 单源 state.js**；addLayer polygon/line 非分析层循环配色（grid/terrain 保 NAVY）。默认面域透明度 0.15。
- **工具要素按钮 toggle-close = `isToolPanelEditing(tool,id)`**（sidebar.js），与 settings popover toggle 同设计语言。
- **右端栏不自动弹开**：`layer:selected`/`cell:selected` 仅 activateTab+refresh（手动 .collapse-right）。
- **tip-popup 全 live 读**：`liveUi()` 每事件重读 paint._ui。
- **预设 split-pill**（主按钮+常驻"+"，替换=移除同名层）；**zonal 4×5 归因** `_attach_4x5_attrs`；**AI chat provider-agnostic**（llm_client，DeepSeek 走 shell env 无 dotenv）；**Overview isAnalysisLayer=_ui.tool 非 layerLevel**。
- **高度算法**：heightOf pc≤2 线性/pc≥3 offset+sqrt；maxHeight 2000/上限 4000；分极性 `_grid_h_pos/neg/neu`；视角按钮 `toggleGridViewMode`（配对去重）；3D 跳 fill；切视角必 reorderLayers；cell-popup kv `.kv-row` 横排。
- **4×5 单源** `poi_4x5_map.AMAP_L1_TO_4X5`（高德大类→domain×element）。

## 下一步（待用户定；候选）
- **【待 F5 验，最高优先】**：start.bat → ①导入 `DATA/performance/yichang_L1_T1`（全域点阵，层级1 2D/3D）+ `yichang_L2_T1`（中心城区，层级2 核密度）→ 切 T1→T3 看叙事递进（score 0.44→0.62）→ grid 指定单元（更新单元.geojson）聚合→Overview+Table 显 4×5 归因（层级3 闭环）。②四件套视觉：影像无注记底图 / 行单击弹栏·双击飞至 / 色段取色 / Range 线宽 1+hover2。③放大镜外环：生成时青→完成橙、反查蓝→橙。
- **Task3 指定区域演示**：城市更新单元 / 用地筛选（商业·公园广场）各自设计（数据下拉+2D/3D 参数+关键信息）。
- **Task4 Overview/Table 优化**；**Task5 AI 问答重做**（prompt 调优/接溯佰科）。
- **AMAP_KEY 到位** → 切真实高德 POI（替 sim fallback）。
- **stray 文件夹** `DATA/‌performance`（含 U+200C，用户手误空壳）可删（红线，用户手动）。

## 新会话 prompt（复制即用）
```
续 main 分支（HEAD=本次 commit，演示数据最终版+四件套+收尾交互已 commit+push）。读 memories/repo/session-handoff.md（最新快照 + 承重）。

本会话任务：<在此填。候选：F5 验后微调 / Task3 指定区域演示 / Task4 Overview 优化 / Task5 AI 问答 / AMAP_KEY 切真实高德>

要点：①演示数据引擎 sim_performance_data.py（scale 0.639 固化，area_type 2 级 core/central_outer，4×5 POI 继承+区域 bias，外环纯热度点不入 L2，L2=L1∩cc）；②AMAP_KEY 缺→sim_centralcity_poi.py fallback（百度位置+水域屏蔽），key 到位跑 pull_amap_poi 一键切；③PERFORMANCE_DIR 合并扫 /data 下拉；④放大镜外环 geocode-loader track(kind,p) 分色（geocode 蓝/generation 青/完成橙），新读取加 KIND_COLORS 一行；⑤Range popup 收起反转（range-outline 开/保持、range-fill+blank 收起）；⑥色段取色器 renderColorPicker 离散非渐变；⑦Range 线宽 1+hover2；⑧承重：PRESET_COLORS 单源/工具要素 toggle-close/右栏不自动弹/tip liveUi/预设 split-pill/zonal 4×5/AI provider-agnostic/heightOf/视角按钮 toggleGridViewMode/3D跳fill/reorderLayers/cell kv-row/4×5 单源 poi_4x5_map。
注：DATA/baidu-heatpoints + DATA/performance + sim POI 已 gitignore（本地有）；换机需重跑引擎复现（需本地百度数据）。
计费按调动次数，工作方式见 ~/.claude.md（不派 subagent）。
```

## 承重 memory 索引（本会话相关）
- 前会话承重：`extrusion-height-maxheight` / `grid-palette-tuning` / `generate-grid-exclusive-vs-viewmode` / `tip-popup-unified-hover-design-language` / `maplibre-query-array-stringify` / `terrain-mesh-rendering` / `grid-4x5-attribution` / `verify-real-endpoint`
- 设计语言一致性铁律（同按钮跨场景交互一致）→ capsule-button-design-language / tool-layer-convention
- 新建议存：**演示数据引擎方法论**（百度去聚合+4×5 双层倾斜）→ 已在 `.claude/agents/sim-emotion-data.agent.md`（文档化，无需 memory）
