# 会话交接卡

> 换机/新会话后读取此文件恢复上下文。**单份当前快照**——每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。

## 🔄 换机协议（常驻）

**离开前**：① `git status` 清空（全 commit）② `git push`（`git log origin/main..HEAD` 应空）③ 更 `docs/revision-log.md` + 本卡 ④ `.claude/` 改动也 commit。
**到机后**：① `git pull` + 确认同步 ② 读本卡「当前节点」③ 天地图 4 底图 JSON 被 gitignore（新机从已有机器拷，key 亦在 `core/config.py`）④ `git status` 确认。

## 当前节点 — 2026-06-28（家用机 · Martin UI 全主线 + 空间分析 P0 完成）

### 机器 & 同步
- **机器 = 家用机**（`C:\Users\Hi\`）。注：与 06-25 办公机（`C:\Users\admin\`）不同机。
- **分支 = `feature/kde-l2-3d`**（已切 feature branch；非 main-only）。已 push，origin 同步。
- `py frontend/serve.py 8080` → `http://localhost:8080/frontend/index.html`（自动起 uvicorn :8000）

### 📋 续作 prompt（粘贴到新会话）
> 续 `feature/kde-l2-3d` 空间分析大改造。**P0 后端地基已完成**（`create_square_grid` F_006 + `/spatial/aggregate` + `/spatial/grid`(hex|square) + schemas + h3/httpx + 10 测试全过）。先读 plan `C:\Users\Hi\.claude\plans\majestic-marinating-cerf.md`（P0 已完成段）+ memory `martin-ui-redesign` + ADR-016。下一步 **P1（核密度重组：拆 综合/极性地形去 L1/L2 命名、移走情绪网格、加 H3 六边形 2D/3D 橙黄-暗红）** 或 **P2（空间聚合骨架 + 标准网格：新 Toolbox 项 + 步骤导航 + 方格 2D/3D 3 极性）**——我定 P1/P2 后再出独立 plan。

### 已完成（本次连续会话，feature/kde-l2-3d）

| Commit | 内容 |
|--------|------|
| `1333914` | **空间分析 P0 后端地基** — `create_square_grid`(F_006, snap-to-grid 4546→4326) + `/spatial/aggregate` + `/spatial/grid`(hex\|square) + schemas + h3/httpx + F_005 补登 + 10 测试 |
| `9f13971` | **A2 UI 层文档** — ADR-016（Martin 导航范式）+ spec §3.4 + ui-redesign-plan Phase 4 + memory `martin-ui-redesign` |
| `3203ad5` | chore: gitignore vendored `kepler.gl-master`（防再误提交） |
| `53b588d` | **B5** 色板圆角 + 品牌蓝查漏（`.swatch` 圆角矩形 + `#007afc`→`#4285F4` token 化 + toast 幽灵 token 修复） |
| `71fa3f0` | **B4** 左端参数弹出栏（`#param-panel`，1:2 分栏，apply 链零改） |
| `651532e` | **B3-rev** 区2 工具栏（白底 + `#384555` 图标 + 漏斗 + 计数） |
| `054e3a1` | **B3** 左端栏三区（tab 互斥 Range/Layers/Toolbox）+ B6 随动复核 |
| `e0b7172` | **B0-B2** 三页架构 + Martin 导航重塑（色彩/单层顶栏/3 按钮集） |
| (rebase) | 剔除 `599883d` kepler 误提交（18MB + Mapbox token，GitHub 密钥扫描拦截） |

**主线收口**：Martin UI 重塑 B0-B5 + B6 + A2 文档（ADR-016）全部完成；空间分析 P0 后端完成。

### 下一步（空间分析 P1-P4，每期独立 plan）

| 期 | 内容 | 后端就绪 |
|----|------|----------|
| **P1** 核密度重组 | 拆 综合/极性地形（去 L1/L2 与管线级撞名）、移走情绪网格、加 H3 六边形(2D/3D, 橙黄-暗红, 无极性) | ✅ `/spatial/grid`(hex) |
| **P2** 空间聚合骨架 + 标准网格 | 新 Toolbox 项（核密度下方）+ 步骤导航组件(新) + 类型组卡片 + 标准网格(方格, 2D/3D, 3 极性, 深色=高值) | ✅ `/spatial/grid`(square) |
| **P3** 指定单元 | zone 聚合 + 面图层选择器（行政区/更新单元/控规/用地） | ✅ `/spatial/aggregate` |
| **P4** Gi\*+Moran's I | 热点 + 空间自相关（**需装 libpysal+esda PySAL 重栈** + 接 `/spatial/hotspot`/`/spatial/moran` 端点） | ⚠️ 函数有，esda 未装 |

**设计共识**：核密度 = 连续密度场（KDE 地形 + H3 密度分箱，无极性）；空间聚合 = 离散面域统计（方格/指定单元 + Gi\*/Moran's I，带极性）。详见 ADR-016 + plan。

### 怎么跑
```
py frontend/serve.py 8080                              # 前端 + 反代 + 自动起 uvicorn :8000
py -m pytest tests/test_spatial_analysis.py -q         # 空间分析 10 测
py -m pytest tests/ -q --ignore=tests/test_relevance_filter.py   # 全量（1 预存失败无关）
```

### ⚠ 注意
- **分支 `feature/kde-l2-3d`**（非 main）；commit 前 `git status`，**勿盲目 `git add -A`**。
- **`docs/minimax-workspace/` 38 条删除是用户在途工作**（未提交；commit 会断 `SCRIPT/generate_l1_mock.py`/`poi_4x5_map.py` 引用）—— 勿动，等用户处置。
- **`docs/kepler.gl-master/` 已 gitignore**；磁盘 3 个游离文件可 `rm -rf docs/kepler.gl-master` 清（需用户点头）。
- **PySAL（libpysal+esda）未装**，仅 P4 需要；P1-P3 不碰。h3 4.5.0 + httpx 0.28.1 已装（P0）。
- 预存 pytest 问题（与本次无关）：① `test_relevance_filter` 需 `requests`；② `test_emotion_analysis::test_capabilities` SnowNLP 断言失败。
- **Martin UI 承重约定**见 memory `martin-ui-redesign`（三区 tab 互斥 / 参数栏随动 B6 / apply 链零改 / 品牌蓝单源 `#4285F4` / 胶囊设计语言）。
- 空间分析 plan：`C:\Users\Hi\.claude\plans\majestic-marinating-cerf.md`（P0 已完成，P1-P4 待做）。
- 每完成一件事必更 `todo.md` + `docs/revision-log.md`；**只说"交接"时才更本卡**。
- `serve.py` 的 `?v=<mtime>` 只覆盖 HTML 中 `<script>` 标签；ES module import 链不受保护，改 JS 后需 Ctrl+Shift+R。
