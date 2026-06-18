// ═══ state.js — app state, sample data, token-derived colors, tier logic ═══
// Emotion colors read from CSS vars (single source = tokens.json `geojson.emotion`).

export const POLARITY_ORDER = [
  'Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive',
];
export const POLARITY_LABEL = {
  'Very Positive': '非常积极', 'Positive': '积极', 'Neutral': '中性',
  'Negative': '消极', 'Very Negative': '非常消极',
};

/** Read a --geojson-* token value from the live :root (single source). */
export function token(name) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name).trim();
}

/** Five emotion colors, keyed by polarity, straight from tokens. */
export function emotionColors() {
  return {
    'Very Positive': token('--geojson-color-emotion-very-positive') || '#78DC32',
    'Positive':      token('--geojson-color-emotion-positive')      || '#5DADE2',
    'Neutral':       token('--geojson-color-emotion-neutral')       || '#C0C0C0',
    'Negative':      token('--geojson-color-emotion-negative')      || '#C4956A',
    'Very Negative': token('--geojson-color-emotion-very-negative') || '#B92D2D',
  };
}

/** L1 confidence orange ramp (Kepler-style): light→dark = low→high confidence.
 *  Used by point coloring (map.js interpolate) + popup badge (confidenceColor). */
export const CONFIDENCE_RAMP = ['#FFD9A0', '#FFB347', '#FF9800', '#FB8C00', '#E65100'];
const CONFIDENCE_STOPS = [0, 0.25, 0.5, 0.75, 1];

/** Map a 0..1 score to a color on a 5-stop ramp (hex). Unknown → mid. */
export function rampColor(ramp, score) {
  const s = (typeof score === 'number' && !Number.isNaN(score)) ? Math.max(0, Math.min(1, score)) : 0.5;
  for (let i = 1; i < CONFIDENCE_STOPS.length; i++) {
    if (s <= CONFIDENCE_STOPS[i]) {
      const a = CONFIDENCE_STOPS[i - 1], b = CONFIDENCE_STOPS[i];
      const t = b === a ? 0 : (s - a) / (b - a);
      return lerpHex(ramp[i - 1], ramp[i], t);
    }
  }
  return ramp[ramp.length - 1];
}
/** Map a 0..1 confidence score to the default orange ramp color. */
export function confidenceColor(score) { return rampColor(CONFIDENCE_RAMP, score); }
function lerpHex(h1, h2, t) {
  const a = hexToRgb(h1), b = hexToRgb(h2);
  const r = Math.round(a[0] + (b[0] - a[0]) * t);
  const g = Math.round(a[1] + (b[1] - a[1]) * t);
  const bl = Math.round(a[2] + (b[2] - a[2]) * t);
  return `#${[r, g, bl].map((x) => x.toString(16).padStart(2, '0')).join('')}`;
}
function hexToRgb(h) {
  const s = h.replace('#', '');
  return [parseInt(s.slice(0, 2), 16), parseInt(s.slice(2, 4), 16), parseInt(s.slice(4, 6), 16)];
}

/**
 * Tiered rendering — port of core/config.py RENDER_TIERS (pixel-based for MapLibre).
 * Returns radius + label. Sampling (>100k) / heatmap downgrade handled by caller.
 */
export function getTier(n) {
  if (n <= 2000)   return { radius: 6, label: 'S·标准', sampled: 0 };
  if (n <= 10000)  return { radius: 4, label: 'M·密集', sampled: 0 };
  if (n <= 50000)  return { radius: 3, label: 'L·紧凑', sampled: 0 };
  return { radius: 2, label: 'XL·抽样', sampled: Math.max(0, n - 50000) };
}

// ── Sample emotion data (宜昌 30.708, 111.286) for Phase 1 shell demo ──
const SAMPLE_TEXTS = {
  'Very Positive': ['滨江公园的绿化太棒了，散步很舒服', '这条新修的绿道体验极佳', '社区活动办得真好'],
  'Positive': ['公交线路挺方便的', '菜市场品种齐全', '夜景灯光不错'],
  'Neutral': ['今天去了趟超市', '路过这段路', '小区门口在卖水果'],
  'Negative': ['这条路又在修，出行不便', '广场舞声音太大', '共享单车乱停没人管'],
  'Very Negative': ['下水道堵了好几天没人修', '深夜施工噪音严重扰民', '路灯坏了两个月没修'],
};
const SAMPLE_LOCATIONS = ['胜利四路', '西陵一路', '滨江公园', '解放路', '东山大道', 'CBD', '夜明珠', '葛洲坝'];

/** Deterministic pseudo-random (seed) for stable sample across reloads. */
function seeded(seed) {
  let s = seed;
  return () => { s = (s * 9301 + 49297) % 233280; return s / 233280; };
}

/** Generate N sample emotion points around Yichang as GeoJSON FeatureCollection. */
export function samplePoints(n = 60, seed = 42) {
  const rnd = seeded(seed);
  const cx = 111.286, cy = 30.708;
  const features = [];
  for (let i = 0; i < n; i++) {
    const pol = POLARITY_ORDER[Math.floor(rnd() * 5)];
    const texts = SAMPLE_TEXTS[pol];
    const lon = cx + (rnd() - 0.5) * 0.06;
    const lat = cy + (rnd() - 0.5) * 0.05;
    features.push({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [lon, lat] },
      properties: {
        id_e: 'e' + String(i + 1).padStart(4, '0'),
        polarity: pol,
        score: pol === 'Very Positive' ? 0.9 : pol === 'Positive' ? 0.7 :
               pol === 'Neutral' ? 0.5 : pol === 'Negative' ? 0.3 : 0.1,
        text: texts[Math.floor(rnd() * texts.length)],
        location: SAMPLE_LOCATIONS[Math.floor(rnd() * SAMPLE_LOCATIONS.length)],
        category: ['设施', '环境', '服务', '文化', '事件'][Math.floor(rnd() * 5)],
        keywords: ['关键词A', '关键词B'].slice(0, 1 + Math.floor(rnd() * 2)),
      },
    });
  }
  return { type: 'FeatureCollection', features };
}

/** Compute polarity stats from a FeatureCollection. */
export function polarityStats(fc) {
  const stats = { 'Very Positive': 0, 'Positive': 0, 'Neutral': 0, 'Negative': 0, 'Very Negative': 0 };
  let scoreSum = 0;
  for (const f of fc.features) {
    stats[f.properties.polarity] = (stats[f.properties.polarity] || 0) + 1;
    scoreSum += f.properties.score || 0.5;
  }
  return { stats, total: fc.features.length, scoreMean: fc.features.length ? scoreSum / fc.features.length : 0 };
}

/** Confidence distribution for L1 layers: 5 equal buckets over 0..1 + mean.
 *  Buckets align with the orange ramp stops so the histogram colors match the points. */
export function confidenceStats(fc) {
  const buckets = [0, 0, 0, 0, 0];
  let sum = 0, n = 0;
  for (const f of fc.features) {
    const s = Number(f.properties && f.properties.score);
    if (Number.isFinite(s)) {
      const i = Math.min(4, Math.max(0, Math.floor(s * 5 - 0.0001)));
      buckets[i]++; sum += s; n++;
    }
  }
  return { buckets, total: n, mean: n ? sum / n : 0 };
}

// ── Layer registry ────────────────────────────────────────────────────────
// One entry per imported file (or the seed sample). Drives the left-panel
// layer manager (eye toggle / trash delete) and multi-layer map rendering.
//   kind: 'point' | 'line' | 'polygon'
//   colorMode (point): 'polarity' (L2 5-color) | 'confidence' (L1 orange ramp) | 'needsAnalysis' (grey)
//   paint (polygon/line): { color, fillOn, lineWidth, fillOpacity }

const NAVY = '#0c1c2e';   // title-bar navy (range outline default)
const _layers = new Map();   // id -> layer object
let _seq = 0;

export function addLayer({ name, kind, fc, needsAnalysis = false, colorMode, paint }) {
  const id = 'L' + (++_seq).toString().padStart(3, '0');
  const defaultPaint = kind === 'polygon'
    ? { color: NAVY, fillOn: false, lineWidth: 2, fillOpacity: 0.3 }
    : kind === 'line'
      ? { color: NAVY, lineWidth: 2 }
      : {};
  const layer = {
    id, name, kind, fc, visible: true, needsAnalysis,
    colorMode: colorMode || (needsAnalysis ? 'needsAnalysis' : 'polarity'),
    paint: { ...defaultPaint, ...(paint || {}) },
  };
  _layers.set(id, layer);
  return layer;
}

/** Update a layer's paint field (used by the settings popover in batch 2; kept here for symmetry). */
export function setLayerPaint(id, patch) {
  const l = _layers.get(id);
  if (l) l.paint = { ...(l.paint || {}), ...patch };
  return l;
}

export function removeLayer(id) {
  if (_selectedLayerId === id) _selectedLayerId = null;
  return _layers.delete(id);
}
export function getLayer(id) { return _layers.get(id); }
export function getLayers() { return Array.from(_layers.values()); }
export function setLayerVisible(id, visible) {
  const l = _layers.get(id);
  if (l) l.visible = visible;
  return l;
}

/** Data level for display (tags / Overview / popup branches):
 *   point needsAnalysis → 'L0' (raw, 需治理) · confidence → 'L1' (可分析) · polarity → 'L2'
 *   polygon/line → 'range'. */
export function layerLevel(layer) {
  if (!layer) return null;
  if (layer.kind === 'polygon' || layer.kind === 'line') return 'range';
  if (layer.colorMode === 'confidence') return 'L1';
  if (layer.colorMode === 'polarity') return 'L2';
  return 'L0';   // needsAnalysis / unknown
}

// ── Selection ──────────────────────────────────────────────────────────────
let _selectedLayerId = null;
export function selectLayer(id) { _selectedLayerId = id; }
export function getSelectedLayer() { return _selectedLayerId ? _layers.get(_selectedLayerId) : null; }
export function getSelectedLayerId() { return _selectedLayerId; }
export function clearSelection() { _selectedLayerId = null; }

/** Reorder layers: move `fromId` to the position of `toId` (before it). toId=null
 *  appends to the end. List order (top→bottom) = map z-order (top→bottom). */
export function reorderLayers(fromId, toId) {
  if (!fromId || fromId === toId || !_layers.has(fromId)) return;
  if (toId != null && !_layers.has(toId)) return;
  const order = Array.from(_layers.keys());
  const from = order.indexOf(fromId);
  if (from < 0) return;
  order.splice(from, 1);
  if (toId == null) order.push(fromId);
  else { const to = order.indexOf(toId); order.splice(to, 0, fromId); }
  const next = new Map();
  for (const k of order) next.set(k, _layers.get(k));
  _layers.clear();
  for (const [k, v] of next) _layers.set(k, v);
}

/** All features from visible POINT layers — feeds Overview stats / Table. */
export function mergedPointFC() {
  const features = [];
  for (const l of _layers.values()) {
    if (l.kind === 'point' && l.visible) features.push(...l.fc.features);
  }
  return { type: 'FeatureCollection', features };
}

/** Generate a fresh unique point id (geojson.io-style merge: never clash). */
export function newPointId() {
  return 'e' + String(++_seq + 10000).padStart(5, '0');
}

/** Field-name synonyms → canonical polarity/score. Lets imported CSV/GeoJSON
 *  with variant column names (sentiment, l2_confidence, 情绪…) map cleanly. */
export const FIELD_SYNONYMS = {
  polarity: ['polarity', 'sentiment', 'label', 'emotion', '情绪', '极性'],
  score: ['score', 'l2_confidence', 'sentiment_score', 'confidence', '分数', '得分'],
  text: ['text', 'content', 'comment', 'review', '评论', '文本', '内容'],
  location: ['location', 'place', 'address', '地点', '位置'],
};
