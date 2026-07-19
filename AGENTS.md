# Emotion Map — Agent 协作规范

> v2.1 | 9 Agent + 自动编排 + MCP 外挂 | 2026-06-17
>
> ⚠️ **概念框架声明（CB-02 讨论1）**：本文件为 AI 行为约束参考 + 新人 onboarding，**不描述运行时 Agent spawn 机制**。实际任务由 Claude Code 主线程直接执行（用户全局「不派 subagent」铁律），SOP 分级指导执行深度而非触发独立 Agent。9 个 Agent 定义 = 角色卡片，非独立执行单元。**避免第三方基于本文件做运行时误判**（CB-01 曾据 AGENTS.md 理论 SOP 模型算调用次数，与实际"主线程直接干"不符）。

## 核心理念

**Claude Code 主线程 = PM**。你不再需要手动 `@agent` 切换。给我一个任务，我在内部自动编排合适的 Agent 完成开发→审查→测试→文档的全流程，你只看到最终结果。

## Agent 清单（9 个）

| Agent | 文件 | 职责 | 可调用 |
|-------|------|------|--------|
| 🛠 Developer | `.claude/agents/developer.agent.md` | 编写代码 + 诊断修复 bug + 决策追踪埋点 | gis-developer |
| 🔍 Reviewer | `.claude/agents/reviewer.agent.md` | 审查代码质量、架构合规、追踪点完整性 | — |
| 🧪 Tester | `.claude/agents/tester.agent.md` | 运行测试、验证功能、CRS 交叉核实 | gis-developer |
| 📡 Data | `.claude/agents/data.agent.md` | L0 多源数据采集 + L1 数据治理 | developer, gis-developer |
| 🎨 Designer | `.claude/agents/designer.agent.md` | UI 视觉设计 + 交互优化 + 设计自审 | — |
| 🗺 GIS Dev | `.claude/agents/gis-developer.agent.md` | 地理空间数据处理、坐标系转换、空间分析 | — |
| 📝 Docs | `.claude/agents/docs.agent.md` | 维护文档体系、更新开发日志、记录 ADR | — |
| 🖥 Ops | `.claude/agents/ops.agent.md` | 环境诊断、依赖同步、requirements.txt 维护 | — |
| 🎯 Sim | `.claude/agents/sim-emotion-data.agent.md` | 演示数据模拟（百度热力点为底座，从演示目的逆推生成 L0~L4） | — |

> **v1.0 → v2.0 变化**：
> - 🐛 Debugger 并入 Developer — Developer 现在同时具备开发和诊断能力
> - 👁 Design Reviewer 并入 Designer — Designer 交付前通过自审清单自行把关
> - 📋 PM 不再作为独立 Agent — Claude Code 主线程承担编排角色；`pm.agent.md` 保留在 `.claude/agents/` 目录作为行为指南参考，未注册到 Agent 列表
> - 🔄 从手动 `@agent` 切换 → Claude 自动编排

## 自动编排流程

你只需要说一句话，我来拆解并自动执行：

```
你说: "实现 XX 功能"
        ↓
我自动:  ① 拆解任务（PM 视角）
         ② 按需 spawn Developer/Designer/Data/GIS Agent
         ③ 自动 spawn Reviewer 审查
         ④ 自动 spawn Tester 验证
         ⑤ 汇总结果汇报给你
```

### 三管线自动路由

| 任务类型 | 自动执行流程 |
|----------|-------------|
| **纯逻辑** | 拆解 → Developer(编码) → Reviewer(审查) → Tester(测试) → Docs(同步) |
| **纯 UI** | 拆解 → Designer(设计+自审) → 汇报 |
| **逻辑+UI** | 拆解 → Designer(出设计稿) → Developer(按稿编码) → Reviewer(审查) → Tester(测试) → Designer(复审还原度) |

### MCP 能力外挂（v2.1 | 2026-06-17）

Agent 在任何阶段可按需调用 MCP 扩充能力，**同类优先智谱**（完整路由见 `docs/mcp-strategy.md`）：

| Agent / 场景 | 首选 MCP | 备注 |
|--------------|----------|------|
| Developer / GIS — 理解开源依赖、读第三方仓库 | `zread` | zread 未收录的仓退 github MCP / 直接 clone |
| Developer — 查最新 API 用法、库变更 | `web-search-prime` | |
| Developer — 读某个文档/网页 URL | `web-reader` | 勿用下划线重复项 `web_reader` |
| Designer / Reviewer — 看设计稿、报错截图、UI 比对 | `zai-mcp-server` | 智谱主；不通退 `vision-bridge`（火山引擎） |
| Tester — 前端 E2E、异步/数据流隐患验证 | `playwright` | 按 CLAUDE.md 验证节奏，非常规改动不滥用 |
| Docs / Ops — GitHub Issue/PR 操作 | `github` MCP | 当前 PAT 失效，修复前用 `gh` CLI |

> 选型铁律：同类功能优先智谱（`zai`/`web-search-prime`/`web-reader`/`zread`），连不上再退备选。

### 何时走 SOP

以下情况自动走 SOP，但按风险等级区分流程深度：

#### SOP 风险分级（v2.1 | 2026-06-16）

| 等级 | 触发条件 | 流程 | 示例 |
|------|----------|------|------|
| **轻量** | 仅 UI/CSS/文案修改、单文件格式调整、注释修改 | Developer 直出 + Reviewer 快速扫（不 spawn Tester） | 改按钮颜色、调间距、修拼写 |
| **标准** | 涉及 2+ 文件、I/O 操作、函数签名修改 | Developer → Reviewer → Tester | 新增 API 端点、修改数据加载逻辑 |
| **严格** | 控制流修改（if/else/loop/try-except）、核心管道、追踪基础设施 | Developer → Reviewer → Tester → Reviewer 复审 | 修改 data_governance.py、tracker.py、分析算法 |

**严格模式附加要求：**
- 必须通过 `python -m pytest tests/ -q` 全部测试
- 必须验证端到端管道（L0→L1→L2）不退化
- 追踪 ID 变更必须在 PR 描述中列出

#### 触发条件详情

以下情况自动走**标准 SOP** 或以上：
- 新增或删除函数 / 类
- 修改函数签名（参数 / 返回值）
- **任何控制流逻辑修改（if/else/for/while/try-except）** → 严格
- 涉及 I/O 操作（文件读写 / API 调用）
- 涉及 2 个及以上文件
- 修改 `core/tracker.py` 或追踪基础设施 → 严格

### 何时跳过（直接 Developer 执行）

- 仅修改注释 / 文档字符串
- 变量 / 函数重命名（不改变签名）
- 单文件内的格式化 / 代码风格调整
- 修复明显的拼写错误

## 完成定义 (Definition of Done)

任务标记完成前必须全部满足：

- [ ] 代码通过 Reviewer 审查（审查报告结论为"通过"）
- [ ] 测试全部通过（Tester 报告结论为"通过"）
- [ ] 新增追踪 ID 已注册到 `core/tracker.py` 注册表
- [ ] 相关文档已更新（Docs Agent 确认）
- [ ] **用户验收**：用真实数据跑一遍，确认效果满足预期
- [ ] 无未提交的调试代码 / 临时文件残留

## 共享知识库

Agent 启动时根据下表选择性阅读知识源：

| 知识源 | 路径 | 内容 |
|--------|------|------|
| 产品需求 | `docs/prd.md` | 产品愿景、用户画像、功能优先级、验收标准 |
| 产品规范 | `docs/spec.md` | 技术实现规范、数据管道字段定义、性能预算 |
| 架构规范 | `docs/architecture-pattern.md` | 七层架构、入口统一、路由规则、决策追踪体系、前端/frontend 迁移 |
| 追踪基础设施 | `core/tracker.py` | 决策追踪系统 API、ID 注册表、使用示例 |
| 任务追踪 | `docs/todo.md` | 当前任务、开发日志 |
| 架构文档 | `docs/architecture.md` | 系统架构说明（含 frontend/MapLibre 前端层） |
| 开发笔记 | `docs/dev-notes.md` | 历史踩坑记录 |
| 决策记录 | `docs/decisions.md` | 架构决策 (ADR) |
| MCP 策略 | `docs/mcp-strategy.md` | MCP 路由手册、智谱优先、清单与测试日志 |

### 按角色推荐阅读

| Agent | 必读 | 选读 |
|-------|------|------|
| **Developer** | `spec.md`, `architecture-pattern.md`, `tracker.py` | `decisions.md`, `dev-notes.md` |
| **Reviewer** | `spec.md`, `architecture-pattern.md`, `tracker.py` | `decisions.md` |
| **Tester** | `spec.md`, `architecture-pattern.md` | `tracker.py`, `dev-notes.md` |
| **Data** | `spec.md`（数据管道章节）, `architecture-pattern.md` | `decisions.md` |
| **GIS Dev** | `spec.md`（坐标规范章节）, `architecture-pattern.md` | `tracker.py` |
| **Designer** | `spec.md`（UI 组件章节）, `design/tokens.css` | — |
| **Docs** | `architecture-pattern.md`, `decisions.md` | `dev-notes.md`, `tracker.py` |
| **Ops** | `requirements.txt`, `spec.md`（依赖章节） | — |

## 编码铁律

以下规则所有 Agent 必须遵守，Reviewer 重点检查：

1. **禁用 emoji**：代码中只允许 ASCII 标记 `[OK]` `[WARN]` `[LOAD]` `[ERR]`
2. **安全打印**：所有 `print()` 必须通过 `_safe_print()` 调用
3. **禁止劫持 builtins.print**：不得重新绑定 `builtins.print`
4. **入口统一**：前端主界面 = `frontend/`（MapLibre GL JS，`py frontend/serve.py 8080`，自起 uvicorn 后端 + Ctrl+C 同停；`apps/` Streamlit 已于 2026-07-18 退役）
5. **分析逻辑共用**：所有入口调用同一个 `run_analysis_task()`
6. **导出命名**：`{name}_{L1|L2|L3|L4}_result_csv.csv`
7. **数据脱敏**：输出的分析结果中禁止包含用户名/用户ID等个人身份信息
8. **空间范围优先**：数据采集以指定范围 Polygon 为第一过滤条件，关键词仅作辅助
9. **决策追踪必埋点**：每个公开函数必须 `@track()`，每个关键决策分支必须 `TrackContext`
10. **追踪 ID 必注册**：所有追踪 ID 必须在 `core/tracker.py` 注册表登记，编号连续不跳号

### 决策追踪系统说明（铁律 9 & 10）

**目的**：让 bug 定位从 O(n) 全量代码搜索降为 O(1) 决策 ID 精准跳转。

**基础设施**：`core/tracker.py` — 提供 `@track()` 装饰器 / `TrackContext` 上下文管理器 / `trace_*()` 快捷函数。

**模块 ID 分配**：

| 状态 | 模块 ID | 文件 |
|------|---------|------|
| ✅ | `MOD_GOV` | `SCRIPT/data_governance.py` |
| ✅ | `MOD_ANA` | `SCRIPT/emotion_analysis_v1.py` |
| ✅ | `MOD_REL` | `SCRIPT/relevance_filter.py` |
| ✅ | `MOD_RUN` | `SCRIPT/run_analysis.py` |
| ✅ | `MOD_GEN` | `SCRIPT/generate_l1_mock.py` |
| ✅ | `MOD_PERF` | `SCRIPT/sim_performance_data.py` |
| ✅ | `MOD_SCRAPER` | `SCRAPER/spiders/` |
| ✅ | `MOD_GEOCODE` | `core/geocode.py` |
| ✅ | `MOD_LLM` | `ai_qa/llm.py` |
| ✅ | `MOD_AIQA` | `ai_qa/paradigm.py` + `ai_qa/prompts.py`（select_template 路由 + 5 build_*_prompt；manifesto.py 纯常量） |
| ✅ | `MOD_SPATIAL` | `core/spatial_analysis.py` + `core/buffer_analysis.py` |
| ✅ | `MOD_FIELD` | `core/field_dictionary.py` |
| ❌ retired | `MOD_APP` | ~~`apps/`~~ 2026-07-18 整层退役（`frontend/` 接管） |
| ⬜ | `MOD_LOADER` | `core/data_loader.py` |
| ⬜ | `MOD_MAP` | `core/map_engine.py` |
| ⬜ | `MOD_TRANSFORM` | `core/coord_transform.py` |
| ⬜ | `MOD_RANGE` | `core/range_selector.py` |
| ⬜ | `MOD_EXPORT` | `core/export.py` |
| ⬜ | `MOD_MM` | `SCRIPT/multimodal_analysis.py` |
| ⬜ | `MOD_UTILS` | `core/utils.py` |
| ⬜ | `MOD_PLACE` | `core/place_layer.py` |
| ⬜ | `MOD_UI` | `core/ui_components.py`（仅 `design/backups/` 残留引用） |
| 🔧 | `MOD_TRACKER` | `core/tracker.py`（infra 本体，非业务模块） |

> **状态图例**：✅ 已埋点+`register_track_id` 注册 / ⬜ 占位待埋点（保留规划意图，不删） / 🔧 追踪 infra 本体。**注册机制** = 各模块 `register_track_id()` 在 import 时调用，运行时填充 `core/tracker.py` 的 `_TRACKING_REGISTRY`（**非** tracker.py 内静态 dict）。
>
> **5.x 主力**：`MOD_SPATIAL` / `MOD_LLM` / `MOD_FIELD` / `MOD_AIQA` 均已正式分配 ✅（ai_qa broader paradigm+prompts 已埋点；manifesto.py 纯常量无函数）。仍待埋点：上表 9 个 ⬜ 模块。**低优先，勿擅自加 ID**（守 `_TRACKING_REGISTRY` 编号连续不跳号红线——待正式分配时整体规划）。

**埋点规则**：
- 公开函数（非 `_` 前缀）→ `@track("MOD_XXX.F_NNN")`
- 关键分支（>5 行 if/else/循环体）→ `with TrackContext("MOD_XXX.D_NNN", ...):`
- I/O 操作（文件读写/API/DB）→ 必须埋点
- 数据管道步骤 → 记录 in_n / out_n
- except 块 → `trace_error()`

**Debug 工作流**：
```
报错 → 看 [TRACE] 日志 → 定位出错决策 ID → 跳转代码 → 精准修复
```

## 跨机协作（办公室 ↔ 家里）

### 换机启动
在新机器上告诉我"同步上下文"，我会：
1. 读取 `memories/repo/session-handoff.md` 恢复上次会话上下文
2. 调用 Ops Agent 执行环境自检
3. 汇报当前任务状态 + 今日计划

### 下班交接
告诉我"下班交接"，我会：
1. 汇总今日完成 + 关键决策 + 待办
2. 更新 `memories/repo/session-handoff.md`
3. 提醒你 git commit + push

### 原理
| 同步方式 | 内容 |
|----------|------|
| **Git** | 代码 + docs/ + requirements.txt + `memories/repo/`（会话交接卡） |
| **pip** | `pip install -r requirements.txt`（ops 自检） |

## 紧急回滚流程

```
发现问题 → 判断严重程度
              ↙           ↘
          紧急回滚        标准修复
           ↓                ↓
     git revert          走 SOP 流程
     + Tester 验证       (Developer → Reviewer → Tester)
     + Reviewer 快速审
```

> 紧急回滚标准：系统无法启动、核心功能崩溃、数据损坏。

## 快速启动

向我直接描述任务即可，无需 `@agent` 前缀：

```
实现 XXX 功能
```

或指定具体任务：

```
开始处理 docs/todo.md 中今天的任务
```
