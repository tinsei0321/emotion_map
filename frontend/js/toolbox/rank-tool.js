// ═══ toolbox/rank-tool.js — Rank 排序 Top N 高亮（手册 v2.2 §5.4）═══
// /geo/rank → rows；Top N 高亮层（现状 _rankToLayer :300-328 逻辑随迁：boundary 合成 /
// layerRef 回匹配双路，_grid_norm 补全，hits 过滤）。
// by 的 domain 中文映射（_DOMAIN_CN2EN）留 tools.js 委托层（§5.4），模块只收规范 by 值。
// _ui.tool='rank'（§4.3）——注意 defaultPaint('rank') 的 _ui.tool='zonal' 为 A2 现状 quirk，
// 本模块显式覆写 _ui（§4.3 契约优先）；着色管线（gridField/gridStops）沿用 defaultPaint。
import { getLayers, getLayer } from '../state.js';
import { geoPost, defaultPaint, buildZonalFc, resolveBoundaryGeo, placeToolLayer,
  collectPointSources, collectBoundarySources, boundarySourceGeo, normalizeGeoNames } from './shared.js';
import { piToNorm, polarityStops } from '../grid-tool.js';
import { openParamPanel, closeParamPanel } from '../param-panel.js';
import { trackGeneration } from '../geocode-loader.js';
import { toast } from '../toast.js';

const dialogEl = () => document.getElementById('rank-dialog');
const DEFAULTS = { by: 'worst', topN: 5 };

let _sources = [];
let _boundaries = [];

function renderRampPreview(dlg) {
  const box = dlg.querySelector('#rank-ramp-preview');
  if (!box) return;
  const stops = polarityStops('overall') || [];
  const grad = `linear-gradient(90deg, ${stops.map(([d, c]) => `${c} ${Math.round(d * 100)}%`).join(', ')})`;
  box.innerHTML = `<div class="zonal-ramp-bar" style="background:${grad}"></div>
    <div class="zonal-ramp-ticks"><span>最差（红）</span><span>最好（绿）</span></div>`;
}

function populateSources(dlg, selValue) {
  _sources = collectPointSources();
  const sel = dlg.querySelector('#rank-source');
  sel.innerHTML = _sources.length
    ? _sources.map((s) => `<option value="${s.value}">${s.label}</option>`).join('')
    : '<option value="" disabled>（暂无情绪点层，先导入或上载数据）</option>';
  if (selValue && _sources.some((s) => s.value === selValue)) sel.value = selValue;
}

async function populateBoundaries(dlg, selValue) {
  const sel = dlg.querySelector('#rank-boundary');
  sel.innerHTML = '<option value="" disabled>加载中…</option>';
  _boundaries = (await collectBoundarySources()).map((b) => ({
    ...b, cleanLabel: b.presetId ? b.label.replace(/（预设）$/, '') : b.label,
  }));
  sel.innerHTML = _boundaries.length
    ? _boundaries.map((b) => `<option value="${b.value}">${b.label}</option>`).join('')
    : '<option value="" disabled>（暂无面域/预设边界）</option>';
  if (selValue && _boundaries.some((b) => b.value === selValue)) sel.value = selValue;
}

// ═══ 单一执行核（§4.2）═══
/** params：{ layer(fc|注册名), by='worst'|'best'|'domain:X'|'element:X', top_n=5,
 *  boundary?(preset|GeoJSON·点聚合后排序), boundaryLabel?, range?, pre_filter?,
 *  layerRef?(无 boundary 时已聚合层名回匹配), as?, sourceId?, boundaryId? } */
async function _execute(params, { editLayerId = '', silent = true } = {}) {
  const by = params.by || 'worst';
  const body = { layer: params.layer, by, top_n: Number(params.top_n) || DEFAULTS.topN };
  if (params.boundary) body.boundary = params.boundary;
  if (params.range) body.range = params.range;
  if (params.pre_filter) body.pre_filter = params.pre_filter;
  const r = await (silent ? geoPost('rank', body) : trackGeneration(geoPost('rank', body)));
  const rows = r.rows || [];
  if (!rows.length) return { layerId: null, layerName: null, featureCount: 0, fc: null, rows, by };

  // Top N 高亮 FC（现状 _rankToLayer 双路 + hits 过滤 + _grid_norm 补全）
  let fc = null;
  if (params.boundary) {
    const geo = typeof params.boundary === 'object' ? params.boundary : await resolveBoundaryGeo(params.boundary);
    fc = geo ? buildZonalFc(rows, normalizeGeoNames(geo)) : null;   // v2.1：MC 系面域先归一要素名（防模糊命中首行）
  }
  if ((!fc || !fc.features.length) && params.layerRef && typeof params.layerRef === 'string') {
    const src = getLayers().find((x) => x.name === params.layerRef || x.id === params.layerRef);
    if (src && src.fc && src.fc.features && src.fc.features.length) {
      const names = new Set(rows.map((row) => String(row.name || '').trim()));
      const feats = src.fc.features.filter((f) => names.has(String((f.properties || {}).name || '').trim()));
      if (feats.length) fc = { type: 'FeatureCollection', features: feats };
    }
  }
  if (fc && fc.features.length) {
    const hits = fc.features.filter((f) => (f.properties || {}).polarity_index != null);
    if (hits.length) fc = { type: 'FeatureCollection', features: hits };
    for (const f of fc.features) {
      const p = f.properties || {};
      if (p._grid_norm == null) p._grid_norm = p.polarity_index != null ? piToNorm(Number(p.polarity_index)) : 0.5;
    }
  }
  const _byCN = by === 'worst' ? '最差' : by === 'best' ? '最好' : String(by).replace(':', '·');
  const _scope = params.boundaryLabel || (params.boundary ? String(params.boundary) : (params.layerRef ? String(params.layerRef) : '排序'));
  const name = params.as || `Top${rows.length}·${_byCN}·${_scope}`;
  let L = null;
  if (fc && fc.features.length) {
    const ui = { tool: 'rank', by, top_n: body.top_n, boundaryId: params.boundaryId, boundaryLabel: params.boundaryLabel,
      sourceId: params.sourceId, layerRef: params.layerRef };
    L = placeToolLayer({ name, kind: 'polygon', fc,
      paint: { ...defaultPaint('rank', 'polygon'), _ui: ui }, editLayerId, silent });
  }
  return { layerId: L && L.id, layerName: L ? name : null, featureCount: fc ? fc.features.length : 0, fc, rows, by };
}

/** EMC 委托唯一接口（§4.1 契约）。 */
export async function generateRankForAI(opts = {}) {
  return _execute(opts, { editLayerId: opts.editLayerId || '', silent: opts.silent ?? true });
}

// ═══ UI dialog ═══

export function openRankDialog(layerId) {
  const dlg = dialogEl();
  if (!dlg) return;
  let seed = null;
  if (layerId) {
    const lyr = getLayer(layerId);
    if (lyr && lyr.paint && lyr.paint._ui && lyr.paint._ui.tool === 'rank') seed = lyr.paint._ui;
  }
  const by = (seed && seed.by === 'best') ? 'best' : 'worst';
  dlg.querySelectorAll('#rank-by .buf-cap').forEach((c) => c.classList.toggle('is-sel', c.dataset.by === by));
  const topN = (seed && seed.top_n) || DEFAULTS.topN;
  dlg.querySelector('#rank-topn').value = topN;
  dlg.querySelector('#rank-topn-val').textContent = `Top ${topN}`;
  populateSources(dlg, seed && seed.sourceId);
  populateBoundaries(dlg, seed && seed.boundaryId);
  renderRampPreview(dlg);
  dlg.dataset.editLayerId = layerId || '';
  if (!_sources.length) toast.info('请先导入或上载情绪点层数据');
  openParamPanel('rank');
}

async function generateRank() {
  const dlg = dialogEl();
  const src = _sources.find((s) => s.value === dlg.querySelector('#rank-source').value);
  if (!src) { toast.error('请选择情绪点层'); return; }
  const bnd = _boundaries.find((b) => b.value === dlg.querySelector('#rank-boundary').value);
  if (!bnd) { toast.error('请选择排序边界（点层需先按边界聚合）'); return; }
  const by = dlg.querySelector('#rank-by .buf-cap.is-sel')?.dataset.by || DEFAULTS.by;
  const top_n = Number(dlg.querySelector('#rank-topn').value) || DEFAULTS.topN;

  const btn = dlg.querySelector('#rank-generate');
  const orig = btn.textContent;
  btn.disabled = true; btn.textContent = '生成中…';
  try {
    const r = await _execute({ layer: src.fc, by, top_n, boundary: bnd.presetId || bnd.fc,
      boundaryLabel: bnd.cleanLabel, boundaryId: bnd.value, sourceId: src.value },
      { editLayerId: dlg.dataset.editLayerId, silent: false });
    if (!r.rows.length) { toast.info(`排序（by=${by}）无结果`); return; }
    if (!r.layerId) { toast.info('排序完成，但边界无法成图（仅表格结果）'); return; }
    closeParamPanel();
    toast.success(`已生成高亮层「${r.layerName}」（Top ${r.rows.length}·极性 choropleth）`);
  } catch (e) {
    console.error('[rank]', e);
    toast.error(`排序失败：${e.message || e}（确认后端已启动：uvicorn api.main:app --port 8000）`);
  } finally {
    btn.disabled = false; btn.textContent = orig;
  }
}

export function initRankTool() {
  const dlg = dialogEl();
  if (!dlg) return;
  dlg.querySelector('#rank-by').addEventListener('click', (e) => {
    const b = e.target.closest('.buf-cap');
    if (!b) return;
    dlg.querySelectorAll('#rank-by .buf-cap').forEach((x) => x.classList.remove('is-sel'));
    b.classList.add('is-sel');
  });
  dlg.querySelector('#rank-topn').addEventListener('input', (e) => {
    dlg.querySelector('#rank-topn-val').textContent = `Top ${e.target.value}`;
  });
  dlg.querySelector('#rank-generate')?.addEventListener('click', generateRank);
}
