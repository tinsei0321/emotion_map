---
name: emc-reuse-toolbox-panel
description: EMC 分析图必须复用 Toolbox 参数面板已有色板/参数；ForAI=dialog 镜像；缺失提醒开发者补
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a53f1d50-18bd-4771-96ac-dfb0994e6ec3
  modified: 2026-07-27T02:57:23.869Z
---

EMC（Smart Agent）产出的所有分析图，必须严格采用 Toolbox·参数面板（dialog）中**已有**的色板/配色/参数，不得在 `generate*ForAI` 入口临时造新内容。参数面板缺失的能力（`PANEL_MISSING`）→ 停下提醒开发者补齐+标准化+本地化，EMC 侧不自行实现。

**Why**：「Smart Agent, Dumb Tool」在产出层的落地——Dumb Tool 的"制式化"= 产出物也必须来自制式化的参数面板，不容许 Smart 侧（ForAI 入口）自定义产出形态。CB-04 触发：[generateHeatmapForAI](frontend/js/heatmap-tool.js#L817) 自带 `rampKey:'rainbow'` 绕过 dialog 的 [computeStyle](frontend/js/heatmap-tool.js#L93)，致"生成 L2 消极点热力图"仍出综合彩虹图（H1）。用户明确指示：缺失项提醒开发者补，不临时造。

**How to apply**：
- **ForAI 入口 = dialog 入口镜像**：`generate*ForAI` 的色板/参数映射复用 dialog 同一函数（computeStyle/terrainRampOf），不自带默认另搞一套。
- **契约三处同步**：改 `generate*ForAI` 须同步 ① `ai_qa/tool_contracts.py`（单一权威源·L2）② 前端 `SKILL_DEFS` 镜像 ③ `prompts.py` 工具描述（参数集为实参超集·可少不可多·可漏不可错）。
- **极性值域统一全词**（overall/positive/negative/neutral），入口 `_normalizePolarity` 归一；治旧单字母（ALL/P/N/O）与全词混用静默回退 overall。
- 落 [AGENTS.md 铁律 11](AGENTS.md)；关联 [[emc-delegates-to-toolbox]]（委托主 Toolbox 不自造 geo 端点）、[[emc-aggregate-column-alias-silent-zero]]（别名静默零·同类契约坑）、[[terrain-mesh-rendering]]（terrain 极性色板复用）。CB-04 反评价 13 agree/0 disagree/1 partial。
