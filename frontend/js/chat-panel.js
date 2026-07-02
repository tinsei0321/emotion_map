// ═══ chat-panel.js — AI 自然语言问答（底部滑出面板，多轮 + 数据引用）═══
// 触发：右下「问答」按钮 → 底部滑出。流式渲染（marked markdown）+ 引用 chip（点击定位）。
// Grounding：每次发送前从选中分析层算紧凑摘要（Top 区域/极性/治理要素）作 context。
// provider-agnostic：后端 /chat 默认 DeepSeek，未来换溯佰科改后端一处。
import { streamChat } from './api.js';
import { getSelectedLayer, getLayers } from './state.js';
import { fitBoundsTo } from './map.js';
import { DOMAIN_LABEL, ELEMENT_LABEL } from './popup.js';
import { toast } from './toast.js';

const DOMAIN_ORDER = ['urban_planning', 'urban_governance', 'urban_renewal', 'urban_operation'];
let _messages = [];     // [{role, content}]
let _streaming = false;

function isAnalysis(l) {
  const ui = l && l.paint && l.paint._ui;
  return !!(l && l.kind === 'polygon' && ui && (ui.tool === 'grid' || ui.tool === 'terrain'));
}

/** 从选中层（或首个分析层）算紧凑摘要供 grounding。 */
function buildContext() {
  const layers = getLayers();
  const sel = getSelectedLayer();
  const an = (sel && isAnalysis(sel)) ? sel : layers.find(isAnalysis);
  const parts = [];
  parts.push('已加载图层：' + layers
    .filter((l) => l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length)
    .map((l) => `${l.name}(${l.fc.features.length}条)`).join('、') || '（无）');
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

/** markdown 渲染（marked 不可用退纯文本转义）+ [ref:NAME] → 可点引用 chip。 */
function renderContent(text) {
  let html = window.marked ? window.marked.parse(text) : `<p>${escapeHtml(text).replace(/\n/g, '<br>')}</p>`;
  html = html.replace(/\[ref:([^\]]+)\]/g, (_, name) =>
    `<button class="cite-chip" data-ref="${escapeHtml(name)}" type="button">${escapeHtml(name)}</button>`);
  return html;
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

function appendMessage(role, contentHtml, { stream = false } = {}) {
  const list = document.getElementById('chat-messages');
  if (!list) return null;
  const el = document.createElement('div');
  el.className = `chat-msg chat-msg-${role}`;
  el.innerHTML = `<div class="chat-bubble">${contentHtml}</div>`;
  list.appendChild(el);
  list.scrollTop = list.scrollHeight;
  return stream ? el.querySelector('.chat-bubble') : null;
}

async function send(text) {
  text = (text || '').trim();
  if (!text || _streaming) return;
  const input = document.getElementById('chat-input');
  input.value = '';
  appendMessage('user', escapeHtml(text));
  _messages.push({ role: 'user', content: text });
  const bubble = appendMessage('assistant', '<span class="chat-cursor">▍</span>', { stream: true });
  _streaming = true;
  updateSendBtn();
  let acc = '';
  const ctx = buildContext();
  try {
    await streamChat(_messages, ctx,
      (tok) => {
        acc += tok;
        if (bubble) bubble.innerHTML = renderContent(acc);
        const list = document.getElementById('chat-messages');
        list.scrollTop = list.scrollHeight;
      },
      (err) => {
        if (bubble) bubble.innerHTML = `<span class="chat-error">[问答失败] ${escapeHtml(err)}</span>`;
      });
    if (acc) _messages.push({ role: 'assistant', content: acc });
    if (bubble && !acc) bubble.innerHTML = '<span class="chat-error">（无内容返回——确认 DEEPSEEK_API_KEY 已配置）</span>';
    else if (bubble) bubble.innerHTML = renderContent(acc);   // 终态再渲染一次（去光标）
  } catch (e) {
    if (bubble) bubble.innerHTML = `<span class="chat-error">[请求失败] ${escapeHtml(e.message || e)}</span>`;
    toast.error('问答请求失败：' + (e.message || e));
  } finally {
    _streaming = false;
    updateSendBtn();
  }
}

function updateSendBtn() {
  const btn = document.getElementById('chat-send');
  if (btn) { btn.disabled = _streaming; btn.textContent = _streaming ? '回答中…' : '发送'; }
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
      toast.info(`定位到「${target}」`);
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

export function initChatPanel() {
  const trigger = document.getElementById('chat-trigger');
  trigger?.addEventListener('click', () => setPanel(true));
  document.getElementById('chat-close')?.addEventListener('click', () => setPanel(false));
  document.getElementById('chat-clear')?.addEventListener('click', () => {
    _messages = [];
    const list = document.getElementById('chat-messages');
    if (list) list.innerHTML = '';
    renderSuggest();
  });
  const sendBtn = document.getElementById('chat-send');
  const input = document.getElementById('chat-input');
  sendBtn?.addEventListener('click', () => send(input?.value));
  input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input.value); }
  });
  // 引用 chip 委托（消息流中动态生成）
  document.getElementById('chat-messages')?.addEventListener('click', (e) => {
    const chip = e.target.closest('.cite-chip');
    if (chip) onCitationClick(chip.dataset.ref);
  });
  renderSuggest();
}
