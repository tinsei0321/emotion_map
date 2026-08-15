---
name: sticky-hover-priority
description: sticky（点击锁定）最高级，hover 不覆盖其长显内容（tip/高亮/词卡）——全局逻辑
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fed1d60a-02fb-4599-aa2e-975832ec5441
---

任何"hover 试探 + click 锁定 sticky"的联动，**sticky 状态最高级**：只要有 sticky（点击锁定）的内容在长显，鼠标 hover 其他项**不覆盖**该 sticky 内容（tip 不换、高亮不换、词卡不换）。直到用户再点释放/切换。

**Why**：5.27 用户报 bug——点关键词锁定地点 tip 后，hover 其他词 tip 被覆盖。"点击状态长亮最高级，鼠标悬停不会覆盖"是全局交互逻辑，不只一处。

**How to apply**（panel.js 极性深读为参考实现）：
- hover handler 开头：`if (_<x>Sticky) return;`（或仅做不影响 sticky 的试探，如 highlightCellSet 的 hover-restore 模式由 clearHighlightCellSet 自处理）。
- 词卡：`if (_polWordTipSticky) return`（hover 不换 tip）；矩阵块：`if (!_polBlockSticky) renderWords()`（sticky 块词组不被 hover 覆盖）。
- 释放：再点同一项 → 清 sticky + tip + 高亮（`resetHighlightCellSet`/`clearLocTips`）。
- 切换：点异项 → 释放旧的 + 设新的（`toggleStickyHighlight` 同 key 释放/异 key 切换）。

与 CLAUDE.md「悬停=试探聚焦(瞬时，leave 回 sticky 或清)；点击=锁定 sticky」一致——hover 可试探，但**试探不顶替 sticky**，leave 必回 sticky。
