"""
4x5 矩阵映射 + 领域/要素权重
============================
吸收自 docs/minimax-workspace/docs/poi-mapping-4x5.md（参考包），供：
  1. POI 种子已预映射（见 yichang_poi_wgs84.json 的 domain/element 字段）；
  2. 未来真实 POI（百度/高德 API）按本表判 domain/element；
  3. pick_domain_element() 的基础权重（背景点无具体 POI 时按分布采样）。

矩阵：domain（规划/更新/运营/治理）x element（设施/环境/服务/文化/事件）= 20 格。
与 7 类情绪（喜怒哀乐愁急盼）正交——deep 4x5 交叉分析留 L3/L4。
"""

# ── 枚举 ──
DOMAINS = ('urban_planning', 'urban_renewal', 'urban_operation', 'urban_governance')
ELEMENTS = ('facility', 'environment', 'service', 'culture', 'event')

DOMAIN_CN = {
    'urban_planning': '城市规划',
    'urban_renewal': '城市更新',
    'urban_operation': '城市运营',
    'urban_governance': '城市治理',
}
ELEMENT_CN = {
    'facility': '设施',
    'environment': '环境',
    'service': '服务',
    'culture': '文化',
    'event': '事件',
}

# ── 基础权重（宜昌主城实际，自参考 §3.1/§3.2）──
# pick_domain_element 在无具体 POI 锚点时按此分布采样；快照演变权重在 generate_l1_mock 的 SNAPSHOTS 配。
DOMAIN_WEIGHTS = {
    'urban_operation': 0.45,    # 商业/餐饮/文旅/夜经济/节庆
    'urban_governance': 0.25,   # 政府/医疗/交通/应急/市政
    'urban_renewal': 0.20,      # 历史街区/老旧小区/改造工程
    'urban_planning': 0.10,     # 控规调整/新基建/产业园区
}
ELEMENT_WEIGHTS = {
    'service': 0.40,            # 日常服务（商业/政务/医疗/教育）
    'facility': 0.25,           # 交通/市政/应急
    'culture': 0.15,            # 历史/文创/文旅
    'environment': 0.12,        # 公园/绿化/滨江
    'event': 0.08,              # 大型活动/夜经济/应急
}

# ── 百度 POI 二级分类 → (domain, element) 精选映射 ──
# 完整 17 大类表见 docs/minimax-workspace/docs/poi-mapping-4x5.md；此处收高频类 + 兜底。
# POI 种子已自带映射，本表主要用于未来 API 拉取的真实 POI。
BAIDU_L2_TO_4X5 = {
    # 美食 / 酒店 / 购物 / 生活服务
    '中餐厅': ('urban_operation', 'service'),
    '外国餐厅': ('urban_operation', 'service'),
    '小吃快餐店': ('urban_operation', 'service'),
    '蛋糕甜品店': ('urban_operation', 'service'),
    '咖啡厅': ('urban_operation', 'culture'),
    '茶座': ('urban_renewal', 'culture'),
    '酒吧': ('urban_operation', 'event'),
    '购物中心': ('urban_operation', 'event'),
    '百货商场': ('urban_operation', 'service'),
    '超市': ('urban_operation', 'service'),
    '便利店': ('urban_operation', 'service'),
    '家居建材': ('urban_renewal', 'facility'),
    '市场': ('urban_operation', 'service'),
    '星级酒店': ('urban_operation', 'service'),
    '快捷酒店': ('urban_operation', 'service'),
    '民宿': ('urban_renewal', 'culture'),
    '房产中介机构': ('urban_renewal', 'service'),
    '公用事业': ('urban_governance', 'facility'),
    '公共厕所': ('urban_governance', 'facility'),
    # 旅游 / 休闲 / 运动
    '公园': ('urban_operation', 'environment'),
    '植物园': ('urban_operation', 'environment'),
    '动物园': ('urban_operation', 'culture'),
    '游乐园': ('urban_operation', 'event'),
    '博物馆': ('urban_renewal', 'culture'),
    '水族馆': ('urban_operation', 'culture'),
    '文物古迹': ('urban_renewal', 'culture'),
    '教堂': ('urban_renewal', 'culture'),
    '风景区': ('urban_operation', 'environment'),
    '景点': ('urban_operation', 'environment'),
    '寺庙': ('urban_renewal', 'culture'),
    '电影院': ('urban_operation', 'event'),
    'KTV': ('urban_operation', 'event'),
    '剧院': ('urban_renewal', 'culture'),
    '歌舞厅': ('urban_operation', 'event'),
    '网吧': ('urban_operation', 'event'),
    '休闲广场': ('urban_operation', 'event'),
    '体育场馆': ('urban_operation', 'event'),
    '健身中心': ('urban_operation', 'service'),
    # 教育 / 文化 / 医疗
    '高等院校': ('urban_operation', 'service'),
    '中学': ('urban_operation', 'service'),
    '小学': ('urban_operation', 'service'),
    '幼儿园': ('urban_operation', 'service'),
    '特殊教育学校': ('urban_governance', 'service'),
    '科研机构': ('urban_planning', 'service'),
    '培训机构': ('urban_operation', 'service'),
    '图书馆': ('urban_operation', 'culture'),
    '科技馆': ('urban_operation', 'culture'),
    '美术馆': ('urban_renewal', 'culture'),
    '展览馆': ('urban_renewal', 'culture'),
    '文化宫': ('urban_renewal', 'culture'),
    '综合医院': ('urban_governance', 'service'),
    '专科医院': ('urban_governance', 'service'),
    '诊所': ('urban_operation', 'service'),
    '药店': ('urban_operation', 'service'),
    '急救中心': ('urban_governance', 'service'),
    '疾控中心': ('urban_governance', 'service'),
    # 交通
    '飞机场': ('urban_governance', 'facility'),
    '火车站': ('urban_governance', 'facility'),
    '地铁站': ('urban_planning', 'facility'),
    '长途汽车站': ('urban_governance', 'facility'),
    '公交车站': ('urban_governance', 'facility'),
    '停车场': ('urban_governance', 'facility'),
    '桥': ('urban_planning', 'facility'),
    '充电站': ('urban_planning', 'facility'),
    '加油加气站': ('urban_operation', 'facility'),
    # 金融 / 房地产 / 公司
    '银行': ('urban_operation', 'service'),
    '写字楼': ('urban_operation', 'service'),
    '住宅区': ('urban_renewal', 'service'),
    '园区': ('urban_planning', 'service'),
    '厂矿': ('urban_renewal', 'facility'),
    # 政府机构
    '各级政府': ('urban_governance', 'service'),
    '行政单位': ('urban_governance', 'service'),
    '公检法机构': ('urban_governance', 'facility'),
    '居民委员会': ('urban_governance', 'service'),
    '福利机构': ('urban_governance', 'service'),
}

# 一级分类兜底（二级未命中时）
_L1_FALLBACK = {
    '美食': ('urban_operation', 'service'),
    '酒店': ('urban_operation', 'service'),
    '购物': ('urban_operation', 'service'),
    '生活服务': ('urban_operation', 'service'),
    '丽人': ('urban_operation', 'service'),
    '旅游景点': ('urban_operation', 'environment'),
    '休闲娱乐': ('urban_operation', 'event'),
    '运动健身': ('urban_operation', 'service'),
    '教育培训': ('urban_operation', 'service'),
    '文化传媒': ('urban_operation', 'culture'),
    '医疗': ('urban_governance', 'service'),
    '汽车服务': ('urban_operation', 'service'),
    '交通设施': ('urban_governance', 'facility'),
    '道路设施': ('urban_governance', 'facility'),
    '金融': ('urban_operation', 'service'),
    '房地产': ('urban_operation', 'service'),
    '公司企业': ('urban_operation', 'service'),
    '政府机构': ('urban_governance', 'service'),
}


def map_baidu_to_4x5(level1='', level2='', name=''):
    """百度分类 -> (domain, element)。先二级精确，再一级兜底，最后全局 operation x service。"""
    if level2 and level2 in BAIDU_L2_TO_4X5:
        return BAIDU_L2_TO_4X5[level2]
    if level1 and level1 in _L1_FALLBACK:
        return _L1_FALLBACK[level1]
    return ('urban_operation', 'service')


if __name__ == '__main__':
    # 自检：权重和应为 1.0
    assert abs(sum(DOMAIN_WEIGHTS.values()) - 1.0) < 1e-9, 'DOMAIN_WEIGHTS != 1.0'
    assert abs(sum(ELEMENT_WEIGHTS.values()) - 1.0) < 1e-9, 'ELEMENT_WEIGHTS != 1.0'
    print('[OK] DOMAIN_WEIGHTS sum =', sum(DOMAIN_WEIGHTS.values()))
    print('[OK] ELEMENT_WEIGHTS sum =', sum(ELEMENT_WEIGHTS.values()))
    print('[OK] BAIDU_L2_TO_4X5 entries =', len(BAIDU_L2_TO_4X5))
    # 抽样
    for lvl2 in ['中餐厅', '博物馆', '火车站', '公园', '各级政府', '住宅区']:
        print(f'  {lvl2} -> {map_baidu_to_4x5(level2=lvl2)}')
