// ═══ tip-popup.js — 网格/柱体/地形环 悬停浮动卡（统一悬停设计语言） ═══
// 单一 #tip-popup（position:fixed, 120×120, 白底, radius 4px, 高阴影），随鼠标灵动跳动。
// 自适应方位：依指针在视口的位置选左/右/上/下，目的=不遮挡主体。
// 灵动算法：hysteresis（位移超阈值才换位）+ 象限翻转 + CSS transition 顺滑滑动。
// 反查防抖：质心 key 缓存 + inflight 去重（同格只发一次 reverseGeocode），切格不重复发。
// 替换 tool 层（grid/terrain）原生 dark tooltip；point 悬停已接入（区域+极性分数+domain×element）；range 暂留 dark tooltip。
import { reverseGeocode } from './api.js';
import { POLARITY_LABEL, valenceOf, valenceColorOf } from './state.js';
import { DOMAIN_LABEL, ELEMENT_LABEL, pickCellFeature, _locLine } from './popup.js';
import { trackGeocode } from './geocode-loader.js';

let _map = null;
const _bound = new Set();          // 已绑定的 maplibre layer id（幂等）
const CW = 120, CH = 120, GAP = 16; // 卡片尺寸 + 与指针间距
const HYSTERESIS = 14;             // 位移阈值（px）：超过才更新位置，否则保持（"不死绑定"）
let _sideH = 'right', _sideV = 'below'; // 当前象限记忆（hysteresis 防抖）
let _rafPending = false;
let _lastPt = null;                // 最近指针 viewport 坐标 { x, y }
let _lastPos = { left: -999, top: -999 }; // 当前落位（判断位移阈值）
const _geoCache = new Map();       // key=`lng,lat` → { zone_name, nearest_poi }
const _inflight = new Set();       // 正在请求的 key（防同格重复发）
let _lastCellKey = null;           // 当前显示的格质心 key（同格不重发反查）
let _lastHoverKey = null;          // 当前高亮 cell key（同格不重敷 hover 层）

const el = () => document.getElementById('tip-popup');

export function initTipPopup(map) {
  _map = map;
  // cell:selected：隐浮动卡但保留柱体升起（点击不缩回，仅 mouseleave 缩回）
  document.addEventListener('cell:selected', hideTipPopup);
  document.addEventListener('layers:changed', () => { hideTipPopup(); clearCellHover(); _lastHoverKey = null; });
}

/** 取指针 viewport 坐标：优先 originalEvent.clientX/Y，fallback e.point + map 容器 rect。 */
function evtClientPt(e) {
  const oe = e && e.originalEvent;
  if (oe && typeof oe.clientX === 'number') return { x: oe.clientX, y: oe.clientY };
  if (e && e.point && _map) {
    const r = _map.getContainer().getBoundingClientRect();
    return { x: r.left + e.point.x, y: r.top + e.point.y };
  }
  return null;
}

/** 绑定某 maplibre layer id 的 mouseenter/mousemove/mouseleave → tip-popup。 */
export function bindTipPopup(layer, lid, uiOverride) {
  if (!_map || !layer || !lid || _bound.has(lid)) return;
  _bound.add(lid);
  const ui = uiOverride || (layer.paint && layer.paint._ui) || {};   // uiOverride：point 层无 paint._ui，显式传 {kind,colorMode}

  const onEnter = (e) => {
    _map.getCanvas().classList.add('is-pointer');
    const f = (ui.kind === 'point') ? (e.features && e.features[0]) : pickCellFeature(e.features || []);
    if (!f) return;
    _lastPt = evtClientPt(e);
    fillContent(f, ui);
    showEl();
    if (_lastPt) positionCard();   // mouseenter 即定位，防首帧停在左上角
    maybeCellHover(f, ui, layer);
  };
  const onMove = (e) => {
    const f = (ui.kind === 'point') ? (e.features && e.features[0]) : pickCellFeature(e.features || []);
    if (!f) return;
    _lastPt = evtClientPt(e);
    fillContent(f, ui);
    showEl();          // mousemove 也确保显示（mouseenter 可能因鼠标已在层内未触发）
    schedulePos();
    maybeCellHover(f, ui, layer);
  };
  _map.on('mouseenter', lid, onEnter);
  _map.on('mousemove', lid, onMove);
  _map.on('mouseleave', lid, () => {
    _map.getCanvas().classList.remove('is-pointer');
    hideTipPopup();
    clearCellHover();          // 仅 mouseleave 缩回柱体（点击不缩回）
    _lastHoverKey = null;
  });
}

export function hideTipPopup() {
  const node = el();
  if (node) node.hidden = true;
  _lastPt = null;
  _lastCellKey = null;
  _rafPending = false;
  // 不清 cell 高亮：cell:selected（点击）时卡片隐但柱体保持升起，仅 mouseleave 缩回
}

// ── Cell hover highlight（网格/柱体悬停：3D 顶圈发光 + 2D 亮粗描边）──
// 叠加层路线（复用 map.js showHoverRing 模式），cell 切换才重敷（_lastHoverKey 防抖）。
function showCellHover(feature, ui, layer) {
  if (!_map || !feature || !feature.geometry) return;
  const SRC = 'cell-hover', LAYER = 'cell-hover-layer';
  if (_map.getLayer(LAYER)) _map.removeLayer(LAYER);
  if (_map.getSource(SRC)) _map.removeSource(SRC);
  // 保留 properties → 3D overlay 用与格层同款 color 表达式（修变色 bug：rampColor 均匀间距 ≠ MapLibre interpolate 实际 stop 位）
  _map.addSource(SRC, { type: 'geojson', data: { type: 'Feature', geometry: feature.geometry, properties: feature.properties || {} } });
  if (ui && ui.mode === '3d') {
    // 3D：整柱 overlay（同色不透明=柱本身），高度 cellH → 2×cellH native transition 升起动画。
    // 高度基准读 LIVE layer.paint._ui（要素按钮调拉伸后 grid-tool 整体替换 editLyr.paint._ui，
    // bindTipPopup 闭包 ui 已过时→曾用旧 maxHeight 致升高比例错。color 同理读 layer.paint live）。
    const liveUi = (layer && layer.paint && layer.paint._ui) || ui || {};
    const hf = liveUi.heightField || '_level';
    const base = Number((feature.properties || {})[hf]) || 0;
    const cellH = base * (liveUi.maxHeight || 1000);
    // 与格层 _gridColorExpr 同款 color 表达式（保证升起柱色 = 原柱色，不变色——承重 note 6）
    const stops = (layer && layer.paint && Array.isArray(layer.paint.gridStops)) ? layer.paint.gridStops : [];
    const field = (layer && layer.paint && layer.paint.gridField) || '_grid_norm';
    const stopArgs = [];
    for (const [d, c] of stops) stopArgs.push(d, c);
    const colorExpr = stopArgs.length ? ['interpolate', ['linear'], ['get', field], ...stopArgs] : '#4285F4';
    _map.addLayer({ id: LAYER, type: 'fill-extrusion', source: SRC,
      paint: {
        'fill-extrusion-color': colorExpr,
        'fill-extrusion-base': 0,
        'fill-extrusion-height': cellH,
        'fill-extrusion-height-transition': { duration: 350, delay: 0 },
        'fill-extrusion-opacity': liveUi.extrusionOpacity ?? 0.9,   // 与格层同透明度（默认 0.9），避免悬停柱突兀
      } });
    // 下一帧触发升高 → transition 动画到 2×（整柱拔高突出显示）
    const target = Math.max(cellH * 2, cellH + 60);
    requestAnimationFrame(() => { if (_map.getLayer(LAYER)) _map.setPaintProperty(LAYER, 'fill-extrusion-height', target); });
  } else {
    _map.addLayer({ id: LAYER, type: 'line', source: SRC,
      paint: { 'line-color': '#4285F4', 'line-width': 3, 'line-opacity': 0.95 } });
  }
}
function clearCellHover() {
  if (!_map) return;
  const SRC = 'cell-hover', LAYER = 'cell-hover-layer';
  if (_map.getLayer(LAYER)) _map.removeLayer(LAYER);
  if (_map.getSource(SRC)) _map.removeSource(SRC);
}
/** cell 悬停高亮防抖：同格不重敷（_lastHoverKey）；point 层不高亮（走 point hover-ring）。 */
function maybeCellHover(feat, ui, layer) {
  if (ui.tool !== 'grid' && ui.tool !== 'terrain') return;
  const c = centroidOf(feat);
  const key = c ? c[0].toFixed(5) + ',' + c[1].toFixed(5) : null;
  if (key === _lastHoverKey) return;
  _lastHoverKey = key;
  showCellHover(feat, ui, layer);
}

// ── 内容 ────────────────────────────────────────────────────────────────────
function showEl() {
  const node = el();
  if (node) node.hidden = false;
}

/** 4 行：地点(异步,纯文本) / 极性判断(cell 有 polarity_index 时,同步) / 口径(同步,HTML) / 边长(同步,HTML) */
function fillContent(feat, ui) {
  const p = (feat.properties || {});
  document.getElementById('tp-metric').innerHTML = metricText(p, ui);
  document.getElementById('tp-size').innerHTML = sizeText(p, ui);

  // 极性判断 / 治理要素行：L2 极性网格(积极/消极/中性)→显 4×5 治理要素（图层已明示极性，不需"极性判断"）；
  // 综合/L1→极性判断(valenceOf 词，valenceColorOf 色，与 cell-popup 同源)
  const valEl = document.getElementById('tp-valence');
  if (valEl) {
    let label, body, color, show;
    if (ui.tool === 'grid' && ui.level === 'L2' && ui.polarity && ui.polarity !== 'overall') {
      const dom = DOMAIN_LABEL[p.domain_top] || p.domain_top;
      const elm = ELEMENT_LABEL[p.element_top] || p.element_top;
      label = '治理要素'; body = (dom || '—') + '·' + (elm || '—'); color = ''; show = !!(dom || elm);
    } else {
      show = p.polarity_index != null;
      label = '极性判断'; body = valenceOf(p.polarity_index); color = valenceColorOf(p.polarity_index);
    }
    valEl.style.display = show ? '' : 'none';
    valEl.innerHTML = show ? `<i class="tp-vk">${label}</i><b class="tp-vv" style="color:${color}">${body}</b>` : '';
  }

  // point：点位用同步属性（点多不宜逐点 geocode）；cell 走异步质心反查
  if (ui.kind === 'point') {
    _lastCellKey = null;
    const z = (p.zone_name && p.zone_name !== '通用市区') ? p.zone_name : '';
    document.getElementById('tp-loc').textContent = z || p.area || p.area_seed || '—';
    return;
  }

  // 地点：按质心 key 去重——同格只发一次 reverseGeocode（cache/inflight），切格才发新
  const c = centroidOf(feat);
  const key = c ? `${c[0].toFixed(5)},${c[1].toFixed(5)}` : null;
  if (key === _lastCellKey) return;        // 同格：地点已填/在填，不重发
  _lastCellKey = key;
  const locEl = document.getElementById('tp-loc');
  if (!key) { locEl.textContent = '—'; return; }
  const cached = _geoCache.get(key);
  if (cached) { locEl.textContent = _locLine(cached); return; }
  locEl.textContent = '定位中…';
  if (_inflight.has(key)) return;          // 同格已在请求
  _inflight.add(key);
  trackGeocode(reverseGeocode(c[0], c[1])).then((res) => {
    _inflight.delete(key);
    const r = res || {};
    _geoCache.set(key, r);
    if (_geoCache.size > 200) _geoCache.delete(_geoCache.keys().next().value);
    const node = el();
    if (!node || node.hidden || _lastCellKey !== key) return;   // 已隐藏/已切格 → 不回填
    locEl.textContent = _locLine(r);
  }).catch(() => {
    _inflight.delete(key);
    _geoCache.set(key, {});                 // 失败也缓存，避免重复打失败请求
    const node = el();
    if (!node || node.hidden || _lastCellKey !== key) return;
    locEl.textContent = '—';
  });
}

/** point：L2→极性+分数 / L1→热度+强度 / L0→原始（着色同 cell pos/neu/neg） */
function pointMetric(p, ui) {
  const mode = ui.colorMode;
  if (mode === 'needsAnalysis') return `<span class="tp-k">L0</span><b class="tp-v">原始</b>`;
  if (mode === 'confidence') {
    const ei = p.emotion_intensity != null ? Number(p.emotion_intensity).toFixed(1) : '—';
    return `<span class="tp-k">热度</span><b class="tp-v">${ei}</b>`;
  }
  const pol = p.polarity || 'Neutral';
  const label = POLARITY_LABEL[pol] || pol;
  const cls = { 'Very Positive': 'pos', 'Positive': 'pos', 'Neutral': 'neu', 'Negative': 'neg', 'Very Negative': 'neg' }[pol] || 'neu';
  const score = p.score != null ? Number(p.score).toFixed(2) : '—';
  return `<span class="tp-k">${label}</span><b class="tp-v"><i class="tp-i ${cls}">${score}</i></b>`;
}

/** L1→`热度 · {点数}`；L2 综合→`积极/中性/消极 · {pos}/{neu}/{neg}`；L2 极性网格→`{极性}点数 · {n}`（该极性聚合程度） */
function metricText(p, ui) {
  if (ui.kind === 'point') return pointMetric(p, ui);
  const level = ui.level;
  const pc = p.point_count ?? 0;
  if (level === 'L1') {
    return `<span class="tp-k">热度</span><b class="tp-v">${pc}</b>`;
  }
  // L2 极性网格（积极/中性/消极）：显该极性点数（=该极性聚合程度，与柱体高度/颜色同源）
  if (ui.polarity && ui.polarity !== 'overall') {
    const nField = { positive: '_grid_n_pos', negative: '_grid_n_neg', neutral: '_grid_n_neu' }[ui.polarity];
    return `<span class="tp-k">${POLARITY_LABEL[ui.polarity] || ''}点数</span><b class="tp-v">${p[nField] || 0}</b>`;
  }
  // L2 综合：三分计数（子值着色）
  const pos = (p.n_positive || 0) + (p.n_very_positive || 0);
  const neu = p.n_neutral || 0;
  const neg = (p.n_negative || 0) + (p.n_very_negative || 0);
  return `<span class="tp-k">积极/中性/消极</span>` +
    `<b class="tp-v"><i class="tp-i pos">${pos}</i>/<i class="tp-i neu">${neu}</i>/<i class="tp-i neg">${neg}</i></b>`;
}

/** point：domain×element（4×5 治理要素，与聚合层一致）；缺则退 primary_emotion */
function pointSize(p) {
  if (p.domain && p.element) {
    return `<span class="tp-k">${DOMAIN_LABEL[p.domain] || p.domain}</span><b class="tp-v">${ELEMENT_LABEL[p.element] || p.element}</b>`;
  }
  if (p.primary_emotion) return `<span class="tp-k">情绪</span><b class="tp-v">${p.primary_emotion}</b>`;
  return `<span class="tp-k">点位</span><b class="tp-v">·</b>`;
}

/** grid→`{cell}×{cell}m`；terrain→`等值环 L{_level}` */
function sizeText(p, ui) {
  if (ui.kind === 'point') return pointSize(p);
  if (ui.tool === 'terrain') {
    const lvl = p._level != null ? Number(p._level).toFixed(2) : '—';
    return `<span class="tp-k">等值环</span><b class="tp-v">L${lvl}</b>`;
  }
  const cs = ui.cellSize;
  return `<span class="tp-k">网格边长</span><b class="tp-v">${cs ? `${cs}×${cs}m` : '—'}</b>`;
}

/** 质心：grid 用预计算 _center（须为数组，经 GeoJSON 中转可能序列化为字符串→回退）；terrain 用 bbox 中心 */
function centroidOf(feat) {
  const p = feat.properties || {};
  if (Array.isArray(p._center) && p._center.length === 2) return p._center;
  const g = feat.geometry;
  if (!g || !g.coordinates) return null;
  let minLng = Infinity, maxLng = -Infinity, minLat = Infinity, maxLat = -Infinity;
  const walk = (arr) => {
    if (typeof arr[0] === 'number') {
      const lng = arr[0], lat = arr[1];
      if (lng < minLng) minLng = lng; if (lng > maxLng) maxLng = lng;
      if (lat < minLat) minLat = lat; if (lat > maxLat) maxLat = lat;
    } else { for (const a of arr) walk(a); }
  };
  walk(g.coordinates);
  if (!isFinite(minLng)) return null;
  return [(minLng + maxLng) / 2, (minLat + maxLat) / 2];
}

// ── 自适应方位 + 灵动跳动 ────────────────────────────────────────────────────
function schedulePos() {
  if (_rafPending || !_lastPt) return;
  _rafPending = true;
  requestAnimationFrame(positionCard);
}

function positionCard() {
  _rafPending = false;
  const node = el();
  if (!node || node.hidden || !_lastPt) return;
  const vw = window.innerWidth, vh = window.innerHeight;
  const ch = node.offsetHeight || CH;   // 实际高度（地点换行自适应后可能 >120）
  const { x: cx, y: cy } = _lastPt;

  // 水平象限：默认右侧；右沿放不下 → 左侧；中段保持现侧（hysteresis）
  let left;
  const fitRight = cx + GAP + CW <= vw - 8;
  const fitLeft = cx - GAP - CW >= 8;
  if (_sideH === 'right' && fitRight) left = cx + GAP;
  else if (_sideH === 'left' && fitLeft) left = cx - GAP - CW;
  else if (fitRight) { _sideH = 'right'; left = cx + GAP; }
  else if (fitLeft) { _sideH = 'left'; left = cx - GAP - CW; }
  else left = vw - CW - 8;

  // 垂直象限：默认下方；下沿放不下 → 上方；中段保持（用实际高度 ch）
  let top;
  const fitBelow = cy + GAP + ch <= vh - 8;
  const fitAbove = cy - GAP - ch >= 8;
  if (_sideV === 'below' && fitBelow) top = cy + GAP;
  else if (_sideV === 'above' && fitAbove) top = cy - GAP - ch;
  else if (fitBelow) { _sideV = 'below'; top = cy + GAP; }
  else if (fitAbove) { _sideV = 'above'; top = cy - GAP - ch; }
  else top = vh - ch - 8;

  left = clamp(left, 8, Math.max(8, vw - CW - 8));
  top = clamp(top, 8, Math.max(8, vh - ch - 8));

  // hysteresis：位移小于阈值 → 保持（"不死绑定"，灵动锚定）
  const dx = Math.abs(left - _lastPos.left);
  const dy = Math.abs(top - _lastPos.top);
  if (_lastPos.left >= 0 && dx < HYSTERESIS && dy < HYSTERESIS) return;

  _lastPos = { left, top };
  node.style.left = `${Math.round(left)}px`;
  node.style.top = `${Math.round(top)}px`;
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
