# DeepSeek 深度扫描评估报告

> **扫描模型**：DeepSeek V4 Pro（0488bc9d-b351-43d0-aa69-05300248e59d）
> **扫描时间**：2026-07-18
> **CB 轮次**：01（首轮）
> **项目**：emotion_map — 城市情绪地图平台
> **开发模型**：Claude Code（主）+ DeepSeek V4（评审）
> **扫描方法**：4 个 Explore Agent 并行深度刺探，覆盖 ~100 个文件，遍历全部核心模块
>
> ---
> **归档信息**：原始路径 `docs/SCAN_DeepSeek.md`，于 2026-07-19 移入 `docs/catch-ball/` 归档。正文内容一字未改。

---

## 第一部分：扫描内容

### 1.1 扫描范围一览

| 维度 | 扫描对象 | 文件数 | 关键发现 |
|------|---------|--------|---------|
| **顶层配置** | AGENTS.md, CLAUDE.md, MEMORY.md, README.md, requirements.txt, pytest.ini, .mcp.json, .gitignore, .claudeignore, .env, .env.example, serve.py | 12 | Agent 协作规范 v2.1，8+1 Agent，三管线自动路由 |
| **Agent/Harness** | `.claude/agents/`（9 活跃 + 3 归档），`.claude/hooks/`（5 hooks），`.claude/commands/`（6 命令），`skills-lock.json`，`.claude/SKILLS_INDEX.md`，`.claude/settings.json`，`vision_bridge_server.py` | 26 | 5 层防护体系：Hook → Command → Agent → SOP → 铁律 |
| **Core 核心库** | `tracker.py`, `config.py`, `utils.py`, `spatial_analysis.py`, `buffer_analysis.py`, `data_loader.py`, `map_engine.py`, `coord_transform.py`, `field_dictionary.py`, `geocode.py`, `place_layer.py`, `export.py`, `range_selector.py`, `ui_components.py`, `db.py`, `topo_scanner.py`, `geo_registry.py`, `layer_registry.py` | 18 | ~5,200 行，决策追踪 55 个 ID，9 个模块仍待埋点 |
| **SCRIPT 分析管道** | `run_analysis.py`, `data_governance.py`, `emotion_analysis_v1.py`, `relevance_filter.py`, `multimodal_analysis.py`, `generate_l1_mock.py`, `generate_test_data.py`, `sim_performance_data.py`, `performance_config.py`, `sim_ermawu_l3l4.py` 等 | 16 | ~11,000 行，L0→L4 管道完整，含 ABC 多引擎分析器 |
| **API 层** | `main.py`, `routes.py`, `geo_routes.py`, `sandbox.py`, `run_routes.py`, `aiqa_routes.py`, `topo_routes.py`, `schemas.py` | 8 | ~2,048 行，FastAPI REST，GIS 工具箱 12 端点，三层安全沙箱 |
| **AI QA 子系统** | `__init__.py`, `manifesto.py`, `paradigm.py`, `prompts.py`, `llm.py`, `review.py`, `wisdom.py`, `router.py`, `episode.py`, `consolidate.py`, `landuse_codes_2023.py` + `industry_kb/`（4 领域） | 14 | ~2,160 行，4 层 Harness（知识/思考/执行/审查），16 技能模板 |
| **Frontend 前端** | `index.html`, `serve.py`, `topology.html`, `js/`（28 ES 模块），`css/`（15 文件），`js/ai_qa/`（6 文件），`vendor/`（6 库） | 64 | ~16,000 行 JS，零构建步骤，MapLibre GL JS + deck.gl |
| **Tests 测试** | `conftest.py`, `test_*.py`（14 模块），`browser/`（E2E），`eval_template_flash.py` | 17 | 182 测试函数，~2,500 行，全部通过（pytest 全绿） |
| **Docs 文档** | 25+ 篇技术文档 + 图片/PDF | 30+ | 覆盖 PRD、架构、规范、ADR、开发日志、场景等 |

### 1.2 扫描深度说明

- **Level 1（全量阅读）**：AGENTS.md, CLAUDE.md, 所有 Agent 定义文件, 所有 Hook 脚本, 所有 Command 定义, `core/tracker.py`, `core/config.py`, `ai_qa/manifesto.py`, `ai_qa/llm.py`, `frontend/serve.py`
- **Level 2（关键函数+结构）**：所有 Core 模块, 所有 API 路由, AI QA 核心文件, Frontend 主要 JS 模块
- **Level 3（概览+头部）**：SCRIPT 分析脚本, 测试文件, 文档文件, Scrapy 爬虫

---

## 第二部分：扫描结果/评价

### 2.1 Vibe Coding 策略评估

#### 2.1.1 总体评价：**良好，存在改进空间**

项目构建了一套完整的 "AI 驱动的软件开发体系"，从 Agent 角色分工 → 自动编排 → 质量门禁 → 知识积累，形成闭环。这套体系在**小团队（1 人）高频迭代**场景下是有效的。

#### 2.1.2 优势

| 优势点 | 具体表现 |
|--------|---------|
| **角色解耦清晰** | 9 个 Agent 各司其职（Developer/Reviewer/Tester/Data/Designer/GIS/Ops/Docs/Sim），互不越界 |
| **SOP 风险分级** | 轻量/标准/严格三级，避免"一刀切"的流程疲劳 |
| **知识分层注入** | Agent 按角色选择性阅读文档（必读/选读），减少无关上下文污染 |
| **铁律硬约束** | 12 条规则 + Hook 拦截（emoji 禁止）+ 测试门禁，减少人工审查 |
| **跨机协作** | session-handoff.md 机制支持办公室↔家里无缝切换 |

#### 2.1.3 问题与隐患

| 问题 | 严重度 | 说明 |
|------|--------|------|
| **自动编排依赖模型判断** | 中 | AGENTS.md 声明"我自动路由到合适的 SOP 层级"，但路由逻辑完全依赖 Claude Code 主线程的模型判断，无结构性强制机制。如果模型误判为"轻量"而实际涉及控制流变更，会跳过必要的 Reviewer/Tester 流程 |
| **Agent 调用链深度风险** | 中 | Data Agent 可调用 Developer + GIS Developer；Developer 可调用 GIS Developer；Tester 可调用 GIS Developer。理论上可形成 Data→Developer→GIS 的 3 层嵌套调用链，每层增加延迟和 token 消耗 |
| **文档膨胀消耗上下文** | 中 | AGENTS.md（251 行）+ CLAUDE.md（279 行）在每次会话启动时全量加载，占用显著上下文窗口。虽有三层记忆体系缓解，但基础负载仍较高 |
| **Sim Agent 未注册** | 低 | `sim-emotion-data.agent.md` 存在于 `.claude/agents/` 且有完整工具权限，但未在 `settings.json` 的 agents 列表中注册，不可发现 |

---

### 2.2 Harness 框架评估

#### 2.2.1 总体评价：**设计精良，是项目最成熟的工程部分**

5 个 Hook 形成"启动自检→编辑拦截→编辑清理→压缩快照→结束摘要"的完整生命周期管理。

#### 2.2.2 Hook 逐项评价

| Hook | 评价 | 亮点 | 隐患 |
|------|------|------|------|
| **on_session_start** | 良好 | 非阻塞式环境自检（API Key、TODO 数量、Git 脏状态、花园阈值） | 依赖 `.env` 和 `.trace/trace.log` 存在，缺失时静默失败 |
| **on_session_end** | 优秀 | **trace 增量摘要**是最佳设计——用 cursor 文件追踪已读行数，每次只增量追加新错误到 `docs/trace-digest.md`，实现跨会话错误持久化 | 依赖 `.claude/.trace-digest-cursor` 文件完整性 |
| **on_pre_edit_lint** | 优秀 | **真正有效的拦截**——exit code 2 阻止工具调用，不是建议而是强制。精准范围：仅拦截补充平面 emoji（U+1F000-U+1FAFF），不误伤 CJK/箭头 | 仅覆盖 `.py` 文件，`.js`/`.md` 文件的 emoji 不会被拦截 |
| **on_post_edit** | 良好 | 精确清理——仅删除被编辑模块的 `.pyc`/`.pyo`，不做全项目递归清理 | 不清理 `__pycache__` 目录本身（仅删除文件），长期可能残留空目录 |
| **on_precompact** | 创新 | 压缩前的机器快照（`.wip.md`）是解决"上下文窗口重置"问题的有效手段 | 快照内容（git status + commits + trace tail）偏工程状态，缺少"当前正在做什么"的语义叙述 |

#### 2.2.3 Commands 评价

| Command | 实用性 | 说明 |
|---------|--------|------|
| `/verify` | ⭐⭐⭐⭐⭐ | 提交前门禁，集成 pytest + tracker 合规 + trace 错误 + PII 守护 |
| `/garden` | ⭐⭐⭐⭐ | 上下文树除草，检测僵尸记忆/大文件膨胀/清单漂移 |
| `/weed` | ⭐⭐⭐⭐ | 文件分类（绿/黄/红安全等级），安全删除流程 |
| `/sync-log` | ⭐⭐⭐ | 提交后同步修订日志和 TODO，但依赖人工记得调用 |
| `/frontend-pitfall-check` | ⭐⭐⭐⭐ | 针对性极强——扫描 3 个 JS 已知陷阱，实用价值高 |
| `/curate-memory` | ⭐⭐⭐ | 深层记忆树 GC，功能强大但使用频率可能较低 |

---

### 2.3 Agent 体系评估

#### 2.3.1 角色定义质量

| Agent | 定义质量 | 亮点 | 不足 |
|-------|---------|------|------|
| Developer | 优秀 | 完整的追踪埋点要求，O(1) 调试范式 | 未明确与 Reviewer 的交互协议（如何响应 NEEDS_CHANGE） |
| Reviewer | 优秀 | 结构化的审查清单（7 轴），明确的 PASS/NEEDS_CHANGE/REJECT 输出格式 | 只读权限，无法执行测试验证 |
| Tester | 良好 | CRS 交叉验证协议（与 GIS Dev 协作） | 缺少 E2E 测试触发条件说明 |
| Data | 优秀 | 详细的双层漏斗策略 + 三种 LLM 分类路线，领域知识丰富 | 可调用 2 个 Agent，调用链最深 |
| Designer | 良好 | 自审清单详细（极简/一致/地图优先/交互合理） | execute 权限说明模糊——"仅用于运行 Token 生成脚本和启动预览" |
| GIS Dev | 优秀 | 强制 CRS 验证协议（读取→确认→执行→校验→通知） | DO NOT 约束清晰（不写业务逻辑、不修改 UI） |
| Docs | 良好 | 明确"只记录已发生的，不捏造" | 缺少文档更新的触发时机说明 |
| Ops | 良好 | 每日启动自检协议详细 | DO NOT 约束较少 |
| Sim | 良好 | 逆向工程方法论（从 Demo 目的反推数据），反 4x5 垄断 | 未注册于 settings.json，不可发现 |

#### 2.3.2 Agent 间协作

- **优点**：Agent 间通过"必读文档"建立共享知识基线；GIS Dev↔Tester 的 CRS 交叉验证协议是亮点
- **不足**：Agent 间缺乏结构化的**交接协议**——当 Developer spawn Reviewer 时，如何传递"我改了哪些文件、为什么这样改"的背景信息？目前完全依赖 spawn 时的 prompt 参数，容易遗漏

---

### 2.4 Skills 体系评估

#### 2.4.1 当前状态

项目仅安装了 2 个本地 Skills：
- `code-review-and-quality`：多轴代码审查（来自 addyosmani/agent-skills）
- `web-design-guidelines`：Web 界面指南合规审查

另有 6 个 ZCode 系统级 Skills（用于诊断配置问题）和 9 个文档 Skills（docx/pdf 等）。

#### 2.4.2 SKILLS_INDEX.md（~50 个优选 Skills）

从 464 个市场 Skills 中精选了 ~50 个，按频率分类。但**实际安装/使用的仅 2 个**。这形成了一种"分析瘫痪"风险——知道有很多可用 Skills，但实际工作流只用到极少数。

#### 2.4.3 评价

- **精选质量高**：挑选逻辑清晰（按角色、按场景），说明撰写专业
- **落地率低**：464 个中选了 50 个，50 个中装了 2 个——大量潜在能力未激活
- **缺少触发规则**：SKILLS_INDEX.md 告诉你有哪些 Skills，但没有说明"什么时候应该用哪个"的自动化路由逻辑

---

### 2.5 项目架构评估

#### 2.5.1 总体评价：**架构清晰，分层合理**

7 层架构自下而上：
```
DATA/ (L0-L4 数据) → SCRAPER/ (采集) → core/ (基础设施) → SCRIPT/ (分析管道) → api/ (REST) → ai_qa/ (AI 对话) → frontend/ (MapLibre 前端)
```

#### 2.5.2 架构亮点

| 亮点 | 说明 |
|------|------|
| **Thin Adapter 模式** | API 层仅做 HTTP 适配，核心逻辑在 `core/`，遵循良好实践 |
| **统一入口** | `run_analysis_task()` 单一分析入口，所有前端共享同一逻辑 |
| **Streamlit→MapLibre 迁移** | `apps/` 于 2026-07-18 整层退役，迁移计划完整记录于 `memories/repo/MapLibre GL JS 完整迁移计划.md` |
| **设计 Token 系统** | `design/tokens.json` 作为单一事实源，自动生成 CSS + Python 常量，前端无硬编码颜色 |
| **安全沙箱** | 三层防护（open guard + AST 扫描 + CORS），帧级信任模型区分用户脚本和库导入 |

#### 2.5.3 架构隐患

| 隐患 | 严重度 | 说明 |
|------|--------|------|
| **core/ui_components.py 与 Streamlit 深度耦合** | 中 | 835 行 Streamlit 专用 UI 组件，但 `apps/` 已退役，该文件处于"僵尸半活"状态——代码还在，但实际入口已切换为 frontend/ |
| **layer_registry.py 依赖 st.session_state** | 中 | 与 Streamlit 会话绑定，无法在 FastAPI 或纯脚本环境复用 |
| **geo_registry.py 硬编码 6 个图层** | 低 | 新增数据快照需修改代码，缺少配置文件驱动的图层注册 |
| **db.py 无空间索引** | 低 | `query_by_bbox` 使用简单 BETWEEN，大数据量下性能差；未启用 SpatiaLite |

---

### 2.6 代码质量评估

#### 2.6.1 总体评价：**核心代码质量高，边缘模块有改进空间**

涉及 ~25,000 行 Python + ~16,000 行 JavaScript 的代码库，整体遵循一致的编码风格和注释规范。

#### 2.6.2 逐模块代码质量

| 模块 | 质量评级 | 关键发现 |
|------|---------|---------|
| `core/tracker.py` | A | 决策追踪系统设计精巧，装饰器+上下文管理器+replay 三位一体 |
| `core/spatial_analysis.py` | A | Gi*热点、Moran's I、H3六边形、KDE地形——空间分析工具箱完整 |
| `core/topo_scanner.py` | A | AST+regex 多源扫描，缓存机制，节点/边/孤立检测——工程化程度高 |
| `ai_qa/llm.py` | A | 多 Provider 回退链，流式边界保护，V4 Pro reasoning_content 提取——生产级品质 |
| `api/sandbox.py` | A | 三层安全防护，帧级信任模型，进程树清理——安全设计严密 |
| `core/db.py` | B+ | 结构清晰但 `iterrows()` 逐行插入（性能隐患），NaN 检查仅覆盖 float 类型 |
| `api/geo_routes.py` | B | 功能完整但存在冗余计算（zonal_stats 中 prop_cols 重复构建、rank 中双次 _props_df） |
| `frontend/js/main.js` | B+ | 入口清晰，但 28 个 ES 模块依赖关系为隐式相对路径，无 import map |
| `frontend/js/ai_qa/harness.js` | A- | ReAct Agent 循环实现完整，review/revise 双循环设计优秀 |

#### 2.6.3 跨模块共性问题

| 问题 | 影响面 | 说明 |
|------|--------|------|
| **中文字符串硬编码** | 全项目 | 错误消息、UI 文本、回复模板均硬编码中文，无 i18n 支持。对于纯中文产品这不是问题，但限制了国际化可能性 |
| **Windows 特有路径** | `core/utils.py`, `api/sandbox.py` | `safe_print()` 为解决 Windows GBK 编码而生，`_kill_tree` 使用 `taskkill /F /T`——这两个功能在 Linux/macOS 上不可用 |
| **@track 覆盖率不均** | 多处 | `core/range_selector.py` 注册了 17 个追踪 ID，而 `core/config.py`, `core/db.py`, `core/geo_registry.py`, 全部 `api/` 模块均无追踪。9 个模块在 AGENTS.md 中标记为 ⬜（占位待埋点） |
| **文档与代码同步风险** | 多处 | `tracking-progress.md` 声明所有模块"已完成"追踪，但实际 9 个模块仍是 ⬜；sim-emotion-data agent 的 SOP 中明确提到"修改 `performance_config.TOPIC_TABLE` 必须同步 `frontend/js/panel.js` 的 `TOPIC_POLARITY` + `TOPIC_ORDER`"——这种跨层同步依赖人工记忆 |

---

### 2.7 推进情况评估

#### 2.7.1 完成度估算

| 子系统 | 完成度 | 说明 |
|--------|--------|------|
| 数据管道（L0→L4） | 90% | L0（采集）、L1（治理）、L2（情绪分析）、L3/L4（语义/归因）全部实现；demo 数据模拟完整 |
| Core 核心库 | 85% | 空间分析/坐标转换/地理编码/字段字典/导出等功能齐全；9/22 子模块待追踪埋点 |
| API 层 | 75% | GIS 工具箱 12 端点 + 安全沙箱 + AI QA 路由 + 拓扑路由已就绪；缺认证/限流/日志中间件 |
| AI QA 子系统 | 70% | 4 层 Harness + 16 技能模板 + ReAct Agent 循环已实现；知识闭环（wisdom→episodes→consolidation）仍在初期 |
| Frontend 前端 | 80% | 28 个 JS 模块覆盖了地图/图层面板/导入/分析工具箱/AI Copilot/时间轴；缺移动端适配 |
| 测试 | 65% | 182 个测试覆盖核心模块，但 AI QA 前端（harness.js/tools.js）无单元测试，前端组件无测试 |
| 文档 | 80% | PRD/Spec/架构/ADR/开发日志齐全；部分文档存在过时引用（如 `apps/` 已退役但仍出现在某些架构图中） |

#### 2.7.2 最新进展（2026-07-18）

从 `session-handoff.md` 和 `todo.md` 可知：
- 修复了天地图 basemap 404 问题
- 完善了 browser E2E 框架 + compare 中文地名解析（Phase 5）
- 清理了 5 个 stale/env 测试失败（pytest 全绿）
- 当前阶段：测试债务清理接近尾声，准备进入项目全局复盘

---

### 2.8 调用次数消耗分析（针对按次计费模型）

#### 2.8.1 当前调用模式

在一次典型的"实现 XX 功能"流程中：

```
用户输入 → Claude Code 主线程（1 次）
  → spawn Developer Agent（1 次）
  → Developer 完成后返回主线程（1 次）
  → spawn Reviewer Agent（1 次）
  → Reviewer 完成后返回主线程（1 次）
  → spawn Tester Agent（1 次）
  → Tester 完成后返回主线程（1 次）
  → 可能 spawn Docs Agent（1 次）
  → 汇总汇报给用户（1 次）
────────────────────────────────
最小调用：3 次（轻量 SOP）
标准调用：7 次（标准 SOP）
严格调用：9+ 次（严格 SOP + 复审）
```

#### 2.8.2 消耗热点

| 热点 | 每次消耗 | 周频率估算 | 周消耗 |
|------|---------|-----------|--------|
| Agent spawn（标准 SOP） | 5-7 次调用/任务 | 3-5 个任务 | 15-35 次 |
| EMC AI Copilot 对话 | 1 次/轮（含大 MANIFESTO） | 10-20 轮 | 10-20 次 |
| /verify 门禁 | 1 次调用 | 每次提交前 | 3-5 次 |
| /garden 维护 | 1 次调用 | 1-2 次/周 | 1-2 次 |
| 跨机同步（早晚各一次） | 2 次调用 | 5 天 | 10 次 |
| **估算周消耗** | | | **40-70 次** |

> **风险评估**：如果每周额度为 200 次，当前消耗占 20-35%，尚可接受。但如果额度为 100 次，占比 40-70%，需要优化。建议向 Claude Code 确认你的模型实际额度。

#### 2.8.3 AI QA 子系统的 Token 消耗

MANIFESTO（~4,000 字）+ paradigm 知识表 + wisdom + industry KB ≈ 每次对话注入 **8,000-12,000 tokens** 的上下文。按 V4 Pro 的定价（输出比输入贵），这部分的成本主要体现在输入 token 上。

---

## 第三部分：优化建议

### 🔴 高优先级：调用次数优化（针对按次计费）

#### 建议 1：引入批量变更 + 集中审查模式

**问题**：当前流程是"改一个功能 → spawn Reviewer → spawn Tester"，每个功能独立走完整流程。

**优化方案**：
- 将多个小型、独立的功能变更合并为一个变更批次
- 收集 3-5 个小变更后，一次性 spawn Reviewer 进行全面审查
- Tester 也只运行一次全量测试

**具体操作**：
```
在 CLAUDE.md 中增加规则：
"当涉及多个小型独立变更（如单文件修复、文案调整）时，
分批收集，每批次 3-5 个变更后统一走一次标准 SOP，
而不是每个变更独立走 SOP。"
```

**预期节省**：每个批次节省 4-8 次 Agent spawn 调用
**风险**：批次过大时 Review 容易遗漏，建议批次上限为 5 个变更

#### 建议 2：将 Reviewer 与 Tester 合并为"QA Agent"

**问题**：当前 Reviewer（只读审查）和 Tester（运行测试）是两个独立 Agent，需要两次 spawn。

**优化方案**：
- 创建新的 `qa.agent.md`，合并 Reviewer + Tester 的职责
- QA Agent 先做静态审查，再运行测试，一次性输出"审查+测试"综合报告

**具体操作**：
```
1. 创建 .claude/agents/qa.agent.md
2. 工具权限：read + execute（保留 Reviewer 的只读 + Tester 的执行）
3. 流程：先审查代码 → 再运行 pytest → 输出综合 PASS/NEEDS_CHANGE 报告
4. 在 AGENTS.md 中将 Standard SOP 从 "Developer → Reviewer → Tester" 
   改为 "Developer → QA"
```

**预期节省**：每次标准 SOP 节省 1 次 Agent spawn（从 5 次降为 4 次）
**风险**：合并后单个 Agent 定义更长，QA Agent 的 prompt 需要精心设计避免角色冲突

#### 建议 3：用本地脚本替代部分 Agent spawn

**问题**：`/verify` 命令和 Tester Agent 的测试运行都可以用**本地 bash 脚本**完成，不需要消耗模型调用次数。

**优化方案**：
- 创建 `.githooks/pre-commit` 的增强版脚本（`scripts/verify.sh`），包含：
  - `python -m pytest tests/ -q`（测试）
  - `python -c "from core.tracker import ..."`（追踪合规）
  - `grep -r '[ERR]' .trace/trace.log`（trace 错误）
- 在提交前手动运行脚本，而不是 spawn Tester Agent

**具体操作**：
```
1. 创建 scripts/verify.sh（Windows 用 .bat）
2. 在 CLAUDE.md 中增加规则：
   "提交前先运行 scripts/verify.sh 本地验证，
   仅当验证失败需要 AI 协助调试时才 spawn Tester Agent"
```

**预期节省**：每次提交前节省 1 次 Agent spawn
**风险**：脚本维护需要与代码同步更新（例如 tracker registry 格式变更时）

#### 建议 4：减少 EMC AI Copilot 的 MANIFESTO 注入

**问题**：每次 EMC 对话都注入完整的 MANIFESTO（~4,000 字），但用户可能只是问一个简单的 GIS 操作问题。

**优化方案**：
- 将 MANIFESTO 分层：`MANIFESTO_CORE`（核心规则，~500 字，每次注入）+ `MANIFESTO_FULL`（完整版，仅在需要时注入）
- 根据用户问题类型动态选择注入层级

**具体操作**：
- 在 `ai_qa/prompts.py` 的 `build_agent_prompt()` 中增加逻辑：
  - 简单 GIS 操作（如"这个区域有多少点"）→ 注入 `MANIFESTO_CORE`
  - 需要领域知识的复杂问题（如"二马路片区情绪为什么偏负面"）→ 注入 `MANIFESTO_FULL`
- 用关键词匹配快速判断问题类型

**预期节省**：简单问题每次节省 ~7,000 tokens 输入
**风险**：分类错误可能导致 AI 回答偏离领域规范

---

### 🟡 中优先级：架构与代码质量改进

#### 建议 5：补全 9 个模块的追踪埋点

**问题**：`core/config.py`, `core/db.py`, `core/geo_registry.py`, 全部 `api/` 模块等 9 个模块缺少 `@track()` 装饰器。在 AGENTS.md 中标记为 ⬜（占位待埋点），但 `tracking-progress.md` 声明"所有模块已完成"——文档与代码不一致。

**优化方案**：
- 优先追踪关键 I/O 路径：`db.py` 的 insert/query、`api/` 的所有 HTTP 端点
- 对纯常量/配置模块（`config.py`, `landuse_codes_2023.py`）可明确标注"无需追踪"而非长期占位

**具体操作**：
```
1. 分配 MOD_DB, MOD_API 等新模块 ID
2. 对 db.py 的 insert_points, query_by_bbox, export_csv 加 @track
3. 对 api/geo_routes.py 的每个端点函数加 @track
4. 在 core/tracker.py 注册表登记新 ID
5. 更新 tracking-progress.md 为实际状态
```

**预期收益**：提升调试效率，O(1) 跳转到出错位置

#### 建议 6：消除 `api/geo_routes.py` 中的冗余计算

**问题**：具体表现为：
- `zonal_stats`（行 321-325）：`prop_cols` 构建了两次，第一次被第二次覆盖
- `rank`（行 384-385）：对同一数据调用了两次 `_props_df()`
- `nearest`（行 483-485）：`dist_col` 变量赋值后未使用

**优化方案**：消除重复计算，合并冗余变量。

**具体操作**：这是纯代码清理，Developer Agent 可直接执行。

#### 建议 7：优化 `core/db.py` 的批量插入性能

**问题**：`insert_points()` 使用 `for _, row in df.iterrows()` 逐行插入。

**优化方案**：使用 `df.to_sql()` 或 `executemany()` 批量插入。

**具体操作**：
```python
# 替换 iterrows() 为批量操作
data = [tuple(row) for row in df.itertuples(index=False)]
cursor.executemany("INSERT INTO points (...) VALUES (...)", data)
```
配合当前的 5000 行批次分割，可以大幅提升插入性能。

---

### 🟢 低优先级：长期改进

#### 建议 8：注册 sim-emotion-data Agent

**问题**：该 Agent 存在但未在 `settings.json` 中注册，导致不可被自动发现。

**具体操作**：在 `.claude/settings.json` 的 agents 列表中添加 `"sim-emotion-data"`。

#### 建议 9：为关键前端模块引入 JSDoc 类型注释

**问题**：28 个 JS 模块无类型检查，拼写错误（如变量名）在运行时才暴露。

**优化方案**：对核心模块（`state.js`, `import.js`, `harness.js`）添加 JSDoc 类型注释，配合 VS Code 的 TypeScript 检查获得编译时类型安全。**不引入 npm/TypeScript 编译器**，保持零构建步骤。

#### 建议 10：补充前端 E2E 测试

**问题**：目前仅 `tests/browser/test_compare_regions.py` 一个 E2E 测试。前端 28 个 JS 模块中，`import.js`（文件导入）、`heatmap-tool.js`（热力分析）、`grid-tool.js`（网格聚合）等核心交互无 E2E 覆盖。

**优化方案**：
- 为导入流程（CSV/GeoJSON/Shapefile）增加 Playwright E2E
- 为热力分析三步向导增加 E2E
- 优先覆盖"用户最常走的路径"

---

## 第四部分：讨论点

### 讨论 1：前端"零构建" vs 引入 Vite

#### 现状
前端使用**零构建步骤**架构：28 个 ES Module 直接通过 `<script type="module">` 加载，11 个 CDN 依赖，`serve.py` 用 `?v=<mtime>` 做缓存破坏。

#### 优点（当前方案）
- 无学习成本，修改即生效
- 部署简单（静态文件服务）
- 开发迭代快

#### 缺点（当前方案）
- 无 tree-shaking，全部代码发送到浏览器（~16K 行 JS）
- 无类型检查，运行时才发现错误
- CDN 依赖有可用性风险（jsdelivr/unpkg 被墙或宕机）
- 无法使用 npm 生态的 lint/format 工具

#### Vite 方案
- **优点**：ESBuild 预处理 → tree-shaking → 代码分割 → HMR → TypeScript 支持
- **缺点**：引入 `package.json` + `node_modules` + 构建步骤，增加项目复杂度
- **折中**：保留当前零构建作为开发模式，增加可选的 `vite build` 用于生产部署

#### 我的看法
对于**单人项目 + 快速原型迭代**阶段，当前零构建方案是合理的。但考虑到：
1. 项目已有 16K 行 JS（且还在增长）
2. 前端复杂度已超过"简单原型"的阶段
3. CDN 依赖（特别是 unpkg）在国内网络环境下不够稳定

**建议在两阶段演进**：
- **Phase 1（当前）**：保留零构建，但将 CDN 依赖下载到 `vendor/` 目录本地化
- **Phase 2（未来）**：当 JS 代码超过 25K 行时，引入 Vite 做构建优化

---

### 讨论 2：Agent 编排模式的选择

#### 现状
Claude Code 主线程作为 PM，"自动判断"何时 spawn 哪个 Agent、走哪条 SOP。

#### 可选模式对比

| 模式 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A. 全自动（当前）** | 主线程模型判断 | 灵活，适应各种情况 | 不可预测，可能误判 |
| **B. 规则路由** | 基于文件数量/类型硬编码路由规则 | 可预测，批量变更自动走严格 SOP | 僵化，无法应对复杂情况 |
| **C. 用户确认** | 关键决策前询问用户"是否走标准 SOP？" | 用户可控 | 打断工作流，增加交互轮次 |
| **D. 混合（推荐）** | 模型判断 + 结构性安全网 | 兼顾灵活性和安全性 | 实现复杂度略高 |

#### 混合模式的具体实现

在 `AGENTS.md` 或 CLAUDE.md 中增加结构性安全网规则：

```
自动路由规则：
1. 如果变更涉及以下文件 → 强制执行 Standard SOP（不依赖模型判断）：
   - core/tracker.py, SCRIPT/data_governance.py（核心管道）
   - 任何 __init__.py（模块导出变更）
   - api/routes.py（API 端点变更）
2. 如果变更仅涉及以下文件类型 → 允许 Lightweight SOP：
   - *.md, *.css, *.json
   - 单文件内的注释/文档字符串修改
3. 其他情况 → 模型自主判断
```

这样既保留了灵活性，又对关键路径提供了硬性保证。

---

### 讨论 3：决策追踪系统的 ROI 评估

#### 现状
- 55 个追踪 ID 已注册
- 每个公开函数必须 `@track()`，每个 >5 行的分支必须 `TrackContext`
- 9 个模块尚待埋点（全部完成后预计 80+ 个 ID）
- Hook 层有 trace 增量摘要机制

#### 正面观点
- O(1) 跳转调试是真实存在的效率提升
- Trace 日志提供了"代码级"的执行路径可视化
- 在 LLM 辅助编程场景下，有了 trace ID，AI 更容易定位问题

#### 反面观点
- 维护成本高：每个新函数都要分配 ID，每次重构要更新注册表
- 编号连续性要求（铁律 10）增加了协作摩擦
- 大部分追踪 ID 可能永远不被触发（覆盖率 ≠ 利用率）
- 如果人手动 debug，全局搜索 `grep` 的速度也很快

#### 我的看法

追踪系统在**理论**上很好，但需要对**实际利用率**做评估。建议在下次复盘时做以下实验：

1. 统计过去 30 天 `.trace/trace.log` 中实际触发了多少个不同的追踪 ID
2. 统计过去 30 天通过 trace ID 定位的 bug 数量
3. 计算"维护追踪点的总时间" vs "通过追踪节省的调试时间"

如果 ROI 为负，考虑**简化**：
- 仅对 I/O 操作、except 块、数据管道步骤保持追踪
- 取消"每个公开函数必须追踪"的要求
- 取消"编号连续性"要求，改用模块内自增 ID

---

### 讨论 4：MCP 策略——"智谱优先"的合理性

#### 现状
`mcp-strategy.md` 规定：同类功能优先智谱（`zai`/`web-search-prime`/`web-reader`/`zread`），连不上再退备选。

#### 智谱优先的理由
- 国内访问速度更快
- 中文支持更好
- 统一的 API 生态

#### 潜在问题
- **Vendor lock-in**：过度依赖单一供应商
- **SLA 风险**：智谱宕机 → 所有 MCP 功能同时失效（web-search + web-read + zread 同时不可用）
- **与 DeepSeek 模型不匹配**：你用的是 DeepSeek V4 作为主模型，Agent 的角色定义中应优先与 DeepSeek 生态匹配的工具

#### 建议
- 保持智谱优先的策略（国内场景确实更好）
- 但为 **web-search** 增加第二个独立备选（如 Bing API 或 SerpAPI），不与智谱共享命运
- 将 `vision-bridge` 从"智谱备选"提升为"独立通道"——视觉分析是关键功能，应有独立保底方案

---

### 讨论 5：Streamlit 退役后的遗留处理

#### 现状
`apps/` 于 2026-07-18 标记退役，但以下文件仍引用 Streamlit：
- `core/ui_components.py`（835 行，Streamlit 专用 UI）
- `core/layer_registry.py`（依赖 `st.session_state`）
- `.streamlit/config.toml`（Streamlit 主题配置）
- `.claude/memory/_archived/` 中 10 个 Streamlit 时代的内存文件

#### 两种处理策略

**策略 A：彻底清理**
- 删除 `core/ui_components.py` 和 `core/layer_registry.py`
- 删除 `.streamlit/` 目录
- 从 `requirements.txt` 移除 `streamlit`
- **风险**：如果有其他模块间接依赖 Streamlit 组件，会导致 import 错误

**策略 B：保留标记**
- 在文件头部添加 `# DEPRECATED: apps/ retired 2026-07-18, kept for reference only`
- 暂不删除，等待确认无依赖后清理
- **风险**：新开发者可能被误导使用已退役的组件

#### 建议
- 先用 `grep` 检测对 `ui_components` 和 `layer_registry` 的引用
- 如果零引用 → 走策略 A 彻底清理
- 如果有引用 → 评估引用方的迁移成本，制定迁移计划后清理

---

### 讨论 6：另一种可能的架构思路——"微服务化"

#### 当前架构
单体 Python 项目，所有模块在同一进程中。API 层通过 uvicorn 启动。

#### 替代方案：轻量微服务

```
[Scraper Service] → Kafka/Redis → [Governance Service] → [Analysis Service] → [API Gateway] → [Frontend]
```

#### 对比

| 维度 | 单体（当前） | 微服务 |
|------|------------|--------|
| 开发复杂度 | 低 | 高 |
| 部署复杂度 | 低（一个进程） | 高（多个进程 + 消息队列）|
| 扩展性 | 差 | 好 |
| 调用次数 | 少（内部函数调用不计） | 多（每个服务间调用 = 1 次 LLM 调用） |
| 适用场景 | 单机、小数据 | 分布式、大数据 |

#### 我的看法

**当前阶段不建议微服务化**。理由：
1. 你是一个人团队，微服务的运维成本远高于收益
2. 数据量级尚小（demo 数据 ~17,000 点），单体架构完全够用
3. 微服务间调用会**大幅增加 LLM 调用次数**（每次跨服务调用都可能触发一次 Agent 分析），与你的计费模型冲突

等到数据量突破 10 万点、用户需要实时分析时，再考虑拆分。

---

## 总结

### 项目健康度评分

| 维度 | 评分 | 趋势 |
|------|------|------|
| 架构设计 | 8.5/10 | → 稳定 |
| 代码质量 | 7.5/10 | ↑ 改善中 |
| 测试覆盖 | 6.5/10 | ↑ 改善中 |
| Harness 工程 | 9/10 | → 稳定 |
| 文档完整度 | 8/10 | → 稳定 |
| 调用效率 | 6/10 | ↓ 需关注 |
| **综合** | **7.6/10** | |

### 最关键的 3 个行动项

1. **调用次数优化**（高优先级）：合并 Reviewer + Tester → QA Agent；引入批量变更模式
2. **追踪系统复盘**（中优先级）：评估实际 ROI，决定是继续推进还是简化
3. **前端 CDN 本地化**（中优先级）：将 unpkg/jsdelivr 依赖下载到 `vendor/`，提升国内访问稳定性

---

> **给 Claude Code 的后续指令**：
> 请阅读本报告，逐条评估优化建议的可行性，对采纳的建议制定实施计划。完成后我会用 DeepSeek 再次扫描验证改进效果，形成闭环对比。
>
> **双模型闭环**：
> ```
> 第一次扫描（DeepSeek 本次）→ 发现问题 → Claude Code 执行优化
> → DeepSeek 第二次扫描 → 对比验证 → 反思改进
> ```
