# -*- coding: utf-8 -*-
"""PT-CB9 P0-1/P0-2 · RAG 黄金集评测器 v2（60 条分类版）。

用法:
  py tools/rag_eval.py              # 核心集 60 条分类 Recall@5 + 旧集刚性判据
  py tools/rag_eval.py --k 5        # 指定 Top-K
  py tools/rag_eval.py --json       # 机读输出（P0-3 门禁用）

组成（v1.2-pre §5.2·tests/rag_golden.yaml）:
  - 分类 Recall@5: caliber/noun/checkup/narrative 四类（软指标·分类呈现防均值掩盖结构）
  - 刚性判据: 越维降级 + 案例不引他城数据（沿 CB-22 rag_gold_set·100% 刚性）
纯函数·ASCII 标记·不调 LLM。
"""
import argparse
import io
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / 'tools'))

from tools.rag_gold_set import GOLD_SET
from tools.rag_index import search


def _tag(ok, msg):
    print(f'[{"OK" if ok else "ERR"}] {msg}')


def load_golden_yaml():
    import yaml
    with io.open(REPO / 'tests' / 'rag_golden.yaml', encoding='utf-8') as fh:
        return yaml.safe_load(fh)


def eval_recall_by_category(k=5, verbose=True):
    """新核心集：60 条·file 级前缀 OR 语义·分类 Recall@K。"""
    golden = load_golden_yaml()
    rows = []
    for cat, items in golden.items():
        for it in items:
            res = search(it['query'], k=it.get('k', k))
            got = [r.get('source', '') for r in (res.get('results') or [])]
            # 归一化：yaml 用语料相对路径·实际 source 带 'docs/urban-renewal-plan/' 或 'ai_qa/' 前缀
            norm = [g.replace('docs/urban-renewal-plan/', '', 1).replace('ai_qa/', '', 1) for g in got]
            hit = any(any(g.startswith(pfx) for pfx in it['expect']) for g in norm)
            rows.append({'id': it['id'], 'category': cat, 'query': it['query'],
                         'hit': hit, 'top1': got[0] if got else ''})
    cats = sorted({r['category'] for r in rows})
    out = {
        'n': len(rows),
        'recall': sum(r['hit'] for r in rows) / max(1, len(rows)),
        'by_category': {c: {'n': sum(1 for r in rows if r['category'] == c),
                            'recall': round(sum(r['hit'] for r in rows if r['category'] == c)
                                            / max(1, sum(1 for r in rows if r['category'] == c)), 4)}
                        for c in cats},
        'misses': [r for r in rows if not r['hit']],
    }
    if verbose:
        for m in out['misses']:
            print(f"  [MISS] {m['id']} [{m['category']}] {m['query'][:26]} | top1={m['top1'][:56]}")
    return out


def eval_rigid():
    """旧集刚性判据：越维 + 案例不引他城数据（100%）。"""
    dim_pass, dim_n, case_pass, case_n = True, 0, True, 0
    for item in GOLD_SET:
        if item['type'] not in ('dimension', 'case_data'):
            continue
        r = search(item['query'], item.get('k', 5))
        if not r.get('ok'):
            continue
        if item['type'] == 'dimension':
            dim_n += 1
            dims = [x.get('data_dim', '') for x in r['results']]
            if item['expect_dim'] not in dims:
                dim_pass = False
                _tag(False, f"越维: {item['query'][:24]} 期望 {item['expect_dim']} 未在 Top")
        else:
            case_n += 1
            joined = ' '.join(x['source'] for x in r['results'])
            bad = [kw for kw in item['forbid_kw'] if kw in joined]
            if bad:
                case_pass = False
                _tag(False, f"案例数据: {item['query'][:24]} 含 {bad}")
    return {'dim_pass': dim_pass, 'dim_n': dim_n, 'case_pass': case_pass, 'case_n': case_n}


def evaluate(k=5, as_json=False):
    rec = eval_recall_by_category(k=k, verbose=not as_json)
    rigid = eval_rigid()
    report = {'recall_at_k': round(rec['recall'], 4), 'k': k, 'n': rec['n'],
              'by_category': rec['by_category'], 'miss_count': len(rec['misses']),
              **rigid}
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"=== 黄金集 v2（{rec['n']} 条·Top-{k}）===")
        print(f"  总体 Recall@{k}: {rec['recall']:.1%}")
        for c, v in rec['by_category'].items():
            print(f"  {c:10s} n={v['n']:2d}  recall={v['recall']:.1%}")
        print(f"  越维降级: {'通过' if rigid['dim_pass'] else '失败'}（刚性·{rigid['dim_n']} 例）")
        print(f"  案例不引他城数据: {'通过' if rigid['case_pass'] else '失败'}（刚性·{rigid['case_n']} 例）")
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    evaluate(k=args.k, as_json=args.json)
