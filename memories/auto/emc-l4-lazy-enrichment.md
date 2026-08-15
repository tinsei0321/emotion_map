---
name: emc-l4-lazy-enrichment
description: L4 多维归因=规则底不动 + lazy LLM enrichment（非 eager）；/aiqa/deep_attribution + MOD_AIQA.F_007；低置信回退规则
metadata: 
  node_type: memory
  type: project
  originSessionId: 7df3929a-b2fc-4538-b199-255debff9d54
---

L4 深度归因（政策→情绪→项目闭环）= **lazy enrichment**：aggregate（zonal/grid/by_boundary_id）的规则归因 `_attach_4x5_attrs`（spatial_analysis.py，按 domain×element 查表产 issue_label/attribution/suggestion）**零改动**；L4 是按需叠层——EMC 深读某簇时 `deep_read_attribution` 工具（tools.js）调 `POST /aiqa/deep_attribution`（aiqa_routes.py）→ `build_deep_attribution_prompt`（prompts.py, **MOD_AIQA.F_007**）拼簇评论+规则底+`industry_kb_text(domain)` → `chat_with_fallback`(flash+json_mode) 出 `{deep_attribution, policy_link, project_link, confidence, blind_spot}`；confidence<0.5/LLM 断 → `_deep_attribution_fallback` 回退规则底（degraded）。**否决 eager**（每 aggregate 跑 LLM 太贵+拖慢）。

**Why:** eager L4 会让每次 zonal/grid 聚合都跑 LLM（成本+延迟），且 aggregate 是承重路径不能动；lazy 只在用户深读某簇时触发，规则底始终在保零回归。

**How to apply:**
- **勿让 L4 变 eager**——L4 只走 `/aiqa/deep_attribution` 按需触发，不进 aggregate/zonal_stats/grid。
- **勿动 `_attach_4x5_attrs` 规则归因**——它是 L4 的 base + 兜底；L4 低置信回退到它。
- **diagnose prompt 永不动保 Flash eval**——L4 改的是 agent prompt 工具目录（加 deep_read_attribution）+ 新 prompt builder，不碰 build_diagnose_prompt/TEMPLATE_REGISTRY/select_template。
- deep_read_attribution 收集 Sim 富归因数据的 L4 种子（policy_seed/project_seed/aspect_primary）作 hints → prompt「优先采用」权威锚（见 [[sim-research-buffer-methodology]]）。普通 L2 无种子→hints 空→退原行为。
- event 要素（赛事/节庆）给瞬时空间影响归因（官方体检按日均忽视的盲区=EMC 差异化价值）。
