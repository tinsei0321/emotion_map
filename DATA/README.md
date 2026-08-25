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
