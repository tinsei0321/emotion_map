// ═══ toolbox/area-stats-tool.js — 面积统计 choropleth（手册 v2.2 §5.3）═══
// /geo/area_stats → rows（area_km2/share 注入要素 properties）；用地（DLMC）由 addToolboxLayer
// 内 landuseLayerPaint 自动附国标色；非用地走 defaultPaint 面默认。
// 单一执行核 _execute（§4.2）：UI dialog 与 generateAreaStatsForAI 共用。
// 边界解析：模块只收 preset_id/GeoJSON；中文要素名由调用方预解析（§3.3①）。
import { getLayer } from '../state.js';
import { geoPost, defaultPaint, resolveBoundaryGeo, placeToolLayer,
  collectBoundarySources, boundarySourceGeo, normalizeGeoNames } from './shared.js';
import { openParamPanel, closeParamPanel } from '../param-panel.js';
import { trackGeneration } from '../geocode-loader.js';
import { toast } from '../toast.js';

const dialogEl = () => document.getElementById('area-stats-dialog');
let _boundaries = [];   // 边界源缓存（value → {label, cleanLabel, fc?|presetId}）

async function populateBoundaries(dlg, selValue) {
  const sel = dlg.querySelector('#as-boundary');
  sel.innerHTML = '<option value="" disabled>加载中…</option>';
  _boundaries = (await collectBoundarySources()).map((b) => ({
    ...b, cleanLabel: b.presetId ? b.label.replace(/（预设）$/, '') : b.label,
  }));
  sel.innerHTML = _boundaries.length
    ? _boundaries.map((b) => `<option value="${b.value}">${b.label}</option>`).join('')
    : '<option value="" disabled>（暂无面域/预设边界）</option>';
  if (selValue && _boundaries.some((b) => b.value === selValue)) sel.value = selValue;
  populateGroupBy(dlg);
}

/** group_by 字段下拉（读边界 fc properties，默认 DLMC/name；空值=按单元不分组）。 */
async function populateGroupBy(dlg, selField) {
  const sel = dlg.querySelector('#as-group-by');
  if (!sel) return;
  const src = _boundaries.find((b) => b.value === dlg.querySelector('#as-boundary').value);
  const geo = src ? await boundarySourceGeo(src) : null;
  const keys = geo && geo.features && geo.features.length ? Object.keys(geo.features[0].properties || {}) : [];
  sel.innerHTML = '<option value="">（不分组·按单元）</option>' + keys.map((k) => `<option value="${k}">${k}</option>`).join('');
  const def = selField || (keys.includes('DLMC') ? 'DLMC' : (keys.includes('name') ? 'name' : ''));
  sel.value = def;
}

// ═══ 单一执行核（§4.2）═══
/** params：{ boundary(preset|GeoJSON), boundaryLabel?, group_by?, as?, boundaryId? } */
async function _execute(params, { editLayerId = '', silent = true } = {}) {
  const body = { boundary: params.boundary };
  if (params.group_by) body.group_by = params.group_by;
  const r = await (silent ? geoPost('area_stats', body) : trackGeneration(geoPost('area_stats', body)));
  const rows = r.rows || [];
  // 合成着色 FC（现状 _areaStatsToLayer :333-357 逻辑：byGroup 精确 / name 模糊双路匹配，无命中不成图）
  const geo = typeof params.boundary === 'object' ? params.boundary : await resolveBoundaryGeo(params.boundary);
  const geoN = normalizeGeoNames(geo);   // v2.1：MC 系面域先归一要素名（name 路径防模糊命中首行）
  const feats = geoN ? (geoN.type === 'FeatureCollection' ? geoN.features : (geoN.type === 'Feature' ? [geoN] : [])) : [];
  let fc = null;
  if (feats.length) {
    // v2.1 修（latent 数据 bug·现状同有）：分组 rows 不回显 group 字段——组值在 row.name（backend area_stats
    // rows={name:组标签,area_km2,share}）。旧 byGroup 判定（rows.some(r[group_by]!=null)）恒 false → 落 name 路径，
    // 空名特征靠 includes('') 恒真模糊命中首行（放大器）。修：byGroup 直接信 group_by；匹配兼容 row[group_by] ?? row.name。
    const byGroup = !!params.group_by;
    const findRow = (f) => {
      const p = f.properties || {};
      if (byGroup) {
        const gv = String(p[params.group_by] ?? '');
        return rows.find((row) => String(row[params.group_by] ?? row.name ?? '') === gv) || null;
      }
      const nm = String(p.name || '').trim();
      if (!nm) return null;   // 空名不模糊（与 buildZonalFc 守卫同则）
      return rows.find((row) => String(row.name || '').trim() === nm)
        || rows.find((row) => { const rn = String(row.name || '').trim(); return rn && (rn.includes(nm) || nm.includes(rn)); }) || null;
    };
    let hit = 0;
    const out = feats.map((f) => {
      const row = findRow(f);
      if (row) hit++;
      return { ...f, properties: { ...(f.properties || {}), area_km2: row ? row.area_km2 : null, share: row ? row.share : null } };
    });
    if (hit) fc = { type: 'FeatureCollection', features: out };
  }
  const label = params.boundaryLabel || (typeof params.boundary === 'string' ? params.boundary
    : ((feats[0] || {}).properties || {}).name) || '面域';
  const name = params.as || `面积·${label}${params.group_by ? '·按' + params.group_by : ''}`;
  let L = null;
  if (fc) {
    const ui = { tool: 'area_stats', boundaryId: params.boundaryId, boundaryLabel: label, group_by: params.group_by };
    L = placeToolLayer({ name, kind: 'polygon', fc,
      paint: { ...defaultPaint('area_stats', 'polygon'), _ui: ui }, editLayerId, silent });
  }
  return { layerId: L && L.id, layerName: L ? name : null, featureCount: fc ? fc.features.length : 0,
    fc, rows, totalAreaKm2: r.total_area_km2, boundaryLabel: label };
}

/** EMC 委托唯一接口（§4.1 契约）。 */
export async function generateAreaStatsForAI(opts = {}) {
  return _execute(opts, { editLayerId: opts.editLayerId || '', silent: opts.silent ?? true });
}

// ═══ UI dialog ═══

export function openAreaStatsDialog(layerId) {
  const dlg = dialogEl();
  if (!dlg) return;
  let seed = null;
  if (layerId) {
    const lyr = getLayer(layerId);
    if (lyr && lyr.paint && lyr.paint._ui && lyr.paint._ui.tool === 'area_stats') seed = lyr.paint._ui;
  }
  populateBoundaries(dlg, seed && seed.boundaryId).then(() => {
    if (seed && seed.group_by) populateGroupBy(dlg, seed.group_by);
  });
  dlg.dataset.editLayerId = layerId || '';
  openParamPanel('area-stats');
}

async function generateAreaStats() {
  const dlg = dialogEl();
  const bnd = _boundaries.find((b) => b.value === dlg.querySelector('#as-boundary').value);
  if (!bnd) { toast.error('请选择统计边界'); return; }
  const group_by = dlg.querySelector('#as-group-by').value || undefined;

  const btn = dlg.querySelector('#as-generate');
  const orig = btn.textContent;
  btn.disabled = true; btn.textContent = '生成中…';
  try {
    const r = await _execute({ boundary: bnd.presetId || bnd.fc, boundaryLabel: bnd.cleanLabel,
      boundaryId: bnd.value, group_by }, { editLayerId: dlg.dataset.editLayerId, silent: false });
    if (!r.rows.length) { toast.info(`面积统计（${bnd.cleanLabel}）无结果`); return; }
    if (!r.layerId) { toast.info('统计完成，但未命中边界要素成图（仅表格结果）'); return; }
    closeParamPanel();
    const total = r.totalAreaKm2 != null ? `，总 ${Number(r.totalAreaKm2).toFixed(1)} km²` : '';
    toast.success(`已生成着色层「${r.layerName}」（${r.featureCount} 单元${total}·面积/占比已入属性）`);
  } catch (e) {
    console.error('[area-stats]', e);
    toast.error(`面积统计失败：${e.message || e}（确认后端已启动：uvicorn api.main:app --port 8000）`);
  } finally {
    btn.disabled = false; btn.textContent = orig;
  }
}

export function initAreaStatsTool() {
  const dlg = dialogEl();
  if (!dlg) return;
  dlg.querySelector('#as-boundary').addEventListener('change', () => populateGroupBy(dlg));
  dlg.querySelector('#as-generate')?.addEventListener('click', generateAreaStats);
}
