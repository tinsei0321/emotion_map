# 99 - 生成脚本

## 文件
- `build_baidu_poi_catalog.py` — 百度 POI 体系生成器
- `build_yichang_poi.py` — 宜昌 POI 表格生成器

## 依赖
- Python 3.8+
- 仅标准库（json, csv, math, os, collections）

## 使用方法

### 1. 生成百度 POI 体系 JSON
```bash
python build_baidu_poi_catalog.py
```
输出：`../data/baidu-poi-catalog.json`

### 2. 生成宜昌精选 POI 表格
```bash
python build_yichang_poi.py
```
输出：
- `../02-yichang-poi-table/yichang-poi-table.md`
- `../02-yichang-poi-table/yichang-poi-table.csv`
- `../02-yichang-poi-table/yichang-poi-seed-rich.json`

## 自定义

### 修改 POI 列表
编辑 `build_yichang_poi.py` 中的 `YICHANG_POIS` 列表：
```python
YICHANG_POIS = [
    {"name": "新增 POI", "level1": "...", "level2": "...",
     "xy": [东向_米, 北向_米], "weight": 1.0, "domain": "...", "element": "...",
     "area": "...", "address_hint": "..."},
    ...
]
```

### 修改百度 POI 体系
编辑 `build_baidu_poi_catalog.py` 中的 `BAIDU_POI_CATALOG` 字典。

## 重新生成
修改后重跑脚本即可重新生成所有输出文件。
