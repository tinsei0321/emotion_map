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
                 'compare_regions', 'generate_point_layer'}   # CB-22d：批量地名标点（knowledge_qa→地图标记）
# required_slots / optional_defaults 键应是工具能接受的入参名（防拼写漂移）
_KNOWN_SLOTS = {'layer', 'range', 'boundary', 'center', 'radius_m', 'by', 'top_n', 'how',
                'layer_a', 'layer_b', 'target', 'k', 'value_col', 'agg_cols', 'pre_filter',
                'bandwidth_m', 'cell_size_m',
                'mode', 'radius', 'weightField', 'cell_size', 'polarity', 'level',
                'boundaries', 'threshold', 'soft_threshold', 'names', 'as'}   # density 委托 Toolbox 的入参名；boundaries = compare_regions 多区入参；threshold/soft_threshold = hotspot 软分级（P1）；names/as = generate_point_layer（CB-22d）


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


def test_diagnose_intent_has_knowledge_qa():
    """CB-22 三层架构：diagnose intent 枚举含 knowledge_qa（知识问答通道·意图判断归位）。

    豁免前提（P0-3 先扩 eval）：diagnose 加类增量·不改不删现有三值——本断言守护枚举存在·
    test_diagnose_existing_three_intents_unchanged 守护现有三值判据未删。
    """
    from ai_qa.prompts import build_diagnose_prompt
    p = build_diagnose_prompt('')
    assert 'knowledge_qa' in p, 'diagnose intent 枚举缺 knowledge_qa（知识问答通道断）'
    # 判据段须含对比句（有哪些=知识问答·什么是=general·防 Flash 混淆·Codex V1）
    assert '有哪些' in p and '什么是' in p, 'knowledge_qa 判据段缺对比句（有哪些 vs 什么是）'


def test_diagnose_existing_three_intents_unchanged():
    """CB-22 三层架构（豁免条件 3）：现有三值判据文本未删（增量不改存量·防重构删类）。"""
    from ai_qa.prompts import build_diagnose_prompt
    p = build_diagnose_prompt('')
    assert 'general=通用问答' in p or 'general' in p, 'general 判据被删（增量豁免·不得删现有）'
    assert 'gis_operation' in p, 'gis_operation 判据被删'
    assert 'emotion_analysis' in p, 'emotion_analysis 判据被删'
    # 多轮续作例外：分析中穿插知识问 → 判 knowledge_qa（非续作 emotion·Codex V1/glm F1）
    assert 'knowledge_qa' in p and '续作' in p, '多轮续作例外段缺失'


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
    """CB-09 D019 极瘦回归守门：final prompt 静态模板 <3KB（CB-10 P0-4 后实测 2641B·含语言风格规则·防 MANIFESTO/industry_kb 回灌致 17KB+·prefill 回潮）。
    出口三段式 P0 观点先行软扩后 2957B < 3000B（实测基线 ~2833B——超 Codex 引用的 2641B 历史快照 192B·CB-14 final_brief 后现状·观点先行 +124B）。
    ⚠️ 模板体积已近硬门禁（余量 ~43B）：**P1 起冻结 FINAL_TEMPLATE 加字**——结论段学术化/观点细化一律走前端确定性聚合（result-struct.js）或 ctx 注入，不再加模板。"""
    from ai_qa.prompts import build_final_prompt
    n = len(build_final_prompt('', '').encode())
    assert n < 3000, f'final prompt 膨胀到 {n} bytes（应 <3KB·含语言风格规则·查是否回灌 MANIFESTO/industry_kb·模板已冻结加字）'


def test_final_prompt_has_insight_first():
    """出口三段式 P0（CB 第三轮 glm/Codex 共识）：FINAL_TEMPLATE 须含"观点先行"正式指令。

    D5 修正依据：观点=核心价值（用户"观点即干货"）→ 须正式模板指令（LLM 必读）·
    非 ctx 附加提示（遵守度弱·落在【当前数据】段被当数据摘要）。防静默删除（承重模板一次一处）。"""
    from ai_qa.prompts import build_final_prompt
    p = build_final_prompt('', '')
    assert '观点先行' in p, 'final prompt 缺"观点先行"指令（出口三段式 P0 核心·D5）'
    assert '观点≠结论' in p, 'final prompt 缺"观点≠结论"区分说明（防观点/结论混写）'
    assert '**观点：**' in p, 'final prompt 缺观点 markdown 约定（前端观点卡提取锚点）'
    # S2 审计（Codex）：观点先行须在三句骨架前（防指令被移到模板底部弱化）
    assert p.index('观点先行') < p.index('三句骨架'), '观点先行指令须在"三句骨架"之前（防被移底弱化·D5 位置守门）'


def test_fc_sys_prompt_keeps_polarity_discipline():
    """CB-10 P2-2 守卫：FC prompt 极性范围纪律段在（防 0073990 式"简化"静默删除 B006 修复）。

    plans/domain_lens/多要素提取指令不恢复不断言——已被 _allToolCalls/autoExpand/契约 when 取代。"""
    from ai_qa.router import build_fc_sys_prompt
    p = build_fc_sys_prompt('')
    assert '极性范围纪律' in p, 'FC prompt 缺极性范围纪律段（B006 修复被删？）'
    assert '严禁自行缩窄' in p, 'FC prompt 缺"严禁自行缩窄"纪律（B006 核心句）'
    assert '全部三个极性' in p, 'FC prompt 缺"全部三个极性"默认（B006 核心）'
    assert 'clip 仅用于点数据' in p, 'FC prompt 缺 clip 面层禁止规则（工具规则锚点）'


def test_search_endpoint_registered():
    """G6b（CB-12）：/aiqa/search 端点注册 + search_chat 无 key 时抛 LLMError（防静默失败）。"""
    from api.aiqa_routes import aiqa_router
    paths = [r.path for r in aiqa_router.routes]
    assert '/aiqa/search' in paths, '搜索端点未注册'
    from ai_qa.llm import search_chat, LLMError
    import os
    _k = os.environ.pop('DEEPSEEK_API_KEY', None)
    try:
        try:
            search_chat('测试')
            assert False, '无 key 应抛 LLMError'
        except LLMError:
            pass
    finally:
        if _k:
            os.environ['DEEPSEEK_API_KEY'] = _k


def test_fc_sys_prompt_keeps_scale_and_domain_lens_instruction():
    """G1（CB-12·glm组 修正 3）：FC prompt 尺度判定段 + domain_lens 标签指令在（防 0073990 式"简化"静默删除）。
    去三字段硬编码的前提 = FC prompt 教 LLM 产出 [scale:xxx]/[domain_lens:xxx] 标签（A 部解析源）。"""
    from ai_qa.router import build_fc_sys_prompt
    p = build_fc_sys_prompt('')
    assert '尺度判定' in p, 'FC prompt 缺尺度判定段（G1 scale A 部源）'
    assert 'macro' in p and 'meso' in p and 'micro' in p, 'FC prompt 尺度段缺 macro/meso/micro'
    assert '[scale:' in p, 'FC prompt 缺 [scale:xxx] 标签指令'
    assert '[domain_lens:' in p, 'FC prompt 缺 [domain_lens:xxx] 标签指令（domain_lens A 部源）'
    assert '出口须随尺度差异化' in p, 'FC prompt 缺出口差异化纪律'


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
