# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月06日 16:00 | 分支 `main` | HEAD=`3273aa7`（**已 push**）

---

## 当前节点：任务2 时间轴开发（T1→T3 成效动画）启动

### 承前（任务1 极性深读已落地 + 细化）
- 5.25 单元深读→极性深读重构（paint 就地切换、Layers 子卡、Toolbox 去极性、Tab sticky）。
- 5.26 review 修正（矩阵数单元、占比、关键词 .ov-kw-sp 卡片、地点 tip feature v1）。
- 5.27 地点锚定系统修（**数据为准**：副本只留地名，`_resolveLocAnchors` 点层 POI→cell，禁猜坐标）+ sticky 最高级（hover 不覆盖 sticky）+ 词点击柱体橙 + 消极 3x。
- 承重全保：`TOPIC_MATRIX_MAP`/双 sub-Tab/paint 就地切换（[paint-inplace-swap-view](memory)）/`_resolveLocAnchors`/`enforceMutualExclusion`/gridSig/sticky 最高级（[sticky-hover-priority](memory)）。

### ⬜ 并行待办（不阻塞时间轴）：地点 tip 全面核对修正
用户报 5.27 后"地点 tip 仍有大量错误"。**先放一放，记录到 `docs/todo.md` 07-06「明日任务」**。执行：审计副本 v3 所有 loc name → area_seed 匹配 → cell 坐标 vs 真实宜昌地理逐项核对 → 副本 name 具体化（避免"东山/点军"等大片区泛匹配）+ 数据缺 POI 的换或标无定位。验证用 webapp-testing skill（[verify-with-webapp-testing-skill](memory)）。memory [loc-anchor-by-data-not-coords](memory) 已立。

### 任务2：时间轴（T1→T3 成效动画）— 本会话推进

**核心决策点（新会话首问用户）**：地图 3D 柱体「起落」动画路线（三选一）：
- **A（推荐）** JS rAF + 每帧 setData 高度插值——贴现有 MapLibre fill-extrusion，demo 网格（数百格）顺，2000+ 格掉帧兜底阶梯淡入。
- **B** 重引入 deck.gl ColumnLayer + transitions——GPU 平滑最优，但与 [map.js:542-544](frontend/js/map.js)「弃 deck.gl」决策冲突，双渲染路径维护重。
- **C** 纯阶梯淡入（不补间柱体，opacity 交叉淡入）——最轻最稳，但无「起落」感。

**前置（任务2 大头）**：Overview 原地更新重构——`panel.js` tier1/2/3 从 innerHTML 字符串重建改为 DOM 原地值更新（find 元素、tween textContent/style）。任务2 面板数字/饼图/矩阵/关键词动画 + 极性深读 hover 动态关键词都受益（可顺手起头）。

**副本已预置**：T1/T3 双副本（`DATA/performance/polarity_deepread_keywords.json` v3），时间轴按 layer.timeTag 选对应 T（注：loc 数据待明日核对修正，但时间轴动画用的主要是数字/矩阵/柱体高度，关键词为辅）。

**设计要点（上会话已与用户商定）**：
- **一条通用时间轴**（非综合/极性两条）：Tab 条下，播放尊重当前 Tab（图层总览→演进综合；极性深读→演进当前极性）。
- **scrub 进度条 + 离散 T 停点**（非两个下拉框）：T1─T2─T3 点选跳转 + play/pause/prev/next。
- **播放起步切 3D**（柱体起落最有张力）；**错峰动画**（柱体 800ms → 数字/饼图/矩阵 600ms → 关键词淡入 300ms）。
- **只动关键 KPI**（总点数/积极/消极/中性 + 矩阵 + 关键词），非全统计（全动 = 噪音）。
- 色彩 `#3A5368` 主 / `#8B658B` 副（用 ui-ux-pro-max:ui-styling skill）。
- 完整可行性客观评估（地图柱体/面板数字/饼图/矩阵/关键词的动画可达性）+ 设计批评见 plan 文件 `C:\Users\Hi\.claude\plans\main-head-46250a6-push-memories-repo-se-sequential-swing.md`（Phase 2 节，任务1细化版）。

### 承重 memory 索引
- 本轮相关：`paint-inplace-swap-view`（时间轴切时间点同样就地切 paint/setData，不注册隐藏层）、`sticky-hover-priority`（时间轴播放时 sticky 让位？需考虑）、`loc-anchor-by-data-not-coords`、`verify-with-webapp-testing-skill`（动画=控制流/数据流，须 webapp-testing 验）、`generate-grid-exclusive-vs-viewmode`（播放切 3D 与 setViewMode 协同）、`todo-revision-log-sync`、`chinese-all-deliverables`、`push-not-redline`、`timestamp-no-weekday`
- 前会话承重：`extrusion-height-maxheight`、`maplibre-query-array-stringify`、`terrain-mesh-rendering`、`capsule-button-design-language`、`tool-layer-convention`、`view-data-conclusion-sync`、`frontend-default-light-theme`、`martin-ui-redesign`、`three-page-architecture`、`topic-table-frontend-sync`、`kde-loadbearing-logic`

## 当前状态
- 分支 `main`，**已 push**（origin/main = HEAD=`3273aa7`）。
- 工作树：todo（地点 tip 明日任务）+ revision-log 5.28 待 commit（本交接卡写入同批）。
- serve 已停。未做：任务2 时间轴（见上）+ 地点 tip 核对（明日）。

## 新会话 prompt（复制即用）
```
续 main（HEAD=3273aa7，已 push）。读 memories/repo/session-handoff.md（任务2 时间轴节点）。

任务：实现任务2「时间轴」（T1→T3 成效动画演示）。先与我对齐两个决策点：
1. 地图 3D 柱体动画路线：A JS rAF+setData（推荐）/ B deck.gl 重引入 / C 阶梯淡入——三选一。
2. Overview 原地更新重构（panel.js innerHTML 重建 → DOM 原地 tween）作为前置先做。

设计要点（已定）：一条通用时间轴（Tab 条下，非综合/极性两条）；scrub 进度条+离散 T 停点（非两下拉框）+ play/pause/prev/next；播放起步切 3D + 错峰动画（柱体→数字饼图矩阵→关键词淡入）；只动关键 KPI；色彩 #3A5368 主/#8B658B 副（ui-ux-pro-max:ui-styling）。副本 T1/T3 已预置。

承重：paint 就地切换（[paint-inplace-swap-view](memory)，时间轴切时间点同样就地 setData+paint，勿注册隐藏层）/双 sub-Tab/`_resolveLocAnchors`/enforceMutualExclusion/gridSig 全保。详 plan Phase 2 + revision-log 5.25-5.28。

并行待办（不阻塞）：地点 tip 核对修正（docs/todo.md 07-06 明日任务）。

计费按调动次数，工作方式见 ~/.claude/CLAUDE.md（不派 subagent、批量并行、给推荐不穷举）。前端验证用 webapp-testing skill（非 Playwright），默认交付肉眼验，动画属控制流/数据流须验。时间戳写"MM月DD日 HH:MM"（不写星期几）。
```
