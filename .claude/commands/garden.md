---
description: 上下文树除草 — 扫过期 memory / 巨型文件 / 漂移 manifest / 僵尸注释，产清单不自动改
argument-hint: "(可选) 只扫某类: memory | files | manifest | zombies"
---

上下文树周期性除草（对应 OpenAI《Harness Engineering》doc-gardening + GC）。**只产除草清单建议，不自动改**——人确认后再执行。逐类扫，汇总优先级。

参数 `$ARGUMENTS` 指定单项则只扫那一类（memory/files/manifest/zombies），否则全扫。

## 步骤

1. **memory 过期**（`memory`）：读 `C:\Users\admin\.claude\projects\d--Github-emotion-map\memory\` 全部 `.md`（除 `MEMORY.md` 索引）。
   对每条：若其正文 `name:` 引用了具体**文件/函数/标志位/端点**，用 Grep/Read 验证该引用是否仍存在。
   - 引用已不存在（文件删/函数改名/端点移除）→ 标 `[STALE]`，建议改写或删（`忘掉 XXX`）。
   - 内容仍真但措辞过期 → 标 `[DUST]`，建议刷新措辞。
   - 记忆体系总量（文件数）若 >50 → 建议合并同主题、拆分过肥者。
2. **巨型文件**（`files`）：`docs/revision-log.md` 与 `docs/todo.md` 字节数。
   - 任一 >500KB → 建议把 §5/日段超 N 个月的旧条目归档到 `docs/archive/`（保顶部「最新动态」+任务树可用，旧历史可检索）。
3. **manifest 漂移**（`manifest`）：
   - `AGENTS.md` / `.claude/SKILLS_INDEX.md` 是否提及当前主力 `ai_qa/`、`ai_qa/industry_kb/`、`core/field_dictionary.py`、`core/spatial_analysis.py`、`frontend/js/ai_qa/`？未提及 → `[DRIFT]` 建议补。
   - `CLAUDE.md` 的「13 模块 55+ 追踪 ID」等硬数字 vs `core/tracker.py` 实际（`_TRACKING_REGISTRY` 长度 + grep `MOD_*` 引用数）→ 不符建议改。
   - 交接卡 `memories/repo/session-handoff.md` 的「Push 状态」vs `git log --oneline -5` + `git status` → 差 ≥1 commit 建议（人确认后）更卡。
4. **僵尸注释**（`zombies`）：grep 注释里引用已删端点/已弃模式（如「端点保留 + deprecated」实已删、「已迁移」指向空位）→ `[ZOMBIE]` 建议清注释。

## 输出格式

- 每条一行：`[STALE] memory/xxx.md — 引用 frontend/old.js 已删，建议删此条` 或 `[DRIFT] AGENTS.md — 未提 ai_qa/`
- 末尾总结：`GARDEN: N 项建议（HIGH=m / MED=n / LOW=k）`，并给「建议先处理」Top 3。
- 全绿时：`GARDEN: CLEAN — 上下文树新鲜`。

遵守 CLAUDE.md：结论先行、ASCII 标记、不夸、中文。这是「上下文连贯纪律」的一环（见全局 `~/.claude/CLAUDE.md`「工作方式」）——**零被动开销，仅手动触发**。
