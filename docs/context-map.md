# 上下文地图（Context Map）

> 一页看清本项目的「上下文树」——你和 Claude 都能一眼定位「去哪深挖」。对应 OpenAI《Harness Engineering》「地图而非说明书」。按需读，不自动注入。
> 维护：结构变了才更；新鲜度自检跑 `/garden`。最后更新：2026-07-16。

## 树形

```text
情绪_map（根·CLAUDE.md 四级：全局→项目→core/apps/SCRIPT）
│
├─ 根 · 规则（全量注入）
│  └─ CLAUDE.md — 顶层不变规则 + 演示逻辑链北极星 + 项目设计哲学 + 编码规范
│     · 全局 ~/.claude/CLAUDE.md — Skill 优先 + Harness 上下文连贯纪律（四纪律）
│
├─ 主干 · 任务与账本（按需读顶）
│  ├─ docs/revision-log.md ★ 任务路线图（ASCII 树 ✅🔄⬜⏸❌）+ §5 最新动态（倒序置顶）
│  └─ docs/todo.md — 日段任务（倒序）；docs/dev-notes.md — 技术心得；docs/decisions.md — ADR；docs/debug-memory.md — **全局调试记忆（R1-R19 踩坑规则库·多组共享·CB-41 建·含维护协议与 dsh 宿主坑·2026-08-21 资产化）**
│
├─ 分支 · 隐规则记忆（索引全量注入、子文件按需）
│  └─ ~/.claude/projects/d--Github-emotion-map/memory/ — MEMORY.md 索引 + 原子 .md（feedback/project/reference）
│     · 僵尸树 .claude/memory/_archived/ — Streamlit 期遗留，仅供 apps/ 查阅，不再增量
│
├─ 叶 · 专项参考（渐进披露，按需）
│  └─ docs/ — brand-visual / copywriting-style / api-conventions / mcp-strategy / ai-qa-design /
│            industry-knowledge-base / landuse-classification-2023 / harness-engineering-baseline（六要素）
│     · 城市体检对接层（阶段 0'·2026-08-11）：DATA/exchange/ — README（三分法）+ manifest.json（引用清单）+ schema_inventory.md + PII_EXCEPTIONS.md + 口径对齐.md
│       —— 上游 zcode 中转站 {URENEWAL_ROOT}/1 宜昌市城市体检/EMC数据中转站（manifest v1.4.6·只引用不复制·PII 例外 building_50year_1）
│       —— 后续：阶段 1' checkup_ingest.py（MOD_CHECKUP·F_001 起）+ geo_registry 注册 + 阶段 2' RAG 消费 04_互通优化
│     · 宜昌基础地理信息数据（未来消费的底层数据·2026-08-11 建立·官方准确）：
│       —— 官方行政边界：`02_空间数据集/行政区划_官方/`（市域县级 14 县区 + 村社区 1682 + SSX 聚合 113 街办含 16 街办口径·WGS84·源自用户提供 shp）
│       —— presets 注册：admin_street（113 街办）/ admin_community（1682·94MB reference_only 只引用）/ admin_county（14 县区）
│       —— 消费链路：geo_registry/range_selector → zonal/密度/落图（12345/体检/项目均可用街办 zonal）
│       —— 关联：街办≠道路（SSX 行政级）·16 街办口径对齐表（CB23-16街办口径对齐表）·街道→街办术语统一
│     · 出口抽象层（立项根本目标）：docs/catch-ball/discuss/EMC-出口抽象层架构讨论_2026-08-03.md（专业+通俗）
│       —— 三铁律 / 软指标可信性缺口 / 出口卡片 / 案例深挖（官方资料·可量化/可感知/可评价三类）
│     · 出向知识库（出口卡片组装数据源）：ai_qa/outlet_kb/ — 7 契约 + 21 指标映射（官方三类）+ 5 案例
│       + summary 四方面闭环·测试守卫（登记：CLAUDE.md「出口抽象层」节 + AutoMemory outlet_kb 指针）
│
├─ 快照 · 跨会话桥（手动触发）
│  ├─ memories/repo/session-handoff.md — 单节点当前态 + 复制即用 prompt（说"交接"才覆写）
│  └─ memories/repo/.wip.md — PreCompact 压缩前机器快照（git/trace 锚点，gitignore）
│
├─ 领域 · Catch-Ball（CB 双模型闭环；repo 内·跨环境同步）
│  └─ docs/catch-ball/ — RULES（CB 规范）/ KNOWLEDGE（CB 记忆库·跨轮蒸馏）/ cb-journal（按轮轨迹）/ retired（退役台账）/ SCAN_DeepSeek_{NN}（第三方报告·只读）/ discuss/（跨组讨论输入·如 EMC体验评估讨论报告_2026-08-01；**EMC×dsh 核心路线 = `EMC-dsh工程预期与双环境同步核心思想_Codex-2026-08-21.md`**）/ _handoff/（换机卡 HOME/OFFICE + CB恢复记忆卡_2026-08-03·Codex/glm 换环境恢复 + glm组记忆_RAG环境补链_2026-08-09·glm组 侧 RAG 补链 learning 镜像 KNOWLEDGE §2）
│     · 触发：新 SCAN → on_session_start hook 一行提示 → /cb 命令编排反评价（主线程，不派 subagent）
│     · 记忆共享：KNOWLEDGE 登记本图 + AutoMemory（cb-knowledge-base 指针），不孤岛（见「记忆共享通则」）
│
└─ 运行时 · 决策可回溯
   └─ core/tracker.py — @track + _REGISTRY（18 模块 / 510+ 引用）；[TRACE] 日志 → ID → 代码 O(1)
```

## 园丁层（保持树不烂）

| 机制 | 触发 | 位置 |
|---|---|---|
| `/garden` 除草 | 手动（按需） | `.claude/commands/garden.md` — 扫过期 memory/巨型文件/漂移 manifest/僵尸注释，产清单不自动改 |
| 阈值提醒 | session-start 自动（超限才打印） | `.claude/hooks/on_session_start.py` — memory>50 或 revision-log>500KB |
| 压缩前快照 | PreCompact 自动 | `.claude/hooks/on_precompact.py` → `memories/repo/.wip.md` |
| 漂移自检 | 读交接卡前手动 ritual | `git log -5` + `git status` 对账（纪律在全局 CLAUDE.md） |

## 记忆共享通则（防孤岛）

**所有记忆系统（无论位置）须与项目总体记忆共享**——不孤岛（用户通则）：

1. **登记**：任何记忆产物（AutoMemory / CLAUDE.md / 专项 docs / CB KNOWLEDGE / 未来领域记忆）在本图登记。
2. **双向链接**：与相关条目互链（如 KNOWLEDGE.md §1 承重 ↔ AutoMemory `[[emc-tri-state-exit-contract]]` 等）。
3. **单一权威源 + 指针**：不重复（一处定义、他处指针）。
4. **不孤岛**：任何记忆文件至少被本图 + 一个索引（MEMORY.md / CLAUDE.md）指向。

**跨环境**：repo 内文件（docs/ / memories/repo/）git 同步、两机都见；`~/.claude` AutoMemory 经 **`memories/auto/` 蒸馏层镜像**跨机（`memory-sync.bat` 双击镜像 → Gitee；`py tools/memory_sync.py pull` 恢复）——原「机本地已知局限」已于 2026-08-15 关闭。全量对话 context 另走 DEV-SYNC-HUB 硬盘 `Memory.bat` 分侧快照（`E:\DEV-SYNC-HUB\memory\<office|home>\<工具>\`，跨机衔接 = AI 会话开场读对端目录）。

**首例**：CB KNOWLEDGE.md（`docs/catch-ball/`）— 登记本图 + AutoMemory `cb-knowledge-base` 指针 + 与 6 条 AutoMemory 双链（`[[emc-tri-state-exit-contract]]` / `[[l0-acquisition-purchase-strategy]]` / `[[emc-delegates-to-toolbox]]` / `[[emc-aggregate-column-alias-silent-zero]]` / `[[emc-eval-empty-context-vs-runtime]]` / `[[project-design-philosophy]]`）。

---

## 新鲜度状态（2026-07-19 快照）

- 记忆条目：62 条（阈值 50，**已超**）+ catch-ball/ 6 文件（RULES/KNOWLEDGE/cb-journal/retired/SCAN_01/SCAN_02，repo 内跨环境同步）。revision-log ≈500KB / todo ≈220KB（阈值 500KB，临界）→ 考虑 `/garden` 除草 + `/curate-memory`。
- 已知待整（`/garden` 会列）：AGENTS.md / SKILLS_INDEX.md 未提 ai_qa/ 等 5.x 主力；CLAUDE.md「13 模块 55+ ID」过期（实 18/510+）；交接卡 push 算术漂移（写 2 实 3）。
- 六要素 harness 成熟度详表见 [harness-engineering-baseline.md](harness-engineering-baseline.md)。
