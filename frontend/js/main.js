// ═══ main.js — entry: wire map + sidebar + panel + toolbar + popup + import ═══
import { initMap, setBasemap, setClickHandler, renderLayer, fitBoundsTo, reorderAllZ } from './map.js';
import { initPanel, activateTab, setOverview, setTable } from './panel.js';
import { initToolbar, setActiveBasemap } from './toolbar.js';
import { initSidebar, openImport, openRightPanel, renderLayerList, showLayerManager, refreshLegend } from './sidebar.js';
import { initPopup, showPopup, showRangePopup } from './popup.js';
import { addLayer, addGroup, getLayers, getSelectedLayer, isDrawActive } from './state.js';
import {
  groupFiles, detectGroupType, parseGroup, reprojectFC, readPrj,
  splitByGeometry, detectColorMode, fcBBox,
} from './import.js';
import { openImportDialog } from './dialog.js';
import { initHeatmapTool } from './heatmap-tool.js';
import { initBufferTool } from './buffer-tool.js';
import { initDrawTool, startDraw, stopDraw } from './draw-tool.js';
import { initHeatmapLegend } from './heatmap-legend.js';
import { initSearchBar } from './search-bar.js';
import { toast } from './toast.js';
import { runExport } from './api.js';

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
          if (lines.features.length)    { const L = addLayer({ name: base, kind: 'line',    fc: lines });    L.srcName = base; renderLayer(L); added++; }
          if (polygons.features.length) { const L = addLayer({ name: base, kind: 'polygon', fc: polygons }); L.srcName = base; renderLayer(L); added++; }
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
              const group = addGroup({ name: 'L2 · 情绪地图 DATA', fc: pfc });
              group.srcName = base;
              const paint = { opacity: 0.80 };   // 80% opacity；radius 走 addPointPaint L2 自适应 3-6px
              const fcOf = (arr) => ({ type: 'FeatureCollection', features: arr });
              if (pos.length) { const L = addLayer({ name: `积极 · ${base}`, kind: 'point', parentId: group.id, colorMode: 'l2-positive', fc: fcOf(pos), paint }); L.srcName = base; renderLayer(L); added++; }
              if (neu.length) { const L = addLayer({ name: `中性 · ${base}`, kind: 'point', parentId: group.id, colorMode: 'l2-neutral',  fc: fcOf(neu), paint }); L.srcName = base; renderLayer(L); added++; }
              if (neg.length) { const L = addLayer({ name: `消极 · ${base}`, kind: 'point', parentId: group.id, colorMode: 'l2-negative', fc: fcOf(neg), paint }); L.srcName = base; renderLayer(L); added++; }
            } else {
              const paint = needsAnalysis ? { color: '#4a4a4a', opacity: 0.80, radius: 4 } : undefined;  // L0 默认深灰 + 80% + 4px
              const L = addLayer({ name: colorMode === 'confidence' ? `热度分布 · ${base}` : base, kind: 'point', fc: pfc, needsAnalysis, colorMode, paint });
              L.srcName = base;
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

/** Range upload: same pipeline as Import but drops CSV + point data; auto-opens the
 *  first range layer's popup (expanded) per spec. No confirm dialog (focused action). */
async function runRangeImport(files) {
  const filtered = Array.from(files || []).filter((f) => !/\.csv$/i.test(f.name));
  if (!filtered.length) { toast.info('Range 仅接受 GeoJSON / KML / Shapefile（不含 CSV）'); return; }
  const groups = groupFiles(filtered);
  let added = 0, firstRange = null, crsAny = false;
  for (const g of groups) {
    const type = detectGroupType(g);
    const base = layerName(g);
    if (!type) { toast.error(`${base}：无法识别格式，已跳过`); continue; }
    try {
      const prj = type === 'shapefile' ? await readPrj(g) : null;
      let fc = await parseGroup(g, type);
      const r = reprojectFC(fc, prj);
      if (r && r._crsWarn) { crsAny = true; fc = r.fc; } else fc = r;
      const { lines, polygons } = splitByGeometry(fc);   // points intentionally dropped (Range = 面/线)
      if (lines.features.length)    { const L = addLayer({ name: base, kind: 'line',    fc: lines });    L.srcName = base; renderLayer(L); if (!firstRange) firstRange = L; added++; }
      if (polygons.features.length) { const L = addLayer({ name: base, kind: 'polygon', fc: polygons }); L.srcName = base; renderLayer(L); if (!firstRange) firstRange = L; added++; }
      const bb = fcBBox(fc);
      if (bb) fitBoundsTo(bb);
    } catch (e) {
      console.error('[range-import]', e);
      toast.error(`${base}：${e.message || '解析失败'}`);
    }
  }
  renderLayerList();
  refreshLegend();
  refreshOverview();
  reorderAllZ();
  if (added) {
    showLayerManager();
    toast.success(`已上载 ${added} 个范围图层`);
    if (crsAny) setTimeout(() => toast.info('部分数据坐标系未知，按 WGS84 加载', 4500), 400);
    // 自动弹首个 range 层 popup（展开态）——用户要求
    if (firstRange && firstRange.fc && firstRange.fc.features && firstRange.fc.features.length) {
      showRangePopup(firstRange.fc.features[0], firstRange);
    }
  }
}

// ── Export helpers（后端 /export → blob 下载）──
function mergeFC(fcs) {
  const feats = [];
  for (const fc of fcs) if (fc && fc.features) feats.push(...fc.features);
  return { type: 'FeatureCollection', features: feats };
}
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
function exportFilename(fname, format, crs) {
  const ext = format === 'geojson' ? 'geojson' : format === 'csv' ? 'csv' : 'zip';
  const tag = (format === 'shp' && crs === 'cgcs2000') ? '_CGCS2000' : '';
  return `${fname}${tag}.${ext}`;
}
async function doExport({ format, crs, geom_csv, scope, desensitize }) {
  const realLayers = getLayers().filter((l) => l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length);
  let fc, fname;
  if (scope === 'all') {
    if (!realLayers.length) { toast.info('暂无可导出的图层'); return; }
    fc = mergeFC(realLayers.map((l) => l.fc));
    fname = 'emotion_map_all';
  } else {
    const sel = getSelectedLayer();
    if (!sel || !sel.fc || !sel.fc.features || !sel.fc.features.length) {
      toast.info('请先在图层列表选中一个图层（或在"范围"选"全部图层"）');
      return;
    }
    fc = sel.fc;
    fname = (sel.srcName || sel.name || 'layer').replace(/[^\w一-龥.\-]/g, '_');
  }
  try {
    const blob = await runExport({ geojson: fc, format, crs, geom_csv, desensitize, filename: fname });
    downloadBlob(blob, exportFilename(fname, format, crs));
    const tag = (format === 'shp' && crs === 'cgcs2000') ? ' (CGCS2000)' : '';
    toast.success(`已导出 ${format.toUpperCase()}${tag}`);
  } catch (e) {
    console.error('[export]', e);
    toast.error(`导出失败：${e.message || e}（确认后端已启动）`);
  }
}

function main() {
  const map = initMap('map');
  window.__map = map;   // dev hook
  // No seed sample — map starts empty; Import brings real data.
  setClickHandler((feature, colors, colorMode) => { if (isDrawActive()) return; showPopup(feature, colors, colorMode); });

  initPanel();
  initPopup(map);
  refreshOverview();    // empty-state overview

  initSidebar({ onFiles: runImport, onRangeFiles: runRangeImport });
  initHeatmapTool();
  initBufferTool();
  initSearchBar();
  initDrawTool(map);
  initHeatmapLegend();

  initToolbar({
    onTool: (tool) => {
      if (tool === 'polygon' || tool === 'rectangle') { startDraw(tool); return; }
      // select / point / line / circle：若在绘制中先退出（toolbar 已切激活态）
      if (isDrawActive()) stopDraw();
      if (tool === 'point' || tool === 'line' || tool === 'circle')
        toast.info('该绘制工具待开放（本轮已实现：多边形/矩形）');
    },
    onImport: () => openImport(),
    onExport: (opts) => doExport(opts),
    onBasemap: (key) => setBasemap(key),
  });
  setActiveBasemap('positron');

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
