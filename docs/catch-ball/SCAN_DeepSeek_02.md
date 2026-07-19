# DeepSeek 深度扫描评估报告（第 02 轮）

> **扫描模型**：DeepSeek V4 Pro（24ea04bd-fb2a-46c6-8d46-558481503334）
> **扫描时间**：2026-07-19
> **CB 轮次**：02
> **项目**：emotion_map — 城市情绪地图平台
> **开发模型**：Claude Code（主）+ DeepSeek V4（评审）
> **扫描方法**：3 个 Explore Agent 并行深度刺探 + 主线程逐模块核实，覆盖 ~200 个文件，遍历全部核心模块

---

## 第〇部分：CB-01 回顾与执行评估

### 0.1 CB-01 建议执行状态表

CB-01 提出 10 条优化建议（4 高 / 3 中 / 3 低）。CB-01→CB-02 期间（commits 5.132–5.135），项目方逐条评估并执行。以下为第三方核实结果：

| # | CB-01 建议 | 优先级 | 采纳状态 | 执行证据 | 第三方评价 |
|---|-----------|--------|---------|---------|-----------|
| 1 | 引入批量变更+集中审查模式 | 🔴 高 | ❌ **declined** | 项目方称"前提不成立——不派 subagent，主线程直接干" | **尊重项目方工作流**。CB-01 的调用次数分析基于 AGENTS.md 理论 SOP 模型，与实际工作流（主线程直接执行）不一致。declined 理由成立 |
| 2 | Reviewer+Tester 合并为 QA Agent | 🔴 高 | ❌ **declined** | 同上——不派 subagent，合并不产生实际节省 | **理由成立**。如果 Agent 系统是概念框架而非运行时机制，合并无意义 |
| 3 | 用本地脚本替代部分 Agent spawn | 🔴 高 | ❌ **declined** | 同上——/verify 已可直接运行 pytest | **部分采纳**。项目方实际已在使用 pytest 本地验证，只是未显式标记为"采纳" |
| 4 | EMC MANIFESTO 分层减 token | 🔴 高 | ❌ **declined** | 撞承重红线——diagnose prompt 永不动保 Flash eval | **尊重承重红线**。CB-01 未意识到 MANIFESTO 与 diagnose 的耦合关系，建议失准 |
| 5 | 补全 9 模块追踪埋点 | 🟡 中 | ⬜ **未处理** | 9 个⬜模块仍为⬜。`db.py` 已退役，`core/ui_components.py`/`layer_registry.py`/`map_engine.py` 已退役，实际待埋点降至 6 模块 | **建议重估**。退役减少了待埋点规模。剩余 6 个⬜中，`geo_registry.py` 最优先（6 个公开函数零追踪） |
| 6 | 消除 api/geo_routes.py 冗余计算 | 🟡 中 | ✅ **已修复** | zonal_stats/rank/nearest 三处清理，零行为变化。zonal_stats latent bug→wontfix（无活消费方）验证充分 | **核实通过**。代码清理完整，wontfix 决策论据扎实（深挖了 3 条消费路径均不依赖死列） |
| 7 | 优化 core/db.py 批量插入 | 🟡 中 | ❌ **declined** | `db.py` 全闲置→退役。且 `insert_points` 早已用 executemany（CB-01 描述失准） | **CB-01 建议失准**。db.py 是死代码，优化它毫无意义。declined + 退役是正确的处理 |
| 8 | 注册 sim-emotion-data Agent | 🟢 低 | ✅ **已修复** | settings.json agents 列表已含 `sim-emotion-data`（8→9）。但 AGENTS.md 表仍称"8 Agent" | **注册完成，文档漂移**。settings.json 正确，AGENTS.md 表未同步更新 |
| 9 | 前端 JSDoc 类型注释 | 🟢 低 | ⬜ **未处理** | 28 个 JS 模块无 JSDoc | **未推进**。CB-01→CB-02 期间优先级低于退役清理 |
| 10 | 补充前端 E2E 测试 | 🟢 低 | ⬜ **未处理** | 仍仅 1 个 E2E 测试（且 browser 环境挂）。C6 计划 4 例仅完成 1 例 | **阻塞于环境问题**。非意愿性延迟 |

**执行统计**：10 条建议中，✅ 2 条完成 / ❌ 4 条拒绝（其中 2 条因 CB-01 描述失准或撞红线）/ ⬜ 3 条待处理 / 1 条部分。有效执行率（完成/有效拒绝）= 60%。

### 0.2 对 CB-01 反评价的第三方审核

CB-01 反评价使用 agree/disagree/partial 三分法。以下为第三方逐条审核：

#### agree（4 条）—— 全部核实通过

| agree 项 | CB-01 发现 | 核实结果 |
|----------|-----------|---------|
| Streamlit 僵尸 | ui_components/layer_registry/map_engine 零活引用 | ✅ 3 个文件 + .streamlit/config.toml 已删除（`core/__init__.py` 已清引用）。项目方还额外发现了 map_engine（pydeck 僵尸，CB-01 未点名） |
| geo_routes 冗余 | zonal_stats/rank/nearest 三处 | ✅ 修复生效。项目方深挖出了 CB-01 未发现的 zonal_stats latent bug，并正确判断 wontfix |
| sim agent 未注册 | settings.json 缺 sim-emotion-data | ✅ 已注册（第 9 个 agent） |
| db.py/Skills/前端无单测/微服务否决 | 多项合理 | ✅ db.py 已退役。其余为观点认同，非可执行项 |

#### disagree（4 条）—— 逐条评估

| disagree 项 | CB-01 原建议 | 项目方反驳 | 第三方评估 |
|-------------|-------------|-----------|-----------|
| 数据管道 90% | 完成度估算偏高 | "L1 未实跑；L3/L4 ⬜预留。真实 ~75%。L0 走购买，sim 非风险" | **部分认可反驳**。CB-01 的 90% 确实偏高（将"接口预留"计为"已实现"）。但 75% 也偏保守——L2 分析、SIM 生成、EMC L4 归因链均已闭环。**建议折中 ~80%** |
| 调用次数=头号高优 | 4 条高优建议均围绕调用次数 | "前提不成立。不派 subagent，主线程直接干" | **反驳成立**。CB-01 基于 AGENTS.md 的 SOP 理论模型计算 spawn 次数，但实际工作流不走 Agent spawn。这暴露了 AGENTS.md 描述与实际工作流的 gap——文档写了一套自动编排体系，但实际不用 |
| MANIFESTO 分层 | 按问题复杂度分层注入 | "撞 diagnose 永不动承重红线" | **反驳成立**。CB-01 未察觉 MANIFESTO 与 Flash eval 的路由耦合。MANIFESTO 分层会破坏 diagnose prompt 的完整性和一致性 |
| MCP 应与 DeepSeek 匹配 | 工具链应与主 LLM 对齐 | "provider-neutral 错标尺。智谱优先因国内视觉/搜索质量" | **反驳部分成立**。工具选择应以功能质量为准，非厂商一致性。但 vendor SLA 单点风险确实存在（CB-01 讨论 4 已指出） |

#### partial（1 条）

| partial 项 | CB-01 建议 | 项目方回应 | 第三方评估 |
|------------|-----------|-----------|----------|
| 追踪 ROI 测量 | 统计 30 天 trace.log 触发率 | "同意做实验，不同意预设简化" | **平衡立场**。实验建议合理，但"不同意简化"也合理——追踪系统投产仅 2 个月，尚未到评估 ROI 的成熟时机 |

#### CB-01 扫描遗漏（项目方补充，第三方确认）

| 遗漏项 | 第三方确认 |
|--------|-----------|
| §0 任务树漂移 3 周 | ✅ 已修复（CB-01 Tier 1，§0 主干+topology+AI 7 月刷新） |
| retired.md 缺失 | ✅ 已新建（5 个退役文件留痕） |
| Toolbox 多维归因 vs EMC deep_attribution 重叠 | ⬜ 仍开放——架构层面的功能重叠未显式解决 |
| `?e2e=1` seam 去生产化 | ✅ 已修复（main.js 零 test 代码，独立 e2e-seam.js，条件 dynamic-import） |

### 0.3 CB-01→CB-02 关键变化摘要

| 维度 | 变化 |
|------|------|
| **退役** | 5 个文件删除（ui_components.py, layer_registry.py, map_engine.py, db.py, .streamlit/config.toml），-1,735 行 |
| **新增** | `frontend/js/e2e-seam.js`（40 行，test 隔离），`docs/retired.md`（退役台账），`docs/cb-journal.md`（CB 轨迹），`docs/SCAN_DeepSeek.md`（CB-01 报告） |
| **修复** | geo_routes.py 三处冗余清理；sim agent 注册 settings.json；tracking-progress 漂移修复；`?e2e=1` 去生产化 |
| **文档刷新** | §0 任务树主干+topology+AI 7 月更新；revision-log §5 追加 5.132–5.135 |
| **未变** | 测试数量 182（零增长）；前端 JS 零单测；9 个⬜追踪模块→6 个（退役减 3）；E2E browser 仍挂 |

---

## 第一部分：扫描内容

### 1.1 扫描范围一览

| 维度 | 扫描对象 | 文件数 | 代码量 | 关键发现 |
|------|---------|--------|--------|---------|
| **顶层配置** | AGENTS.md, CLAUDE.md, MEMORY.md, README.md, requirements.txt, pytest.ini, .mcp.json, .gitignore, .claudeignore, .env.example | 12 | ~900 行 | AGENTS.md 声称 8 Agent 但实际 9；requirements.txt 残留 streamlit+pydeck 僵尸依赖 |
| **Agent/Harness** | `.claude/agents/`（9 活跃+3 归档），`.claude/hooks/`（5），`.claude/commands/`（6），`settings.json` | 26 | ~1,450 行 | sim agent 已注册；5 Hook 全功能正常；AGENTS.md 与 settings.json agent 数量不一致 |
| **Core 核心库** | `tracker.py`, `spatial_analysis.py`, `topo_scanner.py`, `field_dictionary.py`, `geocode.py`, `place_layer.py`, `range_selector.py`, `coord_transform.py`, `buffer_analysis.py`, `geo_registry.py`, `data_loader.py`, `export.py`, `config.py`, `utils.py`, `__init__.py` | 15 | ~5,035 行 | 4 个退役文件已删除；126 个注册追踪 ID；topo_scanner 新增（697 行，A 级质量）；geo_registry 零 @track |
| **SCRIPT 分析管道** | `emotion_analysis_v1.py`, `data_governance.py`, `relevance_filter.py`, `run_analysis.py`, `sim_performance_data.py`, `sim_ermawu_l3l4.py`, `multimodal_analysis.py`, `generate_test_data.py`, `generate_l1_mock.py`, 等 16 文件 | 16 | ~9,274 行 | L0→L4 管道完整；generate_test_data.py (1,232 行) 与 generate_l1_mock.py (522 行) 疑似功能重复 |
| **API 层** | `main.py`, `routes.py`, `geo_routes.py`, `sandbox.py`, `run_routes.py`, `aiqa_routes.py`, `topo_routes.py`, `schemas.py`, `__init__.py` | 9 | ~2,047 行 | geo_routes 三处冗余已清理；sandbox 三层安全模型完善；topo_routes 新（35 行 thin adapter） |
| **AI QA 子系统** | `manifesto.py`, `paradigm.py`, `prompts.py`, `llm.py`, `review.py`, `wisdom.py`, `router.py`, `episode.py`, `consolidate.py`, `schemas.py`, `landuse_codes_2023.py` + `industry_kb/`（4 领域） | 16 | ~2,781 行 | LLM 三 Provider 回退链；wisdom 9 条；industry_kb 621 行跨 4 领域；Flash eval 95% 命中率 |
| **Frontend 前端** | `index.html` (884 行), `serve.py` (325 行), `topology.html` (84 行), `js/` (31 模块), `css/` (16 文件), `js/ai_qa/` (6 文件), `vendor/` (6 库) | ~64 | JS 16,271 行 + CSS 5,305 行 | e2e seam 正确分离；topology 3D 可视化成熟；panel.js (2,098 行) 过大；零 JS 单测 |
| **Tests 测试** | `conftest.py`, 14 个 test_*.py + `eval_template_flash.py`, `browser/` | 17 | ~2,396 行 | 182 测试函数（零增长）；E2E browser 环境挂（非代码问题）；前端零测试 |
| **Docs 文档** | 27 篇 .md + memories/repo/ | ~30 | ~8,565 行 | CB-01 新增 4 篇文档；prd/spec/architecture 含 Streamlit 过时内容；dev-notes 3 周未更新；trace-digest 空 |
| **数据层** | DATA/ (66 文件) + SCRAPER/ (12 文件, 1,875 行) | ~78 | ~1,875 行 | 4 个 Spider 均为参考实现；DATA/ 约 15-20MB |

### 1.2 扫描深度

- **L1（全量阅读）**：AGENTS.md, CLAUDE.md, 所有 Agent 定义, 所有 Hook/Command, `core/tracker.py`, `core/config.py`, `core/topo_scanner.py`, `ai_qa/llm.py`, `ai_qa/manifesto.py`, `frontend/serve.py`, `frontend/js/main.js`, `frontend/js/e2e-seam.js`
- **L2（关键函数+结构）**：所有 Core 模块, 所有 API 路由, 所有 AI QA 核心, Frontend 主要 JS 模块
- **L3（概览）**：SCRIPT 脚本, 测试文件, 文档, Scrapy 爬虫

### 1.3 总代码量

| 语言 | 行数 | vs CB-01 |
|------|------|----------|
| Python（后端） | ~21,012 | -1,735（退役） |
| JavaScript（前端） | 16,271 | +40（e2e-seam.js） |
| CSS | 5,305 | 持平 |
| Markdown（文档） | ~8,565 | +700（CB-01 新增文档） |
| **合计** | **~51,153** | **-995** |

---

## 第二部分：扫描结果/评价

### 2.1 Vibe Coding 策略评估

#### 2.1.1 总体评价：**良好，文档与实际存在 gap**  → 趋势持平

CB-01 提出的核心问题仍然存在：自动编排依赖模型判断、Agent 调用链深度风险、文档膨胀。但 CB-01→CB-02 期间暴露了一个新问题：

**AGENTS.md 与实际工作流的 gap**。AGENTS.md 描述了一套完善的 8 Agent + 三管线自动路由 + SOP 风险分级体系，但项目方在 CB-01 反评价中明确指出"不派 subagent，主线程直接干"。这意味着：
- AGENTS.md 是**概念框架**而非**运行时机制**
- 8 个 Agent 定义文件是**行为参考**而非**独立执行单元**
- CB-01 的"调用次数优化"建议全部基于错误的运行时假设

**这不是 AGENTS.md 的问题——作为新人 onboarding 和 AI 行为约束文档，它仍然出色。** 但文档应明确标注"概念框架"vs"运行时实际"的区分，避免第三方（如 CB-01）基于文档做错误推断。

### 2.2 Harness 框架评估

#### 2.2.1 总体评价：**设计精良，维持高水准** → 趋势持平

5 个 Hook + 6 个 Command 体系未变，工程质量保持 CB-01 评价水平。补充观察：

- **on_session_end trace digest**：代码存在且逻辑正确，但 `docs/trace-digest.md` 实际为空（仅 9 行 header）。这意味着 Hook 从未触发或 trace.log 中无 ERR/WARN——前者是 bug，后者说明项目运行健康
- **on_pre_edit_lint emoji guard**：仍仅覆盖 `.py` 文件。16,271 行 JS 代码无 emoji 拦截保护

### 2.3 Agent 体系评估

#### 2.3.1 总体评价：**注册修复完成，文档漂移未修** ↑ 微改善

| 变化 | 详情 |
|------|------|
| ✅ sim agent 已注册 | settings.json 9 agents（CB-01 时 8） |
| ⚠️ AGENTS.md 未同步 | 标题仍称"8 Agent"，表格仍列 8 个 |
| ⚠️ Bash(streamlit *) 残留 | settings.json 权限含已退役的 streamlit |

### 2.4 Skills 体系评估

#### 2.4.1 总体评价：**无变化** → 趋势持平

仍为 2 个本地 Skills + ~50 个 INDEX 精选。CB-01 指出的"落地率低（2/50）"问题未变。

### 2.5 项目架构评估

#### 2.5.1 总体评价：**更干净，但仍有遗留** ↑ 微改善

**改善**：
- 5 个 CB-01 指出的架构隐患已清除 4 个：
  - ✅ `core/ui_components.py`（Streamlit 僵尸）→ 已删除
  - ✅ `layer_registry.py`（st.session_state 依赖）→ 已删除
  - ✅ `core/map_engine.py`（pydeck 僵尸）→ 已删除
  - ✅ `core/db.py`（无空间索引）→ 已退役
  - ⬜ `geo_registry.py`（硬编码图层）→ 仍为硬编码

**新发现**：
- `core/range_selector.py:20` 使用小写 `data/boundaries` 路径，与项目大写 `DATA/` 惯例不一致。Windows NTFS 不区分大小写所以未暴露，但 Linux/macOS 部署会直接 break
- `core/config.py` 定义 `BOUNDARY_SHP` 指向 `DATA/boundaries/规划范围/`，而 `range_selector.py` 自有 `_BOUNDARIES_DIR`。两套边界路径解析逻辑未统一

**topo_scanner 新增评估**：697 行 AST+regex 多源扫描器，mtime 缓存，节点/边/孤立检测，架构设计优秀。严格遵循"core 逻辑 + api thin adapter"模式（`api/topo_routes.py` 仅 35 行）。

### 2.6 代码质量评估

#### 2.6.1 总体评价：**核心保持 A 级，边缘问题从 CB-01 转移** → 趋势持平

**CB-01 问题修复**：
- `api/geo_routes.py`：B → A（三处冗余已清理 + zonal_stats latent bug wontfix 注释完善）
- `core/db.py`：退役，不再评估

**新发现或持续问题**：

| 问题 | 文件 | 严重度 | 说明 |
|------|------|--------|------|
| **路径大小写不一致** | `range_selector.py:20` | 🔴 高 | `os.path.join(_PROJECT_ROOT, 'data', 'boundaries')` 小写 `data`，全项目其他地方用 `DATA` |
| **geo_registry 零追踪** | `geo_registry.py` | 🟡 中 | 6 个公开函数无 `@track`，是唯一无追踪覆盖的 core 模块 |
| **Sim 代码疑似重复** | `generate_test_data.py` (1,232 行) + `generate_l1_mock.py` (522 行) | 🟡 中 | 两者功能与 `sim_performance_data.py` (729 行) 重叠；`generate_l1_mock.py` 自标"superseded" |
| **panel.js 过大** | `frontend/js/panel.js` (2,098 行) | 🟡 中 | 单文件承担 overview + table + timeline + polarity deep-read 四项职责 |
| **硬编码城市** | `relevance_filter.py`, `geocode.py` | 🟢 低 | `YICHANG_SAFEGUARD_PLACES` 和 `AMAP_CITY = '宜昌'` 硬编码 |
| **Windows 专用路径** | `utils.py`, `sandbox.py` | 🟢 低 | `safe_print`（GBK 编码）和 `_kill_tree`（taskkill）不可跨平台 |

#### 2.6.2 逐模块评级（变化部分）

| 模块 | CB-01 | CB-02 | 变化原因 |
|------|-------|-------|---------|
| `api/geo_routes.py` | B | **A** | 三处冗余清理 + wontfix 注释完善 |
| `core/db.py` | B+ | **退役** | 全闲置，已删除 |
| `core/ui_components.py` | 未评 | **退役** | Streamlit 僵尸，已删除 |
| `core/topo_scanner.py` | 未评 | **A** | 新增模块，AST+regex 扫描，设计优良 |
| `core/range_selector.py` | 未评 | **B** | 追踪覆盖高（16 ID），但路径大小写不一致 |
| `core/geo_registry.py` | 未评 | **B** | 功能完整，零 @track |

### 2.7 推进情况评估

#### 2.7.1 完成度估算（修订）

| 子系统 | CB-01 | CB-02 | 变化说明 |
|--------|-------|-------|---------|
| 数据管道（L0→L4） | 90% | **80%** | CB-01 高估。L1 未实跑、L3/L4 ⬜预留（归因靠 EMC+Sim）。L0 走购买策略已明确 |
| Core 核心库 | 85% | **87%** | 退役 4 个僵尸模块，新增 topo_scanner。待追踪埋点 9→6 |
| API 层 | 75% | **78%** | geo_routes 清理，新增 topo_routes |
| AI QA 子系统 | 70% | **75%** | EMC 3-phase 闭环。wisdom 9 条（+3）。知识闭环仍在初期 |
| Frontend 前端 | 80% | **82%** | e2e seam 去生产化，topology 3D 可视化成熟。零 JS 单测未改善 |
| 测试 | 65% | **65%** | 零增长（182）。E2E browser 仍挂。前端零测试 |
| 文档 | 80% | **78%** | 新增 CB 文档体系（+4 篇），但 prd/spec/architecture 过时内容未清理 |

**综合完成度：~78%（CB-01 估算 75-80% 区间内）**

#### 2.7.2 最新进展（本扫描时）

- 全部 5 个 CB-1 cleanup commit 已同步至本地（HEAD == origin/main）
- 工作树干净（仅 `docs/catch-ball/` 为本次 CB-02 新建）
- 会话交接卡显示：CB-1 实质完成，明天换环境续（前端 JS 单测 / browser 复验 / CB-2）

### 2.8 调用消耗分析（修订）

CB-01 的调用消耗分析基于 AGENTS.md 的理论 SOP 模型（每次标准 SOP = 5-7 次 Agent spawn）。项目方在反评价中明确：

> "项目跑在用户全局'不派 subagent'规则下，AGENTS.md 8 Agent 是概念框架，主线程直接干"

因此 CB-01 的周消耗估算（40-70 次）与实际不符。实际消耗模式更接近：每个任务 1 次主线程调用 + 按需工具调用（不计入模型调用次数）。

**修订后的关注点**：
- **上下文加载**：AGENTS.md (251 行) + CLAUDE.md (279 行) + MEMORY.md 仍在每次会话启动时全量加载，占用 ~8,000-12,000 tokens
- **Skills 上下文**：2 个 Skills 定义文件在触发时加载，总量可控
- **EMC MANIFESTO**：项目方选择不分层（承重红线），每次 ~4,000 字，接受此成本

**结论**：CB-01 的"调用效率 6/10"基于错误前提。但考虑到上下文加载仍较重，上调至 **7/10**。

---

## 第三部分：优化建议

### 🔴 高优先级

#### 建议 1：清理 requirements.txt 僵尸依赖

**问题**：`streamlit==1.58.0` 和 `pydeck`（无版本号）仍在 `requirements.txt` 中，但 `apps/` 已整层退役，`core/map_engine.py`（pydeck 消费方）已删除。这两个依赖是纯僵尸——安装后从不 import。

**验证**：`grep -rn "import streamlit\|from streamlit\|import pydeck\|from pydeck" --include="*.py" core/ api/ SCRIPT/ ai_qa/` 预期零结果。

**操作**：
1. 从 `requirements.txt` 移除 `streamlit==1.58.0` 和 `pydeck`
2. 运行 `pip install -r requirements.txt` 确认无破坏
3. 运行 `pytest tests/ -q` 确认零回归

#### 建议 2：修复 `range_selector.py` 路径大小写不一致

**问题**：`core/range_selector.py:20` 附近：

```python
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BOUNDARIES_DIR = os.path.join(_PROJECT_ROOT, 'data', 'boundaries')  # 小写 'data'！
```

项目全局使用大写 `DATA/`（`DATA/boundaries/`）。此处在 Windows 上侥幸工作（NTFS 大小写不敏感），但在 Linux/macOS 上会直接 `FileNotFoundError`。

**操作**：
1. 将 `'data'` 改为 `'DATA'`
2. 同时审查 `core/config.py` 的 `BOUNDARY_SHP` 路径是否也需要统一
3. 如果计划未来 Linux 部署，建议增加 CI 中 `python -c "from core.range_selector import _BOUNDARIES_DIR; assert os.path.isdir(_BOUNDARIES_DIR)"` 检查

#### 建议 3：统一 AGENTS.md Agent 数量声明

**问题**：AGENTS.md 标题称"8 Agent"，表格列 8 个，但 settings.json 实际注册 9 个（含 `sim-emotion-data`）。

**操作**：
1. AGENTS.md 标题改为 "9 Agent"
2. 表格增加 sim-emotion-data 行
3. 同步更新 `sim-emotion-data` 的可调用关系（无）

---

### 🟡 中优先级

#### 建议 4：删除或归档冗余 Sim 脚本

**问题**：`SCRIPT/generate_l1_mock.py`（522 行）自标"superseded by sim_performance_data.py"，`SCRIPT/generate_test_data.py`（1,232 行）与 `sim_performance_data.py`（729 行）功能重叠。

**操作**：
1. `grep -rn "generate_l1_mock\|generate_test_data" --include="*.py" .` 确认零活引用
2. 若确实零引用，退役并记入 `docs/catch-ball/retired.md`
3. 或移至 `SCRIPT/_archived/` 保留参考

#### 建议 5：为 `geo_registry.py` 补充追踪埋点

**问题**：`geo_registry.py` 是 core 中**唯一**无 `@track` 装饰器的模块。6 个公开函数（`list_point_layers`, `list_boundaries`, `get_layer_points`, `resolve_boundary`, `resolve_points`, `clear_cache`）全部缺少追踪。该模块是数据访问的关键路径。

**操作**：
1. 在 `core/tracker.py` 分配 `MOD_REGISTRY` 模块 ID
2. 为 6 个公开函数添加 `@track("MOD_REGISTRY.F_NNN")`
3. `register_track_id()` 注册

#### 建议 6：清理文档中的 Streamlit 过时内容

**问题**：`prd.md`（2026-06-15）、`spec.md`（§1.1-1.3）、`architecture.md`（下半部分）、`architecture-pattern.md`（表格）仍包含大量 Streamlit 时代的描述。这些文件虽已加退役 banner，但过时内容占据显著篇幅，对新读者造成误导。

**操作**：
1. `spec.md` §1.1-1.3：从完整 Streamlit 规范缩减为一句话引用（"Streamlit 层已于 2026-07-18 退役，历史规范见 git 历史"）
2. `architecture.md`：移除 Streamlit 详细架构段落，保留迁移说明链接
3. `architecture-pattern.md`：表格中"应用层(遗留)"和"UI 组件层(遗留)"改为单行标注"已退役"
4. `prd.md`：更新功能优先级表（部分 P1/P2 功能已通过 EMC 实现，需重新评估）

---

### 🟢 低优先级

#### 建议 7：恢复 dev-notes.md 更新

**问题**：`docs/dev-notes.md` 最后更新 2026-06-27（3 周前）。CB-1 全流程（退役清理、e2e seam、文档刷新）、browser E2E 框架搭建、compare 中文地名解析等均未记录。

**操作**：追加 2026-07-01 至今的关键事件（不必详尽，但应覆盖退役、CB-1、browser E2E、topology 3D）

#### 建议 8：诊断 trace-digest.md 空问题

**问题**：`docs/trace-digest.md` 仅 9 行 header，无任何实际错误条目。on_session_end Hook 的 `_append_trace_digest()` 函数存在且逻辑正确。可能原因：
- `.trace/trace.log` 中确实无 ERR/WARN 行（项目健康）
- 或 cursor 文件 `.claude/.trace-digest-cursor` 异常导致跳过追加

**操作**：手动运行一次 Hook 逻辑验证（检查 cursor 位置和 trace.log 的 ERR/WARN 行数）

#### 建议 9：Bash(streamlit *) 权限清理

**问题**：`.claude/settings.json` 中 `permissions.allow` 包含 `Bash(streamlit *)`，但 streamlit 已退役。

**操作**：从 allow 列表移除 streamlit 项。

#### 建议 10：拆分 panel.js（技术债预防）

**问题**：`frontend/js/panel.js` 达 2,098 行，混合 4 项职责（overview / table / timeline / polarity deep-read）。虽当前功能正常，但继续增长会显著增加维护和调试成本。

**操作**（低优先，不阻塞功能开发）：
1. 将 `panel.js` 拆分为 `panel-overview.js` + `panel-table.js` + `panel-timeline.js`
2. 或至少提取 `panel-table.js`（独立性强，~600 行）

---

## 第四部分：讨论点

### 讨论 1：AGENTS.md 的定位——概念框架还是运行时契约？

CB-01 暴露了一个根本问题：AGENTS.md 描述了一套自动编排体系（8 Agent + 三管线路由 + SOP 分级），但实际运行时"不派 subagent，主线程直接干"。

**两种定位选择**：

| 定位 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A. 概念框架（当前实际）** | AGENTS.md 是行为指南和新人 onboarding 文档，Agent 定义是角色参考卡片。主线程自行判断执行方式 | 灵活、省 token | 第三方（如 SCAN）会基于文档做错误推断 |
| **B. 运行时契约** | AGENTS.md 描述的就是实际执行方式。SOP 分级真的触发 Agent spawn | 可预测、可审计 | 增加调用次数和延迟（项目方已 reject） |

**我的看法**：维持定位 A，但建议在 AGENTS.md 头部显式标注：

> "本文件为概念框架和 AI 行为约束参考，不描述运行时 Agent spawn 机制。实际任务由主线程直接执行，SOP 分级用于指导执行深度而非触发独立 Agent。"

### 讨论 2：topo_scanner 的架构意义——项目进入"自文档化"阶段

`core/topo_scanner.py`（697 行，CB-01 后新增）是值得关注的里程碑：它不仅是一个功能模块，更标志着项目开始**用代码描述自身架构**。

**当前能力**：
- AST 解析 Python import 图
- Regex 解析 JS import 图
- AGENTS.md 模块表解析
- revision-log 任务树解析
- 输出 force-graph JSON → topology.html 3D 可视化

**潜在扩展方向**（不要求立即实现，仅供思考）：
- **依赖健康度**：检测循环依赖、跨层违规引用（如 frontend import core）
- **追踪覆盖热力图**：在拓扑图上用颜色标注 `@track` 覆盖率
- **变更影响分析**：修改文件 A → 自动列出受影响的下游文件

### 讨论 3：E2E 测试的策略困境

**现状**：
- 仅 1 个 E2E 测试（compare_regions），且 browser 环境挂
- C6 计划 4 例，仅完成 1 例
- 环境问题疑似非代码（换环境后可能消失）

**两种策略**：

| 策略 | 描述 | 风险 |
|------|------|------|
| **A. 先修环境再补测试** | 等换环境后 fix browser，然后集中补 C6 余下 3 例 + 新测试 | 环境问题可能反复出现，E2E 测试始终脆弱 |
| **B. 先补 JS 单测（不依赖 browser）** | CB-01 已建议：`field_dictionary.js`、`boundary-resolve.js`、`import.js` 纯函数先上单元测试 | 单测覆盖不了端到端交互 |

**建议**：B 优先（不依赖 browser，可立即执行），A 等环境稳定后跟进。

### 讨论 4：双模型闭环的第一次验证

CB-01→CB-02 是"双模型闭环"的首次实践。回顾效果：

**闭环产生了价值**：
- CB-01 发现 Streamlit 僵尸 → CB-02 确认已退役 ✅
- CB-01 建议补追踪 → 项目方评估后退役 3 个模块，待埋点从 9→6 ✅
- CB-01 误会调用模式 → 项目方澄清，CB-02 修正评估框架 ✅

**闭环暴露了局限**：
- CB-01 基于文档推断运行时行为，实际行为可能不同
- 第三方无法区分"概念框架"和"实际执行"
- 建议的未来轮次中，SCAN 增加一个环节：**先向项目方确认对运行时行为的理解**，再基于确认后的理解做评估

---

## 附录

### A. CB-01 vs CB-02 评分对比

| 维度 | 权重 | CB-01 | CB-02 | 变化 | 说明 |
|------|------|-------|-------|------|------|
| 架构设计 | 20% | 8.5 | **8.5** | → | 僵尸退役（+）offset 路径 case bug（-） |
| 代码质量 | 25% | 7.5 | **7.5** | → | geo_routes 修复（+）offset geo_registry 零追踪 + sim 重复（-） |
| 测试覆盖 | 15% | 6.5 | **6.0** | ↓ | 零增长 + E2E browser 环境挂（CB-01 时测试全绿，CB-02 时 E2E 不可用） |
| Harness 工程 | 20% | 9.0 | **9.0** | → | sim agent 注册（+）offset AGENTS.md 文档漂移（-） |
| 文档完整度 | 10% | 8.0 | **7.5** | ↓ | CB 文档体系新增（+）但 prd/spec/architecture 过时内容积累 + dev-notes 3 周空白（-） |
| 调用效率 | 10% | 6.0 | **7.0** | ↑ | CB-01 基于错误前提（Agent spawn）。修正为基于实际工作流（主线程直接执行）的评估 |
| **综合** | — | **7.6** | **7.6** | → | 结构改善（退役清理）与新增发现（路径 bug、文档 staleness、测试停滞）大致抵消 |

> **趋势解读**：综合分持平，但内部结构变化——架构和代码更干净（退役清理有效），测试和文档出现松动（长期未维护）。项目处于"清理→稳定"过渡期，下一步应聚焦补齐测试和文档短板。

### B. CB-01→CB-02 文件变更清单

| 变更类型 | 文件 | 说明 |
|----------|------|------|
| **删除** | `core/ui_components.py` | Streamlit 僵尸，835 行 |
| **删除** | `core/layer_registry.py` | st.session_state 依赖 |
| **删除** | `core/map_engine.py` | pydeck 僵尸 |
| **删除** | `core/db.py` | SQLite 全闲置，296 行 |
| **删除** | `.streamlit/config.toml` | Streamlit 主题配置 |
| **修改** | `api/geo_routes.py` | 三处冗余清理 + zonal_stats wontfix 注释 |
| **修改** | `.claude/settings.json` | sim agent 注册（8→9） |
| **修改** | `core/__init__.py` | docstring 去 map_engine/ui_components 引用 |
| **修改** | `frontend/js/main.js` | e2e seam 移出 |
| **修改** | `frontend/index.html` | 条件 dynamic-import e2e seam |
| **新增** | `frontend/js/e2e-seam.js` | 独立 test seam（40 行） |
| **新增** | `docs/retired.md` | 退役台账 |
| **新增** | `docs/cb-journal.md` | CB 轨迹 |
| **新增** | `docs/SCAN_DeepSeek.md` | CB-01 评估报告 |
| **修改** | `docs/revision-log.md` | §0 刷新 + §5 追加 5.132–5.135 |
| **修改** | `docs/todo.md` | CB-1 行动项更新 |
| **修改** | `memories/repo/tracking-progress.md` | 指 AGENTS.md 权威源 |
| **修改** | `memories/repo/session-handoff.md` | CB-1 交接 |

---

> **给 Claude Code 的后续指令**：
> 这是 CB-02（第二轮 DeepSeek 扫描）。请阅读本报告，重点关注：
> 1. CB-01 建议执行情况（§0.1）——已完成的确认、declined 的理解、待处理的优先级
> 2. CB-02 新增建议（§三）——特别是 #1（requirements.txt 僵尸）、#2（路径 case）、#3（AGENTS.md 同步）
> 3. 讨论点（§四）——AGENTS.md 定位声明、topo_scanner 扩展、E2E 策略、双模型闭环改进
>
> 完成后在 `docs/catch-ball/cb-journal.md` 追加 CB-02 反评价（agree/disagree/partial + 行动）。
>
> **双模型闭环进度**：
> ```
> CB-01（DeepSeek 扫描）→ 发现问题 → Claude Code 执行优化（5.132-5.135）
> → CB-02（DeepSeek 再扫描）→ 对比验证 → 本报告
> → 等待 Claude Code 反评价 + 行动 → CB-03 ...
> ```
