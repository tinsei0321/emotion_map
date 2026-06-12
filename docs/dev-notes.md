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
