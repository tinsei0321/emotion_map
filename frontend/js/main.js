// ═══ main.js — entry: wire map + sidebar + panel + toolbar + popup + import ═══
import { initMap, setBasemap, setClickHandler, renderLayer, fitBoundsTo, reorderAllZ } from './map.js';
import { initPanel, activateTab, setOverview, setTable } from './panel.js';
import { initToolbar, setActiveBasemap } from './toolbar.js';
import { initSidebar, openImport, openRightPanel, renderLayerList, showLayerManager, refreshLegend } from './sidebar.js';
import { initPopup, showPopup } from './popup.js';
import { addLayer, addGroup, getLayers, getSelectedLayer } from './state.js';
import {
  groupFiles, detectGroupType, parseGroup, reprojectFC, readPrj,
  splitByGeometry, detectColorMode, fcBBox,
} from './import.js';
import { openImportDialog } from './dialog.js';
import { toast } from './toast.js';

function layerName(group) {
  if (group.kind === 'bundle') {
    const shp = group.files.find((f) => /\.shp$/i.test(f.name));
    return (shp ? shp.name : group.files[0].name).replace(/\.[^.]+$/, '');
  }
  return group.files[0].name;
}

/** Enable/disable Export button based on whether any data layers exist. */
function updateExportState() {
  const has = getLayers().some((l) => l.kind !== 'group');
  const btn = document.getElementById('btn-export');
  if (btn) btn.disabled = !has;
}

/** Overview reflects the SELECTED layer (per-layer 3-tier); empty state if none. */
function refreshOverview() {
  const layer = getSelectedLayer();
  setOverview(layer);
  const fc = (layer && layer.kind === 'point') ? layer.fc : { type: 'FeatureCollection', features: [] };
  setTable(fc);
}

/** Import pipeline: group → detect → confirm dialog → parse → CRS → split → register. */
async function runImport(files) {
  const groups = groupFiles(files);
  if (!groups.length) return;
  const detected = groups.map(detectGroupType);

  openImportDialog({
    groups,
    detectedTypes: detected,
    onCancel: () => toast.info('已取消导入'),
    onConfirm: async (chosen) => {
      let added = 0, needsAny = false, crsAny = false;
      for (let i = 0; i < groups.length; i++) {
        const type = chosen[i];
        const base = layerName(groups[i]);
        if (!type) { toast.error(`${base}：无法识别格式，已跳过`); continue; }
        try {
          const prj = type === 'shapefile' ? await readPrj(groups[i]) : null;
          let fc = await parseGroup(groups[i], type);
          const r = reprojectFC(fc, prj);
          if (r && r._crsWarn) { crsAny = true; fc = r.fc; } else fc = r;

          const { points, lines, polygons } = splitByGeometry(fc);
          if (lines.features.length)    { const L = addLayer({ name: base, kind: 'line',    fc: lines });    renderLayer(L); added++; }
          if (polygons.features.length) { const L = addLayer({ name: base, kind: 'polygon', fc: polygons }); renderLayer(L); added++; }
          if (points.features.length) {
            const { fc: pfc, colorMode, needsAnalysis } = detectColorMode(points);
            if (colorMode === 'polarity') {
              // L2 → split into Positive / Neutral / Negative under an L2 group (P→Neutral→N order)
              const pos = [], neu = [], neg = [];
              for (const f of pfc.features) {
                const pol = f.properties && f.properties.polarity;
                if (pol === 'Very Positive' || pol === 'Positive') pos.push(f);
                else if (pol === 'Very Negative' || pol === 'Negative') neg.push(f);
                else neu.push(f);
              }
              const group = addGroup({ name: `${base} · L2`, fc: pfc });
              const paint = { opacity: 0.80, radius: 8 };   // 80% opacity + fixed 8px
              const fcOf = (arr) => ({ type: 'FeatureCollection', features: arr });
              if (pos.length) { const L = addLayer({ name: 'L2-Positive', kind: 'point', parentId: group.id, colorMode: 'l2-positive', fc: fcOf(pos), paint }); renderLayer(L); added++; }
              if (neu.length) { const L = addLayer({ name: 'L2-Neutral',  kind: 'point', parentId: group.id, colorMode: 'l2-neutral',  fc: fcOf(neu), paint }); renderLayer(L); added++; }
              if (neg.length) { const L = addLayer({ name: 'L2-Negative', kind: 'point', parentId: group.id, colorMode: 'l2-negative', fc: fcOf(neg), paint }); renderLayer(L); added++; }
            } else {
              const L = addLayer({ name: base, kind: 'point', fc: pfc, needsAnalysis, colorMode });
              renderLayer(L); added++;
              if (needsAnalysis) needsAny = true;
            }
          }
          const bb = fcBBox(fc);
          if (bb) fitBoundsTo(bb);
        } catch (e) {
          console.error('[import]', e);
          toast.error(`${base}：${e.message || '解析失败'}`);
        }
      }

      renderLayerList();
      refreshLegend();
      refreshOverview();
      reorderAllZ();             // align map z-order with list order (list-top = map-top)
      if (added) {
        showLayerManager();                 // B5: switch to sections + expand Layers
        toast.success(`已导入 ${added} 个图层`);
        if (needsAny) setTimeout(() => toast.info('部分点缺少情绪/置信度字段，标记为「需分析」', 4500), 400);
        if (crsAny)   setTimeout(() => toast.info('部分数据坐标系未知，按 WGS84 加载', 4500), 800);
      }
    },
  });
}

function main() {
  const map = initMap('map');
  window.__map = map;   // dev hook
  // No seed sample — map starts empty; Import brings real data.
  setClickHandler((feature, colors, colorMode) => showPopup(feature, colors, colorMode));

  initPanel();
  initPopup(map);
  refreshOverview();    // empty-state overview

  initSidebar({ onFiles: runImport });

  initToolbar({
    onTool: (tool) => console.log('[tool]', tool),
    onImport: () => openImport(),
    onExport: ({ format, desensitize }) =>
      console.log('[export]', format, 'desensitize=' + desensitize, '(Phase 2)'),
    onBasemap: (key) => setBasemap(key),
  });
  setActiveBasemap('tianditu-img-nolabel');

  // Layer delete/clear → refresh list + legend + overview.
  document.addEventListener('layers:changed', () => {
    renderLayerList();
    refreshLegend();
    refreshOverview();
    updateExportState();
  });

  // Layer row selected → open right panel + show that layer's Overview.
  document.addEventListener('layer:selected', () => {
    openRightPanel();
    activateTab('overview');
    refreshOverview();
  });

  // Layer color edited (settings popover) → legend + Overview track the change.
  document.addEventListener('layer:paint', () => {
    refreshLegend();
    refreshOverview();
  });

  updateExportState();   // Export disabled initially (no data)

  console.log('[OK] emotion-map frontend (OpenFreeMap + toolbar icons + L2 group eye) loaded');
}

document.addEventListener('DOMContentLoaded', main);
