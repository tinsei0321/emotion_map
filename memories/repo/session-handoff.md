# 会话交接卡

> 换机后读取此文件恢复上下文。

## 🔄 换机前必做（离开当前机器前 — 防 todo.md 再漏更）

> **教训（2026-06-17）**：06-16 晚~06-17 凌晨的工作只写进本交接卡 + `frontend/README.md`，**漏更 `docs/todo.md`**，导致办公机读 todo.md 误以为「06-16 后没干活」。git 同步健康，问题在**内容写入策略**——两个状态文件只更了一个。

**离开前 5 步**：

1. `git status` 清空 — 所有改动 commit（**含 `docs/todo.md`**）
2. `git push` — 然后 `git log origin/main..HEAD` 确认输出为空（无未推送）
3. **两个状态文件都要更**：
   - `docs/todo.md` — 正式开发日志（每日任务 + 踩坑），Agent 共享知识库
   - `memories/repo/session-handoff.md` — 本文件，换机恢复上下文
   - 不能只更一个（这是 06-17 漏更的根因）
4. `.claude/` 配置改动（agent / hook / skill）也要 commit — 工作策略同步
5. 记下「下次到机第一步」（见下方「到公司第一步」段，含 gitignore 文件手动补）

**到机后第一步**：

1. `git pull`
2. `git log origin/main..HEAD` 确认同步（应为空）
3. 读本文件「到公司第一步」段，补 gitignore 文件（如天地图底图 JSON）
4. `git status` 确认工作区状态
5. （建议）`git diff` 扫一眼最近提交，确认家用机工作已到位

> **文件职责**：`docs/todo.md` = 正式日志（每日任务 + 踩坑，倒序）；本文件 = 跨机交接（换机恢复上下文 + 临时阻断项）。**职责不同，换机前都要更新**。

## ⚠ 到公司第一步（2026-06-17，必做，否则前端底图 404）

前端 4 张天地图底图里，**影像(img) 2 个 JSON 被 `.gitignore` 屏了**（含内嵌 key），`git pull` 不会带过去。公司机 `git pull` 后**必须手动补这 2 个文件**（key 已在 `core/config.py` 公开、core/CLAUDE.md 批准前端可用）：

**① 在 `apps/static/` 下新建 `tianditu_img_nolabel.json`**（影像·无注记 = 默认底图），内容**原样**粘贴：
```json
{"version": 8, "sources": {"tianditu-img": {"type": "raster", "tiles": ["http://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=4d4dc85287c003c8a18d5520b8920796"], "tileSize": 256}}, "layers": [{"id": "tianditu-img", "type": "raster", "source": "tianditu-img"}]}
```

**② 在 `apps/static/` 下新建 `tianditu_img.json`**（影像·有注记），内容**原样**粘贴：
```json
{"version": 8, "sources": {"tianditu-img": {"type": "raster", "tiles": ["http://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=4d4dc85287c003c8a18d5520b8920796"], "tileSize": 256}, "tianditu-cia": {"type": "raster", "tiles": ["http://t0.tianditu.gov.cn/cia_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cia&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=4d4dc85287c003c8a18d5520b8920796"], "tileSize": 256}}, "layers": [{"id": "tianditu-img", "type": "raster", "source": "tianditu-img"}, {"id": "tianditu-cia", "type": "raster", "source": "tianditu-cia"}]}
```

> 另两张（常规 vec）`tianditu_label.json`/`tianditu_nolabel.json` 同样在本地、不在 git——公司机若已存在就别动；若丢了，把上面 img 版里的 `img`→`vec`、`cia`→`cva` 即得。
> 补完后启动见 [`frontend/README.md`](../../frontend/README.md)「启动」一节。

## 当前节点 — 2026-06-16 傍晚

### 代码状态

| 模块 | 状态 |
|------|------|
| tests/ | 56 tests 全过 |
| apps/app_main.py | ~350 行，工具栏直接调用弹窗，Import 后 A/OV/TB 立即可用 |
| apps/app_dialogs.py | ~1030 行，Import 用 early-return 关闭模式 |
| apps/app_console.py | 不变 |
| api/ | FastAPI 4 端点，就绪未启动 |
| core/db.py | EmotionDB 就绪 |
| core/spatial_analysis.py | Gi* / Moran's I / 行政聚合 / H3 就绪 |
| SCRIPT/emotion_analysis_v1.py | DeepSeekL2Analyzer 代码就绪，未接入 A 对话框 |
| SCRAPER/spiders/ | 4 个 spider (xiaohongshu/weibo/meituan/su12345) |

### A 对话框当前 UI

```
ENG 分析引擎
  ● L2 . SnowNLP粗粒度分析 (离线)
  ○ L3 . LLM 细粒度语义解析 (DeepSeek)     ← Key 自动从 .env 读取
  ○ L4 . 语料库多维归因 (需 LLM + 语料库)

[开始分析]
```

### 搁置项

- 点击详情面板: `core/ui_components.py` 标记 `[SHELVED]`
- 弹窗按钮样式: 尝试 CSS 调整后还原
- Toast CSS: 尝试调整后还原
- v3 UI 改造: 延后

### CLAUDE.md 新增规则

- 开发工作流: 每次修改后清缓存 + 杀旧进程 + 重启
- 沟通方式: 中文回复, 结论先行
- Git: 提交前展示变更, commit 用英文
- 红线: 删文件/改密钥/push 必须先问

## P0 阻断债清理（2026-06-16 家用机完成，待办公机补验证）

> 起因：迁移前全体系审查（见 `C:\Users\Hi\.claude\plans\1-vibe-coding-skill-mcp-agent-ui-2-lively-flute.md`）发现 9 个 🔴 阻断项。已在**家用机**完成其中 5 个代码级修复，但 pytest + FastAPI HTTP 验证因依赖未装（家用机 pypi 直连 SSL 被墙）未能跑，**需在办公机补跑**。

### 已完成（5 项，函数级已验证）

| # | 文件 | 改动 | 验证状态 |
|---|------|------|----------|
| 1 | `core/spatial_analysis.py` | h3 v3→v4 API（`latlng_to_cell`/`cell_to_boundary`，Polygon 坐标序反转） | ✅ 运行时验证（create_hex_grid 返回有效六边形）|
| 2 | `SCRIPT/emotion_analysis_v1.py` | CorpusAnalyzer 双 `analyze_single` 合并为单一带默认参签名 | ✅ compile + ABC 兼容验证 |
| 3 | `docs/decisions.md` | 决策追踪系统 ADR-008 → ADR-011（消解与 Scrapy 的编号冲突）| ✅ grep 验证唯一 |
| 4 | `CLAUDE.md` + `.claude/settings.json` + `.claude/hooks/on_post_edit.py` | "自动执行"承诺对齐 + 新增 PostToolUse hook（仅清 .pyc，不重启/不测试）| ✅ settings.json JSON 合法 + hook stdin 模拟验证 |
| 5 | `SCRIPT/data_governance.py` + `api/routes.py` | 抽出 `run_governance_pipeline()`（API/CLI 共用、不含 sys.exit、保留 LLM 漏斗、可选空间过滤）；`main()` 改薄包装；API `/governance` 删内联+硬编码 relevance，改调主管道 | ✅ 直接调用 run_governance_pipeline 验证：无 DEEPSEEK_API_KEY 时返回明确错误（不再静默产出 keyword-only 假 L1），MOD_GOV.F_007 追踪正常 |

### 待办公机补验证（家用机缺依赖，pypi 被墙）

1. `py -m pytest tests/ -q` —— 56 tests 全过回归（家用机无 pytest）
2. FastAPI `/api/v1/governance` HTTP 冒烟 —— `TestClient` POST，确认 404/无key-500/有key-200 三路径（家用机无 fastapi）
3. governance 等价性：同一 raw 数据，CLI `python SCRIPT/data_governance.py` 与 API `POST /governance` 产出 L1 CSV 行数+列集一致

### 重要提醒

- 这些文件**在会话开始前就已是 modified 状态**（办公机既有未提交改动），`git diff` 含办公机旧改动 + 本次 P0 改动，提交前需人工 review。
- 家用机 Python 实为 **3.13.2**（非 CLAUDE.md 所写 3.14.5）—— 又一处文档/实际不符，归 P1。
- `python` 命令在家用机 bash 下 exit 49 不可用，需用 `py`（hook 已用 `py`）。

## 前端 Phase 1 已落地（2026-06-16 家用机，geojson.io 1:1 外壳）

> 计划见 `C:\Users\Hi\.claude\plans\1-vibe-coding-skill-mcp-agent-ui-2-lively-flute.md` Part E。已用 Playwright 实测渲染通过。

### 已建（`frontend/`，纯 HTML/CSS/JS + MapLibre GL JS）
- **Token 单源**：`tokens.json` 新增 `geojson` 段（brand `#007afc`、gray-50..900、半径/阴影/字体对齐 geojson.io；emotion 五色保留）；`generate_css.py` 扩展生成 `frontend/css/tokens.css`（74 个 `--geojson-*` 变量，Light-first）。改色一处 → 三端同步。
- **外壳**：64px 固定头栏 + 工具栏按钮组（flexbox，非绝对定位）+ flex(map | 320px 右面板) + 折叠 + 右下角图例。
- **地图**：MapLibre GL JS（jsdelivr CDN 可用），默认**天地图底图**（CN 可达，复用 `apps/static/tianditu_label.json`，key 已内嵌）；底图切换 popover。
- **情绪点**：circle 层，五色 match + 白描边；**点击 → 蓝色选中光环 + 右面板「详情」卡片**（复活了 SHELVED 的 F_014）。
- **右面板 4 tab**：概览(五级统计卡+迷你柱状图) / 分析(L2/L3/L4 引擎 radio) / 详情(点击点) / GeoJSON(占位)。
- **Export modal**（geojson.io 风格原生 `<dialog>`，8px 圆角 + shadow-lg + 复选框模块）。

### 预览命令
```
cd d:/Github/emotion_map && py -m http.server 8080
# 浏览器开 http://127.0.0.1:8080/frontend/index.html
```

### 已知限制 / 待办
- **CartoDB 三底图（浅/深/标准）在 CN 被墙**（`tiles.basemaps.cartocdn.com` 连接重置）→ 默认天地图可用；CartoDB 选项留给网络允许时。
- **数据是 Phase 1 样本**（`js/state.js` 生成 80 个宜昌假点）；Phase 2 接 `/api/v1/points`。
- A 分析 tab、Import/Export modal、TB 表格 modal 目前是占位（Phase 2 接真实端点）。
- 边界范围层、热力图切换、空间分析 tab 待 Phase 2-3。

## 前端 v2 — geojson.io 1:1 精细化重做（2026-06-17 家用机，已 Playwright 全验证）

> 计划 Part F（取代 Part E 的 E4/E5/E6）。用户基于 6 张 geojson.io 截图给 8 点指令，全部落地。

### 布局重构（`frontend/`）— **最终外壳已定稿（06-17 晚）**
> 配色历经一次纠正：最初误做成全深色 chrome → 用户明确"默认浅色主题" → 改为**浅色为主 + 深蓝标题带**。**别再做成全深色 chrome。**
- **两层头栏**：上层标题带「宜昌市情绪地图 v1.0」= **深海军蓝 `#0c1c2e` + 白字加粗**（天地图品牌蓝，截图吸色）；下层工具栏 = **浅色白底**，左 `S/Pt/L/Po/R/C/▼` 绘制工具占位（加粗首字母、深字 `#404040`、圆角 4px、hover `#f5f5f5`、选中常亮蓝 `#007afc`+白字）+ 右 `Import/Export`(圆角 6px)/`M`。注：Point 用 `Pt`（与 Polygon 区分）。
- **三栏**：左栏(默认折叠) | 地图 | 右栏(默认展开)。左右各 8px `col-resize` 拖拽条（**max 1800px、JS clamp 到视口-220，可拖很宽看表格**）。
- **折叠钮**：白色竖向药丸条 `#ffffff`（24×44px、1px `#d4d4d4` 边、**朝地图那侧圆角/贴面板那侧直角**、深色 `‹`/`›` 箭头 22px、hover 变品牌蓝+白箭头）；箭头随折叠/展开自动翻转（JS）。
- **左栏状态机**：Import 面板（拖放+支持类型）→ 上传文件后切换为 `Range/Layers/Analysis` 三个可折叠区段（**浅头 `#f5f5f5` + 深字 UPPERCASE + chevron**，非深石板蓝）。**已用真实 xiling_boundary.geojson 上传验证**。
- **右栏** `Overview`(文件/图层/L1·L2 信息卡 + 五级统计 + 迷你柱状图) + `Table`(geojson.io 浅表：列头 `#f5f5f5`、白格、hover `#f5f5f5`、`#e5e5e5` 边，80 行样本)。tab 用**品牌色下划线**选中态（非深色填充）。
- **点击 → 右下角浮窗** `#feature-popup`（280px，非居中、非贴点），取代旧右栏详情 tab。
- **底图**：仅 4 张天地图（影像 img 有/无注记 + 常规 vec 有/无注记），**默认影像无注记**，CartoDB 已移除。新建 `apps/static/tianditu_img.json`(img+cia)、`tianditu_img_nolabel.json`(img)；复用 key，**无需新 API**。

### 新增/改动文件
- 新建：`css/sidebar.css` `css/popup.css` `js/sidebar.js` `js/popup.js` `apps/static/tianditu_img*.json`。
- 改：`index.html` `css/{layout,toolbar,panel,legend,dialog}.css` `js/{main,map,panel,toolbar}.js` `design/tokens.json`(加 chrome/section/table/import-panel/layout 段) + `apps/CLAUDE.md`(UI 规则改 geojson.io)。
- `generate_css.py` 重生成 → `frontend/css/tokens.css` 110 变量（单源未破）。

### 关键修复（Playwright 跑出来才改的）
1. **var-of-var 初始化失败**：`--right-w: var(--geojson-...)` 静默解析为 0px → 改为字面 `--right-w: 340px`（JS 拖拽覆盖）。
2. **工具栏无背景/高度**：`#toolbar` 漏了 `background`+`height:48px` → 补。
3. **切底图后情绪点消失**：`style.load`/`styledata`/轮询三套 re-apply 机制在 MapLibre 5.x 都不稳（有 double-add race 重置 geojson tile 处理 → queryRenderedFeatures 返 0）→ 改用 `setStyle(url, { transformStyle })` **声明式 carry-over emotion-* 源/图层**，永不 wipe。验证：4 张底图来回切，80 点 + 点击浮窗全保留。

### 预览 / 验证
```
cd d:/Github/emotion_map && py -m http.server 8080   # 必须从项目根起，../apps/static 才可达
# 浏览器 http://127.0.0.1:8080/frontend/index.html
```
- 临时验证截图：`v2-shell.png` `v2-shell-fixed.png` `v2-final.png`（repo 根，可删）。
- `main.js` 有 `window.__map = map` dev hook（控制台/测试用，可留可删）。

## 下一阶段

**Phase 2**：接真实数据（新增 `/api/v1/points` 端点 + `api.js` fetch）、A 分析接 `/analyze`、Import/Export/TB modal 功能化。
**P1 清债**：配色单源（删 config.py COLOR_MAP/FOLIUM_COLOR_MAP）、删 folium、Python/pandas 降档、CORS、天地图 Key 移 .env、skill 清理。

完整计划 + 评审见 `C:\Users\Hi\.claude\plans\1-vibe-coding-skill-mcp-agent-ui-2-lively-flute.md`（Part A-E）。
