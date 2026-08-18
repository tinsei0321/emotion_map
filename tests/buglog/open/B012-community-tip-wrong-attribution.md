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
repro_count: 3
last_repro: 2026-08-18
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
| 3 | 08-18 | 指定单元（社区面）聚合场景全量复算：174 社区中 **34 个** bbox 中心归属错名（22 显邻居名 + 12 无归属·建设→港务/朝阳路→石板/金安岭→望洲/五龙↔梅子溪互串 等·含多个两表头部社区），#2 五组全部复现在列 | 同 #2；社区面要素无 `_center` → `centroidOf` 退化 bbox 中心。精确 34 社区清单与复算脚本见 CB-41 发起文档 |

## 修复记录

| 日期 | 操作 | commit |
|------|------|--------|
| 08-18 | CB-41 实施修复（zcode·组合方案）：① 聚合社区面层（grid analysis=zonal / zonal 层）tip 社区行**直读 `feature.properties.name`**（零查找·与 Table 同源·34/174 错配根治）② 标准网格/terrain 社区归属改**鼠标 lngLat 实时空间归属**（原=要素中心·B012 机制源头）+ 指针位移 <4px 节流 ③ point 分支早退前清空 `#tp-community`（dsh 发现的残留连带） | `126537eb`（**待用户验收后关账**） |
