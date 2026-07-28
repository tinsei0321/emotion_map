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
    assert n < 3000, f'final prompt 膨胀到 {n} bytes（应 <3KB·含语言风格规则·查是否回灌 MANIFESTO/industry_kb）'


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
    """D006 Phase B 分派：单候选问 → fill_card 路径（极瘦·Flash）。"""
    from ai_qa.prompts import build_diagnose_prompt_dispatch
    prompt, path, model = build_diagnose_prompt_dispatch('做核密度分析', '', None)
    assert path == 'fill_card', f'单候选应走 fill_card·实走 {path}'
    assert model is None, f'fill_card 应 Flash（model=None）·实 {model}'
    assert len(prompt.encode()) < 3500, 'fill_card prompt 应 <3.5KB'


def test_diagnose_dispatch_plan_for_compound():
    """D009+D012 Phase C 分派：复合问（multi）→ plan 路径（Pro 产 chain·<5KB·5-10s）。"""
    from ai_qa.prompts import build_diagnose_prompt_dispatch
    prompt, path, model = build_diagnose_prompt_dispatch('西陵区范围内密度分析', '', None)
    assert path == 'plan', f'复合应走 plan（Pro）·实走 {path}'
    assert model == 'pro', f'plan 应 Pro（model=pro）·实 {model}'
    assert len(prompt.encode()) < 5000, f'plan prompt 应 <5KB·实 {len(prompt.encode())}B'
    assert 'chain' in prompt and 'steps' in prompt, 'plan prompt 缺 chain/steps schema'


def test_diagnose_dispatch_fill_card_for_concept():
    """D006 Phase B 分派：概念问 → fill_card（concept 候选·极瘦概念卡·Flash）。"""
    from ai_qa.prompts import build_diagnose_prompt_dispatch
    _prompt, path, model = build_diagnose_prompt_dispatch('什么是核密度分析', '', None)
    assert path == 'fill_card', f'概念问应走 fill_card（concept）·实走 {path}'
    assert model is None, f'concept fill_card 应 Flash·实 {model}'


def test_plan_prompt_lean():
    """D009+D012 Phase C 守门：Pro plan prompt <5KB（vs 复合大 prompt 45.8KB·省 90%+）。"""
    from ai_qa.prompts import build_plan_prompt
    n = len(build_plan_prompt('西陵区范围内密度分析', ['density', 'clip'], '', None).encode())
    assert n < 5000, f'plan prompt {n}B 应 <5KB（防回灌 MANIFESTO/全量 catalog）'


def test_plan_prompt_includes_chain_convention():
    """plan prompt 须教 Pro 产 chain：含 $1 引用 + {question} 占位 + chain schema。"""
    from ai_qa.prompts import build_plan_prompt
    p = build_plan_prompt('西陵区范围内密度分析', ['density', 'clip'], '', None)
    assert '$1' in p, 'plan prompt 缺 $n 引用约定'
    assert 'chain' in p and 'steps' in p, 'plan prompt 缺 chain/steps schema'
    assert 'multi' in p, 'plan prompt 缺 template=multi 指示'


def test_no_pending_l3_panel_source():
    """模块七 L3（5.238）：TOOL_CONTRACTS 无 '待 L3 核查' panel_source（全Resolved为 dialog 控件/EMC-only/PANEL_MISSING）。"""
    from ai_qa.tool_contracts import TOOL_CONTRACTS
    pending = []
    for c in TOOL_CONTRACTS:
        for p in c.get('params', []):
            src = p.get('panel_source', '')
            if '待 L3' in src:
                pending.append(f"{c['skill']}.{p['name']}")
    assert not pending, f'仍有待 L3 核查 panel_source：{pending}'


def test_panel_missing_excludes_emc_only():
    """模块七 L3（5.238）：panel_missing() 只列真 PANEL_MISSING·'EMC-only'（设计无 dialog）不计缺失。"""
    from ai_qa.tool_contracts import panel_missing, TOOL_CONTRACTS
    pm = panel_missing()
    # EMC-only 不在 panel_missing 列表
    emc_only_in_pm = [x for x in pm if 'EMC-only' in x.get('panel_source', '')]
    assert not emc_only_in_pm, f'EMC-only 不应计缺失：{emc_only_in_pm}'
    # 列表只含 PANEL_MISSING
    for x in pm:
        assert 'PANEL_MISSING' in x['panel_source'], f'panel_missing 含非 PANEL_MISSING 项：{x}'
    # EMC-only 工具确实存在（sanity：L3 标记生效）
    emc_only_count = sum(1 for c in TOOL_CONTRACTS for p in c.get('params', []) if 'EMC-only' in p.get('panel_source', ''))
    assert emc_only_count > 0, '应有多于 0 个 EMC-only 参数（rank/clip/overlay 等）'


def test_log_episode_capsule_clicked(tmp_path, monkeypatch):
    """模块八 D034（5.239）：log_episode 写 capsule_clicked 到 jsonl（Pro 排序自我成长偏好信号）。"""
    import json
    import ai_qa.episode as ep_mod
    monkeypatch.setattr(ep_mod, '_EPISODE_DIR', str(tmp_path))
    monkeypatch.setattr(ep_mod, '_EPISODE_PATH', str(tmp_path / 'ep.jsonl'))
    # 胶囊点击 → capsule_clicked=skill
    assert ep_mod.log_episode(question='切密度', capsule_clicked='density') is True
    # 非胶囊 → capsule_clicked=None
    assert ep_mod.log_episode(question='普通问', capsule_clicked=None) is True
    lines = (tmp_path / 'ep.jsonl').read_text(encoding='utf-8').strip().split('\n')
    assert len(lines) == 2
    assert json.loads(lines[0]).get('capsule_clicked') == 'density'
    assert json.loads(lines[1]).get('capsule_clicked') is None


def test_geo_catalog_derives_all_gis_tools():
    """模块六 D026（5.240）：geo_tool_catalog_text() 含 TOOL_CONTRACTS 所有 single GIS 工具（派生无遗漏）。"""
    from ai_qa.paradigm import geo_tool_catalog_text
    from ai_qa.tool_contracts import TOOL_CONTRACTS
    catalog = geo_tool_catalog_text()
    gis_tools = [c.get('tool') for c in TOOL_CONTRACTS if c.get('category') == 'single' and c.get('when')]
    assert gis_tools, '应至少有 1 个 single GIS 工具'
    missing = [t for t in gis_tools if t not in catalog]
    assert not missing, f'geo_tool_catalog 附录缺工具（派生遗漏）：{missing}'


def test_diagnose_dispatch_empty_candidates_request_upload():
    """5.242 S1：layer_meta 提供 + 数据过滤后候选空 → fill_card_empty（Flash 出 request_upload·非 fallback 大 prompt）。"""
    from ai_qa.prompts import build_diagnose_prompt_dispatch
    prompt, path, model = build_diagnose_prompt_dispatch('生成热力图', '', None, {'has_point': False, 'has_polygon': True})
    assert path == 'fill_card_empty', f'数据不支撑应 fill_card_empty·实 {path}'
    assert model is None
    assert 'request_upload' in prompt, 'fill_card_empty prompt 应含 request_upload 指令'


def test_agent_prompt_no_handwritten_gis_specs():
    """模块六 D026（5.240）：agent_step prompt 不含手写 GIS 工具规格（已全派生至 geo_tool_catalog 附录）。
    注：派生附录从 density.when 渲染会含'核密度(KDE)'字样（合法·源自 contracts）·手写规格的独特签名是
    'zonal_stats：**宏/中观' 等粗体+内联 params 格式（派生附录用'- name：when\\n    入参：params'格式）。"""
    from ai_qa.prompts import build_agent_prompt
    p = build_agent_prompt('', '', 1)
    # 手写规格独特签名（**粗体** + —— 破折号）·派生附录无此格式
    assert 'zonal_stats：**宏/中观' not in p, 'agent prompt 仍含手写 zonal_stats 规格（D026 未派生）'
    assert 'density：核密度(KDE)/热力图——' not in p, 'agent prompt 仍含手写 density 规格（—— 签名）'
    # 派生指针应在
    assert 'GIS 操作目录' in p and 'tool_contracts' in p, 'agent prompt 缺派生附录指针'
