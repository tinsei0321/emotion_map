// ═══ sidebar.js — left panel: collapse/expand, drag, import trigger, layer manager ═══
import { token, getLayers, getLayer, setLayerVisible, removeLayer } from './state.js';
import { renderLayer, removeLayerFromMap } from './map.js';
import { toast } from './toast.js';

const expandedWidth = { left: 0, right: 0 };

let _onFiles = null;   // (FileList) => void — registered by main.js pipeline

function readVarPx(name) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return parseFloat(v) || 0;
}
function setSideVar(side, px) {
  document.documentElement.style.setProperty(side === 'left' ? '--left-w' : '--right-w', `${px}px`);
}
function clamp(px, min, max) { return Math.max(min, Math.min(max, px)); }

function togglePanel(side) {
  const varName = side === 'left' ? '--left-w' : '--right-w';
  const cur = readVarPx(varName);
  const gutter = document.querySelector(`.gutter-${side}`);
  if (cur > 1) {
    expandedWidth[side] = cur;
    setSideVar(side, 0);
    if (gutter) gutter.classList.add('is-hidden');
  } else {
    const def = side === 'left'
      ? parseFloat(token('--geojson-layout-left-panel-width')) || 300
      : parseFloat(token('--geojson-layout-right-panel-width')) || 340;
    const w = expandedWidth[side] || def;
    setSideVar(side, w);
    if (gutter) gutter.classList.remove('is-hidden');
  }
  const btn = document.querySelector(`.collapse-btn[data-side="${side}"]`);
  if (btn) {
    const folded = readVarPx(varName) < 1;
    btn.textContent = (side === 'left') ? (folded ? '›' : '‹') : (folded ? '‹' : '›');
  }
}

function initDrag(gutter, side) {
  const min = parseFloat(token(side === 'left' ? '--geojson-layout-left-panel-min' : '--geojson-layout-right-panel-min')) || 220;
  const max = parseFloat(token(side === 'left' ? '--geojson-layout-left-panel-max' : '--geojson-layout-right-panel-max')) || 520;
  const varName = side === 'left' ? '--left-w' : '--right-w';
  gutter.addEventListener('mousedown', (e) => {
    e.preventDefault();
    document.body.classList.add('dragging');
    const start = e.clientX;
    const startW = readVarPx(varName);
    const move = (ev) => {
      const dx = ev.clientX - start;
      const viewCap = window.innerWidth - 220;
      const w = clamp(side === 'left' ? startW + dx : startW - dx, min, Math.min(max, viewCap));
      setSideVar(side, w);
    };
    const up = () => {
      document.body.classList.remove('dragging');
      expandedWidth[side] = readVarPx(varName);
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', up);
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
  });
}

// ── Import trigger ────────────────────────────────────────────────────────
// Both toolbar Import and left-panel Import are identical: open the NATIVE file
// picker (no submenu). Does NOT switch the left panel to sections — that only
// happens after a successful load (showLayerManager). 1:1 geojson.io.
export function openImport() {
  if (readVarPx('--left-w') < 1) setLeftMode('import');   // expand folded panel for context
  const input = document.getElementById('import-input');
  if (input) { input.value = ''; input.click(); }
}

/** After a successful load: switch left panel to sections + expand the Layers
 *  section so the layer manager is visible. Called by main.js runImport. */
export function showLayerManager() {
  setLeftMode('sections');
  const sec = document.querySelector('.lp-section[data-section="layers"]');
  if (sec) sec.classList.add('open');
}

/** Show only the legend block(s) matching loaded, visible layers. */
export function refreshLegend() {
  const layers = getLayers();
  const has = (pred) => layers.some((l) => l.visible && pred(l));
  sethidden('legend-polarity',    !has((l) => l.kind === 'point' && l.colorMode === 'polarity'));
  sethidden('legend-confidence',  !has((l) => l.kind === 'point' && l.colorMode === 'confidence'));
  sethidden('legend-range',       !has((l) => l.kind === 'polygon' || l.kind === 'line'));
}
function sethidden(id, hidden) { const el = document.getElementById(id); if (el) el.hidden = hidden; }

// ── Layer manager (left panel) ────────────────────────────────────────────
const KIND_LABEL = { point: '点', line: '线', polygon: '面' };
const eyeOpen = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>';
const eyeOff = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';

/** Re-render the layer list from the registry. Called after import/delete/toggle. */
export function renderLayerList() {
  const list = document.getElementById('layer-list');
  if (!list) return;
  const layers = getLayers();
  if (!layers.length) {
    list.innerHTML = '<div class="layer-empty">尚未导入数据</div>';
    return;
  }
  list.innerHTML = layers.map((l) => `
    <div class="layer-row${l.visible ? '' : ' is-off'}" data-id="${l.id}">
      <button class="layer-eye" data-eye="${l.id}" title="${l.visible ? '隐藏' : '显示'}">${l.visible ? eyeOpen : eyeOff}</button>
      <span class="layer-kind">${KIND_LABEL[l.kind] || '层'}</span>
      <span class="layer-name" title="${l.name}">${l.name}</span>
      ${l.needsAnalysis ? '<span class="layer-tag">需分析</span>' : ''}
      <button class="layer-del" data-del="${l.id}" title="删除">&times;</button>
    </div>`).join('');

  list.querySelectorAll('[data-eye]').forEach((b) => {
    b.addEventListener('click', (e) => { e.stopPropagation(); toggleEye(b.dataset.eye); });
  });
  list.querySelectorAll('[data-del]').forEach((b) => {
    b.addEventListener('click', (e) => { e.stopPropagation(); deleteLayer(b.dataset.del); });
  });
}

function toggleEye(id) {
  const l = getLayer(id);
  if (!l) return;
  setLayerVisible(id, !l.visible);
  renderLayer(l);
  renderLayerList();
  toast.info(`${l.visible ? '显示' : '隐藏'}图层：${l.name}`);
}

function deleteLayer(id) {
  const l = getLayer(id);
  if (!l) return;
  removeLayer(id);
  removeLayerFromMap(id);
  renderLayerList();
  document.dispatchEvent(new CustomEvent('layers:changed'));
  toast.success(`已删除：${l.name}`);
}

export function initSidebar({ onFiles } = {}) {
  _onFiles = onFiles;

  document.querySelectorAll('.collapse-btn').forEach((btn) =>
    btn.addEventListener('click', () => togglePanel(btn.dataset.side)));
  document.querySelectorAll('.gutter').forEach((g) => initDrag(g, g.dataset.side));
  document.querySelectorAll('.lp-section .section-head').forEach((head) =>
    head.addEventListener('click', () => head.parentElement.classList.toggle('open')));

  // clear-all trash at the Layers section header
  document.getElementById('layers-clear')?.addEventListener('click', () => {
    const layers = getLayers();
    if (!layers.length) { toast.info('没有可删除的图层'); return; }
    for (const l of layers) { removeLayer(l.id); removeLayerFromMap(l.id); }
    renderLayerList();
    document.dispatchEvent(new CustomEvent('layers:changed'));
    toast.success('已清空全部图层');
  });

  // placeholder Analysis handlers
  const log = (id) => console.log('[sidebar]', id, '(Phase 2 wiring)');
  document.getElementById('data-source')?.addEventListener('change', (e) => log('data-source=' + e.target.value));
  document.getElementById('run-governance')?.addEventListener('click', () => log('run-governance'));
  document.getElementById('run-analysis')?.addEventListener('click', () => log('run-analysis'));

  // Import: native file picker (multi). Both the panel button and toolbar route here.
  const input = document.getElementById('import-input');
  if (input) {
    input.setAttribute('multiple', '');
    input.addEventListener('change', (e) => {
      const fs = e.target.files;
      if (fs && fs.length && _onFiles) _onFiles(fs);
      e.target.value = '';
    });
  }
  // Left-panel Import = native <label>→<input> (no JS; avoids double picker).

  // Page-level drag-drop onto the map (1:1 geojson.io). Also keeps the dropzone hint.
  const mapEl = document.getElementById('map');
  const dz = document.getElementById('dropzone');
  if (dz) dz.addEventListener('click', () => openImport());
  if (mapEl) {
    mapEl.addEventListener('dragover', (e) => { e.preventDefault(); });
    mapEl.addEventListener('drop', (e) => {
      e.preventDefault();
      if (e.dataTransfer.files && e.dataTransfer.files.length && _onFiles) {
        _onFiles(e.dataTransfer.files);
      }
    });
  }

  renderLayerList();
  refreshLegend();
}

export function setLeftMode(mode) {
  if (readVarPx('--left-w') < 1) togglePanel('left');
  document.querySelectorAll('.lp-mode').forEach((m) => { m.hidden = (m.dataset.mode !== mode); });
}
