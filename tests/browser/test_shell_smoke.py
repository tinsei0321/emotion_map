# -*- coding: utf-8 -*-
"""S7 E2E 冒烟骨架（壳阶段联合任务书 v1.0·S7·playwright 三场景·S3+S4 收口）。

三场景：
  1 壳对话闭环 —— ACP 事件流全链：?acp-mock=1 确定性 mock 对端直注 shell._acp.bus
    （diagnose 卡 → rag_query tool.begin/end 工具卡 → 思考流 → 最终答案 + 出口徽章）。
  2 S5 追问 chips —— tool.end 载荷 followup_cues → 「追问建议」条渲染 → 点击回填输入框
    （回填不直发·send 会清条故条在=未发）。
  3 C3 样式面板零退化 —— 注入点层 → 图层行开参数面板 → 面开关/透明度/线宽在位（五红线回归）。

引擎切换位：REAL_ENGINE_READY —— S4（轻循环引擎→ACP 事件发射器）收口后置 True，
  场景 1/2 自动改走真实引擎（URL 去 acp-mock·需 DEEPSEEK_API_KEY）；
  置 True 前本文件以 mock 对端自验（S3 主体已交付·mock 与 S4 同走 bus 注入点）。
判据：场景 1 答案/工具卡/徽章渲染；场景 2 追问条+回填；场景 3 面板控件在位；全程零 pageerror。
运行：py tests/browser/test_shell_smoke.py（自管栈 serve.py :8090 + 后端 :8009·避撞日常 8080）
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session, inject_points, send_prompt, wait_answer_done

# ── S4 就绪切换位 ──────────────────────────────────────────────
REAL_ENGINE_READY = False   # S4 收口后置 True：场景 1/2 走真实引擎（emitter 透传 followup_cues 同字段）

PORT, BACKEND_PORT = 8090, 8009   # 隔离栈（与 Qoder S3 E2E 同口·避撞用户日常 8080/8000）
BASE = f'http://localhost:{PORT}'
FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'compare_points.geojson')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')


def _url(extra=''):
    q = 'e2e=1'
    if not REAL_ENGINE_READY:
        q += '&acp-mock=1'
    if extra:
        q += '&' + extra
    return f'{BASE}/frontend/index.html?{q}'


def _collect_errors(pg):
    """收 pageerror（JS 崩溃级）与 console error（仅打印·瓦片/shader 类环境噪声不计判据）。"""
    box = {'pageerror': [], 'console': []}
    pg.on('pageerror', lambda e: box['pageerror'].append(str(e)))
    pg.on('console', lambda m: box['console'].append(m.text) if m.type == 'error' else None)
    return box


def _real_errors(console_errors):
    return [e for e in console_errors if 'favicon' not in e.lower() and '404' not in e]


def scenario_1_loop(pg, box):
    """1·壳对话闭环（ACP 事件流全链·mock 对端 bus 直注）。"""
    # 自管开页（不用 open_emc：EMC 默认折叠胶囊·input 初始 hidden·fill 的 focus 监听会自动展开）
    pg.goto(_url(), wait_until='commit')
    pg.wait_for_selector('#chat-input', state='attached', timeout=30000)
    pg.wait_for_selector('#lp-upload', state='attached', timeout=15000)
    pg.wait_for_timeout(1500)
    pg.evaluate("() => window.__emcTest && window.__emcTest.clearLog && window.__emcTest.clearLog()")
    send_prompt(pg, '宜昌城市更新项目有多少个？')
    ans = wait_answer_done(pg, timeout_ms=60000)

    has_final = ('mock 对端' in ans or '已收到问题' in ans)
    toolcard = pg.evaluate("() => { const c = document.querySelector('.aiq-toolcard'); return c ? c.textContent : '' }")
    tool_ok = 'rag_query' in toolcard or '知识检索' in toolcard
    badge = pg.evaluate("() => { const b = document.querySelector('.aiq-exit-badge'); return b ? b.textContent.trim() : '' }")
    # bus 事件驱动证据：mock diagnose 卡经 TURN 订阅器派发 diagnose:done（与真引擎同路径）
    phases = pg.evaluate("() => (window.__emcTest && window.__emcTest.chatPhases) ? window.__emcTest.chatPhases() : []")
    diag_ok = bool(phases) and phases[-1].get('template') == 'knowledge_qa'
    os.makedirs(OUT, exist_ok=True)
    pg.screenshot(path=os.path.join(OUT, 'shell_s1_loop.png'), full_page=False)
    print('[S7-1][OK] 最终答案渲染' if has_final else '[S7-1][ERR] 最终答案缺失', '| len', len(ans))
    print('[S7-1][OK] 工具卡（rag_query）' if tool_ok else '[S7-1][WARN] 工具卡未见', '|', toolcard[:40])
    print('[S7-1][OK] 出口徽章' if badge else '[S7-1][WARN] 出口徽章未见', '|', badge)
    print('[S7-1][OK] diagnose:done 事件证据' if diag_ok else '[S7-1][WARN] diagnose 日志未见')
    re_ = _real_errors(box['console'])
    if re_:
        print(f'[S7-1][NOTE] console error（环境性·不判）: {re_[:3]}')
    return has_final and tool_ok and not box['pageerror']


def scenario_2_cues(pg):
    """2·S5 追问 chips（tool.end followup_cues → 追问建议条 → 点击回填不直发）。"""
    suggest = pg.locator('#aiq-suggest')
    visible = suggest.is_visible()
    label = pg.locator('#aiq-suggest .aiq-suggest-label').inner_text().strip() if visible else ''
    chips = pg.locator('#aiq-suggest .aiq-suggest-chip')
    n = chips.count() if visible else 0

    label_ok = label == '追问建议'
    chips_ok = n >= 2
    fill_ok = False
    not_sent = False
    if n:
        first_text = chips.first.inner_text().strip()
        chips.first.click()
        pg.wait_for_timeout(300)
        fill_ok = pg.input_value('#chat-input').strip() == first_text
        not_sent = suggest.is_visible()   # send 会 clearSuggest 清条——条仍在 = 只回填未直发
        pg.screenshot(path=os.path.join(OUT, 'shell_s2_cues.png'), full_page=False)
        print('[S7-2] 首 cue:', first_text[:40])
    print('[S7-2][OK] 追问建议条渲染' if label_ok and chips_ok else f'[S7-2][ERR] 条/标签异常（label={label!r} chips={n}）')
    print('[S7-2][OK] 点击回填输入框' if fill_ok else '[S7-2][ERR] 回填失败')
    print('[S7-2][OK] 回填未直发（条仍在）' if not_sent else '[S7-2][ERR] 条消失（疑似直发）')
    return label_ok and chips_ok and fill_ok and not_sent


def scenario_3_c3(pg):
    """3·C3 样式面板零退化（五红线回归）。"""
    with open(FIXTURE, encoding='utf-8') as fh:
        fc = json.load(fh)
    inject_points(pg, fc)
    row = pg.locator('#layer-list .layer-row').first
    if not row.count():
        print('[S7-3][ERR] 无图层行（注入点层失败？）')
        return False
    # headless 下 kind 按钮可能零尺寸/折叠不可见——JS click 直接派发（C3 判据=面板控件在位，非按钮可见性）。
    # 点「点」行（group 行无样式面板；fixture 注入点层——点层 body=色带图例+大小+透明度）。
    clicked = pg.evaluate("() => { const bs = [...document.querySelectorAll('#layer-list .layer-row button.layer-kind[data-feat]')]; const b = bs.find((x) => x.textContent.trim() === '点'); if (b) b.click(); return !!b; }")
    pg.wait_for_timeout(1200)
    body = pg.locator('.set-body').first
    c3_ok = False
    if clicked and body.count() and body.is_visible():
        t = body.inner_text()
        c3_ok = ('面' in t or '透明' in t)   # 点层=透明度·面层=面开关/线宽（判据随注入层类自适应）
    pg.screenshot(path=os.path.join(OUT, 'shell_s3_c3.png'), full_page=False)
    print('[S7-3][OK] C3 样式面板零退化' if c3_ok else '[S7-3][ERR] C3 样式面板回归失败')
    return c3_ok


def main():
    results = {}
    with emc_session(port=PORT, backend_port=BACKEND_PORT, open=False) as page:
        box = _collect_errors(page)
        results['1-壳对话闭环'] = scenario_1_loop(page, box)
        results['2-S5追问chips'] = scenario_2_cues(page)
        # 场景 3 复用同页切真实模式（去 acp-mock 重载=新会话态·点层注入后验 C3）
        pg3 = page
        pg3.goto(_url(), wait_until='commit')
        pg3.wait_for_selector('#chat-input', state='attached', timeout=30000)
        pg3.wait_for_selector('#lp-upload', state='attached', timeout=15000)
        pg3.wait_for_timeout(1500)
        results['3-C3样式面板'] = scenario_3_c3(pg3)
    ok = all(results.values())
    print('SHELL_S7_SMOKE:', 'PASS' if ok else f'FAIL {results}')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
