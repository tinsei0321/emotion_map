# DATA/ 入库与归位规则（CB-39 A2·D2 数据池归一）

> 单一权威：本文件 + `core/config.py` 常量。改池语义先改这两处。

| 目录 | 语义 | 入库 | 红线 |
|---|---|---|---|
| `raw/` | 原始输入（购买/自采） | 按来源定（`baidu-heatpoints/`、`raw/landuse/` 已忽略） | 许可与隐私边界随源 |
| `analysis/` | **紧急任务真实数据归集根**（体检/12345/更新素材·CB-39 阶段0 起） | **入库**（93+ 件已全量追踪） | sim 禁入；geojson/xlsx 禁入 RAG（只进口径卡） |
| `performance/` | **演示池**（sim 演进最终版 L1/L2/L3L4·T1-T3） | **入库**（家/办同步） | **真实数据禁入**（E16 后仅剩 sim·时间轴分轴物理前提） |
| `exports/` | 新分析导出（运行产物·可重算） | **不入库**（.gitignore） | 演示最终版有意入库时移 `performance/` 并登记 |
| `boundaries/` | 空间边界 + presets 图层注册（manifest 单点） | 入库（`社区.geojson` 87MB 例外只引用） | 注册走 presets manifest·勿散放 |
| `exchange/` | G 盘中转站对接层（reference-only 溯源） | manifest 入库·大文件只引用 | PII 层只引用不复制（building_50year_1） |

## 迁移记录

- 2026-08-16（CB-39 A2/E16）：`performance/` 内 9 个真实数据文件迁出——`checkup_12345_2024.csv` 等 6 件归位 `analysis/` 各数据族；3 件同名版本对（社区占比表/11类矩阵/事件类型）暂留原位待 B2 对账裁决。旧空目录 `DATA/processed/` 已删除（07-24 手工迁移遗留）。
