# 情绪地图 - POI 数据包

> 宜昌市 POI 数据包，基于百度地图开放平台 POI 分类体系
>
> 用途：L1/L2 数据生成、POI 查询、4×5 矩阵映射
>
> 坐标系：EPSG:4547 (CGCS2000 / 3°GK zone 36 / CM 111°E)，米级
>
> 生成时间：2026-06-23

## 📁 目录结构

```
poi-package/
├── README.md                          # 本文件（入口）
│
├── 01-baidu-poi-catalog/              # 第 1 部分：百度 POI 完整体系
│   ├── README.md
│   └── baidu-poi-catalog.json         # 31 个一级 + ~200 个二级分类
│
├── 02-yichang-poi-table/              # 第 2 部分：宜昌精选 POI 表格
│   ├── README.md
│   ├── yichang-poi-table.md           # 详细 Markdown 表格
│   ├── yichang-poi-table.csv          # CSV（Excel 可打开）
│   └── yichang-poi-seed-rich.json     # 带坐标的 seed（可直接喂给生成器）
│
├── 03-4x5-matrix-mapping/             # 第 3 部分：4×5 矩阵映射
│   ├── README.md
│   └── poi-mapping-4x5.md             # POI → domain × element 完整映射
│
└── 99-scripts/                        # 生成脚本（Python 3.8+）
    ├── README.md
    ├── build_baidu_poi_catalog.py
    └── build_yichang_poi.py
```

## 🚀 快速使用

### 查看 POI 表格
打开 `02-yichang-poi-table/yichang-poi-table.md`（人类可读）或
`02-yichang-poi-table/yichang-poi-table.csv`（Excel 友好）

### 用 seed 重新生成 L1 模拟数据
```bash
# 复制 seed 到生成器期望的位置
cp 02-yichang-poi-table/yichang-poi-seed-rich.json ./poi-seeds.json

# 跑生成器
python 99-scripts/build_yichang_poi.py     # 重新生成 POI 表格
# （生成 L1 数据需要 emotion-map-L1 项目的生成器：generate_emotion_data.py）
```

### 看 4×5 矩阵怎么映射
打开 `03-4x5-matrix-mapping/poi-mapping-4x5.md`（含百度 API 接入代码示例）

## 📊 数据规模

| 指标 | 数值 |
|---|---|
| 百度 POI 一级分类总数 | 31 个 |
| 百度 POI 适用于宜昌的一级分类 | 17 个 |
| 百度 POI 二级分类总数 | 约 200 个 |
| 宜昌精选 POI 数量 | **158 条** |
| 二马路专项 POI 数量 | 16 条 |
| 4×5 矩阵覆盖 | 20 个组合全部覆盖 |

## 🎯 4×5 矩阵分布（宜昌精选）

| 领域\要素 | facility | environment | service | culture | event | 合计 |
|---|---|---|---|---|---|---|
| 城市规划(规划) | 4 | 0 | 6 | 1 | 0 | **11** |
| 城市更新(更新) | 4 | 0 | 5 | 22 | 0 | **31** |
| 城市运营(运营) | 2 | 11 | 50 | 1 | 9 | **73** |
| 城市治理(治理) | 33 | 0 | 10 | 0 | 0 | **43** |
| **合计** | 43 | 11 | 71 | 24 | 9 | **158** |

## 🔧 真实数据接入路径

1. **主数据源**：高德 POI（GCJ-02，免费额度宽松）
2. **补充数据源**：百度 POI（BD09，需企业认证）
3. **接入步骤**：
   - 拉 POI 列表（API）
   - 坐标系转换：原始 → WGS84 → CGCS2000 → EPSG:4547
   - 按 `03-4x5-matrix-mapping/poi-mapping-4x5.md` 映射 domain/element
   - 与 L1 评论数据 join

## 📝 版本

- **版本**：v1.0
- **数据来源**：
  - 百度地图开放平台 POI 分类（2024-04-18 版）
  - 宜昌市公开信息（商圈、景点、政府机构、医疗、教育等）
- **坐标系**：EPSG:4547
- **生成器**：固定随机种子，可重现

## 📞 联系

- 项目：情绪地图（L1/L2 模拟数据 + POI 体系）
- 文档版本：1.0
- 最后更新：2026-06-23
