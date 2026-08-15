---
name: emc-aggregate-column-alias-silent-zero
description: "aggregate 系列硬编码英文列名 gate（if 'polarity' in cols）遇中文别名静默跳过→polarity_index 静默零/domain_top 静默空；加 aggregate stat 须 resolve_field_alias 解析列，输出保规范名"
metadata: 
  node_type: memory
  type: project
  originSessionId: ddcf998d-bff8-4d35-8f23-96f37914a184
---

EMC `core/spatial_analysis.py` 的 aggregate 系列曾硬编码英文 schema 列名 gate：`if 'polarity' in joined.columns` / `if 'domain' in joined.columns`。**这是字面字符串匹配列名，不是 role 查询**——上传层列叫中文别名（情绪/领域/要素/sentiment）时，gate 为 False，整段统计**静默跳过**：polarity_index 静默全 0、domain_top/element_top 静默空、4×5 归因全走兜底。历史同类 bug 记录在 spatial_analysis.py:243 注释。

**修法（⑤② 5.109 已落，2026-07-16）**：用 `resolve_field_alias(role, joined.columns)`（core/field_dictionary.py）拿**实际列名**去读（可能是 '情绪'），**输出仍用规范名**（polarity_index/domain_top/n_dom_*）保前端契约。`resolve_field_alias` 精确命中优先 → 规范列名零回归，别名是额外启用。4 孤岛：aggregate_by_polygons / _attach_4x5_attrs（aggregate+square_grid 共享）/ create_hex_grid / create_square_grid。

**How to apply（future 加 aggregate stat 必守）**：
- 新加按列统计（groupby mode/mean/count），**列名先过 `resolve_field_alias(role, cols)`**，别硬编码字面列名——否则上传别名层静默错值（最阴险的 bug 类：不报错、不出数）。
- 输出 stat 名用**规范 role 名**（前端契约读 polarity_index/domain_top/score_mean），别用解析出的实际列名拼（'得分_mean' 会破前端）。
- **score/emotion_intensity/l1_confidence 的 mean 仍硬编码**（⑤② 未改，缺失=graceful degradation 非静默错值）；若以后要别名化，注意输出名问题。
- ⑤③ popularity（5.110）：category_top（众数，值域自定义故只 mode 不枚举）+ ts_peak_hour（datetime 解析），同 resolve_field_alias 范式。

相关：[[spatial-aggregation-numeric-coerce]]（groupby mean 前 to_numeric(coerce)，别名列不在 agg_cols 默认里不会 coerce）、[[emc-domain-lens-threading]]。
