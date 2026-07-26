// ═══ toolbox/hotspot-tool.js — Gi* 冷热点识别（手册 v2.2 §5.6·纯内嵌无 UI）═══
// /geo/hotspot → feats（hotspot/class/gi_class）→ class→极性重映射点层
// （_CLS_POL 映射随迁：hot=Very Negative 红 / cold=Very Positive 绿 / ns=Neutral 灰，
// 复用离散 5 色极性色带零 map.js 改动；class 原值保留供弹窗/观察）。
// 无 dialog/init/tool-row——仅 generateHotspotForAI 程序化入口（§4.1 契约）。
import { geoPost, placeToolLayer } from './shared.js';

/** params：{ layer(fc|注册名), value_col='score', invert=true, range?, pre_filter?, as? } */
async function _execute(params, { editLayerId = '', silent = true } = {}) {
  const body = { layer: params.layer, value_col: params.value_col || 'score', invert: params.invert !== false };
  if (params.range) body.range = params.range;
  if (params.pre_filter) body.pre_filter = params.pre_filter;
  const r = await geoPost('hotspot', body);
  const feats = (r.geojson && r.geojson.features) || [];
  // class → 极性色槽重映射（现状 :1147-1157）
  const _CLS_POL = { hot: 'Very Negative', cold: 'Very Positive', ns: 'Neutral' };
  const renderFc = {
    type: 'FeatureCollection',
    features: feats.map((f) => {
      const props = { ...(f.properties || {}) };
      const cls = props.hotspot || props.class || props.gi_class || 'ns';
      props.polarity = _CLS_POL[cls] || 'Neutral';
      return { ...f, properties: props };
    }),
  };
  const tally = {};
  feats.forEach((f) => {
    const p = f.properties || {};
    const cls = p.hotspot || p.class || p.gi_class || 'ns';
    tally[cls] = (tally[cls] || 0) + 1;
  });
  const name = params.as || '情绪热点(Gi*)';
  const ui = { tool: 'hotspot', value_col: body.value_col, invert: body.invert };
  const L = feats.length
    ? placeToolLayer({ name, kind: 'point', fc: renderFc, paint: { _ui: ui }, editLayerId, silent })
    : null;
  return { layerId: L && L.id, layerName: L ? name : null, featureCount: feats.length,
    fc: L ? renderFc : null, count: r.count, tally, truncated: r.truncated };
}

/** EMC 委托唯一接口（§4.1 契约）。 */
export async function generateHotspotForAI(opts = {}) {
  return _execute(opts, { editLayerId: opts.editLayerId || '', silent: opts.silent ?? true });
}
