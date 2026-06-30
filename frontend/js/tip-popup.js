// ═══ tip-popup.js — 网格/柱体/地形环 悬停浮动卡（统一悬停设计语言） ═══
// 单一 #tip-popup（position:fixed, 150×150, 白底, radius 4px, 高阴影），随鼠标灵动跳动。
// 自适应方位：依指针在视口的位置选左/右/上/下，目的=不遮挡主体。
// 灵动算法：hysteresis（位移超阈值才换位）+ 象限翻转 + CSS transition 顺滑滑动。
// 反查防抖：质心 key 缓存 + inflight 去重（同格只发一次 reverseGeocode），切格不重复发。
// 替换 tool 层（grid/terrain）原生 dark tooltip；point/range 本轮不动，模块可后续扩展。
import { reverseGeocode } from './api.js';

let _map = null;
const _bound = new Set();          // 已绑定的 maplibre layer id（幂等）
const CW = 150, CH = 150, GAP = 16; // 卡片尺寸 + 与指针间距
const HYSTERESIS = 14;             // 位移阈值（px）：超过才更新位置，否则保持（"不死绑定"）
let _sideH = 'right', _sideV = 'below'; // 当前象限记忆（hysteresis 防抖）
let _rafPending = false;
let _lastPt = null;                // 最近指针 viewport 坐标 { x, y }
let _lastPos = { left: -999, top: -999 }; // 当前落位（判断位移阈值）
const _geoCache = new Map();       // key=`lng,lat` → { zone_name, nearest_poi }
const _inflight = new Set();       // 正在请求的 key（防同格重复发）
let _lastCellKey = null;           // 当前显示的格质心 key（同格不重发反查）

const el = () => document.getElementById('tip-popup');

export function initTipPopup(map) {
  _map = map;
  document.addEventListener('cell:selected', hideTipPopup);   // 点击出持久卡时隐藏浮动卡
  document.addEventListener('layers:changed', hideTipPopup);
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
export function bindTipPopup(layer, lid) {
  if (!_map || !layer || !lid || _bound.has(lid)) return;
  _bound.add(lid);
  const ui = (layer.paint && layer.paint._ui) || {};

  const onEnter = (e) => {
    _map.getCanvas().classList.add('is-pointer');
    const f = e.features && e.features[0];
    if (!f) return;
    _lastPt = evtClientPt(e);
    fillContent(f, ui);
    showEl();
    if (_lastPt) positionCard();   // mouseenter 即定位，防首帧停在左上角
  };
  const onMove = (e) => {
    const f = e.features && e.features[0];
    if (!f) return;
    _lastPt = evtClientPt(e);
    fillContent(f, ui);
    showEl();          // mousemove 也确保显示（mouseenter 可能因鼠标已在层内未触发）
    schedulePos();
  };
  _map.on('mouseenter', lid, onEnter);
  _map.on('mousemove', lid, onMove);
  _map.on('mouseleave', lid, () => {
    _map.getCanvas().classList.remove('is-pointer');
    hideTipPopup();
  });
}

export function hideTipPopup() {
  const node = el();
  if (node) node.hidden = true;
  _lastPt = null;
  _lastCellKey = null;
  _rafPending = false;
}

// ── 内容 ────────────────────────────────────────────────────────────────────
function showEl() {
  const node = el();
  if (node) node.hidden = false;
}

/** 3 行：地点(异步,纯文本) / 口径(同步,HTML) / 边长(同步,HTML) */
function fillContent(feat, ui) {
  const p = (feat.properties || {});
  document.getElementById('tp-metric').innerHTML = metricText(p, ui);
  document.getElementById('tp-size').innerHTML = sizeText(p, ui);

  // 地点：按质心 key 去重——同格只发一次 reverseGeocode（cache/inflight），切格才发新
  const c = centroidOf(feat);
  const key = c ? `${c[0].toFixed(5)},${c[1].toFixed(5)}` : null;
  if (key === _lastCellKey) return;        // 同格：地点已填/在填，不重发
  _lastCellKey = key;
  const locEl = document.getElementById('tp-loc');
  if (!key) { locEl.textContent = '—'; return; }
  const cached = _geoCache.get(key);
  if (cached) { locEl.textContent = locText(cached); return; }
  locEl.textContent = '定位中…';
  if (_inflight.has(key)) return;          // 同格已在请求
  _inflight.add(key);
  reverseGeocode(c[0], c[1]).then((res) => {
    _inflight.delete(key);
    const r = res || {};
    _geoCache.set(key, r);
    if (_geoCache.size > 200) _geoCache.delete(_geoCache.keys().next().value);
    const node = el();
    if (!node || node.hidden || _lastCellKey !== key) return;   // 已隐藏/已切格 → 不回填
    locEl.textContent = locText(r);
  }).catch(() => {
    _inflight.delete(key);
    _geoCache.set(key, {});                 // 失败也缓存，避免重复打失败请求
    const node = el();
    if (!node || node.hidden || _lastCellKey !== key) return;
    locEl.textContent = '—';
  });
}

/** L1→`热度 · {点数}`；L2→`积极/中性/消极 · {pos}/{neu}/{neg}`（子值 HTML 着色） */
function metricText(p, ui) {
  const level = ui.level;
  const pc = p.point_count ?? 0;
  if (level === 'L1') {
    return `<span class="tp-k">热度</span><b class="tp-v">${pc}</b>`;
  }
  const pos = (p.n_positive || 0) + (p.n_very_positive || 0);
  const neu = p.n_neutral || 0;
  const neg = (p.n_negative || 0) + (p.n_very_negative || 0);
  return `<span class="tp-k">积极/中性/消极</span>` +
    `<b class="tp-v"><i class="tp-i pos">${pos}</i>/<i class="tp-i neu">${neu}</i>/<i class="tp-i neg">${neg}</i></b>`;
}

/** grid→`{cell}×{cell}m`；terrain→`等值环 L{_level}` */
function sizeText(p, ui) {
  if (ui.tool === 'terrain') {
    const lvl = p._level != null ? Number(p._level).toFixed(2) : '—';
    return `<span class="tp-k">等值环</span><b class="tp-v">L${lvl}</b>`;
  }
  const cs = ui.cellSize;
  return `<span class="tp-k">网格边长</span><b class="tp-v">${cs ? `${cs}×${cs}m` : '—'}</b>`;
}

function locText(r) {
  const parts = [];
  if (r.zone_name) parts.push(r.zone_name);
  if (r.nearest_poi && r.nearest_poi.name) parts.push(r.nearest_poi.name);
  return parts.length ? parts.join('·') : '—';
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

  // 垂直象限：默认下方；下沿放不下 → 上方；中段保持
  let top;
  const fitBelow = cy + GAP + CH <= vh - 8;
  const fitAbove = cy - GAP - CH >= 8;
  if (_sideV === 'below' && fitBelow) top = cy + GAP;
  else if (_sideV === 'above' && fitAbove) top = cy - GAP - CH;
  else if (fitBelow) { _sideV = 'below'; top = cy + GAP; }
  else if (fitAbove) { _sideV = 'above'; top = cy - GAP - CH; }
  else top = vh - CH - 8;

  left = clamp(left, 8, Math.max(8, vw - CW - 8));
  top = clamp(top, 8, Math.max(8, vh - CH - 8));

  // hysteresis：位移小于阈值 → 保持（"不死绑定"，灵动锚定）
  const dx = Math.abs(left - _lastPos.left);
  const dy = Math.abs(top - _lastPos.top);
  if (_lastPos.left >= 0 && dx < HYSTERESIS && dy < HYSTERESIS) return;

  _lastPos = { left, top };
  node.style.left = `${Math.round(left)}px`;
  node.style.top = `${Math.round(top)}px`;
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
