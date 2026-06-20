// ═══ popup.js — top-right popup stack: emotion point + range polygon ═══
// Two cards stacked in #popup-stack (anchored top-right of #map):
//   • #feature-popup — clicked emotion point (L2 polarity badge | L1 置信度 badge)
//   • #range-popup   — clicked range polygon (navy accent = outline color)
// Each independently expand/collapse (capsule) + close. Click empty map → collapse both.
import { POLARITY_LABEL, rampColor, CONFIDENCE_RAMP, getLayer } from './state.js';

const emoEl = () => document.getElementById('feature-popup');
const rngEl = () => document.getElementById('range-popup');
let _emo = null;          // { colorMode, label?, score?, scoreText? }
let _rng = null;          // { name, color }
let _popupLayerId = null; // layer id of the feature shown in the emotion popup (for color sync)
let _rngLayerId = null;   // layer id of the feature shown in the range popup

const GREY = '#a3a3a3';

/** Resolve the registry layer a queried feature came from (MapLibre sets feature.source). */
function layerFromFeature(f) {
  const s = f && f.source;
  if (!s || typeof s !== 'string' || !s.startsWith('lyr-')) return null;
  return getLayer(s.replace('lyr-', ''));
}

// ── Emotion point popup ────────────────────────────────────────────────────
export function showPopup(feature, colors, colorMode) {
  const p = feature.properties || {};
  const popup = emoEl();
  popup.hidden = false;
  popup.classList.remove('is-collapsed');

  const layer = layerFromFeature(feature);
  _popupLayerId = layer ? layer.id : null;
  const badge = document.getElementById('pp-polarity');
  const scoreEl = document.getElementById('pp-score');

  if (colorMode === 'needsAnalysis') {        // L0: raw — grey capsule, NO polarity/score written
    badge.textContent = '';
    badge.style.background = GREY;
    scoreEl.hidden = true;
    _emo = { colorMode: 'needsAnalysis' };
  } else if (colorMode === 'confidence') {    // L1: confidence badge, color from the layer's ramp
    const score = (typeof p.score === 'number') ? p.score : 0.5;
    const ramp = (layer && layer.paint && layer.paint.ramp) || CONFIDENCE_RAMP;
    badge.textContent = '置信度';
    badge.style.background = rampColor(ramp, score);
    scoreEl.hidden = false;
    scoreEl.textContent = score.toFixed(1);
    _emo = { colorMode: 'confidence', label: '置信度', score };
  } else {                                    // L2: polarity badge (frozen rendering)
    const pol = p.polarity || 'Neutral';
    const label = POLARITY_LABEL[pol] || pol;
    const scoreText = (p.score ?? 0).toFixed(2);
    badge.textContent = label;
    badge.style.background = (colors && colors[pol]) || '#999';
    scoreEl.hidden = false;
    scoreEl.textContent = scoreText;
    _emo = { colorMode: 'polarity', label, scoreText };
  }

  const textEl = document.getElementById('pp-text');
  textEl.textContent = p.text || '';
  textEl.title = p.text || '';

  const rows = [];
  if (p.location) rows.push(['位置', p.location]);
  if (p.category) rows.push(['类别', p.category]);
  if (p.emotion_type) rows.push(['情绪类型', p.emotion_type]);
  if (p.emotion_intensity != null) rows.push(['情绪强度', Number(p.emotion_intensity).toFixed(2)]);
  if (Array.isArray(p.keywords) && p.keywords.length) rows.push(['关键词', p.keywords.join('、')]);
  const c = feature.geometry && feature.geometry.coordinates;
  if (c) rows.push(['坐标', Array.isArray(c[0]) ? feature.geometry.type : `${c[1].toFixed(4)}, ${c[0].toFixed(4)}`]);
  document.getElementById('pp-kv').innerHTML = rows.map(([k, v]) =>
    `<div class="kv-row"><span class="kv-k">${k}</span><span class="kv-v">${v}</span></div>`).join('');

  document.getElementById('pp-id').textContent = p.id_e ? `ID ${p.id_e}` : '';
}

export function collapsePopup() {
  const popup = emoEl();
  if (!popup || popup.hidden || !_emo) return;
  // L0 stays a grey empty capsule; L1 shows score, L2 shows scoreText.
  if (_emo.colorMode === 'confidence') document.getElementById('pp-polarity').textContent = _emo.score.toFixed(1);
  else if (_emo.colorMode === 'polarity') document.getElementById('pp-polarity').textContent = _emo.scoreText;
  // needsAnalysis: badge already empty grey — leave as-is
  popup.classList.add('is-collapsed');
}
export function expandPopup() {
  const popup = emoEl();
  if (!popup || popup.hidden || !_emo) return;
  if (_emo.label != null) document.getElementById('pp-polarity').textContent = _emo.label;
  popup.classList.remove('is-collapsed');
}
export function hidePopup() { _popupLayerId = null; const p = emoEl(); if (p) p.hidden = true; }

// ── Range polygon popup ────────────────────────────────────────────────────
// Layout mirrors the emotion popup: badge (de-emphasized "范围") on top, then
// the NAME as a 2nd-tier "comment" line, then kv stats. Collapsed → bold "Range"
// capsule the same size as the emotion popup's capsule.
export function showRangePopup(feature, layer) {
  const popup = rngEl();
  if (!popup) return;
  popup.hidden = false;
  popup.classList.remove('is-collapsed');

  const color = (layer && layer.paint && layer.paint.color) || '#0c1c2e';
  const name = (layer && layer.name) || (feature.properties && feature.properties.name) || '范围';
  const { area, perimeter, type, vertices, bbox } = geomStats(feature.geometry);

  const badge = document.getElementById('rp-badge');
  badge.textContent = '范围';
  badge.style.background = color;
  // 注：不再给范围 popup 设 accent border —— f9da7c1 引入的实色 navy 轮廓会让看板
  // 出现突兀边框（用户反馈"突然出现的轮廓线框"）。范围 popup 仅靠 box-shadow + badge 区分。
  const nameEl = document.getElementById('rp-name');
  nameEl.textContent = name;
  nameEl.title = name;

  const rows = [
    ['面积', area != null ? `${area.toFixed(3)} km²` : '—'],
    ['周长', perimeter != null ? `${perimeter.toFixed(3)} km` : '—'],
    ['类型', type || '—'],
    ['顶点', vertices != null ? String(vertices) : '—'],
    ['bbox', bbox || '—'],
  ];
  document.getElementById('rp-kv').innerHTML = rows.map(([k, v]) =>
    `<div class="kv-row"><span class="kv-k">${k}</span><span class="kv-v">${v}</span></div>`).join('');

  _rng = { name, color };
  _rngLayerId = layer ? layer.id : null;
}

export function collapseRangePopup() {
  const popup = rngEl();
  if (!popup || popup.hidden || !_rng) return;
  document.getElementById('rp-badge').textContent = 'Range';   // bold English capsule
  popup.classList.add('is-collapsed');
}
export function expandRangePopup() {
  const popup = rngEl();
  if (!popup || popup.hidden || !_rng) return;
  document.getElementById('rp-badge').textContent = '范围';
  popup.classList.remove('is-collapsed');
}
export function hideRangePopup() { _rngLayerId = null; const p = rngEl(); if (p) p.hidden = true; }

/** Live-sync: when a layer's color/ramp changes via the settings popover, refresh
 *  the open popup's capsule color if it belongs to that layer. */
export function refreshPopupForLayer(id) {
  if (!id) return;
  const layer = getLayer(id);
  if (!layer) return;
  const e = emoEl();
  if (_popupLayerId === id && _emo && e && !e.hidden && _emo.colorMode === 'confidence') {
    const ramp = (layer.paint && layer.paint.ramp) || CONFIDENCE_RAMP;
    document.getElementById('pp-polarity').style.background = rampColor(ramp, _emo.score);
  }
  const r = rngEl();
  if (_rngLayerId === id && _rng && r && !r.hidden) {
    const color = (layer.paint && layer.paint.color) || '#0c1c2e';
    document.getElementById('rp-badge').style.background = color;
    // accent border 同上移除（避免突兀轮廓）
    _rng.color = color;
  }
}

// ── Init: close/expand/collapse wiring ─────────────────────────────────────
export function initPopup(map) {
  const e = emoEl(), r = rngEl();
  document.getElementById('popup-close')?.addEventListener('click', hidePopup);
  document.getElementById('range-close')?.addEventListener('click', hideRangePopup);
  e?.addEventListener('click', () => { if (e.classList.contains('is-collapsed')) expandPopup(); });
  r?.addEventListener('click', () => { if (r.classList.contains('is-collapsed')) expandRangePopup(); });
  if (map) {
    map.on('click', (ev) => {
      const tgt = ev.originalEvent && ev.originalEvent.target;
      if (tgt && tgt.closest && (tgt.closest('#feature-popup') || tgt.closest('#range-popup'))) return;
      // bug fix：原判定 feats.length===0 才折叠，但热力图层覆盖大片像素，点哪都命中 feature
      // → 永不折叠。改为只看"可交互要素"（点/面/符号），排除 heatmap/raster 等背景层。
      const feats = map.queryRenderedFeatures(ev.point);
      const interactive = (feats || []).some((f) => {
        const t = f.layer && f.layer.type;
        return t === 'circle' || t === 'fill' || t === 'symbol' || t === 'line';
      });
      if (!interactive) { collapsePopup(); collapseRangePopup(); }
    });
  }
}

// ── Geometry stats (spherical area + haversine perimeter; no turf dep) ──────
const rad = (d) => d * Math.PI / 180;
export function geomStats(geom) {
  if (!geom || !geom.coordinates) return {};
  const rings = collectRings(geom);
  let area = 0, perimeter = 0, vertices = 0;
  const b = [Infinity, Infinity, -Infinity, -Infinity];
  for (const ring of rings) {
    vertices += ring.length;
    if (geom.type === 'Polygon' || geom.type === 'MultiPolygon') area += Math.abs(sphericalArea(ring));
    perimeter += ringLength(ring);
    for (const [x, y] of ring) { if (x < b[0]) b[0] = x; if (y < b[1]) b[1] = y; if (x > b[2]) b[2] = x; if (y > b[3]) b[3] = y; }
  }
  const bbox = (Number.isFinite(b[0]))
    ? `${b[0].toFixed(3)}, ${b[1].toFixed(3)} → ${b[2].toFixed(3)}, ${b[3].toFixed(3)}`
    : null;
  return { area: area / 1e6, perimeter: perimeter / 1000, type: geom.type, vertices, bbox };
}
function collectRings(geom) {
  const t = geom.type, c = geom.coordinates;
  if (t === 'LineString') return [c];
  if (t === 'MultiLineString') return c;
  if (t === 'Polygon') return c;
  if (t === 'MultiPolygon') return c.flat();
  if (t === 'Point' || t === 'MultiPoint') return [];
  return [];
}
function sphericalArea(ring) {
  const R = 6378137;
  let area = 0;
  const n = ring.length;
  if (n < 3) return 0;
  for (let i = 0; i < n; i++) {
    const [x1, y1] = ring[i];
    const [x2, y2] = ring[(i + 1) % n];
    area += rad(x2 - x1) * (2 + Math.sin(rad(y1)) + Math.sin(rad(y2)));
  }
  return (area * R * R) / 2;
}
function ringLength(ring) {
  let d = 0;
  for (let i = 1; i < ring.length; i++) d += haversine(ring[i - 1], ring[i]);
  return d;
}
function haversine(a, b) {
  const R = 6378137;
  const dLat = rad(b[1] - a[1]), dLon = rad(b[0] - a[0]);
  const s = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a[1])) * Math.cos(rad(b[1])) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(s)));
}
