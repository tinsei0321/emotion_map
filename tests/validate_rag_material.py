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
    """P3-3 素材语义：URP-P01 detail 含 55 准确构成（典型片区类 43 + 机制建设类 12·源自笔记 :43）。

    事实核查（CB-22）：「典型片区类/机制建设类」有真实出处（笔记 codex_0819:43 提炼自 00-03 最新版）·
    「43」= 典型片区类项目数（44.93 亿）·**非**「43 个完整社区」（那是 00-02 老版 2030 目标·已拆到 URP-P11）。
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("urban_renewal_knowledge", _URP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    p01 = next(f for f in mod.PROJECTS if f['id'] == 'URP-P01')
    detail = p01['detail']
    # 55 准确构成（源自笔记 :43·非 LLM 自创）
    assert '典型片区类 43 个' in detail, f'URP-P01 缺「典型片区类 43 个」准确构成（43=典型片区类项目数）: {detail}'
    assert '机制建设类 12 个' in detail, f'URP-P01 缺「机制建设类 12 个」: {detail}'
    assert '污水"厂网一体"示范区 16 个' in detail, 'URP-P01 缺 4 子类拆分（污水厂网一体 16）'
    # 防张冠李戴：不得含「43 个完整社区」错口径（那是 00-02 老版·已拆到 URP-P11）
    assert '43 个完整社区' not in detail, f'URP-P01 仍含「43 个完整社区」错口径（版本混用·应拆到 URP-P11）: {detail}'


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
    """P3-3 检索命中：rag_search('典型片区类 55 个项目') 命中 URP-P01（55 构成·防素材缺漏）。"""
    from tools.rag_index import search
    r = search('宜昌城市更新典型片区类和机制建设项目 55 个', 5)
    assert r.get('ok'), f'检索失败: {r.get("error")}'
    sources = [x['source'] for x in r['results']]
    assert any('URP-P01' in s for s in sources), f'「典型片区类 55 个」未命中 URP-P01: {sources}'


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
