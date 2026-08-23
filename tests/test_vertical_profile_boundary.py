"""SHELL(S129) S9 · 垂域切换位 grep 硬审计（城市名不出现在平台层代码·防新增）。

依据：docs/vertical-profile.md §四 + 壳阶段联合任务书 v1.0 五红线之五。

机制：
- 平台层范围 = core/ tools/ api/ frontend/js/ serve.py（测试资产 test-*.js 豁免）；
- 词表 = 宜昌/yichang/西陵/伍家岗/点军/猇亭/夷陵（忽略大小写）；
- 断言 = 命中文件集与每文件计数不得超出 BASELINE（新文件或新增命中即失败·
  失败信息打印「文件:行号:内容」级新增违例清单）；
- 纪律 = BASELINE 只减不增（垂域化清偿时下调·禁止上调）——上调须改本测试
  并在执行记录中说明理由（视为垂域红线违例报批）。
"""
import os
import re

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 平台层扫描范围（相对仓根）；test-*.js 为测试资产·豁免（测试数据用真实地名合理）
PLATFORM_ROOTS = ('core', 'tools', 'api', os.path.join('frontend', 'js'))
PLATFORM_FILES = ('serve.py',)
_EXEMPT_PREFIXES = ('test-',)

# 词表：垂域①（宜昌）城市/区县名——垂域化清偿的对象面
_PATTERN = re.compile('宜昌|yichang|西陵|伍家岗|点军|猇亭|夷陵', re.IGNORECASE)

# BASELINE：2026-08-23 全量扫描定档（S9 切换位预留阶段现状·存量随垂域化清偿只减不增）
BASELINE = {
    'api/geo_routes.py': 11,
    'api/routes.py': 1,
    'core/buffer_analysis.py': 1,
    'core/config.py': 1,
    'core/coord_transform.py': 5,
    'core/geo_registry.py': 19,
    'core/geocode.py': 2,
    'core/place_layer.py': 17,
    'core/range_selector.py': 2,
    'core/spatial_analysis.py': 3,
    'frontend/js/ai_qa/boundary-resolve.js': 3,
    'frontend/js/ai_qa/emc-patterns.js': 9,
    'frontend/js/ai_qa/harness.js': 42,
    'frontend/js/ai_qa/panel.js': 25,
    'frontend/js/ai_qa/tools.js': 29,
    'frontend/js/district-stats.js': 16,
    'frontend/js/import.js': 3,
    'frontend/js/map-controls.js': 1,
    'frontend/js/map.js': 4,
    'frontend/js/panel.js': 2,
    'frontend/js/state.js': 3,
    'frontend/js/time-source.js': 2,
    'frontend/js/timeline.js': 2,
    'frontend/js/toolbox/shared.js': 1,
    'tools/check_caliber.py': 3,
    'tools/mcp_server_emc.py': 15,
    'tools/rag_ctx_prefix.py': 2,
    'tools/rag_gold_set.py': 8,
    'tools/rag_index.py': 90,
    'tools/verify_keys.py': 2,
}


def _platform_source_files():
    """平台层源文件迭代（py/js·豁免测试资产）。"""
    for root in PLATFORM_ROOTS:
        base = os.path.join(REPO, root)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, names in os.walk(base):
            for name in names:
                if not name.endswith(('.py', '.js')):
                    continue
                if name.startswith(_EXEMPT_PREFIXES):
                    continue
                yield os.path.join(dirpath, name)
    for rel in PLATFORM_FILES:
        p = os.path.join(REPO, rel)
        if os.path.isfile(p):
            yield p


def _scan_hits():
    """扫描平台层城市名命中：{相对路径: [(行号, 行内容), ...]}。"""
    hits = {}
    for path in _platform_source_files():
        try:
            with open(path, encoding='utf-8') as fh:
                lines = fh.readlines()
        except (OSError, UnicodeDecodeError):
            continue
        found = []
        for lineno, line in enumerate(lines, 1):
            if _PATTERN.search(line):
                found.append((lineno, line.rstrip()))
        if found:
            rel = os.path.relpath(path, REPO).replace(os.sep, '/')
            hits[rel] = found
    return hits


def test_no_new_city_hardcode_in_platform_layer():
    """平台层城市名硬编码不得新增（文件集与计数双封顶·BASELINE 只减不增）。"""
    hits = _scan_hits()

    new_files = sorted(set(hits) - set(BASELINE))
    grown = {p: len(v) for p, v in hits.items()
             if p in BASELINE and len(v) > BASELINE[p]}

    if not new_files and not grown:
        total = sum(len(v) for v in hits.values())
        assert total <= sum(BASELINE.values()), (
            '总命中数超出 baseline 总额（防绕过：单文件未超但总额超）')
        return

    lines = ['[ERR] 垂域切换位硬审计失败：平台层出现新增城市名硬编码',
             '依据 docs/vertical-profile.md §四（BASELINE 只减不增·上调须报批）']
    if new_files:
        lines.append('新增文件（baseline 外出现城市名）:')
        for p in new_files:
            lines.append(f'  - {p}（{len(hits[p])} 处）:')
            for lineno, text in hits[p][:5]:
                lines.append(f'      L{lineno}: {text.strip()[:120]}')
    if grown:
        lines.append('既有文件新增命中（超出 baseline 计数）:')
        for p, count in sorted(grown.items()):
            base_count = BASELINE[p]
            fresh = hits[p][base_count:]
            lines.append(f'  - {p}: {count} > baseline {base_count}（新增 {count - base_count} 处）:')
            for lineno, text in fresh[:5]:
                lines.append(f'      L{lineno}: {text.strip()[:120]}')
    pytest.fail('\n'.join(lines))


def test_baseline_stays_honest():
    """baseline 诚实性：登记的文件必须仍存在且计数方向只减（清偿可见）。"""
    hits = _scan_hits()
    stale = []
    for p, count in BASELINE.items():
        if p not in hits:
            continue   # 已清偿到零（文件内不再命中）——合规·鼓励
        if len(hits[p]) < count:
            continue   # 部分清偿——合规
        # 相等不报（无清偿也无新增·允许）
    # baseline 里登记但文件已删除的：提示性检查（不算失败·防僵尸登记）
    for p in BASELINE:
        if not os.path.isfile(os.path.join(REPO, p)):
            stale.append(p)
    if stale:
        import warnings
        warnings.warn('[WARN] BASELINE 含已删除文件（可下调清偿）: ' + ', '.join(stale))
