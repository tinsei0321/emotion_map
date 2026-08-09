"""验证 PRM-04 修复：周边 1 公里 → buffer·radius=1000·绝不 merge（Codex 补·对齐 test-cases.js expectRadius:1000）。

跑 3 次同一问句（Flash 方差）·断言：
- 工具链含 buffer 或合法 ask_user（center 缺诚实追问·对齐 verify_prm03_fix.py 判据）
- 绝不 merge（G5 多工具重写·083b78d 根治目标）
- 若实际执行 buffer（非 ask）→ 回答含「1000 米」（radius derive 落地·`1 公里`→1000·harness.js:1598-1601）

运行：py tests/browser/verify_prm04_fix.py（需 serve·自管）
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session, inject_points, send_prompt, wait_answer_done

_Q = '大南门·二马路滨江片区周边 1 公里范围内的情绪点分布'


def _run(page):
    page.evaluate("() => window.__emcTest.newChat()")
    page.wait_for_timeout(500)
    send_prompt(page, _Q)
    ans = wait_answer_done(page, timeout_ms=120000)
    diag = page.evaluate("() => window.__emcTest.chatPhases()")
    execs = page.evaluate("() => window.__emcTest.toolExecs()")
    tpl = [d.get('template') for d in diag if d.get('template')]
    tools = [e.get('tool') for e in execs if e.get('tool')]
    ask = '还缺「center」' in (ans or '') or '等你选择' in (ans or '')
    return {'tpl': tpl, 'tools': tools, 'ask': ask, 'ans': (ans or '')[:90]}


def main() -> int:
    sys.stdout.reconfigure(encoding='utf-8')
    bad = []
    with emc_session() as page:
        fx = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'compare_points.geojson')
        with open(fx, encoding='utf-8') as fh:
            inject_points(page, __import__('json').load(fh))
        for _b in ('社区.geojson', '行政区.geojson', '用地_商业.geojson'):
            page.evaluate("(n) => window.__emcTest.loadRange(n)", _b)
        page.wait_for_timeout(800)
        for i in range(3):
            r = _run(page)
            radius_ok = ('1000 米' in r['ans']) if (not r['ask'] and 'buffer' in (r['tpl'] or [])) else True
            print(f'  [run{i+1}] tpl={r["tpl"]} tools={r["tools"]} ask={r["ask"]} radius1000={radius_ok} 回答={r["ans"]!r}')
            if 'buffer' not in (r['tpl'] or []) and not r['ask']:
                bad.append(f'run{i+1}: 未走 buffer 也未 ask_user（tpl={r["tpl"]} tools={r["tools"]}）')
            if 'merge' in (r['tools'] or []):
                bad.append(f'run{i+1}: 错路由 merge（tools={r["tools"]}）')
            if not radius_ok:
                bad.append(f'run{i+1}: 执行 buffer 但回答未见 1000 米（ans={r["ans"]!r}）')
    if bad:
        print('[FAIL]', '; '.join(bad))
        return 1
    print('[OK] PASS — 周边 1 公里 3 次均走 buffer 或合法 ask_user·绝不 merge·radius=1000')
    return 0


if __name__ == '__main__':
    sys.exit(main())
