# ════════════ G8b（PT-CB5 T2）动态开卷定参 · 契约测试 ════════════
#
# 守护三件事：
#   1. source 参数实时枚举非空且含已知 id（开卷成立）；
#   2. **铁律7/G-2 硬断言**：usage=analysis_output 的层绝不出现在任何枚举里（结论层禁作输入）；
#   3. 兜底：源不可用 → 静态 schema 不崩（结构不变只是无动态 enum）。
# 红线口径：本机制只动 schema enum/description（契约派生链内）·diagnose prompt 文本零接触。

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_qa.tool_contracts import derive_dynamic_enums, contracts_to_tools_schema, _PRESET_MANIFEST


def test_enums_nonempty_and_known_ids():
    dyn = derive_dynamic_enums()
    assert 'layer' in dyn and 'yichang_l2_t1' in dyn['layer'], '点层枚举缺失已知 id'
    assert 'boundary' in dyn and 'admin_district' in dyn['boundary'], 'preset 枚举缺失已知 id'
    for p in ('range', 'center', 'target', 'layer_a', 'layer_b', 'boundaries', 'layers'):
        assert p in dyn, f'source 参数 {p} 未获得实时枚举'


def test_analysis_output_never_in_enums():
    """铁律7/G-2 硬断言：结论层（usage=analysis_output）禁止出现在任何输入枚举。"""
    dyn = derive_dynamic_enums()
    manifest = json.loads(_PRESET_MANIFEST.read_text(encoding='utf-8'))
    stale_ids = {it['id'] for g in manifest for it in g.get('items', []) if it.get('usage') == 'analysis_output'}
    assert stale_ids, 'manifest 无 analysis_output 项（测试前提失效·检查 manifest）'
    for param, ids in dyn.items():
        leaked = stale_ids.intersection(ids)
        assert not leaked, f'[{param}] 枚举漏入结论层（铁律7 违规）: {sorted(leaked)}'


def test_live_schema_injects_enums():
    tools = contracts_to_tools_schema()
    by_name = {t['function']['name']: t for t in tools}
    dens_layer = by_name['density']['function']['parameters']['properties']['layer']
    assert dens_layer.get('enum') and 'yichang_l2_t1' in dens_layer['enum'], 'density.layer 未注入点层枚举'
    assert '实时数据清单' in dens_layer.get('description', ''), '开卷描述缺失'
    cmp_bound = by_name['compare_regions']['function']['parameters']['properties']['boundaries']
    assert cmp_bound.get('enum') and 'admin_district' in cmp_bound['enum'], 'compare.boundaries 未注入 preset 枚举'
    # 静态 enum 不被覆盖：polarity 等手写枚举原样
    dens_pol = by_name['density']['function']['parameters']['properties']['polarity']
    assert dens_pol['enum'] == ['overall', 'positive', 'negative', 'neutral'], '手写枚举被动态覆盖（违规）'


def test_fallback_static_on_missing_manifest(tmp_path, monkeypatch):
    """源不可用 → 静态兜底：不崩·schema 结构不变（仅无动态 enum）。"""
    import ai_qa.tool_contracts as tc
    monkeypatch.setattr(tc, '_PRESET_MANIFEST', tmp_path / 'nonexistent.json')
    dyn = tc.derive_dynamic_enums()
    assert 'boundary' not in dyn and 'range' not in dyn, 'manifest 缺失时 preset 枚举应缺省'
    tools = tc.contracts_to_tools_schema()
    assert len(tools) >= 13, '兜底 schema 工具数异常'
    by_name = {t['function']['name']: t for t in tools}
    assert 'enum' not in by_name['compare_regions']['function']['parameters']['properties']['boundaries'], \
        '兜底模式不应有动态 enum'


def test_static_mode_keeps_plain_schema():
    """live_enums=False → 与旧版结构等价（无动态 enum·回退开关）。"""
    tools = contracts_to_tools_schema(live_enums=False)
    by_name = {t['function']['name']: t for t in tools}
    layer_prop = by_name['density']['function']['parameters']['properties']['layer']
    assert 'enum' not in layer_prop, 'live_enums=False 仍带动态 enum（开关失效）'


if __name__ == '__main__':
    for name, fn in [(k, v) for k, v in sorted(globals().items()) if k.startswith('test_') and callable(v)]:
        try:
            import inspect
            if 'tmp_path' in inspect.signature(fn).parameters or 'monkeypatch' in inspect.signature(fn).parameters:
                print(f'[SKIP] {name}（pytest fixture 用例·请在 pytest 下运行）')
                continue
            fn()
            print(f'[PASS] {name}')
        except AssertionError as e:
            print(f'[FAIL] {name}: {e}')
            sys.exit(1)
    print('\n[OK] G8b 动态开卷定关测试全过（fixture 用例除外）')
