---
name: cb-prompt-copyable
description: CB prompt 交付须可点击复制（VSCode markdown 代码块 hover 复制）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: eb7c663a-3445-4f92-aa32-4718c44b8e6f
  modified: 2026-08-04T04:26:55.062Z
---

用户要求：以后发给 Codex/glm 组的 CB prompt，须增加复制符号（点击复制），方便直接粘贴给两组。

**Why:** 用户每次拿到 prompt 要手动框选复制，多要素长 prompt 易漏行/错选；VSCode 环境 markdown 渲染的代码块 hover 自带复制按钮，零成本实现。

**How to apply:** 交付 CB prompt 时用 ``` 代码块包裹全文（VSCode markdown 预览/侧栏 hover 即出复制按钮）；并在回复末尾保留「本请求由 claude组 发起…」签名行。关联 [[chinese-all-deliverables]]（prompt 正文仍中文）。
