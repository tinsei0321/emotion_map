// ═══ chat-panel.js — AI 自然语言问答（底部滑出面板，多轮 + 组合式交互）═══
// 触发：右下「问答」按钮 → 底部滑出。流式渲染（marked markdown）+ 引用 chip（点击定位）。
// 组合式回答：模型在回答末尾追加 [!action] 标记 → 前端解析为附件卡 → 点击驱动地图/Overview/Table。
// 思考链：Pro(deepseek-reasoner) 的 reasoning_content → 灰显可折叠"思考过程"区（流式）。
// Grounding：每次发送前从选中分析层算紧凑摘要作 context + @关联对象注入。
// provider-agnostic：后端 /chat 默认 DeepSeek，未来换溯佰科改后端一处。
import { orchestrate, resetOrchestrator } from './chat-orchestrator.js';
import { getSelectedLayer, getLayers } from './state.js';
import { fitBoundsTo } from './map.js';
import { activateTab, setOverview, setTable } from './panel.js';
import { DOMAIN_LABEL, ELEMENT_LABEL } from './popup.js';
import { toast } from './toast.js';

let _messages = [];          // [{role, content}]
let _streaming = false;
let _abortCtl = null;        // AbortController（停止生成）
let _contextTokens = [];     // @关联对象（Batch B 拖拽/小工具注入；预留回传 grounding）
let _deepThink = false;      // 深度思考开关（Batch B 加 UI；true→deepseek-reasoner）

function isAnalysis(l) {
  const ui = l && l.paint && l.paint._ui;
  return !!(l && l.kind === 'polygon' && ui && (ui.tool === 'grid' || ui.tool === 'terrain'));
}

/** 取当前分析层（选中层优先，否则首个分析层）。 */
function currentAnalysis() {
  const sel = getSelectedLayer();
  return (sel && isAnalysis(sel)) ? sel : getLayers().find(isAnalysis);
}

/** 从选中层（或首个分析层）算紧凑摘要供 grounding。 */
function buildContext() {
  const layers = getLayers();
  const an = currentAnalysis();
  const parts = [];
  const loaded = layers
    .filter((l) => l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length)
    .map((l) => `${l.name}(${l.fc.features.length}条)`).join('、');
  parts.push('已加载图层：' + (loaded || '（无）'));
  if (!an) {
    parts.push('（暂无网格/指定单元聚合层——建议先用「网格·指定单元」生成聚合后再问区域级问题）');
    return parts.join('\n');
  }
  const feats = an.fc.features;
  parts.push(`当前分析层：${an.name}（${feats.length} 个聚合单元）`);
  // 极性汇总
  const agg = { 'Very Positive': 0, Positive: 0, Neutral: 0, Negative: 0, 'Very Negative': 0 };
  for (const f of feats) {
    const p = f.properties || {};
    agg['Very Positive'] += p.n_very_positive || 0;
    agg.Positive += p.n_positive || 0;
    agg.Neutral += p.n_neutral || 0;
    agg.Negative += p.n_negative || 0;
    agg['Very Negative'] += p.n_very_negative || 0;
  }
  parts.push(`极性计数：非常积极${agg['Very Positive']} / 积极${agg.Positive} / 中性${agg.Neutral} / 消极${agg.Negative} / 非常消极${agg['Very Negative']}`);
  // Top 区域（按 |pi| 降序，最多 10）
  const top = feats
    .map((f) => f.properties || {})
    .filter((p) => p.polarity_index != null && !isNaN(p.polarity_index))
    .sort((a, b) => Math.abs(b.polarity_index) - Math.abs(a.polarity_index))
    .slice(0, 10);
  if (top.length) {
    parts.push('高张力区域（极性指数越偏离 0 越聚集）：\n' + top.map((p) => {
      const name = p.name || p.issue_label || '未命名';
      const dom = DOMAIN_LABEL[p.domain_top] || p.domain_top || '?';
      const elm = ELEMENT_LABEL[p.element_top] || p.element_top || '?';
      return `  - ${name}：极性 ${Number(p.polarity_index).toFixed(2)}，${dom}×${elm}，问题=${p.issue_label || '—'}，${p.point_count || 0}点`;
    }).join('\n'));
  }
  return parts.join('\n');
}

/** 引导提问（随选中层动态）。 */
function suggestedQuestions() {
  const sel = getSelectedLayer();
  if (sel && isAnalysis(sel)) {
    const n = sel.name.split('·').slice(1, 3).join('·') || sel.name;
    return [
      `「${n}」中情绪最差的区域是哪里？为什么？`,
      '主要的治理要素问题集中在哪类（设施/环境/服务）？',
      '给出针对最差区域的更新建议',
    ];
  }
  return [
    '当前地图的情绪总体表现如何？',
    '哪些区域情绪最差？为什么？',
    '如何在规划层面改善消极情绪聚集区？',
  ];
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

// ── 组合式回答：动作标记解析 + 附件卡 ──────────────────────────────────────
// 模型在回答末尾追加 [!type:args] 单行标记；前端剥离正文 + 渲染附件卡。
//   [!focus:a,b,c] / [!overview] / [!table] / [!layer:名|筛选]
const _ACTION_RE = /^[ \t]*\[!(\w+)(?::([^\]]+))?\][ \t]*$/gm;

function parseActions(text) {
  const actions = [];
  const cleaned = text.replace(_ACTION_RE, (_m, type, args) => {
    actions.push({ type, args: args ? args.trim() : '' });
    return '';
  }).replace(/\n{3,}/g, '\n\n').trim();
  return { cleaned, actions };
}

function actionCardHtml(a) {
  if (a.type === 'focus') {
    const names = a.args.split(',').map((s) => s.trim()).filter(Boolean);
    if (!names.length) return '';
    return `<button class="chat-action-card" data-action="focus" data-names="${escapeHtml(names.join('|'))}" type="button">🗺 聚焦 ${names.length} 个区域</button>`;
  }
  if (a.type === 'overview') {
    return `<button class="chat-action-card" data-action="overview" type="button">📊 在 Overview 查看归因</button>`;
  }
  if (a.type === 'table') {
    return `<button class="chat-action-card" data-action="table" type="button">📋 在 Table 查看明细</button>`;
  }
  if (a.type === 'layer') {
    const parts = a.args.split('|');
    const name = (parts.shift() || '').trim();
    const filter = parts.join('|').trim();
    return `<button class="chat-action-card" data-action="layer" data-name="${escapeHtml(name || '未命名')}" data-filter="${escapeHtml(filter)}" type="button">📍 加入图层：${escapeHtml(name || '未命名')}</button>`;
  }
  return '';
}

function actionsToHtml(actions) {
  if (!actions.length) return '';
  return `<div class="chat-actions">${actions.map(actionCardHtml).filter(Boolean).join('')}</div>`;
}

/** markdown 渲染（marked 不可用退纯文本转义）+ [ref:NAME] → 引用 chip + 末尾附件卡。 */
function renderAnswer(text) {
  const { cleaned, actions } = parseActions(text);
  let html = window.marked ? window.marked.parse(cleaned) : `<p>${escapeHtml(cleaned).replace(/\n/g, '<br>')}</p>`;
  html = html.replace(/\[ref:([^\]]+)\]/g, (_, name) =>
    `<button class="cite-chip" data-ref="${escapeHtml(name)}" type="button">${escapeHtml(name)}</button>`);
  return html + actionsToHtml(actions);
}

function renderSuggest() {
  const wrap = document.getElementById('chat-suggest');
  if (!wrap) return;
  wrap.innerHTML = suggestedQuestions()
    .map((q) => `<button class="chat-suggest-chip" type="button">${escapeHtml(q)}</button>`).join('');
  wrap.querySelectorAll('.chat-suggest-chip').forEach((b) => {
    b.addEventListener('click', () => {
      const inp = document.getElementById('chat-input');
      inp.value = b.textContent;
      inp.focus();
    });
  });
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

/** assistant 气泡骨架：思考链区 + 实现路径/执行轨道区 + 结论区(光标)。编排器回调分别填充。 */
function appendAssistantShell() {
  const list = document.getElementById('chat-messages');
  if (!list) return {};
  const el = document.createElement('div');
  el.className = 'chat-msg chat-msg-assistant';
  el.innerHTML = `<div class="chat-bubble">
    <div class="chat-reason" hidden><div class="chat-reason-head">▸ 思考过程</div><div class="chat-reason-body"></div></div>
    <div class="chat-plan" hidden><div class="chat-plan-head">实现路径</div><div class="chat-plan-thinking-body"></div><div class="chat-track"></div></div>
    <div class="chat-answer"><span class="chat-cursor">▍</span></div>
  </div>`;
  list.appendChild(el);
  scrollBottom();
  return {
    reasonEl: el.querySelector('.chat-reason'),
    planEl: el.querySelector('.chat-plan'),
    trackEl: el.querySelector('.chat-track'),
    answerEl: el.querySelector('.chat-answer'),
  };
}

// ── 执行轨道 UI（端到端编排：plan 的 steps[] → 步骤清单，逐步实时状态）──
const STEP_ICON = { pending: '○', running: '⟳', done: '✓', error: '✕' };

function renderTrack(trackEl, steps) {
  const els = {};
  if (!trackEl || !steps || !steps.length) return els;
  trackEl.innerHTML = steps.map((s) => {
    const id = s.id || '';
    return `<div class="chat-step" data-id="${escapeHtml(id)}">`
      + `<span class="chat-step-ico">${STEP_ICON.pending}</span>`
      + `<span class="chat-step-label">${escapeHtml(s.label || s.tool || '')}</span>`
      + `<span class="chat-step-note"></span>`
      + `</div>`;
  }).join('');
  trackEl.querySelectorAll('.chat-step').forEach((row) => { els[row.dataset.id] = row; });
  return els;
}

function updateStep(row, status, note) {
  if (!row) return;
  row.classList.remove('is-running', 'is-done', 'is-error');
  if (status === 'running') row.classList.add('is-running');
  else if (status === 'done') row.classList.add('is-done');
  else if (status === 'error') row.classList.add('is-error');
  const ico = row.querySelector('.chat-step-ico');
  if (ico) ico.textContent = STEP_ICON[status] || STEP_ICON.pending;
  const n = row.querySelector('.chat-step-note');
  if (n && note) n.textContent = '→ ' + note;
}

async function send(text) {
  text = (text || '').trim();
  if (!text || _streaming) return;
  const input = document.getElementById('chat-input');
  input.value = '';
  appendMessage('user', escapeHtml(text));
  _messages.push({ role: 'user', content: text });

  const shell = appendAssistantShell();
  const reasonEl = shell.reasonEl;
  const answerEl = shell.answerEl;
  const planEl = shell.planEl;
  const trackEl = shell.trackEl;
  let reasonAcc = '';
  let answerAcc = '';
  let stepEls = {};
  _streaming = true;
  updateSendBtn();

  const ctx = buildContext();
  _abortCtl = new AbortController();
  try {
    await orchestrate(text, {
      context: ctx,
      signal: _abortCtl.signal,
      deepThink: _deepThink,
      contextTokens: _contextTokens.length ? _contextTokens : undefined,
      onReason: (tok) => {
        reasonAcc += tok;
        if (reasonEl) {
          reasonEl.hidden = false;
          const body = reasonEl.querySelector('.chat-reason-body');
          if (body) body.textContent = reasonAcc;
        }
        scrollBottom();
      },
      onPlan: (thinking, steps) => {
        if (planEl) {
          planEl.hidden = false;
          const tb = planEl.querySelector('.chat-plan-thinking-body');
          if (tb) tb.textContent = thinking;
        }
        stepEls = renderTrack(trackEl, steps);
        scrollBottom();
      },
      onStepState: (id, status, note) => {
        updateStep(stepEls[id], status, note);
        scrollBottom();
      },
      onAnswer: (tok) => {
        answerAcc += tok;
        if (answerEl) { answerEl.innerHTML = renderAnswer(answerAcc); scrollBottom(); }
      },
    });
    if (!answerAcc && answerEl) answerEl.innerHTML = '<span class="chat-error">（未生成结论——确认 DEEPSEEK_API_KEY 已配置）</span>';
    if (answerAcc) _messages.push({ role: 'assistant', content: answerAcc });
    if (reasonEl) { reasonEl.hidden = !reasonAcc; if (reasonAcc) reasonEl.classList.add('is-done'); }
  } catch (e) {
    const aborted = e && e.name === 'AbortError';
    if (answerEl) answerEl.innerHTML += aborted ? ' <span class="chat-error">（已停止）</span>'
      : `<span class="chat-error">[请求失败] ${escapeHtml(e.message || e)}</span>`;
    if (!aborted) toast.error('问答请求失败：' + (e.message || e));
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

function setPanel(open) {
  const panel = document.getElementById('chat-panel');
  if (!panel) return;
  panel.classList.toggle('is-collapsed', !open);
  if (open) {
    renderSuggest();
    setTimeout(() => document.getElementById('chat-input')?.focus(), 50);
  }
}

/** 引用 chip 点击 → 在分析层里按名匹配 feature → 飞到 + cell:selected 深读。 */
function onCitationClick(name) {
  const layers = getLayers();
  const target = name.trim();
  for (const l of layers) {
    if (!isAnalysis(l) || !l.fc || !l.fc.features) continue;
    const f = l.fc.features.find((ff) => {
      const nm = (ff.properties || {}).name || '';
      return nm === target || (nm && (nm.includes(target) || target.includes(nm)));
    });
    if (f) {
      selectCell(f, l);
      return;
    }
  }
  toast.info(`未在当前分析层找到「${target}」`);
}

function selectCell(f, l) {
  const g = f.geometry;
  if (g && (g.type === 'Polygon' || g.type === 'MultiPolygon')) {
    let coords = g.type === 'Polygon' ? g.coordinates[0] : g.coordinates.flatMap((p) => p[0]);
    if (coords && coords.length) {
      let mnX = Infinity, mxX = -Infinity, mnY = Infinity, mxY = -Infinity;
      for (const [x, y] of coords) { if (x < mnX) mnX = x; if (x > mxX) mxX = x; if (y < mnY) mnY = y; if (y > mxY) mxY = y; }
      if (isFinite(mnX)) fitBoundsTo([mnX, mnY, mxX, mxY]);
    }
  }
  document.dispatchEvent(new CustomEvent('cell:selected', { detail: { feature: f, layer: l } }));
}

/** 附件卡点击 → 驱动地图/Overview/Table（复用事件总线）。 */
function onActionClick(card) {
  const action = card.dataset.action;
  if (action === 'focus') {
    const names = (card.dataset.names || '').split('|').filter(Boolean);
    if (!names.length) return;
    names.forEach((n) => onCitationClick(n));   // 逐个定位（末个 fitBounds）
    toast.info(`聚焦 ${names.length} 个区域`);
  } else if (action === 'overview') {
    const an = currentAnalysis();
    if (an) { activateTab('overview'); setOverview(an); toast.info('已切到 Overview 归因视图'); }
    else toast.info('暂无分析层可展示');
  } else if (action === 'table') {
    const an = currentAnalysis();
    if (an && an.fc) { activateTab('table'); setTable(an.fc, an); toast.info('已切到 Table 明细'); }
    else toast.info('暂无分析层数据');
  } else if (action === 'layer') {
    // Batch B：Layers「AI问答」组卡挂载（mirror 工具层 layers:changed）。
    toast.info(`「加入图层」将在 UI 重做阶段接入：${card.dataset.name}`);
  }
}

export function initChatPanel() {
  const trigger = document.getElementById('chat-trigger');
  trigger?.addEventListener('click', () => setPanel(true));
  document.getElementById('chat-close')?.addEventListener('click', () => setPanel(false));
  document.getElementById('chat-clear')?.addEventListener('click', () => {
    _messages = [];
    resetOrchestrator();
    const list = document.getElementById('chat-messages');
    if (list) list.innerHTML = '';
    renderSuggest();
  });
  const sendBtn = document.getElementById('chat-send');
  const input = document.getElementById('chat-input');
  sendBtn?.addEventListener('click', () => {
    if (_streaming && _abortCtl) { _abortCtl.abort(); return; }   // 流式中 → 停止
    send(input?.value);
  });
  input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input.value); }
  });
  // 引用 chip + 附件卡 委托（消息流中动态生成）
  document.getElementById('chat-messages')?.addEventListener('click', (e) => {
    const reason = e.target.closest('.chat-reason.is-done');
    if (reason) { reason.classList.toggle('is-open'); return; }   // 思考链流后点击折叠/展开
    const chip = e.target.closest('.cite-chip');
    if (chip) { onCitationClick(chip.dataset.ref); return; }
    const card = e.target.closest('.chat-action-card');
    if (card) onActionClick(card);
  });
  renderSuggest();
}
