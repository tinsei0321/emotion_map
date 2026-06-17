// ═══ popup.js — top-right popup stack: emotion point + range polygon ═══
// Two cards stacked in #popup-stack (anchored top-right of #map):
//   • #feature-popup — clicked emotion point (L2 polarity badge | L1 置信度 badge)
//   • #range-popup   — clicked range polygon (navy accent = outline color)
// Each independently expand/collapse (capsule) + close. Click empty map → collapse both.
import { POLARITY_LABEL, confidenceColor } from './state.js';

const emoEl = () => document.getElementById('feature-popup');
const rngEl = () => document.getElementById('range-popup');
let _emo = null;   // { colorMode, label, score|scoreText }
let _rng = null;   // { name, color }

// ── Emotion point popup ────────────────────────────────────────────────────
export function showPopup(feature, colors, colorMode) {
  const p = feature.properties || {};
  const popup = emoEl();
  popup.hidden = false;
  popup.classList.remove('is-collapsed');

  const badge = document.getElementById('pp-polarity');
  const scoreEl = document.getElementById('pp-score');

  if (colorMode === 'confidence') {           // L1: confidence orange badge
    const score = (typeof p.score === 'number') ? p.score : 0.5;
    badge.textContent = '置信度';
    badge.style.background = confidenceColor(score);
    scoreEl.textContent = score.toFixed(1);
    _emo = { colorMode: 'confidence', label: '置信度', score };
  } else {                                    // L2: polarity badge
    const pol = p.polarity || 'Neutral';
    const label = POLARITY_LABEL[pol] || pol;
    const scoreText = (p.score ?? 0).toFixed(2);
    badge.textContent = label;
    badge.style.background = (colors && colors[pol]) || '#999';
    scoreEl.textContent = scoreText;
    _emo = { colorMode: 'polarity', label, scoreText };
  }

  const textEl = document.getElementById('pp-text');
  textEl.textContent = p.text || '';
  textEl.title = p.text || '';

  const rows = [];
  if (p.location) rows.push(['位置', p.location]);
  if (p.category) rows.push(['类别', p.category]);
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
  document.getElementById('pp-polarity').textContent =
    _emo.colorMode === 'confidence' ? _emo.score.toFixed(1) : _emo.scoreText;
  popup.classList.add('is-collapsed');
}
export function expandPopup() {
  const popup = emoEl();
  if (!popup || popup.hidden || !_emo) return;
  document.getElementById('pp-polarity').textContent = _emo.label;
  popup.classList.remove('is-collapsed');
}
export function hidePopup() { const p = emoEl(); if (p) p.hidden = true; }

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
  popup.style.borderColor = color;            // accent ties to outline color
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
export function hideRangePopup() { const p = rngEl(); if (p) p.hidden = true; }

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
      const feats = map.queryRenderedFeatures(ev.point);
      if (!feats || feats.length === 0) { collapsePopup(); collapseRangePopup(); }
    });
  }
}

// ── Geometry stats (spherical area + haversine perimeter; no turf dep) ──────
const rad = (d) => d * Math.PI / 180;
function geomStats(geom) {
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
