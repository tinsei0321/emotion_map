# geojson.io 借鉴参考（一页速查）

> 用途：把 docs/geojson.io/ 源码里**可借鉴的点**固化在此，**后续开发查本文件即可，不必再翻那个文件夹**（省 token）。
> geojson.io = Mapbox-GL + React + TypeScript + jotai + Deck.gl 渲染层。底层**完全自实现绘制**（不用 mapbox-gl-draw）。
> 可移植性图例：🟢 纯逻辑/UX 可直接搬到原生 JS｜🟡 需改造｜🔴 React/Deck/jotai 强绑定，仅思路参考。

---

## 1. 绘制（已移植 → frontend/js/draw-tool.js）

geojson.io 绘制 handler 在 `app/lib/handlers/{polygon,rectangle,line,point,circle}.ts`，自实现，可移植。

| 点 | 源（docs/geojson.io/）| 移植到 | 状态 |
|----|------|--------|------|
| Mode 枚举状态机 | `state/mode.ts:7-15`（NONE/DRAW_POINT/LINE/POLYGON/RECTANGLE/CIRCLE/LASSO + ModeOptions）| state.js `_mode` + getMode/setMode/isDrawActive | ✅ |
| 全局快捷键 | `app/hooks/use_map_keybindings.ts:37-137`（1-6 切模式 / Esc 取消 / Enter 完成 / Del 删除 / Cmd-Z 撤销）| draw-tool.js onKeyDown（Esc/Enter）| ✅ Esc/Enter（数字键未接） |
| 多边形完成三判定 | `app/lib/handlers/polygon.ts:83-116`（点起点 `slice(0,-2)+first`）/ `:223-253`（dblclick `splice(-3,2)`）/ `:254-269`（Enter）| draw-tool.js onClick/onDblClick/finishPolygon | ✅ |
| closePolygon | `app/lib/map_operations/close_polygon.ts:9-18`（ring>4 时 `slice(0,-2)`，append firstPoint）| draw-tool finishPolygon | ✅ |
| 橡皮筋临时点 | `polygon.ts:184-195`（ring 末位=光标，move 更新，完成剥除）| draw-tool setPolygonTemp | ✅ |
| 矩形拖拽 | `app/lib/handlers/rectangle.ts:14-128`（down 记起点→move 4 角→up；Shift 锁正方形）| draw-tool onMouseDown/Move/Up + rectCorners | ✅ |
| 光标样式/提示文案 | `map_component.tsx:432-447` / `mode_hints.tsx` | toolbar.css .draw-hint + canvas cursor | ✅ |
| e6 坐标精度 | `app/lib/geometry.ts:316-327`（`Math.round(x*1e6)/1e6`）| draw-tool e6/ll2coord | ✅ |
| Shift 正角度锁 | `use_held.ts lockDirection`（角度吸附 45° 倍数）| — | ⬜ 未接（可选 polish） |
| 吸附 snap | `app/lib/handlers/utils.ts:167-192`（turf nearestPointOnLine + polygonToLine）| — | ⬜ 跳过（画边界不需要；接时要 turf + queryRenderedFeatures 替 Deck pickMultipleObjects）|
| 点/线/圆 handler | `handlers/point.ts` / `line.ts`（同 polygon 的 click-click-dblclick）/ `circle.ts`（makeCircle 三类型）| — | ⬜ 后续（架构已留 setMode 分支） |

> Deck.gl→MapLibre 替换点：`pmap.overlay.pickMultipleObjects` → `map.queryRenderedFeatures(point,{layers})`；`map.unproject` 同义。

---

## 2. 几何工具（纯逻辑，后续可移植，多走后端 geopandas 替代）

geojson.io 的几何操作多数是 turf 调用 + 自实现，部分可前端移植、部分建议后端 geopandas（我们已有 buffer 后端范式）。

| 工具 | 源 | 我们现状 | 建议 |
|------|-----|---------|------|
| 面积/周长 | `feature_editor/geometry/polygon_area.tsx`(turf area) / `line_geometry.tsx`(turf length) | popup.js geomStats **已自实现球面面积+Haversine**（无 turf）| 已够用 |
| Buffer | `lib/buffer.ts` + `dialogs/buffer.tsx`(turf buffer, Web Worker) | **后端 core/buffer_analysis.py geopandas EPSG:4546** ✅ | 维持后端 |
| 简化 simplify | `lib/map_operations/simplify.ts:31-259`（**自实现 Douglas-Peucker + radial dist**，无 turf）| ⬜ | 🟢 可前端移植（纯算法，无依赖） |
| 画圆 circle | `lib/circle.ts:216-261`（**自实现** Mercator/Geodesic/Degrees 三类型）| ⬜ | 🟢 可移植（配合 circle 绘制 handler） |
| 合并 merge | `lib/map_operations/merge_features.ts`(turf union) | ⬜ | 🟡 后端 geopandas overlay.union 更稳 |
| 质心 centroids | `lib/map_operations/draw_centroids.ts`(turf centroid) | ⬜ | 🟡 后端 geopandas centroid |
| 标注点 label points | `lib/map_operations/draw_label_points.ts`(turf pointOnFeature) | ⬜ | 🟡 后端 |
| 大圆弧 great arc | context_actions（2 点画弧）| ⬜ | 🔴 niche，暂不 |
| 坐标精度 e6 | `lib/geometry.ts:316` | draw-tool ✅ | — |

---

## 3. Table / 要素编辑器 / 右键菜单（后续任务思路）

**Feature Table**（`app/components/panels/feature_table.tsx`）🔴 React+@tanstack/react-virtual+Formik+Fuse.js，仅思路：
- 虚拟滚动（大数据必备）；列宽自适应（`measureColumn`：扫每列最长字符串 × 字宽）。
- 属性列编辑 + 增删列 + 搜索（Fuse.js 模糊）。
- 行 = feature，列 = properties + 几何摘要。
- → 我们 Table 任务（任务树「Table 数据表格」）借鉴：虚拟滚动 + 列宽测量思路，用原生 JS 重写。

**Feature Editor**（`feature_editor.tsx` + inner/geometry/properties/style/data tabs）🟡 UI 结构可借鉴：
- 5 tab：Geometry（面积/周长/bbox/顶点数）/ Properties（键值编辑）/ Style / Data（原始 GeoJSON）/ ID。
- 顶点编辑 `feature_editor_vertex.tsx`（拖拽顶点）—— 与绘制 handler 同套 vertex 模型。
- → 我们要素设置弹窗（Import 的 Kepler 设置弹窗）已部分覆盖 Style；Properties/Data 编辑待 Table。

**Context Actions 右键菜单**（`context_actions/geometry_actions.tsx:54-271`）🟢 动作清单 + 适用条件可移植：
- Zoom to / Divide / Add inner ring / Buffer / Duplicate / Great arc / Delete / Centroids / Label points / Merge。
- 每动作 `applicable` 按选中要素的几何类型/数量判定。
- → 我们未来右键菜单直接抄这份动作清单 + 条件判断（UI 用原生 dialog/popover）。

---

## 4. 不可移植（仅思路）

- **React 组件树 + jotai atoms**（state/jotai: modeAtom/selectionAtom/dataAtom）🔴 → 我们用 state.js + CustomEvent 总线（layers:changed / layer:selected / layer:paint）。
- **Deck.gl 渲染层** 🔴 → 我们用 MapLibre GL JS（source/layer/circle/fill/line）。
- **@tanstack/react-virtual 虚拟滚动** 🔴 → Table 任务原生实现或轻量库。
- **react-hotkeys-hook** 🟡 → 原生 document keydown（draw-tool 已示范）。

---

## 5. 关键文件索引（需要细节时定向读，勿全翻）

- 绘制 handler：`app/lib/handlers/{polygon,rectangle,line,point,circle}.ts`
- 几何操作：`app/lib/map_operations/*.ts`（close_polygon/simplify/merge_features/draw_centroids/draw_label_points/buffer）
- 圆/工具函数：`app/lib/circle.ts`、`app/lib/geometry.ts`（e6/isRectangleNonzero 等）
- 模式/状态：`state/mode.ts`、`app/hooks/use_map_keybindings.ts`
- UI 组件：`app/components/{modes,mode_hints,map_component,keybindings,context_actions}.tsx`、`app/components/panels/feature_{table,editor}.tsx`
