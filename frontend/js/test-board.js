// ═══ test-board.js — 测试飞轮 v3（行内摘要·工具标注·重跑修复·固定位置报告·随时停）═══
import { CASES, CATEGORIES } from './test-cases.js';

const t = window.__emcTest;
let _running = false, _stop = false;
const _results = {};        // id → {pass, stage, obs, tools?, review?, durationSolo, userVote?, chatIdx?, rerun?}
const _runMeta = {};        // {mode, cats, total, startedAt}
let _lastReport = null;
let _toastTimer;

function _el(tag, cls, html) { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
const w = (ms) => new Promise((r) => setTimeout(r, ms));

// ── 工具名提取（从 fetch 拦截的真实端点 /geo /spatial 抓）──
function _toolLabel(url) {
  const m = String(url).split('?')[0].match(/(?:geo|spatial)\/([a-z_0-9]+)/i);
  return m ? m[1] : null;
}
// ── 行内摘要（一眼判通过·工具类直接标工具名·其他回退 obs）──
function _summary(r) {
  if (!r) return '';
  if (Array.isArray(r.tools) && r.tools.length) return `<span class="tb-tool">tool: ${r.tools.join(', ')}</span>`;
  if (r.obs) return String(r.obs).slice(0, 60);
  return r.stage ? `[${r.stage}]` : (r.pass ? '[OK]' : '');
}
// ── toast 反馈（让每次操作都有可见响应）──
function _toast(msg) {
  let el = document.getElementById('tb-toast');
  if (!el) { el = _el('div', 'tb-toast'); el.id = 'tb-toast'; document.body.appendChild(el); }
  el.textContent = msg; el.classList.add('tb-show');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => el.classList.remove('tb-show'), 2800);
}

// ── 浮动按钮 ──
function _createFab() {
  const btn = _el('button', 'tb-fab', '[OK]'); btn.id = 'tb-fab'; btn.title = '测试飞轮';
  btn.addEventListener('click', () => { if (_running) return; _openSetupDialog(); });
  return btn;
}

// ── 设置弹窗（选类别/模式/数量/时间）──
function _openSetupDialog() {
  const overlay = _el('div', 'tb-overlay');
  const dialog = _el('div', 'tb-dialog');
  let html = '<div class="tb-dialog-head">测试配置 <button class="tb-dialog-close">x</button></div>';
  html += '<div class="tb-section"><div class="tb-section-label">模式</div>'
    + '<label><input type="radio" name="tb-mode" value="no-llm" checked> no-llm（0 DeepSeek）</label> '
    + '<label><input type="radio" name="tb-mode" value="llm"> llm（需 DeepSeek）</label> '
    + '<label><input type="radio" name="tb-mode" value="all"> 全部</label></div>';
  html += '<div class="tb-section"><div class="tb-section-label">类别（多选）</div>';
  html += '<label><input type="checkbox" class="tb-cat" value="ALL" checked> 全选</label> ';
  for (const cat of CATEGORIES) html += `<label><input type="checkbox" class="tb-cat" value="${cat}" checked> ${cat}</label> `;
  html += '</div>';
  html += '<div class="tb-section"><div class="tb-section-label">限制</div>'
    + '<label>数量 <input type="number" id="tb-limit" value="0" min="0" style="width:50px"> (0=全部)</label> '
    + '<label>超时 <input type="number" id="tb-timeout" value="0" min="0" style="width:50px"> 分钟 (0=不限)</label></div>';
  html += '<div class="tb-section"><button id="tb-dialog-start" class="tb-btn">开始测试</button></div>';
  dialog.innerHTML = html;
  overlay.appendChild(dialog);
  document.body.appendChild(overlay);
  const allCb = dialog.querySelector('.tb-cat[value="ALL"]');
  allCb.addEventListener('change', () => dialog.querySelectorAll('.tb-cat:not([value="ALL"])').forEach(c => c.checked = allCb.checked));
  dialog.querySelector('.tb-dialog-close').addEventListener('click', () => overlay.remove());
  overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
  dialog.querySelector('#tb-dialog-start').addEventListener('click', () => {
    const mode = dialog.querySelector('input[name="tb-mode"]:checked')?.value || 'no-llm';
    const cats = [...dialog.querySelectorAll('.tb-cat:checked')].map(c => c.value).filter(v => v !== 'ALL');
    const allCats = !cats.length || dialog.querySelector('.tb-cat[value="ALL"]').checked;
    const limit = parseInt(dialog.querySelector('#tb-limit').value) || 0;
    const timeout = parseInt(dialog.querySelector('#tb-timeout').value) || 0;
    overlay.remove();
    _startTests({ mode, cats: allCats ? [] : cats, limit, timeout });
  });
}

// ── 抽屉 ──
function _createDrawer() {
  const d = _el('div', 'tb-drawer'); d.hidden = true; d.id = 'tb-drawer';
  d.innerHTML = '<div class="tb-head"><span class="tb-title">测试飞轮</span><span id="tb-stats-text" class="tb-stats-inline">—</span><button class="tb-close">x</button></div>'
    + '<div class="tb-toolbar"><button id="tb-stop" class="tb-btn tb-stop" hidden>停止</button><button id="tb-report" class="tb-btn tb-export" hidden>存报告</button></div>'
    + '<div class="tb-list" id="tb-list"></div>';
  document.body.appendChild(d);
  d.querySelector('.tb-close').addEventListener('click', () => d.hidden = true);
  d.querySelector('#tb-stop').addEventListener('click', () => { _stop = true; _toast('停止中…当前例跑完即停并自动存报告'); });
  d.querySelector('#tb-report').addEventListener('click', () => _saveReport('manual'));
  return d;
}

function _populateList(cases) {
  const list = document.getElementById('tb-list'); if (!list) return;
  list.innerHTML = '';
  for (const c of cases) {
    const row = _el('div', 'tb-row tb-pending');
    row.id = `tb-row-${c.id}`;
    row.innerHTML = `<span class="tb-dot"></span><span class="tb-id">${c.id}</span><span class="tb-name">${c.name}</span><span class="tb-cat">${c.category}</span><span class="tb-type">${c.type}</span><span class="tb-stage"></span><span class="tb-time"></span><button class="tb-vote-btn tb-vote-ok" data-id="${c.id}" data-vote="ok" title="通过">V</button><button class="tb-vote-btn tb-vote-bad" data-id="${c.id}" data-vote="bad" title="不通过">X</button><button class="tb-rerun" title="重跑该例">[R]</button><span class="tb-summary"></span>`;
    row.addEventListener('click', (e) => { if (!e.target.classList.contains('tb-rerun') && !e.target.classList.contains('tb-vote-btn')) _jumpToAnswer(c.id); });
    row.querySelector('.tb-rerun').addEventListener('click', (e) => { e.stopPropagation(); _rerunOne(c); });
    row.querySelectorAll('.tb-vote-btn').forEach((b) => b.addEventListener('click', (e) => {
      e.stopPropagation();
      const vid = e.target.dataset.id; const vt = e.target.dataset.vote;
      if (!_results[vid]) _results[vid] = {};
      _results[vid].userVote = vt;
      const r = document.getElementById(`tb-row-${vid}`);
      r.querySelectorAll('.tb-vote-btn').forEach((x) => x.classList.remove('active'));
      e.target.classList.add('active');
      r.className = `tb-row tb-${vt === 'ok' ? 'pass' : 'fail'}`;
    }));
    list.appendChild(row);
  }
}

// ── 开始测试 ──
function _startTests(opts) {
  let cases = CASES;
  if (opts.mode === 'no-llm') cases = cases.filter(c => c.type === 'no-llm');
  else if (opts.mode === 'llm') cases = cases.filter(c => c.type === 'llm');
  if (opts.cats?.length) cases = cases.filter(c => opts.cats.includes(c.category));
  if (opts.limit > 0) cases = cases.slice(0, opts.limit);
  Object.assign(_runMeta, { mode: opts.mode, cats: opts.cats || [], total: cases.length, startedAt: Date.now() });
  for (const id of Object.keys(_results)) delete _results[id];   // 新轮清旧结果
  _running = true; _stop = false;
  const fab = document.getElementById('tb-fab');
  fab.classList.add('tb-fab-running'); fab.textContent = '...';
  const drawer = document.getElementById('tb-drawer'); drawer.hidden = false;
  document.getElementById('tb-stop').hidden = false;
  document.getElementById('tb-report').hidden = true;
  _populateList(cases);
  _runCases(cases, opts.timeout);
}

async function _runCases(cases, timeoutMin) {
  const startMs = Date.now();
  let p = 0, f = 0;
  for (let i = 0; i < cases.length; i++) {
    if (_stop) break;
    if (timeoutMin && (Date.now() - startMs) / 60000 >= timeoutMin) break;
    const c = cases[i];
    _setRow(c.id, 'running');
    _updateStats(i, cases.length, p, f);
    if (c.type === 'llm') document.getElementById('chat-input')?.focus();
    await w(300);
    const soloStart = Date.now();
    let result;
    try { result = await c.run(t); } catch (e) { result = { pass: false, stage: 'error', obs: (e?.message) || String(e) }; }
    result.durationSolo = Date.now() - soloStart;   // 本例真实耗时（v2 误用累积值已修）
    result.chatIdx = document.querySelectorAll('.chat-msg-assistant').length - 1;
    _results[c.id] = result;
    if (result.pass) p++; else f++;
    _setRow(c.id, result.pass ? 'pass' : 'fail', result);
    _updateStats(i + 1, cases.length, p, f);
    if (i < cases.length - 1 && !_stop) await w(500);
  }
  const stopped = _stop;
  _running = false; _stop = false;
  const fab = document.getElementById('tb-fab');
  fab.classList.remove('tb-fab-running'); fab.textContent = '[OK]';
  document.getElementById('tb-stop').hidden = true;
  document.getElementById('tb-report').hidden = false;
  // 停止/完成 都自动存报告到固定位置（用户痛点1：随时停下随时报告）
  _saveReport(stopped ? 'stop' : 'done');
}

// ── 重跑单例（修复：批量中点 R 不再静默——先停批量再重跑，永远有响应）──
async function _rerunOne(c) {
  if (_running) {
    _stop = true;
    _toast(`已停止批量，准备重跑 ${c.id}…`);
    while (_running) await w(80);   // 等当前例跑完、批量退出（避免 chat 并发冲突）
  }
  _setRow(c.id, 'running');
  if (c.type === 'llm') { document.getElementById('chat-input')?.focus(); await w(300); t.newChat(); await w(300); }
  const soloStart = Date.now();
  let result;
  try { result = await c.run(t); } catch (e) { result = { pass: false, stage: 'error', obs: (e?.message) || String(e) }; }
  result.durationSolo = Date.now() - soloStart;
  result.chatIdx = document.querySelectorAll('.chat-msg-assistant').length - 1;
  result.rerun = true;
  _results[c.id] = result;
  _setRow(c.id, result.pass ? 'pass' : 'fail', result);
  _toast(`${c.id} 重跑 ${result.pass ? '[OK]' : '[ERR]'} · ${result.tools?.length ? 'tool=' + result.tools.join(',') : (result.obs || '').slice(0, 40)}`);
  document.getElementById('tb-report').hidden = false;
}

// ── 行状态更新 + 行内摘要（取代 v2 永不可见的 .tb-extra）──
function _setRow(id, status, result) {
  const row = document.getElementById(`tb-row-${id}`); if (!row) return;
  row.className = `tb-row tb-${status}`;
  const sum = row.querySelector('.tb-summary');
  if (result) {
    row.querySelector('.tb-stage').textContent = result.stage ? `[${result.stage}]` : (status === 'pass' ? '[OK]' : '[ERR]');
    row.querySelector('.tb-time').textContent = result.durationSolo ? `${(result.durationSolo / 1000).toFixed(1)}s` : '';
    let html = _summary(result);
    if (result.review) html += ` <span class="tb-review-inline">▸ ${result.review}</span>`;
    if (result.rerun) html = `<span class="tb-rerun-tag">↻</span> ${html}`;
    if (sum) sum.innerHTML = html;
  } else if (sum) {
    sum.innerHTML = status === 'running' ? '<span class="tb-run">运行中…</span>' : '';
  }
}

function _updateStats(done, total, p, f) {
  const el = document.getElementById('tb-stats-text'); if (!el) return;
  el.textContent = `${done}/${total} | [OK]${p} [ERR]${f}`;
}

// ── 点击行→EMC 跳转 ──
function _jumpToAnswer(id) {
  const r = _results[id]; if (!r || r.chatIdx == null) { _toast(`${id}: 暂无答案可跳转`); return; }
  const msgs = document.querySelectorAll('.chat-msg-assistant');
  const target = msgs[r.chatIdx]; if (!target) { _toast(`${id}: 答案节点已失效（重跑可刷新）`); return; }
  const input = document.getElementById('chat-input'); if (input) input.focus();
  setTimeout(() => {
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    target.classList.add('tb-highlight');
    setTimeout(() => target.classList.remove('tb-highlight'), 2000);
  }, 300);
}

// ── 构建报告 markdown（含工具列 + 待复查清单）──
function _buildMarkdown() {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  const ts = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
  const ids = Object.keys(_results);
  let p = 0, f = 0, uo = 0, ub = 0;
  for (const id of ids) {
    const r = _results[id];
    if (r.userVote === 'bad' || (!r.userVote && !r.pass)) f++; else p++;
    if (r.userVote === 'ok') uo++; else if (r.userVote === 'bad') ub++;
  }
  const cats = _runMeta.cats?.length ? _runMeta.cats.join(', ') : '全选';
  let md = `# EMC 测试报告 · ${ts}\n\n`;
  md += `- 模式: **${_runMeta.mode || 'all'}** ｜ 类别: ${cats} ｜ 用例: ${ids.length}\n`;
  md += `- 判定: [OK]${p} [ERR]${f} ｜ 用户 OK ${uo} / BAD ${ub} / 未评 ${ids.length - uo - ub}\n\n`;
  md += `| ID | 名称 | 类型 | 自动 | 用户 | 工具 | 阶段 | 耗时 | obs |\n|---|---|---|---|---|---|---|---|---|\n`;
  for (const id of ids) {
    const r = _results[id]; const c = CASES.find(x => x.id === id) || {};
    const auto = r.pass ? 'OK' : 'ERR';
    const user = r.userVote ? (r.userVote === 'ok' ? 'OK' : 'BAD') : '—';
    const tools = Array.isArray(r.tools) && r.tools.length ? r.tools.join('+') : '—';
    const dur = r.durationSolo ? `${(r.durationSolo / 1000).toFixed(1)}s` : '—';
    const obs = (r.obs || '').replace(/\|/g, '/').slice(0, 80);
    md += `| ${id} | ${c.name || ''} | ${c.type || ''} | ${auto} | ${user} | ${tools} | ${r.stage || ''} | ${dur} | ${obs} |\n`;
  }
  const fails = ids.filter(id => { const r = _results[id]; return r.userVote === 'bad' || (!r.userVote && !r.pass); });
  if (fails.length) {
    md += `\n## 待复查（${fails.length}）\n`;
    for (const id of fails) {
      const r = _results[id];
      const tt = Array.isArray(r.tools) && r.tools.length ? `tool=${r.tools.join('+')} ` : '';
      md += `- **${id}** [${r.stage || ''}] ${tt}${(r.obs || '').slice(0, 80)}\n`;
    }
  }
  return md;
}

// ── 存报告到固定位置 tests/reports/（痛点1·日期+编号+类型）──
async function _saveReport(reason) {
  const ids = Object.keys(_results);
  if (!ids.length) { if (reason === 'manual') _toast('尚无结果可报告'); return; }
  const md = _buildMarkdown();
  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  const date = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  const type = (_runMeta.mode || 'run').replace(/[^a-zA-Z0-9_-]/g, '') || 'run';
  try {
    const res = await fetch('/_test/report', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: md, type, date, reason }) });
    if (!res.ok) throw new Error('http ' + res.status);
    const j = await res.json();
    _lastReport = j.name;
    const p = ids.filter(id => { const r = _results[id]; return !(r.userVote === 'bad' || (!r.userVote && !r.pass)); }).length;
    _toast(`报告已存 [OK]${p}/${ids.length}: ${j.name}`);
    const stats = document.getElementById('tb-stats-text'); if (stats) stats.title = `最近报告: tests/reports/${j.name}`;
  } catch (e) {
    // serve 端点不可用（旧版 serve / file://）→ 退回新窗口
    _toast('serve 落盘端点不可用 → 开新窗口（建议走 serve.py）');
    const win = window.open('', '_blank');
    if (win) { win.document.write(`<pre>${md.replace(/</g, '&lt;')}</pre>`); win.document.close(); }
  }
}

// ── 初始化 ──
document.body.appendChild(_createFab());
_createDrawer();
console.log('[test-board] v3 就绪（行内摘要·工具标注·重跑修复·固定位置报告·?test=1）');
