---
name: prompt-delivery-codeblock
description: 给用户的转发 prompt 一律用单个代码块包裹交付（一键复制），不用裸 markdown/分隔线
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7567b0ec-9bc8-4a64-8f5a-7bf41bb12d6c
  modified: 2026-08-16T04:16:39.400Z
---

用户 2026-08-16 明确："prompt 都用一键复制的方式给我"。

**Why:** 转发给其他 AI 组（codex/zcode/dsh）的 prompt 需要整段复制粘贴；裸 markdown + 分隔线形式要手动框选，易漏头尾；VSCode/终端渲染的代码块自带复制按钮，一键拿全文。

**How to apply:** 凡交付"给用户转发的 prompt"（CB 发起 prompt、通知 prompt、任务分配 prompt 等），一律放进单个 ``` 围栏代码块，块内是纯文本 prompt 全文；块外只留极简说明。代码块内容不再嵌套 markdown 标题渲染问题无所谓，保纯文本可粘贴。
