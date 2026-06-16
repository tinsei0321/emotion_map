// ═══ main.js — entry: wire map + layers + panel + toolbar ═══
import { initMap, addEmotionPoints, setBasemap, setHeatmap } from './map.js';
import { initPanel, setOverview, fillDetail } from './panel.js';
import { initToolbar } from './toolbar.js';
import { samplePoints, polarityStats } from './state.js';

function main() {
  // 1. Sample emotion data (Phase 1; Phase 2 → api.fetchPoints)
  const fc = samplePoints(80, 42);
  const { stats, total, scoreMean } = polarityStats(fc);

  // 2. Map (single init) + points layer + click → detail card
  const map = initMap('map');
  map.on('load', () => {
    addEmotionPoints(fc, (feature, colors) => fillDetail(feature, colors));
  });

  // 3. Right panel: overview + interactions
  initPanel();
  setOverview({ stats, total, scoreMean });

  // 4. Toolbar
  initToolbar({
    onTool: (tool) => {
      if (tool === 'overview') activateTabById('overview');
      else if (tool === 'analysis') activateTabById('analysis');
      else if (tool === 'detail') activateTabById('detail');
      else console.log('[tool]', tool, '(Phase 2+ wiring)');
    },
    onBasemap: (key) => setBasemap(key),
    onHeatToggle: (on) => setHeatmap(on),
    onExport: ({ format }) => console.log('[export]', format, '(Phase 2)'),
  });

  console.log('[OK] emotion-map frontend loaded —', total, 'sample points');
}

function activateTabById(name) {
  document.querySelectorAll('.ptab').forEach((t) =>
    t.classList.toggle('is-active', t.dataset.tab === name));
  document.querySelectorAll('.tab-pane').forEach((p) =>
    p.classList.toggle('is-active', p.dataset.pane === name));
}

document.addEventListener('DOMContentLoaded', main);
