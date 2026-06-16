// ═══ map.js — MapLibre GL JS instance + basemap switch ═══
import { emotionColors, getTier, token } from './state.js';

// Basemap styles. CartoDB GL styles via CDN; 天地图 via local MapLibre style JSON (apps/static).
export const BASEMAPS = {
  'carto-light':   'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
  'carto-dark':    'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  'carto-voyager': 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
  'tianditu-label': '../apps/static/tianditu_label.json',
};

const YICHANG = { center: [111.286, 30.708], zoom: 12 };

let map = null;
let _emotionFC = null;        // current emotion FeatureCollection (re-applied on style change)
let _onPointClick = null;
let _heatmapOn = false;

export function initMap(container = 'map') {
  map = new maplibregl.Map({
    container,
    style: BASEMAPS['tianditu-label'],   // default: 天地图 (CN-accessible; CartoDB blocked in CN)
    center: YICHANG.center,
    zoom: YICHANG.zoom,
    attributionControl: true,
  });
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), 'bottom-left');

  // After any setStyle, re-apply emotion layers (setStyle wipes sources/layers).
  map.on('style.load', () => {
    if (_emotionFC) applyEmotionLayers();
  });
  return map;
}

export function getMap() { return map; }

export function setBasemap(key) {
  if (!map || !BASEMAPS[key]) return;
  // Re-apply emotion layers after the new style loads (setStyle wipes sources/layers).
  map.once('style.load', () => { if (_emotionFC) applyEmotionLayers(); });
  map.setStyle(BASEMAPS[key]);
}

/** Add emotion points + selection halo. Keeps data for re-apply after style change. */
export function addEmotionPoints(fc, onPointClick) {
  _emotionFC = fc;
  _onPointClick = onPointClick;
  applyEmotionLayers();
}

export function setHeatmap(on) {
  _heatmapOn = on;
  if (!map || !_emotionFC) return;
  applyEmotionLayers();
}

function applyEmotionLayers() {
  const colors = emotionColors();
  const tier = getTier(_emotionFC.features.length);

  const SRC = 'emotion-points';
  const LAYER_POINTS = 'emotion-points-circle';

  // (re)add source — guard by actual existence
  if (map.getLayer(LAYER_POINTS)) map.removeLayer(LAYER_POINTS);
  if (map.getSource(SRC)) map.removeSource(SRC);

  map.addSource(SRC, { type: 'geojson', data: _emotionFC });

  if (_heatmapOn) {
    map.addLayer({
      id: LAYER_POINTS, type: 'heatmap', source: SRC,
      paint: {
        'heatmap-weight': ['interpolate', ['linear'], ['get', 'score'], 0, 0, 1, 1],
        'heatmap-radius': 18,
        'heatmap-opacity': 0.7,
        'heatmap-color': [
          'interpolate', ['linear'], ['heatmap-density'],
          0, 'rgba(0,0,0,0)',
          0.3, colors['Neutral'],
          0.6, colors['Negative'],
          1, colors['Very Negative'],
        ],
      },
    });
    return;
  }

  // Circle layer — 5-color by polarity (data-driven match), white halo stroke.
  const colorExpr = ['match', ['get', 'polarity'],
    'Very Positive', colors['Very Positive'],
    'Positive',      colors['Positive'],
    'Neutral',       colors['Neutral'],
    'Negative',      colors['Negative'],
    'Very Negative', colors['Very Negative'],
    colors['Neutral']];

  map.addLayer({
    id: LAYER_POINTS, type: 'circle', source: SRC,
    paint: {
      'circle-radius': tier.radius,
      'circle-color': colorExpr,
      'circle-stroke-color': token('--geojson-feature-point-stroke') || '#ffffff',
      'circle-stroke-width': Number(token('--geojson-feature-point-stroke-width')) || 1,
      'circle-opacity': 0.9,
      'circle-stroke-opacity': 0.9,
    },
  });

  // Hover cursor + popup tooltip
  map.on('mouseenter', LAYER_POINTS, () => { map.getCanvas().style.cursor = 'pointer'; });
  map.on('mouseleave', LAYER_POINTS, () => { map.getCanvas().style.cursor = ''; });

  // Click → selection halo + callback (revives SHELVED F_014 detail)
  map.on('click', LAYER_POINTS, (e) => {
    const f = e.features[0];
    if (!f) return;
    showSelectionHalo(f, colors);
    if (_onPointClick) _onPointClick(f, colors);
  });
}

/** Selection halo — geojson.io blue ring behind the selected point. */
function showSelectionHalo(feature, colors) {
  const SRC = 'emotion-selected';
  const LAYER = 'emotion-selected-halo';
  if (map.getLayer(LAYER)) map.removeLayer(LAYER);
  if (map.getSource(SRC)) map.removeSource(SRC);

  const haloColor = token('--geojson-feature-selection-halo-color') || '#007afc';
  const haloOp = Number(token('--geojson-feature-selection-halo-opacity')) || 0.25;
  const haloScale = Number(token('--geojson-feature-selection-halo-scale')) || 1.8;
  const tier = getTier(_emotionFC.features.length);

  map.addSource(SRC, {
    type: 'geojson',
    data: { type: 'Feature', geometry: feature.geometry, properties: {} },
  });
  map.addLayer({
    id: LAYER, type: 'circle', source: SRC,
    paint: {
      'circle-radius': tier.radius * haloScale,
      'circle-color': haloColor,
      'circle-opacity': haloOp,
      'circle-stroke-color': haloColor,
      'circle-stroke-width': 1,
      'circle-stroke-opacity': 0.6,
    },
  });
}
