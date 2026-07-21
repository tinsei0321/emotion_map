# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月21日（**批4 Swipe 完成 + grid 镜像 bug 待诊断 + design-system.md 设计规范加入**）| 分支 `main` | HEAD `58de460`

---

## 当前节点：批4 时间对比完成；grid 镜像 bug 待诊断；design-system.md 加入

### 背景
本会话三大主线：① 宏观 thesis reframe（产品定位再校准）② 批4 时间对比·Swipe 卷帘（thesis 首落地）③ 设计系统规范化。另：第三方配色 mishap 已处理。

### ✅ 本会话已做

| commit | 内容 |
|---|---|
| `1964dc7` | 产品定位 reframe：宏观主观诊断透镜（CLAUDE.md 固化 thesis + 演示链末环改"定位+假设+排序" + §0 重排）|
| `1e6116e`→`f056c1e` | 批4 Swipe Step 1-5（scaffold/镜像/grid A-B/A-B UI/收尾）|
| `b13eb62` | 批4 grid 镜像 bug 诊断日志（map.js/time-bar.js `[compare]` log，临时，修后删）|
| `5377027` `58de460` | 用户保留的 2 commit（poi / workbuddy第三方）|
| （本次） | `docs/design-system.md` 设计系统规范 v1.0（正冷/负暖色带 + EMC 权重 + 渐进披露 + Token 管线）|

**宏观 thesis（5.148，已入 CLAUDE.md「产品本质」节）**：情绪地图 = 城市"连续主观体检"/情绪气象图 = 宏观主观诊断透镜。业界对标：官方城市体检「社会满意度调查」的连续地理版 + 国际 emotional mapping（eMOTIONAL Cities/MIT/Pánek）皆宏观聚合。宏观是护城河不是局限；「越细归因=越精确」是陷阱。Lean 宏观（张力/对比/趋势/主题分布），away 微观深归因（deep_attribution/多维归因）。

**批4 Swipe 卷帘架构**（memory `batch4-swipe-compare`）：双 map(mapA+mapB) + manual sync + clip divider + grid-only mirror + A/B 分片；cycle 约束(timeline→map 故 map 不能 import timeline → time-bar 编排)；事件 `compare:mapBready`/`compare:exit`。承重：mapA 路径零改动（mirror 非侵入 + renderSliceToMap 纯 setData）。进 compare = `c` 键或卡片「对比」按钮。

### ⚠️ 待办（下会话首做）

1. **【最优先】批4 grid 镜像 bug 诊断**：带 grid 进 compare 时 mapB 右半 + A/B 角标不正常显（无 grid 时 mechanics 验过正常——mapB 底图/divider/角标都显）。diag 日志已加（b13eb62，map.js `_focusedGridId`/`_mirrorLayersToMapB` + time-bar `compare:mapBready`，含 catch 错误）。**下会话第一步：F5 → 进 compare（带 grid）→ 贴 `[compare]` console 几行** → 定位断点（grid 没找到 / mirror addSource/addLayer 报错 / 事件没触发 / renderSliceToMap 失败）→ 修 → 删 diag 日志。
2. **配色对齐 design-system.md**：新规范定「正冷/负暖」（正=青绿 `#5DCAA5`/`#0F6E56`，负=珊瑚 `#F0997B`/`#D85A30`，中=`#C0C0C0`）。当前 `design/tokens.json`+`state.js emotionColors` 仍是**旧棕红负色**（Negative `#C4956A`/Very Negative `#B92D2D`）—— 与规范不一致，待对齐（tokens.json/css/py + state.js fallback）。
3. **批4 mapB 3D 暗底图同步**（polish）：3D compare 时 mapA 暗（dm- overlay）、mapB 仍亮底图 → 视觉不一致。2D compare 不影响。mapB 也敷 dm- overlay（较繁，后续）。

### 承重（必守）
- **调用次数优先策略**（全局 `~/.claude` 唯一权威）：默认主线程 + 会话切分首选 + subagent 仅大宗隔离。
- **paint-inplace-swap-view**：时间切换/批4 grid 走 setData 不重建层。
- **批4 cycle 约束**：map.js 不能 import timeline（timeline→map 已有）→ grid A/B 由 time-bar 编排（事件解耦）。
- **承重红线**：四态/diagnose 永不动；tracker 签名/_REGISTRY 不动；网格 snap-to-grid 算法保留只改组织。
- **CB 低频维护**：每 5-10 commit 一次 SCAN。
- 专业词+通俗解释；todo+revision-log 置顶同步；**只 commit 不 push（用户手动）**——用户明确说 push 时才 push。

### 本轮改/加的关键文件
- 新：[docs/design-system.md](docs/design-system.md)（设计系统规范 v1.0）。
- 批4：[frontend/js/map.js](frontend/js/map.js)（mapB+sync+divider+mirror+getMapB+setCompareMode）/ [time-bar.js](frontend/js/time-bar.js)（compare-aware _pick+对比按钮+A/B 角标+_activeSliceKey）/ [timeline.js](frontend/js/timeline.js)（renderSliceToMap+getBoundSliceKeys）/ [compare.css](frontend/css/compare.css)。
- thesis：[CLAUDE.md](CLAUDE.md)（产品本质节）。
- memory：`global-time-axis` / `batch4-swipe-compare` + MEMORY.md 索引。

### 跨环境待办（Hi 机补写，机本地 ~/.claude）
本会话 memory（`batch4-swipe-compare`）+ 之前未同步的（`global-time-axis` 等）—— admin 机本地，Hi 机需复制 + MEMORY.md 索引同步。

---

## 新会话 prompt（批4 grid bug 诊断，复制即用）

```
接续 07-21 会话（批4 Swipe 完成 + grid 镜像 bug 待诊断 + design-system.md 加入，详见 memories/repo/session-handoff.md）。
本会话目标：① 诊断批4 grid 镜像 bug（最优先）② 据结果修 + 去 diag 日志 ③（可选）配色对齐 design-system.md。

【首做】F5 → 导入 L2 + 生成标准网格 → 进 compare（'c' 或卡片「对比」）→ F12 贴 [compare] console 几行。
       diag 日志在 b13eb62（map.js _focusedGridId/_mirrorLayersToMapB + time-bar compare:mapBready，含 catch 错误）。
       据 log 定位：grid 没找到(_focusedGridId null) / mirror addSource/addLayer 报错 / compare:mapBready 没触发 / renderSliceToMap 失败。

先读（不动代码）：
- memories/repo/session-handoff.md（当前节点 + 承重）
- docs/revision-log.md §5.149-5.154（批4 五步 + design-system）
- frontend/js/map.js（_focusedGridId/_mirrorLayersToMapB/compare 块）/ time-bar.js（compare:mapBready 监听）
- memory batch4-swipe-compare（架构 + cycle 约束）

承重：调用次数优先 / paint-inplace-swap-view / 批4 cycle 约束(map 不 import timeline) / 四态·diagnose 不碰。
修完 bug 删 diag 日志（b13eb62 的 [compare] console.log）。
```
