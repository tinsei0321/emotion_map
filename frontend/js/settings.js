// ═══ settings.js — Kepler-style layer settings popover (batch 2) ═══
// Opened by the 要素按钮 (.layer-kind) in each layer row. Adapts to layer kind/colorMode:
//   • point · confidence (L1) → sequential ramp picker + opacity
//   • point · polarity (L2) / needsAnalysis → opacity only (color is semantic/fixed)
//   • polygon              → fill toggle + color swatches + line width + fill opacity
//   • line                 → (no popover; marker non-interactive)
// Live: control change → setLayerPaint + renderLayer (re-renders that layer).

import { getLayer, setLayerPaint } from './state.js';
import { renderLayer } from './map.js';

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
const KIND_ZH = { point: '点', line: '线', polygon: '面' };

let _layerId = null;
let _outsideBound = false;

const el = () => document.getElementById('settings-popover');

/** @returns {string|null} the layer id whose popover is open (for sidebar .is-active). */
export function openSettingsLayerId() { return _layerId; }
export function isOpen() { return _layerId != null; }

/** Apply a paint patch to the open layer + re-render it on the map. */
function applyPaint(patch) {
  const l = getLayer(_layerId);
  if (!l) return;
  setLayerPaint(_layerId, patch);
  renderLayer(l);
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
  const lp = document.getElementById('left-panel').getBoundingClientRect();
  const btn = anchorBtn.getBoundingClientRect();
  const top = Math.max(80, Math.min(btn.top, window.innerHeight - 260));
  pop.style.top = `${top}px`;
  pop.style.left = `${lp.right + 8}px`;
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
      body = sectionRamp(p.ramp) + sectionOpacity(p.opacity ?? 0.75);
    } else {
      const whyFixed = layer.colorMode === 'needsAnalysis'
        ? '颜色：暂无情绪字段（需分析）'
        : '颜色：由极性决定（L2）';
      body = `<div class="set-note">${whyFixed}</div>` + sectionOpacity(p.opacity ?? (layer.colorMode === 'needsAnalysis' ? 0.85 : 0.9));
    }
  } else if (layer.kind === 'polygon') {
    body = sectionFill(p.fillOn) + sectionColor(p.color || '#0c1c2e') + sectionLineWidth(p.lineWidth ?? 2) + sectionFillOpacity(p.fillOpacity ?? 0.3, p.fillOn);
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

  // ramp (point confidence)
  pop.querySelectorAll('[data-ramp-id]').forEach((b) => {
    b.addEventListener('click', () => {
      const r = PRESET_RAMPS.find((x) => x.id === b.dataset.rampId);
      if (!r) return;
      applyPaint({ ramp: r.stops });
      pop.querySelectorAll('[data-ramp-id]').forEach((x) => x.classList.remove('is-sel'));
      b.classList.add('is-sel');
    });
  });

  // color swatch (polygon)
  pop.querySelectorAll('[data-color]').forEach((b) => {
    b.addEventListener('click', () => {
      applyPaint({ color: b.dataset.color });
      pop.querySelectorAll('[data-color]').forEach((x) => x.classList.remove('is-sel'));
      b.classList.add('is-sel');
    });
  });

  // fill toggle (polygon)
  pop.querySelector('[data-fill]')?.addEventListener('change', (e) => {
    applyPaint({ fillOn: e.target.checked });
    const wrap = pop.querySelector('[data-fillop-wrap]');
    if (wrap) wrap.classList.toggle('is-hidden', !e.target.checked);
  });

  // ranges
  bindRange(pop, '[data-op]', (v) => applyPaint({ opacity: v / 100 }), '%');
  bindRange(pop, '[data-width]', (v) => applyPaint({ lineWidth: v }), 'px');
  bindRange(pop, '[data-fillop]', (v) => applyPaint({ fillOpacity: v / 100 }), '%');
}
function bindRange(pop, sel, fn, unit) {
  const r = pop.querySelector(sel);
  if (!r) return;
  const valFor = sel.replace(/[[\]]/g, '');   // "data-op" → matches data-val-for
  const label = pop.querySelector(`[data-val-for="${valFor}"]`);
  r.addEventListener('input', (e) => {
    fn(Number(e.target.value));
    if (label) label.textContent = e.target.value + unit;
  });
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
