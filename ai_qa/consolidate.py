"""L3→L2 沉淀命令：读 episodes.jsonl -> 聚簇 -> 打印 L2 编辑提议（人审，不自动写）。

用法：py -m ai_qa.consolidate

自成长闭环的"周期维护"环：自动写入只进 L3；本命令从 L3 挖掘重复模式/失败模式/高质范例，
**提议** ai_qa/wisdom.py 的编辑（diff 形式打印）。人确认后才手工落 wisdom.py（或让 Claude 代改）。
不自动改 L2 -- 人审是 L2 不腐烂的前提。
输出标记全 ASCII（Windows GBK 安全，遵 CLAUDE.md 编码规范）。
"""
from collections import Counter, defaultdict

from ai_qa.episode import read_episodes, episode_path
from ai_qa.wisdom import WISDOM


def _key(ep):
    """ep -> (scale, domain) 聚簇 key（取 diagnose.domains 第一个或 '_'）。"""
    dg = ep.get('diagnose') or {}
    if dg.get('degraded'):
        return ('?', '?')
    scale = dg.get('scale') or '?'
    doms = dg.get('domains') or []
    dom = doms[0] if doms else '_'
    return (scale, dom)


def _covered(scale, dom):
    """该 (scale, dom) 是否已有 WISDOM 条目覆盖。"""
    for w in WISDOM:
        ws = w.get('scale')
        if ws not in ('*', scale) and ws != scale:
            continue
        wd = w.get('domains') or []
        if not wd or dom in wd:
            return True
    return False


def _rev(e):
    """安全取 review dict。"""
    return e.get('review') or {}


def _is_fail(e):
    r = _rev(e)
    return bool(r) and not r.get('pass') and not r.get('degraded')


def propose():
    eps = read_episodes()
    print('=== L3 episode dig report ({} rows @ {}) ===\n'.format(len(eps), episode_path()))
    if not eps:
        print('(no episode yet -- ask a few questions, then re-run. Capture is implicit: each Q&A auto-logs one.)')
        return

    clusters = defaultdict(list)
    for ep in eps:
        clusters[_key(ep)].append(ep)

    print('>> by scale x domain:')
    for (scale, dom), es in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
        n = len(es)
        npass = sum(1 for e in es if _rev(e).get('pass'))
        nfail = sum(1 for e in es if _is_fail(e))
        ndeg = sum(1 for e in es if _rev(e).get('degraded'))
        bad = Counter()
        for e in es:
            for k, v in (_rev(e).get('verdicts') or {}).items():
                if v in ('fail', 'warn'):
                    bad[k] += 1
        cov = '[v] covered' if _covered(scale, dom) else '[x] WISDOM gap'
        print('  {}/{}: {} rows (pass {} / fail {} / degraded {}) {}'.format(scale, dom, n, npass, nfail, ndeg, cov))
        if bad:
            print('    oft-fail/warn checklist: ' + ', '.join('{}({})'.format(k, v) for k, v in bad.most_common(4)))

    print('\n>> proposals (human reviews, then edits ai_qa/wisdom.py; this cmd does NOT auto-write):')
    proposed = False
    for (scale, dom), es in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
        if scale == '?':
            continue
        n = len(es)
        nfail = sum(1 for e in es if _is_fail(e))
        if n >= 3 and nfail / n >= 0.34:
            bad = Counter()
            for e in es:
                for k, v in (_rev(e).get('verdicts') or {}).items():
                    if v == 'fail':
                        bad[k] += 1
            top = bad.most_common(1)
            tag = ' (oft-fail {})'.format(top[0][0]) if top else ''
            print('  [!] [{}/{}] fail rate {}/{}{} -> strengthen dont (see failing Q below)'.format(scale, dom, nfail, n, tag))
            for e in es:
                if _is_fail(e):
                    print('      fail eg: ' + (e.get('question') or '')[:60])
                    break
            proposed = True
        exemplars = [e for e in es if _rev(e).get('pass')
                     and all(v == 'pass' for v in (_rev(e).get('verdicts') or {}).values())]
        if exemplars:
            e = exemplars[-1]
            print('  [*] [{}/{}] exemplar candidate (pass + all verdicts pass): '.format(scale, dom) + (e.get('question') or '')[:60])
            print('      final_excerpt: ' + (e.get('final_excerpt') or '')[:120])
            proposed = True
        if n >= 3 and not _covered(scale, dom):
            print('  [+] [{}/{}]: {} rows but no WISDOM entry -> add one (do/dont/exemplar TBD by human)'.format(scale, dom, n))
            proposed = True

    if not proposed:
        print('  (no notable proposal yet -- few episodes or balanced quality. Ask more, then re-run.)')
    print('\n>> no action taken: proposals only. Confirm, then hand-edit wisdom.py (or have Claude apply per proposal).')


if __name__ == '__main__':
    propose()
