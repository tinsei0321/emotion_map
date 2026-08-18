#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G8a（PT-CB1 T2）：契约单一源 -> 前端契约镜像自动生成。

生成 frontend/js/ai_qa/contract_mirror.generated.js：
  - SKILL_DEFS（skill -> tool/category/required_slots/optional_defaults）
  - TOOL_ALIAS（tool -> {alias: canonical}·每工具全量·由 params[].alias 派生）

单一源 = ai_qa/tool_contracts.py（铁律 11）。旧 stages.js 手写镜像永久退役：
改契约只改 tool_contracts.py，然后 `py tools/gen_stages_mirror.py` 再生成；
CI 守护 = tests/validate_skill_params.py::test_mirror_freshness（派生 diff=0）。

别名分层说明（G8a 行为变更·有意）：
  旧版 = 通用 _PARAM_ALIAS + 工具专属 _TOOL_ALIAS 两层手写；通用层的
  field_name->'field' 为无主映射（漂移 bug·hotspot 无 field 参数）。G8a 起
  全部别名按工具派生（每工具自己的 params[].alias），语义严格更安全：
  同名别名在不同工具可指向不同规范名（如 lookup_place 的 name->q 与
  出图层工具的 name->as 不再互扰）。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from ai_qa.tool_contracts import TOOL_CONTRACTS, _derive_defaults  # noqa: E402

GEN_TARGET = REPO / 'frontend' / 'js' / 'ai_qa' / 'contract_mirror.generated.js'

_HEADER = """\
// ═══ contract_mirror.generated.js — 前端契约镜像（自动生成·禁手改）═══
// 单一源 = ai_qa/tool_contracts.py（铁律 11）。再生成：py tools/gen_stages_mirror.py
// CI 守护 = tests/validate_skill_params.py::test_mirror_freshness（派生 diff=0）。
// G8a（PT-CB1 T2·2026-08-18）：stages.js 手写 SKILL_DEFS/别名表永久退役。
// 承重纪律（承袭旧手写镜像注释）：rank/buffer/clip/zonal 不硬默认 layer——
//   硬默认会经 validateParams 合并绕过 resolvePointLayer 可见过滤（"只传 L1 却跑 L2"）；
//   contracts 中这些工具的 layer 参数无 default，生成结果自然保持无默认。
"""


def _skill_defs_entries():
    """TOOL_CONTRACTS -> [(skill, def_dict)]（排除 knowledge 伪工具·同 derive_template_registry 过滤）。"""
    out = []
    for c in TOOL_CONTRACTS:
        if c.get('category') == 'knowledge':
            continue
        out.append((c['skill'], {
            'tool': c.get('tool'),
            'category': c['category'],
            'required_slots': list(c.get('required_slots', [])),
            'optional_defaults': _derive_defaults(c.get('params', [])),
        }))
    return out


def _tool_alias_entries():
    """TOOL_CONTRACTS -> [(tool, {alias: canonical})]（仅单工具·全量别名·按工具隔离）。"""
    out = []
    for c in TOOL_CONTRACTS:
        tool = c.get('tool')
        if not tool:
            continue
        m = {}
        for p in c.get('params', []):
            for a in p.get('alias', []):
                m[a] = p['name']
        if m:
            out.append((tool, m))
    return out


def render():
    """确定性渲染生成文件全文（无时间戳·幂等）。"""
    lines = [_HEADER]
    lines.append('')
    lines.append('export const SKILL_DEFS = {')
    for skill, d in _skill_defs_entries():
        lines.append(f'  {skill}: ' + _dump(d) + ',')
    lines.append('};')
    lines.append('')
    lines.append('// 每工具全量别名（由 contracts 各工具 params[].alias 派生·G8a 起替代旧「通用+专属」双层手写）。')
    lines.append('export const TOOL_ALIAS = {')
    for tool, m in _tool_alias_entries():
        lines.append(f'  {tool}: ' + _dump(m) + ',')
    lines.append('};')
    lines.append('')
    return '\n'.join(lines)


def _dump(obj):
    import json
    return json.dumps(obj, ensure_ascii=False, separators=(', ', ': '))


def main():
    text = render()
    GEN_TARGET.write_text(text, encoding='utf-8', newline='\n')
    skills = _skill_defs_entries()
    aliases = _tool_alias_entries()
    print(f'[OK] contract_mirror.generated.js: SKILL_DEFS={len(skills)} skills, TOOL_ALIAS={len(aliases)} tools')
    print(f'[OK] target: {GEN_TARGET.relative_to(REPO)}')


if __name__ == '__main__':
    main()
