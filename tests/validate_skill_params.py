# ════════════ CB-04 L2 · 参数契约一致性校验（SCAN Phase 3.1）════════════
#
# 守护"单一真相源 = ai_qa/tool_contracts.py"与各镜像一致。漂移即报红（pytest 失败）。
#
# 校验项：
#   1. contracts derive_geo_catalog() == paradigm.GEO_TOOL_CATALOG（name/when/params/yields 等价）
#   2. contracts derive_template_registry() optional_defaults == paradigm.TEMPLATE_REGISTRY
#   3. contracts defaults == 前端 SKILL_DEFS.optional_defaults（G8a 起解析生成文件真身）
#   4. （G8a 新增）镜像新鲜度：contract_mirror.generated.js == gen_stages_mirror.render()（派生 diff=0）
#   5. （G8a 新增）TOOL_ALIAS 派生等价：生成文件别名表 == contracts params[].alias 按工具派生
#   6. （G8a 新增·报告项）paradigm guard 字段（scale/preconditions/failure_modes/examples）
#      与 contracts 差异清单——只报告不 fail（diagnose prompt 红线：该 4 字段手写属 prompt 内容，
#      改动须走豁免流程；报告=让漂移可见、不静默）
#   7. panel_missing 清单打印（L3 提醒开发者补齐参数面板·PANEL_MISSING）
#
# 运行：py -m pytest tests/validate_skill_params.py -q  或  py tests/validate_skill_params.py
#
# G8a（PT-CB1 T2·2026-08-18）后格局：
#   前端 stages.js 手写镜像永久退役 -> tools/gen_stages_mirror.py 自动生成
#   frontend/js/ai_qa/contract_mirror.generated.js（SKILL_DEFS + TOOL_ALIAS）。
#   paradigm 侧：when/params/yields/contributes 导入时派生同步（运行时等价）；
#   guard 4 字段手写保留（diagnose prompt 永不动红线·差异见第 6 项报告）。

import sys, os, json, re
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_qa.tool_contracts import derive_geo_catalog, derive_template_registry, panel_missing, TOOL_CONTRACTS
import ai_qa.paradigm as P

# CB-39 P0-2（D4 裁定 b）：手抄镜像 → 真身解析（铁律 11 单一源·漂移自动报红）。
# G8a：真身从 stages.js 迁至自动生成文件 contract_mirror.generated.js。
_MIRROR_JS = Path(__file__).resolve().parent.parent / 'frontend' / 'js' / 'ai_qa' / 'contract_mirror.generated.js'


def _strip_js_comments(text):
    """去 // 行注释（字符串字面量内的 // 不动·状态机跟踪引号与转义）。"""
    out, i, n, q = [], 0, len(text), None
    while i < n:
        c = text[i]
        if q:
            out.append(c)
            if c == '\\' and i + 1 < n:
                out.append(text[i + 1]); i += 2; continue
            if c == q:
                q = None
            i += 1; continue
        if c in ('"', "'"):
            q = c; out.append(c); i += 1; continue
        if c == '/' and i + 1 < n and text[i + 1] == '/':
            while i < n and text[i] != '\n':
                i += 1
            continue
        out.append(c); i += 1
    return ''.join(out)


def _load_skill_defs():
    """解析生成文件 `export const SKILL_DEFS = {...}` 真身 → dict（18 技能全量·G8a 起真身在生成文件）。"""
    text = _strip_js_comments(_MIRROR_JS.read_text(encoding='utf-8'))
    m = re.search(r'export const SKILL_DEFS\s*=\s*\{', text)
    assert m, 'contract_mirror.generated.js 未找到 SKILL_DEFS 导出'
    return _parse_js_object(text, m)


def _load_tool_alias():
    """解析生成文件 `export const TOOL_ALIAS = {...}` 真身 → dict。"""
    text = _strip_js_comments(_MIRROR_JS.read_text(encoding='utf-8'))
    m = re.search(r'export const TOOL_ALIAS\s*=\s*\{', text)
    assert m, 'contract_mirror.generated.js 未找到 TOOL_ALIAS 导出'
    return _parse_js_object(text, m)


def _parse_js_object(text, m):
    """从 re.match 处提取完整花括号对象并 JSON 化（键引号补齐/单引号/尾逗号容错）。"""
    depth, end, start = 0, None, m.end() - 1
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                end = i; break
    assert end is not None, '花括号不配对（生成文件语法异常？）'
    block = text[start:end + 1]
    block = re.sub(r"(?<=[{,\n])\s*([A-Za-z_$][\w$]*)\s*:", lambda mm: '"' + mm.group(1) + '":', block)
    block = block.replace("'", '"')
    block = re.sub(r",\s*([}\]])", r"\1", block)
    return json.loads(block)


SKILL_DEFS_JS = _load_skill_defs()
SKILL_DEFS_DEFAULTS = {k: v.get('optional_defaults', {}) for k, v in SKILL_DEFS_JS.items()}


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
    """contracts defaults == 前端 SKILL_DEFS.optional_defaults（G8a 真身=生成文件）。"""
    errs = []
    for skill, js_defaults in SKILL_DEFS_DEFAULTS.items():
        cd = _contracts_defaults(skill)
        if cd is None:
            errs.append(f"contracts 缺 skill={skill}")
            continue
        if cd != js_defaults:
            errs.append(f"[{skill}] contracts={cd} ≠ 前端SKILL_DEFS={js_defaults}（改 contracts 后须 py tools/gen_stages_mirror.py 再生成）")
    assert not errs, '\n'.join(errs)


def test_mirror_freshness():
    """G8a：生成文件新鲜度——磁盘内容 == 生成器渲染（派生 diff=0·PT-CB1 T2 验收项）。"""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
    import gen_stages_mirror
    committed = _MIRROR_JS.read_text(encoding='utf-8')
    rendered = gen_stages_mirror.render()
    assert committed == rendered, (
        'contract_mirror.generated.js 与 tool_contracts.py 派生结果不一致——'
        '改契约后须执行 `py tools/gen_stages_mirror.py` 再生成并提交（禁手改生成文件）'
    )


def test_tool_alias_derived():
    """G8a：TOOL_ALIAS == contracts 各工具 params[].alias 按工具派生（禁手改/漏项）。"""
    js_alias = _load_tool_alias()
    expected = {}
    for c in TOOL_CONTRACTS:
        tool = c.get('tool')
        if not tool:
            continue
        m = {}
        for p in c.get('params', []):
            for a in p.get('alias', []):
                m[a] = p['name']
        if m:
            expected[tool] = m
    errs = []
    for tool, exp_map in expected.items():
        got = js_alias.get(tool)
        if got != exp_map:
            errs.append(f"[{tool}] contracts={exp_map} ≠ 生成文件={got}")
    extra = set(js_alias) - set(expected)
    if extra:
        errs.append(f"生成文件多出无契约工具: {sorted(extra)}")
    assert not errs, '\n'.join(errs)


def test_geo_catalog_guard_fields_report():
    """G8a 报告项（不 fail）：paradigm guard 4 字段（scale/preconditions/failure_modes/examples）
    与 contracts 的差异清单。该 4 字段手写属 diagnose prompt 内容（永不动红线）——
    差异不阻塞，但必须可见：改 contracts 这些字段时须显式决定是否同步 paradigm（走 prompt 豁免流程）。"""
    derived = {d['name']: d for d in derive_geo_catalog()}
    diffs = []
    for t in P.GEO_TOOL_CATALOG:
        d = derived.get(t['name'])
        if not d:
            continue
        for k in ('scale', 'preconditions', 'failure_modes', 'examples'):
            if d.get(k) != t.get(k):
                diffs.append(f"[{t['name']}].{k}")
    if diffs:
        print(f"\n[G8a][报告] paradigm guard 字段与 contracts 差异 {len(diffs)} 处（prompt 红线保护区·改动须豁免流程）：")
        for x in diffs:
            print(f"  {x}")
    else:
        print("\n[G8a][报告] paradigm guard 字段与 contracts 全一致")


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
        ('mirror_freshness', test_mirror_freshness),
        ('tool_alias_derived', test_tool_alias_derived),
        ('geo_catalog_guard_fields_report', test_geo_catalog_guard_fields_report),
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
