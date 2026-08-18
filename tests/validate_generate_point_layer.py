# ════════════ CB-22d · generate_point_layer 契约/镜像/接线一致性校验 ════════════
#
# 守护「知识问答→地图标记」新工具的契约单一真相源（ai_qa/tool_contracts.py）与各镜像一致，
# 以及 harness 路由接线到位（否则"工具实现了却从不被触发"——glm 点破的修复层脱节风险）。
#
# 运行：py -m pytest tests/validate_generate_point_layer.py -q

import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_qa.tool_contracts import TOOL_CONTRACTS, derive_geo_catalog, derive_template_registry
import ai_qa.paradigm as P

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)


def _read(path):
    with open(os.path.join(_REPO, path), encoding='utf-8') as f:
        return f.read()


def test_contract_exists():
    """tool_contracts 有 generate_point_layer（skill/tool/names 必填）。"""
    c = next((c for c in TOOL_CONTRACTS if c['skill'] == 'generate_point_layer'), None)
    assert c, 'tool_contracts 缺 generate_point_layer 契约'
    assert c['tool'] == 'generate_point_layer'
    names = [p['name'] for p in c.get('params', [])]
    assert 'names' in names, '契约缺 names 参数'
    assert 'names' in c.get('required_slots', []), 'names 应为 required_slots'


def test_contract_when_induces():
    """FC 走契约 when 诱导（glm B.2）——when 须含「标记/地图/项目名→点位」触发词。"""
    c = next((c for c in TOOL_CONTRACTS if c['skill'] == 'generate_point_layer'), None)
    when = c['when']
    for kw in ['标记', '地图', '点位']:
        assert kw in when, f'契约 when 缺触发词「{kw}」·FC LLM 无法从 when 选到新工具'


def test_geo_catalog_mirror():
    """paradigm.GEO_TOOL_CATALOG 含 generate_point_layer（name/when/yields 等价于 contracts）。"""
    derived = {g['name']: g for g in derive_geo_catalog()}
    assert 'generate_point_layer' in derived, 'contracts 派生目录缺 generate_point_layer'
    p = next((g for g in P.GEO_TOOL_CATALOG if g['name'] == 'generate_point_layer'), None)
    assert p, 'paradigm.GEO_TOOL_CATALOG 缺 generate_point_layer'
    for k in ['when', 'params', 'yields', 'contributes']:
        assert derived['generate_point_layer'].get(k) == p.get(k), f'GEO_TOOL_CATALOG[{k}] 不一致'


def test_template_registry_mirror():
    """paradigm.TEMPLATE_REGISTRY 含 generate_point_layer（diagnose 可选 template·Codex P0-3）。"""
    skills = {s['skill'] for s in P.TEMPLATE_REGISTRY}
    assert 'generate_point_layer' in skills, 'TEMPLATE_REGISTRY 缺 generate_point_layer（diagnose 选不到）'
    d = {s['skill']: s for s in derive_template_registry()}
    assert 'generate_point_layer' in d, 'contracts 派生 TEMPLATE_REGISTRY 缺 generate_point_layer'


def test_skill_defs_mirror():
    """前端 SKILL_DEFS 含 generate_point_layer + names required_slots（G8a 起真身在生成文件）。"""
    js = _read('frontend/js/ai_qa/contract_mirror.generated.js')
    assert re.search(r"generate_point_layer:\s*\{[^}]*\"required_slots\":\s*\[\"names\"\]", js), \
        'contract_mirror.generated.js SKILL_DEFS 缺 generate_point_layer 或 names required_slots'


def test_tools_impl_exists():
    """前端 tools.js 有 generate_point_layer 实现（async + addToolboxLayer 落图 + 未命中诚实 + 聚合名放弃 + names split）。"""
    js = _read('frontend/js/ai_qa/tools.js')
    body = js.split('async generate_point_layer')[1][:6000]
    assert 'async generate_point_layer' in js, 'tools.js 缺 generate_point_layer 实现'
    assert 'addToolboxLayer' in body, '实现未用 addToolboxLayer 落图'
    assert 'unmatched' in body, '实现缺未命中诚实列表'
    assert '_isAggregate' in body, '实现缺聚合名检测（用户想法·无地点就放弃）'
    assert '.split(/[,，、;；' in body, '实现缺 names split（拼接串→逐名·Codex 根因 C）'
    assert 'amap_first=true' in body, '实现缺高德优先（成熟 API·不造轮子）'


def test_harness_routing_wired():
    """harness.js 路由接线到位（P0-0：_markupCue 注入 / runTemplatePath 诚实出口 / _deterministicRecover 兜底）。"""
    js = _read('frontend/js/ai_qa/harness.js')
    assert '_markupCue' in js, 'harness 缺 _markupCue 路由注入（P0-0-1/2）'
    assert 'generate-point-layer-no-hit' in js, 'harness 缺 runTemplatePath 零图层诚实出口（P0-0-3）'
    assert "template: 'generate_point_layer'" in js, 'harness 缺 _deterministicRecover 兜底（P0-0-5）'


def test_no_hit_zero_llm_exit():
    """B1（用户想法 2）：全未命中 → 零 LLM 确定性文字出口（不调 finalStep·像人放弃·防挂起）。
    若零命中仍调 stages.finalStep → 单调用挂起/超时无兜底 → UI 卡死（「停半途」根因）。"""
    js = _read('frontend/js/ai_qa/harness.js')
    # 定位 generate_point_layer 零命中特判块：从 def.tool 条件到 exit:'answered' 的 return
    start = js.find("def.tool === 'generate_point_layer'")
    assert start >= 0, '找不到 generate_point_layer 特判'
    # 特判块 = 到第一个 onDefense 之后（含 return）
    block = js[start:js.find('exit: \'answered\'', start) + 20]
    assert 'stages.finalStep' not in block, 'B1 未生效：零命中仍调 finalStep LLM（会挂起）'
    assert 'onFinalDone' in block, 'B1 缺 onFinalDone（计时必须收尾）'
    assert "exit: 'answered'" in block, 'B1 出口应为 answered（诚实文字）'


def test_panel_prior_turn_wired():
    """panel.js priorTurn 蒸馏补 rag 识别 + final_excerpt（P0-0-1/4·FC 才能提取 names）。"""
    js = _read('frontend/js/ai_qa/panel.js')
    assert 'final_excerpt' in js, 'panel 缺 final_excerpt（上轮回答片段供 FC 提取项目名）'
    assert 'knowledge_qa' in js.split('final_excerpt')[0] or "dg.rag" in js, 'panel 缺 quick-rag 轮 rag 识别'


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    fails = 0
    for fn in fns:
        try:
            fn(); print(f'[PASS] {fn.__name__}')
        except AssertionError as e:
            fails += 1; print(f'[FAIL] {fn.__name__}\n  {e}')
    print(f'\n{"[OK] 全部通过" if not fails else f"{fails} 项失败"}')
    sys.exit(1 if fails else 0)
