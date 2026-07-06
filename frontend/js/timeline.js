// ═══ timeline.js — 任务2 时间轴（T1→T3 成效动画演示）═══════════════════════════════
// 一条通用时间轴（Tab 条下）：scrub 进度条 + 离散 T1/T2/T3 停点 + play/pause/prev/next。
// 播放尊重当前 sub-Tab：图层总览 → 演进综合（count line + 饼图）；极性深读 → 演进当前极性（count + 矩阵）。
//
// 地图柱体动画 = 路线 A（JS rAF + setData）：每帧 lerp 各 cell 的 _grid_h/_grid_norm 等属性 →
//   map.getSource(sid).setData(lerpedFc)（updateGridSourceData）。承重 paint-inplace-swap-view：单 source、
//   不注册隐藏层、不 removeSource/re-renderLayer（保 tip/选中/bindings）。
//
// 数据：L2 点要素（DATA/performance/yichang_L2_T{1,2,3}_*.geojson）自带 polarity/domain/element/time_label。
//   snap-to-grid O(1) 聚合进活跃 grid scaffold 格 → 每 T 的 per-cell 统计 → 共享 max 归一化 _grid_h（跨 T 可比）。
//
// 错峰：柱体(800ms) → 数字/饼/矩阵(600ms, delay 200ms) → 关键词淡入(300ms)。
// 色彩 #3A5368 主 / #8B658B 副（timeline.css）。
// 详见 plan + revision-log 5.29；承重 memory: paint-inplace-swap-view / sticky-hover-priority /
//   generate-grid-exclusive-vs-viewmode / verify-with-webapp-testing-skill。

import { getLayer, deriveTimeTag } from './state.js';
import { updateGridSourceData } from './map.js';
import { piToNorm } from './grid-tool.js';
import {
  overviewKpiFromFeats, polarityKpiFromFeats, overallMatrixFromFeats,
  paintOverallKpi, paintPolarityKpi, paintOverallMatrix, paintOverallKeywords, flashOverviewKeywords,
} from './panel.js';

// ── 常量 ──
const TL_T = ['T1', 'T2', 'T3'];                    // 进度 0/1/2
const PT_URL = (T) => `/DATA/performance/yichang_L2_${T}_L2_result_geojson.geojson`;
const SEG_DUR = 1100;                                // 每 T 段时长 ms（柱体 800 + 关键词尾 300）
const KPI_DELAY = 200, KPI_WINDOW = 600;            // KPI 窗口（错峰）
const TL_MAIN = '#3A5368', TL_SUB = '#8B658B';      // 与 css 同源（JS 动态色用）
const T_LABEL = { T1: 'T1 · 基线', T2: 'T2 · 过渡', T3: 'T3 · 成效' };

// heightOf 复刻自 grid-tool.preprocessGrid（offset+sqrt γ=0.5；shared max 跨 T 可比 → 不调 preprocessGrid 承重路径）
const H_OFFSET = 2, H_GAMMA = 0.5, H_LOW_UNIT = 0.025;
function heightOf(val, maxVal) {
  if (val <= 0) return 0;
  if (val <= H_OFFSET) return val * H_LOW_UNIT;
  const denom = Math.max(maxVal - H_OFFSET, 1);
  return Math.min(1, Math.pow((val - H_OFFSET) / denom, H_GAMMA));
}
const easeInOut = (t) => { t = Math.max(0, Math.min(1, t)); return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; };
const lerp = (a, b, t) => a + (b - a) * t;

// ── 状态 ──
let _el = null;             // 时间轴根 DOM (.tl-wrap)
let _layer = null;          // 绑定的活跃 L2 综合 grid 层
let _snaps = null;          // { T1:{fc,overall,polarities}, T2:.., T3:.. }
let _progress = 0;          // 0..2 连续进度
let _playing = false, _raf = 0, _playStart = 0, _playFrom = 0, _playTo = 0;
let _segFlashed = -1;       // 错峰关键词 flash 已触发的段（-1 none）
let _busy = false;          // 数据 prep 中（禁用控件）

// ── DOM 构建（自包含组件，注入 #timeline-wrap）──
function _buildDom() {
  const wrap = document.createElement('div');
  wrap.className = 'tl-wrap';
  wrap.innerHTML = `
    <div class="tl-head"><span class="tl-title">时间轴</span><span class="tl-label" id="tl-label">—</span></div>
    <div class="tl-bar">
      <div class="tl-track" id="tl-track">
        <div class="tl-progress" id="tl-progress"></div>
        <button class="tl-stop" data-t="0" style="left:0%">T1</button>
        <button class="tl-stop" data-t="1" style="left:50%">T2</button>
        <button class="tl-stop" data-t="2" style="left:100%">T3</button>
        <div class="tl-thumb" id="tl-thumb"></div>
      </div>
    </div>
    <div class="tl-controls">
      <button class="tl-btn" id="tl-prev" title="上一时间点" type="button">&#9664;</button>
      <button class="tl-btn tl-play" id="tl-play" title="播放/暂停" type="button">&#9654;</button>
      <button class="tl-btn" id="tl-next" title="下一时间点" type="button">&#9654;</button>
    </div>`;
  return wrap;
}

/** 初始化：注入 DOM + 绑事件（main.js 启动时调一次）。 */
export function initTimeline() {
  const host = document.getElementById('timeline-wrap');
  if (!host || _el) return;
  _el = _buildDom();
  _el.hidden = true;   // 初始隐藏（refreshOverview 先于 init 跑过 hideTimeline 但 _el 尚未建）
  host.appendChild(_el);
  // [DEBUG 临时] 暴露内部状态便于诊断（提交前删）
  window.__tl = () => ({
    hasLayer: !!_layer, layerId: _layer && _layer.id, layerFeats: _layer && _layer.fc && _layer.fc.features && _layer.fc.features.length,
    layerUi: _layer && _layer.paint && _layer.paint._ui && { tool: _layer.paint._ui.tool, level: _layer.paint._ui.level, polarity: _layer.paint._ui.polarity },
    hidden: _el && _el.hidden,
    hasSnaps: !!_snaps, forId: _snaps && _snaps._for, snapKeys: _snaps && Object.keys(_snaps.T),
    t1: _snaps && _snaps.T && _snaps.T.T1 && { feats: _snaps.T.T1.fc.features.length, withPts: _snaps.T.T1.fc.features.filter((f) => (f.properties.point_count || 0) > 0).length, overall: _snaps.T.T1.overall },
    busy: _busy, playing: _playing, progress: _progress,
  });
  _el.querySelector('#tl-track').addEventListener('click', (e) => {
    if (_busy) return;
    const r = e.currentTarget.getBoundingClientRect();
    const p = Math.max(0, Math.min(2, ((e.clientX - r.left) / r.width) * 2));
    _jumpTo(p);
  });
  _el.querySelectorAll('.tl-stop').forEach((b) =>
    b.addEventListener('click', (e) => { e.stopPropagation(); if (!_busy) _jumpTo(parseInt(b.dataset.t, 10)); }));
  _el.querySelector('#tl-prev').addEventListener('click', () => { if (!_busy) _jumpTo(Math.round(_progress) - 1); });
  _el.querySelector('#tl-next').addEventListener('click', () => { if (!_busy) _jumpTo(Math.round(_progress) + 1); });
  _el.querySelector('#tl-play').addEventListener('click', () => { if (!_busy) _togglePlay(); });
}

// ── 显隐（仅 L2 综合 grid 焦点层时显；main.js 调）──
export function showTimeline(layer) {
  if (!_el) initTimeline();
  console.log('[timeline] showTimeline', layer && layer.id, 'feats=', layer && layer.fc && layer.fc.features && layer.fc.features.length);
  _el.hidden = false;
  _layer = layer;
  _lastKwSnap = null;   // 重新激活 → 关键词首帧重画
  _progress = Math.max(0, Math.min(2, TL_T.indexOf(layer.timeTag || deriveTimeTag(layer.fc))));
  _prepare(layer).then(() => { console.log('[timeline] prepare done →', window.__tl && window.__tl()); _renderAt(_progress); _updateLabel(); });
}
export function hideTimeline() {
  _stop();
  if (_layer && _snaps) {
    // 还原活跃层原始 source data（回到该层真实 T 的 _grid_h/_grid_norm）
    updateGridSourceData(_layer, _layer.fc);
  }
  _layer = null; _snaps = null;
  if (_el) _el.hidden = true;
}

// ── 数据 prep：snap-to-grid 聚合 T1/T2/T3 进 scaffold，建 per-T snapshot ──
async function _prepare(layer) {
  if (_snaps && _snaps._for === layer.id) return;
  _busy = true; _setBusy(true);
  try {
    const scaffold = layer.fc.features;
    const step = (layer.paint && layer.paint._ui && layer.paint._ui.cellSize) || 400;
    const idx = _buildCellIndex(scaffold, step);   // {originX,originY,step,cells:Map}
    // 拉 3 T 点集 + 聚合
    const perT = {};
    for (const T of TL_T) {
      const fc = await _fetchPoints(T);
      perT[T] = fc ? _aggregate(fc.features, idx) : null;
    }
    // 共享 max（跨 T 可比）
    const maxes = { all: 0, pos: 0, neg: 0, neu: 0 };
    for (const T of TL_T) {
      const a = perT[T]; if (!a) continue;
      for (const c of a.cells) {
        if (c.point_count > maxes.all) maxes.all = c.point_count;
        if (c.np > maxes.pos) maxes.pos = c.np;
        if (c.nn > maxes.neg) maxes.neg = c.nn;
        if (c.ne > maxes.neu) maxes.neu = c.ne;
      }
    }
    // 建 per-T virtual fc + KPI snapshot
    _snaps = { _for: layer.id, step, idx, scaffold, T: {} };
    for (const T of TL_T) {
      const a = perT[T]; if (!a) { _snaps.T[T] = _snaps.T[TL_T[0]] || _emptySnap(layer); continue; }
      const fc = _buildVirtualFc(layer, a, maxes);
      _snaps.T[T] = {
        fc,
        overall: overviewKpiFromFeats(fc.features),
        overallMatrix: overallMatrixFromFeats(fc.features),
        polarities: {
          positive: polarityKpiFromFeats(fc.features, 'positive'),
          negative: polarityKpiFromFeats(fc.features, 'negative'),
          neutral: polarityKpiFromFeats(fc.features, 'neutral'),
        },
      };
    }
  } catch (e) {
    console.error('[timeline] prep 失败：', e);
    _setLabel('数据准备失败：' + ((e && e.message) || e));
  } finally {
    _busy = false; _setBusy(false);
  }
}

function _emptySnap(layer) {
  const fc = { type: 'FeatureCollection', features: layer.fc.features.map((f) => ({ ...f, properties: { ...(f.properties || {}) } })) };
  return { fc, overall: overviewKpiFromFeats(fc.features), overallMatrix: overallMatrixFromFeats(fc.features), polarities: { positive: { cell: {}, total: 0 }, negative: { cell: {}, total: 0 }, neutral: { cell: {}, total: 0 } } };
}

async function _fetchPoints(T) {
  try {
    const r = await fetch(PT_URL(T), { cache: 'force-cache' });
    return r.ok ? await r.json() : null;
  } catch { return null; }
}

/** scaffold 格 → snap-to-grid 桶索引（${ix},${iy} → [{i,cx,cy}]）。
 *  step 必须是「度」（cell 经纬度宽高），不是 cellSize 米——用米除经纬度会让所有格塌进一格。
 *  从单格 bbox 实算 stepLng/stepLat；失败 fallback cellSize 米按宜昌纬度转度。
 *  桶存数组：重投影(4546→4326)致相邻格 min-corner 取整可能碰撞，同桶多格 → 点取最近质心格（不丢格）。 */
function _buildCellIndex(scaffold, cellSizeM) {
  let minX = Infinity, minY = Infinity;
  let stepLng = null, stepLat = null;
  const meta = [];   // [ix, iy, cxC, cyC] per cell
  for (let i = 0; i < scaffold.length; i++) {
    const f = scaffold[i];
    const ring = (f.geometry && f.geometry.coordinates && f.geometry.coordinates[0]) || [];
    let cxMin = Infinity, cyMin = Infinity, cxMax = -Infinity, cyMax = -Infinity;
    for (const [x, y] of ring) { if (x < cxMin) cxMin = x; if (y < cyMin) cyMin = y; if (x > cxMax) cxMax = x; if (y > cyMax) cyMax = y; }
    if (cxMin < minX) minX = cxMin;
    if (cyMin < minY) minY = cyMin;
    if (stepLng == null && cxMax > cxMin) stepLng = cxMax - cxMin;   // 单格宽（度）
    if (stepLat == null && cyMax > cyMin) stepLat = cyMax - cyMin;   // 单格高（度）
    meta.push([cxMin, cyMin, (cxMin + cxMax) / 2, (cyMin + cyMax) / 2]);
  }
  if (!stepLng || !stepLat) {   // fallback：cellSize 米按宜昌纬度（~30.7°N）转度
    const latRad = 30.7 * Math.PI / 180;
    stepLng = cellSizeM / (111320 * Math.cos(latRad));
    stepLat = cellSizeM / 110540;
  }
  const buckets = new Map();
  for (let i = 0; i < scaffold.length; i++) {
    const [cxMin, cyMin, cxC, cyC] = meta[i];
    const ix = Math.round((cxMin - minX) / stepLng);
    const iy = Math.round((cyMin - minY) / stepLat);
    const k = `${ix},${iy}`;
    if (!buckets.has(k)) buckets.set(k, []);
    buckets.get(k).push({ i, cx: cxC, cy: cyC });
  }
  return { originX: minX, originY: minY, stepLng, stepLat, buckets, n: scaffold.length };
}

/** 把点聚合进 scaffold 格：每格 {point_count, n_*, domain/element 多数}。arr 按 scaffold 长度全填 blank（零洞）。
 *  碰撞桶 → 点取最近质心格。返回 {cells, counted}。 */
function _aggregate(points, idx) {
  const { originX, originY, stepLng, stepLat, buckets, n } = idx;
  const arr = new Array(n);
  for (let i = 0; i < n; i++) arr[i] = _blankCell();
  let counted = 0;
  for (const pt of points) {
    const c = pt.geometry && pt.geometry.coordinates;
    if (!c) continue;
    const ix = Math.floor((c[0] - originX) / stepLng);
    const iy = Math.floor((c[1] - originY) / stepLat);
    const list = buckets.get(`${ix},${iy}`);
    if (!list || !list.length) continue;   // 点在 scaffold 外 → 跳过
    let best = list[0], bestD = Infinity;
    for (const e of list) { const d = (e.cx - c[0]) * (e.cx - c[0]) + (e.cy - c[1]) * (e.cy - c[1]); if (d < bestD) { bestD = d; best = e; } }
    _tally(arr[best.i], pt.properties || {});
    counted++;
  }
  return { cells: arr, counted };
}
function _blankCell() {
  return { point_count: 0, n_very_positive: 0, n_positive: 0, n_neutral: 0, n_negative: 0, n_very_negative: 0, dom: {}, elm: {} };
}
function _tally(c, p) {
  c.point_count++;
  const pol = p.polarity;
  if (pol === 'Very Positive') c.n_very_positive++;
  else if (pol === 'Positive') c.n_positive++;
  else if (pol === 'Neutral') c.n_neutral++;
  else if (pol === 'Negative') c.n_negative++;
  else if (pol === 'Very Negative') c.n_very_negative++;
  if (p.domain) c.dom[p.domain] = (c.dom[p.domain] || 0) + 1;
  if (p.element) c.elm[p.element] = (c.elm[p.element] || 0) + 1;
}
function _topKey(obj) {
  let best = null, bestN = 0;
  for (const k in obj) if (obj[k] > bestN) { bestN = obj[k]; best = k; }
  return best || '';
}

/** scaffold 几何 + per-T 统计 + _grid_* （共享 max）。返回独立 fc（不污染 layer.fc）。 */
function _buildVirtualFc(layer, agg, maxes) {
  const scaffold = layer.fc.features;
  const feats = new Array(scaffold.length);
  for (let i = 0; i < scaffold.length; i++) {
    const src = scaffold[i];
    const a = agg.cells[i] || _blankCell();
    const np = a.n_positive + a.n_very_positive;
    const nn = a.n_negative + a.n_very_negative;
    const ne = a.n_neutral;
    const pi = a.point_count > 0
      ? (a.n_very_positive * 2 + a.n_positive * 1 + a.n_negative * -1 + a.n_very_negative * -2) / a.point_count
      : null;
    const props = {
      ...(src.properties || {}),
      point_count: a.point_count,
      n_very_positive: a.n_very_positive, n_positive: a.n_positive, n_neutral: a.n_neutral,
      n_negative: a.n_negative, n_very_negative: a.n_very_negative,
      _grid_n_pos: np, _grid_n_neg: nn, _grid_n_neu: ne,
      domain_top: _topKey(a.dom), element_top: _topKey(a.elm),
      polarity_index: pi,
      _grid_h: heightOf(a.point_count, maxes.all),
      _grid_h_pos: heightOf(np, maxes.pos), _grid_h_neg: heightOf(nn, maxes.neg), _grid_h_neu: heightOf(ne, maxes.neu),
      _grid_norm: piToNorm(pi),
    };
    feats[i] = { type: 'Feature', geometry: src.geometry, properties: props };
  }
  return { type: 'FeatureCollection', features: feats };
}

// ── 渲染（每帧 / scrub）──

/** 检测当前 sub-Tab + 极性。返回 {mode:'layer'|'polarity', pol?}。 */
function _currentMode() {
  const polPane = document.getElementById('ov-polarity-pane');
  if (polPane && polPane.classList.contains('is-active')) {
    const tab = document.querySelector('#ov-polarity-pane .ov-pol-tab.is-active');
    return { mode: 'polarity', pol: (tab && tab.dataset.pol) || 'positive' };
  }
  return { mode: 'layer' };
}

/** 在 progress（0..2 连续）处渲染一帧（scrub 用；无错峰）。 */
function _renderAt(progress) {
  if (!_snaps || !_layer) return;
  const i = Math.floor(progress);
  const a = _snaps.T[TL_T[Math.max(0, Math.min(2, i))]];
  const b = _snaps.T[TL_T[Math.max(0, Math.min(2, i + 1))]] || a;
  const t = easeInOut(progress - i);
  _renderFrame(a, b, t, t);
  _updateThumb(progress);
}

/** 核心帧渲染：map bars 用 barsT、KPI 用 kpiT（错峰时两者不同步）。 */
let _lastKwSnap = null;   // 上次关键词所用 snap（综合模式跨段才换词，避免每帧重渲染）
function _renderFrame(snapA, snapB, barsT, kpiT) {
  // map：lerp 每 cell 的高度/色字段 → setData。**不 lerp _grid_n_***（极性 filter `_grid_n_*>0`
  //   若 lerp 穿越 0 → cell 闪烁；保持 snapA 值让 filter 稳定，高度/色用 _grid_h_* 平滑过渡）。
  const fa = snapA.fc.features, fb = snapB.fc.features;
  const lerped = new Array(fa.length);
  const flds = ['_grid_h', '_grid_h_pos', '_grid_h_neg', '_grid_h_neu', '_grid_norm', 'polarity_index', 'point_count'];
  for (let i = 0; i < fa.length; i++) {
    const pa = fa[i].properties || {}, pb = (fb[i] && fb[i].properties) || {};
    const props = {};
    for (const k of Object.keys(pa)) props[k] = pa[k];   // 拷贝（含 _grid_n_*/domain_top/element_top/topic_top 等非动画字段）
    for (const k of flds) props[k] = lerp(pa[k] || 0, pb[k] || 0, barsT);
    props._grid_norm = lerp(pa._grid_norm ?? 0.5, pb._grid_norm ?? 0.5, barsT);   // 颜色随 pi 平滑
    lerped[i] = { type: 'Feature', geometry: fa[i].geometry, properties: props };
  }
  updateGridSourceData(_layer, { type: 'FeatureCollection', features: lerped });

  // Overview KPI（按当前 sub-Tab）
  const m = _currentMode();
  if (m.mode === 'polarity') {
    const ka = snapA.polarities[m.pol], kb = snapB.polarities[m.pol];
    paintPolarityKpi(m.pol, _lerpPolKpi(ka, kb, kpiT));
  } else {
    paintOverallKpi(_lerpOvKpi(snapA.overall, snapB.overall, kpiT));
    paintOverallMatrix(_lerpOverallMatrix(snapA.overallMatrix, snapB.overallMatrix, kpiT));
    // 关键词离散切换：按最近 T 停点，跨 0.5 才换（避免每帧重渲染、保 flash 动画）
    const kwSnap = barsT < 0.5 ? snapA : snapB;
    if (kwSnap !== _lastKwSnap) { paintOverallKeywords(kwSnap.fc.features); _lastKwSnap = kwSnap; }
  }
}
/** 综合 4×5 矩阵 lerp：n 固定（scaffold 格数跨 T 不变），pi 均值 lerp（→ 颜色变）。
 *  返回 cell map；piSum=piAvg, piCnt=1 → _matrixHtml 算 pi=piAvg。 */
function _lerpOverallMatrix(a, b, t) {
  const cell = {};
  const keys = new Set([...Object.keys(a || {}), ...Object.keys(b || {})]);
  for (const k of keys) {
    const ca = (a && a[k]) || { n: 0, piSum: 0, piCnt: 0 }, cb = (b && b[k]) || { n: 0, piSum: 0, piCnt: 0 };
    const piA = ca.piCnt ? ca.piSum / ca.piCnt : 0, piB = cb.piCnt ? cb.piSum / cb.piCnt : 0;
    cell[k] = { n: ca.n || cb.n, piSum: lerp(piA, piB, t), piCnt: 1 };
  }
  return cell;
}
function _lerpOvKpi(a, b, t) {
  const agg = {};
  for (const k of ['Very Positive', 'Positive', 'Neutral', 'Negative', 'Very Negative']) agg[k] = lerp(a.agg[k] || 0, b.agg[k] || 0, t);
  return { total: lerp(a.total, b.total, t), pos: lerp(a.pos, b.pos, t), neg: lerp(a.neg, b.neg, t), neu: lerp(a.neu, b.neu, t), agg };
}
function _lerpPolKpi(a, b, t) {
  const cell = {};
  const keys = new Set([...Object.keys(a.cell || {}), ...Object.keys(b.cell || {})]);
  for (const k of keys) cell[k] = { n: Math.round(lerp((a.cell[k] || {}).n || 0, (b.cell[k] || {}).n || 0, t)) };
  return { total: lerp(a.total, b.total, t), cell };
}

function _updateThumb(p) {
  if (!_el) return;
  const pct = (p / 2) * 100;
  const prog = _el.querySelector('#tl-progress');
  const thumb = _el.querySelector('#tl-thumb');
  if (prog) prog.style.width = pct + '%';
  if (thumb) thumb.style.left = pct + '%';
}
function _updateLabel() {
  if (!_el) return;
  const T = TL_T[Math.max(0, Math.min(2, Math.round(_progress)))];
  const lab = _el.querySelector('#tl-label');
  if (lab) lab.textContent = T_LABEL[T] || T;
}

// ── 播放控制 ──
function _togglePlay() {
  if (_playing) _stop();
  else _play();
}
function _setLabel(txt) {
  const lab = _el && _el.querySelector('#tl-label');
  if (lab) lab.textContent = txt;
}
function _play() {
  if (!_snaps) {
    console.error('[timeline] play 阻塞：_snaps 为 null（数据 prep 失败或未完成）', window.__tl && window.__tl());
    _setLabel('数据未就绪（F12 控制台见 [timeline]）');
    return;
  }
  _playing = true;
  _playFrom = (Math.round(_progress) >= 2) ? 0 : _progress;   // 已到 T3 → 回 T1 重播
  _playTo = 2;
  _playStart = performance.now();
  _segFlashed = -1;
  _setPlayIcon(true);
  _tick();
}
function _stop() {
  if (!_playing) return;
  _playing = false;
  if (_raf) cancelAnimationFrame(_raf);
  _raf = 0;
  _setPlayIcon(false);
}
function _tick() {
  if (!_playing) return;
  const elapsed = performance.now() - _playStart;
  const totalSegs = _playTo - _playFrom;
  const totalDur = totalSegs * SEG_DUR;
  if (elapsed >= totalDur) {
    _progress = _playTo;
    _renderAt(_progress); _updateThumb(_progress); _updateLabel();
    _stop(); return;
  }
  const p = _playFrom + elapsed / SEG_DUR;   // 每段 SEG_DUR ms（段 = 相邻 T 停点）
  _progress = p;
  // 错峰：每段内 barsT(0..1 全程) / kpiT(delay+window) / 关键词 flash(段尾)
  const seg = Math.floor(p);
  const segLocal = p - seg;
  const barsT = easeInOut(segLocal);
  const kpiT = easeInOut(Math.max(0, Math.min(1, (segLocal * SEG_DUR - KPI_DELAY) / KPI_WINDOW)));
  if (segLocal >= 0.75 && _segFlashed < seg) { flashOverviewKeywords(); _segFlashed = seg; }
  const a = _snaps.T[TL_T[seg]];
  const b = _snaps.T[TL_T[Math.min(2, seg + 1)]] || a;
  _renderFrame(a, b, barsT, kpiT);
  _updateThumb(p);
  _updateLabel();
  _raf = requestAnimationFrame(_tick);
}

/** 跳到 progress（scrub click / 停点 / prev/next）：停点用 easeTo 短动画，否则即时。 */
function _jumpTo(p) {
  p = Math.max(0, Math.min(2, p));
  console.log('[timeline] jumpTo', p, 'snaps=', !!_snaps);
  _stop();
  _progress = p;
  _renderAt(p);
  _updateThumb(p);
  _updateLabel();
}

function _setPlayIcon(playing) {
  const b = _el && _el.querySelector('#tl-play');
  if (b) b.innerHTML = playing ? '&#10074;&#10074;' : '&#9654;';
}
function _setBusy(busy) {
  if (!_el) return;
  _el.classList.toggle('is-busy', busy);
  const lab = _el.querySelector('#tl-label');
  if (lab) lab.textContent = busy ? '加载数据…' : (T_LABEL[TL_T[Math.max(0, Math.min(2, Math.round(_progress)))]] || '—');
}
