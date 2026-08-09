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


def test_urp_p01_has_correct_43_semantics():
    """P3-3 素材语义：URP-P01 detail 含 43 完整社区正确语义（防张冠李戴回退·「43」=完整社区非典型片区）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("urban_renewal_knowledge", _URP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    p01 = next(f for f in mod.PROJECTS if f['id'] == 'URP-P01')
    detail = p01['detail']
    assert '43 个完整社区' in detail, f'URP-P01 缺「43 个完整社区」正确语义（曾张冠李戴到典型片区）: {detail}'
    assert '00-02' in p01['source'], 'URP-P01 双来源标注缺失（55=00-03·43=00-02·防混算）'
    assert '勿混算' in detail, 'URP-P01 缺口径区分提示（43 完整社区与 55 项目不同口径）'


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
    """P3-3 检索命中：rag_search('43 个完整社区') 命中 URP-P01（防素材缺漏）。"""
    from tools.rag_index import search
    r = search('43 个完整社区', 5)
    assert r.get('ok'), f'检索失败: {r.get("error")}'
    sources = [x['source'] for x in r['results']]
    assert any('URP-P01' in s for s in sources), f'「43 个完整社区」未命中 URP-P01: {sources}'


def test_rag_search_hits_concept():
    """P1 检索命中：rag_search('什么是情绪地图') 命中 concept 类型（概念库可检索·三级链路消费方）。"""
    from tools.rag_index import search
    r = search('什么是情绪地图', 5)
    assert r.get('ok'), f'检索失败: {r.get("error")}'
    types = [x['type'] for x in r['results']]
    assert 'concept' in types, f'「什么是情绪地图」未命中概念卡: {types}'
