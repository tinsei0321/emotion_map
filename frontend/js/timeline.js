// ═══ timeline.js — 全局时间轴 · grid 演进 headless 引擎（A3）═══════════════════════════
// 从「带 UI 的 T1-T3 小动画玩具」改造为 headless 引擎：无自带 UI，由 time-bar 驱动。
//   - 数据：从 manifest 发现片（slicesOf/loadSlice，time-source.js），不再写死 T1/T2/T3。
//   - 片数泛化 N（_progress 0..n-1）；阶段=lerp 平滑演进 / 日度=离散（按 period，time-bar 决定）。
//   - 导出：bindGrid/unbindGrid（绑定焦点 grid）/ renderSlice（离散）/ play+stop（动画）/ isBound。
//   - UI（旧侧栏 #timeline-wrap widget）已 retire → 时间按钮 + 卡片在 time-bar.js。
//
// 地图柱体动画 = 路线 A（JS rAF + setData）：每帧 lerp 各 cell 的 _grid_h/_grid_norm →
//   updateGridSourceData（= getSource().setData）。承重 paint-inplace-swap-view：单 source、
//   不注册隐藏层、不 removeSource/re-renderLayer（保 tip/选中/bindings）。
//
// 播放语义：grid 平滑 lerp（张力来源），点层在片边界离散换源（time-bar 的 onSlice 回调 applyTime）。
//   grid 焦点时 _renderFrame 已 paint OverallKpi（按 Overview 当前 sub-Tab）。
// 详见 plan 07-19-cb-lovely-quiche.md（A3）；承重 memory: paint-inplace-swap-view / tool-no-auto-overview。

import { updateGridSourceData } from './map.js';
import { piToNorm } from './grid-tool.js';
import { slicesOf, loadSlice, tagLayer } from './time-source.js';
import {
  overviewKpiFromFeats, polarityKpiFromFeats, overallMatrixFromFeats,
  paintOverallKpi, paintPolarityKpi, paintOverallMatrix, paintOverallKeywords, flashOverviewKeywords,
} from './panel.js';

// ── 常量 ──
const SEG_DUR = 1100;                                // 每片段时长 ms（柱体 800 + 关键词尾 300）
const KPI_DELAY = 200, KPI_WINDOW = 600;            // KPI 错峰窗口

// heightOf 复刻自 grid-tool.preprocessGrid（offset+sqrt γ=0.5；shared max 跨片可比 → 不调 preprocessGrid 承重路径）
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
let _layer = null;          // 绑定的活跃 L2 综合 grid 层
let _snaps = null;          // { _for, step, idx, scaffold, byKey:Map<key,snap>, keys:[key...] }
let _progress = 0;          // 0..(n-1) 连续进度
let _playing = false, _raf = 0, _playStart = 0, _playFrom = 0, _playTo = 0;
let _segFlashed = -1;       // 错峰关键词 flash 已触发的段
let _lastFiredSeg = -1;     // onSlice 已触发的片索引（去重）
let _onSlice = null;        // play 片边界回调 (key)=>...（time-bar 用来 applyTime 换点层 + 刷高亮）
let _onDone = null;          // play 自然结束回调（time-bar 用来复位 ▶ 图标）
let _busy = false;          // 数据 prep 中
let _lastKwSnap = null;     // 上次关键词所用 snap（综合模式跨段才换词）

/** headless：无 DOM 初始化。main.js 启动仍调用（兼容），此处 no-op。 */
export function initTimeline() { /* headless engine — 无 widget DOM */ }

// ── 绑定 / 解绑（main.js refreshOverview 调：焦点是 L2 综合 grid → bindGrid，否则 unbindGrid）──

/** 绑定焦点 grid 层：补打 datasetId（grid 生成时未打）→ 按 manifest 预聚所有片 → 渲染当前片。 */
export function bindGrid(layer) {
  if (!layer) return;
  if (!layer.datasetId) tagLayer(layer);            // grid-tool 生成时未 tag → 按源 srcName 补打（matchDataset）
  _layer = layer;
  _lastKwSnap = null;
  _prepare(layer).then(() => {
    if (!_snaps) return;
    const cur = (layer.sliceKey && _snaps.keys.includes(layer.sliceKey)) ? layer.sliceKey : _snaps.keys[0];
    renderSlice(cur);
  });
}
/** 解绑：停播 + 还原活跃层原始 source data（回该层真实片的 _grid_h/_grid_norm）。 */
export function unbindGrid() {
  stop();
  if (_layer && _snaps) updateGridSourceData(_layer, _layer.fc);
  _layer = null; _snaps = null;
}
export function isBound() { return !!(_layer && _snaps); }

// ── 离散渲染（time-bar _pick / bindGrid 初始片用）──

/** 即时把绑定 grid 设到 sliceKey 片（a=b=snap, t=1 → 无 lerp）。片不在 snaps → no-op。 */
export function renderSlice(sliceKey) {
  if (!_snaps || !_layer) return;
  const snap = _snaps.byKey.get(sliceKey);
  if (!snap) return;
  _progress = _snaps.keys.indexOf(sliceKey);
  _renderFrame(snap, snap, 1, 1);
}

// ── 播放（time-bar play 按钮驱动）──

/** 播放 fromKey..toKey（rAF lerp 跨片）；每进新片边界调 onSlice(key)；自然结束调 onDone()。 */
export function play(fromKey, toKey, onSlice, onDone) {
  if (!_snaps) return;
  const keys = _snaps.keys;
  const from = Math.max(0, keys.indexOf(fromKey));
  let to = keys.indexOf(toKey);
  if (to < 0 || to <= from) to = keys.length - 1;    // 越界/单段 → 播到末
  _playing = true;
  _playFrom = from; _playTo = to;
  _onSlice = onSlice || null;
  _onDone = onDone || null;
  _segFlashed = -1;
  _lastFiredSeg = from - 1;                          // 首帧 from 片也触发 onSlice
  _playStart = performance.now();
  _tick();
}
/** 停播（用户操作 slider/stop/切粒度/收起时调；清回调不调 onDone）。 */
export function stop() {
  if (!_playing) return;
  _playing = false;
  if (_raf) cancelAnimationFrame(_raf);
  _raf = 0;
  _onSlice = null;
  _onDone = null;
}

// ── 数据 prep：snap-to-grid 聚合所有片进 scaffold，建 per-key snapshot ──

async function _prepare(layer) {
  if (_snaps && _snaps._for === layer.id) return;
  const datasetId = layer.datasetId;
  const keys = datasetId ? slicesOf(datasetId).map((s) => s.key) : [];
  if (!keys.length) { _snaps = null; return; }       // 无数据集/无片 → 不动画（grid 保持原状）
  _busy = true;
  try {
    const scaffold = layer.fc.features;
    const step = (layer.paint && layer.paint._ui && layer.paint._ui.cellSize) || 400;
    const idx = _buildCellIndex(scaffold, step);
    // 拉所有片点集 + 聚合（phase 片少全量；日/周/月密集 → 未来改 lazy，当前 manifest 仅 phase）
    const perKey = {};
    for (const k of keys) {
      const fc = await loadSlice(datasetId, k);
      perKey[k] = fc ? _aggregate(fc.features, idx) : null;
    }
    // 共享 max（跨片可比）
    const maxes = { all: 0, pos: 0, neg: 0, neu: 0 };
    for (const k of keys) {
      const a = perKey[k]; if (!a) continue;
      for (const c of a.cells) {
        if (c.point_count > maxes.all) maxes.all = c.point_count;
        if (c.np > maxes.pos) maxes.pos = c.np;
        if (c.nn > maxes.neg) maxes.neg = c.nn;
        if (c.ne > maxes.neu) maxes.neu = c.ne;
      }
    }
    // 建 per-key virtual fc + KPI snapshot
    const byKey = new Map();
    for (const k of keys) {
      const a = perKey[k];
      const fc = a ? _buildVirtualFc(layer, a, maxes) : _emptyFc(layer);
      byKey.set(k, {
        fc,
        overall: overviewKpiFromFeats(fc.features),
        overallMatrix: overallMatrixFromFeats(fc.features),
        polarities: {
          positive: polarityKpiFromFeats(fc.features, 'positive'),
          negative: polarityKpiFromFeats(fc.features, 'negative'),
          neutral: polarityKpiFromFeats(fc.features, 'neutral'),
        },
      });
    }
    _snaps = { _for: layer.id, step, idx, scaffold, byKey, keys };
  } catch (e) {
    console.error('[timeline] prep 失败：', e);
    _snaps = null;
  } finally {
    _busy = false;
  }
}

function _emptyFc(layer) {
  const fc = { type: 'FeatureCollection', features: layer.fc.features.map((f) => ({ ...f, properties: { ...(f.properties || {}) } })) };
  return fc;
}

// ── snap-to-grid 算法（承重：保留不动）──

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

/** scaffold 几何 + per-片统计 + _grid_*（共享 max）。返回独立 fc（不污染 layer.fc）。 */
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

// ── 渲染（每帧 / 离散）──

/** 检测当前 Overview sub-Tab + 极性。返回 {mode:'layer'|'polarity', pol?}。 */
function _currentMode() {
  const polPane = document.getElementById('ov-polarity-pane');
  if (polPane && polPane.classList.contains('is-active')) {
    const tab = document.querySelector('#ov-polarity-pane .ov-pol-tab.is-active');
    return { mode: 'polarity', pol: (tab && tab.dataset.pol) || 'positive' };
  }
  return { mode: 'layer' };
}

/** 在 progress（0..n-1 连续）处渲染一帧（离散 renderSlice 走 a=b=t=1）。 */
function _renderAt(progress) {
  if (!_snaps || !_layer) return;
  const keys = _snaps.keys, n = keys.length;
  const i = Math.max(0, Math.min(n - 1, Math.floor(progress)));
  const a = _snaps.byKey.get(keys[i]);
  const b = _snaps.byKey.get(keys[Math.min(n - 1, i + 1)]) || a;
  const t = easeInOut(progress - i);
  _renderFrame(a, b, t, t);
}

/** 核心帧渲染：map bars 用 barsT、KPI 用 kpiT（错峰时两者不同步）。 */
function _renderFrame(snapA, snapB, barsT, kpiT) {
  // map：lerp 每 cell 的高度/色字段 → setData。**不 lerp _grid_n_***（极性 filter `_grid_n_*>0`
  //   若 lerp 穿越 0 → cell 闪烁；保持 snapA 值让 filter 稳定，高度/色用 _grid_h_* 平滑过渡）。
  const fa = snapA.fc.features, fb = snapB.fc.features;
  const lerped = new Array(fa.length);
  const flds = ['_grid_h', '_grid_h_pos', '_grid_h_neg', '_grid_h_neu', '_grid_norm', 'polarity_index', 'point_count'];
  for (let i = 0; i < fa.length; i++) {
    const pa = fa[i].properties || {}, pb = (fb[i] && fb[i].properties) || {};
    const props = {};
    for (const k of Object.keys(pa)) props[k] = pa[k];   // 拷贝（含 _grid_n_*/domain_top/element_top 等非动画字段）
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
    // 关键词离散切换：按最近片停点，跨 0.5 才换（避免每帧重渲染、保 flash 动画）
    const kwSnap = barsT < 0.5 ? snapA : snapB;
    if (kwSnap !== _lastKwSnap) { paintOverallKeywords(kwSnap.fc.features); _lastKwSnap = kwSnap; }
  }
}
/** 综合 4×5 矩阵 lerp：n 固定（scaffold 格数跨片不变），pi 均值 lerp（→ 颜色变）。
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

// ── rAF 播放循环（N 片泛化）──

function _tick() {
  if (!_playing || !_snaps) return;
  const keys = _snaps.keys, n = keys.length;
  const elapsed = performance.now() - _playStart;
  const totalSegs = _playTo - _playFrom;
  const totalDur = totalSegs * SEG_DUR;
  if (elapsed >= totalDur) {
    _progress = _playTo;
    _renderAt(_progress);
    _fireOnSlice(Math.round(_progress));        // 末片边界
    const done = _onDone;                        // 捕获后 stop 清空不调
    stop();
    if (done) done();
    return;
  }
  const p = _playFrom + elapsed / SEG_DUR;      // 每段 SEG_DUR ms（段 = 相邻片）
  _progress = p;
  const seg = Math.floor(p);
  // 片边界 onSlice：进入新片（seg 增）→ 通知 time-bar 换点层
  if (seg > _lastFiredSeg && seg <= _playTo) { _fireOnSlice(seg); }
  const segLocal = p - seg;
  const barsT = easeInOut(segLocal);
  const kpiT = easeInOut(Math.max(0, Math.min(1, (segLocal * SEG_DUR - KPI_DELAY) / KPI_WINDOW)));
  if (segLocal >= 0.75 && _segFlashed < seg) { flashOverviewKeywords(); _segFlashed = seg; }
  const a = _snaps.byKey.get(keys[Math.min(n - 1, seg)]);
  const b = _snaps.byKey.get(keys[Math.min(n - 1, seg + 1)]) || a;
  _renderFrame(a, b, barsT, kpiT);
  _raf = requestAnimationFrame(_tick);
}

/** 触发片边界回调（去重：同 seg 不重复）。 */
function _fireOnSlice(seg) {
  if (!_snaps || _onSlice === null) return;
  if (seg === _lastFiredSeg) return;
  _lastFiredSeg = seg;
  const key = _snaps.keys[Math.max(0, Math.min(_snaps.keys.length - 1, seg))];
  if (key) _onSlice(key);
}
