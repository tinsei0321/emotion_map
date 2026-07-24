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
// template/工具 id → 中文名（摘要用，治「tpl=zonal 看不懂」）
const _TPL_CN = {
  zonal: '分区统计', rank: '排序', density: '密度', buffer: '缓冲', clip: '裁剪',
  overlay: '叠置', compare: '对比', concept: '概念问答', multi: '多步骤',
  extract_feature: '抽取要素', filter_attr: '属性筛选', hotspot: '热点',
  area_stats: '面积统计', merge: '合并', nearest: '邻近', unknown: '未知',
};

// ── 行内摘要（3 行中文·固定结构）：①工具 ②图层 ③状态。
//    转译例（有 template/tools/newLayers）显示 3 行；no-llm/非转译例回退 obs/stage。
//    完整 ①②③ 含「计划执行命中数/判断正确数占比/计划生成数」需 diagnose method/plan 采集（后续批），本批用现有数据。
function _summary(r) {
  if (!r) return '';
  const tools = Array.isArray(r.tools) && r.tools.length ? r.tools : [];
  if (!(r.template || tools.length || r.newLayers)) {
    if (r.obs) return String(r.obs).slice(0, 60);
    return r.stage ? `[${r.stage}]` : (r.pass ? '[OK]' : '');
  }
  // ①工具
  const tBits = [];
  if (r.template) tBits.push(_TPL_CN[r.template] || r.template);
  for (const t of tools) if (t !== r.template) tBits.push(_TPL_CN[t] || t);
  const line1 = `①工具：${tools.length ? `触发${tools.length}个(${tBits.slice(0, 4).join('·')})` : (r.template ? `选${_TPL_CN[r.template] || r.template}` : '未触发')}`;
  // ②图层（实际生成数 + 参数摘要）
  const p = r.params || {};
  const pBits = [];
  if (p.boundary) pBits.push(`区=${p.boundary}`); else if (p.boundaries) pBits.push(`区=${p.boundaries}`);
  if (p.cell != null) pBits.push(`格${p.cell}m`);
  if (p.radius != null) pBits.push(`缓冲${p.radius}m`);
  const line2 = `②图层：${r.newLayers ? `实际${r.newLayers}层` : '未生成'}${pBits.length ? `(${pBits.join(' ')})` : ''}`;
  // ③状态（pass=完成 / s3=超时未完成 / 否则未完成）
  const st = r.pass ? '完成' : (r.stage === 's3' ? '未完成(超时)' : '未完成');
  const line3 = `③状态：${st}`;
  return `<span class="tb-tool">${line1}<br>${line2}<br>${line3}</span>`;
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
  const date = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  const ids = Object.keys(_results);
  let p = 0, f = 0, uo = 0, ub = 0;
  let timeout = 0, gap = 0, falseKill = 0, missFail = 0;   // EMC-SUM 批级聚合
  const durs = [];
  for (const id of ids) {
    const r = _results[id];
    if (r.userVote === 'bad' || (!r.userVote && !r.pass)) f++; else p++;
    if (r.userVote === 'ok') uo++; else if (r.userVote === 'bad') ub++;
    if (/超时/.test(r.obs || '') || r.stage === 's3') timeout++;
    if (/缺数据|未产出|需上传|GAP/.test(r.obs || '')) gap++;
    if (r.pass === false && r.userVote === 'ok') falseKill++;    // 误杀：系统判败但用户认可
    if (r.pass === true && r.userVote === 'bad') missFail++;     // 漏判：系统判过但用户否定
    if (r.durationSolo) durs.push(r.durationSolo);
  }
  durs.sort((a, b) => a - b);
  const pct = (q) => durs.length ? Math.round(durs[Math.min(durs.length - 1, Math.floor(q * durs.length))] / 1000) : 0;
  const cats = _runMeta.cats?.length ? _runMeta.cats.join(', ') : '全选';
  let md = `# EMC 测试报告 · ${ts}\n\n`;
  // EMC-SUM v1 批级头部（占比唯一住所·键值定序·可 grep；commit 由 serve.py 落 JSON 时补）
  md += `## RUN ${date} | schema=EMC-SUM v1 | mode=${_runMeta.mode || 'all'} | n=${ids.length} | pass=${p} ${ids.length ? (p / ids.length * 100).toFixed(0) : 0}% | timeout=${timeout} | gap=${gap} | 误杀=${falseKill} 漏判=${missFail} | t_p50=${pct(0.5)}s t_p95=${pct(0.95)}s | cats=${cats}\n`;
  md += `- 用户 OK ${uo} / BAD ${ub} / 未评 ${ids.length - uo - ub}\n\n`;
  md += `| ID | 名称 | 类型 | 判定 | judge | 用户 | template | 工具 | 参数/产物 | obs |\n|---|---|---|---|---|---|---|---|---|---|\n`;
  for (const id of ids) {
    const r = _results[id]; const c = CASES.find((x) => x.id === id) || {};
    const auto = r.pass ? 'OK' : 'ERR';
    const judge = (r.userVote === 'ok' && !r.pass) ? '误杀' : (r.userVote === 'bad' && r.pass) ? '漏判' : (r.pass ? 'ok' : 'err');
    const user = r.userVote ? (r.userVote === 'ok' ? 'OK' : 'BAD') : '—';
    const tmpl = r.template || '?';                 // 键永在·值缺失填 ?（H1 修通前 template=? 即观测盲区信号）
    const tools = Array.isArray(r.tools) && r.tools.length ? r.tools.join('+') : '?';
    const pp = [];
    if (r.params) { if (r.params.boundary) pp.push(`区=${r.params.boundary}`); if (r.params.boundaries) pp.push(`区=${r.params.boundaries}`); if (r.params.cell != null) pp.push(`cell=${r.params.cell}`); if (r.params.radius != null) pp.push(`r=${r.params.radius}`); }
    if (r.newLayers) pp.push(`+${r.newLayers}层`);
    const ppStr = pp.join(' ') || '?';
    const obs = (r.obs || '').replace(/\|/g, '/').slice(0, 60) || '?';
    md += `| ${id} | ${c.name || ''} | ${c.type || ''} | ${auto} | ${judge} | ${user} | ${tmpl} | ${tools} | ${ppStr} | ${obs} |\n`;
  }
  const fails = ids.filter((id) => { const r = _results[id]; return r.userVote === 'bad' || (!r.userVote && !r.pass); });
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

function _buildJSON() {
  // H5: 机器可读报告（与 md 同 schema，serve.py 落 report-*.json，补 commit/savedAt）。
  const ids = Object.keys(_results);
  const cases = ids.map((id) => {
    const r = _results[id]; const c = CASES.find((x) => x.id === id) || {};
    return {
      id, name: c.name || '', category: c.category || '', type: c.type || '',
      pass: !!r.pass, stage: r.stage || '',
      template: r.template || null, tools: Array.isArray(r.tools) ? r.tools : [],
      params: r.params || null, newLayers: r.newLayers || 0,
      durationSolo: r.durationSolo || 0, userVote: r.userVote || null,
      obs: r.obs || '', review: r.review || '',
    };
  });
  return { meta: { schema: 'EMC-SUM', version: 'v1', mode: _runMeta.mode || 'all', cats: _runMeta.cats || [], total: ids.length, startedAt: _runMeta.startedAt || null }, cases };
}

async function _saveReport(reason) {
  const ids = Object.keys(_results);
  if (!ids.length) { if (reason === 'manual') _toast('尚无结果可报告'); return; }
  const md = _buildMarkdown();
  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  const date = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  const type = (_runMeta.mode || 'run').replace(/[^a-zA-Z0-9_-]/g, '') || 'run';
  const body = { content: md, json: _buildJSON(), type, date, reason };
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
