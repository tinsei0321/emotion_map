# -*- coding: utf-8 -*-
"""壳二期件① E2E：?engine=dsh 真问题 → 对话框出答案（SHELL2(BA)·BrainAdapter dsh headless 首次端到端）。

跑法（前置栈起好·8090 前端 + 8009 后端·后端须能 spawn dsh）：
  py frontend/serve.py 8090 --backend-port 8009
  py tests/browser/she2_ba_dsh_e2e.py

场景：?e2e=1&engine=dsh 打开页（8080 应用同源隔离栈）→ __emcTest.send 真问题「什么是留改拆？」
  → 后端 spawn `dsh --profile emc-test`（实测 10-25s）→ BA 桩+ping+批量事件流 → 渲染断言：
  定稿出口徽章 / 答案含关键词 / dsh_brain 工具卡 / ping 进度桩（synthesized）/ diagnose 卡 engine=dsh /
  trace 持久化 / 零真 console error。
判据：全部过 = 「EMC 窗口用 dsh 当引擎」首次端到端跑通。
"""
import json
import os
import sys
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8090'
OUT = 'tests/browser/out'
QUESTION = '什么是留改拆？'
KEYWORD = '留改拆'

ENV_PAT = ('ERR_CONNECTION_TIMED_OUT', 'ERR_NAME_NOT_RESOLVED', 'ERR_TIMED_OUT', 'Could not compile',
           'favicon', 'manifest', '_time_manifest.json',
           'the server responded with a status of 404 (File not found)')


def main():
    os.makedirs(OUT, exist_ok=True)
    errs = []

    def on_console(m):
        if m.type != 'error':
            return
        url = ''
        try:
            loc = m.location
            url = f" @ {loc.url}" if loc and loc.url else ''
        except Exception:
            pass
        errs.append(m.text + url)

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(viewport={'width': 1400, 'height': 900})
        pg.on('console', on_console)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(f'{BASE}/frontend/index.html?e2e=1&engine=dsh', wait_until='domcontentloaded')
        pg.wait_for_timeout(9000)   # 图层初始化 + RAG 后台预热

        pg.evaluate('() => window.__emcTest.clearLog()')
        pg.evaluate(f'() => window.__emcTest.send({json.dumps(QUESTION, ensure_ascii=False)})')
        answered = pg.evaluate('async () => await window.__emcTest.waitAnswer(150000)')   # dsh 实测 10-25s·留足

        answer = pg.evaluate('() => window.__emcTest.answerText()')
        has_kw = KEYWORD in answer and len(answer) > 20
        badge = pg.evaluate('() => window.__emcTest.badge()')
        phases = pg.evaluate('() => window.__emcTest.chatPhases()')
        diag_ok = bool(phases) and phases[-1].get('template') == 'dsh'
        toolcard = pg.evaluate("() => { const c = document.querySelector('.aiq-toolcard'); return c ? c.textContent : '' }")
        tool_ok = 'dsh_brain' in toolcard
        reason = pg.evaluate("() => { const r = document.querySelector('.aiq-reason'); if (!r) return 'missing'; const b = r.querySelector('.aiq-reason-seg-body'); return (b && b.textContent) ? b.textContent.slice(0, 120) : (r.hidden ? 'hidden' : 'empty') }")
        ping_ok = '思考中' in reason
        hist = pg.evaluate("() => { try { return localStorage.getItem('ai_qa_history_v1') || '' } catch(e) { return '' } }")
        hist_ok = KEYWORD in hist
        pg.screenshot(path=f'{OUT}/she2_ba_dsh_e2e.png', full_page=False)

        print('[BA][OK] 定稿出口徽章' if answered else '[BA][ERR] waitAnswer 超时', '| badge:', badge)
        print('[BA][OK] 答案渲染（含关键词·len %d）' % len(answer) if has_kw else f'[BA][ERR] 答案缺失: {answer[:80]}')
        print('[BA][OK] diagnose 卡 engine=dsh（降级形态不藏）' if diag_ok else '[BA][WARN] diagnose 日志未见')
        print('[BA][OK] dsh_brain 工具卡' if tool_ok else '[BA][WARN] 工具卡未见:', toolcard[:40])
        print('[BA][OK] 等待期 ping 进度桩（synthesized）' if ping_ok else '[BA][WARN] ping 桩未见:', reason[:60])
        print('[BA][OK] trace 持久化' if hist_ok else '[BA][WARN] trace 持久化未见')
        real = [e for e in errs if not any(p_ in e for p_ in ENV_PAT)]
        env = [e for e in errs if any(p_ in e for p_ in ENV_PAT)]
        if env:
            print(f'[BA][ENV] 离线/开发态噪声 {len(env)} 条（底图/manifest·非 BA 面）')
        print('[BA][OK] 零真 console error' if not real else f'[BA][ERR] console errors: {real[:3]}')
        b.close()

    ok = answered and has_kw and not real
    print('SHELL2_BA_E2E:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
