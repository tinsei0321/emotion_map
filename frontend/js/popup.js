// ═══ popup.js — top-right popup stack: emotion point + range polygon ═══
// Two cards stacked in #popup-stack (anchored top-right of #map):
//   • #feature-popup — clicked emotion point (L2 polarity badge | L1 置信度 badge)
//   • #range-popup   — clicked range polygon (navy accent = outline color)
// Each independently expand/collapse (capsule) + close. Click empty map → collapse both.
import { POLARITY_LABEL, rampColor, CONFIDENCE_RAMP, getLayer, computeHotness, hotnessColor, isDrawActive } from './state.js';

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
  } else if (colorMode === 'confidence') {    // L1: 热度值 = 情绪强度 × 置信度（3 段色）
    const hotness = computeHotness(feature);
    const buckets = (layer && layer.paint && layer.paint.hotnessBuckets) || [0.33, 0.66];
    badge.textContent = '热度值';
    badge.title = '热度值 = 情绪强度 × 置信度（0~1）。情绪越浓且与城市规划相关性越高，热度值越大；按当前图层分布动态分 3 段（浅橙→橙→深橙红）。';
    badge.style.background = hotnessColor(buckets, hotness);
    scoreEl.hidden = false;
    scoreEl.textContent = hotness.toFixed(2);
    _emo = { colorMode: 'confidence', label: '热度值', score: hotness };
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

  // rows = [key, value, tip?, dim?] —— tip 挂 kv-k 的 title；dim 弱化（坐标同 ID 级小字灰）
  const rows = [];
  if (p.location) rows.push(['位置', p.location]);
  if (p.category) rows.push(['类别', p.category]);
  if (p.emotion_type) rows.push(['情绪类型', p.emotion_type]);
  if (p.emotion_intensity != null) rows.push(['情绪强度', Number(p.emotion_intensity).toFixed(2)]);
  if (p.l1_confidence != null) rows.push(['置信度', Number(p.l1_confidence).toFixed(2),
    'L1 治理阶段由 LLM（DeepSeek）判断的数据相关性置信度（0~1）：该条数据与城市规划情绪分析的相关程度。可收集、可复现。']);
  if (Array.isArray(p.keywords) && p.keywords.length) rows.push(['关键词', p.keywords.join('、')]);
  const c = feature.geometry && feature.geometry.coordinates;
  if (c) rows.push(['坐标', Array.isArray(c[0]) ? feature.geometry.type : `${c[1].toFixed(4)}, ${c[0].toFixed(4)}`, '', 'dim']);
  document.getElementById('pp-kv').innerHTML = rows.map(([k, v, tip, dim]) =>
    `<div class="kv-row${dim ? ' kv-dim' : ''}"><span class="kv-k"${tip ? ` title="${tip}"` : ''}>${k}</span><span class="kv-v">${v}</span></div>`).join('');

  document.getElementById('pp-id').textContent = p.id_e ? `ID ${p.id_e}` : '';
}

export function collapsePopup() {
  const popup = emoEl();
  if (!popup || popup.hidden || !_emo) return;
  // L0 stays a grey empty capsule; L1 shows hotness, L2 shows scoreText.
  if (_emo.colorMode === 'confidence') document.getElementById('pp-polarity').textContent = _emo.score.toFixed(2);
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
  const isBuffer = !!(layer && layer.paint && layer.paint._ui && layer.paint._ui.tool === 'buffer');
  popup.classList.toggle('is-buffer', isBuffer);   // CSS：收起胶囊距离（非大写、稍小字号）
  const ui = (layer && layer.paint && layer.paint._ui) || {};
  const distLabel = ui.distance != null ? `${ui.distance} m` : '';

  const badge = document.getElementById('rp-badge');
  const distEl = document.getElementById('rp-distance');
  badge.style.background = color;
  const nameEl = document.getElementById('rp-name');
  const { type } = geomStats(feature.geometry);

  if (isBuffer) {
    // 缓冲：badge「缓冲」+ 右侧距离 + 灰色文件名 + 仅「类型」行
    badge.textContent = '缓冲';
    if (distEl) { distEl.textContent = distLabel; distEl.hidden = !distLabel; }
    const fname = (layer && (layer.srcName || layer.name)) || '缓冲';
    nameEl.textContent = fname; nameEl.title = fname;
    document.getElementById('rp-kv').innerHTML =
      `<div class="kv-row"><span class="kv-k">类型</span><span class="kv-v">${type || '—'}</span></div>`;
    _rng = { name: fname, color, isBuffer: true, distance: distLabel };
  } else {
    // 范围：badge 依来源（绘制→形状「多边形/矩形」；上载→「上载」）+ 名称 + 面积/周长/类型
    const drawn = ui.tool === 'draw';
    const badgeText = drawn ? (ui.shape || '多边形') : '上载';
    badge.textContent = badgeText;
    if (distEl) distEl.hidden = true;
    const { area, perimeter } = geomStats(feature.geometry);
    const name = (layer && layer.name) || (feature.properties && feature.properties.name) || '范围';
    nameEl.textContent = name; nameEl.title = name;
    const rows = [
      ['面积', area != null ? `${area.toFixed(3)} km²` : '—'],
      ['周长', perimeter != null ? `${perimeter.toFixed(3)} km` : '—'],
      ['类型', type || '—'],
    ];
    document.getElementById('rp-kv').innerHTML = rows.map(([k, v]) =>
      `<div class="kv-row"><span class="kv-k">${k}</span><span class="kv-v">${v}</span></div>`).join('');
    _rng = { name, color, isBuffer: false, expandedText: badgeText, area };
  }
  _rngLayerId = layer ? layer.id : null;
}

export function collapseRangePopup() {
  const popup = rngEl();
  if (!popup || popup.hidden || !_rng) return;
  // 缓冲：收起胶囊显示距离；范围：收起胶囊显示面积（2 位小数 + km²）
  const badge = document.getElementById('rp-badge');
  badge.textContent = _rng.isBuffer
    ? (_rng.distance || '缓冲')
    : (_rng.area != null ? `${_rng.area.toFixed(2)} km²` : (_rng.expandedText || '范围'));
  popup.classList.add('is-collapsed');
}
export function expandRangePopup() {
  const popup = rngEl();
  if (!popup || popup.hidden || !_rng) return;
  document.getElementById('rp-badge').textContent = _rng.isBuffer ? '缓冲' : (_rng.expandedText || '范围');
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

// ── Click classification (single source of truth for popup open/collapse) ──
// 透明 hit 带（lyr-{id}-hit，宽 HIT_WIDTH、opacity 0，为好点细轮廓）单独成类：
//   popup 展开时点 hit 带（用户感知"轮廓以外"）= 收起；popup 关着时点 hit 带 = 开（易命中）。
//   可见轮廓（fill/line 非 -hit，2px）= 始终保持/刷新。一处判定驱动两个 popup，杜绝同质 bug。
function classifyMapClick(feats, ev) {
  const tgt = ev.originalEvent && ev.originalEvent.target;
  if (tgt && tgt.closest && (tgt.closest('#feature-popup') || tgt.closest('#range-popup'))) return 'popup';
  // 只认本项目数据层（id 以 lyr- 开头），排除底图 fill/line/circle（landcover/water/road…）——
  // 否则点底图水面/土地利用也会被当成"点中范围/点"，误开 popup（原 hitRange 逻辑的同质漏网）。
  const ours = feats.filter((f) => f.layer && String(f.layer.id).startsWith('lyr-'));
  if (ours.some((f) => f.layer.type === 'circle')) return 'point';
  if (ours.some((f) => (f.layer.type === 'fill' || f.layer.type === 'line') && !String(f.layer.id).endsWith('-hit'))) return 'range-visible';
  if (ours.some((f) => String(f.layer.id).endsWith('-hit'))) return 'range-hitband';
  return 'blank';
}
function isRangePopupExpanded() {
  const p = rngEl();
  return !!p && !p.hidden && !p.classList.contains('is-collapsed') && !!_rng;
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
      if (isDrawActive()) return;   // 绘制中：click 归 draw-tool，不触发 popup
      const feats = map.queryRenderedFeatures(ev.point) || [];
      const k = classifyMapClick(feats, ev);
      if (k === 'popup') return;
      // 情绪点：非命中即收（开 popup 仍由 map.js 点层 click 负责）
      if (k !== 'point') collapsePopup();
      // 范围：可见轮廓→保持/刷新；hit 带→未展开则开(易命中)/已展开则收；都没有→收
      if (k === 'range-visible') {
        const f = feats.find((ff) => ff.layer && String(ff.layer.id).startsWith('lyr-') && (ff.layer.type === 'fill' || ff.layer.type === 'line') && !String(ff.layer.id).endsWith('-hit'));
        const layer = f && layerFromFeature(f);
        if (layer) showRangePopup(f, layer);
      } else if (k === 'range-hitband') {
        if (!isRangePopupExpanded()) {
          const f = feats.find((ff) => ff.layer && String(ff.layer.id).startsWith('lyr-') && String(ff.layer.id).endsWith('-hit'));
          const layer = f && layerFromFeature(f);
          if (layer) showRangePopup(f, layer); else collapseRangePopup();
        } else {
          collapseRangePopup();
        }
      } else {
        collapseRangePopup();
      }
    });
  }
  // 图层隐藏/删除时同步隐藏对应 popup：情绪点 popup 跟 _popupLayerId，范围 popup 跟 _rngLayerId。
  // layers:changed 在 setLayerVisible / removeLayer 后由 sidebar/main 触发。
  document.addEventListener('layers:changed', () => {
    if (_popupLayerId) {
      const l = getLayer(_popupLayerId);
      if (!l || !l.visible) hidePopup();          // 点层隐藏/删除 → 情绪点 popup 消失
    }
    if (_rngLayerId) {
      const l = getLayer(_rngLayerId);
      if (!l || !l.visible) hideRangePopup();     // 面层隐藏/删除 → 范围 popup 消失
    }
  });
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
