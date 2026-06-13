# Emotion Map — Agent 协作规范

> 本项目使用多 Agent 协作模式开发。所有 Agent 必须遵守本文档定义的协作流程。

## Agent 清单

| Agent | 文件 | 职责 | 可调用 |
|-------|------|------|--------|
| 📋 进度管理员 | `.github/agents/pm.agent.md` | 任务分配、进度跟踪、状态更新、跨机上下文同步 | data, developer, debugger, reviewer, tester, docs, ops, designer, design-reviewer |
| 📡 数据管家 | `.github/agents/data.agent.md` | L0 多源数据采集 + L1 数据治理（坐标/范围/相关性筛选/脱敏） | developer, gis-developer |
| 🛠 程序开发员 | `.github/agents/developer.agent.md` | 编写代码、实现功能 | — |
| 🐛 Debug 师 | `.github/agents/debugger.agent.md` | 诊断错误、定位根因 | — |
| 🔍 代码审查员 | `.github/agents/reviewer.agent.md` | 审查代码质量与规范 | — |
| 🧪 测试工程师 | `.github/agents/tester.agent.md` | 运行测试、验证功能 | debugger |
| 📝 文档维护员 | `.github/agents/docs.agent.md` | 维护文档体系 | — |
| 🖥 环境管家 | `.github/agents/ops.agent.md` | 环境诊断、依赖同步、requirements.txt 维护 | — |
| 🎨 UI 设计师 | `.github/agents/designer.agent.md` | 前端视觉设计、布局优化、交互体验 | — |
| 👁 设计审查员 | `.github/agents/design-reviewer.agent.md` | 审查 UI 设计质量、审美一致性、设计迭代把关 | designer |
| 🗺 GIS 开发员 | `.github/agents/gis-developer.agent.md` | 地理空间数据处理、坐标系转换、空间分析 | — |

## 标准开发流程 (SOP)

```
用户需求 → PM(拆解任务) → Developer(编码)
                              ↓
                         Reviewer(审查)
                         ↙          ↘
                    通过            有问题
                     ↓                ↓
                  Tester(测试)    Debugger(诊断)
                  ↙       ↘        ↓
               通过      失败   Developer(修复)
                ↓        ↓        ↓
              Docs     Debugger  Reviewer(复审)
              (文档)   (诊断)       ↓
                ↓                Tester(重测)
              PM(闭环)              ↓
                                  ...
```

### 流程规则

1. **PM 驱动**：所有开发任务由 PM 从 `docs/todo.md` 中取任务发起
2. **先审查再测试**：代码必须经过 Reviewer 审查通过后才能交给 Tester
3. **测试失败回 Debug**：Tester 发现问题时调用 Debugger 诊断，不直接改代码
4. **修复后重审**：Debugger 输出修复方案 → Developer 修改 → Reviewer 复审
5. **文档同步**：功能验证通过后，Docs Agent 更新相关文档
6. **PM 闭环**：所有步骤完成后 PM 在 `docs/todo.md` 标记 ✅

## 共享知识库

所有 Agent 在开始工作前，应先读取以下文件了解项目上下文：

| 知识源 | 路径 | 内容 |
|--------|------|------|
| 架构规范 | `docs/architecture-pattern.md` | 七层架构、入口统一、路由规则、文件职责、关键概念、**决策追踪体系** |
| 追踪基础设施 | `core/tracker.py` | 决策追踪系统 API、ID 注册表、使用示例 |
| 任务追踪 | `docs/todo.md` | 当前任务、开发日志 |
| 架构文档 | `docs/architecture.md` | 系统架构说明 |
| 开发笔记 | `docs/dev-notes.md` | 历史踩坑记录 |
| 决策记录 | `docs/decisions.md` | 架构决策 (ADR) |

## 编码铁律

以下规则所有 Agent 必须遵守，Reviewer 重点检查：

1. **禁用 emoji**：代码中只允许 ASCII 标记 `[OK]` `[WARN]` `[LOAD]` `[ERR]`
2. **安全打印**：所有 `print()` 必须通过 `_safe_print()` 调用
3. **禁止劫持 builtins.print**：不得重新绑定 `builtins.print`
4. **入口统一**：Streamlit 只用端口 8501，子页面用 `?page=` 路由
5. **分析逻辑共用**：所有入口调用同一个 `run_analysis_task()`
6. **导出命名**：`{name}_{L1|L2|L3|L4}_result_csv.csv`
7. **数据脱敏**：输出的分析结果中禁止包含用户名/用户ID等个人身份信息
8. **空间范围优先**：数据采集以指定范围 Polygon 为第一过滤条件，关键词仅作辅助
9. **决策追踪必埋点**：每个公开函数必须 `@track()`，每个关键决策分支必须 `TrackContext`（详见铁律9说明）
10. **追踪 ID 必注册**：所有追踪 ID 必须在 `core/tracker.py` 注册表登记，编号连续不跳号

### 铁律 9 & 10 说明：决策追踪系统

**目的**：让 bug 定位从 O(n) 全量代码搜索降为 O(1) 决策 ID 精准跳转。

**基础设施**：`core/tracker.py` — 提供 `@track()` 装饰器 / `TrackContext` 上下文管理器 / `trace_*()` 快捷函数。

**模块 ID 分配**：

| 模块 ID | 文件 | 
|---------|------|
| `MOD_GOV` | `SCRIPT/data_governance.py` |
| `MOD_ANA` | `SCRIPT/emotion_analysis_v1.py` |
| `MOD_REL` | `SCRIPT/relevance_filter.py` |
| `MOD_RUN` | `SCRIPT/run_analysis.py` |
| `MOD_LOADER` | `core/data_loader.py` |
| `MOD_MAP` | `core/map_engine.py` |
| `MOD_TRANSFORM` | `core/coord_transform.py` |
| `MOD_RANGE` | `core/range_selector.py` |
| `MOD_EXPORT` | `core/export.py` |
| `MOD_UI` | `core/ui_components.py` |
| `MOD_APP` | `apps/app_main.py` |
| `MOD_SCRAPER` | `SCRAPER/spiders/` |
| `MOD_TRACKER` | `core/tracker.py` |

**埋点规则**：
- 公开函数（非 `_` 前缀）→ `@track("MOD_XXX.F_NNN")`
- 关键分支（>5 行 if/else/循环体）→ `with TrackContext("MOD_XXX.D_NNN", ...):`
- I/O 操作（文件读写/API/DB）→ 必须埋点
- 数据管道步骤 → 记录 in_n / out_n
- except 块 → `trace_error()`

**Debug 工作流**（配合 Debugger Agent）：
```
报错 → 看 [TRACE] 日志 → 定位出错决策 ID → 跳转代码 → 精准修复
```

## Agent 使用场景

> 每个 Agent 都有专属触发词和典型场景，方便快速指派任务。

### 📋 PM — 进度管理员 `@pm`
**关键词**：规划任务、分配工作、查看进度、更新状态、拆解需求、同步上下文、下班交接
**场景**：开始一天工作、启动 SOP、换机恢复上下文 | **可调用**：data, developer, debugger, reviewer, tester, docs, ops
> `@pm 开始处理 2026-06-12 的任务 1：情绪数据爬取方案调研`
> `@pm 今天有什么任务？帮我规划优先级` 
> `@pm 今天的任务都完成了，更新 todo.md 做日结`
> `@pm 同步上下文`（换机后恢复上一次会话）
> `@pm 下班交接`（离开前保存上下文到 Git）

### 📡 Data — 数据管家 `@data`
**关键词**：爬数据、采集、数据治理、L0、L1、相关性筛选、坐标转换、范围过滤
**场景**：需要采集新数据、治理原始数据、筛选城市情绪有效数据 | **可调用**：developer, gis-developer
> `@data 用 Selenium 采集小红书"规划范围"相关笔记，目标 1000 条`
> `@data 对 L0 原始数据执行 L1 治理管道（含相关性筛选）`
> `@data 检查最新 L1 数据的质量报告`

### 🛠 Developer — 程序开发员 `@developer`
**关键词**：写代码、实现功能、新建文件、修改逻辑、加页面、重构、优化性能
**场景**：实现功能、修改代码、创建模块 | **调用者**：你/PM/Debugger | 多文件必须走 SOP
> `@developer 在 app_main.py 中新增 show_heatmap_page() 子页面`
> `@developer 按 debugger 的修复方案修改 emotion_analysis_v1.py L234`

### 🐛 Debugger — Debug 师 `@debugger`
**关键词**：报错、崩溃、异常、bug、不工作、排查、定位根因、诊断
**场景**：程序报错、测试失败、编码问题(GBK/emoji)、不确定问题在哪 | **只诊断不改代码**
> `@debugger 诊断 app_main.py 中的报错：UnicodeEncodeError: 'gbk' codec...`
> `@debugger 跑 run_analysis.py 时报错，帮我定位根因`

### 🔍 Reviewer — 代码审查员 `@reviewer`
**关键词**：审查、review、检查代码、架构合规、编码规范、代码质量、复审
**场景**：代码写完后把关、重大改动前检查 | **纯静态审查，不改不跑**
> `@reviewer 审查 apps/app_main.py 的架构合规性`
> `@reviewer 审查最近修改的所有 .py 文件` | `@reviewer 重点检查 _safe_print 使用情况`

### 🧪 Tester — 测试工程师 `@tester`
**关键词**：测试、验证、跑脚本、检查输出、回归、确认功能
**场景**：审查通过后验证、发版前回归 | **发现问题找 Debugger，不改代码**
> `@tester 用 data/raw/test_0609_1.csv 跑完整分析流程，检查输出`
> `@tester 验证 Streamlit 子页面是否能正常加载`

### 📝 Docs — 文档维护员 `@docs`
**关键词**：文档、更新说明、changelog、记录、写纪要、同步、架构决策
**场景**：功能完成后同步、踩坑记录、架构变更 | **只碰文档，不改代码**
> `@docs 功能"三级分析架构重构"已完成，更新 docs/dev-notes.md`
> `@docs 在长期备忘里加一条：Docker 部署方案`

### 🖥 Ops — 环境管家 `@ops`
**关键词**：环境同步、依赖更新、pip install、两机协同、缺什么包、虚拟环境、venv
**场景**：办公室↔家里环境同步、新增依赖后更新清单、排查导入报错是否缺包 | **只碰环境，不改代码**
> `@ops 检查当前环境和 requirements.txt 是否一致，列出差异`
> `@ops 我刚 pip install 了新包，帮我更新 requirements.txt`
> `@ops 生成一份家里电脑的环境同步脚本`

### 🎨 Designer — UI 设计师 `@designer`
**关键词**：界面、布局、颜色、按钮、样式、交互、美观、UI、UX
**场景**：页面不好看、布局需调整、组件风格不统一、交互流程优化 | **只碰 UI，不改业务逻辑**
> `@designer 优化 app_main.py 的 HUD 按钮布局，统一半透明圆角风格`
> `@designer 重新设计初始载入页，去掉居中按钮，用左侧纵向三按钮导航`

### 👁 Design Reviewer — 设计审查员 `@design-reviewer`
**关键词**：设计审查、审美、风格、一致性、配色、间距、交互审查、设计走查
**场景**：设计师交付后把关审美质量、检查视觉一致性、迭代修改直到合格 | **可调用 designer**
> `@design-reviewer 审查 app_main.py 界面，重点看颜色和间距一致性`
> `@design-reviewer 设计师提交了新方案，帮我做一轮设计走查`

### 设计审查流程（子 SOP）
```
用户需求 → Designer(设计) → Design Reviewer(审美审查)
                              ↙              ↘
                           通过              有问题
                            ↓                 ↓
                           PM              Designer(修改)
                                              ↓
                                        Design Reviewer(复审)
                                              ↓
                                           ...迭代...
```

## 跨机协作（办公室 ↔ 家里）

> 两台电脑通过 Git 同步代码和上下文。每天换机后的标准操作流程：

### 换机启动（到新机器后第一件事）
```
@pm 同步上下文
```
PM 会自动：
1. 读取 `memories/repo/session-handoff.md` 恢复上次会话上下文
2. 调用 ops 执行环境自检（`@ops 环境自检`）
3. 汇报当前任务状态 + 今日计划

### 下班交接（离开前最后一件事）
```
@pm 下班交接
```
PM 会自动：
1. 汇总今日完成 + 关键决策 + 待办
2. 更新 `memories/repo/session-handoff.md`
3. 提醒你 git commit + push

### 原理
| 同步方式 | 内容 |
|----------|------|
| **Git** | 代码 + docs/ + requirements.txt + `memories/repo/`（会话交接卡） |
| **pip** | `pip install -r requirements.txt`（ops 自检） |
| **手动** | VS Code 设置/扩展（暂无自动同步） |

### ⚡ 跳过流程（仅简单改动）
单文件小改、注释修正、变量重命名等可直接 `@developer` 跳过 SOP。
> ⚠️ 涉及架构、多文件、新功能时**必须走完整 SOP**。

## 快速启动

向 PM Agent 发送以下指令即可启动标准开发流程：

```
@pm 开始处理 docs/todo.md 中今天的一个任务
```

或直接指定任务：

```
@pm 实现 XXX 功能
```
