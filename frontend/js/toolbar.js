// ═══ toolbar.js — header tool buttons, basemap popover, export modal ═══

export function initToolbar({ onTool, onBasemap, onHeatToggle, onExport }) {
  // Generic tool buttons
  document.querySelectorAll('.tbtn[data-tool]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const tool = btn.dataset.tool;
      if (tool === 'basemap') return togglePopover();
      if (tool === 'export')  return openModal();
      if (tool === 'heat') {
        const next = btn.getAttribute('aria-pressed') !== 'true';
        btn.setAttribute('aria-pressed', String(next));
        btn.textContent = next ? 'H*' : 'H';
        if (onHeatToggle) onHeatToggle(next);
        return;
      }
      if (onTool) onTool(tool, btn);
    });
  });

  // Basemap popover
  document.querySelectorAll('.bm-cell').forEach((cell) => {
    cell.addEventListener('click', () => {
      document.querySelectorAll('.bm-cell').forEach((c) => c.classList.remove('is-active'));
      cell.classList.add('is-active');
      if (onBasemap) onBasemap(cell.dataset.basemap);
    });
  });
  // close popover on outside click
  document.addEventListener('click', (e) => {
    const pop = document.getElementById('basemap-popover');
    if (pop.hidden) return;
    if (!pop.contains(e.target) && !e.target.closest('[data-tool="basemap"]')) pop.hidden = true;
  });

  // Export modal
  document.querySelectorAll('[data-close]').forEach((b) =>
    b.addEventListener('click', () => document.getElementById('modal-export').close()));
  const confirmBtn = document.getElementById('export-confirm');
  confirmBtn.addEventListener('click', () => {
    const fmt = document.getElementById('export-format').value;
    const desensitize = document.getElementById('export-desensitize').checked;
    if (onExport) onExport({ format: fmt, desensitize });
    document.getElementById('modal-export').close();
  });
}

function togglePopover() {
  const pop = document.getElementById('basemap-popover');
  pop.hidden = !pop.hidden;
}

function openModal() {
  document.getElementById('modal-export').showModal();
}
