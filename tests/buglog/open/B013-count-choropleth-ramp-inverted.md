---
id: B013
title: L0 点层聚合 choropleth 色带反语义——点数越多颜色越浅、零点社区落最深红
type: BUG
severity: HIGH
priority: P1
status: open
module: UI
source: 用户实测
cb: CB-41
rootcause: ''
case_ref: ''
repro_count: 2
last_repro: 2026-08-18
---

## 标准化用例

**问句**：「城市体检点（民生+安全两方面合并）聚合到 174 社区，为什么点数密集的社区颜色反而浅？」(L0 count choropleth inverted ramp)

**数据前提**：点层 = `DATA/analysis/77项量化/checkup_qty_合并_全覆盖.geojson`（2296 点·属性仅 指标/中类/board/类/来源·无极性无 score·L0）+ 聚合面域 = 预设 `checkup_cfg_community174`（174 社区）。

**预期行为**：
① 点数越多颜色越深（用户语义：问题点密集 = 重灾区 = 深色）；
② 零点社区不得落最深色端（无数据 ≠ 最严重，30/174 社区零点）；
③ 图例/口径文字与数值语义一致（点数档），不得显示情绪「负面/中性/正面」。

## 已知失败模式

| # | 日期 | 表现 | 根因 |
|:-:|------|------|------|
| 1 | ~08 中旬 | 用户觉得默认「高浅黄低深红」怪（CB-23 加 reverse 开关·默认仍不反转） | `grid-tool.js gridStyle`：L0/L1 走 grid-warm（暗红→金黄·高值端=浅金）+ `_grid_h` 点数高度字段 |
| 2 | 08-18 | 体检两方面合并点 174 社区聚合：中央密集社区浅金、边缘稀疏/零点社区深红 | 同上（`grid-tool.js:81-88` + `preprocessGrid` `_grid_h`）·零点 `_grid_h=0` → 钳到色带 0 端 #8B0000 最深红 |
| 3 | 08-18 | 5.259 修复后用户复测：中央密集社区**完全无填充**（非浅色）——零点透明语义忠实暴露 | **B014**（计数根因非着色）：`/spatial/aggregate` membership 值匹配静默丢点 1696/2296·中央社区计数全零·详见 `B014-membership-silent-point-drop.md` |

## 修复记录

| 日期 | 操作 | commit |
|------|------|--------|
| 08-18 | CB-41 实施修复（zcode）：① grid 对话框「着色语义」显式分叉（点数(临时)/极性·默认随数据轨 L0/L1→点数·L2→极性·手选锁定）② `_count_norm=log1p(pc)/log1p(max)` 计数着色·grid-warm 反转（低浅高深·点数越多越深）③ 零点面域透明不填色（`zeroIsNoData` case 特判）④ zonal-tool UI 自动分叉（rows 无极性→点数·toast 提示）⑤ 图例/层名/tip 指标行点数模式适配 ⑥ ForAI 契约零变化（generateGridForAI 不传 semantic=旧行为）·新测 `tests/test_zonal_count_semantic.py` 3 passed | `126537eb`（**待用户验收后关账**） |
