"""
4x5 矩阵映射 + 领域/要素权重
============================
吸收自 docs/minimax-workspace/docs/poi-mapping-4x5.md（参考包），供：
  1. POI 种子已预映射（见 yichang_poi_wgs84.json / amap_poi_wgs84.json 的 domain/element 字段）；
  2. 高德真实 POI 按本表判 domain/element —— 本表是高德→4×5 的【唯一权威源】，
     pull_amap_poi.AMAP_TYPES 经本表派生 domain/element（单源，勿在他处重复硬编码）；
  3. pick_domain_element() 的基础权重（背景点无具体 POI 时按分布采样）。

矩阵：domain（规划/更新/运营/治理）x element（设施/环境/服务/文化/事件）= 20 格。
与 7 类情绪（喜怒哀乐愁急盼）正交——deep 4x5 交叉分析留 L3/L4。

历史：旧 BAIDU_L2_TO_4X5 / _L1_FALLBACK / map_baidu_to_4x5 为百度类名死码（零调用 +
高德数据不匹配全 fallback），已删；高德 13 大类映射统一收敛到下方 AMAP_L1_TO_4X5。
memory `grid-4x5-attribution`。
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

# ── 高德 POI 大类 → (domain, element) 单一权威映射 ──
# 与 pull_amap_poi.AMAP_TYPES 一一对应（typecode 050000~170000，13 大类）；
# pull_amap_poi 拉取时经本表派生 domain/element 写入 seed，generate_l1_mock 80% 概率继承。
# 高德官方大类中未在本表/未拉取的类（公共设施/道路附属/社会保障等）→ map_amap_to_4x5 落默认。
AMAP_L1_TO_4X5 = {
    # 体验愉悦型（打卡/休闲/美食/购物/住宿）
    '餐饮服务': ('urban_operation', 'service'),
    '购物服务': ('urban_operation', 'service'),
    '生活服务': ('urban_operation', 'service'),
    '休闲娱乐': ('urban_operation', 'event'),
    '体育休闲服务': ('urban_operation', 'event'),
    '住宿服务': ('urban_operation', 'service'),
    '风景名胜': ('urban_operation', 'environment'),
    # 文化
    '科教文化服务': ('urban_operation', 'culture'),
    # 摩擦型（住宅/物业/办事/交通/金融）
    '商务住宅': ('urban_renewal', 'service'),           # 住宅小区/写字楼
    '政府机构及社会团体': ('urban_governance', 'service'),
    '交通设施服务': ('urban_governance', 'facility'),
    '金融保险服务': ('urban_operation', 'service'),
    '公司企业': ('urban_operation', 'service'),
}


def map_amap_to_4x5(level1='', name=''):
    """高德大类 -> (domain, element)。先 AMAP_L1_TO_4X5 精确命中，miss 落全局 operation x service。
    level1 取高德 POI 大类中文名（pull_amap_poi 存入 seed 的 baidu_level1 字段=高德中文名）。
    name 预留（未来按 POI 名称关键词回退），当前未用。"""
    if level1 and level1 in AMAP_L1_TO_4X5:
        return AMAP_L1_TO_4X5[level1]
    return ('urban_operation', 'service')


if __name__ == '__main__':
    # 自检：权重和应为 1.0
    assert abs(sum(DOMAIN_WEIGHTS.values()) - 1.0) < 1e-9, 'DOMAIN_WEIGHTS != 1.0'
    assert abs(sum(ELEMENT_WEIGHTS.values()) - 1.0) < 1e-9, 'ELEMENT_WEIGHTS != 1.0'
    print('[OK] DOMAIN_WEIGHTS sum =', sum(DOMAIN_WEIGHTS.values()))
    print('[OK] ELEMENT_WEIGHTS sum =', sum(ELEMENT_WEIGHTS.values()))
    print('[OK] AMAP_L1_TO_4X5 entries =', len(AMAP_L1_TO_4X5))
    # 抽样（高德大类 + 一条未收录类验证默认兜底）
    for lvl1 in ['餐饮服务', '风景名胜', '交通设施服务', '政府机构及社会团体', '商务住宅', '未收录类']:
        print('  {} -> {}'.format(lvl1, map_amap_to_4x5(level1=lvl1)))
