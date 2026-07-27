"""L3→L2 沉淀命令：读 episodes.jsonl -> 聚簇 -> 打印 L2 编辑提议（人审，不自动写）。

用法：py -m ai_qa.consolidate

自成长闭环的"周期维护"环：自动写入只进 L3；本命令从 L3 挖掘重复模式/失败模式/高质范例，
**提议** ai_qa/wisdom.py 的编辑（diff 形式打印）。人确认后才手工落 wisdom.py（或让 Claude 代改）。
不自动改 L2 -- 人审是 L2 不腐烂的前提。
输出标记全 ASCII（Windows GBK 安全，遵 CLAUDE.md 编码规范）。
"""
from collections import Counter, defaultdict
import sys

# Windows GBK 兼容：episode final_excerpt 可能含 emoji（✅ 等），裸 print 会 UnicodeEncodeError。
# reconfigure stdout 为 utf-8（同 sim_performance_data.py:36 范式；docstring「全 ASCII」未覆盖用户答文 excerpt）。
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

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


def _def(e):
    """安全取 defense dict（CB-09 D024·取代旧 review）。"""
    return e.get('defense') or {}


def _is_fail(e):
    """CB-09 D024：fail = 防线降级（degraded=true·结论被 L3 替换）且 fixes 非空（真问题·非纯跳过）。
    向后兼容：旧 episode 无 defense 字段→返 False（旧 review 数据自然老化·不强报错）。"""
    d = _def(e)
    return bool(d) and bool(d.get('degraded')) and bool(d.get('fixes'))


def _is_clean(e):
    """高质量范例：无降级 + 无任何 fix（防线一无所修·LLM 结论干净）。"""
    d = _def(e)
    return bool(d) and not d.get('degraded') and not (d.get('fixes') or [])


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
        nclean = sum(1 for e in es if _is_clean(e))
        nfail = sum(1 for e in es if _is_fail(e))
        ndeg = sum(1 for e in es if _def(e).get('degraded'))
        fixed = Counter()   # CB-09 D024：fixes 规则计数（取代旧 verdicts fail/warn）
        for e in es:
            for f in (_def(e).get('fixes') or []):
                r = f.get('rule') if isinstance(f, dict) else None
                if r:
                    fixed[r] += 1
        cov = '[v] covered' if _covered(scale, dom) else '[x] WISDOM gap'
        print('  {}/{}: {} rows (clean {} / fail {} / degraded {}) {}'.format(scale, dom, n, nclean, nfail, ndeg, cov))
        if fixed:
            print('    oft-fixed rules: ' + ', '.join('{}({})'.format(k, v) for k, v in fixed.most_common(4)))

    print('\n>> proposals (human reviews, then edits ai_qa/wisdom.py; this cmd does NOT auto-write):')
    proposed = False
    for (scale, dom), es in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
        if scale == '?':
            continue
        n = len(es)
        nfail = sum(1 for e in es if _is_fail(e))
        if n >= 3 and nfail / n >= 0.34:
            bad = Counter()   # CB-09 D024：fail 集的 fixes 规则计数（取代旧 verdicts fail）
            for e in es:
                if not _is_fail(e):
                    continue
                for f in (_def(e).get('fixes') or []):
                    r = f.get('rule') if isinstance(f, dict) else None
                    if r:
                        bad[r] += 1
            top = bad.most_common(1)
            tag = ' (oft-fix {})'.format(top[0][0]) if top else ''
            print('  [!] [{}/{}] fail rate {}/{}{} -> strengthen dont (see failing Q below)'.format(scale, dom, nfail, n, tag))
            for e in es:
                if _is_fail(e):
                    print('      fail eg: ' + (e.get('question') or '')[:60])
                    break
            proposed = True
        exemplars = [e for e in es if _is_clean(e)]
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
