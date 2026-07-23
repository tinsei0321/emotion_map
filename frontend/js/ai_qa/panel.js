// ═══ panel.js — AI 问答 UI（底部滑出 · agent loop · 历史持久化 · 思考深度开关 · 动态状态）═══
import { orchestrate, getTemplateStats } from './harness.js';
import { buildContext, TOOLS, resetStepResults, resetCurrentResults, cleanupConsumedResults, getFig } from './tools.js';
import { initCpdState, subscribe, getCurStepIdx, CPD_STEPS, relayoutFloats } from './cpd-state.js';
import { initCpdGuide, recomputeGuidance, refreshGuidance, suppressGuidance } from './cpd-guide.js';   // CPD：引导引擎（依赖注入，零反向 import）
import { getLayers, selectLayer, getSelectedLayer } from '../state.js';
import { getLastUsage, resetCallStats, getCallStats } from './api.js';

const HISTORY_KEY = 'ai_qa_history_v1';
const ARCHIVE_KEY = 'ai_qa_archive_v1';
const MODE_KEY = 'ai_qa_think_mode';
const _INPUT_PH_EXPANDED = '问 EMC：哪些区域情绪最差？为什么？  （Enter 发送 · Shift+Enter 换行 · Esc 中断）';
const _INPUT_PH_COLLAPSED = '向 EmotionMap Copilot 提问：了解"情绪地图"，观察、分析、总结城市情绪数据。';

// 动态思考状态文案（轮换，随机感；参考 Claude/ChatGPT "正在思考"动态提示）。
const THINK_PHRASES = ['正在思考', '正在分析', '正在计算', '正在构思', '正在比对数据', '正在归纳', '正在权衡证据', '正在检索线索', '正在梳理逻辑'];

let _streaming = false;
let _abortCtl = null;
let _history = loadHistory();
let _archive = loadArchive();
let _curTrace = null;
let _consecutiveAsks = 0;   // P1 ask_user 跨 orchestrate 连续计数：≥2 时下轮注入"禁止再 ask_user"防博弈式无限追问（MAX_ROUNDS 对 ask 无效，因 ask 直接 return 不计 round）
let _thinkMode = localStorage.getItem(MODE_KEY) || 'pro';   // 'pro' | 'flash'
let _thinkTimer = null;
let _emcCollapsed = true;   // F5 默认折叠胶囊（不记忆上轮展开态·用户定 2026-07-22）
let _userPinned = false;   // 用户上滑停跟；回到底部后恢复跟随

const CTX_BUDGET = 1000000;   // DeepSeek V4 Pro 上下文 1M token
const _CAP_C = 2 * Math.PI * 9;   // SVG 圆周长（r=9）
/** 容量圆圈（SVG 环）：填充=当前 prompt_tokens 占 1M 比例；深灰常显、≥60% 变橙；悬停弹富 tooltip（5 类明细）。 */
function updateContextCapacity(usage) {
  const el = document.getElementById('ctx-cap');
  if (!el) return;
  const fg = el.querySelector('.ctx-cap-fg');
  if (!usage || !usage.prompt_tokens) {
    el.classList.remove('warn');
    if (fg) fg.setAttribute('stroke-dashoffset', _CAP_C.toFixed(2));
    return;
  }
  const ratio = Math.min(usage.prompt_tokens / CTX_BUDGET, 1);
  el.classList.toggle('warn', ratio >= 0.6);
  if (fg) fg.setAttribute('stroke-dashoffset', (_CAP_C * (1 - ratio)).toFixed(2));
}
/** 容量 tooltip 单例（挂 body，position:fixed 不被 EMC overflow 裁切）。 */
function _ctxCapTip() {
  let tip = document.getElementById('ctx-cap-tip');
  if (!tip) {
    tip = document.createElement('div');
    tip.id = 'ctx-cap-tip';
    tip.className = 'aiq-cap-tip';
    tip.setAttribute('role', 'tooltip');
    tip.hidden = true;
    document.body.appendChild(tip);
  }
  return tip;
}
/** tooltip 内容：顶部容量% + 橙进度条，下方 5 类明细（输入/输出/思考链/缓存命中/会话规模）。
 *  思考链 reasoning_tokens、缓存 prompt_cache_hit/miss 为运行时确认字段（DeepSeek 返了才显，否则 —）。 */
function _ctxCapTipHtml(usage, stats) {
  if (!usage || !usage.prompt_tokens) {
    return '<div class="aiq-cap-tip-title">上下文容量</div><div class="aiq-cap-tip-empty">暂无数据（尚未生成回答）</div>';
  }
  const prompt = usage.prompt_tokens || 0;
  const ratio = Math.min(prompt / CTX_BUDGET, 1);
  const pct = (ratio * 100).toFixed(ratio < 0.1 ? 1 : 0);
  const completion = usage.completion_tokens || 0;
  const reasoning = usage.reasoning_tokens;
  const hit = usage.prompt_cache_hit_tokens;
  const miss = usage.prompt_cache_miss_tokens;
  const cacheRate = (hit != null && (hit + (miss || 0)) > 0) ? Math.round((hit / (hit + (miss || 0))) * 100) : null;
  const steps = (_curTrace && _curTrace.steps) ? _curTrace.steps.length : 0;
  const hist = _history ? _history.length : 0;
  const row = (k, v) => `<div class="aiq-cap-tip-row"><span class="k">${k}</span><span class="v">${v}</span></div>`;
  return `<div class="aiq-cap-tip-title">上下文容量</div>
    <div class="aiq-cap-tip-pct">${pct}<span class="pct-sgn">%</span></div>
    <div class="aiq-cap-tip-bar"><div class="aiq-cap-tip-bar-fill" style="width:${pct}%"></div></div>
    <div class="aiq-cap-tip-meta">${prompt.toLocaleString()} / 1,000,000 token</div>
    <div class="aiq-cap-tip-rows">
      ${row('输入 Prompt', prompt.toLocaleString())}
      ${row('输出 Completion', completion.toLocaleString())}
      ${row('思考链 Reasoning', reasoning != null ? Number(reasoning).toLocaleString() : '—')}
      ${row('缓存命中', cacheRate != null ? `${Number(hit).toLocaleString()} · ${cacheRate}%` : '—')}
      ${row('会话规模', `${stats.calls} 次 · ${steps} 步 · ${hist} 条`)}
    </div>`;
}
function _ctxCapShowTip() {
  const cap = document.getElementById('ctx-cap');
  const tip = _ctxCapTip();
  if (!cap || !tip) return;
  tip.innerHTML = _ctxCapTipHtml(getLastUsage(), getCallStats());
  tip.hidden = false;
  const r = cap.getBoundingClientRect();
  const tw = tip.offsetWidth, th = tip.offsetHeight;
  let left = r.left + r.width / 2 - tw / 2;   // 水平居中于圆圈
  let top = r.top - th - 8;                    // 默认上方 8px
  if (top < 8) top = r.bottom + 8;             // 上方放不下翻下方
  left = Math.max(8, Math.min(left, window.innerWidth - tw - 8));
  tip.style.left = left + 'px';
  tip.style.top = top + 'px';
}
function _ctxCapHideTip() {
  const tip = document.getElementById('ctx-cap-tip');
  if (tip) tip.hidden = true;
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
/** CPD：折叠态文本自适应——镜像量测 placeholder 实际占高，11-14px 自调字号塞进胶囊 2 行。
 *  未来 AI 动态改此处文案（_INPUT_PH_COLLAPSED）时，调本函数即可保持完整显示。 */
function _fitCollapsedText() {
  const ta = document.getElementById('chat-input');
  const panel = document.getElementById('emc-panel');
  if (!ta || !panel || !panel.classList.contains('is-collapsed')) return;
  const text = ta.placeholder || '';
  if (!text) return;
  let m = document.getElementById('_emc-fit');
  if (!m) {
    m = document.createElement('div'); m.id = '_emc-fit';
    m.style.cssText = 'position:absolute;left:-9999px;top:0;visibility:hidden;white-space:pre-wrap;word-break:break-word;pointer-events:none;';
    document.body.appendChild(m);
  }
  const cs = getComputedStyle(ta);
  const r = ta.getBoundingClientRect();
  m.style.width = (r.width - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight)) + 'px';
  m.style.fontFamily = cs.fontFamily;
  m.style.lineHeight = '1.3';
  m.style.fontWeight = '700';   /* CPD ③：折叠态内容粗体，镜像须同权重以保自适应量测准 */
  const maxH = r.height - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
  m.textContent = text;
  let fs = 14;
  for (; fs >= 11; fs -= 0.5) { m.style.fontSize = fs + 'px'; if (m.offsetHeight <= maxH + 1) break; }
  ta.style.fontSize = fs + 'px';
}

function setEmcCollapsed(c) {
  _emcCollapsed = !!c;
  const panel = document.getElementById('emc-panel');
  if (panel) panel.classList.toggle('is-collapsed', _emcCollapsed);
  const input = document.getElementById('chat-input');
  if (input) input.placeholder = _emcCollapsed ? _INPUT_PH_COLLAPSED : _INPUT_PH_EXPANDED;   // 折叠/展开切换文案
  if (_emcCollapsed) _fitCollapsedText();   // CPD：折叠态文本自适应
  if (!_emcCollapsed) { relaxEmc(); _scheduleFit(); }   // 展开：回落 + 内容驱动高度自适应
  refreshGuidance();   // CPD：折叠↔展开重算引导（展开后 suppress 不生效→提示条反映当前引导·修 hint 消失 bug）
}

// ── CPD G1：引导引擎落地（cpd-guide.js 派发 cpd:guidance → 此处套光环/文案/CTA/examples）──
// 折叠态：光环 + placeholder；展开态：examples 示例胶囊（多分支→对话交接·plan §决策2）。engage 解除：CTA 点击 → suppressGuidance。
let _curGuidance = null;   // 最近一次 cpd:guidance 载荷（{kind,text,ctaKind,examples?}|null）
/** 末条答案 [ref:区域]/{{focus:}} 抽取的区域名（确定性变量·复用 _followUps 同源正则·plan §4.3）。 */
function _lastRegion() {
  const tr = _history.at(-1) && _history.at(-1).trace;
  const ans = (tr && tr.final) || '';
  const ref = (ans.match(/\[ref:([^\]]+)\]/) || ans.match(/\{{1,2}focus:([^}]+)\}{1,2}/) || [])[1];
  return ref ? ref.trim() : '';
}
/** 引导落地（cpd:guidance/setEmcCollapsed 调）：折叠态=光环+placeholder；展开态=CPD 提示条（双域 UI）。 */
function _applyGuidance() {
  const panel = document.getElementById('emc-panel');
  if (!panel) return;
  const has = !!_curGuidance;
  // 折叠态：光环胶囊 + placeholder 文案
  panel.classList.toggle('has-guidance', _emcCollapsed && has);
  if (_emcCollapsed) {
    const input = document.getElementById('chat-input');
    if (input) {
      input.placeholder = has ? _curGuidance.text : _INPUT_PH_COLLAPSED;
      _fitCollapsedText();
    }
  }
  // 展开态：CPD 提示条（进度点上方·EMC 接手时 CPD 同步进界面作提示语·v1.2 双域）
  _applyCpdHint(has ? _curGuidance : null);
}

/** 展开态 CPD 提示条（.emc-cpd-hint）：填 guidance.text + data-cta；无引导则隐。点击 → _runGuidanceCta。 */
function _applyCpdHint(g) {
  const hint = document.querySelector('.emc-cpd-hint');
  if (!hint) return;
  if (!g) { hint.hidden = true; return; }
  hint.hidden = false;
  const txt = hint.querySelector('.emc-cpd-hint-text');
  if (txt) txt.textContent = g.text;
  hint.dataset.cta = g.ctaKind || '';
}
/** 光环 CTA 调度：import/range/layers → cpd:focus-tab（sidebar 监听）；analyze/interpret/export → 打开对话窗口（展开 input）。 */
function _runGuidanceCta(kind) {
  if (kind === 'import' || kind === 'range' || kind === 'layers') {
    document.dispatchEvent(new CustomEvent('cpd:focus-tab', { detail: kind }));
    return;
  }
  // analyze/interpret/export/input → 打开对话窗口收集意图（展开 input 聚焦）→ 用户选方向/细化/示例或自由输入 → EMC harness
  const input = document.getElementById('chat-input');
  if (input) { setEmcCollapsed(false); input.focus(); }
  _renderGuidanceContent();   // 展开（或已展开）后显引导内容（方向级联/examples·幂等）
}

// ── CPD 阶段 A/B 引导内容（导游·确定性·不调 LLM·意图识别归 harness）──
// intent（点+范围就绪）= 阶段 A 大方向胶囊 → 阶段 B 细化追问胶囊；interpret（dock 产图）= examples 读图。
let _guidanceExamplesShown = false;   // 引导内容占用 #aiq-suggest 标志（防 clearGuidanceExamples 误清答案后 _followUps）
let _curDirection = null;             // 阶段 A→B 级联：用户选的大方向（null=显方向；已选=显细化）
/** 引导内容仅在「从未问答过」（首次分析前）显——一旦有答案，追问胶囊 _followUps 接管（互斥）。 */
function _shouldShowGuidanceExamples() {
  return !_streaming && !_history.some((h) => h.role === 'assistant');
}
/** 渲染 examples 到 #aiq-suggest（复用 .aiq-suggest-chip 样式·零新 CSS）；点击 → send → harness diagnose。 */
function renderGuidanceExamples(items) {
  const el = document.getElementById('aiq-suggest');
  if (!el || !Array.isArray(items) || !items.length) return;
  el.hidden = false;
  el.innerHTML = '<span class="aiq-suggest-label">试试</span>'
    + items.map((it) => `<button type="button" class="aiq-suggest-chip" data-prompt="${escapeHtml(it.text)}"><span class="aiq-suggest-tag">${escapeHtml(it.tag)}</span>${escapeHtml(it.text)}</button>`).join('');
  el.querySelectorAll('.aiq-suggest-chip').forEach((b) => b.addEventListener('click', () => send(b.dataset.prompt)));
  _guidanceExamplesShown = true;
}
/** 清引导内容（仅当占用时清，不动答案后 _followUps）。 */
function clearGuidanceExamples() {
  if (!_guidanceExamplesShown) return;
  const el = document.getElementById('aiq-suggest');
  if (el) { el.hidden = true; el.innerHTML = ''; }
  _guidanceExamplesShown = false;
}
/** 渲染引导内容总调度（cpd:guidance/CTA/级联切换调）：intent=方向级联(A/B)；interpret=examples；其余清。 */
function _renderGuidanceContent() {
  if (!_shouldShowGuidanceExamples()) { clearGuidanceExamples(); return; }
  const g = _curGuidance;
  if (!g) { clearGuidanceExamples(); return; }
  if (g.kind === 'intent' && g.directions) {
    if (_curDirection && g.refinements && g.refinements[_curDirection]) _renderRefinements(g.refinements[_curDirection]);
    else _renderDirections(g.directions);
  } else if (g.examples) {
    _curDirection = null;
    renderGuidanceExamples(g.examples);
  } else {
    clearGuidanceExamples();
  }
}
/** 阶段 A：渲染大方向胶囊（label「方向」）；点击 → 记 _curDirection → 阶段 B 细化。 */
function _renderDirections(dirs) {
  const el = document.getElementById('aiq-suggest');
  if (!el || !Array.isArray(dirs) || !dirs.length) return;
  el.hidden = false;
  el.innerHTML = '<span class="aiq-suggest-label">方向</span>'
    + dirs.map((d) => `<button type="button" class="aiq-suggest-chip" data-dir="${escapeHtml(d.dir)}"><span class="aiq-suggest-tag">${escapeHtml(d.tag)}</span>${escapeHtml(d.hint || '')}</button>`).join('');
  el.querySelectorAll('.aiq-suggest-chip[data-dir]').forEach((b) =>
    b.addEventListener('click', () => { _curDirection = b.dataset.dir; _renderGuidanceContent(); }));
  _guidanceExamplesShown = true;
}
/** 阶段 B：渲染细化追问胶囊 +「‹ 返回方向」；点击细化 → send → EMC harness；返回 → 重选方向。 */
function _renderRefinements(refs) {
  const el = document.getElementById('aiq-suggest');
  if (!el || !Array.isArray(refs) || !refs.length) return;
  el.hidden = false;
  el.innerHTML = '<span class="aiq-suggest-label">细化</span>'
    + refs.map((t) => `<button type="button" class="aiq-suggest-chip" data-prompt="${escapeHtml(t)}">${escapeHtml(t)}</button>`).join('')
    + '<button type="button" class="aiq-suggest-chip aiq-suggest-back">‹ 返回方向</button>';
  el.querySelectorAll('.aiq-suggest-chip[data-prompt]').forEach((b) =>
    b.addEventListener('click', () => send(b.dataset.prompt)));
  const back = el.querySelector('.aiq-suggest-back');
  if (back) back.addEventListener('click', () => { _curDirection = null; _renderGuidanceContent(); });
  _guidanceExamplesShown = true;
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
  _consecutiveAsks = 0;   // P1: 切会话重置 ask 计数（switchSession 不走 clearChat，单独补）
  saveArchive(); saveHistory(); restoreHistory();
  updateContextCapacity(null);
  if (_view === 'history') renderHistoryList(document.getElementById('emc-history-search')?.value || '');
}
function deleteSession(id) {
  _archive = _archive.filter((s) => s.id !== id);
  saveArchive();
  if (_view === 'history') renderHistoryList(document.getElementById('emc-history-search')?.value || '');
}
/** 一键清空全部历史会话（仅 _archive；当前会话 _history 不动）。用户定 2026-07-22。 */
function clearAllHistory() {
  if (_streaming) return;
  if (!_archive.length) return;
  if (!window.confirm('确定清空全部历史会话？此操作不可撤销。')) return;
  _archive = [];
  saveArchive();
  if (_view === 'history') renderHistoryList(document.getElementById('emc-history-search')?.value || '');
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
/* ── 思考链主题折叠（reorganizeReason）：把一段纯文本思考切成「主题目录（默认收起）+ 展开体」。
 *   流式期 onReason 照常 textContent 累加（保持现场感）；流末 finalizeReason + 历史恢复调 reorganizeReason。 */
const _REASON_TRANSITIONS = ['不过', '但是', '然而', '因此', '所以', '综上', '首先', '其次', '然后', '另外', '此外', '最终', '需要注意的是', '可见', '由此', '总之', '总的来说'];
function _splitReasonTopics(text) {
  let parts = String(text).split(/\n\s*\n+/).map((s) => s.trim()).filter(Boolean);
  if (parts.length <= 1 && text.length > 120) {   // 单段且长 → 按转折词兜底切（保留词在段首）
    const re = new RegExp('(?=(' + _REASON_TRANSITIONS.join('|') + '))', 'g');
    const sub = String(text).split(re).map((s) => s.trim()).filter(Boolean);
    if (sub.length > 1) parts = sub;
  }
  return parts.length ? parts : [String(text)];
}
function _reasonTopicTitle(text) {
  const m = String(text).trim().match(/^[^。？！\n]+[。？！]?/);
  let first = m ? m[0].trim() : String(text).trim();
  if (first.length > 32) first = first.slice(0, 32) + '…';
  return first || '（思考片段）';
}
function _highlightReasonTransitions(text) {   // 先 escapeHtml 防注入，再包 <strong>（中文转折词不受转义影响）
  return escapeHtml(text).replace(new RegExp('(' + _REASON_TRANSITIONS.join('|') + ')', 'g'), '<strong class="aiq-reason-transition">$1</strong>');
}
/** 把每个 segment 的纯文本（seg-body.textContent）切成多个 .aiq-reason-topic（默认收起，点 head 展开）。
 *  从 DOM 读 → 流式路径与历史恢复路径统一；已含 topic 的 segment 跳过（幂等）。 */
function reorganizeReason(shell) {
  if (!shell || !shell.reasonEl || shell.reasonEl.classList.contains('is-flash')) return;
  shell.reasonBody.querySelectorAll('.aiq-reason-segment').forEach((seg) => {
    const bodyEl = seg.querySelector('.aiq-reason-seg-body');
    if (!bodyEl || bodyEl.querySelector('.aiq-reason-topic')) return;
    const raw = bodyEl.textContent || '';
    if (!raw.trim()) return;
    const topics = _splitReasonTopics(raw);
    if (topics.length <= 1) {   // 单主题：直接显示（无需目录），仅加粗转折词
      bodyEl.innerHTML = `<div class="aiq-reason-topic-detail is-solo">${_highlightReasonTransitions(topics[0])}</div>`;
    } else {   // 多主题：目录（默认收起）+ 点开看展开体
      bodyEl.innerHTML = topics.map((tp) =>
        `<div class="aiq-reason-topic"><div class="aiq-reason-topic-head"><span class="aiq-reason-topic-chev">▸</span><span class="aiq-reason-topic-title">${escapeHtml(_reasonTopicTitle(tp))}</span></div><div class="aiq-reason-topic-detail">${_highlightReasonTransitions(tp)}</div></div>`
      ).join('');
    }
  });
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
  // 兼容 1~2 花括号：.format() 把模板示例 {{focus:}} 吞成单括号喂给 LLM，模型常输出单括号 {focus:}（对齐 chart/fig 5.67/5.83）
  html = html.replace(/\{{1,2}(focus|show|inspect):([^}]+)\}{1,2}/g, (_, act, tgt) => {
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

/** 完毕戳（回答完毕 + 版本 + 时间戳 + 复制回答按钮）；存 trace.doneAt 供历史恢复。 */
function _fmtTokens(n) { return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n); }
/** 三态出口徽章（CARTO 教训：显式呈现每一步建信任）。据 trace.exit/newLayerCount/diagnose.intent 派生。
 *  返回 {txt, cls} 或 null。 */
function _exitBadge(t) {
  if (!t) return null;
  const intent = t.diagnose && !t.diagnose.degraded && t.diagnose.intent;
  const skipped = t.review && t.review.skipped;
  if (t.exit === 'gap' || skipped === 'gap') return { txt: '缺数据·需上传', cls: 'warn' };
  if (t.exit === 'drift' || skipped === 'drift') return { txt: '生成异常·已拦截', cls: 'warn' };
  if (t.exit === 'ask') return { txt: '等你选择', cls: 'warn' };
  if (t.exit === 'partial' || skipped === 'partial') return { txt: '部分完成·需补充', cls: 'warn' };
  if (intent === 'general' || skipped === 'general') return { txt: '纯问答', cls: 'neutral' };
  const n = t.newLayerCount || 0;
  if (n > 0) return { txt: '已生成 ' + n + ' 个图层', cls: 'ok' };
  return { txt: '分析完成', cls: 'ok' };
}

/** 渲染页脚：出口徽章 + meta 文本（用时/版本/时间戳）+ 复制回答 icon（复制为 markdown，剥离 {{action}} 模板）。 */
function _renderFooter(shell, metaText, md, badge) {
  if (!shell || !shell.footerEl) return;
  shell.footerEl.hidden = false;
  shell.footerEl.innerHTML = '';
  if (badge) {
    const b = document.createElement('span');
    b.className = 'aiq-exit-badge ' + (badge.cls || '');
    b.textContent = badge.txt;
    shell.footerEl.appendChild(b);
  }
  const span = document.createElement('span');
  span.className = 'aiq-footer-meta'; span.textContent = metaText;
  const rbtn = document.createElement('button');
  rbtn.className = 'aiq-footer-report'; rbtn.type = 'button'; rbtn.title = '导出分析报告（可打印存 PDF）';
  rbtn.innerHTML = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/></svg>';
  rbtn.addEventListener('click', () => { _exportReport(shell); rbtn.classList.add('is-ok'); setTimeout(() => rbtn.classList.remove('is-ok'), 1200); });
  const btn = document.createElement('button');
  btn.className = 'aiq-footer-copy'; btn.type = 'button'; btn.title = '复制回答（Markdown）';
  btn.innerHTML = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>';
  btn.addEventListener('click', () => {
    const raw = md || shell._finalMd || (shell.answerEl && shell.answerEl.innerText) || '';
    const clean = raw.replace(/\{\{[^}]+\}\}/g, '').replace(/\n{3,}/g, '\n\n').trim();   // 剥离 {{action}} UI 模板
    navigator.clipboard?.writeText(clean);
    btn.classList.add('is-ok'); setTimeout(() => btn.classList.remove('is-ok'), 1200);
  });
  shell.footerEl.appendChild(span);
  shell.footerEl.appendChild(rbtn);
  shell.footerEl.appendChild(btn);
}

/** 导出分析报告：拼自包含可打印 HTML（答案 + 图表 PNG + 问题），新窗 print→存 PDF。事企业客户（住建局）"城市体检报告"出口。 */
function _exportReport(shell) {
  const ans = shell && shell.answerEl;
  if (!ans) return;
  const clone = ans.cloneNode(true);
  // canvas.chart → <img dataURL>（Chart.js 画布支持 toDataURL；纯文字答无图表也不影响）
  const orig = [...ans.querySelectorAll('canvas.aiq-chart')];
  const dup = [...clone.querySelectorAll('canvas.aiq-chart')];
  orig.forEach((cv, i) => { if (dup[i]) { const img = new Image(); img.src = cv.toDataURL('image/png'); img.style.maxWidth = '100%'; dup[i].replaceWith(img); } });
  const uq = [..._history].reverse().find((m) => m.role === 'user');
  const qTxt = uq ? uq.text : '';
  const ts = formatTs(Date.now());
  const css = 'body{font-family:system-ui,"Microsoft YaHei",sans-serif;max-width:780px;margin:32px auto;padding:0 24px;color:#1f2328;line-height:1.65}'
    + 'h1{font-size:22px;margin:0 0 4px} .meta{color:#888;font-size:13px;margin-bottom:20px;border-bottom:1px solid #eee;padding-bottom:8px}'
    + 'h3{font-size:15px;margin:22px 0 8px;color:#555} .answer{font-size:14px} .answer h1,.answer h2,.answer h3{margin:16px 0 6px}'
    + '.answer table{border-collapse:collapse;width:100%;font-size:13px} .answer td,.answer th{border:1px solid #ddd;padding:4px 8px}'
    + '.chat-action-btn,.aiq-chart-bad,.emc-msg-actions{display:none} img{display:block;margin:8px 0;max-width:100%}'
    + 'footer{margin-top:32px;border-top:1px solid #eee;padding-top:8px;color:#aaa;font-size:12px}';
  const html = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>宜昌市情绪地图 · 分析报告</title><style>'
    + css + '</style></head><body>'
    + '<h1>宜昌市情绪地图 · 分析报告</h1>'
    + `<div class="meta">生成时间 ${ts} · 情绪地图控制台 v1.0 · 由 EmotionMap Copilot 生成</div>`
    + (qTxt ? `<h3>问题</h3><div>${escapeHtml(qTxt)}</div>` : '')
    + '<h3>分析</h3><div class="answer">' + clone.innerHTML + '</div>'
    + '<footer>本报告基于多源情绪数据（社交媒体/12345 热线）+ GIS 空间分析自动生成；极性指数约 -2..2；归因落点 = 4 领域（规划/更新/运营/治理）× 5 要素（设施/环境/服务/文化/事件）。</footer>'
    + '</body></html>';
  const w = window.open('', '_blank');
  if (!w) return;   // 弹窗被拦截（罕见）— 静默，is-ok 仍反馈
  w.document.write(html); w.document.close(); w.focus();
  setTimeout(() => { try { w.print(); } catch (e) {} }, 500);
}
function stampDone(shell) {
  if (_curTrace) _curTrace.doneAt = Date.now();
  if (shell && shell.footerEl) {
    const secs = _curTrace && _curTrace.startedAt ? Math.max(1, Math.round((_curTrace.doneAt - _curTrace.startedAt) / 1000)) : 0;
    const cs = getCallStats();
    const ts = getTemplateStats();   // ⑤④ Flash template 累积命中率（跨会话，驱动 80% gate）
    const _tplMeta = ts.samples > 0 ? ` · Flash 模板 ${ts.hits}/${ts.samples}(${Math.round(ts.rate * 100)}%)` : '';
    const _skipSum = ts.skips ? (ts.skips.missing_slot + ts.skips.tool_failed) : 0;   // ⑤④ execSkips（另一轴，不污染 gate）
    const _skipMeta = _skipSum > 0 ? ` · skip ${_skipSum}` : '';
    _renderFooter(shell, `回答完毕 · 用时 ${secs}s · 用量 ${_fmtTokens(cs.total)} token / ${cs.calls} 次${_tplMeta}${_skipMeta} · 情绪地图 v1.0 · ${formatTs(_curTrace && _curTrace.doneAt)}`, shell._finalMd || (_curTrace && _curTrace.final), _exitBadge(_curTrace));
  }
  updateReasonMeta(shell);
  renderSuggest(_curTrace);   // 推荐追问胶囊（答案完毕后）
}

/** 推荐追问胶囊：据出口/intent 给上下文相关的下一步（静态 starter 兜底）。返回 [{tag, text}]。
 *  轻量上下文：复用 exit/intent + 抽答案首个 [ref:区域]/{{focus:}} 落到具体区域，不重计算。 */
function _followUps(t) {
  const intent = t && t.diagnose && !t.diagnose.degraded && t.diagnose.intent;
  const exit = t && t.exit;
  const skipped = t && t.review && t.review.skipped;
  const ans = (t && t.final) || '';
  const ref = (ans.match(/\[ref:([^\]]+)\]/) || ans.match(/\{{1,2}focus:([^}]+)\}{1,2}/) || [])[1];
  const region = ref ? ref.trim() : '';
  if (exit === 'gap' || skipped === 'gap') {
    return [
      { tag: '上传数据', text: '我已上传所需数据，请继续完成刚才的分析' },
      { tag: '换问法', text: '缩小范围重试：指定某个区或某类用地' },
      { tag: '现有能力', text: '用现有数据能做哪些分析？' },
    ];
  }
  if (exit === 'ask') return [];   // 选项胶囊已在答案区内（onAskUser 渲染），底部不再重复追问
  if (exit === 'drift' || skipped === 'drift') {
    return [
      { tag: '重试', text: '换一种问法重试刚才的分析' },
      { tag: '缩小范围', text: '缩小范围重试：指定某区或某类用地' },
    ];
  }
  if (exit === 'partial' || skipped === 'partial') {
    return [
      { tag: '补完分析', text: '我已上传所需数据，请补完刚才未完成的部分' },
      { tag: '换问法', text: '缩小范围重试：指定某个区或某类用地' },
      { tag: '看现有', text: '基于现有数据先给出完整结论' },
    ];
  }
  if (intent === 'general' || skipped === 'general') {
    return [
      { tag: '情绪分析', text: '哪些区域情绪最差？为什么？' },
      { tag: 'GIS 操作', text: '筛选西陵区的商业用地' },
      { tag: '周边分析', text: '滨江公园周边 500 米情绪如何？' },
    ];
  }
  if (intent === 'gis_operation') {
    return [
      { tag: '叠加分析', text: '把刚才的结果与周边情绪点叠置分析' },
      { tag: '缓冲区', text: '在刚才的结果周边做 500m 缓冲' },
      { tag: region ? '深读' : '归因', text: region ? `深读「${region}」的情绪归因` : '聚焦看结果区域的情绪归因' },
    ];
  }
  return [   // emotion_analysis（结果）
    { tag: '深读归因', text: region ? `深读「${region}」的 4×5 归因` : '深读最差区域的 4×5 归因' },
    { tag: '区域对比', text: '对比情绪最好和最差区域的差异' },
    { tag: '热点分析', text: '对负面情绪做核密度热点分析' },
  ];
}

/** 渲染推荐追问胶囊到 #aiq-suggest（答案完毕后显，点击即发）。 */
function renderSuggest(t) {
  const el = document.getElementById('aiq-suggest');
  if (!el) return;
  _guidanceExamplesShown = false;   // 答案后 _followUps 接管 #aiq-suggest，清 examples 占用标志（防 clearGuidanceExamples 误清追问）
  const items = _followUps(t);
  if (!items.length) { el.hidden = true; el.innerHTML = ''; return; }
  el.hidden = false;
  el.innerHTML = '<span class="aiq-suggest-label">追问</span>'
    + items.map((it) => `<button type="button" class="aiq-suggest-chip" data-prompt="${escapeHtml(it.text)}"><span class="aiq-suggest-tag">${escapeHtml(it.tag)}</span>${escapeHtml(it.text)}</button>`).join('');
  el.querySelectorAll('.aiq-suggest-chip').forEach((b) => b.addEventListener('click', () => send(b.dataset.prompt)));
}
function clearSuggest() {
  const el = document.getElementById('aiq-suggest');
  if (el) { el.hidden = true; el.innerHTML = ''; }
  _guidanceExamplesShown = false;   // send/切会话清空时，examples 占用标志同步清
  _curDirection = null;             // 重置阶段 A→B 级联（下次 analyze 重新显方向）
}

/** 长对话折叠：答案摘录（剥离 {{action}} 模板 + 标签，取首 ~70 字）。 */
function _answerExcerpt(msgEl) {
  const ans = msgEl.querySelector('.aiq-answer');
  if (!ans) return '';
  const t = ans.innerText.replace(/\{\{[^}]+\}\}/g, '').replace(/\s+/g, ' ').trim();
  return t.length > 70 ? t.slice(0, 70) + '…' : t;
}
/** 设单条 assistant 消息折叠/展开态。collapsed=true：藏内容显摘要 stub + 钮文"展开"。 */
function _setCollapsed(msgEl, collapsed) {
  if (!msgEl) return;
  msgEl.classList.toggle('is-collapsed', collapsed);
  const stub = msgEl.querySelector('.aiq-collapsed-stub');
  if (stub) {
    stub.hidden = !collapsed;
    if (collapsed) {
      const ex = stub.querySelector('.aiq-collapse-excerpt');
      if (ex) ex.textContent = _answerExcerpt(msgEl) || '（点击展开查看完整回答）';
    }
  }
  const btn = msgEl.querySelector('.emc-collapse-btn');
  if (btn) btn.textContent = collapsed ? '展开' : '折叠';
}
/** 长对话折叠：assistant 消息 > KEEP 条时，自动折叠旧的（留近 KEEP 条展开）；
 *  用户手动展开过的（data-user-expanded）保留展开。在 send 末尾 + restoreHistory 调用。 */
function applyLongConvCollapse() {
  const list = document.getElementById('chat-messages');
  if (!list) return;
  const msgs = [...list.querySelectorAll('.chat-msg-assistant')];
  const total = msgs.length;
  const KEEP = 2;
  msgs.forEach((m, i) => {
    const btn = m.querySelector('.emc-collapse-btn');
    if (btn) btn.hidden = total <= KEEP;                  // 消息少（≤KEEP）不显折叠钮
    if (m.dataset.userExpanded === '1') { _setCollapsed(m, false); return; }
    _setCollapsed(m, i < total - KEEP);                   // 近 KEEP 条展开，其余折叠
  });
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
// ── 答案内图表（{{chart:TYPE|title=..|x=..|y=..}} → Chart.js canvas）──────────────
// 对标 mapgpt/GIS Copilot/ChartGPT：EMC 不再只有文字，排序/对比/趋势直接出图。
// 离散分段配色（遵 ramp-discrete-segments，禁连续渐变）；解析失败留原文不崩（graceful）。
const _CHART_PALETTE = ['#D97757', '#4285F4', '#4ADE80', '#FBBF24', '#A78BFA', '#F472B6', '#34D399', '#60A5FA'];

/** 解析 {{chart:TYPE|title=..|x=labels|y=values}} 紧凑规格 → {type,title,labels,values} 或 null。 */
function _parseChartSpec(raw) {
  const parts = String(raw || '').split('|');
  const type = (parts[0] || '').trim().toLowerCase();
  if (!['bar', 'line', 'pie', 'doughnut'].includes(type)) return null;
  const kv = {};
  for (let i = 1; i < parts.length; i++) {
    const eq = parts[i].indexOf('=');
    if (eq < 0) continue;
    kv[parts[i].slice(0, eq).trim()] = parts[i].slice(eq + 1).trim();
  }
  const labels = (kv.x || kv.labels || '').split(',').map((s) => s.trim()).filter(Boolean);
  const values = (kv.y || kv.values || '').split(',').map((s) => Number(s.trim())).filter((n) => !isNaN(n));
  if (!labels.length || values.length !== labels.length) return null;
  return { type, title: kv.title || '', labels, values };
}

/** 答案内 {{chart:...}} → Chart.js（柱/折/饼）。独占段落的 chart 整段换 wrap div（最干净），
 *  残留内联的换内联 canvas 兜底。EMC 深色主题 → 浅色字。解析失败留 <code> 不崩。 */
function _renderCharts(el) {
  if (!el || !window.Chart) return;
  if (!window.Chart._emcThemed) {
    window.Chart.defaults.color = '#9ca3af';            // EMC 深色答案泡 → 浅色刻度/标签
    window.Chart.defaults.borderColor = 'rgba(255,255,255,0.08)';
    window.Chart.defaults.font.family = 'system-ui, "Microsoft YaHei", sans-serif';
    window.Chart._emcThemed = true;
  }
  const specs = [];
  // 单次扫描：兼容 1~2 个花括号（.format 后 {{chart}}→{chart} 单括号；模型也可能双括号）。
  //  独占段落（<p>{{chart:..}}</p>）→ wrap div；内联 → inline span。bad 用 HTML 实体编码花括号防二次匹配嵌套。
  el.innerHTML = el.innerHTML.replace(/(<p>\s*)?\{{1,2}chart:([^}]+?)\}{1,2}(\s*<\/p>)?/gi, (m, p1, spec, p2) => {
    const s = _parseChartSpec(spec);
    if (!s) return `<code class="aiq-chart-bad">&#123;&#123;chart:${spec}&#125;&#125;</code>`;
    specs.push(s);
    return p1 ? `<div class="aiq-chart-wrap"><canvas class="aiq-chart"></canvas></div>`
      : `<span class="aiq-chart-wrap aiq-chart-inline"><canvas class="aiq-chart"></canvas></span>`;
  });
  if (!specs.length) return;
  el.querySelectorAll('canvas.aiq-chart').forEach((cv, i) => {
    if (cv.dataset.bound || !specs[i]) return;
    const s = specs[i];
    cv.dataset.bound = '1';
    const colors = s.values.map((_, k) => _CHART_PALETTE[k % _CHART_PALETTE.length]);
    const isPie = s.type === 'pie' || s.type === 'doughnut';
    const isLine = s.type === 'line';
    try {
      new window.Chart(cv, {
        type: s.type,
        data: { labels: s.labels, datasets: [{
          label: s.title || '数据', data: s.values,
          backgroundColor: isLine ? 'rgba(217,119,87,0.18)' : (isPie ? colors : colors.map((c) => c + 'CC')),
          borderColor: isLine ? '#D97757' : colors, borderWidth: 2,
          fill: isLine, tension: 0.3,
        }] },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { title: { display: !!s.title, text: s.title, font: { size: 13 } },
                     legend: { display: isPie, position: 'right' } },
          scales: isPie ? {} : { x: { grid: { display: false } }, y: { beginAtZero: true } },
        },
      });
    } catch (e) { /* 解析/渲染失败不崩，留 canvas 空位 */ }
  });
}

/** 答案内 {{fig:ID}} → <img>（run_python 工具产图，figId→dataUri 从 tools.js _figCache 取）。
 *  范式照 _renderCharts：兼容 1~2 花括号（marked.parse 后 {{→{ 单括号，模型也可能单括号）、
 *  独占段落 wrap div、内联 span、解析失败留 <code>（HTML 实体编码花括号防二次匹配）。 */
function _renderFigs(el) {
  if (!el) return;
  el.innerHTML = el.innerHTML.replace(
    /(<p>\s*)?\{{1,2}fig:(\w+)(\s*<\/p>)?/gi,
    (m, p1, figId) => {
      const dataUri = getFig(figId);   // figId=\w+ 纯字母数字，安全无需 escape
      if (!dataUri) {
        return `<code class="aiq-fig-bad">&#123;&#123;fig:${figId}&#125;&#125;（图缺失）</code>`;
      }
      const img = `<img class="aiq-fig" src="${dataUri}" alt="${figId}" loading="lazy" />`;
      return p1
        ? `<div class="aiq-fig-wrap">${img}</div>`
        : `<span class="aiq-fig-wrap aiq-fig-inline">${img}</span>`;
    }
  );
}

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
  _renderCharts(el);   // 答案内 {{chart:...}} → Chart.js（所有 renderAnswer 站点经此覆盖）
  _renderFigs(el);     // 答案内 {{fig:ID}} → <img>（run_python 产图，所有 renderAnswer 站点经此覆盖）
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
      : strat === 'fallback_annotated' ? '（结论将标注口径（=统计范围）局限）' : ''}</div>`
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
  clearSuggest();   // 新一轮提问：清上一轮的推荐追问胶囊
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
    <div class="aiq-collapsed-stub" hidden><span class="aiq-collapse-chev">▸</span><span class="aiq-collapse-excerpt"></span></div>
    <div class="aiq-card aiq-card-diagnose" hidden></div>
    <div class="aiq-reason ${isFlash ? 'is-flash' : ''}" ${hasReason ? '' : 'hidden'}><div class="aiq-reason-head"><span class="aiq-reason-title">${isFlash ? 'Flash · 直接作答' : 'Thinking…'}</span><span class="aiq-reason-meta"></span></div><div class="aiq-reason-body"></div></div>
    <div class="aiq-steps" ${trace && trace.steps && trace.steps.length ? '' : 'hidden'}><div class="aiq-steps-head">工具调用（Agent Loop）</div></div>
    <div class="aiq-review" ${trace && trace.review ? '' : 'hidden'}><div class="aiq-review-head">审查</div><div class="aiq-review-body"></div></div>
    <div class="aiq-step aiq-step-final"><span class="aiq-step-tag">结论</span><div class="aiq-answer"><span class="aiq-answer-stream"></span><span class="chat-cursor" hidden>▍</span></div></div>
    <div class="aiq-card aiq-card-caliber" hidden></div>
    <div class="aiq-answer-footer" hidden></div>
  </div>
  <div class="emc-msg-actions"><button class="emc-collapse-btn" type="button" title="折叠/展开" hidden>折叠</button><button class="emc-copy-btn" type="button" title="复制回答"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h8"/></svg></button></div>`;
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
    // P1：ask_user 历史恢复——重建选项胶囊（onAskUser 存了 trace.ask，刷新/切会话后重渲染 + rebind 点击）
    if (trace.ask && trace.ask.type === 'ask_user') {
      const _opts = Array.isArray(trace.ask.options) ? trace.ask.options : [];
      if (_opts.length) {
        const _optDiv = document.createElement('div');
        _optDiv.className = 'aiq-ask-options';
        _optDiv.innerHTML = _opts.map((o) => `<button type="button" class="aiq-suggest-chip aiq-ask-chip" data-prompt="${escapeHtml(o)}"><span class="aiq-suggest-tag">选项</span>${escapeHtml(o)}</button>`).join('');
        shell.answerEl.appendChild(_optDiv);
        _optDiv.querySelectorAll('.aiq-ask-chip').forEach((b) => b.addEventListener('click', () => send(b.dataset.prompt)));
      }
    }
    updateReasonMeta(shell, trace);
    if (trace.diagnose) renderDiagnoseCard(shell.diagnoseEl, trace.diagnose);
    if (trace.caliber) renderCaliber(shell, trace.caliber);
    if (trace.doneAt && shell.footerEl) {
      _renderFooter(shell, '回答完毕 · 情绪地图测试版 v1.0 · ' + formatTs(trace.doneAt), trace.final, _exitBadge(trace));
    }
    reorganizeReason(shell);   // 历史会话思考也切主题目录（与实时路径一致）
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
  /** 思考收尾：flush 最后一帧 RAF 文本到 DOM → 整块 is-done → reorganizeReason 切主题目录。 */
  function finalizeReason() {
    if (isFlash || !shell.reasonEl) return;
    if (reasonRaf) { cancelAnimationFrame(reasonRaf); reasonRaf = 0; }
    for (const r of Object.keys(reasonSegs)) {
      const body = shell.reasonBody.querySelector(`.aiq-reason-segment[data-round="${r}"] .aiq-reason-seg-body`);
      if (body) body.textContent = reasonSegs[r];
    }
    flushReasonSegs();
    if (Object.keys(reasonSegs).length) {
      shell.reasonEl.classList.add('is-done');
      reorganizeReason(shell);
    } else {
      shell.reasonEl.hidden = true;
    }
  }

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
    onAskUser: (action, round) => {
      // P1 主动问澄清：步骤卡显"问澄清"+问题摘要；答案区渲染问题 + 选项胶囊（复用 aiq-suggest-chip）；用户点选项 → send 续作。
      cancelStream();
      stopThinking();
      updateContextCapacity(getLastUsage());
      const card = shell.stepsEl.querySelector(`.aiq-toolcard[data-round="${round}"]`);
      if (card) {
        card.querySelector('.aiq-toolcard-name').textContent = '问澄清';
        card.querySelector('.aiq-toolcard-target').textContent = '· ' + String(action && action.question || '').slice(0, 40);
      }
      if (_curTrace && _curTrace.steps.length) _curTrace.steps[_curTrace.steps.length - 1].action = action;
      const q = (action && action.question) || '请补充一点信息，我接着分析';
      const opts = Array.isArray(action && action.options) ? action.options : [];
      let html = renderAnswer(q, getValidRefNames());
      if (opts.length) {
        html += '<div class="aiq-ask-options">' + opts.map((o) => `<button type="button" class="aiq-suggest-chip aiq-ask-chip" data-prompt="${escapeHtml(o)}"><span class="aiq-suggest-tag">选项</span>${escapeHtml(o)}</button>`).join('') + '</div>';
      }
      shell.answerEl.innerHTML = html;
      enhanceCodeBlocks(shell.answerEl);
      shell.answerEl.querySelectorAll('.aiq-ask-chip').forEach((b) => b.addEventListener('click', () => send(b.dataset.prompt)));
      if (_curTrace) { _curTrace.exit = 'ask'; _curTrace.ask = action; _curTrace.final = q; }
      shell._finalMd = q;
      finalizeReason();
      autoScroll();
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
      finalizeReason();   // flush 最后一帧思考 + 整块 is-done + 主题目录重切
      if (_curTrace) _curTrace.final = text;
      shell._finalMd = text;   // 供页脚「复制回答」取最终 markdown
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
      shell._finalMd = text;   // 重写后更新最终 markdown
      const v = shell.reviewBody.querySelector('.aiq-review-verdict.fail');
      if (v) v.textContent = '审查未过·已重写';
      autoScroll();
    },
    onDegraded: (_text) => {
      cancelStream();
      stopThinking();
      // 永不裸输原始 token（根治代码块/计划文泄漏）：固定降级卡，忽略传入的 raw 文本
      const _degradedText = '## 暂未能完成此分析\n\n模型输出未能解析为可执行动作，且最终结论生成失败。\n\n**建议**：换一种问法或缩小范围（指定某区、某类用地、某时点）后重试；若反复失败，可上传更明确的数据范围。';
      shell.answerEl.innerHTML = renderAnswer(_degradedText, getValidRefNames());
      enhanceCodeBlocks(shell.answerEl);
      if (_curTrace) { _curTrace.exit = 'gap'; _curTrace.final = _degradedText; }
      shell._finalMd = _degradedText;
      finalizeReason();   // 降级前已流式的思考也结构化（无思考内容则藏 reason 块）
    },
  };
}

/** 蒸馏单个 assistant trace → 一轮上下文摘要（intent/method/已做/缺口/strategy）。 */
function _distillTurn(h) {
  const t = h.trace, dg = t.diagnose || {}, dp = (dg.data_plan || {});
  const method = Array.isArray(dg.method) ? dg.method.join(' → ') : (dg.method || '');
  const done = (t.steps || []).map((s) => {
    const a = s.action || {};
    if (a.type === 'ask_user') return '问澄清：' + String(a.question || '').slice(0, 30);   // ask 无 name/params，特化避免 '已做=?' 噪声
    return `${a.name || '?'}${a.params ? '(' + JSON.stringify(a.params).slice(0, 50) + ')' : ''}`;
  }).join('；');
  const gap = ((t.caliber && t.caliber.length) ? t.caliber : (dp.gap || [])).join('、');
  return { intent: dg.intent || '', method, done: done || '（无工具调用）', gap: gap || '', strategy: dp.strategy || '' };
}

/** 收集最近 maxN 轮 assistant trace → oldest-first 列表（B2 多轮滚动记忆）。
 *  trace 全量已存 _history/localStorage；旧逻辑只回灌上 1 轮 final → 续作失忆，此处扩多轮结构化。 */
function _buildTurnHistory(maxN = 3) {
  const turns = [];
  for (let i = _history.length - 2; i >= 0 && turns.length < maxN; i--) {   // -1 = 当前 user；往前收末 maxN 个 assistant
    const h = _history[i];
    if (h.role === 'assistant' && h.trace) turns.push(_distillTurn(h));
  }
  return turns.reverse();   // oldest-first（意图收敛轨迹：旧→新）
}

/** 蒸馏上一个 assistant trace → priorTurn（单轮；harness 的 gis_operation 续作检查仍用此）。 */
function _buildPriorTurn() {
  return _buildTurnHistory(1)[0] || null;
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
    priorTurn: _buildPriorTurn(),               // 多轮连续性：上轮 intent/method/已做/缺口（续作承接；harness gis 续作检查用）
    turnHistory: _buildTurnHistory(3),          // B2 多轮滚动记忆：最近 ≤3 轮（意图收敛轨迹，旧→新），注入 ctx.context 顶部
    resume: false };
  // P1：上一轮以 ask_user 结束（用户点选项胶囊续作）→ 强制续作，跳过 general/request_upload 短路，承接上轮 method（选项文本不含"继续/那个"等线索词，正则识别不到）
  const _prevTrace = _history.length >= 2 ? (_history[_history.length - 2].trace || null) : null;
  const _resumingAsk = !!(_prevTrace && _prevTrace.exit === 'ask');
  ctx.resume = _resumingAsk || !!(ctx.priorTurn && _isResumeCue(text));
  // P1 ask_user 速率上限：连续问 ≥2 次后，本轮注入"禁止再 ask_user"，防博弈式无限追问逃避执行
  if (_consecutiveAsks >= 2) {
    ctx.context = '【澄清上限】已连续问过 ' + _consecutiveAsks + ' 次澄清，本轮**禁止 ask_user**——必须基于现有信息直接 answer 或调工具完成，不得再问。\n\n' + (ctx.context || '');
  }
  let settled = false;
  try {
    const _result = await orchestrate(ctx, buildHooks(shell));
    settled = true;
    if (_curTrace && _result) { _curTrace.exit = _result.exit || _curTrace.exit; _curTrace.newLayerCount = _result.newLayerCount; }
    if (_result && _result.exit === 'ask') _consecutiveAsks++; else _consecutiveAsks = 0;   // P1 ask 连续计数（跨 orchestrate，≥2 触发下轮禁止）
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
    applyLongConvCollapse();   // 长对话折叠：新答完毕后，折叠旧的留近 N 展开
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
    // CPD G1 引擎接缝（plan §4.3·H1 修 general 断链）：settled 守卫 dispatch turn-ended（覆盖 general exit=null）
    // + 单调去重（cpd-guide.js turnId > lastProcessed）。abort（settled=false）不 dispatch（无假 exit 信号）。
    if (settled) document.dispatchEvent(new CustomEvent('cpd:turn-ended', {
      detail: { exit: _curTrace?.exit ?? null, turnId: _history.length, intent: _curTrace?.diagnose?.intent ?? null },
    }));
    recomputeGuidance();   // abort/streaming 后恢复引导（settled=false 不 dispatch，但仍按当前状态重算 guide）
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
  _scheduleFit();   // CPD：欢迎卡显/隐→内容高变→重算 panel 高（缩回欢迎卡高度；内容增则拉长）
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
  applyLongConvCollapse();   // 长对话折叠：恢复后按近 N 展开折叠旧消息
  clearSuggest();   // 历史/切换会话：不沿用上一轮的推荐追问
}

function clearChat() {
  _history = [];
  _consecutiveAsks = 0;   // P1: 重置跨会话 ask 计数（防上会话泄漏到新会话首问·chat-new 复用 clearChat 同样覆盖）
  saveHistory();
  restoreHistory();
  _scheduleFit();   // CPD：新对话回欢迎卡→显式触发高度缩回（保险，不单靠 MutationObserver）
  recomputeGuidance();   // CPD G1：切会话/新对话恢复引导（reset 去重 + 按 _history=[] 重算→import）
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
  if (v === 'chat') _scheduleFit();   // CPD：切回对话视图→内容驱动重算高度
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
    + (it.isCurrent ? '' : `<button class="emc-history-del" data-id="${it.id}" title="删除该会话"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7h14M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M7 7l1 13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1l1-13"/></svg></button>`)
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
  const stub = e.target.closest('.aiq-collapsed-stub');   // 长对话折叠：点摘要 stub 展开
  if (stub) {
    const msg = stub.closest('.chat-msg-assistant');
    if (msg) { _setCollapsed(msg, false); msg.dataset.userExpanded = '1'; }
    return;
  }
  const colBtn = e.target.closest('.emc-collapse-btn');   // 折叠/展开钮
  if (colBtn) {
    const msg = colBtn.closest('.chat-msg-assistant');
    if (msg) {
      const willCollapse = !msg.classList.contains('is-collapsed');
      _setCollapsed(msg, willCollapse);
      if (willCollapse) delete msg.dataset.userExpanded; else msg.dataset.userExpanded = '1';
    }
    return;
  }
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
  if (reason) {
    const topicHead = e.target.closest('.aiq-reason-topic-head');   // 主题折叠：点主题标题切该主题（不冒泡整块）
    if (topicHead) { topicHead.closest('.aiq-reason-topic')?.classList.toggle('is-open'); return; }
    if (e.target.closest('.aiq-reason-head')) reason.classList.toggle('is-open');   // 仅点"Thought for Ns"标题条收/展整块；body 内其他位置不触发
    return;
  }
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
      + '</div></div>'
      + '<div class="aiq-suggest" id="aiq-suggest" hidden></div>';   // 推荐追问胶囊（答案完毕后显，点击即发）
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
// ── CPD：EMC 浮窗化（reparent 到 #map + 自持缩放手柄 + 尺寸持久化）──
//   #emc-panel DOM 仍在 #left-panel（index.html），运行期 reparent 到 #map 作浮窗
//   （position:absolute 锚 #map，见 layout.css）。缩放用自持 .emc-resize-grip（显眼斜线符号，
//   pointer 事件驱动，min/max 钳制不压比例尺）—— 替代难发现的原生 resize 角；ResizeObserver 存 localStorage。
//   原 setEmcMode 三档自动调高（写 --emc-h）随浮窗化退役为无害 no-op（height 固定 + grip 自持）。
function _setupEmcFloat() {
  const emc = document.getElementById('emc-panel');
  const map = document.getElementById('map');
  if (!emc || !map) return;
  if (emc.parentElement !== map) map.appendChild(emc);   // reparent 到 #map（幂等）
  // F5 默认尺寸（不记忆上轮 resize·用户定 2026-07-22）：宽 430（欢迎卡副标题整句一行）× 高 640
  emc.style.width = '430px';
  emc.style.height = '640px';
  // 自持缩放手柄（pointer 事件；min 300×200 / max 不压比例尺，与 CSS max-height 同步）
  if (!emc.querySelector('.emc-resize-grip')) {
    const grip = document.createElement('div');
    grip.className = 'emc-resize-grip';
    grip.title = '拖拽调整窗口大小';
    grip.innerHTML = '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true">'
      + '<path d="M11 5.5L5.5 11M14 8.5L8.5 14M8 14L14 8" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linecap="round"/></svg>';
    emc.appendChild(grip);
    let dragging = false, sx = 0, sy = 0, sw = 0, sh = 0;
    grip.addEventListener('pointerdown', (e) => {
      if (emc.classList.contains('is-collapsed')) return;   // 折叠态不缩放
      e.preventDefault(); e.stopPropagation();
      dragging = true; sx = e.clientX; sy = e.clientY;
      sw = emc.offsetWidth; sh = emc.offsetHeight;
      try { grip.setPointerCapture(e.pointerId); } catch (_) {}
    });
    grip.addEventListener('pointermove', (e) => {
      if (!dragging) return;
      const minW = 300, minH = 200;
      const maxW = Math.floor(window.innerWidth * 0.92);
      const maxH = Math.max(minH, window.innerHeight - 138);   // 与 layout.css max-height 同步（top40+底留50）
      emc.style.width = Math.max(minW, Math.min(maxW, sw + (e.clientX - sx))) + 'px';
      emc.style.height = Math.max(minH, Math.min(maxH, sh + (e.clientY - sy))) + 'px';
    });
    const end = (e) => { if (!dragging) return; dragging = false; try { grip.releasePointerCapture(e.pointerId); } catch (_) {} };
    grip.addEventListener('pointerup', end);
    grip.addEventListener('pointercancel', end);
  }
  // ResizeObserver：尺寸变化（grip 拖动 / 恢复）→ 持久化（rAF 节流，折叠态不存）
  let raf = 0;
  if (typeof ResizeObserver !== 'undefined' && !emc._floatObs) {
    emc._floatObs = new ResizeObserver(() => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        if (emc.classList.contains('is-collapsed')) _fitCollapsedText();   // CPD：折叠态宽度变 → 文本自适应重排
        relayoutFloats();        // CPD ③④：EMC 宽度变 → 抽屉 + param-panel 浮层自适应重排
      });
    });
    emc._floatObs.observe(emc);
  }
}

// ── CPD：内容驱动高度自适应（用户定 2026-07-22）──
//   chat-messages 内容增→panel 拉长至容纳（不超 max-height，超则内部滚）；内容减/跳欢迎卡→缩短。
//   增量法：need = panel高 - msgs可见高 + msgs内容总高（= 非内容部分 head/input/suggest + 内容总高）。
//   rAF 节流防抖（流式 characterData 高频触发）；折叠态/历史视图跳过。grip 手动拖动改 height 不触发
//   chat-messages MutationObserver，故用户拖大后内容不变→保持手动尺寸，内容再变才重算。
let _fitRaf = 0;
function _fitEmcToContent() {
  if (_emcCollapsed) return;
  if (_view === 'history') return;   // 历史列表自管高度
  const emc = document.getElementById('emc-panel');
  const msgs = document.getElementById('chat-messages');
  if (!emc || !msgs) return;
  const minH = 360;   // 下限（保 head + input + 最小消息区；同 EMC_MIN 量级）
  const maxH = Math.max(minH, window.innerHeight - 138);   // 同 layout.css max-height（top30+底留约108）
  // 非内容部分（head/suggest/input）= panel - msgs 当前撑满可见高
  const nonContent = emc.offsetHeight - msgs.clientHeight;
  // 内容自然高：临时取消 flex 拉伸量真实高——直接 scrollHeight 在「内容<可见区」时 = clientHeight
  // （flex 撑满致失真，是"缩短"失效根因；内容多溢出时 scrollHeight 才大于 clientHeight，故"拉长"原正常）
  const sf = msgs.style.flex, sh = msgs.style.height;
  msgs.style.flex = '0 0 auto'; msgs.style.height = 'auto';
  const contentH = msgs.offsetHeight;
  msgs.style.flex = sf; msgs.style.height = sh;   // 同步恢复（同帧不绘制无闪烁；style 变不触发 MutationObserver）
  const need = nonContent + contentH;
  emc.style.height = Math.max(minH, Math.min(maxH, need)) + 'px';
}
function _scheduleFit() {
  if (_fitRaf) return;
  _fitRaf = requestAnimationFrame(() => { _fitRaf = 0; _fitEmcToContent(); });
}
function _setupEmcContentFit() {
  const msgs = document.getElementById('chat-messages');
  if (msgs && !msgs._fitObs) {
    msgs._fitObs = new MutationObserver(() => _scheduleFit());
    msgs._fitObs.observe(msgs, { childList: true, subtree: true, characterData: true });
  }
}

// ── CPD Phase 2a：EMC 顶部软折叠栏（5 步进度条 + Layers/Range/Toolbox 摘要 chip）──
//   软折叠：chip 行始终可达（业内同行可一键聚焦左栏对应 tab）；进度点据 curState 染色。
//   chip 点击派发 cpd:focus-tab → sidebar.js 监听切 tab + 展开左栏（2a 桥接，左栏暂不移除）。
function _setupCpdBar() {
  const emc = document.getElementById('emc-panel');
  if (!emc || emc.querySelector('.emc-cpd-bar')) return;
  const bar = document.createElement('div');
  bar.className = 'emc-cpd-bar';
  // 进度条（5 点 + 步骤标签）
  const prog = document.createElement('div');
  prog.className = 'emc-cpd-prog';
  // CPD ③：进度行加「进度」说明 + 每点描述性 hover title（明确意义，去「意义不明」）
  prog.innerHTML = '<span class="emc-cpd-prog-cap">进度</span>'
    + CPD_STEPS.map((s, i) => `<span class="emc-cpd-dot" data-idx="${i}" title="步骤 ${i + 1}/${CPD_STEPS.length}：${s.label}"></span>`).join('')
    + '<span class="emc-cpd-prog-label">—</span>';
  bar.appendChild(prog);
  // chip 行（软折叠·始终可达；图层 chip 带计数）
  const chips = document.createElement('div');
  chips.className = 'emc-cpd-chips';
  chips.innerHTML =
    '<button class="emc-cpd-chip" data-tab="layers" title="图层管理">'
    + '<span class="emc-cpd-chip-lbl">图层</span><span class="emc-cpd-chip-cnt" data-cnt="layers">0</span></button>'
    + '<button class="emc-cpd-chip" data-tab="range" title="指定范围"><span class="emc-cpd-chip-lbl">范围</span></button>'
    + '<button class="emc-cpd-chip" data-tab="toolbox" title="空间分析工具"><span class="emc-cpd-chip-lbl">工具</span></button>';
  bar.appendChild(chips);
  // CPD v1.2 双域 UI：展开态提示条（进度点上方·收起态随 .emc-cpd-bar display:none 隐藏）。
  // EMC 接手时 CPD 同步进界面作提示语（去光环·阴影·Light/Dark），点击 = 光环同款 CTA。
  const hint = document.createElement('div');
  hint.className = 'emc-cpd-hint';
  hint.hidden = true;
  hint.innerHTML = '<span class="emc-cpd-hint-text"></span><span class="emc-cpd-hint-arrow" aria-hidden="true">›</span>';
  hint.title = '点击执行下一步';
  hint.addEventListener('click', () => { if (_curGuidance) _runGuidanceCta(_curGuidance.ctaKind); });
  bar.prepend(hint);   // 进度点 .emc-cpd-prog 上方
  // 插入 chat-head 之后（chat-head 之下、emc-view 之上）
  const head = emc.querySelector('.chat-head');
  if (head) head.after(bar); else emc.prepend(bar);
  // chip 点击 → 聚焦左栏 tab（sidebar.js 监听 cpd:focus-tab）
  bar.querySelectorAll('.emc-cpd-chip').forEach((c) =>
    c.addEventListener('click', () => document.dispatchEvent(new CustomEvent('cpd:focus-tab', { detail: c.dataset.tab }))));
  // 渲染：进度点染色 + 步骤标签 + 图层计数
  const render = () => {
    const idx = getCurStepIdx();
    bar.querySelectorAll('.emc-cpd-dot').forEach((d, i) => {
      d.classList.toggle('is-cur', i === idx);
      d.classList.toggle('is-done', i < idx);
    });
    const lbl = bar.querySelector('.emc-cpd-prog-label');
    if (lbl && CPD_STEPS[idx]) lbl.textContent = `${idx + 1}/${CPD_STEPS.length} · ${CPD_STEPS[idx].label}`;
    const cnt = bar.querySelector('[data-cnt="layers"]');
    if (cnt) cnt.textContent = String(document.querySelectorAll('#layer-list .layer-row').length);
  };
  subscribe(render);
  document.addEventListener('layers:changed', render);
  render();
  initCpdState();   // 启动状态推导 + 全局监听

  // CPD G1：引导引擎落地接线（cpd-guide.js 派发 cpd:guidance → 套光环/文案；光环 click → CTA）。
  document.addEventListener('cpd:guidance', (e) => {
    _curGuidance = (e && e.detail && e.detail.guidance) || null;
    _applyGuidance();
    _renderGuidanceContent();   // 展开态：intent=方向级联(A/B) / interpret=examples / 其余清（首次分析前显·有答案 _followUps 接管）
  });
  // 光环可点 CTA（plan §八 G1·U2）：折叠态有引导时，点 .emc-input-area = CTA（拦截 focus-expand）。
  const area = emc.querySelector('.emc-input-area');
  if (area && !area._cpdCta) {
    area._cpdCta = true;
    area.addEventListener('mousedown', (e) => {
      if (_emcCollapsed && _curGuidance) e.preventDefault();   // 拦截 textarea 聚焦（聚焦会展开，与 CTA 冲突）
    });
    area.addEventListener('click', () => {
      if (!_emcCollapsed || !_curGuidance) return;             // 无引导：默认 focus→展开（既有行为）
      _runGuidanceCta(_curGuidance.ctaKind);
      suppressGuidance();                                      // engage 解除（同 kind 不重亮·plan §6.2.3）
      const panel = document.getElementById('emc-panel');
      if (panel) panel.classList.remove('has-guidance');       // 立即移除光环（下次状态变化 _compute 重算）
      const input = document.getElementById('chat-input');
      if (input) { input.placeholder = _INPUT_PH_COLLAPSED; _fitCollapsedText(); }
    });
  }
}

export function initChatPanel() {
  _setupEmcFloat();   // CPD Phase 1b：reparent EMC 到 #map 浮窗 + 恢复尺寸（先于事件绑定）
  _setupCpdBar();     // CPD Phase 2a：顶部进度条 + 摘要 chip（软折叠）
  // CPD Phase 3b：主题切换（仅 #emc-panel scope，chrome 保持 Light）。localStorage 持久化。
  const _applyTheme = (t) => {
    document.documentElement.setAttribute('data-theme', t);
    const b = document.getElementById('chat-theme');
    if (b) b.title = (t === 'light') ? '切换 Dark 主题' : '切换 Light 主题';
  };
  try { _applyTheme(localStorage.getItem('emc-theme') || 'light'); } catch (_) { _applyTheme('light'); }   // CPD：默认 Light（用户定）
  document.getElementById('chat-theme')?.addEventListener('click', () => {
    const cur = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = cur === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('emc-theme', next); } catch (_) {}
    _applyTheme(next);
  });
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
  // 容量圆圈 hover 弹富 tooltip（5 类明细）
  const cap = document.getElementById('ctx-cap');
  if (cap && !cap.dataset.capTip) {
    cap.dataset.capTip = '1';
    cap.addEventListener('mouseenter', _ctxCapShowTip);
    cap.addEventListener('mouseleave', _ctxCapHideTip);
  }
  document.getElementById('chat-history')?.addEventListener('click', () => toggleHistoryView());
  document.getElementById('emc-history-clear')?.addEventListener('click', clearAllHistory);
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
  // F5 启动：上轮当前会话归档进 _archive（可从历史记录翻看，不丢），主区从欢迎卡开场·用户定 2026-07-22
  if (_history.length) {
    _archive.unshift({ id: 's' + Date.now(), title: _titleOf(_history), history: [..._history], createdAt: Date.now() });
    _history = [];
    saveArchive(); saveHistory();
  }
  restoreHistory();
  mountChatChrome();
  _setupEmcContentFit();   // CPD：内容驱动高度自适应（监听 chat-messages DOM 变化）
  setupEmcHeightObservers();
  setEmcMode('comfort');

  // 折叠键 + 输入框触发展开 + 折叠态持久化恢复
  document.getElementById('chat-collapse')?.addEventListener('click', () => setEmcCollapsed(!_emcCollapsed));
  input?.addEventListener('focus', () => { if (_emcCollapsed) setEmcCollapsed(false); });   // 折叠态点输入框 → 展开
  if (_emcCollapsed) {
    document.getElementById('emc-panel')?.classList.add('is-collapsed');   // 初始即折叠：套类（局部覆盖 --emc-h=40px + min-height:0）
    if (input) input.placeholder = _INPUT_PH_COLLAPSED;
    _fitCollapsedText();   // CPD：初始折叠态文本自适应
  }
  // CPD G1：启动引导引擎（依赖注入 getter；首次 _compute 读末条 trace.exit 恢复引导·plan §4.3）。
  // 放 F5 归档（_history=[]）之后，保证首算用最终 _history。
  initCpdGuide({
    getLastExit: () => _history.at(-1)?.trace?.exit ?? null,
    isStreaming: () => _streaming,
    getLastRegion: _lastRegion,
    isCollapsed: () => _emcCollapsed,
  });
}
