"""RAG 黄金集（CB-22 深度评估·3 类·供 tools/rag_eval.py 评估检索质量）。

3 类（对齐 glm 刚性区分）：
- recall（正确召回）·10-15 条·断言 Top-K 含期望 source（召回率 ≥80%·软指标）
- dimension（越维降级）·3-5 条·断言回答含"无法到更细维度"声明（刚性 100%·原则红线）
- case_data（案例不引数据）·3-5 条·断言检索 Top-K 不含他城数据（刚性 100%·防张冠李戴）

期望 source 用关键词（source 含片段即可·防路径硬编码脆弱）。
"""
GOLD_SET = [
    # ── ① 正确召回（recall）──────────────────────────────────
    {'type': 'recall', 'query': '宜昌市城市更新有哪些项目',
     'expect_kw': ['urban_renewal_knowledge', '0819_260713'],
     'k': 5, 'note': '更新项目'},
    {'type': 'recall', 'query': '葛洲坝片区停车泊位缺口',
     'expect_kw': ['urban_renewal_knowledge', '停车'],
     'k': 5, 'note': '停车缺口（曾 Top-1 南京·须本地）'},
    {'type': 'recall', 'query': '伍家岗危旧房改造项目',
     'expect_kw': ['urban_renewal_knowledge', '伍家岗'],
     'k': 5, 'note': '危旧房 16.4 亿'},
    {'type': 'recall', 'query': '葛洲坝片区体检有什么问题',
     'expect_kw': ['葛洲坝', '体检'],
     'k': 5, 'note': '葛洲坝体检'},
    {'type': 'recall', 'query': '宜昌历史建筑空置率',
     'expect_kw': ['urban_renewal_knowledge', '历史建筑'],
     'k': 5, 'note': '历史建筑 100%'},
    {'type': 'recall', 'query': '城市更新防止大拆大建底线',
     'expect_kw': ['urban_renewal_knowledge', '大拆大建'],
     'k': 5, 'note': '政策底线'},
    {'type': 'recall', 'query': '宜昌重点更新片区有哪些',
     'expect_kw': ['urban_renewal_knowledge', '重点更新片区'],
     'k': 5, 'note': '5 重点片区'},
    {'type': 'recall', 'query': '汉宜村安置房多少钱',
     'expect_kw': ['urban_renewal_knowledge', '汉宜村'],
     'k': 5, 'note': '汉宜村安置'},
    {'type': 'recall', 'query': '城市更新专项规划编制导则',
     'expect_kw': ['编制导则', 'urban_renewal_knowledge'],
     'k': 5, 'note': '编制导则 46 号'},
    {'type': 'recall', 'query': '中学覆盖率不足',
     'expect_kw': ['urban_renewal_knowledge', '中学'],
     'k': 5, 'note': '中学覆盖率'},

    # ── ② 越维降级（dimension·刚性 100%）────────────────────
    {'type': 'dimension', 'query': '葛洲坝片区 12 个项目中具体是哪几栋危房',
     'expect_dim': '片区', 'k': 5, 'note': '数据到片区·问栋→须降级声明'},
    {'type': 'dimension', 'query': '宜昌停车泊位缺口具体到哪栋楼',
     'expect_dim': '小区', 'k': 5, 'note': '数据到小区·问栋→须降级'},

    # ── ③ 案例不引数据（case_data·刚性 100%）────────────────
    {'type': 'case_data', 'query': '宜昌停车难怎么治理',
     'forbid_kw': ['南京', '87.65', 'nanjing'], 'k': 5, 'note': '不得返回南京数据作为宜昌答案'},
    {'type': 'case_data', 'query': '城市体检满意度调查方法',
     'forbid_kw': ['45,578', '93.60', '6.5 万'], 'k': 5, 'note': '他城数值不得进检索'},
]
