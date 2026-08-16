---
id: B012
title: 网格/地形悬停社区行张冠李戴——按格中心单点归属而非指针位置，跨界格显示邻居社区
type: BUG
severity: MED
priority: P1
status: open
module: UI
source: 用户实测
cb: CB-38
rootcause: ''
case_ref: ''
repro_count: 2
last_repro: 2026-08-16
---

## 标准化用例

**问句**：「鼠标悬停网格/地形层时，tip 社区行显示的社区为什么是错的？」(community tip wrong attribution on hover)

**数据前提**：任一 grid/terrain 分析层 + preset `checkup_cfg_community`（`DATA/boundaries/presets/checkup_配置_社区.geojson`·174 面·字段`社区`）；鼠标位于跨界格或大而扁的等值环范围。

**预期行为**：
① 指针处属于哪个社区，tip 社区行就显示哪个（指针语义，非格中心语义）；
② 跨界格/指针落格内另一社区时不得显示邻居社区名；
③ terrain 等值环的社区归属不得用 bbox 中心（可偏出数公里）。

## 已知失败模式

| # | 日期 | 表现 | 根因 |
|:-:|------|------|------|
| 1 | ~08 上旬 | 用户首次口头报告"社区 tip 错误"（无书面记录·本次补录） | 见下 |
| 2 | 08-16 | 五组实测：悬金安岭显望洲 / 竹涛山显宝联 / 常刘路显营盘 / 建设显港务 / 朝阳显石板 | `tip-popup.js:433-435 fillCommunity(centroidOf(feat))`：归属点=要素中心（grid=格中心`_center`·terrain=环bbox中心），非鼠标 lngLat；fillCommunity 遍历 174 面首命中即返。实测证据：五组配对全部相邻（shapely 共享边界）·400m 网格每对交界 4-5 个跨界格、归属随格中心落侧翻转；朝阳-石板（不相邻）由 terrain bbox 中心解释。数据侧已排除：174 面两两零重叠、全库无复合名 |

## 修复记录

| 日期 | 操作 | commit |
|------|------|--------|
| - | 待修复（CB-38 E1·方向候选：A 鼠标 lngLat 实时归属+空间索引节流 / B 跨界格并列显示 / C 现状+文案标注） | - |
