# -*- coding: utf-8 -*-
"""
整理百度 POI 完整对照表（2024-04-18 版）为结构化 JSON
来源：https://lbsyun.baidu.com/index.php?title=open/poitags
"""
import json
import os

# 百度 POI 一级 + 二级分类
# 字段：
#   code: 分类标识（自定义）
#   name_cn: 中文名
#   name_en: 英文名（部分）
#   parent: 一级分类
#   weight_default: 默认采样权重（用于模拟数据）
#   applicable_to_yichang: 是否适用于宜昌
BAIDU_POI_CATALOG = {
    "美食": {
        "code": "catering",
        "secondary": [
            "中餐厅", "外国餐厅", "小吃快餐店", "蛋糕甜品店",
            "咖啡厅", "茶座", "酒吧", "其他"
        ],
        "weight_default": 0.30,
        "applicable_to_yichang": True,
    },
    "酒店": {
        "code": "hotel",
        "secondary": [
            "星级酒店", "快捷酒店", "公寓式酒店", "民宿", "其他"
        ],
        "weight_default": 0.05,
        "applicable_to_yichang": True,
    },
    "购物": {
        "code": "shopping",
        "secondary": [
            "购物中心", "百货商场", "超市", "便利店",
            "家居建材", "家电数码", "商铺", "市场", "其他"
        ],
        "weight_default": 0.20,
        "applicable_to_yichang": True,
    },
    "生活服务": {
        "code": "life_service",
        "secondary": [
            "通讯营业厅", "邮局", "物流公司", "售票处", "洗衣店",
            "图文快印店", "照相馆", "房产中介机构", "公用事业", "维修点",
            "家政服务", "殡葬服务", "彩票销售点", "宠物服务", "报刊亭",
            "公共厕所", "步骑行专用道驿站", "其他"
        ],
        "weight_default": 0.10,
        "applicable_to_yichang": True,
    },
    "丽人": {
        "code": "beauty",
        "secondary": ["美容", "美发", "美甲", "美体", "其他"],
        "weight_default": 0.03,
        "applicable_to_yichang": True,
    },
    "旅游景点": {
        "code": "scenic",
        "secondary": [
            "公园", "动物园", "植物园", "游乐园", "博物馆",
            "水族馆", "海滨浴场", "文物古迹", "教堂", "风景区",
            "景点", "寺庙", "其他"
        ],
        "weight_default": 0.15,
        "applicable_to_yichang": True,
    },
    "休闲娱乐": {
        "code": "leisure",
        "secondary": [
            "度假村", "农家院", "电影院", "ktv", "剧院",
            "歌舞厅", "网吧", "游戏场所", "洗浴按摩", "休闲广场", "其他"
        ],
        "weight_default": 0.10,
        "applicable_to_yichang": True,
    },
    "运动健身": {
        "code": "fitness",
        "secondary": ["体育场馆", "极限运动场所", "健身中心", "其他"],
        "weight_default": 0.03,
        "applicable_to_yichang": True,
    },
    "教育培训": {
        "code": "education",
        "secondary": [
            "高等院校", "中学", "小学", "幼儿园", "成人教育",
            "亲子教育", "特殊教育学校", "留学中介机构", "科研机构",
            "培训机构", "图书馆", "科技馆", "其他"
        ],
        "weight_default": 0.06,
        "applicable_to_yichang": True,
    },
    "文化传媒": {
        "code": "media",
        "secondary": [
            "新闻出版", "广播电视", "艺术团体", "美术馆",
            "展览馆", "文化宫", "其他"
        ],
        "weight_default": 0.02,
        "applicable_to_yichang": True,
    },
    "医疗": {
        "code": "medical",
        "secondary": [
            "综合医院", "专科医院", "诊所", "药店", "体检机构",
            "疗养院", "急救中心", "疾控中心", "医疗器械", "医疗保健",
            "核酸检测点", "新冠疫苗接种点", "风险点", "方舱医院",
            "发热门诊", "其他"
        ],
        "weight_default": 0.05,
        "applicable_to_yichang": True,
    },
    "汽车服务": {
        "code": "auto_service",
        "secondary": [
            "汽车销售", "汽车维修", "汽车美容", "汽车配件",
            "汽车租赁", "汽车检测场", "其他"
        ],
        "weight_default": 0.04,
        "applicable_to_yichang": True,
    },
    "交通设施": {
        "code": "transport",
        "secondary": [
            "飞机场", "火车站", "地铁站", "地铁线路", "长途汽车站",
            "公交车站", "港口", "停车场", "停车区", "停车位",
            "加油加气站", "服务区", "收费站", "桥", "充电站",
            "路侧停车位", "普通停车位", "接送点", "电动自行车充电站",
            "高速公路停车区", "其他"
        ],
        "weight_default": 0.10,
        "applicable_to_yichang": True,
    },
    "金融": {
        "code": "finance",
        "secondary": [
            "银行", "ATM", "信用社", "投资理财", "典当行", "其他"
        ],
        "weight_default": 0.04,
        "applicable_to_yichang": True,
    },
    "房地产": {
        "code": "real_estate",
        "secondary": [
            "写字楼", "住宅区", "宿舍", "内部楼栋", "其他"
        ],
        "weight_default": 0.05,
        "applicable_to_yichang": True,
    },
    "公司企业": {
        "code": "company",
        "secondary": [
            "公司", "园区", "农林园艺", "厂矿", "其他"
        ],
        "weight_default": 0.03,
        "applicable_to_yichang": True,
    },
    "政府机构": {
        "code": "government",
        "secondary": [
            "中央机构", "各级政府", "行政单位", "公检法机构",
            "涉外机构", "党派团体", "福利机构", "政治教育机构",
            "社会团体", "民主党派", "居民委员会", "其他"
        ],
        "weight_default": 0.03,
        "applicable_to_yichang": True,
    },
    "出入口": {
        "code": "entrance",
        "secondary": [
            "高速公路出口", "高速公路入口", "机场出口", "机场入口",
            "车站出口", "车站入口", "门", "停车场出入口",
            "自行车高速出口", "自行车高速入口", "自行车高速出入口",
            "停车场出口", "停车场入口", "其他"
        ],
        "weight_default": 0.0,  # 模拟数据基本不用
        "applicable_to_yichang": False,
    },
    "自然地物": {
        "code": "natural_feature",
        "secondary": ["岛屿", "山峰", "水系", "其他"],
        "weight_default": 0.0,  # 模拟数据不直接生成
        "applicable_to_yichang": False,
    },
    "行政地标": {
        "code": "admin_landmark",
        "secondary": [
            "省", "省级城市", "城市", "地级市", "区县",
            "商圈", "乡镇", "村庄", "其他"
        ],
        "weight_default": 0.0,
        "applicable_to_yichang": False,
    },
    "门址": {
        "code": "door_address",
        "secondary": ["门址点", "其他"],
        "weight_default": 0.0,
        "applicable_to_yichang": False,
    },
    "道路": {
        "code": "road",
        "secondary": [
            "高速公路", "国道", "省道", "县道", "乡道",
            "城市快速路", "城市主干道", "城市次干道", "城市支路",
            "车渡线", "路口", "其他"
        ],
        "weight_default": 0.0,
        "applicable_to_yichang": False,
    },
    "铁路": {
        "code": "railway",
        "secondary": [
            "铁路", "地铁/轻轨", "磁悬浮列车", "有轨电车",
            "城际快轨", "其他"
        ],
        "weight_default": 0.0,
        "applicable_to_yichang": False,
    },
    "行政界线": {
        "code": "admin_boundary",
        "secondary": [
            "其他国家国界", "已定国界", "未定国界", "港澳界线",
            "南海范围线", "已定省界", "未定省界", "海岸线", "其他"
        ],
        "weight_default": 0.0,
        "applicable_to_yichang": False,
    },
    "其他线要素": {
        "code": "other_line",
        "secondary": [
            "桥梁", "隧道", "行政假想线", "水域假想线",
            "绿地假想线", "岛屿假想线", "疫情管控区", "其他"
        ],
        "weight_default": 0.0,
        "applicable_to_yichang": False,
    },
    "行政区划": {
        "code": "admin_division",
        "secondary": [
            "世界级", "国家级", "省级", "市级", "区县级",
            "热点区域", "建成区", "智能区域", "其他"
        ],
        "weight_default": 0.0,
        "applicable_to_yichang": False,
    },
    "水系": {
        "code": "water",
        "secondary": ["双线河", "湖沼", "海洋", "其他"],
        "weight_default": 0.0,
        "applicable_to_yichang": False,
    },
    "绿地": {
        "code": "green",
        "secondary": [
            "绿地公园", "高尔夫球场", "岛", "绿化带",
            "机场", "机场道路", "其他"
        ],
        "weight_default": 0.0,
        "applicable_to_yichang": False,
    },
    "标注": {
        "code": "annotation",
        "secondary": [
            "大洲标注", "大洋标注", "海域标注", "水系标注",
            "岛屿标注", "非水系标注", "其他"
        ],
        "weight_default": 0.0,
        "applicable_to_yichang": False,
    },
    "公交线路": {
        "code": "bus_line",
        "secondary": [
            "普通日行公交车", "地铁\\轻轨", "有轨电车",
            "机场巴士（前往机场）", "机场巴士（从机场返回）",
            "机场巴士（机场之间）", "旅游线路车", "夜班车",
            "轮渡", "快车", "慢车",
            "机场快轨（前往机场）", "机场快轨（从机场返回）",
            "机场轨道交通环路", "其他"
        ],
        "weight_default": 0.0,
        "applicable_to_yichang": False,
    },
    "电子眼": {
        "code": "camera",
        "secondary": [
            "限速电子眼", "应急车道电子眼", "公交车道电子眼",
            "外地车辆电子眼", "违章电子眼", "其他"
        ],
        "weight_default": 0.0,
        "applicable_to_yichang": False,
    },
}


def build_full_catalog():
    """构建完整 POI 对照表结构"""
    catalog = {
        "metadata": {
            "source": "百度地图开放平台 POI 分类",
            "source_url": "https://lbsyun.baidu.com/index.php?title=open/poitags",
            "version": "2024-04-18",
            "first_level_count": len(BAIDU_POI_CATALOG),
            "applicable_to_yichang_count": sum(
                1 for v in BAIDU_POI_CATALOG.values() if v["applicable_to_yichang"]
            ),
        },
        "categories": {}
    }
    for cat_name, cfg in BAIDU_POI_CATALOG.items():
        catalog["categories"][cat_name] = {
            "code": cfg["code"],
            "secondary": cfg["secondary"],
            "secondary_count": len(cfg["secondary"]),
            "weight_default": cfg["weight_default"],
            "applicable_to_yichang": cfg["applicable_to_yichang"],
        }
    return catalog


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(base_dir), "data")
    os.makedirs(data_dir, exist_ok=True)

    catalog = build_full_catalog()

    # 输出 JSON
    json_path = os.path.join(data_dir, "baidu-poi-catalog.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"✓ 百度 POI 完整体系: {json_path}")
    print(f"  一级分类: {catalog['metadata']['first_level_count']} 个")
    print(f"  适用于宜昌: {catalog['metadata']['applicable_to_yichang_count']} 个")

    return catalog


if __name__ == "__main__":
    main()
