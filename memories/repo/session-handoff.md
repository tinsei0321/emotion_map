# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月06日 13:25 | 分支 `main` | HEAD=`ea8e66f`（**已 push**）

---

## 当前节点：任务1 完成（极性深读重构）→ 任务2 时间轴待新会话推进

### 本会话 Recap（07月06日 13:25，承 46250a6 → ea8e66f）
- **pivot**：用户否决上会话「Q2 推荐深读清单 + cluster①分级」（单格大头针思路延续），改为整体重构——**单元深读（单格级）→ 极性深读（极性·聚合域级）**。深读价值聚焦「支撑 4×5 什么行动」。
- **任务1 完成 + Playwright 验证全通过**（0 控制台错误）：
  - **Layers 子卡**：grid 类目拆「标准网格/指定单元」（`subGroupRowHtml`，2px gap，双击折叠）；层名瘦身 `T1·综合·file`。
  - **Toolbox 去极性**：删 `#grid-polarity-section`（仅综合可生成）；聚合面域下拉 `isRangeLayer` 过滤 + `（N 面）` label。
  - **极性深读 paint 就地切换**（替原设想 3 隐藏图层）：综合 fc 已带 `_grid_h_pos/neg/neu`+`_grid_n_pos/neg/neu`，切极性 = 改 `paint.gridField/gridStops/heightField`+`_polarityFilter`+`renderLayer`。生成时备份 `_overallPaint`。实测 MapLibre fill 层 filter `_grid_n_pos>0`⇄`_grid_n_neg>0` 切换正常。
  - **动态关键词 + 副本**：hover/选中矩阵块 → 查 `DATA/performance/polarity_deepread_keywords.json`（T1+T3 × 3 极性 × 20 块，规划/更新×设施/环境/文化块 4-6 词强项目味）填 `#ov-block-kw`。
  - **Tab 条 sticky**：`.ov-subtabs`(top:0)+`.ov-pol-tabs`(top:30px)。
- **承重全保**：`TOPIC_MATRIX_MAP`/双 sub-Tab(layer|polarity)/`easeToCell`/`highlightCellSet`/`_attach_4x5_attrs`/`enforceMutualExclusion`/KDE cascade-exclude/gridSig 配对/4×5 单源全有效。

### 任务2：极性深读·时间轴（T1→T3 成效动画）—— 待新会话推进

**核心决策点（新会话首问用户）**：地图 3D 柱体「起落」动画路线（三选一）：
- **A（推荐）** JS rAF + 每帧 setData 高度插值——贴现有 MapLibre fill-extrusion，demo 网格（数百格）顺，2000+ 格掉帧兜底阶梯淡入。
- **B** 重引入 deck.gl ColumnLayer + transitions——GPU 平滑最优，但与 [map.js:542-544](frontend/js/map.js)「弃 deck.gl 走 MapLibre」决策冲突，双渲染路径维护重。
- **C** 纯阶梯淡入（不补间柱体，opacity 交叉淡入）——最轻最稳，但无「起落」感。

**前置（任务2 大头）**：Overview 原地更新重构——`panel.js` tier1/2/3 从 innerHTML 字符串重建改为 DOM 原地值更新（find 元素、tween textContent/style）。任务2 面板数字/饼图/矩阵/关键词动画 + 本任务 hover 动态关键词都受益（可顺手起头）。

**副本已预置**：T1/T3 双副本已建（`DATA/performance/polarity_deepread_keywords.json`），任务2 时间轴直接复用（按 layer.timeTag 选对应 T）。

**设计要点（本会话已与用户商定）**：
- **一条通用时间轴**（非综合/极性两条）：Tab 条下，播放尊重当前 Tab（图层总览→演进综合；极性深读→演进当前极性）。
- **scrub 进度条 + 离散 T 停点**（非两个下拉框）：T1─T2─T3 点选跳转 + play/pause/prev/next。
- **播放起步切 3D**（柱体起落最有张力）；**错峰动画**（柱体 800ms → 数字/饼图/矩阵 600ms → 关键词淡入 300ms）。
- **只动关键 KPI**（总点数/积极/消极/中性 + 矩阵 + 关键词），非全统计（全动 = 噪音）。
- 色彩 `#3A5368` 主 / `#8B658B` 副（用 ui-ux-pro-max:ui-styling skill）。
- 可行性客观评估 + 设计批评见 plan 文件 `C:\Users\Hi\.claude\plans\main-head-46250a6-push-memories-repo-se-sequential-swing.md`（Phase 2 节）。

### 承重 memory 索引
- 本轮相关：`topic-table-frontend-sync`、`generate-grid-exclusive-vs-viewmode`（paint 切换勿与 2D/3D 耦合）、`kde-loadbearing-logic`、`no-handoff-on-routine-commit`（本非 routine，任务边界可覆写）、`todo-revision-log-sync`、`chinese-all-deliverables`、`push-not-redline`、`no-routine-playwright-verify`（本任务涉数据流已验）
- 前会话承重：`extrusion-height-maxheight`、`maplibre-query-array-stringify`、`terrain-mesh-rendering`、`capsule-button-design-language`、`tool-layer-convention`、`view-data-conclusion-sync`、`frontend-default-light-theme`、`martin-ui-redesign`、`three-page-architecture`

## 当前状态
- 分支 `main`，**已 push**（origin/main = HEAD=ea8e66f）。
- 工作树：净（commit 已含 11 文件；仅 untracked `polarity-deepread-negative.png` Playwright 截图 + `~/.claude/plans/...md` plan 文件，皆不入仓）。
- serve 已停（本会话验证后 netstat+taskkill 清了 :8080/:8000）。
- 未做：任务2 时间轴（见上）。

## 新会话 prompt（复制即用）
```
续 main（HEAD=ea8e66f，已 push）。读 memories/repo/session-handoff.md（任务1 完成→任务2 时间轴快照）。

任务：实现任务2「极性深读·时间轴」（T1→T3 成效动画演示）。先与我对齐两个决策点：
1. 地图 3D 柱体动画路线：A JS rAF+setData（推荐）/ B deck.gl 重引入 / C 阶梯淡入——三选一。
2. Overview 原地更新重构（panel.js innerHTML 重建 → DOM 原地 tween）作为前置先做。

设计要点（上会话已定）：一条通用时间轴（Tab 条下，非综合/极性两条）；scrub 进度条+离散 T 停点（非两下拉框）+ play/pause/prev/next；播放起步切 3D + 错峰动画（柱体→数字饼图矩阵→关键词淡入）；只动关键 KPI；色彩 #3A5368 主/#8B658B 副（ui-ux-pro-max:ui-styling）。副本 T1/T3 已预置（DATA/performance/polarity_deepread_keywords.json）。

承重：TOPIC_MATRIX_MAP/双 sub-Tab/paint 就地切换机制（_overallPaint 备份+_polarityFilter）/enforceMutualExclusion/gridSig 全保。详 plan Phase 2 + revision-log 5.25。

计费按调动次数，工作方式见 ~/.claude/CLAUDE.md（不派 subagent、批量并行、给推荐不穷举、常规前端改交付肉眼验）。时间戳写"MM月DD日 HH:MM"。
```
