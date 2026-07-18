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
