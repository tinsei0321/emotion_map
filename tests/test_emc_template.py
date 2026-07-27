"""EMC P1 技能化编排·结构测（Flash 80% go/no-go gate 的基础，CI 可跑）。

校验后端 TEMPLATE_REGISTRY 结构健全 + template_registry_text 渲染 + diagnose prompt 注入。
前端 stages.js SKILL_DEFS 须与 TEMPLATE_REGISTRY 的 tool/category/required_slots/optional_defaults 同步
（仿 field_dictionary 两份字典模式——此处校验后端半，前端半由 node ESM + 手动同步保证）。
真 Flash 命中率评测见 eval_template_flash.py（手动跑，需 API Key）。"""
import pytest
from ai_qa.paradigm import TEMPLATE_REGISTRY, template_registry_text

_CATEGORIES = {'concept', 'single', 'multi', 'unknown'}
# single 技能的 tool 必须是已知 geo 工具（与 tools.js TOOLS / GEO_TOOL_CATALOG 对齐）
# 注：compare_regions 是前端复合工具（复用 zonal_stats 逐区聚合，无独立 geo 端点，守委托 Toolbox 红线）
_SINGLE_TOOLS = {'density', 'rank', 'buffer', 'clip', 'overlay', 'zonal_stats',
                 'nearest', 'hotspot', 'area_stats', 'merge', 'extract_feature', 'filter_attr',
                 'compare_regions'}
# required_slots / optional_defaults 键应是工具能接受的入参名（防拼写漂移）
_KNOWN_SLOTS = {'layer', 'range', 'boundary', 'center', 'radius_m', 'by', 'top_n', 'how',
                'layer_a', 'layer_b', 'target', 'k', 'value_col', 'agg_cols', 'pre_filter',
                'bandwidth_m', 'cell_size_m',
                'mode', 'radius', 'weightField', 'cell_size', 'polarity', 'level',
                'boundaries'}   # density 委托 Toolbox 的入参名；boundaries = compare_regions 多区入参


def test_registry_structure():
    assert len(TEMPLATE_REGISTRY) >= 9, '至少 7 命名技能 + 2 兜底（multi/unknown）'
    skills = set()
    for s in TEMPLATE_REGISTRY:
        for k in ('skill', 'name', 'category', 'tool', 'required_slots', 'optional_defaults',
                  'voice', 'triggers', 'planning_common'):
            assert k in s, f'技能缺字段 {k}: {s}'
        assert s['category'] in _CATEGORIES, f'非法 category: {s["category"]}'
        assert s['skill'] not in skills, f'技能 id 重复: {s["skill"]}'
        skills.add(s['skill'])
        assert isinstance(s['required_slots'], list), f'required_slots 非 list: {s["skill"]}'
        assert isinstance(s['optional_defaults'], dict), f'optional_defaults 非 dict: {s["skill"]}'
        if s['category'] == 'single':
            assert s['tool'] in _SINGLE_TOOLS, f'single 技能 tool 非已知 geo 工具: {s["tool"]}'
        else:  # concept/multi/unknown 不绑单工具
            assert s['tool'] is None, f'{s["category"]} 类技能 tool 应为 None: {s["skill"]}'


def test_text_renders_all_skills():
    txt = template_registry_text()
    assert txt and '技能' in txt
    for s in TEMPLATE_REGISTRY:
        assert s['skill'] in txt, f'渲染缺技能 id: {s["skill"]}'
        assert s['voice'] in txt, f'渲染缺 voice: {s["skill"]}'


def test_diagnose_prompt_includes_registry():
    from ai_qa.prompts import build_diagnose_prompt
    p = build_diagnose_prompt('test')
    assert '技能目录' in p and 'template' in p, 'diagnose prompt 未注入技能目录/template 字段'
    for s in TEMPLATE_REGISTRY:
        assert s['skill'] in p, f'diagnose prompt 缺技能: {s["skill"]}'


def test_required_slots_known():
    for s in TEMPLATE_REGISTRY:
        for slot in s['required_slots']:
            assert slot in _KNOWN_SLOTS, f'{s["skill"]} required_slot 未知入参名: {slot}'


def test_optional_defaults_keys_known():
    for s in TEMPLATE_REGISTRY:
        for k in s['optional_defaults']:
            assert k in _KNOWN_SLOTS, f'{s["skill"]} optional_defaults 未知键: {k}'


def test_final_prompt_includes_capsule_rule():
    """CB-09 D020：finalStep 极瘦 prompt 须含追问胶囊规则（LLM 产 {{capsule:...}} 三级胶囊）。"""
    from ai_qa.prompts import build_final_prompt
    p = build_final_prompt('', '')
    assert '追问胶囊' in p, 'final prompt 缺追问胶囊规则段'
    assert 'capsule:' in p, 'final prompt 缺 {{capsule:}} 格式说明'
    # 范例须含一个合法 skill（density）+ L1 级别（防 prompt 把级别/技能写错）
    assert 'density' in p and 'L1' in p, 'final prompt 胶囊范例缺 skill/level'


def test_final_prompt_stays_lean():
    """CB-09 D019 极瘦回归守门：final prompt 须 <2KB（防 MANIFESTO/industry_kb 回灌致 17KB+·prefill 20-35s 回潮）。
    含胶囊规则（~360 字节·Chinese UTF-8）仍远低于 2KB·与 D019 表 ~1-2KB 目标一致。"""
    from ai_qa.prompts import build_final_prompt
    n = len(build_final_prompt('', '').encode())
    assert n < 2000, f'final prompt 膨胀到 {n} bytes（应 <2KB·查是否回灌 MANIFESTO/industry_kb）'


def test_fill_card_prompt_lean():
    """CB-09 D006 Phase B 极瘦填卡守门：<3.5KB（1-4 候选·prefill <2s·diagnose <5s）。
    防 build_fill_card_prompt 回灌 MANIFESTO/全量 catalog 致 45.8KB 回潮。"""
    from ai_qa.prompts import build_fill_card_prompt
    n1 = len(build_fill_card_prompt('做核密度分析', ['density'], '', None).encode())
    n4 = len(build_fill_card_prompt('多候选', ['density', 'hotspot', 'zonal', 'rank'], '', None).encode())
    assert n1 < 3500, f'fill_card prompt（1 候选）{n1}B 应 <3.5KB'
    assert n4 < 3500, f'fill_card prompt（4 候选）{n4}B 应 <3.5KB'


def test_fill_card_includes_candidate_schema():
    """fill_card prompt 须注入候选 skill 的入参 schema（required/optional）·Flash 据此填 params。"""
    from ai_qa.prompts import build_fill_card_prompt
    p = build_fill_card_prompt('做核密度分析', ['density'], '', None)
    assert 'density' in p and 'template' in p, 'fill_card 缺候选 skill / 卡 schema'
    assert 'polarity' in p or 'mode' in p, 'fill_card 缺 density 入参 schema'  # density optional_defaults 键


def test_diagnose_dispatch_fill_card_for_single():
    """D006 Phase B 分派：单候选问 → fill_card 路径（极瘦）。"""
    from ai_qa.prompts import build_diagnose_prompt_dispatch
    prompt, path = build_diagnose_prompt_dispatch('做核密度分析', '', None)
    assert path == 'fill_card', f'单候选应走 fill_card·实走 {path}'
    assert len(prompt.encode()) < 3500, 'fill_card prompt 应 <3.5KB'


def test_diagnose_dispatch_fallback_for_compound():
    """D006 Phase B 分派：复合问（multi）→ fallback 大 prompt（不回归·45.8KB）。"""
    from ai_qa.prompts import build_diagnose_prompt_dispatch
    # 复合（scope+analyze）→ select_candidates 返 multi → fallback
    prompt, path = build_diagnose_prompt_dispatch('西陵区范围内密度分析', '', None)
    assert path == 'fallback', f'复合应走 fallback·实走 {path}'
    assert len(prompt.encode()) > 20000, 'fallback 大 prompt 应 ~45.8KB（非极瘦）'


def test_diagnose_dispatch_fallback_for_concept():
    """D006 Phase B 分派：概念问 → fill_card（concept 候选·极瘦概念卡）。"""
    from ai_qa.prompts import build_diagnose_prompt_dispatch
    _prompt, path = build_diagnose_prompt_dispatch('什么是核密度分析', '', None)
    assert path == 'fill_card', f'概念问应走 fill_card（concept）·实走 {path}'
