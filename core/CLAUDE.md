# core/ — 基础设施层 CLAUDE.md

> 优先级: 本文件 > 项目根 CLAUDE.md > 全局 CLAUDE.md

## 模块职责

提供全局基础设施：配置、数据加载、坐标转换、导出、范围选择、追踪系统（map_engine/ui_components 已于 CB-01 退役）。

## 文件清单

| 文件 | 职责 | 修改门槛 |
|------|------|----------|
| `config.py` | 全局常量（天地图Key、路径、阈值、颜色映射） | 低（配置变更） |
| `tracker.py` | 决策追踪系统（@track/TrackContext/trace_*） | **高（基础设施，必须 SOP）** |
| `data_loader.py` | 统一数据加载入口 | 中 |
| `export.py` | CSV/GeoJSON 导出 | 中 |
| `coord_transform.py` | GCJ-02↔WGS84 数学转换 | 中 |
| `range_selector.py` | 范围 Shapefile 加载 + CRS 检测 | 中 |

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
- 新增追踪 ID 必须同步更新注册表 `_TRACKING_REGISTRY`
- 不删除已有追踪 ID（保留兼容性）

## 坐标转换规范 (core/coord_transform.py)

### 双源输入策略（宜昌专项）

```
数据源 A：社交媒体（地理坐标系）          数据源 B：规划数据（投影坐标系）
  GCJ-02 / WGS84 / BD-09                   CGCS2000 投影（EPSG:4546 / 4547 / 4548）
        ↓                                        ↓
  coord_transform.gcj02_to_wgs84()          pyproj.Transformer 逆投影
        ↓                                        ↓
               WGS84 (EPSG:4326) ← 统一中转基准
                        ↓
              按需投影 → CGCS2000 EPSG:4546 (宜昌 CM 111E)
                        → 或保持 WGS84 用于 pydeck 地图渲染
```

### 宜昌标准

| 参数 | 值 |
|------|-----|
| 目标投影 | CGCS2000 3-degree Gauss-Kruger |
| 中央经线 (CM) | **111°E**（宜昌所在 3° 带） |
| EPSG | **4546** |
| 备用 EPSG | 4547 (CM 114E)、4548 (CM 117E) — 省内其他城市 |
| 地图渲染 | WGS84 EPSG:4326 |
| 规划数据基准 | CGCS2000 EPSG:4546（米制，精度 < 1m） |

### 转换策略

- **原则**：不假设输入坐标系，始终检测并显式转换
- GCJ-02→WGS84: 数学转换（约 100-700m 偏移），`core/coord_transform.py`
- WGS84→CGCS2000: `pyproj.Transformer`（厘米级精度）
- CGCS2000→WGS84: 逆变换，用于规划数据叠加到地图
- BD-09→WGS84: 暂不实现（百度坐标极少见于城市规划场景）
- **灵活原则**：规划数据可能自带不同的投影参数（CM 可能不是 111E），模块需支持自定义 EPSG 输入

## 导出规范 (core/export.py)

- CSV: UTF-8 BOM 编码（`utf-8-sig`），Excel 兼容
- GeoJSON: UTF-8，CRS 标记为 `urn:ogc:def:crs:OGC:1.3:CRS84`
- 导出文件名格式: `{name}_{phase}_result_csv.csv` / `{name}_{phase}_result_geojson.geojson`

## 禁止事项

- 不要修改 `tracker.py` 的 `@track()` 装饰器签名
- 不要在 `config.py` 中存储 API Key 或敏感信息
- 不要修改坐标转换算法的数学常量
- 不要删除 `_TRACKING_REGISTRY` 中已注册的追踪 ID
- 不要硬编码文件路径（使用 `config.py` 中的路径常量）
