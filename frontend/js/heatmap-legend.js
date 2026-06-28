// ═══ heatmap-legend.js — 右下图例：随选中热力图层显隐 + 离散分段色带 ═══
// 与极性/置信度/范围图例同处 #legend-stack（右下），保持设计语言统一。
// 监听 layer:selected / layers:changed，自包含；main.js 只需 initHeatmapLegend()。
import { getLayer, HEATMAP_RAMPS, rampDisplaySegs } from './state.js';

const OVERALL_RAMPS = ['rainbow', 'terrain-9', 'green-3', 'red-3', 'blue-3', 'diverging-rg'];

const boxEl = () => document.getElementById('legend-heatmap');
const rampEl = () => document.querySelector('#legend-heatmap .legend-heat-ramp');
const loEl = () => document.getElementById('legend-heat-lo');
const hiEl = () => document.getElementById('legend-heat-hi');

/** 按选中图层刷新图例；非热力图层 → 隐藏。 */
export function refreshHeatmapLegend(layer) {
  const box = boxEl();
  if (!box) return;
  if (!layer || layer.kind !== 'heatmap') { box.hidden = true; return; }
  const rampKey = (layer.paint && layer.paint.rampKey) || null;
  const ramp = (layer.paint && layer.paint.rampStops) ? { stops: layer.paint.rampStops } : (rampKey ? HEATMAP_RAMPS[rampKey] : null);
  if (!ramp) { box.hidden = true; return; }
  const segs = rampDisplaySegs(rampKey, ramp);
  const re = rampEl();
  if (re) re.innerHTML = segs.map((c) => `<span class="legend-heat-seg" style="background:${c}"></span>`).join('');
  // 类型细分色带显示已反转（rampDisplaySegs 高→低），标注随之反转：左=密集(强情绪·热核) / 右=稀疏(弱)
  const overall = OVERALL_RAMPS.includes(rampKey);
  const segment = ['positive', 'negative', 'neutral'].includes(rampKey);
  if (loEl()) loEl().textContent = overall ? '洼地/稀疏' : (segment ? '密集' : '稀疏');
  if (hiEl()) hiEl().textContent = overall ? '高地/密集' : (segment ? '稀疏' : '密集');
  box.hidden = false;
}

/** 当前选中的图层（从 sidebar 高亮行取，fallback 到 selected 状态）。 */
function selectedLayer() {
  const row = document.querySelector('.layer-row.is-selected');
  if (row) return getLayer(row.dataset.id);
  return null;
}

/** 初始化：监听选中/变更事件。 */
export function initHeatmapLegend() {
  document.addEventListener('layer:selected', (e) => {
    refreshHeatmapLegend(getLayer(e.detail));
  });
  // 图层显隐/删除（toggleEye/toggleGroupEye/removeLayer）→ 图例同步：
  // 选中层非热力图或不可见 → 隐藏；热力图且可见 → 显色带。
  document.addEventListener('layers:changed', () => {
    const l = selectedLayer();
    if (l && l.kind === 'heatmap' && l.visible) refreshHeatmapLegend(l);
    else { const box = boxEl(); if (box) box.hidden = true; }
  });
}
