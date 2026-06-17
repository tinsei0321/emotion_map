// ═══ map.js — MapLibre GL JS instance + basemap switch ═══
import { emotionColors, getTier, token } from './state.js';
import { initControls } from './map-controls.js';

// Basemap styles — 天地图 only (CartoDB blocked in CN). 4 variants:
//   影像 img (+ 影像注记 cia) · 常规矢量 vec (+ 矢量注记 cva), 各有 有/无注记 两版.
// Default = 影像无注记 (tianditu-img-nolabel). All tile-based WMTS raster (reuses embedded key).
export const BASEMAPS = {
  'tianditu-img-nolabel': '../apps/static/tianditu_img_nolabel.json',   // 影像（无注记）[默认]
  'tianditu-img':         '../apps/static/tianditu_img.json',           // 影像（含注记）
  'tianditu-vec-nolabel': '../apps/static/tianditu_nolabel.json',       // 常规（无注记）
  'tianditu-vec':         '../apps/static/tianditu_label.json',         // 常规（含注记）
};

export const DEFAULT_BASEMAP = 'tianditu-img-nolabel';

const YICHANG = { center: [111.286, 30.708], zoom: 12 };

let map = null;
let _emotionFC = null;        // current emotion FeatureCollection (re-applied on style change)
let _onPointClick = null;
let _heatmapOn = false;
let _interactionsBound = false;

export function initMap(container = 'map') {
  map = new maplibregl.Map({
    container,
    style: BASEMAPS[DEFAULT_BASEMAP],   // default: 天地图影像（无注记）
    center: YICHANG.center,
    zoom: YICHANG.zoom,
    attributionControl: true,
  });
  // Bottom-left unified cluster (reset / 2D-3D / +/- / north) + one-segment scale.
  // Replaces the native NavigationControl; zoom+/- and reset-north stay functionally
  // identical. Anchored to #map → rides along when the left panel folds. Needs the
  // current emotion FC for the reset→fitBounds, hence the lazy getter.
  initControls(map, { getFC: () => _emotionFC });
  // Emotion layers survive basemap switches via setBasemap's transformStyle (declarative carry-over,
  // no wipe → no re-add timing race). Click/hover handlers are bound once and key off the stable layer id.
  return map;
}

export function getMap() { return map; }

export function setBasemap(key) {
  if (!map || !BASEMAPS[key]) return;
  // transformStyle carries our emotion-* sources/layers into the new style so they aren't wiped
  // by setStyle (the reliable cross-version pattern; avoids style.load/styledata timing races).
  map.setStyle(BASEMAPS[key], {
    transformStyle: (previousStyle, nextStyle) => {
      const carrySources = {};
      for (const [id, spec] of Object.entries(previousStyle?.sources || {})) {
        if (id.startsWith('emotion-')) carrySources[id] = spec;
      }
      const carryLayers = (previousStyle?.layers || []).filter((l) => l.id.startsWith('emotion-'));
      return {
        ...nextStyle,
        sources: { ...(nextStyle.sources || {}), ...carrySources },
        layers: [...(nextStyle.layers || []), ...carryLayers],
      };
    },
  });
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

  // Hover cursor + click → selection halo + popup. Bound once (handlers survive re-adds
  // since the layer id is stable); avoids accumulating listeners across style switches.
  if (!_interactionsBound) {
    _interactionsBound = true;
    map.on('mouseenter', LAYER_POINTS, () => { map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', LAYER_POINTS, () => { map.getCanvas().style.cursor = ''; });
    map.on('click', LAYER_POINTS, (e) => {
      const f = e.features[0];
      if (!f) return;
      showSelectionHalo(f, emotionColors());
      if (_onPointClick) _onPointClick(f, emotionColors());
    });
  }
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
