# 情绪地图项目架构规范

## 七层架构（从下至上）

| 层级 | 目录 | 职责 |
|------|------|------|
| 数据层 | `data/` | L0(原始爬取) / L1~L4(分析结果)，格式 csv/geojson |
| 数据采集层 | `SCRAPER/` | 多源数据爬取（大众点评/美团/小红书/微博/12345），基于 Scrapy，输出到 data/raw/ |
| 基础设施层 | `core/` | config / data_loader / export |
| 数据分析引擎层 | `SCRIPT/` | L1(数据治理)→L2(SnowNLP)→L3(LLM/溯佰科)→L4(多维归因) 四级管道 |
| 空间分析引擎层 | `core/` | 底图渲染 + 空间可视化(点状/热力图) + 空间分析(热点/缓冲区/聚合) |
| UI 组件层 | `core/` | Streamlit 可复用组件（HUD/弹窗/图例/CSS） |
| 应用层 | `apps/` | Streamlit 主应用，所有页面通过 ?page= 路由 |

## 入口统一原则
- 项目只有一个 Streamlit 端口 (8501)，所有页面在 `app_main.py` 内通过 `st.query_params['page']` 路由
- `launch.py` 只启动一个 Streamlit 进程
- `run_analysis.py` 是独立的 CLI + Tkinter 桌面入口，不依赖 Streamlit

## 新增子页面流程
1. 在 `app_main.py` 中新建 `show_xxx_page()` 函数
2. 在 `main()` 顶部路由表中注册：`if page == 'xxx': show_xxx_page(); return`
3. 侧边栏放 `[返回地图浏览器](/)` 链接
4. 页面间跳转用 `st.link_button` 或 `st.markdown` 链接，URL 格式 `/?page=xxx&param=value`

## 分析逻辑共用
- 所有 UI（CLI / Tkinter / Streamlit）调用同一个 `run_analysis_task()`（在 `emotion_analysis_v1.py`）
- 导出文件命名统一：`{name}_{L1|L2|L3|L4}_result_csv.csv`
- print() 全部用 `_safe_print()` 包裹，防止 Windows GBK 编码崩溃
- 禁止劫持 `builtins.print`

## 文件职责
| 文件 | 职责 |
|------|------|
| `apps/app_main.py` | Streamlit 主应用（地图 + 所有子页面路由） |
| `SCRIPT/emotion_analysis_v1.py` | 核心分析引擎（数据结构、管道、任务入口） |
| `SCRIPT/run_analysis.py` | CLI + Tkinter 桌面入口 |
| `core/config.py` | 全局配置（天地图Key、情绪阈值、颜色映射等） |
| `core/data_loader.py` | 统一数据加载入口 |
| `core/map_engine.py` | 空间分析引擎（底图/点状/热力图/空间分析） |
| `core/ui_components.py` | 可复用 Streamlit UI 组件 |
| `core/export.py` | CSV/GeoJSON 导出 |
| `SCRAPER/data_scraper.py` | 多源数据爬取统一入口（EmotionScraper 类 + CLI） |
| `SCRAPER/spiders/` | Scrapy Spider 目录（首个：xiaohongshu_spider） |
| `SCRAPER/settings.py` | Scrapy 全局配置 |
| `launch.py` | 一键启动 Streamlit |

## 关键概念
- **溯佰科**：城市规划时空大模型平台（数据底座+GIS工具+NL工作台），非 LLM 大模型。情绪地图未来以 Agent 嵌入
- **L0~L4 数据分级**：L0=原始爬取 → L1=治理后城市情绪DATA → L2=SnowNLP情绪地图DATA → L3=LLM增强DATA → L4=多维归因DATA
- **空间分析 MVP**：geopandas + shapely 自研，3个核心功能（热点分析/缓冲区分析/行政单元聚合）
- **数据采集铁律（空间范围优先）**：
  1. 第一优先级：加载行政区划边界 Polygon → 搜索边界内的地理位置内容
  2. 关键词搜索仅作为发现内部地名/POI的辅助手段
  3. 坐标生成必须用 point-in-polygon 约束（排除水域/山体等非建成区）
  4. 此策略适用于所有平台：大众点评/美团/小红书/微博/12345
- **数据隐私规范**：
  - 输出数据中禁止包含用户名、用户ID等个人身份信息
  - 保留：标题/正文（已公开发布的内容）、发布时间、点赞数、来源平台、子区域标签

## Agent 协作体系
- 项目使用 6 个专用 Agent 协作开发，定义在 `.github/agents/*.agent.md`
- 全局协作规则见根目录 `AGENTS.md`
- 标准流程：PM 分配 → Developer 编码 → Reviewer 审查 → Tester 测试 → Docs 文档 → PM 闭环
- 遇到 Bug 时由 Debugger 诊断，不改代码，输出修复方案交给 Developer
- 所有 Agent 启动时自动加载本文件了解架构规范
