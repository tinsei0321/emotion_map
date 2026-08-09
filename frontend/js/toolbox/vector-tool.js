// ═══ toolbox/vector-tool.js — 矢量 GIS 五操作合一（手册 v2.2 §5.5）═══
// overlay 叠置 / clip 裁剪 / extract_feature 抽取 / merge 合并 / filter_attr 筛选。
// 单一执行核 _execute 按 op 分派（§4.2）；UI dialog 与 5 个 ForAI 入口共用。
// _ui.tool = 各操作名（§4.3），编辑分派全路由 openVectorDialog，按 _ui 参数回填操作卡。
// extract 字段预校验（getFieldCard）属 LLM 恢复链，留 tools.js 委托层（§5.5），模块不做。
import { getLayer, getLayers } from '../state.js';
import { geoPost, defaultPaint, placeToolLayer,
  collectPointSources, collectBoundarySources, boundarySourceGeo } from './shared.js';
import { renderColorPicker } from '../settings.js';
import { openParamPanel, closeParamPanel } from '../param-panel.js';
import { trackGeneration } from '../geocode-loader.js';
import { toast } from '../toast.js';

const dialogEl = () => document.getElementById('vector-dialog');
const DEFAULT_COLOR = '#4FC3F7';
const OPS = ['overlay', 'clip', 'extract_feature', 'merge', 'filter_attr'];
const HOW_CN = { intersection: '交', union: '并', difference: '差', symmetric_difference: '对称差' };

let _ptSources = [];    // 点层源（clip/filter）
let _polySources = [];  // 面/边界源（overlay A/B、extract、merge、clip range、filter range）
let _vecColor = DEFAULT_COLOR;

const _lab = (x) => (typeof x === 'string' ? x : (x && x.name) || '图层');
const _srcLabel = (src) => (src ? (src.cleanLabel || src.label) : '');
function _polyPaint(op, ui, style) {
  return style && style.color
    ? { color: style.color, fillOn: true, fillOpacity: style.fillOpacity ?? 0.2, lineWidth: 2, _ui: ui }
    : { ...defaultPaint(op, 'polygon'), _ui: ui };
}

// ── 五操作实现（现状 tools.js 各工具 geoFetch body/命名/属性逻辑随迁）──

async function _opOverlay(params, ctx) {
  const body = { layer_a: params.layer_a, layer_b: params.layer_b, how: params.how || 'intersection' };
  const r = await (ctx.silent ? geoPost('overlay', body) : trackGeneration(geoPost('overlay', body)));
  const feats = (r.geojson && r.geojson.features) || [];
  const total = feats.reduce((a, f) => a + (Number((f.properties || {}).area_km2) || 0), 0);
  const howCN = HOW_CN[body.how] || body.how;
  const name = params.as || `${howCN}·${_lab(params.layer_a_label || params.layer_a)}与${_lab(params.layer_b_label || params.layer_b)}`;
  const ui = { tool: 'overlay', layerAId: params.layerAId, layerALabel: params.layer_a_label,
    layerBId: params.layerBId, layerBLabel: params.layer_b_label, how: body.how, style: params.style };
  const L = placeToolLayer({ name, kind: 'polygon', fc: r.geojson, paint: _polyPaint('overlay', ui, params.style), ...ctx });
  return { layerId: L && L.id, layerName: name, featureCount: feats.length, fc: r.geojson,
    count: r.count, totalAreaKm2: total, how: r.how || body.how, message: r.message };
}

async function _opClip(params, ctx) {
  const body = { layer: params.layer, range: params.range };
  if (params.pre_filter) body.pre_filter = params.pre_filter;
  const r = await (ctx.silent ? geoPost('clip', body) : trackGeneration(geoPost('clip', body)));
  const feats = (r.geojson && r.geojson.features) || [];
  const name = params.as || (typeof params.range === 'string' ? params.range : (params.rangeLabel || '范围裁剪'));
  const ui = { tool: 'clip', sourceId: params.sourceId, sourceLabel: params.sourceLabel,
    rangeId: params.rangeId, rangeLabel: params.rangeLabel, pre_filter: params.pre_filter };
  // P1-5（CB-11 用户测试③·族 D）：样式继承——clip 裁出情绪点须继承源层 colorMode + 图例 paint（5 级极性·大小/颜色/线框/透明度）
  //   严格用固化图例·不临时创造样式。源层 = params.sourceId（layer id）或 params.layer（id/name）。
  let _inherit = null;
  const _srcRef = params.sourceId || (typeof params.layer === 'string' ? params.layer : null);
  if (_srcRef && getLayer) {
    const _src = getLayer(_srcRef) || (getLayers && getLayers().find((l) => l.id === _srcRef || l.name === _srcRef));
    if (_src && _src.kind === 'point' && typeof _src.colorMode === 'string' && (_src.colorMode.indexOf('l2-') === 0 || _src.colorMode === 'polarity')) {
      _inherit = { colorMode: _src.colorMode, paint: _src.paint || {} };   // 继承源层极性样式
    }
  }
  const _paint = _inherit ? { ...(_inherit.paint || {}), _ui: ui } : { _ui: ui };
  const L = placeToolLayer({ name, kind: 'point', fc: r.geojson, colorMode: _inherit ? _inherit.colorMode : undefined, paint: _paint, ...ctx });
  return { layerId: L && L.id, layerName: name, featureCount: feats.length, fc: r.geojson,
    count: r.count, truncated: r.truncated };
}

async function _opExtract(params, ctx) {
  const body = { layer: params.layer };
  if (params.where) body.where = params.where;
  const r = await (ctx.silent ? geoPost('extract_feature', body) : trackGeneration(geoPost('extract_feature', body)));
  const feats = (r.geojson && r.geojson.features) || [];
  const nm = (f) => { const p = f.properties || {}; return p.name || p[r.name_field] || Object.values(p).find((v) => typeof v === 'string') || '未命名'; };
  const labels = feats.map(nm);
  const name = params.as || (labels.slice(0, 2).join('·') || _lab(params.sourceLabel || params.layer));
  const ui = { tool: 'extract_feature', sourceId: params.sourceId, sourceLabel: params.sourceLabel,
    where: params.where, style: params.style };
  const L = placeToolLayer({ name, kind: 'polygon', fc: r.geojson, paint: _polyPaint('extract_feature', ui, params.style), ...ctx });
  return { layerId: L && L.id, layerName: name, featureCount: feats.length, fc: r.geojson,
    count: r.count, nameField: r.name_field, labels };
}

async function _opMerge(params, ctx) {
  const body = {};
  if (params.boundary) body.boundary = params.boundary;
  if (params.layers) body.layers = params.layers;   // CB-11：多图层 concat
  if (params.by) body.by = params.by;
  const r = await (ctx.silent ? geoPost('merge', body) : trackGeneration(geoPost('merge', body)));
  const feats = (r.geojson && r.geojson.features) || [];
  const total = feats.reduce((a, f) => a + (Number((f.properties || {}).area_km2) || 0), 0);
  const name = params.as || String(params.boundaryLabel || params.boundary || '合并范围');
  const ui = { tool: 'merge', boundaryId: params.boundaryId, boundaryLabel: params.boundaryLabel,
    by: params.by, style: params.style };
  const L = placeToolLayer({ name, kind: 'polygon', fc: r.geojson, paint: _polyPaint('merge', ui, params.style), ...ctx });
  return { layerId: L && L.id, layerName: name, featureCount: feats.length, fc: r.geojson,
    count: r.count, totalAreaKm2: total };
}

async function _opFilter(params, ctx) {
  const body = { layer: params.layer, pre_filter: params.pre_filter };
  if (params.range) body.range = params.range;
  const r = await (ctx.silent ? geoPost('filter_attr', body) : trackGeneration(geoPost('filter_attr', body)));
  const feats = (r.geojson && r.geojson.features) || [];
  const name = params.as || String((params.pre_filter && (params.pre_filter.value || params.pre_filter.field)) || '属性筛选');
  const ui = { tool: 'filter_attr', sourceId: params.sourceId, sourceLabel: params.sourceLabel,
    pre_filter: params.pre_filter, rangeId: params.rangeId, rangeLabel: params.rangeLabel };
  const L = placeToolLayer({ name, kind: 'point', fc: r.geojson, paint: { _ui: ui }, ...ctx });
  return { layerId: L && L.id, layerName: name, featureCount: feats.length, fc: r.geojson,
    count: r.count, truncated: r.truncated };
}

// ═══ 单一执行核（§4.2）═══
async function _execute(params, { editLayerId = '', silent = true } = {}) {
  const ctx = { editLayerId, silent };
  switch (params.op) {
    case 'overlay': return _opOverlay(params, ctx);
    case 'clip': return _opClip(params, ctx);
    case 'extract_feature': return _opExtract(params, ctx);
    case 'merge': return _opMerge(params, ctx);
    case 'filter_attr': return _opFilter(params, ctx);
    default: throw new Error(`未知矢量操作: ${params.op}`);
  }
}

/** EMC 委托唯一接口（§4.1 契约·五入口）。 */
export async function generateOverlayForAI(opts = {}) { return _execute({ ...opts, op: 'overlay' }, { editLayerId: opts.editLayerId || '', silent: opts.silent ?? true }); }
export async function generateClipForAI(opts = {}) { return _execute({ ...opts, op: 'clip' }, { editLayerId: opts.editLayerId || '', silent: opts.silent ?? true }); }
export async function generateExtractForAI(opts = {}) { return _execute({ ...opts, op: 'extract_feature' }, { editLayerId: opts.editLayerId || '', silent: opts.silent ?? true }); }
export async function generateMergeForAI(opts = {}) { return _execute({ ...opts, op: 'merge' }, { editLayerId: opts.editLayerId || '', silent: opts.silent ?? true }); }
export async function generateFilterForAI(opts = {}) { return _execute({ ...opts, op: 'filter_attr' }, { editLayerId: opts.editLayerId || '', silent: opts.silent ?? true }); }

// ═══ UI dialog ═══

function setHidden(dlg, sel, hidden) { const el = dlg.querySelector(sel); if (el) el.hidden = hidden; }
function selectedOp(dlg) { return dlg.querySelector('#vec-op .buf-cap.is-sel')?.dataset.op || 'overlay'; }

/** 参数区按操作显隐（镜像 grid constrainParams）；样式组仅 polygon 结果显示。 */
function constrainOp(dlg) {
  const op = selectedOp(dlg);
  dlg.querySelectorAll('[data-vop-pane]').forEach((p) => { p.hidden = p.dataset.vopPane !== op; });
  setHidden(dlg, '#vec-style-group', op === 'clip' || op === 'filter_attr');
}

function renderVecColor(dlg, current = DEFAULT_COLOR) {
  const box = dlg.querySelector('#vec-color-list');
  if (!box) return;
  _vecColor = current;
  renderColorPicker(box, { current, onPick: (hex) => { _vecColor = hex; } });
}

function populatePtSources(dlg, selValue) {
  _ptSources = collectPointSources();
  const opts = _ptSources.length
    ? _ptSources.map((s) => `<option value="${s.value}">${s.label}</option>`).join('')
    : '<option value="" disabled>（暂无情绪点层）</option>';
  for (const id of ['#vec-clip-source', '#vec-flt-source']) {
    const sel = dlg.querySelector(id);
    if (sel) { sel.innerHTML = opts; if (selValue && _ptSources.some((s) => s.value === selValue)) sel.value = selValue; }
  }
  populatePfFields(dlg, '#vec-clip-source', '#vec-clip-pf-field');
  populatePfFields(dlg, '#vec-flt-source', '#vec-flt-pf-field');
}

async function populatePolySources(dlg, selMap = {}) {
  _polySources = (await collectBoundarySources()).map((b) => ({
    ...b, cleanLabel: b.presetId ? b.label.replace(/（预设）$/, '') : b.label,
  }));
  const opts = _polySources.length
    ? _polySources.map((b) => `<option value="${b.value}">${b.label}</option>`).join('')
    : '<option value="" disabled>（暂无面域/预设边界）</option>';
  const withEmpty = '<option value="">（不限范围）</option>' + opts;
  const fill = (id, withEmp, selValue) => {
    const sel = dlg.querySelector(id);
    if (!sel) return;
    sel.innerHTML = withEmp ? withEmpty : opts;
    if (selValue && _polySources.some((b) => b.value === selValue)) sel.value = selValue;
  };
  fill('#vec-layer-a', false, selMap.layerAId);
  fill('#vec-layer-b', false, selMap.layerBId);
  fill('#vec-clip-range', false, selMap.rangeId);
  fill('#vec-ext-source', false, selMap.sourceId);
  fill('#vec-merge-source', false, selMap.boundaryId);
  fill('#vec-flt-range', true, selMap.rangeId);
  populatePfFields(dlg, '#vec-ext-source', '#vec-ext-where-field');
  populateMergeBy(dlg, selMap.by);
}

/** 字段下拉（读指定源 fc properties；带空选项=不过滤/无条件）。 */
function populatePfFields(dlg, srcSelId, fieldSelId, selField) {
  const srcSel = dlg.querySelector(srcSelId); const fieldSel = dlg.querySelector(fieldSelId);
  if (!srcSel || !fieldSel) return;
  const src = (_ptSources.find((s) => s.value === srcSel.value)) || (_polySources.find((b) => b.value === srcSel.value));
  const done = (keys) => {
    fieldSel.innerHTML = '<option value="">（无）</option>' + keys.map((k) => `<option value="${k}">${k}</option>`).join('');
    if (selField && keys.includes(selField)) fieldSel.value = selField;
  };
  if (src && src.fc && src.fc.features.length) return done(Object.keys(src.fc.features[0].properties || {}));
  if (src && src.presetId) {
    boundarySourceGeo(src).then((geo) => done(geo && geo.features.length ? Object.keys(geo.features[0].properties || {}) : []));
    return;
  }
  done([]);
}

async function populateMergeBy(dlg, selField) {
  const srcSel = dlg.querySelector('#vec-merge-source');
  const sel = dlg.querySelector('#vec-merge-by');
  if (!srcSel || !sel) return;
  const src = _polySources.find((b) => b.value === srcSel.value);
  const geo = src ? await boundarySourceGeo(src) : null;
  const keys = geo && geo.features.length ? Object.keys(geo.features[0].properties || {}) : [];
  sel.innerHTML = '<option value="">（整体合并）</option>' + keys.map((k) => `<option value="${k}">${k}</option>`).join('');
  if (selField && keys.includes(selField)) sel.value = selField;
}

function readPf(dlg, fieldId, opId, valId) {
  const field = dlg.querySelector(fieldId).value;
  if (!field) return undefined;
  const op = dlg.querySelector(opId).value || 'eq';
  const raw = dlg.querySelector(valId).value.trim();
  if (!raw) return undefined;
  const num = Number(raw);
  return { field, op, value: isNaN(num) || raw === '' ? raw : num };
}

const _geoOf = (src) => (src ? (src.presetId || src.fc) : null);

export function openVectorDialog(layerId) {
  const dlg = dialogEl();
  if (!dlg) return;
  let seed = null;
  if (layerId) {
    const lyr = getLayer(layerId);
    if (lyr && lyr.paint && lyr.paint._ui && OPS.includes(lyr.paint._ui.tool)) seed = lyr.paint._ui;
  }
  const op = (seed && seed.tool) || 'overlay';
  dlg.querySelectorAll('#vec-op .buf-cap').forEach((c) => c.classList.toggle('is-sel', c.dataset.op === op));
  populatePtSources(dlg, seed && seed.sourceId);
  populatePolySources(dlg, seed || {}).then(() => {
    if (!seed) return;
    if (seed.where) {
      populatePfFields(dlg, '#vec-ext-source', '#vec-ext-where-field', seed.where.field);
      const o = dlg.querySelector('#vec-ext-where-op'); const v = dlg.querySelector('#vec-ext-where-value');
      if (o) o.value = seed.where.op || 'eq';
      if (v) v.value = Array.isArray(seed.where.value) ? seed.where.value.join(',') : (seed.where.value ?? '');
    }
    const pf = seed.pre_filter;
    if (pf) {
      const fid = op === 'clip' ? '#vec-clip-pf' : '#vec-flt-pf';
      populatePfFields(dlg, op === 'clip' ? '#vec-clip-source' : '#vec-flt-source', `${fid}-field`, pf.field);
      const o = dlg.querySelector(`${fid}-op`); const v = dlg.querySelector(`${fid}-value`);
      if (o) o.value = pf.op || 'eq';
      if (v) v.value = Array.isArray(pf.value) ? pf.value.join(',') : (pf.value ?? '');
    }
  });
  if (seed && seed.how) {
    dlg.querySelectorAll('#vec-how .buf-cap').forEach((c) => c.classList.toggle('is-sel', c.dataset.how === seed.how));
  }
  renderVecColor(dlg, (seed && seed.style && seed.style.color) || DEFAULT_COLOR);
  const fo = Math.round(((seed && seed.style && seed.style.fillOpacity) ?? 0.2) * 100);
  dlg.querySelector('#vec-opacity').value = fo;
  dlg.querySelector('#vec-opacity-val').textContent = `${fo}%`;
  constrainOp(dlg);
  dlg.dataset.editLayerId = layerId || '';
  openParamPanel('vector');
}

async function generateVector() {
  const dlg = dialogEl();
  const op = selectedOp(dlg);
  const style = { color: _vecColor, fillOpacity: Number(dlg.querySelector('#vec-opacity').value) / 100 };
  const poly = (id) => _polySources.find((b) => b.value === dlg.querySelector(id).value);
  const pt = (id) => _ptSources.find((s) => s.value === dlg.querySelector(id).value);
  const params = { op, style };
  if (op === 'overlay') {
    const a = poly('#vec-layer-a'); const b = poly('#vec-layer-b');
    if (!a || !b) { toast.error('请选择叠置图层 A 与 B'); return; }
    if (a.value === b.value) { toast.error('图层 A 与 B 不能相同'); return; }
    Object.assign(params, { layer_a: _geoOf(a), layer_b: _geoOf(b), layer_a_label: _srcLabel(a), layer_b_label: _srcLabel(b),
      layerAId: a.value, layerBId: b.value, how: dlg.querySelector('#vec-how .buf-cap.is-sel')?.dataset.how || 'intersection' });
  } else if (op === 'clip') {
    const s = pt('#vec-clip-source'); const rg = poly('#vec-clip-range');
    if (!s) { toast.error('请选择目标点层'); return; }
    if (!rg) { toast.error('请选择裁剪范围'); return; }
    Object.assign(params, { layer: s.fc, sourceId: s.value, sourceLabel: s.label, range: _geoOf(rg),
      rangeId: rg.value, rangeLabel: _srcLabel(rg), pre_filter: readPf(dlg, '#vec-clip-pf-field', '#vec-clip-pf-op', '#vec-clip-pf-value') });
  } else if (op === 'extract_feature') {
    const s = poly('#vec-ext-source');
    if (!s) { toast.error('请选择抽取面层'); return; }
    const where = readPf(dlg, '#vec-ext-where-field', '#vec-ext-where-op', '#vec-ext-where-value');
    Object.assign(params, { layer: _geoOf(s), sourceId: s.value, sourceLabel: _srcLabel(s), where });
  } else if (op === 'merge') {
    const s = poly('#vec-merge-source');
    if (!s) { toast.error('请选择合并面层'); return; }
    Object.assign(params, { boundary: _geoOf(s), boundaryId: s.value, boundaryLabel: _srcLabel(s),
      by: dlg.querySelector('#vec-merge-by').value || undefined });
  } else if (op === 'filter_attr') {
    const s = pt('#vec-flt-source');
    if (!s) { toast.error('请选择筛选点层'); return; }
    const pf = readPf(dlg, '#vec-flt-pf-field', '#vec-flt-pf-op', '#vec-flt-pf-value');
    if (!pf) { toast.error('筛选需填字段与值（属性过滤三段）'); return; }
    const rg = poly('#vec-flt-range');
    Object.assign(params, { layer: s.fc, sourceId: s.value, sourceLabel: s.label, pre_filter: pf,
      range: rg ? _geoOf(rg) : undefined, rangeId: rg && rg.value, rangeLabel: rg && _srcLabel(rg) });
  }

  const btn = dlg.querySelector('#vec-generate');
  const orig = btn.textContent;
  btn.disabled = true; btn.textContent = '生成中…';
  try {
    const r = await _execute(params, { editLayerId: dlg.dataset.editLayerId, silent: false });
    closeParamPanel();
    toast.success(`已生成图层「${r.layerName}」（${r.featureCount} 个要素）`);
  } catch (e) {
    console.error('[vector]', e);
    toast.error(`矢量分析失败：${e.message || e}（确认后端已启动：uvicorn api.main:app --port 8000）`);
  } finally {
    btn.disabled = false; btn.textContent = orig;
  }
}

export function initVectorTool() {
  const dlg = dialogEl();
  if (!dlg) return;
  dlg.querySelector('#vec-op').addEventListener('click', (e) => {
    const b = e.target.closest('.buf-cap');
    if (!b) return;
    dlg.querySelectorAll('#vec-op .buf-cap').forEach((x) => x.classList.remove('is-sel'));
    b.classList.add('is-sel');
    constrainOp(dlg);
  });
  dlg.querySelector('#vec-how').addEventListener('click', (e) => {
    const b = e.target.closest('.buf-cap');
    if (!b) return;
    dlg.querySelectorAll('#vec-how .buf-cap').forEach((x) => x.classList.remove('is-sel'));
    b.classList.add('is-sel');
  });
  dlg.querySelector('#vec-clip-source').addEventListener('change', () => populatePfFields(dlg, '#vec-clip-source', '#vec-clip-pf-field'));
  dlg.querySelector('#vec-flt-source').addEventListener('change', () => populatePfFields(dlg, '#vec-flt-source', '#vec-flt-pf-field'));
  dlg.querySelector('#vec-ext-source').addEventListener('change', () => populatePfFields(dlg, '#vec-ext-source', '#vec-ext-where-field'));
  dlg.querySelector('#vec-merge-source').addEventListener('change', () => populateMergeBy(dlg));
  dlg.querySelector('#vec-opacity').addEventListener('input', (e) => {
    dlg.querySelector('#vec-opacity-val').textContent = `${e.target.value}%`;
  });
  dlg.querySelector('#vec-generate')?.addEventListener('click', generateVector);
}
