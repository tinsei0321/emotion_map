---
name: avoid-frames-fill-style
description: 全局避免线框(border)，胶囊/徽章/状态标用填充式(字体+背景填充保形状)
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 34991651-8633-4485-b6f8-4f807051fc53
  modified: 2026-07-22T04:03:44.005Z
---

用户设计原则（2026-07-22 宣告）：**所有设计尽量避免线框形式**——线框观感不好。胶囊/徽章/状态标签改用"字体 + 背景填充"保形（去 border，实/半透明填充 + 对比字），保 border-radius 胶囊形。

落地首例：`.aiq-exit-badge`（"分析完成"等三态出口徽章）原亮绿 `#4ADE80` 字 + 绿线框 → 去 border + teal 柔填充（Dark `rgba(45,212,191,0.16)` 底 + `#5EEAD4` 字；Light 深 teal `#0F766E`），warn/neutral 同步填充式。

**Why**：线框在高密度 UI 里显杂乱、廉价；填充式更现代、层次清晰（Claude/Linear 风）。亮高饱和色（纯绿 `#4ADE80`）配线框尤其突兀——用户明确点名。

**How to apply**：新建胶囊/徽章/标签默认填充式（`border:none` + bg + 对比字 + radius），勿用亮高饱和色；改现有线框组件先 grep 同类统一（[[design-language-consistency-iron-rule]]）。可点击交互胶囊另参 [[capsule-button-design-language]]（无线框+阴影+hover 反馈）。注意：非装饰性分隔（toolcard/code block 的细边、input 盒子边框）属另一范畴，本原则针对"装饰性/状态性线框徽章"。
