# 会话交接卡

> 换机/新会话后读取此文件恢复上下文。**单份当前快照**——每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：2026-07-03 夜 | 分支 `main` | **已 push（本批 2 commit：`5cdd36b` feat + docs 本提交）**

---

## 🔔 本机待办（回家第一件事）：装今天新装的 skill

办公机 shell 的 git 连不上 github.com（443 超时，无代理），4 个 `claude plugin` 装不了；**回家开 VPN 在终端跑**（用本机扩展 bundle 的 claude.exe 全路径，不依赖 PATH）：

```powershell
# 1) 定位 claude.exe（扩展版本号随升级变，先 dir 查最新）
dir $env:USERPROFILE\.vscode\extensions\anthropic.claude-code-*
$CLAUDE="$env:USERPROFILE\.vscode\extensions\anthropic.claude-code-<版本号>\resources\native-binary\claude.exe"
& $CLAUDE --version   # 确认能跑

# 2) 装 4 个 claude-plugin（GitHub marketplace，必须 VPN）
& $CLAUDE plugin marketplace add anthropics/claude-plugins-official
& $CLAUDE plugin install superpowers@claude-plugins-official
& $CLAUDE plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
& $CLAUDE plugin install ui-ux-pro-max@ui-ux-pro-max-skill
& $CLAUDE plugin marketplace add OthmanAdi/planning-with-files
& $CLAUDE plugin install planning-with-files@planning-with-files
& $CLAUDE plugin marketplace add thedotmack/claude-mem
& $CLAUDE plugin install claude-mem
& $CLAUDE plugin list   # 核验
```

**另 2 个 npx skill**（办公机已装，家机也要装——走 npm registry 不需 VPN，但需 node/npx）：
```bash
npx -y skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines
npx -y skills add https://github.com/addyosmani/agent-skills --skill code-review-and-quality
```

装完若 `git status` 出现 `.agents/` / `.claude/skills/code-review-and-quality/` / `.claude/skills/web-design-guidelines/` / `skills-lock.json`——**已 gitignore（per-machine 符号链接至 .agents/，不入库）**，别提交。

**全局规则**已写 `~/.claude/CLAUDE.md`（①改前端优先用 skill 不造轮子 ②识别重复操作提示建 skill）——家机若没该文件，从办公机拷或重建（内容见 `docs/revision-log.md` 07-03 batch-2 行⑧）。

---

## 当前节点（07-03 夜，Overview batch-2 精修 + skill 扩充）

**本会话主线 = Overview「视野-数据-结论同步」第二批精修（11 项反馈）+ vibe-coding skill 体系扩充**。plan：`C:\Users\admin\.claude\plans\main-head-9bff353-overview-elegant-fountain.md`（已批准执行）。feat commit `5cdd36b`：

1. **图层互斥 + Overview 追随可见层**（任务6/7，架构核心）：[`state.js`](frontend/js/state.js) 新增 `enforceMutualExclusion`/`isToolAnalysisLayer`/`isEmotionPointLayer`——B 组分析层(heatmap/grid/terrain/buffer)内部互斥、A↔B(点/分析)不共存、A 组同一时刻只显一个数据源(同 L2 group 极性子层同源保留)、Range 永不被动关。接入 [sidebar.js](frontend/js/sidebar.js) 眼睛/分组/类别/全量切换 + grid/heatmap/buffer 生成 + `toggleGridViewMode`（替原 ad-hoc 关他循环）；[main.js](frontend/js/main.js) `refreshOverview` 改**追随当前可见层**（选中不可见→回退最顶可见分析层/点层并选它）。**修"换层后 Overview 仍显旧层、2D·3D 提示串台"根因**（眼睛只改可见性不改选中）。
2. **橙柱易选 + 单元深读高亮**（任务9）：[`tip-popup.js`](frontend/js/tip-popup.js) `pickHLCell`（橙柱层 `cell-hl-set-layer` 命中优先，修 `pickCellFeature` 只认注册层致点橙柱选中背后格）+ `focusCell`（深读：单格橙色**原高 mh**、其余 sticky 取消）；[`popup.js`](frontend/js/popup.js) click/hover 优先橙柱；`cell:selected` 同步清饼图/矩阵/关键词 `.is-sticky`（[`panel.js`](frontend/js/panel.js) 加监听）。
3. **选中橙框 #ff9000 4px**（任务8）：饼图(SVG stroke)/矩阵(inset box-shadow)/关键词 sticky。**修关键词框被 `.ov-kw-track{overflow:hidden}` 裁切看不见** → 橙框从 `.ov-kw-fill` 改挂到 `.ov-kw-track`。
4. **"i" 浮窗**（任务1）：原 `.info-i::after` `position:absolute` 被 `.panel-body{overflow-y:auto}` 裁切（困右栏内）→ 改 `position:fixed` 单例 `#info-i-tip`（append body, z9999，JS mouseover 委托 + getBoundingClientRect 定位，上不够翻下）；浅灰底 `#f0f1f4` 深灰字 `#3a3f4a` 10px 不加粗。
5. **3D 重叠/穿模**（任务4 反馈）：悬停升起柱 `cell-hover-layer` `extrusionOpacity??0.9` 半透明 + 下方原柱(grid 0.9)仍在 → 两色重叠；升起起始高度=原柱 → 顶面共面穿模闪烁。改 overlay **不透明 1.0**（同色完全遮原柱，共面也无可见闪烁）。高亮/focus overlay 本就 1.0。
6. **视觉小改**（任务2/3/5/10）：去"数据分析"标题；count 行去"城市情绪"+11px+去 `text-overflow:ellipsis`；横条数字 `#fff→#3a3a3a`（修白字溢出灰底不可读）；矩阵 `DOMAIN_ORDER` 改 `[规划,更新,运营,治理]`（客户画像序）+ 行标显全称"城市规划"+ 列宽 42→60 + `.mx-rowlabel` 左齐（与"归因矩阵"题头纵对齐）；饼图+图例包 `.ov-pie-block`（整体居中纵列，修"一下一上"错位，[`panel.js`](frontend/js/panel.js) overviewRow 3 栏→2 栏）。
7. **关键词 Top10**（任务11）：标题 `关键词Top5→Top10`；`_keywordRank` slice 5→10；点击高亮 `_topKeywordCells` 5→10；`KEYWORD_TABLE`（[`state.js`](frontend/js/state.js)）用**用户勾选 30 词**按 4×5 桶语义重填（全 60 槽：断头路打通/盼BRT/断头路、网红打卡地/夜市摆摊/噪音扰民、堵车/内涝/停车难…）；表头 `.ov-kw-col-head` font-weight bold→400（细体，与内容区分）。
8. **skill 体系扩充**：web-design-guidelines + code-review-and-quality（npx 已装）；`~/.claude/CLAUDE.md` 全局规则（2 条）；4 个 claude-plugin **待回家装**（见顶部）。

## 当前状态
- 分支 `main`，**已 push**（本批 `5cdd36b` feat + docs 本提交；origin/main 已同步）。
- **24 个前端 JS `node --check` 全过**；本会话**未跑 pytest**（仅前端 JS/CSS 改动 + 承重保护，无 Python 改动；下机前如要保险可 `py -m pytest tests/ -q`）。
- **未 F5 实测**：batch-2 全部视觉/交互待肉眼验（互斥切换、橙柱选中、三处橙框、i 浮窗跨栏、3D 不重叠、关键词 Top10）← **回家装完 skill 后 F5 验**。
- skill 产物 `.agents/` + `.claude/skills/{code-review-and-quality,web-design-guidelines}`(符号链接) + `skills-lock.json` **已 gitignore**（per-machine；换机重装）。
- `.gitignore`：`DATA/baidu-heatpoints/`、`DATA/raw/landuse/`、`SCRIPT/poi_data/amap_poi_centralcity_wgs84.json` 仍忽略；换机重跑 `ingest_landuse_preset.py`（map.json 就绪）复现用地 preset。AMAP_KEY 已配不动。

## 承重（本会话新增/强化，勿破）
- **`enforceMutualExclusion`**（[`state.js`](frontend/js/state.js)）：严格 `isRangeLayer` 跳过（Range 永不被动关）；不动同 parentId 的 L2 极性兄弟。`generateGrid` 清场与 `setViewMode` 视角切换仍解耦（承重 [[generate-grid-exclusive-vs-viewmode]] 不破，二者各自调 enforce）。
- **`pickHLCell`/`focusCell`**（[`tip-popup.js`](frontend/js/tip-popup.js)）：HL 层（`cell-hl-set-layer`）无注册层身份，靠 `_hlLayer`（_applyHL/focusCell 写入）配对注册层；橙柱命中优先于 `pickCellFeature`。focusCell 高度=原柱 mh（非 ×2），与 sticky 拔高(_applyHL mh*2) 区分。
- **"i" 浮窗 `#info-i-tip`**（[`panel.js`](frontend/js/panel.js) `_initInfoTip` + [`panel.css`](frontend/css/panel.css)）：单例 append body，事件委托 document（含动态渲染的 .info-i）。`.info-i::after` 纯 CSS tooltip 已删（别回退，会被 overflow 裁切）。
- **hover overlay 不透明 1.0**（[`tip-popup.js`](frontend/js/tip-popup.js) `showCellHover` 3D）：修两色重叠/穿模；别改回 `extrusionOpacity`（半透明必叠影）。
- **关键词橙框挂 track**（[`panel.css`](frontend/css/panel.css) `.ov-kw-item.is-sticky .ov-kw-track`）：fill 在 `overflow:hidden` 内被裁，框必须挂 track。

## 承重（前会话，仍有效）
- **演示数据引擎** `sim_performance_data.py`(scale 0.639)；**PRESET_COLORS 单源**；**isRangeLayer 独占保 Range**；**工具要素按钮 toggle-close=`isToolPanelEditing`**；**右栏不自动弹**（layer:selected/cell:selected 仅 activateTab+refresh）；**tip liveUi**（`liveUi()` 每事件重读 layer.paint._ui）；**预设 split-pill**；**zonal 4×5 `_attach_4x5_attrs`**；**AI provider-agnostic**；**Overview isAnalysisLayer=_ui.tool**；**heightOf**（pc≤2 线性/pc≥3 offset+sqrt，maxHeight 2000/上限 4000，分极性 `_grid_h_pos/neg/neu`）；**视角按钮 toggleGridViewMode**（同 sig 互斥，配对层接替槽位）；**3D 跳 fill**；**切视角必 reorderLayers**；**cell-popup kv `.kv-row`**；**4×5 单源 poi_4x5_map**；**放大镜外环 geocode-loader**；**Range popup 收起反转**；**色段取色器 renderColorPicker**；**Range 线宽 1+hover2**；**影像无注记底图**；**图层行单击弹栏双击 fitToLayer**。
- **Overview 双层 sub-Tab**（panel.js setOverview→#ov-layer-pane / setCellOverview→#ov-cell-pane，activateOvTab {silent}，勿回退单容器覆写）；**easeToCell _cellModeZoom 进入单元层固定一次**（切格只 pan 不抬）；**Overview→地图同步高亮 tip-popup highlightCellSet/toggleStickyHighlight**（橙 #ff9000、opacity 1.0、3D mh*2 拔高；独立于 showCellHover；layers:changed/cell:cleared→resetHighlightCellSet）；**_cellsByPolarity 阈值**（点数>10/neu>1 且占比>40%）；**_piColor Material 600**（中性蓝非灰）；**关键词 3 列色 is-pos/is-neu/is-neg=绿/蓝/红 同矩阵**；**Range 图例矩形**（legend.css .range-dot + refreshLegend 同步线/填充+层名）。

## 下一步（待用户定；候选）
- **【回家装 skill · 最高优先】** 见顶部「本机待办」。
- **【待 F5 验 batch-2】**：start.bat → 导入 L1/L2 → 生成网格 → 验：① 图层互斥（开网格→点层自动隐；开分析→其他分析隐；切层 Overview 即时切换；Range 始终留；2D↔3D 不串台）② 点橙柱命中正确格 + 进深读该格橙原高/其他消失/饼图 sticky 取消 ③ 三处选中橙框（饼图/矩阵/关键词横条）④ "i" hover 跨右栏浮于地图上方、浅灰底深灰字 ⑤ 3D 悬停升起无两色重叠/穿模 ⑥ 关键词 Top10 + 表头细体 ⑦ 去"数据分析"、count 单行无省略、横条深灰数字、矩阵全称+新序+左齐、饼图图例整体居中。
- **关键词措辞微调**：`KEYWORD_TABLE`（state.js）某桶词若不顺眼，用户说「pos: X 换 Y」改对应 `domain|element|sign` 键。
- **更新单元干净矢量**（用户重导 → 替换 `presets/更新单元.geojson`）；**Task5 AI 问答重做**；**POI/地名纠错**（后期）。

## 新会话 prompt（复制即用）
```
续 main 分支（HEAD=本批 docs 提交，Overview batch-2 精修 已 commit+push，origin/main 同步）。读 memories/repo/session-handoff.md（最新快照 + 承重）。

本会话任务：<在此填。候选：F5 验 batch-2 后微调 / 关键词措辞微调 / Task5 AI 问答 / 更新单元干净矢量 / POI 地名纠错 / 回家装 skill 后续配置>

要点：①图层互斥 enforceMutualExclusion(state.js: B 分析层互斥/A↔B 不共存/A 同源极性保留/保 Range)接入 sidebar 眼睛+工具生成+toggleGridViewMode；refreshOverview 追随可见层(选中不可见→回退最顶可见)；②橙柱命中 pickHLCell(tip-popup,HL 层配 _hlLayer)+focusCell(单格橙原高 mh)；popup click/hover 优先橙柱；cell:selected 清 .is-sticky；③选中橙框 #ff9000 4px(饼stroke/矩阵inset/关键词挂 track 防 overflow 裁切)；④"i" 浮窗 #info-i-tip(position:fixed 单例,panel.js _initInfoTip,别回退 CSS ::after 会被 panel-body overflow 裁)；⑤3D 悬停 overlay 不透明 1.0(修两色重叠/穿模)；⑥关键词 Top10(KEYWORD_TABLE 用户勾选 30 词按 4×5 桶)+表头细体；⑦承重：isRangeLayer 独占保 Range/generateGrid 清场与 setViewMode 解耦/heightOf/tip liveUi/右栏不自动弹/双 sub-Tab/easeToCell _cellModeFixed/highlightCellSet mh*2 拔高。
注：DATA/baidu-heatpoints + DATA/raw/landuse + amap_poi_centralcity_wgs84.json 已 gitignore；换机重跑 ingest_landuse_preset.py 复现用地 preset。AMAP_KEY 已配不动。skill 产物(.agents/+.claude/skills 符号链接+skills-lock.json)已 gitignore per-machine。
计费按调动次数，工作方式见 ~/.claude/CLAUDE.md（不派 subagent、优先用 skill）。
```

## 承重 memory 索引（本会话相关）
- 本会话强化：`view-data-conclusion-sync`（Overview 追随可见层/互斥/橙柱选中）、`design-language-consistency-iron-rule`（三处橙框统一）、`tip-popup-unified-hover-design-language`、`frontend-default-light-theme`（chrome 白底）、`no-routine-playwright-verify`（实现→交付→F5）、`no-handoff-on-routine-commit`（说"交接"才覆写本卡）、`todo-revision-log-sync`
- 前会话承重：`extrusion-height-maxheight` / `grid-palette-tuning` / `maplibre-query-array-stringify`（pickCellFeature 读数组/非注册层陷阱）/ `terrain-mesh-rendering` / `grid-4x5-attribution` / `verify-real-endpoint` / `capsule-button-design-language` / `tool-layer-convention` / `generate-grid-exclusive-vs-viewmode` / `kde-loadbearing-logic`
