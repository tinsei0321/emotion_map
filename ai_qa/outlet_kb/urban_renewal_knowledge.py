"""城市更新知识事实卡（L1.5 数据层 · CB-22b/22c）。

从 L0 资料库（docs/urban-renewal-plan/ 提炼笔记）确定性提取的结构化事实卡——
供 B 路径 query_knowledge_base（确定性查询）+ RAG 向量化（rag_index _load_facts）共用。

**schema**：{id, city, region, topic, name, detail(≤80字), dimension, year, keywords, source}
- dimension：数据维度（住房/小区/社区/街区/城区/城中村专项/方法论）——颗粒度原则：结论细粒度=数据来源维度
- source：_INDEX 编号 / G 盘相对路径（可溯源·防张冠李戴）

**来源**：三组提炼笔记（claude/codex/glm·2026-08-09）·真实数据·非 LLM 编造。
"""
from __future__ import annotations

# CB-22f D5（B 路径收尾）：追踪埋点——query_knowledge_base 是公开函数（MOD_AIQA.F_016·编号连续 F_015 rag_search 后）
try:
    from core.tracker import track
except Exception:  # 独立调试兜底
    def track(*a, **k):
        def deco(f):
            return f
        return deco

# ── 更新项目（PROJECTS）──────────────────────────────────────────
PROJECTS = [
    {'id': 'URP-P01', 'city': '宜昌', 'region': '中心城区', 'topic': 'project',
     'name': '2025-2027 城市更新项目（55 个）', 'detail': '2025-2027 拟实施城市更新项目 55 个·总投资 51.33 亿元：'
     '污水"厂网一体"示范区 16 个 20.14 亿 / 葛洲坝片区 12 个 11.07 亿 / '
     '夷陵三峡移民老城片区 12 个 6.15 亿 / 红星路-二马路历史文化街区 3 个 7.57 亿 / '
     '其他项目 12 个 6.39 亿（前 4 组合计 43 个·44.93 亿）',
     'dimension': '片区', 'year': '2025-2027', 'keywords': '更新项目 城市更新项目 污水厂网一体 葛洲坝 夷陵三峡移民 红星路二马路',
     'source': '宜昌市中心城区城市更新专项规划260713（阶段性成果 PDF 版）·项目库章节（2026.7 最新版）', 'source_path': 'docs/urban-renewal-plan/_笔记/codex_0819_260713_2026-08-09.md#43'},
    {'id': 'URP-P11', 'city': '宜昌', 'region': '中心城区', 'topic': 'project',
     'name': '2030 核心目标（老版口径）', 'detail': '2030 核心目标（00-02 阶段性成果 0610 老版口径·勿与 00-03 最新版 55 项目混算）：'
     '5 个重点片区更新完成（葛洲坝/老城中心/环三峡大学/滨江商务/小溪塔中心）·2005 年前老旧小区全部更新·21 个片区 + 32 个城中村改造·'
     '"1 园 4 厂"老旧厂区 + 43 个完整社区建设 + 10-15 平方公里低效用地盘活·二马路/织布街历史文化街区活化',
     'dimension': '片区', 'year': '2030', 'keywords': '2030 核心目标 完整社区 重点片区 城中村 低效用地',
     'source': '宜昌市中心城区城市更新专项规划0610（阶段性成果 PDF 版）·核心目标章节（2026.6 老版）', 'source_path': 'docs/urban-renewal-plan/_笔记/codex_0819_260713_2026-08-09.md#00-02(0610)'},
    {'id': 'URP-P02', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'project',
     'name': '葛洲坝片区更新项目', 'detail': '12 个·11.07 亿',
     'dimension': '片区', 'year': '2025-2027', 'keywords': '葛洲坝 项目 投资',
     'source': '宜昌市中心城区城市更新专项规划260713（阶段性成果 PDF 版）·项目库章节', 'source_path': 'docs/urban-renewal-plan/_INDEX#00-03(260713)'},
    {'id': 'URP-P03', 'city': '宜昌', 'region': '伍家岗区', 'topic': 'project',
     'name': '危旧房改造', 'detail': '入库 4 栋 C/D + 45 栋危旧 + 36 栋非成套·16.4 亿',
     'dimension': '住房', 'year': '十五五', 'keywords': '危旧房 改造 投资',
     'source': 'docs/urban-renewal-plan/_INDEX#00-04(伍家岗十五五)'},
    {'id': 'URP-P04', 'city': '宜昌', 'region': '伍家岗区', 'topic': 'project',
     'name': '汉宜村安置房', 'detail': '1960 套·18.06 亿',
     'dimension': '城中村专项', 'year': '十五五', 'keywords': '汉宜村 安置 城中村',
     'source': 'docs/urban-renewal-plan/_INDEX#00-04(伍家岗十五五)'},
    {'id': 'URP-P05', 'city': '宜昌', 'region': '老城中心', 'topic': 'project',
     'name': '老城中心片区更新', 'detail': '16 个·16.6 亿',
     'dimension': '片区', 'year': '2025-2027', 'keywords': '老城中心 项目 投资',
     'source': 'docs/urban-renewal-plan/_INDEX#00-03(260713)'},
    {'id': 'URP-P06', 'city': '宜昌', 'region': '红星路-二马路', 'topic': 'project',
     'name': '红星路-二马路历史文化街区', 'detail': '3 个·7.57 亿',
     'dimension': '街区', 'year': '2025-2027', 'keywords': '历史街区 二马路 投资',
     'source': 'docs/urban-renewal-plan/_INDEX#00-03(260713)'},
    {'id': 'URP-P07', 'city': '宜昌', 'region': '伍家岗区', 'topic': 'project',
     'name': '静态交通停车场', 'detail': '40 个停车场·6200 泊位',
     'dimension': '城区', 'year': '十五五', 'keywords': '停车 停车场 泊位',
     'source': 'docs/urban-renewal-plan/_INDEX#00-04(伍家岗十五五)'},
    {'id': 'URP-P08', 'city': '宜昌', 'region': '伍家岗区', 'topic': 'project',
     'name': '完整社区建设', 'detail': '优先 16 个社区·约 2940 万',
     'dimension': '社区', 'year': '十五五', 'keywords': '完整社区 建设',
     'source': 'docs/urban-renewal-plan/_INDEX#00-04(伍家岗十五五)'},
]

# ── 体检指标数值（INDICATORS）────────────────────────────────────
INDICATORS = [
    {'id': 'URP-I01', 'city': '宜昌', 'region': '中心城区', 'topic': 'indicator',
     'name': '结构安全隐患住宅', 'detail': '42 栋',
     'dimension': '住房', 'year': '2025', 'keywords': '结构隐患 危房 住宅',
     'source': 'docs/urban-renewal-plan/_INDEX#03-01(附件1)'},
    {'id': 'URP-I02', 'city': '宜昌', 'region': '中心城区', 'topic': 'indicator',
     'name': '围护安全隐患住宅', 'detail': '454 栋',
     'dimension': '住房', 'year': '2025', 'keywords': '围护隐患 漏水 住宅',
     'source': 'docs/urban-renewal-plan/_INDEX#03-01(附件1)'},
    {'id': 'URP-I03', 'city': '宜昌', 'region': '中心城区', 'topic': 'indicator',
     'name': '停车泊位缺口', 'detail': '140 个小区',
     'dimension': '小区', 'year': '2025', 'keywords': '停车 泊位 缺口 小区',
     'source': 'docs/urban-renewal-plan/_INDEX#03-01(附件1)'},
    {'id': 'URP-I04', 'city': '宜昌', 'region': '中心城区', 'topic': 'indicator',
     'name': '小学学位缺口', 'detail': '31 所·李家湖 400 个',
     'dimension': '小区', 'year': '2025', 'keywords': '学位 小学 缺口',
     'source': 'docs/urban-renewal-plan/_INDEX#03-01(附件1)'},
    {'id': 'URP-I05', 'city': '宜昌', 'region': '中心城区', 'topic': 'indicator',
     'name': '中学覆盖率', 'detail': '56.10%·生物产业园 0%',
     'dimension': '街区', 'year': '2025', 'keywords': '中学 覆盖率',
     'source': 'docs/urban-renewal-plan/_INDEX#03-01(附件1)'},
    {'id': 'URP-I06', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'indicator',
     'name': '完整社区达标率', 'detail': '19%·仅 6 社区达标',
     'dimension': '社区', 'year': '2025', 'keywords': '完整社区 达标率',
     'source': 'docs/urban-renewal-plan/_INDEX#03-05(葛洲坝)'},
    {'id': 'URP-I07', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'indicator',
     'name': '停车设施专项体检·泊位结构', 'detail': '92:6:2（不达标·标准≥85:10-15:≤5）',
     'dimension': '城区', 'year': '2025', 'keywords': '停车 泊位结构 体检',
     'source': 'docs/urban-renewal-plan/_INDEX#03-04(停车专项)'},
    {'id': 'URP-I08', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'indicator',
     'name': '低效用地面积', 'detail': '葛洲坝片区 285.9 公顷·工业占 54%',
     'dimension': '片区', 'year': '2025', 'keywords': '低效用地 面积 工业',
     'source': 'docs/urban-renewal-plan/_INDEX#03-05(葛洲坝)'},
]

# ── 体检问题清单（CHECKUP_ISSUES）──────────────────────────────
CHECKUP_ISSUES = [
    {'id': 'URP-C01', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'issue',
     'name': '葛洲坝体检问题·五大方面', 'detail': '既有建筑/完整社区/老旧街区/公服短板/基础设施',
     'dimension': '片区', 'year': '2025', 'keywords': '葛洲坝 体检 问题',
     'source': 'docs/urban-renewal-plan/_INDEX#03-05(葛洲坝)'},
    {'id': 'URP-C02', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'issue',
     'name': '历史建筑空置率', 'detail': '100%·西坝甲街/皂角树民居未活化',
     'dimension': '街区', 'year': '2025', 'keywords': '历史建筑 空置 活化',
     'source': 'docs/urban-renewal-plan/_INDEX#03-05(葛洲坝)'},
    {'id': 'URP-C03', 'city': '宜昌', 'region': '中心城区', 'topic': 'issue',
     'name': '未实施物业管理小区', 'detail': '273 个',
     'dimension': '小区', 'year': '2025', 'keywords': '物业 管理 小区',
     'source': 'docs/urban-renewal-plan/_INDEX#03-01(附件1)'},
    {'id': 'URP-C04', 'city': '宜昌', 'region': '中心城区', 'topic': 'issue',
     'name': '消防 5 分钟可达覆盖率', 'detail': '59.69%（标准 100%）',
     'dimension': '城区', 'year': '2024', 'keywords': '消防 覆盖 安全',
     'source': 'docs/urban-renewal-plan/_INDEX#03-06(2024体检)'},
]

# ── 更新片区（PANELS）────────────────────────────────────────────
PANELS = [
    {'id': 'URP-A01', 'city': '宜昌', 'region': '中心城区', 'topic': 'panel',
     'name': '重点更新片区（5 个）', 'detail': '葛洲坝/老城中心/环三峡大学/滨江商务/小溪塔中心',
     'dimension': '片区', 'year': '2025-2030', 'keywords': '重点片区 更新',
     'source': 'docs/urban-renewal-plan/_INDEX#00-02/00-03'},
    {'id': 'URP-A02', 'city': '宜昌', 'region': '中心城区', 'topic': 'panel',
     'name': '更新片区（23 个）', 'detail': '0.5-3 平方公里·四大分类（功能活力/宜居品质/产业迭代/历史街区）',
     'dimension': '片区', 'year': '2026', 'keywords': '更新片区 分类 23',
     'source': 'docs/urban-renewal-plan/_INDEX#00-01(0809)'},
    {'id': 'URP-A03', 'city': '宜昌', 'region': '伍家岗区', 'topic': 'panel',
     'name': '伍家岗重点更新片区（10 个）', 'detail': '滨江商务/五一广场/临江溪/双创产业园等·住区/园区/景区三类',
     'dimension': '片区', 'year': '十五五', 'keywords': '伍家岗 片区 10',
     'source': 'docs/urban-renewal-plan/_INDEX#00-04(伍家岗十五五)'},
]

# ── 案例方法论（CASES·由 case_library point 派生）────────────
CASES = [
    {'id': 'URP-K01', 'city': '湖北宜昌', 'region': '葛洲坝片区', 'topic': 'case',
     'name': '望洲岗原拆原建', 'detail': '坝坝会+入户+算账说服·全量评论流替代小样本问卷',
     'dimension': '方法论', 'year': '2025', 'keywords': '望洲岗 原拆原建 示范',
     'source': 'ai_qa/outlet_kb/case_library.py#yichang_wangzhou'},
    {'id': 'URP-K02', 'city': '上海', 'region': '上海市', 'topic': 'case',
     'name': '上海体检满意度调查', 'detail': '线上问卷+社区座谈·一表三清单·问卷低分项情绪定位',
     'dimension': '方法论', 'year': '2025', 'keywords': '上海 满意度 调查 方法论',
     'source': 'ai_qa/outlet_kb/case_library.py#shanghai_satisfaction'},
    {'id': 'URP-K03', 'city': '南京', 'region': '南京市', 'topic': 'case',
     'name': '南京大数据定位交通断点', 'detail': '大数据+问卷+踏勘·客观位置与主观感受双重证据',
     'dimension': '方法论', 'year': '2024', 'keywords': '南京 大数据 交通 方法论',
     'source': 'ai_qa/outlet_kb/case_library.py#nanjing_bigdata'},
    {'id': 'URP-K04', 'city': '广州', 'region': '广州市', 'topic': 'case',
     'name': '广州体检满意度调查', 'detail': '线上问卷+进社区意见征询+观察员·四好框架·青年专项对焦',
     'dimension': '方法论', 'year': '2025', 'keywords': '广州 满意度 四好 方法论',
     'source': 'ai_qa/outlet_kb/case_library.py#guangzhou_satisfaction'},
    {'id': 'URP-K05', 'city': '宁夏', 'region': '宁夏', 'topic': 'case',
     'name': '宁夏编制导则标准', 'detail': '专项规划/片区策划成果标准表格图件·图文字数一致',
     'dimension': '方法论', 'year': '2024', 'keywords': '宁夏 编制导则 标准 方法论',
     'source': 'ai_qa/outlet_kb/case_library.py#ningxia_guideline'},
]

# ── 政策要点（POLICIES·gist 级）────────────────────────────────
POLICIES = [
    {'id': 'URP-L01', 'city': '国家', 'region': '全国', 'topic': 'policy',
     'name': '城市更新行动意见', 'detail': '专项规划-片区策划-项目实施方案三级体系·8 大任务',
     'dimension': '方法论', 'year': '2025', 'keywords': '城市更新 意见 三级体系',
     'source': 'docs/urban-renewal-plan/_INDEX#01-01(中办国办)'},
    {'id': 'URP-L02', 'city': '国家', 'region': '全国', 'topic': 'policy',
     'name': '防止大拆大建', 'detail': '拆≤20%·拆建比≤2·就地就近安置≥50%',
     'dimension': '方法论', 'year': '2021', 'keywords': '大拆大建 底线 拆建比',
     'source': 'docs/urban-renewal-plan/_INDEX#01-02(建科63号)'},
    {'id': 'URP-L03', 'city': '国家', 'region': '全国', 'topic': 'policy',
     'name': '城市更新专项规划编制导则', 'detail': '规划期 5 年·适用 4 类城市·内容 7 项',
     'dimension': '方法论', 'year': '2025', 'keywords': '编制导则 46号 专项规划',
     'source': 'docs/urban-renewal-plan/_笔记/glm_05编制导则'},
    {'id': 'URP-L04', 'city': '宜昌', 'region': '宜昌', 'topic': 'policy',
     'name': '宜昌城市更新行动方案', 'detail': '"1+4+N"机制·三个聚焦·危旧房市场化路径',
     'dimension': '方法论', 'year': '2025-2027', 'keywords': '宜昌 行动方案 1+4+N',
     'source': 'docs/urban-renewal-plan/_INDEX#01-11(宜昌行动方案)'},
]

# ── 指标体系（METRICS_SYSTEM·框架与数值分离）────────────────────
METRICS_SYSTEM = [
    {'id': 'URP-M01', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'metric',
     'name': '片区体检指标（20 项）', 'detail': '既有建筑/老旧小区/完整社区/老旧街区/公服/基础设施/生态/历史 8 方面',
     'dimension': '方法论', 'year': '2025', 'keywords': '体检指标 20项 片区',
     'source': 'docs/urban-renewal-plan/_INDEX#03-05(葛洲坝)'},
    {'id': 'URP-M02', 'city': '宜昌', 'region': '伍家岗区', 'topic': 'metric',
     'name': '区十五五指标（40 项）', 'detail': '住房保障/城市宜居/市政设施/城市韧性 6 大类',
     'dimension': '方法论', 'year': '十五五', 'keywords': '伍家岗 40项 指标',
     'source': 'docs/urban-renewal-plan/_INDEX#00-04(伍家岗十五五)'},
    {'id': 'URP-M03', 'city': '宜昌', 'region': '中心城区', 'topic': 'metric',
     'name': '更新指标（21 项细化）', 'detail': '安全韧性 10/服务群众 6/赋能潜力 5·危旧房 294→386 等',
     'dimension': '方法论', 'year': '2027-2030', 'keywords': '更新指标 21项 细化',
     'source': 'docs/urban-renewal-plan/_INDEX#00-04(说明书0714)'},
]


def all_facts():
    """全部事实卡（供 query_knowledge_base / rag_index 检索）。"""
    return (PROJECTS + INDICATORS + CHECKUP_ISSUES + PANELS + CASES + POLICIES + METRICS_SYSTEM)


@track("MOD_AIQA.F_016", track_args=False)
def query_knowledge_base(query='', city='宜昌', topic=None, keyword=None, limit=5):
    """B 路径：确定性查询事实卡（关键词精确 WHERE·非向量·CB-22f D5 收尾）。

    场景：精确数字类问（"55 个分别是什么"/"葛洲坝几个项目"）——向量模糊时·确定性兜底。
    匹配链：① 关键词命中 fact 的 keywords/region/name/topic ② 再按 topic 过滤 ③ Top-N 兜底。
    返回与 RAG 结果同构（可混合注入 finalStep 素材）：[{id,name,detail,dimension,year,source,region,topic}]。
    """
    if not query and not keyword and not topic:
        return []
    facts = all_facts()
    if city:
        facts = [f for f in facts if f.get('city') == city or city in str(f.get('city', ''))]
    scored = []
    for f in facts:
        s = 0
        hay = ' '.join([str(f.get(k, '')) for k in ('keywords', 'region', 'name', 'topic', 'detail')])
        for kw in (keyword or '').split():
            if kw and kw in hay:
                s += 1
        if query:
            # query 清洗：去疑问词/量词 → fact 的 keywords/region 是否作为子串出现在 query 中（中文无空格·整串反查）
            #   「葛洲坝片区几个项目」→ 反查 fact keywords 含「葛洲坝」→ 命中（比正查稳·防滑窗噪音）
            _qclean = query.replace('有哪些', '').replace('是什么', '').replace('多少', '').replace('几个', '').replace('多少', '').strip()
            for _kw in (str(f.get('keywords', '')).split() + [str(f.get('region', ''))]):
                if len(_kw) >= 2 and _kw in _qclean:
                    s += 1
        if topic and topic == f.get('topic'):
            s += 2
        if s > 0:
            scored.append((s, f))
    scored.sort(key=lambda x: -x[0])
    return [{
        'id': f['id'], 'name': f['name'], 'detail': f['detail'], 'dimension': f.get('dimension', ''),
        'year': f.get('year', ''), 'source': f.get('source', ''), 'region': f.get('region', ''),
        'topic': f.get('topic', ''), 'keywords': f.get('keywords', ''),
    } for _s, f in scored[:limit]]


if __name__ == '__main__':
    facts = all_facts()
    print(f'[OK] 事实卡总数: {len(facts)}')
    from collections import Counter
    print('  分类:', dict(Counter(f['topic'] for f in facts)))
    print('  维度:', dict(Counter(f['dimension'] for f in facts)))
    # schema 校验
    for f in facts:
        for k in ('id', 'city', 'region', 'topic', 'name', 'detail', 'dimension', 'year', 'keywords', 'source'):
            assert k in f, f'{f["id"]} 缺 {k}'
        assert len(f['detail']) <= 80, f'{f["id"]} detail 超 80 字'
    print('[OK] 事实卡 schema 校验通过')
