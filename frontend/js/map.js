// ═══ map.js — MapLibre GL JS instance, multi-layer registry, basemap switch ═══
import { emotionColors, token, POLARITY_ORDER, getLayers, CONFIDENCE_RAMP, confidenceColor, L2_POSITIVE, L2_NEGATIVE, L2_NEUTRAL_COLOR } from './state.js';
import { initControls } from './map-controls.js';
import { showRangePopup } from './popup.js';

export const BASEMAPS = {
  'tianditu-img-nolabel': '../apps/static/tianditu_img_nolabel.json',
  'tianditu-img':         '../apps/static/tianditu_img.json',
  'tianditu-vec-nolabel': '../apps/static/tianditu_nolabel.json',
  'tianditu-vec':         '../apps/static/tianditu_label.json',
};
export const DEFAULT_BASEMAP = 'tianditu-img-nolabel';
const YICHANG = { center: [111.286, 30.708], zoom: 12 };
const NAVY = '#0c1c2e';
const HIT_WIDTH = 12;           // transparent hit-line width (easy hover/click on thin outlines)

/** Density-adaptive point radius (user spec, L0-L4 uniform): by point count → tier,
 *  and within a tier the radius breathes with zoom (zoom in = bigger).
 *    < 500           → 14–18px (= current sparse baseline)
 *    500 ≤ n < 2000  → 8–11px  (≈ 1/2 ~ 2/3)
 *    ≥ 2000          → 3–5px   (≈ 1/4, even smaller)
 *  Returns [rAtZoom8, rAtZoom14]. */
function densityStops(count) {
  if (count < 500) return [14, 18];
  if (count < 2000) return [8, 11];
  return [3, 5];
}
function densityRadiusExpr(count) {
  const [r8, r14] = densityStops(count);
  return ['interpolate', ['linear'], ['zoom'], 8, r8, 14, r14];
}
function densityRadiusAt(count, zoom) {
  const [r8, r14] = densityStops(count);
  const z = Math.max(8, Math.min(14, zoom));
  return r8 + (r14 - r8) * (z - 8) / 6;
}
/** Effective point radius for the settings slider default: paint.radius override, else density value at the current zoom. */
export function effectivePointRadius(layer) {
  const p = layer.paint || {};
  if (p.radius != null) return p.radius;
  return densityRadiusAt(layer.fc.features.length, map ? map.getZoom() : 11);
}

let map = null;
let _onPointClick = null;
let _selectedLayerId = null;   // which layer the selection halo belongs to (clear on hide/remove)
const _boundPoint = new Set();
const _boundRange = new Set();
let _tooltip = null;

export function initMap(container = 'map') {
  map = new maplibregl.Map({
    container, style: BASEMAPS[DEFAULT_BASEMAP],
    center: YICHANG.center, zoom: YICHANG.zoom, attributionControl: true,
  });
  initControls(map, { getBBox: mergedBBox });
  const canvas = map.getCanvas();
  map.on('dragstart', () => canvas.classList.add('is-grabbing'));
  map.on('dragend', () => canvas.classList.remove('is-grabbing'));
  return map;
}

export function getMap() { return map; }

export function setBasemap(key) {
  if (!map || !BASEMAPS[key]) return;
  map.setStyle(BASEMAPS[key], {
    transformStyle: (prev, next) => {
      const carrySources = {};
      for (const [id, spec] of Object.entries(prev?.sources || {})) {
        if (id.startsWith('lyr-') || id.startsWith('emotion-')) carrySources[id] = spec;
      }
      const carryLayers = (prev?.layers || []).filter((l) => l.id.startsWith('lyr-') || l.id.startsWith('emotion-'));
      return { ...next, sources: { ...(next.sources || {}), ...carrySources }, layers: [...(next.layers || []), ...carryLayers] };
    },
  });
}

export function setClickHandler(fn) { _onPointClick = fn; }

// ── Layer rendering ────────────────────────────────────────────────────────
const lyrSrc = (id) => `lyr-${id}`;
const lyrLid = (id) => `lyr-${id}`;
const lyrLineLid = (id) => `lyr-${id}-line`;
const lyrHitLid = (id) => `lyr-${id}-hit`;

/** (Re)render one registry layer. Hidden layers are fully removed (fill + outline + hit). */
export function renderLayer(layer) {
  if (!map) return;
  if (layer.kind === 'group') return;   // group container is not rendered on the map
  const sid = lyrSrc(layer.id);
  const lid = lyrLid(layer.id);
  const lineLid = lyrLineLid(layer.id);
  const hitLid = lyrHitLid(layer.id);
  for (const l of [hitLid, lineLid, lid]) if (map.getLayer(l)) map.removeLayer(l);
  if (map.getSource(sid)) map.removeSource(sid);
  if (!layer.visible || !layer.fc.features.length) {
    // hiding a point layer → its selection halo must go too
    if (!layer.visible && layer.kind === 'point') clearSelectionHalo(layer.id);
    return;
  }

  map.addSource(sid, { type: 'geojson', data: layer.fc });
  if (layer.kind === 'point') {
    addPointPaint(layer, sid, lid);
    bindPointInteractions(layer, lid);
  } else if (layer.kind === 'polygon') {
    addPolygonPaint(layer, sid, lid, lineLid, hitLid);
    bindRangeInteractions(layer, hitLid, lineLid);
  } else if (layer.kind === 'line') {
    addLinePaint(layer, sid, lid, hitLid);
    bindRangeInteractions(layer, hitLid, lid);
  }
  restackZ();   // keep z-order tied to list order (survives toggles)
}

/** Lightweight z-order fix using moveLayer (no re-render). Moves all lyr-* layers
 *  to match list order: list-top = map-top. Called after every renderLayer so
 *  toggling visibility doesn't scramble the stacking. */
export function restackZ() {
  if (!map) return;
  const layers = getLayers();
  for (let i = layers.length - 1; i >= 0; i--) {
    const l = layers[i];
    if (l.kind === 'group') continue;
    const ids = [lyrLid(l.id), lyrLineLid(l.id), lyrHitLid(l.id)];
    for (const id of ids) {
      if (map.getLayer(id)) map.moveLayer(id);   // move to top (no beforeId)
    }
  }
}

export function removeLayerFromMap(id) {
  if (!map) return;
  const sid = lyrSrc(id), lid = lyrLid(id), lineLid = lyrLineLid(id), hitLid = lyrHitLid(id);
  for (const l of [hitLid, lineLid, lid]) if (map.getLayer(l)) map.removeLayer(l);
  if (map.getSource(sid)) map.removeSource(sid);
  _boundPoint.delete(id); _boundRange.delete(id);
  clearSelectionHalo();   // a layer going away → selection halo can't stay (resets _selectedLayerId)
  removeHoverRing();
}

/** Remove the selection halo. Pass `id` to clear only if it matches the selected layer
 *  (used when hiding a specific point layer). No arg = clear unconditionally. */
export function clearSelectionHalo(id) {
  if (id != null && _selectedLayerId != null && _selectedLayerId !== id) return;
  _selectedLayerId = null;
  if (!map) return;
  const LAYER = 'emotion-selected-halo', SRC = 'emotion-selected';
  if (map.getLayer(LAYER)) map.removeLayer(LAYER);
  if (map.getSource(SRC)) map.removeSource(SRC);
}

export function applyAllLayers() { for (const layer of getLayers()) renderLayer(layer); }

/** Re-stack so list order = map z-order (list top = map top). Render in reverse
 *  list order → last rendered (list[0]) ends on top. Called after drag-reorder. */
export function reorderAllZ() {
  const layers = getLayers();
  for (let i = layers.length - 1; i >= 0; i--) renderLayer(layers[i]);
}

// ── Paint per kind ────────────────────────────────────────────────────────
function addPointPaint(layer, sid, lid) {
  const count = layer.fc.features.length;
  const p = layer.paint || {};
  // px override (settings slider) else density-adaptive zoom-interpolated radius
  const radius = (p.radius != null) ? p.radius : densityRadiusExpr(count);
  let colorExpr, strokeW, opacity;
  if (layer.colorMode === 'confidence') {
    const ramp = p.ramp || CONFIDENCE_RAMP;
    colorExpr = ['interpolate', ['linear'], ['get', 'score'],
      0, ramp[0], 0.25, ramp[1], 0.5, ramp[2], 0.75, ramp[3], 1, ramp[4]];
    strokeW = 0; opacity = p.opacity ?? 0.75;
  } else if (layer.colorMode === 'l2-positive') {
    colorExpr = ['match', ['get', 'polarity'], 'Very Positive', L2_POSITIVE['Very Positive'], 'Positive', L2_POSITIVE['Positive'], L2_POSITIVE['Positive']];
    strokeW = 0; opacity = p.opacity ?? 0.18;
  } else if (layer.colorMode === 'l2-negative') {
    colorExpr = ['match', ['get', 'polarity'], 'Very Negative', L2_NEGATIVE['Very Negative'], 'Negative', L2_NEGATIVE['Negative'], L2_NEGATIVE['Negative']];
    strokeW = 0; opacity = p.opacity ?? 0.18;
  } else if (layer.colorMode === 'l2-neutral') {
    colorExpr = L2_NEUTRAL_COLOR;
    strokeW = 0; opacity = p.opacity ?? 0.18;
  } else if (layer.colorMode === 'needsAnalysis' || layer.needsAnalysis) {
    colorExpr = token('--geojson-color-emotion-neutral') || '#a3a3a3';
    strokeW = 0; opacity = p.opacity ?? 0.5;
  } else {
    // legacy single polarity layer (frozen) — keep 5-color
    const colors = emotionColors();
    colorExpr = ['match', ['get', 'polarity'],
      'Very Positive', colors['Very Positive'], 'Positive', colors['Positive'],
      'Neutral', colors['Neutral'], 'Negative', colors['Negative'],
      'Very Negative', colors['Very Negative'], colors['Neutral']];
    strokeW = 1; opacity = p.opacity ?? 0.9;
  }
  map.addLayer({
    id: lid, type: 'circle', source: sid,
    paint: {
      'circle-radius': radius,
      'circle-color': colorExpr,
      'circle-stroke-color': token('--geojson-feature-point-stroke') || '#ffffff',
      'circle-stroke-width': strokeW,
      'circle-opacity': opacity,
      'circle-stroke-opacity': strokeW ? 0.9 : 0,
    },
  });
}

function addPolygonPaint(layer, sid, lid, lineLid, hitLid) {
  const p = layer.paint || {};
  const color = p.color || NAVY;
  if (p.fillOn) {
    map.addLayer({ id: lid, type: 'fill', source: sid,
      paint: { 'fill-color': color, 'fill-opacity': p.fillOpacity ?? 0.3 } });
  }
  // visible outline (thin navy by default)
  map.addLayer({ id: lineLid, type: 'line', source: sid,
    paint: { 'line-color': color, 'line-width': p.lineWidth ?? 2, 'line-opacity': 0.9 } });
  // transparent wide hit layer → easy hover/click without thickening the visible outline
  addHitLayer(hitLid, sid);
}

function addLinePaint(layer, sid, lid, hitLid) {
  const p = layer.paint || {};
  map.addLayer({ id: lid, type: 'line', source: sid,
    paint: { 'line-color': p.color || NAVY, 'line-width': p.lineWidth ?? 2, 'line-opacity': 0.9 } });
  addHitLayer(hitLid, sid);
}

function addHitLayer(hitLid, sid) {
  map.addLayer({ id: hitLid, type: 'line', source: sid, layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: { 'line-color': '#000', 'line-width': HIT_WIDTH, 'line-opacity': 0 } });
}

// ── Interactions ──────────────────────────────────────────────────────────
function bindPointInteractions(layer, lid) {
  if (_boundPoint.has(layer.id)) return;
  _boundPoint.add(layer.id);
  const mode = layer.colorMode;
  map.on('mouseenter', lid, (e) => {
    map.getCanvas().classList.add('is-pointer');
  });
  map.on('mouseleave', lid, () => { map.getCanvas().classList.remove('is-pointer'); removeHoverRing(); });
  map.on('click', lid, (e) => {
    const f = e.features && e.features[0]; if (!f) return;
    _selectedLayerId = layer.id;       // remember which layer the halo belongs to
    showSelectionHalo(f);
    if (_onPointClick) _onPointClick(f, emotionColors(), mode);
  });
}

/** Range hover/click bound to the transparent hit layer; hover widens the visible outline. */
function bindRangeInteractions(layer, hitLid, outlineLid) {
  if (_boundRange.has(layer.id)) return;
  _boundRange.add(layer.id);
  const baseW = (layer.paint && layer.paint.lineWidth) ?? 2;
  map.on('mouseenter', hitLid, (e) => {
    map.getCanvas().classList.add('is-pointer');
    try { map.setPaintProperty(outlineLid, 'line-width', baseW + 3); } catch (_) {}
    showRangeTooltip(e.lngLat, layer.name);
  });
  map.on('mousemove', hitLid, (e) => { if (_tooltip) _tooltip.setLngLat(e.lngLat); });
  map.on('mouseleave', hitLid, () => {
    map.getCanvas().classList.remove('is-pointer');
    try { map.setPaintProperty(outlineLid, 'line-width', baseW); } catch (_) {}
    hideRangeTooltip();
  });
  map.on('click', hitLid, (e) => {
    const f = e.features && e.features[0]; if (!f) return;
    showRangePopup(f, layer);
  });
}

function showRangeTooltip(lngLat, name) {
  if (!_tooltip) _tooltip = new maplibregl.Popup({ closeButton: false, closeOnClick: false, className: 'range-tooltip', offset: 12 });
  _tooltip.setHTML(`<div class="rt-name">${name || '范围'}</div>`).setLngLat(lngLat).addTo(map);
}
function hideRangeTooltip() { if (_tooltip) _tooltip.remove(); }

// ── Point halos ───────────────────────────────────────────────────────────
function showSelectionHalo(feature) {
  const SRC = 'emotion-selected', LAYER = 'emotion-selected-halo';
  if (map.getLayer(LAYER)) map.removeLayer(LAYER);
  if (map.getSource(SRC)) map.removeSource(SRC);
  const r = pointRadiusFor(feature);
  map.addSource(SRC, { type: 'geojson', data: { type: 'Feature', geometry: feature.geometry, properties: {} } });
  map.addLayer({
    id: LAYER, type: 'circle', source: SRC,
    paint: {
      'circle-radius': r + 2,              // ring hugging just outside the point
      'circle-color': 'rgba(0,0,0,0)',     // no fill
      'circle-opacity': 0,
      'circle-stroke-color': '#E8E8E8',    // gray-white
      'circle-stroke-width': 3.5,          // thick
      'circle-stroke-opacity': 0.95,
    },
  });
}
function showHoverRing(feature) {
  const SRC = 'emotion-hover', LAYER = 'emotion-hover-ring';
  if (map.getLayer(LAYER)) map.removeLayer(LAYER);
  if (map.getSource(SRC)) map.removeSource(SRC);
  const ringColor = token('--geojson-feature-selection-halo-color') || '#007afc';
  const r = pointRadiusFor(feature);
  map.addSource(SRC, { type: 'geojson', data: { type: 'Feature', geometry: feature.geometry, properties: {} } });
  map.addLayer({ id: LAYER, type: 'circle', source: SRC,
    paint: { 'circle-radius': r * 1.6, 'circle-color': 'rgba(0,0,0,0)', 'circle-opacity': 0,
      'circle-stroke-color': ringColor, 'circle-stroke-width': 2, 'circle-stroke-opacity': 0.8 } });
}
function removeHoverRing() {
  const SRC = 'emotion-hover', LAYER = 'emotion-hover-ring';
  if (map.getLayer(LAYER)) map.removeLayer(LAYER);
  if (map.getSource(SRC)) map.removeSource(SRC);
}
function pointRadiusFor(feature) {
  const zoom = map ? map.getZoom() : 11;
  let count = 0;
  const s = feature && feature.source;
  if (s) { const id = s.replace('lyr-', ''); const l = getLayers().find((x) => x.id === id);
    if (l) count = l.fc.features.length; }
  if (!count) { for (const l of getLayers()) if (l.kind === 'point' && l.visible) count += l.fc.features.length; }
  return densityRadiusAt(count || 1, zoom);
}

// ── Helpers ───────────────────────────────────────────────────────────────
function visiblePointCount() {
  let n = 0;
  for (const l of getLayers()) if (l.kind === 'point' && l.visible) n += l.fc.features.length;
  return n || 1;
}
function mergedBBox() {
  let b = null;
  for (const layer of getLayers()) {
    if (!layer.visible) continue;
    for (const f of layer.fc.features) {
      const c = findFirstCoord(f.geometry);
      if (!c) continue;
      if (!b) b = [c[0], c[1], c[0], c[1]];
      else { if (c[0] < b[0]) b[0] = c[0]; if (c[1] < b[1]) b[1] = c[1]; if (c[0] > b[2]) b[2] = c[0]; if (c[1] > b[3]) b[3] = c[1]; }
    }
  }
  return b;
}
function findFirstCoord(geom) {
  if (!geom || !geom.coordinates) return null;
  const dive = (a) => Array.isArray(a[0]) ? dive(a[0]) : a;
  try { return dive(geom.coordinates); } catch (e) { return null; }
}

export function fitBoundsTo(bbox, padding = 100) {
  if (!map || !bbox) return;
  try { map.fitBounds([[bbox[0], bbox[1]], [bbox[2], bbox[3]]], { padding }); } catch (e) {}
}
