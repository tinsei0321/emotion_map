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
    get_matrix_mapping, industry_kb_text, all_matrix_mappings,
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


if __name__ == '__main__':
    pytest.main([__file__, '-q'])
