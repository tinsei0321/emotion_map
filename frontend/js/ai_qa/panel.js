// ═══ panel.js — AI 问答 UI（底部滑出 · agent loop · 历史持久化 · 思考深度开关 · 动态状态）═══
import { orchestrate, getTemplateStats } from './harness.js';
import { createAcpChannel, ACP_FAMILY } from './acp-channel.js';   // S3：壳对话框架事件化（hooks→ACP bus）
import { runAcpMockPeer } from './acp-mock-peer.js';   // S3 主体：mock 对端（?engine=mock / ?acp-mock=1 启用·默认零副作用）
import { getEngineMode, runDshEngine } from './brain-adapter-dsh.js';   // 壳二期 BA：dsh headless 引擎（?engine=dsh·三引擎切换·降级形态 synthesized）
import { runCodexEngine } from './brain-adapter-codex.js';   // PT-CB15 SPIKE：Codex app-server 引擎（?engine=codex·全量形态真流式）
import { normalizeFollowupCues, pickFollowupSource } from './followup.js';   // SHELL2(FIX) FIX-09：追问纯逻辑（可单测·语义与原内联逐字一致）
import { buildContext, buildOptimizeContext, TOOLS, resetStepResults, resetCurrentResults, cleanupConsumedResults, getFig } from './tools.js';
import { initCpdState, subscribe, getCurStepIdx, CPD_STEPS, relayoutFloats } from './cpd-state.js';
import { initCpdGuide, recomputeGuidance, refreshGuidance, suppressGuidance } from './cpd-guide.js';   // CPD：引导引擎（依赖注入，零反向 import）
import { getLayers, selectLayer, getSelectedLayer } from '../state.js';
import { getLastUsage, resetCallStats, getCallStats } from './api.js';
import { SKILL_DEFS, optimizeStep } from './stages.js';   // 阶段 D 参数引导 + 5.215 optimizeStep（LLM 优化 prompt）

const HISTORY_KEY = 'ai_qa_history_v1';
const ARCHIVE_KEY = 'ai_qa_archive_v1';
const MODE_KEY = 'ai_qa_think_mode';
const _INPUT_PH_EXPANDED = '问 EMC：哪些区域情绪最差？为什么？  （Enter 发送 · Shift+Enter 换行 · Esc 中断）';
const _INPUT_PH_COLLAPSED = '向 EmotionMap Copilot 提问：了解"情绪地图"，观察、分析、总结城市情绪数据。';

// 动态思考状态文案（轮换，随机感；参考 Claude/ChatGPT "正在思考"动态提示）。
const THINK_PHRASES = ['正在思考', '正在分析', '正在计算', '正在构思', '正在比对数据', '正在归纳', '正在权衡证据', '正在检索线索', '正在梳理逻辑'];

let _streaming = false;
let _t0 = 0, _phaseTs = {}, _elapsedTimer = null, _layerBase = 0, _abortDelegation = false;   // E2 进度透明（治 C9）：总起始/阶段时间戳/计时循环/图层基线/取消 delegation
let _abortCtl = null;
let _history = loadHistory();
let _archive = loadArchive();
let _curTrace = null;
let _pendingStruct = null;   // 出口三段式 P0：结果结构化暂存（harness onResultStruct → onFinalDone 统一渲染观点卡/4要点卡）
let _consecutiveAsks = 0;   // P1 ask_user 跨 orchestrate 连续计数：≥2 时下轮注入"禁止再 ask_user"防博弈式无限追问（MAX_ROUNDS 对 ask 无效，因 ask 直接 return 不计 round）
let _thinkMode = localStorage.getItem(MODE_KEY) || 'flash';   // WS1 F1.1：默认 flash（去 deliberate 串行·治超时）·复杂问题手动开 Pro | 'pro' | 'flash'
// CB-12（用户拍板）：flash 足够·**强制 flash**——pro 停用（localStorage 有 pro 也强制回 flash·防残留）
if (_thinkMode !== 'flash') { _thinkMode = 'flash'; localStorage.setItem(MODE_KEY, 'flash'); }
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
  // 所有 kind → 展开 EMC 对话框 + input 聚焦 + 引导内容（5.224 治 Bug5·移除 cpd:focus-tab 切走·用户点胶囊期望留在 EMC）
  const input = document.getElementById('chat-input');
  if (input) { setEmcCollapsed(false); input.focus(); }
  _renderGuidanceContent();   // 展开 + 显引导内容（含补数据提示·非切 tab 离开 EMC）
}

// ── CPD 阶段 A/B 引导内容（导游·确定性·不调 LLM·意图识别归 harness）──
// intent（点+范围就绪）= 阶段 A 大方向胶囊 → 阶段 B 细化追问胶囊；interpret（dock 产图）= examples 读图。
let _guidanceCardShown = false;       // CPD 引导焦点卡片占用 #chat-messages 标志（与欢迎卡/追问互斥）
let _curDirection = null;             // 阶段 A→B 级联：用户选的大方向（null=显方向；已选=显细化）
/** 引导卡片仅在「从未问答过」（首次分析前）显——一旦有答案，追问 _followUps 接管（互斥）。 */
function _shouldShowGuidanceExamples() {
  return !_streaming && !_history.some((h) => h.role === 'assistant');
}
/** 点击引导选项 → 填入对话框（不直接发·让用户确认/编辑后自发送·导游不代决定）。 */
function _fillInput(text) {
  const input = document.getElementById('chat-input');
  if (!input) return;
  input.value = text;
  input.style.height = 'auto';
  input.style.height = Math.min(160, input.scrollHeight) + 'px';   // textarea 自适应高度
  input.focus();
}
/** 渲染 CPD 引导焦点卡片到 #chat-messages 主显示区（视觉焦点·大卡片·取代边缘小胶囊·用户定）。
 *  @param {{title:string, opts:[{tag?,text,dir?,prompt?}], back?:boolean}} spec */
function _renderGuideCard(spec) {
  const list = document.getElementById('chat-messages');
  if (!list || !spec || !Array.isArray(spec.opts) || !spec.opts.length) return;
  let card = list.querySelector('.cpd-guide-card');
  if (!card) { card = document.createElement('div'); card.className = 'cpd-guide-card'; list.prepend(card); }
  const optHtml = (o) => {
    const tag = o.tag ? `<span class="cpd-guide-opt-tag">${escapeHtml(o.tag)}</span>` : '';
    const attrs = `${o.dir ? ` data-dir="${escapeHtml(o.dir)}"` : ''}${o.prompt ? ` data-prompt="${escapeHtml(o.prompt)}"` : ''}`;
    return `<button type="button" class="cpd-guide-opt"${attrs}>${tag}<span class="cpd-guide-opt-text">${escapeHtml(o.text)}</span></button>`;
  };
  card.innerHTML = '<div class="cpd-guide-card-head">'
    + '<svg class="cpd-guide-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>'
    + `<div class="cpd-guide-card-title">${escapeHtml(spec.title)}</div></div>`
    + `<div class="cpd-guide-card-body">${spec.opts.map(optHtml).join('')}</div>`
    + (spec.back ? '<button type="button" class="cpd-guide-back">‹ 返回方向</button>' : '');
  card.querySelectorAll('.cpd-guide-opt').forEach((b) => {
    if (b.dataset.dir) b.addEventListener('click', () => { _curDirection = b.dataset.dir; _renderGuidanceContent(); });
    else if (b.dataset.prompt) b.addEventListener('click', () => _fillInput(b.dataset.prompt));
  });
  const back = card.querySelector('.cpd-guide-back');
  if (back) back.addEventListener('click', () => { _curDirection = null; _renderGuidanceContent(); });
  _guidanceCardShown = true;
}

/** 出口三段式 P0：4 要点信息卡（方法/数据/结果/结论·确定性聚合·紧凑·仿 outlet-card token）。 */
function _pointsCardHtml(points) {
  if (!points) return '';
  const rows = [
    ['分析方法', points.method], ['使用数据', points.data],
    ['分析结果', points.result], ['分析结论', points.conclusion],
  ].filter(([, v]) => v && String(v).trim() && String(v) !== '暂无数据')
    .map(([k, v]) => `<div class="emc-points-row"><span class="emc-points-key">${escapeHtml(k)}</span>`
      + `<span class="emc-points-val">${escapeHtml(String(v))}</span></div>`)
    .join('');
  if (!rows) return '';
  return '<div class="emc-points-card"><div class="emc-card-head">分析支撑（4 要点）</div>' + rows + '</div>';
}

/** CB-16 Wave 0：出口卡片渲染（结果范式 agent·第三段·确定性 JSON → 纯模板）。
 *  仿 .cpd-guide-card·用既有 token（--geojson-color-* / --emc-accent）·不新造样式。
 *  7 要素：接口标识/数据基础/定量定性/地理定位/对接建议/局限标注。
 *  数据全来自后端 build_outlet_schema JSON·前端不计算不补字段·字段缺失显示"暂无数据"灰。
 *  {{show:图层}} 走 renderAnswer ref 解析（复用·不另造联动）。 */
function renderOutletCard(card) {
  const list = document.getElementById('chat-messages');
  if (!list || !card) return;
  const old = list.querySelector('.outlet-card');
  if (old) old.remove();   // 新一轮覆盖旧卡
  const el = document.createElement('div');
  el.className = 'outlet-card';

  const esc = escapeHtml;
  const fieldsHtml = Object.entries(card.fields || {}).map(([k, v]) => {
    const val = (v && v.value != null) ? String(v.value) : '暂无数据';
    const gray = (val === '暂无数据') ? ' class="outlet-muted"' : '';
    return `<div class="outlet-field"><span class="outlet-field-key">${esc(k)}</span><span${gray}>${esc(val)}</span></div>`;
  }).join('');

  const limits = (card.limitations || []).map((l) => `> ${esc(l)}`).join('\n');
  const task = (card.task_link || []).map((t) => esc(t)).join('、');
  const base = (card.data_base && card.data_base.N != null)
    ? `N=${card.data_base.N} 条评论${card.data_base.note ? `（${esc(card.data_base.note)}）` : ''}` : '';

  // 可感知体检指标（compute_perceptible_metrics·2a/2b·③z2 Codex P2 并入：UI 可见性）
  const metricsHtml = (card.perceptible_metrics || []).map((mt) => {
    const gray = (mt.value === '暂无数据') ? ' class="outlet-muted"' : '';
    return `<div class="outlet-field"><span class="outlet-field-key">${esc(mt.metric)}</span>`
      + `<span${gray} title="${esc(mt.source || '')}">${esc(mt.value)}</span></div>`;
  }).join('');
  const metricsBlock = metricsHtml
    ? `<div class="outlet-metrics"><div class="outlet-metrics-title">可感知体检指标</div>${metricsHtml}</div>`
    : '';

  // 卡片头（接口标识）+ 字段 + 对接建议 + 局限（引用块·与 CB-12 降级格式一致）
  el.innerHTML = `<div class="cpd-guide-card-head">`
    + `<div class="cpd-guide-card-title">${esc(card.name || '行业出口卡片')}</div></div>`
    + `<div class="outlet-card-body">`
    + `<div class="outlet-interface">${esc(card.interface || '')}</div>`
    + (base ? `<div class="outlet-base">${base}</div>` : '')
    + fieldsHtml
    + metricsBlock
    + (task ? `<div class="outlet-task"><span class="outlet-field-key">对接任务</span>${task}</div>` : '')
    + (limits ? `<div class="outlet-limits">${limits}</div>` : '')
    + `<div class="outlet-source">${esc(card.source || '确定性组装')}</div>`
    + `</div>`
    // P1-4（glm P1P2 评估 W3）：CSV 一键入库按钮（前端本地生成·防功能空转）
    + `<button type="button" class="outlet-export-btn" title="导出 CSV（一键入库）">导出 CSV</button>`;

  // {{show:图层}} 联动复用 renderAnswer 的 ref 解析（按钮可点·聚焦图层）
  const refs = el.querySelectorAll('.outlet-interface, .outlet-field');
  refs.forEach((n) => {
    if (n.textContent.includes('{{show:')) {
      const md = n.textContent.replace(/\{\{show:([^}]+)\}\}/g, (_, name) => `{{show:${name}}}`);
      n.innerHTML = renderAnswer(md, getValidRefNames());
    }
  });
  // P1-4（glm P1P2 评估 W3）：CSV 一键入库（前端本地生成·Card JSON → CSV Blob 下载）
  const _btn = el.querySelector('.outlet-export-btn');
  if (_btn) _btn.addEventListener('click', () => _exportOutletCardCsv(card));
  list.appendChild(el);
}

/** P1-4：出口卡片 → CSV 本地下载（确定性·前端生成·UTF-8 BOM·Excel 兼容·对齐后端 export_outlet_card_csv 字段）。 */
function _exportOutletCardCsv(card) {
  try {
    const esc = escapeHtml;
    const flat = Object.entries(card.fields || {}).map(([k, v]) =>
      [k, (v && typeof v === 'object') ? (v.value ?? '') : v]);
    const rows = [
      ['outlet_id', card.outlet_id || ''], ['name', card.name || ''], ['scale', card.scale || ''],
      ['interface', card.interface || ''], ...flat,
      ['data_base_N', card.data_base?.N ?? ''], ['data_base_note', card.data_base?.note ?? ''],
      ['task_link', (card.task_link || []).join('、')],
      ['limitations', (card.limitations || []).join('；')],
      ['geo_label', card.geo_label || ''], ['source', card.source || ''],
    ];
    const csv = '﻿' + rows.map(([k, v]) => `${k},${String(v ?? '').replace(/"/g, '""')}`).join('\r\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${(card.name || 'outlet_card').replace(/[\\/:*?"<>|]/g, '_')}.csv`;
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(a.href);
    a.remove();
  } catch (_) { /* 导出失败不阻塞 */ }
}
/** 清引导焦点卡片。 */
function _clearGuideCard() {
  const card = document.querySelector('.cpd-guide-card');
  if (card) card.remove();
  _guidanceCardShown = false;
}
/** 渲染引导内容总调度（cpd:guidance/CTA/级联切换调）：intent=方向级联(A/B)/interpret=examples → 焦点卡片；其余清。末尾同步欢迎卡。 */
function _renderGuidanceContent() {
  if (!_shouldShowGuidanceExamples()) { _clearGuideCard(); renderEmptyState(); return; }
  const g = _curGuidance;
  if (!g) { _clearGuideCard(); renderEmptyState(); return; }
  if (g.kind === 'intent' && g.directions) {
    if (_curDirection && g.refinements && g.refinements[_curDirection]) {
      const dir = g.directions.find((d) => d.dir === _curDirection);
      _renderGuideCard({ title: (dir ? dir.tag + ' · ' : '') + '细化你的需求', back: true, opts: g.refinements[_curDirection].map((t) => ({ text: t, prompt: t })) });
    } else {
      _renderGuideCard({ title: '选一个分析方向', opts: g.directions.map((d) => ({ tag: d.tag, text: d.hint || '', dir: d.dir })) });
    }
  } else if (g.examples) {
    _curDirection = null;
    _renderGuideCard({ title: '这张图说明了什么？试试', opts: g.examples.map((e) => ({ tag: e.tag, text: e.text, prompt: e.text })) });
  } else {
    _clearGuideCard();
  }
  renderEmptyState();   // 同步欢迎卡（引导卡显→欢迎隐；清空且 _history 空→显）
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
  // CB-05 删除符号根治 Layer 1：strip markdown 删除线（~~text~~ → text·治根因A·不可绕过·不靠 Flash 守 prompt）
  text = String(text).replace(/~~([\s\S]+?)~~/g, '$1').replace(/~~/g, '');
  let html = window.marked ? window.marked.parse(text) : `<p>${escapeHtml(text).replace(/\n/g, '<br>')}</p>`;
  // CB-22 素材术语/来源排版：来源标注弱化（小号浅灰·随文不换行）——主：〔来源：...〕（LLM 约定格式·注入指令已约定）；
  //   兜底：自由格式（来源：...）/（来源：...）（LLM 不守约定时·glm 方案 B 主 + A 兜底）
  html = html.replace(/〔来源：([^\〕]+)〕/g, '<span class="answer-source">〔来源：$1〕</span>')
             .replace(/（来源：([^）]+)）/g, '<span class="answer-source">（来源：$1）</span>');
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
  // CB-09 D020：剥离 {{capsule:...}} 标记（defense 已抽走·防早返路径 quick-general 等漏网·胶囊只在 #aiq-suggest 显·不内联）
  html = html.replace(/\{{1,2}capsule:[^}]+\}{1,2}/g, '');
  return html;
}

const _DOMAIN_LABEL = { urban_planning: '城市规划', urban_renewal: '城市更新', urban_operation: '城市运营', urban_governance: '城市治理' };
const _SCALE_LABEL = { macro: '宏观（片区/城区）', meso: '中观（街道/单元）', micro: '微观（点位）' };
const _STRATEGY_LABEL = { ready: '数据齐全', fallback_annotated: '部分数据替代', request_upload: '需补充数据' };

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
  const skipped = t.defense && t.defense.skipped;
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
    const _modelLabel = _thinkMode === 'pro' ? 'Pro' : 'Flash';
    const _tplMeta = ts.samples > 0 ? ` · ${_modelLabel} 模板 ${ts.hits}/${ts.samples}(${Math.round(ts.rate * 100)}%)` : '';
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
  const skipped = t && t.defense && t.defense.skipped;
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
  // SHELL2(FIX) FIX-11：dsh 引擎轮兜底追问（知识类·不与静态情绪分析问法混调）
  if (intent === 'dsh') {
    return [
      { tag: '深问', text: '把刚才回答里的关键概念再展开讲讲' },
      { tag: '求据', text: '这个结论有哪些依据或出处？' },
      { tag: '本地分析', text: '哪些区域情绪最差？为什么？' },
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
  // CB-09 D032/D033（5.239 CPD 收尾）：胶囊 turn-over 自然移除（新话轮重建·D032）+ 无胶囊时静态 _followUps 或空（D033 完成态）。
  const el = document.getElementById('aiq-suggest');
  if (!el) return;
  _guidanceCardShown = false;   // 答案后 胶囊/_followUps 接管，清引导卡片标志
  // SHELL2(FIX) FIX-09：追问源选择纯函数化——优先级不变（cues > 胶囊 > 静态兜底·ask 互斥）。
  const _src = pickFollowupSource(t);
  if (_src.kind === 'cues') {
    el.hidden = false;
    el.innerHTML = '<span class="aiq-suggest-label">追问建议</span>'
      + _src.items.map((c) => `<button type="button" class="aiq-suggest-chip" data-followup-cue="1">${escapeHtml(c)}</button>`).join('');
    el.querySelectorAll('.aiq-suggest-chip').forEach((b) => b.addEventListener('click', () => _fillInput(b.textContent)));
    return;
  }
  // CB-09 D020：优先动态胶囊（LLM 产·trace.defense.capsules·{label,level,skill,params}）·无则静态 _followUps 兜底（gap/ask/general）
  const capsules = (_src.kind === 'capsules') ? _src.items : [];
  let chipHtml;
  if (capsules.length) {
    chipHtml = capsules.map((c, i) => `<button type="button" class="aiq-suggest-chip aiq-capsule" data-capsule-idx="${i}"><span class="aiq-suggest-tag">${escapeHtml(c.level || 'L1')}</span>${escapeHtml(c.label)}</button>`).join('');
  } else {
    const items = _followUps(t);
    if (!items.length) { el.hidden = true; el.innerHTML = ''; return; }
    chipHtml = items.map((it) => `<button type="button" class="aiq-suggest-chip" data-prompt="${escapeHtml(it.text)}"><span class="aiq-suggest-tag">${escapeHtml(it.tag)}</span>${escapeHtml(it.text)}</button>`).join('');
  }
  el.hidden = false;
  el.innerHTML = '<span class="aiq-suggest-label">追问</span>' + chipHtml;
  el.querySelectorAll('.aiq-suggest-chip').forEach((b) => b.addEventListener('click', () => {
    if (b.dataset.capsuleIdx != null) {   // 胶囊 chip → send(null,capsule) 走 runCapsule（L1 直达/L2 Pro 确认）
      const cap = capsules[Number(b.dataset.capsuleIdx)];
      if (cap) send(null, cap);
    } else {                               // 静态文本 chip → send(text) 走完整管线
      send(b.dataset.prompt);
    }
  }));
}
function clearSuggest() {
  const el = document.getElementById('aiq-suggest');
  if (el) { el.hidden = true; el.innerHTML = ''; }
  const card = document.querySelector('.cpd-guide-card');
  if (card) card.remove();            // send/切会话：清引导焦点卡片（对话接管）
  _guidanceCardShown = false;
  _curDirection = null;               // 重置阶段 A→B 级联（下次 analyze 重新显方向）
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

/** Thinking 头：答完显「推理完成（Ns）· Nk token」（折叠态可见）。trace 缺省=实时 _curTrace。
 *  Feature 2：与流式期动态头标签一致（正在推理…→推理完成）；耗时入 overflow、token 入 meta。 */
function updateReasonMeta(shell, trace) {
  if (!shell || !shell.reasonEl) return;
  const t = trace || _curTrace;
  const title = shell.reasonEl.querySelector('.aiq-reason-title');
  const meta = shell.reasonEl.querySelector('.aiq-reason-meta');
  const ov = shell.reasonEl.querySelector('.aiq-reason-overflow');
  const secs = t && t.startedAt && t.doneAt ? Math.max(1, Math.round((t.doneAt - t.startedAt) / 1000)) : 0;
  if (title) title.textContent = secs ? '推理完成' : 'Thinking…';
  if (ov) ov.textContent = secs ? `（${secs}s）` : '';
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
// 阶段 D 参数提示（确定性·SKILL_DEFS.required_slots → 人话标签·CPD 导游预告"要哪些参数"）。
const _PARAM_LABELS = {
  boundary: '聚合范围（上传面/选方格）', boundaries: '对比范围（多区）', center: '设施位置（点地图/输入地名）',
  range: '范围', layer: '图层', layer_a: '图层A', layer_b: '图层B', pre_filter: '筛选条件', target: '目标',
};
function renderDiagnoseCard(el, card) {
  if (!el) return;
  if (!card || card.degraded) { el.hidden = true; return; }
  el.hidden = false;
  const dom = (card.domain_lens || []).map((k) => _DOMAIN_LABEL[k] || k).filter(Boolean);
  const strat = (card.data_plan && card.data_plan.strategy) || 'unknown';   // T4：缺省不显「齐全」（unknown）·治胶囊矛盾（05-llm Q2·真缺口勿伪装 ready）
  const method = (card.method || []).filter(Boolean);
  el.classList.toggle('is-upload', strat === 'request_upload');
  // 阶段 D：diagnose 选定 template → SKILL_DEFS.required_slots → 参数提示（缺参时预告用户要补什么）
  const def = card.template && SKILL_DEFS[card.template];
  const req = (def && def.required_slots) || [];
  const params = req.length ? `<div class="aiq-diag-params"><span class="aiq-diag-params-tag">需要</span>${req.map((s) => _PARAM_LABELS[s] || s).join(' · ')}</div>` : '';
  const chip = (t) => `<span class="aiq-diag-chip">${escapeHtml(t)}</span>`;
  el.innerHTML = `<div class="aiq-card-head">问题理解</div>`
    + `<div class="aiq-diag-row">${[dom.join('/'), _SCALE_LABEL[card.scale] || card.scale, card.decision_type, card.outlet].filter(Boolean).map(chip).join('')}</div>`
    + `<div class="aiq-diag-strategy ${strat}"><span class="aiq-diag-strat-tag">${
      strat === 'unknown' ? '数据状况待确认' : (_STRATEGY_LABEL[strat] || strat)}</span>${
      strat === 'request_upload' ? '（缺关键数据，已请你上传）'
      : strat === 'fallback_annotated' ? '（部分数据用替代，结论会注明）'
      : strat === 'unknown' ? '（诊断未明确数据完备性）' : ''}</div>`
    + (method.length ? `<div class="aiq-diag-method">方法：${escapeHtml(method.join(' → '))}</div>` : '')
    + params;
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
    // CB-05 Layer 3：去掉 grid/terrain 限制——所有 polygon 图层的 feature name 都入白名单
    // （zonal_stats/area_stats/extract_feature 等工具产出的地名同样有效·治 cite-chip-invalid 假阳性删除线·治根因B 主因）
    for (const f of l.fc.features) {
      const p = f.properties || {};
      const nm = p.name || p.issue_label;
      if (nm) names.add(String(nm));
    }
  }
  return names;
}

/** CB-09 D024：质量防线结果供 episode 自成长·不显 UI（旧 review 七条 ✓/△/✕ 审查区已退役·永隐）。 */
function renderReview(reviewEl) {
  if (reviewEl) reviewEl.hidden = true;
}

/** 思考 dock（单例，挂 #chat-suggest 槽，永贴底不被顶走）。 */
function dockEl() { return document.getElementById('aiq-thinking-dock'); }

/** 动态思考指示器：轮换文案 + 跳动点 + 阶段 chip + 阶段计时（E2 进度透明·治 C9"还在跑/跑到哪/已多久"）。 */
function startThinking() {
  setEmcMode('expand');
  clearSuggest();   // 新一轮提问：清上一轮的推荐追问胶囊
  _t0 = Date.now(); _phaseTs = {};   // E2：总起始 + 阶段时间戳重置
  try { _layerBase = document.querySelectorAll('#layer-list .layer-row').length; } catch (_) { _layerBase = 0; }   // E2：图层基线（本轮新增 = 现 - 基线）
  const d = dockEl();
  if (d) { d.hidden = false; const ab = d.querySelector('.aiq-abort-btn'); if (ab) ab.hidden = false; setPhase('理解'); }
  _startElapsedTimer();
  if (!_abortDelegation) {   // E2：取消按钮 delegation（dock 单例动态建·挂一次最稳）
    document.addEventListener('click', (e) => { const t = e.target; if (_streaming && _abortCtl && t && t.closest && t.closest('.aiq-abort-btn')) _abortCtl.abort(); });
    _abortDelegation = true;
  }
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
  _stopElapsedTimer();   // E2：停计时
  const d = dockEl();
  if (d) { d.hidden = true; const ab = d.querySelector('.aiq-abort-btn'); if (ab) ab.hidden = true; }
}
const _PHASE_ORDER = ['理解', '思考', '生成'];   // Feature 3：5 阶段(诊断/思考/检索/生成/审查)→3 阶段·映射 EMC 三模块（理解=FC诊断/思考=工具执行/生成=finalStep）
/** 阶段进度 chip 点亮 + done 标记（E2 加阶段时间戳 + 已完成段填充）。 */
function setPhase(chip) {
  const d = dockEl();
  if (!d) return;
  _phaseTs[chip] = _phaseTs[chip] || Date.now();   // E2：阶段进入时间戳（首次·防回切重置耗时）
  const idx = _PHASE_ORDER.indexOf(chip);
  d.querySelectorAll('.aiq-phase-chips span').forEach((s) => {
    const si = _PHASE_ORDER.indexOf(s.dataset.phase);
    s.classList.toggle('active', s.dataset.phase === chip);
    s.classList.toggle('done', si >= 0 && si < idx);   // E2：已完成段（当前之前的）
  });
  _renderElapsed();
}
/** E2：工具名 → 中文名（onAction 显"正在执行·CN"·治 C9 跑到哪感知）。 */
const _TOOL_CN = {
  zonal_stats: '分区统计', rank: '排序', density: '密度', buffer: '缓冲', clip: '裁剪',
  overlay: '叠置', extract_feature: '抽取要素', filter_attr: '属性筛选', merge: '合并',
  nearest: '邻近', hotspot: '热点', area_stats: '面积统计', compare_regions: '区域对比',
  query_layers: '查图层', query_zone_stats: '查区域统计', query_attribution: '查归因',
  query_keywords: '查关键词', inspect_zone: '深读单元', deep_read_attribution: '深度归因',
  focus_zones: '定位区域', open_attribution: '展开归因', ensure_zone: '生成聚合域',
};
/** E2：渲染阶段耗时（当前段 + 总耗时），0.5s 刷新·治 C9"已多久"感知。 */
function _renderElapsed() {
  const d = dockEl(); if (!d || d.hidden) return;
  const el = d.querySelector('.aiq-thinking-elapsed'); if (!el) return;
  const now = Date.now();
  const total = _t0 ? Math.floor((now - _t0) / 1000) : 0;
  const phases = Object.keys(_phaseTs);
  const cur = phases.length ? phases[phases.length - 1] : '';
  const curS = cur ? Math.floor((now - _phaseTs[cur]) / 1000) : 0;
  el.hidden = false;
  el.textContent = cur ? `${cur} ${curS}s · 共 ${total}s` : `${total}s`;
}
function _startElapsedTimer() { _stopElapsedTimer(); _renderElapsed(); _elapsedTimer = setInterval(_renderElapsed, 500); }
function _stopElapsedTimer() { if (_elapsedTimer) { clearInterval(_elapsedTimer); _elapsedTimer = null; } }
// 5.213 实时识别（输入时显"已识别"chip·prompt 工程显化·代码关键词·几 ms·非 LLM·预览非 diagnose 精确）
const _REC_INTENT = [
  [/排序|最差|最好|排名|优先/, '排序'],
  [/对比|比较|\bvs\b|哪个更/, '对比'],
  [/密度|热力|分布|集中|密集/, '密度'],
  [/缓冲|周边|附近|半径/, '缓冲'],
  [/归因|为什么|原因|怎么回事/, '归因'],
  [/聚集|热点|冷热/, '热点'],
  [/面积|占比|用地结构/, '面积'],
  [/裁出|裁剪|范围内|区内/, '裁取'],
];
const _REC_SCALE = [[/整体|中心城区|全域|哪类/, '宏观'], [/街道|社区|单元|哪个区/, '中观'], [/点位|这个点|哪条街|哪里最/, '微观']];
function _liveRecognize(t) {   // 5.216 发散启发：基于用户输入类型·提示更多相关要素（地点→子地点/密度→专业名词/多地点→对比）
  if (!t || !t.trim()) return [];
  const q = t;
  const tags = [];
  // 区名 → 发散子地点/相关（启发用户具体化）
  if (/中心城区|全域|整体|全市/.test(q)) tags.push('中心城区', '西陵区', '伍家岗区', '夷陵区');
  else if (/西陵/.test(q)) tags.push('西陵区', '二马路', 'CBD');
  else if (/伍家岗/.test(q)) tags.push('伍家岗区', '东站片区');
  else if (/夷陵/.test(q)) tags.push('夷陵区', '小溪塔');
  else if (/点军/.test(q)) tags.push('点军区');
  else if (/猇亭/.test(q)) tags.push('猇亭区');
  // 情绪/密度/分布 → 专业名词（启发用户用术语）
  if (/密度|热力|分布|集中|密集|集聚|热度/.test(q)) tags.push('热力图', '核密度', '热点分布');
  if (/聚集|热点|冷热/.test(q)) tags.push('Gi* 热点', '冷热点');
  if (/归因|为什么|原因|怎么回事/.test(q)) tags.push('4×5 归因');
  if (/排序|最差|最好|排名|优先/.test(q)) tags.push('Top N 排序');
  if (/缓冲|周边|附近|半径/.test(q)) tags.push('缓冲区');
  if (/面积|占比|用地结构/.test(q)) tags.push('用地占比');
  if (/裁出|裁剪|范围内|区内/.test(q)) tags.push('范围裁取');
  // 多地点 → 对比提示
  const _dc = (q.match(/(西陵|伍家岗|夷陵|点军|猇亭)区?/g) || []);
  if (_dc.length >= 2 && !tags.includes('区域对比')) tags.push('区域对比');
  else if (/对比|比较|vs|哪个更/.test(q)) tags.push('区域对比');
  // 尺度（启发颗粒度）
  if (/整体|全域|哪类/.test(q)) tags.push('宏观');
  else if (/街道|社区|单元|哪个区/.test(q)) tags.push('中观');
  if (/点位|这个点|哪条街|哪里最/.test(q)) tags.push('微观');
  return tags.slice(0, 6);   // 最多 6 chip（发散·flex-wrap 换行）
}
// 5.215 优化键（LLM·Flash 流式 <3s·不增维度）+ 输入提示（5.213 chip 恢复·对话框下）
let _originalInput = '';   // 优化前原文（撤销用）
/** 5.213/5.218 输入时实时 chip 提示（对话框下·两行：短语 + 方法 tip·代码几 ms·非 LLM）。 */
function _renderRecognize(tags, tip) {
  const el = document.getElementById('aiq-recognize');
  if (!el) return;
  const has = (tags && tags.length) || tip;
  el.hidden = !has;
  if (!has) { el.innerHTML = ''; return; }
  const _sparkle = '<span class="aiq-rec-icon"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.8 4.2L18 9l-4.2 1.8L12 15l-1.8-4.2L6 9l4.2-1.8z"/><path d="M5 4v2M4 5h2"/><path d="M19 18v2M18 19h2"/></svg></span>';
  const line1 = (tags && tags.length) ? `<div class="aiq-rec-line">${_sparkle}${tags.map((t) => `<span class="aiq-rec-chip">${escapeHtml(t)}</span>`).join('')}</div>` : '';
  const line2 = tip ? `<div class="aiq-rec-tip">${escapeHtml(tip)}</div>` : '';
  el.innerHTML = line1 + line2;
}
/** 5.218 方法 tip（第二行·基于意图+区名→分析方法长句·启发用户操作思路）。 */
function _liveRecTip(t) {
  const tags = _liveRecognize(t);
  const d = tags.find((x) => /区$/.test(x)) || '该范围';
  if (tags.includes('热力图') || tags.includes('核密度') || tags.includes('热点分布')) return `tip：用密度热力图或分区统计（区域着色）分析${d}的极性（积极/中性/消极）空间分布`;
  if (tags.includes('Top N 排序')) return `tip：按极性排序·找出${d}最差/最好区域 Top N`;
  if (tags.includes('4×5 归因')) return `tip：按行政/规划单元聚合${d}·4×5 领域×要素归因`;
  if (tags.includes('区域对比')) return `tip：并排对比${d}的情绪极性差异`;
  if (tags.includes('Gi* 热点') || tags.includes('冷热点')) return `tip：用聚集热点统计识别${d}负面情绪显著聚集的冷热点`;
  if (tags.includes('用地占比')) return `tip：统计${d}各类用地面积占比`;
  if (tags.includes('缓冲区')) return `tip：分析${d}周边缓冲区范围内的情绪聚合`;
  if (tags.includes('范围裁取')) return `tip：裁取${d}范围内的情绪点`;
  return '';
}
/** 5.217 优化输出解析：拦 JSON（thought/action）/ 去围栏·返干净文本（空=失败）。 */
function _parseOptimize(raw) {
  const t = String(raw || '').trim();
  if (/^\s*\{[\s\S]*"(thought|action)"/.test(t)) return '';   // JSON（diagnose/agent 误出）→ 拦截
  return t.replace(/^```[a-z]*\n?|\n?```$/g, '');   // 去围栏（防御代码块显示）
}
/** 5.215/5.217 优化/撤销切换（LLM·sparkle ⇄ loading ⇄ undo·拦 JSON·失败提示）。 */
async function _toggleOptimize() {
  const input = document.getElementById('chat-input');
  const btn = document.getElementById('aiq-optimize');
  if (!input || !btn) return;
  if (_originalInput) {   // 撤销
    input.value = _originalInput; _originalInput = '';
    btn.classList.remove('is-optimized'); btn.title = '一键优化 prompt（再点撤销原文）';
    input.focus(); input.dispatchEvent(new Event('input'));
    return;
  }
  const orig = (input.value || '').trim();
  if (!orig) return;
  btn.classList.add('is-loading'); btn.title = 'prompt 优化中…';
  _originalInput = input.value;
  const _oldPh = input.placeholder;
  try {
    const ctx = { context: buildOptimizeContext(), signal: _abortCtl ? _abortCtl.signal : undefined };   // 5.217 精简 context（同步·<3s）·非 buildContext（完整·慢）
    input.placeholder = 'prompt 优化中…';
    input.value = '';
    const finalAcc = await optimizeStep(ctx, {
      onOptimize: (acc) => {
        if (/^\s*\{[\s\S]*"(thought|action)"/.test(acc)) return;   // JSON → 不写输入框（拦截流式·防代码块闪）
        input.value = acc; input.scrollTop = input.scrollHeight;
      },
    }, orig);
    input.placeholder = _oldPh;
    const _opt = _parseOptimize(finalAcc);
    if (_opt) {
      input.value = _opt;
      btn.classList.remove('is-loading'); btn.classList.add('is-optimized'); btn.title = '撤销（恢复原文）';
    } else {   // JSON 或空 → 失败·恢复原文 + 提示
      input.value = _originalInput; _originalInput = '';
      btn.classList.remove('is-loading'); btn.title = '一键优化 prompt（再点撤销原文）';
      input.placeholder = '优化失败（格式错）·请重试或手动描述';
      setTimeout(() => { input.placeholder = _oldPh; }, 3000);
    }
  } catch (e) {
    input.value = _originalInput; _originalInput = ''; input.placeholder = _oldPh;
    btn.classList.remove('is-loading'); btn.title = '一键优化 prompt（再点撤销）';
  }
  input.focus();
}
function _resetOptimize() {   // send 后重置（清原文 + 按钮回 sparkle + 清 chip）
  _originalInput = '';
  const btn = document.getElementById('aiq-optimize');
  if (btn) { btn.classList.remove('is-optimized', 'is-loading'); btn.title = '一键优化 prompt（再点撤销原文）'; }
  _renderRecognize([], '');
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
    <div class="aiq-timeline">
    <div class="aiq-reason" ${hasReason ? '' : 'hidden'}><div class="aiq-reason-head"><span class="aiq-reason-title">理解问题</span><span class="aiq-reason-overflow"></span><span class="aiq-reason-meta"></span><span class="aiq-reason-copy" hidden title="复制完整思考过程">复制</span></div><div class="aiq-reason-body"></div></div>
    <div class="aiq-step aiq-step-final" hidden><span class="aiq-step-tag">结论</span><div class="aiq-answer"><span class="aiq-answer-stream"></span><span class="chat-cursor" hidden>▍</span></div></div>
    </div>
    <div class="aiq-review" hidden><div class="aiq-review-head">审查</div><div class="aiq-review-body"></div></div>
    <div class="aiq-card aiq-card-caliber" hidden></div>
    <div class="aiq-answer-footer" hidden></div>
  </div>
  <div class="emc-msg-actions"><button class="emc-collapse-btn" type="button" title="折叠/展开" hidden>折叠</button><button class="emc-copy-btn" type="button" title="复制回答"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h8"/></svg></button></div>`;
  list.appendChild(el);
  const shell = {
    diagnoseEl: el.querySelector('.aiq-card-diagnose'),
    reasonEl: el.querySelector('.aiq-reason'),
    reasonBody: el.querySelector('.aiq-reason-body'),
    reasonCopyEl: el.querySelector('.aiq-reason-copy'),
    stepsEl: el.querySelector('.aiq-timeline'),   // Feature 2: 时间线容器（toolcard 直接挂此·竖线上成节点·原 .aiq-steps 包装已移除）
    timelineEl: el.querySelector('.aiq-timeline'),
    finalEl: el.querySelector('.aiq-step-final'),   // Feature 2: 生成节点（toolcard 在其前 insertBefore）
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
    renderReview(shell.reviewEl);   // CB-09 D024：defense 不显 UI（永隐）
    shell.answerEl.innerHTML = trace.final ? renderAnswer(trace.final, getValidRefNames()) : '<span class="chat-error">（未生成结论）</span>';
    enhanceCodeBlocks(shell.answerEl);
    if (shell.finalEl && trace.final) { shell.finalEl.hidden = false; shell.finalEl.classList.add('is-done'); }   // Feature 2：历史答案节点显灰点
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
    card.className = 'aiq-toolcard is-open is-streaming';   // Feature 2: 初始=进行中（竖线上绿脉动节点）
    card.dataset.round = round;
    card.innerHTML = `<div class="aiq-toolcard-head">
        <span class="aiq-toolcard-name">第 ${round} 步</span>
        <span class="aiq-toolcard-target"></span>
        <span class="aiq-toolcard-chev">▸</span>
      </div>
      <div class="aiq-toolcard-body">
        <div class="aiq-toolcard-thought"></div>
        <div class="aiq-toolcard-obs"></div>
      </div>`;
    card.querySelector('.aiq-toolcard-head').addEventListener('click', () => card.classList.toggle('is-open'));
    const finalEl = stepsEl.querySelector('.aiq-step-final');   // Feature 2: toolcard 挂"生成"节点前（时间线顺序：理解→工具…→生成）
    stepsEl.insertBefore(card, finalEl || null);
  }
  if (thought != null) card.querySelector('.aiq-toolcard-thought').textContent = thought || '';
  if (action) {
    card.querySelector('.aiq-toolcard-name').textContent = action.name || 'step';
    card.querySelector('.aiq-toolcard-target').textContent = actionTargetSummary(action);
  }
  if (observation != null) {
    card.querySelector('.aiq-toolcard-obs').textContent = observation || '';
    const fail = /失败|\[ERR\]|错误|未知工具/.test(observation);
    card.classList.remove('is-streaming');   // Feature 2: 完成→灰点（失败→红点·CSS .is-fail）
    card.classList.add('is-done');
    card.classList.toggle('is-fail', fail);
    card.classList.remove('is-open');   // 结果到→折叠（Claude Code 自动折叠已完成调用）
  }
}

function buildHooks(shell) {
  const reasonSegs = {};   // round -> text
  let streamAcc = '';      // onFinal 流缓冲（RAF drain·治 O(n²) 每 token marked.parse）
  let streamRaf = 0;
  let reasonRaf = 0;
  const isFlash = _thinkMode === 'flash';
  // Feature 2：reason 折叠块动态头（读秒 + 溢出末句·Claude-Code 式"正在推理···Ns"）。
  let reasonTimer = 0;
  let reasonStartTs = 0;
  let reasonStarted = false;
  function _startReasonTimer() {
    if (reasonTimer || !shell.reasonEl) return;
    reasonStartTs = Date.now();
    reasonTimer = setInterval(() => {
      if (!shell.reasonEl || shell.reasonEl.hidden) { if (reasonTimer) { clearInterval(reasonTimer); reasonTimer = 0; } return; }
      const m = shell.reasonEl.querySelector('.aiq-reason-meta');
      if (m) m.textContent = ((Date.now() - reasonStartTs) / 1000).toFixed(1) + 's';
    }, 500);
  }
  function _stopReasonTimer(secs) {
    if (reasonTimer) { clearInterval(reasonTimer); reasonTimer = 0; }
    const m = shell.reasonEl && shell.reasonEl.querySelector('.aiq-reason-meta');
    if (m) m.textContent = secs != null ? secs + 's' : '';
  }
  function _updateReasonOverflow(text) {
    const ov = shell.reasonEl && shell.reasonEl.querySelector('.aiq-reason-overflow');
    if (!ov) return;
    const s = String(text || '').replace(/\s+/g, ' ').trim();
    ov.textContent = s ? '· ' + s.slice(-28) : '';
  }
  /** Feature 2：reason 折叠块首发（首 token 或 onRoundStart 触发·幂等）——显块 + 头改"正在推理…" + 启动读秒。 */
  function _ensureReasonStarted() {
    if (!shell.reasonEl) return;
    if (!reasonStarted) { reasonStarted = true; shell.reasonEl.hidden = false; _startReasonTimer(); }
    // Feature 2：每波推理激活节点（绿脉动·竖线上）——含 final-reason 复活（onDiagnose 后 finalStep 又推理）。
    shell.reasonEl.classList.remove('is-done');
    shell.reasonEl.classList.add('is-streaming');
    const _t = shell.reasonEl.querySelector('.aiq-reason-title');
    if (_t) _t.textContent = '正在推理…';
  }
  /** Feature 2：reason 节点标完成（灰点·折叠）——onDiagnose/onFinal 中间态。 */
  function _markReasonDone() {
    if (!shell.reasonEl) return;
    shell.reasonEl.classList.remove('is-streaming');
    shell.reasonEl.classList.add('is-done');
    const _t = shell.reasonEl.querySelector('.aiq-reason-title');
    if (_t) _t.textContent = '推理完成';
    _wireReasonCopy();
  }
  /** Feature 2：生成节点激活/完成（绿脉动流式 / 灰完成）。 */
  function _setFinalState(state) {
    if (!shell.finalEl) return;
    shell.finalEl.hidden = false;
    shell.finalEl.classList.toggle('is-streaming', state === 'streaming');
    shell.finalEl.classList.toggle('is-done', state === 'done');
  }
  /** Feature 2：合并所有轮 reason 为完整思考原文（复制用·非折叠简版·增补需求 1）。 */
  function getFullReason() {
    return Object.keys(reasonSegs).sort((a, b) => Number(a) - Number(b)).map((r) => reasonSegs[r]).join('\n\n');
  }
  let _reasonCopyWired = false;
  /** Feature 2：复制思考过程按钮——done 态显·点复制完整原文（反馈"已复制"·复用代码块复制范式）。 */
  function _wireReasonCopy() {
    if (_reasonCopyWired || !shell.reasonCopyEl) return;
    _reasonCopyWired = true;
    shell.reasonCopyEl.hidden = false;
    shell.reasonCopyEl.addEventListener('click', (e) => {
      e.stopPropagation();
      navigator.clipboard?.writeText(getFullReason());
      shell.reasonCopyEl.textContent = '已复制';
      setTimeout(() => { if (shell.reasonCopyEl) shell.reasonCopyEl.textContent = '复制'; }, 1200);
    });
  }

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
  /** 流式期裸文本节点（流末 onFinalDone 才 marked.parse 一次）。 */
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
    if (!shell.reasonEl) return;   // Hotfix R2 S6：去 isFlash 门（Flash 也渲染+收尾 reason）
    if (reasonRaf) { cancelAnimationFrame(reasonRaf); reasonRaf = 0; }
    for (const r of Object.keys(reasonSegs)) {
      const body = shell.reasonBody.querySelector(`.aiq-reason-segment[data-round="${r}"] .aiq-reason-seg-body`);
      if (body) body.textContent = reasonSegs[r];
    }
    flushReasonSegs();
    if (Object.keys(reasonSegs).length) {
      const _secs = reasonStartTs ? ((Date.now() - reasonStartTs) / 1000).toFixed(1) : null;
      _stopReasonTimer(_secs);   // Feature 2：停读秒·头改"推理完成（Ns）"·自动折叠
      const _t = shell.reasonEl.querySelector('.aiq-reason-title');
      if (_t) _t.textContent = '推理完成';
      const _ov = shell.reasonEl.querySelector('.aiq-reason-overflow');
      if (_ov) _ov.textContent = _secs ? `（${_secs}s）` : '';
      shell.reasonEl.classList.add('is-done');
      _wireReasonCopy();   // Feature 2：复制思考按钮（done 态显）
      reorganizeReason(shell);   // 主题目录（详略折叠·展开后按主题切·用户要的"折叠成块"）
    } else {
      _stopReasonTimer();
      shell.reasonEl.hidden = true;
    }
  }

  // ── S3 事件化：hooks 回调面 → ACP bus 订阅（渲染器注册于本闭包·状态共享；emitter 保持 legacy 签名·harness 零改动）──
  const _acp = createAcpChannel();
  shell._acp = _acp;   // S7 E2E/BrainAdapter 注入点预留（远端引擎未来直注事件·壳渲染零改动）
  const _bus = _acp.bus;

  _bus.on(ACP_FAMILY.TURN, (e) => {
    if (e.phase === 'diagnose') { const card = e.card;
      if (_curTrace) _curTrace.diagnose = card;
      // H1 信号源：派发 diagnose 卡可观测面，飞轮/调试工具据此抓 template（生产零副作用·无人听则空转）。
      // 替代「抓 /chat 请求体」——diagnose 是后端响应产物，请求体（ChatRequest）本无此字段。
      document.dispatchEvent(new CustomEvent('diagnose:done', { detail: card }));
      renderDiagnoseCard(shell.diagnoseEl, card);
      _markReasonDone();   // Feature 2：理解节点完成（灰·折叠）·FC 推理告一段落
      if (card && !card.degraded) setPhase('思考');
    } else if (e.phase === 'round.start') { const round = e.round;
      if (isFlash) return;
      _ensureReasonStarted();
      ensureSeg(round);
    }
  });
  _bus.on(ACP_FAMILY.MSG_DELTA, (e) => {
    if (e.kind === 'reason') { const tok = e.token, round = e.round;
      // Hotfix R2 S6：去 isFlash 门——Flash 默认下也渲染 reason（逐 token RAF drain）。
      // Feature 2：首 token（经 _ensureReasonStarted 幂等）启动读秒 + 头显"正在推理…"。
      _ensureReasonStarted();
      const r = round || 0;
      ensureSeg(r);
      reasonSegs[r] += tok;
      // RAF 合流：每帧最多写一次 textContent（不再每 token querySelector+textContent）
      if (reasonRaf) return;
      reasonRaf = requestAnimationFrame(() => {
        reasonRaf = 0;
        const body = shell.reasonBody.querySelector(`.aiq-reason-segment[data-round="${r}"] .aiq-reason-seg-body`);
        if (body) body.textContent = reasonSegs[r];
        _updateReasonOverflow(reasonSegs[r]);   // Feature 2：溢出末句（"正在想什么"）
        flushReasonSegs();
        autoScroll();
      });
    }
  });
  _bus.on(ACP_FAMILY.TOOL_BEGIN, (e) => {
    if (e.sub === 'thought') { const thought = e.thought, round = e.round;
      shell.stepsEl.hidden = false;
      renderToolCard(shell.stepsEl, round, thought, null, null);
      if (_curTrace) _curTrace.steps.push({ round, thought, action: null, observation: null });
      setPhase('思考');
      autoScroll();
    } else { const action = e.action, round = e.round;
      renderToolCard(shell.stepsEl, round, null, action, null);
      if (_curTrace && _curTrace.steps.length) _curTrace.steps[_curTrace.steps.length - 1].action = action;
      const _cn = action && _TOOL_CN[action.name];   // E2：dock 显"正在执行·CN"（治 C9 跑到哪）
      if (_cn) { const _t = dockEl() && dockEl().querySelector('.aiq-thinking-text'); if (_t) _t.textContent = `正在执行·${_cn}…`; }
    }
  });
  _bus.on(ACP_FAMILY.RENDER, (e) => {
    if (e.kind === 'ask_user') { const action = e.action, round = e.round;
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
    }
  });
  _bus.on(ACP_FAMILY.TOOL_END, (e) => {
    { const obs = e.observation, round = e.round;
      renderToolCard(shell.stepsEl, round, null, null, obs);
      if (_curTrace && _curTrace.steps.length) _curTrace.steps[_curTrace.steps.length - 1].observation = obs;
      // S5 追问 chips：tool.end 载荷 followup_cues（契约 v1.1 §5-3·过程通道·确定性追问线索·零 LLM）
      //   存 trace·答案完毕后 renderSuggest 优先渲染为「追问建议」条（点击回填输入框·不直发）
      //   SHELL2(FIX) FIX-09：归一化改走纯函数（非数组/非串/空串/超 3 条统一处理）
      const _cuesNorm = normalizeFollowupCues(e.followup_cues);
      if (_cuesNorm.length && _curTrace) {
        _curTrace.followupCues = _cuesNorm;
      }
      setPhase('思考');   // Feature 3：工具结果属"思考"阶段（原"检索"并入思考·检索非独立步骤）
      const _lc = (() => { try { return document.querySelectorAll('#layer-list .layer-row').length - _layerBase; } catch (_) { return 0; } })();
      const _t = dockEl() && dockEl().querySelector('.aiq-thinking-text');   // E2：dock 显"已生成 N 层"（增量落图·图在长感知）
      if (_t) _t.textContent = _lc > 0 ? `已生成 ${_lc} 层·继续…` : '整合结果中…';
      autoScroll();
    }
  });
  _bus.on(ACP_FAMILY.MSG_DELTA, (e) => {
    if (e.kind === 'content') { const tok = e.token;
      if (!streamAcc) { _markReasonDone(); _setFinalState('streaming'); }   // Feature 2：首 token→理解节点完成 + 生成节点激活（绿脉动流式）
      setPhase('生成');
      streamAcc += tok;
      if (_curTrace) _curTrace.final = streamAcc;
      if (!streamRaf) streamRaf = requestAnimationFrame(drainStream);
    }
  });
  // 出口三段式 P0：结果结构化（harness 确定性组装·先于 seal 派发·seal 统一渲染）
  _bus.on(ACP_FAMILY.RENDER, (e) => {
    if (e.kind === 'result.struct') { const struct = e.struct;
      _pendingStruct = struct || null;
    }
  });
  _bus.on(ACP_FAMILY.TURN, (e) => {
    if (e.verb === 'seal') { const text = e.text;
      cancelStream();
      streamAcc = text || '';
      stopThinking();
      updateContextCapacity(getLastUsage());
      // 出口三段式 P0：观点卡置顶 + 4 要点卡底部（确定性提取·无观点不显卡·提取失败不阻塞正文）
      let _answerText = text || '';
      let _insightHtml = '';
      let _pointsHtml = '';
      try {
        const _s = _pendingStruct;
        if (_s && _s.insight) {
          _insightHtml = '<div class="emc-insight-card"><div class="emc-card-head">观点</div>'
            + `<div class="emc-insight-text">${escapeHtml(_s.insight)}</div></div>`;
          // 移除观点引用块防正文重复（整块捕获·与 result-struct 提取正则对齐·防多行引用残留）
          _answerText = _answerText.replace(/^>\s*\*\*观点：\*\*\s*[\s\S]*?(?=\n\n|\n\s*[^>]|$)/m, '');
        }
        if (_s && _s.points) _pointsHtml = _pointsCardHtml(_s.points);
      } catch (_) { /* 提取失败不阻塞正文 */ }
      _pendingStruct = null;
      shell.answerEl.innerHTML = _insightHtml + renderAnswer(_answerText, getValidRefNames()) + _pointsHtml;
      enhanceCodeBlocks(shell.answerEl);
      finalizeReason();   // flush 最后一帧思考 + 整块 is-done + 主题目录重切
      _setFinalState('done');   // Feature 2：生成节点完成（灰）
      if (_curTrace) _curTrace.final = text;
      shell._finalMd = text;   // 供页脚「复制回答」取最终 markdown
      // CB-09 D024：seal 即完成（defense 不显 UI·renderReview 永隐）；history 在 send 末尾统一持久化
    }
  });
  // CB-16 Wave 0/3：出口卡片（结果范式 agent·第三段）·确定性 JSON → 纯模板渲染（Wave 3 多卡循环）
  _bus.on(ACP_FAMILY.RENDER, (e) => {
    if (e.kind === 'outlet.card') { const cards = e.cards;
      if (!cards) return;
      const list = Array.isArray(cards) ? cards : [cards];   // 兼容单卡（旧端点 d.card）
      if (!list.length) return;
      if (_curTrace) _curTrace.outlet_card = list;
      for (const c of list) { try { renderOutletCard(c); } catch (_) { /* 渲染失败不阻塞 */ } }
    }
  });
  // CB-09 D024：质量防线结果（取代旧 onReview）·供 episode 自成长·不显 UI（renderReview 永隐）
  _bus.on(ACP_FAMILY.RENDER, (e) => {
    if (e.kind === 'defense') { const defense = e.defense;
      if (_curTrace) _curTrace.defense = defense;
      renderReview(shell.reviewEl);
    }
  });
  _bus.on(ACP_FAMILY.ERROR, (e) => {
    if (e.kind !== 'degraded') return;
      cancelStream();
      stopThinking();
      // SHELL2(FIX) FIX-10：白名单原因行（非裸文本）——按错误码映射固定文案·未知码归通用行；
      // 原始 hint 只存 trace 供调试（不显 UI）·保持「永不裸输原始错误」红线。
      const _REASON_LABEL = { 'DEGRADED_PARSE': '模型输出未能解析为可执行动作', 'DSH_ENGINE_FAIL': '[dsh引擎] 端点暂不可用（已自动诊断）' };
      const _code = (e.wire && e.wire.code) || '';
      const _reasonLine = `> 原因：${_REASON_LABEL[_code] || '处理过程中出现异常'}（自动诊断）\n\n`;
      // 永不裸输原始 token（根治代码块/计划文泄漏）：固定降级卡，忽略传入的 raw 文本
      const _degradedText = '## 暂未能完成此分析\n\n模型输出未能解析为可执行动作，且最终结论生成失败。\n\n**建议**：换一种问法或缩小范围（指定某区、某类用地、某时点）后重试；若反复失败，可上传更明确的数据范围。';
      shell.answerEl.innerHTML = renderAnswer(_reasonLine + _degradedText, getValidRefNames());
      enhanceCodeBlocks(shell.answerEl);
      if (_curTrace) { _curTrace.exit = 'gap'; _curTrace.final = _degradedText; _curTrace.degradeReason = _code || 'unknown'; if (e.hint) _curTrace.degradeHint = String(e.hint).slice(0, 200); }
      shell._finalMd = _degradedText;
      finalizeReason();   // 降级前已流式的思考也结构化（无思考内容则藏 reason 块）
  });
  return _acp.emitter;
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
  // CB-22d P0-0-4：quick-rag 轮知识问答标记——diagnose.rag=true（_assembleKnowledgeQA 返回）→ intent 归 knowledge_qa
  //   （quick-rag 不调 diagnose·_distillTurn 原 intent='general'·导致下轮 priorTurn.intent 非 knowledge_qa·P0-2 路由条件失效）
  const _intent = (dg.rag && !dg.intent) ? 'knowledge_qa' : (dg.intent || '');
  // CB-22d P0-0-1：final_excerpt——上轮回答片段供下轮「标记到地图」提取项目名（LLM 看不到 final 原文的修复·glm F.1）
  // CB-22f D3：extracted 回灌——上轮知识问答的结构化地理/归因实体（追问衔接消费·≤2KB 守卫防上下文膨胀·glm/Codex）
  const _ext = (dg.extracted && dg.extracted.geo && dg.extracted.geo.length) ? dg.extracted : null;
  // CB-22i 修：extracted 是 {geo,attrs} 对象·`JSON.parse(...).slice` 报错（追问标记崩溃根因）·
  //   限制 = geo 数组截 ≤5（对象不能 .slice）·深拷贝防共享引用污染
  const _extLimited = _ext ? { geo: JSON.parse(JSON.stringify(_ext.geo || [])).slice(0, 5), attrs: (_ext.attrs || []).slice(0, 8) } : null;
  return { intent: _intent, method, done: done || '（无工具调用）', gap: gap || '', strategy: dp.strategy || '', final_excerpt: (t.final || '').slice(0, 400), extracted: _extLimited };
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

/** G6c（CB-12·依据 4 连问最简版）：分句——按句界标点切分（代码确定性·不做 LLM 拆解）。
 *  >1 句 → 拆成独立问（句数上限 2·防拖死）；单句 → 原样（不分）。
 *  逗号不分句（常在同一问内·如"分析西陵区，看看哪里最差"）。 */
function splitQuestions(text) {
  const t = String(text || '').trim();
  if (!t) return [];
  const parts = t.split(/[？?。！!；;\n]/).map((s) => s.trim()).filter(Boolean);
  if (parts.length < 2) return [t];
  return parts.slice(0, 2);   // 句数上限 2（防拖死·体验优先）
}

async function send(text, capsule) {
  const isCapsule = !!capsule;
  if (_streaming) return;
  _pendingStruct = null;   // 出口三段式 P0：send 起始重置（S1 审计·防中断后跨轮残留旧观点卡）
  // G6c：非胶囊非续作 → 多问拆解——逐句走完整管线（各自答案卡·防线/管线全继承·不新造执行）
  if (!isCapsule) {
    const _qs = splitQuestions(text);
    if (_qs.length > 1) {
      for (const q of _qs) await send(q, null);
      return;
    }
  }
  if (isCapsule) {   // CB-09 D020 胶囊点击：label 当用户消息 + ctx.capsule 路由 runCapsule（跳 diagnose Flash）
    text = (capsule && capsule.label) || '';
  } else {
    text = (text || '').trim();
    if (!text) return;
  }
  _userPinned = false;   // E6 新话轮强制跟随：上滑停跟仅话轮内有效，发新问即复位（appendMessage 已滚底 + 流式 autoScroll 续跟；ChatGPT/Claude 标准）
  const input = document.getElementById('chat-input');
  if (input && !isCapsule) input.value = '';
  _resetOptimize();   // 5.214 清优化状态（原文 + 按钮回 sparkle）
  appendMessage('user', escapeHtml(text));
  _history.push({ role: 'user', text });
  saveHistory();

  const shell = appendAssistantShell(null);
  if (!shell) return;
  _curTrace = { reason: '', reasonSegments: [], steps: [], final: '', defense: null, diagnose: null, caliber: null, startedAt: Date.now(), doneAt: null };
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
    capsule: isCapsule ? capsule : null,        // CB-09 D020 胶囊路由（null=NL 走 diagnose·对象=orchestrate 顶路由 runCapsule）
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
    // 引擎分发（壳二期 BA·三引擎可切换）：light=轻循环引擎（默认·?engine 缺省即此·零退化红线）/
    // dsh=BrainAdapter headless（降级形态·synthesized 桩事件）/ mock=S3 mock 对端（?acp-mock=1 回兼容）。
    // 三路均先走 buildHooks 接渲染订阅（bus 在其闭包内创建），再各自驱动事件流——send 尾部零改动。
    let _result;
    buildHooks(shell);
    const _engine = getEngineMode();
    if (_engine === 'dsh') {
      _result = await runDshEngine(shell._acp, ctx);
    } else if (_engine === 'codex') {   // PT-CB15 SPIKE：第四引擎（SSE 真流式·恒 real）
      _result = await runCodexEngine(shell._acp, ctx);
    } else if (_engine === 'mock') {
      _result = await runAcpMockPeer(shell._acp, ctx);
    } else {
      _result = await orchestrate(ctx, shell._acp);   // S4：传 ACP 通道·引擎侧原生 wire 发射
    }
    settled = true;
    if (_curTrace && _result) { _curTrace.exit = _result.exit || _curTrace.exit; _curTrace.newLayerCount = _result.newLayerCount; if (_result.defense) _curTrace.defense = _result.defense; }
    // CB-22d P0-0-4：quick-rag 轮知识问答标记——orchestrate 返回的 diagnose 含 rag:true（_assembleKnowledgeQA）
    //   写回 _curTrace.diagnose（onDiagnose 仅 diagnose 路径触发·quick-rag 不调·防下轮 priorTurn.intent='' 死代码）
    if (_curTrace && _result && _result.diagnose && _result.diagnose.rag && !_curTrace.diagnose) { _curTrace.diagnose = _result.diagnose; }
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
    // 统一在答案结束后持久化（onFinalDone 不再 push）
    if (_curTrace && (settled || _curTrace.final)) {
      _history.push({ role: 'assistant', trace: JSON.parse(JSON.stringify(_curTrace)) });
      saveHistory();
    }
    applyLongConvCollapse();   // 长对话折叠：新答完毕后，折叠旧的留近 N 展开
    // L3 情境日志（自成长闭环原料；fire-and-forget，失败静默不阻塞交付）
    if (_curTrace) {
      fetch('/api/v1/aiqa/episode', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text, diagnose: _curTrace.diagnose, final: _curTrace.final, defense: _curTrace.defense, ok: settled, capsule_clicked: isCapsule ? (capsule && capsule.skill) || null : null }),   // CB-09 D034：点击的胶囊 skill→episode→Pro 排序自我成长偏好
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
    if (!b || b.disabled) return;   // CB-12：pro 停用（disabled·点击忽略·强制 flash）
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
  if (_history.length === 0 && !_guidanceCardShown) {   // 空态且无 CPD 引导卡片才显欢迎卡（互斥）
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
      + '<div class="aiq-thinking-row"><span class="aiq-thinking-text">正在思考…</span><span class="aiq-dots"><i></i><i></i><i></i></span><span class="aiq-thinking-elapsed" hidden></span><button class="aiq-abort-btn" type="button" title="取消（Esc）" hidden>取消</button></div>'
      + '<div class="aiq-phase-chips">'
      + ['理解', '思考', '生成'].map((c) => `<span data-phase="${c}">${c}</span>`).join('')
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
    btn.textContent = '↓';
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
  const sf = msgs.style.flex, sh = msgs.style.height, savedTop = msgs.scrollTop;
  msgs.style.flex = '0 0 auto'; msgs.style.height = 'auto';
  const contentH = msgs.offsetHeight;
  msgs.style.flex = sf; msgs.style.height = sh;   // 同步恢复（同帧不绘制无闪烁；style 变不触发 MutationObserver）
  msgs.scrollTop = savedTop;   // Bug 修复（v1.5）：height='auto' 测量会重置 scrollTop=0（容器撑满无溢出）→ 流式期 MutationObserver 每 token 触发 → 一直跳顶。save/restore 保滚动位置。
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

/** PT-CB14 C4（D-7 销号）：8080 对话框常驻引擎徽标——chat-head 内常驻显示当前 engine 模式
 * （light/dsh/mock·?engine 或 window.__EMC_ENGINE_MODE__ 决定·getEngineMode 单一权威）。 */
function _initEngineBadge() {
  const emc = document.getElementById('emc-panel');
  if (!emc || emc.querySelector('.emc-engine-badge')) return;
  const head = emc.querySelector('.chat-head');
  if (!head) return;
  const MODES = {
    light: { txt: '引擎·light', c: '#8fa0b5', bg: 'rgba(143,160,181,0.16)' },
    dsh: { txt: '引擎·dsh', c: '#d97757', bg: 'rgba(217,119,87,0.16)' },
    codex: { txt: '引擎·codex', c: '#10a37f', bg: 'rgba(16,163,127,0.16)' },
    mock: { txt: '引擎·mock', c: '#9a8fd8', bg: 'rgba(154,143,216,0.16)' },
  };
  const m = MODES[getEngineMode()] || MODES.light;
  const b = document.createElement('span');
  b.className = 'emc-engine-badge';
  b.textContent = m.txt;
  b.title = '当前引擎模式（?engine=light|dsh|codex|mock）';
  b.style.cssText = `font:10px/1.5 ui-monospace,Consolas,monospace;color:${m.c};`
    + `background:${m.bg};padding:1px 7px;border-radius:3px;`;
  const spacer = head.querySelector('.chat-head-spacer');
  if (spacer) head.insertBefore(b, spacer);   // 徽标贴标题右缘（spacer 撑开其余）
  else head.appendChild(b);
}

export function initChatPanel() {
  _setupEmcFloat();   // CPD Phase 1b：reparent EMC 到 #map 浮窗 + 恢复尺寸（先于事件绑定）
  _setupCpdBar();     // CPD Phase 2a：顶部进度条 + 摘要 chip（软折叠）
  _initEngineBadge();   // PT-CB14 C4（D-7 销号）：引擎徽标常驻（light/dsh/mock 跟随）
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
  document.getElementById('aiq-optimize')?.addEventListener('click', _toggleOptimize);   // 5.214 一键优化/撤销
  input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input.value); }
    else if (e.key === 'Escape' && _streaming && _abortCtl) { e.preventDefault(); _abortCtl.abort(); }
  });
  // textarea 自适应增高（长 prompt 体验，封顶 160px）
  input?.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(160, input.scrollHeight) + 'px';
    const _tags = _liveRecognize(input.value); _renderRecognize(_tags, _liveRecTip(input.value));   // 5.218 chip 两行：短语 + 方法 tip
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
