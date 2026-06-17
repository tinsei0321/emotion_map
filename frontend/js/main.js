// ═══ main.js — entry: wire map + sidebar + panel + toolbar + popup ═══
import { initMap, addEmotionPoints, setBasemap } from './map.js';
import { initPanel, setInfoCard, setOverview, setTable } from './panel.js';
import { initToolbar, setActiveBasemap } from './toolbar.js';
import { initSidebar, openImport } from './sidebar.js';
import { initPopup, showPopup } from './popup.js';
import { samplePoints, polarityStats, emotionColors } from './state.js';

function main() {
  // 1. Sample emotion data (Phase 1; Phase 2 → api.fetchPoints)
  const fc = samplePoints(80, 42);
  const { stats, total, scoreMean } = polarityStats(fc);

  // 2. Map (single init) + points layer + click → bottom-right popup
  const map = initMap('map');
  window.__map = map;   // dev hook (query/click in console + tests)
  map.on('load', () => {
    const colors = emotionColors();
    addEmotionPoints(fc, (feature) => showPopup(feature, colors));
  });

  // 3. Right panel: info card + overview + table
  initPanel();
  setInfoCard({
    file: 'sample_points.json',
    layers: '情绪点',
    l1: '—',
    l2: total,
    total,
  });
  setOverview({ stats, total, scoreMean });
  setTable(fc);

  // 4. Popup (close + empty-map collapse + capsule-click expand)
  initPopup(map);

  // 5. Left sidebar (collapse/expand, drag, import→sections, section toggles)
  initSidebar({
    onImport: (file) => {
      // Phase 1: just reflect the loaded file name; real parse is Phase 2
      setInfoCard({ file: file.name, layers: '情绪点', l1: '—', l2: total, total });
      console.log('[import] file =', file.name, '(Phase 2 parse)');
    },
  });

  // 6. Toolbar (draw-tool placeholders, Import/Export/M, basemap switch)
  initToolbar({
    onTool: (tool) => console.log('[tool]', tool),
    onImport: () => openImport(),
    onExport: ({ format, desensitize }) =>
      console.log('[export]', format, 'desensitize=' + desensitize, '(Phase 2)'),
    onBasemap: (key) => setBasemap(key),
  });
  setActiveBasemap('tianditu-img-nolabel');

  console.log('[OK] emotion-map frontend (geojson.io v2) loaded —', total, 'sample points');
}

document.addEventListener('DOMContentLoaded', main);
