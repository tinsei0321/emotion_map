// ═══ popup.js — top-right popup stack: emotion point + range polygon ═══
// Two cards stacked in #popup-stack (anchored top-right of #map):
//   • #feature-popup — clicked emotion point (L2 polarity badge | L1 置信度 badge)
//   • #range-popup   — clicked range polygon (navy accent = outline color)
// Each independently expand/collapse (capsule) + close. Click empty map → collapse both.
import { POLARITY_LABEL, rampColor, CONFIDENCE_RAMP, getLayer, computeHotness, hotnessColor, isDrawActive, deriveTimeTag, L2_POSITIVE, L2_NEGATIVE, L2_NEUTRAL_COLOR } from './state.js';
import { reverseGeocode } from './api.js';

const emoEl = () => document.getElementById('feature-popup');
const rngEl = () => document.getElementById('range-popup');
let _emo = null;          // { colorMode, label?, score?, scoreText? }
let _popupRevToken = 0;   // 反查 token：切换点时过期旧响应，防串台
let _rng = null;          // { name, color }
let _popupLayerId = null; // layer id of the feature shown in the emotion popup (for color sync)
let _rngLayerId = null;   // layer id of the feature shown in the range popup

const GREY = '#a3a3a3';

// ── 4×5 domain/element 友好标签（cell popup + Overview 共用）──
export const DOMAIN_LABEL = { urban_operation: '城市运营', urban_governance: '城市治理', urban_renewal: '城市更新', urban_planning: '城市规划' };
export const ELEMENT_LABEL = { facility: '设施', environment: '环境', service: '服务', culture: '文化', event: '事件' };

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

  if (colorMode === 'needsAnalysis') {        // L0: raw — grey capsule, label only (no score); matches L1/L2 rhythm
    badge.textContent = 'L0';
    badge.style.background = GREY;
    scoreEl.hidden = true;
    _emo = { colorMode: 'needsAnalysis', label: 'L0' };
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
  textEl.textContent = p.text || p.name || '';
  textEl.title = p.text || p.name || '';

  // rows = [key, value, tip?, dim?] —— tip 挂 kv-k 的 title；dim 弱化（坐标同 ID 级小字灰）
  const rows = [];
  if (p.location) rows.push(['位置', p.location]);
  if (p.category) rows.push(['类别', p.category]);
  if (p.emotion_type) rows.push(['情绪类型', p.emotion_type]);
  if (p.emotion_intensity != null) rows.push(['情绪强度', Number(p.emotion_intensity).toFixed(2)]);
  if (p.l1_confidence != null) rows.push(['置信度', Number(p.l1_confidence).toFixed(2),
    'L1 治理阶段由 LLM（DeepSeek）判断的数据相关性置信度（0~1）：该条数据与城市规划情绪分析的相关程度。可收集、可复现。']);
  if (Array.isArray(p.keywords) && p.keywords.length) rows.push(['关键词', p.keywords.join('、')]);
  // POI / 地点属性（导入 pois_wgs84.geojson 等 POI 数据时显示；情绪数据无这些字段、自然跳过）
  if (p.zone_name) rows.push(['区域', p.zone_name]);
  if (p.baidu_level1) rows.push(['类别', p.baidu_level1 + (p.baidu_level2 ? ' / ' + p.baidu_level2 : '')]);
  if (p.area) rows.push(['片区', p.area]);
  if (p.source) rows.push(['数据源', p.source]);
  if (p.in_water === true || p.in_water === 'true') rows.push(['落水', '是']);
  const c = feature.geometry && feature.geometry.coordinates;
  const isPoint = !!(c && !Array.isArray(c[0]));
  if (c) rows.push(['坐标', isPoint ? `${c[1].toFixed(6)}, ${c[0].toFixed(6)}` : feature.geometry.type]);   // 6 位精度、不再 dim（核查要清楚）
  document.getElementById('pp-kv').innerHTML = rows.map(([k, v, tip, dim]) =>
    `<div class="kv-row${dim ? ' kv-dim' : ''}"><span class="kv-k"${tip ? ` title="${tip}"` : ''}>${k}</span><span class="kv-v">${v}</span></div>`).join('');

  document.getElementById('pp-id').textContent = p.id_e ? `ID ${p.id_e}` : '';

  // 地点信息（区域 + 最近 POI）— async 反查，便于核查「这条数据落在哪、贴哪个 POI」
  if (isPoint) {
    const myToken = ++_popupRevToken;
    reverseGeocode(c[0], c[1]).then((res) => {
      if (myToken !== _popupRevToken || popup.hidden) return;   // 过期（已切别的点）/已关 → 丢弃
      const r = res || {};
      const extras = [];
      if (r.zone_name && !p.zone_name) extras.push(['区域', r.zone_name]);   // 静态已有 zone_name 就跳过
      if (r.nearest_poi && r.nearest_poi.name) {
        extras.push(['最近 POI', r.nearest_poi.name + (r.nearest_poi.dist_m != null ? ' · ' + r.nearest_poi.dist_m + 'm' : '')]);
      }
      if (extras.length) {
        const kv = document.getElementById('pp-kv');
        kv.innerHTML += extras.map(([k, v]) =>
          `<div class="kv-row"><span class="kv-k">${_pEsc(k)}</span><span class="kv-v">${_pEsc(v)}</span></div>`).join('');
      }
    }).catch(() => {});
  }
}

export function collapsePopup() {
  const popup = emoEl();
  if (!popup || popup.hidden || !_emo) return;
  // L0 stays grey '原始' capsule; L1 shows hotness, L2 shows scoreText.
  if (_emo.colorMode === 'confidence') document.getElementById('pp-polarity').textContent = _emo.score.toFixed(2);
  else if (_emo.colorMode === 'polarity') document.getElementById('pp-polarity').textContent = _emo.scoreText;
  // needsAnalysis: badge stays '原始' grey — label set in showPopup, no score to condense
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

// ── Cell popup（网格/柱体/地形环 点击 → 持久胶囊卡：聚类口径）──
// 镜像 range popup：胶囊(单元色) + 右侧边长 + 灰填充两行(地点/元数据) + kv(聚类)。
// 归因(issue_label/attribution/suggestion)不进本卡 → 进 Overview（识别问题深读）。
const cellEl = () => document.getElementById('cell-popup');
let _cell = null;            // { typeWord, color, isTerrain, sizeText }
let _cellLayerId = null;
let _cellGeoToken = 0;       // 反查 token：切格过期旧响应，防串台

const TERRAIN_POL_CN = { overall: '综合', positive: '积极', negative: '消极', neutral: '中性' };
const ANALYSIS_CN = { square: '标准网格', zonal: '指定单元' };
const _fmt = (v, d = 2) => (v == null || v === '') ? '—' : Number(v).toFixed(d);
const _bucket = (v) => (v == null ? '—' : v > 0.66 ? '高' : v > 0.33 ? '中' : '低');
const _valence = (pi) => (pi == null ? '—' : pi > 0.15 ? '偏积极' : pi < -0.15 ? '偏消极' : '中性');
const _valenceColor = (pi) => (pi == null ? '#999' : pi > 0.15 ? L2_POSITIVE['Positive'] : pi < -0.15 ? L2_NEGATIVE['Negative'] : L2_NEUTRAL_COLOR);

export function showCellPopup(feature, layer) {
  const popup = cellEl();
  if (!popup) return;
  popup.hidden = false;
  popup.classList.remove('is-collapsed');
  const p = feature.properties || {};
  const ui = (layer && layer.paint && layer.paint._ui) || {};
  const isTerrain = ui.tool === 'terrain';
  const is3d = ui.mode === '3d';
  const typeWord = isTerrain ? '地形环' : (is3d ? '柱体' : '网格');

  // 胶囊：单元色（gridStops 拍平 → rampColor 取该单元值）+ 类型词
  const stops = (layer.paint && Array.isArray(layer.paint.gridStops)) ? layer.paint.gridStops : [];
  const flat = stops.map((s) => (Array.isArray(s) ? s[1] : s));
  const fieldVal = layer.paint && layer.paint.gridField ? Number(p[layer.paint.gridField]) : NaN;
  const color = flat.length ? rampColor(flat, fieldVal) : '#0c1c2e';
  const badge = document.getElementById('cp-badge');
  badge.textContent = typeWord;
  badge.style.background = color;

  // 胶囊右侧：边长 / 等值环级
  const sizeText = isTerrain
    ? `等值环 L${_fmt(p._level)}`
    : (ui.cellSize ? `${ui.cellSize}×${ui.cellSize}m` : '—');
  document.getElementById('cp-size').textContent = sizeText;

  // 灰填充行 2 元数据（同步）：level·T·口径·分析类型
  document.getElementById('cp-meta').textContent = _cellMeta(layer, ui, isTerrain);

  // kv 聚类口径（禁面积/周长）
  const rows = _cellKvRows(p, ui, isTerrain);
  document.getElementById('cp-kv').innerHTML = rows.map(([k, v, tip, col]) =>
    `<div class="kv-row"><span class="kv-k"${tip ? ` title="${tip}"` : ''}>${k}</span>` +
    `<span class="kv-v"${col ? ` style="color:${col}"` : ''}>${v}</span></div>`).join('');

  // 灰填充行 1 地点（异步反查质心，防串台）
  const c = _cellCentroid(feature);
  const locEl = document.getElementById('cp-loc');
  locEl.textContent = '定位中…';
  if (c) {
    const myToken = ++_cellGeoToken;
    reverseGeocode(c[0], c[1]).then((res) => {
      if (myToken !== _cellGeoToken || popup.hidden) return;
      locEl.textContent = _locLine(res);
    }).catch(() => { if (myToken === _cellGeoToken) locEl.textContent = '—'; });
  } else locEl.textContent = '—';

  _cell = { typeWord, color, isTerrain, sizeText };
  _cellLayerId = layer ? layer.id : null;
}

export function collapseCellPopup() {
  const popup = cellEl();
  if (!popup || popup.hidden || !_cell) return;
  popup.classList.add('is-collapsed');   // 折叠：仅胶囊(类型词)，size/body 由 CSS 隐藏
}
export function expandCellPopup() {
  const popup = cellEl();
  if (!popup || popup.hidden || !_cell) return;
  popup.classList.remove('is-collapsed');
}
export function hideCellPopup() {
  const had = !!_cellLayerId;
  _cellLayerId = null; _cell = null;
  const p = cellEl(); if (p) p.hidden = true;
  if (had) document.dispatchEvent(new CustomEvent('cell:cleared'));   // 通知 main.js 回 layer Overview
}

/** 元数据行：`L2·T1·综合·标准网格`（T 从源层反查 deriveTimeTag） */
function _cellMeta(layer, ui, isTerrain) {
  const level = ui.level || 'L2';
  const tTag = _sourceTimeTag(ui.source);
  let mood;
  if (isTerrain) mood = TERRAIN_POL_CN[ui.terrainPol] || TERRAIN_POL_CN[ui.polarity] || '综合';
  else if (level === 'L1') mood = '热度';
  else mood = POLARITY_LABEL[ui.polarity] || '综合';
  const analysis = isTerrain ? '情绪地形' : (ANALYSIS_CN[ui.analysis] || '标准网格');
  return [level, tTag, mood, analysis].filter(Boolean).join('·');
}

/** kv 聚类口径：点数 / 聚类程度 / [L2] 极性指数 / [L1] 置信度 / [terrain] 强度 / 均分 */
function _cellKvRows(p, ui, isTerrain) {
  const rows = [];
  rows.push(['情绪点数', p.point_count ?? 0]);
  const heatV = isTerrain ? p._level : p._grid_h;
  rows.push(['聚类程度', `${_fmt(heatV)}（${_bucket(heatV)}）`, '该单元情绪聚合的高/中/低判断依据（密度×强度归一化）']);
  if (ui.level === 'L2' && p.polarity_index != null) {
    rows.push(['极性指数', `${_fmt(p.polarity_index)}（${_valence(p.polarity_index)}）`, null, _valenceColor(p.polarity_index)]);
  }
  if (!isTerrain && p.l1_confidence_mean != null) rows.push(['置信度', _fmt(p.l1_confidence_mean)]);
  if (isTerrain && p.emotion_intensity_mean != null) rows.push(['强度均值', _fmt(p.emotion_intensity_mean)]);
  if (p.score_mean != null) rows.push(['平均分数', _fmt(p.score_mean)]);
  return rows;
}

function _locLine(r) {
  const parts = [];
  if (r && r.zone_name) parts.push(r.zone_name);
  if (r && r.nearest_poi && r.nearest_poi.name) parts.push(r.nearest_poi.name);
  return parts.length ? parts.join('·') : '—';
}

/** 质心：grid 用预计算 _center；terrain/无 _center 用 bbox 中心（近似够反查） */
function _cellCentroid(feat) {
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

/** 从 _ui.source（group:id / layer:id）反查源层 time 标签 */
function _sourceTimeTag(source) {
  if (!source) return '';
  const m = String(source).match(/^(?:group|layer):([^#]+)/);
  if (!m) return '';
  const src = getLayer(m[1]);
  return (src && src.fc && deriveTimeTag(src.fc)) || '';
}

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
  if (tgt && tgt.closest && (tgt.closest('#feature-popup') || tgt.closest('#range-popup') || tgt.closest('#cell-popup') || tgt.closest('#point-popup') || tgt.closest('#tip-popup'))) return 'popup';
  // 只认本项目数据层（id 以 lyr- 开头），排除底图 fill/line/circle（landcover/water/road…）——
  // 否则点底图水面/土地利用也会被当成"点中范围/点"，误开 popup（原 hitRange 逻辑的同质漏网）。
  const ours = feats.filter((f) => f.layer && String(f.layer.id).startsWith('lyr-'));
  if (ours.some((f) => f.layer.type === 'circle')) return 'point';
  // cell（grid/terrain 工具层，fill 或 fill-extrusion）须在 range-visible 之前判定，避免网格格误入范围分支
  if (ours.some((f) => isCellFeature(f))) return 'cell';
  if (ours.some((f) => (f.layer.type === 'fill' || f.layer.type === 'line') && !String(f.layer.id).endsWith('-hit'))) return 'range-visible';
  if (ours.some((f) => String(f.layer.id).endsWith('-hit'))) return 'range-hitband';
  return 'blank';
}

/** 命中 feature 是否属于 grid/terrain 工具层（聚合单元，走 cell popup 而非 range popup）。 */
function isCellFeature(f) {
  const l = layerFromFeature(f);
  return !!(l && l.paint && l.paint._ui && (l.paint._ui.tool === 'grid' || l.paint._ui.tool === 'terrain'));
}
function isRangePopupExpanded() {
  const p = rngEl();
  return !!p && !p.hidden && !p.classList.contains('is-collapsed') && !!_rng;
}

// ── Point popup（搜索结果标记 → 第三张胶囊卡，顺序在 Range 之下）──
const ptEl = () => document.getElementById('point-popup');
let _point = null;   // { name, lng, lat }

function _pEsc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function _ptRow(k, v) {
  return '<div class="kv-row"><span class="kv-k">' + _pEsc(k) + '</span><span class="kv-v">' + _pEsc(v) + '</span></div>';
}

export function showPointPopup(hit) {
  const p = ptEl();
  if (!p || !hit) return;
  p.hidden = false;
  p.classList.remove('is-collapsed');
  const badge = document.getElementById('pt-badge');
  badge.textContent = 'Point';
  badge.style.background = '#e53935';   // 与红色大头针同色，视觉绑定
  badge.style.color = '#fff';
  document.getElementById('pt-name').textContent = hit.name || '';
  const rows = [];
  const _dsLabel = { amap: '高德POI库', seed: '种子(手标)', 'amap-api': '高德API补全' };
  rows.push(_ptRow('数据源', _dsLabel[hit.data_source] || hit.source || '-'));
  const _lv = (hit.baidu_level1 && hit.baidu_level2)
    ? hit.baidu_level1 + ' / ' + hit.baidu_level2
    : (hit.baidu_level1 || hit.baidu_level2 || hit.category || '');
  if (_lv) rows.push(_ptRow('类别', _lv));
  if (hit.zone_name) rows.push(_ptRow('区域', hit.zone_name));
  if (hit.area) rows.push(_ptRow('片区', hit.area));
  rows.push(_ptRow('坐标', Number(hit.lat).toFixed(6) + ', ' + Number(hit.lng).toFixed(6)));
  document.getElementById('pt-kv').innerHTML = rows.join('');
  _point = { name: hit.name, lng: hit.lng, lat: hit.lat };
}

export function collapsePointPopup() {
  const p = ptEl();
  if (!p || p.hidden || !_point) return;
  p.classList.add('is-collapsed');
}

export function expandPointPopup() {
  const p = ptEl();
  if (!p || p.hidden || !_point) return;
  p.classList.remove('is-collapsed');
}

export function hidePointPopup() {
  _point = null;
  const p = ptEl();
  if (p) p.hidden = true;
}

// ── Init: close/expand/collapse wiring ─────────────────────────────────────
export function initPopup(map) {
  const e = emoEl(), r = rngEl(), cp = cellEl();
  document.getElementById('popup-close')?.addEventListener('click', hidePopup);
  document.getElementById('range-close')?.addEventListener('click', hideRangePopup);
  document.getElementById('cell-close')?.addEventListener('click', hideCellPopup);
  document.getElementById('point-close')?.addEventListener('click', () => {
    hidePointPopup();
    document.dispatchEvent(new CustomEvent('point:hide'));   // 通知 search-bar 移除标记
  });
  e?.addEventListener('click', () => { if (e.classList.contains('is-collapsed')) expandPopup(); });
  r?.addEventListener('click', () => { if (r.classList.contains('is-collapsed')) expandRangePopup(); });
  cp?.addEventListener('click', () => { if (cp.classList.contains('is-collapsed')) expandCellPopup(); });
  const pt = ptEl();
  pt?.addEventListener('click', () => { if (pt.classList.contains('is-collapsed')) expandPointPopup(); });
  if (map) {
    map.on('click', (ev) => {
      if (isDrawActive()) return;   // 绘制中：click 归 draw-tool，不触发 popup
      const feats = map.queryRenderedFeatures(ev.point) || [];
      const k = classifyMapClick(feats, ev);
      if (k === 'popup') return;
      // 搜索标记以外（地图任意点击）→ 收起 Point 卡 + 缩小搜索标记
      collapsePointPopup();
      document.dispatchEvent(new CustomEvent('point:collapse'));
      // 聚合单元（网格/柱体/地形环）：cell popup + Overview 联动，收 point/range 后 return
      if (k === 'cell') {
        const f = feats.find(isCellFeature);
        const layer = f && layerFromFeature(f);
        if (layer) {
          showCellPopup(f, layer);
          document.dispatchEvent(new CustomEvent('cell:selected', { detail: { feature: f, layer } }));
        }
        collapsePopup();
        collapseRangePopup();
        return;
      }
      // 非单元点击 → 折叠 cell 卡（不消失，点胶囊可展开；仅 close 按钮/层隐藏才彻底关）
      collapseCellPopup();
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
    if (_cellLayerId) {
      const l = getLayer(_cellLayerId);
      if (!l || !l.visible) hideCellPopup();      // 工具层隐藏/删除 → cell popup 消失 + cell:cleared
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
