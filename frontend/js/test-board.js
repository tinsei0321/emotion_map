// ═══ test-board.js — 测试飞轮 v2（弹窗选类型 + 重跑 + 跳转 + 👍/👎 + 按钮状态 + LLM 自动展开）═══
import { CASES, CATEGORIES } from './test-cases.js';

const t = window.__emcTest;
let _running = false, _stop = false;
const _results = {};   // id → {pass, stage, obs, review?, duration, userVote?, chatIdx?}

function _el(tag, cls, html) { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
const w = (ms) => new Promise((r) => setTimeout(r, ms));

// ── 浮动按钮（v2：状态化）──
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
  // 模式
  html += '<div class="tb-section"><div class="tb-section-label">模式</div>'
    + '<label><input type="radio" name="tb-mode" value="no-llm" checked> no-llm（0 DeepSeek）</label> '
    + '<label><input type="radio" name="tb-mode" value="llm"> llm（需 DeepSeek）</label> '
    + '<label><input type="radio" name="tb-mode" value="all"> 全部</label></div>';
  // 类别
  html += '<div class="tb-section"><div class="tb-section-label">类别（多选）</div>';
  html += '<label><input type="checkbox" class="tb-cat" value="ALL" checked> 全选</label> ';
  for (const cat of CATEGORIES) html += `<label><input type="checkbox" class="tb-cat" value="${cat}" checked> ${cat}</label> `;
  html += '</div>';
  // 数量/时间
  html += '<div class="tb-section"><div class="tb-section-label">限制</div>'
    + '<label>数量 <input type="number" id="tb-limit" value="0" min="0" style="width:50px"> (0=全部)</label> '
    + '<label>超时 <input type="number" id="tb-timeout" value="0" min="0" style="width:50px"> 分钟 (0=不限)</label></div>';
  // 按钮
  html += '<div class="tb-section"><button id="tb-dialog-start" class="tb-btn">开始测试</button></div>';
  dialog.innerHTML = html;
  overlay.appendChild(dialog);
  document.body.appendChild(overlay);
  // 全选联动
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
    + '<div class="tb-toolbar"><button id="tb-stop" class="tb-btn tb-stop" hidden>停止</button><button id="tb-export" class="tb-btn tb-export" hidden>导出报告</button></div>'
    + '<div class="tb-list" id="tb-list"></div>';
  document.body.appendChild(d);
  d.querySelector('.tb-close').addEventListener('click', () => d.hidden = true);
  d.querySelector('#tb-stop').addEventListener('click', () => { _stop = true; });
  d.querySelector('#tb-export').addEventListener('click', _exportReport);
  return d;
}

function _populateList(cases) {
  const list = document.getElementById('tb-list'); if (!list) return;
  list.innerHTML = '';
  for (const c of cases) {
    const row = _el('div', 'tb-row tb-pending');
    row.id = `tb-row-${c.id}`;
    row.innerHTML = `<span class="tb-dot"></span><span class="tb-id">${c.id}</span><span class="tb-name">${c.name}</span><span class="tb-cat">${c.category}</span><span class="tb-type">${c.type}</span><span class="tb-stage"></span><span class="tb-time"></span><button class="tb-vote-btn tb-vote-ok" data-id="${c.id}" data-vote="ok" title="通过">V</button><button class="tb-vote-btn tb-vote-bad" data-id="${c.id}" data-vote="bad" title="不通过">X</button><button class="tb-rerun" title="重跑">[R]</button>`;
    // 点击行（非按钮）→ EMC 跳转
    row.addEventListener('click', (e) => { if (!e.target.classList.contains('tb-rerun') && !e.target.classList.contains('tb-vote-btn')) _jumpToAnswer(c.id); });
    // 重跑按钮
    row.querySelector('.tb-rerun').addEventListener('click', (e) => { e.stopPropagation(); _rerunOne(c); });
    // 评价按钮（行内·V/X·灰色默认·点击亮起）
    row.querySelectorAll('.tb-vote-btn').forEach((b) => b.addEventListener('click', (e) => {
      e.stopPropagation();
      const vid = e.target.dataset.id; const vt = e.target.dataset.vote;
      if (!_results[vid]) _results[vid] = {};
      _results[vid].userVote = vt;
      // 同行清除另一个的 active，点亮当前
      const r = document.getElementById(`tb-row-${vid}`);
      r.querySelectorAll('.tb-vote-btn').forEach((x) => x.classList.remove('active'));
      e.target.classList.add('active');
      // 覆盖行状态
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

  _running = true; _stop = false;
  const fab = document.getElementById('tb-fab');
  fab.classList.add('tb-fab-running'); fab.textContent = '...';
  const drawer = document.getElementById('tb-drawer'); drawer.hidden = false;
  document.getElementById('tb-stop').hidden = false;
  document.getElementById('tb-export').hidden = true;
  _populateList(cases);
  _runCases(cases, opts.timeout);
}

async function _runCases(cases, timeoutMin) {
  const startMs = Date.now();
  let p = 0, f = 0, r = 0;
  for (let i = 0; i < cases.length; i++) {
    if (_stop) break;
    if (timeoutMin && (Date.now() - startMs) / 60000 >= timeoutMin) break;
    const c = cases[i];
    _setRow(c.id, 'running');
    _updateStats(i, cases.length, p, f, r);
    // LLM 自动展开 EMC
    if (c.type === 'llm') document.getElementById('chat-input')?.focus();
    await w(300);
    // 记录 chat 消息索引（跑前）
    const chatBefore = document.querySelectorAll('.chat-msg-assistant').length;
    let result;
    try { result = await c.run(t); } catch (e) { result = { pass: false, stage: 'error', obs: (e?.message) || String(e) }; }
    result.duration = Date.now() - startMs;   // 粗略（含之前累积）
    result.durationSolo = Date.now() - (result._start || Date.now());
    const chatAfter = document.querySelectorAll('.chat-msg-assistant').length;
    result.chatIdx = chatAfter - 1;   // 最后一条 assistant = 本例答案
    _results[c.id] = result;
    const status = result.pass ? 'pass' : 'fail';
    if (status === 'pass') p++; else f++;
    _setRow(c.id, status, result);
    _updateStats(i + 1, cases.length, p, f, r);
    if (i < cases.length - 1) await w(500);
  }
  _running = false;
  const fab = document.getElementById('tb-fab');
  fab.classList.remove('tb-fab-running'); fab.textContent = '[OK]';
  document.getElementById('tb-stop').hidden = true;
  document.getElementById('tb-export').hidden = false;
}

// ── 重跑单例 ──
async function _rerunOne(c) {
  if (_running) return;
  _setRow(c.id, 'running');
  if (c.type === 'llm') { document.getElementById('chat-input')?.focus(); await w(300); t.newChat(); await w(300); }
  let result;
  try { result = await c.run(t); } catch (e) { result = { pass: false, stage: 'error', obs: (e?.message) || String(e) }; }
  result.chatIdx = document.querySelectorAll('.chat-msg-assistant').length - 1;
  _results[c.id] = result;
  _setRow(c.id, result.pass ? 'pass' : 'fail', result);
}

// ── 行状态更新 + 👍/👎 ──
function _setRow(id, status, result) {
  const row = document.getElementById(`tb-row-${id}`); if (!row) return;
  row.className = `tb-row tb-${status}`;
  if (result) {
    row.querySelector('.tb-stage').textContent = result.stage ? `[${result.stage}]` : (status === 'pass' ? '[OK]' : '[ERR]');
    row.querySelector('.tb-time').textContent = result.durationSolo ? `${(result.durationSolo / 1000).toFixed(1)}s` : '';
    let extra = row.querySelector('.tb-extra'); if (!extra) { extra = _el('div', 'tb-extra'); row.appendChild(extra); }
    let html = `<div class="tb-obs">${result.obs || ''}</div>`;
    // 每例都有 👍/👎（用户满意度覆盖自动）
    const vote = _results[id]?.userVote;
    html += `<div class="tb-vote">满意度 <button class="tb-thumb ${vote === 'ok' ? 'active' : ''}" data-id="${id}" data-vote="ok">OK</button><button class="tb-thumb ${vote === 'bad' ? 'active' : ''}" data-id="${id}" data-vote="bad">BAD</button></div>`;
    if (result.review) html += `<div class="tb-review-prompt">${result.review}</div>`;
    extra.innerHTML = html;
    extra.querySelectorAll('.tb-thumb').forEach(b => b.addEventListener('click', (e) => {
      e.stopPropagation();
      const vid = e.target.dataset.id; const vt = e.target.dataset.vote;
      if (!_results[vid]) _results[vid] = {};
      _results[vid].userVote = vt;
      // 用户判断覆盖行状态
      const r = document.getElementById(`tb-row-${vid}`);
      r.className = `tb-row tb-${vt === 'ok' ? 'pass' : 'fail'}`;
      extra.querySelectorAll('.tb-thumb').forEach(x => x.classList.remove('active'));
      e.target.classList.add('active');
    }));
  }
}

function _updateStats(done, total, p, f, r) {
  const el = document.getElementById('tb-stats-text'); if (!el) return;
  el.textContent = `${done}/${total} | [OK]${p} [ERR]${f}`;
}

// ── 点击行→EMC 跳转 ──
function _jumpToAnswer(id) {
  const r = _results[id]; if (!r || r.chatIdx == null) return;
  const msgs = document.querySelectorAll('.chat-msg-assistant');
  const target = msgs[r.chatIdx]; if (!target) return;
  // 展开 EMC
  const input = document.getElementById('chat-input'); if (input) input.focus();
  setTimeout(() => {
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    target.classList.add('tb-highlight');
    setTimeout(() => target.classList.remove('tb-highlight'), 2000);
  }, 300);
}

// ── 导出报告 ──
function _exportReport() {
  const now = new Date();
  const ts = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  const ids = Object.keys(_results);
  const pass = ids.filter(id => { const r = _results[id]; return r.userVote === 'ok' || (!r.userVote && r.pass); }).length;
  const fail = ids.filter(id => { const r = _results[id]; return r.userVote === 'bad' || (!r.userVote && !r.pass); }).length;
  let md = `## 测试 session ${ts}\n\n总数: ${ids.length} | [OK]${pass} | [ERR]${fail}\n\n`;
  md += `| ID | 名称 | 自动 | 用户 | 阶段 | obs |\n|---|---|---|---|---|---|\n`;
  for (const id of ids) {
    const r = _results[id]; const c = CASES.find(x => x.id === id) || {};
    const auto = r.pass ? '[OK]' : '[ERR]';
    const user = r.userVote ? (r.userVote === 'ok' ? 'OK' : 'BAD') : '—';
    md += `| ${id} | ${c.name || ''} | ${auto} | ${user} | ${r.stage || ''} | ${(r.obs || '').slice(0, 60)} |\n`;
  }
  const win = window.open('', '_blank');
  if (win) { win.document.write(`<pre>${md.replace(/</g, '&lt;')}</pre>`); win.document.close(); }
}

// ── 初始化 ──
document.body.appendChild(_createFab());
_createDrawer();
console.log('[test-board] v2 就绪（100 例·?test=1）');
