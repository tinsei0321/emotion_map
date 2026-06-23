# 4×5 矩阵 × 百度 POI 映射建议

> 适用于情绪地图项目：把百度 POI 分类映射到 4 个领域（规划/更新/运营/治理）× 5 类要素（设施/环境/服务/文化/事件）
>
> 用于：L1 数据生成时根据 POI 类别自动判定 domain × element 归属
>
> 来源：百度地图开放平台 POI 分类（2024-04-18 版）+ 情绪地图项目场景

---

## 1. 4×5 矩阵总览

| 领域 \ 要素 | facility 设施 | environment 环境 | service 服务（功能） | culture 文化 | event 事件 |
|---|---|---|---|---|---|
| **urban_planning** 城市规划(设计) | 控规调整中的设施 | 规划中的绿地/水系 | 控规配套服务 | 规划中历史保护 | 规划公示/听证 |
| **urban_renewal** 城市更新 | 老旧改造施工 | 改造后环境提升 | 改造后便民服务 | 历史街区/工业遗存 | 改造进展/居民反应 |
| **urban_operation** 城市运营 | 运营期设施维护 | 日常环境 | 商业/政务/医疗/教育 | 文旅/节庆 | 夜经济/市集/赛事 |
| **urban_governance** 城市治理 | 公共设施投诉 | 污染/噪声/防汛 | 政务投诉/服务效率 | 文化执法 | 应急/舆情/群访 |

---

## 2. 百度 POI 二级分类 → 4×5 归属 完整映射

### 2.1 美食
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 中餐厅 | urban_operation | service | 日常商业运营 |
| 外国餐厅 | urban_operation | service | 商业运营 |
| 小吃快餐店 | urban_operation | service | 商业运营 |
| 蛋糕甜品店 | urban_operation | service | 商业运营 |
| 咖啡厅 | urban_operation | culture | 文化/休闲属性更强 |
| 茶座 | urban_operation / urban_renewal | culture | 老字号茶座偏向更新/文化 |
| 酒吧 | urban_operation | event | 夜经济属性 |
| 其他 | urban_operation | service | 兜底 |

### 2.2 酒店
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 星级酒店 | urban_operation | service | 城市服务 |
| 快捷酒店 | urban_operation | service | 商业运营 |
| 公寓式酒店 | urban_operation | service | 商业运营 |
| 民宿 | urban_renewal | culture | 民宿多为历史街区改造 |
| 其他 | urban_operation | service | 兜底 |

### 2.3 购物
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 购物中心 | urban_operation | event | 商业综合体含事件属性 |
| 百货商场 | urban_operation | service | 商业服务 |
| 超市 | urban_operation | service | 便民服务 |
| 便利店 | urban_operation | service | 便民服务 |
| 家居建材 | urban_renewal | facility | 改造相关 |
| 家电数码 | urban_operation | service | 商业服务 |
| 商铺 | urban_operation / urban_renewal | service / culture | 老街区商铺偏更新 |
| 市场 | urban_operation | service | 集贸/菜市场 |
| 其他 | urban_operation | service | 兜底 |

### 2.4 生活服务
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 通讯营业厅 | urban_operation | service | 便民 |
| 邮局 | urban_operation | service | 公共服务 |
| 物流公司 | urban_operation | service | 物流运营 |
| 售票处 | urban_operation | service | 服务 |
| 洗衣店 | urban_operation | service | 便民 |
| 图文快印店 | urban_operation | service | 便民 |
| 照相馆 | urban_operation | service | 便民 |
| 房产中介机构 | urban_renewal | service | 与更新强相关 |
| 公用事业 | urban_governance | facility | 治理类 |
| 维修点 | urban_operation | service | 便民 |
| 家政服务 | urban_operation | service | 便民 |
| 殡葬服务 | urban_operation | service | 服务 |
| 彩票销售点 | urban_operation | service | 服务 |
| 宠物服务 | urban_operation | service | 服务 |
| 报刊亭 | urban_operation | service | 服务 |
| 公共厕所 | urban_governance | facility | 公共设施 |
| 步骑行专用道驿站 | urban_operation | facility | 设施 |
| 其他 | urban_operation | service | 兜底 |

### 2.5 丽人
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 美容 | urban_operation | service | 商业 |
| 美发 | urban_operation | service | 商业 |
| 美甲 | urban_operation | service | 商业 |
| 美体 | urban_operation | service | 商业 |
| 其他 | urban_operation | service | 兜底 |

### 2.6 旅游景点
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 公园 | urban_operation | environment | 城市环境 |
| 动物园 | urban_operation | culture | 文旅 |
| 植物园 | urban_operation | environment | 环境 |
| 游乐园 | urban_operation | event | 事件/活动 |
| 博物馆 | urban_renewal | culture | 文化传承 |
| 水族馆 | urban_operation | culture | 文旅 |
| 海滨浴场 | — | — | 宜昌无海滨 |
| 文物古迹 | urban_renewal | culture | 历史保护 |
| 教堂 | urban_renewal | culture | 历史保护 |
| 风景区 | urban_operation / urban_renewal | environment / culture | 三峡大坝等偏运营，古迹偏更新 |
| 景点 | urban_operation | environment | 日常文旅 |
| 寺庙 | urban_renewal | culture | 历史/文化 |
| 其他 | urban_operation | environment | 兜底 |

### 2.7 休闲娱乐
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 度假村 | urban_operation | event | 休闲 |
| 农家院 | urban_operation | event | 休闲 |
| 电影院 | urban_operation | event | 文化活动 |
| ktv | urban_operation | event | 夜经济 |
| 剧院 | urban_renewal / urban_operation | culture | 历史剧院偏更新 |
| 歌舞厅 | urban_operation | event | 夜经济 |
| 网吧 | urban_operation | event | 休闲 |
| 游戏场所 | urban_operation | event | 休闲 |
| 洗浴按摩 | urban_operation | service | 服务 |
| 休闲广场 | urban_operation | event | 公共活动 |
| 其他 | urban_operation | event | 兜底 |

### 2.8 运动健身
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 体育场馆 | urban_operation | event | 大型活动 |
| 极限运动场所 | urban_operation | event | 活动 |
| 健身中心 | urban_operation | service | 服务 |
| 其他 | urban_operation | service | 兜底 |

### 2.9 教育培训
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 高等院校 | urban_operation | service | 教育服务 |
| 中学 | urban_operation | service | 教育 |
| 小学 | urban_operation | service | 教育 |
| 幼儿园 | urban_operation | service | 教育 |
| 成人教育 | urban_operation | service | 教育 |
| 亲子教育 | urban_operation | service | 教育 |
| 特殊教育学校 | urban_governance | service | 公共教育 |
| 留学中介机构 | urban_operation | service | 服务 |
| 科研机构 | urban_planning | service | 与规划相关 |
| 培训机构 | urban_operation | service | 教育 |
| 图书馆 | urban_operation | culture | 文化服务 |
| 科技馆 | urban_operation | culture | 文化服务 |
| 其他 | urban_operation | service | 兜底 |

### 2.10 文化传媒
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 新闻出版 | urban_operation | culture | 文化 |
| 广播电视 | urban_operation | culture | 文化 |
| 艺术团体 | urban_renewal | culture | 与更新/传承相关 |
| 美术馆 | urban_renewal | culture | 文化 |
| 展览馆 | urban_renewal | culture | 文化 |
| 文化宫 | urban_renewal | culture | 老场馆 |
| 其他 | urban_operation | culture | 兜底 |

### 2.11 医疗
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 综合医院 | urban_governance | service | 公共服务 |
| 专科医院 | urban_governance | service | 公共服务 |
| 诊所 | urban_operation | service | 商业医疗 |
| 药店 | urban_operation | service | 商业 |
| 体检机构 | urban_operation | service | 商业 |
| 疗养院 | urban_operation | service | 服务 |
| 急救中心 | urban_governance | service | 应急 |
| 疾控中心 | urban_governance | service | 公共卫生 |
| 医疗器械 | urban_operation | service | 商业 |
| 医疗保健 | urban_operation | service | 商业 |
| 核酸检测点 | urban_governance | service | 公共卫生 |
| 新冠疫苗接种点 | urban_governance | service | 公共卫生 |
| 风险点 | urban_governance | facility | 应急 |
| 方舱医院 | urban_governance | facility | 应急 |
| 发热门诊 | urban_governance | service | 公共卫生 |
| 其他 | urban_operation | service | 兜底 |

### 2.12 汽车服务
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 汽车销售 | urban_operation | service | 商业 |
| 汽车维修 | urban_operation | service | 商业 |
| 汽车美容 | urban_operation | service | 商业 |
| 汽车配件 | urban_operation | service | 商业 |
| 汽车租赁 | urban_operation | service | 商业 |
| 汽车检测场 | urban_governance | service | 监管类 |
| 其他 | urban_operation | service | 兜底 |

### 2.13 交通设施
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 飞机场 | urban_governance | facility | 重要交通设施 |
| 火车站 | urban_governance | facility | 重要交通设施 |
| 地铁站 | urban_planning | facility | 重大规划 |
| 地铁线路 | urban_planning | facility | 重大规划 |
| 长途汽车站 | urban_governance | facility | 交通 |
| 公交车站 | urban_governance | facility | 交通 |
| 港口 | urban_governance | facility | 交通 |
| 停车场 | urban_governance | facility | 交通 |
| 停车区 | urban_governance | facility | 交通 |
| 停车位 | urban_governance | facility | 交通 |
| 加油加气站 | urban_operation | facility | 商业设施 |
| 服务区 | urban_governance | facility | 交通 |
| 收费站 | urban_governance | facility | 交通 |
| 桥 | urban_planning | facility | 重大工程 |
| 充电站 | urban_planning | facility | 新基建 |
| 路侧停车位 | urban_governance | facility | 治理 |
| 普通停车位 | urban_governance | facility | 治理 |
| 接送点 | urban_governance | facility | 交通 |
| 电动自行车充电站 | urban_governance | facility | 治理 |
| 高速公路停车区 | urban_governance | facility | 交通 |
| 其他 | urban_governance | facility | 兜底 |

### 2.14 金融
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 银行 | urban_operation | service | 商业服务 |
| ATM | urban_operation | service | 商业服务 |
| 信用社 | urban_operation | service | 服务 |
| 投资理财 | urban_operation | service | 服务 |
| 典当行 | urban_operation | service | 服务 |
| 其他 | urban_operation | service | 兜底 |

### 2.15 房地产
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 写字楼 | urban_operation | service | 商务 |
| 住宅区 | urban_renewal | service / culture | 老小区偏更新，新小区偏服务 |
| 宿舍 | urban_operation | service | 服务 |
| 内部楼栋 | urban_operation | service | 服务 |
| 其他 | urban_operation | service | 兜底 |

### 2.16 公司企业
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 公司 | urban_operation | service | 商务 |
| 园区 | urban_planning | service | 园区规划 |
| 农林园艺 | urban_operation | environment | 农林 |
| 厂矿 | urban_planning / urban_renewal | facility | 工业遗存偏更新 |
| 其他 | urban_operation | service | 兜底 |

### 2.17 政府机构
| 百度二级 | domain | element | 说明 |
|---|---|---|---|
| 中央机构 | urban_governance | service | 中央 |
| 各级政府 | urban_governance | service | 政务 |
| 行政单位 | urban_governance | service / facility | 行政服务/设施 |
| 公检法机构 | urban_governance | facility | 公共安全 |
| 涉外机构 | urban_governance | service | 政务 |
| 党派团体 | urban_governance | service | 政务 |
| 福利机构 | urban_governance | service | 民生 |
| 政治教育机构 | urban_governance | service | 政务 |
| 社会团体 | urban_governance | service | 治理 |
| 民主党派 | urban_governance | service | 治理 |
| 居民委员会 | urban_governance | service | 基层治理 |
| 其他 | urban_governance | service | 兜底 |

---

## 3. 模拟数据权重建议

### 3.1 4 领域分配（基于宜昌实际）
| 领域 | 占比 | 主要 POI 类型 |
|---|---|---|
| urban_operation 运营 | 45% | 商业、餐饮、文旅、夜经济、节庆 |
| urban_governance 治理 | 25% | 政府、医疗、交通、应急、市政 |
| urban_renewal 更新 | 20% | 历史街区、老旧小区、改造工程 |
| urban_planning 规划 | 10% | 控规调整、新基建、产业园区 |

### 3.2 5 要素分配
| 要素 | 占比 | 触发场景 |
|---|---|---|
| service 服务 | 40% | 日常服务（商业、政务、医疗、教育） |
| facility 设施 | 25% | 交通、市政、应急 |
| culture 文化 | 15% | 历史、文创、文旅 |
| environment 环境 | 12% | 公园、绿化、滨江 |
| event 事件 | 8% | 大型活动、夜经济、应急 |

### 3.3 二马路专项权重
- urban_renewal × culture：占二马路数据的 40%（老字号/历史建筑/改造进展）
- urban_renewal × facility：占 20%（改造施工、市政设施）
- urban_operation × culture/event：占 25%（文创市集、老茶馆、节庆）
- urban_governance × service：占 15%（基层治理、12345）

---

## 4. 与真实数据接入的衔接

### 4.1 百度 POI 检索 API 接入
```python
# 伪代码：通过百度 API 检索 POI
import requests

def fetch_baidu_poi(city="宜昌", category="美食", location="111.31,30.71", radius=2000):
    url = "https://api.map.baidu.com/place/v2/search"
    params = {
        "query": category,
        "region": city,
        "location": location,  # "lng,lat"
        "radius": radius,
        "output": "json",
        "ak": "YOUR_BAIDU_AK",
    }
    r = requests.get(url, params=params)
    pois = r.json()["results"]
    for p in pois:
        # 转换 GCJ-02 → WGS84 → CGCS2000 → EPSG:4547
        yield transform_poi(p)
```

### 4.2 字段映射（百度 API → L1 schema）
| 百度 API 字段 | L1 字段 | 说明 |
|---|---|---|
| `name` | `text` / `poi_hint` | 名称 |
| `address` | `address` | 地址 |
| `location.lat/lng` | `geometry.coordinates` | 需 CRS 转换 |
| `detail_info.tag` | `poi_hint` | 标签 |
| `detail_info.type` | `baidu_level2` | 百度二级分类 |
| — | `domain` / `element` | 按本表映射规则 |
| — | `polarity_hint` | 通过评论/外部数据推断 |

### 4.3 高德 POI 同步接入（推荐）
高德 POI 接口更稳定、限流更宽松，作为主数据源：
- **API**：https://restapi.amap.com/v3/place/text
- **分类码**：高德有自己的分类体系（010000 美食类、090000 商业类等）
- **转换**：GCJ-02 → CGCS2000 → EPSG:4547

---

## 5. 落地建议

### 5.1 立即可用
直接用 `data/yichang-poi-seed-rich.json`（158 条宜昌精选 POI）替换之前的简化版 `poi-seeds.json`，再跑 `scripts/generate_emotion_data.py` 即可生成基于真实位置的模拟数据。

### 5.2 接入真实数据
1. 申请百度/高德 API Key（个人开发者免费额度够用）
2. 写 ETL 脚本：拉 POI → CRS 转换 → 按本表映射 domain/element
3. 把 L1 数据源从模拟切到混合（真实 POI + 模拟评论）
4. 后续接入评论数据（小红书、微博、12345）

### 5.3 长期优化
- POI 数据更新：季度/半年刷新一次（百度 POI 调整较频繁）
- 增加垂直 POI：临时市集、活动场地、节庆场地（百度覆盖不全）
- 接入热力图：百度慧眼/高德慧行（商业付费）

---

## 6. 文件清单

- `data/baidu-poi-catalog.json` — 百度 POI 完整体系（31 个一级、约 200 个二级）
- `data/yichang-poi-table.md` — 宜昌精选 POI 表格（158 条，Markdown 详细版）
- `data/yichang-poi-table.csv` — 宜昌精选 POI 表格（CSV，Excel 可打开）
- `data/yichang-poi-seed-rich.json` — 宜昌精选 POI seed（带 EPSG:4547 坐标）
- `docs/poi-mapping-4x5.md` — 本文档（4×5 矩阵映射）
