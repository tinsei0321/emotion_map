// ═══ panel.js — AI 问答 UI（底部滑出 · agent loop · 历史持久化 · 思考深度开关 · 动态状态）═══
import { orchestrate } from './harness.js';
import { buildContext, TOOLS, resetStepResults, resetCurrentResults, cleanupConsumedResults } from './tools.js';
import { getLayers, selectLayer, getSelectedLayer } from '../state.js';
import { getLastUsage, resetCallStats, getCallStats } from './api.js';

const HISTORY_KEY = 'ai_qa_history_v1';
const ARCHIVE_KEY = 'ai_qa_archive_v1';
const MODE_KEY = 'ai_qa_think_mode';
const COLLAPSE_KEY = 'ai_qa_emc_collapsed';   // EMC 折叠态持久化（收起=只剩一行输入触发条）

// 动态思考状态文案（轮换，随机感；参考 Claude/ChatGPT "正在思考"动态提示）。
const THINK_PHRASES = ['正在思考', '正在分析', '正在计算', '正在构思', '正在比对数据', '正在归纳', '正在权衡证据', '正在检索线索', '正在梳理逻辑'];

let _streaming = false;
let _abortCtl = null;
let _history = loadHistory();
let _archive = loadArchive();
let _curTrace = null;
let _thinkMode = localStorage.getItem(MODE_KEY) || 'pro';   // 'pro' | 'flash'
let _thinkTimer = null;
let _emcCollapsed = localStorage.getItem(COLLAPSE_KEY) === '1';   // EMC 折叠态（收起→一行输入触发条，点击展开）
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

// ── EMC 智能高度调度（三档 compact/comfort/expand + 手动基线回退）──
//   档位按窗口高算 px；setEmcMode 改 --emc-h；手动拖拽写 --emc-h-user（sidebar.js initVDrag），relax 时回落基线。
//   拖拽中(body.dragging)不自动调，防打架；流式中(_streaming)不让位。
//   EMC_MIN = 320：chat-head(40)+input-area(130)+chat-messages(≥150) 的下限。低于此 chat-messages 会被挤没
//   （曾 compact=160 致 chat-messages 塌缩到 24px→对话空白 bug，5.49）。5 处下限须同步：本文件 2 处 + sidebar.js 2 处 + layout.css min-height。
const EMC_MIN = 320;
function _emcTierPx() {
  const win = window.innerHeight;
  return { compact: EMC_MIN, comfort: Math.round(win / 2), expand: Math.round(win * 2 / 3) };
}
function _emcClamp(px) {
  const win = window.innerHeight;
  return Math.max(EMC_MIN, Math.min(win - win / 3, px));
}
function _emcUserBaselinePx() {
  const v = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--emc-h-user'));
  return v > 0 ? v : 0;
}
function setEmcMode(mode, { relax = false } = {}) {
  if (document.body.classList.contains('dragging')) return;
  if (_emcCollapsed) return;   // 折叠态：--emc-h 由 .is-collapsed 局部覆盖，跳过自动档
  let px = relax ? (_emcUserBaselinePx() || _emcTierPx()[mode]) : _emcTierPx()[mode];
  document.documentElement.style.setProperty('--emc-h', `${_emcClamp(px)}px`);
}
/** 提交时：当前 < comfort 则升 comfort（需求 2）。 */
function ensureEmcHeight() {
  if (_emcCollapsed) return;
  const panel = document.getElementById('emc-panel');
  const cur = panel ? panel.offsetHeight : 0;
  if (cur < _emcTierPx().comfort - 8) setEmcMode('comfort');
}
/** 流式后回落：有手动基线回基线，无则回 comfort（不留在 expand）。 */
function relaxEmc() {
  if (_emcCollapsed) return;
  const base = _emcUserBaselinePx();
  if (base) document.documentElement.style.setProperty('--emc-h', `${_emcClamp(base)}px`);
  else setEmcMode('comfort');
}
/** EMC 折叠/展开切换：折叠→.is-collapsed（局部覆盖 --emc-h=48px，藏 head/view/foot，留一行输入触发条）；
 *  展开→移除类 + 回落正常档。持久化到 localStorage。 */
function setEmcCollapsed(c) {
  _emcCollapsed = !!c;
  const panel = document.getElementById('emc-panel');
  if (panel) panel.classList.toggle('is-collapsed', _emcCollapsed);
  try { localStorage.setItem(COLLAPSE_KEY, _emcCollapsed ? '1' : '0'); } catch (_) {}
  if (!_emcCollapsed) relaxEmc();   // 展开：回落 comfort/用户基线
}
let _crowdedRaf = 0;
function _checkCrowded() {
  if (_streaming) return;
  if (_emcCollapsed) return;   // 折叠态不让位
  const layerCount = document.querySelectorAll('#layer-list .layer-row').length;
  if (layerCount === 0) { setEmcMode('comfort'); return; }   // 无图层（含 import 空态）→ comfort，不误判 operate 占位为拥挤
  const op = document.querySelector('.lp-zone-operate');
  if (!op || op.clientHeight <= 0) return;
  const crowded = op.scrollHeight > op.clientHeight * 0.92;
  if (crowded) setEmcMode('compact');
  else if (layerCount <= 3) setEmcMode('comfort');
}
function _scheduleCrowdedCheck() {
  if (_crowdedRaf) return;
  _crowdedRaf = requestAnimationFrame(() => { _crowdedRaf = 0; _checkCrowded(); });
}
function setupEmcHeightObservers() {
  const list = document.getElementById('layer-list');
  if (list && !list._emcObs) {
    list._emcObs = new MutationObserver(() => _scheduleCrowdedCheck());
    list._emcObs.observe(list, { childList: true, subtree: true });
    list.addEventListener('click', () => _scheduleCrowdedCheck());   // 点层→上层焦点→重算
  }
  _scheduleCrowdedCheck();
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
  if (_view === 'history') renderHistoryList(document.getElementById('emc-history-search')?.value || '');
}
function deleteSession(id) {
  _archive = _archive.filter((s) => s.id !== id);
  saveArchive();
  if (_view === 'history') renderHistoryList(document.getElementById('emc-history-search')?.value || '');
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
  const w = list.querySelector('.emc-welcome'); if (w) w.remove();   // 有消息即清空态欢迎
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
  updateReasonMeta(shell);
}

/** Thinking 头：答完显「Thought for Ns · Nk token」（折叠态可见）。trace 缺省=实时 _curTrace。 */
function updateReasonMeta(shell, trace) {
  if (!shell || !shell.reasonEl || shell.reasonEl.classList.contains('is-flash')) return;
  const t = trace || _curTrace;
  const title = shell.reasonEl.querySelector('.aiq-reason-title');
  const meta = shell.reasonEl.querySelector('.aiq-reason-meta');
  const secs = t && t.startedAt && t.doneAt ? Math.max(1, Math.round((t.doneAt - t.startedAt) / 1000)) : 0;
  if (title) title.textContent = secs ? `Thought for ${secs}s` : 'Thinking…';
  if (meta) {
    const cs = trace ? { total: 0 } : getCallStats();   // 仅 live 取实时 token；历史会话不存 token
    meta.textContent = cs.total ? `· ${_fmtTokens(cs.total)} token` : '';
  }
}

/** 代码块加 hover 复制按钮（marked 渲染后后处理）。 */
function enhanceCodeBlocks(el) {
  if (!el) return;
  el.querySelectorAll('pre').forEach((pre) => {
    if (pre.querySelector('.emc-code-copy')) return;
    const btn = document.createElement('button');
    btn.className = 'emc-code-copy';
    btn.type = 'button';
    btn.textContent = '复制';
    btn.addEventListener('click', () => {
      const code = pre.querySelector('code');
      navigator.clipboard?.writeText(code ? code.innerText : pre.innerText);
      btn.textContent = '✓';
      setTimeout(() => { btn.textContent = '复制'; }, 1200);
    });
    pre.appendChild(btn);
  });
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
  setEmcMode('expand');
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
  const hasReason = !!(trace && (trace.reasonSegments?.length || trace.reason));
  el.innerHTML = `<div class="chat-bubble">
    <div class="aiq-card aiq-card-diagnose" hidden></div>
    <div class="aiq-reason ${isFlash ? 'is-flash' : ''}" ${hasReason ? '' : 'hidden'}><div class="aiq-reason-head"><span class="aiq-reason-title">${isFlash ? 'Flash · 直接作答' : 'Thinking…'}</span><span class="aiq-reason-meta"></span></div><div class="aiq-reason-body"></div></div>
    <div class="aiq-steps" ${trace && trace.steps && trace.steps.length ? '' : 'hidden'}><div class="aiq-steps-head">工具调用（Agent Loop）</div></div>
    <div class="aiq-review" ${trace && trace.review ? '' : 'hidden'}><div class="aiq-review-head">审查</div><div class="aiq-review-body"></div></div>
    <div class="aiq-step aiq-step-final"><span class="aiq-step-tag">结论</span><div class="aiq-answer"><span class="aiq-answer-stream"></span><span class="chat-cursor" hidden>▍</span></div></div>
    <div class="aiq-card aiq-card-caliber" hidden></div>
    <div class="aiq-answer-footer" hidden></div>
  </div>
  <div class="emc-msg-actions"><button class="emc-copy-btn" type="button" title="复制回答"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h8"/></svg></button></div>`;
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
    (trace.steps || []).forEach((s) => renderToolCard(shell.stepsEl, s.round, s.thought, s.action, s.observation));
    if (trace.review) renderReview(shell.reviewEl, shell.reviewBody, trace.review);
    shell.answerEl.innerHTML = trace.final ? renderAnswer(trace.final, getValidRefNames()) : '<span class="chat-error">（未生成结论）</span>';
    enhanceCodeBlocks(shell.answerEl);
    updateReasonMeta(shell, trace);
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
/** 工具目标摘要（取 params 里最显眼的 name/layer/zone/preset 字段）。 */
function actionTargetSummary(action) {
  if (!action || !action.params) return '';
  const p = action.params;
  const key = Object.keys(p).find((k) => /name|layer|zone|target|preset|level|field|range/i.test(k)) || Object.keys(p)[0];
  if (!key) return '';
  const v = p[key];
  const s = Array.isArray(v) ? v.slice(0, 3).join(',') : String(v);
  return s ? '· ' + s.slice(0, 40) : '';
}
/** 工具调用卡（Claude Code 式：头=工具名+目标+状态，体=thought/observation 可折叠）。
 *  增量调用：onThought 建卡设 thought；onAction 填头；onObservation 填 obs+状态+折叠。 */
function renderToolCard(stepsEl, round, thought, action, observation) {
  let card = stepsEl.querySelector(`.aiq-toolcard[data-round="${round}"]`);
  if (!card) {
    card = document.createElement('div');
    card.className = 'aiq-toolcard is-open';
    card.dataset.round = round;
    card.innerHTML = `<div class="aiq-toolcard-head">
        <span class="aiq-toolcard-icon run">⏳</span>
        <span class="aiq-toolcard-name">第 ${round} 步</span>
        <span class="aiq-toolcard-target"></span>
        <span class="aiq-toolcard-chev">▸</span>
      </div>
      <div class="aiq-toolcard-body">
        <div class="aiq-toolcard-thought"></div>
        <div class="aiq-toolcard-obs"></div>
      </div>`;
    card.querySelector('.aiq-toolcard-head').addEventListener('click', () => card.classList.toggle('is-open'));
    stepsEl.appendChild(card);
  }
  if (thought != null) card.querySelector('.aiq-toolcard-thought').textContent = thought || '';
  if (action) {
    card.querySelector('.aiq-toolcard-name').textContent = action.name || 'step';
    card.querySelector('.aiq-toolcard-target').textContent = actionTargetSummary(action);
  }
  if (observation != null) {
    card.querySelector('.aiq-toolcard-obs').textContent = observation || '';
    const fail = /失败|\[ERR\]|错误|未知工具/.test(observation);
    const icon = card.querySelector('.aiq-toolcard-icon');
    icon.textContent = fail ? '✕' : '✓';
    icon.className = 'aiq-toolcard-icon ' + (fail ? 'fail' : 'ok');
    card.classList.remove('is-open');   // 结果到→折叠（Claude Code 自动折叠已完成调用）
  }
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
      renderToolCard(shell.stepsEl, round, thought, null, null);
      if (_curTrace) _curTrace.steps.push({ round, thought, action: null, observation: null });
      setPhase('思考');
      autoScroll();
    },
    onAction: (action, round) => {
      renderToolCard(shell.stepsEl, round, null, action, null);
      if (_curTrace && _curTrace.steps.length) _curTrace.steps[_curTrace.steps.length - 1].action = action;
    },
    onObservation: (obs, round) => {
      renderToolCard(shell.stepsEl, round, null, null, obs);
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
      enhanceCodeBlocks(shell.answerEl);
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
      enhanceCodeBlocks(shell.answerEl);
      if (_curTrace) { _curTrace.revised = text; _curTrace.final = text; }
      const v = shell.reviewBody.querySelector('.aiq-review-verdict.fail');
      if (v) v.textContent = '审查未过·已重写';
      autoScroll();
    },
    onDegraded: (text) => {
      cancelStream();
      stopThinking();
      shell.answerEl.innerHTML = renderAnswer(text || '（未生成有效回答——模型输出无法解析为动作，且最终结论生成失败）', getValidRefNames());
      enhanceCodeBlocks(shell.answerEl);
    },
  };
}

/** 蒸馏上一个 assistant trace → priorTurn（多轮续作用：让下轮 LLM 承接上轮 intent/method/已做/缺口）。
 *  trace 全量已存 _history/localStorage，但旧逻辑只回灌 trace.final → 续作失忆；此处补结构化上轮。 */
function _buildPriorTurn() {
  for (let i = _history.length - 2; i >= 0; i--) {   // -1 = 当前 user；往前找末个 assistant
    const h = _history[i];
    if (h.role === 'assistant' && h.trace) {
      const t = h.trace, dg = t.diagnose || {}, dp = (dg.data_plan || {});
      const method = Array.isArray(dg.method) ? dg.method.join(' → ') : (dg.method || '');
      const done = (t.steps || []).map((s) => {
        const a = s.action || {};
        return `${a.name || '?'}${a.params ? '(' + JSON.stringify(a.params).slice(0, 50) + ')' : ''}`;
      }).join('；');
      const gap = ((t.caliber && t.caliber.length) ? t.caliber : (dp.gap || [])).join('、');
      return { intent: dg.intent || '', method, done: done || '（无工具调用）', gap: gap || '', strategy: dp.strategy || '' };
    }
  }
  return null;
}
/** 续作线索识别：继续/接着/补充/那个/上一个/把刚才 等（命中且存在 priorTurn → 视为续作）。 */
function _isResumeCue(q) {
  const s = (q || '').trim();
  return !!s && /继续|接着|续做|补充|那个|上一个|把刚才/.test(s);
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
  resetCurrentResults();   // 沉浸聚焦：新一轮查询清空上轮结果登记
  _streaming = true;
  updateSendBtn();
  ensureEmcHeight();
  startThinking();
  _abortCtl = new AbortController();
  // 多轮上下文：前几轮 user/assistant.final 作为历史带给 LLM（stages.js 拼进 messages）
  const _hist = [];
  for (const h of _history.slice(0, -1)) {   // 排除当前刚 push 的 user
    if (h.role === 'user') _hist.push({ role: 'user', content: h.text });
    else if (h.role === 'assistant' && h.trace && h.trace.final) _hist.push({ role: 'assistant', content: h.trace.final });
  }
  const ctx = { question: text, context: await buildContext(), signal: _abortCtl.signal, model: _thinkMode, history: _hist.slice(-10),
    priorTurn: _buildPriorTurn(),               // 多轮连续性：上轮 intent/method/已做/缺口（续作承接）
    resume: false };
  ctx.resume = !!(ctx.priorTurn && _isResumeCue(text));   // 续作线索 → harness 跳过 general/request_upload 短路、续跑上轮 method
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
    relaxEmc();
    cleanupConsumedResults();   // 轮末兜底：清掉被后续工具消费的中间结果层，EMC 组只留最终答案图层
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

/** Pro/Flash 切换：绑定输入区静态 #aiq-mode（不再注入 head）。 */
function wireModeSwitch() {
  const seg = document.getElementById('aiq-mode');
  if (!seg || seg._wired) return;
  seg._wired = true;
  seg.querySelectorAll('button').forEach((x) => x.classList.toggle('is-active', x.dataset.mode === _thinkMode));
  seg.addEventListener('click', (e) => {
    const b = e.target.closest('button[data-mode]');
    if (!b) return;
    _thinkMode = b.dataset.mode;
    localStorage.setItem(MODE_KEY, _thinkMode);
    seg.querySelectorAll('button').forEach((x) => x.classList.toggle('is-active', x.dataset.mode === _thinkMode));
  });
}

/** 空态欢迎卡：无对话时显问候 + 能力清单 + 示例追问（点击即发）。有消息则移除。 */
const WELCOME_PROMPTS = [
  { tag: '情绪分析', text: '哪些区域情绪最差？为什么？' },
  { tag: '区域对比', text: '对比西陵区和伍家岗区的情绪与归因' },
  { tag: 'GIS 操作', text: '筛选西陵区的商业用地' },
  { tag: '周边分析', text: '滨江公园周边 500 米情绪如何？' },
];
function renderEmptyState() {
  const list = document.getElementById('chat-messages');
  if (!list) return;
  const existing = list.querySelector('.emc-welcome');
  if (_history.length === 0) {
    if (existing) return;
    const cap = [
      ['情绪评价', '区域情绪排序 · 4×5 治理归因 · 热点识别'],
      ['GIS 操作', '裁剪/抽取/叠置/缓冲，结果自动落地图'],
      ['多轮追问', '承接上轮计划续做，上传数据即纳入分析'],
    ].map(([k, v]) => `<div class="emc-welcome-cap-row"><span class="emc-welcome-cap-key">${k}</span><span class="emc-welcome-cap-val">${v}</span></div>`).join('');
    const chips = WELCOME_PROMPTS.map((p) => `<button type="button" class="emc-welcome-chip" data-prompt="${escapeHtml(p.text)}"><span class="emc-welcome-chip-tag">${p.tag}</span>${escapeHtml(p.text)}</button>`).join('');
    const el = document.createElement('div');
    el.className = 'emc-welcome';
    el.innerHTML = '<div class="emc-welcome-head">'
      + '<svg class="emc-welcome-logo" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a7 7 0 0 0-7 7c0 3.5 2.5 5 2.5 8h9c0-3 2.5-4.5 2.5-8a7 7 0 0 0-7-7z"/><path d="M9.5 21h5"/></svg>'
      + '<div><div class="emc-welcome-title">你好，我是 EmotionMap Copilot</div>'
      + '<div class="emc-welcome-sub">用情绪地图看懂市民心声——问区域情绪、做空间分析、追原因与建议。</div></div></div>'
      + `<div><div class="emc-welcome-section-label">我能做什么</div><div class="emc-welcome-cap">${cap}</div></div>`
      + `<div><div class="emc-welcome-section-label">试试这些</div><div class="emc-welcome-ex">${chips}</div></div>`;
    list.appendChild(el);
  } else if (existing) {
    existing.remove();
  }
}

function restoreHistory() {
  const list = document.getElementById('chat-messages');
  if (!list) return;
  list.innerHTML = '';
  for (const m of _history) {
    if (m.role === 'user') appendMessage('user', escapeHtml(m.text));
    else appendAssistantShell(m.trace);
  }
  renderEmptyState();
}

function clearChat() {
  _history = [];
  saveHistory();
  restoreHistory();
}

/** 历史记录：EMC 内就地视图切换（chat ↔ history），1:1 Claude Code。
 *  搜索 + 点选进入 + 垃圾桶删除。数据层 _archive/_history/switchSession/deleteSession 复用，零改。 */
let _view = 'chat';   // 'chat' | 'history'
function setView(v) {
  _view = v;
  const c = document.getElementById('emc-view-chat');
  const h = document.getElementById('emc-view-history');
  if (c) c.hidden = (v !== 'chat');
  if (h) h.hidden = (v !== 'history');
  if (v === 'history') renderHistoryList(document.getElementById('emc-history-search')?.value || '');
}
function toggleHistoryView() {
  if (_streaming) return;
  setView(_view === 'history' ? 'chat' : 'history');
}
function renderHistoryList(q) {
  const list = document.getElementById('emc-history-list');
  if (!list) return;
  q = (q || '').trim().toLowerCase();
  const items = [];
  const hasCur = _history.some((h) => h.role === 'user');
  if (hasCur) items.push({ id: '__current__', title: _titleOf(_history), ts: Date.now(), isCurrent: true });
  _archive.forEach((s) => items.push({ id: s.id, title: s.title || '会话', ts: s.createdAt || 0, isCurrent: false }));
  const filtered = q ? items.filter((it) => (it.title || '').toLowerCase().includes(q)) : items;
  if (!filtered.length) { list.innerHTML = '<div class="emc-history-empty">暂无匹配会话</div>'; return; }
  filtered.sort((a, b) => b.ts - a.ts);
  list.innerHTML = filtered.map((it) =>
    `<div class="emc-history-item${it.isCurrent ? ' is-current' : ''}" data-id="${it.id}">`
    + `<span class="emc-history-txt"><span class="emc-history-title">${escapeHtml(it.title)}</span>`
    + `<span class="emc-history-time">${formatTs(it.ts)}</span></span>`
    + (it.isCurrent ? '' : `<button class="emc-history-del" data-id="${it.id}" title="删除该会话"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7h14M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M7 7l1 13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1l1-13"/></svg></button>`)
    + `</div>`
  ).join('');
  list.querySelectorAll('.emc-history-item').forEach((row) => {
    row.addEventListener('click', (e) => {
      if (e.target.closest('.emc-history-del')) return;
      const id = row.dataset.id;
      if (id === '__current__') { setView('chat'); return; }
      switchSession(id); setView('chat');
    });
  });
  list.querySelectorAll('.emc-history-del').forEach((b) => b.addEventListener('click', (e) => { e.stopPropagation(); deleteSession(b.dataset.id); }));
}

function onMsgClick(e) {
  const wChip = e.target.closest('.emc-welcome-chip');   // 空态示例追问：点击即发
  if (wChip && wChip.dataset.prompt) { send(wChip.dataset.prompt); return; }
  const copy = e.target.closest('.emc-copy-btn');
  if (copy) {
    const bubble = copy.closest('.chat-bubble');
    const answer = bubble && bubble.querySelector('.aiq-answer');
    const text = answer ? answer.innerText : (bubble ? bubble.innerText : '');
    navigator.clipboard?.writeText(text);
    copy.classList.add('is-ok'); setTimeout(() => copy.classList.remove('is-ok'), 1200);
    return;
  }
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

/** 主窗口入口。EMC 常驻左端栏下半区（无 trigger / 无 close ×）。 */
export function initChatPanel() {
  document.getElementById('chat-new')?.addEventListener('click', () => {
    if (_streaming) return;   // 流式中忽略
    if (_history.length) {   // 当前会话存档
      _archive.unshift({ id: 's' + Date.now(), title: _titleOf(_history), history: [..._history], createdAt: Date.now() });
      saveArchive();
    }
    clearChat();
    updateContextCapacity(null);
    if (_view === 'history') setView('chat');
    document.getElementById('chat-input')?.focus();
  });
  document.getElementById('chat-history')?.addEventListener('click', () => toggleHistoryView());
  document.getElementById('emc-history-search')?.addEventListener('input', (e) => renderHistoryList(e.target.value));

  // 发送 / Enter 发送 / Esc 中断
  const sendBtn = document.getElementById('chat-send');
  const input = document.getElementById('chat-input');
  sendBtn?.addEventListener('click', () => {
    if (_streaming && _abortCtl) { _abortCtl.abort(); return; }
    send(input?.value);
  });
  input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input.value); }
    else if (e.key === 'Escape' && _streaming && _abortCtl) { e.preventDefault(); _abortCtl.abort(); }
  });
  // textarea 自适应增高（长 prompt 体验，封顶 160px）
  input?.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(160, input.scrollHeight) + 'px';
  });

  // + 附加当前选中图层/范围作上下文
  document.getElementById('emc-affix-add')?.addEventListener('click', () => {
    const sel = getSelectedLayer();
    const name = sel && sel.name;
    if (name && input) {
      const tag = `（参考图层：${name}）`;
      input.value = (input.value && !input.value.endsWith(' ')) ? input.value + ' ' + tag : (input.value || '') + tag;
      input.focus();
    } else {
      input?.focus();
    }
  });

  document.getElementById('chat-messages')?.addEventListener('click', onMsgClick);
  wireModeSwitch();
  restoreHistory();
  mountChatChrome();
  setupEmcHeightObservers();
  setEmcMode('comfort');

  // 折叠键 + 输入框触发展开 + 折叠态持久化恢复
  document.getElementById('chat-collapse')?.addEventListener('click', () => setEmcCollapsed(!_emcCollapsed));
  input?.addEventListener('focus', () => { if (_emcCollapsed) setEmcCollapsed(false); });   // 折叠态点输入框 → 展开
  if (_emcCollapsed) document.getElementById('emc-panel')?.classList.add('is-collapsed');   // 初始即折叠：套类（局部覆盖 --emc-h=48px）
}
