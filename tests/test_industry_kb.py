"""EMC 行业知识库 v1 · 结构与合法性测（CI 可跑）。

校验：
1) 四领域模块 schema 完整（顶层政策/核心概念/术语/底线/项目类型/案例/情绪焦点/矩阵映射/出处）。
2) MATRIX_MAPPING 多归属合法性（domain/element 在 EMC 4×5 合法集、role∈{主,次}、每领域有主归属）。
3) 索引/渲染/反查函数正常 + 与 EMC domain_lens 对齐。
4) 项目设计哲学落位（城市规划=设计全谱、事件差异化）。
"""
import pytest

from ai_qa.industry_kb import (
    INDUSTRY_DOMAINS, DOMAIN_KEYS, ELEMENTS, ROLES,
    get_matrix_mapping, industry_kb_text, industry_kb_brief_text, industry_kb_lens_appendix,
    all_matrix_mappings,
)

_SCHEMA_FIELDS = (
    'DOMAIN_KEY', 'NAME', 'AUTHORITY', 'LAST_UPDATED',
    'TOP_DESIGN', 'CORE_FRAMEWORK', 'KEY_TERMS', 'METRICS_BASELINE',
    'PROJECT_TYPES', 'CASES', 'EMOTION_FOCUS', 'MATRIX_MAPPING', 'ELEMENT_HINTS', 'SOURCES',
)


def test_four_domains_present_and_aligned():
    assert set(DOMAIN_KEYS) == {'urban_planning', 'urban_renewal', 'urban_operation', 'urban_governance'}
    for dk in DOMAIN_KEYS:
        assert dk in INDUSTRY_DOMAINS


@pytest.mark.parametrize('dk', list(DOMAIN_KEYS))
def test_domain_schema_complete(dk):
    mod = INDUSTRY_DOMAINS[dk]
    for fld in _SCHEMA_FIELDS:
        v = getattr(mod, fld, None)
        assert v, f'{dk} 缺字段或空: {fld}'
    assert mod.DOMAIN_KEY == dk
    # TOP_DESIGN 每条结构
    for d in mod.TOP_DESIGN:
        for k in ('policy', 'doc', 'year', 'gist'):
            assert k in d, f'{dk} TOP_DESIGN 缺 {k}'
    # CASES 每条结构
    for c in mod.CASES:
        for k in ('city', 'project', 'point'):
            assert k in c, f'{dk} CASES 缺 {k}'


@pytest.mark.parametrize('dk', list(DOMAIN_KEYS))
def test_matrix_mapping_legal_and_has_primary(dk):
    mp = get_matrix_mapping(dk)
    assert mp, f'{dk} MATRIX_MAPPING 空'
    roles_seen = set()
    for dom, elem, role in mp:
        assert dom in DOMAIN_KEYS, f'{dk} 非法 domain: {dom}'
        assert elem in ELEMENTS, f'{dk} 非法 element: {elem}'
        assert role in ROLES, f'{dk} 非法 role: {role}'
        roles_seen.add(role)
    assert '主' in roles_seen, f'{dk} 缺主归属（每领域应在矩阵有主导格）'


def test_all_matrix_mappings_aggregate():
    all_mp = all_matrix_mappings()
    assert len(all_mp) >= 20   # 四领域合计 ≥20 条
    # 每条 4 元组 (domain, element, role, source_domain)
    for dom, elem, role, src in all_mp:
        assert dom in DOMAIN_KEYS and elem in ELEMENTS and role in ROLES and src in DOMAIN_KEYS


def test_render_nonempty_with_terms():
    for dk in DOMAIN_KEYS:
        txt = industry_kb_text(dk)
        assert txt and '权威语境' in txt and '顶层政策' in txt and '矩阵多归属映射' in txt
        mod = INDUSTRY_DOMAINS[dk]
        assert mod.NAME in txt


def test_brief_text_has_all_domains_terms_projects():
    """industry_kb_brief_text（注入 diagnose）：含四领域 + 术语 + 项目类型。"""
    txt = industry_kb_brief_text()
    assert txt and '官方术语与项目类型速查' in txt
    for dk in DOMAIN_KEYS:
        mod = INDUSTRY_DOMAINS[dk]
        assert mod.NAME in txt, f'brief 缺领域名: {dk}'
    # 含代表性官方术语（各领域一个）
    for term in ('三区三线', '留改拆', '一网统管', '接诉即办'):
        assert term in txt, f'brief 缺术语: {term}'


def test_urban_planning_is_design_full_spectrum():
    """项目设计哲学：城市规划 = 城市规划设计全谱（含城市设计/景观/详规，非仅国土空间）。"""
    mod = INDUSTRY_DOMAINS['urban_planning']
    assert '设计' in mod.NAME   # 领域名含"设计"
    fw = ' '.join(mod.CORE_FRAMEWORK.keys()) + ' ' + ' '.join(mod.CORE_FRAMEWORK.values())
    assert '城市设计' in fw and '景观' in str(mod.PROJECT_TYPES) + str(mod.CORE_FRAMEWORK)


def test_operation_event_is_differentiation():
    """事件要素在城市运营/治理有主/次归属（补官方盲区的差异化价值点）。"""
    op_ev = [(e, r) for d, e, r in get_matrix_mapping('urban_operation') if e == '事件']
    assert op_ev, '城市运营应在事件格有映射（差异化价值）'


@pytest.mark.parametrize('dk', list(DOMAIN_KEYS))
def test_render_full_enriched_fields(dk):
    """④ v2 全量渲染：含官方术语全表/底线指标/要素归因细化/他城案例四新段落（v1 仅 8 字段漏这 4 项）。
    锁 ELEMENT_HINTS（③ 厚化内容）/ KEY_TERMS 全表（非 brief 前 4）/ METRICS_BASELINE 进入渲染。"""
    txt = industry_kb_text(dk)
    mod = INDUSTRY_DOMAINS[dk]
    # 四新段落标题（v1 漏）
    for header in ('官方术语：', '底线指标：', '要素归因细化：', '他城案例：'):
        assert header in txt, f'{dk} 全量渲染缺段落: {header}'
    # KEY_TERMS 全表（brief 只取前 4；全量应含全部 key）
    for k in mod.KEY_TERMS:
        assert k in txt, f'{dk} 全量渲染漏 KEY_TERMS: {k}'
    # METRICS_BASELINE 每条整句进入渲染
    for m in mod.METRICS_BASELINE:
        assert m in txt, f'{dk} 全量渲染漏底线指标: {m}'
    # ELEMENT_HINTS 每个 element 名进入渲染
    for e in mod.ELEMENT_HINTS:
        assert e in txt, f'{dk} 全量渲染漏 ELEMENT_HINTS element: {e}'
    # 不变量（test_render_nonempty_with_terms 的四关键词）仍保持
    assert '权威语境' in txt and '顶层政策' in txt and '矩阵多归属映射' in txt and mod.NAME in txt


def test_lens_appendix_gating():
    """industry_kb_lens_appendix 门控：命中有效域→含标题+该域权威语境；'general'/空/None/非法→空串；去重。"""
    # 命中有效域
    ap = industry_kb_lens_appendix(['urban_renewal'])
    assert ap and '聚焦领域权威语境' in ap and '城市更新' in ap and '留改拆' in ap
    # 多域
    ap2 = industry_kb_lens_appendix(['urban_planning', 'urban_renewal'])
    assert '城市规划' in ap2 and '城市更新' in ap2
    # 'general' 过滤（通用问答无需领域权威）
    assert industry_kb_lens_appendix(['general']) == ''
    # 空 / None / 非法 domain
    assert industry_kb_lens_appendix(None) == ''
    assert industry_kb_lens_appendix([]) == ''
    assert industry_kb_lens_appendix(['not_a_domain']) == ''
    # 去重保序（同一域不重复渲染）
    ap3 = industry_kb_lens_appendix(['urban_renewal', 'urban_renewal'])
    assert ap3.count('【城市更新') == 1


def test_build_final_prompt_injects_lens_appendix():
    """build_final_prompt(domain_lens) 注入门控：有效域→含权威语境附录；'general'/None→不含。
    （diagnose 不注此，保 Flash eval 95%。）"""
    from ai_qa.prompts import build_final_prompt
    p_hit = build_final_prompt(context='x', domain_lens=['urban_renewal'])
    assert '聚焦领域权威语境' in p_hit and '城市更新' in p_hit
    p_general = build_final_prompt(context='x', domain_lens=['general'])
    assert '聚焦领域权威语境' not in p_general
    p_none = build_final_prompt(context='x', domain_lens=None)
    assert '聚焦领域权威语境' not in p_none


if __name__ == '__main__':
    pytest.main([__file__, '-q'])
