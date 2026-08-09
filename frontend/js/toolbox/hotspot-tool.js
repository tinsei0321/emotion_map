// ═══ toolbox/hotspot-tool.js — Gi* 冷热点识别（手册 v2.2 §5.6·纯内嵌无 UI）═══
// /geo/hotspot → feats（hotspot/hotspot_tier/gi_class）→ 显著性符号点层
// （P1 修正·glm/Codex P1 修正评估：弃 _CLS_POL 极性色——Gi* 是显著性检验非极性；
//   走 map.js colorMode='hotspot' 显著性符号层·五档 hot/tend_hot/ns/tend_cold/cold
//   单色系 + 符号大小/描边分档·与 KDE 极性色解耦（两层视觉语义不再冲突）。
//   hotspot/hotspot_tier/Gi_Z 原值保留供弹窗/深读）。
// 无 dialog/init/tool-row——仅 generateHotspotForAI 程序化入口（§4.1 契约）。
import { geoPost, placeToolLayer } from './shared.js';

/** params：{ layer(fc|注册名), value_col='score', invert=true, range?, pre_filter?, threshold?, soft_threshold?, as? } */
async function _execute(params, { editLayerId = '', silent = true } = {}) {
  const body = { layer: params.layer, value_col: params.value_col || 'score', invert: params.invert !== false };
  if (params.range) body.range = params.range;
  if (params.pre_filter) body.pre_filter = params.pre_filter;
  if (params.threshold != null) body.threshold = params.threshold;           // W2 审计：转发显著性阈值（契约承诺参数化·补齐运行时缺口）
  if (params.soft_threshold != null) body.soft_threshold = params.soft_threshold;
  const r = await geoPost('hotspot', body);
  const feats = (r.geojson && r.geojson.features) || [];
  // P1 修正：不再映射 polarity（去极性色）·保留 hotspot_tier 五档原值（map.js 显著性符号层消费）
  const renderFc = {
    type: 'FeatureCollection',
    features: feats.map((f) => {
      const props = { ...(f.properties || {}) };
      props.hotspot_tier = props.hotspot_tier || props.hotspot || props.class || props.gi_class || 'ns';
      return { ...f, properties: props };
    }),
  };
  const tally = {};
  feats.forEach((f) => {
    const p = f.properties || {};
    const cls = p.hotspot || p.hotspot_tier || p.class || p.gi_class || 'ns';
    tally[cls] = (tally[cls] || 0) + 1;
  });
  const name = params.as || '显著聚集点(Gi*)';
  const ui = { tool: 'hotspot', value_col: body.value_col, invert: body.invert };
  const L = feats.length
    ? placeToolLayer({ name, kind: 'point', fc: renderFc, colorMode: 'hotspot', paint: { _ui: ui }, editLayerId, silent })
    : null;
  return { layerId: L && L.id, layerName: L ? name : null, featureCount: feats.length,
    fc: L ? renderFc : null, count: r.count, tally, truncated: r.truncated };
}

/** EMC 委托唯一接口（§4.1 契约）。 */
export async function generateHotspotForAI(opts = {}) {
  return _execute(opts, { editLayerId: opts.editLayerId || '', silent: opts.silent ?? true });
}
