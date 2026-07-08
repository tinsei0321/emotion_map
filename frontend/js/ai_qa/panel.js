// ═══ panel.js — AI 问答 UI（底部滑出 · agent loop · 历史持久化 · 思考深度开关 · 动态状态）═══
import { orchestrate } from './harness.js';
import { buildContext, TOOLS, resetStepResults } from './tools.js';
import { getLayers, selectLayer } from '../state.js';
import { getLastUsage, resetCallStats, getCallStats } from './api.js';

const HISTORY_KEY = 'ai_qa_history_v1';
const ARCHIVE_KEY = 'ai_qa_archive_v1';
const MODE_KEY = 'ai_qa_think_mode';

// 动态思考状态文案（轮换，随机感；参考 Claude/ChatGPT "正在思考"动态提示）。
const THINK_PHRASES = ['正在思考', '正在分析', '正在计算', '正在构思', '正在比对数据', '正在归纳', '正在权衡证据', '正在检索线索', '正在梳理逻辑'];

let _streaming = false;
let _abortCtl = null;
let _history = loadHistory();
let _archive = loadArchive();
let _curTrace = null;
let _thinkMode = localStorage.getItem(MODE_KEY) || 'pro';   // 'pro' | 'flash'
let _thinkTimer = null;
let _userPinned = false;   // 用户上滑停跟；回到底部后恢复跟随

const CTX_BUDGET = 1000000;   // DeepSeek V4 Pro 上下文 1M token
const _CAP_C = 2 * Math.PI * 9;   // SVG 圆周长（r=9）
/** 容量圆圈（SVG 环）：填充=当前 prompt_tokens 占 1M 比例；深灰常显、≥60% 变橙；悬停 title 显百分比。 */
function updateContextCapacity(usage) {
  const el = document.getElementById('ctx-cap');
  if (!el) return;
  const fg = el.querySelector('.ctx-cap-fg');
  if (!usage || !usage.prompt_tokens) {
    el.classList.remove('warn');
    if (fg) fg.setAttribute('stroke-dashoffset', _CAP_C.toFixed(2));
    el.setAttribute('title', '上下文容量（V4 Pro 1M）');
    return;
  }
  const ratio = Math.min(usage.prompt_tokens / CTX_BUDGET, 1);
  el.classList.toggle('warn', ratio >= 0.6);
  if (fg) fg.setAttribute('stroke-dashoffset', (_CAP_C * (1 - ratio)).toFixed(2));
  const pct = (ratio * 100).toFixed(ratio < 0.1 ? 1 : 0);
  el.setAttribute('title', `上下文 ${usage.prompt_tokens.toLocaleString()} / 1,000,000 token · ${pct}%`);
}

function loadHistory() {
  try { const v = localStorage.getItem(HISTORY_KEY); return v ? JSON.parse(v) : []; }
  catch (_) { return []; }
}
function saveHistory() {
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(_history)); } catch (_) {}
}
function loadArchive() {
  try { const v = localStorage.getItem(ARCHIVE_KEY); return v ? JSON.parse(v) : []; }
  catch (_) { return []; }
}
function saveArchive() {
  try { localStorage.setItem(ARCHIVE_KEY, JSON.stringify(_archive)); } catch (_) {}
}
function _titleOf(hist) {
  const u = hist.find((h) => h.role === 'user');
  return u && u.text ? u.text.slice(0, 30) : '会话';
}
/** 切换到存档会话：当前 _history 先存档，再加载目标会话。 */
function switchSession(id) {
  if (_streaming) return;
  if (_history.length) {
    _archive.unshift({ id: 's' + Date.now(), title: _titleOf(_history), history: [..._history], createdAt: Date.now() });
  }
  const idx = _archive.findIndex((s) => s.id === id);
  if (idx >= 0) { _history = _archive[idx].history; _archive.splice(idx, 1); }
  saveArchive(); saveHistory(); restoreHistory();
  updateContextCapacity(null);
  document.getElementById('chat-history-pop')?.remove();
}
function deleteSession(id) {
  _archive = _archive.filter((s) => s.id !== id);
  saveArchive();
  document.getElementById('chat-history-pop')?.remove();
  toggleHistoryDropdown();
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function scrollBottom() {
  const list = document.getElementById('chat-messages');
  if (list) list.scrollTop = list.scrollHeight;
}
function nearBottom(list) {
  return list.scrollHeight - list.scrollTop - list.clientHeight < 48;
}
/** 流式增量时用：用户在底才跟随，上滑停跟（业界标准）。 */
function autoScroll() {
  if (!_userPinned) scrollBottom();
}
function setBackBtn(show) {
  const b = document.getElementById('chat-back-btn');
  if (b) b.hidden = !show;
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
  // D2: {{focus|show|inspect:target}} → 可点操作按钮（点击触发对应 TOOLS：飞到/显示图层/深读归因）
  html = html.replace(/\{\{(focus|show|inspect):([^}]+)\}\}/g, (_, act, tgt) => {
    const t = tgt.trim();
    const lbl = act === 'focus' ? '飞到 ' + t : act === 'show' ? '显示 ' + t : '深读 ' + t;
    return `<button class="chat-action-btn" data-action="${act}" data-target="${escapeHtml(t)}" type="button">${escapeHtml(lbl)}</button>`;
  });
  return html;
}

const _DOMAIN_LABEL = { urban_planning: '城市规划', urban_renewal: '城市更新', urban_operation: '城市运营', urban_governance: '城市治理' };
const _SCALE_LABEL = { macro: '宏观（片区/城区）', meso: '中观（街道/单元）', micro: '微观（点位）' };
const _STRATEGY_LABEL = { ready: '数据齐全', fallback_annotated: '软缺口·降级标注', request_upload: '硬缺口·需上传' };

/** MM月DD日 HH:MM（不写星期）。 */
function formatTs(ts) {
  const d = ts ? new Date(ts) : new Date();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  const hh = String(d.getHours()).padStart(2, '0');
  const mi = String(d.getMinutes()).padStart(2, '0');
  return `${mm}月${dd}日 ${hh}:${mi}`;
}

/** 完毕戳（回答完毕 + 版本 + 时间戳）；存 trace.doneAt 供历史恢复。 */
function _fmtTokens(n) { return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n); }
function stampDone(shell) {
  if (_curTrace) _curTrace.doneAt = Date.now();
  if (shell && shell.footerEl) {
    const secs = _curTrace && _curTrace.startedAt ? Math.max(1, Math.round((_curTrace.doneAt - _curTrace.startedAt) / 1000)) : 0;
    const cs = getCallStats();
    shell.footerEl.hidden = false;
    shell.footerEl.textContent = `回答完毕 · 用时 ${secs}s · 用量 ${_fmtTokens(cs.total)} token / ${cs.calls} 次 · 情绪地图 v1.0 · ${formatTs(_curTrace && _curTrace.doneAt)}`;
  }
}

/** 渲染问题理解卡（DIAGNOSE）：domain/scale/decision/outlet + strategy 徽章 + method。 */
function renderDiagnoseCard(el, card) {
  if (!el) return;
  if (!card || card.degraded) { el.hidden = true; return; }
  el.hidden = false;
  const dom = (card.domain_lens || []).map((k) => _DOMAIN_LABEL[k] || k).filter(Boolean);
  const strat = (card.data_plan && card.data_plan.strategy) || 'ready';
  const method = (card.method || []).filter(Boolean);
  el.classList.toggle('is-upload', strat === 'request_upload');
  const chip = (t) => `<span class="aiq-diag-chip">${escapeHtml(t)}</span>`;
  el.innerHTML = `<div class="aiq-card-head">问题理解</div>`
    + `<div class="aiq-diag-row">${[dom.join('/'), _SCALE_LABEL[card.scale] || card.scale, card.decision_type, card.outlet].filter(Boolean).map(chip).join('')}</div>`
    + `<div class="aiq-diag-strategy ${strat}"><span class="aiq-diag-strat-tag">${_STRATEGY_LABEL[strat] || strat}</span>${
      strat === 'request_upload' ? '（关键数据缺失，已请用户上传）'
      : strat === 'fallback_annotated' ? '（结论将标注口径局限）' : ''}</div>`
    + (method.length ? `<div class="aiq-diag-method">方法：${escapeHtml(method.join(' → '))}</div>` : '');
}

/** 渲染软缺口口径标注（fallback_annotated），append 到答案后。 */
function renderCaliber(shell, gap) {
  if (!shell || !shell.caliberEl) return;
  const g = (Array.isArray(gap) ? gap : [gap]).filter(Boolean);
  shell.caliberEl.hidden = false;
  shell.caliberEl.innerHTML = `<div class="aiq-card-head">口径说明</div>`
    + `<div>本结论基于现有情绪数据给出${g.length ? '，缺：' + escapeHtml(g.join('、')) : ''}，属情绪视角的参考性结论，非综合评估。</div>`;
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

/** 渲染审查状态区（七条 ✓/△/✕ + 整体结论）。 */
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

/** 思考 dock（单例，挂 #chat-suggest 槽，永贴底不被顶走）。 */
function dockEl() { return document.getElementById('aiq-thinking-dock'); }

/** 动态思考指示器：轮换文案 + 跳动点 + 阶段 chip。 */
function startThinking() {
  const d = dockEl();
  if (d) { d.hidden = false; setPhase('诊断'); }
  const txt = d && d.querySelector('.aiq-thinking-text');
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
function stopThinking() {
  if (_thinkTimer) { clearInterval(_thinkTimer); _thinkTimer = null; }
  const d = dockEl();
  if (d) d.hidden = true;
}
/** 阶段进度 chip 点亮（诊断/思考/检索/生成/审查）。 */
function setPhase(chip) {
  const d = dockEl();
  if (!d) return;
  d.querySelectorAll('.aiq-phase-chips span').forEach((s) => s.classList.toggle('active', s.dataset.phase === chip));
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
    <div class="aiq-card aiq-card-diagnose" hidden></div>
    <div class="aiq-reason ${isFlash ? 'is-flash' : ''}" ${hasReason ? '' : 'hidden'}><div class="aiq-reason-head">${reasonHead}</div><div class="aiq-reason-body"></div></div>
    <div class="aiq-steps" ${trace && trace.steps && trace.steps.length ? '' : 'hidden'}><div class="aiq-steps-head">解题过程（Agent Loop）</div></div>
    <div class="aiq-review" ${trace && trace.review ? '' : 'hidden'}><div class="aiq-review-head">审查</div><div class="aiq-review-body"></div></div>
    <div class="aiq-step aiq-step-final"><span class="aiq-step-tag">结论</span><div class="aiq-answer"><span class="aiq-answer-stream"></span><span class="chat-cursor" hidden>▍</span></div></div>
    <div class="aiq-card aiq-card-caliber" hidden></div>
    <div class="aiq-answer-footer" hidden></div>
  </div>`;
  list.appendChild(el);
  const shell = {
    diagnoseEl: el.querySelector('.aiq-card-diagnose'),
    reasonEl: el.querySelector('.aiq-reason'),
    reasonBody: el.querySelector('.aiq-reason-body'),
    stepsEl: el.querySelector('.aiq-steps'),
    reviewEl: el.querySelector('.aiq-review'),
    reviewBody: el.querySelector('.aiq-review-body'),
    answerEl: el.querySelector('.aiq-answer'),
    answerStreamEl: el.querySelector('.aiq-answer-stream'),
    caliberEl: el.querySelector('.aiq-card-caliber'),
    footerEl: el.querySelector('.aiq-answer-footer'),
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
    if (trace.diagnose) renderDiagnoseCard(shell.diagnoseEl, trace.diagnose);
    if (trace.caliber) renderCaliber(shell, trace.caliber);
    if (trace.doneAt && shell.footerEl) {
      shell.footerEl.hidden = false;
      shell.footerEl.textContent = '回答完毕 · 情绪地图测试版 v1.0 · ' + formatTs(trace.doneAt);
    }
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
  const reasonSegs = {};   // round -> text
  let streamAcc = '';      // onFinal/onRevise 共用流缓冲（RAF drain，治 O(n²) 每 token marked.parse）
  let streamRaf = 0;
  let reasonRaf = 0;
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
  /** 流式期裸文本节点（流末 onFinalDone/onReviseDone 才 marked.parse 一次）。 */
  function ensureStream() {
    if (!shell.answerEl.querySelector('.aiq-answer-stream')) {
      shell.answerEl.innerHTML = '<span class="aiq-answer-stream"></span><span class="chat-cursor">▍</span>';
    }
    return shell.answerEl.querySelector('.aiq-answer-stream');
  }
  function drainStream() {
    streamRaf = 0;
    const s = ensureStream();
    s.textContent = streamAcc;
    const cur = shell.answerEl.querySelector('.chat-cursor');
    if (cur) cur.hidden = false;
    autoScroll();
  }
  function cancelStream() { if (streamRaf) { cancelAnimationFrame(streamRaf); streamRaf = 0; } }

  return {
    onDiagnose: (card) => {
      if (_curTrace) _curTrace.diagnose = card;
      renderDiagnoseCard(shell.diagnoseEl, card);
      if (card && !card.degraded) setPhase('思考');
    },
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
      // RAF 合流：每帧最多写一次 textContent（不再每 token querySelector+textContent）
      if (reasonRaf) return;
      reasonRaf = requestAnimationFrame(() => {
        reasonRaf = 0;
        const body = shell.reasonBody.querySelector(`.aiq-reason-segment[data-round="${r}"] .aiq-reason-seg-body`);
        if (body) body.textContent = reasonSegs[r];
        flushReasonSegs();
        autoScroll();
      });
    },
    onRound: () => {},
    onThought: (thought, round) => {
      shell.stepsEl.hidden = false;
      renderStepRow(shell.stepsEl, round, thought, null, null);
      if (_curTrace) _curTrace.steps.push({ round, thought, action: null, observation: null });
      setPhase('思考');
      autoScroll();
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
      setPhase('检索');
      autoScroll();
    },
    onFinal: (tok) => {
      setPhase('生成');
      streamAcc += tok;
      if (_curTrace) _curTrace.final = streamAcc;
      if (!streamRaf) streamRaf = requestAnimationFrame(drainStream);
    },
    onFinalDone: (text) => {
      cancelStream();
      streamAcc = text || '';
      stopThinking();
      updateContextCapacity(getLastUsage());
      shell.answerEl.innerHTML = renderAnswer(text, getValidRefNames());
      if (shell.reasonEl && !isFlash) shell.reasonEl.classList.add('is-done');
      if (_curTrace) _curTrace.final = text;
      // 显示审查中占位（review 回来覆盖）；history 在 send 末尾统一持久化
      shell.reviewEl.hidden = false;
      shell.reviewBody.innerHTML = '<div class="aiq-review-verdict warn">审查中…</div>';
      setPhase('审查');
    },
    onReview: (review) => {
      if (_curTrace) _curTrace.review = review;
      renderReview(shell.reviewEl, shell.reviewBody, review);
      setPhase('审查');
      autoScroll();
    },
    onReviseStart: () => {
      cancelStream();
      streamAcc = '';
      setPhase('生成');
      shell.answerEl.innerHTML = '<span class="aiq-revising-hint">审查未过，重写中…</span><span class="chat-cursor">▍</span>';
      autoScroll();
    },
    onRevise: (tok) => {
      streamAcc += tok;
      if (_curTrace) { _curTrace.revised = streamAcc; _curTrace.final = streamAcc; }
      if (!streamRaf) streamRaf = requestAnimationFrame(drainStream);
    },
    onReviseDone: (text) => {
      cancelStream();
      streamAcc = text || '';
      shell.answerEl.innerHTML = renderAnswer(text, getValidRefNames());
      if (_curTrace) { _curTrace.revised = text; _curTrace.final = text; }
      const v = shell.reviewBody.querySelector('.aiq-review-verdict.fail');
      if (v) v.textContent = '审查未过·已重写';
      autoScroll();
    },
    onDegraded: (text) => {
      cancelStream();
      stopThinking();
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
  _curTrace = { reason: '', reasonSegments: [], steps: [], final: '', review: null, revised: '', diagnose: null, caliber: null, startedAt: Date.now(), doneAt: null };
  resetCallStats();
  resetStepResults();
  _streaming = true;
  updateSendBtn();
  startThinking();
  _abortCtl = new AbortController();
  // 多轮上下文：前几轮 user/assistant.final 作为历史带给 LLM（stages.js 拼进 messages）
  const _hist = [];
  for (const h of _history.slice(0, -1)) {   // 排除当前刚 push 的 user
    if (h.role === 'user') _hist.push({ role: 'user', content: h.text });
    else if (h.role === 'assistant' && h.trace && h.trace.final) _hist.push({ role: 'assistant', content: h.trace.final });
  }
  const ctx = { question: text, context: await buildContext(), signal: _abortCtl.signal, model: _thinkMode, history: _hist.slice(-10) };
  let settled = false;
  try {
    await orchestrate(ctx, buildHooks(shell));
    settled = true;
    // C：软缺口降级口径标注（fallback_annotated）
    const strat = _curTrace && _curTrace.diagnose && _curTrace.diagnose.data_plan && _curTrace.diagnose.data_plan.strategy;
    if (strat === 'fallback_annotated') {
      _curTrace.caliber = _curTrace.diagnose.data_plan.gap || [];
      renderCaliber(shell, _curTrace.caliber);
    }
    stampDone(shell);   // D3：回答完毕 + 版本 + 时间戳（含 request_upload 短路 / degraded 终态）
  } catch (e) {
    stopThinking();
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
    // L3 情境日志（自成长闭环原料；fire-and-forget，失败静默不阻塞交付）
    if (_curTrace) {
      fetch('/api/v1/aiqa/episode', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text, diagnose: _curTrace.diagnose, final: _curTrace.final, review: _curTrace.review, ok: settled }),
      }).catch(() => {});
    }
    _streaming = false;
    _abortCtl = null;
    updateSendBtn();
  }
}

const _SVG_SEND = '<svg viewBox="0 0 24 24" width="18" height="18"><path d="M12 4l8 8h-5v8h-6v-8H4z" fill="currentColor"/></svg>';
const _SVG_STOP = '<svg viewBox="0 0 24 24" width="14" height="14"><rect x="5" y="5" width="14" height="14" rx="3" fill="currentColor"/></svg>';
function updateSendBtn() {
  const btn = document.getElementById('chat-send');
  if (!btn) return;
  if (_streaming) { btn.innerHTML = _SVG_STOP; btn.classList.add('is-stop'); btn.title = '停止'; }
  else { btn.innerHTML = _SVG_SEND; btn.classList.remove('is-stop'); btn.title = '发送'; }
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

/** 历史记录下拉：列存档会话 + 当前会话；点击切换、垃圾桶删除。 */
function toggleHistoryDropdown() {
  const existing = document.getElementById('chat-history-pop');
  if (existing) { existing.remove(); return; }
  const pop = document.createElement('div');
  pop.id = 'chat-history-pop';
  pop.className = 'chat-pop';
  const hasCur = _history.some((h) => h.role === 'user');
  if (!_archive.length && !hasCur) {
    pop.innerHTML = '<div class="chat-pop-empty">暂无历史会话</div>';
  } else {
    const items = [];
    if (hasCur) items.push({ id: '__current__', title: _titleOf(_history) + '（当前）', isCurrent: true });
    _archive.forEach((s) => items.push({ id: s.id, title: s.title, isCurrent: false }));
    pop.innerHTML = items.map((it) =>
      `<div class="chat-pop-item${it.isCurrent ? ' is-current' : ''}"><span class="chat-pop-txt" data-id="${it.id}">${escapeHtml(it.title)}</span>` +
      (it.isCurrent ? '' : `<button class="chat-pop-del" data-id="${it.id}" title="删除该会话"><svg viewBox="0 0 24 24" width="13" height="13"><path d="M5 7h14M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M7 7l1 13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1l1-13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>`) +
      `</div>`
    ).join('');
    pop.querySelectorAll('.chat-pop-txt').forEach((el) => {
      el.style.cursor = el.dataset.id === '__current__' ? 'default' : 'pointer';
      el.addEventListener('click', () => { if (el.dataset.id !== '__current__') switchSession(el.dataset.id); });
    });
    pop.querySelectorAll('.chat-pop-del').forEach((b) => b.addEventListener('click', () => deleteSession(b.dataset.id)));
  }
  const head = document.querySelector('#chat-panel .chat-head');
  if (head) head.appendChild(pop);
  setTimeout(() => {
    const onDoc = (e) => { if (!pop.contains(e.target) && !e.target.closest('#chat-history')) { pop.remove(); document.removeEventListener('click', onDoc); } };
    document.addEventListener('click', onDoc);
  }, 0);
}

function onMsgClick(e) {
  const reason = e.target.closest('.aiq-reason.is-done');
  if (reason) { reason.classList.toggle('is-open'); return; }
  const chip = e.target.closest('.cite-chip');
  if (chip) { TOOLS.focus_zones({ names: [chip.dataset.ref] }); return; }
  const act = e.target.closest('.chat-action-btn');
  if (act) {
    const op = act.dataset.action, tgt = act.dataset.target;
    if (op === 'focus') TOOLS.focus_zones({ names: [tgt] });
    else if (op === 'inspect') TOOLS.inspect_zone({ name: tgt });
    else if (op === 'show') {
      const l = getLayers().find((x) => x.name === tgt || (x.name && (x.name.includes(tgt) || tgt.includes(x.name))));
      if (l && l.id) selectLayer(l.id);
    }
    return;
  }
}

/** 挂思考 dock（#chat-suggest 槽，单例贴底）+ 回到底部浮钮 + 滚动停跟。
 *  注意：restoreHistory() 会清空 #chat-messages，带走 back-btn；故 back-btn 每次（缺失时）重挂，
 *  scroll 监听用 dataset 守卫只挂一次。须在 restoreHistory 之后调用。 */
function mountChatChrome() {
  const suggest = document.getElementById('chat-suggest');
  if (suggest && !document.getElementById('aiq-thinking-dock')) {
    suggest.innerHTML = '<div class="aiq-thinking-dock" id="aiq-thinking-dock" hidden>'
      + '<div class="aiq-thinking-row"><span class="aiq-thinking-text">正在思考…</span><span class="aiq-dots"><i></i><i></i><i></i></span></div>'
      + '<div class="aiq-phase-chips">'
      + ['诊断', '思考', '检索', '生成', '审查'].map((c) => `<span data-phase="${c}">${c}</span>`).join('')
      + '</div></div>';
  }
  const list = document.getElementById('chat-messages');
  if (!list) return;
  if (!list.dataset.aiqScroll) {                 // scroll 监听只挂一次（防多次开面板累积）
    list.dataset.aiqScroll = '1';
    list.addEventListener('scroll', () => {
      _userPinned = !nearBottom(list);
      const b = document.getElementById('chat-back-btn');
      if (b) b.hidden = _userPinned ? false : true;
    });
  }
  if (!document.getElementById('chat-back-btn')) { // 被 restoreHistory 清走则重挂
    const btn = document.createElement('button');
    btn.id = 'chat-back-btn';
    btn.type = 'button';
    btn.className = 'chat-back-btn';
    btn.hidden = true;
    btn.textContent = '回到底部 ↓';
    btn.addEventListener('click', () => { _userPinned = false; scrollBottom(); btn.hidden = true; });
    list.appendChild(btn);
  }
}

/** 主窗口入口。 */
export function initChatPanel() {
  const trigger = document.getElementById('chat-trigger');
  trigger?.addEventListener('click', () => {
    const panel = document.getElementById('chat-panel');
    if (!panel) return;
    const open = panel.classList.contains('is-collapsed');
    panel.classList.toggle('is-collapsed', !open);
    if (open) {
      injectModeSwitch(); mountChatChrome();
      // 流式中不 restoreHistory：它会清空 #chat-messages 重建，破坏进行中的 shell（hooks 指向脱离 DOM 的旧元素 → 回答停住）
      if (!_streaming) restoreHistory();
      setTimeout(() => document.getElementById('chat-input')?.focus(), 50);
    }
  });
  document.getElementById('chat-close')?.addEventListener('click', () => {
    document.getElementById('chat-panel')?.classList.add('is-collapsed');
  });
  document.getElementById('chat-new')?.addEventListener('click', () => {
    if (_streaming) return;   // 流式中忽略
    if (_history.length) {   // 当前会话存档
      _archive.unshift({ id: 's' + Date.now(), title: _titleOf(_history), history: [..._history], createdAt: Date.now() });
      saveArchive();
    }
    clearChat();
    updateContextCapacity(null);
    document.getElementById('chat-input')?.focus();
  });
  document.getElementById('chat-history')?.addEventListener('click', (e) => { e.stopPropagation(); toggleHistoryDropdown(); });
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
  mountChatChrome();
}
