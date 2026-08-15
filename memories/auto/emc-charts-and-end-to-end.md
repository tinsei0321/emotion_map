---
name: emc-charts-and-end-to-end
description: "EMC 答案内图表({{chart:TYPE|..}}→Chart.js)；端到端升级 Phase1(图表)已完，Phase2 DataEye/Phase3 复合工具+报告待做；.format 花括号陷阱"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5427afe1-8eef-46a1-872f-0c031aea6d9a
---

EMC「略复杂任务端到端、超越同行」升级（2026-07-10 起），对标开源 AI+GIS agent。

**Phase 1 图表生成（已完，5.67）**：答案里 `{{chart:TYPE|title=..|x=标签,逗号|y=数值,逗号}}` → Chart.js 柱/折/饼（bar=排序对比 / line=时序T1→T3 / pie/doughnut=占比）。实现于 [panel.js](frontend/js/ai_qa/panel.js) `_renderCharts`（挂 `enhanceCodeBlocks` 末尾，覆盖所有 renderAnswer 站点）+ Chart.js@4 CDN（index.html）+ FINAL_TEMPLATE 教模型出图。离散配色（[[ramp-discrete-segments]]）。

**两个花括号陷阱（必记，下次改 chart/focus 模板时）**：
1. **`.format()` 吞一层括号**：FINAL_TEMPLATE 经 `str.format` 后 `{{chart}}`→`{chart}`（单括号）喂模型。故 `_renderCharts` 正则**兼容 1~2 花括号** `\{{1,2}chart:...\}{1,2}`。现有 `{{focus}}` 同样有此隐患（模型可能输出单括号，前端双括号正则匹配不到——latent bug，未修）。
2. **bad 规格防嵌套**：畸形 `{{chart:bogus}}` 的 fallback 文本若含 `{{chart:}}` 会被二次正则匹配→嵌套 `<code>`。解法：bad 文本用 HTML 实体 `&#123;&#123;chart:` 编码花括号，正则（匹字面 `{`）不再匹配。

**Phase 2 DataEye 深化（2026-07-12 已完，5.69）**：[tools.js buildContext](frontend/js/ai_qa/tools.js) 新增 `_fieldSamples(fc)`——层摘要从"字段名"升级到"字段=类型:2 样本值"（`DLMC=str:商业`/`polarity_index=num:0.32|-0.45`），borrow GIS Copilot。模型写 where 有真实值参照。实测 buildContext 输出含样本值。

**Phase 3 复合工具+报告导出（报告 2026-07-12 已完，5.69；复合工具 compare/timeseries 仍待做）**：报告导出 = [panel.js _exportReport](frontend/js/ai_qa/panel.js)——答案脚"导出报告"钮 → 拼自包含可打印 HTML（标题+时间+问题+答案[canvas→`toDataURL` PNG]+落款，CSS 藏 action 按钮）→ 新窗 `print()` 存 PDF。实测生成 21.8KB HTML 含图表 PNG。复合工具 compare/timeseries（后端 geo_routes+spatial_analysis + tools.js）仍未做。

**Phase 4 未来**：tool-doc RAG（FAISS 检索工具文档替代 prompt 塞满，GIS Copilot 路，工具数翻倍再做）+ code-gen kernel。

**研究基础**（站在巨人肩膀上）：GIS Copilot/SpatialAnalysisAgent（DataEye 抽字段+样本值+CRS、tool-doc RAG、SmartDebugger、code-gen kernel、任务 L1/L2/L3 分级）；LLM-Geo/GISclaw（autonomous GIS=LLM 大脑+工作流规划+代码生成+自调试）；GeoGPT（三-agent tool-agent 架构）；ChartGPT（NL→图）；CARTO（把每步显式呈现建信任）。用户上传的 `docs/mapgpt-main` = 纯营销页无代码可 copy，印证缺图表+报告方向，**读完即删不入仓**。

**承重勿碰**：三态出口契约（[[emc-tri-state-exit-contract]]）/ 视野-数据-结论同步 / KDE cascade-exclude / 4×5 / 对称拉伸 / tip-popup / EMC 深色。图表纯增量（新模板+后处理器），不动渲染管线。
