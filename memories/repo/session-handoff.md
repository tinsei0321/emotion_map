# 会话交接卡

> 换机/新会话后读取此文件恢复上下文。**单份当前快照**——每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：2026-07-01 | 分支 `feature/kde-l2-3d`（本批 push 后 = HEAD/origin 同步）

## 上一节点（07-01）—— Task 2.7 交互桥修复+增强（cell-popup / tip-popup / hover 高亮 / 颜色校准）

**核心交付：聚合单元点击/悬停的 popup+浮动卡+高亮 全链路打通并校准颜色与极性判断一致性。** 本会话三批迭代（均本次 push）：

1. **交互桥修复+内容增强**：①**点击错格 bug**——`popup.js:pickCellFeature` 按 fill-extrusion>fill>line-hit 优先级选格（替 `feats.find(isCellFeature)`；根因 3D 下 queryRenderedFeatures 同时返回被遮挡邻格 base fill、2D 边缘命中 20px hit-line 串邻居），点击路由+tip 悬停共用。②**cell-popup**：地点改「区·街道·最近POI·距离」（后端 `reverse_geocode` always regeo `extensions=all` 返 district/township/street），drop 无效「通用市区」；移除「平均分数」（与极性指数重复+与置信度数值区间重叠）；kv 缩字号细体（对齐 Range）。③**tip-popup**：150→**120px**、地点同 cell-popup、计数上方加「极性判断」行、高度自适应（地点换行不被截）。④**state.js** 新增 `valenceOf`/`valenceColorOf`（5 级：非常积极/偏积极/中性/偏消极/非常消极）全站共用。⑤**悬停高亮**叠加层（复用 `showHoverRing` 模式）。
2. **3D 整柱升高动画**：`showCellHover` overlay 整柱 cellH→1.5×cellH native **transition 350ms**（`fill-extrusion-height-transition`），同色不透明。
3. **颜色彻底校准**（用户两轮反馈"颜色不准/未根治"后）：①**piToNorm 固定分段映射**（[grid-tool.js](frontend/js/grid-tool.js) + 后端 [spatial_analysis.py](core/spatial_analysis.py) `_pi_to_norm` 同公式）替旧 p95 对称拉伸——后者**数据相关致色带边界无法对齐 valenceOf 判断阈值=颜色不准根因**；pi=0→0.5、pi=±0.15→0.4/0.6、pi=±1→0/1。②terrain-9 中性段收窄对齐 pi±0.15。③**升起变色 bug**——overlay 改用**与格层同款 color 表达式**（`interpolate(linear,get(gridField),...stops)`+保留 properties；原 `rampColor` 均匀间距 ≠ MapLibre 实际 stop 位→变色）。④**点击保持升起**——`clearCellHover` 拆出 `hideTipPopup`，仅 mouseleave 触发。⑤`valenceColorOf` 改用 **TERRAIN_*[2]/[1]**（与 terrain-9 色带同源，修"字翠绿/卡深绿"不一致）。

**前序已 push（本会话早段）**：poi_4x5_map 高德单源（4766ccb）、tip-popup point 悬停（f0038a9）。

## 当前状态
- 分支 `feature/kde-l2-3d`，本批 push 后 origin 同步
- **未 F5 实测**（Playwright 环境阻断：:8080 当前=项目根 directory listing 非 serve.py + 缓存 chrome 1223 与 playwright 1.61.1 CDP 协议错配）。静态全过：node --check / py compile / piToNorm 数学验证 / pytest 10 passed（spatial）零新回归
- **用户须**：`start.bat` 起 serve.py → F5 → **重新生成网格/地形**（`_grid_norm`/`_norm` 在生成时计算，F5+重生成才应用 piToNorm）→ 肉眼验

## 承重注意事项（踩坑，勿重复）
1. **演示逻辑链是北极星**（CLAUDE.md 最高优先级）：张力=表现力、4×5 归因=有用性、popup+Overview=交互桥。memory `emotion-map-logic-chain`
2. **JS 中文变量名陷阱**：`let中文`(无空格)被吞成单标识符，node --check 查不出、运行时 ReferenceError。变量名一律英文。memory `js-chinese-identifier-trap`
3. **MapLibre queryRenderedFeatures 的 properties 只支持标量**：数组/对象字段（`_center`）被序列化成字符串；读数组 property 必 `Array.isArray` 校验。memory `maplibre-query-array-stringify`
4. **点击/悬停选格必走 `pickCellFeature`**（fill-extrusion>fill>line-hit 优先级）；勿用 `feats.find(isCellFeature)`——3D 遮挡邻格 base fill + 2D 边缘 hit-line 串邻居致错格
5. **`_norm`/`_grid_norm` 现为 piToNorm 固定分段**（替旧 p95 对称拉伸）：`piToNorm(pi)`（grid-tool）+ `_pi_to_norm`（后端）同公式，对齐 valenceOf 5 级阈值；terrain-9 色带中性段对齐 pi±0.15。**改色须 grid+terrain 同步**。旧 p95 拉伸已废（数据相关=颜色不准根因）
6. **悬停升起 overlay 必用格层同款 color 表达式**（`interpolate(linear,get(gridField),...stops)`+保留 feature.properties）；`rampColor` 均匀间距 ≠ MapLibre 实际 stop 位 → 升起柱变色
7. **极性判断字色须用 TERRAIN_*[2]/[1]**（valenceColorOf，与 terrain-9 色带同源）；勿用 L2 荧光色（字/卡不一致）
8. **node --check 只查语法不查运行时**：交互/异步/控制流改动必上 Playwright 真数据实测（本会话因环境阻断未跑，**待用户 F5 验**）
9. **l1_confidence 用局部密度 dens_norm**（amap POI weight 恒 1.0）。memory `confidence-local-density`
10. **POI→4×5 唯一权威源 = poi_4x5_map.AMAP_L1_TO_4X5**（旧百度 _L1_FALLBACK 死码已删勿复活）。memory `grid-4x5-attribution`
11. **4×5 归因在聚合层**（DEMO `_ATTRIBUTION_RULES`，L3/L4 接管后删表）；字段在格 properties 供 popup/Overview
12. terrain 渲染走 fill-extrusion（高度 `_level`/maxHeight 绝对米）；memory `terrain-mesh-rendering`
13. 工具生成不弹 Overview；`generateGrid` 独占 vs `setViewMode` 配对=两独立场景。memory `generate-grid-exclusive-vs-viewmode`
14. 后端聚合数值列必须 `pd.to_numeric(coerce)`；后端无 `--reload`，改 `core/` 后须 start.bat 重启。memory `spatial-aggregation-numeric-coerce`

## 下一步（待用户在新会话定；候选，按优先级）
- **【待 F5 验】** Task 2.7 交互桥三批：start.bat→F5→重生成网格/地形，验颜色(偏消极=红)/升起不变色/点击保持升起/字色对齐
- **Overview 深化（项 4）**——本周偏后：展开分析→更有指向性结论+落地建议
- **⏸ #6 L2 地形渲染重做 — 已搁置**：三出路性价比均低，待用户另议期望效果
- **range tooltip 迁移 tip-popup** / **Task 2.2 时间轴** / **Task 3 热点图**（map.js addHotpointLayer 半成品）

## 新会话 prompt（复制即用）
```
续 feature/kde-l2-3d（Task 2.7 交互桥修复+增强已 push：pickCellFeature 修错格 + cell/tip-popup 增强 + 3D 升起动画 + piToNorm 颜色校准；待 F5 重生成验）。读 memories/repo/session-handoff.md（最新快照 + 承重 14 条）。

本会话任务：<在此填。候选：Overview 深化(项4)/range tooltip 迁移/Task 3 热点图>

要点：①颜色已换 piToNorm 固定分段（grid-tool+后端同公式，对齐 valenceOf），terrain-9 中性段对齐 pi±0.15，**改色须 grid+terrain 同步**；②悬停升起 overlay 必用格层同款 color 表达式（保 properties，勿用 rampColor）；③valenceColorOf 用 TERRAIN_*；④点击选格走 pickCellFeature。
计费按调动次数，工作方式见 ~/.claude/CLAUDE.md（不派 subagent）。
```

## 承重 memory 索引（本会话相关）
- `js-chinese-identifier-trap` / `maplibre-query-array-stringify` / `tip-popup-unified-hover-design-language`（前批）
- `emotion-map-logic-chain` / `confidence-local-density` / `grid-4x5-attribution` / `spatial-aggregation-numeric-coerce` / `generate-grid-exclusive-vs-viewmode`
- 注：`symmetric-norm-stretch`（旧 p95 公式）已废，piToNorm 替代——见承重 note 5
