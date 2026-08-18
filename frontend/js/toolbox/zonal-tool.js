// ═══ toolbox/zonal-tool.js — Zonal 面域归因聚合（手册 v2.2 §5.2：聚合/多区对比双模式）═══
// 聚合：/geo/zonal_stats → rows + buildZonalFc 合成红绿 choropleth（_ui.tool='zonal' 复用 grid 着色管线）。
// 对比：≤4 区逐区 zonal_stats → 合并成图（现状 tools.js _compareToLayer 逻辑随迁）。
// 单一执行核 _execute（§4.2）：UI dialog 与 generateZonalForAI/generateCompareForAI 共用。
// 边界解析：模块只收 preset_id/GeoJSON（shared resolveBoundaryGeo）；中文要素名由调用方预解析（§3.3①）。
import { getLayer } from '../state.js';
import { geoPost, defaultPaint, buildZonalFc, resolveBoundaryGeo, placeToolLayer,
  collectPointSources, collectBoundarySources, boundarySourceGeo,
  featName as _featName, normalizeGeoNames as _normalizeGeoNames } from './shared.js';
import { polarityStops } from '../grid-tool.js';
import { openParamPanel, closeParamPanel } from '../param-panel.js';
import { trackGeneration } from '../geocode-loader.js';
import { toast } from '../toast.js';

const dialogEl = () => document.getElementById('zonal-dialog');
const DEFAULTS = { mode: 'aggregate' };
const PF_OPS = [['eq', '='], ['ne', '≠'], ['gt', '>'], ['gte', '≥'], ['lt', '<'], ['lte', '≤'], ['contains', '包含']];

let _sources = [];     // 点层源缓存（value → fc/level）
let _boundaries = [];  // 边界源缓存（value → {label, cleanLabel, fc?|presetId}）

function setHidden(dlg, sel, hidden) { const el = dlg.querySelector(sel); if (el) el.hidden = hidden; }
function selectedMode(dlg) { return dlg.querySelector('#zonal-mode .buf-cap.is-sel')?.dataset.mode || DEFAULTS.mode; }
function constrainMode(dlg) { setHidden(dlg, '#zonal-compare-section', selectedMode(dlg) !== 'compare'); }

// _featName/_normalizeGeoNames 已上移 shared.js（v2.1·rank/area-stats 共用）。

/** 红绿 choropleth 色带预览（polarityStops('overall')·只读）。 */
function renderRampPreview(dlg) {
  const box = dlg.querySelector('#zonal-ramp-preview');
  if (!box) return;
  const stops = polarityStops('overall') || [];
  const grad = `linear-gradient(90deg, ${stops.map(([d, c]) => `${c} ${Math.round(d * 100)}%`).join(', ')})`;
  box.innerHTML = `<div class="zonal-ramp-bar" style="background:${grad}"></div>
    <div class="zonal-ramp-ticks"><span>负面</span><span>中性</span><span>正面</span></div>`;
}

function populateSources(dlg, selValue) {
  _sources = collectPointSources();
  const sel = dlg.querySelector('#zonal-source');
  sel.innerHTML = _sources.length
    ? _sources.map((s) => `<option value="${s.value}">${s.label}</option>`).join('')
    : '<option value="" disabled>（暂无情绪点层，先导入或上载数据）</option>';
  if (selValue && _sources.some((s) => s.value === selValue)) sel.value = selValue;
  populatePfFields(dlg);
}

async function populateBoundaries(dlg, selValue) {
  const sel = dlg.querySelector('#zonal-boundary');
  sel.innerHTML = '<option value="" disabled>加载中…</option>';
  _boundaries = (await collectBoundarySources()).map((b) => ({
    ...b, cleanLabel: b.presetId ? b.label.replace(/（预设）$/, '') : b.label,
  }));
  sel.innerHTML = _boundaries.length
    ? _boundaries.map((b) => `<option value="${b.value}">${b.label}</option>`).join('')
    : '<option value="" disabled>（暂无面域/预设边界）</option>';
  if (selValue && _boundaries.some((b) => b.value === selValue)) sel.value = selValue;
  loadCompareFeatures(dlg);
}

/** 对比模式：按当前边界源加载要素胶囊（多选 ≤4）。 */
async function loadCompareFeatures(dlg, selNames) {
  const box = dlg.querySelector('#zonal-features');
  if (!box) return;
  const src = _boundaries.find((b) => b.value === dlg.querySelector('#zonal-boundary').value);
  const geo = src ? await boundarySourceGeo(src) : null;
  const feats = (geo && geo.features) || [];
  if (!feats.length) { box.innerHTML = '<span class="zonal-feat-empty">（该边界无可选要素）</span>'; return; }
  box.innerHTML = feats.slice(0, 60).map((f, i) => {
    const nm = _featName(f, i);
    const on = selNames && selNames.includes(nm) ? ' is-sel' : '';
    return `<button type="button" class="buf-cap zonal-feat${on}" data-name="${nm}">${nm}</button>`;
  }).join('');
}

function populatePfFields(dlg) {
  const sel = dlg.querySelector('#zonal-pf-field');
  if (!sel) return;
  const src = _sources.find((s) => s.value === dlg.querySelector('#zonal-source').value);
  const keys = src && src.fc && src.fc.features.length ? Object.keys(src.fc.features[0].properties || {}) : [];
  sel.innerHTML = '<option value="">（不过滤）</option>' + keys.map((k) => `<option value="${k}">${k}</option>`).join('');
}

function readPreFilter(dlg) {
  const field = dlg.querySelector('#zonal-pf-field').value;
  if (!field) return undefined;
  const op = dlg.querySelector('#zonal-pf-op').value || 'eq';
  const raw = dlg.querySelector('#zonal-pf-value').value.trim();
  if (!raw) return undefined;
  const num = Number(raw);
  return { field, op, value: isNaN(num) || raw === '' ? raw : num };
}

// ═══ 单一执行核（§4.2）═══
/** params.mode='aggregate'：{ layer(fc|注册名), boundary(preset|GeoJSON), boundaryLabel?, range?, pre_filter?, top_n?, as?, sourceId?, level? }
 *  params.mode='compare'：{ layer, boundaries:[{label, geo}]|[(preset|GeoJSON)...], pre_filter?, as? } */
async function _execute(params, { editLayerId = '', silent = true } = {}) {
  const mode = params.mode || 'aggregate';

  if (mode === 'compare') {
    const bs = (params.boundaries || []).slice(0, 4);
    const results = [];
    for (const b of bs) {
      const geo = (b && typeof b === 'object' && (b.geo || b.boundary)) || b;   // 归一：{label, geo} | FC | preset str
      const label = (b && b.label) || (typeof b === 'string' ? b : (((geo.features || [])[0] || {}).properties || {}).name) || '区域';
      try {
        const body = { layer: params.layer, boundary: geo };
        if (params.pre_filter) body.pre_filter = params.pre_filter;
        const r = await (silent ? geoPost('zonal_stats', body) : trackGeneration(geoPost('zonal_stats', body)));
        const rows = r.rows || [];
        results.push({ boundary: label, boundaryGeo: geo, row: rows[0] || null, n: rows.length, sort_by: r.sort_by });
      } catch (e) { results.push({ boundary: label, row: null, err: String((e && e.message) || e) }); }
    }
    // 合成合并聚合 FC（现状 _compareToLayer :254-267 逻辑）
    const feats = []; const labels = [];
    for (const x of results) {
      if (!x.row || !x.boundaryGeo) continue;
      const geo = typeof x.boundaryGeo === 'object' ? x.boundaryGeo : await resolveBoundaryGeo(x.boundaryGeo);
      const fc = geo ? buildZonalFc([x.row], _normalizeGeoNames(geo)) : null;
      if (fc && fc.features.length) { feats.push(...fc.features); labels.push(x.boundary); }
    }
    const okN = results.filter((x) => x.row).length;
    const name = params.as || `对比·${labels.join('·')}`;
    let L = null;
    if (okN >= 2 && feats.length) {
      const ui = { tool: 'zonal', mode: 'compare', boundaries: labels, sourceId: params.sourceId, level: params.level,
        pre_filter: params.pre_filter, boundaryId: params.boundaryId };
      L = placeToolLayer({ name, kind: 'polygon', fc: { type: 'FeatureCollection', features: feats },
        paint: { ...defaultPaint('zonal', 'polygon'), _ui: ui }, editLayerId, silent });
    }
    return { layerId: L && L.id, layerName: L ? name : null, featureCount: feats.length,
      fc: L ? { type: 'FeatureCollection', features: feats } : null, comparison: results, okCount: okN };
  }

  // aggregate
  const body = { layer: params.layer, boundary: params.boundary };
  if (params.range) body.range = params.range;
  if (params.pre_filter) body.pre_filter = params.pre_filter;
  if (params.top_n != null) body.top_n = Number(params.top_n);
  const r = await (silent ? geoPost('zonal_stats', body) : trackGeneration(geoPost('zonal_stats', body)));
  const rows = r.rows || [];
  if (!rows.length) return { layerId: null, layerName: null, featureCount: 0, fc: null, rows, sortBy: r.sort_by, boundaryLabel: params.boundaryLabel };
  const geo = typeof params.boundary === 'object' ? params.boundary : await resolveBoundaryGeo(params.boundary);
  // CB-41 §六：着色语义分叉——semantic='count'（显式点数·临时分析图）| 'auto'（UI 路径：rows 无极性→自动点数）；
  // 不传/其他 = 旧行为（极性 choropleth）——ForAI（generateZonalForAI）不传 → 契约与默认行为零变化。
  const noPol = rows.length > 0 && rows.every((x) => x.polarity_index == null || x.polarity_index === '');
  const semantic = params.semantic === 'count' ? 'count'
    : (params.semantic === 'auto' && noPol ? 'count' : undefined);
  const fc = buildZonalFc(rows, _normalizeGeoNames(geo), semantic);
  const label = params.boundaryLabel || (typeof params.boundary === 'string' ? params.boundary
    : ((((geo && geo.features) || [])[0] || {}).properties || {}).name) || '面域';
  const name = params.as || (semantic === 'count' ? `点数·聚合·${label}` : `聚合·${label}`);
  let L = null;
  if (fc && fc.features.length) {
    const ui = { tool: 'zonal', mode: 'aggregate', boundaryId: params.boundaryId, boundaryLabel: label,
      sourceId: params.sourceId, level: params.level, pre_filter: params.pre_filter,
      ...(semantic ? { semantic } : {}) };
    L = placeToolLayer({ name, kind: 'polygon', fc,
      paint: { ...defaultPaint('zonal', 'polygon', semantic), _ui: ui }, editLayerId, silent });
  }
  return { layerId: L && L.id, layerName: L ? name : null, featureCount: fc ? fc.features.length : 0,
    fc, rows, sortBy: r.sort_by, boundaryLabel: label, semantic };
}

/** EMC 委托唯一接口（§4.1 契约）。 */
export async function generateZonalForAI(opts = {}) {
  return _execute({ ...opts, mode: 'aggregate' }, { editLayerId: opts.editLayerId || '', silent: opts.silent ?? true });
}
export async function generateCompareForAI(opts = {}) {
  return _execute({ ...opts, mode: 'compare' }, { editLayerId: opts.editLayerId || '', silent: opts.silent ?? true });
}

// ═══ UI dialog ═══

export function openZonalDialog(layerId) {
  const dlg = dialogEl();
  if (!dlg) return;
  let seed = null;
  if (layerId) {
    const lyr = getLayer(layerId);
    if (lyr && lyr.paint && lyr.paint._ui && lyr.paint._ui.tool === 'zonal') seed = lyr.paint._ui;
  }
  const mode = (seed && seed.mode) || DEFAULTS.mode;
  dlg.querySelectorAll('#zonal-mode .buf-cap').forEach((c) => c.classList.toggle('is-sel', c.dataset.mode === mode));
  populateSources(dlg, seed && seed.sourceId);
  populateBoundaries(dlg, seed && seed.boundaryId).then(() => {
    if (seed && seed.mode === 'compare' && seed.boundaries) loadCompareFeatures(dlg, seed.boundaries);
  });
  if (seed && seed.pre_filter) {
    const f = dlg.querySelector('#zonal-pf-field'); const o = dlg.querySelector('#zonal-pf-op'); const v = dlg.querySelector('#zonal-pf-value');
    if (f) f.value = seed.pre_filter.field || '';
    if (o) o.value = seed.pre_filter.op || 'eq';
    if (v) v.value = Array.isArray(seed.pre_filter.value) ? seed.pre_filter.value.join(',') : (seed.pre_filter.value ?? '');
  } else {
    const f = dlg.querySelector('#zonal-pf-field'); const v = dlg.querySelector('#zonal-pf-value');
    if (f) f.value = ''; if (v) v.value = '';
  }
  constrainMode(dlg);
  renderRampPreview(dlg);
  dlg.dataset.editLayerId = layerId || '';
  if (!_sources.length) toast.info('请先导入或上载情绪点层数据');
  openParamPanel('zonal');
}

async function generateZonal() {
  const dlg = dialogEl();
  const mode = selectedMode(dlg);
  const src = _sources.find((s) => s.value === dlg.querySelector('#zonal-source').value);
  if (!src) { toast.error('请选择情绪点层'); return; }
  const bnd = _boundaries.find((b) => b.value === dlg.querySelector('#zonal-boundary').value);
  if (!bnd) { toast.error('请选择聚合边界'); return; }
  const pre_filter = readPreFilter(dlg);

  const btn = dlg.querySelector('#zonal-generate');
  const orig = btn.textContent;
  btn.disabled = true; btn.textContent = '生成中…';
  try {
    let r;
    if (mode === 'compare') {
      const names = [...dlg.querySelectorAll('#zonal-features .zonal-feat.is-sel')].map((b) => b.dataset.name);
      if (names.length < 2) { toast.error('多区对比至少选 2 个要素'); return; }
      const geo = await boundarySourceGeo(bnd);
      const feats = (geo && geo.features) || [];
      const boundaries = names.map((nm) => {
        const f = feats.find((x, i) => _featName(x, i) === nm);
        return { label: nm, geo: f ? { type: 'FeatureCollection', features: [f] } : null };
      }).filter((b) => b.geo);
      r = await _execute({ mode, layer: src.fc, boundaries, pre_filter,
        sourceId: src.value, level: src.level, boundaryId: bnd.value }, { editLayerId: dlg.dataset.editLayerId, silent: false });
      if (r.okCount < 2) { toast.error(`区域对比仅 ${r.okCount} 区有结果`); return; }
      if (!r.layerId) { toast.info('对比完成，但边界无法成图（仅表格结果）'); return; }
    } else {
      // CB-41 §六：semantic='auto'——rows 无极性字段时自动转「点数」着色（检测在 _execute 内·拿到 rows 判定）
      r = await _execute({ mode, layer: src.fc, boundary: bnd.presetId || bnd.fc, boundaryLabel: bnd.cleanLabel,
        boundaryId: bnd.value, pre_filter, sourceId: src.value, level: src.level, semantic: 'auto' }, { editLayerId: dlg.dataset.editLayerId, silent: false });
      if (r.semantic === 'count') toast.info('源点层无极性字段 → 按点数着色（越多越深·零点不填色·临时分析图）', 4500);
      if (!r.rows.length) { toast.info(`面域聚合（${bnd.cleanLabel}）无结果`); return; }
      if (!r.layerId) { toast.info('聚合完成，但边界无法解析成图（仅表格结果）'); return; }
    }
    closeParamPanel();
    toast.success(`已生成图层「${r.layerName}」（${r.featureCount} 个单元·${r.semantic === 'count' ? '点数 choropleth（临时）' : '极性 choropleth'}）`);
  } catch (e) {
    console.error('[zonal]', e);
    toast.error(`面域聚合失败：${e.message || e}（确认后端已启动：uvicorn api.main:app --port 8000）`);
  } finally {
    btn.disabled = false; btn.textContent = orig;
  }
}

export function initZonalTool() {
  const dlg = dialogEl();
  if (!dlg) return;
  dlg.querySelector('#zonal-mode').addEventListener('click', (e) => {
    const b = e.target.closest('.buf-cap');
    if (!b) return;
    dlg.querySelectorAll('#zonal-mode .buf-cap').forEach((x) => x.classList.remove('is-sel'));
    b.classList.add('is-sel');
    constrainMode(dlg);
  });
  dlg.querySelector('#zonal-source').addEventListener('change', () => populatePfFields(dlg));
  dlg.querySelector('#zonal-boundary').addEventListener('change', () => loadCompareFeatures(dlg));
  dlg.querySelector('#zonal-features').addEventListener('click', (e) => {
    const b = e.target.closest('.zonal-feat');
    if (!b) return;
    if (!b.classList.contains('is-sel') && dlg.querySelectorAll('#zonal-features .zonal-feat.is-sel').length >= 4) {
      toast.info('多区对比最多选 4 个要素'); return;
    }
    b.classList.toggle('is-sel');
  });
  dlg.querySelector('#zonal-generate')?.addEventListener('click', generateZonal);
}
