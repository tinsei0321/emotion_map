// ═══ buffer-tool.js — Buffer 覆盖范围分析（后端 EPSG:4546，整层缓冲，纯几何） ═══
// 镜像 heatmap-tool：① 输入图层 ② 缓冲参数 ③ 显示样式。
// B 按钮打开（editLayerId）→ 回填当前层参数 + 原地更新（layer id 稳定，镜像 H「继续编辑」）。
// 后端 POST /api/v1/spatial/buffer 在 EPSG:4546 下 buffer，回 WGS84 GeoJSON 落图。
import { getLayers, addLayer, getLayer, selectLayer } from './state.js';
import { renderLayer, fitBoundsTo, reorderAllZ, removeLayerFromMap } from './map.js';
import { renderLayerList, refreshLegend, showLayerManager } from './sidebar.js';
import { fcBBox } from './import.js';
import { runBuffer } from './api.js';
import { toast } from './toast.js';
import { PRESET_COLORS } from './settings.js';

const dialogEl = () => document.getElementById('buffer-dialog');
const DEFAULT_COLOR = '#4FC3F7';   // 天蓝（缓冲默认色；轮廓与填充同色）
const DEFAULTS = { distance: 1000, dissolve: false, color: DEFAULT_COLOR, lineWidth: 1, lineStyle: 'solid', fillOpacity: 0.15 };

/** 可缓冲图层：已加载的点/线/面（排除 group / heatmap）。excludeId 用于编辑态排除自身。 */
const BUFFERABLE = (l) => l && (l.kind === 'point' || l.kind === 'line' || l.kind === 'polygon');

function populateLayers(excludeId) {
  const sel = document.getElementById('buf-layer');
  if (!sel) return;
  const layers = getLayers().filter((l) => BUFFERABLE(l) && l.id !== excludeId);
  sel.innerHTML = layers.length
    ? layers.map((l) => `<option value="${l.id}">${l.name}</option>`).join('')
    : '<option value="" disabled>（暂无可缓冲的图层，先导入或上载数据）</option>';
  return layers;
}

/** 渲染颜色预设 swatches（复用全局 PRESET_COLORS；默认/回填色选中）。 */
function renderColorSwatches(current = DEFAULT_COLOR) {
  const box = document.getElementById('buf-color-list');
  if (!box) return;
  box.innerHTML = PRESET_COLORS.map((c) =>
    `<button type="button" class="swatch${c.toLowerCase() === current.toLowerCase() ? ' is-sel' : ''}" style="background:${c}" data-color="${c}" title="${c}"></button>`).join('');
  box.querySelectorAll('.swatch').forEach((b) => {
    b.addEventListener('click', () => {
      box.querySelectorAll('.swatch').forEach((x) => x.classList.remove('is-sel'));
      b.classList.add('is-sel');
    });
  });
}

/** 应用一组参数到对话框控件（新建默认态 / 编辑态回填共用）。 */
function applyParams(dlg, p) {
  const dist = p.distance ?? DEFAULTS.distance;
  dlg.querySelector('#buf-distance-num').value = dist;
  const slider = dlg.querySelector('#buf-distance');
  slider.value = Math.min(Number(slider.max), Math.max(Number(slider.min), dist));
  const diss = p.dissolve ? 'true' : 'false';
  const dr = dlg.querySelector(`input[name="buf-dissolve"][value="${diss}"]`);
  if (dr) dr.checked = true;
  renderColorSwatches(p.color || DEFAULTS.color);
  const lw = p.lineWidth ?? DEFAULTS.lineWidth;
  dlg.querySelector('#buf-linewidth').value = lw;
  dlg.querySelector('#buf-linewidth-val').textContent = `${lw} px`;
  const ls = p.lineStyle || DEFAULTS.lineStyle;
  dlg.querySelectorAll('#buf-linestyle .buf-cap').forEach((c) => c.classList.toggle('is-sel', c.dataset.linestyle === ls));
  const fo = Math.round((p.fillOpacity ?? DEFAULTS.fillOpacity) * 100);
  dlg.querySelector('#buf-opacity').value = fo;
  dlg.querySelector('#buf-opacity-val').textContent = `${fo}%`;
}

export function openBufferDialog(layerId) {
  const dlg = dialogEl();
  if (!dlg) return;
  if (dlg.open) dlg.close();

  // 编辑态：从既有缓冲层的 paint._ui 回填参数 + 源图层锁定
  let seed = null;
  let sourceLayerId = null;
  if (layerId) {
    const lyr = getLayer(layerId);
    if (lyr && lyr.paint && lyr.paint._ui && lyr.paint._ui.tool === 'buffer') {
      seed = lyr.paint._ui;
      sourceLayerId = lyr.paint._ui.sourceLayer;
    }
  }
  const layers = populateLayers(layerId);   // 编辑态排除自身（避免缓冲自己）
  if (sourceLayerId && layers && layers.find((l) => l.id === sourceLayerId)) {
    dlg.querySelector('#buf-layer').value = sourceLayerId;
  }
  applyParams(dlg, seed || DEFAULTS);
  dlg.dataset.editLayerId = layerId || '';

  if (!getLayers().some(BUFFERABLE)) {
    toast.info('请先导入或上载一个点/线/面图层作为缓冲对象');
  }
  dlg.showModal();
}

function readParams(dlg) {
  return {
    distance: Number(dlg.querySelector('#buf-distance-num').value) || 0,
    dissolve: dlg.querySelector('input[name="buf-dissolve"]:checked')?.value === 'true',
    color: dlg.querySelector('#buf-color-list .swatch.is-sel')?.dataset.color || DEFAULT_COLOR,
    lineWidth: Number(dlg.querySelector('#buf-linewidth').value),
    lineStyle: dlg.querySelector('#buf-linestyle .buf-cap.is-sel')?.dataset.linestyle || 'solid',
    fillOpacity: Number(dlg.querySelector('#buf-opacity').value) / 100,
  };
}

async function generateBuffer() {
  const dlg = dialogEl();
  const p = readParams(dlg);
  if (p.distance <= 0) { toast.error('缓冲距离需 > 0'); return; }

  const sourceLayer = getLayers().find((l) => l.id === dlg.querySelector('#buf-layer').value);
  if (!sourceLayer || !sourceLayer.fc || !sourceLayer.fc.features || !sourceLayer.fc.features.length) {
    toast.error('请先选择一个有效的设施图层'); return;
  }

  const btn = dlg.querySelector('#buf-generate');
  const orig = btn.textContent;
  btn.disabled = true; btn.textContent = '生成中…';

  try {
    const res = await runBuffer({ geojson: sourceLayer.fc, distance: p.distance, unit: 'm', dissolve: p.dissolve });
    if (!res || !res.success || !res.buffer_geojson) throw new Error((res && res.message) || '后端返回异常');
    const fc = res.buffer_geojson;
    if (!fc.features || !fc.features.length) { toast.error('缓冲结果为空'); return; }

    const ui = { tool: 'buffer', sourceLayer: sourceLayer.id, distance: p.distance, dissolve: p.dissolve,
                 color: p.color, lineWidth: p.lineWidth, lineStyle: p.lineStyle, fillOpacity: p.fillOpacity };
    const paint = { color: p.color, fillOn: true, fillOpacity: p.fillOpacity, lineWidth: p.lineWidth, lineStyle: p.lineStyle, _ui: ui };
    const labelName = `缓冲 · ${p.distance}m · ${sourceLayer.srcName || sourceLayer.name}`;

    // ── B「继续编辑」：原地更新该层（layer id 稳定，镜像 heatmap）──
    const editLayerId = dlg.dataset.editLayerId;
    const editingLayer = editLayerId ? getLayer(editLayerId) : null;
    if (editingLayer && editingLayer.paint && editingLayer.paint._ui && editingLayer.paint._ui.tool === 'buffer') {
      editingLayer.fc = fc;
      editingLayer.paint = paint;
      editingLayer.name = labelName;
      editingLayer.srcName = sourceLayer.srcName || sourceLayer.name;
      removeLayerFromMap(editLayerId);
      renderLayer(editingLayer);
      selectLayer(editLayerId);
      document.dispatchEvent(new CustomEvent('layers:changed'));
      document.dispatchEvent(new CustomEvent('layer:selected', { detail: editLayerId }));
      const bb = fcBBox(fc); if (bb) fitBoundsTo(bb);
      dlg.close();
      toast.success(`已更新缓冲区：${p.distance}m · ${fc.features.length} 个`);
      return;
    }

    // ── 新建 ──
    const L = addLayer({ name: labelName, kind: 'polygon', fc, paint });
    L.srcName = sourceLayer.srcName || sourceLayer.name;
    renderLayer(L);
    const bb = fcBBox(fc); if (bb) fitBoundsTo(bb);
    renderLayerList();
    refreshLegend();
    reorderAllZ();
    showLayerManager();
    document.dispatchEvent(new CustomEvent('layers:changed'));
    document.dispatchEvent(new CustomEvent('layer:selected', { detail: L.id }));
    dlg.close();
    toast.success(`已生成 ${res.feature_count} 个缓冲区，总覆盖 ${res.covered_area_km2} km²`);
  } catch (e) {
    console.error('[buffer]', e);
    toast.error(`缓冲分析失败：${e.message || e}（确认后端已启动：uvicorn api.main:app --port 8000）`);
  } finally {
    btn.disabled = false; btn.textContent = orig;
  }
}

export function initBufferTool() {
  const dlg = dialogEl();
  if (!dlg) return;

  // 距离：手动输入框 ↔ 滑块 同步（输入框权威，可超滑块上限；单位 m 为静态后缀，不再重复显示值）
  const num = dlg.querySelector('#buf-distance-num');
  const slider = dlg.querySelector('#buf-distance');
  const clampSlider = (n) => Math.max(Number(slider.min), Math.min(Number(slider.max), n));
  num.addEventListener('input', () => { slider.value = clampSlider(Number(num.value) || 0); });
  slider.addEventListener('input', () => { num.value = slider.value; });
  dlg.querySelector('#buf-presets').addEventListener('click', (e) => {
    const b = e.target.closest('.buf-preset');
    if (!b) return;
    num.value = b.dataset.dist;
    slider.value = clampSlider(Number(b.dataset.dist));
  });

  // 线型胶囊（实线/虚线）单选
  dlg.querySelector('#buf-linestyle').addEventListener('click', (e) => {
    const b = e.target.closest('.buf-cap');
    if (!b) return;
    dlg.querySelectorAll('#buf-linestyle .buf-cap').forEach((x) => x.classList.remove('is-sel'));
    b.classList.add('is-sel');
  });

  // 线宽 / 填充透明度 live label
  dlg.querySelector('#buf-linewidth').addEventListener('input', (e) => {
    dlg.querySelector('#buf-linewidth-val').textContent = `${e.target.value} px`;
  });
  dlg.querySelector('#buf-opacity').addEventListener('input', (e) => {
    dlg.querySelector('#buf-opacity-val').textContent = `${e.target.value}%`;
  });

  dlg.querySelector('#buf-generate')?.addEventListener('click', generateBuffer);
}
