// ═══ settings.js — Kepler-style layer settings popover (batch 2) ═══
// Opened by the 要素按钮 (.layer-kind) in each layer row. Adapts to layer kind/colorMode:
//   • point · confidence (L1) → sequential ramp picker + opacity
//   • point · polarity (L2) / needsAnalysis → opacity only (color is semantic/fixed)
//   • polygon              → fill toggle + color swatches + line width + fill opacity
//   • line                 → (no popover; marker non-interactive)
// Live: control change → setLayerPaint + renderLayer (re-renders that layer).

import { getLayer, setLayerPaint, L2_POSITIVE, L2_NEGATIVE, L2_NEUTRAL_COLOR, HEATMAP_NEGATIVE_STOPS, HEATMAP_RAMPS, HOTNESS_RAMP } from './state.js';
import { renderLayer, effectivePointRadius } from './map.js';
import { refreshPopupForLayer } from './popup.js';

// ── Presets ────────────────────────────────────────────────────────────────
const PRESET_RAMPS = [
  { id: 'orange', name: '橙', stops: ['#FFD9A0', '#FFB347', '#FF9800', '#FB8C00', '#E65100'] },
  { id: 'blue',   name: '蓝', stops: ['#CFE3F6', '#7FB8E8', '#3B8FD9', '#1E6BB8', '#0F3D72'] },
  { id: 'green',  name: '绿', stops: ['#D5F0D5', '#9CE0A0', '#5CCB6E', '#2EA84A', '#16632B'] },
  { id: 'purple', name: '紫', stops: ['#E5D9F0', '#C3A3DD', '#9870C4', '#6D44A0', '#3E1F66'] },
  { id: 'red',    name: '红', stops: ['#FAD4D0', '#F29A92', '#E15F54', '#B53A30', '#7A1E16'] },
  { id: 'gray',   name: '灰', stops: ['#E8E8E8', '#BDBDBD', '#8C8C8C', '#5A5A5A', '#2A2A2A'] },
];
const PRESET_COLORS = [
  '#0c1c2e', '#007afc', '#22b14c', '#e04848', '#9b59b6',
  '#1abc9c', '#e67e22', '#7f8c8d', '#c0392b', '#16a085',
];
const KIND_ZH = { point: '点', line: '线', polygon: '面', heatmap: '热' };

let _layerId = null;
let _outsideBound = false;

const el = () => document.getElementById('settings-popover');

/** @returns {string|null} the layer id whose popover is open (for sidebar .is-active). */
export function openSettingsLayerId() { return _layerId; }
export function isOpen() { return _layerId != null; }

/** Apply a paint patch: live-update map + popup (on every input tick).
 *  Pass commit=true on discrete actions / slider release to also fan out the
 *  change to legend + Overview (the "element-property tracks everywhere" rule). */
function applyPaint(patch, commit = false) {
  const l = getLayer(_layerId);
  if (!l) return;
  setLayerPaint(_layerId, patch);
  renderLayer(l);
  refreshPopupForLayer(_layerId);            // live-sync popup capsule
  if (commit) commitPaint();
}
function commitPaint() {
  document.dispatchEvent(new CustomEvent('layer:paint', { detail: _layerId }));
}

/** Open (or switch to) the popover for a layer, anchored beside the clicked button. */
export function openSettingsPopover(layer, anchorBtn) {
  if (!layer) return;
  _layerId = layer.id;
  build(layer);
  position(anchorBtn);
  const pop = el();
  if (pop) pop.hidden = false;
  bindOutside();
}

export function closeSettingsPopover() {
  _layerId = null;
  const pop = el();
  if (pop) pop.hidden = true;
}

function position(anchorBtn) {
  const pop = el();
  if (!pop || !anchorBtn) return;
  // align with the bottom-left map cluster (same left offset — "浮窗对齐边栏"基本逻辑)
  const cluster = document.querySelector('.emotion-controls-root');
  const leftX = cluster ? cluster.getBoundingClientRect().left
    : document.getElementById('left-panel').getBoundingClientRect().right + 10;
  const btn = anchorBtn.getBoundingClientRect();
  const top = Math.max(80, Math.min(btn.top, window.innerHeight - 320));
  pop.style.top = `${top}px`;
  pop.style.left = `${leftX}px`;
}

// ── Build popover DOM for a layer ──────────────────────────────────────────
function build(layer) {
  const pop = el();
  if (!pop) return;
  const p = layer.paint || {};
  const header = `
    <div class="set-head">
      <span class="set-kind">${KIND_ZH[layer.kind] || '层'}</span>
      <span class="set-name" title="${layer.name}">${layer.name}</span>
      <button class="set-close" id="set-close" title="关闭">&times;</button>
    </div>`;

  let body = '';
  if (layer.kind === 'point') {
    if (layer.colorMode === 'confidence') {
      // L1 热度值 = 强度 × 置信度，3 段动态分位（只读，色板随图层自动）
      const segs = HOTNESS_RAMP.map((c) => `<span class="set-legend-seg" style="background:${c}"></span>`).join('');
      body = `<div class="set-section"><div class="set-label">热度值（3 段·自动分位）</div>`
        + `<div class="set-legend-heat set-legend-segmented">${segs}</div>`
        + `<div class="set-legend-cap"><span>低</span><span>高</span></div></div>`
        + sectionPointSize(layer) + sectionOpacity(p.opacity ?? 0.75);
    } else if (layer.colorMode === 'l2-positive' || layer.colorMode === 'l2-negative' || layer.colorMode === 'l2-neutral') {
      body = l2PaletteLegend(layer.colorMode) + sectionPointSize(layer) + sectionOpacity(p.opacity ?? 0.18);
    } else if (layer.colorMode === 'needsAnalysis') {
      body = `<div class="set-note">颜色：暂无情绪字段（需治理）</div>` + sectionPointSize(layer) + sectionOpacity(p.opacity ?? 0.5);
    } else {
      body = `<div class="set-note">颜色：由极性决定</div>` + sectionPointSize(layer) + sectionOpacity(p.opacity ?? 0.9);
    }
  } else if (layer.kind === 'polygon') {
    body = sectionFill(p.fillOn) + sectionColor(p.color || '#0c1c2e') + sectionLineWidth(p.lineWidth ?? 2) + sectionFillOpacity(p.fillOpacity ?? 0.3, p.fillOn);
  } else if (layer.kind === 'heatmap') {
    // Full parameter set: Color (ramp legend) + Radius + Opacity + Intensity
    const rampName = (HEATMAP_RAMPS[p.rampKey] && HEATMAP_RAMPS[p.rampKey].name) || '消极红';
    body = sectionHeatmapLegend(p.rampKey)
      + `<div class="set-section"><div class="set-label">色带 <span class="set-val">${rampName}</span></div></div>`
      + rangeSection('半径', p.radius ?? 45, 'data-radius', 'px', 5, 150, 1)
      + rangeSection('透明度', Math.round((p.opacity ?? 0.7) * 100), 'data-op')
      + rangeSection('强度', p.intensity ?? 1, 'data-intensity', '', 0, 3, 0.1)
      + `<div class="set-section"><div class="set-label">权重字段 <span class="set-val">${p.weightField || 'score'}</span></div></div>`
      + `<div class="set-section"><div class="set-label">权重曲线 <span class="set-val">${p.weightCurve || 'linear-inverse'}</span></div></div>`;
  }
  pop.innerHTML = header + `<div class="set-body">${body}</div>`;
  wire(layer);
}

// ── Section templates ──────────────────────────────────────────────────────
function sectionRamp(currentRamp) {
  const cur = currentRamp ? JSON.stringify(currentRamp) : JSON.stringify(PRESET_RAMPS[0].stops);
  const items = PRESET_RAMPS.map((r) =>
    `<button class="ramp-btn${JSON.stringify(r.stops) === cur ? ' is-sel' : ''}" data-ramp-id="${r.id}" title="${r.name}">
      <span class="ramp-bar" style="background:linear-gradient(90deg, ${r.stops.join(',')})"></span>
    </button>`).join('');
  return `<div class="set-section"><div class="set-label">颜色 / Color</div><div class="ramp-list">${items}</div></div>`;
}
function sectionColor(currentColor) {
  const items = PRESET_COLORS.map((c) =>
    `<button class="swatch${c.toLowerCase() === (currentColor || '').toLowerCase() ? ' is-sel' : ''}" style="background:${c}" data-color="${c}" title="${c}"></button>`).join('');
  return `<div class="set-section"><div class="set-label">颜色 / Color</div><div class="swatch-list">${items}</div></div>`;
}
function sectionOpacity(op) {
  return rangeSection('透明度', Math.round(op * 100), 'data-op');
}
function sectionLineWidth(w) {
  return rangeSection('线宽', w, 'data-width', 'px', 1, 8, 1);
}
function sectionFillOpacity(op, fillOn) {
  return `<div class="set-section${fillOn ? '' : ' is-hidden'}" data-fillop-wrap>${rangeSection('填充透明度', Math.round(op * 100), 'data-fillop')}</div>`;
}
function sectionFill(fillOn) {
  return `<div class="set-section"><label class="set-toggle"><input type="checkbox" ${fillOn ? 'checked' : ''} data-fill><span>填充面域</span></label></div>`;
}
/** Point size slider (px). Default = effective radius (density or paint.radius override). */
function sectionPointSize(layer) {
  const r = effectivePointRadius(layer);
  return rangeSection('点大小', Number(r.toFixed(1)), 'data-radius', 'px', 1, 30, 0.5);
}
/** Read-only palette legend for L2 sub-layers (colors are fixed presets). */
function l2PaletteLegend(cm) {
  const sw = (hex, label) => `<span class="set-sw" style="background:${hex}"></span>${label}`;
  let inner = '';
  if (cm === 'l2-positive') inner = sw(L2_POSITIVE['Very Positive'], '非常积极') + sw(L2_POSITIVE['Positive'], '积极');
  else if (cm === 'l2-negative') inner = sw(L2_NEGATIVE['Very Negative'], '非常消极') + sw(L2_NEGATIVE['Negative'], '消极');
  else if (cm === 'l2-neutral') inner = sw(L2_NEUTRAL_COLOR, '中性');
  return `<div class="set-section"><div class="set-label">色板（固定）</div><div class="set-legend">${inner}</div></div>`;
}
/** Read-only density gradient bar for heatmap (Kepler Color). 稀疏→密集. */
function sectionHeatmapLegend(rampKey) {
  const stops = (HEATMAP_RAMPS[rampKey] && HEATMAP_RAMPS[rampKey].stops) || HEATMAP_NEGATIVE_STOPS;
  const segs = stops.slice(1).map(([, c]) => `<span class="set-legend-seg" style="background:${c}"></span>`).join('');
  const name = (HEATMAP_RAMPS[rampKey] && HEATMAP_RAMPS[rampKey].name) || '消极红';
  return `<div class="set-section">
    <div class="set-label">色带 / Color（${name}）</div>
    <div class="set-legend-heat set-legend-segmented">${segs}</div>
    <div class="set-legend-cap"><span>稀疏</span><span>密集</span></div>
  </div>`;
}
function rangeSection(label, val, attr, unit = '%', min = 0, max = 100, step = 1) {
  return `<div class="set-section">
    <div class="set-label">${label} <span class="set-val" data-val-for="${attr}">${val}${unit}</span></div>
    <input type="range" class="set-range" min="${min}" max="${max}" step="${step}" value="${val}" ${attr}>
  </div>`;
}

// ── Wire controls → applyPaint ─────────────────────────────────────────────
function wire(layer) {
  const pop = el();
  if (!pop) return;

  pop.querySelector('#set-close')?.addEventListener('click', closeSettingsPopover);

  // ramp (point confidence) — discrete click → commit
  pop.querySelectorAll('[data-ramp-id]').forEach((b) => {
    b.addEventListener('click', () => {
      const r = PRESET_RAMPS.find((x) => x.id === b.dataset.rampId);
      if (!r) return;
      applyPaint({ ramp: r.stops }, true);
      pop.querySelectorAll('[data-ramp-id]').forEach((x) => x.classList.remove('is-sel'));
      b.classList.add('is-sel');
    });
  });

  // color swatch (polygon) — discrete click → commit
  pop.querySelectorAll('[data-color]').forEach((b) => {
    b.addEventListener('click', () => {
      applyPaint({ color: b.dataset.color }, true);
      pop.querySelectorAll('[data-color]').forEach((x) => x.classList.remove('is-sel'));
      b.classList.add('is-sel');
    });
  });

  // fill toggle (polygon) — change → commit
  pop.querySelector('[data-fill]')?.addEventListener('change', (e) => {
    applyPaint({ fillOn: e.target.checked }, true);
    const wrap = pop.querySelector('[data-fillop-wrap]');
    if (wrap) wrap.classList.toggle('is-hidden', !e.target.checked);
  });

  // ranges
  bindRange(pop, '[data-op]', (v) => applyPaint({ opacity: v / 100 }), '%');
  bindRange(pop, '[data-width]', (v) => applyPaint({ lineWidth: v }), 'px');
  bindRange(pop, '[data-fillop]', (v) => applyPaint({ fillOpacity: v / 100 }), '%');
  bindRange(pop, '[data-radius]', (v) => applyPaint({ radius: v }), 'px');
  bindRange(pop, '[data-intensity]', (v) => applyPaint({ intensity: v }), '');
}
function bindRange(pop, sel, fn, unit) {
  const r = pop.querySelector(sel);
  if (!r) return;
  const valFor = sel.replace(/[[\]]/g, '');   // "data-op" → matches data-val-for
  const label = pop.querySelector(`[data-val-for="${valFor}"]`);
  // input = live (map + popup); change = release → commit (legend + Overview)
  r.addEventListener('input', (e) => {
    fn(Number(e.target.value));
    if (label) label.textContent = e.target.value + unit;
  });
  r.addEventListener('change', commitPaint);
}

// ── Outside-click / Escape to close ────────────────────────────────────────
function bindOutside() {
  if (_outsideBound) return;
  _outsideBound = true;
  document.addEventListener('click', (e) => {
    if (_layerId == null) return;
    const pop = el();
    if (pop && pop.contains(e.target)) return;
    if (e.target.closest && e.target.closest('.layer-kind')) return;   // sidebar handles
    closeSettingsPopover();
    document.dispatchEvent(new CustomEvent('layer-settings:closed'));
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && _layerId != null) { closeSettingsPopover(); document.dispatchEvent(new CustomEvent('layer-settings:closed')); } });
}
