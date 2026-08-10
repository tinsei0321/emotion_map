"""CB-22f A 路由打通·守护断言（5 条·Codex 焦点 B① 清单）。

knowledge_qa 伪工具（方案 B）四向守护：
  1. TOOL_CONTRACTS 含 knowledge_qa（category='knowledge'·tool='knowledge_qa'·when=None·params=[]）
  2. derive_geo_catalog() 不含 knowledge_qa（when=None 天然排除·显式断言防未来误加 when）
  3. derive_template_registry() 不含 knowledge_qa（category 过滤·防技能目录进 diagnose prompt 撞红线）
  4. contracts_to_tools_schema() 含 knowledge_qa（FC 可调·证明 exclude_categories 未误扩）
  5. build_fc_sys_prompt() 输出含知识选型纪律句（防 0073990 式静默删除）

运行：py -m pytest tests/validate_knowledge_route.py -q
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from ai_qa.tool_contracts import (
    TOOL_CONTRACTS, derive_geo_catalog, derive_template_registry, contracts_to_tools_schema,
)
from ai_qa.router import build_fc_sys_prompt


def _knowledge_contract():
    for c in TOOL_CONTRACTS:
        if c.get('skill') == 'knowledge_qa':
            return c
    return None


def test_knowledge_contract_exists():
    """TOOL_CONTRACTS 含 knowledge_qa（category='knowledge'·tool='knowledge_qa'·when=None·params=[]）。"""
    c = _knowledge_contract()
    assert c is not None, 'TOOL_CONTRACTS 应含 knowledge_qa 契约'
    assert c.get('category') == 'knowledge', f'category 应为 knowledge: {c.get("category")}'
    assert c.get('tool') == 'knowledge_qa', f'tool 应为 knowledge_qa: {c.get("tool")}'
    assert c.get('when') is None, 'when 应为 None（不进 GEO_TOOL_CATALOG）'
    assert c.get('params') == [], f'params 应为 []: {c.get("params")}'


def test_knowledge_not_in_geo_catalog():
    """derive_geo_catalog 不含 knowledge_qa（when=None 天然排除·防未来误加 when）。"""
    names = [g.get('name') for g in derive_geo_catalog()]
    assert 'knowledge_qa' not in names, 'knowledge_qa 误进 GEO_TOOL_CATALOG（when 不应为 None）'


def test_knowledge_not_in_template_registry():
    """derive_template_registry 不含 knowledge_qa（category 过滤·防技能目录进 diagnose prompt 撞红线）。"""
    skills = [t.get('skill') for t in derive_template_registry()]
    assert 'knowledge_qa' not in skills, 'knowledge_qa 误进 TEMPLATE_REGISTRY（须 category 过滤）'


def test_knowledge_in_fc_schema():
    """contracts_to_tools_schema 含 knowledge_qa（FC 可调·证明 exclude_categories 未误扩 ('concept','knowledge')）。"""
    names = [(t.get('function') or {}).get('name') for t in contracts_to_tools_schema()]
    assert 'knowledge_qa' in names, 'knowledge_qa 应从 FC schema 可见（exclude_categories 默认保持 concept 不动）'


def test_fc_prompt_has_knowledge_discipline():
    """build_fc_sys_prompt 输出含知识选型纪律句（防 0073990 式静默删除）。"""
    p = build_fc_sys_prompt('')
    assert '知识问答选型' in p, 'FC prompt 应含知识问答选型纪律段'
    assert 'knowledge_qa' in p, 'FC prompt 应含 knowledge_qa 工具名'
    assert '双条件守卫' in p, 'FC prompt 应含双条件守卫说明'
