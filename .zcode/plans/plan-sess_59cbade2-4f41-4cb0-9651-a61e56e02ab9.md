## CB-2 实施方案（最终版）

### 一、目录结构

```
docs/catch-ball/                         ← 新建，仅在此目录内写入
├── RULES.md                             ← 新建：评估规则与工作指南
├── SCAN_DeepSeek_01.md                  ← 新建：CB-1 原文归档（从 origin/main 复制）
├── SCAN_DeepSeek_02.md                  ← 新建：CB-2 本次评估
├── cb-journal.md                        ← 新建：从 origin/main 复制 CB-01 轨迹 + 追加 CB-02
└── retired.md                           ← 新建：从 origin/main 复制退役台账
```

### 二、编号规则

- SCAN 文档：`SCAN_DeepSeek_{NN}.md`，两位零填充，01 起始，顺序递增
- cb-journal 内章节：`## CB-01` / `## CB-02` 对应每轮
- 每轮 SCAN 报告第一章固定为「上一轮回顾与执行评估」

### 三、RULES.md 内容纲要

| 章节 | 内容 |
|------|------|
| **评估原则** | 第三方中立、证据驱动（文件路径+行号）、建设性批评、双模型闭环 |
| **评估方法** | 6 轴评分体系（架构 20% / 代码 25% / 测试 15% / Harness 20% / 文档 10% / 调用效率 10%）+ 三级扫描深度（L1 全量/L2 关键函数/L3 概览）|
| **评估维度** | 8 子维度：Vibe Coding 策略 / Harness 框架 / Agent 体系 / Skills 体系 / 架构设计 / 代码质量 / 推进情况 / 调用消耗 |
| **CB 环节** | SCAN（扫描评价）→ Journal（反评价+行动）→ Retired（退役留痕）→ 下一轮 SCAN（对比验证） |
| **文档编号** | SCAN 两位零填充序号；journal 内章节对应轮次；每轮首章固定回顾上轮 |
| **CB 权限** | 仅可编辑 `docs/catch-ball/`；不可编辑其他文件；不可 commit/push；读取项目文件不受限 |
| **报告模板** | 固定 5 部分：回顾 → 范围 → 评价 → 建议 → 讨论 |

### 四、执行步骤

#### 步骤 1：创建 catch-ball 目录 + 规则文档
- 新建 `docs/catch-ball/RULES.md`（按上述纲要完整撰写）

#### 步骤 2：归档 CB-1 全部文件
- 从 origin/main 读取并写入：
  - `SCAN_DeepSeek_01.md` ← `docs/SCAN_DeepSeek.md` 原文（仅头部加归档元信息：轮次、归档日期、原始路径）
  - `cb-journal.md` ← `docs/cb-journal.md` 原文
  - `retired.md` ← `docs/retired.md` 原文

#### 步骤 3：全面扫描项目（基于本地 working tree 当前状态）
使用多个 Explore Agent 并行深度刺探，覆盖全部核心模块：

| 批次 | 扫描对象 | 文件数 |
|------|---------|--------|
| **配置层** | AGENTS.md, CLAUDE.md, MEMORY.md, README.md, requirements.txt, pytest.ini, .mcp.json, .gitignore, .claudeignore, .env.example | ~12 |
| **Agent/Harness** | `.claude/agents/`（全部 9 活跃+3 归档）、`.claude/hooks/`（全部 5 hooks）、`.claude/commands/`（全部 6 命令）、`.claude/settings.json` | ~26 |
| **Core 核心库** | `core/` 全部 .py 文件（spatial_analysis, buffer_analysis, tracker, config, utils, topo_scanner, geocode, coord_transform, field_dictionary, place_layer, range_selector, export, geo_registry, data_loader 等）| ~18 |
| **SCRIPT 分析管道** | `SCRIPT/` 全部 .py 文件（emotion_analysis, data_governance, relevance_filter, run_analysis, multimodal_analysis, sim_performance_data, sim_ermawu_l3l4, generate_test_data 等）| ~16 |
| **API 层** | `api/` 全部 .py 文件（main, routes, geo_routes, sandbox, run_routes, aiqa_routes, topo_routes, schemas）| ~8 |
| **AI QA 子系统** | `ai_qa/` 全部 .py 文件（manifesto, paradigm, prompts, llm, review, wisdom, router, episode, consolidate）+ `industry_kb/` 全部 | ~15 |
| **Frontend 前端** | `frontend/js/`（全部 28+ 模块）、`frontend/css/`（全部 15+ 文件）、`frontend/*.html`、`frontend/vendor/`、`frontend/serve.py`、`frontend/js/ai_qa/`（6 文件）| ~64 |
| **Tests 测试** | `tests/` 全部 test_*.py + conftest.py + browser/ | ~17 |
| **Docs 文档** | `docs/` 全部 .md 文件 + `memories/repo/` | ~30+ |
| **数据层** | `DATA/` 目录结构概览 + `SCRAPER/` 爬虫状态 | ~20 |

> 同步对比 origin/main 确认 CB-1 后 10 commits 的变更内容，标注与本地 working tree 的差异。

#### 步骤 4：生成 CB-2 报告 `SCAN_DeepSeek_02.md`

**报告结构（5 部分）：**

**第〇部分：CB-01 回顾与执行评估**
- CB-01 10 条建议执行状态表（逐条列出 → 采纳/拒绝/部分 → 执行证据 → 第三方评价）
- 对 CB-01 反评价论断的第三方审核（agree 项核实、disagree 项论据评估）
- CB-01 遗漏补充
- 项目 CB-01→CB-02 关键变化摘要

**第一部分：扫描内容**
- 9 维度 × 文件数 × 关键发现总览表
- L1/L2/L3 深度说明

**第二部分：扫描结果/评价**
- 每个子维度独立评分 + 趋势箭头（↑改善 / →持平 / ↓退步）
- 详述：Vibe Coding / Harness / Agent / Skills / 架构 / 代码质量 / 推进 / 调用消耗

**第三部分：优化建议**
- 高/中/低三级优先级
- CB-01 遗留项标注（✅ 已修复 / ⬜ 未处理 / ❌ declined）
- 新增发现独立标注

**第四部分：讨论点**
- 基于最新状态的新话题

**附录**
- CB-01 vs CB-02 6 轴评分对比表
- 两轮扫描间文件变更清单

#### 步骤 5：更新 cb-journal
- 在 `docs/catch-ball/cb-journal.md` 末尾追加 `## CB-02` 章节
- ① SCAN 摘要 ② 状态：open（等待反评价）

### 五、约束
- 全部写入仅限 `docs/catch-ball/` 目录
- 读取项目文件通过 Explore Agent / Read / git show（只读）
- **零 commit / 零 push / 零副作用**