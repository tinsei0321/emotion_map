---
name: emc-domain-lens-threading
description: EMC diagnose 卡的结构化字段（domain_lens 等）被前端压扁进 ctx.context 丢失；下游要结构化用须显式回传 ChatRequest + threading，别从 context 串正则抠
metadata: 
  node_type: memory
  type: project
  originSessionId: ddcf998d-bff8-4d35-8f23-96f37914a184
---

EMC diagnose 卡（8 字段 JSON）产出后，前端 `harness.js` 的 `formatDiagnoseSummary` 把 **domain_lens 数组压扁成中文标签串** `domain=城市规划/城市更新` 前插进 `ctx.context`，所有后续 phase（agent/answer/review/revise）只看到这个压扁串。**结构化数组本身从不回传后端**——`ChatRequest` 原无此字段，后端 prompt builder 签名也无此参数。

**④（5.108, 2026-07-16）的修法范式**（未来其他 diagnose 卡字段要结构化复用时照此）：
- 前端：`ctx.domainLens = diagnose.domain_lens`（orchestrate 内 diagnose 后设一次，过滤 'general'）→ 各 step streamChat opts 加 `domainLens: ctx.domainLens` → `api.js` body 加 `domain_lens`。
- 后端：`ChatRequest` 加 `domain_lens` 字段 → `router.py` 各 phase 透传 → `build_*_prompt`/`_build_review_prompt` 加 `domain_lens` 参，调 `industry_kb_lens_appendix(domain_lens)` 拼附录。

**Why**：diagnose 卡字段（scale/decision_type/outlet 等）同理都会被压扁；若下游要结构化用，**唯一干净路径 = 加请求 schema 字段 + 显式 threading**，别从 ctx.context 串正则抠（fragile）。

**How to apply**：注入完整权威语境只在 post-diagnose step（agent/answer/revise/review）；**diagnose prompt 永远不动**（它产 lens + 已有 brief 全 4 域速查，改它伤 Flash eval 95%）。helper 放 `industry_kb` 公共位（非 prompts 私有），避私有跨模块 import + 无环。复用范式照 `build_diagnose_prompt` 拼 brief 附录（`.format()` 后纯字符串拼接，花括号安全）。

相关：[[emc-eval-empty-context-vs-runtime]]（eval 空 context 不模拟已加载层/卡字段，验回答层注入须 browser/probe 非 eval）、[[emc-delegates-to-toolbox]]。
