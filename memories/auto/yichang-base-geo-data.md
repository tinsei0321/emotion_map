---
name: yichang-base-geo-data
description: 宜昌基础地理信息数据资产（官方·2026-08-11 建立）——行政区划_官方（14县区/1682村社区/113街办）+ 12345 治理 + 项目端 gdb·未来可直接消费的底层数据·全局知晓
metadata: 
  node_type: memory
  type: project
  originSessionId: 39bfd82d-8d26-4166-80e7-aaa1fc2ce3b9
  modified: 2026-08-11T14:54:27.135Z
---

**宜昌基础地理信息数据**（2026-08-11 用户提供·官方准确·未来消费的底层数据·全局知晓其存在）：

1. **官方行政边界**（`02_空间数据集/行政区划_官方/`·用户提供 shp→WGS84）：
   - 市域县级 14 县区（EPSG:4525→4326）
   - 村社区 1682（94MB·reference_only 只引用·清单 CSV 150KB 含 lon/lat）
   - **SSX 聚合 113 街办**（中心城区 25 含 16 街办口径·含点军/猇亭）
   - presets：admin_street（113）/ admin_community（1682 引用）/ admin_county（14）
   - **消费**：geo_registry/range_selector → zonal/密度/落图（12345/体检/项目均可用街办 zonal·宝塔河 3066 已验证）

2. **12345 治理数据**（`06_主观数据治理/`·57265 行）：
   - 治理清洗版 + 情绪地图中转版（polarity 5级/score 0~1/4×5/topic/place/region_scope/cross_region）
   - `checkup_12345_2024` 层（DATA/performance·18171 有坐标·中心城区 77%）·PII 干净·噪声 0.05%
   - 4x5 映射 + 方法论（模拟数据黄金样本）

3. **项目端**（183 项目·十五五储备表 excel + 重点项目 gdb）：
   - gdb point185+line102=183·**gdb 只读**（用户明确勿动）·excel 匹配 99%
   - `checkup_project_point/line` 层（presets·含 TZE 投资额）

**Why**：用户 2026-08-11 强调「今天涉及很多宜昌市基础地理信息数据·都是未来可以直接消费的底层数据·需全局知晓」。这些是城市体检/更新/情绪分析的**底层基础设施**·跨会话、跨项目（宜昌专项规划）可复用。

**How to apply**：
- 分析/问答消费底层数据时：街办 zonal 用 admin_street（官方 113）·社区级用 admin_community（引用）·12345 用 checkup_12345_2024·项目用 checkup_project
- 街道=行政单元（≠道路·SSX 行政级）·术语统一「街办」
- 16 街办口径对齐表（体检 16 vs 官方 113·4 管理区高新区托管）·引用标注
- 数据源红线：中转站真实数据·sim 禁入

关联：[[checkup-exchange-layer]]（对接层）· [[checkup-spatial-location-caliber]]（铁律7）· [[street-vs-road-distinction]]（街道≠道路）
