# Emotion Map — Agent 协作规范

> 本项目使用多 Agent 协作模式开发。所有 Agent 必须遵守本文档定义的协作流程。

## Agent 清单

| Agent | 文件 | 职责 | 可调用 |
|-------|------|------|--------|
| 📋 进度管理员 | `.github/agents/pm.agent.md` | 任务分配、进度跟踪、状态更新 | developer, debugger, reviewer, tester, docs |
| 🛠 程序开发员 | `.github/agents/developer.agent.md` | 编写代码、实现功能 | — |
| 🐛 Debug 师 | `.github/agents/debugger.agent.md` | 诊断错误、定位根因 | — |
| 🔍 代码审查员 | `.github/agents/reviewer.agent.md` | 审查代码质量与规范 | — |
| 🧪 测试工程师 | `.github/agents/tester.agent.md` | 运行测试、验证功能 | debugger |
| 📝 文档维护员 | `.github/agents/docs.agent.md` | 维护文档体系 | — |

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
| 架构规范 | `docs/architecture-pattern.md` | 七层架构、入口统一、路由规则、文件职责、关键概念 |
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
8. **空间范围优先**：数据采集以行政区划边界 Polygon 为第一过滤条件，关键词仅作辅助

## Agent 使用场景

> 每个 Agent 都有专属触发词和典型场景，方便快速指派任务。

### 📋 PM — 进度管理员 `@pm`
**关键词**：规划任务、分配工作、查看进度、更新状态、拆解需求
**场景**：开始一天工作、启动 SOP、多人协作 | **可调用**：developer, debugger, reviewer, tester, docs
> `@pm 开始处理 2026-06-12 的任务 1：情绪数据爬取方案调研`
> `@pm 今天有什么任务？帮我规划优先级` 
> `@pm 今天的任务都完成了，更新 todo.md 做日结`

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
