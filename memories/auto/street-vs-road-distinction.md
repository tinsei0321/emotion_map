---
name: street-vs-road-distinction
description: 街道（办）≠道路——街道=行政区划级别(含若干社区)·道路=交通线；12345/行政数据里「街道」指行政单元
metadata: 
  node_type: memory
  type: reference
  originSessionId: 39bfd82d-8d26-4166-80e7-aaa1fc2ce3b9
  modified: 2026-08-11T13:55:50.662Z
---

**街道（办）≠ 道路**（用户 2026-08-11 提示·城市规划/行政术语）：

- **街道（办）** = 行政区划中的一个级别（乡镇级·如西陵区云集街办）·一个街道通常包含若干个社区·是**行政单元**（做 zonal/社区归属/统计用）。
- **道路** = 交通基础设施（如二马路/兴润路·LineString）·与街道无关。

**How to apply**：
- 数据字段 `SSX`（村社区层）=`街道/镇/办事处` 行政级·聚合出的 `admin_street` = 街道办行政面（含若干社区）·非道路。
- 12345/体检数据里「街道」指行政单元·「道路」指交通线（乱停乱放 4 条路等）·分析/文档区分。
- zonal/聚合按街道办行政面·不把道路线当街道。

关联：[[checkup-spatial-location-caliber]]（空间落位口径）
