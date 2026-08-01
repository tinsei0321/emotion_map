"""P0 复现脚本：B002/B005/B003 实测（CB-10 Day1）。

数据前提：行政区面层 + 商业/居住/公园广场用地 + L2 情绪点层。
经 ?e2e=1 seam 注入（loadRange 面层 / loadCSV 点层）。
每问 dump：诊断 template / toolExec / geo 调用 / 图层产出 / 回答 / 耗时。
--case B005 单跑（干净隔离·避免跨问交错污染）。

运行（自管 serve.py）：
    py tests/browser/test_p0_repro.py [--case B002|B005|B003|all]
前置：.env DEEPSEEK_API_KEY；playwright 已装。
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session, open_emc, wait_answer_done  # noqa: E402

CASES = [
    ('B002', '剪裁出西陵区范围内的商业+居住+公园广场用地'),
    ('B005', '将西陵区+伍家岗区范围内商业用地筛选出来'),
    ('B003', '我上传了哪些数据？'),
    ('B006', '能帮我筛选出西陵区的情绪点吗'),
]

SHOW_ERRORS = True

POLY_RANGES = [
    'presets/行政区.geojson',
    'presets/用地_商业.geojson',
    'presets/用地_居住.geojson',
    'presets/用地_公园广场.geojson',
]


def dump_state(page, tag, consoles, page_errors):
    diag = page.evaluate("() => (window._testDiagnoseLog || []).slice()")
    tools = page.evaluate("() => (window._testToolExecLog || []).slice()")
    geos = page.evaluate(
        "() => (window._testFetchLog || []).filter(e => /\\/(geo|spatial)\\//.test(e.url))"
        ".map(e => ({ url: e.url.split('?')[0], status: e.status }))")
    names = page.evaluate("() => __emcTest.layerNames()")
    ans = page.evaluate("() => __emcTest.answerText()")
    print(f'--- [{tag}] ---')
    print(f'  diagnose: {json.dumps(diag, ensure_ascii=False)[:500]}')
    print(f'  tools: {json.dumps(tools, ensure_ascii=False)[:400]}')
    print(f'  geo: {json.dumps(geos, ensure_ascii=False)[:500]}')
    print(f'  layers({len(names)}): {names}')
    print(f'  answer: {ans[:400]}')
    interesting = [c for c in consoles if any(k in c for k in
        ('autoExpand', 'recover', 'plans', 'runAllToolCalls', 'FC', 'chain', 'toolHistory'))]
    for c in interesting[-12:]:
        print(f'  [console] {c[:300]}')
    if SHOW_ERRORS and page_errors:
        print('  [pageerror]')
        for e in page_errors[-8:]:
            print(f'    {e[:300]}')


def wait_new_answer(page, prev_count, timeout_ms=120000):
    """等 .aiq-answer 数量 > prev_count 且无光标（治 prev answer 恒真误判）。"""
    import time as _t
    deadline = _t.time() + timeout_ms / 1000
    while _t.time() < deadline:
        n = page.evaluate("() => document.querySelectorAll('.aiq-answer').length")
        cur = page.evaluate("() => !!document.querySelector('.chat-cursor')")
        if n > prev_count and not cur:
            return True
        page.wait_for_timeout(400)
    return False


def main() -> int:
    with emc_session(open=False) as page:
        consoles = []
        page_errors = []
        page.on('console', lambda m: consoles.append(m.text))
        page.on('pageerror', lambda e: page_errors.append(str(e)))
        req_t, resp_t = {}, {}
        page.on('request', lambda r: req_t.__setitem__(r.url, time.time()))
        page.on('response', lambda r: resp_t.__setitem__(r.url, time.time()))
        open_emc(page, url='http://localhost:8080/frontend/index.html?e2e=1', wait_ms=2500)
        page.wait_for_function("() => !!window.__emcTest", timeout=45000)
        for r in POLY_RANGES:
            res = page.evaluate("(name) => __emcTest.loadRange(name)", r)
            print(f'[inject] {r} -> {res}')
        res = page.evaluate("() => __emcTest.loadCSV('yichang_L2_T1_L2_result_csv.csv')")
        print(f'[inject] L2 points -> {res}')
        page.wait_for_timeout(2000)

        for tag, q in CASES:
            prev = page.evaluate("() => document.querySelectorAll('.aiq-answer').length")
            page.evaluate("(t) => __emcTest.send(t)", q)
            t0 = time.time()
            ok = wait_new_answer(page, prev, timeout_ms=120000)
            el = time.time() - t0
            print(f'[question] {tag}: "{q}" -> {el:.1f}s (done={ok})')
            dump_state(page, tag, consoles, page_errors)
            # overlay 请求→响应间隔（定位前端 vs 网络挂起）
            for u, tr in req_t.items():
                if '/geo/overlay' in u and u in resp_t:
                    print(f'  [net] overlay {round((resp_t[u]-tr)*1000)}ms req->resp')
            page.wait_for_timeout(1500)
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--case', default='all', choices=['B002', 'B005', 'B003', 'B006', 'all'])
    a = ap.parse_args()
    if a.case != 'all':
        CASES[:] = [c for c in CASES if c[0] == a.case]
    sys.exit(main())
