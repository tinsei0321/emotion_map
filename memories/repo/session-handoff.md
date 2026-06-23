# 会话交接卡

> 换机后读取此文件恢复上下文。**单份当前快照，每日翻新**——每次换机/新会话**覆写「当前节点」**，旧的（已交接的）直接删；历史在 `docs/revision-log.md` + git，不在此累积。

## 🔄 换机协议（常驻）

**离开前 5 步**（防 todo.md 再漏更——06-17 教训）：
1. `git status` 清空——所有改动 commit（**含 `docs/todo.md`**）
2. `git push`——`git log origin/main..HEAD` 确认输出为空（无未推送）
3. **两个状态文件都更**：`docs/todo.md`（正式日志）+ 本文件（交接）；不能只更一个
4. `.claude/` 配置改动（agent/hook/skill/memory）也要 commit
5. 记下「到机第一步」

**到机后**：
1. `git pull` + `git log origin/main..HEAD` 确认同步（应为空）
2. 读本文件「当前节点」接上下文
3. **天地图 img 底图 JSON 被 gitignore**（含内嵌 key）——新机若 `apps/static/tianditu_img*.json` 缺失，从已有机器拷 4 张（img / img_nolabel / label / nolabel）；key 亦在 `core/config.py`
4. `git status` 确认工作区

> 文件职责：`docs/todo.md` = 正式日志（每日任务+踩坑，倒序）；本文件 = 跨机交接（单节点快照）。职责不同，换机前都更。

## 当前节点 — 2026-06-23（办公机 · 换机恢复 + 方向重定）

### 机器 & 同步
- **机器 = 办公机**（`C:\Users\admin\`；家用机 = `C:\Users\Hi\`）。auto-memory 已同步（9 条在本机生效）。
- Git：HEAD = `dab9a86`（buffer），`origin/main..HEAD` 与 `HEAD..origin/main` 均空 → 完全同步、工作区干净。家用机标"待 push"的 buffer 已 push。
- 天地图 4 张底图 JSON 全在，不用手补。

### 上轮产出（家用机，已同步、待肉眼验）
- **缓冲分析（Buffer）工具** ✅ 端到端：后端 [core/buffer_analysis.py](../../core/buffer_analysis.py)（geopandas EPSG:4546 米制）+ `POST /api/v1/spatial/buffer`；前端 [buffer-tool.js](../../frontend/js/buffer-tool.js)（3 段弹窗）+ Toolbox `#tool-buffer` + `api.js runBuffer`；B 要素按钮开弹窗（编辑态 `paint._ui` 回填 + 原地更新，layer id 稳定）；独立组卡；popup 复用 Range。**待肉眼验**：popup 排版 / 组卡双击折叠 / 色板尺寸（自动识图对 UI 配色不准，开页验）。
- L0 点精修（4px / 80% / 深灰 #4a4a4a + 全局 `PRESET_COLORS`）；`serve.py` 自动起后端（`py frontend/serve.py 8080` 一条命令 + F5 迭代）。

### 本轮方向（用户重定，跨会话大盘）

**✅ 快赢**：① 本文件翻新（单节点）；② skill 精简 `.claude/skills/` 465→235（230 个 `git mv` 归档 `skills_archive/`，零删除可逆）。

**✅ 多边形/矩形绘制 + 图层导出（本轮主产出）**——国内登不上 geojson.io → 把多边形绘制（原任务三.1）提前：
- **绘制**：移植 geojson.io 自实现 handler（不用 mapbox-gl-draw，与 MapLibre 5 不兼容）→ 新 [frontend/js/draw-tool.js](../../frontend/js/draw-tool.js)。多边形（点顶点→双击/回车/点起点完成）+ 矩形（拖拽，Shift 锁正方形）；[state.js](../../frontend/js/state.js) 加 mode 状态机；提交走 buffer 同款链路 → range popup；**绘制卡提为 `#left-panel` 常驻（空地图态即可画，无需先导入）**。Playwright 验证通过。
- **导出**：客户端 shp-write 无 UMD 死路 → **后端 geopandas** `POST /api/v1/export`（[core/export.py](../../core/export.py) `export_layer` F_005）。GeoJSON(WGS84)/CSV(WKT·lonlat·仅属性)/Shapefile.zip(WGS84·CGCS2000 4546，混合几何按类型分组) + 脱敏。模态加 CRS(仅shp)/CSV几何/范围(选中·全部)选项。4 路径 + CRS 实转（.prj GEOGCS↔PROJCS）验证通过。
- 借鉴固化 [docs/geojson-io-reference.md](../../docs/geojson-io-reference.md)（**以后不翻 docs/geojson.io/ 文件夹**）。

**⚠ 开发摩擦（记下）**：[serve.py](../../frontend/serve.py) 的 uvicorn **无 --reload** → 后端路由/代码改动需重启 serve；TaskStop serve 会**孤儿化 uvicorn**（占 :8000 提供陈旧路由，新 uvicorn 起不来 → 表现为 404）。修复：`netstat -ano|grep :8000` 找 PID → `taskkill //F //PID <pid>` → 重启 serve。后续可考虑给 serve.py 加 --reload 或起前清端口。

- **任务一（模拟数据 L0/L1/L2，MapLibre 标签）✅ 边界已解锁**：
  - 西陵伍家核心主城（~140km²）= **用户提供 shp 包**（Import）。
  - 二马路历史街区（~2km²）= **用新绘制工具画**（或绘制后导出复用）。
  - 两尺度嵌套（二马路 ⊂ 核心主城），只模拟核心主城一套，二马路区域加密。
  - 设计骨架（我的意见，待逐条对齐）：① 坐标 = 统一 WGS84 渲染 + CGCS2000 EPSG:4546 米制分析（GCJ-02/BD09 入库即转，**无需人工偏移修复**）；② L1 加 `domain`（规划/更新/运营/治理）+ `element`（设施/环境/服务/文化/事件）两列，与 7 类情绪正交；③ 点位 = POI 密度加权 + 陆地掩膜（百度热力 API 拿不到实时人流，付费数据商超范围）；④ 3 快照 = 2025-01 / 2025-09 / 2026-04（跨至 2026-07），讲二马路更新叙事（前消极→后积极）+ 季节调制 + 空间焦点漂移；⑤ L2 = 工程化文本锚定极性带（SnowNLP 确定性）。
- **任务二**（热点图，KDE 之上加 L1/L2 热点切换，参考百度 MapV）/ **任务三**（① 多边形范围选取 **✅ 本轮交付（多边形/矩形；点/线/圆待续）** ② 工具栏测量 ③ 地点检索接入百度 geocoding）。

### 怎么跑
```
py frontend/serve.py 8080   # 自动带后端（geopandas 已装）；F5 迭代；Ctrl+C 同停
# http://127.0.0.1:8080/frontend/index.html
```

### 下轮
- 边界到位（西陵伍家 shp Import + 二马路用绘制工具画）→ 任务一设计逐条定稿（坐标/字段 4×5/点位 POI 代理/3 快照叙事）→ 模拟器脚本构建（3 份 L1 MapLibre 标签 + L1→L2）。用户肉眼复验：绘制交互/提示条/导出模态选项/绘制卡常驻位。

## 工作机制速查（memory 在线时的快查；若 memory 丢失看此恢复）

- **session-handoff**：满载 / 任务自然边界 / 用户提 token / 主题大切换 → 主动给 **4 件套**（①提示+理由 ②新会话衔接说明 ③衔接操作 ④commit 小结+状态）。
- **token-saving**：①分会话（最有效）②subagent 分流（探索/规划/大读）③少全读（grep+offset/limit）。**不降 effort**。
- **maintain-revision-log**：每次 commit → revision-log §5 追加一行（日期|commit|意图|文件）；任务树（顶部 ★）全程维护（新分支即追加 + 状态 ✅🔄⬜⏸❌）。
- **kde-loadbearing**（底层逻辑勿破坏）：①联动排除（无字段层级自动排除）②独占显示（新热力图隐其他层 + dispatch `layers:changed`）。
- **tool-layer-convention**：工具生成层 = 独立组卡（`categoryOf` 加该工具 category）+ 要素按钮（H/B/…）开本工具弹窗（编辑态 `paint._ui` 回填 + 原地更新，layer id 稳定）。
- **中文交付**（plan/报告/docs 中文；代码/路径/标识符英文）+ **术语纠正**（非专业表述→专业术语）。
- **auto-compact**：`CLAUDE_CODE_AUTO_COMPACT_WINDOW=1000000`（晚压缩）。
- **交接卡新约定（2026-06-23）**：单节点翻新，不累积历史；旧节点删（已进 revision-log + git）。
