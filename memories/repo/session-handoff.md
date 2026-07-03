# 会话交接卡

> 换机/新会话后读取此文件恢复上下文。**单份当前快照**——每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：2026-07-03 收工 | 分支 `main`（单分支工作流）| **未 push（ahead origin/main 4）**

## 当前节点（07-03，连续两批 Overview 重做）

**本会话主线 = Overview「视野-数据-结论同步」从骨架做到精修**（4 commit，HEAD=`04e1e0a`）：

1. `dc9ab49` — performance 入库同步 + gitignore landuse 源（修 .gitignore 尾行注释 bug）。
2. `bc343c8` — **Overview 双层 sub-Tab**（图层总览 | 单元深读，`activateOvTab`/`easeBackFromCell`）；**easeToCell** 进入单元层固定 `_cellModeZoom`（切格只 pan 不抬，修 stacking）；**isRangeLayer** 抽 state.js → toolbox 新建层关其他但**保 Range**；**用地 ingest**（`ingest_landuse_preset.py` 修 `_detect_geographic` Polygon 嵌套 bug；跑 390MB 三调 → 拆 商业服务业设施用地/公园与绿地+广场用地/城镇住宅用地 3 preset）；**搜索历史** 单条×+清除；**上传限制** 80→200MB。
3. `f434adb` — **Overview 4 板块重构** + 数据总览（饼图+领域柱）+ 归因矩阵 + 关键词 Top5 + **Overview→地图同步高亮基础设施**（`highlightCellSet`/`toggleStickyHighlight`，橙 #ff9000）；`KEYWORD_TABLE`（初版 pos/neg）；「视野-数据-结论同步性」写入 CLAUDE.md 演示逻辑链（铁律）+ memory。
4. `04e1e0a`（本批 9 项精修）：
   - **Range 图例**：横线 → **矩形线框+面域填充**（同步线/填充态），名称=层实际名。
   - **全局"i"**：`.info-i`（灰填圆 + 纯 CSS hover tooltip）+ Overview 三题头行内提示迁入。
   - **板块样式**：去线框+阴影加深+灰填充；属性行1 小浅灰、行2/3 粗；三部分灰色横线分隔；题头深灰 #384555。
   - **数据总览**：饼图 +20%、图例纵向小字去粗（色复用 L2_* 同地图极性图例）；去"均分"→ count 行 `共 N 条·积极/消极/中性`。
   - **归因矩阵**：`_piColor` 重做（活泼、**中性蓝非灰**、Material 600）；行标列 64→42 + 去"城市"前缀（整体左齐）。
   - **关键词**：3 列（正面/积极·中性/期盼·负面/消极）；`KEYWORD_TABLE` **网感重写 3 sign**（地铁通了/盼BRT/红灯长/网红打卡点/夜经济/噪音大/老旧小区/断头路…）；点击高亮 **~10 格** + fitBounds；色与矩阵同源。
   - **饼图选中逻辑**：`_cellsByPolarity` 格被选中 ⟺ 点数>阈值(积极/消极>10、中性>1) **且** 占比>40%。
   - **3D 高亮拔高**：`_applyHL` 高度 `mh→mh*2`（选中柱升高 2× + 橙 #ff9000 + 100%，修"与 2D 同效"）。
   - **sticky 白色外轮廓**：pie slice/矩阵格/关键词条 `.is-sticky` 白 stroke/box-shadow。

## 当前状态
- 分支 `main`，HEAD=`04e1e0a`。**ahead origin/main 4 commit（未 push，红线待用户确认）**。
- pytest 116 passed / 5 预存在失败（`test_capabilities`、`test_create_hex_grid_basic`/`test_grid_endpoint_hex`〔办公机未装 h3〕、`test_relaxed_threshold_returns_more`/`test_relaxed_has_low_scores`〔geocode 离线数据相关〕）— **零回归**。JS node --check 全过。
- AMAP_KEY 已配且与给定值一致（`.env`，**不动**）。
- **`.gitignore`**：`DATA/baidu-heatpoints/`（购买/许可）、`DATA/raw/landuse/`（390MB 三调源）、`SCRIPT/poi_data/amap_poi_centralcity_wgs84.json`（generated）仍忽略；`DATA/performance/` 已入库同步。换机重跑 `ingest_landuse_preset.py --split DATA/raw/landuse/1623_FeaturesToJSO.geojson --map DATA/raw/landuse/map.json` 复现用地 preset（map.json 已就绪）。
- **未 F5 实测**：本会话所有 Overview 视觉/交互（双层 Tab、饼图/矩阵/关键词同步高亮、3D 拔高、Range 图例矩形、"i" 图标、板块灰填充/横线）全待肉眼验 ← **新会话最高优先**。

## 承重（本会话新增/强化，勿破）
1. **Overview 双层 sub-Tab**（[`panel.js`](frontend/js/panel.js)）：`setOverview`→`#ov-layer-pane`、`setCellOverview`→`#ov-cell-pane`（**不再互相覆盖**，切换内容互不丢）；`activateOvTab(name,{silent})`；`easeBackFromCell`（切回图层总览/换层时恢复视野）。
2. **`easeToCell`**（[`map.js`](frontend/js/map.js)）：`_cellModeZoom` **进入单元层固定一次**（clamp[13,15.5]），切格只 pan 不抬高（修 stacking）；`_preCellView` 跨切格保留首快照。
3. **`isRangeLayer`**（[`state.js`](frontend/js/state.js)）：polygon/line 无 `_ui.tool` = 用户范围；grid/heatmap 独占关他处 `&& !isRangeLayer(other)` 跳过（保 Range）。
4. **Overview→地图同步高亮**（[`tip-popup.js`](frontend/js/tip-popup.js)）：`highlightCellSet`/`clearHighlightCellSet`/`toggleStickyHighlight`/`resetHighlightCellSet`，**独立于** `showCellHover`（地图直接悬停单格）；`cell-hl-set-layer` 3D = fill-extrusion 橙色/opacity 1.0/**高度 2× 原柱**（拔高）；hover 试探、click sticky（再点/异项切换）；`layers:changed`/`cell:selected` → `resetHighlightCellSet`。
5. **`_cellsByPolarity`**（[`panel.js`](frontend/js/panel.js)）：阈值规则（`POL_SELECT_MIN` 积极/消极>10、中性>1；`POL_SELECT_RATIO` 0.4）— 别回退成"全部相关格"。
6. **`_topKeywordCells`**：`slice(0, 10)`（~10 格/词，用户定）+ bbox fitBounds。
7. **`_piColor`**：Material 600 发散（绿/红/蓝，中性蓝非灰）；`KEYWORD_TABLE`（[`state.js`](frontend/js/state.js)）3 sign 网感词；关键词三列色 `is-pos/is-neu/is-neg` = #43A047/#1E88E5/#E53935（与矩阵同源）。
8. **`.info-i`**（[`panel.css`](frontend/css/panel.css)）：全局统一"i"（灰填圆+纯 CSS `::after` tooltip 读 `data-tip`）；**新提示都用它**，别造第三套 `.hm-info`/`.tool-info`（已存在，可逐步统一）。
9. **Range 图例矩形**（[`legend.css`](frontend/css/legend.css) `.range-dot` + [`sidebar.js`](frontend/js/sidebar.js) `refreshLegend`）：`border-color`=线色、`background`= `color-mix(in srgb, color fillPct%, transparent)` 或 transparent（fillOn 态）。
10. **「视野-数据-结论同步性」** 已入 CLAUDE.md 演示逻辑链（与三环同等优先级）+ memory `view-data-conclusion-sync`。

## 承重（前会话，仍有效）
- **演示数据引擎** [`sim_performance_data.py`](SCRIPT/sim_performance_data.py)：scale=0.639 固化；area_type 2 级（core/central_outer）；4×5 双层（POI 继承+区域 bias）；外环纯热度点不入 L2；L2=L1∩cc。调参 [`performance_config.py`](SCRIPT/performance_config.py)；agent 手册 `.claude/agents/sim-emotion-data.agent.md`。
- **`PERFORMANCE_DIR`**（[`config.py`](core/config.py)）：[`/data`](api/routes.py) 合并扫 DATA/processed + DATA/performance 入下拉。
- **PRESET_COLORS 单源 state.js**；**工具要素按钮 toggle-close = `isToolPanelEditing`**；**右栏不自动弹**（`layer:selected`/`cell:selected` 仅 activateTab+refresh）；**tip-popup 全 live 读 `liveUi`**；**预设 split-pill**；**zonal 4×5 归因 `_attach_4x5_attrs`**；**AI chat provider-agnostic**（llm_client）；**Overview isAnalysisLayer=_ui.tool**；**heightOf**（pc≤2 线性/pc≥3 offset+sqrt，maxHeight 2000/上限 4000，分极性 `_grid_h_pos/neg/neu`）；**视角按钮 `toggleGridViewMode`**；**3D 跳 fill**；**切视角必 reorderLayers**；**cell-popup kv `.kv-row`**；**4×5 单源 `poi_4x5_map.AMAP_L1_TO_4X5`**。
- **放大镜外环** `geocode-loader.js` `track(kind,p)` + `KIND_COLORS`（geocode 蓝/generation 青/完成橙 #F5A623）；**Range popup 收起反转**（range-outline 开/保持、range-fill+blank 收起）；**色段取色器 `renderColorPicker`**（离散非渐变）；**Range 线宽 1+hover2**；**影像无注记底图** `tianditu-img-nolabel`；**图层行单击弹栏/双击 fitToLayer**。

## 下一步（待用户定；候选）
- **【待 F5 验，最高优先】**：start.bat → 导入 L1/L2 → 生成网格 → 验：① 双层 Tab + 单元 zoom（切格不堆叠）② toolbox 新建层保 Range ③ 数据总览饼图+图例+count 行 ④ 矩阵色（中性蓝）+左齐 ⑤ **饼图/矩阵/关键词 hover/click → 地图橙高亮（3D 拔高 2×）** ⑥ 关键词 3 列网感词+点击 ~10 格 ⑦ sticky 白轮廓 ⑧ Range 图例矩形+名称 ⑨ "i" hover 文案 ⑩ 用地 preset（Range tab→商业/公园广场/居住）。
- **关键词措辞**：`KEYWORD_TABLE`（state.js）60 条是初稿（参考人民日报/澎湃城市热词），验后调。
- **更新单元干净矢量**：用户重导 → 替换 `presets/更新单元.geojson`（`load_preset` nameField='编号' 自动注入编号）。
- **Task5 AI 问答重做**（prompt 调优/接溯佰科）；**POI/地名纠错**（后期）；**F5 验后微调**。
- **push**：ahead 4 commit，待用户确认后 `git push`。

## 新会话 prompt（复制即用）
```
续 main 分支（HEAD=04e1e0a，Overview 视野-数据-结论同步 骨架+精修 已 commit，**未 push，ahead origin/main 4**）。读 memories/repo/session-handoff.md（最新快照 + 承重）。

本会话任务：<在此填。候选：F5 验后微调 / Task5 AI 问答 / 更新单元干净矢量 / 关键词措辞调 / POI 地名纠错>

要点：①Overview 双层 sub-Tab（panel.js setOverview→#ov-layer-pane / setCellOverview→#ov-cell-pane，activateOvTab，勿回退单容器覆写）；②easeToCell _cellModeZoom 进入单元层固定一次（切格只 pan 不抬）；③isRangeLayer（state.js）= polygon/line 无 _ui.tool（toolbox 独占关他保 Range）；④Overview→地图同步高亮 tip-popup.js highlightCellSet/toggleStickyHighlight（橙 #ff9000、opacity 1.0、3D mh*2 拔高；独立于 showCellHover；layers:changed/cell:selected→resetHighlightCellSet）；⑤_cellsByPolarity 阈值规则（点数>10/neu>1 且占比>40%）；⑥_topKeywordCells slice(0,10)；⑦_piColor Material 600（中性蓝非灰）；KEYWORD_TABLE state.js 3 sign 网感词；关键词 3 列色 is-pos/is-neu/is-neg=绿/蓝/红 同矩阵；⑧.info-i 全局"i"（panel.css 纯 CSS tooltip）；⑨Range 图例矩形（legend.css .range-dot + refreshLegend 同步线/填充+层名）；⑩承重：演示数据引擎 sim_performance_data.py(scale 0.639)/PRESET_COLORS 单源/工具要素 toggle-close/右栏不自动弹/tip liveUi/预设 split-pill/zonal 4×5/AI provider-agnostic/heightOf/视角按钮 toggleGridViewMode/3D跳fill/reorderLayers/cell kv-row/4×5 单源 poi_4x5_map/放大镜外环 geocode-loader/Range popup 收起反转/色段取色器/Range 线宽 1+hover2/影像无注记底图/图层行单击弹栏双击 fitToLayer。
注：DATA/baidu-heatpoints + DATA/raw/landuse + amap_poi_centralcity_wgs84.json 已 gitignore（本地）；换机重跑 ingest_landuse_preset.py（map.json 已就绪）复现用地 preset。AMAP_KEY 已配不动。
计费按调动次数，工作方式见 ~/.claude.md（不派 subagent）。
```

## 承重 memory 索引（本会话相关）
- 本会话强化：`view-data-conclusion-sync`（Overview 互动指挥台 / 橙色高亮 / sticky 锁定 / tip-popup highlightCellSet）
- 前会话承重：`extrusion-height-maxheight` / `grid-palette-tuning` / `tip-popup-unified-hover-design-language` / `maplibre-query-array-stringify` / `terrain-mesh-rendering` / `grid-4x5-attribution` / `verify-real-endpoint` / `design-language-consistency-iron-rule`（同按钮/feature 跨场景一致）/ `capsule-button-design-language` / `tool-layer-convention`
- 工作机制：`session-handoff`（边界主动提示新会话）/ `no-handoff-on-routine-commit`（平时只更 revision-log）/ `todo-revision-log-sync`（每完成一件同步两文件）/ `token-saving-workstyle` / `no-routine-playwright-verify`（实现→交付→用户 F5）/ `frontend-default-light-theme`（chrome 白底，勿信 analyze_image 配色）
