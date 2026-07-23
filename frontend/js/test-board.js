// ═══ test-board.js — 测试飞轮 v4（分型摘要·按钮状态机·slider·覆盖确认）═══
import { CASES, CATEGORIES } from './test-cases.js';

const t = window.__emcTest;
let _running = false, _stop = false;
const _results = {};
const _runMeta = {};
let _lastReport = null;
let _lastOpts = null;       // 上次配置（重新开始时预填）
let _toastTimer;

function _el(tag, cls, html) { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
const w = (ms) => new Promise((r) => setTimeout(r, ms));

// ── 行内摘要（极简但关键）：意图/工具类显 template+工具+参数+产物；其他回退 obs ──
function _summary(r) {
  if (!r) return '';
  const bits = [];
  if (r.template) bits.push(`tpl=${r.template}`);
  if (Array.isArray(r.tools) && r.tools.length) bits.push(`tools:${r.tools.join(',')}`);
  if (r.params) {
    const p = r.params;
    if (p.boundary) bits.push(`区=${p.boundary}`);
    else if (p.boundaries) bits.push(`区=${p.boundaries}`);
    if (p.cell != null) bits.push(`cell=${p.cell}m`);
    if (p.radius != null) bits.push(`r=${p.radius}m`);
  }
  if (r.newLayers) bits.push(`+${r.newLayers}层`);
  if (bits.length) return `<span class="tb-tool">${bits.join(' · ')}</span>`;
  if (r.obs) return String(r.obs).slice(0, 60);
  return r.stage ? `[${r.stage}]` : (r.pass ? '[OK]' : '');
}
function _toast(msg) {
  let el = document.getElementById('tb-toast');
  if (!el) { el = _el('div', 'tb-toast'); el.id = 'tb-toast'; document.body.appendChild(el); }
  el.textContent = msg; el.classList.add('tb-show');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => el.classList.remove('tb-show'), 2800);
}

// ── 浮动按钮（始终可重新配置）──
function _createFab() {
  const btn = _el('button', 'tb-fab', '[OK]'); btn.id = 'tb-fab'; btn.title = '测试飞轮（重新配置）';
  btn.addEventListener('click', () => { if (_running) return; _openSetupDialog(_lastOpts); });
  return btn;
}

// ── 设置弹窗（slider 默认 25 · 重新开始预填）──
function _openSetupDialog(prefill) {
  const overlay = _el('div', 'tb-overlay');
  const dialog = _el('div', 'tb-dialog');
  const lim = prefill?.limit ?? 25;
  let html = '<div class="tb-dialog-head">测试配置 <button class="tb-dialog-close">x</button></div>';
  const mode = prefill?.mode || 'no-llm';
  html += '<div class="tb-section"><div class="tb-section-label">模式</div>'
    + `<label><input type="radio" name="tb-mode" value="no-llm" ${mode==='no-llm'?'checked':''}> no-llm（0 DeepSeek）</label> `
    + `<label><input type="radio" name="tb-mode" value="llm" ${mode==='llm'?'checked':''}> llm（需 DeepSeek）</label> `
    + `<label><input type="radio" name="tb-mode" value="all" ${mode==='all'?'checked':''}> 全部</label></div>`;
  const selCats = new Set(prefill?.cats || []);
  html += '<div class="tb-section"><div class="tb-section-label">类别（多选）</div>';
  html += `<label><input type="checkbox" class="tb-cat" value="ALL" ${!prefill||!prefill.cats?.length?'checked':''}> 全选</label> `;
  for (const cat of CATEGORIES) html += `<label><input type="checkbox" class="tb-cat" value="${cat}" ${!selCats.size||selCats.has(cat)?'checked':''}> ${cat}</label> `;
  html += '</div>';
  html += `<div class="tb-section"><div class="tb-section-label">数量</div>`
    + `<div class="tb-slider-row"><input type="range" id="tb-limit" min="0" max="100" step="5" value="${lim}"><span id="tb-limit-val" class="tb-limit-val">${lim}</span><span class="tb-limit-hint">（0=全部）</span></div></div>`;
  html += `<div class="tb-section"><div class="tb-section-label">超时</div>`
    + `<label><input type="number" id="tb-timeout" value="${prefill?.timeout||0}" min="0" style="width:50px"> 分钟 (0=不限)</label></div>`;
  html += '<div class="tb-section"><button id="tb-dialog-start" class="tb-btn">开始测试</button></div>';
  dialog.innerHTML = html;
  overlay.appendChild(dialog);
  document.body.appendChild(overlay);
  const slider = dialog.querySelector('#tb-limit');
  const sval = dialog.querySelector('#tb-limit-val');
  slider.addEventListener('input', () => { sval.textContent = slider.value; });
  const allCb = dialog.querySelector('.tb-cat[value="ALL"]');
  allCb.addEventListener('change', () => dialog.querySelectorAll('.tb-cat:not([value="ALL"])').forEach(c => c.checked = allCb.checked));
  dialog.querySelector('.tb-dialog-close').addEventListener('click', () => overlay.remove());
  overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
  dialog.querySelector('#tb-dialog-start').addEventListener('click', () => {
    const mode = dialog.querySelector('input[name="tb-mode"]:checked')?.value || 'no-llm';
    const cats = [...dialog.querySelectorAll('.tb-cat:checked')].map(c => c.value).filter(v => v !== 'ALL');
    const allCats = !cats.length || dialog.querySelector('.tb-cat[value="ALL"]').checked;
    const limit = parseInt(slider.value) || 0;
    const timeout = parseInt(dialog.querySelector('#tb-timeout').value) || 0;
    overlay.remove();
    _startTests({ mode, cats: allCats ? [] : cats, limit, timeout });
  });
}

// ── 抽屉 ──
function _createDrawer() {
  const d = _el('div', 'tb-drawer'); d.hidden = true; d.id = 'tb-drawer';
  d.innerHTML = '<div class="tb-head"><span class="tb-title">测试飞轮</span><span id="tb-stats-text" class="tb-stats-inline">—</span><button class="tb-close">x</button></div>'
    + '<div class="tb-toolbar"><button id="tb-action" class="tb-btn tb-stop" hidden>停止</button><button id="tb-report" class="tb-btn tb-export" hidden>存报告</button></div>'
    + '<div class="tb-list" id="tb-list"></div>';
  document.body.appendChild(d);
  d.querySelector('.tb-close').addEventListener('click', () => d.hidden = true);
  d.querySelector('#tb-report').addEventListener('click', () => _saveReport('manual'));
  return d;
}

// 主按钮状态机：停止 ↔ 重新开始（连贯多场景）
function _setAction(state) {
  const btn = document.getElementById('tb-action'); if (!btn) return;
  if (state === 'stop') {
    btn.hidden = false; btn.textContent = '停止'; btn.className = 'tb-btn tb-stop';
    btn.onclick = () => { _stop = true; _toast('停止中…当前例跑完即停并自动存报告'); };
  } else if (state === 'restart') {
    btn.hidden = false; btn.textContent = '重新开始'; btn.className = 'tb-btn tb-restart';
    btn.onclick = () => { _openSetupDialog(_lastOpts); };
  } else {
    btn.hidden = true;
  }
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

function _startTests(opts) {
  let cases = CASES;
  if (opts.mode === 'no-llm') cases = cases.filter(c => c.type === 'no-llm');
  else if (opts.mode === 'llm') cases = cases.filter(c => c.type === 'llm');
  if (opts.cats?.length) cases = cases.filter(c => opts.cats.includes(c.category));
  if (opts.limit > 0) cases = cases.slice(0, opts.limit);
  Object.assign(_runMeta, { mode: opts.mode, cats: opts.cats || [], total: cases.length, startedAt: Date.now() });
  _lastOpts = opts;                                   // 记配置，重新开始预填
  for (const id of Object.keys(_results)) delete _results[id];
  _running = true; _stop = false;
  const fab = document.getElementById('tb-fab');
  fab.classList.add('tb-fab-running'); fab.textContent = '...';
  const drawer = document.getElementById('tb-drawer'); drawer.hidden = false;
  _setAction('stop');
  document.getElementById('tb-report').hidden = true;
  _populateList(cases);
  _toast(`开始：${cases.length} 例（${opts.mode}${opts.cats?.length?'/'+opts.cats.join(','):''}）`);
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
    result.durationSolo = Date.now() - soloStart;
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
  _setAction('restart');                              // 完成后 → 重新开始
  document.getElementById('tb-report').hidden = false;
  _saveReport(stopped ? 'stop' : 'done');
}

async function _rerunOne(c) {
  if (_running) {
    _stop = true;
    _toast(`已停止批量，准备重跑 ${c.id}…`);
    while (_running) await w(80);
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
  _toast(`${c.id} 重跑 ${result.pass ? '[OK]' : '[ERR]'} · ${_summary(result).replace(/<[^>]+>/g, '').slice(0, 40)}`);
  _setAction('restart');
  document.getElementById('tb-report').hidden = false;
}

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
  md += `| ID | 名称 | 类型 | 自动 | 用户 | template | 工具 | 参数/产物 | obs |\n|---|---|---|---|---|---|---|---|---|\n`;
  for (const id of ids) {
    const r = _results[id]; const c = CASES.find(x => x.id === id) || {};
    const auto = r.pass ? 'OK' : 'ERR';
    const user = r.userVote ? (r.userVote === 'ok' ? 'OK' : 'BAD') : '—';
    const tmpl = r.template || '—';
    const tools = Array.isArray(r.tools) && r.tools.length ? r.tools.join('+') : '—';
    const pp = [];
    if (r.params) { if (r.params.boundary) pp.push(`区=${r.params.boundary}`); if (r.params.boundaries) pp.push(`区=${r.params.boundaries}`); if (r.params.cell != null) pp.push(`cell=${r.params.cell}`); if (r.params.radius != null) pp.push(`r=${r.params.radius}`); }
    if (r.newLayers) pp.push(`+${r.newLayers}层`);
    const ppStr = pp.join(' ') || '—';
    const obs = (r.obs || '').replace(/\|/g, '/').slice(0, 60);
    md += `| ${id} | ${c.name || ''} | ${c.type || ''} | ${auto} | ${user} | ${tmpl} | ${tools} | ${ppStr} | ${obs} |\n`;
  }
  const fails = ids.filter(id => { const r = _results[id]; return r.userVote === 'bad' || (!r.userVote && !r.pass); });
  if (fails.length) {
    md += `\n## 待复查（${fails.length}）\n`;
    for (const id of fails) {
      const r = _results[id];
      const tt = Array.isArray(r.tools) && r.tools.length ? `tools=${r.tools.join('+')} ` : '';
      md += `- **${id}** [${r.stage || ''}] tpl=${r.template || '?'} ${tt}${(r.obs || '').slice(0, 70)}\n`;
    }
  }
  return md;
}

async function _saveReport(reason) {
  const ids = Object.keys(_results);
  if (!ids.length) { if (reason === 'manual') _toast('尚无结果可报告'); return; }
  const md = _buildMarkdown();
  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  const date = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  const type = (_runMeta.mode || 'run').replace(/[^a-zA-Z0-9_-]/g, '') || 'run';
  const body = { content: md, type, date, reason };
  // 手动存 + 本 session 已存过 → 询问是否覆盖（痛点5）
  if (reason === 'manual' && _lastReport) {
    const ov = confirm(`本次已存过报告：\n${_lastReport}\n\n确定覆盖该文件？（取消 = 另存新编号）`);
    if (ov) body.name = _lastReport.replace(/\.md$/, '');
  }
  try {
    const res = await fetch('/_test/report', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!res.ok) throw new Error('http ' + res.status);
    const j = await res.json();
    _lastReport = j.name;
    const pk = ids.filter(id => { const r = _results[id]; return !(r.userVote === 'bad' || (!r.userVote && !r.pass)); }).length;
    _toast(`报告已存 [OK]${pk}/${ids.length}: ${j.name}`);
    const stats = document.getElementById('tb-stats-text'); if (stats) stats.title = `最近报告: tests/reports/${j.name}`;
  } catch (e) {
    _toast('serve 落盘端点不可用 → 开新窗口（建议走 serve.py）');
    const win = window.open('', '_blank');
    if (win) { win.document.write(`<pre>${md.replace(/</g, '&lt;')}</pre>`); win.document.close(); }
  }
}

// ── 初始化 ──
document.body.appendChild(_createFab());
_createDrawer();
console.log('[test-board] v4 就绪（分型摘要·转译断言·状态机·slider·?test=1）');
