# 会话交接卡

> 换机/新会话后读取此文件恢复上下文。**单份当前快照**——每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：2026-07-01 | 分支 `feature/kde-l2-3d`（本批 push 后 = HEAD/origin 同步）

## 上一节点（07-01）—— Task 2.16-2.21 视角按钮 + popup 缩高 + 多 bug hotfix

**核心交付：图层栏视角按钮（替左下角 2D/3D）+ 配对去重合并显示 + cell-popup 横排缩高 + 一串 bug 修复。** 本会话八项：

1. **极性 popup 聚焦该极性+4×5**（2.16）：cell-popup `_cellKvRows` 极性分支去"极性程度判断"行（图层已明示极性），加"治理要素 domain×element"+"问题识别 issue_label"；tip `tp-valence` 极性网格显"治理要素"（替综合判断）。
2. **视角按钮 + 配对合并**（2.16/2.17）：`modeChip` span→`button.layer-view`（字面=当前 2D/3D，参考要素按钮设计）；`renderLayerList` 按 gridSig 配对去重（`_sigGroups`，代表：可见优先→`getGridViewMode`最近切 mode→兜底最后）；2D/3D 合并显示一条。
3. **图层栏紧凑**（2.16）：`layerRowHtml` GRIP 移至 del 左侧；`.layer-row gap` → 1px。
4. **眼睛关闭后分裂+失效 bug**（2.17）：去重旧逻辑只跳"有可见配对的隐藏层"→都隐藏时分裂；`setViewMode` filter(visible) 空→视角按钮失效。修：去重按 sig 组（不论可见）+ 新增 `toggleGridViewMode(layerId)`（针对该 sig、不依赖 visible）+ `_lastGridMode`（sig→最近切 mode，选代表避切回选错）。
5. **3D fill 重叠"2D3D 同显"bug**（2.18）：`addPolygonPaint` 3D 时 `fillOn` 仍加 fill 色块（地面）+ extru 柱 → 视觉判"2D 3D 同显"。修：3D 跳过 fill（`if (fillOn && !isTool3d)`，柱体自含面不需地面色块）。
6. **cp-loc 换行被遮挡 bug**（2.19）：`.popup-text` 通用 `-webkit-line-clamp:2 + overflow:hidden`，cp-loc 继承致地点换行被切。修：`.popup-cell .cp-loc` 重置 `display:block + line-clamp:unset + overflow:visible`。
7. **popup 间距 2px + 自适应高度**（2.20）：popup-text margin-bottom / popup-kv gap / kv-row gap → 2px；`.popup` 去 `min/max-height + overflow-y:auto` → 展开自适应无滚动条。
8. **cell-popup 横排缩高 + 拖拽跳序修复**（2.21）：`_cellKvRows` 改返 `[label,valueHTML,color?]` 元组，渲染 `.kv-row`（grid auto 1fr，"属性：值"横排单行）；`.popup-cell .kv-v` 字号 2xs+bold（=属性字号、粗体）；删 cp-row dead CSS。拖拽后切视角跳序根因 `addLayer` push pair 末尾→修 `toggleGridViewMode`/`setViewMode` **每次切** `reorderLayers(pair.id, l.id)` 接替原层槽位（保拖拽顺序）。

## 当前状态
- 分支 `feature/kde-l2-3d`，本批 push 后 origin 同步
- 全前端（popup/sidebar/map.js + popup/sidebar.css + README）；前批 2.10-2.15 改 grid-tool/state/heatmap-tool/tip-popup
- 静态全过：node --check；**未 F5 实测**（Playwright :8080 = directory listing，serve.py 从项目根跑需访问 `/frontend/index.html`，环境问题未深究）→ 待用户 start.bat（cd frontend）+ F5 验

## 承重（本会话新增，勿破）
1. **视角按钮 = `toggleGridViewMode(layerId)`**（map.js，针对该 sig、不依赖该层 visible，配对可见性=原层可见性）；**配对去重** `_sigGroups`（不论可见，代表：可见优先→`getGridViewMode`→最后）；`setViewMode`（左下角 btnView，全局切可见 grid）两函数并存，勿混
2. **`_lastGridMode`**（map.js 模块级 Map）+ **`getGridViewMode(sig)`** export——切后记 sig→mode，sidebar 选代表用
3. **3D grid 层跳过 fill**（`fillOn && !isTool3d`），柱体自含面；2D 仍 fill
4. **cell-popup kv = `.kv-row` 横排**（`_cellKvRows` 返 `[label,value,color?]` 元组，渲染 grid auto 1fr）；`.popup-cell .kv-v` 字号 2xs+bold
5. **`.popup` 自适应高度**（无 max-height/overflow-y）；属性信息间距 2px
6. **cp-loc 重置 line-clamp**（display:block + unset），地点多行不截
7. **切视角必 `reorderLayers(pair.id, l.id)`** 接替原层槽位（保拖拽顺序，避免 addLayer push 末尾致跳序）

## 承重（前会话，仍有效）
- **高度算法 `heightOf`**（grid-tool.js preprocessGrid，全局含分极性）：pc≤2 线性 `val×0.025`（1→50m/2→100m），pc≥3 `((pc-2)/(max-2))^0.5`（3→237m 起、max→满高）；ref=max 零 clamp；`maxHeight` 默认 2000/上限 4000；分极性 `_grid_h_pos/neg/neu`（各自 max）；`filterPolarityZero` 去 0 点格
- **L2 极性网格语义**：颜色 field + heightField 同源 = 该极性点数（`_grid_h_pos`，非占比 `_grid_pos`）；popup 极性分支显该极性点数+治理要素
- **色板**：L1 grid-warm renorm `[0/0.15/0.30/0.50/0.78/1.0]=[#8B0000/#C92A20/#F06428/#FF9900/#FFC63C/#FFDF00]`（红段收窄）；green/red/blue-3 = `gradientStops(TERRAIN_*, 6)`；3D `setVerticalFieldOfView(55)` + `setLight([1.5,45,60],0.5)`（东北光）；`#map` 背景随底图（setBasemap 设）防 3D 上沿白条
- piToNorm 固定分段（替 p95）；改色 grid+terrain 同步；overlay 用同款 color 表达式（保 properties）；valenceColorOf 用 TERRAIN_*；点击选格走 pickCellFeature

## 下一步（待用户在新会话定；候选）
- **【待 F5 验】** Task 2.16-2.21 全批：start.bat（cd frontend）→F5→重生成网格，验视角按钮/合并/紧凑/popup 横排缩高/拖拽不跳序/眼睛关后不分裂
- **Overview 深化（项 4）**：展开分析→更有指向性结论+落地建议
- range tooltip 迁移 tip-popup / Task 3 热点图 / Task 2.2 时间轴

## 新会话 prompt（复制即用）
```
续 feature/kde-l2-3d（Task 2.16-2.21 视角按钮+popup缩高+多bug 已 push）。读 memories/repo/session-handoff.md（最新快照 + 承重）。

本会话任务：<在此填。候选：Overview 深化/range tooltip 迁移/Task 3 热点图/F5 验后微调>

要点：①视角按钮=toggleGridViewMode（针对sig不依赖visible）；配对去重 _sigGroups（代表：可见优先→getGridViewMode→最后）；setViewMode（左下角）两函数并存；②3D 层跳 fill（fillOn && !isTool3d）；③cell-popup kv-row 横排（_cellKvRows 返 [label,value,color?] 元组），kv-v 2xs bold；④.popup 自适应高度无滚动条，间距 2px；cp-loc 重置 line-clamp；⑤切视角必 reorderLayers(pair,l.id) 接替槽位；⑥高度 heightOf（offset=2+sqrt，1→50/2→100/3→237），maxHeight 2000/4000，分极性 _grid_h_pos；⑦L1 grid-warm renorm 红段收窄；green/red/blue-3 6 段；FOV55+东北光。
计费按调动次数，工作方式见 ~/.claude.md（不派 subagent）。
```

## 承重 memory 索引（本会话相关）
- `extrusion-height-maxheight`（高度算法 heightOf + L2 极性网格语义 + maxHeight 2000/4000 + 迭代教训）
- `grid-palette-tuning`（grid-warm renorm + green/red/blue-3 6段 + FOV55/东北光/#map背景）
- `generate-grid-exclusive-vs-viewmode`（generateGrid 独占 vs setViewMode 配对——本会话加 toggleGridViewMode 第三场景）
- `tip-popup-unified-hover-design-language` / `maplibre-query-array-stringify` / `terrain-mesh-rendering`（前会话）
