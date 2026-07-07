// ═══ panel.js — AI 问答 UI（底部滑出 · agent loop · 历史持久化 · 思考深度开关 · 动态状态）═══
import { orchestrate } from './harness.js';
import { buildContext, TOOLS } from './tools.js';
import { getLayers } from '../state.js';

const HISTORY_KEY = 'ai_qa_history_v1';
const MODE_KEY = 'ai_qa_think_mode';

// 动态思考状态文案（轮换，随机感；参考 Claude/ChatGPT "正在思考"动态提示）。
const THINK_PHRASES = ['正在思考', '正在分析', '正在计算', '正在构思', '正在比对数据', '正在归纳', '正在权衡证据', '正在检索线索', '正在梳理逻辑'];

let _streaming = false;
let _abortCtl = null;
let _history = loadHistory();
let _curTrace = null;
let _thinkMode = localStorage.getItem(MODE_KEY) || 'pro';   // 'pro' | 'flash'
let _thinkTimer = null;

function loadHistory() {
  try { const v = localStorage.getItem(HISTORY_KEY); return v ? JSON.parse(v) : []; }
  catch (_) { return []; }
}
function saveHistory() {
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(_history)); } catch (_) {}
}

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
function renderAnswer(text, validNames) {
  let html = window.marked ? window.marked.parse(text) : `<p>${escapeHtml(text).replace(/\n/g, '<br>')}</p>`;
  html = html.replace(/\[ref:([^\]]+)\]/g, (_, name) => {
    const valid = !validNames || validNames.has(name);
    const cls = valid ? 'cite-chip' : 'cite-chip cite-chip-invalid';
    return `<button class="${cls}" data-ref="${escapeHtml(name)}" type="button"${valid ? '' : ' disabled'}>${escapeHtml(name)}</button>`;
  });
  return html;
}

/** 聚合层存在的区域名集合（ref 校验白名单，臆造名标灰）。与 tools.js isAnalysis 同口径。 */
function getValidRefNames() {
  const names = new Set();
  for (const l of getLayers()) {
    if (!l || l.kind !== 'polygon' || !l.fc || !l.fc.features) continue;
    const ui = l.paint && l.paint._ui;
    if (!ui || (ui.tool !== 'grid' && ui.tool !== 'terrain')) continue;
    for (const f of l.fc.features) {
      const p = f.properties || {};
      const nm = p.name || p.issue_label;
      if (nm) names.add(String(nm));
    }
  }
  return names;
}

/** 渲染审查状态区（六条 ✓/△/✕ + 整体结论）。 */
function renderReview(reviewEl, body, review) {
  if (!review) { reviewEl.hidden = true; return; }
  reviewEl.hidden = false;
  if (review.degraded) {
    body.innerHTML = `<div class="aiq-review-verdict warn">审查跳过（${escapeHtml(review.degraded_reason || '审查员不可用')}）</div>`;
    return;
  }
  const icon = { pass: '✓', warn: '△', fail: '✕' };
  const items = (review.scores || []).map((s) =>
    `<span class="aiq-review-item ${s.verdict}" title="${escapeHtml(s.comment || s.name || '')}">${icon[s.verdict] || '?'} ${escapeHtml(s.name || s.key)}</span>`
  ).join('');
  const cls = review.pass ? 'pass' : 'fail';
  const txt = review.pass ? '审查通过' : '审查未过·重写中';
  body.innerHTML = `<div class="aiq-review-verdict ${cls}">${txt}</div><div class="aiq-review-items">${items}</div>`;
}

/** 动态思考指示器：轮换文案 + 跳动点。 */
function startThinking(shell) {
  if (!shell || !shell.thinkingEl) return;
  shell.thinkingEl.hidden = false;
  const txt = shell.thinkingEl.querySelector('.aiq-thinking-text');
  let i = 0;
  if (txt) txt.textContent = THINK_PHRASES[0] + '…';
  _thinkTimer = setInterval(() => {
    if (!txt) return;
    // 随机感：70% 顺序轮换，30% 随机跳（活泼不死板）。
    const idx = Math.random() < 0.3 ? Math.floor(Math.random() * THINK_PHRASES.length) : (i + 1) % THINK_PHRASES.length;
    i = idx;
    txt.textContent = THINK_PHRASES[idx] + '…';
  }, 1300);
}
function stopThinking(shell) {
  if (_thinkTimer) { clearInterval(_thinkTimer); _thinkTimer = null; }
  if (shell && shell.thinkingEl) shell.thinkingEl.hidden = true;
}

/** assistant 消息骨架（思考链 + 动态状态 + 解题步骤 + 结论）。trace 非空 = 历史恢复。 */
function appendAssistantShell(trace) {
  const list = document.getElementById('chat-messages');
  if (!list) return null;
  const el = document.createElement('div');
  el.className = 'chat-msg chat-msg-assistant';
  const isFlash = _thinkMode === 'flash';
  const reasonHead = isFlash ? 'Flash · 直接作答（无思考链）' : '▸ 思考过程（Pro · 实时）';
  const hasReason = !!(trace && (trace.reasonSegments?.length || trace.reason));
  el.innerHTML = `<div class="chat-bubble">
    <div class="aiq-reason ${isFlash ? 'is-flash' : ''}" ${hasReason ? '' : 'hidden'}><div class="aiq-reason-head">${reasonHead}</div><div class="aiq-reason-body"></div></div>
    <div class="aiq-thinking" hidden><span class="aiq-thinking-text">正在思考…</span><span class="aiq-dots"><i></i><i></i><i></i></span></div>
    <div class="aiq-steps" ${trace && trace.steps && trace.steps.length ? '' : 'hidden'}><div class="aiq-steps-head">解题过程（Agent Loop）</div></div>
    <div class="aiq-review" ${trace && trace.review ? '' : 'hidden'}><div class="aiq-review-head">审查</div><div class="aiq-review-body"></div></div>
    <div class="aiq-step aiq-step-final"><span class="aiq-step-tag">结论</span><div class="aiq-answer"><span class="chat-cursor">▍</span></div></div>
  </div>`;
  list.appendChild(el);
  const shell = {
    reasonEl: el.querySelector('.aiq-reason'),
    reasonBody: el.querySelector('.aiq-reason-body'),
    thinkingEl: el.querySelector('.aiq-thinking'),
    stepsEl: el.querySelector('.aiq-steps'),
    reviewEl: el.querySelector('.aiq-review'),
    reviewBody: el.querySelector('.aiq-review-body'),
    answerEl: el.querySelector('.aiq-answer'),
  };
  if (trace) {
    if (trace.reasonSegments && trace.reasonSegments.length) {
      for (const seg of trace.reasonSegments) {
        const segEl = document.createElement('div');
        segEl.className = 'aiq-reason-segment';
        segEl.dataset.round = seg.round;
        segEl.innerHTML = `<div class="aiq-reason-seg-head">${seg.round === 0 ? '最终结论思考' : '第 ' + seg.round + ' 轮思考'}</div><div class="aiq-reason-seg-body">${escapeHtml(seg.text || '')}</div>`;
        shell.reasonBody.appendChild(segEl);
      }
      shell.reasonEl.hidden = false;
      shell.reasonEl.classList.add('is-done');
    } else if (trace.reason) {
      const segEl = document.createElement('div');
      segEl.className = 'aiq-reason-segment';
      segEl.innerHTML = `<div class="aiq-reason-seg-body">${escapeHtml(trace.reason)}</div>`;
      shell.reasonBody.appendChild(segEl);
      shell.reasonEl.hidden = false;
      shell.reasonEl.classList.add('is-done');
    }
    (trace.steps || []).forEach((s) => renderStepRow(shell.stepsEl, s.round, s.thought, s.action, s.observation));
    if (trace.review) renderReview(shell.reviewEl, shell.reviewBody, trace.review);
    shell.answerEl.innerHTML = trace.final ? renderAnswer(trace.final, getValidRefNames()) : '<span class="chat-error">（未生成结论）</span>';
  }
  scrollBottom();
  return shell;
}

function actionLabel(action) {
  if (!action) return '';
  if (action.type === 'answer') return '✓ 决定出结论';
  const p = action.params && Object.keys(action.params).length ? JSON.stringify(action.params) : '';
  return `→ ${action.name}${p ? '(' + p + ')' : ''}`;
}
function renderStepRow(stepsEl, round, thought, action, observation) {
  const row = document.createElement('div');
  row.className = 'aiq-step-row';
  row.dataset.round = round;
  row.innerHTML = `<span class="aiq-step-num">${round}</span><div class="aiq-step-content">`
    + `<div class="aiq-step-thought">${escapeHtml(thought || '…')}</div>`
    + (action ? `<div class="aiq-step-action">${escapeHtml(actionLabel(action))}</div>` : '')
    + (observation ? `<div class="aiq-step-obs">${escapeHtml(observation)}</div>` : '')
    + `</div>`;
  stepsEl.appendChild(row);
}

function buildHooks(shell) {
  let answerAcc = '';
  let reviseAcc = '';
  const reasonSegs = {};   // round -> text
  const isFlash = _thinkMode === 'flash';

  function ensureSeg(round) {
    if (reasonSegs[round]) return;
    const seg = document.createElement('div');
    seg.className = 'aiq-reason-segment';
    seg.dataset.round = round;
    seg.innerHTML = `<div class="aiq-reason-seg-head">${round === 0 ? '最终结论思考' : '第 ' + round + ' 轮思考'}</div><div class="aiq-reason-seg-body"></div>`;
    shell.reasonBody.appendChild(seg);
    reasonSegs[round] = '';
  }
  function flushReasonSegs() {
    if (_curTrace) _curTrace.reasonSegments = Object.keys(reasonSegs).map((k) => ({ round: Number(k), text: reasonSegs[k] }));
  }

  return {
    onRoundStart: (round) => {
      if (isFlash) return;
      shell.reasonEl.hidden = false;
      ensureSeg(round);
    },
    onReason: (tok, round) => {
      if (isFlash) return;
      shell.reasonEl.hidden = false;
      const r = round || 0;
      ensureSeg(r);
      reasonSegs[r] += tok;
      const body = shell.reasonBody.querySelector(`.aiq-reason-segment[data-round="${r}"] .aiq-reason-seg-body`);
      if (body) body.textContent = reasonSegs[r];
      flushReasonSegs();
      scrollBottom();
    },
    onRound: () => {},
    onThought: (thought, round) => {
      shell.stepsEl.hidden = false;
      renderStepRow(shell.stepsEl, round, thought, null, null);
      if (_curTrace) _curTrace.steps.push({ round, thought, action: null, observation: null });
      scrollBottom();
    },
    onAction: (action, round) => {
      const row = shell.stepsEl.querySelector(`.aiq-step-row[data-round="${round}"]`);
      if (row) row.querySelector('.aiq-step-content').insertAdjacentHTML('beforeend',
        `<div class="aiq-step-action">${escapeHtml(actionLabel(action))}</div>`);
      if (_curTrace && _curTrace.steps.length) _curTrace.steps[_curTrace.steps.length - 1].action = action;
    },
    onObservation: (obs, round) => {
      const row = shell.stepsEl.querySelector(`.aiq-step-row[data-round="${round}"]`);
      if (row) row.querySelector('.aiq-step-content').insertAdjacentHTML('beforeend',
        `<div class="aiq-step-obs">${escapeHtml(obs)}</div>`);
      if (_curTrace && _curTrace.steps.length) _curTrace.steps[_curTrace.steps.length - 1].observation = obs;
      scrollBottom();
    },
    onFinal: (tok) => {
      answerAcc += tok;
      shell.answerEl.innerHTML = renderAnswer(answerAcc, getValidRefNames()) + '<span class="chat-cursor">▍</span>';
      if (_curTrace) _curTrace.final = answerAcc;
      scrollBottom();
    },
    onFinalDone: (text) => {
      stopThinking(shell);
      shell.answerEl.innerHTML = renderAnswer(text, getValidRefNames());
      if (shell.reasonEl && !isFlash) shell.reasonEl.classList.add('is-done');
      if (_curTrace) _curTrace.final = text;
      // 显示审查中占位（review 回来覆盖）；history 在 send 末尾统一持久化
      shell.reviewEl.hidden = false;
      shell.reviewBody.innerHTML = '<div class="aiq-review-verdict warn">审查中…</div>';
    },
    onReview: (review) => {
      if (_curTrace) _curTrace.review = review;
      renderReview(shell.reviewEl, shell.reviewBody, review);
      scrollBottom();
    },
    onReviseStart: () => {
      reviseAcc = '';
      shell.answerEl.innerHTML = '<span class="aiq-revising-hint">审查未过，重写中…</span><span class="chat-cursor">▍</span>';
      scrollBottom();
    },
    onRevise: (tok) => {
      reviseAcc += tok;
      shell.answerEl.innerHTML = renderAnswer(reviseAcc, getValidRefNames()) + '<span class="chat-cursor">▍</span>';
      if (_curTrace) { _curTrace.revised = reviseAcc; _curTrace.final = reviseAcc; }
      scrollBottom();
    },
    onReviseDone: (text) => {
      shell.answerEl.innerHTML = renderAnswer(text, getValidRefNames());
      if (_curTrace) { _curTrace.revised = text; _curTrace.final = text; }
      const v = shell.reviewBody.querySelector('.aiq-review-verdict.fail');
      if (v) v.textContent = '审查未过·已重写';
      scrollBottom();
    },
    onDegraded: (text) => {
      stopThinking(shell);
      shell.answerEl.innerHTML = renderAnswer(text || '（未生成有效回答——模型输出无法解析为动作，且最终结论生成失败）', getValidRefNames());
    },
  };
}

async function send(text) {
  text = (text || '').trim();
  if (!text || _streaming) return;
  const input = document.getElementById('chat-input');
  if (input) input.value = '';
  appendMessage('user', escapeHtml(text));
  _history.push({ role: 'user', text });
  saveHistory();

  const shell = appendAssistantShell(null);
  if (!shell) return;
  _curTrace = { reason: '', reasonSegments: [], steps: [], final: '', review: null, revised: '' };
  _streaming = true;
  updateSendBtn();
  startThinking(shell);
  _abortCtl = new AbortController();
  const ctx = { question: text, context: buildContext(), signal: _abortCtl.signal, model: _thinkMode };
  let settled = false;
  try {
    await orchestrate(ctx, buildHooks(shell));
    settled = true;
  } catch (e) {
    stopThinking(shell);
    const aborted = e && e.name === 'AbortError';
    if (shell.answerEl) shell.answerEl.innerHTML += aborted
      ? ' <span class="chat-error">（已停止）</span>'
      : `<span class="chat-error">[请求失败] ${escapeHtml(e.message || e)}</span>`;
  } finally {
    // 统一在 review/revise 结束后持久化（onFinalDone 不再 push）
    if (_curTrace && (settled || _curTrace.final)) {
      _history.push({ role: 'assistant', trace: JSON.parse(JSON.stringify(_curTrace)) });
      saveHistory();
    }
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

function injectModeSwitch() {
  const head = document.querySelector('#chat-panel .chat-head');
  if (!head || document.getElementById('aiq-mode')) return;
  const seg = document.createElement('div');
  seg.id = 'aiq-mode';
  seg.className = 'aiq-mode';
  seg.innerHTML = `<button type="button" data-mode="pro" class="${_thinkMode === 'pro' ? 'is-active' : ''}" title="V4 Pro · 旗舰推理（深度思考，慢）">Pro 深度</button>`
    + `<button type="button" data-mode="flash" class="${_thinkMode === 'flash' ? 'is-active' : ''}" title="V4 Flash · 快速经济（无深度思考）">Flash 快</button>`;
  seg.addEventListener('click', (e) => {
    const b = e.target.closest('button[data-mode]');
    if (!b) return;
    _thinkMode = b.dataset.mode;
    localStorage.setItem(MODE_KEY, _thinkMode);
    seg.querySelectorAll('button').forEach((x) => x.classList.toggle('is-active', x.dataset.mode === _thinkMode));
  });
  head.insertBefore(seg, head.querySelector('.chat-head-spacer'));
}

function restoreHistory() {
  const list = document.getElementById('chat-messages');
  if (!list) return;
  list.innerHTML = '';
  for (const m of _history) {
    if (m.role === 'user') appendMessage('user', escapeHtml(m.text));
    else appendAssistantShell(m.trace);
  }
}

function clearChat() {
  _history = [];
  saveHistory();
  restoreHistory();
}

function onMsgClick(e) {
  const reason = e.target.closest('.aiq-reason.is-done');
  if (reason) { reason.classList.toggle('is-open'); return; }
  const chip = e.target.closest('.cite-chip');
  if (chip) { TOOLS.focus_zones({ names: [chip.dataset.ref] }); return; }
}

/** 主窗口入口。 */
export function initChatPanel() {
  const trigger = document.getElementById('chat-trigger');
  trigger?.addEventListener('click', () => {
    const panel = document.getElementById('chat-panel');
    if (!panel) return;
    const open = panel.classList.contains('is-collapsed');
    panel.classList.toggle('is-collapsed', !open);
    if (open) { injectModeSwitch(); restoreHistory(); setTimeout(() => document.getElementById('chat-input')?.focus(), 50); }
  });
  document.getElementById('chat-close')?.addEventListener('click', () => {
    document.getElementById('chat-panel')?.classList.add('is-collapsed');
  });
  document.getElementById('chat-clear')?.addEventListener('click', clearChat);
  const sendBtn = document.getElementById('chat-send');
  const input = document.getElementById('chat-input');
  sendBtn?.addEventListener('click', () => {
    if (_streaming && _abortCtl) { _abortCtl.abort(); return; }
    send(input?.value);
  });
  input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input.value); }
  });
  document.getElementById('chat-messages')?.addEventListener('click', onMsgClick);
  injectModeSwitch();
  restoreHistory();
}
