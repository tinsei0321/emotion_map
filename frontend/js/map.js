// ═══ map.js — MapLibre GL JS instance, multi-layer registry, basemap switch ═══
import { emotionColors, token, POLARITY_ORDER, getLayers, CONFIDENCE_RAMP, confidenceColor, L2_POSITIVE, L2_NEGATIVE, L2_NEUTRAL_COLOR, HEATMAP_NEGATIVE_STOPS, HEATMAP_RAMPS, HOTNESS_RAMP, computeHotness, hotnessBuckets } from './state.js';
import { initControls } from './map-controls.js';

export const BASEMAPS = {
  // CARTO GL 矢量素图（kepler/MVP 同款，无注记，CDN 矢量瓦片，细节丰富+缩放清晰+快）
  'positron':    'https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json',
  'dark-matter': 'https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json',
  'voyager':     'https://basemaps.cartocdn.com/gl/voyager-nolabels-gl-style/style.json',
  // 天地图（可选，非默认；HTTP+影像/矢量大瓦片，较慢）
  'tianditu-img': '../apps/static/tianditu_img.json',
  'tianditu-vec': '../apps/static/tianditu_label.json',
};
export const DEFAULT_BASEMAP = 'positron';
const YICHANG = { center: [111.286, 30.708], zoom: 12 };
const NAVY = '#0c1c2e';
const HIT_WIDTH = 20;           // transparent hit-line width (easy hover/open on thin outlines; visible line stays 2px)

/** Density-adaptive point radius (user spec, L0-L4 uniform): by point count → tier,
 *  and within a tier the radius breathes with zoom (zoom in = bigger).
 *  Cap: 默认最大 ≤10px（密度大可更小，但稀疏档顶 10px——不再 14–18）。
 *    < 500           → 6–10px (sparse, capped at 10)
 *    500 ≤ n < 2000  → 4–7px
 *    ≥ 2000          → 2–4px
 *  Returns [rAtZoom8, rAtZoom14]. */
function densityStops(count) {
  if (count < 500) return [6, 10];
  if (count < 2000) return [4, 7];
  return [2, 4];
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
const lyrExtruLid = (id) => `lyr-${id}-extru`;   // grid 3D fill-extrusion sub-layer

/** (Re)render one registry layer. Hidden layers are fully removed (fill + outline + hit). */
export function renderLayer(layer) {
  if (!map) return;
  if (layer.kind === 'group') return;   // group container is not rendered on the map
  const sid = lyrSrc(layer.id);
  const lid = lyrLid(layer.id);
  const lineLid = lyrLineLid(layer.id);
  const hitLid = lyrHitLid(layer.id);
  const extruLid = lyrExtruLid(layer.id);
  for (const l of [hitLid, extruLid, lineLid, lid]) if (map.getLayer(l)) map.removeLayer(l);
  if (map.getSource(sid)) map.removeSource(sid);
  if (!layer.visible || !layer.fc.features.length) {
    if (layer._deckOverlay) layer._deckOverlay.setProps({ layers: [] });   // 隐藏 hotpoint（deck.gl）
    // hiding a point layer → its selection halo must go too
    if (!layer.visible && layer.kind === 'point') clearSelectionHalo(layer.id);
    return;
  }

  // 预处理：L1 confidence 层在 addSource 前把 hotness 写入 properties ——
  // MapLibre source 持有 addSource 时的快照，enrich 在 addSource 之后则 step 表达式
  // ['get','hotness'] 读到 undefined，Chrome 下图层不渲染（regression 根因）。
  if (layer.kind === 'point' && layer.colorMode === 'confidence') {
    const feats = layer.fc.features;
    for (const f of feats) {
      if (!f.properties) f.properties = {};
      if (f.properties.hotness == null) f.properties.hotness = computeHotness(f);
    }
    layer.paint = layer.paint || {};
    layer.paint.hotnessBuckets = hotnessBuckets(feats);
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
  } else if (layer.kind === 'heatmap') {
    addHeatmapPaint(layer, sid, lid);   // density overlay — no hit layer, no click
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
    const ids = [lyrLid(l.id), lyrLineLid(l.id)];
    if (map.getLayer(lyrExtruLid(l.id))) ids.push(lyrExtruLid(l.id));   // grid 3D 在 line 上、hit 下
    ids.push(lyrHitLid(l.id));
    for (const id of ids) {
      if (map.getLayer(id)) map.moveLayer(id);   // move to top (no beforeId)
    }
  }
}

export function removeLayerFromMap(id) {
  if (!map) return;
  const _layer = getLayers().find((l) => l.id === id);
  if (_layer && _layer._deckOverlay) { map.removeControl(_layer._deckOverlay); _layer._deckOverlay = null; }
  const sid = lyrSrc(id), lid = lyrLid(id), lineLid = lyrLineLid(id), extruLid = lyrExtruLid(id), hitLid = lyrHitLid(id);
  for (const l of [hitLid, extruLid, lineLid, lid]) if (map.getLayer(l)) map.removeLayer(l);
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
  // px override (settings slider) else L2 情绪点 3-6px zoom 自适应 / 其他 density-adaptive
  const _isL2 = layer.colorMode === 'l2-positive' || layer.colorMode === 'l2-negative' || layer.colorMode === 'l2-neutral';
  const _l2Radius = ['interpolate', ['linear'], ['zoom'], 8, 3, 14, 6];
  const radius = (p.radius != null) ? p.radius : (_isL2 ? _l2Radius : densityRadiusExpr(count));
  let colorExpr, strokeW, opacity;
  if (layer.colorMode === 'confidence') {
    // L1 热度值 = 情绪强度 × 置信度，3 段动态分位。hotness/buckets 已在 renderLayer
    // addSource 前预处理（写入 properties + paint.hotnessBuckets），此处直接落色。
    const buckets = p.hotnessBuckets || [0.33, 0.66];
    colorExpr = ['step', ['get', 'hotness'], HOTNESS_RAMP[0],
      buckets[0], HOTNESS_RAMP[1], buckets[1], HOTNESS_RAMP[2]];
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
    colorExpr = p.color || '#4a4a4a';   // L0 默认深灰；paint.color（预设色板）可覆盖
    strokeW = 0; opacity = p.opacity ?? 0.80;
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

/** Grid 极性色带 → MapLibre fill-color 表达式。
 *  p.gridField='_grid_norm'|'_grid_pos'|'_grid_neg'；p.gridStops=[[0,c0],...,[1,cN]]（归一化 0~1，无透明）。
 *  返回 interpolate(linear, get(field), ...)；无有效 stops → null（落回单色）。 */
function _gridColorExpr(p) {
  if (!p.gridField || !Array.isArray(p.gridStops) || !p.gridStops.length) return null;
  const stops = [];
  for (const [d, c] of p.gridStops) stops.push(d, c);
  return ['interpolate', ['linear'], ['get', p.gridField], ...stops];
}

function addPolygonPaint(layer, sid, lid, lineLid, hitLid) {
  const p = layer.paint || {};
  const isGrid = !!(p._ui && p._ui.tool === 'grid');
  const isGrid3d = isGrid && p._ui.mode === '3d';
  const color = p.color || NAVY;
  const fillExpr = isGrid ? _gridColorExpr(p) : null;

  if (p.fillOn) {
    map.addLayer({ id: lid, type: 'fill', source: sid,
      paint: { 'fill-color': fillExpr || color, 'fill-opacity': p.fillOpacity ?? (isGrid ? 1 : 0.3) } });   // grid 2D 默认不透明
  }

  // grid 3D：fill-extrusion（实心 opacity 1 + 高度分位 _grid_h × scale 张力 + 颜色同 2D 极性色带）
  if (isGrid3d) {
    const s = p.extrusionScale ?? 1;
    map.addLayer({
      id: lyrExtruLid(layer.id), type: 'fill-extrusion', source: sid,
      paint: {
        'fill-extrusion-color': fillExpr || color,
        'fill-extrusion-height': ['interpolate', ['linear'], ['get', '_grid_h'], 0, 0, 1, 1500 * s],
        'fill-extrusion-base': 0,
        'fill-extrusion-opacity': p._ui.extrusionOpacity ?? 1,   // 3D 透明度可调（默认 1 实心；_ui.extrusionOpacity）
      },
    });
  }

  // visible outline；grid 3D 去底部线框（只 2D 加浅灰细线，区分 buffer 实线 / Range 点划线）
  if (!isGrid3d) {
    const lineColor = isGrid ? '#666' : color;
    const linePaint = { 'line-color': lineColor, 'line-width': p.lineWidth ?? (isGrid ? 0.5 : 2), 'line-opacity': isGrid ? 0.45 : 0.9 };
    const lineLayout = {};
    if (p.lineStyle === 'dashed') {
      linePaint['line-dasharray'] = [2, 1.5];                    // 缓冲面域：短虚线
    } else if (p.lineStyle === 'dashdot') {
      linePaint['line-dasharray'] = [6, 3, 1, 3];                // Range：点划线（线段+点+线段）
      lineLayout['line-cap'] = 'round';                          // round cap 让 1-unit 短段呈圆点（line-cap 属 layout）
    }
    map.addLayer({ id: lineLid, type: 'line', source: sid, layout: lineLayout, paint: linePaint });
  }
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

/** Heatmap (Kepler-aligned): native MapLibre `type:'heatmap'` = Gaussian KDE (same algo as
 *  deck.gl HeatmapLayer under Kepler). Color maps DENSITY (not polarity); polarity enters via
 *  weight. Full parameter set: Color/Opacity/Radius/Weight/Intensity/Curve/ZoomRange/Unit.
 *
 *  Radius 单位语义（v2）：
 *  - 'm'（默认，GIS 核密度语义）: radius=真实米数，按 zoom 换算成 px，缩放时地理覆盖稳定。
 *    公式 px(z)=meters/mpp(z,lat)，mpp(z,lat)≈156543.03*cos(lat)/2^z。
 *  - 'px'（高级）: 固定屏幕像素，缩放时屏幕半径不变但地理面积随 zoom 漂移。
 *  L2 类型/强度筛选（typesFilter/intensityMin）在 heatmap-tool.js 生成时已过滤 fc，
 *  这里只负责渲染。 */
function addHeatmapPaint(layer, sid, lid) {
  const p = layer.paint || {};
  const unit = p.unit || 'm';                       // 'm' default, 'px' advanced
  const radius = p.radius ?? (unit === 'm' ? 300 : 45);
  const opacity = p.opacity ?? 0.7;
  const intensity = p.intensity ?? 1;
  const weightField = p.weightField || 'emotion_intensity';
  const weightCurve = p.weightCurve || 'linear';
  const rampKey = p.rampKey || 'rainbow';
  const ramp = p.rampStops || (HEATMAP_RAMPS[rampKey] && HEATMAP_RAMPS[rampKey].stops) || HEATMAP_NEGATIVE_STOPS;
  const colorStops = ramp.flat();
  const weightExpr = buildWeightExpression(weightField, weightCurve);

  const paint = {
    'heatmap-radius': radius,
    'heatmap-opacity': opacity,
    'heatmap-intensity': intensity,
    'heatmap-weight': weightExpr,
    'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'], ...colorStops],
  };

  if (unit === 'm') {
    // 地理米 → 各 zoom 下应渲染的 px。宜昌纬度 30.7°N 常量。
    const latRad = 30.7 * Math.PI / 180;
    const cosLat = Math.cos(latRad);
    const mpp = (z) => 156543.03 * cosLat / Math.pow(2, z);
    const pxAt = (z) => radius / mpp(z);
    paint['heatmap-radius'] = ['interpolate', ['linear'], ['zoom'],
      8, pxAt(8),
      10, pxAt(10),
      12, pxAt(12),
      14, pxAt(14),
      16, pxAt(16),
      18, pxAt(18),
      20, pxAt(20),
    ];
  } else if (p.geoRadius) {
    // 向后兼容：旧 px + geoRadius 标志（已弃用，保留以防旧图层）
    paint['heatmap-radius'] = ['interpolate', ['linear'], ['zoom'],
      0, Math.max(2, radius * 0.02),
      8, Math.max(4, radius * 0.3),
      12, Math.max(8, radius * 0.6),
      16, radius,
      20, radius * 1.5,
    ];
  }

  const opts = { id: lid, type: 'heatmap', source: sid, paint };
  if (p.minzoom != null) opts.minzoom = p.minzoom;
  if (p.maxzoom != null && p.maxzoom < 22) opts.maxzoom = p.maxzoom;

  map.addLayer(opts);
}

/* global deck */  // deck.gl standalone UMD（index.html CDN 引入）
/** 热点图（deck.gl）：ScreenGridLayer 屏幕方格聚合 + MapboxOverlay 叠 MapLibre。
 *  bloom 先靠 CSS filter（map canvas）近似；效果不足再引 @luma.gl/postprocessing。 */
function addHotpointLayer(layer, sid, lid) {
  if (typeof deck === 'undefined' || !deck.ScreenGridLayer || !deck.MapboxOverlay) {
    console.error('[Hotpoint] deck.gl 未加载（ScreenGridLayer/MapboxOverlay 缺失），检查 index.html CDN');
    return;
  }
  const p = layer.paint || {};
  const weightField = p.weightField || 'emotion_intensity';
  const rampKey = p.rampKey || 'rainbow';
  const ramp = p.rampStops || (HEATMAP_RAMPS[rampKey] && HEATMAP_RAMPS[rampKey].stops) || HEATMAP_NEGATIVE_STOPS;
  const opacity = p.opacity ?? 0.8;
  const cellSize = Math.max(4, Math.min(40, Math.round((p.radius ?? 100) / 6)));  // radius(m)→cellSize(px) 近似
  // ramp stops 是 [t, '#hex'|'rgba(...)'] 格式 → deck colorRange 需 [[r,g,b],...]（6 色）
  const _toRgb = (c) => {
    if (Array.isArray(c)) return c;
    if (typeof c !== 'string') return [255, 255, 255];
    const m = c.match(/rgba?\(([^)]+)\)/i);
    if (m) { const p = m[1].split(',').map(Number); return [p[0] || 0, p[1] || 0, p[2] || 0]; }
    let h = c.replace('#', '');
    if (h.length === 3) h = h.split('').map((x) => x + x).join('');
    const n = parseInt(h, 16);
    return isNaN(n) ? [255, 255, 255] : [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  };
  const _cols = ramp.map((x) => _toRgb(x[1]));
  const colorRange = [];
  for (let i = 0; i < 6; i++) colorRange.push(_cols[i] || _cols[_cols.length - 1] || [255, 255, 255]);
  const sgl = new deck.ScreenGridLayer({
    id: lid,
    data: layer.fc.features,
    getPosition: (f) => f.geometry.coordinates,
    getWeight: (f) => Number((f.properties || {})[weightField] ?? 0.5),
    cellSize, colorRange, opacity,
    pickable: false,
  });
  if (layer._deckOverlay) {
    layer._deckOverlay.setProps({ layers: [sgl] });
  } else {
    layer._deckOverlay = new deck.MapboxOverlay({ layers: [sgl] });
    map.addControl(layer._deckOverlay);
  }
}

/* global deck */
/** 标准网格（square）：deck.gl 渲染（业界成熟，kepler 同款光影/聚合/分位色）。
 *  2D：GridLayer extruded:false（吃原始点自动聚合色块）。
 *  3D：后端预聚合方格 + ColumnLayer（格中心+高度分位+极色+material 光影）。
 *  GridLayer extruded（方柱 GridCellLayer）在此环境 deck.gl@9.1.0 不渲染，故 3D 改用 ColumnLayer（圆柱，已验证渲染）。 */
// ── deck.gl grid 渲染已弃用（回 MapLibre fill-extrusion：addPolygonPaint grid 分支）──
// grid 工具 square/zonal 都走 addPolygonPaint（fill + fill-extrusion + _gridColorExpr 极性色带）。
// 放弃原因：deck.gl GridLayer extruded（方柱）在 MapLibre+MapboxOverlay 不渲染；ColumnLayer 效果不及 kepler 理想 → 用户决定回自创 fill-extrusion（去透明度+去线框）。
// addHotpointLayer（热点图）仍用 deck.gl ScreenGridLayer（搁置，独立功能）。

/** Build a heatmap-weight expression from field + curve mode.
 *  Modes: linear|exponential × normal|inverse. "inverse" = lower value → higher weight. */
function buildWeightExpression(field, curve) {
  if (field === 'uniform') return 1;
  const get = ['coalesce', ['to-number', ['get', field]], 0.3];
  const inverse = curve.endsWith('-inverse');
  const mode = inverse ? curve.replace('-inverse', '') : curve;

  if (mode === 'exponential') {
    // exponential via pre-computed stops: weight = e^(3*val) mapped over 5 stops
    const stops = inverse
      ? [0, 1, 0.25, 0.7, 0.5, 0.3, 0.75, 0.08, 1, 0.01]
      : [0, 0.01, 0.25, 0.08, 0.5, 0.3, 0.75, 0.7, 1, 1];
    return ['interpolate', ['linear'], get, ...stops];
  }
  // linear: direct mapping or inverse
  if (inverse) {
    return ['interpolate', ['linear'], get,
      0, 1, 0.25, 0.8, 0.5, 0.5, 0.75, 0.2, 1, 0];
  }
  return ['interpolate', ['linear'], get,
    0, 0, 0.25, 0.2, 0.5, 0.5, 0.75, 0.8, 1, 1];
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

/** Range hover bound to the transparent hit layer; hover widens the visible outline + tooltip.
 *  Click-to-open moved to popup.js central handler (classifyMapClick) so open/collapse share
 *  one decision (no open-then-collapse race); hover behaviour preserved unchanged. */
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
  const ringColor = token('--geojson-feature-selection-halo-color') || '#4285F4';
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
