# -*- coding: utf-8 -*-
"""PT-CB9 P0-3 · RAG 门禁（快档·Q-A 裁定）+ D4 双入口断言。

设计（v1.1 修-1 + v1.2 终版）:
  - 基线相对制：读 tests/rag_gate_snapshot.json 对照——抽样条目不允许 hit→miss 翻转（零退化）
    （满分断言留收口总验收·全量 60 条手动跑: py tools/rag_eval.py）
  - 刚性判据：越维降级 + 案例不引他城数据·动态计数 100%
  - skipif 两态：索引缺失 OR sentence-transformers 不可用 → skip 不红（开门不红）
  - 模型加载 module-scope 单次（BGE 预热 ~15s·全档 ~25s）
  - D4：MCP rag_query 与 rag_index.search 同一检索核心——sources 逐位相等（换脑零知识损失守门）
"""
import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / 'tools'))

_INDEX = REPO / 'DATA' / 'RAG' / 'rag_index'
if not (_INDEX / 'vectors.npy').exists():
    pytest.skip('RAG 索引未构建（py tools/rag_index.py --build）', allow_module_level=True)
st = pytest.importorskip('sentence_transformers', reason='sentence-transformers 未安装')

from tools.rag_eval import eval_rigid, load_golden_yaml  # noqa: E402
from tools.rag_index import search  # noqa: E402

_SNAPSHOT = REPO / 'tests' / 'rag_gate_snapshot.json'


def _norm(src):
    return src.replace('docs/urban-renewal-plan/', '', 1).replace('ai_qa/', '', 1)


def _hit(query, expects, k=5):
    res = search(query, k=k)
    got = [_norm(r.get('source', '')) for r in (res.get('results') or [])]
    return any(any(g.startswith(p) for p in expects) for g in got)


# 快档抽样：固定步长取 12 条（确定性抽样·非随机）
_SAMPLE_STEP = 5


def test_rigid_judgments_100_percent():
    out = eval_rigid()
    assert out['dim_pass'] and out['dim_n'] >= 1, '越维降级刚性判据失败（红线条目）'
    assert out['case_pass'] and out['case_n'] >= 1, '案例不引他城数据刚性判据失败（红线条目）'


def test_sample_zero_regression_vs_snapshot():
    """抽样 12 条对照快照：不允许 hit→miss 翻转（miss→hit 的改善放行）。"""
    if not _SNAPSHOT.exists():
        pytest.skip('快照未生成（py tools/rag_eval.py --snapshot）')
    with open(_SNAPSHOT, encoding='utf-8') as fh:
        snap = json.load(fh)
    by_id = {e['id']: e for e in snap['entries']}
    golden = load_golden_yaml()
    flat = [dict(it, category=cat) for cat, items in golden.items() for it in items]
    sample = flat[::_SAMPLE_STEP]
    assert len(sample) >= 10, '抽样数异常'
    flips = []
    for it in sample:
        base_hit = by_id.get(it['id'], {}).get('hit')
        if base_hit is None:
            continue
        now_hit = _hit(it['query'], it['expect'])
        if base_hit and not now_hit:
            flips.append(f"{it['id']} {it['query'][:20]}")
    assert not flips, f'抽样零退化违例（hit→miss 翻转）: {flips}'


def test_dual_entry_single_core_d4():
    """D4：MCP rag_query 与检索核心 search 同源——Top-K sources 逐位相等。

    PT-CB9R-B3 扩展：条目标注一致性（caliber_note 逐位相等）+ 过滤观测一致性（suppressed_count 相等）。"""
    from tools.mcp_server_emc import rag_query
    for q, k in [('什么是情绪地图', 3), ('双高 16 格', 10)]:   # k≤10（rag_query 夹取上限·超限会致长度分叉）
        via_mcp = rag_query(query=q, k=k, synthesize=False)
        via_core = search(q, k=k)
        mcp_src = [r.get('source') for r in (via_mcp.get('results') or [])]
        core_src = [r.get('source') for r in (via_core.get('results') or [])]
        assert mcp_src == core_src, f'双入口分叉: mcp={mcp_src[:2]} core={core_src[:2]}'
        mcp_notes = [r.get('caliber_note') for r in (via_mcp.get('results') or [])]
        core_notes = [r.get('caliber_note') for r in (via_core.get('results') or [])]
        assert mcp_notes == core_notes, f'双入口标注分叉（{q[:8]}）: mcp={mcp_notes} core={core_notes}'
        assert via_mcp.get('suppressed_count') == via_core.get('suppressed_count'), \
            f'suppressed_count 分叉: {via_mcp.get("suppressed_count")} vs {via_core.get("suppressed_count")}'


def test_x01_history_annotation_existence():
    """PT-CB9R-B3 +2-1：历史叙述类条目（X-01 关联登记 chunk）带 caliber_note·替代指针确定性。

    ①登记表↔语料一致性（登记源必须存在且 active·superseded 指针源必须已登记作废）；
    ②派生函数逐条确定性（现行见<替代指针>）；
    ③检索面——命中登记 chunk 的查询在返回条目上可见标注。
    """
    from tools import rag_index as _ri
    chunks = _ri.load_chunks()
    by_src = {c['source']: c for c in chunks}
    for src, ptr in _ri._X01_HISTORICAL_NARRATIVE.items():
        assert src in by_src, f'登记源不在语料: {src}'
        assert by_src[src].get('status') == 'active', f'登记源应为 active: {src}'
        assert _ri._history_note(src) == f'历史口径·现行见{ptr}'
    for src in _ri._X01_SUPERSEDED_POINTERS:
        assert src in _ri._SUPERSEDED_SOURCES, f'superseded 指针源未登记作废: {src}'
    res = search('双高 16 格', k=15)
    rows = res.get('results', [])
    tagged = [r for r in rows if r.get('caliber_note')]
    assert tagged, '检索未命中任何 X-01 登记 chunk（语料/索引变动·先核对登记表）'
    for r in tagged:
        assert r['caliber_note'] == f'历史口径·现行见{_ri._X01_HISTORICAL_NARRATIVE[r["source"]]}'


def test_current_entries_zero_label():
    """PT-CB9R-B3 +2-2：现行条目零标签——登记集外 chunk 一律无 caliber_note（不对称标注默认态）。

    全语料 meta 级断言（登记集变更必须显式改登记表+本测试同步）；检索面同断言。"""
    from tools import rag_index as _ri
    vectors, metas = _ri.load_index()
    assert vectors is not None, '索引不可用（py tools/rag_index.py --build）'
    for m in metas:
        src = m.get('source', '')
        note = _ri._history_note(src, m.get('lineage'))
        if src in _ri._X01_HISTORICAL_NARRATIVE:
            continue
        assert note is None, f'{src} 不应被标注: {note}'
    res = search('葛洲坝有哪些更新项目', k=10)
    for r in res.get('results', []):
        if r.get('source') in _ri._X01_HISTORICAL_NARRATIVE:
            assert r.get('caliber_note')
        else:
            assert 'caliber_note' not in r
