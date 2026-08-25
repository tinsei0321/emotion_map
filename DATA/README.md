# DATA/ 目录规则（2026-08-25 重组）

> 单一权威：本文件 + `core/config.py`。改池语义先改这两处。

## 顶层目录

| 目录 | 语义 |
|---|---|
| `AUTHORITY/` | 权威范围/点/线数据（RAG 权威层；`boundaries_`/`points_`/`lines_` 前缀） |
| `THEME/` | 专题数据（`themes_point/polygon/line_主题_数量`；城市体检 + 12345 政务热线） |
| `RAG/` | RAG 索引与自成长记录（`rag_index/` + `ai_qa/`） |
| `REGISTRY/` | 预设注册表（`presets/manifest.json` 与图层文件；boundaries 已退休） |
| `RAW/` 或 `raw/` | 原始输入（购买/自采） |
| `SIM/` 或 `sim/` | 模拟数据 |
| `performance/` | 展演/演示池 |
| `POI/` | 地点/POI（`place/`、`baidu-heatpoints/`、`yichang_pois*`） |
| `Export/` | 分析导出与运行产物（`analysis/`、`processed/`、`exchange/`、`exports/`） |
| `_Retired/` | 退休/过时/错误/非数据格式/敏感数据（重复只留一份） |
| `others/` | 同文件名不同格式的副格式暂存（如 .geojson 与 .csv 同时存在时移 .csv） |

## 敏感数据红线

- 用地数据、建成区数据：不在 RAG/知识库保留；未来使用由用户一次性上传，不落盘、不记录。
- 当前已移入 `_Retired/敏感数据_用地建成区/`，待彻底删除。

## 旧路径 → 新路径映射（2026-08-25）

| 旧路径 | 新路径 | 说明 |
|---|---|---|
| `DATA/boundaries/presets/` | `DATA/REGISTRY/presets/` | 预设注册表（manifest + 图层文件） |
| `DATA/boundaries/现状水系.geojson` | `DATA/AUTHORITY/boundaries_现状水系.geojson` | 权威水系边界 |
| `DATA/boundaries/西陵伍家核心主城.geojson` | `DATA/AUTHORITY/boundaries_核心主城_西陵伍家_1.geojson` | 核心主城边界 |
| `DATA/analysis/体检对象_*` | `DATA/AUTHORITY/boundaries_*` / `points_*` | 权威边界/点 |
| `DATA/analysis/77项量化/checkup_qty_*` | `DATA/THEME/theme_城市体检/themes_point_checkup_*` | 城市体检专题点层 |
| `DATA/analysis/12345主观/` | `DATA/THEME/theme_城市体检/12345_政务热线_城市体检分析/` | 12345 城市体检派生 |
| `DATA/analysis/theme_12345政务热线/` | `DATA/THEME/theme_12345政务热线/` | 12345 专题（L0-L3） |
| `DATA/rag_index/`、`DATA/ai_qa/` | `DATA/RAG/rag_index/`、`DATA/RAG/ai_qa/` | RAG 索引与自成长记录 |
| `DATA/place/`、`DATA/baidu-heatpoints/` | `DATA/POI/place/`、`DATA/POI/baidu-heatpoints/` | POI 整合 |
| `DATA/analysis/`、`DATA/exchange/`、`DATA/processed/`、`DATA/exports/` | `DATA/Export/analysis/`、`DATA/Export/exchange/`、`DATA/Export/processed/`、`DATA/Export/exports/` | 导出与运行产物 |
| `DATA/old_data_processed/` | `DATA/_Retired/old_data_processed/` | 退休 |

## 代码常量（权威）

- `core/config.py`：`PROCESSED_DIR = DATA/Export/exports`、`PERFORMANCE_DIR = DATA/performance`。
- `core/range_selector.py`：`_BOUNDARIES_DIR = DATA/REGISTRY`、`_PRESETS_DIR = DATA/REGISTRY/presets`。
- `tools/rag_index.py`：`RAG_DIR = DATA/RAG/rag_index`。
- `ai_qa/episode.py`：`_EPISODE_DIR = DATA/RAG/ai_qa`。
- `core/place_layer.py`：place 数据 = `DATA/POI/place`，水系/主城 = `DATA/AUTHORITY`。
