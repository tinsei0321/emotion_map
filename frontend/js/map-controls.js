// ═══ map-controls.js — bottom-left unified cluster + one-segment scale bar ═══
// Cluster (one maplibregl-ctrl-group, geojson.io style): reset / 2D-3D / + / − / north.
// Anchored to #map via addControl('bottom-left') → rides along when the left panel
// folds (same logic as the old native NavigationControl; #map is a flex child that
// grows leftward as --left-w → 0). No --left-w reading needed.
//
// Design language: buttons reuse .maplibregl-ctrl-group button (32×32 white, token
// radius, gray-100 hover) so the whole cluster + the existing zoom buttons share ONE
// hover token → "deepen hover gray" stays a one-line global change (per user rule).
//
// No emoji (CLAUDE.md rule 1): SVG glyphs + ASCII/letters only.

import { toast } from './toast.js';

// Fixed pitch per view mode (industry-standard: Mapbox nav / Google Earth city = 60).
// Center + zoom are PRESERVED on toggle (non-jarring; matches Google/Mapbox 2D-3D UX).
const PITCH_2D = 0;
const PITCH_3D = 60;
const TOGGLE_DURATION = 600;   // ms — smooth easeTo
const RESET_DURATION = 800;

// Home view (mirrors map.js YICHANG) — reset target when no data is loaded.
const HOME = { center: [111.286, 30.708], zoom: 12 };

// ── SVG glyphs (currentColor → inherits button color) ──
const ICON_RESET =
  '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true">' +
  '<circle cx="8" cy="8" r="3.2"/><circle cx="8" cy="8" r="0.9" fill="currentColor" stroke="none"/>' +
  '<line x1="8" y1="0.8" x2="8" y2="3.4"/><line x1="8" y1="12.6" x2="8" y2="15.2"/>' +
  '<line x1="0.8" y1="8" x2="3.4" y2="8"/><line x1="12.6" y1="8" x2="15.2" y2="8"/></svg>';

const ICON_NORTH =
  '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">' +
  '<path d="M8 1.5 L11.8 13 L8 10 L4.2 13 Z" fill="currentColor"/></svg>';

// ── B2: 3-button tool set (cursor / measure / layers) — sits ABOVE the nav cluster ──
const ICON_CURSOR =
  '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round" aria-hidden="true">' +
  '<path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/></svg>';
const ICON_MEASURE =
  '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
  '<path d="M21.3 8.7l-8.5-8.5a1 1 0 0 0-1.4 0L1.3 10.4a1 1 0 0 0 0 1.4l8.5 8.5a1 1 0 0 0 1.4 0l10.1-10.1a1 1 0 0 0 0-1.4z"/>' +
  '<path d="M7.5 10.5l1.5 1.5M10.5 7.5l1.5 1.5M13.5 4.5l1.5 1.5M4.5 13.5l1.5 1.5"/></svg>';
const ICON_LAYERS =
  '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true">' +
  '<path d="M12 3L22 8L12 13L2 8L12 3Z"/><path d="M2 12L12 17L22 12"/><path d="M2 16L12 21L22 16"/></svg>';
const ICON_TIMELINE =
  '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
  '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>';

// ── geometry helpers ──
function metersPerPixel(map) {
  // Standard Web Mercator ground resolution at the map center, PITCH-INDEPENDENT.
  // (Scale bars show nominal map scale — same as Mapbox/MapLibre native ScaleControl.
  // Using screen unproject would mis-read under 3D tilt, since pitched pixels cover
  // more ground near the horizon than at the view center.)
  const lat = map.getCenter().lat;
  const zoom = map.getZoom();
  return (40075016.686 * Math.abs(Math.cos((lat * Math.PI) / 180))) /
    (256 * Math.pow(2, zoom));
}

/** Pick a "nice" round distance whose pixel width lands in [MIN, MAX] px. */
function niceSegment(mpp) {
  const CANDIDATES = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000];
  const MIN_PX = 60, MAX_PX = 120;
  let chosen = CANDIDATES[0];
  for (const c of CANDIDATES) {
    const px = c / mpp;
    if (px <= MAX_PX) chosen = c;        // largest that still fits under MAX
    if (px >= MIN_PX && px <= MAX_PX) { chosen = c; break; }  // ideal band
  }
  let px = chosen / mpp;
  if (px > MAX_PX) px = MAX_PX;
  if (px < MIN_PX) px = MIN_PX;
  const text = chosen >= 1000 ? (chosen / 1000) + ' km' : chosen + ' m';
  return { px: Math.round(px), text };
}

function featureBounds(fc) {
  let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity;
  for (const f of (fc.features || [])) {
    const c = f.geometry && f.geometry.coordinates;
    if (!c) continue;
    if (f.geometry.type === 'Point') {
      minLng = Math.min(minLng, c[0]); maxLng = Math.max(maxLng, c[0]);
      minLat = Math.min(minLat, c[1]); maxLat = Math.max(maxLat, c[1]);
    }
  }
  if (minLng === Infinity) return null;
  return [[minLng, minLat], [maxLng, maxLat]];
}

// ── build DOM ──
function makeButton(cls, innerHTML, title) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = cls;
  b.title = title;
  b.setAttribute('aria-label', title);
  b.innerHTML = innerHTML;
  return b;
}

/**
 * CPD Bottom dock + scale cluster (⑤⑥)。
 *  - 底部左 .emotion-controls-root：比例尺 + 放大/缩小 小圆钮（与 dock 底间隙一致）。
 *  - 底部中央 .bottom-dock：7 圆钮 cursor/measure/timeline/2D-3D/reset/north/basemap，
 *    与 time-bar / search 同尺寸 32px 圆形，gap 2px，始终居中。时间轴并入 dock
 *    （proxy 点击隐藏的 .time-bar，其 .tb-card 卡片独立定位照常弹出）。
 *  - reset 保当前 2D/3D 视角（只 recenter）；north 恢复 2D 正北（pitch 0 + bearing 0）。
 *
 * @param {maplibregl.Map} map
 * @param {() => object|null} getFC  reset 用其 fitBounds 到数据；null → HOME。
 */
export function initControls(map, { getFC } = {}) {
  // ══ 底部左：比例尺 + 缩放 +/- 小圆钮 ══
  const root = document.createElement('div');
  root.className = 'maplibregl-ctrl emotion-controls-root';
  const scale = document.createElement('div');
  scale.className = 'emotion-scale-ctrl';
  scale.innerHTML = '<span class="emotion-scale-label">—</span><div class="emotion-scale"></div>';
  const btnZoomIn = makeButton('emotion-scale-zoom', '+', '放大 / Zoom in');
  const btnZoomOut = makeButton('emotion-scale-zoom', '−', '缩小 / Zoom out');
  root.append(scale, btnZoomIn, btnZoomOut);

  // ══ 底部中央：Bottom dock（7 圆钮，与 time-bar/search 同尺寸 32px）══
  const dock = document.createElement('div');
  dock.className = 'bottom-dock';
  dock.setAttribute('role', 'toolbar');
  dock.setAttribute('aria-label', '底部 dock 栏');
  const btnCursor = makeButton('draw-tool is-active', ICON_CURSOR, '选择 / Select');
  btnCursor.setAttribute('data-tool', 'select');
  btnCursor.setAttribute('aria-pressed', 'true');
  const btnMeasure = makeButton('draw-tool', ICON_MEASURE, '测量 / Measure（待开发）');
  const btnTimeline = makeButton('dock-timeline', ICON_TIMELINE, '时间轴 / Timeline');
  const btnView = makeButton('emotion-ctrl-view', '2D', '切换 2D / 3D 视图');
  const btnReset = makeButton('emotion-ctrl-reset', ICON_RESET, '复位（保持当前 2D/3D 视角）');
  const btnNorth = makeButton('emotion-ctrl-compass', ICON_NORTH, '复北（恢复 2D 视图）');
  const btnBasemap = makeButton('draw-tool', ICON_LAYERS, '底图 / Basemap');
  btnBasemap.setAttribute('data-action', 'basemap');
  btnBasemap.setAttribute('aria-pressed', 'false');
  dock.append(btnCursor, btnMeasure, btnTimeline, btnView, btnReset, btnNorth, btnBasemap);
  btnMeasure.addEventListener('click', () => toast.info('测量功能待开发'));
  btnTimeline.addEventListener('click', () => document.querySelector('.time-bar')?.click());   // proxy 隐藏的 time-bar

  // ── behaviors ──
  btnZoomIn.addEventListener('click', () => map.zoomIn());
  btnZoomOut.addEventListener('click', () => map.zoomOut());
  // 复北：恢复 2D 正北（pitch 0 + bearing 0）
  btnNorth.addEventListener('click', () => map.easeTo({ pitch: 0, bearing: 0, duration: TOGGLE_DURATION }));

  // 2D/3D：保持 center+zoom，切 pitch（事件解耦 map.js setViewMode，免循环依赖）
  const syncViewLabel = () => {
    const is3D = map.getPitch() > 0.5;
    btnView.textContent = is3D ? '3D' : '2D';
    btnView.classList.toggle('is-active', is3D);
    btnView.setAttribute('aria-pressed', String(is3D));
  };
  btnView.addEventListener('click', () => {
    const to3D = map.getPitch() <= 0.5;
    document.dispatchEvent(new CustomEvent('grid:viewmode', { detail: to3D ? '3d' : '2d' }));
  });
  map.on('pitchend', syncViewLabel);
  syncViewLabel();

  // 复位：fit 数据/HOME，保持当前 pitch+bearing（不强制回 2D）
  btnReset.addEventListener('click', () => {
    const pitch = map.getPitch(), bearing = map.getBearing();
    const fc = getFC && getFC();
    const bounds = fc ? featureBounds(fc) : null;
    if (bounds) {
      map.fitBounds(bounds, { padding: 40, pitch, bearing, duration: RESET_DURATION });
    } else {
      map.flyTo({ center: HOME.center, zoom: HOME.zoom, pitch, bearing, duration: RESET_DURATION });
    }
  });

  // 比例尺：随 move 重算
  const label = scale.querySelector('.emotion-scale-label');
  const bar = scale.querySelector('.emotion-scale');
  const updateScale = () => {
    const mpp = metersPerPixel(map);
    if (!isFinite(mpp) || mpp <= 0) return;
    const { px, text } = niceSegment(mpp);
    bar.style.width = px + 'px';
    label.textContent = text;
  };
  map.on('move', updateScale);
  updateScale();

  map.getContainer().appendChild(root);
  map.getContainer().appendChild(dock);
  return { root, dock };
}
