// ═══ panel.js — AI 问答 UI（主窗口底部滑出 · agent loop · 历史持久化）═══
// 还原 B1 底部滑出形态（删独立窗 + 跨窗口协议），panel 直调主窗口（map/state/tools）。
// agent loop 思考流：reasoning 跨轮累积（实时）+ 每轮 thought/action/observation 逐行追加。
// 问答历史 localStorage 持久化，打开 panel 恢复。
import { orchestrate } from './harness.js';
import { buildContext, TOOLS } from './tools.js';

const HISTORY_KEY = 'ai_qa_history_v1';
const MAX_ROUNDS_HINT = 8;

let _streaming = false;
let _abortCtl = null;
let _history = loadHistory();
let _curTrace = null;

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
function renderAnswer(text) {
  let html = window.marked ? window.marked.parse(text) : `<p>${escapeHtml(text).replace(/\n/g, '<br>')}</p>`;
  html = html.replace(/\[ref:([^\]]+)\]/g, (_, name) =>
    `<button class="cite-chip" data-ref="${escapeHtml(name)}" type="button">${escapeHtml(name)}</button>`);
  return html;
}

/** assistant 消息骨架（思考链 + 解题步骤 + 结论）。trace 非空 = 历史恢复（直接填）。 */
function appendAssistantShell(trace) {
  const list = document.getElementById('chat-messages');
  if (!list) return null;
  const el = document.createElement('div');
  el.className = 'chat-msg chat-msg-assistant';
  el.innerHTML = `<div class="chat-bubble">
    <div class="aiq-reason" ${trace && trace.reason ? '' : 'hidden'}><div class="aiq-reason-head">▸ 思考过程（Pro · 实时）</div><div class="aiq-reason-body"></div></div>
    <div class="aiq-steps" ${trace && trace.steps && trace.steps.length ? '' : 'hidden'}><div class="aiq-steps-head">解题过程（Agent Loop）</div></div>
    <div class="aiq-step aiq-step-final"><span class="aiq-step-tag">结论</span><div class="aiq-answer"><span class="chat-cursor">▍</span></div></div>
  </div>`;
  list.appendChild(el);
  const shell = {
    reasonEl: el.querySelector('.aiq-reason'),
    reasonBody: el.querySelector('.aiq-reason-body'),
    stepsEl: el.querySelector('.aiq-steps'),
    answerEl: el.querySelector('.aiq-answer'),
  };
  if (trace) {
    if (trace.reason) shell.reasonBody.textContent = trace.reason;
    if (trace.reason) shell.reasonEl.classList.add('is-done');
    (trace.steps || []).forEach((s) => renderStepRow(shell.stepsEl, s.round, s.thought, s.action, s.observation));
    if (trace.final) shell.answerEl.innerHTML = renderAnswer(trace.final);
    else shell.answerEl.innerHTML = '<span class="chat-error">（未生成结论）</span>';
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
  let reasonAcc = '';
  let answerAcc = '';
  return {
    onReason: (tok) => {
      reasonAcc += tok;
      shell.reasonEl.hidden = false;
      shell.reasonBody.textContent = reasonAcc;
      if (_curTrace) _curTrace.reason = reasonAcc;
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
      shell.answerEl.innerHTML = renderAnswer(answerAcc) + '<span class="chat-cursor">▍</span>';
      if (_curTrace) _curTrace.final = answerAcc;
      scrollBottom();
    },
    onFinalDone: (text) => {
      shell.answerEl.innerHTML = renderAnswer(text);
      if (shell.reasonEl && reasonAcc) shell.reasonEl.classList.add('is-done');
      if (_curTrace) {
        _curTrace.final = text;
        _history.push({ role: 'assistant', trace: JSON.parse(JSON.stringify(_curTrace)) });
        saveHistory();
      }
    },
    onDegraded: (text) => {
      shell.answerEl.innerHTML = renderAnswer(text || '（未生成有效回答——模型输出无法解析为动作）');
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
  _curTrace = { reason: '', steps: [], final: '' };
  _streaming = true;
  updateSendBtn();
  _abortCtl = new AbortController();
  const ctx = { question: text, context: buildContext(), signal: _abortCtl.signal };
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

/** 主窗口入口：绑事件 + 恢复历史。问答按钮 #chat-trigger 切换 panel 显隐。 */
export function initChatPanel() {
  const trigger = document.getElementById('chat-trigger');
  trigger?.addEventListener('click', () => {
    const panel = document.getElementById('chat-panel');
    if (!panel) return;
    const open = panel.classList.contains('is-collapsed');
    panel.classList.toggle('is-collapsed', !open);
    if (open) { restoreHistory(); setTimeout(() => document.getElementById('chat-input')?.focus(), 50); }
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
  restoreHistory();
}
