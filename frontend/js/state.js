// ═══ state.js — app state, sample data, token-derived colors, tier logic ═══
// Emotion colors read from CSS vars (single source = tokens.json `geojson.emotion`).

export const POLARITY_ORDER = [
  'Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive',
];
export const POLARITY_LABEL = {
  'Very Positive': '非常积极', 'Positive': '积极', 'Neutral': '中性',
  'Negative': '消极', 'Very Negative': '非常消极',
};

/** 城市情绪关键词表（独立于 issue_label；网感 + 城市生活具象词）。key = `${domain}|${element}|${sign}`，sign ∈ pos/neu/neg。
 *  词非"评价性"（好/不好），而是市民具象用语（停车难/断头路/网红打卡点/夜经济/盼BRT…）；neu=期盼/讨论中。
 *  演示链"识别问题"环：关键词Top10 正/中/负 = 4×5 桶按正/中/负点数排名 → 本表映射（用户勾选词 + 桶语义匹配）。 */
export const KEYWORD_TABLE = {
  // planning 城市规划（路网/绿地/公服/地标/新区）—— 业内同行演示，专业词突出
  'urban_planning|facility|pos': '断头路打通',  'urban_planning|facility|neu': '盼BRT',        'urban_planning|facility|neg': '断头路',
  'urban_planning|environment|pos': '绿道成网', 'urban_planning|environment|neu': '规划绿地',  'urban_planning|environment|neg': '内涝积水',
  'urban_planning|service|pos': '新学校启用',   'urban_planning|service|neu': '学区划分',      'urban_planning|service|neg': '没配套',
  'urban_planning|culture|pos': '新地标',       'urban_planning|culture|neu': '规划落地',      'urban_planning|culture|neg': '没特色',
  'urban_planning|event|pos': '新中心开业',     'urban_planning|event|neu': '新区规划',        'urban_planning|event|neg': '烂尾',
  // renewal 城市更新（老旧小区/电梯/物业/老街/施工）—— 业内同行演示重点板块
  'urban_renewal|facility|pos': '加装电梯',     'urban_renewal|facility|neu': '盼电梯',        'urban_renewal|facility|neg': '没电梯',
  'urban_renewal|environment|pos': '老旧焕新',  'urban_renewal|environment|neu': '老街改造',  'urban_renewal|environment|neg': '墙皮脱落',
  'urban_renewal|service|pos': '物业靠谱',      'urban_renewal|service|neu': '物业',          'urban_renewal|service|neg': '物业差',
  'urban_renewal|culture|pos': '老街新生',      'urban_renewal|culture|neu': '历史街区',      'urban_renewal|culture|neg': '拆没了',
  'urban_renewal|event|pos': '微更新活化',      'urban_renewal|event|neu': '改造中',          'urban_renewal|event|neg': '施工扰民',
  // operation 城市运营（商圈/网红/夜经济/滨江）—— 用户指定高频市民网感词
  'urban_operation|facility|pos': '公交到门口', 'urban_operation|facility|neu': '公交线优化', 'urban_operation|facility|neg': '停车难',
  'urban_operation|environment|pos': '滨江步道', 'urban_operation|environment|neu': '口袋公园', 'urban_operation|environment|neg': '绿化失养',
  'urban_operation|service|pos': '网红',        'urban_operation|service|neu': '业态',        'urban_operation|service|neg': '底商空置冷清',
  'urban_operation|culture|pos': '15分钟生活区', 'urban_operation|culture|neu': '社区服务配套', 'urban_operation|culture|neg': '没意思',
  'urban_operation|event|pos': '夜经济',        'urban_operation|event|neu': '夜市筹备',      'urban_operation|event|neg': '噪音',
  // governance 城市治理（信号/环卫/政务/文化/拥堵）
  'urban_governance|facility|pos': '红绿灯优化了', 'urban_governance|facility|neu': '停车收费讨论', 'urban_governance|facility|neg': '红绿灯',
  'urban_governance|environment|pos': '街道干净整洁', 'urban_governance|environment|neu': '垃圾分类讨论', 'urban_governance|environment|neg': '垃圾乱扔',
  'urban_governance|service|pos': '政务秒批',   'urban_governance|service|neu': '办事指南',    'urban_governance|service|neg': '办事难',
  'urban_governance|culture|pos': '文化活动',   'urban_governance|culture|neu': '活动预告',    'urban_governance|culture|neg': '没去处',
  'urban_governance|event|pos': '拥堵缓解',     'urban_governance|event|neu': '早晚高峰',      'urban_governance|event|neg': '堵车',
};

/** Read a --geojson-* token value from the live :root (single source). */
export function token(name) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name).trim();
}

/** 从图层 features 派生时间标签 T（读首点 properties.time_label，缺则空）。
 *  命名/组卡/数据导航统一用它前缀 T1/T2/T3，打通时间轴显示侧。 */
export function deriveTimeTag(fc) {
  if (!fc || !fc.features || !fc.features.length) return '';
  const p = fc.features[0].properties || {};
  return p.time_label ? String(p.time_label) : '';
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

/** Map a 0..1 value to a color by interpolating REAL [pos, hex] stops — mirrors MapLibre
 *  `['interpolate',['linear'],['get',field],...stops]` exactly (sRGB, same as lerpHex).
 *  Use this (NOT rampColor) when the stops carry non-even positions (e.g. piToNorm
 *  breakpoints at 0/.4/.5/.6/1) — rampColor assumes even spacing and would mis-color.
 *  stops: [[pos, hex], ...] sorted ascending by pos. */
export function rampColorAt(stops, val) {
  if (!Array.isArray(stops) || !stops.length) return '#0c1c2e';
  const v = (typeof val === 'number' && !Number.isNaN(val)) ? Math.max(0, Math.min(1, val)) : 0.5;
  if (v <= stops[0][0]) return stops[0][1];
  for (let i = 1; i < stops.length; i++) {
    if (v <= stops[i][0]) {
      const p0 = stops[i - 1][0], c0 = stops[i - 1][1];
      const p1 = stops[i][0], c1 = stops[i][1];
      const t = (p1 === p0) ? 0 : (v - p0) / (p1 - p0);
      return lerpHex(c0, c1, t);
    }
  }
  return stops[stops.length - 1][1];
}

// ── L1 热度值（hotness）= 情绪强度 × 置信度，3 段动态分位色板 ──
// 置信度 = L1 治理阶段 LLM 判断的数据相关性置信度（l1_confidence，0~1，可收集可复现）。
// 热度值语义 = 该数据点作为"情绪热点"的可信强度（情绪浓且与城规相关）。
export const HOTNESS_RAMP = ['#FFD9A0', '#FF9800', '#E65100'];   // 浅橙 → 橙 → 深橙红（低→高）

/** 热度值 = emotion_intensity × l1_confidence（clamp 0~1）。
 *  intensity 兼容两种量表：0~1 比例（SnowNLP）或 1~5 等级（模拟数据）——>1 时按 5 级归一化。 */
export function computeHotness(f) {
  const p = (f && f.properties) || {};
  let inten = Number(p.emotion_intensity ?? 0);
  if (inten > 1) inten = inten / 5;        // 1~5 等级 → 0~1
  const conf = Number(p.l1_confidence ?? 0);
  const h = inten * conf;
  return Number.isFinite(h) ? Math.max(0, Math.min(1, h)) : 0;
}

/** 按图层 features 的 hotness 分布算 33%/66% 分位阈值 → [t1, t2]（动态 3 段区间）。
 *  退化（数据全相等/不足）兜底 [0.33,0.66]——避免 MapLibre step 阈值不严格递增在 Chrome 下 throw。 */
export function hotnessBuckets(features) {
  const hs = (features || []).map(computeHotness).filter((h) => h > 0).sort((a, b) => a - b);
  if (hs.length < 2) return [0.33, 0.66];
  const at = (q) => hs[Math.min(hs.length - 1, Math.floor(hs.length * q))];
  let t1 = at(0.33), t2 = at(0.66);
  if (!(t1 < t2)) { t1 = 0.33; t2 = 0.66; }   // 全相等/退化 → 兜底
  return [t1, t2];
}

/** 热度值 → 3 段色（分段，非插值）。 */
export function hotnessColor(buckets, hotness) {
  const [t1, t2] = buckets;
  if (hotness <= t1) return HOTNESS_RAMP[0];
  if (hotness <= t2) return HOTNESS_RAMP[1];
  return HOTNESS_RAMP[2];
}
/** Map a 0..1 confidence score to the default orange ramp color. */
export function confidenceColor(score) { return rampColor(CONFIDENCE_RAMP, score); }
export function lerpHex(h1, h2, t) {
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
/** 范围/边界层自动配色色板（按加载顺序循环；与 settings/buffer 取色器同源）。 */
export const PRESET_COLORS = [
  '#4a4a4a', '#0c1c2e', '#007afc', '#4FC3F7', '#22b14c',
  '#e04848', '#9b59b6', '#1abc9c', '#e67e22', '#c0392b',
];

/** Range 面/线层「色段条取色器」预设：每条 = 端点色数组，渲染为 linear-gradient bar，
 *  点击 bar 上某位置 → rampColorAt 归一化插值取该处色（连续取色，比离散色块更丰富）。
 *  语义色段（综合彩虹=饱和度优化降彩、综合极性=红→灰→绿发散、积极/消极/中性单色系）
 *  + 感知均匀/艺术高级色板（Viridis/Magma/Cividis/Turbo/Spectral + 日落暖金）。
 *  改色只改本表（与 PRESET_COLORS 同单源理念，settings.js import 复用）。 */
export const RANGE_GRADIENTS = [
  { id: 'rainbow',  name: '综合彩虹',     stops: ['#6488ea', '#00b3a4', '#3fb967', '#e8c547', '#e8923c', '#d8552f'] },
  { id: 'polarity', name: '综合极性',     stops: ['#a3321a', '#e07142', '#d8d8d8', '#86d28a', '#3dba3d', '#0d6b2e'] },
  { id: 'positive', name: '积极（绿）',   stops: ['#d4f4a0', '#a8e065', '#5cb85c', '#2e8b3d', '#16632b'] },
  { id: 'negative', name: '消极（红）',   stops: ['#f6c9b0', '#f29a92', '#e15f54', '#b53a30', '#7a1e16'] },
  { id: 'neutral',  name: '中性（蓝灰）', stops: ['#cfe0ee', '#9bb5c8', '#6889a0', '#3f6080', '#1f3f5c'] },
  { id: 'viridis',  name: 'Viridis',      stops: ['#440154', '#414487', '#2a788e', '#22a884', '#7ad151', '#fde725'] },
  { id: 'magma',    name: 'Magma',        stops: ['#000004', '#3b0f70', '#8c2981', '#de4968', '#fe9f6d', '#fcfdbf'] },
  { id: 'cividis',  name: 'Cividis',      stops: ['#00204d', '#3b528b', '#9fb478', '#e3e35d', '#fde738'] },
  { id: 'turbo',    name: 'Turbo',        stops: ['#30123b', '#2c83fc', '#35f2cd', '#f6f527', '#fd8b2a', '#a52a2a', '#7a0403'] },
  { id: 'spectral', name: 'Spectral',     stops: ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', '#abdda4', '#3288bd'] },
  { id: 'sunset',   name: '日落（暖金）', stops: ['#1a1a2e', '#5a2a4a', '#b5446a', '#e8893a', '#f5d77a', '#fff4c4'] },
];

const _layers = new Map();   // id -> layer object
let _seq = 0;

// ── Layer category grouping (render-layer aggregation; UI state only — never stored in _layers) ──
export const CATEGORY_LABEL = { heatmap: '热力图', l2: 'L2 · 情绪地图 DATA', l1: 'L1 · 城市情绪 DATA', l0: 'L0 · 原始', range: '范围边界', buffer: '缓冲分析', grid: '网格聚合', terrain: '情绪地形', ai: 'EmotionMap Copilot', other: '其他' };
// 默认图层组序（上→下 = 地图顶层→底层）：L 数据 → 核密度 → 空间聚合(grid/terrain) → Buffer → Range → 其他。
// 用户可拖拽 group 卡覆写（reorderGroupSegment 改本数组）；组内按 timeRank(T1<T2<T3) + typeRank(热度<综合<极性) 稳定排序。
// range 与 ai（AI 工作区）恒钉最末（range 在 ai 上）—— applyGroupOrder / renderLayerList 双重保底。
let _groupOrder = ['l0', 'l1', 'l2', 'heatmap', 'grid', 'terrain', 'buffer', 'other', 'range', 'ai'];
const _groupCollapse = new Set();                                    // collapsed category set
const _groupFold = new Set();                                        // folded real-group set（真 L2 组单独折叠，按 group id；区别于 category 级 _groupCollapse）
const _frozenCats = new Set();                                       // 用户手动 within-category 拖拽过的 category → applyGroupOrder 跳过其组内排序（保手动序）；新层加入时解冻让其归位

// ── L2 palettes (polarity split: Positive green / Negative orange-red / Neutral moody blue) ──
export const L2_POSITIVE = { 'Very Positive': '#78DC32', 'Positive': '#5DADE2' };   // 对齐 tokens.css --geojson-color-emotion-*（= tokens.json geojson.emotion 权威源 = emotionColors()）；旧 #86E61C 套是跑偏异类，已归一
export const L2_NEGATIVE = { 'Very Negative': '#B92D2D', 'Negative': '#C4956A' };    // 同上，红↔褐对齐 tokens
export const L2_NEUTRAL_COLOR = '#C0C0C0';                                            // 浅灰，对齐 tokens neutral

// ── 4×5 治理要素专用色源（综合/单极性 Overview 共用，单源勿散用）──
export const DOMAIN_BAR_COLOR = '#4876FF';      // 4 领域横条（综合数据总览 + 单极性总览统一）
export const ELEMENT_BAR_COLOR = '#836FFF';     // 4 要素横条（单极性总览）
// 单极性归因矩阵 count 三级色段（数量 max→mid→min = 深→中→浅；强调矩阵内分布，非极性色）
// 深紫罗兰 #A020F0 / 中紫罗兰 #9370DB / 蓟紫淡 #D8BFD8 —— 拉开差距便于分辨（替旧 #6A5ACD/#7B68EE/#8470FF 太接近）
export const POL_MATRIX_TIERS = { high: '#A020F0', mid: '#9370DB', low: '#D8BFD8' };

/** 极性指数(pi, -2~2) → 5 级判断词。cell-popup「极性指数」+ tip-popup「极性判断」行共用，
 *  保证全站同步（勿在他处另写阈值）。 */
export function valenceOf(pi) {
  if (pi == null || pi === '') return '—';
  const v = Number(pi);
  if (!isFinite(v)) return '—';
  if (v >= 1.0) return '非常积极';
  if (v >= 0.15) return '偏积极';
  if (v <= -1.0) return '非常消极';
  if (v <= -0.15) return '偏消极';
  return '中性';
}
/** 极性判断配色（与 terrain-9 色带同源：非常级=TERRAIN_*[2] 深色端、偏级=[1] 中色、中性=中蓝）。
 *  与 L2 点位荧光色解耦——色卡/网格用 TERRAIN 深色，判断字色跟随，避免「字翠绿/卡深绿」不一致。 */
export function valenceColorOf(pi) {
  const v = Number(pi);
  if (!isFinite(v)) return '#999';
  if (v >= 1.0) return TERRAIN_GREEN[2];      // 深绿（terrain-9 极积极段）
  if (v >= 0.15) return TERRAIN_GREEN[1];     // 中绿（偏积极）
  if (v <= -1.0) return TERRAIN_RED[2];       // 深红（极消极段）
  if (v <= -0.15) return TERRAIN_RED[1];      // 中红（偏消极）
  return TERRAIN_BLUE[1];                      // 中蓝（中性）
}

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

// ── Heatmap color ramp presets ──
// Each ramp = { name, stops: [[density,color], ...] }. density 0 always transparent.

// gradientStops：从端点色（hex[]）线性插值出 n 段渐变 stops（density 0 透明）。
// 用于"积极/消极/中性"由 7 大类胶囊色派生的分段色板（胶囊色 ↔ 色板一一对应）。
function _hex2rgb(h) { h = String(h).replace('#', ''); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; }
function _rgb2hex(rgb) { return '#' + rgb.map((x) => Math.round(x).toString(16).padStart(2, '0')).join(''); }

// ── HSL 工具：色相插值（替 RGB lerpHex）—— 色相旋转保持明度，中间色明亮
//    （绿↔黄 中间黄绿，非 RGB 土黄；红↔紫 逆时针经品红）
function _hex2hsl(h) {
  const [r, g, b] = _hex2rgb(h).map((x) => x / 255);
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  const l = (max + min) / 2;
  const d = max - min;
  let s = 0, hue = 0;
  if (d !== 0) {
    s = d / (1 - Math.abs(2 * l - 1));
    if (max === r) hue = ((g - b) / d) % 6;
    else if (max === g) hue = (b - r) / d + 2;
    else hue = (r - g) / d + 4;
    hue *= 60;
    if (hue < 0) hue += 360;
  }
  return [hue, s * 100, l * 100];
}
function _hsl2hex(hsl) {
  const [h, s, l] = hsl;
  const _s = s / 100, _l = l / 100;
  const c = (1 - Math.abs(2 * _l - 1)) * _s;
  const x = c * (1 - Math.abs((h / 60) % 2 - 1));
  const m = _l - c / 2;
  let r = 0, g = 0, b = 0;
  if (h < 60) [r, g, b] = [c, x, 0];
  else if (h < 120) [r, g, b] = [x, c, 0];
  else if (h < 180) [r, g, b] = [0, c, x];
  else if (h < 240) [r, g, b] = [0, x, c];
  else if (h < 300) [r, g, b] = [x, 0, c];
  else [r, g, b] = [c, 0, x];
  return _rgb2hex([r, g, b].map((v) => Math.round((v + m) * 255)));
}
/** HSL 插值（hue 最短路径，sat/lightness 线性）—— 色相旋转保明度，中间明亮。 */
export function lerpHsl(h1, h2, t) {
  const a = _hex2hsl(h1), b = _hex2hsl(h2);
  let dh = b[0] - a[0];
  if (dh > 180) dh -= 360;
  if (dh < -180) dh += 360;
  const hue = (a[0] + dh * t + 360) % 360;
  const sat = a[1] + (b[1] - a[1]) * t;
  const light = a[2] + (b[2] - a[2]) * t;
  return _hsl2hex([hue, sat, light]);
}
/** HSL 空间插值生成 n 段 stops（色相渐变，中间明亮不土黄）。 */
export function gradientStopsHsl(colors, n) {
  const stops = [[0, `rgba(${_hex2rgb(colors[0]).join(',')},0)`]];
  for (let i = 1; i <= n; i++) {
    const t = (i - 1) / (n - 1) * (colors.length - 1);
    const lo = Math.floor(t), hi = Math.min(colors.length - 1, lo + 1), f = t - lo;
    stops.push([i / n, lerpHsl(colors[lo], colors[hi], f)]);
  }
  return stops;
}

export function gradientStops(colors, n) {
  const pts = colors.map(_hex2rgb);
  const stops = [[0, `rgba(${pts[0][0]},${pts[0][1]},${pts[0][2]},0)`]];
  for (let i = 1; i <= n; i++) {
    const t = (i - 1) / (n - 1) * (pts.length - 1);   // 0..len-1
    const lo = Math.floor(t), hi = Math.min(pts.length - 1, lo + 1), f = t - lo;
    const c = [0, 1, 2].map((k) => pts[lo][k] + (pts[hi][k] - pts[lo][k]) * f);
    stops.push([i / n, _rgb2hex(c)]);
  }
  return stops;
}

// 7 大类胶囊色（喜怒哀乐愁急盼 = 绿/橙/红/紫红/紫/深蓝/天蓝）—— 单一调色源。
// 胶囊(EMOTION_MACRO)、classify-7、积极/消极/中性格色板均派生自此，保证全局一致。
export const MACRO_COLORS = ['#43C063', '#F5A623', '#E53935', '#C2185B', '#8E44AD', '#1A3A8C', '#4FC3F7'];

// 地形/网格 综合（消极/中性/积极）三段色源——terrain-9 与 green-3/red-3/blue-3 共用，
// 改色只需改这三组端点（密度低→高 = 浅→深）。density 0→1 = 洼地消极 → 中性 → 高地积极。
export const TERRAIN_RED = ['#F6C9B0', '#C44A2E', '#5C1208'];   // 消极：浅橙淡 → 深红深
export const TERRAIN_BLUE = ['#CFE0EE', '#3A7CA5', '#0D3B5C'];  // 中性：浅蓝淡 → 深蓝深
export const TERRAIN_GREEN = ['#D4F4D0', '#3DBA3D', '#063006']; // 积极：浅绿淡 → 深绿深

export const HEATMAP_RAMPS = {
  // 类型细分色板：density 弱→强（stops 低→高），高值=热核=该极性最强情绪（不可变约束）。
  //   积极：乐(橙)弱 → 喜(绿)强；消极：愁(紫)弱 → 哀(紫红)中 → 怒(红)强；中性：盼(天蓝)弱 → 急(深蓝)强。
  //   色带"显示"由 rampDisplaySegs() 对类型细分反转（高→低，对齐 EMOTION_MACRO_ORDER 胶囊序）；
  //   地图 paint（map.js heatmap-color）用本 stops 原序（density 0→1=弱→强，热核=强情绪）——数据轴与显示轴分离。
  positive: { name: '积极', stops: gradientStops(['#F5A623', '#43C063'], 7) },              // 乐橙(弱/低) → 喜绿(强/高·热核)
  negative: { name: '消极', stops: gradientStops(['#8E44AD', '#C2185B', '#E53935'], 7) },    // 愁紫(弱) → 哀紫红(中) → 怒红(强/高·热核)
  neutral:  { name: '中性', stops: gradientStops(['#4FC3F7', '#1A3A8C'], 7) },               // 盼天蓝(弱/低) → 急深蓝(强/高·热核)
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
    // 单色热力（L1 默认色，舆情热度）— 橙红色调（参考 ColorBrewer Reds 暖段）
    name: '单色热力',
    stops: [
      [0.00, 'rgba(255,245,240,0)'],
      [0.15, '#FCBBA1'],
      [0.30, '#FC9272'],
      [0.50, '#FB6A4A'],
      [0.70, '#EF3B2C'],
      [0.85, '#CB181D'],
      [1.00, '#99000D'],
    ],
  },
  // 红/蓝/绿渐变（3D 综合情绪地形高程着色，terrain-9 的平滑变体）：
  // 发散·两端深色：消极深红(低值) → 浅红 → 中性蓝(浅-中-浅) → 浅绿 → 积极深绿(高值)。
  // 端点序 = 红反转(深→浅) + 蓝(浅-中-浅) + 绿(浅→深)，HSL 平滑插值。
  'diverging-rg': (() => {
    const ends = [...[...TERRAIN_RED].reverse(), TERRAIN_BLUE[0], TERRAIN_BLUE[1], TERRAIN_BLUE[0], ...TERRAIN_GREEN];
    return { name: '红蓝绿地形（平滑·两端深色）', stops: gradientStopsHsl(ends, 9) };
  })(),
  // 网格暖色谱（暗红→金黄 sequential）。红段收窄(renorm 0-0.15)→数据主体(q25-q90, γ=0.5 下 _grid_h 0.12-0.40)
  // 落在红橙/橙黄过渡段(0.15-0.50)，避免"大面积纯红"，呈现自然红→黄中间层次。
  // 低端暗红 #8B0000 不变、中间橙黄 #FF9900、高端亮金 #FFDF00。
  'grid-warm': {
    name: '网格暖色（暗红→金黄）',
    stops: [
      [0.00, 'rgba(139,0,0,0)'],
      [0.10, '#8B0000'],   // 暗红（renorm 0.00；最低，pc<<1）
      [0.235, '#C92A20'],  // 鲜红（renorm 0.15；pc≈1=q25，红段收窄到此）
      [0.370, '#F06428'],  // 红橙（renorm 0.30；pc≈3-4=q50，更亮暖替原 EE5A28）
      [0.550, '#FF9900'],  // 橙黄（renorm 0.50；pc≈12=q90，中间）
      [0.802, '#FFC63C'],  // 橙金（renorm 0.78；pc≈30+）
      [1.00, '#FFDF00'],   // 亮金黄（renorm 1.00；pc=max，高端）
    ],
  },
  // 7 色情绪分类色板 = 7 大类胶囊色同源同序（喜怒哀乐愁急盼）。作 chip/legend 调色源。
  'classify-7': {
    name: '情绪 7 类',
    stops: [
      [0.00, 'rgba(67,192,99,0)'],
      [0.14, '#43C063'],   // 喜 绿
      [0.28, '#F5A623'],   // 乐 橙
      [0.42, '#E53935'],   // 怒 红
      [0.56, '#C2185B'],   // 哀 紫红
      [0.70, '#8E44AD'],   // 愁 紫
      [0.84, '#1A3A8C'],   // 急 深蓝
      [1.00, '#4FC3F7'],   // 盼 天蓝
    ],
  },
  // 总体情况色板（地形/网格，红蓝绿发散；与类型细分的胶囊色渐变不同源）
  // density 0→1 = 洼地(最消极,深红) → 浅红 → 中性蓝(浅-中-浅) → 浅绿 → 高地(最积极,深绿)。
  // 发散规约：两端深色（消极端深红 / 积极端深绿），中性居中两端浅（避免内部深色斑）。
  // 9 段 = 消极3(深→浅) + 中性3(浅-中-浅) + 积极3(浅→深)，色源与 green-3/red-3/blue-3 同源。
  'terrain-9': (() => {
    const seg = (cols, lo, hi) => cols.map((c, i) => [lo + (hi - lo) * i / (cols.length - 1), c]);
    // 配 piToNorm 固定分段映射：中性带对齐 pi±0.15（renorm 后 ≈0.42-0.57），偏级落红/绿段。
    // 替 p95 拉伸（数据相关致色带边界无法对齐 valenceOf 判断阈值=颜色不准根因）。
    const stops = [
      [0.00, 'rgba(122,30,22,0)'],
      ...seg([...TERRAIN_RED].reverse(), 0.06, 0.45),                          // 深红(pi≤-1) → 浅红(pi=-0.15 边界)
      ...seg([TERRAIN_BLUE[0], TERRAIN_BLUE[1], TERRAIN_BLUE[0]], 0.46, 0.60), // 中性蓝（pi±0.15 窄带）
      ...seg(TERRAIN_GREEN, 0.61, 1.00),                                       // 浅绿(pi=0.15) → 深绿(pi≥1)
    ];
    return { name: '红蓝绿地形（消极/中性/积极·对齐 piToNorm 固定分段）', stops };
  })(),
  // 网格+L2 积极/消极/中性 各 3 段（端点色与 terrain-9 同源）
  'green-3':  { name: '积极（绿）', stops: gradientStops(TERRAIN_GREEN, 6) },   // 6 段（中间过渡多，张力）；极性网格颜色=_grid_h_pos 该极性点数
  'red-3':    { name: '消极（红）', stops: gradientStops(TERRAIN_RED, 6) },     // 6 段；颜色=_grid_h_neg
  'blue-3':   { name: '中性（蓝）', stops: gradientStops(TERRAIN_BLUE, 6) },    // 6 段；颜色=_grid_h_neu
};

// sorted keys for UI iteration（类型细分渐变 + 总体情况红蓝绿地形 + 网格 3 段）
export const HEATMAP_RAMP_KEYS = ['rainbow', 'positive', 'negative', 'neutral', 'anxiety', 'mono', 'diverging-rg', 'grid-warm', 'classify-7', 'terrain-9', 'green-3', 'red-3', 'blue-3'];

/** 色带"显示用"离散色块（供弹窗③ / 图例 / Overview 的分段条渲染）。
 *  类型细分(positive/negative/neutral) → 反转：density 高→低显示（左端=强情绪=热核，对齐 EMOTION_MACRO_ORDER 胶囊序）。
 *  其他 density 色板 → 原序：低→高（总体情况有地形/彩虹语义，不反）。
 *  地图 paint（map.js heatmap-color）直接用 ramp.stops 原序（density 0→1=弱→强，热核=强情绪），与此显示方向无关——数据轴与显示轴分离。 */
export function rampDisplaySegs(rampKey, ramp) {
  if (!ramp || !ramp.stops) return ['#ccc'];
  const segs = ramp.stops.filter(([d]) => d > 0).map(([, c]) => c);
  return ['positive', 'negative', 'neutral'].includes(rampKey) ? segs.reverse() : segs;
}

// ── Emotion type palette — 小类色 = 所属大类色系派生 ──
// 单小类大类：小类色 = 大类色（见 EMOTION_MACRO）；愁类 2 小类（焦虑担忧/不满抱怨）用紫色系明度梯度区分。
// 改大类色（EMOTION_MACRO / MACRO_COLORS）须同步此处，保证小类归属大类色系。
// 治理动作映射（EMOTION_TYPE_ACTION）与 SCRIPT/emotion_lexicon.py EMOTION_LEXICON 保持一致。
export const EMOTION_TYPE_COLORS = {
  '不满抱怨': '#7D3C98',   // 愁·深紫（大类 #8E44AD 加深）—— 设施/服务整改
  '焦虑担忧': '#A569BD',   // 愁·中紫（大类 #8E44AD 提浅）—— 安全/出行治理
  '失望厌恶': '#C2185B',   // = 哀·紫红 —— 环境整治
  '愤怒': '#E53935',       // = 怒·红 —— 紧急响应
  '期待建议': '#4FC3F7',   // = 盼·天蓝 —— 献策纳规
  '喜悦满意': '#43C063',   // = 喜·绿 —— 标杆保护
  '怀旧认同': '#F5A623',   // = 乐·橙 —— 文化传承
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

// ── 情绪大类（7 类，固定）：喜怒哀乐愁急盼 + Tol Bright 7 色（图2 采样 6 色 + 柔和绿） ──
// 大类 = 高度抽象固定分类；小类（emotion_type）= 数据动态归纳，无固定数量。
// polarity 字段用于"选极性 → 自动选大类胶囊"的传导：
//   positive → 喜+乐, negative → 怒+哀+愁, neutral → 急+盼
// 7 大类胶囊色 ↔ classify-7 色板同源同序（喜绿/乐橙/怒红/哀紫红/愁紫/急深蓝/盼天蓝）。
// 改色须同步：classify-7 色板、积极/消极/中性格色板、Overview/图例（全局一致规范）。
export const EMOTION_MACRO = {
  '喜': { color: '#43C063', polarity: 'positive', desc: '满意/愉悦/赞美（绿）' },
  '乐': { color: '#F5A623', polarity: 'positive', desc: '欢愉/欣赏/认同（橙）' },
  '怒': { color: '#E53935', polarity: 'negative', desc: '愤怒/侵权/极端不满（红）' },
  '哀': { color: '#C2185B', polarity: 'negative', desc: '失望/沮丧/无奈（紫红）' },
  '愁': { color: '#8E44AD', polarity: 'negative', desc: '焦虑/担忧/隐患（紫）' },
  '急': { color: '#1A3A8C', polarity: 'neutral',  desc: '紧迫/催促/呼吁（深蓝）' },
  '盼': { color: '#4FC3F7', polarity: 'neutral',  desc: '期待/希望/建议（天蓝）' },
};
export const EMOTION_MACRO_ORDER = ['喜', '乐', '怒', '哀', '愁', '急', '盼'];

// 小类（微观 emotion_type）→ 大类 默认归属。数据中未列出的小类按 polarity 派生兜底。
export const EMOTION_MACRO_MAP = {
  '喜悦满意': '喜',
  '怀旧认同': '乐',
  '失望厌恶': '哀',
  '愤怒': '怒',
  '焦虑担忧': '愁',
  '不满抱怨': '愁',   // 抱怨多源于焦虑/担忧情绪
  '期待建议': '盼',
};

/** 从 polarity 兜底派生大类（小类未在 EMOTION_MACRO_MAP 中时使用）。 */
export function macroOfPolarity(polarity) {
  if (polarity === 'Very Positive' || polarity === 'Positive') return '喜';
  if (polarity === 'Very Negative') return '怒';
  if (polarity === 'Negative') return '哀';
  return '盼';   // Neutral / 未知
}

// 各极性大类按 density 弱→强序（强情绪在高 density 端 = 热核）。
//   积极：乐(弱)→喜(强)；消极：愁(弱)→哀(中)→怒(强)；中性：盼(弱)→急(强)。
//   与 HEATMAP_RAMPS.positive/negative/neutral 的端点序一致 → 全选时 buildMacroRamp 等同固定 ramp。
export const MACRO_DENSITY_ORDER = {
  positive: ['乐', '喜'],
  negative: ['愁', '哀', '怒'],
  neutral: ['盼', '急'],
};

/** 按选中大类 + 极性生成 inline ramp（类色 HSL 色相插值，每类占 3 段）。
 *  段数 = 选中类数 × 3：积极 6 / 消极 9 / 中性 6 / 单类 3。
 *  整体色相连续渐变（类间不割裂，HSL 中间明亮不土黄）；density 弱→强（热核=最强情绪）。
 *  色带"显示"由 rampDisplaySegs 据 polarity reverse（高→低 = 胶囊序）。 */
export function buildMacroRamp(selectedMacros, polarity) {
  const order = MACRO_DENSITY_ORDER[polarity];
  if (!order) return null;
  const macros = order.filter((m) => selectedMacros.includes(m));   // density 序 ∩ 选中
  if (!macros.length) return null;
  const colors = macros.map((m) => EMOTION_MACRO[m] && EMOTION_MACRO[m].color).filter(Boolean);
  if (!colors.length) return null;
  return {
    name: macros.slice().reverse().join('→'),                        // 强→弱（胶囊序展示）
    stops: gradientStopsHsl(colors, colors.length * 3),              // 类色 HSL 插值，每类 3 段色相（整体连续渐变）
  };
}

// ── Heatmap source tracking: sourceKey → heatmap layer id ──
// sourceKey = sanitized string identifying the data source (group id / child layer id).
// When generating a new heatmap for the same sourceKey, the old one is removed first.
const _heatmapSources = new Map();
export function getHeatmapForSource(sourceKey) { return _heatmapSources.get(sourceKey); }
export function setHeatmapForSource(sourceKey, layerId) { _heatmapSources.set(sourceKey, layerId); }
export function removeHeatmapSource(sourceKey) { _heatmapSources.delete(sourceKey); }
export function clearHeatmapSources() { _heatmapSources.clear(); }

// ── Draw mode state (neutral hub — draw-tool/popup/main all import state, avoids cycles) ──
// Mode values mirror geojson.io state/mode.ts (NONE + DRAW_*). isDrawActive gates popup/selection
// handlers so draw clicks don't trigger feature popups.
let _drawMode = 'NONE';
export function getMode() { return _drawMode; }
export function setMode(m) { _drawMode = m; }
export function isDrawActive() { return _drawMode !== 'NONE'; }

/** 范围/边界层判定（polygon/line 且非工具产物 = 用户绘/导入的范围；独占关他时保留）。
 *  与 addLayer 内 isRange 同源（state.js:623），抽此供 grid/heatmap/buffer-tool 复用。 */
export function isRangeLayer(l) {
  return !!(l && (l.kind === 'polygon' || l.kind === 'line') &&
    !(l.paint && l.paint._ui && l.paint._ui.tool));
}

export function addLayer({ name, kind, fc, needsAnalysis = false, colorMode, paint, parentId }) {
  const id = 'L' + (++_seq).toString().padStart(3, '0');
  // 范围/边界层（polygon/line 非分析）自动配色：按现有同类层数循环 PRESET_COLORS，保持图层间可区分。
  // 分析层（grid/terrain，paint._ui.tool 存在）不配色板槽、保持 NAVY（其渲染走 gridField 不用 color）。
  const isRange = (kind === 'polygon' || kind === 'line') && !(paint && paint._ui && paint._ui.tool);
  const rangeColor = isRange
    ? PRESET_COLORS[[..._layers.values()].filter((l) =>
        (l.kind === 'polygon' || l.kind === 'line') && !(l.paint && l.paint._ui && l.paint._ui.tool)).length % PRESET_COLORS.length]
    : NAVY;
  const defaultPaint = kind === 'polygon'
    ? { color: rangeColor, fillOn: false, lineWidth: 1, fillOpacity: 0.15 }
    : kind === 'line'
      ? { color: rangeColor, lineWidth: 1 }
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
    colorMode: colorMode || (kind === 'point' ? (needsAnalysis ? 'needsAnalysis' : 'polarity') : 'range'),  // 情绪色系(polarity)是 point 专属；polygon/line 默认 'range'，避免误触发极性图例
    paint: { ...defaultPaint, ...(paint || {}) },
    crsInfo: (fc && fc.__crs) || undefined,   // import 标注（投影→WGS84 或 WGS84）；分析层无 → panel 默认 WGS84
  };
  _layers.set(id, layer);
  _frozenCats.delete(categoryOf(layer));   // 新层加入 → 解冻其 category，让 applyGroupOrder 按规则给新层归位
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
  // bug④ fix：热力图层 level 不再硬判 L2——L1 彩虹热力图会被错标成 L2。
  // 从生成时持久化的 paint._ui.level 推断；无 _ui（旧层）时按 colorMode 兜底。
  if (layer.kind === 'heatmap') {
    const uiLevel = layer.paint && layer.paint._ui && layer.paint._ui.level;
    if (uiLevel) return uiLevel;
    return 'L2';   // 兜底（多数热力图源出 L2）
  }
  if (layer.kind === 'polygon' || layer.kind === 'line') {
    // bug fix：网格聚合/地形等 polygon 分析层持久化了 _ui.level（L1/L2）—— 须优先用它，
    // 否则被一刀切判成 'range'，Overview 标题误显 'Range·极性·…'。无 _ui（纯范围面/线）才回退 'range'。
    const uiLevel = layer.paint && layer.paint._ui && layer.paint._ui.level;
    if (uiLevel) return uiLevel;
    return 'range';
  }
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

/** L 徽章配色：网格/地形层行标签 "L1·G"/"L2·E" 中 L 前缀色 = 该 level 情绪点层标签色。
 *  L1=CONFIDENCE 中段橙（L1 治理置信度色板）；L2=L2 Positive teal（情绪点代表色）。 */
export function levelPointColor(lv) {
  if (lv === 'L1') return '#FF9800';
  if (lv === 'L2') return '#3DBA9D';
  return '#9aa0a6';
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

/** Derive a layer's display category (UI grouping only — never stored on the object).
 *  Mutually exclusive order: heatmap > group/l2-* > confidence > needsAnalysis > polygon|line > other.
 *  L2 group AND its 3 polarity children all derive 'l2', so the whole block stays contiguous
 *  through applyGroupOrder (children never separate from their group). */
export function categoryOf(l) {
  if (!l) return 'other';
  if (l.kind === 'heatmap') return 'heatmap';
  if (l.kind === 'group') return l.name === 'EmotionMap Copilot' ? 'ai' : 'l2';   // EmotionMap Copilot 组独立成类（钉底），余 group 归 l2
  if (typeof l.colorMode === 'string' && l.colorMode.indexOf('l2-') === 0) return 'l2';
  if (l.colorMode === 'confidence') return 'l1';
  if (l.needsAnalysis || l.colorMode === 'needsAnalysis') return 'l0';
  if (l.kind === 'polygon' || l.kind === 'line') {
    if (l.paint && l.paint._ui && l.paint._ui.tool === 'buffer') return 'buffer';
    if (l.paint && l.paint._ui && l.paint._ui.tool === 'grid') return 'grid';
    if (l.paint && l.paint._ui && l.paint._ui.tool === 'terrain') return 'terrain';
    return 'range';
  }
  return 'other';
}

export function getGroupOrder() { return _groupOrder.slice(); }
/** 标记某 category 为「手动 within-category 重排过」——applyGroupOrder 不再重排其组内顺序（保留用户拖拽）。 */
export function freezeCategoryOrder(cat) { if (cat) _frozenCats.add(cat); }
export function isCollapsed(cat) { return _groupCollapse.has(cat); }
export function toggleCollapsed(cat) {
  if (_groupCollapse.has(cat)) _groupCollapse.delete(cat);
  else _groupCollapse.add(cat);
}
export function isGroupFold(id) { return id != null && _groupFold.has(id); }
export function toggleGroupFold(id) {
  if (id == null) return;
  if (_groupFold.has(id)) _groupFold.delete(id);
  else _groupFold.add(id);
}

/** Normalize _layers order to match _groupOrder (stable within each category; children stay
 *  attached to their group). Idempotent — returns false when already in order so callers can
 *  skip the z-sync. Keeps the list-top = map-top invariant once the list is grouped by category. */
/** 层时间序：deriveTimeTag → T1=0/T2=1/T3=2，未识别=3（末）。L2 group 取 group.fc 首点 time_label。 */
function _layerTimeFromName(name) {
  // 工具生成层（grid/heatmap）cell feature 无 time_label；层名 T 前缀兜底（"T1·综合·标准网格·..."）。
  const m = /^T([1-3])·/.exec(name || '');
  return m ? 'T' + m[1] : '';
}
function _layerTimeRank(l) {
  if (!l) return 3;
  // 优先显式 timeTag（工具生成层注入）；次选 feature time_label；末选层名 T 前缀（全局排序兜底）
  const t = l.timeTag || deriveTimeTag(l.fc) || _layerTimeFromName(l.name);
  return t === 'T1' ? 0 : t === 'T2' ? 1 : t === 'T3' ? 2 : 3;
}
/** 层级序（主键）：L1=0 < L2=1。L 数据优先于 T 的核心排序键（需求：L 最优先，其次 T）。
 *  _ui.level 优先；无 _ui（点/面导入层）按 colorMode 兜底（confidence=L1, l2-*=L2）。 */
function _layerLevelRank(l) {
  const ui = l && l.paint && l.paint._ui;
  if (ui && ui.level) return ui.level === 'L1' ? 0 : 1;
  if (l && l.colorMode === 'confidence') return 0;
  if (l && typeof l.colorMode === 'string' && l.colorMode.indexOf('l2-') === 0) return 1;
  return 0;
}
/** 极性序（末键，仅 L2 grid/heatmap 有意义）：overall=0 < positive=1 < neutral=2 < negative=3。 */
function _layerPolarityRank(l) {
  const pol = l && l.paint && l.paint._ui && l.paint._ui.polarity;
  if (pol === 'positive') return 1;
  if (pol === 'neutral') return 2;
  if (pol === 'negative') return 3;
  return 0;   // overall / 无极性
}

/** Normalize _layers order to match _groupOrder（组内 levelRank × timeRank × polarityRank 稳定排序；children 留 parent 后）。
 *  Idempotent — 返回 false 表示已就序（调用方可跳过 z-sync，但 renderLayerList 现无条件 restackZ）。
 *  _frozenCats 中的 category 跳过组内排序（保留用户手动拖拽序），仅遵守 category 间 _groupOrder。 */
export function applyGroupOrder() {
  const keys = Array.from(_layers.keys());
  // 按类别分桶；桶内稳定排序 (levelRank, timeRank, polarityRank)——L 主、T 次、极性末。
  // L2 group 与其 children 同 level/timeRank → 稳定排序保连续。
  const byCat = {};
  for (const k of keys) {
    const l = _layers.get(k);
    const c = categoryOf(l);
    (byCat[c] = byCat[c] || []).push(k);
  }
  for (const c of Object.keys(byCat)) {
    if (_frozenCats.has(c)) continue;   // 用户手动重排过 → 保留现状不覆盖
    byCat[c].sort((a, b) => {
      const la = _layers.get(a), lb = _layers.get(b);
      const lvA = _layerLevelRank(la), lvB = _layerLevelRank(lb);
      if (lvA !== lvB) return lvA - lvB;                          // L1 < L2 主键
      const ta = _layerTimeRank(la), tb = _layerTimeRank(lb);
      if (ta !== tb) return ta - tb;                              // T1<T2<T3 次键
      return _layerPolarityRank(la) - _layerPolarityRank(lb);     // 综合<积极<中性<消极 末键
    });
  }
  // 钉底：range 恒在 ai（AI 工作区）之上，二者为最末两组（用户要求「恒定」；与 renderLayerList 显示钉底一致）。
  const PINNED = ['range', 'ai'];
  const desired = [];
  const used = new Set();
  for (const cat of _groupOrder) {
    if (PINNED.includes(cat)) continue;                  // 钉底组跳过，末尾统一输出
    for (const k of (byCat[cat] || [])) { desired.push(k); used.add(k); }
  }
  for (const k of keys) {                                 // categories missing from _groupOrder（且非钉底）
    if (used.has(k)) continue;
    if (PINNED.includes(categoryOf(_layers.get(k)))) continue;
    desired.push(k); used.add(k);
  }
  for (const cat of PINNED) {                             // 钉底组最后输出：range 在 ai 前
    for (const k of (byCat[cat] || [])) { desired.push(k); used.add(k); }
  }
  const same = desired.length === keys.length && desired.every((k, i) => k === keys[i]);
  if (same) return false;
  const nxt = new Map();
  for (const k of desired) nxt.set(k, _layers.get(k));
  _layers.clear();
  for (const [k, v] of nxt) _layers.set(k, v);
  return true;
}

/** Inter-category reorder (group-card drag): move fromCat's segment before/after toCat,
 *  then apply to _layers. */
export function reorderGroupSegment(fromCat, toCat, before) {
  if (!fromCat || fromCat === toCat) return;
  if (fromCat === 'range' || fromCat === 'ai') return;   // 钉底组不可拖动（恒在最末）
  const order = _groupOrder.filter((c) => c !== fromCat);
  let idx = order.indexOf(toCat);
  if (idx < 0) idx = order.length;
  order.splice(before ? idx : idx + 1, 0, fromCat);
  _groupOrder = order;
  applyGroupOrder();
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

// P1: FIELD_SYNONYMS 收敛到 field_dictionary.js（统一字段语义层）。
// re-export 兼容旧调用方（import.js detectColorMode 等）；新代码建议直接用 resolveRole/findKeyByRole。
export { FIELD_SYNONYMS } from './field_dictionary.js';

// ── 「视野-数据-结论同步」图层互斥规则（任务6/7）─────────────────────────────
// 两组：A=情绪点(l0/l1/l2)，B=Toolbox空间分析(heatmap/grid/terrain/buffer)，R=Range(范围)。
// 规则：① B 组内部同时只显示一个（开一个关其他 B）。② A 与 B 不能同屏（开 A 关 B，开 B 关 A）。
//       ③ A 组同时只显示一个数据源（同一 L2 group 的极性子层视为同源，保留）。④ R 与谁都共存，永不被动关。
/** Toolbox 空间分析层（B 组）。 */
export function isToolAnalysisLayer(l) {
  const c = categoryOf(l);
  return c === 'heatmap' || c === 'grid' || c === 'terrain' || c === 'buffer';
}
/** 情绪点层（A 组）。 */
export function isEmotionPointLayer(l) {
  const c = categoryOf(l);
  return c === 'l0' || c === 'l1' || c === 'l2';
}
/** 当 onId 设为可见时，按互斥规则隐藏冲突层。返回被隐藏的层 id 数组（调用方 renderLayer + 选中超链）。
 *  承重：不动 Range（isRangeLayer 跳过）、不动同 L2 group 兄弟（同源极性保留）。 */
export function enforceMutualExclusion(onId) {
  const on = getLayer(onId);
  if (!on || !on.visible) return [];
  const onIsB = isToolAnalysisLayer(on);
  if (!onIsB && !isEmotionPointLayer(on)) return [];   // Range/other → 不动
  const hidden = [];
  for (const l of getLayers()) {
    if (l.id === onId || l.kind === 'group' || !l.visible) continue;
    if (isRangeLayer(l)) continue;                      // Range 永不被动关（承重）
    let hide = false;
    if (onIsB) {
      // 开分析层 → 关其他分析层(B) + 所有点层(A)
      hide = isToolAnalysisLayer(l) || isEmotionPointLayer(l);
    } else {
      // 开点层(A) → 关所有分析层(B)；点层内部：同 L2 group 兄弟保留，不同源关
      hide = isToolAnalysisLayer(l);
      if (!hide && isEmotionPointLayer(l)) {
        hide = !(on.parentId && l.parentId && on.parentId === l.parentId);
      }
    }
    if (hide) { setLayerVisible(l.id, false); hidden.push(l.id); }
  }
  return hidden;
}
