// ═══ main.js — entry: wire map + sidebar + panel + toolbar + popup + import ═══
import { initMap, setBasemap, setClickHandler, renderLayer, fitBoundsTo, reorderAllZ, getMap, setCompareMode, isCompareMode } from './map.js';
import { initPanel, activateTab, setOverview, setTable, activateOvTab, isOverallGrid } from './panel.js';
import { initTipPopup } from './tip-popup.js';
import { initToolbar, setActiveBasemap } from './toolbar.js';
import { initSidebar, openImport, renderLayerList, showLayerManager, refreshLegend } from './sidebar.js';
import { initPopup, showPopup, showRangePopup } from './popup.js';
import { addLayer, addGroup, getLayers, getSelectedLayer, selectLayer, focusLayer, getChildren, isRangeLayer, isToolAnalysisLayer, isEmotionPointLayer, isDrawActive, deriveTimeTag } from './state.js';
import {
  groupFiles, detectGroupType, parseGroup, reprojectFC, readPrj,
  splitByGeometry, detectColorMode, fcBBox,
} from './import.js';
import { openImportDialog } from './dialog.js';
import { landuseLayerPaint } from './landuse_colors.js';   // 导入的用地多边形自动附标准色

// E2E test seam 已去生产化 → frontend/js/e2e-seam.js（仅 ?e2e=1 时 index.html dynamic-import；生产永不加载，main.js 零 test 代码）。
import { initHeatmapTool } from './heatmap-tool.js';
import { initBufferTool } from './buffer-tool.js';
import { initGridTool } from './grid-tool.js';
import { initRangePresets } from './range-presets.js';
import { initChatPanel } from './ai_qa/panel.js';
import { initParamPanel } from './param-panel.js';
import { initDrawTool, startDraw, stopDraw } from './draw-tool.js';
import { initHeatmapLegend } from './heatmap-legend.js';
import { initSearchBar } from './search-bar.js';
import { initTimeline, bindGrid, unbindGrid } from './timeline.js';
import { loadManifest, tagLayer } from './time-source.js';
import { initTimeBar } from './time-bar.js';
import { toast } from './toast.js';
import { runExport } from './api.js';

function layerName(group) {
  if (group.kind === 'bundle') {
    const shp = group.files.find((f) => /\.shp$/i.test(f.name));
    return (shp ? shp.name : group.files[0].name).replace(/\.[^.]+$/, '');
  }
  return group.files[0].name;
}

/** 组卡标题带时间标签 T：有 T → `${base} · T1`；无 → base（去臃肿：T1/T2/T3 可区分）。 */
function tTagFor(fc, base) {
  const t = deriveTimeTag(fc);
  return t ? `${base} · ${t}` : base;
}

/** Enable/disable Export button based on whether any data layers exist. */
function updateExportState() {
  const has = getLayers().some((l) => l.kind !== 'group');
  const btn = document.getElementById('btn-export');
  if (btn) btn.disabled = !has;
}

/** 给所有层打时间标（datasetId/sliceKey，time-source.tagLayer）。
 *  幂等：manifest 未就绪时静默跳过，loadManifest 就绪后会再调一次兜底（处理「导入早于 manifest 就绪」竞态）。 */
function tagAllLayers() {
  getLayers().forEach(tagLayer);
}

/** Overview reflects the current VISIBLE focus layer（视野-数据-结论同步）。
 *  选中层可见 → 显它；否则回退到最顶可见分析层/点层并选它（眼睛切换图层后 Overview 即时追随）。
 *  Range 层不作为 Overview 焦点（它无归因数据）。 */
function refreshOverview() {
  let layer = getSelectedLayer();
  const visFocus = (l) => l && (l.kind === 'group' ? getChildren(l.id).some((c) => c.visible) : l.visible);
  if (!visFocus(layer)) {
    const vis = getLayers().filter((l) => l.visible && l.kind !== 'group' && !isRangeLayer(l));
    layer = vis.find(isToolAnalysisLayer) || vis.find(isEmotionPointLayer) || null;
    if (layer) selectLayer((focusLayer(layer) || layer).id);
  }
  setOverview(layer);
  // 时间轴（任务2）：仅 L2·综合·标准网格 焦点层时显（其 scaffold cell 承载 T1→T3 演进）
  const fl = layer && (focusLayer(layer) || layer);
  if (fl && isOverallGrid((fl.paint && fl.paint._ui) || {})) bindGrid(fl);
  else unbindGrid();
  const fc = (layer && layer.kind === 'point') ? layer.fc : { type: 'FeatureCollection', features: [] };
  setTable(fc, layer);
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
        const { type, config } = chosen[i] || {};
        const base = layerName(groups[i]);
        if (!type) { toast.error(`${base}：无法识别格式，已跳过`); continue; }
        try {
          const prj = type === 'shapefile' ? await readPrj(groups[i]) : null;
          let fc = await parseGroup(groups[i], type, config);
          const r = reprojectFC(fc, { prjWkt: prj, crs: config?.crs });
          if (r && r._crsWarn) { crsAny = true; fc = r.fc; } else fc = r;
          const ck = config?.crs;
          fc.__crs = (r && r._crsWarn) ? '投影坐标系 → WGS84 (EPSG:4326)'
            : ck?.type === 'gcj02' ? 'GCJ-02 → WGS84 (EPSG:4326)'
            : ck?.type === 'proj' ? '源坐标系 → WGS84 (EPSG:4326)'
            : 'WGS84 (EPSG:4326)';

          const { points, lines, polygons } = splitByGeometry(fc);
          if (fc.__crs) { points.__crs = lines.__crs = polygons.__crs = fc.__crs; }   // 传给 addLayer → layer.crsInfo
          if (lines.features.length)    { const L = addLayer({ name: base, kind: 'line',    fc: lines });    L.srcName = base; renderLayer(L); added++; }
          if (polygons.features.length) { const L = addLayer({ name: base, kind: 'polygon', fc: polygons, paint: landuseLayerPaint(polygons, base) || undefined }); L.srcName = base; renderLayer(L); added++; }
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
              const group = addGroup({ name: tTagFor(pfc, 'L2 · 情绪地图'), fc: pfc });
              group.srcName = base;
              const paint = { opacity: 0.80 };   // 80% opacity；radius 走 addPointPaint L2 自适应 3-6px
              const fcOf = (arr) => ({ type: 'FeatureCollection', features: arr });
              const tPref = (fc) => { const t = deriveTimeTag(fc); return t ? `${t}·` : ''; };
              if (pos.length) { const L = addLayer({ name: `${tPref(fcOf(pos))}积极·${base}`, kind: 'point', parentId: group.id, colorMode: 'l2-positive', fc: fcOf(pos), paint }); L.srcName = base; renderLayer(L); added++; }
              if (neu.length) { const L = addLayer({ name: `${tPref(fcOf(neu))}中性·${base}`, kind: 'point', parentId: group.id, colorMode: 'l2-neutral',  fc: fcOf(neu), paint }); L.srcName = base; renderLayer(L); added++; }
              if (neg.length) { const L = addLayer({ name: `${tPref(fcOf(neg))}消极·${base}`, kind: 'point', parentId: group.id, colorMode: 'l2-negative', fc: fcOf(neg), paint }); L.srcName = base; renderLayer(L); added++; }
            } else {
              const paint = needsAnalysis ? { color: '#4a4a4a', opacity: 0.80, radius: 4 } : undefined;  // L0 默认深灰 + 80% + 4px
              const _t = deriveTimeTag(pfc);
              const _tp = _t ? `${_t}·` : '';
              // 命名新规：L1 = 时间·热度分布·文件名；L0 = 时间·文件名（无 time_label 则无 T 前缀）
              const _name = colorMode === 'confidence' ? `${_tp}热度分布·${base}` : `${_tp}${base}`;
              const L = addLayer({ name: _name, kind: 'point', fc: pfc, needsAnalysis, colorMode, paint });
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
      tagAllLayers();            // 全局时间轴：给新导入层打 datasetId/sliceKey 标
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
      const r = reprojectFC(fc, { prjWkt: prj });
      if (r && r._crsWarn) { crsAny = true; fc = r.fc; } else fc = r;
      fc.__crs = (r && r._crsWarn) ? '投影坐标系 → WGS84 (EPSG:4326)' : 'WGS84 (EPSG:4326)';
      const { lines, polygons } = splitByGeometry(fc);   // points intentionally dropped (Range = 面/线)
      if (fc.__crs) { lines.__crs = polygons.__crs = fc.__crs; }
      if (lines.features.length)    { const L = addLayer({ name: base, kind: 'line',    fc: lines });    L.srcName = base; renderLayer(L); if (!firstRange) firstRange = L; added++; }
      if (polygons.features.length) { const L = addLayer({ name: base, kind: 'polygon', fc: polygons, paint: landuseLayerPaint(polygons, base) || undefined }); L.srcName = base; renderLayer(L); if (!firstRange) firstRange = L; added++; }
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
  initTipPopup(map);    // 网格/柱体/地形环 悬停浮动卡（自适应方位）
  refreshOverview();    // empty-state overview

  initSidebar({ onFiles: runImport, onRangeFiles: runRangeImport });
  initHeatmapTool();
  initBufferTool();
  initGridTool();
  initRangePresets();
  initChatPanel();
  initParamPanel();
  initSearchBar();
  initTimeline();
  initTimeBar();
  // 批4 Swipe 卷帘 POC：'c' 键 toggle compare 模式（Step 4 改 time-bar 正式入口）
  document.addEventListener('keydown', (e) => {
    if ((e.key === 'c' || e.key === 'C') && !/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) {
      setCompareMode(!isCompareMode());
    }
  });
  loadManifest().then(tagAllLayers).catch(() => {});   // 全局时间轴 manifest（就绪后给已导入层补打标）
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

  // Layer selected → 按"当前面板状态"路由（全局选择逻辑）：
  //   折叠展开 / 无激活态 / Overview 激活 → 显 Overview；
  //   Table 激活且未折叠 → 保持 Table（setTable(focused) 把下拉+表格切到该层）。
  document.addEventListener('layer:selected', (e) => {
    const wasFolded = !!(e.detail && e.detail.wasFolded);
    const ap = document.querySelector('.tab-pane.is-active');
    const isTable = !!(ap && ap.dataset.pane === 'table');
    if (wasFolded || !ap || !isTable) activateTab('overview');   // 折叠/无态/非Table → Overview
    refreshOverview();   // setOverview + setTable 都跑；激活的 pane 显对应内容
  });

  // 单元深读已改极性深读（非单格级）→ cell:selected 不再切 Overview 深读 tab / 不 zoom 单格。
  // cell-popup 地图胶囊卡由 tip-popup/popup 模块独立保留（hover/click 信息）；本事件口子留供 _renderIssueTable 行点击等复用。
  document.addEventListener('cell:selected', () => { /* 极性深读非单格级，无动作 */ });
  document.addEventListener('cell:cleared', () => {
    refreshOverview();
    activateOvTab('layer');     // 回「图层总览」+ easeBackFromCell 抬高视野
  });

  // Layer color edited (settings popover) → legend + Overview track the change.
  document.addEventListener('layer:paint', () => {
    refreshLegend();
    refreshOverview();
  });

  updateExportState();   // Export disabled initially (no data)

  // 启动自检：后端 :8000 是否就绪（serve.py 自起后端 + /api 反代）。
  // 失败 → 明确提示用 start.bat（勿用 py -m http.server 或 file://，二者无后端/反代，所有 /api 调用必失败）。
  fetch('/api/v1/health', { cache: 'no-store' })
    .then((r) => (r.ok ? r.json() : null))
    .then((j) => {
      if (j && j.status === 'ok') console.log('[OK] backend ready (:8000 via proxy)');
      else toast.info('后端未响应——请双击 start.bat 启动（serve.py 自起后端；勿用 py -m http.server 或 file://）', 6000);
    })
    .catch(() => toast.info('后端未响应——请双击 start.bat 启动（serve.py 自起后端；勿用 py -m http.server 或 file://）', 6000));

  console.log('[OK] emotion-map frontend (OpenFreeMap + toolbar icons + L2 group eye) loaded');
}

document.addEventListener('DOMContentLoaded', main);
