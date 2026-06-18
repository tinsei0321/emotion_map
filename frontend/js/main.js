// ═══ main.js — entry: wire map + sidebar + panel + toolbar + popup + import ═══
import { initMap, setBasemap, setClickHandler, renderLayer, fitBoundsTo } from './map.js';
import { initPanel, setInfoCard, setOverview, setTable } from './panel.js';
import { initToolbar, setActiveBasemap } from './toolbar.js';
import { initSidebar, openImport, renderLayerList, showLayerManager, refreshLegend } from './sidebar.js';
import { initPopup, showPopup } from './popup.js';
import { polarityStats, addLayer, mergedPointFC } from './state.js';
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

/** Right panel aggregated over visible point layers. */
function refreshOverview() {
  const fc = mergedPointFC();
  const { stats, total, scoreMean } = polarityStats(fc);
  setInfoCard({ file: total ? '已导入数据' : '未导入', layers: total ? '情绪点' : '—', l1: '—', l2: total, total });
  setOverview({ stats, total, scoreMean });
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
            const L = addLayer({ name: base, kind: 'point', fc: pfc, needsAnalysis, colorMode });
            renderLayer(L); added++;
            if (needsAnalysis) needsAny = true;
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
  });

  console.log('[OK] emotion-map frontend (Import v2 batch2) loaded');
}

document.addEventListener('DOMContentLoaded', main);
