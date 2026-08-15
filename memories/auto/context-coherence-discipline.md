---
name: context-coherence-discipline
description: 上下文连贯四纪律（除草/压缩前快照/漂移自检/单写者）+ 项目已有 7 机制即上下文树；OpenAI harness 工程对齐
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 64210e14-45f0-4874-b8e9-ced5d44d7f05
---

项目的上下文连贯已由 7 套机制构成一棵「上下文树」（CLAUDE.md 四级根 + revision-log ★任务路线图主干 + 三层 memory 分支 + docs 叶 + 交接卡快照 + §5账本 + tracker 运行时），高度对齐 OpenAI《Harness Engineering》的「地图非说明书 + 渐进式披露」。缺的不是树，是「园丁层」。

**四纪律（已入全局 `~/.claude/CLAUDE.md`「Harness 工作方式」）**：
1. **除草**：`/garden` 命令按需扫过期 memory/巨型文件/漂移 manifest/僵尸注释（产清单不自动改）+ `on_session_start.py` 阈值提醒（memory>50 或 revision-log>500KB 打印一行，零 LLM 开销）。
2. **压缩前快照**：`on_precompact.py`（PreCompact hook）→ `memories/repo/.wip.md`（git/trace 锚点，已 gitignore）；压缩后/新会话先读它恢复。
3. **漂移自检**：读交接卡前 `git log -5`+`git status` 对账卡的 push 算术/文件名；差即以 git 为准顺手更卡。不盲信快照里具体文件名/标志位，用前 Grep 验证。
4. **单写者**：并行 subagent 只回结论给主线程，主线程独写连贯文件（交接卡/memory/revision-log/todo）。

**Why:** 项目越厚漂移越快——实证：交接卡写"2 commits 待 push"实际 3 个（9ab1d62 也未推）；两套记忆树（僵尸 `.claude/memory/` 10 文件被 apps/CLAUDE.md 引用）已致碎片；AGENTS.md/SKILLS_INDEX.md 停在 EMC 前不提 ai_qa/。OpenAI 文章核心 = doc-gardening + 熵的垃圾回收（只长不烂）。

**How to apply:** 见腐烂迹象（过期数字/僵尸引用/巨型文件）主动 `/garden`；重活前确认 `.wip.md` 新鲜；接手新会话先 git 对账交接卡；派并行 subagent 时交代"只回结论"。本项目落点见 [[docs/context-map.md]]（注：docs 不入 memory 索引，按需读）+ `docs/harness-engineering-baseline.md`（六要素详表）。关联 [[token-saving-workstyle]] [[no-handoff-on-routine-commit]] [[maintain-revision-log]] [[todo-revision-log-sync]]。
