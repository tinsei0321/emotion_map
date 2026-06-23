# 02 - 宜昌精选 POI 表格

## 文件
| 文件 | 大小 | 说明 |
|---|---|---|
| `yichang-poi-table.md` | ~25KB | 详细 Markdown 表格（带统计、二马路专项） |
| `yichang-poi-table.csv` | ~22KB | CSV 格式，Excel 可直接打开 |
| `yichang-poi-seed-rich.json` | ~63KB | 带 EPSG:4547 坐标的 seed（可喂给 L1 生成器） |

## 内容概览
- **158 条**宜昌核心主城（西陵区 + 伍家岗区）真实 POI
- **16 条**二马路历史街区专项 POI
- 每条包含：百度一级/二级分类、坐标、采样权重、4×5 矩阵归属
- 覆盖 16 个百度一级分类、4 个 domain、5 个 element

## 字段说明

| 字段 | 说明 |
|---|---|
| `id` | `yc_poi_000` ~ `yc_poi_157` |
| `name` | POI 中文名 |
| `baidu_level1` | 百度一级分类 |
| `baidu_level2` | 百度二级分类 |
| `xy_y_m` | Y_东向_米（EPSG:4547） |
| `xy_x_m` | X_北向_米（EPSG:4547） |
| `weight` | 采样权重（0.3 ~ 2.5，越高密度越大） |
| `domain` | urban_planning / urban_renewal / urban_operation / urban_governance |
| `element` | facility / environment / service / culture / event |
| `area` | 自定义区域标签（西陵-CBD、伍家-万达 等） |
| `address_hint` | 地址提示 |
| `radius_m` | 影响半径（默认 300m） |

## 使用方式

### 方式 1：作为 L1 模拟数据的 seed
```bash
# 复制到生成器期望的位置
cp yichang-poi-seed-rich.json ../poi-seeds.json
python ../99-scripts/build_yichang_poi.py
```

### 方式 2：Python 加载
```python
import json
with open("yichang-poi-seed-rich.json", "r", encoding="utf-8") as f:
    seed = json.load(f)

# 获取所有"二马路专项"POI
ermalu = [p for p in seed["pois"]
          if "二马路" in p["area"] or "大南门" in p["area"]
          or "红星路" in p["area"] or "献福路" in p["area"]]
print(f"二马路 POI 数量: {len(ermalu)}")
```

### 方式 3：Excel 查看
直接双击 `yichang-poi-table.csv`，所有字段一目了然，可筛选/排序。

## 重点 POI（精选）

### 二马路历史街区（16 条）
- **历史建筑**：大南门、文庙、古佛寺、大南门 5 号历史建筑
- **老字号**：二马路老茶馆、九码头、陶然居、老宜昌
- **居住区**：二马路老社区、二马路 1 号院落、红星路 12 号民居
- **文创**：二马路非遗工坊、二马路 18 号文创店
- **政务**：西陵区市民服务中心、二马路改造指挥部
- **社区**：献福路社区中心、大南门老茶馆（网红）

### 核心商圈（17 条）
- **CBD**：万达广场、兴发广场、卓悦广场、水悦城、太古里
- **步行街**：解放路步行街、铁路坝商圈
- **百货**：国贸大厦、大洋百货、新世纪百货、雅斯百货
- **超市**：北山超市、东方超市、悦活里

### 公共服务（30+ 条）
- **政府**：市民中心、西陵区政府、伍家岗区政府
- **医疗**：中心医院、一医院、二医院、中医医院、伍家医院
- **教育**：三峡大学、宜昌一中、夷陵中学
- **交通**：宜昌站、宜昌东站、BRT 站、加油站

### 文旅景点（14 条）
- **公园**：滨江公园、东山公园、磨基山、儿童公园
- **文化**：三峡博物馆、规划展览馆、美术馆、图书馆
- **历史**：镇江阁、西陵剧场
