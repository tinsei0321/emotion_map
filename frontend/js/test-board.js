// ═══ test-board.js — 测试飞轮抽屉（v1.7·?test=1 加载）═══
// 浮动 🧪 按钮 → 抽屉（用例列表 + 参数 + 实时结果 + 导出报告）。
// 复用 e2e-seam test helpers（window.__emcTest）+ design tokens。
import { CASES } from './test-cases.js';

const t = window.__emcTest;
let _running = false, _stop = false;
const _results = [];

function _el(tag, cls, html) { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }

function _createUI() {
  // 浮动按钮
  const btn = _el('button', 'tb-fab', '[OK]'); btn.title = '测试飞轮'; btn.id = 'tb-fab';
  btn.addEventListener('click', () => { drawer.hidden = !drawer.hidden; });
  // 抽屉
  const drawer = _el('div', 'tb-drawer'); drawer.hidden = true;
  // Header
  const head = _el('div', 'tb-head', '<span class="tb-title">测试飞轮</span>');
  const closeBtn = _el('button', 'tb-close', 'x'); closeBtn.addEventListener('click', () => drawer.hidden = true);
  head.appendChild(closeBtn); drawer.appendChild(head);
  // 参数栏
  const ctrl = _el('div', 'tb-ctrl');
  ctrl.innerHTML = '<label><input type="radio" name="tb-mode" value="no-llm" checked> no-llm</label>'
    + '<label><input type="radio" name="tb-mode" value="full"> full</label>'
    + '<button id="tb-start" class="tb-btn">开始</button> <button id="tb-stop" class="tb-btn tb-stop" hidden>停止</button>';
  drawer.appendChild(ctrl);
  // 统计
  const stats = _el('div', 'tb-stats', '<span id="tb-stats-text">— / —</span>');
  drawer.appendChild(stats);
  // 用例列表
  const list = _el('div', 'tb-list'); list.id = 'tb-list';
  for (const c of CASES) {
    const row = _el('div', `tb-row tb-pending`, `<span class="tb-dot"></span><span class="tb-id">${c.id}</span><span class="tb-name">${c.name}</span><span class="tb-cat">${c.category}</span><span class="tb-type">${c.type}</span><span class="tb-stage"></span><span class="tb-time"></span>`);
    row.id = `tb-row-${c.id}`;
    row.addEventListener('click', () => row.classList.toggle('tb-expanded'));
    list.appendChild(row);
  }
  drawer.appendChild(list);
  // 导出
  const exportBtn = _el('button', 'tb-btn tb-export', '导出报告'); exportBtn.hidden = true; exportBtn.id = 'tb-export';
  exportBtn.addEventListener('click', _exportReport);
  drawer.appendChild(exportBtn);
  // 挂载
  document.body.appendChild(btn);
  document.body.appendChild(drawer);
  // 绑定
  document.getElementById('tb-start').addEventListener('click', _onStart);
  document.getElementById('tb-stop').addEventListener('click', () => { _stop = true; });
}

function _onStart() {
  if (_running) return;
  const mode = document.querySelector('input[name="tb-mode"]:checked')?.value || 'no-llm';
  const cases = mode === 'full' ? CASES : CASES.filter(c => c.type === 'no-llm');
  _running = true; _stop = false; _results.length = 0;
  document.getElementById('tb-start').hidden = true;
  document.getElementById('tb-stop').hidden = false;
  document.getElementById('tb-export').hidden = true;
  // reset rows
  for (const c of CASES) { const r = document.getElementById(`tb-row-${c.id}`); r.className = 'tb-row tb-pending'; r.querySelector('.tb-stage').textContent = ''; r.querySelector('.tb-time').textContent = ''; }
  _runCases(cases);
}

async function _runCases(cases) {
  let pass = 0, fail = 0, review = 0;
  for (let i = 0; i < cases.length; i++) {
    if (_stop) break;
    const c = cases[i];
    _setRow(c.id, 'running', '');
    document.getElementById('tb-stats-text').textContent = `${i + 1}/${cases.length}`;
    const start = Date.now();
    let result;
    try { result = await c.run(t); } catch (e) { result = { pass: false, stage: 'error', obs: (e && e.message) || String(e) }; }
    result.duration = Date.now() - start;
    _results.push({ ...c, ...result });
    const status = result.pass ? (result.review ? 'review' : 'pass') : 'fail';
    if (status === 'pass') pass++; else if (status === 'review') review++; else fail++;
    _setRow(c.id, status, result);
    document.getElementById('tb-stats-text').textContent = `${i + 1}/${cases.length} | [OK]${pass} [ERR]${fail} ~${review}`;
    if (i < cases.length - 1) await new Promise(r => setTimeout(r, 500));
  }
  _running = false;
  document.getElementById('tb-start').hidden = false;
  document.getElementById('tb-stop').hidden = true;
  document.getElementById('tb-export').hidden = false;
}

function _setRow(id, status, result) {
  const row = document.getElementById(`tb-row-${id}`);
  if (!row) return;
  row.className = `tb-row tb-${status}`;
  if (result) {
    const stage = row.querySelector('.tb-stage');
    stage.textContent = result.stage ? `[${result.stage}]` : (status === 'pass' ? '[OK]' : '');
    row.querySelector('.tb-time').textContent = result.duration ? `${(result.duration / 1000).toFixed(1)}s` : '';
    // obs + review（展开区）
    let extra = row.querySelector('.tb-extra');
    if (!extra) { extra = _el('div', 'tb-extra'); row.appendChild(extra); }
    let html = `<div class="tb-obs">${result.obs || ''}</div>`;
    if (result.review) {
      html += `<div class="tb-review">[WARN] ${result.review} <button class="tb-thumb" data-id="${id}" data-vote="ok">OK</button><button class="tb-thumb" data-id="${id}" data-vote="bad">BAD</button></div>`;
    }
    extra.innerHTML = html;
    extra.querySelectorAll('.tb-thumb').forEach(b => b.addEventListener('click', (e) => {
      const vote = e.target.dataset.vote;
      const r = _results.find(x => x.id === id);
      if (r) r.userVote = vote;
      e.target.parentElement.innerHTML = vote === 'ok' ? '[OK] 合理' : '[ERR] 不合理';
    }));
  }
}

function _exportReport() {
  const now = new Date();
  const ts = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  const pass = _results.filter(r => r.pass && !r.review).length;
  const fail = _results.filter(r => !r.pass).length;
  const review = _results.filter(r => r.review).length;
  const total = _results.length;
  const totalTime = _results.reduce((s, r) => s + (r.duration || 0), 0);
  let md = `## 测试 session ${ts}（${document.querySelector('input[name="tb-mode"]:checked')?.value}）\n\n`;
  md += `总数: ${total} | [OK]${pass} | [ERR]${fail} | ~${review} | 耗时 ${(totalTime / 1000 / 60).toFixed(1)}min\n\n`;
  md += `### 明细\n\n| ID | 名称 | 状态 | 阶段 | 耗时 | obs |\n|---|---|---|---|---|---|\n`;
  for (const r of _results) {
    const st = r.pass ? (r.review ? '~review' : '[OK]pass') : '[ERR]fail';
    const vote = r.userVote ? ` (${r.userVote === 'ok' ? 'OK' : 'BAD'})` : '';
    md += `| ${r.id} | ${r.name} | ${st}${vote} | ${r.stage || ''} | ${r.duration ? (r.duration / 1000).toFixed(1) + 's' : ''} | ${(r.obs || '').slice(0, 80)} |\n`;
  }
  const w = window.open('', '_blank');
  if (w) { w.document.write(`<pre>${md.replace(/</g, '&lt;')}</pre>`); w.document.close(); }
}

_createUI();
console.log('[test-board] 测试飞轮抽屉就绪（?test=1）');
