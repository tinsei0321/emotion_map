"""验证 PRM-05/07 修复：小溪塔 → request_upload（不产层）·西陵区聚合 → zonal 执行。"""
import json as _json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session, inject_points, send_prompt, wait_answer_done

_QS = [
    ('PRM-07', '小溪塔范围内按面聚合情绪统计及 4×5 归因', lambda a: ('需上传' in a or '上传' in a or '不硬猜' in a or '标准' in a)),
    ('PRM-05', '西陵区范围内按面聚合情绪统计及 4×5 归因', lambda a: ('聚合' in a or 'zonal' in a or '完成' in a)),
]


def _run(page, q):
    page.evaluate("() => window.__emcTest.newChat()")
    page.wait_for_timeout(500)
    send_prompt(page, q)
    ans = wait_answer_done(page, timeout_ms=120000)
    return ans or ''


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
        for name, q, pred in _QS:
            ans = _run(page, q)
            ok = pred(ans)
            print(f'  [{name}] pred={ok} 回答={ans[:90]!r}')
            if not ok:
                bad.append(f'{name}: 断言失败（回答={ans[:120]!r}）')
    if bad:
        print('[FAIL]', '; '.join(bad))
        return 1
    print('[OK] PASS — PRM-07 小溪塔 request_upload·PRM-05 西陵区聚合执行')
    return 0


if __name__ == '__main__':
    sys.exit(main())
