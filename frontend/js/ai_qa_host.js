// ═══ ai_qa_host.js — 主窗口(地图)侧 · BroadcastChannel 监听执行器 ═══
// 职责：接收 chat 窗口的协议指令（ensure_zone/rank_zones/inspect_zone/open_attribution/focus），
// 映射到主窗口地图函数（generateGridForAI/setOverview/fitBoundsTo/cell:selected）并回包；
// 图层变化时主动推送 buildContext() grounding 摘要给 chat。
// 问答按钮 #chat-trigger → window.open(chat.html) 独立小窗；弹窗被拦 → 降级主页面浮窗。
import { CHANNEL, REQ, NOTIFY, PUSH } from './ai_qa/protocol.js';
import { getLayers, getSelectedLayer } from './state.js';
import { fitBoundsTo } from './map.js';
import { activateTab, setOverview } from './panel.js';
import { DOMAIN_LABEL, ELEMENT_LABEL } from './popup.js';
import { generateGridForAI } from './grid-tool.js';

let _ch = null;
let _lastGrid = null;          // 最近生成聚合层（ensure_zone/rank_zones 优先用）
let _floatInited = false;      // 浮窗降级是否已初始化

// ── 分析层判定 + 当前聚合层 ──────────────────────────────────────
function isAnalysis(l) {
  const ui = l && l.paint && l.paint._ui;
  return !!(l && l.kind === 'polygon' && ui && (ui.tool === 'grid' || ui.tool === 'terrain'));
}
function activeAnalysis() {
  if (_lastGrid && _lastGrid.layerId) {
    const l = getLayers().find((x) => x.id === _lastGrid.layerId);
    if (l) return l;
  }
  const sel = getSelectedLayer();
  if (sel && isAnalysis(sel)) return sel;
  return getLayers().find((l) => isAnalysis(l) && l.fc && l.fc.features && l.fc.features.length) || null;
}

/** 飞到单个 feature 的包络盒。 */
function fitToFeature(f) {
  const g = f && f.geometry;
  if (!g) return;
  const rings = g.type === 'Polygon' ? g.coordinates[0]
    : (g.type === 'MultiPolygon' ? g.coordinates.flatMap((p) => p[0]) : null);
  if (!rings || !rings.length) return;
  let mnX = Infinity, mxX = -Infinity, mnY = Infinity, mxY = -Infinity;
  for (const [x, y] of rings) { if (x < mnX) mnX = x; if (x > mxX) mxX = x; if (y < mnY) mnY = y; if (y > mxY) mxY = y; }
  if (isFinite(mnX)) fitBoundsTo([mnX, mnY, mxX, mxY]);
}

// ── buildContext：从主窗口图层算 grounding 摘要（迁自 chat-panel.js，chat 侧只接收）──
function buildContext() {
  const layers = getLayers();
  const an = activeAnalysis();
  const parts = [];
  const loaded = layers
    .filter((l) => l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length)
    .map((l) => `${l.name}(${l.fc.features.length}条)`).join('、');
  parts.push('已加载图层：' + (loaded || '（无）'));
  if (!an) {
    parts.push('（暂无网格/指定单元聚合层——区域级问题建议先 ensure_zone 生成聚合）');
    return parts.join('\n');
  }
  const feats = an.fc.features;
  parts.push(`当前分析层：${an.name}（${feats.length} 个聚合单元）`);
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

function pushContext() {
  if (!_ch) return;
  try { _ch.postMessage({ kind: 'push', type: PUSH.CONTEXT, payload: { summary: buildContext() } }); } catch (_) {}
}

// ── 排序：按维度找区域 ──────────────────────────────────────────
function sortZones(feats, crit) {
  const pi = (f) => Number((f.properties || {}).polarity_index);
  if (crit === 'worst') return feats.slice().sort((a, b) => pi(a) - pi(b));
  if (crit === 'best') return feats.slice().sort((a, b) => pi(b) - pi(a));
  if (crit.startsWith('domain:')) {
    const d = crit.split(':')[1];
    return feats.slice().sort((a, b) => {
      const pa = String((a.properties || {}).domain_top || '').includes(d) ? 1 : 0;
      const pb = String((b.properties || {}).domain_top || '').includes(d) ? 1 : 0;
      if (pb !== pa) return pb - pa;
      return Math.abs(pi(b)) - Math.abs(pi(a));
    });
  }
  if (crit.startsWith('element:')) {
    const e = crit.split(':')[1];
    return feats.slice().sort((a, b) => {
      const pa = String((a.properties || {}).element_top || '').includes(e) ? 1 : 0;
      const pb = String((b.properties || {}).element_top || '').includes(e) ? 1 : 0;
      if (pb !== pa) return pb - pa;
      return Math.abs(pi(b)) - Math.abs(pi(a));
    });
  }
  return feats.slice().sort((a, b) => Math.abs(pi(b)) - Math.abs(pi(a)));   // keyword / 未知 → |pi| 降序
}

// ── 指令处理（request）──
async function handleRequest(type, params) {
  switch (type) {
    case REQ.ENSURE_ZONE: return handleEnsureZone(params || {});
    case REQ.RANK_ZONES: return handleRankZones(params || {});
    case REQ.INSPECT_ZONE: return handleInspectZone(params || {});
    case REQ.OPEN_ATTRIBUTION: return handleOpenAttribution();
    default: return { ok: false, note: '未知请求：' + type };
  }
}

async function handleEnsureZone(params) {
  const existing = activeAnalysis();
  if (existing && existing.fc && existing.fc.features && existing.fc.features.length) {
    const n = existing.fc.features.length;
    return {
      ok: true,
      note: `复用现有聚合层「${existing.name}」（${n} 单元）`,
      data: { layerName: existing.name, featureCount: n, level: (existing.paint && existing.paint._ui && existing.paint._ui.level) || '' },
    };
  }
  try {
    const r = await generateGridForAI({
      analysis: params.analysis === 'zonal' ? 'zonal' : 'square',
      cellSize: Number(params.cell_size) || undefined,
      polarity: params.polarity || 'overall',
      mode: params.mode === '3d' ? '3d' : '2d',
      silent: true,
    });
    _lastGrid = { layerId: r && (r.layerId || r.id) };
    pushContext();   // 新层生成 → 推送新 grounding
    return {
      ok: true,
      note: `已生成聚合层「${r.layerName}」（${r.featureCount} 单元）`,
      data: { layerName: r.layerName, featureCount: r.featureCount, level: r.level },
    };
  } catch (e) {
    return { ok: false, note: '聚合层生成失败：' + (e && e.message ? e.message : e) };
  }
}

function handleRankZones(params) {
  const an = activeAnalysis();
  if (!an || !an.fc || !an.fc.features) return { ok: false, note: '暂无聚合层可定位（建议先 ensure_zone）' };
  const crit = params.criteria || 'worst';
  const top = Math.min(Math.max(Number(params.top) || 3, 1), 10);
  let feats = an.fc.features
    .filter((f) => f.properties && f.properties.polarity_index != null && !isNaN(f.properties.polarity_index));
  if (!feats.length) return { ok: false, note: '聚合层无极性数据，无法按情绪排序' };
  feats = sortZones(feats, crit).slice(0, top);
  const found = feats.map((f) => {
    const p = f.properties || {};
    return {
      name: p.name || p.issue_label || '未命名',
      pi: Number(p.polarity_index).toFixed(2),
      dom: DOMAIN_LABEL[p.domain_top] || p.domain_top || '?',
      elm: ELEMENT_LABEL[p.element_top] || p.element_top || '?',
      pc: p.point_count || 0,
    };
  });
  feats.forEach((f) => fitToFeature(f));   // 逐个飞过（末个停留）
  const label = { worst: '情绪最差', best: '情绪最好' }[crit] || crit;
  return { ok: true, note: `${label}：` + found.map((x) => `${x.name}(极性${x.pi})`).join('、'), data: { found } };
}

function handleInspectZone(params) {
  const an = activeAnalysis();
  const name = (params.name || '').trim();
  if (!an || !name) return { ok: false, note: '缺区域名或暂无聚合层' };
  const f = an.fc.features.find((ff) => {
    const nm = (ff.properties || {}).name || '';
    return nm === name || (nm && (nm.includes(name) || name.includes(nm)));
  });
  if (!f) return { ok: false, note: `未找到「${name}」` };
  fitToFeature(f);
  document.dispatchEvent(new CustomEvent('cell:selected', { detail: { feature: f, layer: an } }));
  const p = f.properties || {};
  return {
    ok: true,
    note: `已深读「${name}」`,
    data: { detail: `极性指数 ${Number(p.polarity_index).toFixed(2)}，${DOMAIN_LABEL[p.domain_top] || p.domain_top || '?'}×${ELEMENT_LABEL[p.element_top] || p.element_top || '?'}，${p.point_count || 0} 点；问题=${p.issue_label || '—'}` },
  };
}

function handleOpenAttribution() {
  const an = activeAnalysis();
  if (!an) return { ok: false, note: '暂无聚合层可展示归因' };
  activateTab('overview');
  setOverview(an);
  return { ok: true, note: '已展开 Overview 归因视图' };
}

// ── 单向通知（focus 定位）──
function handleNotify(type, params) {
  if (type === NOTIFY.FOCUS) {
    const names = Array.isArray(params.names) ? params.names : [];
    names.filter(Boolean).forEach((n) => focusByName(n));
  }
}
function focusByName(name) {
  const target = String(name).trim();
  for (const l of getLayers()) {
    if (!isAnalysis(l) || !l.fc || !l.fc.features) continue;
    const f = l.fc.features.find((ff) => {
      const nm = (ff.properties || {}).name || '';
      return nm === target || (nm && (nm.includes(target) || target.includes(nm)));
    });
    if (f) { fitToFeature(f); document.dispatchEvent(new CustomEvent('cell:selected', { detail: { feature: f, layer: l } })); return; }
  }
}

// ── 问答按钮：独立窗口 + 浮窗降级 ─────────────────────────────────
export function openChat() {
  const win = window.open('chat.html', 'emotion_map_ai',
    'width=440,height=620,menubar=no,toolbar=no,location=no,status=no,resizable=yes,scrollbars=yes');
  if (!win) {
    // 弹窗被拦 → 降级主页面浮窗（#chat-panel 从底部全宽改为右下浮窗，不挡地图）
    const panel = document.getElementById('chat-panel');
    if (panel) { panel.classList.remove('is-collapsed'); panel.classList.add('is-float-fallback'); initFloatingPanel(); }
  }
}

async function initFloatingPanel() {
  if (_floatInited) return;
  _floatInited = true;
  const { initChat } = await import('./ai_qa/panel.js');
  initChat({ onClose: () => {
    const panel = document.getElementById('chat-panel');
    if (panel) { panel.classList.add('is-collapsed'); panel.classList.remove('is-float-fallback'); }
  } });
}

/** 主窗口入口：挂 BroadcastChannel 监听 + 问答按钮。 */
export function initAiQaHost() {
  _ch = new BroadcastChannel(CHANNEL);
  _ch.onmessage = async (ev) => {
    const m = ev.data || {};
    if (m.kind === 'hello') { pushContext(); return; }
    if (m.kind === 'request') {
      const { id, type, params } = m;
      try {
        const r = await handleRequest(type, params || {});
        _ch.postMessage({ kind: 'response', id, ok: !!r.ok, data: r.data || null, note: r.note || '' });
      } catch (e) {
        _ch.postMessage({ kind: 'response', id, ok: false, note: (e && e.message) || String(e) });
      }
      return;
    }
    if (m.kind === 'notify') { handleNotify(m.type, m.params || {}); }
  };
  // 图层/选中变化 → 推送 grounding（chat 实时追随）
  document.addEventListener('layers:changed', pushContext);
  document.addEventListener('layer:selected', pushContext);
  // 问答按钮 → 独立窗口（降级浮窗）
  document.getElementById('chat-trigger')?.addEventListener('click', openChat);
}
