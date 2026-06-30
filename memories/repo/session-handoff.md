# 会话交接卡

> 换机/新会话后读取此文件恢复上下文。**单份当前快照**——每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：2026-06-30 | 分支 `feature/kde-l2-3d` @ `cad4b25`（本批 push 后 = HEAD/origin 同步）

## 上一节点（06-30）—— Task 2.7 网格/地形 popup + tip-popup + Overview 接 4×5 归因（演示链"交互→识别"桥贯通）

**核心交付：聚合单元点击/悬停 → 两套 popup + Overview，4×5 归因（issue_label/domain×element/attribution/suggestion）端到端打通并 Playwright 真数据实测通过。**

1. **#cell-popup（点击持久卡，复用范围卡模式）**：胶囊底色=该单元色板色（`rampColor(gridStops 拍平, prop[gridField])`）+ 类型词「网格/柱体/地形环」；右侧边长 `200×200m`（terrain→`等值环 L{x}`）；灰填充两行=地点（reverseGeocode 质心 `区域·poi`）+ 元数据（`L2·T1·综合·标准网格`，T 从源层 `_ui.source` 反查 `deriveTimeTag`）；kv 聚类口径（点数/聚类程度 `_grid_h` 高中低/[L2] 极性指数偏积极/..，**禁面积周长**）；折叠=类型词胶囊；归因不进本卡。
2. **#tip-popup（悬停浮动卡，新统一悬停设计语言）**：150×150 白底 4px 圆角高阴影、`position:fixed pointer-events:none`；**自适应方位**（视口左/右/上/下 40% 阈值选象限不遮挡）+ **灵动跳动**（hysteresis 位移>14px 才换位 + CSS `transition:left/top 120ms`）；3 行精简（地点/口径·L2 积极·中性·消极计数着色/边长）；tool 层(grid/terrain)悬停改绑 tip-popup，**删 bindTerrainInteractions + dark terrain-tooltip CSS**。**未来 point/range hover 也迁移到此**（memory `tip-popup-unified-hover-design-language`）。
3. **Overview 单元模式**：点击 dispatch `cell:selected`→main.js 开右栏+`setCellOverview`（T1 issue 标题+domain×element / T2 极性 badge+点数分数置信度 / T3 归因+建议=识别问题深读）；`cell:cleared`（close 按钮/层隐删）→回 layer Overview；**点空白只折叠不消失**（collapseCellPopup）。
4. **click 路由**：`classifyMapClick` 在 range-visible 前加 `isCellFeature`（fill+fill-extrusion 同 source 解析）→'cell'；3D 柱/环 click 走 `queryRenderedFeatures` 免单独绑定。

**首轮实测 5 连 bug 修复**（Playwright 真实导入 L2 T1+生成网格复现，**字段全对、纯前端 bug**）：①size 行 `textContent` 赋 HTML→字面化（改 innerHTML）；②tip 卡左上角=onMove 没 showEl+mouseenter 未触发（onMove 也 showEl+坐标 fallback）；③地点永「定位中」=mousemove 高频 `++_geoToken` 作废在途 + **MapLibre queryRenderedFeatures 把数组 property 序列化成字符串**（`_center` source 数组→query 字符串）→key 去重+`Array.isArray` 防御；④cell-popup 全空+Overview 不切=**`let口径;`（let 后无空格+中文）被词法器吞成单标识符 `let口径`**，运行时 ReferenceError（node --check 查不出）→改英文 `mood`；⑤点外部消失=误调 hideCellPopup→改 collapseCellPopup。**实测通过**：hover tip 跟鼠标（left468/top307 vs 鼠标452,291+16px）+loc「通用市区·凝聚新天地」+size「200×200m」+metric「2/1/1」；click cell loc/meta/kv 全显+Overview issue「情绪聚集区」+attribution；点空白 collapsed=true hidden=false。

## 当前状态
- 分支 `feature/kde-l2-3d` @ `cad4b25`，origin 同步（已 push）
- 后端 :8000 + 前端 :8080 在线。**后端已加载 ce13da2 新聚合代码**（实测格子含 domain_top/issue_label/attribution 全对——`urban_operation`/`event`/`情绪聚集区`）
- 用户 F5 即可看 Task 2.7 效果（前端 no-cache 自动拉新；后端无需再重启）

## 承重注意事项（踩坑，勿重复）
1. **演示逻辑链是北极星**（CLAUDE.md 最高优先级）：张力=表现力、4×5 归因=有用性、popup+Overview=交互桥。memory `emotion-map-logic-chain`
2. **JS 中文变量名陷阱**：`let口径`(let 后无空格+中文)被吞成单标识符，`node --check` 查不出、运行时 ReferenceError。**变量名一律英文**（中文只进字符串/对象 key）。memory `js-chinese-identifier-trap`
3. **MapLibre queryRenderedFeatures 的 properties 只支持标量**：数组/对象字段（如 `_center`）会被序列化成字符串；读数组 property 必 `Array.isArray` 校验或从 geometry 现算。memory `maplibre-query-array-stringify`
4. **`textContent` 赋 HTML 字符串=字面化标签**：HTML 内容必走 `innerHTML`，纯文本才 `textContent`
5. **mousemove 高频回调里发异步请求须按 key 去重**（cache+inflight），token 不能在每次回调自增（会作废全部在途）
6. **`node --check` 只查语法不查运行时**：前端改动（尤其交互/异步/控制流）**必上 Playwright 真数据实测**才能抓 bug；纯加载自检（0 console 错）不够
7. **tip-popup 是统一悬停设计语言**：tool 层(grid/terrain)已接入；未来 point/range hover 迁移到此，别再造 maplibregl Popup/dark tooltip。memory `tip-popup-unified-hover-design-language`
8. **`_norm`/`_grid_norm` 对称拉伸须 grid+terrain 同步**（同公式 `0.5+sign(pi)·min(1,|pi|/p95)·0.5`）。memory `symmetric-norm-stretch`
9. **l1_confidence 用局部密度 dens_norm**（amap POI weight 恒 1.0）。memory `confidence-local-density`
10. **POI 已预映射 domain/element 直接读 seed**；勿用 `poi_4x5_map._L1_FALLBACK`（高德类名不匹配全 fallback）。memory `grid-4x5-attribution`
11. **4×5 归因在聚合层**（DEMO 规则表 `_ATTRIBUTION_RULES`），L3/L4 LLM 归因上线后删表；字段在格 properties 供 popup/Overview
12. terrain 渲染走 fill-extrusion（高度 `_level`/maxHeight 绝对米）；memory `terrain-mesh-rendering`/`extrusion-height-maxheight`
13. 工具生成不弹 Overview（不 dispatch `layer:selected`）；`generateGrid` 独占 vs `setViewMode` 配对=两独立场景。memory `tool-no-auto-overview`/`generate-grid-exclusive-vs-viewmode`
14. 后端聚合数值列必须 `pd.to_numeric(coerce)`；后端无 `--reload`，改 `core/` 后须 start.bat 重启。memory `spatial-aggregation-numeric-coerce`

## 下一步（待用户在新会话定；候选，按优先级）
- **【用户已 flag】#6 L2 地形渲染重做**：用户反馈"完全没法用，算法+渲染方式都要重做"，先放一放待用户展开期望效果（KDE 等值面表达？高度/着色/密度算法换思路？）。**本周待讨论重点**
- **tip-popup 扩展到 point/range hover**（统一设计语言落地，模块已可复用 `bindTipPopup`+`fillContent` 按层类型分支）
- **修 `_L1_FALLBACK` 高德类名缺口**（补"餐饮服务/购物服务/风景名胜"等高德 13 类 key，小修）
- **Task 2.2 时间轴架构** / **Task 3 热点图**（map.js addHotpointLayer 半成品）

## 新会话 prompt（复制即用）
```
续 feature/kde-l2-3d @ cad4b25（Task 2.7 网格/地形 popup + tip-popup + Overview 已 push 并 Playwright 实测通过；演示链"交互→识别"桥贯通）。读 memories/repo/session-handoff.md（最新快照 + 承重 14 条）。

本会话任务：<在此填。建议「#6 L2 地形渲染重做」——用户已 flag "完全没法用，算法+渲染都要重做"，待用户展开期望效果>

要点：①当前地形=create_terrain_mesh(KDE 等值面 fill-extrusion，高度_level/着色_norm)，用户不满效果；②先与用户对齐"哪里不可用/期望什么效果"再动（算法层 KDE？渲染层 fill-extrusion→别的方式？）；③terrain 走 _norm 对称拉伸(勿破)、归因字段已在环 properties(tip-popup/cell-popup/Overview 已接)。

计费按调动次数，工作方式见 ~/.claude/CLAUDE.md（不派 subagent）。
```

## 承重 memory 索引（本会话新增 3 条）
- `js-chinese-identifier-trap` — `let中文`(无空格)被吞成单标识符，node --check 查不出、运行时 ReferenceError；变量名一律英文
- `maplibre-query-array-stringify` — queryRenderedFeatures 的 properties 数组/对象会被序列化成字符串；读数组 property 必 Array.isArray 校验
- `tip-popup-unified-hover-design-language` — 聚合单元悬停=浮动卡(自适应方位+灵动跳动)；未来 point/range hover 迁移到此
- （前批）`emotion-map-logic-chain`/`symmetric-norm-stretch`/`confidence-local-density`/`grid-4x5-attribution`
