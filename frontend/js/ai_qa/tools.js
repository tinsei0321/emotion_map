// ═══ tools.js — Agent Loop 工具集（查询型 + 操作型，直调主窗口函数）═══
// 还原单窗口后，tools 直调 map/state/panel（删跨窗口协议）。每个 tool 返回 {observation, data?}：
//   observation = 给 LLM 看的摘要字符串（入 tool_history）；data = 结构化（前端可选用于渲染）。
import { getLayers, getSelectedLayer, addLayer, addGroup, removeLayer } from '../state.js';
import { fitBoundsTo, renderLayer, reorderAllZ, removeLayerFromMap } from '../map.js';
import { activateTab, setOverview } from '../panel.js';
import { DOMAIN_LABEL, ELEMENT_LABEL } from '../popup.js';
import { generateGridForAI } from '../grid-tool.js';
import { renderLayerList, refreshLegend } from '../sidebar.js';
import { fcBBox } from '../import.js';

let _lastGrid = null;   // 最近生成聚合层（ensure_zone/query 优先用）

// ── GIS 工具骨干（POST /api/v1/geo/*）═══════════════════════════════════════
let _geoCatalogPromise = null;
const _DOMAIN_CN2EN = { '规划': 'urban_planning', '更新': 'urban_renewal', '运营': 'urban_operation', '治理': 'urban_governance' };

/** GET /api/v1/geo/catalog（模块级缓存，buildContext 增列「边界/时点/工具」用）。 */
export function getGeoCatalog() {
  if (_geoCatalogPromise) return _geoCatalogPromise;
  _geoCatalogPromise = fetch('/api/v1/geo/catalog')
    .then((r) => (r.ok ? r.json() : null))
    .catch(() => null)
    .then((c) => c || null);
  return _geoCatalogPromise;
}

/** GET /api/v1/aiqa/wisdom（模块级缓存，buildContext 增列 L2 答问智慧用）。 */
export function getWisdom() {
  if (_wisdomPromise) return _wisdomPromise;
  _wisdomPromise = fetch('/api/v1/aiqa/wisdom')
    .then((r) => (r.ok ? r.json() : null))
    .catch(() => null)
    .then((w) => (w && w.wisdom_text) || '');
  return _wisdomPromise;
}
let _wisdomPromise = null;

/** POST /api/v1/geo/<path> 取 JSON；失败抛 Error(.detail)。 */
const _LAYER_REF_KEYS = ['layer', 'range', 'layer_a', 'layer_b', 'boundary', 'center', 'target'];
/** 图层引用解析：参数值若匹配前端已加载图层名 → 返回其 geojson（send-in 给后端 resolve_boundary/resolve_points）。
 * 支持 chain——extract 出的"西陵区"图层可直接作为 overlay/clip 的输入。精确匹配优先，否则唯一包含匹配。 */
function ref(v) {
  if (typeof v === 'string' && v) {
    const all = getLayers().filter((x) => x.fc && x.fc.features && x.fc.features.length);
    let l = all.find((x) => x.name === v);
    if (!l) {
      const inc = all.filter((x) => x.name && x.name.includes(v));
      if (inc.length === 1) l = inc[0];   // 唯一包含才匹配，避免歧义
    }
    if (l) return l.fc;
  }
  return v;
}
async function geoFetch(path, body) {
  const b = {};
  for (const k of Object.keys(body || {})) b[k] = _LAYER_REF_KEYS.includes(k) ? ref(body[k]) : body[k];
  const r = await fetch('/api/v1/geo/' + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(b),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((j && (j.detail || j.error)) || ('HTTP ' + r.status));
  return j;
}

/** pre_filter 容错：字符串 'field/op/value'（或 | 分隔）或对象 → 后端 {field,op,value}。 */
function normPreFilter(pf) {
  if (!pf) return undefined;
  let o = pf;
  if (typeof pf === 'string') {
    const parts = pf.split(/[/|]/).map((s) => s.trim()).filter(Boolean);
    if (parts.length < 3) return undefined;
    o = { field: parts[0], op: parts[1], value: parts.slice(2).join('/') };
  }
  if (!o || !o.field || !o.op) return undefined;
  if (o.op === 'in' && typeof o.value === 'string') o.value = o.value.split(',').map((s) => s.trim()).filter(Boolean);
  return o;
}

const _ERR = (name, e) => ({ observation: '[ERR] ' + name + ' 失败：' + ((e && e.message) || e) });
const _fmtPi = (v) => (v !== '' && v != null && !isNaN(v) ? Number(v).toFixed(2) : '?');
const _fmtRow = (row) => {
  const dom = DOMAIN_LABEL[row.domain_top] || row.domain_top || '?';
  const elm = ELEMENT_LABEL[row.element_top] || row.element_top || '?';
  return `  - ${row.name || '未命名'}：极性 ${_fmtPi(row.polarity_index)}，${row.point_count || 0}点，${dom}×${elm}，问题=${row.issue_label || '—'}`;
};


function isAnalysis(l) {
  const ui = l && l.paint && l.paint._ui;
  return !!(l && l.kind === 'polygon' && ui && (ui.tool === 'grid' || ui.tool === 'terrain'));
}
function activeAnalysis() {
  if (_lastGrid && _lastGrid.layerId) {
    const l = getLayers().find((x) => x.id === _lastGrid.layerId);
    if (l) return l;
  }
  const sel = getSelectedLayer();
  if (sel && isAnalysis(sel)) return sel;
  return getLayers().find((l) => isAnalysis(l) && l.fc && l.fc.features && l.fc.features.length) || null;
}
function fitToFeature(f) {
  const g = f && f.geometry;
  if (!g) return;
  const rings = g.type === 'Polygon' ? g.coordinates[0]
    : (g.type === 'MultiPolygon' ? g.coordinates.flatMap((p) => p[0]) : null);
  if (!rings || !rings.length) return;
  let mnX = Infinity, mxX = -Infinity, mnY = Infinity, mxY = -Infinity;
  for (const [x, y] of rings) { if (x < mnX) mnX = x; if (x > mxX) mxX = x; if (y < mnY) mnY = y; if (y > mxY) mxY = y; }
  if (isFinite(mnX)) fitBoundsTo([mnX, mnY, mxX, mxY]);
}

/** AI 工具产出的图层统一归入「AI 工作区」组（复用 state.addGroup；组卡片由 sidebar 现有逻辑渲染）。 */
function _aiGroup() {
  const existing = getLayers().find((l) => l.kind === 'group' && l.name === 'AI 工作区');
  return existing || addGroup({ name: 'AI 工作区' });
}

/** 把 geo 工具产出的 GeoJSON 落地图为新图层（统一回写，复用 range-presets/grid-tool 范式）。
 * 替换语义：同名旧结果层先移除再新建（防重复堆叠）。name=图层名，kind=point|polygon。
 * 点层自动按 polarity 上色（addLayer 默认 colorMode）；面层需传 paint.fillOn 才可见。 */
export function addResultLayer({ name, kind = 'polygon', fc, paint }) {
  if (!fc || !fc.features || !fc.features.length) return null;
  for (const l of getLayers()) {
    if (l.name === name) { removeLayerFromMap(l.id); removeLayer(l.id); }
  }
  const L = addLayer({ name, kind, fc, paint, parentId: _aiGroup().id });
  L.srcName = name;
  renderLayer(L);
  renderLayerList(); refreshLegend(); reorderAllZ();
  const bb = fcBBox(fc); if (bb) fitBoundsTo(bb);
  document.dispatchEvent(new CustomEvent('layers:changed'));
  return L;
}
function pi(f) { return Number((f.properties || {}).polarity_index); }

function sortZones(feats, crit) {
  if (crit === 'worst') return feats.slice().sort((a, b) => pi(a) - pi(b));
  if (crit === 'best') return feats.slice().sort((a, b) => pi(b) - pi(a));
  if (crit.startsWith('domain:')) {
    const d = crit.split(':')[1];
    return feats.slice().sort((a, b) => {
      const pa = String((a.properties || {}).domain_top || '').includes(d) ? 1 : 0;
      const pb = String((b.properties || {}).domain_top || '').includes(d) ? 1 : 0;
      return (pb - pa) || (Math.abs(pi(b)) - Math.abs(pi(a)));
    });
  }
  if (crit.startsWith('element:')) {
    const e = crit.split(':')[1];
    return feats.slice().sort((a, b) => {
      const pa = String((a.properties || {}).element_top || '').includes(e) ? 1 : 0;
      const pb = String((b.properties || {}).element_top || '').includes(e) ? 1 : 0;
      return (pb - pa) || (Math.abs(pi(b)) - Math.abs(pi(a)));
    });
  }
  return feats.slice().sort((a, b) => Math.abs(pi(b)) - Math.abs(pi(a)));
}

/** 格式化 geo catalog → grounding 段（边界 preset / 时点 / GIS 工具清单）。 */
function formatGeoCatalog(cat) {
  if (!cat) return '';
  const out = [];
  const pls = (cat.point_layers || []).filter((p) => p.available !== false);
  if (pls.length) out.push('【可用地层】' + pls.map((p) => {
    const fs = (p.fields || []).slice(0, 14).join('/');
    return `${p.label || p.id}${fs ? `[字段:${fs}]` : ''}`;
  }).join('；'));
  const bds = (cat.boundaries || []).filter((b) => b.available !== false);
  if (bds.length) out.push('【可用边界】' + bds.map((b) => `${b.label || b.id}(按字段 ${b.name_field || 'name'} 抽取/筛选某区某单元)`).join('、'));
  const tls = (cat.tools || []).map((t) => t.name).filter(Boolean);
  if (tls.length) out.push('【可用 GIS 工具】' + tls.join('/') + '（结果自动落地图为新图层）');
  return out.join('\n');
}

/** buildContext：grounding 摘要（panel send + query_layers 共用）。 */
export async function buildContext() {
  const layers = getLayers();
  const an = activeAnalysis();
  const parts = [];
  const loaded = layers
    .filter((l) => l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length)
    .map((l) => `${l.name}(${l.fc.features.length}条)`).join('、');
  parts.push('已加载图层：' + (loaded || '（无）'));
  const geo = formatGeoCatalog(await getGeoCatalog());
  if (geo) parts.push(geo);
  const wisdom = await getWisdom();
  if (wisdom) parts.push(wisdom);
  if (!an) {
    parts.push('（暂无聚合层——区域级问题建议先 ensure_zone 生成）');
    return parts.join('\n');
  }
  const feats = an.fc.features;
  parts.push(`当前分析层：${an.name}（${feats.length} 个聚合单元）`);
  const agg = { 'Very Positive': 0, Positive: 0, Neutral: 0, Negative: 0, 'Very Negative': 0 };
  for (const f of feats) {
    const p = f.properties || {};
    agg['Very Positive'] += p.n_very_positive || 0;
    agg.Positive += p.n_positive || 0;
    agg.Neutral += p.n_neutral || 0;
    agg.Negative += p.n_negative || 0;
    agg['Very Negative'] += p.n_very_negative || 0;
  }
  parts.push(`极性计数：非常积极${agg['Very Positive']} / 积极${agg.Positive} / 中性${agg.Neutral} / 消极${agg.Negative} / 非常消极${agg['Very Negative']}`);
  const top = feats
    .map((f) => f.properties || {})
    .filter((p) => p.polarity_index != null && !isNaN(p.polarity_index))
    .sort((a, b) => Math.abs(b.polarity_index) - Math.abs(a.polarity_index))
    .slice(0, 8);
  if (top.length) {
    parts.push('高张力区域：\n' + top.map((p) => {
      const name = p.name || p.issue_label || '未命名';
      const dom = DOMAIN_LABEL[p.domain_top] || p.domain_top || '?';
      const elm = ELEMENT_LABEL[p.element_top] || p.element_top || '?';
      return `  - ${name}：极性 ${Number(p.polarity_index).toFixed(2)}，${dom}×${elm}，问题=${p.issue_label || '—'}，${p.point_count || 0}点`;
    }).join('\n'));
  }
  return parts.join('\n');
}

export const TOOLS = {
  /** 查当前已加载的图层/数据。 */
  query_layers() {
    const an = activeAnalysis();
    const loaded = getLayers()
      .filter((l) => l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length)
      .map((l) => `${l.name}(${l.fc.features.length}条)`).join('、');
    return { observation: `已加载图层：${loaded || '（无）'}\n当前分析层：${an ? an.name + '（' + an.fc.features.length + ' 单元）' : '暂无聚合层（区域级问题建议 ensure_zone）'}` };
  },

  /** 按维度排序找区域（地图同步飞到）。 */
  query_zone_stats(params = {}) {
    const an = activeAnalysis();
    if (!an || !an.fc) return { observation: '暂无聚合层（建议先 ensure_zone 生成）' };
    const crit = params.criteria || 'worst';
    const top = Math.min(Math.max(Number(params.top) || 3, 1), 10);
    let feats = an.fc.features
      .filter((f) => { const p = f.properties || {}; return p.polarity_index != null && !isNaN(p.polarity_index); });
    if (!feats.length) return { observation: '聚合层无极性数据' };
    feats = sortZones(feats, crit).slice(0, top);
    const found = feats.map((f) => {
      const p = f.properties || {};
      return { name: p.name || p.issue_label || '未命名', pi: Number(p.polarity_index).toFixed(2),
        dom: DOMAIN_LABEL[p.domain_top] || p.domain_top || '?', elm: ELEMENT_LABEL[p.element_top] || p.element_top || '?',
        pc: p.point_count || 0, issue: p.issue_label || '—' };
    });
    feats.forEach((f) => fitToFeature(f));
    const label = { worst: '情绪最差', best: '情绪最好' }[crit] || crit;
    return {
      observation: `${label} Top${top}：\n` + found.map((x) => `  - ${x.name}：极性${x.pi}，${x.dom}×${x.elm}，${x.pc}点，问题=${x.issue}`).join('\n'),
      data: { found },
    };
  },

  /** 查 4×5 归因（全局或某区域）。 */
  query_attribution(params = {}) {
    const an = activeAnalysis();
    if (!an || !an.fc) return { observation: '暂无聚合层' };
    const zone = (params.zone || '').trim();
    let feats = an.fc.features
      .filter((f) => { const p = f.properties || {}; return p.polarity_index != null && !isNaN(p.polarity_index); });
    if (zone) feats = feats.filter((f) => { const nm = (f.properties || {}).name || ''; return nm === zone || nm.includes(zone) || zone.includes(nm); });
    feats = feats.sort((a, b) => Math.abs(pi(b)) - Math.abs(pi(a))).slice(0, 8);
    if (!feats.length) return { observation: zone ? `未找到「${zone}」的归因数据` : '无归因数据' };
    const rows = feats.map((f) => {
      const p = f.properties || {};
      return `  - ${p.name || p.issue_label || '未命名'}：极性${Number(p.polarity_index).toFixed(2)}，${DOMAIN_LABEL[p.domain_top] || p.domain_top}×${ELEMENT_LABEL[p.element_top] || p.element_top}，${p.point_count || 0}点，问题=${p.issue_label || '—'}`;
    });
    return { observation: (zone ? `「${zone}」及相近区域归因` : '高张力区域归因') + '：\n' + rows.join('\n') };
  },

  /** 查关键词/热门话题（按 issue_label 聚合近似）。 */
  query_keywords(params = {}) {
    const an = activeAnalysis();
    if (!an || !an.fc) return { observation: '暂无聚合层' };
    const pol = params.polarity || 'overall';
    let feats = an.fc.features;
    if (pol !== 'overall') feats = feats.filter((f) => {
      const v = Number((f.properties || {}).polarity_index);
      return pol === 'positive' ? v > 0.15 : v < -0.15;
    });
    const kw = {};
    feats.forEach((f) => {
      const p = f.properties || {};
      const k = p.issue_label || '';
      if (k) kw[k] = (kw[k] || 0) + (p.point_count || 1);
    });
    const top = Object.entries(kw).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([k, v]) => `${k}(${v})`).join('、');
    return { observation: `${pol === 'overall' ? '综合' : pol === 'positive' ? '积极' : '消极'}关键词/问题 Top：${top || '（无）'}` };
  },

  /** 生成/确保聚合域（无则生成，有则复用）。 */
  async ensure_zone(params = {}) {
    const existing = activeAnalysis();
    if (existing && existing.fc && existing.fc.features && existing.fc.features.length) {
      return { observation: `复用现有聚合层「${existing.name}」（${existing.fc.features.length} 单元）` };
    }
    try {
      const r = await generateGridForAI({
        analysis: params.analysis === 'zonal' ? 'zonal' : 'square',
        cellSize: Number(params.cell_size) || undefined,
        polarity: params.polarity || 'overall',
        mode: params.mode === '3d' ? '3d' : '2d',
        silent: true,
      });
      _lastGrid = { layerId: r && (r.layerId || r.id) };
      return { observation: `已生成聚合层「${r.layerName}」（${r.featureCount} 单元）` };
    } catch (e) {
      return { observation: '聚合层生成失败：' + (e && e.message ? e.message : e) };
    }
  },

  /** 定位区域到地图（飞到+高亮）。 */
  focus_zones(params = {}) {
    const names = Array.isArray(params.names) ? params.names : [];
    let n = 0;
    names.filter(Boolean).forEach((nm) => {
      for (const l of getLayers()) {
        if (!isAnalysis(l) || !l.fc) continue;
        const f = l.fc.features.find((ff) => { const n2 = (ff.properties || {}).name || ''; return n2 === nm || n2.includes(nm) || nm.includes(n2); });
        if (f) { fitToFeature(f); document.dispatchEvent(new CustomEvent('cell:selected', { detail: { feature: f, layer: l } })); n++; break; }
      }
    });
    return { observation: `已定位 ${n}/${names.length} 个区域` };
  },

  /** 展开 Overview 归因面板。 */
  open_attribution() {
    const an = activeAnalysis();
    if (!an) return { observation: '暂无聚合层' };
    activateTab('overview');
    setOverview(an);
    return { observation: '已展开 Overview 归因面板（4×5 矩阵 + 关键词）' };
  },

  /** 深读某区域明细。 */
  inspect_zone(params = {}) {
    const an = activeAnalysis();
    const name = (params.name || '').trim();
    if (!an || !name) return { observation: '缺区域名或暂无聚合层' };
    const f = an.fc.features.find((ff) => { const nm = (ff.properties || {}).name || ''; return nm === name || nm.includes(name) || name.includes(nm); });
    if (!f) return { observation: `未找到「${name}」` };
    fitToFeature(f);
    document.dispatchEvent(new CustomEvent('cell:selected', { detail: { feature: f, layer: an } }));
    const p = f.properties || {};
    return { observation: `「${name}」深读：极性${Number(p.polarity_index).toFixed(2)}，${DOMAIN_LABEL[p.domain_top] || p.domain_top}×${ELEMENT_LABEL[p.element_top] || p.element_top}，${p.point_count || 0}点，问题=${p.issue_label || '—'}` };
  },

  // ── GIS 工具骨干（POST /api/v1/geo/*，结构化/归因/排序结论主干）─────────────
  /** 宏/中观结论主干：按边界聚合点层，得每单元极性/点数/4×5 归因+排序。 */
  async zonal_stats(params = {}) {
    if (!params.boundary) return { observation: '[ERR] zonal_stats 需 boundary（preset_id）' };
    const body = { layer: params.layer || 'yichang_l2_t1', boundary: params.boundary };
    if (params.range) body.range = params.range;
    const pf = normPreFilter(params.pre_filter); if (pf) body.pre_filter = pf;
    if (params.top_n != null) body.top_n = Number(params.top_n);
    try {
      const r = await geoFetch('zonal_stats', body);
      const rows = r.rows || [];
      if (!rows.length) return { observation: `面域聚合（boundary=${params.boundary}）无结果` };
      return { observation: `面域聚合 ${rows.length} 单元（boundary=${params.boundary}，按 |${r.sort_by || 'polarity_index'}| 降序）：\n` + rows.map(_fmtRow).join('\n'), data: { rows, sort_by: r.sort_by } };
    } catch (e) { return _ERR('zonal_stats', e); }
  },

  /** Top N 排序（最差/最好/按 domain·element 占比）。 */
  async rank(params = {}) {
    let by = params.by || 'worst';
    if (by.startsWith('domain:')) { const cn = by.split(':')[1]; by = 'domain:' + (_DOMAIN_CN2EN[cn] || cn); }
    const body = { layer: params.layer || 'yichang_l2_t1', by, top_n: Number(params.top_n) || 5 };
    if (params.boundary) body.boundary = params.boundary;
    if (params.range) body.range = params.range;
    const pf = normPreFilter(params.pre_filter); if (pf) body.pre_filter = pf;
    try {
      const r = await geoFetch('rank', body);
      const rows = r.rows || [];
      if (!rows.length) return { observation: `排序（by=${by}）无结果` };
      return { observation: `排序 Top${rows.length}（by=${by}）：\n` + rows.map(_fmtRow).join('\n'), data: { rows, by } };
    } catch (e) { return _ERR('rank', e); }
  },

  /** 按属性筛选（用地/极性/domain/element/时点）。 */
  async filter_attr(params = {}) {
    const pf = normPreFilter(params.pre_filter);
    if (!pf) return { observation: '[ERR] filter_attr 需 pre_filter（field/op/value）' };
    const body = { layer: params.layer || 'yichang_l2_t1', pre_filter: pf };
    if (params.range) body.range = params.range;
    try {
      const r = await geoFetch('filter_attr', body);
      const feats = (r.geojson && r.geojson.features) || [];
      const _fName = params.as || `筛选·${pf.field}=${pf.value}`;
      const _fL = addResultLayer({ name: _fName, kind: 'point', fc: r.geojson });
      const sample = feats.slice(0, 3).map((f) => {
        const p = f.properties || {};
        return '{' + Object.keys(p).slice(0, 5).map((k) => `${k}=${p[k]}`).join(', ') + '}';
      });
      return { observation: `属性筛选命中 ${r.count} 个要素${r.truncated ? '（已截断）' : ''} → 已生成图层「${_fName}」${_fL ? '(' + feats.length + '点)' : ''}，示例：${sample.join(' | ') || '（无属性）'}`, data: { count: r.count, layerId: _fL && _fL.id } };
    } catch (e) { return _ERR('filter_attr', e); }
  },

  /** 按几何裁剪（某区/某公园范围内的点），结果落地图为新点图层。 */
  async clip(params = {}) {
    if (!params.range) return { observation: '[ERR] clip 需 range（preset_id|geojson）' };
    const body = { layer: params.layer || 'yichang_l2_t1', range: params.range };
    const pf = normPreFilter(params.pre_filter); if (pf) body.pre_filter = pf;
    try {
      const r = await geoFetch('clip', body);
      const feats = (r.geojson && r.geojson.features) || [];
      const name = params.as || `裁剪·${params.range}`;
      const L = addResultLayer({ name, kind: 'point', fc: r.geojson });
      const sample = feats.slice(0, 3).map((f) => { const p = f.properties || {}; return p.name || p.issue_label || '未命名'; });
      return { observation: `裁剪命中 ${r.count} 个要素${r.truncated ? '（已截断）' : ''}（range=${params.range}）→ 已生成图层「${name}」${L ? '(' + feats.length + '点)' : ''}，示例：${sample.join('、') || '（无）'}`, data: { count: r.count, layerId: L && L.id } };
    } catch (e) { return _ERR('clip', e); }
  },
  /** 从面边界按属性抽单要素为独立面图层（裁出某区/某单元），结果落地图。 */
  async extract_feature(params = {}) {
    if (!params.layer) return { observation: '[ERR] extract_feature 需 layer（preset_id|geojson）' };
    const body = { layer: params.layer };
    if (params.where) body.where = params.where;
    try {
      const r = await geoFetch('extract_feature', body);
      const feats = (r.geojson && r.geojson.features) || [];
      const _nm = (f) => { const p = f.properties || {}; return p.name || p[r.name_field] || Object.values(p).find((v) => typeof v === 'string') || '未命名'; };
      const labels = feats.map(_nm);
      const name = params.as || `抽取·${labels.slice(0, 2).join('/') || params.layer}`;
      const L = addResultLayer({ name, kind: 'polygon', fc: r.geojson, paint: { fillOn: true, lineWidth: 2, fillOpacity: 0.2 } });
      return { observation: `属性抽取命中 ${r.count} 个面要素（layer=${params.layer}${params.where ? ', where=' + params.where : ''}）→ 已生成图层「${name}」${L ? '(' + feats.length + '面)' : ''}：${labels.slice(0, 5).join('、') || '（无）'}`, data: { count: r.count, layerId: L && L.id } };
    } catch (e) { return _ERR('extract_feature', e); }
  },

  /** 各类用地/各单元面积占比。 */
  async area_stats(params = {}) {
    if (!params.boundary) return { observation: '[ERR] area_stats 需 boundary' };
    const body = { boundary: params.boundary };
    if (params.group_by) body.group_by = params.group_by;
    try {
      const r = await geoFetch('area_stats', body);
      const rows = r.rows || [];
      const total = r.total_area_km2 != null ? `（总 ${Number(r.total_area_km2).toFixed(1)} km²）` : '';
      const seg = rows.map((row) => {
        const label = row[params.group_by] || row.name || '组';
        const share = row.share != null ? (Number(row.share) * 100).toFixed(1) + '%' : '?';
        const area = row.area_km2 != null ? Number(row.area_km2).toFixed(1) + 'km²' : '?';
        return `${label} ${share}(${area})`;
      });
      return { observation: `面积统计${total}：${seg.join('、') || '（无）'}`, data: { rows } };
    } catch (e) { return _ERR('area_stats', e); }
  },

  /** 合并/dissolve。 */
  async merge(params = {}) {
    if (!params.boundary) return { observation: '[ERR] merge 需 boundary' };
    const body = { boundary: params.boundary };
    if (params.by) body.by = params.by;
    try {
      const r = await geoFetch('merge', body);
      const feats = (r.geojson && r.geojson.features) || [];
      const total = feats.reduce((a, f) => a + (Number((f.properties || {}).area_km2) || 0), 0);
      const _mName = params.as || `合并·${params.boundary}`;
      const _mL = addResultLayer({ name: _mName, kind: 'polygon', fc: r.geojson, paint: { fillOn: true, lineWidth: 2, fillOpacity: 0.2 } });
      return { observation: `合并得 ${r.count} 个面，总面积 ${total.toFixed(1)} km² → 已生成图层「${_mName}」${_mL ? '(' + feats.length + '面)' : ''}`, data: { count: r.count, layerId: _mL && _mL.id } };
    } catch (e) { return _ERR('merge', e); }
  },

  /** 设施缓冲区。 */
  async buffer(params = {}) {
    if (!params.center) return { observation: '[ERR] buffer 需 center' };
    const body = { center: params.center, radius_m: Number(params.radius_m) || 500 };
    try {
      const r = await geoFetch('buffer', body);
      const feats = (r.geojson && r.geojson.features) || [];
      const area = feats.length ? Number((feats[0].properties || {}).area_km2) || 0 : 0;
      const _bName = params.as || `缓冲·${body.radius_m}m`;
      const _bL = addResultLayer({ name: _bName, kind: 'polygon', fc: r.geojson, paint: { fillOn: true, lineWidth: 2, fillOpacity: 0.2 } });
      return { observation: `缓冲区 radius=${r.radius_m || body.radius_m}m，得 ${feats.length} 个面（约 ${area.toFixed(2)} km²）→ 已生成图层「${_bName}」`, data: { radius_m: r.radius_m, layerId: _bL && _bL.id } };
    } catch (e) { return _ERR('buffer', e); }
  },

  /** 叠置（交/并/差/对称差）。 */
  async overlay(params = {}) {
    if (!params.layer_a || !params.layer_b) return { observation: '[ERR] overlay 需 layer_a + layer_b' };
    const body = { layer_a: params.layer_a, layer_b: params.layer_b, how: params.how || 'intersection' };
    try {
      const r = await geoFetch('overlay', body);
      const feats = (r.geojson && r.geojson.features) || [];
      const total = feats.reduce((a, f) => a + (Number((f.properties || {}).area_km2) || 0), 0);
      const _oName = params.as || `叠置·${body.how}`;
      const _oL = addResultLayer({ name: _oName, kind: 'polygon', fc: r.geojson, paint: { fillOn: true, lineWidth: 2, fillOpacity: 0.25 } });
      return { observation: `叠置(${r.how || body.how}) 得 ${r.count} 个面，总面积 ${total.toFixed(1)} km² → 已生成图层「${_oName}」${_oL ? '(' + feats.length + '面)' : ''}${r.message ? '（' + r.message + '）' : ''}`, data: { count: r.count, layerId: _oL && _oL.id } };
    } catch (e) { return _ERR('overlay', e); }
  },

  /** 最近邻。 */
  async nearest(params = {}) {
    if (!params.target) return { observation: '[ERR] nearest 需 target' };
    const body = { layer: params.layer || 'yichang_l2_t1', target: params.target, k: Number(params.k) || 1 };
    try {
      const r = await geoFetch('nearest', body);
      const rows = r.rows || [];
      if (!rows.length) return { observation: '最近邻无结果' };
      const lines = rows.map((row) => `${row.name || row.issue_label || '点'}(${row.distance != null ? Number(row.distance).toFixed(0) + 'm' : '?'})`);
      return { observation: `最近邻(k=${body.k})：${lines.join('、')}`, data: { rows } };
    } catch (e) { return _ERR('nearest', e); }
  },

  /** Gi* 热点识别。 */
  async hotspot(params = {}) {
    const body = { layer: params.layer || 'yichang_l2_t1', value_col: params.value_col || 'score', invert: params.invert !== false };
    if (params.range) body.range = params.range;
    const pf = normPreFilter(params.pre_filter); if (pf) body.pre_filter = pf;
    try {
      const r = await geoFetch('hotspot', body);
      const feats = (r.geojson && r.geojson.features) || [];
      const tally = {};
      feats.forEach((f) => {
        const p = f.properties || {};
        const cls = p.class || p.classification || p.gi_class || p.hot_cold || p.category || 'ns';
        tally[cls] = (tally[cls] || 0) + 1;
      });
      const dist = Object.keys(tally).length ? Object.entries(tally).map(([k, v]) => `${k}:${v}`).join('、') : `${feats.length}要素`;
      const leg = r.legend ? '（' + Object.entries(r.legend).map(([k, v]) => `${k}=${v}`).join('、') + '）' : '';
      return { observation: `热点分析：${dist}${r.truncated ? '（已截断）' : ''}${leg}`, data: { count: r.count, tally } };
    } catch (e) { return _ERR('hotspot', e); }
  },
};
