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
    // Emotion type assignment based on polarity + text
    const emoTypeByPolarity = {
      'Very Negative': ['愤怒', '不满抱怨', '失望厌恶'],
      'Negative': ['不满抱怨', '焦虑担忧', '失望厌恶'],
      'Neutral': ['期待建议', '怀旧认同'],
      'Positive': ['喜悦满意', '怀旧认同'],
      'Very Positive': ['喜悦满意'],
    };
    const candidates = emoTypeByPolarity[pol] || ['期待建议'];
    const emoType = candidates[Math.floor(rnd() * candidates.length)];
    const emoIntensity = pol === 'Very Negative' || pol === 'Very Positive'
      ? 0.7 + rnd() * 0.3 : pol === 'Negative' || pol === 'Positive'
      ? 0.4 + rnd() * 0.4 : rnd() * 0.4;

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
        emotion_type: emoType,
        emotion_intensity: Math.round(emoIntensity * 1000) / 1000,
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
// One entry per imported file. Drives the left-panel layer manager + map rendering.
//   kind: 'point' | 'line' | 'polygon' | 'group' | 'heatmap'
//         (group = L2 container, non-rendered; heatmap = native MapLibre density layer)
//   colorMode (point): 'l2-positive' | 'l2-neutral' | 'l2-negative' | 'confidence'(L1) | 'needsAnalysis'(L0)
//   colorMode (heatmap): 'heatmap-negative'
//   parentId: set on group children; group itself has children[]
//   paint: polygon/line {color,fillOn,lineWidth,fillOpacity}; point {ramp?,opacity?,radius?}
//          heatmap {
//            unit: 'm'|'px', radius (m or px), opacity, intensity,
//            rampKey, weightField, weightCurve,
//            typesFilter: string[] | null,    // L2 emotion_type 多选筛选
//            intensityMin: 0..1,              // emotion_intensity 下限
//            blurFactor, minzoom?, maxzoom?,
//          }

const NAVY = '#0c1c2e';   // title-bar navy (range outline default)
const _layers = new Map();   // id -> layer object
let _seq = 0;

// ── L2 palettes (polarity split: Positive green / Negative orange-red / Neutral moody blue) ──
export const L2_POSITIVE = { 'Very Positive': '#86E61C', 'Positive': '#3DBA9E' };   // 鲜艳荧光绿→蓝绿(teal)
export const L2_NEGATIVE = { 'Very Negative': '#A3321A', 'Negative': '#E07142' };    // 暗橘红→浅橘红
export const L2_NEUTRAL_COLOR = '#3A7CA5';                                            // 忧郁蓝（会合色）

// ── Heatmap color stops (Kepler-aligned: density-mapped ramp, NOT polarity) ──
// 消极热力图：稀疏消极区→冷蓝，密集消极区→深红。density 0 必须透明（低密度不显示）。
// 格式 = [densityStop, color][]，喂给 MapLibre heatmap-color 的 interpolate 表达式。
export const HEATMAP_NEGATIVE_STOPS = [
  [0.00, 'rgba(58,124,165,0)'],   // 透明（无密度）
  [0.10, '#3A7CA5'],              // 中性浅（消极点稀疏）
  [0.25, '#5288A0'],
  [0.40, '#6A9BB5'],              // 中性深
  [0.55, '#E07142'],              // 消极浅（L2 Negative 浅橘红）
  [0.70, '#C44A2E'],
  [0.85, '#A3321A'],              // 非常消极（L2 Very Negative 暗橘红）
  [1.00, '#7A1E16'],              // 高密度深红
];

// ── Heatmap color ramp presets (6 themes for emotion-map use cases) ──
// Each ramp = { name, stops: [[density,color], ...] }. density 0 always transparent.
export const HEATMAP_RAMPS = {
  negative: {
    name: '消极红',
    stops: HEATMAP_NEGATIVE_STOPS,
  },
  positive: {
    name: '积极绿',
    stops: [
      [0.00, 'rgba(30,120,80,0)'],
      [0.10, '#A8E6A0'],
      [0.25, '#6BCF6B'],
      [0.40, '#3DBA3D'],
      [0.55, '#219A21'],
      [0.70, '#167A16'],
      [0.85, '#0E5C0E'],
      [1.00, '#083D08'],
    ],
  },
  neutral: {
    name: '中性蓝',
    stops: [
      [0.00, 'rgba(100,140,180,0)'],
      [0.10, '#B0C8E0'],
      [0.25, '#8AA8C8'],
      [0.40, '#6088B0'],
      [0.55, '#4A7098'],
      [0.70, '#385878'],
      [0.85, '#284060'],
      [1.00, '#1A2C48'],
    ],
  },
  anxiety: {
    name: '焦虑紫',
    stops: [
      [0.00, 'rgba(120,80,160,0)'],
      [0.10, '#C8B0E8'],
      [0.25, '#A890D0'],
      [0.40, '#8870B8'],
      [0.55, '#6A4E9E'],
      [0.70, '#4E3680'],
      [0.85, '#362260'],
      [1.00, '#241448'],
    ],
  },
  rainbow: {
    name: '综合彩虹',
    stops: [
      [0.00, 'rgba(0,0,255,0)'],
      [0.15, '#0000FF'],
      [0.30, '#00FF00'],
      [0.50, '#FFFF00'],
      [0.70, '#FF8800'],
      [0.85, '#FF4400'],
      [1.00, '#FF0000'],
    ],
  },
  mono: {
    name: '单色热力',
    stops: [
      [0.00, 'rgba(0,0,0,0)'],
      [0.15, 'rgba(60,60,60,0.25)'],
      [0.35, 'rgba(120,120,120,0.45)'],
      [0.55, 'rgba(180,180,180,0.65)'],
      [0.75, 'rgba(220,220,220,0.82)'],
      [1.00, 'rgba(255,255,255,0.95)'],
    ],
  },
  // 6 级色板（论文方法 + 用户需求）：3 级情绪 + 3 级中性过渡，density 0 透明
  'positive-6': {
    name: '积极6级',
    stops: [
      [0.00, 'rgba(30,120,80,0)'],
      [0.15, '#C8E6C9'],   // 中性浅
      [0.30, '#A5D6A7'],   // 中性
      [0.45, '#81C784'],   // 中性→积极过渡
      [0.62, '#4CAF50'],   // 积极浅
      [0.80, '#2E7D32'],   // 积极
      [1.00, '#1B5E20'],   // 非常积极（深绿）
    ],
  },
  'negative-6': {
    name: '消极6级',
    stops: [
      [0.00, 'rgba(120,80,160,0)'],
      [0.15, '#E0E0E0'],   // 中性浅
      [0.30, '#BCAAA4'],   // 中性
      [0.45, '#A1887F'],   // 中性→消极过渡
      [0.62, '#E07142'],   // 消极浅
      [0.80, '#C44A2E'],   // 消极
      [1.00, '#7A1E16'],   // 非常消极（深红）
    ],
  },
};

// sorted keys for UI iteration
export const HEATMAP_RAMP_KEYS = ['negative', 'positive', 'neutral', 'anxiety', 'rainbow', 'mono', 'positive-6', 'negative-6'];

// ── Emotion type palette — 论文双层体系（微观具体情绪，7 类，每类对齐治理动作）──
// 类型与 SCRIPT/emotion_lexicon.py EMOTION_LEXICON 保持一致。
// 治理动作映射供未来"点格网看建议"用。
export const EMOTION_TYPE_COLORS = {
  '不满抱怨': '#E07142',   // 设施/服务整改（脏乱/老旧/同质化）
  '焦虑担忧': '#9B59B6',   // 安全/出行治理（拥堵/停车/租房）
  '失望厌恶': '#7F8C8D',   // 环境整治（扰民/噪音/水臭）
  '愤怒': '#C0392B',       // 紧急响应（事故类极端负面）
  '期待建议': '#3498DB',   // 献策纳规（诉求类）
  '喜悦满意': '#2ECC71',   // 标杆保护（太阳/花朵/美食）
  '怀旧认同': '#F39C12',   // 文化传承（武侯祠/历史文化）
};
export const EMOTION_TYPE_ORDER = ['不满抱怨', '焦虑担忧', '失望厌恶', '愤怒', '期待建议', '喜悦满意', '怀旧认同'];
export const EMOTION_TYPE_ACTION = {
  '不满抱怨': '设施/服务整改',
  '焦虑担忧': '安全/出行治理',
  '失望厌恶': '环境整治',
  '愤怒': '紧急响应',
  '期待建议': '献策纳规',
  '喜悦满意': '标杆保护',
  '怀旧认同': '文化传承',
};

// ── Heatmap source tracking: sourceKey → heatmap layer id ──
// sourceKey = sanitized string identifying the data source (group id / child layer id).
// When generating a new heatmap for the same sourceKey, the old one is removed first.
const _heatmapSources = new Map();
export function getHeatmapForSource(sourceKey) { return _heatmapSources.get(sourceKey); }
export function setHeatmapForSource(sourceKey, layerId) { _heatmapSources.set(sourceKey, layerId); }
export function removeHeatmapSource(sourceKey) { _heatmapSources.delete(sourceKey); }
export function clearHeatmapSources() { _heatmapSources.clear(); }

export function addLayer({ name, kind, fc, needsAnalysis = false, colorMode, paint, parentId }) {
  const id = 'L' + (++_seq).toString().padStart(3, '0');
  const defaultPaint = kind === 'polygon'
    ? { color: NAVY, fillOn: false, lineWidth: 2, fillOpacity: 0.3 }
    : kind === 'line'
      ? { color: NAVY, lineWidth: 2 }
      : kind === 'heatmap'
        ? {
            unit: 'm',           // 'm' (geographic meters, default) | 'px' (screen pixels)
            radius: 300,         // 300 m default — 城市规划尺度核密度带宽
            opacity: 0.7,
            intensity: 1,
            rampKey: 'rainbow',  // 中立色带，不暗示极性
            weightField: 'emotion_intensity',  // 强度做权重（v2 L2 颗粒度）
            weightCurve: 'linear',
            typesFilter: null,   // null = 全部；数组 = 仅显示 emotion_type ∈ 数组的点
            intensityMin: 0,     // emotion_intensity ≥ 阈值 才进入热力图
            blurFactor: 1.0,     // 预留：blur = radius * blurFactor（MapLibre 内部固定，留接口）
          }
        : {};
  const layer = {
    id, name, kind, fc, visible: true, needsAnalysis, parentId: parentId || null,
    colorMode: colorMode || (needsAnalysis ? 'needsAnalysis' : 'polarity'),
    paint: { ...defaultPaint, ...(paint || {}) },
  };
  _layers.set(id, layer);
  if (parentId) {
    const parent = _layers.get(parentId);
    if (parent && parent.kind === 'group') parent.children.push(id);
  }
  return layer;
}

/** Create an L2 group container (non-rendered) holding the full L2 FC for Overview. */
export function addGroup({ name, fc }) {
  const id = 'G' + (++_seq).toString().padStart(3, '0');
  const group = { id, name, kind: 'group', fc, visible: true, children: [], parentId: null };
  _layers.set(id, group);
  return group;
}
export function getChildren(groupId) {
  const g = _layers.get(groupId);
  return g ? g.children.map((cid) => _layers.get(cid)).filter(Boolean) : [];
}
/** Full FC of a group (all children merged) — for Overview aggregate. */
export function groupFC(groupId) {
  const feats = [];
  for (const c of getChildren(groupId)) if (c.visible) feats.push(...(c.fc.features || []));
  return { type: 'FeatureCollection', features: feats };
}

/** Update a layer's paint field (used by the settings popover in batch 2; kept here for symmetry). */
export function setLayerPaint(id, patch) {
  const l = _layers.get(id);
  if (l) l.paint = { ...(l.paint || {}), ...patch };
  return l;
}

export function removeLayer(id) {
  const l = _layers.get(id);
  if (!l) return false;
  if (_selectedLayerId === id) _selectedLayerId = null;
  if (l.kind === 'group') {
    // cascade: remove all children
    for (const cid of [...(l.children || [])]) removeLayer(cid);
  }
  if (l.parentId) {
    const p = _layers.get(l.parentId);
    if (p && p.children) p.children = p.children.filter((c) => c !== id);
  }
  // Clean heatmap source tracking when source layer or heatmap is removed
  if (l.kind === 'heatmap') {
    for (const [key, lid] of _heatmapSources) {
      if (lid === id) { _heatmapSources.delete(key); break; }
    }
  }
  // If a point layer used as heatmap source is removed, clean its heatmap tracking
  if (l.kind === 'point') {
    for (const [key, lid] of _heatmapSources) {
      if (key === `child:${id}` || key === `layer:${id}`) {
        _heatmapSources.delete(key);
      }
    }
  }
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
 *   point needsAnalysis → 'L0' · confidence → 'L1' · l2-positive/neutral/negative → 'L2'
 *   polygon/line → 'range' · group → 'L2' (L2 group container). */
export function layerLevel(layer) {
  if (!layer) return null;
  if (layer.kind === 'group') return 'L2';
  if (layer.kind === 'heatmap') return 'L2';          // heatmap = L2 density visualization
  if (layer.kind === 'polygon' || layer.kind === 'line') return 'range';
  if (layer.colorMode === 'confidence') return 'L1';
  if (layer.colorMode === 'l2-positive' || layer.colorMode === 'l2-negative' || layer.colorMode === 'l2-neutral' || layer.colorMode === 'polarity') return 'L2';
  return 'L0';
}

/** Resolve a layer to its "focus layer" for Overview linkage: an L2 child → its parent group;
 *  group/standalone → itself. (Overview recognizes the big level, not sub-layers.) */
export function focusLayer(layer) {
  if (!layer) return null;
  if (layer.parentId) return _layers.get(layer.parentId) || layer;
  return layer;
}

/** Display color for hint chip / badges — synced with the layer's current paint. */
export function layerDisplayColor(layer) {
  if (!layer) return '#a3a3a3';
  if (layer.kind === 'polygon' || layer.kind === 'line') return (layer.paint && layer.paint.color) || NAVY;
  if (layer.kind === 'heatmap') return L2_NEGATIVE['Negative'];   // representative mid-negative (orange-red)
  const cm = layer.colorMode;
  if (cm === 'confidence') {
    const ramp = (layer.paint && layer.paint.ramp) || CONFIDENCE_RAMP;
    return rampColor(ramp, 0.6);   // mid-high confidence → representative hue
  }
  if (cm === 'l2-positive') return L2_POSITIVE['Positive'];      // 翠绿
  if (cm === 'l2-negative') return L2_NEGATIVE['Negative'];      // 浅橘红
  if (cm === 'l2-neutral') return L2_NEUTRAL_COLOR;              // 忧郁蓝
  return '#a3a3a3';   // L0 grey
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
  emotion_type: ['emotion_type', 'emotionType', '情绪类型', '情感类型', 'emotion'],
  emotion_intensity: ['emotion_intensity', 'emotionIntensity', '情绪强度', '情感强度', 'intensity'],
};
