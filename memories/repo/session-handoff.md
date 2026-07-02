# 会话交接卡

> 换机/新会话后读取此文件恢复上下文。**单份当前快照**——每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：2026-07-02 | 分支 `main`（feature/kde-l2-3d 已合并删除，现单分支工作流）

## 上一节点（07-02）—— 演示链三件套 + 收尾修复（已 commit c16b071 + 746c331，**已 push origin/main**）

本会话三块大功能 + 三轮修复，串行做透：

**Task 演示链三件套**（commit 51faa0c）：
1. **指定范围·极性+归因分析**：后端 `aggregate_by_polygons` 抽 `_attach_4x5_attrs` helper 补 **4×5 归因**（原仅 square_grid/terrain 有）+ `polygon_name_col` dead param 落地为 `name`；预设范围库 `DATA/boundaries/presets/manifest.json`（行政区/街道/社区/更新单元/用地占位）+ 端点 `GET /range/presets`、`/range/preset`、`POST /range/preset/upload`；前端 `range-presets.js` 渲 Range tab 胶囊 + `grid-tool.openGridDialog(layerId,preset)` zonal 预填。
2. **Overview/Table 升级**（保留右栏双 tab）：分析层（grid/zonal/terrain）tier3 故事化（极性聚合计数柱 + **4×5 归因矩阵热力** + **Top5 问题聚集** + 治理要素分布）；Table 按层自适应（点层=geojson.io 表 / 分析层=**可排序问题清单表**，点行飞到+cell:selected）。
3. **AI 问答**：`core/llm_client.py`（provider-agnostic，httpx SSE，**未来换溯佰科改 base_url/model/key 一处**）+ `core/chat_context.py` grounding + `POST /chat` SSE；`chat-panel.js` 底部滑出（marked markdown + `[ref:区域名]`→可点 chip 定位 + 多轮 + 引导提问胶囊）。

**收尾修复**（commit 7caa038 / c16b071）：
- tip-popup `fillContent` 改 `liveUi()` 实时读 `layer.paint._ui`（修要素按钮调边长后 tip 边长不更新；`showCellHover` 早已 live，fillContent 漏修）
- 右端栏（Overview/Table）**不再自动弹开**：移除 `layer:selected`/`cell:selected` 的 `openRightPanel()`；仅 `.collapse-right` 手动开合
- 预设按钮改 **split-pill**：主按钮（可用→载入分析 / 待上传→上传）+ 常驻 "+"（始终上传/替换，已上传范围的永久重传入口）；替换语义=移除同名旧层
- **范围层自动配色**：`PRESET_COLORS` 迁 state.js 单源；`addLayer` 对 polygon/line 非分析层按已有数循环配色（分析层 grid/terrain 保 NAVY 不占槽）
- 默认面域透明度 **30%→15%**（`addLayer` + settings popover；buffer 本就 0.15）
- **工具层要素按钮 toggle-close**（设计语言统一）：heatmap/grid/buffer/terrain `[data-feat]` 再点同层关 param-panel（`isToolPanelEditing` = panel 开+激活 tab+`{tab}-dialog.editLayerId===id`），镜像 point/line/range 的 settings popover toggle

## 当前状态
- 分支 `main`（单分支工作流，feature/kde-l2-3d 已合并删除），HEAD = `746c331` = origin/main（**已 push**；c16b071 / 7caa038 均在远程）
- 家里会话（07-02 晚）：`git pull` 同步办公环境合并 + 清理本地废弃 feature 分支，工作区 clean，单分支干净
- 用户上传了真实预设 `DATA/boundaries/presets/更新单元.geojson`（已入 c16b071，可激活"更新单元"按钮）
- 静态全过：11 JS node --check；pytest 113 过 / 5 预先存在（h3/SnowNLP/geocode）零回归
- **未 F5 实测**：Task 三件套 + 收尾修复全待用户 start.bat + F5 肉眼验 ← **晚上优先项**

## 承重（本会话新增，勿破）
1. **PRESET_COLORS 单源在 [state.js](frontend/js/state.js)**（settings.js import + re-export；buffer-tool 经 re-export 复用）。`addLayer` 自动配色仅对 **polygon/line 非分析层**（无 `paint._ui.tool`）按已有同类层数循环；grid/terrain（有 `_ui.tool`）保 NAVY 不占槽、不走 palette
2. **默认面域透明度 0.15**：`addLayer` polygon default + settings popover 兜底 `?? 0.15`；buffer DEFAULTS 本就 0.15。fillOn toggle 只设 fillOn 不动 fillOpacity → 由默认兜底
3. **工具要素按钮 toggle-close = `isToolPanelEditing(tool,id)`**（[sidebar.js](frontend/js/sidebar.js)）：param-panel.is-open + `.pp-tab.is-active` 对应 tool + `{tab}-dialog.dataset.editLayerId===id`。tool→tab = {heatmap,grid,buffer} / terrain→heatmap。与 settings popover toggle **同设计语言**（用户铁律：同按钮跨场景交互必须一致）
4. **右端栏不自动弹开**：`layer:selected`/`cell:selected` 仅 `activateTab+refresh`，不调 `openRightPanel()`（已删 import）。手动开合仅 `.collapse-right`
5. **tip-popup 全 live 读**：`bindTipPopup` 的 `liveUi()` 每事件重读 `layer.paint._ui`；fillContent（cellSize/mode）+ showCellHover（maxHeight）都用 live，闭包 ui 仅 fallback
6. **预设 split-pill**：主按钮 data-action=load|upload，"+" data-action=upload；triggerUpload 解析→上传→renderRangePresets→loadPresetRange（替换=移除同名"范围·{label}"层）
7. **zonal 4×5 归因**：`aggregate_by_polygons` 调 `_attach_4x5_attrs(joined,grouped,agg_stats)`（与 create_square_grid 同源 helper）；`polygon_name_col`→输出 `name` 字段。fillna 按 dtype（数值填 0，字符串归因列填 ''）
8. **AI chat provider-agnostic**：`core/llm_client.py` `LLMClient`，DeepSeek 默认（base/model/key env），换溯佰科改三参；`POST /chat` SSE（data:{token}/[DONE]/data:{error}）。**DEEPSEEK_API_KEY 走 shell env（无 dotenv 自动加载）**，缺 key 优雅报 SSE error。前端 `streamChat` fetch+ReadableStream 解析；grounding=前端从选中分析层算摘要回传
9. **Overview isAnalysisLayer = `paint._ui.tool in [grid,terrain]`**（NOT layerLevel——layerLevel 对所有 polygon 返回 'range'）；分析层 tier3 用 n_* 聚合计数（非逐条 polarity），score 用 score_mean
10. **grid-tool `openGridDialog(layerId, preset)`**：preset={analysis:zonal, polygonLayer, nameCol} 强制 zonal 卡 + 预选面域 + name_col（preset 走 `params = preset?{...DEFAULTS,analysis}:...`）

## 承重（前会话，仍有效）
- **高度算法 `heightOf`**（grid-tool preprocessGrid）：pc≤2 线性 `val×0.025`（1→50m/2→100m），pc≥3 `((pc-2)/(max-2))^0.5`；`maxHeight` 默认 2000/上限 4000；分极性 `_grid_h_pos/neg/neu`；`filterPolarityZero` 去 0 点格
- **L2 极性网格语义**：颜色 field + heightField 同源 = 该极性点数（`_grid_h_pos`，非占比）
- **色板**：L1 grid-warm renorm `[0/0.15/0.30/0.50/0.78/1.0]`；green/red/blue-3 = `gradientStops(TERRAIN_*,6)`；3D `FOV55 + setLight([1.5,45,60],0.5)`；`#map` 背景随底图。piToNorm 固定分段（grid+terrain 同步）
- **视角按钮 = `toggleGridViewMode`**（针对 sig、不依赖 visible）；配对去重 `_sigGroups`（不论可见，代表：可见优先→`getGridViewMode`→最后）；`setViewMode`（左下角）两函数并存
- **3D grid 层跳 fill**（`fillOn && !isTool3d`）；**切视角必 `reorderLayers(pair.id, l.id)`** 接替槽位
- **cell-popup kv = `.kv-row` 横排**（`_cellKvRows` 返 `[label,value,color?]`）；**`.popup` 自适应高度**（无 max-height/overflow-y）；**cp-loc 重置 line-clamp**

## 下一步（待用户在新会话定；候选）
- **【✅ push 已完成】** c16b071 + 746c331 均已在 origin/main（家里 07-02 晚 fetch 确认）
- **【待 F5 验】** 全批：start.bat（cd frontend）→ F5 → ①导入情绪点+上传边界（更新单元已就绪）→ zonal 聚合→popup/Overview 显归因 ②多范围层色不同+填充 15% ③要素按钮调边长 tip 同步 ④点要素按钮不弹右栏 ⑤heatmap/grid/buffer 要素按钮再点关闭 ⑥配 DEEPSEEK_API_KEY 后右下"问答"试问
- Overview 矩阵/Top5 视觉打磨；AI 问答 prompt 调优（引用 chip 命中率）
- 接入溯佰科规划大模型（换 llm_client base_url/model/key）；L3/L4 LLM 归因上线后删 `_ATTRIBUTION_RULES` 规则表

## 新会话 prompt（复制即用）
```
续 main 分支（HEAD=746c331=origin/main，演示链三件套+收尾修复已 commit+push，单分支干净）。读 memories/repo/session-handoff.md（最新快照 + 承重）。

本会话任务：<在此填。候选：F5 验后微调/Overview 视觉打磨/AI prompt 调优/接入溯佰科/range tooltip 迁移 tip-popup>

要点：①PRESET_COLORS 单源 state.js，addLayer 仅 polygon/line 非分析层循环配色；②默认面域透明度 0.15；③工具要素按钮 toggle-close=isToolPanelEditing（镜像 settings popover toggle，设计语言一致是用户铁律）；④右端栏不自动弹开（仅 .collapse-right 手动）；⑤tip-popup liveUi() 实时读 paint._ui；⑥预设 split-pill 主按钮+"+";⑦zonal 调 _attach_4x5_attrs 补 4×5 归因；⑧AI chat provider-agnostic（llm_client，DeepSeek 走 shell env 无 dotenv）；⑨Overview isAnalysisLayer=_ui.tool 非 layerLevel；⑩承重：heightOf/maxHeight/_grid_h_pos/视角按钮 toggleGridViewMode/3D跳fill/reorderLayers/cell-popup kv-row。
计费按调动次数，工作方式见 ~/.claude.md（不派 subagent）。
```

## 承重 memory 索引（本会话相关）
- `extrusion-height-maxheight` / `grid-palette-tuning` / `generate-grid-exclusive-vs-viewmode`（前会话承重）
- `tip-popup-unified-hover-design-language`（本会话加 liveUi 全 live 读）
- `maplibre-query-array-stringify` / `terrain-mesh-rendering` / `grid-4x5-attribution`（zonal 现也产归因）
- `verify-real-endpoint`（zonal 归因打真 POST 实测）
- 新建议存：**设计语言一致性铁律**（同按钮跨场景交互必须一致）→ 待写 Auto Memory
