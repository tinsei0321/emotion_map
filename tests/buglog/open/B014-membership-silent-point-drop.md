---
id: B014
title: membership 值匹配静默丢点——异构属性点文件空值列触发整行丢弃（/spatial/aggregate 计数大错）
type: BUG
severity: HIGH
priority: P0
status: open
module: 数据识别
source: 用户实测
cb: CB-41
rootcause: ''
case_ref: ''
repro_count: 2
last_repro: 2026-08-18
---

## 标准化用例

**问句**：「体检两方面合并点做 174 社区聚合，为什么中间密集社区的点像没识别到（计数为零）？」(membership silent point drop on heterogeneous geojson)

**数据前提**：点层 = `checkup_qty_合并_全覆盖.geojson`（2296 点·**异构属性**——600 个楼栋类要素带 `社区/街办_源/楼栋_源` 列、1696 个不带）+ 面域 = 174 社区（名称列 `社区`）+ 工具 = grid「指定单元」（后端 `/spatial/aggregate`·`name_col=null` 自动推断）。

**预期行为**：
① membership 列有值 → 按值匹配聚合（CB-23 语义不变）；
② membership 列空值（NaN/''）→ 回退几何 sjoin（空值不含归属信息·几何是唯一依据·不得静默丢点）；
③ 空值且 `geocode_status=region` → 丢弃（质心坐标无定位意义·CB-23 区级点保护延续）；
④ 计数须与纯几何 sjoin 基准一致（2296 点 → sum 2283·非零 144·零点 30·TOP=五龙 112/润城 110/深圳路 107）。

## 已知失败模式

| # | 日期 | 表现 | 根因 |
|:-:|------|------|------|
| 1 | 08-18 | 用户实测：B013 修复后中央密集社区**完全无填充**（零点透明语义忠实暴露计数为零）；边缘浅黄=600 个带值点被正确匹配 | `aggregate_by_polygons` CB-23 快速路径：点带与面名称同名列即全量值匹配·空值行被 `isin` 整行丢弃（2296→600·136/174 社区清零·`/geo/zonal_stats` 因硬编码 `polygon_name_col='name'` 幸免·grid `/spatial/aggregate` `name_col=null` 自动推断 `社区` 必中） |
| 2 | 08-18 | zcode 离线复算钉死：from_features 联合列 vs read_file 差异·`find_boundary_name_column` boundary_name role 优先级使 `社区` 压过 `name` | 同上；08-12 CB-23 引入时未遇异构属性文件（12345 点 `社区` 列空值=区级点·当时语义巧合成立） |

## 修复记录

| 日期 | 操作 | commit |
|------|------|--------|
| 08-18 | CB-41 增补修复（zcode）：混合策略——值匹配（不变）+ 空值非 region 回退 sjoin（仅取面 geometry·防列污染）+ 空值 region 丢弃；真实数据验证 sum 2283/非零 144/TOP8=客观表头部逐字吻合；12345 民生基础 6487/148 社区与 5.251 口径一致；CB-23 老测试同步新规范（region 判别收紧为显式 `geocode_status` 标记）；pytest 全量 372 passed | 见 5.260（**待用户验收后关账**） |
