// ═══ time-source.js — 全局时间轴 · 数据层（TimeSource 抽象 + GeoJSON 实现）═══════════════
// 时间是一等公民：时间片从 manifest「发现」，不写死 T1/T2/T3。本模块是 Track A（GeoJSON）
// 与 Track B（MVT/矢量瓦片）的接缝——上层（timeline / time-bar / panel）只调本模块接口，
// 换后端实现时上层零改动。
//
// 职责（纯数据，不碰渲染）：
//   1. loadManifest() — 拉 DATA/processed/_time_manifest.json（单一权威源），缓存。
//   2. matchDataset(srcName) — 层文件名 → manifest 数据集 + slice key（按 sourceTemplate 正则匹配）。
//   3. tagLayer(layer) — 给导入层打 datasetId/sliceKey 标（替换 deriveTimeTag 文件名猜测的脆弱逻辑）。
//   4. loadSlice(datasetId, sliceKey) — 按片拉 FeatureCollection，带内存缓存（fetch force-cache 双层）。
//   5. datasetOf / slicesOf / periodOf — 同步查询（UI 渲染用，等 manifest 就绪后调用）。
//   6. applyTime(period, sliceKey) — 全局时间控制器：setCurrentTime + 换源所有时间感知点/面层。
//
// 承重：paint-inplace-swap-view（换源走 setData，不重建层）—— applyTime 经 map.updateGridSourceData 守。
// 详见 plan 07-19-cb-lovely-quiche.md / revision-log §0「全局时间轴」分支。

import { getLayers, setCurrentTime } from './state.js';
import { updateGridSourceData } from './map.js';

const MANIFEST_URL = '/DATA/processed/_time_manifest.json';

let _manifest = null;          // manifest 对象（datasets 数组）
let _manifestLoading = null;   // 进行中的 Promise（防重复拉）
const _sliceCache = new Map(); // `${datasetId}|${sliceKey}` → FeatureCollection

// ── manifest ──

/** 拉 manifest（幂等，重复调返回同一 Promise）。main.js 启动时调一次。 */
export function loadManifest() {
  if (_manifest) return Promise.resolve(_manifest);
  if (_manifestLoading) return _manifestLoading;
  _manifestLoading = fetch(MANIFEST_URL, { cache: 'force-cache' })
    .then((r) => { if (!r.ok) throw new Error('manifest HTTP ' + r.status); return r.json(); })
    .then((m) => { _manifest = m; return m; })
    .catch((e) => { console.error('[time-source] manifest 拉取失败：', e); _manifestLoading = null; throw e; });
  return _manifestLoading;
}

/** 同步取已就绪 manifest（未就绪返 null）。UI 渲染前先判 isManifestReady()。 */
export function getManifest() { return _manifest; }
export function isManifestReady() { return !!_manifest; }

/** manifest 里所有数据集（就绪后同步取）。 */
export function datasets() {
  return (_manifest && Array.isArray(_manifest.datasets)) ? _manifest.datasets : [];
}

// ── 层 ↔ 数据集匹配（sourceTemplate → 正则）──

/** sourceTemplate basename（去目录 + 去 .geojson）→ 把 {slice} 拆成捕获组的正则。
 *  "yichang_L2_{slice}_L2_result_geojson" → /^yichang_L2_([A-Za-z0-9_\-]+)_L2_result_geojson$/
 *  模板须含且仅含一个 {slice}；否则返回 null（该数据集不参与文件名匹配）。 */
function _templateRegex(dataset) {
  const base = String(dataset.sourceTemplate || '').split('/').pop().replace(/\.geojson$/i, '');
  const parts = base.split('{slice}');
  if (parts.length !== 2) return null;
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  try { return new RegExp('^' + esc(parts[0]) + '([A-Za-z0-9_\\-]+)' + esc(parts[1]) + '$'); }
  catch (e) { return null; }
}

/** 层 srcName（或 name）→ { datasetId, sliceKey }；未匹配返 null。
 *  遍历 datasets，首个正则命中即返。manifest 未就绪返 null（层暂不打标，后续不参与时间过滤）。
 *  注意：layerName()（main.js）对普通文件上传不去扩展名 → srcName 带 .geojson/.csv 等；
 *  此处先剥常见扩展名再匹配（模板正则是按去 ext 的 basename 生成的）。 */
export function matchDataset(srcName) {
  if (!srcName || !_manifest) return null;
  const clean = String(srcName).replace(/\.(geojson|json|csv|kml|gpx|topojson|shp)$/i, '');
  for (const d of datasets()) {
    const re = _templateRegex(d);
    if (!re) continue;
    const m = re.exec(clean);
    if (m) return { datasetId: d.id, sliceKey: m[1] };
  }
  return null;
}

// ── 层打标（导入时调）──

/** 给层打时间标：layer.datasetId / layer.sliceKey。
 *  优先用 matchDataset(srcName)；srcName 缺则 fallback deriveTimeTag(fc) 当 sliceKey（datasetId=null）。
 *  返回 layer 本身（链式）。无 manifest 时静默跳过（不阻塞导入）。 */
export function tagLayer(layer) {
  if (!layer) return layer;
  const srcName = layer.srcName || layer.name || '';
  const hit = matchDataset(srcName);
  if (hit) { layer.datasetId = hit.datasetId; layer.sliceKey = hit.sliceKey; return layer; }
  // fallback：feature 自带 time_label（T1/T2/T3）但文件名不匹配模板 → 仅记 sliceKey，datasetId 留空
  //   （仍可参与「同 sliceKey 过滤」，但不能跨片换源）
  try {
    const p = layer.fc && layer.fc.features && layer.fc.features[0] && layer.fc.features[0].properties;
    if (p && p.time_label) { layer.sliceKey = String(p.time_label); }
  } catch (e) { /* ignore */ }
  return layer;
}

// ── 按片加载（带缓存）──

/** 拉 (datasetId, sliceKey) 的 FeatureCollection。命中缓存直返；否则按 sourceTemplate 拼 URL fetch。
 *  数据集/slice 不存在或拉取失败返 null（调用方兜底，不崩）。 */
export function loadSlice(datasetId, sliceKey) {
  if (!datasetId || !sliceKey) return Promise.resolve(null);
  const ck = datasetId + '|' + sliceKey;
  const cached = _sliceCache.get(ck);
  if (cached) return Promise.resolve(cached);
  const d = datasetOf(datasetId);
  if (!d) return Promise.resolve(null);
  const has = (d.slices || []).some((s) => s.key === sliceKey);
  if (!has) return Promise.resolve(null);
  const url = d.sourceTemplate.replace('{slice}', sliceKey);
  return fetch(url, { cache: 'force-cache' })
    .then((r) => { if (!r.ok) throw new Error('slice HTTP ' + r.status); return r.json(); })
    .then((fc) => { _sliceCache.set(ck, fc); return fc; })
    .catch((e) => { console.error('[time-source] loadSlice 失败', datasetId, sliceKey, e); return null; });
}

/** 清某数据集的切片缓存（数据更新时调；当前无热更新场景，预留）。 */
export function invalidateDataset(datasetId) {
  for (const k of Array.from(_sliceCache.keys())) {
    if (k.indexOf(datasetId + '|') === 0) _sliceCache.delete(k);
  }
}

// ── 同步查询（UI 用）──

export function datasetOf(datasetId) {
  return datasets().find((d) => d.id === datasetId) || null;
}
export function slicesOf(datasetId) {
  const d = datasetOf(datasetId); return d ? (d.slices || []) : [];
}
export function periodOf(datasetId) {
  const d = datasetOf(datasetId); return d ? d.period : null;
}
/** manifest 里出现过的所有 period（去重，保序）—— time-bar 粒度胶囊条只显这些。 */
export function availablePeriods() {
  const seen = new Set(); const out = [];
  for (const d of datasets()) { if (d.period && !seen.has(d.period)) { seen.add(d.period); out.push(d.period); } }
  return out;
}

/** 某 period 下所有片的并集（跨数据集去重 by key，按 order 升序）。
 *  time-bar 的停点/日历/滑动条都基于此——所有同粒度数据集的片汇成一条时间轴。 */
export function slicesForPeriod(period) {
  const map = new Map();
  for (const d of datasets()) {
    if (d.period !== period) continue;
    for (const s of (d.slices || [])) {
      if (!map.has(s.key)) map.set(s.key, { key: s.key, label: s.label || s.key, order: s.order ?? 999 });
    }
  }
  return Array.from(map.values()).sort((a, b) => a.order - b.order);
}

const PERIOD_LABEL = { phase: '阶段', day: '日', week: '周', month: '月', quarter: '季', year: '年', 'custom-range': '自选' };
/** period → 中文胶囊标签（time-bar 粒度条用）。未知 period 原样返回。 */
export function periodLabel(period) { return PERIOD_LABEL[period] || period; }

// ── 全局时间控制器（applyTime：换源所有时间感知点/面层）──

// L2 极性子层 → 该子层保留的极性集合（slice fc 含全极性，子层只显其一 → 按 colorMode 重切）。
const _POL_SETS = {
  'l2-positive': new Set(['Positive', 'Very Positive']),
  'l2-neutral': new Set(['Neutral']),
  'l2-negative': new Set(['Negative', 'Very Negative']),
};
function _filterPolarity(fc, set) {
  if (!set || !fc) return fc;
  const feats = (fc.features || []).filter((f) => {
    const p = f.properties && f.properties.polarity;
    return p && set.has(p);
  });
  return { ...fc, features: feats };
}

/** 应用全局时间片：setCurrentTime（emit time:changed）+ 换源所有时间感知点/面层。
 *  - grid/terrain 层跳过：由 timeline.js 监听 time:changed 重聚合（A3）。
 *  - L2 极性子层按 colorMode 重切极性。
 *  - 承重 paint-inplace-swap-view：走 updateGridSourceData（= getSource().setData），不重建层/不碰 tip·选中。
 *  - silent=true（grid 焦点时）：跳过 layers:changed dispatch——避与 timeline._renderFrame 抢刷 Overview
 *    （grid 层 fc 不随 renderSlice 更新，dispatch 会用旧 fc 覆盖 _renderFrame 的正确 Overview 画）。
 *    点焦点时 silent=false：dispatch → refreshOverview 读焦点点层新 fc 追随。
 *  loadSlice 失败（fc=null）静默跳过（兜底不崩）。返回 Promise（调用方可 await，也可忽略）。 */
export function applyTime(period, sliceKey, silent = false) {
  setCurrentTime({ period, sliceKey });
  const tasks = [];
  for (const layer of getLayers()) {
    if (!layer.datasetId || layer.kind === 'group') continue;
    if (!slicesOf(layer.datasetId).some((s) => s.key === sliceKey)) continue;   // 该数据集无此片 → 跳过
    const tool = layer.paint && layer.paint._ui && layer.paint._ui.tool;
    if (tool === 'grid' || tool === 'terrain') continue;   // grid/terrain 由 timeline.js 处理（A3）
    tasks.push(loadSlice(layer.datasetId, sliceKey).then((fc) => {
      if (!fc) return;
      const out = _filterPolarity(fc, _POL_SETS[layer.colorMode]);
      layer.fc = out;
      layer.sliceKey = sliceKey;
      updateGridSourceData(layer, out);   // 点/面层也走 lyrSrc setData（函数名 legacy，实为通用换源）
    }));
  }
  const done = Promise.all(tasks);
  if (silent) return done;   // grid 焦点：不 dispatch（避抢刷 _renderFrame 的 Overview）
  return done.then(() => document.dispatchEvent(new CustomEvent('layers:changed')));   // 点焦点：追随新 fc
}
