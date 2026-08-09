"""RAG 检索质量评估（CB-22 深度评估·黄金集 3 类）。

用法：
  py tools/rag_eval.py            # 跑黄金集·输出三类分项通过率
  py tools/rag_eval.py --k 5      # 指定 Top-K

三类判据（glm 刚性区分·CB-22 深度评估）：
- recall（正确召回）·Top-K 含期望 source·召回率 ≥80%（软指标）
- dimension（越维降级）·检索返回含维度标注·回答须声明不越维（刚性 100%·原则红线）
- case_data（案例不引数据）·Top-K 不含他城数据（刚性 100%·防张冠李戴）

纯函数·ASCII 标记（[OK]/[ERR]）·不调 LLM。
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / 'tools'))

from tools.rag_gold_set import GOLD_SET
from tools.rag_index import search


def _tag(ok, msg):
    print(f'[{"OK" if ok else "ERR"}] {msg}')


def evaluate(k=5):
    """跑黄金集·输出三类分项通过率。返回 dict（recall_rate/dim_pass/case_pass）。"""
    recall_hit = 0
    recall_total = 0
    dim_pass = True
    dim_total = 0
    case_pass = True
    case_total = 0

    for item in GOLD_SET:
        q = item['query']
        qk = item.get('k', k)
        r = search(q, qk)
        if not r['ok']:
            _tag(False, f'检索失败: {q}·{r.get("error", "")}')
            continue

        if item['type'] == 'recall':
            recall_total += 1
            hits = [res['source'] for res in r['results']]
            hit = any(kw in ' '.join(hits) for kw in item['expect_kw'])
            if hit:
                recall_hit += 1
                _tag(True, f'召回: "{q}" 命中')
            else:
                _tag(False, f'召回: "{q}" 未命中·Top={hits[:2]}')

        elif item['type'] == 'dimension':
            dim_total += 1
            # 检索结果带维度标注（data_dim）·且回答不得越维（此处检检索层维度标注存在）
            dims = [res.get('data_dim', '') for res in r['results']]
            expect = item['expect_dim']
            if expect not in dims:
                _tag(False, f'越维: "{q}" 期望维度 {expect} 未在 Top-{qk}·dims={dims[:3]}')
                dim_pass = False
            else:
                _tag(True, f'越维: "{q}" 命中维度 {expect}')

        elif item['type'] == 'case_data':
            case_total += 1
            hits = [res['source'] for res in r['results']]
            forbidden = [kw for kw in item['forbid_kw'] if kw in ' '.join(hits)]
            if forbidden:
                _tag(False, f'案例数据: "{q}" Top-{qk} 含他城数据 {forbidden}')
                case_pass = False
            else:
                _tag(True, f'案例数据: "{q}" 无他城数据')

    recall_rate = recall_hit / recall_total if recall_total else 0.0
    print()
    print(f'=== 黄金集结果 ===')
    print(f'  正确召回: {recall_hit}/{recall_total} = {recall_rate:.0%}（目标 ≥80%·软指标）')
    print(f'  越维降级: {"通过" if dim_pass else "失败"}（刚性 100%·{dim_total} 例）')
    print(f'  案例不引数据: {"通过" if case_pass else "失败"}（刚性 100%·{case_total} 例）')
    ok = recall_rate >= 0.8 and dim_pass and case_pass
    _tag(ok, '黄金集整体通过' if ok else '黄金集未通过·见上')
    return {'recall_rate': recall_rate, 'dim_pass': dim_pass, 'case_pass': case_pass}


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--k', type=int, default=5)
    args = ap.parse_args()
    evaluate(k=args.k)
