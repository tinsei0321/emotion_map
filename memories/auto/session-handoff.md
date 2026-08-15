---
name: session-handoff
description: Proactively prompt new-session handoff at task boundaries / context bloat; give 4-part package (prompt + handoff note + steps + recap)
metadata: 
  node_type: memory
  type: feedback
  originSessionId: dbb1bb3e-6788-4d49-a6d3-3dc712468cfe
---

主动判断何时该开新会话，在节点给 **4 件套**（提示 + 衔接说明 + 衔接操作 + 小结），不等用户问。

**触发判断（满足任一即提示开新会话）**：
1. **任务自然边界**：一批 / 一个完整功能完成（如批1 做完、一组 bug 修完、一个模块收尾）
2. **上下文膨胀信号**：会话轮次 >15-20 / 多次读大文件 / kepler 源码探索 / 用户多次改 SVG（每次注入完整 diff 进上下文）
3. **用户提 token 消耗**（"token 多"/"消耗大"）
4. **主题大切换**（换完全不相关的大主题）

**4 件套（触发时给）**：
1. **提示**：建议现在开新会话 + 理由（上下文膨胀程度 / 任务边界 / token）
2. **衔接说明**：新会话第一句贴给 AI 的话（"读 `docs/revision-log.md` 顶部任务树 + 当前状态 + 下一步任务"）
3. **衔接操作**：关本会话 → 开新会话 → 贴衔接说明
4. **小结**：本会话 commit 列表 + 任务状态（哪些 ✅ / 🔄 / ⬜）

**Why:** 单会话满载每轮发全历史是 token 最大头（用户日报 1-2 亿）。任务边界换会话 + revision-log 任务树衔接 = token 断崖降，且不丢上下文（任务树持久化、跨会话常驻）。

**How to apply:** 每轮自检触发条件。触发即主动给 4 件套（不等用户问"何时换会话"）。配合 [[token-saving-workstyle]] + [[maintain-revision-log]]。
