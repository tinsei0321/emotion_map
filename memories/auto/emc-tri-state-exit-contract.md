---
name: emc-tri-state-exit-contract
description: EMC 回答策略=三态出口契约(harness 代码强制)；格式漂移→修复非裸输；密度出口=真KDE raster工具
metadata: 
  node_type: memory
  type: project
  originSessionId: 34685879-1b3b-4dec-be44-2cdf88d14069
---

EMC（情绪地图 AI 问答）的回答策略最高纲领 = **三态出口契约**（2026-07-10 重构，落地于 `harness.js orchestrate`）：每次问答必落且仅落一种干净终态，**由 harness 代码裁定，非靠模型自觉**——
- **EXIT_RESULT 做成了**：intent∈{B操作,C情绪} 且 successObs>0 或 newLayerCount>0 → 数据驱动结论 + `{{focus/show/inspect}}` 操作按钮。
- **EXIT_GAP 做不成**：零成功+零新图层 → 确定性「缺数据卡」(`composeGapCard`，**不走 LLM**)，绝不编造/纯计划文。
- **EXIT_CONCEPT 纯问答**：intent=A → 直接答。
最高杠杆：intent∈{B,C} 零成功时**禁止**走叙述型 finalStep，直接 EXIT_GAP。

**Why**：用户反复报「只说不做」+ 把工具调用以 ```json 代码块糊进答案。根因不是策略缺失（prompt 里早有出口/诚实铁律），而是**只在 prompt 不在代码**——DeepSeek 格式漂移（`{action:"x",arguments:{}}`/prose 包裹 ```json```）→ parseAgentStep 返畸形 → 8 轮空转 → `onDegraded` 把**原始 token 糊进答案泡**（=用户看到的代码块）。

**How to apply**：
- 改 EMC 回答行为时，守「出口契约」——出口必须是「图层生成+结论」或「诚实缺数据卡」，**永不裸输原始 token**（`panel.js onDegraded` 是最终保险，已固定降级卡）。
- 解析层 `stages.js parseAgentStep` 是代码块泄漏的根治点：归一 drift schema + 入参别名（inverse→invert / output_layer→as / radius→radius_m，**解析期单源**）+ 纯叙述返 `{narrated:true}` 哨兵（harness 纠偏重发≤1 轮，不裸输）。改它须过格式漂移注入测试。
- 密度出口 = 真 KDE：`core/spatial_analysis.kde_raster`(F_005) + `api/geo_routes /geo/density` + 前端 `tools.js density`（离散分段色带 DENSITY_RAMP，2D 复用 map.js `isTool` 色带 fill 管线，tool='density'）。hotspot 也已修落图层（hot=红/cold=绿/ns=灰，复用离散 5 色极性）。
- 依赖：scipy/libpysal/esda（hotspot Gi* 与 KDE 共需，曾本机未装致两者都失败）。改 EMC 架构参考 `docs/ai-qa-design.md 第 5.5 章`。承重铁律勿碰（见 [[view-data-conclusion-sync]] / [[kde-loadbearing-logic]] / [[generate-grid-exclusive-vs-viewmode]]）。站在巨人肩膀上：CARTO「agent 失败是结构失败」+ QGIS Copilot「优雅交接」+ LLM-Geo/GISclaw「自调试+内联渲染」。
