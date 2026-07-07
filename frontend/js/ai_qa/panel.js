// ═══ panel.js — AI 问答 UI（chat.html 独立窗 + 主页面浮窗降级 共用）═══
// 形态无关：不 import map/state/panel（主窗口函数），全经 protocol.js 与主窗口通信。
// 4 区骨架（每条 assistant 消息）：①思考链(Pro 原生) ②解题面板(STEP①-④) ③结论区(STEP⑤) ④审查状态区。
// 入口 initChat({onClose})：chat.html DOMContentLoaded 调；浮窗降级时 ai_qa_host 调。
import { orchestrate } from './harness.js';
import { onPush, hello, bye, notify, NOTIFY, PUSH } from './protocol.js';

let _context = '';            // 主窗口推送的 grounding 摘要
let _contextTokens = [];      // @关联对象（预留）
let _enableReview = true;     // 审查层开关（MVP 默认开）
let _streaming = false;
let _abortCtl = null;
let _onClose = null;
let _messages = [];           // 多轮历史（MVP 存文本）

// ── 工具 ─────────────────────────────────────────────────────────
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function scrollBottom() {
  const list = document.getElementById('chat-messages');
  if (list) list.scrollTop = list.scrollHeight;
}
function appendMessage(role, contentHtml) {
  const list = document.getElementById('chat-messages');
  if (!list) return;
  const el = document.createElement('div');
  el.className = `chat-msg chat-msg-${role}`;
  el.innerHTML = `<div class="chat-bubble">${contentHtml}</div>`;
  list.appendChild(el);
  scrollBottom();
}

/** markdown 渲染（marked 不可用退纯文本）+ [ref:NAME] → 可点 chip。 */
function renderAnswer(text) {
  let html = window.marked ? window.marked.parse(text) : `<p>${escapeHtml(text).replace(/\n/g, '<br>')}</p>`;
  html = html.replace(/\[ref:([^\]]+)\]/g, (_, name) =>
    `<button class="cite-chip" data-ref="${escapeHtml(name)}" type="button">${escapeHtml(name)}</button>`);
  return html;
}

// ── 执行轨道（STEP③ 的 steps[] 清单，逐步实时状态）──
const STEP_ICON = { pending: '○', running: '⟳', done: '✓', error: '✕' };
function renderTrack(trackEl, steps) {
  const els = {};
  if (!trackEl || !steps || !steps.length) return els;
  trackEl.innerHTML = steps.map((s) => {
    const id = s.id || '';
    return `<div class="aiq-step-row" data-id="${escapeHtml(id)}">`
      + `<span class="aiq-step-ico">${STEP_ICON.pending}</span>`
      + `<span class="aiq-step-label">${escapeHtml(s.label || s.tool || '')}</span>`
      + `<span class="aiq-step-note"></span></div>`;
  }).join('');
  trackEl.querySelectorAll('.aiq-step-row').forEach((row) => { els[row.dataset.id] = row; });
  return els;
}
function updateStep(row, status, note) {
  if (!row) return;
  row.classList.remove('is-running', 'is-done', 'is-error');
  if (status === 'running') row.classList.add('is-running');
  else if (status === 'done') row.classList.add('is-done');
  else if (status === 'error') row.classList.add('is-error');
  const ico = row.querySelector('.aiq-step-ico');
  if (ico) ico.textContent = STEP_ICON[status] || STEP_ICON.pending;
  const n = row.querySelector('.aiq-step-note');
  if (n && note) n.textContent = '→ ' + note;
}

/** 审查状态区：6 条 checks（✓/✕）+ 总判定。 */
function renderReview(result) {
  const checks = result.checks || [];
  const overall = result.pass
    ? '<div class="aiq-verdict is-pass">✓ 审查通过</div>'
    : '<div class="aiq-verdict is-fail">✕ 不达标 · 触发修订</div>';
  const rows = checks.map((c) => {
    const cls = c.pass ? 'is-ok' : 'is-bad';
    const mark = c.pass ? '✓' : '✕';
    const note = c.note ? `<span class="aiq-check-note">${escapeHtml(c.note)}</span>` : '';
    return `<div class="aiq-check ${cls}"><span class="aiq-check-mark">${mark}</span><span class="aiq-check-name">${escapeHtml(c.name || c.key)}</span>${note}</div>`;
  }).join('');
  return overall + rows;
}

// ── assistant 消息骨架（4 区）──
function appendAssistantShell() {
  const list = document.getElementById('chat-messages');
  if (!list) return null;
  const el = document.createElement('div');
  el.className = 'chat-msg chat-msg-assistant';
  el.innerHTML = `<div class="chat-bubble">
    <div class="aiq-reason" hidden><div class="aiq-reason-head">▸ 思考过程（Pro 原生）</div><div class="aiq-reason-body"></div></div>
    <div class="aiq-solve" hidden>
      <div class="aiq-solve-head">解题过程</div>
      <div class="aiq-step"><span class="aiq-step-tag">① 问题定性</span><div class="aiq-step-body" data-k="framing">…</div></div>
      <div class="aiq-step"><span class="aiq-step-tag">② 框架映射</span><div class="aiq-step-body" data-k="mapping">…</div></div>
      <div class="aiq-step"><span class="aiq-step-tag">③ 路径规划</span><div class="aiq-track"></div></div>
      <div class="aiq-step"><span class="aiq-step-tag">④ 执行观察</span><div class="aiq-step-body" data-k="obs">…</div></div>
    </div>
    <div class="aiq-step"><span class="aiq-step-tag">⑤ 结论</span><div class="aiq-answer"><span class="chat-cursor">▍</span></div></div>
    <div class="aiq-review" hidden><div class="aiq-review-head">审查 · 六条质量标准</div><div class="aiq-review-body"></div></div>
  </div>`;
  list.appendChild(el);
  scrollBottom();
  return {
    reasonEl: el.querySelector('.aiq-reason'),
    reasonBody: el.querySelector('.aiq-reason-body'),
    solveEl: el.querySelector('.aiq-solve'),
    framingBody: el.querySelector('[data-k="framing"]'),
    mappingBody: el.querySelector('[data-k="mapping"]'),
    trackEl: el.querySelector('.aiq-track'),
    obsBody: el.querySelector('[data-k="obs"]'),
    answerEl: el.querySelector('.aiq-answer'),
    reviewEl: el.querySelector('.aiq-review'),
    reviewBody: el.querySelector('.aiq-review-body'),
  };
}

/** 构造 hooks（绑定到一条 assistant 消息的 DOM）。 */
function buildHooks(shell) {
  let reasonAcc = '';
  let answerAcc = '';
  let stepEls = {};
  return {
    onReason: (tok) => {
      reasonAcc += tok;
      if (shell.reasonEl) {
        shell.reasonEl.hidden = false;
        shell.reasonBody.textContent = reasonAcc;
        scrollBottom();
      }
    },
    onFraming: (text) => {
      if (shell.solveEl) shell.solveEl.hidden = false;
      if (shell.framingBody) shell.framingBody.textContent = text;
      scrollBottom();
    },
    onMapping: (text) => {
      if (shell.solveEl) shell.solveEl.hidden = false;
      if (shell.mappingBody) shell.mappingBody.textContent = text;
      scrollBottom();
    },
    onPlan: (steps) => {
      if (shell.solveEl) shell.solveEl.hidden = false;
      stepEls = renderTrack(shell.trackEl, steps);
      scrollBottom();
    },
    onStepState: (id, status, note) => { updateStep(stepEls[id], status, note); scrollBottom(); },
    onObservation: (text) => { if (shell.obsBody) shell.obsBody.textContent = text; scrollBottom(); },
    onDraft: (tok) => {
      answerAcc += tok;
      if (shell.answerEl) shell.answerEl.innerHTML = renderAnswer(answerAcc) + '<span class="chat-cursor">▍</span>';
      scrollBottom();
    },
    onDraftReset: () => {
      answerAcc = '';
      if (shell.answerEl) shell.answerEl.innerHTML = '<span class="chat-cursor">▍</span>';
    },
    onReview: (result) => {
      if (shell.reviewEl) { shell.reviewEl.hidden = false; shell.reviewBody.innerHTML = renderReview(result); scrollBottom(); }
    },
    onRevise: (round, hints) => {
      if (shell.reviewBody) shell.reviewBody.insertAdjacentHTML('beforeend',
        `<div class="aiq-revise">↻ 第 ${round} 轮修订 · ${escapeHtml((hints || '').slice(0, 140))}…</div>`);
      scrollBottom();
    },
    onReviewError: (msg) => {
      if (shell.reviewEl) {
        shell.reviewEl.hidden = false;
        shell.reviewBody.innerHTML = `<div class="aiq-review-err">审查未执行：${escapeHtml(msg)}（直接采用初稿）</div>`;
      }
    },
    onDegraded: (text) => { if (shell.answerEl) shell.answerEl.innerHTML = renderAnswer(text || '（未生成有效回答）'); },
    onFinal: (text, meta) => {
      if (shell.answerEl) {
        shell.answerEl.innerHTML = renderAnswer(text);
        if (meta.revised) shell.answerEl.insertAdjacentHTML('beforeend', '<div class="aiq-final-tag">↻ 已按审查修订</div>');
        else if (meta.review && meta.review.pass) shell.answerEl.insertAdjacentHTML('beforeend', '<div class="aiq-final-tag">✓ 审查通过</div>');
      }
      if (shell.reasonEl && reasonAcc) shell.reasonEl.classList.add('is-done');
      if (text) _messages.push({ role: 'assistant', content: text });
    },
  };
}

async function send(text) {
  text = (text || '').trim();
  if (!text || _streaming) return;
  const input = document.getElementById('chat-input');
  if (input) input.value = '';
  appendMessage('user', escapeHtml(text));
  _messages.push({ role: 'user', content: text });

  const shell = appendAssistantShell();
  if (!shell) return;
  _streaming = true;
  updateSendBtn();
  _abortCtl = new AbortController();
  const ctx = {
    question: text,
    context: _context,
    contextTokens: _contextTokens.length ? _contextTokens : undefined,
    signal: _abortCtl.signal,
    enableReview: _enableReview,
  };
  try {
    await orchestrate(ctx, buildHooks(shell));
  } catch (e) {
    const aborted = e && e.name === 'AbortError';
    if (shell.answerEl) shell.answerEl.innerHTML += aborted
      ? ' <span class="chat-error">（已停止）</span>'
      : `<span class="chat-error">[请求失败] ${escapeHtml(e.message || e)}</span>`;
  } finally {
    _streaming = false;
    _abortCtl = null;
    updateSendBtn();
  }
}

function updateSendBtn() {
  const btn = document.getElementById('chat-send');
  if (!btn) return;
  if (_streaming) { btn.textContent = '停止'; btn.classList.add('is-stop'); }
  else { btn.textContent = '发送'; btn.classList.remove('is-stop'); }
}

function clearChat() {
  _messages = [];
  const list = document.getElementById('chat-messages');
  if (list) list.innerHTML = '';
}

function onMsgClick(e) {
  const reason = e.target.closest('.aiq-reason.is-done');
  if (reason) { reason.classList.toggle('is-open'); return; }
  const chip = e.target.closest('.cite-chip');
  if (chip) { notify(NOTIFY.FOCUS, { names: [chip.dataset.ref] }); return; }
}

/** 入口：chat.html 与浮窗降级共用。opts.onClose = 关闭回调（独立窗 window.close / 浮窗隐藏）。 */
export function initChat(opts = {}) {
  _onClose = opts.onClose || (() => {});
  // 订阅主窗口推送
  onPush((type, payload) => {
    if (type === PUSH.CONTEXT) _context = (payload && payload.summary) || '';
    else if (type === PUSH.TOKENS) _contextTokens = Array.isArray(payload) ? payload : [];
  });
  // 事件绑定
  document.getElementById('chat-send')?.addEventListener('click', () => {
    if (_streaming && _abortCtl) { _abortCtl.abort(); return; }
    send(document.getElementById('chat-input')?.value);
  });
  document.getElementById('chat-input')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(e.target.value); }
  });
  document.getElementById('chat-clear')?.addEventListener('click', clearChat);
  document.getElementById('chat-close')?.addEventListener('click', () => { bye(); _onClose(); });
  document.getElementById('chat-messages')?.addEventListener('click', onMsgClick);
  // 握手主窗口（推送 context / selection）
  hello();
  setTimeout(() => document.getElementById('chat-input')?.focus(), 60);
}
