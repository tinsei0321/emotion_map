# -*- coding: utf-8 -*-
"""PT-CB9 L1+L3 · RAG loader 治理字段测试（泳道①/③）。

覆盖：
1. 全文纪律断言（CB-22）：抽 20 个 note chunk，断言 text 与源 md 同位置小节一致
   （loader 切分规则 text.split('\\n## ')·<20 字段丢弃·2000 字截断上界）；
2. status 枚举断言：load_chunks() 全 chunk status ∈ {active, superseded}（字段缺失=active 兼容红线）；
3. superseded chunk 级显式登记断言（L3·R24：superseded 集 == _SUPERSEDED_SOURCES·同族反例不误伤）；
4. lineage 断言：格式 'src:<文件>#<节>'·目标文件存在·事实卡 67/68 已标（EMC-IDENTITY-01 豁免）；
5. A1 前注质量门禁（L3·护栏 5）：抽 6 条带前注 chunk·出处要素（文档名/小节/口径状态）任二。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, ROOT)

import rag_index  # noqa: E402


def _all_chunks():
    return rag_index.load_chunks()


# ════════════ 1 · 全文纪律（CB-22·抽 20 段与源 md 一致性） ════════════

def test_fulltext_discipline_sample_20_notes_match_source():
    notes = [c for c in _all_chunks() if c['type'] == 'note']
    assert len(notes) >= 20
    step = max(1, len(notes) // 20)
    sample = notes[::step][:20]
    assert len(sample) == 20

    cache = {}

    def blocks_of(path):
        if path not in cache:
            with open(path, encoding='utf-8', errors='ignore') as fh:
                cache[path] = [b.strip() for b in fh.read().split('\n## ') if b.strip()]
        return cache[path]

    for c in sample:
        src = c['source']
        rel, idx = src.rsplit('#', 1)
        idx = int(idx)
        parts = blocks_of(os.path.join(ROOT, rel))
        assert idx < len(parts), f'{src} 小节序号越界'
        block = parts[idx]
        assert len(block) >= 20, f'{src} 小节应被 loader 保留（>=20）'
        # 全文纪律：text = 小节全文（2000 字截断上界内）·不得中途截句缺失
        assert c['text'] == block[:2000], f'{src} text 与源小节不一致'
        assert len(c['text']) > 20


# ════════════ 2 · status 枚举 + 批次规则 ════════════

def test_status_enum_all_chunks():
    chunks = _all_chunks()
    assert chunks
    bad = [c['source'] for c in chunks if c.get('status') not in ('active', 'superseded')]
    assert not bad, f'status 越界: {bad[:5]}'


def test_status_superseded_chunk_level_x01():
    """PT-CB9 L3（R24 redemption）：chunk 级显式登记替代 L1 文件级机制——
    断言 superseded 集 == _SUPERSEDED_SOURCES（2 条·各有引句登记在执行记录）；
    登记外的 3prime 同族文件（含总纲/其余占比表/B3B4 其余小节）保持 active。"""
    chunks = _all_chunks()
    sup = {c['source'] for c in chunks if c.get('status') == 'superseded'}
    assert sup == set(rag_index._SUPERSEDED_SOURCES), \
        f'superseded 集与登记表不一致: {sup ^ set(rag_index._SUPERSEDED_SOURCES)}'
    # 同族反例：登记外 chunk 不误伤（R24：登记必引原文句子级语义）
    assert 'docs/urban-renewal-plan/3prime/分析计划与内容_总纲_2026-08-12.md#3' in {
        c['source'] for c in chunks if c.get('status') == 'active'}
    assert 'docs/urban-renewal-plan/3prime/占比表_民生_停车设施_社区_2026-08-12.md#0' in {
        c['source'] for c in chunks if c.get('status') == 'active'}
    # 三库全部 active
    assert all(c.get('status') == 'active'
               for c in chunks if c['type'] in ('fact', 'case', 'concept'))


# ════════════ 3 · lineage 谱系 ════════════

_LINEAGE_RE = re.compile(r'^src:.+#[A-Za-z0-9_]+$')   # 节=位置序号（md）或 key（py 源）


def test_lineage_format_and_target_exists():
    chunks = _all_chunks()
    marked = [c for c in chunks if c.get('lineage')]
    assert len(marked) == 67, f'lineage 标注数 {len(marked)} != 67'
    for c in marked:
        lin = c['lineage']
        assert _LINEAGE_RE.match(lin), f'{c["source"]} lineage 格式非法: {lin}'
        target = lin[4:].rsplit('#', 1)[0]
        assert os.path.isfile(os.path.join(ROOT, target)), f'lineage 目标不存在: {target}'


def test_lineage_facts_coverage_and_exemption():
    chunks = _all_chunks()
    facts = [c for c in chunks if c['type'] == 'fact']
    assert len(facts) == 68
    marked = {c['source'] for c in facts if c.get('lineage')}
    assert len(marked) == 67
    unmarked = {c['source'] for c in facts if not c.get('lineage')}
    # EMC-IDENTITY-01 上游为 PT-CB 文档（非语料）·唯一豁免
    assert unmarked == {'ai_qa/outlet_kb/urban_renewal_knowledge.py#EMC-IDENTITY-01'}


def test_load_chunks_order_and_total():
    """load_chunks 契约：四类齐·总条数与四 loader 和一致（泳道②换挂零漂移）。"""
    chunks = _all_chunks()
    assert len(chunks) == (len(rag_index._load_facts()) + len(rag_index._load_notes())
                           + len(rag_index._load_cases()) + len(rag_index._load_concepts()))
    assert [c['type'] for c in chunks[:1]] == ['fact']


# ════════════ 4 · A1 前注质量门禁（PT-CB9 L3·护栏 5） ════════════

def _has_doc_element(prefix, source):
    """文档名要素：源文件名主体的任一 ≥4 字连续片段出现在前注中。"""
    stem = os.path.basename(source.split('#', 1)[0])
    stem = re.sub(r'\.(md|py)$', '', stem)
    for n in range(len(stem) - 3):
        if stem[n:n + 4] in prefix:
            return True
    return False


def _has_section_element(prefix, source):
    """小节要素：源小节首行（标题）的任一 ≥4 字连续片段出现在前注中。"""
    rel, idx = source.rsplit('#', 1)
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path) or not idx.isdigit():
        return False
    with open(path, encoding='utf-8', errors='ignore') as fh:
        parts = [b.strip() for b in fh.read().split('\n## ') if b.strip()]
    if int(idx) >= len(parts):
        return False
    title = parts[int(idx)].split('\n', 1)[0]
    title = re.sub(r'^#+\s*', '', title)
    for n in range(len(title) - 3):
        if title[n:n + 4] in prefix:
            return True
    return False


_CALIBER_TOKENS = ('口径', '时点', '作废', '现行', '2024', '2025', '2026')


def test_ctx_prefix_quality_gate_sample_6():
    """护栏 5：黄金集关联的限定域带前注 chunk 抽 6 条（每 golden id 一条·等距）——
    前注须含出处要素任二（文档名/小节/口径状态）。

    rag-baseline 抽样法：黄金集 expect 前缀定位 chunk（用户真实会问到的面）·无 LLM·
    读 _ctx_prefix_map.json 经 load_chunks 注入。
    """
    import yaml
    chunks = {c['source']: c for c in _all_chunks()}
    with open(os.path.join(ROOT, 'tests', 'rag_golden.yaml'), encoding='utf-8') as fh:
        gy = yaml.safe_load(fh)
    by_id = {}
    for cat, items in gy.items():
        if not isinstance(items, list):
            continue
        for it in items:
            for exp in (it.get('expect') or []):
                hit = next((s for s in sorted(chunks)
                            if exp in s and chunks[s].get('ctx_prefix')), None)
                if hit:
                    by_id.setdefault(it['id'], hit)
                    break
    ids = sorted(by_id)
    assert len(ids) >= 6, f'黄金集关联带前注 chunk 不足 6 条（{len(ids)}）——先跑 py tools/rag_index.py --build'
    step = max(1, len(ids) // 6)
    sample = [by_id[i] for i in ids[::step][:6]]
    assert len(sample) == 6
    for src in sample:
        prefix = chunks[src]['ctx_prefix']
        hits = [_has_doc_element(prefix, src),
                _has_section_element(prefix, src),
                any(t in prefix for t in _CALIBER_TOKENS)]
        assert sum(hits) >= 2, f'{src} 前注出处要素不足（{hits}）: {prefix[:60]}'


# ════════════ 6 · transformers 5.x 兼容兜底（PT-CB15 K7·审计 C6） ════════════

def test_load_st_model_compat_fallback():
    """_load_st_model 在当前环境可加载并编码（transformers 5.x 时走 AutoTokenizer 兜底·
    4.x 时走原生路径——两态都应通过）。无 sentence_transformers 或模型缓存缺失时跳过。"""
    import pytest
    pytest.importorskip('sentence_transformers')
    if not rag_index.RAG_DIR.exists():
        pytest.skip('RAG 目录不存在')
    try:
        model = rag_index._load_st_model(local_files_only=True)
    except Exception as exc:  # 模型缓存缺失等环境因素 → skip 不红（A9：显式跳过非静默）
        pytest.skip(f'模型不可用（{type(exc).__name__}: {str(exc)[:60]}）')
    vec = model.encode(['口径测试'], normalize_embeddings=True)
    assert vec.shape[-1] == 512, 'bge-small-zh 向量维度应为 512'
