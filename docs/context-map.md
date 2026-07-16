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
│  └─ docs/todo.md — 日段任务（倒序）；docs/dev-notes.md — 技术心得；docs/decisions.md — ADR
│
├─ 分支 · 隐规则记忆（索引全量注入、子文件按需）
│  └─ ~/.claude/projects/d--Github-emotion-map/memory/ — MEMORY.md 索引 + 原子 .md（feedback/project/reference）
│     · 僵尸树 .claude/memory/_archived/ — Streamlit 期遗留，仅供 apps/ 查阅，不再增量
│
├─ 叶 · 专项参考（渐进披露，按需）
│  └─ docs/ — brand-visual / copywriting-style / api-conventions / mcp-strategy / ai-qa-design /
│            industry-knowledge-base / landuse-classification-2023 / harness-engineering-baseline（六要素）
│
├─ 快照 · 跨会话桥（手动触发）
│  ├─ memories/repo/session-handoff.md — 单节点当前态 + 复制即用 prompt（说"交接"才覆写）
│  └─ memories/repo/.wip.md — PreCompact 压缩前机器快照（git/trace 锚点，gitignore）
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

## 新鲜度状态（2026-07-16 快照）

- 记忆条目：44 条（阈值 50，接近）。revision-log ≈443KB / todo ≈209KB（阈值 500KB，接近）→ 阈值提醒尚未触发，增长到限即提示 `/garden`。
- 已知待整（`/garden` 会列）：AGENTS.md / SKILLS_INDEX.md 未提 ai_qa/ 等 5.x 主力；CLAUDE.md「13 模块 55+ ID」过期（实 18/510+）；交接卡 push 算术漂移（写 2 实 3）。
- 六要素 harness 成熟度详表见 [harness-engineering-baseline.md](harness-engineering-baseline.md)。
