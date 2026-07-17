---
description: commit 后一键同步 — append revision-log §5 顶部 + 同步 todo 当日段（不动交接卡，除非说"交接"）
argument-hint: "(可选) 本次工作一句话摘要；省略则从 git diff 推断"
---

commit 后高频手写两份（revision-log §5 + todo 当日段）的固化。沉淀 memory `maintain-revision-log` + `todo-revision-log-sync` + `no-handoff-on-routine-commit`。

## 步骤

1. **推断摘要**：`$ARGUMENTS` 给了就用；否则 `git log -1 --pretty=%B` + `git diff HEAD~1 --stat` 推断"本次改了什么 + 为什么"。
2. **revision-log §5**（[docs/revision-log.md](docs/revision-log.md)）：在 §5「最新动态」指针下方、最新 bullet 前，append 一条新 bullet：
   - 格式 `> - **5.NNN <标题>（<主题>）**：<用户意图 → 落地 · 文件>。承重：<...>。详见本条。`
   - 编号 5.NNN = 上一条 +1（连续不跳号）
   - 同步更新顶部「📍 最新动态」指针指向新 5.NNN + 重写"最新工作 ="
3. **todo.md 当日段**（[docs/todo.md](docs/todo.md)）：在顶部当日 `## 📅 <日期>` 下、最新 `### ✅/🔄` 任务前，append `### ✅ <标题>（revision-log 5.NNN，commit <短哈希> · **用户手动 push**）` + 要点 bullet。**最新置顶，勿底部追加**。
4. **交接卡**（[memories/repo/session-handoff.md](memories/repo/session-handoff.md)）：**不动**（`no-handoff-on-routine-commit`）——除非 `$ARGUMENTS` 含「交接」或用户本会话明确说"交接"，才覆写。

## 注意

- 结论先行、ASCII 标记、中文、最新置顶。
- revision-log 写"用户意图（非程序员表述 → 专业精炼）+ 落地"，非纯技术流水（revision-log 第 1 节分工）。
- todo 与 revision-log 的 5.NNN 必须对应。
- 遵守 `只 commit 不 push`（commit 后告知"待你 push"）。
