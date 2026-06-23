#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情绪地图 L1 模拟数据生成器
===========================

生成西陵伍家核心主城（~140 km²）+ 二马路历史街区（~2 km²，详）的 L1 数据
覆盖 3 个时间点：T1 (2025-01-15), T2 (2025-10-20), T3 (2026-06-25)

坐标系：EPSG:4546 (CGCS2000 / 3-degree Gauss-Kruger zone 37, CM 111°E)
单位：米
GeoJSON coordinates: [东向_米, 北向_米] = [Y_投影, X_投影]

依赖：仅 Python 3.8+ 标准库（json, random, math, datetime）
"""

import json
import math
import random
import os
from datetime import datetime, timedelta, timezone

random.seed(20260123)  # 固定种子，可重现

# ============================================================================
# 1. POI 种子表（基于宜昌核心主城真实地理结构）
# ============================================================================
# 坐标系统：EPSG:4547 米级
# Y_投影 (东向): 中央经线 111°E = 500000m，宜昌主城 515000~545000
# X_投影 (北向): 30.6°N~30.78°N 对应 3395000~3420000

POI_SEEDS = {
    # === 核心商圈（高密度） ===
    "cbd_wanda":     {"xy": [529890, 3397978], "radius": 300,  "weight": 1.0, "area": "西陵-商圈核心"},
    "yiling_square":     {"xy": [527784, 3397307], "radius": 300,  "weight": 1.0, "area": "西陵-夷陵广场"},
    "解放路步行街":     {"xy": [527593, 3396863], "radius": 300,  "weight": 1.2, "area": "西陵-解放路"},
    "铁路坝":     {"xy": [529221, 3397310], "radius": 300,  "weight": 0.8, "area": "西陵-铁路坝"},
    "cbd_taikoo":     {"xy": [530463, 3398533], "radius": 300,  "weight": 0.9, "area": "西陵-太古里"},

    # === 二马路历史街区（详，最高密度） ===
    "ermalu_main":     {"xy": [526349, 3396416], "radius": 400,  "weight": 2.0, "area": "西陵-二马路"},
    "dananmen":     {"xy": [526062, 3396083], "radius": 300,  "weight": 1.8, "area": "西陵-大南门"},
    "hongxinglu":     {"xy": [526827, 3396639], "radius": 300,  "weight": 1.6, "area": "西陵-红星路"},
    "jiexi_bus_st":     {"xy": [527593, 3396863], "radius": 300,  "weight": 1.5, "area": "西陵-解放路步行街"},
    "xianrenqi":     {"xy": [526253, 3396527], "radius": 300,  "weight": 1.4, "area": "西陵-献福路"},
    "qiaohuling":     {"xy": [526635, 3396860], "radius": 300,  "weight": 1.3, "area": "西陵-樵湖岭"},

    # === 滨江带（中密度，T3 重点） ===
    "binjiang_park":     {"xy": [527593, 3396974], "radius": 500,  "weight": 0.7, "area": "西陵-滨江公园"},
    "binjiang_walk":     {"xy": [528359, 3397308], "radius": 300,  "weight": 0.6, "area": "西陵-滨江步道"},
    "mojishan":     {"xy": [531133, 3398757], "radius": 600,  "weight": 0.4, "area": "西陵-磨基山"},
    "yiling_yangtze":     {"xy": [532182, 3400201], "radius": 300,  "weight": 0.3, "area": "伍家-长江沿线"},
    "xiaoting_dam":     {"xy": [523474, 3396631], "radius": 300,  "weight": 0.5, "area": "西陵-临江"},

    # === 居住区（中-低密度） ===
    "dongshan_garden":     {"xy": [531800, 3399757], "radius": 600,  "weight": 0.6, "area": "伍家-东山花园"},
    "wujiashan_block":     {"xy": [534956, 3401430], "radius": 700,  "weight": 0.5, "area": "伍家-伍家岗"},
    "wujia_north":     {"xy": [536387, 3403097], "radius": 800,  "weight": 0.4, "area": "伍家-伍家北"},
    "dongshan_edu":     {"xy": [533907, 3399985], "radius": 300,  "weight": 0.5, "area": "伍家-东山教育"},
    "wujia_old":     {"xy": [534574, 3401096], "radius": 300,  "weight": 0.5, "area": "伍家-老居住区"},

    # === 文旅节点 ===
    "three_gorges_mus":     {"xy": [527305, 3397084], "radius": 300, "weight": 0.6, "area": "西陵-三峡博物馆"},
    "dongshan_park":     {"xy": [531322, 3399755], "radius": 700, "weight": 0.5, "area": "伍家-东山公园"},
    "sanxia_family":     {"xy": [527497, 3397195], "radius": 300, "weight": 0.4, "area": "西陵-三峡人家"},
    "wenmiao":     {"xy": [526157, 3396416], "radius": 300, "weight": 1.0, "area": "西陵-文庙"},

    # === 公共服务 ===
    "yichang_station":     {"xy": [529602, 3398088], "radius": 500, "weight": 0.7, "area": "西陵-宜昌站"},
    "yichang_east":     {"xy": [537922, 3402216], "radius": 500, "weight": 0.6, "area": "伍家-宜昌东站"},
    "central_hosp":     {"xy": [528644, 3397974], "radius": 300, "weight": 0.5, "area": "西陵-中心医院"},
    "wujia_hosp":     {"xy": [534574, 3401096], "radius": 300, "weight": 0.4, "area": "伍家-伍家医院"},
    "gov_center":     {"xy": [527880, 3397085], "radius": 300, "weight": 0.4, "area": "西陵-政务中心"},
    "12345_center":     {"xy": [527880, 3397085], "radius": 300, "weight": 0.3, "area": "西陵-12345受理"},

    # === 教育 ===
    "sanxia_univ":     {"xy": [527972, 3398638], "radius": 600, "weight": 0.4, "area": "西陵-三峡大学"},
    "yichang_high":     {"xy": [527210, 3396862], "radius": 300, "weight": 0.4, "area": "西陵-宜昌一中"},
    "wujia_school":     {"xy": [534574, 3400985], "radius": 300, "weight": 0.3, "area": "伍家-伍家学校"},
}

# ============================================================================
# 2. 边界过滤（粗略多边形，避免点落在长江/山体）
# ============================================================================
# 长江水面：x < 3406500 或接近的长江边界，简化为排除 Y < 526000 且 X < 3407500 的区域
# 山体：西北部，简化为排除 X > 3414000 且 Y < 528000 的区域

def is_in_valid_area(x, y, area_filter=None):
    """判断点是否在合法区域内
    x = 北向投影（米），y = 东向投影（米）
    """
    # 主城边界（基于真实 POI 范围：Y 523474~545947, X 3396083~3406682，扩展一点采样空间）
    if not (515000 <= y <= 550000):
        return False
    if not (3395000 <= x <= 3410000):
        return False
    # 长江水面（宜昌主城段长江在西/南侧，江面在 lng<111.18° 即 y<512000 附近）
    # 二马路（y≈526349）远离江面
    if y < 512000:
        return False
    # 西北部山体（点军方向）
    if x > 3414000 and y < 527500:
        return False
    # 伍家岗东南角偏远区域
    if y > 544000 and x > 3413000:
        return False
    # 二马路范围限制（如果是 ermalu 区域）
    if area_filter == "ermalu":
        # 二马路 2 km² 范围（约 1414m × 1414m）
        ex, ey = 526349, 3396416
        if not (ex - 1100 <= y <= ex + 1100):
            return False
        if not (ey - 1100 <= x <= ey + 1100):
            return False
    return True


# ============================================================================
# 3. 4×5 矩阵配置
# ============================================================================
MATRIX_CONFIG = {
    "urban_planning": {
        "facility":    {"weight": 0.05, "polarity": ["neutral", "mixed", "positive"]},
        "environment": {"weight": 0.08, "polarity": ["positive", "neutral", "mixed"]},
        "service":     {"weight": 0.04, "polarity": ["neutral", "positive", "negative"]},
        "culture":     {"weight": 0.03, "polarity": ["positive", "neutral"]},
        "event":       {"weight": 0.02, "polarity": ["neutral", "positive"]},
    },
    "urban_renewal": {
        "facility":    {"weight": 0.07, "polarity": ["negative", "mixed", "positive"]},
        "environment": {"weight": 0.06, "polarity": ["mixed", "positive", "negative"]},
        "service":     {"weight": 0.05, "polarity": ["negative", "mixed"]},
        "culture":     {"weight": 0.10, "polarity": ["mixed", "positive", "negative"]},
        "event":       {"weight": 0.04, "polarity": ["negative", "neutral"]},
    },
    "urban_operation": {
        "facility":    {"weight": 0.04, "polarity": ["positive", "neutral"]},
        "environment": {"weight": 0.05, "polarity": ["positive", "neutral"]},
        "service":     {"weight": 0.12, "polarity": ["positive", "neutral", "mixed"]},
        "culture":     {"weight": 0.10, "polarity": ["positive", "mixed"]},
        "event":       {"weight": 0.15, "polarity": ["positive", "mixed", "neutral"]},
    },
    "urban_governance": {
        "facility":    {"weight": 0.10, "polarity": ["negative", "mixed", "neutral"]},
        "environment": {"weight": 0.08, "polarity": ["negative", "neutral", "mixed"]},
        "service":     {"weight": 0.09, "polarity": ["negative", "neutral", "mixed"]},
        "culture":     {"weight": 0.02, "polarity": ["neutral", "mixed"]},
        "event":       {"weight": 0.06, "polarity": ["negative", "mixed", "neutral"]},
    },
}

# ============================================================================
# 4. 评论文本模板（按 polarity × element 分类）
# ============================================================================
TEMPLATES = {
    "positive": {
        "facility": [
            "新开通的地铁站真方便，出门就能坐，再也不用担心堵车。",
            "BRT 站台干净整洁，等车有座椅，给宜昌公交点赞。",
            "家门口的快递柜升级了，取件再也不用排长队。",
            "新充电桩布局很合理，半小时充电就能跑一周。",
            "公共自行车扫码就能骑，绿色出行真方便。",
        ],
        "environment": [
            "滨江公园的夜景太美了，长江边上散步非常舒服。",
            "东山公园改造后绿植多了很多，跑步道也很专业。",
            "空气比前几年好多了，蓝天白云越来越常见。",
            "沿江绿道修得真漂亮，宜居城市名副其实。",
            "新种的花海太美了，路过都忍不住拍照。",
        ],
        "service": [
            "政务中心办事效率高，工作人员态度也好。",
            "社区医院的医生很耐心，挂号也比以前方便。",
            "便利店开到深夜，应急买药终于不愁了。",
            "学校门口的接送区设计得很合理，缓解拥堵。",
            "社区食堂价格实惠，老人很喜欢。",
        ],
        "culture": [
            "三峡博物馆的展览很震撼，宜昌历史讲得清楚。",
            "二马路的老字号味道还是那么正宗，情怀满分。",
            "文庙修缮后古韵十足，免费参观很贴心。",
            "非遗展演让人感受到宜昌的文化底蕴。",
            "解放路步行街的非遗市集很有意思。",
        ],
        "event": [
            "滨江夜市开业了，美食多多，氛围超棒。",
            "城市马拉松办得很成功，宜昌越来越有活力。",
            "国庆灯光秀把江边照得金灿灿的，特别震撼。",
            "端午龙舟赛很精彩，宜昌传统不能丢。",
            "跨年烟火太美了，长江边上人头攒动。",
        ],
    },
    "negative": {
        "facility": [
            "施工围挡把人行道占了一大半，行人无路可走。",
            "公交站牌信息更新不及时，等错好几趟车。",
            "老旧小区电梯经常故障，老人上下楼太难了。",
            "下水道堵塞没人管，一下雨就积水。",
            "公共厕所太少，外出如厕太不方便。",
        ],
        "environment": [
            "滨江公园座椅太少了，走累了都没地方坐。",
            "工地扬尘严重，路过都得捂鼻子。",
            "绿化带杂草丛生，没人养护。",
            "长江边渔港气味难闻，夏天更甚。",
            "夜晚施工噪音扰民，居民投诉无门。",
        ],
        "service": [
            "政务窗口办事流程繁琐，跑了好几趟才办成。",
            "社区医院药品不全，还得去大医院。",
            "幼儿园学位紧张，孩子入园困难。",
            "快递柜经常满员，放件超时还要收费。",
            "物业服务跟不上，缴费反而涨价了。",
        ],
        "culture": [
            "二马路改造把老街风貌破坏了，太可惜。",
            "博物馆讲解员太少，参观体验一般。",
            "老字号越来越少，传统味道断了代。",
            "历史建筑保护不到位，乱搭乱建严重。",
            "文化活动商业化太重，缺乏内涵。",
        ],
        "event": [
            "网红打卡点全是人，体验感为零。",
            "跨年活动组织混乱，挤得水泄不通。",
            "灯光秀只放了十分钟，人山人海不值。",
            "节庆交通管制太严，出行极不方便。",
            "夜市卫生堪忧，食材新鲜度存疑。",
        ],
    },
    "neutral": {
        "facility": [
            "路过这个公交站，车次一般。",
            "地铁 2 号线延长段在建设中，预计明年通车。",
            "附近充电桩数量一般，等位有时。",
            "新修的市政道路，比以前宽敞了一些。",
            "停车场收费标准公示了。",
        ],
        "environment": [
            "滨江公园今天人不多，适合散步。",
            "东山公园在维护，部分区域封闭。",
            "天气预报说明天有雨，空气质量待观察。",
            "江边的栏杆加高了，安全系数提升。",
            "城市绿道里程达到 200 公里。",
        ],
        "service": [
            "政务大厅增加了自助办理区。",
            "社区服务中心上班时间为早 9 晚 5。",
            "医院推行分时段预约挂号。",
            "图书馆开放时间调整，周末延后闭馆。",
            "新开的便民超市，品类齐全。",
        ],
        "culture": [
            "文庙定期举办公益讲座。",
            "博物馆近期有新展，可关注官方公众号。",
            "二马路老街区在慢慢变化。",
            "非遗传承人公开收徒，感兴趣可联系。",
            "解放路步行街有文创小店。",
        ],
        "event": [
            "本月城市日历：马拉松、文化展、灯光秀。",
            "节庆活动预告，关注文旅公众号。",
            "免费公园活动适合周末遛娃。",
            "城市更新项目现场说明会召开。",
            "应急演练在部分社区进行。",
        ],
    },
    "mixed": {
        "facility": [
            "新公交站牌挺好，但是站台没遮挡，下雨麻烦。",
            "停车场扩建了，但价格也涨了。",
            "地铁开通方便了，但是施工期间堵车严重。",
            "共享单车多了，但乱停乱放也多了。",
            "新电梯不错，但是维护周期长。",
        ],
        "environment": [
            "滨江夜景漂亮，但夏季蚊子太多。",
            "公园改造后设施齐全，但商业气息浓了。",
            "空气质量好转，但偶尔还有雾霾天。",
            "江边绿道修好了，部分路段被摊贩占据。",
            "绿化漂亮，但浇水时间不合理，行人路滑。",
        ],
        "service": [
            "政务服务在线办理方便，但线下窗口少了。",
            "社区医院离家近，但医生水平参差。",
            "学校硬件升级，但作业负担没减。",
            "便利店多，但同质化严重。",
            "公交卡可以线上充值，但老年群体不会用。",
        ],
        "culture": [
            "二马路改造后有设计感，但老味道少了。",
            "博物馆免费参观，但人太多影响体验。",
            "文创产品有意思，但价格偏高。",
            "非遗展示很好，但讲解不够详细。",
            "文化街区商业化与历史感难以平衡。",
        ],
        "event": [
            "灯光秀震撼，但人挤人体验打折扣。",
            "夜市热闹，但卫生需要加强。",
            "马拉松组织专业，但封路影响出行。",
            "节庆气氛浓，但商业促销太抢戏。",
            "公共活动免费，但报名需要抢。",
        ],
    },
}

# ============================================================================
# 5. 子类映射（element × source → sub_element）
# ============================================================================
SUB_ELEMENT_MAP = {
    "facility": {
        "dianping":   "transport.metro",
        "meituan":    "transport.parking",
        "xiaohongshu": "transport.shared_bike",
        "weibo":      "transport.brt",
        "12345":      "facility.public",
    },
    "environment": {
        "dianping":   "park.riverside",
        "meituan":    "park.commercial",
        "xiaohongshu": "park.greenway",
        "weibo":      "environment.green",
        "12345":      "environment.pollution",
    },
    "service": {
        "dianping":   "retail.food",
        "meituan":    "retail.daily",
        "xiaohongshu": "service.community",
        "weibo":      "service.medical",
        "12345":      "service.government",
    },
    "culture": {
        "dianping":   "culture.old_brand",
        "meituan":    "culture.food",
        "xiaohongshu": "culture.creative",
        "weibo":      "culture.heritage",
        "12345":      "culture.protection",
    },
    "event": {
        "dianping":   "event.festival",
        "meituan":    "event.food_fair",
        "xiaohongshu": "event.popular",
        "weibo":      "event.heat",
        "12345":      "event.complaint",
    },
}

# POI 类型映射（用于 poi_hint）
POI_HINT_BY_ELEMENT = {
    "facility":    ["公交站", "地铁站", "BRT 站", "停车场", "公共自行车点"],
    "environment": ["公园", "滨江绿道", "绿化带", "广场", "景观节点"],
    "service":     ["政务中心", "医院", "社区", "学校", "便利店"],
    "culture":     ["博物馆", "老字号", "文创店", "历史建筑", "非遗工坊"],
    "event":       ["市集", "灯光秀", "夜市", "节庆活动", "文化演出"],
}

ADDRESS_PREFIX = ["宜昌市西陵区", "宜昌市伍家岗区"]

# ============================================================================
# 6. 时间配置
# ============================================================================
TIME_CONFIG = {
    "T1": {
        "label": "2025-01-15",
        "datetime": datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=8))),
        "total_main": 600,
        "total_ermalu": 220,
        "season_topics": {
            "positive": ["春节", "年货", "年夜饭", "团圆", "冰雪"],
            "negative": ["寒潮", "春运", "出行", "老旧改造"],
            "neutral":  ["季节", "天气", "日常"],
            "mixed":    ["改造推进", "建设"],
        },
        "热点区域": ["cbd_wanda", "yiling_square", "解放路步行街", "ermalu_main", "dananmen",
                    "yichang_station", "yichang_east", "wujia_old"],
        "polarity_distribution": {"positive": 0.60, "negative": 0.25, "neutral": 0.10, "mixed": 0.05},
    },
    "T2": {
        "label": "2025-10-20",
        "datetime": datetime(2025, 10, 20, 10, 0, 0, tzinfo=timezone(timedelta(hours=8))),
        "total_main": 800,
        "total_ermalu": 280,
        "season_topics": {
            "positive": ["国庆", "银杏季", "文创市集", "夜经济"],
            "negative": ["老旧改造", "网红打卡点", "噪音", "拥堵"],
            "neutral":  ["秋季", "运营", "日常"],
            "mixed":    ["改造中期", "争议"],
        },
        "热点区域": ["dongshan_park", "three_gorges_mus", "ermalu_main", "hongxinglu",
                    "sanxia_univ", "wujia_north", "binjiang_park"],
        "polarity_distribution": {"positive": 0.50, "negative": 0.30, "neutral": 0.15, "mixed": 0.05},
    },
    "T3": {
        "label": "2026-06-25",
        "datetime": datetime(2026, 6, 25, 10, 0, 0, tzinfo=timezone(timedelta(hours=8))),
        "total_main": 700,
        "total_ermalu": 260,
        "season_topics": {
            "positive": ["夜经济", "滨江夜市", "夏季活动", "改造完成"],
            "negative": ["高温", "防汛内涝", "暑期拥堵"],
            "neutral":  ["夏季", "汛期", "日常"],
            "mixed":    ["夜经济治理", "改造后期"],
        },
        "热点区域": ["binjiang_park", "binjiang_walk", "mojishan", "ermalu_main",
                    "yiling_yangtze", "cbd_wanda", "jiexi_bus_st"],
        "polarity_distribution": {"positive": 0.55, "negative": 0.30, "neutral": 0.10, "mixed": 0.05},
    },
}

# ============================================================================
# 7. 5 个数据源分布
# ============================================================================
SOURCE_DISTRIBUTION = {
    "dianping":   0.25,
    "meituan":    0.25,
    "xiaohongshu": 0.20,
    "weibo":      0.15,
    "12345":      0.15,
}

USER_ARCHETYPES = ["local", "tourist", "worker", "student", "migrant", "retiree"]


# ============================================================================
# 8. 生成器核心
# ============================================================================
def sample_in_circle(center_x, center_y, radius, area_filter=None):
    """在指定圆内随机采样一个点"""
    for _ in range(200):
        # 平方根采样保证均匀分布
        r = radius * math.sqrt(random.random())
        theta = random.uniform(0, 2 * math.pi)
        x = center_y + r * math.cos(theta)  # x = 北向（投影 X）
        y = center_x + r * math.sin(theta)  # y = 东向（投影 Y）
        if is_in_valid_area(x, y, area_filter):
            return (x, y)
    # 退而求其次：在 0.3*radius 内均匀采样（保证接近圆心）
    for _ in range(50):
        r = radius * 0.3 * math.sqrt(random.random())
        theta = random.uniform(0, 2 * math.pi)
        x = center_y + r * math.cos(theta)
        y = center_x + r * math.sin(theta)
        if is_in_valid_area(x, y, area_filter):
            return (x, y)
    return (center_y, center_x)


def pick_source():
    r = random.random()
    cum = 0
    for src, w in SOURCE_DISTRIBUTION.items():
        cum += w
        if r < cum:
            return src
    return "dianping"


def pick_user():
    return random.choice(USER_ARCHETYPES)


def pick_polarity(dist):
    r = random.random()
    cum = 0
    for p, w in dist.items():
        cum += w
        if r < cum:
            return p
    return "neutral"


def pick_domain_element(polarity):
    """根据极性偏好选择 domain × element 组合"""
    candidates = []
    for domain, elements in MATRIX_CONFIG.items():
        for element, cfg in elements.items():
            if polarity in cfg["polarity"]:
                candidates.append((domain, element, cfg["weight"]))
    total = sum(w for _, _, w in candidates)
    r = random.random() * total
    cum = 0
    for d, e, w in candidates:
        cum += w
        if r < cum:
            return d, e
    return "urban_operation", "service"


def generate_feature(idx, time_label, dt_base, polarity_dist, season_topics,
                    area_filter=None, is_ermalu=False):
    """生成单条 GeoJSON Feature"""
    # 时间偏移（+/- 3 天内的随机时间）
    dt = dt_base + timedelta(
        days=random.randint(-3, 3),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )

    # 选极性
    polarity = pick_polarity(polarity_dist)

    # 选 domain × element
    domain, element = pick_domain_element(polarity)

    # 选 POI 种子（按权重）
    if is_ermalu:
        # 二马路区域只使用真正的二马路种子（去掉 cbd_wanda，避免 fallback 出范围）
        candidates = ["ermalu_main", "dananmen", "hongxinglu", "jiexi_bus_st",
                     "xianrenqi", "qiaohuling", "wenmiao"]
    else:
        candidates = list(POI_SEEDS.keys())
    weights = [POI_SEEDS[c]["weight"] for c in candidates]
    seed_name = random.choices(candidates, weights=weights)[0]
    seed = POI_SEEDS[seed_name]

    # 采样坐标
    cx, cy = seed["xy"]
    x, y = sample_in_circle(cx, cy, seed["radius"], area_filter=area_filter)

    # 选 source
    source = pick_source()

    # 选评论文本
    text_pool = TEMPLATES[polarity][element]
    text = random.choice(text_pool)
    # 30% 概率叠加季节话题词
    if random.random() < 0.30 and season_topics.get(polarity):
        topic = random.choice(season_topics[polarity])
        text = f"{text} #{topic}#"

    # 子类
    sub_element = SUB_ELEMENT_MAP[element].get(source, element)

    # poi_hint
    poi_hint = random.choice(POI_HINT_BY_ELEMENT[element])

    # 强度（极性越极端，强度越高）
    intensity = {
        "positive": random.choices([3, 4, 5], weights=[0.3, 0.4, 0.3])[0],
        "negative": random.choices([3, 4, 5], weights=[0.3, 0.4, 0.3])[0],
        "neutral":  random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0],
        "mixed":    random.choices([2, 3, 4], weights=[0.3, 0.4, 0.3])[0],
    }[polarity]

    # 话题关键词
    topic_keywords = [t for t in season_topics.get(polarity, [])[:2]]
    if topic_keywords:
        topic_keywords = topic_keywords[:1]  # 取 1 个作为主关键词

    # 地址
    district = "西陵区" if "西陵" in seed["area"] else "伍家岗区"
    street_guess = seed["area"].split("-")[1] if "-" in seed["area"] else seed["area"]
    address = f"宜昌市{district}{street_guess}{random.choice(['路', '街', '巷'])}{random.randint(1,200)}号附近"

    # 地理编码置信度
    geocode_confidence = round(0.7 + random.random() * 0.3, 2)

    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [round(y, 2), round(x, 2)]  # GeoJSON: [东向_米, 北向_米]
        },
        "properties": {
            "id": f"f-{time_label}-{idx:05d}",
            "source": source,
            "created_at": dt.isoformat(),
            "text": text,
            "user_archetype": pick_user(),
            "domain": domain,
            "element": element,
            "sub_element": sub_element,
            "poi_hint": poi_hint,
            "address": address,
            "polarity_hint": polarity,
            "intensity": intensity,
            "topic_keywords": topic_keywords,
            "language": "zh-cn",
            "geocode_confidence": geocode_confidence,
            "area_seed": seed_name,
            "time_label": time_label,
        }
    }
    return feature


def build_featurecollection(features, name, description):
    """构建 FeatureCollection"""
    return {
        "type": "FeatureCollection",
        "name": name,
        "crs": {
            "type": "name",
            "properties": {"name": "EPSG:4546"}
        },
        "metadata": {
            "name": name,
            "description": description,
            "coordinate_system": "EPSG:4546 (CGCS2000 / 3-degree Gauss-Kruger zone 37, CM 111°E)",
            "unit": "meter",
            "feature_count": len(features),
            "generated_at": datetime.now().isoformat(),
            "schema_version": "L1-v1.0",
            "domain_count": 4,
            "element_count": 5,
        },
        "features": features,
    }


def generate_for_time(time_key, output_dir):
    """为单个时间点生成核心主城 + 二马路数据"""
    cfg = TIME_CONFIG[time_key]
    label = cfg["label"]
    dt_base = cfg["datetime"]
    print(f"\n=== 生成 {time_key} ({label}) ===")

    # 核心主城
    main_features = []
    for i in range(cfg["total_main"]):
        f = generate_feature(
            i, time_key, dt_base,
            cfg["polarity_distribution"], cfg["season_topics"],
            area_filter=None, is_ermalu=False,
        )
        main_features.append(f)

    main_fc = build_featurecollection(
        main_features,
        name=f"xiling-wujia-L1-{time_key}",
        description=f"西陵伍家核心主城 L1 数据，时间点 {label}，{cfg['total_main']} 个情绪点"
    )

    main_path = os.path.join(output_dir, f"xiling-wujia-L1-{time_key}-{label[:4]}Q{(int(label[5:7])-1)//3+1}.geojson")
    with open(main_path, "w", encoding="utf-8") as fp:
        json.dump(main_fc, fp, ensure_ascii=False, indent=2)
    print(f"  ✓ 核心主城: {main_path} ({cfg['total_main']} 点)")

    # 二马路详细
    ermalu_features = []
    for i in range(cfg["total_ermalu"]):
        f = generate_feature(
            i, time_key, dt_base,
            cfg["polarity_distribution"], cfg["season_topics"],
            area_filter="ermalu", is_ermalu=True,
        )
        ermalu_features.append(f)

    ermalu_fc = build_featurecollection(
        ermalu_features,
        name=f"ermalu-detail-L1-{time_key}",
        description=f"二马路历史街区 L1 详细数据，时间点 {label}，{cfg['total_ermalu']} 个情绪点"
    )

    ermalu_path = os.path.join(output_dir, f"ermalu-detail-L1-{time_key}-{label[:4]}Q{(int(label[5:7])-1)//3+1}.geojson")
    with open(ermalu_path, "w", encoding="utf-8") as fp:
        json.dump(ermalu_fc, fp, ensure_ascii=False, indent=2)
    print(f"  ✓ 二马路: {ermalu_path} ({cfg['total_ermalu']} 点)")

    return main_path, ermalu_path


def export_poi_seeds(output_dir):
    """导出 POI 种子表"""
    out = {
        "metadata": {
            "description": "宜昌核心主城 POI 种子表（基于 EPSG:4546 米级坐标）",
            "coordinate_system": "EPSG:4546",
            "unit": "meter",
            "count": len(POI_SEEDS),
        },
        "pois": [
            {
                "id": k,
                "xy_y_m": v["xy"][0],  # 东向
                "xy_x_m": v["xy"][1],  # 北向
                "radius_m": v["radius"],
                "weight": v["weight"],
                "area": v["area"],
            }
            for k, v in POI_SEEDS.items()
        ]
    }
    path = os.path.join(output_dir, "poi-seeds.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)
    print(f"\n✓ POI 种子表: {path} ({len(POI_SEEDS)} 条)")
    return path


def export_schema(output_dir):
    """导出字段 Schema"""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "EmotionMap L1 Feature Schema",
        "description": "情绪地图 L1 数据 GeoJSON Feature Schema",
        "type": "object",
        "required": ["type", "geometry", "properties"],
        "properties": {
            "type": {"const": "Feature"},
            "geometry": {
                "type": "object",
                "properties": {
                    "type": {"const": "Point"},
                    "coordinates": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                        "description": "[东向_米, 北向_米] in EPSG:4546"
                    }
                }
            },
            "properties": {
                "type": "object",
                "required": ["id", "source", "created_at", "text", "domain",
                            "element", "polarity_hint", "intensity"],
                "properties": {
                    "id":                {"type": "string", "pattern": "^f-[T0-9]+-[0-9]{5}$"},
                    "source":            {"enum": ["dianping", "meituan", "xiaohongshu", "weibo", "12345"]},
                    "created_at":        {"type": "string", "format": "date-time"},
                    "text":              {"type": "string"},
                    "user_archetype":    {"enum": ["local", "tourist", "worker", "student", "migrant", "retiree"]},
                    "domain":            {"enum": ["urban_planning", "urban_renewal", "urban_operation", "urban_governance"]},
                    "element":           {"enum": ["facility", "environment", "service", "culture", "event"]},
                    "sub_element":       {"type": "string"},
                    "poi_hint":          {"type": "string"},
                    "address":           {"type": "string"},
                    "polarity_hint":     {"enum": ["positive", "negative", "neutral", "mixed"]},
                    "intensity":         {"type": "integer", "minimum": 1, "maximum": 5},
                    "topic_keywords":    {"type": "array", "items": {"type": "string"}},
                    "language":          {"const": "zh-cn"},
                    "geocode_confidence":{"type": "number", "minimum": 0, "maximum": 1},
                    "area_seed":         {"type": "string"},
                    "time_label":        {"type": "string", "pattern": "^T[1-3]$"}
                }
            }
        }
    }
    path = os.path.join(output_dir, "L1-schema.json")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(schema, fp, ensure_ascii=False, indent=2)
    print(f"✓ Schema: {path}")
    return path


def validate_data(geojson_path):
    """校验数据完整性"""
    with open(geojson_path, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    feats = data["features"]
    issues = []
    polarity_count = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
    domain_count = {}
    element_count = {}
    out_of_range = 0
    in_water = 0
    in_mountain = 0
    for f in feats:
        p = f["properties"]
        polarity_count[p["polarity_hint"]] = polarity_count.get(p["polarity_hint"], 0) + 1
        domain_count[p["domain"]] = domain_count.get(p["domain"], 0) + 1
        element_count[p["element"]] = element_count.get(p["element"], 0) + 1
        x, y = f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0]
        if not (515000 <= y <= 545000 and 3395000 <= x <= 3420000):
            out_of_range += 1
        # 简化水/山检测（修正后的水域阈值）
        if x < 3408000 and y < 521000:
            in_water += 1
        # 山体检测
        if x > 3414000 and y < 527500:
            in_mountain += 1
    print(f"  {os.path.basename(geojson_path)}: {len(feats)} 点")
    print(f"    极性分布: {polarity_count}")
    print(f"    domain 分布: {domain_count}")
    print(f"    element 分布: {element_count}")
    if out_of_range > 0:
        print(f"    ⚠️ {out_of_range} 点超出主城边界")
    if in_water > 0:
        print(f"    ⚠️ {in_water} 点疑似在水中")
    if in_mountain > 0:
        print(f"    ⚠️ {in_mountain} 点疑似在山体")
    return len(feats), polarity_count, in_water, in_mountain


# ============================================================================
# 9. 主入口
# ============================================================================
def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    workspace = os.path.dirname(base_dir)
    data_dir = os.path.join(workspace, "data")
    schema_dir = os.path.join(workspace, "schema")

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(schema_dir, exist_ok=True)

    print("=" * 60)
    print("情绪地图 L1 模拟数据生成器")
    print("EPSG:4546 (CGCS2000 / 3°GK zone 37 / CM 111°E)")
    print("=" * 60)

    # 1. POI 种子
    export_poi_seeds(data_dir)

    # 2. Schema
    export_schema(schema_dir)

    # 3. 三个时间点的数据
    summary = {}
    for tk in ["T1", "T2", "T3"]:
        main_path, ermalu_path = generate_for_time(tk, data_dir)
        summary[tk] = {
            "main": validate_data(main_path),
            "ermalu": validate_data(ermalu_path),
        }

    print("\n" + "=" * 60)
    print("生成完成！")
    print("=" * 60)
    total = sum(s["main"][0] + s["ermalu"][0] for s in summary.values())
    print(f"总计 {total} 个 L1 数据点")
    print(f"输出目录: {data_dir}")
    return summary


if __name__ == "__main__":
    main()
