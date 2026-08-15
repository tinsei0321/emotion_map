---
name: time-format-date-hm
description: "todo/交接卡/revision-log 时间戳统一写\"MM月DD日 HH:MM\"(24h)，如\"07月06日 14:30\"，不单写日期"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e49e5ca2-2dbe-424c-9fd8-f63d293f3640
---

写 `docs/todo.md` / `memories/repo/session-handoff.md` / `docs/revision-log.md` 的时间戳时，格式统一为「MM月DD日 HH:MM」（24 小时制），如「07月06日 14:30」——日期 + 具体时间，不光写日期。

**Why:** 用户 07月06日 00:46 提出：单写日期（"2026-07-06"）跨会话、跨日夜班容易乱；加具体时间可精确排序、避免同日多次改动混淆。

**How to apply:** 这三类文件的时间戳（handoff「最后更新」、revision-log 板块标题日期、todo 状态变更标记）一律"MM月DD日 HH:MM"。取代旧"YYYY-MM-DD"或"2026-07-05 夜"等模糊写法。关联 [[maintain-revision-log]] [[todo-revision-log-sync]] [[session-handoff]]。
