---
name: flex-stretch-scrollheight-distortion
description: flex:1 撑满时 scrollHeight=clientHeight 失真；量内容自然高须临时 flex:0 0 auto+height:auto
metadata: 
  node_type: memory
  type: reference
  originSessionId: 34991651-8633-4485-b6f8-4f807051fc53
  modified: 2026-07-22T04:16:17.173Z
---

EMC 内容驱动高度自适应（`_fitEmcToContent`）的坑：`chat-messages` 用 `flex:1 1 auto` 撑满 panel，当**内容少于可见区**（欢迎卡 / 清空态）时，`element.scrollHeight === element.clientHeight`（都=撑满高），增量法 `need = panel − clientHeight + scrollHeight` 退化为 `= panel`，**永远缩不回去**。内容多（溢出）时 scrollHeight 才 > clientHeight，故"拉长"正常、"缩短"失效——症状正好是用户报的"回欢迎卡不缩"。

正解：量内容自然高时**临时** `msgs.style.flex='0 0 auto'; msgs.style.height='auto'` → 读 `offsetHeight`（真内容高）→ 同步恢复原值。同帧改+量+恢复，浏览器回调结束才绘制，无闪烁；style 变不触发 MutationObserver（只监 childList/characterData），不循环。

**How to apply**：任何"容器 flex 撑满 + 按内容自适应高度"场景，勿直接用 scrollHeight 量内容高；用临时取消 flex 拉伸的 offsetHeight 量法。另见 [[extrusion-height-maxheight]]（3D 高度量法）、[[frontend-pitfall-check]]（前端三坑）。
