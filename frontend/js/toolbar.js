// ═══ toolbar.js — draw-tool select, Import/Export/M actions, basemap popover ═══

/**
 * @param {object}  handlers
 * @param {(tool:string)=>void}  handlers.onTool      draw tool selected (select/point/line/...)
 * @param {()=>void}             handlers.onImport    open left sidebar Import
 * @param {({format,desensitize})=>void} handlers.onExport
 * @param {(key:string)=>void}   handlers.onBasemap   basemap key switched
 */
export function initToolbar({ onTool, onImport, onExport, onBasemap } = {}) {
  // ── Draw tools: single-select active group (S/P/L/Po/R/C) ──
  const drawTools = Array.from(document.querySelectorAll('.draw-tool[data-tool]'));
  drawTools.forEach((btn) => {
    btn.addEventListener('click', () => {
      const tool = btn.dataset.tool;
      if (tool === 'more') {                 // dropdown placeholder
        console.log('[toolbar] more-tools (Phase 2)');
        return;
      }
      drawTools.forEach((b) => {
        if (b.dataset.tool !== 'more') {
          b.setAttribute('aria-pressed', 'false');
          b.classList.remove('is-active');
        }
      });
      btn.setAttribute('aria-pressed', 'true');
      btn.classList.add('is-active');
      if (onTool) onTool(tool);
      console.log('[toolbar] tool =', tool, '(Phase 2 wiring)');
    });
  });

  // ── Right group: Import / Export / M ──
  document.querySelector('[data-action="import"]')?.addEventListener('click', () => {
    if (onImport) onImport();
  });
  document.querySelector('[data-action="export"]')?.addEventListener('click', () => {
    document.getElementById('modal-export').showModal();
  });
  document.querySelector('[data-action="basemap"]')?.addEventListener('click', (e) => {
    e.stopPropagation();
    togglePopover();
  });

  // ── Basemap popover cells ──
  document.querySelectorAll('.bm-cell').forEach((cell) => {
    cell.addEventListener('click', () => {
      document.querySelectorAll('.bm-cell').forEach((c) => c.classList.remove('is-active'));
      cell.classList.add('is-active');
      if (onBasemap) onBasemap(cell.dataset.basemap);
      document.getElementById('basemap-popover').hidden = true;
    });
  });
  // close popover on outside click
  document.addEventListener('click', (e) => {
    const pop = document.getElementById('basemap-popover');
    if (pop.hidden) return;
    if (!pop.contains(e.target) && !e.target.closest('[data-action="basemap"]')) pop.hidden = true;
  });

  // ── Export modal buttons ──
  document.querySelectorAll('[data-close]').forEach((b) =>
    b.addEventListener('click', () => document.getElementById('modal-export').close()));
  document.getElementById('export-confirm')?.addEventListener('click', () => {
    const format = document.getElementById('export-format').value;
    const desensitize = document.getElementById('export-desensitize').checked;
    if (onExport) onExport({ format, desensitize });
    document.getElementById('modal-export').close();
  });
}

function togglePopover() {
  const pop = document.getElementById('basemap-popover');
  pop.hidden = !pop.hidden;
}

/** Mark the active basemap cell (keeps popover in sync on programmatic switch). */
export function setActiveBasemap(key) {
  document.querySelectorAll('.bm-cell').forEach((c) =>
    c.classList.toggle('is-active', c.dataset.basemap === key));
}
