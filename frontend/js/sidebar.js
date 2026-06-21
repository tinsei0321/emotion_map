// ═══ sidebar.js — left panel: collapse/expand, drag, import trigger, layer manager ═══
import { token, getLayers, getLayer, setLayerVisible, removeLayer, layerLevel, layerDisplayColor, selectLayer, getSelectedLayerId, getSelectedLayer, reorderLayers, addLayer, getChildren, CONFIDENCE_RAMP, L2_POSITIVE, L2_NEGATIVE, L2_NEUTRAL_COLOR, HOTNESS_RAMP } from './state.js';
import { renderLayer, removeLayerFromMap, reorderAllZ } from './map.js';
import { toast } from './toast.js';
import { openSettingsPopover, closeSettingsPopover, openSettingsLayerId, isOpen } from './settings.js';
import { openHeatmapDialog } from './heatmap-tool.js';

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

/** Expand the right panel if folded (used when a layer is selected → show Overview). */
export function openRightPanel() {
  if (readVarPx('--right-w') < 1) togglePanel('right');
}

/** Show + color the legend block(s) for visible layers. The ramp/outline color
 *  tracks the SELECTED layer's paint (or the first visible layer of that type),
 *  so the legend stays in sync when a layer's color is edited. */
export function refreshLegend() {
  const vis = getLayers().filter((l) => l.visible);
  const sel = getSelectedLayer();
  const has = (pred) => vis.some(pred);

  // polarity (L2) — 5-color gradient bar (VP lime → P teal → Neutral blue → N orange → VN dark red)
  const l2 = vis.find((l) => l.colorMode === 'l2-positive' || l.colorMode === 'l2-neutral' || l.colorMode === 'l2-negative' || l.colorMode === 'polarity');
  sethidden('legend-polarity', !l2);
  if (l2) {
    const items = [
      ['非常积极', L2_POSITIVE['Very Positive']],
      ['积极',     L2_POSITIVE['Positive']],
      ['中性',     L2_NEUTRAL_COLOR],
      ['消极',     L2_NEGATIVE['Negative']],
      ['非常消极', L2_NEGATIVE['Very Negative']],
    ];
    const rows = document.getElementById('legend-l2-rows');
    if (rows) rows.innerHTML = items.map(([label, color]) =>
      `<div class="legend-row"><span class="dot" style="background:${color};border-color:${color}"></span>${label}</div>`).join('');
  }

  // confidence (L1) — ramp colored from the focus layer's paint.ramp
  const conf = (sel && sel.colorMode === 'confidence' && sel.visible) ? sel : vis.find((l) => l.colorMode === 'confidence');
  sethidden('legend-confidence', !conf);
  if (conf) {
    // L1 热度值 3 段离散色带（浅橙→橙→深橙红）
    const rampEl = document.querySelector('#legend-confidence .legend-ramp');
    if (rampEl) rampEl.innerHTML = HOTNESS_RAMP.map((c) => `<span class="legend-heat-seg" style="background:${c}"></span>`).join('');
  }

  // range — outline color from the focus range layer's paint.color
  const range = (sel && (sel.kind === 'polygon' || sel.kind === 'line') && sel.visible) ? sel : vis.find((l) => l.kind === 'polygon' || l.kind === 'line');
  sethidden('legend-range', !range);
  if (range) {
    const color = (range.paint && range.paint.color) || '#0c1c2e';
    const dot = document.querySelector('#legend-range .range-dot');
    if (dot) dot.style.borderTopColor = color;
  }
}
function sethidden(id, hidden) { const el = document.getElementById(id); if (el) el.hidden = hidden; }

// ── Layer manager (left panel) ────────────────────────────────────────────
const KIND_LABEL = { point: '点', line: '线', polygon: '面', heatmap: 'H' };
const eyeOpen = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>';
const eyeOff = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
// drag grip = three horizontal bars (movable hint), revealed on hover/drag
const GRIP = '<span class="layer-grip" title="拖拽排序"><svg viewBox="0 0 16 16" width="12" height="12"><line x1="3" y1="4" x2="13" y2="4"/><line x1="3" y1="8" x2="13" y2="8"/><line x1="3" y1="12" x2="13" y2="12"/></svg></span>';

let _dragId = null;   // id of the row being dragged

/** Level → next-action tag (blue). L0 需治理；L1/L2/range 无标记。 */
function levelTag(l) {
  const lv = layerLevel(l);
  if (lv === 'L0') return '<span class="layer-tag is-action">需治理</span>';
  return '';
}

/** Hint letter between 要素按钮 and name: R (range) / L0·L1·L2 (point), colored by the layer's display color. */
function hintChip(l) {
  const lv = layerLevel(l);
  const text = lv === 'range' ? 'R' : (lv || 'L0');
  return `<span class="layer-hint" style="color:${layerDisplayColor(l)}">${text}</span>`;
}

/** Group header row (draggable + eye to toggle all children; no select/del — those are on children). */
function groupRowHtml(g, children) {
  const allVis = children.length > 0 && children.every((c) => c.visible);
  return `<div class="layer-group" data-id="${g.id}" draggable="true" title="拖拽排序">
    ${GRIP}
    <button class="layer-eye" data-group-eye="${g.id}" title="${allVis ? '隐藏全部' : '显示全部'}">${allVis ? eyeOpen : eyeOff}</button>
    <span class="layer-group-chev">&#9662;</span>
    <span class="layer-group-name">${g.name}</span>
    <span class="layer-group-count">${children.length}</span>
  </div>`;
}

/** A single layer row (standalone or indented child). */
function layerRowHtml(l, openId, selId, isChild) {
  const kindEl = (l.kind === 'point' || l.kind === 'polygon' || l.kind === 'heatmap')
    ? `<button class="layer-kind${openId === l.id ? ' is-active' : ''}" data-feat="${l.id}" title="要素设置">${KIND_LABEL[l.kind]}</button>`
    : `<span class="layer-kind is-disabled" title="线暂未开放设置">${KIND_LABEL[l.kind] || '层'}</span>`;
  const sel = selId === l.id ? ' is-selected' : '';
  const childCls = isChild ? ' is-child' : '';
  const dragAttr = isChild ? '' : ' draggable="true"';   // children fixed order (P→Neutral→N)
  const grip = isChild ? '<span class="layer-grip-spacer"></span>' : GRIP;
  return `<div class="layer-row${sel}${childCls}${l.visible ? '' : ' is-off'}" data-id="${l.id}"${dragAttr}>
    ${grip}
    <button class="layer-eye" data-eye="${l.id}" title="${l.visible ? '隐藏' : '显示'}">${l.visible ? eyeOpen : eyeOff}</button>
    ${kindEl}
    ${hintChip(l)}
    <span class="layer-name" title="${l.name}">${l.name}</span>
    ${levelTag(l)}
    <button class="layer-del" data-del="${l.id}" title="删除">&times;</button>
  </div>`;
}

/** Re-render the layer list (groups + nested children + standalone layers). */
export function renderLayerList() {
  const list = document.getElementById('layer-list');
  if (!list) return;
  const all = getLayers();
  if (!all.length) { list.innerHTML = '<div class="layer-empty">尚未导入数据</div>'; return; }
  const openId = openSettingsLayerId();
  const selId = getSelectedLayerId();
  const byId = new Map(all.map((l) => [l.id, l]));
  const top = all.filter((l) => !l.parentId);   // groups + standalone layers

  let html = '';
  for (const l of top) {
    if (l.kind === 'group') {
      const kids = (l.children || []).map((cid) => byId.get(cid)).filter(Boolean);
      html += groupRowHtml(l, kids);
      for (const c of kids) html += layerRowHtml(c, openId, selId, true);
    } else {
      html += layerRowHtml(l, openId, selId, false);
    }
  }
  list.innerHTML = html;

  // wire button events (eye / del / feat)
  list.querySelectorAll('[data-eye]').forEach((b) =>
    b.addEventListener('click', (e) => { e.stopPropagation(); toggleEye(b.dataset.eye); }));
  list.querySelectorAll('[data-del]').forEach((b) =>
    b.addEventListener('click', (e) => { e.stopPropagation(); deleteLayer(b.dataset.del); }));
  list.querySelectorAll('[data-group-eye]').forEach((b) =>
    b.addEventListener('click', (e) => { e.stopPropagation(); toggleGroupEye(b.dataset.groupEye); }));
  list.querySelectorAll('[data-feat]').forEach((b) =>
    b.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = b.dataset.feat;
      const l = getLayer(id);
      if (!l) return;
      // Bug 2 fix: heatmap 图层的 H 按钮统一转调 HeatMap 弹窗（与 Toolbox 同入口、同参数集）
      if (l.kind === 'heatmap') { openHeatmapDialog(id); return; }
      if (isOpen() && openSettingsLayerId() === id) closeSettingsPopover();
      else {
        openSettingsPopover(l, b);
        selectLayer(id);
        document.dispatchEvent(new CustomEvent('layer:selected', { detail: id }));
      }
      renderLayerList();
    }));

  // row click → select (rows + L2 groups — both open Overview)
  list.querySelectorAll('.layer-row').forEach((row) =>
    row.addEventListener('click', () => selectLayerRow(row.dataset.id)));
  list.querySelectorAll('.layer-group').forEach((grp) =>
    grp.addEventListener('click', () => selectLayerRow(grp.dataset.id)));

  // drag → reorder z-order (bind to ALL draggable: top-level rows + L2 groups; children excluded)
  list.querySelectorAll('[draggable]').forEach((el) => {
    el.addEventListener('dragstart', (e) => {
      _dragId = el.dataset.id;
      el.classList.add('is-dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', _dragId);
    });
    el.addEventListener('dragend', () => { el.classList.remove('is-dragging'); clearDropHints(); });
    el.addEventListener('dragover', (e) => { e.preventDefault(); el.classList.add('is-drop-over'); });
    el.addEventListener('dragleave', () => el.classList.remove('is-drop-over'));
    el.addEventListener('drop', (e) => {
      e.preventDefault(); e.stopPropagation();
      const targetId = el.dataset.id;
      if (_dragId && _dragId !== targetId) {
        const rect = el.getBoundingClientRect();
        const after = (e.clientY - rect.top) > rect.height / 2;
        const ls = getLayers();
        const idx = ls.findIndex((x) => x.id === targetId);
        const toId = after ? (ls[idx + 1] ? ls[idx + 1].id : null) : targetId;
        reorderLayers(_dragId, toId);
        reorderAllZ();
      }
      _dragId = null;
      clearDropHints();
      renderLayerList();
      toast.info('图层顺序已更新');
    });
  });
}

function clearDropHints() {
  document.querySelectorAll('.layer-row.is-drop-over').forEach((r) => r.classList.remove('is-drop-over'));
}

/** Select a layer row → highlight + tell main.js to open the right panel + Overview. */
function selectLayerRow(id) {
  const l = getLayer(id);
  if (!l) return;
  selectLayer(id);
  renderLayerList();
  document.dispatchEvent(new CustomEvent('layer:selected', { detail: id }));
}

function toggleEye(id) {
  const l = getLayer(id);
  if (!l) return;
  setLayerVisible(id, !l.visible);
  renderLayer(l);
  renderLayerList();
  refreshLegend();   // legend syncs with visibility (hidden layer → legend hides)
  document.dispatchEvent(new CustomEvent('layers:changed'));   // 显隐 → popup/Overview 同步
  toast.info(`${l.visible ? '显示' : '隐藏'}图层：${l.name}`);
}

/** L2 group eye: toggle ALL children at once (any hidden → show all; all visible → hide all). */
function toggleGroupEye(groupId) {
  const children = getLayers().filter((l) => l.parentId === groupId);
  if (!children.length) return;
  const showAll = !children.every((c) => c.visible);
  for (const c of children) {
    setLayerVisible(c.id, showAll);
    renderLayer(c);
  }
  renderLayerList();
  refreshLegend();
  document.dispatchEvent(new CustomEvent('layers:changed'));   // 组显隐 → popup/Overview 同步
  toast.info(`${showAll ? '显示' : '隐藏'}全部子图层`);
}

function deleteLayer(id) {
  const l = getLayer(id);
  if (!l) return;
  if (openSettingsLayerId() === id) closeSettingsPopover();
  if (l.kind === 'group') {
    // remove children's map layers first, then state-cascade the group
    for (const cid of [...(l.children || [])]) removeLayerFromMap(cid);
    removeLayer(id);
  } else {
    const pid = l.parentId;
    removeLayerFromMap(id);
    removeLayer(id);
    if (pid) {   // child removed → drop the group if now empty
      const p = getLayer(pid);
      if (p && p.kind === 'group' && (!p.children || !p.children.length)) removeLayer(pid);
    }
  }
  renderLayerList();
  document.dispatchEvent(new CustomEvent('layers:changed'));
  toast.success(`已删除：${l.name}`);
}

/** Build a heatmap layer from L2 negative points (VN+N). Kepler-style density overlay:
 *  maps density through HEATMAP_NEGATIVE_STOPS, weights by score (more negative = hotter).
 *  First variant = 'negative' (积极/综合 待后续).
 *  v2: 废弃直接生成逻辑，统一转调 HeatMap 弹窗（避免旧入口与新入口并存导致 Bug 1）。 */
export function createHeatmap(variant = 'negative') {
  openHeatmapDialog();
}

// ── 工具栏 i 信息图标 tooltip（独立于 KDE 弹窗内的 #hm-tooltip）──
// 挂 body、触发 .tool-info[data-tip]，hover 显示应用场景简介；click 不冒泡到 .tool-row。
let _toolTipInit = false;
function initToolInfoTooltip() {
  if (_toolTipInit) return;
  _toolTipInit = true;
  const tip = document.createElement('div');
  tip.className = 'tool-tooltip';
  document.body.appendChild(tip);
  const show = (info) => {
    const text = info.dataset.tip || '';
    if (!text) return;
    tip.textContent = text;
    tip.classList.add('is-show');
    const r = info.getBoundingClientRect();
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    let left = r.left + r.width / 2 - tw / 2;
    let top = r.top - th - 8;
    if (top < 8) top = r.bottom + 8;
    left = Math.max(8, Math.min(left, window.innerWidth - tw - 8));
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  };
  const hide = () => tip.classList.remove('is-show');
  document.addEventListener('mouseover', (e) => {
    const info = e.target.closest('.tool-info');
    if (info) show(info);
  });
  document.addEventListener('mouseout', (e) => {
    if (e.target.closest('.tool-info')) hide();
  });
  // 点 i 仅看介绍，不触发所在 .tool-row（避免误开工具弹窗）
  document.addEventListener('click', (e) => {
    if (e.target.closest('.tool-info')) e.stopPropagation();
  }, true);
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
    closeSettingsPopover();
    for (const l of layers) { removeLayer(l.id); removeLayerFromMap(l.id); }
    renderLayerList();
    document.dispatchEvent(new CustomEvent('layers:changed'));
    toast.success('已清空全部图层');
  });

  // popover closed via outside-click/Escape → clear the kind marker's active state
  document.addEventListener('layer-settings:closed', renderLayerList);

  // placeholder Analysis handlers
  const log = (id) => console.log('[sidebar]', id, '(Phase 2 wiring)');
  document.getElementById('data-source')?.addEventListener('change', (e) => log('data-source=' + e.target.value));
  document.getElementById('run-governance')?.addEventListener('click', () => log('run-governance'));
  document.getElementById('run-analysis')?.addEventListener('click', () => log('run-analysis'));
  document.getElementById('tool-heatmap')?.addEventListener('click', () => openHeatmapDialog());
  document.getElementById('tool-attribution')?.addEventListener('click', () => {
    toast.info('多维归因分析（Toolbox 独立工具，开发中）');
  });
  initToolInfoTooltip();

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
