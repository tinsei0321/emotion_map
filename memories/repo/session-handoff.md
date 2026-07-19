# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月19日（**极性深读时间轴 · Track A 阶段一（A0-A2）+ A2 复测修复**）| 分支 `main` | 本次会话 = 5.140–5.141

---

## 当前节点：时间轴重做 阶段一 done；A2 修复**待复测**；下会话 A3+A4+拓扑同步

### 背景
极性深读时间轴（revision-log §0「批2 全局时间轴 ◆ 架构转折点」）推倒重做：T1/T2/T3 烧死文件名 → **全局时间维度（time 是一等公民，manifest 声明，时间轴从数据发现片，适配未来天/周/月购买数据）**。三方向已定（plan `C:\Users\admin\.claude\plans\07-19-cb-lovely-quiche.md`）：后端 tippecanoe+Martin 文件模式（Track B，A 落地后）/ 全局时间轴（非局部）/ 展示=混合（日历+粒度切换+播放）。

排序策略：**Track A（GeoJSON，优先）+ Track B（MVT，可插拔）靠 `TimeSource` 接缝解耦**，换后端时上层零改动。

### ✅ 本会话已做（5.140–5.141）

| commit | 5.NNN | 内容 |
|---|---|---|
| `486488d` | 5.140 | 时间轴 A0-A2：manifest + TimeSource + applyTime + 时间按钮 UI（已 push？待本次一起 push）|
| （本次） | 5.141 | A2 复测三问题修复：matchDataset 扩展名根因 + 蓝 #1A73E8 + 滑动轴 |

**A0-A2 详**：
- **A0 manifest**：[DATA/processed/_time_manifest.json](DATA/processed/_time_manifest.json) 单一权威源，4 数据集（yichang_L2 / xiling_wujia_L1·L2 / ermawu_l3l4，全 phase T1-T3）+ `period`∈{phase,day,week,month,quarter,year,custom-range} + `sourceTemplate` `{slice}` 占位。
- **A1 TimeSource**：[time-source.js](frontend/js/time-source.js)（manifest 加载/缓存 + matchDataset + tagLayer + loadSlice + applyTime 控制器 + slicesForPeriod/availablePeriods）；[state.js](frontend/js/state.js) 加 currentTime + time:changed；[main.js](frontend/js/main.js) 启动 loadManifest+tagAllLayers + 导入后打标。
- **A2 时间按钮+卡片**：[time-bar.js](frontend/js/time-bar.js) + [time-bar.css](frontend/css/time-bar.css) 底部居中圆按钮（对齐顶部搜索按钮）+ Martin 风展开卡片（粒度胶囊 + 阶段停点/日历 + 滑动轴）。

**5.141 修复**：
- **matchDataset 扩展名根因**（"切换无反应"真因）：[main.js](frontend/js/main.js) `layerName()` 对普通上传**不去扩展名** → srcName 带 `.geojson` → matchDataset 正则（按去 ext 的模板生成）匹配不上 → 层未打标 → applyTime 全跳过。修：matchDataset 先剥 ext 再匹配。
- 蓝 `#4285F4`→`#1A73E8`（图片过期未采 Martin 精确 hex，用户可替换）。
- 卡片底部加通用滑动轴（_sliceIndex + _syncActive 跟随）。

### ⚠️ 待办（收工前未完成 / 下会话首做）

1. **【复测】A2 点层换源未用户确认**：用户收工前没复测 matchDataset 修复。**下会话第一步：请用户 F5 导入 L2 点数据 → 点 T1/T3 → 确认点层换源**。若仍无反应，疑 `/DATA/` 静态路由（serve.py `super().do_GET()` 走 cwd；理论上 repo_root 起则 /DATA/ 可达，但未实跑验证）→ 上 **Playwright 实跑定位**（导入文件→点片→查 source data 变化）。
   - 注意：applyTime **只换点/面层**，grid/terrain 跳过（A3）。用户若看网格层无变化属预期。
2. **A3 grid 演进 + play 动画**：[timeline.js](frontend/js/timeline.js) 接 global currentTime（监听 time:changed 重聚合 grid）；阶段数据保 rAF lerp / 日度离散；加 play 按钮；**retire 旧侧栏 `#timeline-wrap` widget**（与新底部 time-bar 统一，避免并存）。
3. **A4 Overview 原地追随**：时间切换 Overview 原地刷值（现 applyTime 走 layers:changed 整刷，A4 细化平滑）。
4. **拓扑同步收尾**：[topo_scanner.py](core/topo_scanner.py) 加 time-axis 语义边（→layers/map/state/overview）+ 新 memory `global-time-axis` + MEMORY.md 索引 + [context-map.md](docs/context-map.md) 登记（记忆共享通则）。

### 承重（必守）
- **调用次数优先策略**（全局 `~/.claude/CLAUDE.md` 唯一权威）：默认主线程 + 会话切分首选 + subagent 仅大宗隔离。
- **paint-inplace-swap-view**：时间切换走 `map.updateGridSourceData`（=getSource().setData），不 removeSource/重建层/碰 tip·选中·bindings。
- **tool-no-auto-overview**：time-bar 不抢 Overview 焦点（走 layers:changed/setData，不 dispatch layer:selected）。
- **承重红线**：四态出口契约 / diagnose 永不动 / tracker 签名·_REGISTRY 不动；网格 snap-to-grid 算法保留只改组织。
- **CB 低频维护**：每 5-10 功能 commit 一次 SCAN。
- 专业词+通俗解释；todo+revision-log 置顶同步。
- **push 政策**：平时只 commit 用户手动 push；**用户明确说 push 时才 push**（本次 5.141 用户指定 push）。

### 本轮改的关键文件
- 新：[DATA/processed/_time_manifest.json](DATA/processed/_time_manifest.json) / [frontend/js/time-source.js](frontend/js/time-source.js) / [frontend/js/time-bar.js](frontend/js/time-bar.js) / [frontend/css/time-bar.css](frontend/css/time-bar.css)
- 改：[frontend/js/state.js](frontend/js/state.js)（currentTime）/ [frontend/js/main.js](frontend/js/main.js)（loadManifest+tagAllLayers+initTimeBar）/ [frontend/index.html](frontend/index.html)（CSS 链接）/ [docs/revision-log.md](docs/revision-log.md)（§0 批2 展开 + §5.140/5.141）

### 跨环境待办（Hi 机补写，机本地 ~/.claude）
本次无新全局 memory（拓扑收尾的 `global-time-axis` memory 待下会话 A3/A4 后写）。admin 机 memory 无新增。

---

## 新会话 prompt（时间轴 A3：grid 演进 + play，复制即用）

```
接续 07-19 会话（极性深读时间轴 Track A 阶段一 done，5.140-5.141，详见 memories/repo/session-handoff.md）。
本会话目标：时间轴 A3（grid 演进 + play 动画）+ A4（Overview 原地追随）+ 拓扑同步收尾。

【首做】先请用户复测 5.141 matchDataset 修复：F5 导入 L2 点数据 → 点 T1/T3 → 确认点层换源。
       若仍无反应 → Playwright 实跑定位（/DATA/ 路由？导入层是否打标？applyTime 是否跑？）。

先读（不动代码）：
- memories/repo/session-handoff.md（当前节点 + A2 修复待复测）
- docs/revision-log.md §5.140/5.141 + §0 批2 全局时间轴分支
- frontend/js/time-source.js（TimeSource + applyTime）/ time-bar.js（时间按钮+卡片）/ timeline.js（现有 grid 动画引擎，A3 改造对象）
- C:\Users\admin\.claude\plans\07-19-cb-lovely-quiche.md（A3/A4/Track B 全 plan）

A3 任务：
1. timeline.js 接 global currentTime（监听 time:changed → 按 currentTime.sliceKey 重聚合 grid，不再写死 T1-T3）。
2. 时间从 manifest 发现（复用 time-source.js loadSlice/slicesForPeriod，删 timeline.js 的 PT_URL 硬编码）。
3. 阶段保 rAF lerp（_renderFrame/_tick 框架留），日度离散；time-bar 加 play 按钮 → 驱动 timeline.js。
4. retire 旧侧栏 #timeline-wrap widget（与底部 time-bar 统一，避免并存混淆）。

承重：调用次数优先 / paint-inplace-swap-view（grid 重聚合走 updateGridSourceData）/ 四态·diagnose 不碰 / tool-no-auto-overview / 拓扑同步（retire widget 改拓扑图）。
```
