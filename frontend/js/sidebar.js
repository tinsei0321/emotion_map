// ═══ sidebar.js — left panel: collapse/expand, drag gutters, import→sections, section toggles ═══
import { token } from './state.js';

const expandedWidth = { left: 0, right: 0 };   // last expanded width per side (for fold/restore)

function readVarPx(name) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return parseFloat(v) || 0;
}
function setSideVar(side, px) {
  document.documentElement.style.setProperty(side === 'left' ? '--left-w' : '--right-w', `${px}px`);
}

function clamp(px, min, max) { return Math.max(min, Math.min(max, px)); }

/** Toggle a panel between folded (0) and its last expanded width. */
function togglePanel(side) {
  const varName = side === 'left' ? '--left-w' : '--right-w';
  const cur = readVarPx(varName);
  const gutter = document.querySelector(`.gutter-${side}`);
  if (cur > 1) {
    // fold: remember width, collapse to 0
    expandedWidth[side] = cur;
    setSideVar(side, 0);
    if (gutter) gutter.classList.add('is-hidden');
  } else {
    // expand: restore (or default)
    const def = side === 'left'
      ? parseFloat(token('--geojson-layout-left-panel-width')) || 300
      : parseFloat(token('--geojson-layout-right-panel-width')) || 340;
    const w = expandedWidth[side] || def;
    setSideVar(side, w);
    if (gutter) gutter.classList.remove('is-hidden');
  }
  // flip chevron: expanded → fold-direction, folded → expand-direction
  const btn = document.querySelector(`.collapse-btn[data-side="${side}"]`);
  if (btn) {
    const folded = readVarPx(varName) < 1;
    btn.textContent = (side === 'left')
      ? (folded ? '›' : '‹')   // › expand  / ‹ fold
      : (folded ? '‹' : '›');  // ‹ expand  / › fold
  }
}

/** Initialize a drag gutter for a side (updates --left-w / --right-w live). */
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
      // allow very wide (table-friendly) but never overflow the viewport
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

export function initSidebar({ onImport } = {}) {
  // Collapse buttons
  document.querySelectorAll('.collapse-btn').forEach((btn) => {
    btn.addEventListener('click', () => togglePanel(btn.dataset.side));
  });

  // Drag gutters
  document.querySelectorAll('.gutter').forEach((g) => initDrag(g, g.dataset.side));

  // Section head toggles (Range / Layers / Analysis)
  document.querySelectorAll('.lp-section .section-head').forEach((head) => {
    head.addEventListener('click', () => head.parentElement.classList.toggle('open'));
  });

  // Placeholder handlers (Phase 2 wiring)
  const log = (id) => console.log('[sidebar]', id, '(Phase 2 wiring)');
  document.getElementById('data-source')?.addEventListener('change', (e) => log('data-source=' + e.target.value));
  document.getElementById('run-governance')?.addEventListener('click', () => log('run-governance'));
  document.getElementById('run-analysis')?.addEventListener('click', () => log('run-analysis'));
  document.querySelectorAll('[data-layer]').forEach((cb) =>
    cb.addEventListener('change', (e) => log('layer=' + e.target.dataset.layer + '=' + e.target.checked)));

  // Import triggers: file input + dropzone (drag/drop + click)
  const input = document.getElementById('import-input');
  const dropzone = document.getElementById('dropzone');
  const finishImport = (file) => {
    if (onImport) onImport(file);
    setLeftMode('sections');
  };
  input?.addEventListener('change', (e) => { if (e.target.files[0]) finishImport(e.target.files[0]); });
  if (dropzone) {
    dropzone.addEventListener('click', () => input?.click());
    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('drag-over'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('drag-over');
      if (e.dataTransfer.files[0]) finishImport(e.dataTransfer.files[0]);
    });
  }
}

/** Switch the left panel between 'import' and 'sections' modes, expanding it if folded. */
export function setLeftMode(mode) {
  // expand left if currently folded
  if (readVarPx('--left-w') < 1) togglePanel('left');
  document.querySelectorAll('.lp-mode').forEach((m) => {
    m.hidden = (m.dataset.mode !== mode);
  });
}

/** Open the left sidebar in Import mode (called by toolbar Import button). */
export function openImport() {
  setLeftMode('import');
  const input = document.getElementById('import-input');
  if (input) input.value = '';   // reset so same file re-triggers change
}
