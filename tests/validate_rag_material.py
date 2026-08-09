"""CB-22 三层架构：RAG 素材语义 + 概念库断言（P1/P3 验收·防素材回退）。

1. P3-3 素材语义：URP-P01 detail 含 43 完整社区正确语义（双来源标注·55 与 43 不同口径勿混算）——防「43 典型片区」张冠李戴回归
2. P1 概念库：概念卡 3 类 9 条存在·type='concept' 可检索命中——防概念库缺失
3. 检索命中断言：rag_search('43 个完整社区') 命中 URP-P01·rag_search('什么是情绪地图') 命中 concept

跑：py -m pytest tests/validate_rag_material.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_RAG = Path(__file__).resolve().parent.parent / "tools" / "rag_index.py"
_URP = Path(__file__).resolve().parent.parent / "ai_qa" / "outlet_kb" / "urban_renewal_knowledge.py"
_CONCEPTS = Path(__file__).resolve().parent.parent / "ai_qa" / "outlet_kb" / "concept_knowledge.py"


def test_urp_p01_has_correct_55_composition():
    """P3-3 素材语义：URP-P01 detail 含 55 准确构成（罗列 5 项·无硬造分类·CB-22 素材术语纪律）。

    用户实测（CB-22）：「典型片区类/机制建设类」是非正式工作稿用语·判定不要·**不硬造分类**——
    detail 直接罗列 5 项（污水 16/葛洲坝 12/夷陵 12/红星路-二马路 3/其他项目 12）·「前 4 组合计 43 个」事实描述非分类名。
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("urban_renewal_knowledge", _URP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    p01 = next(f for f in mod.PROJECTS if f['id'] == 'URP-P01')
    detail = p01['detail']
    # 55 准确构成（罗列 5 项·数字自明）
    assert '污水"厂网一体"示范区 16 个' in detail, 'URP-P01 缺罗列（污水厂网一体 16）'
    assert '葛洲坝片区 12 个' in detail, 'URP-P01 缺罗列（葛洲坝 12）'
    assert '夷陵三峡移民老城片区 12 个' in detail, 'URP-P01 缺罗列（夷陵 12）'
    assert '红星路-二马路历史文化街区 3 个' in detail, 'URP-P01 缺罗列（红星路-二马路 3）'
    assert '其他项目 12 个' in detail, 'URP-P01 缺罗列（其他项目 12·排除描述非分类名）'
    assert '前 4 组合计 43 个' in detail, 'URP-P01 缺「前 4 组合计 43 个」事实描述'
    # 素材术语纪律（CB-22 用户实测）：不得含硬造分类标签
    assert '典型片区类' not in detail, f'URP-P01 仍含硬造分类「典型片区类」（用户判定不要·素材术语纪律）: {detail}'
    assert '机制建设类' not in detail, f'URP-P01 仍含硬造分类「机制建设类」（用户判定不要·素材术语纪律）: {detail}'
    assert '43 个完整社区' not in detail, f'URP-P01 仍含「43 个完整社区」错口径（版本混用·应拆到 URP-P11）: {detail}'
    # name 同步去非正式词（Codex 细节 1）
    assert '典型片区' not in p01['name'] and '机制' not in p01['name'], f'URP-P01 name 仍含非正式词: {p01["name"]}'


def test_urp_p01_has_readable_source():
    """A 来源标注可读性：URP-P01 source 用可读完整名称（非内部代号 00-03/260713 版·用户使用逻辑）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("urban_renewal_knowledge", _URP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    p01 = next(f for f in mod.PROJECTS if f['id'] == 'URP-P01')
    src = p01['source']
    assert '宜昌市中心城区城市更新专项规划260713' in src, f'URP-P01 来源缺可读完整名称（须用户能看懂）: {src}'
    assert '00-03' not in src and '260713 版' not in src, f'URP-P01 来源仍用内部代号（用户看不懂）: {src}'
    assert p01.get('source_path'), 'URP-P01 缺 source_path（内部路径·供检索）'


def test_urp_p11_old_version_separated():
    """C 版本口径分离：「43 完整社区」在 URP-P11（00-02 老版·2030 目标）·与 55 项目（00-03 最新）分离防混算。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("urban_renewal_knowledge", _URP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ids = [f['id'] for f in mod.PROJECTS]
    assert 'URP-P11' in ids, '缺 URP-P11（00-02 老版·43 完整社区）'
    p11 = next(f for f in mod.PROJECTS if f['id'] == 'URP-P11')
    assert '43 个完整社区' in p11['detail'], 'URP-P11 缺「43 个完整社区」（00-02 老版口径）'
    assert '0610' in p11['source'], 'URP-P11 来源须标 00-02 老版（0610·防混算）'


def test_concept_knowledge_three_categories():
    """P1 概念库：3 类（产品定位/方法论/边界认知）9 条存在。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("concept_knowledge", _CONCEPTS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cats = {c['topic'] for c in mod.CONCEPTS}
    assert {'产品定位', '方法论', '边界认知'} <= cats, f'概念卡缺类（应 3 类）: {cats}'
    assert len(mod.CONCEPTS) >= 9, f'概念卡 <9 条: {len(mod.CONCEPTS)}'
    for c in mod.CONCEPTS:
        assert 'source' in c and c['source'], f'概念卡缺来源标注（Codex V5·防随意生成）: {c["id"]}'
        assert len(c['detail']) <= 400, f'概念卡超凝练长度: {c["id"]}'


def test_rag_search_hits_urp_p01():
    """P3-3 检索命中：rag_search('宜昌城市更新项目 55 个') 命中 URP-P01（55 构成·防素材缺漏）。"""
    from tools.rag_index import search
    r = search('宜昌城市更新项目 55 个', 5)
    assert r.get('ok'), f'检索失败: {r.get("error")}'
    sources = [x['source'] for x in r['results']]
    assert any('URP-P01' in s for s in sources), f'「宜昌城市更新项目 55 个」未命中 URP-P01: {sources}'


def test_rag_search_hits_urp_p11_not_p01():
    """版本分离：rag_search('43 个完整社区') 命中 URP-P11（00-02 老版）·不命中 URP-P01（55 构成·勿混算）。

    k=8（URP-P11 在 Top-5~8 区间·0.57·与 00-02 笔记同源正确）。
    """
    from tools.rag_index import search
    r = search('43 个完整社区', 8)
    assert r.get('ok'), f'检索失败: {r.get("error")}'
    sources = [x['source'] for x in r['results']]
    assert any('URP-P11' in s for s in sources), f'「43 个完整社区」未命中 URP-P11（00-02 老版）: {sources}'
    assert not any('URP-P01' in s for s in sources), f'「43 个完整社区」误命中 URP-P01（版本混用·应只命中 URP-P11）: {sources}'


def test_rag_search_hits_concept():
    """P1 检索命中：rag_search('什么是情绪地图') 命中 concept 类型（概念库可检索·三级链路消费方）。"""
    from tools.rag_index import search
    r = search('什么是情绪地图', 5)
    assert r.get('ok'), f'检索失败: {r.get("error")}'
    types = [x['type'] for x in r['results']]
    assert 'concept' in types, f'「什么是情绪地图」未命中概念卡: {types}'


# CB-22 杜绝概念创造（两组评估·Codex 漏改发现 + glm 全仓建议）：硬造分类黑名单·全仓素材扫描防残留
_HARDCODED_TERMS = ['典型片区类', '机制建设类']   # 确认硬造（提炼者归纳·源文档无正式分类）·未来新增须人工注册（防误拦官方词）


def test_no_hardcoded_terms_in_materials():
    """① 素材清洁断言：全部向量化素材（fact + note + concept）无硬造分类（防 fact/note 任一残留）。

    全仓语义（Codex）：用户「杜绝」是全仓·非只运行时素材——扫 _load_notes/_load_facts/_load_concepts
    （索引实际加载的全部·含总览报告不在索引但 note 段落覆盖）。
    """
    import tools.rag_index as ri
    chunks = ri._load_facts() + ri._load_notes() + ri._load_concepts()
    assert chunks, '素材加载为空（索引构建异常）'
    for t in _HARDCODED_TERMS:
        hits = [c['source'] for c in chunks if t in c['text']]
        assert not hits, f'素材仍含硬造分类「{t}」（杜绝概念创造·CB-22）: {hits}'


def test_retrieval_injection_clean():
    """① 素材清洁断言（用户复测路径）：rag_search('宜昌有哪些更新项目') 注入素材无硬造分类。"""
    from tools.rag_index import search
    r = search('宜昌有哪些更新项目', 5)
    assert r.get('ok'), f'检索失败: {r.get("error")}'
    for x in r['results']:
        txt = x.get('text', '')
        for t in _HARDCODED_TERMS:
            assert t not in txt, f'检索注入素材仍含硬造分类「{t}」（用户复测会看到）: {x["source"]}'
