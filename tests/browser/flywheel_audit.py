"""一次性审计驱动：测试飞轮大规模实测（不改飞轮任何代码）。

用法：
  py tests/browser/flywheel_audit.py --batch B0     # no-llm 全量 45 例（0 DeepSeek）
  py tests/browser/flywheel_audit.py --batch B1     # llm 意图识别 100 例
  py tests/browser/flywheel_audit.py --batch B2     # llm 工具选择 100 例
  py tests/browser/flywheel_audit.py --batch B3     # llm 参数/成果/Smart/CPD/UI 26 例（含 RST-L06·08-08 对齐注释）
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

# F-4（CB-10 飞轮审查）：三档拆分——smoke（每次 commit）/ regression（每日或每 N commit）/ full（发版验收）。
# smoke 选 no-llm 全量 + llm 关键 10 例（成果范式/Smart/产物语义·省时）；regression 加意图/工具精选；full = B1-B3。
TIERS = {
    'smoke': ['B0', 'B3-smoke'],
    'regression': ['B0', 'B1', 'B2', 'B3'],
    'full': ['B0', 'B1', 'B2', 'B3'],
}
# B3-smoke：llm 子集（成果范式+Smart+产物语义·~10 例·每次 commit 可跑）
B3_SMOKE_CATS = ['成果范式', 'Smart交流', '产物语义']

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
    ap.add_argument('--batch', choices=list(BATCHES.keys()) + ['all'], help='指定 batch（B0-B3/all）')
    ap.add_argument('--tier', choices=['smoke', 'regression', 'full'], help='三档拆分（F-4）：smoke=每次commit / regression=每日 / full=发版验收')
    ap.add_argument('--collect', metavar='AUDIT_JSON', help='F-8：从 audit JSON 失败行生成 buglog 草稿（人工确认入库）')
    args = ap.parse_args()
    if args.collect:
        sys.exit(collect_buglog_drafts(args.collect))
    if args.tier:
        # tier → batches（含 B3-smoke 子集：成果范式+Smart+产物语义）
        batches = []
        for b in TIERS[args.tier]:
            if b == 'B3-smoke':
                run_batch_smoke()
                continue
            batches.append(b)
    elif args.batch:
        batches = list(BATCHES.keys()) if args.batch == 'all' else [args.batch]
    else:
        ap.error('须给 --batch 或 --tier')
    for b in batches:
        try:
            run_batch(b)
        except Exception as e:
            print(f'[{b}] FATAL: {e}', flush=True)


def collect_buglog_drafts(audit_json):
    """F-8（CB-10 飞轮审查）：从 audit JSON 失败行生成 buglog 草稿（人工确认入库）。

    草稿写到 tests/buglog/open/_drafts/（不直接入 open/·人工 review 后 move + 填根因）。
    复用 bug-collector skill 的 frontmatter 契约（ASCII type/severity/module·YAML）。
    """
    import datetime as _dt
    with open(audit_json, encoding='utf-8') as fh:
        d = json.load(fh)
    rows = d.get('rows', [])
    fails = [r for r in rows if 'tb-fail' in r['cls'] or 'tb-pending' in r['cls']]
    if not fails:
        print(f'[OK] 无失败行（audit 共 {len(rows)} 行）——无需生成草稿')
        return 0
    drafts_dir = os.path.join(REPO, 'tests', 'buglog', 'open', '_drafts')
    os.makedirs(drafts_dir, exist_ok=True)
    today = _dt.date.today().isoformat()
    made = 0
    for r in fails:
        fid = r.get('id') or 'UNKNOWN'
        name = r.get('name') or fid
        cat = r.get('cat') or '未知'
        summ = (r.get('summary') or '').strip()
        slug = fid.lower().replace('-', '-').replace(' ', '-') or 'bug'
        path = os.path.join(drafts_dir, f'DRAFT-{slug}.md')
        body = f"""---
id: DRAFT
title: '飞轮失败：{name}（{cat}）'
type: BUG
severity: MED
priority: P1
status: open
module: 飞轮
source: 飞轮采集
cb: CB-10
rootcause: ''
case_ref: '{fid}'
repro_count: 1
last_repro: {today}
---

# DRAFT · 飞轮失败：{name}

## 标准化用例（草稿·待人工补全）

**问句**：（待人工填写）

**数据前提**：（待人工填写）

**失败表现**：{summ}

---
*本文件为 {audit_json} 自动生成草稿（flywheel_audit --collect）·人工确认后移入 buglog open/ 并填根因。*
"""
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(body)
        made += 1
        print(f'  [草稿] {path}')
    print(f'[OK] 生成 {made} 条 buglog 草稿 → {drafts_dir}（人工 review 后移入 open/）')
    return 0


def run_batch_smoke():
    """B3-smoke：llm 子集（成果范式+Smart+产物语义）·每次 commit 可跑（~10 例）。"""
    cfg = {'mode': 'llm', 'cats': B3_SMOKE_CATS, 'timeout_min': 60}
    os.makedirs(OUT, exist_ok=True)
    before_reports = set(os.listdir(REPORTS)) if os.path.isdir(REPORTS) else set()
    t0 = time.time()
    with emc_session(open=False) as page:
        open_emc(page, url=TEST_URL, wait_ms=2500)
        page.wait_for_selector('#tb-fab', timeout=45000)
        _configure_and_start(page, cfg['mode'], cfg['cats'])
        print('[B3-smoke] started llm 子集（成果范式+Smart+产物语义）', flush=True)
        finished = _wait_done(page, cfg['timeout_min'], 'B3-smoke')
        page.wait_for_timeout(5000)
        rows = page.evaluate(ROWS_JS)
        fetchlog = page.evaluate(FETCH_JS)
        local_storage = page.evaluate("() => Object.fromEntries(Object.entries(localStorage))")
    elapsed = time.time() - t0
    after_reports = set(os.listdir(REPORTS)) if os.path.isdir(REPORTS) else set()
    new_reports = sorted(after_reports - before_reports)
    passes = [r for r in rows if 'tb-pass' in r['cls']]
    fails = [r for r in rows if 'tb-fail' in r['cls']]
    print(f'\n═══ [B3-smoke] done finished={finished} elapsed={elapsed/60:.1f}min ═══')
    print(f'  rows={len(rows)} pass={len(passes)} fail={len(fails)}')
    print(f'  new_reports={new_reports}')
    for f in fails:
        print(f'    [ERR] {f["id"]} | {f["name"][:40]} | {f["summary"][:80]}')
    return None


if __name__ == '__main__':
    main()
