"""验证 PRM-03/04 修复：周边 Nm 情绪 → 不再错路由 merge/lookup_place·走 buffer（或合法 ask_user）。

跑 3 次同一问句（Flash 方差）·断言每次工具链含 buffer 或合法 ask_user·绝不 merge。
"""
import json as _json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session, inject_points, send_prompt, wait_answer_done

_Q = '大南门·二马路滨江片区周边 300 米范围内的情绪点分布'


def _run(page):
    page.evaluate("() => window.__emcTest.newChat()")
    page.wait_for_timeout(500)
    send_prompt(page, _Q)
    ans = wait_answer_done(page, timeout_ms=120000)
    diag = page.evaluate("() => window.__emcTest.chatPhases()")
    execs = page.evaluate("() => window.__emcTest.toolExecs()")
    tpl = [d.get('template') for d in diag if d.get('template')]
    tools = [e.get('tool') for e in execs if e.get('tool')]
    # 检查回答是否 ask_user（center 缺）
    ask = '还缺「center」' in (ans or '') or '等你选择' in (ans or '')
    return {'tpl': tpl, 'tools': tools, 'ask': ask, 'ans': (ans or '')[:60]}


def main() -> int:
    sys.stdout.reconfigure(encoding='utf-8')
    bad = []
    with emc_session() as page:
        fx = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'compare_points.geojson')
        with open(fx, encoding='utf-8') as fh:
            inject_points(page, _json.load(fh))
        for _b in ('社区.geojson', '行政区.geojson', '用地_商业.geojson'):
            page.evaluate("(n) => window.__emcTest.loadRange(n)", _b)
        page.wait_for_timeout(800)
        for i in range(3):
            r = _run(page)
            print(f'  [run{i+1}] tpl={r["tpl"]} tools={r["tools"]} ask={r["ask"]}')
            if 'buffer' not in (r['tpl'] or []) and not r['ask']:
                bad.append(f'run{i+1}: 未走 buffer 也未 ask_user（tpl={r["tpl"]} tools={r["tools"]}）')
            if 'merge' in (r['tools'] or []):
                bad.append(f'run{i+1}: 错路由 merge（tools={r["tools"]}）')
    if bad:
        print('[FAIL]', '; '.join(bad))
        return 1
    print('[OK] PASS — 周边 Nm 情绪 3 次均走 buffer 或合法 ask_user·绝不 merge')
    return 0


if __name__ == '__main__':
    sys.exit(main())
