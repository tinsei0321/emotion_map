# -*- coding: utf-8 -*-
"""SHELL2(FIX) FIX-09/FIX-11：追问 chips 三态 + dsh 兜底追问测试。

跑法（Part B/C 需隔离栈：py frontend/serve.py 8090 --backend-port 8009）：
  py tests/browser/test_followup_chips.py

Part A（node·零依赖）：followup.js 纯逻辑——空/非数组/脏数据过滤/截 3/ask 互斥/优先级三档。
Part B（browser·mock 引擎）：tool.end 携 cues→「追问建议」条渲染（优先级压过静态兜底·
  标签=追问建议而非追问）→点击回填输入框·条仍在（不直发）。
Part C（browser·dsh 引擎·约 15-60s）：dsh 轮无 cues→静态兜底走 FIX-11 dsh 分支
  （知识类追问文案·不与情绪分析问法混调）。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
BASE = 'http://127.0.0.1:8090'
DUMP = HERE / 'followup_chips_dump.mjs'
OUT = HERE / 'out'


def part_a_node():
    """Part A：node 纯逻辑断言（空/脏数据/截 3/ask 互斥/优先级）。"""
    try:
        proc = subprocess.run(['node', str(DUMP)], capture_output=True, text=True,
                              encoding='utf-8', timeout=60, cwd=str(HERE))
    except FileNotFoundError:
        print('[A][SKIP] node 不可用')
        return True
    data = json.loads(proc.stdout)
    bad = [r for r in data['results'] if not r['ok']]
    for r in data['results']:
        print(('[A][OK] ' if r['ok'] else '[A][ERR] ') + r['msg'])
    print('[A] PASS' if not bad else f'[A] FAIL {len(bad)} 项')
    return not bad


def _stack_ready():
    import urllib.request
    try:
        urllib.request.urlopen(f'{BASE}/api/v1/health', timeout=3).read()
        return True
    except Exception:
        return False


def part_b_mock_cues(pg):
    """Part B：mock 引擎携 cues→追问建议条+回填不直发（优先级实证）。"""
    pg.goto(f'{BASE}/frontend/index.html?e2e=1&acp-mock=1', wait_until='domcontentloaded')
    pg.wait_for_timeout(9000)
    pg.evaluate('() => window.__emcTest.clearLog()')
    pg.evaluate("() => window.__emcTest.send('mock 追问测试')")
    pg.evaluate('async () => await window.__emcTest.waitAnswer(60000)')
    pg.wait_for_timeout(800)
    label = pg.evaluate("() => { const l = document.querySelector('#aiq-suggest .aiq-suggest-label'); return l ? l.textContent : '' }")
    n_chips = pg.evaluate("() => document.querySelectorAll('#aiq-suggest .aiq-suggest-chip').length")
    label_ok = label == '追问建议'   # 优先级实证：cues 压过静态兜底（静态标签=追问）
    chips_ok = n_chips >= 2
    first_text = pg.evaluate("() => { const c = document.querySelector('#aiq-suggest .aiq-suggest-chip'); return c ? c.textContent : '' }")
    pg.evaluate("() => { const c = document.querySelector('#aiq-suggest .aiq-suggest-chip'); if (c) c.click(); }")
    pg.wait_for_timeout(500)
    filled = pg.evaluate('() => window.__emcTest.inputValue()')
    fill_ok = filled == first_text and bool(first_text)
    still = pg.evaluate("() => { const s = document.getElementById('aiq-suggest'); return s ? !s.hidden : false }")
    pg.screenshot(path=os.path.join(str(OUT), 'fix09_mock_cues.png'), full_page=False)
    print('[B][OK] 追问建议条渲染（优先级压静态兜底）' if label_ok and chips_ok else f'[B][ERR] label={label!r} chips={n_chips}')
    print('[B][OK] 点击回填输入框' if fill_ok else f'[B][ERR] 回填失败（input={filled!r} chip={first_text!r}）')
    print('[B][OK] 回填未直发（条仍在）' if still else '[B][ERR] 条消失（疑似直发）')
    return label_ok and chips_ok and fill_ok and still


def part_c_dsh_static(pg):
    """Part C：dsh 轮静态兜底=FIX-11 dsh 分支（知识类追问·约 15-60s 真 dsh）。"""
    pg.goto(f'{BASE}/frontend/index.html?e2e=1&engine=dsh', wait_until='domcontentloaded')
    pg.wait_for_timeout(9000)
    pg.evaluate("() => window.__emcTest.send('什么是留改拆？')")
    answered = pg.evaluate('async () => await window.__emcTest.waitAnswer(150000)')
    pg.wait_for_timeout(800)
    label = pg.evaluate("() => { const l = document.querySelector('#aiq-suggest .aiq-suggest-label'); return l ? l.textContent : '' }")
    chips_text = pg.evaluate("() => [...document.querySelectorAll('#aiq-suggest .aiq-suggest-chip')].map((c) => c.textContent).join('|')")
    # FIX-11 dsh 分支特征文案（深问/求据·知识类）；静态情绪分析兜底=深读归因/区域对比（不应出现）
    dsh_branch = ('展开讲讲' in chips_text or '依据或出处' in chips_text)
    no_emotion = '深读' not in chips_text and '归因' not in chips_text
    pg.screenshot(path=os.path.join(str(OUT), 'fix11_dsh_static.png'), full_page=False)
    print('[C][OK] dsh 轮回答完成' if answered else '[C][ERR] waitAnswer 超时')
    print('[C][OK] FIX-11 dsh 分支追问（知识类文案）' if dsh_branch else f'[C][ERR] chips={chips_text[:80]!r}')
    print('[C][OK] 未混入情绪分析问法' if no_emotion else '[C][ERR] 混入情绪分析问法')
    return answered and dsh_branch and no_emotion


def main():
    os.makedirs(OUT, exist_ok=True)
    ok_a = part_a_node()
    if not _stack_ready():
        print('[B/C][SKIP] 隔离栈未起（8090）——起栈后复跑：py frontend/serve.py 8090 --backend-port 8009')
        print('FOLLOWUP_CHIPS:', 'PASS(A only)' if ok_a else 'FAIL')
        return 0 if ok_a else 1
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(viewport={'width': 1400, 'height': 900})
        ok_b = part_b_mock_cues(pg)
        ok_c = part_c_dsh_static(pg)
        b.close()
    ok = ok_a and ok_b and ok_c
    print('FOLLOWUP_CHIPS:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
