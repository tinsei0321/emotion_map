# ════════════ CB-04 L2 · 参数契约一致性校验（SCAN Phase 3.1）════════════
#
# 守护"单一真相源 = ai_qa/tool_contracts.py"与各镜像（paradigm GEO_TOOL_CATALOG/TEMPLATE_REGISTRY
# + 前端 SKILL_DEFS optional_defaults）一致。漂移即报红（pytest 失败）。
#
# 校验项：
#   1. contracts derive_geo_catalog() == paradigm.GEO_TOOL_CATALOG（name/when/params/yields 等价）
#   2. contracts derive_template_registry() optional_defaults == paradigm.TEMPLATE_REGISTRY
#   3. contracts _derive_defaults == 前端 SKILL_DEFS optional_defaults（静态清单·JS 无法 import）
#   4. panel_missing 清单打印（L3 提醒开发者补齐参数面板·PANEL_MISSING）
#
# 运行：py -m pytest tests/validate_skill_params.py -q  或  py tests/validate_skill_params.py
#
# 为什么不派生（paradigm=derive）而用校验：
#   diagnose prompt 是 eval 红线（永不动）。派生改"怎么生成"虽保内容等价，但大段重构 + 派生格式微差
#   可能破坏 Flash eval。务实版用"真相(contracts)+镜像(paradigm/SKILL_DEFS)+守护(validate)"达防分裂目的，
#   不触 eval 红线。加参数时改 contracts（真相）+ 同步镜像，validate 报漂移。

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_qa.tool_contracts import derive_geo_catalog, derive_template_registry, panel_missing, TOOL_CONTRACTS
import ai_qa.paradigm as P

# 前端 SKILL_DEFS.optional_defaults 静态镜像（从 frontend/js/ai_qa/stages.js 读到的当前状态·JS 无法 import）
# 改 stages.js SKILL_DEFS 后须同步此处（validate 守护·漂移报红）
SKILL_DEFS_DEFAULTS = {
    'density': {'mode': '2d', 'radius': 300, 'weightField': 'emotion_intensity', 'cell_size': 600, 'polarity': 'overall'},
    'rank': {'by': 'worst', 'top_n': 5},
    'buffer': {'radius_m': 500, 'agg_cols': ['score']},
    'clip': {},
    'overlay': {'how': 'intersection'},
    'zonal': {'agg_cols': ['score']},
    'compare': {'agg_cols': ['score', 'polarity_index']},
    'extract_feature': {},
    'area_stats': {},
    'merge': {},
    'nearest': {'k': 1},
    'hotspot': {'value_col': 'score', 'threshold': 1.96, 'soft_threshold': 1.0},   # P1 软分级透传（W6 审计）
    'filter_attr': {},
}


def _contracts_defaults(skill):
    c = next((c for c in TOOL_CONTRACTS if c['skill'] == skill), None)
    if not c:
        return None
    return {p['name']: p['default'] for p in c.get('params', []) if p.get('default') is not None}


def test_geo_catalog_equivalent():
    """contracts GEO_TOOL_CATALOG 派生 == paradigm 手写（name/when/params/yields）。"""
    derived = derive_geo_catalog()
    # compare 是 CB-04 新增（P1c）·paradigm 若已含则全比，否则 contracts 多 1（compare）
    pmap = {g['name']: g for g in P.GEO_TOOL_CATALOG}
    errs = []
    for d in derived:
        p = pmap.get(d['name'])
        if not p:
            errs.append(f"paradigm GEO_TOOL_CATALOG 缺 {d['name']}（CB-04 新增·须补 paradigm 或转派生）")
            continue
        for k in ['when', 'params', 'yields', 'contributes']:
            if d.get(k) != p.get(k):
                errs.append(f"[{d['name']}].{k}: contracts≠paradigm\n    contracts={d.get(k)!r}\n    paradigm={p.get(k)!r}")
    assert not errs, '\n'.join(errs)


def test_template_registry_defaults():
    """contracts TEMPLATE_REGISTRY optional_defaults(派生) == paradigm。"""
    derived = {s['skill']: s for s in derive_template_registry()}
    errs = []
    for p in P.TEMPLATE_REGISTRY:
        d = derived.get(p['skill'])
        if not d:
            errs.append(f"contracts 缺 skill={p['skill']}")
            continue
        if d['optional_defaults'] != p.get('optional_defaults', {}):
            errs.append(f"[{p['skill']}] optional_defaults: contracts={d['optional_defaults']} ≠ paradigm={p.get('optional_defaults')}")
    assert not errs, '\n'.join(errs)


def test_skill_defs_mirror():
    """contracts defaults == 前端 SKILL_DEFS.optional_defaults（静态镜像）。"""
    errs = []
    for skill, js_defaults in SKILL_DEFS_DEFAULTS.items():
        cd = _contracts_defaults(skill)
        if cd is None:
            errs.append(f"contracts 缺 skill={skill}")
            continue
        if cd != js_defaults:
            errs.append(f"[{skill}] contracts={cd} ≠ 前端SKILL_DEFS={js_defaults}（改 stages.js 后须同步 SKILL_DEFS_DEFAULTS）")
    assert not errs, '\n'.join(errs)


def test_panel_source_report():
    """L3：打印 panel_source 待核查/缺失清单（非 fail·提醒开发者补齐参数面板）。"""
    pm = panel_missing()
    print(f"\n[L3] panel_source 待核查/缺失 {len(pm)} 项（density 已完整·其余 L3 补）：")
    by_skill = {}
    for x in pm:
        by_skill.setdefault(x['skill'], []).append(x['param'])
    for skill, params in sorted(by_skill.items()):
        print(f"  {skill}: {', '.join(params)}")
    # density 应全部有 panel_source（L2 首例完整）
    density_missing = [x for x in pm if x['skill'] == 'density']
    assert not density_missing, f"density（L2 首例）panel_source 须完整·缺：{density_missing}"


if __name__ == '__main__':
    failures = []
    for name, fn in [
        ('geo_catalog_equivalent', test_geo_catalog_equivalent),
        ('template_registry_defaults', test_template_registry_defaults),
        ('skill_defs_mirror', test_skill_defs_mirror),
        ('panel_source_report', test_panel_source_report),
    ]:
        try:
            fn()
            print(f'[PASS] {name}')
        except AssertionError as e:
            failures.append((name, str(e)))
            print(f'[FAIL] {name}\n{e}')
    if failures:
        print(f'\n=== {len(failures)} 项失败 ===')
        sys.exit(1)
    print('\n[OK] contracts <-> paradigm <-> SKILL_DEFS 全一致')
