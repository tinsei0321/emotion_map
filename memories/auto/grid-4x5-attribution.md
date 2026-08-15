---
name: grid-4x5-attribution
description: 4×5 归因在聚合层规则生成(domain_top/element_top/issue_label)；POI 已预映射 domain/element 直接读 seed
metadata: 
  node_type: memory
  type: project
  originSessionId: 763f315e-5f99-4d75-9826-b918ac7c6bfa
---

演示链"识别具体问题"环的数据底座（供 Task 2.7 popup/Overview 接入）。

**POI 已预映射**：amap POI 每条带 `domain`/`element`（0 缺失，4×5 多样铺开：governance×facility 交通市政、renewal×service 住宅、operation×environment 公园 等真实成簇）。`generate_l1_mock._seed_domain_element` 直接读 seed 字段做空间聚类。**勿用 `poi_4x5_map._L1_FALLBACK`**——其 key 是百度类名（"美食/购物"），高德实际类名（"餐饮服务/购物服务"）不匹配会全 fallback 到 `(operation,service)`。此缺口待修。

**聚合层 4×5**：`core/spatial_analysis.py` 的 `create_square_grid`/`create_terrain_mesh` 每格/环加 `domain_top`/`element_top`（众数）+ `n_dom_*`/`n_elem_*`（计数，前端除 point_count 得占比）。

**归因（DEMO 临时）**：`_ATTRIBUTION_RULES` + `lookup_attribution(domain, element, sign(pi))` 查表生成 `issue_label`/`attribution`/`suggestion`。**L3/L4 LLM 归因上线后删规则表**（用户要求清洗避免重复）。key 覆盖 POI 实际 7 组 domain×element × 正负。

**三层极性**（保叙事弧 `_check`）：arc 采样 + POI `POI_POLARITY_LEAN` 18% 翻转 + 对称拉伸（[[symmetric-norm-stretch]]）。归因字段在聚合产出层（非 L1/L2 per-point），清洗 = 后端不再生成。见 [[emotion-map-logic-chain]]。
