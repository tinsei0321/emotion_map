# -*- coding: utf-8 -*-
"""PT-CB9 L1 · RAG loader 治理字段测试（泳道①）。

覆盖：
1. 全文纪律断言（CB-22）：抽 20 个 note chunk，断言 text 与源 md 同位置小节一致
   （loader 切分规则 text.split('\\n## ')·<20 字段丢弃·2000 字截断上界）；
2. status 枚举断言：load_chunks() 全 chunk status ∈ {active, superseded}（字段缺失=active 兼容红线）；
3. superseded 批次断言：3prime 15 个数据文件全节命中·总纲（待裁豁免）保持 active；
4. lineage 断言：格式 'src:<文件>#<节>'·目标文件存在·事实卡 67/68 已标（EMC-IDENTITY-01 豁免）。
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


def test_status_superseded_batch_3prime():
    """主手裁决改写（08-22·L1 回收）：3prime 批量压旧系对 03-10§一 的语义误读——
    原文=「新区增量·空间互斥·直接相加」非取代→占比表族回 active·规则表清空（机制保留）。
    本测试现断言回滚态：全域 active·规则表位在（空=无文件级压旧）。"""
    chunks = _all_chunks()
    sup = [c for c in chunks if c.get('status') == 'superseded']
    assert not sup, f'回滚后不应有 superseded chunk（现存 {len(sup)}·如为 X-01 作废定位请显式登记规则表）'
    # 机制保留：规则表常量在（空=无文件级压旧·真正作废走逐 chunk 显式登记）
    from tools import rag_index as _ri
    assert hasattr(_ri, '_SUPERSEDED_FILE_PREFIX')
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
