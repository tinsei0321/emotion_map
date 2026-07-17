---
description: 全局 memory 树 GC — 标僵尸/过时/重复/冗余，提议删/合并 + 更新 MEMORY.md 索引（扩 /garden 到记忆层）
argument-hint: "check(默认只产清单) | apply(人审后执行删/合并)"
---

`/garden` 的记忆层延伸：review 全局 memory 树，标僵尸/过时/重复/冗余，提议删或合并，并同步 MEMORY.md 索引。**默认 check 只产清单，apply 才执行**。沉淀 `context-coherence-discipline`。

memory 目录：`C:\Users\Hi\.claude\projects\d--Github-emotion-map\memory\`（全局 auto-memory，索引 = MEMORY.md）。

## 步骤

1. **读全部 memory**：读 memory 目录全部 `.md`（除 MEMORY.md）+ MEMORY.md 索引。
2. **逐条体检**（每条对照 memory 三纪律）：
   - **僵尸 [STALE]**：引用的文件/函数/端点/标志位已不存在（Grep/Read 验证 `name:` 正文里的具体引用）→ 提议删（或 `忘掉 XXX`）。
   - **过时 [DUST]**：内容仍真但措辞/数字过期（模块表行号、API 旧名、已迁的旧路径）→ 提议刷新。
   - **重复 [DUP]**：多条讲同一事（如 3 条都说 aggregate 别名静默零）→ 提议合并为 1。
   - **冗余 [REDUNDANT]**：repo 已记录（CLAUDE.md/git/code 自带）的 → 提议删（memory 不复述 repo，只记非显然的）。
   - **承重 [KEEP]**：高频 `[[link]]` 引用、近期会话用过、踩坑结晶 → 保留。
3. **MEMORY.md 索引对账**：每条 memory 是否在 MEMORY.md 有索引行？hook 是否准确？孤儿（有文件无索引）/ 幽灵（有索引无文件）→ `[IDX]`。
4. **apply 模式**（`$ARGUMENTS` 含 apply）：人审清单后执行删/合并 + 重写 MEMORY.md 索引；check 模式只产清单。

## 输出

- `[STALE] xxx.md — 引用 frontend/old.js 已删 → 建议删`
- `[DUP] a.md + b.md 同讲 aggregate 别名 → 合并为 a.md`
- 末尾 `CURATE: N 项（删 x / 合并 y / 刷新 z / KEEP k）`，给 Top 3 建议。
- 全绿：`CURATE: CLEAN — memory 树新鲜（M 条全承重）`。

遵守 CLAUDE.md：结论先行、ASCII、不夸、中文。零被动开销，仅手动触发。删除红线：apply 前人审确认。
