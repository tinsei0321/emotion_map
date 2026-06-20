// ═══ heatmap-legend.js — 右下图例：随选中热力图层显隐 + 离散分段色带 ═══
// 与极性/置信度/范围图例同处 #legend-stack（右下），保持设计语言统一。
// 监听 layer:selected / layers:changed，自包含；main.js 只需 initHeatmapLegend()。
import { getLayer, HEATMAP_RAMPS } from './state.js';

const OVERALL_RAMPS = ['rainbow', 'terrain-9', 'grid-warm', 'green-3', 'red-3', 'blue-3', 'diverging-rg'];

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
  const ramp = rampKey ? HEATMAP_RAMPS[rampKey] : null;
  if (!ramp) { box.hidden = true; return; }
  const segs = ramp.stops.filter(([d]) => d > 0).map(([, c]) => c);
  const re = rampEl();
  if (re) re.innerHTML = segs.map((c) => `<span class="legend-heat-seg" style="background:${c}"></span>`).join('');
  const overall = OVERALL_RAMPS.includes(rampKey);
  if (loEl()) loEl().textContent = overall ? '洼地/稀疏' : '稀疏';
  if (hiEl()) hiEl().textContent = overall ? '高地/密集' : '密集';
  box.hidden = false;
}

/** 初始化：监听选中/变更事件。 */
export function initHeatmapLegend() {
  document.addEventListener('layer:selected', (e) => {
    const l = getLayer(e.detail);
    refreshHeatmapLegend(l);
  });
  document.addEventListener('layers:changed', () => {
    // layers 变更（删除/清空）后，若当前无选中热力图层则隐藏
    const box = boxEl();
    if (!box || box.hidden) return;
    const sel = document.querySelector('.layer-row.is-selected');
    if (!sel) { box.hidden = true; }
  });
}
