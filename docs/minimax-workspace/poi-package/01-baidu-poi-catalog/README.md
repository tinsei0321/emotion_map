# 01 - 百度 POI 完整对照表

## 文件
- `baidu-poi-catalog.json`（12KB）

## 内容
- **31 个一级分类**：美食、酒店、购物、生活服务、丽人、旅游景点、休闲娱乐、运动健身、教育培训、文化传媒、医疗、汽车服务、交通设施、金融、房地产、公司企业、政府机构、出入口、自然地物、行政地标、门址、道路、铁路、行政界线、其他线要素、行政区划、水系、绿地、标注、公交线路、电子眼
- **约 200 个二级分类**：每个一级下的子分类
- **宜昌适用性标记**：哪些适用于宜昌场景

## 数据结构
```json
{
  "metadata": {
    "source": "百度地图开放平台 POI 分类",
    "source_url": "https://lbsyun.baidu.com/index.php?title=open/poitags",
    "version": "2024-04-18",
    "first_level_count": 31,
    "applicable_to_yichang_count": 17
  },
  "categories": {
    "美食": {
      "code": "catering",
      "secondary": ["中餐厅", "外国餐厅", ...],
      "secondary_count": 8,
      "weight_default": 0.30,
      "applicable_to_yichang": true
    },
    ...
  }
}
```

## 使用方式

### Python 读取
```python
import json
with open("baidu-poi-catalog.json", "r", encoding="utf-8") as f:
    catalog = json.load(f)

# 列出所有适用于宜昌的一级分类
applicable = [name for name, cfg in catalog["categories"].items()
              if cfg["applicable_to_yichang"]]
print(applicable)
# ['美食', '酒店', '购物', '生活服务', '丽人', '旅游景点', '休闲娱乐', ...]

# 列出"美食"下的所有二级分类
food_subs = catalog["categories"]["美食"]["secondary"]
print(food_subs)
# ['中餐厅', '外国餐厅', '小吃快餐店', '蛋糕甜品店', '咖啡厅', '茶座', '酒吧', '其他']
```

## 适用场景
- POI 分类标准化对照表
- 接入百度/高德 API 时的字段映射参考
- 模拟数据生成时的分类体系基础
- 4×5 矩阵归属判断（详见 `../03-4x5-matrix-mapping/`）
