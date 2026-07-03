# 情绪地图 (Emotion Map)

> Agent v2.0 | MCP 7 | 2026-06-17

## 项目概述

基于多源社交数据（大众点评/美团/小红书/微博/12345热线）的城市情绪空间分析平台。通过 NLP + GIS，让城市规划者能"看见"市民情绪的空间分布——用数据替代直觉，用地图承载叙事。

## 演示逻辑链（项目全局纲领 · 最高优先级）

> 本节是项目开发的北极星，**优先级高于具体编码规范**。凡削弱表现力或脱离应用场景的"纯技术正确但无用"实现，均让位于此链。每个数据/功能决策都应对应此链的某一环。

**核心哲学**：
- **一切数据都是为了演示的表现力（数据可用性）**——数据须服务于"图面有张力、能引导用户点击突出的好/差位置"。
- **一切演示都是为了应用场景的有用性**——演示须服务于"能识别具体城市建设/更新问题、对规划决策有用"。

**演示叙事链**（数据 → 演示 → 应用的贯通主线）：

`张力图面`（深红/深绿、高低柱体） → `引导点击`突出要素（很好的 / 很差的位置在哪） → `交互分析`张力原因 → `识别具体城建/更新问题`（如 治理×设施=交通拥堵、更新×环境=老旧小区物业）

三环对应：
- **表现力环**（张力图面）：渲染对称拉伸、色带、空间自相关、密度对比——让"突出要素"在图面上可见。
- **有用性环**（识别问题）：4×5 治理要素归因（domain×element）、极性空间聚类、单元级可解读属性——让点击后能讲清"这里是什么问题"。
- **交互环**（点击→分析→归因展示）桥接两者。

**视野-数据-结论 同步性**（演示铁律，与三环同等优先级）：演示三要素须始终同步——
- **视野（地图）**：当前聚焦的空间对象（hover/click 的格/集）。
- **数据（Overview）**：该对象的统计/归因展示。
- **结论（归因/建议）**：从数据推出的城建问题识别。

任何一端 hover/click，另两端即时联动（同色 / 同对象 / 同状态）。Overview **不是只读报表，是互动指挥台**：悬停 = 试探性聚焦（瞬时，leave 回 sticky 或清）；点击 = 锁定深读（sticky，再点 / 点异项切换释放）。同步高亮统一设计语言：饼图 slice / 4×5 矩阵格 / 关键词 → 地图同步高亮对应网格 / 柱体（橙色 `#ff9000`、不透明 100%）。递进：图层总览（宏观）→ 单元深读（微观）→ 关键词聚集（专题）。

> 落地样本：数据语义化重模拟（POI-anchored domain/element/极性）+ 对称拉伸 + 4×5 聚合归因 = 表现力与有用性的首次合流。

## 技术栈

- **语言**：Python 3.14.5
- **前端**：MapLibre GL JS（`frontend/`，geojson.io 1:1 外壳，主 UI 面）；Streamlit 1.58.0 为迁移期遗留（`apps/` :8501）
- **情感分析**：SnowNLP + jieba 分词
- **空间分析**：Shapely + pyproj（EPSG:4546）；地图渲染 = MapLibre GL JS + 天地图瓦片（`frontend/`），pydeck 仅遗留
- **数据采集**：Scrapy 2.16
- **LLM**：DeepSeek API (deepseek-chat)，火山引擎 API，讯飞 API
- **包管理**：pip + requirements.txt
- **坐标系（宜昌专项）**：
  - 社交媒体 → GCJ-02 → **WGS84 EPSG:4326**（统一基准）→ CGCS2000 EPSG:4546（CM 111E）
  - 规划矢量 → CGCS2000 投影 → WGS84（地图渲染）
  - 灵活输入：支持自定义 EPSG，不硬编码单一投影

## 项目结构

```
emotion_map/
├── frontend/       # 前端主界面（MapLibre GL JS，geojson.io 1:1 外壳）
├── apps/           # Streamlit 迁移期遗留层（app_main.py + 子页面，:8501）
│   └── CLAUDE.md   ── 模块级约定
├── core/           # 基础设施层（config/loader/export/tracker/map/UI）
│   └── CLAUDE.md   ── 模块级约定
├── SCRIPT/         # 分析引擎层（L0→L1→L2→L3→L4 管道）
│   └── CLAUDE.md   ── 模块级约定
├── SCRAPER/        # 数据采集层（Scrapy spiders）
├── DATA/           # 数据层（raw/ + processed/ + boundaries/）
├── design/         # 设计令牌系统（tokens.json + CSS）
├── docs/           # 文档体系（prd/spec/architecture/decisions/todo/dev-notes）
├── .claude/        # Claude Code Harness（agents/skills/memory/settings/commands/hooks）
└── memories/repo/  # 跨机会话交接卡
```

**数据管道**：`L0(原始采集) → L1(治理:坐标+相关+脱敏) → L2(SnowNLP情绪) → L3(LLM语义) → L4(归因)`
- L0→L1: `SCRIPT/data_governance.py`（需 DEEPSEEK_API_KEY）
- L1→L2: `SCRIPT/emotion_analysis_v1.py` → `run_analysis_task()`
- 所有入口（CLI/Tkinter/Streamlit）共用同一个 `run_analysis_task()`

## 编码规范

1. **禁用 emoji** — 代码中只允许 ASCII 标记：`[OK]` `[WARN]` `[LOAD]` `[ERR]`
2. **安全打印** — 所有 `print()` 必须通过 `_safe_print()` 调用（Windows GBK 兼容）
3. **禁止劫持 `builtins.print`** — 不得重新绑定
4. **入口统一** — 前端主入口 = `frontend/index.html`（**双击根目录 `start.bat`** 或 `py frontend/serve.py 8080`；serve.py **自起后端** uvicorn :8000 + `/api` 反代、Ctrl+C 同停，**无需手动跑 uvicorn**）；no-cache 开发服务器，返回 index.html 时**自动给本地 css/js 引用注入 `?v=<mtime>`**，文件一改浏览器即拉新、开发者零手动 bump 版本号）；**务必走 serve、禁 `file://`**（自动注入只在 serve 时生效）；Streamlit（:8501）为迁移期遗留，仅维护不扩展
5. **分析逻辑共用** — 所有入口调用同一个 `run_analysis_task()`
6. **导出命名规范** — `{name}_{L1|L2|L3|L4}_result_csv.csv`
7. **数据脱敏** — 分析结果中禁止包含用户名、用户ID 等个人身份信息
8. **空间范围优先** — 数据采集以范围 Polygon 为第一过滤条件，关键词仅作辅助
9. **决策追踪必埋点** — 公开函数 `@track("MOD_XXX.F_NNN")`，关键分支 `TrackContext("MOD_XXX.D_NNN")`
10. **追踪 ID 必注册** — 所有 ID 在 `core/tracker.py` 的 `_REGISTRY` 中登记，编号连续不跳号
11. **图像粘贴自动识别** — 用户粘贴图片后，自动查找 `%LOCALAPPDATA%\Temp\ScreenShot_*.png` 中最新的文件，调用 `mcp__zai-mcp-server__analyze_image`（智谱，主）识图；智谱不可用退 `mcp__vision-bridge__analyze_image`（火山引擎）。不需要等待用户明确说"看图"
12. **MCP 同类择优选智谱** — 同功能 MCP 优先智谱（Z.AI/BigModel），连不上再退备选：视觉=`zai-mcp-server`（主）→`vision-bridge`（火山引擎，备）；联网搜索=`web-search-prime`；读网页=`web-reader`；读开源仓=`zread`。完整路由见 `docs/mcp-strategy.md`

**Bug 定位流程**：`[TRACE] 日志 → 决策 ID → 代码跳转（O(1)）`

**模块 ID 分配** 详见 `AGENTS.md`

## 当前开发状态

- ✅ 项目框架搭建完成（七层架构；初版基于 Streamlit）
- ✅ 前端迁移 Phase 1（`frontend/` MapLibre GL JS，geojson.io 1:1 外壳，已 Playwright 验证）
- ✅ L0→L1→L2 数据管道实现（L1 LLM 分类需 API Key）
- ✅ 决策追踪系统（`core/tracker.py`，13 模块 55+ 追踪 ID）
- ✅ 坐标转换工具（GCJ-02 ↔ WGS84 ↔ CGCS2000）
- ✅ 范围选择引擎（Shapefile/GeoJSON/GPKG 上传 + CRS 检测）
- ✅ Design Token 体系（双主题 Light/Dark + 150+ Token）
- ✅ Agent 协作体系（v2.0，8 Agent 自动编排）
- ✅ Claude Code Harness（CLAUDE.md + Hooks + Skills + Subagents）
- ✅ MCP 能力层（7 服务 2026-06-17 实测，智谱优先，`docs/mcp-strategy.md`）
- 🔄 L0→L1 完整管线待验证（需 DeepSeek API Key 已配置）
- ⬜ L3（LLM 语义增强）接口已预留，待接入
- ⬜ L4（多维归因）框架已预留，待实现
- ⬜ 空间分析引擎 MVP（缓冲区 + 行政单元聚合）
- ⬜ UI 设计优化（布局、色彩、交互）

## 注意事项

- **数据安全**：`DATA/raw/` 原始数据不要修改；`.env` 文件不提交到 Git（API Key）
- **核心管道保护**：修改 `data_governance.py` / `emotion_analysis_v1.py` 必须走完整 SOP
- **基础设施保护**：不要修改 `core/tracker.py` 的 `@track()` 签名和 `_REGISTRY` 格式
- **依赖管理**：新增 Python 包必须同步更新 `requirements.txt`
- **Git 规范**：不要直接 commit 到 main（紧急修复除外），每天下班前提交并推送
- **SOP 门槛**：涉及 2+ 文件 / 控制流修改 / I/O 操作 → 走 Developer→Reviewer→Tester 完整流程
- **编码禁忌**：代码中禁止使用 emoji；API Key 禁止硬编码在 `.py` 文件中

## 记忆体系（三层）

本项目的记忆体系采用三层叠加：

### 第一层：CLAUDE.md（全量加载 — 明规则）

本文件。每次会话自动完整注入上下文。只放**顶层、不变、须严守**的规则。

### 第二层：Auto Memory（按需加载 — 隐规则）

Agent 在工作过程中自动记录的隐形知识：
- 我的习惯、反馈、项目踩坑会被后台 agent 静静记录
- 文件存放在项目目录下，换项目需重新积累
- 不会全量注入上下文——只读 `memory.md` 索引，遇到具体问题才读对应子文件
- 可随时说"忘掉 XXX"来删除错误记忆
- **主动写入**：用户给出明确反馈/偏好、或踩到非显然的坑 → 当场写一条 Auto Memory 并更新 `MEMORY.md` 索引（不只是后台记录）。记忆目录：`~/.claude/projects/<proj>/memory/`

> CLAUDE.md = 第一优先级、全量注入的**明规则**；Auto Memory = 第二优先级、按需注入的**隐规则**。

### 第三层：专项参考文档（渐进式披露 — 按需读取）

仿照 Skill 的渐进式披露机制。不适合全塞进 CLAUDE.md（太长、太专门），但需要时必须查到。

| 需求场景 | 必读文档 |
|----------|----------|
| 修改前端视觉、调颜色、调间距 | `docs/brand-visual.md` |
| 写产品文案、按钮文字、提示语 | `docs/copywriting-style.md` |
| 写 API 调用、定义返回格式、对接外部服务 | `docs/api-conventions.md` |
| 选 MCP、识图/搜索/读仓工具 | `docs/mcp-strategy.md` |

> 只在"需要的时候"才去读完整文档——保证准确性，不占多余上下文。

## 参考文档索引

| 文档 | 路径 | 用途 |
|------|------|------|
| **前端启动** | `frontend/README.md` | MapLibre 主界面启动手册（`serve.py` no-cache + CARTO 矢量底图） |
| **MCP 策略** | `docs/mcp-strategy.md` | MCP 路由手册、智谱优先策略、清单与测试日志 |
| 产品需求 | `docs/prd.md` | 用户画像、功能优先级、验收标准 |
| 产品规范 | `docs/spec.md` | 字段定义、UI 规格、性能预算 |
| 品牌视觉 | `docs/brand-visual.md` | 颜色、主题、标记样式 |
| 文案风格 | `docs/copywriting-style.md` | UI 文本、术语、错误信息 |
| API 约定 | `docs/api-conventions.md` | Key 管理、重试、返回格式 |
| 架构设计 | `docs/architecture.md` | 系统架构说明 |
| 架构规范 | `docs/architecture-pattern.md` | 七层架构、路由、代码组织 |
| 决策记录 | `docs/decisions.md` | 12 个架构决策（ADR，含 ADR-012 前端迁移） |
| 开发日志 | `docs/todo.md` | 每日任务 + 踩坑记录 |
| Agent 规范 | `AGENTS.md` | Agent 协作、SOP、完成定义 |
| Skills 索引 | `.claude/SKILLS_INDEX.md` | 项目相关 Skill 精选 |
| 会话交接 | `memories/repo/session-handoff.md` | 跨机协作上下文 |
| 视觉中转站 | `docs/vision-inbox/latest.md` | MCP 自动识图（vision-bridge server），备用手动文本桥接 |
| MCP 视觉桥接 | `.claude/mcp_servers/vision_bridge_server.py` | 火山引擎 Ark Vision MCP Server — 让不支持图片的模型也能看图 |

## 沟通方式

- 默认中文回复；代码、命令、变量名、文件路径保持英文
- 结论先行，简洁直接，不先铺垫背景
- 不谄媚，不夸"这是个很好的问题"，不以"当然可以"开头
- 给真实判断——方案有问题直接指出，发现更好做法主动说明
- **工作方式见全局 `~/.claude/CLAUDE.md`（调动次数优先）**——不派 subagent、批量并行、合并修改、给推荐不穷举、不跑非必要验证；plan mode 默认"派 Explore/Plan agent"工作流已被该全局规则覆盖

## Git

- 提交前先展示将要提交的变更摘要
- commit message 使用简洁英文

## 红线操作

以下操作即使在 auto-accept 模式下也必须先问：

- 删除文件、目录或 git 历史
- 修改 `.env`、密钥、token、证书、CI/CD 配置
- `git push`、`git rebase`、`git reset --hard`、强制推送
- 公开发布（`npm publish`、生产部署等）

## 开发工作流

修改 Python 代码后的标准动作（**清缓存已自动化，重启与测试按需手动**）：

1. **清理缓存（自动）**：每次 `Edit`/`Write`/`MultiEdit` 作用于 `.py` 后，
   `PostToolUse` hook（`.claude/hooks/on_post_edit.py`）自动删除被编辑模块在
   `__pycache__` 中的过期 `.pyc`，无需手动 `find ... -delete`。
2. **重启服务（手动，按需）**：
   - **前端**（`frontend/`，主）：改 HTML/CSS/JS 后浏览器 F5 即可，无需重启。
   - **遗留 Streamlit**（`apps/`/`core/`，:8501）：仅改动影响遗留运行态时，杀旧进程 → `py launch.py`（后台）；未改运行逻辑可跳过。
3. **跑测试（手动，提交前必做）**：`py -m pytest tests/ -q` 确认全过；
   走 SOP 时由 Tester 统一执行。
4. **验证节奏（不每次跑 Playwright/识图）**：常规前端/CSS/HTML/JS 改动 → 实现后
   **确保页面能加载**即可，视觉细节**交给用户开页肉眼验证**（自动识图对 UI 配色不准，
   别依赖它）。**仅以下三种情况才上 Playwright/MCP 验证**：
   (a) 用户明确要求；
   (b) 改动涉及**异步/控制流/数据流**等肉眼看不出的隐患（例：底图切换后图层重敷、
       >100k 采样降级、治理管线分支、坐标系转换）；
   (c) 风险功能提交前的最终回归。
   默认链路：**实现 → 交付 → 用户验证**。

> 注：hook 命令用 `py`（Windows launcher）；若环境 `python` 可用亦可。
> 重启服务（前端 http.server / 遗留 Streamlit）与 pytest 不纳入 hook——它们耗时会打断会话，由人按需触发。
