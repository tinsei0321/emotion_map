# -*- coding: utf-8 -*-
"""PT-CB9 · A1 上下文前注生成器（消融层试验·数据/表格类 chunk 专用域）。

v1.2 判决：A1=消融层可选件·数据喊痛才开——基线+泳道②后 miss 集中于表格类 chunk 语境缺失
（占比表/体检数据文件），本脚本对限定域生成 ctx_prefix（1-2 句·文档名+小节定位+口径状态）。

护栏（v1.2-pre §二）:
  1. 生成物进 git（docs/urban-renewal-plan/_ctx_prefix_map.json·chunk source→前注+模型+hash）
  2. 增量：仅对 map 中缺失/正文变更的 chunk 生成（--generate 跳过已有）
  3. 三字段沿 loader 契约（ctx_prefix/ctx_prefix_model/ctx_prefix_hash）

用法:
  py tools/rag_ctx_prefix.py --generate     # 增量生成（DeepSeek flash·确定性参数）
  py tools/rag_ctx_prefix.py --stats        # 查看覆盖统计
"""
import argparse
import hashlib
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, 'tools'))

MAP_PATH = os.path.join(REPO, 'docs', 'urban-renewal-plan', '_ctx_prefix_map.json')

# 限定域（v1.2 判决·口径/数据类专用）：占比表族 + 体检数据交付族 + 总纲
SCOPE_PREFIXES = (
    '3prime/占比表_',
    '3prime/77项_',
    '3prime/B1_客观落位',
    '3prime/B2_主观落位',
    '3prime/B3B4_归纳与落图',
    '3prime/分析计划与内容_总纲',
    '00-宜昌专项/03-10',
    '00-宜昌专项/03-07',
)

_PROMPT = (
    '你是知识库编目员。给下面这段资料生成一句「上下文前注」（30-60 字），'
    '必须包含：所属文档主题 + 本节讲什么 + 数据时点或口径状态（如有）。'
    '只输出前注本身，不要解释。\n\n资料片段：\n'
)


def _text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]


def _load_map():
    if os.path.exists(MAP_PATH):
        with io.open(MAP_PATH, encoding='utf-8') as fh:
            return json.load(fh)
    return {}


def _save_map(m):
    with io.open(MAP_PATH, 'w', encoding='utf-8', newline='') as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def _in_scope(source):
    rel = source.replace('docs/urban-renewal-plan/', '', 1)
    return any(rel.startswith(p) for p in SCOPE_PREFIXES)


def generate():
    from ai_qa.llm import chat_with_fallback
    from tools.rag_index import _load_notes
    chunks = [c for c in _load_notes() if _in_scope(c['source'])]
    m = _load_map()
    made, skipped = 0, 0
    for c in chunks:
        src, text = c['source'], c['text']
        th = _text_hash(text)
        ent = m.get(src)
        if ent and ent.get('text_hash') == th and ent.get('ctx_prefix'):
            skipped += 1
            continue
        toks = []
        try:
            for item in chat_with_fallback(
                    [{'role': 'user', 'content': _PROMPT + text[:1500]}],
                    tier='flash', stream=False, with_reason=True):
                # with_reason=True → ('reason'|'content', tok)·尾包 ('usage', {...}) 滤除
                if isinstance(item, tuple) and len(item) == 2 and item[0] == 'content':
                    toks.append(item[1])
        except Exception as exc:
            print(f'[WARN] 生成失败跳过: {src}: {exc}')
            continue
        prefix = ''.join(toks).strip().replace('\n', ' ')[:120]
        if not prefix:
            print(f'[WARN] 空前注跳过: {src}')
            continue
        m[src] = {'ctx_prefix': prefix, 'text_hash': th,
                  'model': 'deepseek-flash@2026-08', 'lineage': c.get('lineage')}
        made += 1
        print(f'[OK] {src[:58]} -> {prefix[:44]}...')
    _save_map(m)
    print(f'=== 生成 {made} 条·跳过（未变更）{skipped} 条·map 总 {len(m)} ===')
    # PT-CB9 L3（护栏 4）：返回计数供 --build 一体化摘要（禁手工两步·双机一条命令）
    return {'made': made, 'skipped': skipped, 'map_total': len(m)}


def stats():
    from tools.rag_index import _load_notes
    chunks = _load_notes()
    scoped = [c for c in chunks if _in_scope(c['source'])]
    m = _load_map()
    covered = sum(1 for c in scoped if c['source'] in m)
    print(f'限定域 chunk: {len(scoped)} ·已覆盖: {covered} ·map 总条目: {len(m)}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--generate', action='store_true')
    ap.add_argument('--stats', action='store_true')
    args = ap.parse_args()
    if args.generate:
        generate()
    elif args.stats:
        stats()
    else:
        print(__doc__)
