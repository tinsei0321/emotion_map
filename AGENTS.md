# Emotion Map — Agent 协作规范

> 本项目使用多 Agent 协作模式开发。所有 Agent 必须遵守本文档定义的协作流程。

## Agent 清单

| Agent | 文件 | 职责 | 可调用 |
|-------|------|------|--------|
| 📋 进度管理员 | `.github/agents/pm.agent.md` | 任务分配、进度跟踪、状态更新、跨机上下文同步 | data, developer, debugger, reviewer, tester, docs, ops, designer, design-reviewer, gis-developer |
| 📡 数据管家 | `.github/agents/data.agent.md` | L0 多源数据采集 + L1 数据治理（调度 GIS Developer 执行坐标转换/范围过滤 + 相关性筛选/脱敏） | developer, gis-developer |
| 🛠 程序开发员 | `.github/agents/developer.agent.md` | 编写代码、实现功能 | debugger, gis-developer |
| 🐛 Debug 师 | `.github/agents/debugger.agent.md` | 诊断错误、定位根因 | — |
| 🔍 代码审查员 | `.github/agents/reviewer.agent.md` | 审查代码质量与规范 | — |
| 🧪 测试工程师 | `.github/agents/tester.agent.md` | 运行测试、验证功能 | debugger, gis-developer |
| 📝 文档维护员 | `.github/agents/docs.agent.md` | 维护文档体系 | — |
| 🖥 环境管家 | `.github/agents/ops.agent.md` | 环境诊断、依赖同步、requirements.txt 维护 | — |
| 🎨 UI 设计师 | `.github/agents/designer.agent.md` | 前端视觉设计、布局优化、交互体验 | — |
| 👁 设计审查员 | `.github/agents/design-reviewer.agent.md` | 审查 UI 设计质量、审美一致性、设计迭代把关 | designer |
| 🗺 GIS 开发员 | `.github/agents/gis-developer.agent.md` | 地理空间数据处理、坐标系转换、空间分析 | — |

## 标准开发流程 (SOP)

> PM 根据任务类型将需求路由到不同管线：纯逻辑走代码线，纯 UI 走设计线，逻辑+UI 两线并行。

```
                        用户需求
                           ↓
                      PM(拆解+路由)
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
          纯 UI 任务   逻辑+UI 任务   纯逻辑任务
              │            │            │
    ┌─────────┘    ┌───────┴───────┐    │
    ↓              ↓               ↓    │
 Designer     Designer         Developer │
    ↓         (设计稿)             │     │
  Design         ↓               │     │
 Reviewer    Developer           │     │
    ↓         (编码)             │     │
  通过?          ↓               │     │
  ├─ 否→迭代   合并              │     │
  ↓              │               │     │
  PM             ↓               ↓     ↓
              Reviewer ──────────┘     │
              ↙          ↘            │
           通过          有问题        │
            ↓              ↓           │
         Tester       Debugger(诊断)   │
         ↙    ↘          ↓            │
      通过   失败    Developer(修复)   │
       ↓      ↓          ↓            │
     Docs  Debugger   Reviewer(复审)   │
       ↓   (诊断)        ↓            │
       ↓               Tester(重测)    │
       ↓                  ↓            │
       └──────────┬───────┘            │
                  ↓                    │
              用户验收 ←───────────────┘
              ↙      ↘
           通过       失败 → PM 路由回对应 Agent
            ↓                   ├─ 逻辑问题 → Developer → Reviewer → Tester
         PM(闭环)               ├─ UI 问题   → Designer → Design Reviewer
                                └─ 性能问题 → Developer → Reviewer（快速审）→ Tester
```

### 三种任务路由

| 任务类型 | 管线 | 示例 |
|----------|------|------|
| **纯逻辑** | PM → Developer → Reviewer → Tester → Docs → 验收 | 新增分析算法、修改数据管道 |
| **纯 UI** | PM → Designer → Design Reviewer → 验收 | 调整按钮样式、重新布局 |
| **逻辑 + UI** | 设计线先行 → 设计稿交付后代码线启动 → 合并 → Tester → Docs → 验收 | 新增热力图页面、重构分析控制台 |

> 逻辑+UI 任务中，Designer 交付后 Developer 按设计稿编码，Design Reviewer 在最终验收阶段复审设计还原度。

### UI 改动在流程中的位置

所有 UI 相关改动（无论任务类型）都经过 Designer → Design Reviewer 闭环：
- **纯 UI 任务**：Designer 设计 → Design Reviewer 审查 → PM 放行 → 用户验收 → PM 闭环
- **逻辑+UI 任务**：Designer 先出设计稿 → Design Reviewer 审查通过 → Developer 按稿编码 → Reviewer → Tester → 用户验收（Design Reviewer 在此阶段复审设计还原度）
- **纯逻辑任务**：不涉及 UI，跳过设计审查

### 流程规则

1. **PM 驱动**：所有开发任务由 PM 从 `docs/todo.md` 中取任务发起，按任务类型路由
2. **设计先行**：逻辑+UI 任务必须先出设计稿，Developer 再按稿编码
3. **先审查再测试**：代码必须经过 Reviewer 审查通过后才能交给 Tester
4. **测试失败回 Debug**：Tester 发现问题时调用 Debugger 诊断，不直接改代码
5. **修复后重审**：Debugger 输出修复方案 → Developer 修改 → Reviewer 复审
6. **文档同步**：功能验证通过后，Docs Agent 更新相关文档
7. **用户验收**：用真实数据跑一遍，确认效果满足预期（含设计还原度检查）
8. **PM 闭环**：所有步骤完成后 PM 在 `docs/todo.md` 标记 ✅

### 用户验收失败路径

用户验收不通过时，PM 判断问题类型并路由回对应 Agent：
- 数据结果/分析逻辑问题 → Developer 修改 → Reviewer → Tester → 用户验收
- UI 交互/视觉效果问题 → Designer 修改 → Design Reviewer → 用户验收
- 性能不达标 → Developer 优化 → Reviewer（快速审）→ Tester 重测 → 用户验收

### 任务就绪定义 (Definition of Ready)

Developer / Designer 接任务前必须满足：

- [ ] 任务目标一句话可描述（做什么、为什么做）
- [ ] 涉及的文件/模块已明确列出
- [ ] 依赖的其他 Agent 产出已就绪（如 Designer 稿、Data Agent 数据集）
- [ ] 验收标准已与 PM 对齐（怎么算"做完"）
- [ ] 阻塞项已提前识别并记录

### 完成定义 (Definition of Done)

任务标记 ✅ 前必须全部满足：

- [ ] 代码通过 Reviewer 审查（审查报告结论为"通过"）
- [ ] 测试全部通过（Tester 报告结论为"通过"）
- [ ] 新增追踪 ID 已注册到 `core/tracker.py` 注册表
- [ ] 相关文档已更新（Docs Agent 确认）
- [ ] **用户验收**：用真实数据跑一遍，确认效果满足预期
- [ ] 无未提交的调试代码 / 临时文件残留

## 共享知识库

Agent 启动时根据下表选择性阅读知识源。如需深入了解特定领域，再查阅对应文件：

| 知识源 | 路径 | 内容 |
|--------|------|------|
| 架构规范 | `docs/architecture-pattern.md` | 七层架构、入口统一、路由规则、文件职责、关键概念、**决策追踪体系** |
| 追踪基础设施 | `core/tracker.py` | 决策追踪系统 API、ID 注册表、使用示例 |
| 任务追踪 | `docs/todo.md` | 当前任务、开发日志 |
| 架构文档 | `docs/architecture.md` | 系统架构说明 |
| 开发笔记 | `docs/dev-notes.md` | 历史踩坑记录 |
| 决策记录 | `docs/decisions.md` | 架构决策 (ADR) |

### 按角色推荐阅读

> 不必全读。下表标注各 Agent 的必读与选读知识源。

| Agent | 必读 | 选读 |
|-------|------|------|
| **PM** | `architecture-pattern.md`, `todo.md` | `decisions.md`, `dev-notes.md` |
| **Developer** | `architecture-pattern.md`, `tracker.py` | `decisions.md`, `dev-notes.md` |
| **Reviewer** | `architecture-pattern.md`, `tracker.py` | `decisions.md` |
| **Tester** | `architecture-pattern.md` | `tracker.py`, `dev-notes.md` |
| **Debugger** | `tracker.py`, `architecture-pattern.md` | `dev-notes.md` |
| **Data Agent** | `architecture-pattern.md`, `config.py` | `decisions.md` |
| **GIS Developer** | `architecture-pattern.md`（空间分析章节）, `config.py` | `tracker.py` |
| **Designer** | `architecture-pattern.md`（文件职责章节）, `design/tokens.css` | — |
| **Design Reviewer** | `architecture-pattern.md`（文件职责章节）, `design/tokens.css` | — |
| **Docs** | `architecture-pattern.md`, `decisions.md` | `dev-notes.md`, `tracker.py` |
| **Ops** | `requirements.txt`, `architecture-pattern.md` | — |

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

> **调用方式**：Agent 之间通过你（用户）手动 `@agent` 调用来串联流程，并非自动编排。
> 例如：PM 会输出"请 @developer 实现 X"，然后由你手动切换。

| Agent | 触发词 | 场景 | 可调用 | 详细定义 |
|-------|--------|------|--------|----------|
| 📋 PM | 规划任务、分配工作、查看进度、拆解需求、同步上下文、下班交接 | 开始一天工作、启动 SOP、换机恢复上下文 | data, developer, debugger, reviewer, tester, docs, ops, designer, design-reviewer, gis-developer | `pm.agent.md` |
| 📡 Data | 爬数据、采集、数据治理、L0、L1、相关性筛选、坐标转换、范围过滤 | 采集新数据、治理原始数据、筛选有效数据 | developer, gis-developer | `data.agent.md` |
| 🛠 Developer | 写代码、实现功能、新建文件、修改逻辑、加页面、重构、优化性能 | 实现功能、修改代码、创建模块 | debugger, gis-developer | `developer.agent.md` |
| 🐛 Debugger | 报错、崩溃、异常、bug、排查、定位根因、诊断 | 程序报错、测试失败、编码问题 | — | `debugger.agent.md` |
| 🔍 Reviewer | 审查、review、检查代码、架构合规、编码规范、代码质量、复审 | 代码写完后把关、重大改动前检查 | — | `reviewer.agent.md` |
| 🧪 Tester | 测试、验证、跑脚本、检查输出、回归、确认功能 | 审查通过后验证、发版前回归 | debugger, gis-developer | `tester.agent.md` |
| 📝 Docs | 文档、更新说明、changelog、写纪要、同步、架构决策 | 功能完成后同步、踩坑记录、架构变更 | — | `docs.agent.md` |
| 🖥 Ops | 环境同步、依赖更新、pip install、两机协同、虚拟环境、venv | 环境同步、新增依赖、排查缺包 | — | `ops.agent.md` |
| 🎨 Designer | 界面、布局、颜色、按钮、样式、交互、美观、UI、UX | 页面设计、布局调整、交互流程优化 | — | `designer.agent.md` |
| 👁 Design Reviewer | 设计审查、审美、风格、一致性、配色、间距、交互审查、设计走查 | 设计师交付后把关审美质量、检查视觉一致性 | designer | `design-reviewer.agent.md` |
| 🗺 GIS Dev | 坐标转换、CRS、投影、空间分析、GeoJSON、Shapely | 地理空间数据处理、坐标系转换 | — | `gis-developer.agent.md` |

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

以下情况可跳过 SOP，直接 `@developer` 执行：
- 仅修改注释 / 文档字符串
- 变量 / 函数重命名（不改变签名）
- 单文件内的格式化 / 代码风格调整
- 修复明显的拼写错误

以下情况**必须走完整 SOP**：
- 新增或删除函数 / 类
- 修改函数签名（参数 / 返回值）
- **任何控制流逻辑修改（if/else/for/while/try-except，无论行数）**
- 涉及 I/O 操作（文件读写 / API 调用 / DB）
- 涉及 2 个及以上文件
- 修改 `core/tracker.py` 或追踪基础设施

> ⚠️ 不确定时，走 SOP（宁可多一步审查，不放一个隐患）。

### 🔄 紧急回滚流程

如果已部署的变更需要紧急回滚：

```
发现问题 → PM 判断严重程度
              ↙           ↘
          紧急回滚        标准修复
           ↓                ↓
    PM 直接 git revert   走 SOP 流程
     + @tester 验证      (Debugger → Developer → Reviewer → Tester)
     + @reviewer 快速审查回滚 diff
           ↓
    PM 记录到 todo.md
```

> 紧急回滚标准：系统无法启动、核心功能崩溃、数据损坏。

## 快速启动

向 PM Agent 发送以下指令即可启动标准开发流程：

```
@pm 开始处理 docs/todo.md 中今天的一个任务
```

或直接指定任务：

```
@pm 实现 XXX 功能
```
