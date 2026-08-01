// ═══ toolbox/shared.js — Toolbox 统一工具集层 · 唯一共享基建（手册 v2.2 §5.1）═══
// 抽取自 ai_qa/tools.js（函数去向见 .codebuddy/plans/toolbox-unified-toolset-execution.md §3.2）。
// 依赖红线：toolbox/* 严禁 import ai_qa/*。
// 循环说明：import sidebar（renderLayerList/refreshLegend）为既有模式（grid-tool.js:12 /
// heatmap-tool.js:12 / buffer-tool.js:7 同），二者均 export function 提升声明，ES module
// 循环下仅作运行时调用、不触 TDZ；严禁顶层 const 求值依赖 sidebar export。
import { getLayers, getLayer, addLayer, removeLayer, selectLayer, enforceMutualExclusion, isRangeLayer } from '../state.js';
import * as data_registry from '../data_registry.js';   // R2：统一数据注册表（tool 来源标注）
import { renderLayer, fitBoundsTo, reorderAllZ, removeLayerFromMap } from '../map.js';
import { renderLayerList, refreshLegend, showLayerManager } from '../sidebar.js';
import { fcBBox } from '../import.js';
import { landuseLayerPaint } from '../landuse_colors.js';
import { fetchRangePresets, fetchRangePreset } from '../api.js';
import { piToNorm, polarityStops } from '../grid-tool.js';

// geoPost 实现于 api.js（通用 /api/v1/geo/* POST），此处 re-export 供 toolbox 模块单点引用。
export { geoPost } from '../api.js';

/** 要素名探测（导入面域不改物理列名：MC/区名 等也认——与后端 find_boundary_name_column 同语义优先级）。 */
const _NAME_KEYS = ['name', 'Name', 'NAME', 'MC', '区名', '街道', '社区', '行政区', '单元'];
export function featName(f, i) {
  const p = (f && f.properties) || {};
  for (const k of _NAME_KEYS) {
    if (p[k] != null && p[k] !== '') return String(p[k]);
  }
  return `要素 ${(i ?? 0) + 1}`;
}
/** 合成前归一：features 缺 name 时按 featName 补（buildZonalFc/面积统计按 name 回匹配 rows——
 *  否则 MC 系面域全部特征模糊命中首行（旧 fuzzy fallback 放大器）。 */
export function normalizeGeoNames(geo) {
  if (!geo || !geo.features) return geo;
  return { ...geo, features: geo.features.map((f, i) => {
    const p = f.properties || {};
    return p.name != null && p.name !== '' ? f : { ...f, properties: { ...p, name: featName(f, i) } };
  }) };
}

/** P1（v1.4）：rows + boundary geojson → 合成聚合 polygon FC（每 feature 注入 _grid_norm/polarity_index 供 choropleth 着色）。
 *  仅当 boundary 解析为 GeoJSON（中文名）时合成；preset_id（无 geojson）返 null（只给表格 rows）。
 *  （自 tools.js _buildZonalFc :218 迁移）
 *  v2.1 修：空名特征不再 fuzzy 命中首行（s='' 时 includes('') 恒真→全部特征拿首行极性·数据错误放大器）；
 *  调用方应先用 normalizeGeoNames 补名（zonal/rank 模块已接）。 */
export function buildZonalFc(rows, boundary) {
  const feats = !boundary ? [] : (boundary.type === 'FeatureCollection' ? boundary.features : (boundary.type === 'Feature' ? [boundary] : []));
  if (!feats.length) return null;
  const findRow = (nm) => {
    const s = String(nm || '').trim();
    if (!s) return null;   // v2.1：空名不模糊匹配（防首行放大器）
    return rows.find((r) => String(r.name || '').trim() === s)
      || rows.find((r) => { const rn = String(r.name || '').trim(); return rn && (rn.includes(s) || s.includes(rn)); });
  };
  const out = [];
  for (const f of feats) {
    const nm = (f.properties && f.properties.name) || '';
    const row = findRow(nm);
    const pi = row && row.polarity_index != null && !isNaN(Number(row.polarity_index)) ? Number(row.polarity_index) : null;
    out.push({
      ...f,
      properties: {
        ...(f.properties || {}), name: nm || (row && row.name) || '',
        polarity_index: pi, _grid_norm: pi != null ? piToNorm(pi) : 0.5,
        point_count: row ? (row.point_count || 0) : 0,
        domain_top: row ? row.domain_top : null, element_top: row ? row.element_top : null,
        issue_label: row ? row.issue_label : null,
      },
    });
  }
  return { type: 'FeatureCollection', features: out };
}

const _presetGeoCache = new Map();   // preset_id → 归一化 GeoJSON（properties.name 已对齐·Dumb 缓存）
/** A1 共用：boundary 入参（preset_id | 中文 preset 标签 | 中文要素名 | GeoJSON dict）→ 归一化 GeoJSON（features 带 properties.name）。
 *  解析失败返 null（调用方降级纯表格，不报错·Dumb Tool 不猜）。
 *  §3.3①：中文要素名解析经 resolveName 回调注入（tools.js 委托层注 resolveBoundaryInput）——
 *  本模块不 import ai_qa/*；toolbox 模块直连时中文名须由调用方预解析成 GeoJSON/preset_id。
 *  （自 tools.js _resolveBoundaryGeo :268-294 迁移） */
export async function resolveBoundaryGeo(input, { resolveName } = {}) {
  if (!input) return null;
  if (typeof input === 'object') return input;   // GeoJSON dict 直通
  let pid = String(input);
  if (resolveName) {
    try {
      const via = await resolveName(input);   // 中文要素名 → 单要素 GeoJSON dict；preset_id → 原样 str
      if (via && typeof via === 'object') return via;
      if (typeof via === 'string') pid = via;
    } catch (_) { /* 索引构建失败 → 继续 preset 路径 */ }
  }
  if (_presetGeoCache.has(pid)) return _presetGeoCache.get(pid);
  try {
    const groups = await fetchRangePresets();
    const items = [];
    for (const g of (groups || [])) for (const it of (g.items || [])) items.push(it);
    const hit = items.find((it) => it.id === pid || it.label === pid);   // 中文标签（如「行政区」）→ preset_id
    if (hit) pid = hit.id;
    const res = await fetchRangePreset(pid);
    if (!res || !res.geojson) return null;
    const nf = res.nameField || 'name';
    const fc = { type: 'FeatureCollection', features: (res.geojson.features || []).map((f) => ({ ...f, properties: { ...(f.properties || {}), name: (f.properties || {})[nf] ?? (f.properties || {}).name } })) };
    _presetGeoCache.set(pid, fc);
    return fc;
  } catch (_) { return null; }
}

/** 工具产物层内容签名（B srcId·用户#3 点名两次）：与 main.js _contentSig 同语义——
 *  featureCount + bbox + 前 5 feature 几何/属性键。治仅按 name 去重 → 异名同内容堆叠。
 *  待统一：后续重构移到 state.js 共享，消除与 main.js 重复（两处签名须保持一致·本次不动 main.js）。
 *  （自 tools.js _toolContentSig :421-435 迁移） */
const _r4 = (x) => Math.round(x * 1e4) / 1e4;
export function toolContentSig(fc) {
  const feats = (fc && fc.features) || [];
  const bb = fcBBox(fc);
  const head = feats.slice(0, 5).map((f) => {
    const g = f.geometry || {}; const c = g.coordinates;
    const cSig = Array.isArray(c) ? (typeof c[0] === 'number' ? `${_r4(c[0])},${_r4(c[1])}` : JSON.stringify(c).slice(0, 48)) : '';
    const keys = f.properties ? Object.keys(f.properties).sort().join(',') : '';
    return `${g.type || ''}:${cSig}:${keys}`;
  }).join('|');
  return `${feats.length}|${bb ? bb.map(_r4).join(',') : ''}|${head}`;
}

/** A2 paint 统一：落图层确定性默认（设计语言单一来源·样式不再散落各工具）。
 *  kind=line → 关联连线（#ff9000 标注色·非数据编码）；tool=zonal/rank → 极性 choropleth（复用 grid 着色管线）；
 *  其余面结果 → 浅填充描边。buffer 等带 _ui 元数据的工具自行展开合并（{...defaultPaint(...), _ui}）。
 *  （自 tools.js _defaultPaint :437-447 迁移） */
export function defaultPaint(tool, kind) {
  if (kind === 'line') return { color: '#ff9000', lineWidth: 2 };
  if (tool === 'zonal' || tool === 'rank') {
    return { _ui: { tool: 'zonal' }, fillOn: true, fillOpacity: 0.72, lineWidth: 1, lineOpacity: 0.6,
      gridField: '_grid_norm', gridStops: polarityStops('overall') || [] };
  }
  return { fillOn: true, lineWidth: 2, fillOpacity: 0.2 };
}
/** A2 落图自检备注：渲染异常（partial/failed）时给 observation 追加中文提示（渲染层标记·不触出口裁定承重）。
 *  （自 tools.js _renderNote :448-451 迁移） */
export function renderNote(L) {
  return (L && L._renderState && L._renderState !== 'ok') ? '（注意：落图异常，图层已入列表但可能未正确渲染）' : '';
}

/** A3 尺度表（确定性钳制·K3 §4.3）：按范围/对象名推断分析尺度默认半径（米）。
 *  社区/街道级 250 · 行政区/单元/片区 500 · 主城/全域 1000（ tier 序敏感：先细后粗）。
 *  LLM 显式给值时经 clampM 钳到 [50, 5000] 合理域（双保险·Dumb Tool 不盲信数值参数）。
 *  （自 tools.js _SCALE_TABLE/_scaleRadius/_clampM :453-466 迁移） */
export const SCALE_TABLE = [
  { re: /社区|街道|小区|公园|广场|学校/, radius: 250 },
  { re: /主城|城区|中心|全域|全市|宜昌/, radius: 1000 },
  { re: /区|单元|片区/, radius: 500 },
];
export function scaleRadius(hint) {
  const s = String(hint || '');
  for (const t of SCALE_TABLE) if (t.re.test(s)) return t.radius;
  return null;
}
export function clampM(v) { return Math.min(5000, Math.max(50, Math.round(v))); }

/** 通用落图（手册 §3.3②·自 tools.js addResultLayer :473-519 拆出）：签名去重 + 用地国标色覆写 +
 *  addLayer/renderLayer + 落图自检 _renderState + renderLayerList/refreshLegend/reorderAllZ + 缩放 + layers:changed。
 *  不含 EMC 簿记（_ui.tool 注入/registry/$n/keep/consumed/focusOnlyResults——由 tools.js addResultLayer 叠加）。
 *  parentId 可选（addResultLayer 传 _aiGroup().id）；fit=false 时本层不缩放（调用方自行并集缩放）。 */
export function addToolboxLayer({ name, kind = 'polygon', fc, paint, colorMode, parentId, fit = true }) {
  if (!fc || !fc.features || !fc.features.length) return null;
  const _sig = toolContentSig(fc);   // B srcId：异名同内容也去重（治仅按 name 去重漏洞·用户#3）
  for (const l of getLayers()) {
    if (l.name === name || l.srcId === _sig) { removeLayerFromMap(l.id); removeLayer(l.id); }
  }
  // 用地层自动附制图规范标准色（任何工具产物：extract/clip/filter/overlay/merge/buffer…）。
  // kind=polygon 且检测为用地（有 DLMC 或层名含用地关键词）→ 标准色覆盖默认 paint 的 color/fillOpacity。
  let _paint = paint;
  if (kind === 'polygon') {
    const _lu = landuseLayerPaint(fc, name);
    if (_lu) _paint = { ...(paint || {}), ..._lu };
  }
  const L = addLayer({ name, kind, fc, paint: _paint, colorMode, ...(parentId ? { parentId } : {}) });
  L.srcName = name;
  L.srcId = _sig;   // 工具产物层挂 srcId（与 main.js 导入层同语义·供 EMC grounding + 后续去重）
  data_registry.register({ name, kind, source: 'tool', fc, layerId: L.id });   // R2：登记工具产物（registry 标来源）
  renderLayer(L);
  // A2 落图自检（渲染层标记·不触出口裁定承重）：bbox 越界（WGS84 合法域外）→ partial；
  // renderLayer addSource 失败（map.js 已标 _renderState=failed）→ 告警。observation 侧经 renderNote 消费。
  const _bb = fcBBox(fc);
  const _bboxBad = !!_bb && !(_bb[0] >= -180 && _bb[2] <= 180 && _bb[1] >= -90 && _bb[3] <= 90);
  if (_bboxBad || L._renderState !== 'ok') {
    L._renderState = _bboxBad ? 'partial' : (L._renderState || 'failed');
    console.warn('[addToolboxLayer] 落图异常:', name, L._renderState, _bboxBad ? 'bbox 越界' : '');
  }
  renderLayerList(); refreshLegend(); reorderAllZ();
  if (fit && _bb) fitBoundsTo(_bb, 100, 16);
  document.dispatchEvent(new CustomEvent('layers:changed'));
  return L;
}

/** 工具产物落位（手册 §4.2 骨架配套·新建或原地更新）：addToolboxLayer 通用落图 + 同类互斥 + 可选选中。
 *  editLayerId 命中且同 _ui.tool → 原地更新（layer id 稳定·镜像「继续编辑」）；否则新建。
 *  silent=false（UI 路径）时 selectLayer + showLayerManager + layer:selected 超链。 */
export function placeToolLayer({ name, kind = 'polygon', fc, paint, colorMode, editLayerId = '', silent = true }) {
  if (!fc || !fc.features || !fc.features.length) return null;   // 空结果守卫（镜像 addResultLayer :474·0 命中 filter/clip/overlay 不崩）
  const editingLayer = editLayerId ? getLayer(editLayerId) : null;
  const tool = paint && paint._ui && paint._ui.tool;
  if (editingLayer && tool && editingLayer.paint && editingLayer.paint._ui && editingLayer.paint._ui.tool === tool) {
    editingLayer.fc = fc;
    editingLayer.paint = paint;
    editingLayer.name = name;
    removeLayerFromMap(editLayerId);
    renderLayer(editingLayer);
    if (!silent) {
      selectLayer(editLayerId);
      document.dispatchEvent(new CustomEvent('layers:changed'));
      document.dispatchEvent(new CustomEvent('layer:selected', { detail: editLayerId }));
    }
    const bb = fcBBox(fc); if (bb) fitBoundsTo(bb);
    return editingLayer;
  }
  const L = addToolboxLayer({ name, kind, fc, paint, colorMode });
  for (const hid of enforceMutualExclusion(L.id)) { const hl = getLayer(hid); if (hl) renderLayer(hl); }
  if (!silent) {
    selectLayer(L.id);
    showLayerManager();
    document.dispatchEvent(new CustomEvent('layer:selected', { detail: L.id }));
  }
  return L;
}

// ── 数据源/边界收集（toolbox 各模块 dialog 共用）──
/** 情绪点层源（镜像 grid-tool collectSources：L2 group 合并极性子层 + L1/L2 单点层）。 */
export function collectPointSources() {
  const sources = [];
  for (const l of getLayers()) {
    if (l.kind === 'group' && l.children && l.children.length) {
      let merged = [];
      for (const cid of l.children) {
        const child = getLayer(cid);
        if (child && child.fc && child.fc.features.length) merged = merged.concat(child.fc.features);
      }
      if (merged.length) sources.push({
        value: `group:${l.id}`, label: l.name, level: 'L2', srcName: l.srcName || l.name,
        fc: { type: 'FeatureCollection', features: merged },
      });
    } else if (l.kind === 'point' && l.fc && l.fc.features.length &&
               (l.colorMode === 'l2-positive' || l.colorMode === 'l2-negative' || l.colorMode === 'l2-neutral' ||
                l.colorMode === 'confidence')) {
      sources.push({
        value: `layer:${l.id}`, label: l.name, srcName: l.srcName || l.name,
        level: l.colorMode === 'confidence' ? 'L1' : 'L2', fc: l.fc,
      });
    }
  }
  return sources;
}

/** 聚合边界源（已载 Range 面层 + 预设库合并；preset 的 GeoJSON 懒取 boundarySourceGeo）。 */
export async function collectBoundarySources() {
  const out = getLayers()
    .filter((l) => l.kind === 'polygon' && isRangeLayer(l) && l.fc && l.fc.features && l.fc.features.length)
    .map((l) => ({ value: `layer:${l.id}`, label: l.name, fc: l.fc }));
  try {
    const groups = await fetchRangePresets();
    for (const g of (groups || [])) {
      for (const it of (g.items || [])) {
        if (it.available) out.push({ value: `preset:${it.id}`, label: `${it.label || it.id}（预设）`, presetId: it.id });
      }
    }
  } catch (_) { /* 预设库不可达 → 仅用已载面层 */ }
  return out;
}

/** 边界源 → GeoJSON（layer 直通；preset 经 /range/preset 取）。 */
export async function boundarySourceGeo(src) {
  if (!src) return null;
  if (src.fc) return src.fc;
  if (src.presetId) {
    try {
      const res = await fetchRangePreset(src.presetId);
      return (res && res.geojson) || null;
    } catch (_) { return null; }
  }
  return null;
}
