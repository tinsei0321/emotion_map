"""行业知识库 · 城市治理领域权威源（v1）。

领域定位：城市基层治理与运行管理（党建引领基层治理）——"人民城市"理念、网格化管理（主动发现/
精细化）、12345 接诉即办（被动响应/三率考评）。聚焦交通拥堵/停车/施工扰民/环境秩序/市容市貌/
投诉热点。EMC 的 12345 热线数据源即本领域。

归因底层逻辑（政策→情绪→项目）：人民城市/基层治理现代化政策（人民满意导向）→ 情绪地图归因
（市民投诉/负面聚集的痛点定位，"急难愁盼"）→ 指向具体治理项目（点位处置/专项整治）。

**本模块是该领域的单一权威源**；做厚路径（接诉即办三率细则/各地交通治堵/网格化标准等）
见 docs/industry-knowledge-base.md。
"""

DOMAIN_KEY = 'urban_governance'
NAME = '城市治理'
AUTHORITY = '党委政法委/基层治理办 / 城管 / 12345 政务服务热线 / 街道乡镇'
LAST_UPDATED = '2026-07-15'

TOP_DESIGN = [
    {'policy': '人民城市理念', 'doc': '习近平 2019 上海考察', 'year': '2019',
     'url': 'http://naes.org.cn/cj_zwz/zczx/lldt/202507/t20250723_5890653.shtml',
     'gist': '"人民城市人民建，人民城市为人民"，以人民为中心的城市发展思想'},
    {'policy': '关于进一步深化接诉即办改革的意见', 'doc': '中共北京市委', 'year': '2024',
     'url': 'https://zwfwj.beijing.gov.cn/zwgk/2024zcwj/202506/t20250623_4119758.html',
     'gist': '12345 市民服务热线驱动超大城市治理，三率（响应率/解决率/满意率）考评'},
    {'policy': '关于加强基层治理体系和治理能力现代化建设的实施意见', 'doc': '各地（北京等）', 'year': '2022+',
     'url': 'https://www.bjdj.gov.cn/article/38887.html',
     'gist': '网格化与接诉即办有机衔接、街乡吹哨部门报到'},
]

CORE_FRAMEWORK = {
    '人民城市': '城市建设的出发点和落脚点是满足人民群众对美好生活的向往（以人民为中心）',
    '网格化管理': '把城市划分为网格单元，主动巡查、精细化管理（部件/事件）',
    '12345 接诉即办': '以市民诉求驱动治理：12345 热线接诉→派单→部门办理→三率考评',
    '三率考评': '响应率 / 解决率 / 满意率——接诉即办核心考评指标',
    '吹哨报到': '街乡吹哨、部门报到——基层协调联动机制',
    '每月一题': '聚焦高频共性问题专项治理（接诉即办深化）',
    '新时代枫桥经验（城市版）': '矛盾不上交、就地解决的城市基层治理范式',
}

KEY_TERMS = {
    '人民城市': '以人民为中心的城市发展理念',
    '接诉即办': '12345 市民热线接诉→即办→三率考评',
    '网格化': '城市网格单元的主动巡查与精细化管理',
    '三率': '响应率/解决率/满意率',
    '吹哨报到': '街乡吹哨、部门报到',
    '急难愁盼': '市民紧急/困难/愁苦/期盼的高频共性问题',
}

METRICS_BASELINE = [
    '接诉即办三率：响应率 / 解决率 / 满意率（北京解决率从 53%→85%）',
    '12345 整合多渠道热线（北京整合 54 条），日均万件级',
    '网格化事件处置闭环（发现→派遣→处置→核查→评价）',
    '每月一题：聚焦高频共性问题',
]

PROJECT_TYPES = [
    '交通拥堵点位治理', '停车难治理（路内/路外/共享停车）', '施工扰政治理',
    '环境秩序/市容市貌整治', '投诉热点（12345）专项整治', '垃圾分类治理',
    '网格化事件处置', '每月一题专项',
]

CASES = [
    {'city': '北京', 'project': '12345 接诉即办', 'point': '市民诉求驱动治理、三率考评、每月一题'},
    {'city': '上海', 'project': '一网统管+网格化', 'point': '主动发现与接诉响应结合'},
    {'city': '各地', 'project': '交通治堵/停车治理', 'point': '拥堵点位工程改造+信号优化+停车扩容'},
    {'city': '宜昌（本项目所在）', 'project': '12345 热线/城管', 'point': 'EMC 12345 数据源归因（交通/停车/施工）'},
]

EMOTION_FOCUS = (
    '市民对治理痛点的反映（12345 投诉/负面情绪聚集）：交通拥堵、停车难、施工扰民、环境脏乱、'
    '市容秩序、物业纠纷等"急难愁盼"。情绪归因指向具体治理项目（拥堵点位工程改造、停车扩容、'
    '施工时段/围挡优化、脏乱点位整治、投诉热点专项）。EMC 用情绪数据定位"痛点在哪"，对接接诉即办'
    '"解决率/满意率"目标。'
)

MATRIX_MAPPING = [
    ('urban_governance', '服务', '主'),   # 政务服务/物业/公共服务体验（接诉即办核心）
    ('urban_governance', '环境', '主'),   # 环境秩序/市容市貌/脏乱治理
    ('urban_governance', '设施', '主'),   # 交通/停车/市政设施治理
    ('urban_governance', '事件', '次'),   # 突发/投诉事件处置
    ('urban_operation', '环境', '次'),    # 舆情/负面聚集的运营监测
    ('urban_renewal', '环境', '次'),      # 更新中施工扰民/秩序治理
]

ELEMENT_HINTS = {
    '服务': '政务服务/物业/公共服务体验、12345 接诉即办',
    '环境': '环境秩序/市容市貌/脏乱差/空气水质治理',
    '设施': '交通拥堵治理、停车、市政设施维护',
    '事件': '突发投诉/聚集事件处置、每月一题专项；大型活动相关的秩序维护/散场交通拥堵/聚集安全治理（接诉即办响应侧）',
}

SOURCES = [
    '人民城市理念：http://naes.org.cn/cj_zwz/zczx/lldt/202507/t20250723_5890653.shtml',
    '北京接诉即办深化意见：https://zwfwj.beijing.gov.cn/zwgk/2024zcwj/202506/t20250623_4119758.html',
    '北京基层治理现代化实施意见：https://www.bjdj.gov.cn/article/38887.html',
    '人民网：接诉即办与人民城市',
]


if __name__ == '__main__':
    assert DOMAIN_KEY == 'urban_governance'
    for fld in ('TOP_DESIGN', 'PROJECT_TYPES', 'CASES', 'MATRIX_MAPPING', 'SOURCES'):
        v = globals()[fld]
        assert isinstance(v, list) and v, f'{fld} 应为非空 list'
    for dd in TOP_DESIGN:
        for k in ('policy', 'doc', 'year', 'gist'):
            assert k in dd, f'TOP_DESIGN 缺 {k}'
    for domain, element, role in MATRIX_MAPPING:
        assert role in ('主', '次')
        assert element in ('设施', '环境', '服务', '文化', '事件')
        assert domain in ('urban_planning', 'urban_renewal', 'urban_operation', 'urban_governance')
    print(f'[OK] {NAME}（{DOMAIN_KEY}）自检通过 | 政策{len(TOP_DESIGN)} 概念{len(CORE_FRAMEWORK)} '
          f'术语{len(KEY_TERMS)} 项目类型{len(PROJECT_TYPES)} 案例{len(CASES)} 矩阵映射{len(MATRIX_MAPPING)}')
