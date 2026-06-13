# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

---

## 📋 每日模板

```markdown
## 📅 YYYY-MM-DD（周X）

### ☑ TODO List
<!-- 当日计划完成的任务，每天 ≤ 3 个大任务 -->

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ⬜ | 做什么 | `xxx.py` | |
| 2 | ⬜ | 做什么 | `xxx.py` | |
| 3 | ⬜ | 做什么 | `xxx.py` | |

> 💡 标准启动指令：`@pm 开始处理 YYYY-MM-DD 的任务 N：任务名称`

### 📝 开发日志
<!-- 记录实际做了什么、踩了什么坑、收获了什么 -->

**关键字**：tag1, tag2

#### 做了什么
- 

#### 踩坑 & 收获
- 

#### 碎片想法
- 

#### 🔜 次日计划 (YYYY-MM-DD)
- 
```

---

## 📅 2026-06-13（周六）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | 规划范围真实数据落图（L1治理+坐标转换+范围过滤管道） | `SCRIPT/data_governance.py`（新建）, `core/coord_transform.py`, `core/range_selector.py` | 边界=规划范围(LineString→buffer Polygon)；管道已就绪，24条占位坐标全部被过滤（预期行为），待真实坐标数据后完整验证 |
| 2 | ✅ | Data Agent 创建 + L0→L1 相关性筛选模块 | `SCRIPT/relevance_filter.py`（新建）, `data_governance.py`（重构 v1.1）, `.github/agents/data.agent.md`, `AGENTS.md` | 两层漏斗：关键词粗筛 + DeepSeek LLM 精分类；Agent 整合入全局调度 |
| 3 | ➡ | L1 治理 + L2 分析 端到端验证 | `data_governance.py`, `emotion_analysis_v1.py`, `DATA/` | 数据爬取暂时放弃，MVP 专注 L0→L2 管线跑通，确保各层数据有价值 |
| 4 | ✅ | 情绪点显示样式优化（颜色/光晕/描边） | `core/config.py`, `core/map_engine.py`, `core/ui_components.py` | Designer 重设计：双层光晕 + Material色板 + Neutral改琥珀色 |
| 5 | ✅ | Design Token 体系搭建（设计令牌系统） | `design/tokens.json`, `design/generate_css.py`, `design/tokens.css`, `design/tokens.py` | Designer 创建完整设计体系：7大类150+token + 自动生成器 + ui_components.py 全部 Token 化 |
| 6 | ✅ | Token 双模式 (Light/Dark) + 设计系统展示页 | `design/tokens.json`(重构), `design/generate_css.py`(重写), `design/tokens.css`, `design/tokens.py`, `core/ui_components.py`, `apps/app_design_system.py`(新建) | Dark/Light 镜像双主题 + prefers-color-scheme 自动跟随 + [data-theme] 手动切换 + 独立 Kitchen Sink 展示页 |
| 7 | ✅ | 主应用集成新 Design Token（低饱和色卡+CSS变量） | `apps/app_main.py`, `design/tokens.css`, `design/tokens.py` | 添加 inject_theme_css() 调用 + 重新生成 Token CSS/Python |
| 8 | ✅ | 修复注记开关 [LB] 导致底图偏移/复位 | `apps/app_main.py` | st_folium() 返回值保存 last_center/last_zoom 到 session_state，rerun 后视图保持 |
| 9 | ✅ | 边界线粗细+颜色可调节（[R]窗口内） | `apps/app_main.py`, `core/map_engine.py` | show_range_dialog 新增 slider(1-20) + 7色 selectbox；add_boundary_layer 动态 hex→RGB + weight 参数 |
| 7 | ✅ | 决策追踪系统 (Decision Tracking System) | `core/tracker.py`(新建), `.github/agents/debugger.agent.md`, `developer.agent.md`, `reviewer.agent.md`, `AGENTS.md`, `docs/architecture-pattern.md`, `docs/decisions.md` | 决策 ID + 行为 + Log + Tracking 体系；bug 定位 O(n)→O(1)；全局配套更新 |

> 💡 标准启动指令：`@pm 开始处理 YYYY-MM-DD 的任务 N：任务名称`

> ⚠️ 策略调整 (2026-06-13)：数据爬取暂时放弃（后期购买稳定数据），MVP 焦点转为 **L1 数据治理 + L2 数据分析 端到端跑通**，确保每一层产出的数据都有实际价值。

### 📝 开发日志

**关键字**：Data Agent, 相关性筛选, DeepSeek LLM, 两层漏斗, L0→L1 治理重构, 人民城市, 情绪点样式重设计, Design Token 体系, **决策追踪系统, Decision Tracking, Trace ID**

#### 做了什么
- 创建新 Agent：📡 数据管家（Data Agent），定义在 `.github/agents/data.agent.md`
  - 职责：L0 多源数据采集 + L1 数据治理（坐标转换/范围过滤/相关性筛选/脱敏/字段规范化）
  - 可调用：developer, gis-developer
  - 已整合入 AGENTS.md 全局调度体系（Agent 从 10 → 11）
- 新建 `SCRIPT/relevance_filter.py` L0→L1 相关性筛选模块（~330 行）
  - 第一层：关键词粗筛（30 个广告/灌水关键词），旅游/美食/探店全部放行
  - 第二层：DeepSeek LLM 精分类，判断市民城市感受 → 映射五要素（设施/环境/服务/文化/事件）
  - 批量并发（ThreadPoolExecutor，每批 5 条），3 次指数退避重试
  - 新增 L1 字段：relevance, relevance_dimensions, relevance_emotion, relevance_urban_value, relevance_summary, filter_layer
- 重构 `SCRIPT/data_governance.py` v1.0 → v1.1
  - 管线从 4 步扩展为 5 步：坐标转换 → 范围过滤 → **相关性筛选（新）** → 脱敏+导出 → L2 分析
  - 脱敏时机后移（LLM 需要原始文本做分类）
  - 无 API Key 时优雅降级跳过
- 全部走完整 SOP：Developer → Reviewer（发现 1 个 bug + 1 个优化）→ Developer 修复 → Reviewer 复审 → Tester 测试（17/17 用例通过）
- Designer 重设计情绪点显示样式：双层光晕（外层 radius=13 opacity=0.12 + 内层 radius=7 opacity=0.92 stroke=#fff）+ Neutral 从灰色改为亮琥珀色 #ffd740 → 卫星底图上可见性大幅提升
- Designer 创建完整 Design Token 体系：7 大类 150+ token（color/typography/spacing/radius/shadow/effect/component），含 JSON 单源 + CSS/Python 自动生成器 + ui_components.py 全部 Token 化
- Designer 扩展 Token 体系为 Light/Dark 双模式：tokens.json 增加 theme 层级，Dark/Light 镜像对称（深色半透明底↔浅色半透明底），CSS 支持 prefers-color-scheme 自动跟随 + [data-theme] 手动切换
- Designer 创建设计系统展示页 `apps/app_design_system.py`：独立 Streamlit Kitchen Sink，含主题切换/色板/字体/间距/圆角/阴影/组件全展示
- **PM 搭建决策追踪系统 (Decision Tracking System)**：
  - 新建 `core/tracker.py`（~280 行）：装饰器 `@track()` / 上下文管理器 `TrackContext` / 快捷函数 `trace_*()` / 全局注册表
  - 更新 debugger.agent.md：新诊断流程基于 [TRACE] 日志 + 决策 ID 精准定位
  - 更新 developer.agent.md：新增决策追踪编码标准 + 模块 ID 分配表 + 埋点规则
  - 更新 reviewer.agent.md：新增追踪点完整性审查清单
  - 更新 AGENTS.md：铁律 9/10 + 决策追踪系统说明 + 共享知识库
  - 更新 docs/architecture-pattern.md：增加决策追踪系统章节
  - 更新 docs/decisions.md：ADR-008 决策追踪系统
  - **渐进式埋点完成（13文件55追踪ID）**：全部 core/ + SCRIPT/ + apps/ + SCRAPER/ 模块已添加 @track() 装饰器和 register_track_id() 注册

#### 关键设计决策
- **相关性筛选理念**：从"是否属于城市规划领域"转变为"感知市民对城市的感受与需求"，践行"人民城市"理念
- **宽容原则**：旅游打卡、美食探店、街区体验全部保留（城市活力信号），不确定时倾向于保留
- **LLM 选型**：DeepSeek-V3（已有 API Key + 推理能力强 + 中文理解好）
- **两层漏斗**：先关键词快筛（免费），再 LLM 精分类（API），减少 API 调用量
- **决策追踪系统**：自研 `core/tracker.py`（~280 行），用决策 ID（MOD_XXX.F_NNN / D_NNN）装饰器 + 上下文管理器实现 O(1) 精准 bug 定位；全员遵守铁律 9/10 埋点规范

#### 踩坑 & 收获
- Reviewer 发现 relevance_summary 在 error 分支被覆盖 → 详细字段填充移入 else 互斥分支
- 并发累加计数器是代码异味 → 改为批次完成后从 DataFrame 列值统计
- 情绪点 Neutral 用灰色在天地图卫星底图上完全不可见 → Designer 改用亮琥珀色 #ffd740（绿→黄→红灯语义），双层光晕（外层 radius=13 opacity=0.12 + 内层 radius=7 opacity=0.92 stroke=#fff）大幅提升可见性

#### 🔜 次日计划 (2026-06-14)
- L0→L1→L2 端到端管线验证（准备有意义的测试数据 + 跑通全流程）
- L2 SnowNLP 分析结果质量评估（极性分布合理性、关键词有效性）
- 优化 L2 输出：情绪关键词提取质量 + 可视化落图

---

## 📅 2026-06-12（周五）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | 情绪数据爬取方案调研+小范围测试（西陵区） | `SCRAPER/data_scraper.py`（新建） | Scrapy 框架搭建完成 + 小红书 Spider 测试通过（HTTP 200） |
| 2 | ✅ | ~~西陵区真实数据落图~~ → 移至 06-13 任务1，范围改为规划范围 | — | 边界从西陵区改为用户上传的规划范围 Shapefile |
| 3 | ✅ | Agent 协作体系搭建：程序开发/调试/进度管理/审查/测试/文档 Agent | `.github/agents/*.agent.md`, `AGENTS.md` | 6 Agent + AGENTS.md + 架构记忆 + 使用场景，基础搭建完成 |
| 4 | ✅ | 系统架构优化：七层架构 + 空间分析引擎重定义 + 溯佰科定位修正 | `docs/architecture.md`, `docs/decisions.md`, `docs/dev-notes.md`, `memories/repo/architecture-pattern.md`, `SCRIPT/emotion_analysis_v1.py`, `core/map_engine.py` | PM 研判 → Developer 改代码 → PM 同步文档，SOP 首次实战 |
| 5 | ✅ | 环境同步：requirements.txt 补全 + 新增环境管家 Agent | `requirements.txt`, `.github/agents/ops.agent.md`, `AGENTS.md` | Scrapy 未装、streamlit-folium/shapely/pyproj 漏登记 |
| 6 | ✅ | 跨机协作体系：会话交接卡 + ops 自检 + PM 交接流程 | `memories/repo/session-handoff.md`, `ops.agent.md`, `pm.agent.md`, `AGENTS.md` | 换机 `@pm 同步上下文`，下班 `@pm 下班交接` |
| 7 | ✅ | Agent 扩展：UI设计师/设计审查员/GIS开发员（10 Agent） | `.github/agents/designer.agent.md`, `design-reviewer.agent.md`, `gis-developer.agent.md`, `AGENTS.md` | 设计→审查→迭代闭环，GIS 专项能力 |
| 8 | ✅ | 初始页面重构：左侧三功能按钮 R/D/A + 全屏地图 | `app_main.py`, `core/ui_components.py` | 极简风格，CSS 统一到 ui_components，emoji 全清 |
| 9 | ✅ | 范围选择引擎：矢量文件上传/CRS检测/缓存/边界叠加 | `core/range_selector.py`, `app_main.py`, `data/boundaries/` | 支持 .shp/.geojson/.gpkg，自动投影转换 |
| 10 | ✅ | 坐标转换工具（WGS84/GCJ02/BD09）+ 宜昌标准 CGCS2000 | `core/coord_transform.py` | 社交媒体→WGS84→CGCS2000 投影完整链路 |
| 11 | ✅ | 爬虫验证：Scrapy 2.16 兼容修复 + 24条小红书数据采集 | `SCRAPER/spiders/xiaohongshu_spider.py` | start_urls 兼容 + explore 页 SSR 提取 |
| 12 | ✅ | 全局代码审查 + UI审查 + 交互审查（三 Agent 并行） | `app_main.py`, `ui_components.py`, `export.py` | 16 项问题全部修复，通过 Tester 验证 |

### 📝 开发日志

**关键字**：Agent扩展, UI重构, 范围引擎, 坐标转换, 跨机协作, 审查闭环, Scrapy兼容

#### 做了什么
- Agent 阵容从 6 → 10 个（新增 Ops/Designer/Design Reviewer/GIS Developer）
- 初始页面重构：左侧 R/D/A 三按钮 + 全屏地图，极简 ASCII 统一风格
- 范围选择引擎：支持 .shp/.geojson/.gpkg 上传，CRS 自动检测转换，边界叠加
- 坐标转换工具：GCJ02/BD09→WGS84，宜昌标准 CGCS2000_3_Degree_GK_CM_111E
- Scrapy 2.16 兼容修复：start_urls 空列表 bug + explore 页 SSR 数据提取
- 全局代码/UI/交互三 Agent 并行审查，16 项问题全部修复
- 跨机环境同步 + 会话交接卡体系
- CSS 统一收归 ui_components.py，空状态引导，emoji 全清

#### 踩坑 & 收获
- Streamlit @st.dialog 内 st.rerun() 导致对话框消失 → 去掉 rerun，利用自动重跑
- file_uploader 残留问题 → 最终去掉对话框内上传，改为读取 data/boundaries/ 目录
- 旧建成区文件 11280 区域导致卡顿 → 清理残留，0.1s 秒开
- Shapefile 单文件无法读取 → 多文件上传 + 子文件夹组织
- Scrapy 2.16 要求 start_urls 非空 → 加占位 start_urls 兼容
- geom.crs 不存在 → 改为 gdf.crs
- 边界只在数据加载后显示 → 空状态也叠加（selected_ranges 判定）

#### 碎片想法
- Tester Agent 必须每次都用，不通过不提交
- GIS 开发员和 Tester 交叉核实 CRS 很有价值
- SHP→GeoJSON 当前方案已足够，暂不需要独立转换工具

#### 🔜 06-13(周六)
- 西陵区真实数据落图（L1 数据治理 + 坐标转换 + 范围过滤）
- 数据爬取方案最终确定（登录 API vs 购买数据）
- 空间分析引擎 MVP（缓冲区分析 + 行政单元聚合）开始编码


## 📅 2026-06-11（周四）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | L2/L3/L4 三级分析架构重构 | `emotion_analysis_v1.py`, `config.py`, `map_engine.py`, `ui_components.py`, `export.py` | 五级极性、引擎模板、导出命名统一 |
| 2 | ✅ | 入口统一：CLI + Tkinter + Streamlit 共用 run_analysis_task() | `run_analysis.py`, `app_main.py`, `launch.py` | 控制台合并进 main 为子页面，删 analysis_console.py |
| 3 | ✅ | GBK 编码修复 + docs/ 文档体系 | 全项目 `.py`, `docs/*.md` | emoji→ASCII，\_safe_print，架构规范入记忆 |

### 📝 开发日志

**关键字**：重构, 架构, 编码, GUI, 路由

#### 做了什么
- 重构 EmotionResult 为 L2→L3→L4 三级叠加结构，五级极性全链路更新
- 新增 run_analysis_task() 统一分析入口，CLI/Tkinter/Streamlit 全部调用它
- analysis_console 合并进 app_main，用 `?page=console` 路由，只启一个端口 8501
- 建立 docs/ 五文件（dev-notes/architecture/decisions/todo/scenarios）
- Tkinter GUI 美化，状态栏清晰
- 全项目 emoji 换 ASCII([OK]/[WARN]/[LOAD])，\_safe_print 防崩溃

#### 踩坑 & 收获
- Windows GBK 编码是最大坑——emoji 在 print/Streamlit 中反复崩溃，最终全量替换 + \_safe_print 解决
- builtins.print 劫持导致递归无限循环，改用显式 \_safe_print() 调用
- `?page=console&file=xxx` 路由模式是未来子页面的标准做法

#### 碎片想法
- 三入口统一到 run_analysis_task() 是正确的架构决策
- 导出含 L2/L3/L4 阶段标识，溯源清晰

#### 🔜 明日
- 西陵区数据爬取启动 + Agent 协作体系搭建


## 📅 2026-06-10（周三）及之前

| 日期 | 关键进展 |
|------|----------|
| 06-09 | SnowNLP pipeline 初版、点状地图、CSV/GeoJSON 导出、模块化重构 |
| 05-28~31 | 课题启动：20 轮对话确定三段式框架、技术栈、七大应用场景 |


## 🗂 长期备忘

| # | 想法 | 状态 |
|---|------|------|
| L1 | LLM 大模型接入（溯佰科平台 Agent 嵌入） | ⬜ |
| L2 | 时序分析（多时间切片对比） | ⬜ |
| L3 | 行政区划聚合视图 | ⬜ |
| L4 | 自动报告生成（PDF） | ⬜ |
| L5 | 空间自相关分析（Moran's I） | ⬜ |
| L6 | 问题-对策映射引擎 | ⬜ |
| L7 | Docker 部署 | ⬜ |
| L8 | 配置外部化（.env） | ⬜ |
| L9 | 移动端适配 | ⬜ |
| L10 | 语料库本地化词典 | ⬜ |
| L11 | 空间分析引擎 MVP（缓冲区分析 + 行政单元聚合） | ⬜ |
