# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

---

## 📋 每日模板

```markdown
## 📅 YYYY-MM-DD（周X）

### ☑ TODO List
<!-- 今天计划完成的任务，每天 ≤ 3 个大任务 -->

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

#### 🔜 明日
- 
```

---

## 📅 2026-06-12（周五）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ⬜ | 情绪数据爬取方案调研+小范围测试（西陵区） | `SCRIPT/data_scraper.py`（新建） | 数据源: 大众点评/美团/小红书/微博/12345 |
| 2 | ⬜ | 西陵区真实数据落图 | `data/raw/xiling_v1.csv` | 第一份真实情绪地图快照 |
| 3 | ✅ | Agent 协作体系搭建：程序开发/调试/进度管理/审查/测试/文档 Agent | `.github/agents/*.agent.md`, `AGENTS.md` | 6 Agent + AGENTS.md + 架构记忆 + 使用场景，基础搭建完成 |

### 📝 开发日志

**关键字**：—

#### 做了什么
- 

#### 踩坑 & 收获
- 

#### 碎片想法
- 如果爬取受阻，备用方案：手动标注 50 条 + 公开数据集

#### 🔜 明日
- Agent 架构优化 + 联动烟雾测试


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
| L1 | LLM 大模型接入 | ⬜ |
| L2 | 时序分析（多时间切片对比） | ⬜ |
| L3 | 行政区划聚合视图 | ⬜ |
| L4 | 自动报告生成（PDF） | ⬜ |
| L5 | 空间自相关分析（Moran's I） | ⬜ |
| L6 | 问题-对策映射引擎 | ⬜ |
| L7 | Docker 部署 | ⬜ |
| L8 | 配置外部化（.env） | ⬜ |
| L9 | 移动端适配 | ⬜ |
| L10 | 语料库本地化词典 | ⬜ |
