# 开发笔记 (Dev Notes)

> 按时间倒序记录开发过程、思路、踩坑与心得。  
> 格式：`YYYY-MM-DD | 主题 | 关键词`

---

## 📝 日志模板

```markdown
## YYYY-MM-DD | 一句话标题

**关键词**：tag1, tag2, tag3

### 做了什么
- 具体操作 1
- 具体操作 2

### 遇到的问题
- 问题描述 → 解决方案

### 收获 / 心得
- 学到了什么
```

---

## 📋 日志列表

<!-- 在此按时间倒序添加日志 -->

### 2026-06-17 | 前端外壳打磨 — 地图控件 / 排版体系 / popup / 光标 / 悬停

**关键词**：MapLibre 控件, design token, 3级字体浓度, popup 折叠胶囊, geojson.io 光标, 悬停高亮

#### 做了什么
- **地图控件**（`map-controls.js` 新建）：左下统一簇 复位/2D-3D(pitch 60°)/+/-/复北 + 一段式白色比例尺（Web Mercator 公式，pitch 无关）；替换原生 NavigationControl。
- **排版体系**（`design/tokens.json` geojson 段）：3 级字体浓度（`#404040/#737373/#a3a3a3`，禁纯黑）+ size 补档(2xs/xl/2xl) + lineHeight/letterSpacing/胶囊 token；8 组件 CSS 硬编码扫平到 token；`brand-visual.md` 新增「字体系统」整章（信息层级原则 + 深/浅底配字规则 + 场景表）。
- **外壳打磨**：标题拆分（中文加大粗 + 24px + 英文小细）；图例→右下、popup→右上（absolute 锚 `#map` 跟随右栏）；popup 4 层级 + 胶囊圆角(28px) + **点空白折叠成极性色分数胶囊**（复用 badge）+ 评论 2 行省略 + `[hidden]` 修复；左簇改 absolute 与图例底平齐；Overview/Table 标签**深蓝激活态(#004691)+白粗**；Table 字号缩小密度提高；地图光标 **geojson.io 式**（箭头/pointer/grabbing 三态 class 切换，样式表 `!important` 压过 MapLibre 行内 grab，无点击闪手）；点**悬停轮廓环**；S 工具→空心指针 SVG；激活工具统一**蓝底白字**。
- 提交：`ba6b0ad` `b8097c0` `2b4315b` `d010ffb`（59 tests 全程过）。

#### 收获 / 心得
- **同源定位才能真平齐**：左簇（MapLibre 控件 + margin）与图例（absolute）两套机制靠调像素永远对不齐 → 都改成 absolute 锚 `#map` 同 `bottom` → 几何必然平齐（实测 829=829）。
- **`display:flex` 会压过 HTML `hidden`**：`.popup{display:flex}` 优先级高于 `[hidden]{display:none}` → 首屏空白 popup + × 关不掉 + 连锁折叠失效；`.popup[hidden]{display:none}` 一处修复全部。
- **地图光标稳压 MapLibre**：行内 `style.cursor`（非 !important）必输给样式表 `!important`；用 class(`is-pointer`/`is-grabbing`)+`dragstart/dragend` 切换，既保留点的 pointer、又只在真拖拽变手（无点击闪手）。
- **验证节奏**：视觉/布局小改 → 起页交用户肉眼验（**不上 Playwright**，识图对 UI 不准）；控制流/异步（折叠、光标、比例尺）才上 Playwright——这条已写进 Auto Memory。
- 数据侧摸清：**CSV/GeoJSON 文件，非数据库**；FastAPI `api/` 已就绪可跑（下轮 Analysis 接线即可）。

---

### 2026-06-17 | 闭环补强 — 把开环的 harness×agent×MCP×skill 补成闭环（ADR-014）

**关键词**：闭环, 反馈链, trace 落盘, pre-commit, emoji hook, PII guard, Auto Memory, CI

#### 做了什么
- 诊断：协作体系=半成品（agent 孤岛、MCP/skill 未下沉进 agent 定义），闭环体系=开环（trace 不落盘、无提交门禁、Auto Memory 空转且索引缺失）
- 8 波补强：①tracker 落盘+recent_errors ②/verify+pre-commit ③emoji PreToolUse hook+PII 测试 ④SessionEnd trace 摘要回灌 ⑤8 agent v2.1+MCP 能力段 ⑥MEMORY.md 索引+修陈旧记忆+种子 ⑦GitHub Actions CI ⑧skill 索引(物理移除暂缓)
- 验证：pytest 56→59 passed 零回归；emoji hook 精确拦 U+1F389 放行中文/箭头；trace 落盘+recent_errors 实测；digest 生成+游标防重实测；pre-commit hook 实测放行

#### 收获 / 心得
- **闭环的关键是反馈，不是前向**：前向链（dev→review→test→docs）早就齐，缺的是"经验回灌"——trace 落盘+摘要、提交门禁、记忆召回，这三处补上才从开环变闭环
- **索引是召回的前提**：Auto Memory 写了 6 条但没 MEMORY.md 索引，等于全废——写记忆必须同步写索引
- **Windows hook 必须 UTF-8 显式解码**：emoji hook 初版被 cp936 坑到静默放行，`sys.stdin.buffer.read().decode('utf-8')` 是正解
- **红线项要敢暂停确认**：skill 物理移除 1521 文件、卸载行为不确定，及时停下问用户比盲执行好——选了"保留现状"

---

### 2026-06-17 | MCP 能力层纳入 vibe coding — 实测 + 智谱优先路由策略

**关键词**：MCP, 智谱优先, vibe coding, ADR-013, vision-bridge, zai-mcp-server, github PAT

#### 做了什么
- 全量冒烟测试 9 个 MCP（项目 `.mcp.json` 3 + 用户 `~/.claude.json` 4 + 插件来源 2）：7 通 / github 认证失败 / web-reader 与 web_reader 重复
- 新建 `docs/mcp-strategy.md`：原则（智谱优先 + 回退阶梯）、清单、任务→MCP 路由表、分家族手册、运维、测试日志
- CLAUDE.md：头部戳更新（`Skill 464`→`MCP 7`，06-15→06-17）、规则 11 视觉主备改（zai 主 / vision-bridge 备）、新增规则 12（智谱优先）、登记文档×2、补开发状态行
- AGENTS.md 升 v2.1：新增「MCP 能力外挂」子节（按 Agent/场景给首选 MCP）、知识库表登记
- ADR-013 落档：MCP 能力层 + 智谱优先，选项 A/B/C 对比

#### 收获 / 心得
- 「同功能多 provider」是 MCP 时代的常见混乱源——需一份路由表 + 选型铁律收敛，否则凭直觉选、付费能力被埋没
- MCP 的 `disabled:true` 不可靠：github 标了禁用仍被加载并报认证错——要禁干净得移除条目或重启确认
- 主循环模型本就是 GLM 系，智谱 MCP 与之同源，认证/延迟统一，「智谱优先」既是偏好也是工程合理

---

### 2026-06-12 | Scrapy 数据采集系统搭建 — 确定爬取技术方案

**关键词**：Scrapy, 数据采集, 小红书, Spider, Pipeline

#### 做了什么
- 完成数据爬取技术选型：Scrapy 框架（选项对比：自研脚本 / Scrapy / 购买数据）
- 搭建 SCRAPER/ 标准 Scrapy 项目（settings / items / pipelines / middlewares / spiders）
- 编写首个 Spider：xiaohongshu_spider（目标：西陵区笔记搜索）
- 实现 EmotionDataPipeline：URL 去重 → 文本清洗 → 自动导出 CSV 到 data/raw/
- 实现 UA 轮换中间件、礼貌爬取策略（延迟 2s、并发=1）
- 测试验证：小红书搜索页 HTTP 200，SSR 数据可提取（无需登录）
- 编写统一入口 data_scraper.py（EmotionScraper 类 + CLI argparse）
- 全流程 SOP 实战：PM 拆解 → Developer 搭建 → Reviewer 审查（通过）→ Tester 验证（通过）

#### 收获 / 心得
- Scrapy 框架非常适合多源持续采集场景，内置的 Pipeline/去重/限速省去大量手写代码
- 小红书搜索页目前无需登录即可访问，SSR 数据（__INITIAL_STATE__）可直接解析，这是提取数据的可行路径
- _safe_print 在 SCRAPER/ 中有 3 处重复定义，长期考虑提取到 core/ 统一导入

---

### 2026-06-12 | 系统架构优化 — 七层架构 + 空间分析引擎重定义

**关键词**：架构, 重构, 数据采集, 空间分析, 溯佰科

#### 做了什么
- 系统架构从 6 层扩展为 7 层：新增"数据采集层"（SCRAPER/），置于数据层之上
- "地图引擎层"→"空间分析引擎层"，扩展职责为底图渲染 + 空间可视化 + 空间分析（热点/缓冲区/行政单元聚合）
- "分析引擎层"→"数据分析引擎层"，明确 L1(数据治理)→L2(SnowNLP)→L3(LLM)→L4(多维归因) 四级管道
- 纠正溯佰科定位：从"LLM大模型"改为"城市规划时空大模型平台（数据底座+GIS工具+NL工作台）"
- 数据层引入 L0~L4 五级数据分级概念
- 空间分析工具选型决策：MVP 阶段使用 geopandas + shapely 自研
- 同步更新 `architecture.md`、`decisions.md`（ADR-007）、`architecture-pattern.md`、`emotion_analysis_v1.py`、`map_engine.py`

#### 收获 / 心得
- 好的架构命名反映了对问题域的理解深度："地图引擎"→"空间分析引擎"不只是换名字，而是重新定义了这层的职责边界
- 数据分级(L0~L4)让数据管道可溯源——每一级输出都是独立的数据资产
- 溯佰科定位纠正是关键修正——避免团队在错误的技术方向上前进
- 作为 PM Agent 调度的第一个任务，验证了 SOP 流程的有效性：PM 研判 → Developer 修改代码 → PM 同步文档

---

### 2026-06-11 | 项目文档化 — 建立 docs 目录

**关键词**：文档, 架构, TODO, 项目管理

#### 做了什么
- 创建 `docs/` 目录，包含：
  - `dev-notes.md` — 开发笔记（本文件）
  - `architecture.md` — 系统架构设计
  - `decisions.md` — 技术决策记录
  - `todo.md` — 待办事项（按阶段推进）

#### 收获 / 心得
- 文档化是项目从原型向工程化演进的关键一步
- 好的文档结构不追求多，追求"刚好够用"：开发笔记 + 架构 + 决策 + TODO 四种文件覆盖了日常所需

---

### 2026-06-09 | 情绪分析引擎 v1.0 — 模块化重构

**关键词**：重构, 抽象接口, 工厂模式, 可插拔架构

#### 做了什么
- 将散落在 `test_scripts.py` / `test_scripts_2.py` 中的分析逻辑抽象到 `SCRIPT/emotion_analysis_v1.py`
- 设计了 `AnalyzerBase` 抽象基类，统一 SnowNLP 和未来 LLM 的调用接口
- 实现 `SnowNLPAnalyzer`（批量向量化 + 逐条模式）
- 实现 `LLMAnalyzer` 模板（为溯佰科大模型预留）
- 添加 `create_analyzer()` 工厂函数和 `run_pipeline()` 一键管道

#### 收获 / 心得
- 用 ABC + dataclass 让架构清晰且可扩展
- Pipe and Filter 模式很适合数据分析管道
- 引擎切换只需改一行代码

---

### 2026-06-09 | Streamlit 全屏地图应用 — v3 重构

**关键词**：Streamlit, HUD, 弹窗, 模块化

#### 做了什么
- 将 `streamlit_app_v2` 迁移到 `apps/app_main.py`，基于 `core/` 模块
- 实现 HUD 浮动按钮系统（📂数据源 / ⚙设置 / 📊概览 / 📋表格）
- 实现 Streamlit Dialog 弹窗（数据源选择、数据概览、数据表格、设置）
- 添加坐标重复度分析面板
- 使用 CSS `position:fixed` + JS 实现零留白全屏地图

#### 遇到的问题
- Folium iframe 在全屏模式下有留白 → 使用 `position:fixed` + JS 动态调整解决
- Streamlit 按钮默认 z-index 较低被地图遮挡 → 统一设置 `z-index: 9999/10000`

#### 收获 / 心得
- Streamlit Dialog 适合模态弹窗场景，但要注意 session_state 的状态管理
- 全屏地图的 CSS hack 在不同浏览器需要验证

---

### 2026-05-28 ~ 05-31 | 项目启动 — DeepSeek 对话 + 框架搭建

**关键词**：课题启动, 需求梳理, 三段式框架, Vibe Coding, 零基础

#### 做了什么
- 与 AI 进行了 20 轮对话（详见 README.md 问题清单）
- 确定了"三段式"工作框架：理论 → 软件/采集 → 治理/分析/可视化
- 明确了技术栈：Python + SnowNLP + Streamlit + Folium
- 确定了 MVP 策略：SnowNLP 先行，完整版换 Senta/BERT/LLM
- 梳理了七个落地应用场景

#### 关键决策
- Python 学到"能审计 AI 输出"的程度，而非精通
- SnowNLP 的不准确恰好可以成为研究发现的来源
- MVP 只需 L2 中观空间单元 + 三维核心指标 + 问题-对策映射表

---

## 🔖 附录：常用命令

```bash
# 启动 Streamlit 主应用
python -m streamlit run apps/app_main.py

# 运行情绪分析引擎
python SCRIPT/run_analysis.py

# 安装依赖
pip install -r requirements.txt
```
