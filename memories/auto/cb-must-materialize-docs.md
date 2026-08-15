---
name: cb-must-materialize-docs
description: 每次要两组介入评估时，claude组（项目负责组）必须先把 prompt 落成正式复验文档 + 推送，不能只给用户转发文本
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2e205ce2-450a-4746-8760-5c1df66b418e
  modified: 2026-08-08T11:54:59.927Z
---

用户 2026-08-08 明确：要两组介入评估时，**claude组 须先把 prompt 落成正式复验文档 + git push**，再让用户转发。这次（5115d7c 黑名单修复复验）我直接给了转发文本没落文档，用户纠正「下次要记得落成正式复验文档+推送」。

**Why**：落成文档是 CB 流程的一部分（发起/预检文档可 push·供两组跨环境读 + 历史可溯）；只给转发文本则无正式记录、两组读不到完整上下文、跨机不同步。用户把「持续优化工作方式」列为项目负责组的职责。

**How to apply**：任何「需要两组介入」的环节（复验/预检/评估/回归）→ ① 写 `docs/catch-ball/discuss/{topic}_{类型}_{date}.md`（含背景/必读/焦点/附 A prompt）→ ② git commit + push（发起文档可 push）→ ③ 才把附 A prompt 给用户转发。与 [[acceptance-through-cb]] 呼应：验收/评估都走 CB 文档化。
