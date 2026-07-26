// ═══ toolbox/nearest-tool.js — 最近邻连线层（手册 v2.2 §5.6·纯内嵌无 UI）═══
// /geo/nearest → rows（tgt_lon/tgt_lat/pt_lon/pt_lat）→ LineString 连线层（#ff9000 关联标注色·非数据编码）。
// 现状 tools.js _nearestToLayer :362-375 逻辑随迁；缺坐标行跳过（Dumb 不猜）。
// 无 dialog/init/tool-row——仅 generateNearestForAI 程序化入口（§4.1 契约）。
import { geoPost, defaultPaint, placeToolLayer } from './shared.js';

/** params：{ layer(fc|注册名), target(preset|GeoJSON|string), targetLabel?, k=1, as? } */
async function _execute(params, { editLayerId = '', silent = true } = {}) {
  const body = { layer: params.layer, target: params.target, k: Number(params.k) || 1 };
  if (!body.target) throw new Error('nearest 需 target');
  const r = await geoPost('nearest', body);
  const rows = r.rows || [];
  const targetLabel = params.targetLabel || (typeof params.target === 'string' ? params.target : '目标');
  // 连线 FC（现状 _nearestToLayer：缺坐标行跳过）
  const feats = [];
  for (const row of rows) {
    const c = [Number(row.tgt_lon), Number(row.tgt_lat), Number(row.pt_lon), Number(row.pt_lat)];
    if (!c.every(Number.isFinite)) continue;
    feats.push({ type: 'Feature',
      properties: { name: row.name || row.issue_label || '最近点', distance: row.distance, target: targetLabel },
      geometry: { type: 'LineString', coordinates: [[c[0], c[1]], [c[2], c[3]]] } });
  }
  const name = params.as || `最近邻·${targetLabel}`;
  let L = null;
  if (feats.length) {
    const ui = { tool: 'nearest', target: targetLabel, k: body.k };
    L = placeToolLayer({ name, kind: 'line', fc: { type: 'FeatureCollection', features: feats },
      paint: { ...defaultPaint('nearest', 'line'), _ui: ui }, editLayerId, silent });
  }
  return { layerId: L && L.id, layerName: L ? name : null, featureCount: feats.length,
    fc: L ? { type: 'FeatureCollection', features: feats } : null, rows, k: body.k, targetLabel };
}

/** EMC 委托唯一接口（§4.1 契约）。 */
export async function generateNearestForAI(opts = {}) {
  return _execute(opts, { editLayerId: opts.editLayerId || '', silent: opts.silent ?? true });
}
