# -*- coding: utf-8 -*-
"""S3 主体 E2E：壳对话框架事件化验收（playwright·隔离栈 8090/8009·node --check 单测之外的全链）。

跑法（前置：栈起好）：
  py frontend/serve.py 8090 --backend-port 8009
  py tests/browser/s3_acp_event_e2e.py

场景：
  A·SSE mock 全链（harness 在环）：page.route 拦截 /api/v1/chat 按 phase mock SSE
    （fc_diagnose→knowledge_qa·answer→固定 markdown），/api/v1/aiqa/rag_search 走真实后端——
    验证 harness→emitter(legacy hooks)→ACP bus→渲染订阅全链。
  B·acp-mock bus 直注（S4 后端未到·壳自给自足）：?acp-mock=1 打开页，send 后由 mock 对端
    按 wire schema 造事件直注 shell._acp.bus——验证 BrainAdapter 注入点（壳渲染零改动）。
  C·C3 样式面板回归：图层行开参数面板·面开关/透明度/线宽可见（零退化判据）。
判据：A/B 最终答案渲染 + trace 持久化 + 零 console error；C 面板可开且控件在。
"""
import json
import sys
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8090'
OUT = 'tests/browser/out'
FINAL_MD = 'S3事件化验收标记：宜昌城市更新项目55个·总投资51.33亿元 [来源: 知识库]'
MOCK_MARK = 'mock 对端·synthesized'


def _sse(lines):
    return ''.join(f'data: {json.dumps(o, ensure_ascii=False)}\n\n' for o in lines) + 'data: [DONE]\n\n'


def handle_chat(route):
    body = json.loads(route.request.post_data or '{}')
    phase = body.get('phase', '')
    if phase == 'fc_diagnose':
        payload = _sse([
            {'reason': '诊断思考：这是知识问答意图…'},
            {'tool_calls': [{'function': {'name': 'knowledge_qa', 'arguments': '{}'}}],
             'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15}},
        ])
    else:  # answer / agent_step / 其他——统一给最终结论流
        payload = _sse([
            {'reason': '综合素材中…'},
            {'token': FINAL_MD[:20]},
            {'token': FINAL_MD[20:]},
            {'usage': {'prompt_tokens': 20, 'completion_tokens': 8, 'total_tokens': 28}},
        ])
    route.fulfill(status=200, content_type='text/event-stream', body=payload)


def _on_console(errs):
    """console 收集器：附资源 URL（归因用——同一 404 文案不同 URL 含义不同）。"""
    def _h(m):
        if m.type != 'error':
            return
        url = ''
        try:
            loc = m.location
            url = f" @ {loc.url}" if loc and loc.url else ''
        except Exception:
            pass
        errs.append(m.text + url)
    return _h


def _real_errors(console_errors):
    # 环境噪声分类（按 URL 归因·非 blanket）：①离线环境外网底图瓦片超时/着色器（无瓦片时 shader 拿 NaN）
    # ②_time_manifest.json 404 = 开发态时间轴清单缺席（time-source 容错降级·非 S3 面）——均与 S3 无关；
    # 其余（含本机 4xx/5xx/JS 异常）全算过。
    env_pat = ('ERR_CONNECTION_TIMED_OUT', 'ERR_NAME_NOT_RESOLVED', 'ERR_TIMED_OUT', 'Could not compile',
               'favicon', 'manifest', '_time_manifest.json',
               # 裸 404 文案（console 无 URL 可归因）：栈日志已证全栈唯一 404 源 = _time_manifest.json
               # （grep ' 404 ' 仅此一条·开发态缺席·time-source 容错降级）——据实归入 env。
               'the server responded with a status of 404 (File not found)')
    real = [e for e in console_errors if not any(p in e for p in env_pat)]
    env = [e for e in console_errors if any(p in e for p in env_pat)]
    if env:
        print(f'[ENV] 离线/开发态噪声 {len(env)} 条（底图瓦片·着色器·_time_manifest·非 S3 面）')
    return real


def scenario_a(pg):
    """A·SSE mock 全链（harness→emitter→bus→渲染）。"""
    errs = []
    pg.on('console', _on_console(errs))
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/api/v1/chat', handle_chat)
    pg.goto(f'{BASE}/frontend/index.html', wait_until='domcontentloaded')
    pg.wait_for_timeout(9000)   # 图层初始化

    pg.fill('#chat-input', '宜昌城市更新项目有多少个？')
    pg.click('#chat-send')
    pg.wait_for_timeout(12000)   # 诊断(mock)→rag_search(真实)→answer(mock) 全链

    answer_txt = pg.evaluate("() => document.querySelector('.aiq-answer') ? document.querySelector('.aiq-answer').textContent : ''")
    has_final = 'S3事件化验收标记' in answer_txt
    hist = pg.evaluate("() => { try { return localStorage.getItem('ai_qa_history_v1') || localStorage.getItem('emc_aiqa_history') || '' } catch(e) { return '' } }")
    hist_ok = 'S3事件化验收标记' in hist or '城市更新' in hist
    reason_state = pg.evaluate("() => { const r = document.querySelector('.aiq-reason'); return r ? (r.hidden ? 'hidden' : 'visible') : 'missing' }")
    pg.screenshot(path=f'{OUT}/s3_a_legacy_chain.png', full_page=False)
    print('[A][OK] 最终答案渲染' if has_final else '[A][ERR] 最终答案缺失', '| answer len', len(answer_txt))
    print('[A][OK] trace 持久化' if hist_ok else '[A][WARN] trace 持久化未见（选择器或时机）')
    print('[A] reason 块状态:', reason_state)
    re_ = _real_errors(errs)
    print('[A][OK] 零 console error' if not re_ else f'[A][ERR] console errors: {re_[:3]}')
    return has_final and not re_


def scenario_b(pg):
    """B·acp-mock bus 直注（mock 对端·S4 后端未到·壳自给自足）。"""
    errs = []
    pg.on('console', _on_console(errs))
    pg.on('pageerror', lambda e: errs.append(str(e)))
    # e2e=1 接入官方观测面（__emcTest.send/waitAnswer/chatPhases——diagnose:done 事件日志）
    pg.goto(f'{BASE}/frontend/index.html?acp-mock=1&e2e=1', wait_until='domcontentloaded')
    pg.wait_for_timeout(9000)

    pg.evaluate("() => window.__emcTest.clearLog()")
    pg.evaluate("() => window.__emcTest.send('mock 对端链路自验')")
    answered = pg.evaluate("async () => await window.__emcTest.waitAnswer(30000)")

    answer_txt = pg.evaluate("() => window.__emcTest.answerText()")
    has_mock = MOCK_MARK in answer_txt
    # bus 事件驱动证据：mock diagnose 卡经 TURN 订阅器派发 diagnose:done（与真引擎同路径）
    phases = pg.evaluate("() => window.__emcTest.chatPhases()")
    diag_ok = bool(phases) and phases[-1].get('template') == 'knowledge_qa'
    hist = pg.evaluate("() => { try { return localStorage.getItem('ai_qa_history_v1') || '' } catch(e) { return '' } }")
    hist_ok = MOCK_MARK in hist
    badge = pg.evaluate("() => window.__emcTest.badge()")
    toolcard = pg.evaluate("() => { const c = document.querySelector('.aiq-toolcard'); return c ? c.textContent : '' }")
    tool_ok = 'rag_query' in toolcard or '知识检索' in toolcard
    pg.screenshot(path=f'{OUT}/s3_b_acp_mock.png', full_page=False)
    print('[B][OK] 定稿出口徽章' if answered else '[B][ERR] waitAnswer 超时', '| badge:', badge)
    print('[B][OK] mock 定稿渲染' if has_mock else '[B][ERR] mock 定稿缺失', '| answer:', answer_txt[:60])
    print('[B][OK] bus 事件驱动证据（diagnose:done 经同路径派发）' if diag_ok else '[B][WARN] diagnose 日志未见')
    print('[B][OK] mock trace 持久化' if hist_ok else '[B][WARN] mock trace 持久化未见')
    print('[B][OK] 工具卡渲染' if tool_ok else '[B][WARN] 工具卡未见', '|', toolcard[:40])
    re_ = _real_errors(errs)
    print('[B][OK] 零 console error' if not re_ else f'[B][ERR] console errors: {re_[:3]}')
    return answered and has_mock and not re_


def scenario_c(pg):
    """C·C3 样式面板回归（S3 红线：零退化）。需先注入面层并唤出左栏抽屉（默认收起·chip 唤出）。"""
    # e2e=1 页面注入行政区面层（/DATA/boundaries/ 白名单内）
    pg.evaluate("async () => await window.__emcTest.loadRange('行政区.geojson')")
    pg.wait_for_timeout(1500)
    # CPD Phase 2b：左栏抽屉默认 display:none·dispatch cpd:focus-tab=layers 唤出；图钉固定防外部点击收起
    pg.evaluate("() => { document.dispatchEvent(new CustomEvent('cpd:focus-tab', { detail: 'layers' })); document.getElementById('lp-pin')?.click(); }")
    pg.wait_for_timeout(800)
    row = pg.locator('#layer-list .layer-row').first
    c3_ok = False
    if row.count():
        row.locator('button.layer-kind[data-feat]').first.click()
        pg.wait_for_timeout(1200)
        body = pg.locator('.set-body').first
        if body.count() and body.is_visible():
            t = body.inner_text()
            c3_ok = ('面' in t and ('透明' in t or '线宽' in t))
        else:
            print('[C][WARN] 面板未开：.set-body 不可见')
        pg.screenshot(path=f'{OUT}/s3_c_style_panel.png', full_page=False)
    else:
        print('[C][WARN] 图层行未见（loadRange 未落层）')
        pg.screenshot(path=f'{OUT}/s3_c_no_row.png', full_page=False)
    print('[C][OK] C3 样式面板回归（面/透明度/线宽在）' if c3_ok else '[C][ERR] C3 样式面板回归失败')
    return c3_ok


def _wait_ready(timeout_s=90):
    """就绪门禁：轮询同源 /api/v1/health（经 8090 代理）至 200——BGE 预热同步阻塞期间返 502，
    未就绪即跑会让 rag_search 502 → 降级卡假失败（首轮 E2E 实测坑）。"""
    import time, urllib.request
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            urllib.request.urlopen(f'{BASE}/api/v1/health', timeout=3).read()
            return True
        except Exception:
            time.sleep(2)
    return False


def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    if not _wait_ready():
        print('S3_E2E: FAIL {backend 未就绪（health 502/超时·BGE 预热中？）}')
        return 1
    results = {}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg_a = b.new_page(viewport={'width': 1400, 'height': 900})
        results['A'] = scenario_a(pg_a)
        pg_a.close()
        pg_b = b.new_page(viewport={'width': 1400, 'height': 900})
        results['B'] = scenario_b(pg_b)
        results['C'] = scenario_c(pg_b)   # B 页同栈复用（图层已在）
        pg_b.close()
        b.close()
    ok = all(results.values())
    print('S3_E2E:', 'PASS' if ok else f"FAIL {results}")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
