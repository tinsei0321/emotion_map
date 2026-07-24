"""一次性审计驱动：测试飞轮大规模实测（不改飞轮任何代码）。

用法：
  py tests/browser/flywheel_audit.py --batch B0     # no-llm 全量 45 例（0 DeepSeek）
  py tests/browser/flywheel_audit.py --batch B1     # llm 意图识别 100 例
  py tests/browser/flywheel_audit.py --batch B2     # llm 工具选择 100 例
  py tests/browser/flywheel_audit.py --batch B3     # llm 参数/成果/Smart/CPD/UI 25 例
  py tests/browser/flywheel_audit.py --batch all    # B0→B3 顺序全跑

采集（三路，绕开 test-board.js 模块闭包 _results 不可达的限制）：
  1. DOM 行态：.tb-row 的 class/stage/time/summary（runner 自动判定结果）
  2. window._testFetchLog（e2e-seam fetch 拦截，window 全局可读）：/chat phase 计数 +
     bodyKeys（验 template 信号断链：ChatRequest 无 diagnose 字段）+ /geo status
  3. tests/reports/ 落盘 diff（runner _saveReport 自动存）+ localStorage dump（template 遥测）
输出：tests/browser/out/audit-<batch>-<ts>.json（原始记录）+ stdout 聚合摘要。
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.emc_helpers import emc_session, open_emc   # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORTS = os.path.join(REPO, 'tests', 'reports')
OUT = os.path.join(REPO, 'tests', 'browser', 'out')
TEST_URL = 'http://localhost:8080/frontend/index.html?test=1'

BATCHES = {
    'B0': {'mode': 'no-llm', 'cats': [], 'timeout_min': 40},
    'B1': {'mode': 'llm', 'cats': ['意图识别'], 'timeout_min': 200},
    'B2': {'mode': 'llm', 'cats': ['工具选择'], 'timeout_min': 200},
    'B3': {'mode': 'llm', 'cats': ['参数正确性', '成果范式', 'Smart交流', 'CPD导游', 'UI渲染'], 'timeout_min': 120},
}

ROWS_JS = """() => [...document.querySelectorAll('.tb-row')].map(r => ({
  id: (r.querySelector('.tb-id')||{}).textContent || '',
  name: (r.querySelector('.tb-name')||{}).textContent || '',
  cat: (r.querySelector('.tb-cat')||{}).textContent || '',
  type: (r.querySelector('.tb-type')||{}).textContent || '',
  cls: r.className,
  stage: (r.querySelector('.tb-stage')||{}).textContent || '',
  time: (r.querySelector('.tb-time')||{}).textContent || '',
  summary: ((r.querySelector('.tb-summary')||{}).innerText || '').trim(),
}))"""

# 只留 /chat 与 /geo|/spatial 条目；bodyKeys 验 ChatRequest 结构（diagnose 字段存在性）
FETCH_JS = """() => (window._testFetchLog || [])
  .filter(e => /\\/(chat|geo|spatial)\\//.test(e.url))
  .map(e => ({
    url: e.url.split('?')[0].replace(/^.*\\/api\\/v1/, ''),
    status: e.status,
    phase: e.body && e.body.phase || null,
    bodyKeys: e.body ? Object.keys(e.body) : null,
    tpl: (e.body && e.body.diagnose && e.body.diagnose.template) || null,
  }))"""


def _configure_and_start(page, mode, cats):
    """DOM 驱动：FAB → 配置弹窗（模式/类别/slider=0 全部/超时=0）→ 开始。"""
    page.click('#tb-fab')
    page.wait_for_selector('#tb-dialog-start', timeout=10000)
    page.check(f'input[name="tb-mode"][value="{mode}"]')
    if cats:
        page.uncheck('.tb-cat[value="ALL"]')   # change 监听会联动清空其余
        for c in cats:
            page.check(f'.tb-cat[value="{c}"]')
    page.evaluate("() => { const s = document.getElementById('tb-limit'); s.value = '0'; s.dispatchEvent(new Event('input')); }")
    page.fill('#tb-timeout', '0')
    page.click('#tb-dialog-start')
    page.wait_for_function("() => document.getElementById('tb-action') && !document.getElementById('tb-action').hidden", timeout=15000)


def _wait_done(page, timeout_min, tag):
    """轮询主按钮状态机：'重新开始' = 跑完/停止。每 30s 打进度。"""
    deadline = time.time() + timeout_min * 60
    last_log = 0
    while time.time() < deadline:
        txt = page.evaluate("() => (document.getElementById('tb-action')||{}).textContent || ''")
        if txt.strip() == '重新开始':
            return True
        if time.time() - last_log > 30:
            stats = page.evaluate("() => (document.getElementById('tb-stats-text')||{}).textContent || ''")
            print(f'  [{tag}] {time.strftime("%H:%M:%S")} {stats}', flush=True)
            last_log = time.time()
        page.wait_for_timeout(3000)
    return False


def run_batch(batch):
    cfg = BATCHES[batch]
    os.makedirs(OUT, exist_ok=True)
    before_reports = set(os.listdir(REPORTS)) if os.path.isdir(REPORTS) else set()
    t0 = time.time()
    with emc_session(open=False) as page:
        open_emc(page, url=TEST_URL, wait_ms=2500)
        page.wait_for_selector('#tb-fab', timeout=45000)
        _configure_and_start(page, cfg['mode'], cfg['cats'])
        print(f'[{batch}] started mode={cfg["mode"]} cats={cfg["cats"] or "ALL"}', flush=True)
        finished = _wait_done(page, cfg['timeout_min'], batch)
        page.wait_for_timeout(5000)   # 等 _saveReport 落盘
        rows = page.evaluate(ROWS_JS)
        fetchlog = page.evaluate(FETCH_JS)
        local_storage = page.evaluate("() => Object.fromEntries(Object.entries(localStorage))")
    elapsed = time.time() - t0
    after_reports = set(os.listdir(REPORTS)) if os.path.isdir(REPORTS) else set()
    new_reports = sorted(after_reports - before_reports)

    passes = [r for r in rows if 'tb-pass' in r['cls']]
    fails = [r for r in rows if 'tb-fail' in r['cls']]
    pending = [r for r in rows if 'tb-pending' in r['cls'] or 'tb-running' in r['cls']]
    chat = [f for f in fetchlog if f['url'].endswith('/chat')]
    geo = [f for f in fetchlog if '/geo/' in f['url'] or '/spatial/' in f['url']]
    rec = {
        'batch': batch, 'cfg': cfg, 'finished': finished, 'elapsed_s': round(elapsed, 1),
        'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
        'rows': rows,
        'stats': {'total': len(rows), 'pass': len(passes), 'fail': len(fails), 'pending': len(pending)},
        'chat_phases': {}, 'chat_body_keys': None, 'chat_tpl_nonnull': 0,
        'geo_calls': geo, 'new_reports': new_reports, 'local_storage': local_storage,
    }
    for c in chat:
        ph = c['phase'] or '(none)'
        rec['chat_phases'][ph] = rec['chat_phases'].get(ph, 0) + 1
        if c['bodyKeys'] and rec['chat_body_keys'] is None:
            rec['chat_body_keys'] = c['bodyKeys']
        if c['tpl']:
            rec['chat_tpl_nonnull'] += 1

    out_path = os.path.join(OUT, f'audit-{batch}-{time.strftime("%H%M%S")}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)

    print(f'\n═══ [{batch}] done finished={finished} elapsed={elapsed/60:.1f}min ═══')
    print(f'  rows={len(rows)} pass={len(passes)} fail={len(fails)} pending={len(pending)}')
    by_cat = {}
    for r in rows:
        d = by_cat.setdefault(r['cat'], [0, 0])
        d[0 if 'tb-pass' in r['cls'] else 1] += 1
    for cat, (p, fl) in by_cat.items():
        print(f'    {cat}: [OK]{p} [ERR]{fl}')
    print(f'  chat_phases={rec["chat_phases"]} bodyKeys={rec["chat_body_keys"]} tpl_nonnull={rec["chat_tpl_nonnull"]}')
    geo_bad = [g for g in geo if g['status'] and g['status'] >= 400]
    print(f'  geo_calls={len(geo)} 4xx/5xx={len(geo_bad)} new_reports={new_reports}')
    print(f'  out: {out_path}', flush=True)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch', required=True, choices=list(BATCHES.keys()) + ['all'])
    args = ap.parse_args()
    batches = list(BATCHES.keys()) if args.batch == 'all' else [args.batch]
    for b in batches:
        try:
            run_batch(b)
        except Exception as e:
            print(f'[{b}] FATAL: {e}', flush=True)


if __name__ == '__main__':
    main()
