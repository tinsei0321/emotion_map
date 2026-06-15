# core/ — 基础设施层 CLAUDE.md

> 优先级: 本文件 > 项目根 CLAUDE.md > 全局 CLAUDE.md

## 模块职责

提供全局基础设施：配置、数据加载、坐标转换、导出、地图引擎、范围选择、追踪系统、UI 组件。

## 文件清单

| 文件 | 职责 | 修改门槛 |
|------|------|----------|
| `config.py` | 全局常量（天地图Key、路径、阈值、颜色映射） | 低（配置变更） |
| `tracker.py` | 决策追踪系统（@track/TrackContext/trace_*） | **高（基础设施，必须 SOP）** |
| `data_loader.py` | 统一数据加载入口 | 中 |
| `export.py` | CSV/GeoJSON 导出 | 中 |
| `coord_transform.py` | GCJ-02↔WGS84 数学转换 | 中 |
| `map_engine.py` | Folium 底图 + 标记 + 热力 + 边界 | 中 |
| `range_selector.py` | 范围 Shapefile 加载 + CRS 检测 | 中 |
| `ui_components.py` | Streamlit 可复用 UI 组件 | 低（UI 调整） |

## 配置规范

- `config.py` 中所有路径使用 `PROJECT_ROOT` 相对路径
- 天地图 Key 硬编码在 `config.py`（非敏感，前端可公开）
- 颜色映射 `POLARITY_RGBA` 五级对应五级极性
- 新增配置项必须加注释说明用途
- API Key 绝不出现在 `config.py`（使用 `.env`）

## 追踪系统规范 (core/tracker.py)

- 模块 ID: `MOD_TRACKER`
- 追踪 ID 格式: `MOD_XXX.F_NNN`（函数）或 `MOD_XXX.D_NNN`（决策分支）
- 编号必须连续，不跳号
- 新增追踪 ID 必须同步更新注册表 `_REGISTRY`
- 不删除已有追踪 ID（保留兼容性）

## 坐标转换规范 (core/coord_transform.py)

- GCJ-02→WGS84: 数学转换（约 100-700m 偏移）
- 不做 BD-09→WGS84（百度坐标极少使用）
- 输出始终为 WGS84 EPSG:4326（地图渲染基准）

## 导出规范 (core/export.py)

- CSV: UTF-8 BOM 编码（`utf-8-sig`），Excel 兼容
- GeoJSON: UTF-8，CRS 标记为 `urn:ogc:def:crs:OGC:1.3:CRS84`
- 导出文件名格式: `{name}_{phase}_result_csv.csv` / `{name}_{phase}_result_geojson.geojson`

## 禁止事项

- 不要修改 `tracker.py` 的 `@track()` 装饰器签名
- 不要在 `config.py` 中存储 API Key 或敏感信息
- 不要修改坐标转换算法的数学常量
- 不要删除 `_REGISTRY` 中已注册的追踪 ID
- 不要硬编码文件路径（使用 `config.py` 中的路径常量）
