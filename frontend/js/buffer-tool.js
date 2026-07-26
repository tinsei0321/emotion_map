// ═══ buffer-tool.js — Buffer 统一工具（手册 v2.2 §5.7 原地增强：cover 覆盖范围 + emotion 圈内情绪）═══
// cover：纯几何整层缓冲（/spatial/buffer，EPSG:4546，dissolve）——现状逻辑零改。
// emotion：圈内情绪聚合（/geo/buffer，center+radius+点层，返 point_count/极性入 properties）。
// 单一执行核 _execute：UI dialog 与 generateBufferForAI 共用（手册 §4.2 骨架，杜绝双实现债）。
// 编辑态：B 按钮打开（editLayerId）→ 按 paint._ui 回填 + 原地更新（layer id 稳定，镜像 H「继续编辑」）。
// _ui 契约（§4.3）：新产物显式 kind；存量无 kind 按 color 判据（有 color→cover，否则→emotion）。
import { getLayers, getLayer, selectLayer, enforceMutualExclusion } from './state.js';
import { renderLayer, fitBoundsTo, removeLayerFromMap, getMap } from './map.js';
import { showLayerManager } from './sidebar.js';
import { fcBBox } from './import.js';
import { runBuffer, geoPost, searchPlaces } from './api.js';
import { trackGeneration } from './geocode-loader.js';   // 生成接入放大镜外环（青→橙）
import { toast } from './toast.js';
import { renderColorPicker } from './settings.js';
import { openParamPanel, closeParamPanel } from './param-panel.js';
import { defaultPaint, clampM, scaleRadius, addToolboxLayer } from './toolbox/shared.js';
import { polyCentroid } from './district-stats.js';

const dialogEl = () => document.getElementById('buffer-dialog');
const DEFAULT_COLOR = '#4FC3F7';   // 天蓝（缓冲默认色；轮廓与填充同色）
const DEFAULTS = { kind: 'cover', distance: 1000, dissolve: false, color: DEFAULT_COLOR, lineWidth: 1, lineStyle: 'solid', fillOpacity: 0.15 };
const EMO_STYLE = { lineWidth: 2, fillOpacity: 0.2, lineStyle: 'solid' };   // emotion 固定样式（与 EMC 现状一致·不含 color）

/** 可缓冲图层：已加载的点/线/面（排除 group / heatmap）。excludeId 用于编辑态排除自身。 */
const BUFFERABLE = (l) => l && (l.kind === 'point' || l.kind === 'line' || l.kind === 'polygon');
/** 情绪点层（圈内聚合对象）：点层且有数据。 */
const EMO_PT = (l) => l && l.kind === 'point' && l.fc && l.fc.features && l.fc.features.length;
/** 中心要素来源层：点/面层（点取 coordinates，面取质心）。 */
const CENTER_SRC = (l) => l && (l.kind === 'point' || l.kind === 'polygon') && l.fc && l.fc.features && l.fc.features.length;

// ── 中心选择状态（emotion 四路输入共用）──
let _centerSel = null;   // { name, lng, lat } | null
let _picking = false;    // 地图取点态

function _setCenter(sel, label) {
  _centerSel = sel;
  const el = dialogEl()?.querySelector('#buf-center-val');
  if (el) el.textContent = sel ? `已选：${label || sel.name}` : '';
}

function populateLayers(excludeId) {
  const sel = document.getElementById('buf-layer');
  if (!sel) return;
  const layers = getLayers().filter((l) => BUFFERABLE(l) && l.id !== excludeId);
  sel.innerHTML = layers.length
    ? layers.map((l) => `<option value="${l.id}">${l.name}</option>`).join('')
    : '<option value="" disabled>（暂无可缓冲的图层，先导入或上载数据）</option>';
  return layers;
}

function populateEmoLayers() {
  const sel = document.getElementById('buf-emo-layer');
  if (!sel) return;
  const layers = getLayers().filter(EMO_PT);
  sel.innerHTML = layers.length
    ? layers.map((l) => `<option value="${l.id}">${l.name}</option>`).join('')
    : '<option value="" disabled>（暂无情绪点层）</option>';
  return layers;
}

function populateCenterLayers(excludeId) {
  const sel = document.getElementById('buf-center-layer');
  if (!sel) return;
  const layers = getLayers().filter((l) => CENTER_SRC(l) && l.id !== excludeId);
  sel.innerHTML = '<option value="">（选图层）</option>' +
    layers.map((l) => `<option value="${l.id}">${l.name}</option>`).join('');
  return layers;
}

function populateCenterFeatures(layerId) {
  const sel = document.getElementById('buf-center-feature');
  if (!sel) return;
  const l = layerId ? getLayer(layerId) : null;
  const feats = (l && l.fc && l.fc.features) || [];
  sel.innerHTML = '<option value="">（选要素）</option>' + feats.slice(0, 500).map((f, i) => {
    const nm = (f.properties && (f.properties.name || f.properties.Name || f.properties.NAME)) || `要素 ${i + 1}`;
    return `<option value="${i}">${nm}</option>`;
  }).join('');
}

/** 当前缓冲色（picker 写、generate 读；闭包替代旧 DOM .swatch.is-sel 查询）。 */
let _bufColor = DEFAULT_COLOR;
/** 渲染颜色取色器（与 settings 要素色板同源 renderColorPicker：离散色段，点段取预设色）。 */
function renderBufferColor(current = DEFAULT_COLOR) {
  const box = document.getElementById('buf-color-list');
  if (!box) return;
  _bufColor = current;
  renderColorPicker(box, { current, onPick: (hex) => { _bufColor = hex; } });
}

function setHidden(dlg, sel, hidden) { const el = dlg.querySelector(sel); if (el) el.hidden = hidden; }

/** 模式显隐（镜像 grid-tool constrainParams）：cover=输入图层+dissolve+样式；emotion=中心四路+点层。 */
function constrainKind(dlg) {
  const kind = selectedKind(dlg);
  setHidden(dlg, '#buf-cover-params', kind !== 'cover');
  setHidden(dlg, '#buf-emotion-params', kind !== 'emotion');
  setHidden(dlg, '#buf-dissolve-section', kind !== 'cover');
  setHidden(dlg, '#buf-style-group', kind !== 'cover');
  const lab = dlg.querySelector('#buf-dist-label'); if (lab) lab.textContent = kind === 'emotion' ? '缓冲半径' : '缓冲距离';
}
function selectedKind(dlg) {
  return dlg.querySelector('#buf-kind .buf-cap.is-sel')?.dataset.kind || DEFAULTS.kind;
}

/** 应用一组参数到对话框控件（新建默认态 / 编辑态回填共用）。 */
function applyParams(dlg, p) {
  const dist = p.distance ?? p.radius_m ?? DEFAULTS.distance;
  dlg.querySelector('#buf-distance-num').value = dist;
  const slider = dlg.querySelector('#buf-distance');
  slider.value = Math.min(Number(slider.max), Math.max(Number(slider.min), dist));
  const diss = p.dissolve ? 'true' : 'false';
  const dr = dlg.querySelector(`input[name="buf-dissolve"][value="${diss}"]`);
  if (dr) dr.checked = true;
  renderBufferColor(p.color || DEFAULTS.color);
  const lw = p.lineWidth ?? DEFAULTS.lineWidth;
  dlg.querySelector('#buf-linewidth').value = lw;
  dlg.querySelector('#buf-linewidth-val').textContent = `${lw} px`;
  const ls = p.lineStyle || DEFAULTS.lineStyle;
  dlg.querySelectorAll('#buf-linestyle .buf-cap').forEach((c) => c.classList.toggle('is-sel', c.dataset.linestyle === ls));
  const fo = Math.round((p.fillOpacity ?? DEFAULTS.fillOpacity) * 100);
  dlg.querySelector('#buf-opacity').value = fo;
  dlg.querySelector('#buf-opacity-val').textContent = `${fo}%`;
}

/** emotion 编辑回填：center FC → _centerSel + 手输坐标；点层 → 下拉选中。 */
function applyEmotionSeed(dlg, seed) {
  const c = seed.center;
  const geom = c && c.type === 'FeatureCollection' ? (c.features[0] || {}).geometry : (c && c.type === 'Feature' ? c.geometry : c);
  const coord = geom && geom.type === 'Point' ? geom.coordinates : null;
  if (coord && coord.length >= 2) {
    // 回填切到「手输坐标」页签（中心可检视可微调；其余三路不留存快照）
    dlg.querySelectorAll('#buf-center-mode .buf-cap').forEach((x) => x.classList.toggle('is-sel', x.dataset.cmode === 'coord'));
    dlg.querySelectorAll('[data-cmode-pane]').forEach((p) => { p.hidden = p.dataset.cmodePane !== 'coord'; });
    const lngEl = dlg.querySelector('#buf-center-lng'); const latEl = dlg.querySelector('#buf-center-lat');
    if (lngEl) lngEl.value = coord[0]; if (latEl) latEl.value = coord[1];
    _setCenter({ name: seed.centerName || '编辑中心', lng: coord[0], lat: coord[1] }, seed.centerName);
  }
  if (seed.layerId) { const sel = dlg.querySelector('#buf-emo-layer'); if (sel) sel.value = seed.layerId; }
}

export function openBufferDialog(layerId) {
  const dlg = dialogEl();
  if (!dlg) return;

  // 编辑态：从既有缓冲层的 paint._ui 回填参数 + 源图层锁定
  // kind 判据（§4.3 v2.2）：显式 kind 优先；存量无 kind → 有 color 字段为 cover，否则 emotion
  let seed = null;
  let kind = DEFAULTS.kind;
  if (layerId) {
    const lyr = getLayer(layerId);
    if (lyr && lyr.paint && lyr.paint._ui && lyr.paint._ui.tool === 'buffer') {
      seed = lyr.paint._ui;
      kind = seed.kind || (seed.color ? 'cover' : 'emotion');
    }
  }
  dlg.querySelectorAll('#buf-kind .buf-cap').forEach((c) => c.classList.toggle('is-sel', c.dataset.kind === kind));

  populateLayers(layerId);   // 编辑态排除自身（避免缓冲自己）
  populateEmoLayers();
  populateCenterLayers(layerId);
  _setCenter(null);
  if (seed && kind === 'cover' && seed.sourceLayer) {
    const el = dlg.querySelector('#buf-layer');
    if (el && getLayer(seed.sourceLayer)) el.value = seed.sourceLayer;
  }
  applyParams(dlg, seed || DEFAULTS);
  if (seed && kind === 'emotion') applyEmotionSeed(dlg, seed);
  constrainKind(dlg);
  dlg.dataset.editLayerId = layerId || '';

  if (kind === 'cover' && !getLayers().some(BUFFERABLE)) {
    toast.info('请先导入或上载一个点/线/面图层作为缓冲对象');
  }
  // B4：挂载点迁入 #param-panel 右栏缓冲页签；原 dlg.showModal() → 面板显隐 + 激活页签。
  openParamPanel('buffer');
}

function readParams(dlg) {
  const kind = selectedKind(dlg);
  const base = {
    kind,
    distance: Number(dlg.querySelector('#buf-distance-num').value) || 0,
    dissolve: dlg.querySelector('input[name="buf-dissolve"]:checked')?.value === 'true',
    color: _bufColor,
    lineWidth: Number(dlg.querySelector('#buf-linewidth').value),
    lineStyle: dlg.querySelector('#buf-linestyle .buf-cap.is-sel')?.dataset.linestyle || 'solid',
    fillOpacity: Number(dlg.querySelector('#buf-opacity').value) / 100,
  };
  if (kind === 'emotion') {
    const emoLayerId = dlg.querySelector('#buf-emo-layer')?.value || '';
    const emoLayer = emoLayerId ? getLayer(emoLayerId) : null;
    base.center = _centerSel;
    base.emoLayerId = emoLayer ? emoLayer.id : '';
    base.emoLayerName = emoLayer ? emoLayer.name : '';
    base.emoLayerFc = emoLayer ? emoLayer.fc : null;
  }
  return base;
}

// ═══ 单一执行核（手册 §4.2）：UI 与 ForAI 共用 ═══
/** params.kind='cover'：{ sourceLayer(id|layer), distance, dissolve, color, lineWidth, lineStyle, fillOpacity }
 *  params.kind='emotion'：{ center({name,lng,lat}|PointFC|preset str), radius|distance, layer|emoLayerFc|emoLayerName, agg_cols?, range?, pre_filter?, as? } */
async function _execute(params, { editLayerId = '', silent = true } = {}) {
  const kind = params.kind || 'cover';
  let fc, labelName, ui, paint, extra = {};

  if (kind === 'emotion') {
    // ── 圈内情绪聚合（/geo/buffer）──
    const c = params.center;
    const centerName = (c && c.name) || params.centerName || '设施';
    const centerFC = (c && c.lng != null)
      ? { type: 'FeatureCollection', features: [{ type: 'Feature', properties: { name: centerName }, geometry: { type: 'Point', coordinates: [Number(c.lng), Number(c.lat)] } }] }
      : c;   // 已是 FC / preset_id 字符串（ForAI 路径）
    if (!centerFC) throw new Error('emotion 模式需中心（四路输入或 center 参数）');
    const radius = clampM(Number(params.radius) || Number(params.distance) || scaleRadius(centerName) || 500);
    const body = { center: centerFC, radius_m: radius };
    const emoFc = params.emoLayerFc || (params.layer && typeof params.layer === 'object' ? params.layer : null);
    if (emoFc) body.layer = emoFc;   // send-in GeoJSON（前端层）
    else if (params.layer) body.layer = params.layer;   // 后端注册层名/id（EMC 委托现状）
    else if (params.emoLayerName) body.layer = params.emoLayerName;
    if (params.agg_cols) body.agg_cols = params.agg_cols;
    if (params.range) body.range = params.range;
    if (params.pre_filter) body.pre_filter = params.pre_filter;

    const r = silent ? await geoPost('buffer', body) : await trackGeneration(geoPost('buffer', body));
    fc = r.geojson;
    if (!fc || !fc.features || !fc.features.length) throw new Error('缓冲结果为空');
    const p0 = (fc.features[0] && fc.features[0].properties) || {};
    extra = { radiusM: r.radius_m || radius, areaKm2: Number(p0.area_km2) || 0,
      aggregated: p0.point_count != null, pointCount: p0.point_count, polarityIndex: p0.polarity_index };
    labelName = params.as || `${centerName}·${radius}m`;   // 名=对象+半径（C6 现状：「滨江公园·500m」）
    ui = { tool: 'buffer', kind: 'emotion', center: centerFC, centerName, radius_m: radius, distance: radius,
      layerId: params.emoLayerId || undefined, layerName: params.emoLayerName || (typeof params.layer === 'string' ? params.layer : undefined),
      dissolve: false, ...EMO_STYLE };   // §4.3：emotion 不含 color（存量 color 判据兼容）
    paint = { ...defaultPaint('buffer', 'polygon'), _ui: ui };
  } else {
    // ── 覆盖范围（/spatial/buffer·现状逻辑零改）──
    const sourceLayer = params.sourceLayer && params.sourceLayer.fc
      ? params.sourceLayer
      : getLayers().find((l) => l.id === (params.sourceLayer || params.sourceLayerId));
    if (!sourceLayer || !sourceLayer.fc || !sourceLayer.fc.features || !sourceLayer.fc.features.length) {
      throw new Error('请先选择一个有效的设施图层');
    }
    const run = runBuffer({ geojson: sourceLayer.fc, distance: params.distance, unit: 'm', dissolve: params.dissolve });
    const res = silent ? await run : await trackGeneration(run);
    if (!res || !res.success || !res.buffer_geojson) throw new Error((res && res.message) || '后端返回异常');
    fc = res.buffer_geojson;
    if (!fc.features || !fc.features.length) throw new Error('缓冲结果为空');
    extra = { featureCount: res.feature_count, coveredAreaKm2: res.covered_area_km2 };
    ui = { tool: 'buffer', kind: 'cover', sourceLayer: sourceLayer.id, distance: params.distance, dissolve: params.dissolve,
      color: params.color, lineWidth: params.lineWidth, lineStyle: params.lineStyle, fillOpacity: params.fillOpacity };
    paint = { color: params.color, fillOn: true, fillOpacity: params.fillOpacity, lineWidth: params.lineWidth, lineStyle: params.lineStyle, _ui: ui };
    labelName = params.as || `缓冲 · ${params.distance}m · ${sourceLayer.srcName || sourceLayer.name}`;
  }

  // ── B「继续编辑」：原地更新（layer id 稳定；仅当编辑层 kind 与本次一致，防 cover/emotion 互覆）──
  const editingLayer = editLayerId ? getLayer(editLayerId) : null;
  if (editingLayer && editingLayer.paint && editingLayer.paint._ui && editingLayer.paint._ui.tool === 'buffer') {
    const editKind = editingLayer.paint._ui.kind || (editingLayer.paint._ui.color ? 'cover' : 'emotion');
    if (editKind === kind) {
      editingLayer.fc = fc;
      editingLayer.paint = paint;
      editingLayer.name = labelName;
      removeLayerFromMap(editLayerId);
      renderLayer(editingLayer);
      if (!silent) {
        selectLayer(editLayerId);
        document.dispatchEvent(new CustomEvent('layers:changed'));
        document.dispatchEvent(new CustomEvent('layer:selected', { detail: editLayerId }));
      }
      const bb = fcBBox(fc); if (bb) fitBoundsTo(bb);
      return { layerId: editLayerId, layerName: labelName, featureCount: extra.featureCount ?? fc.features.length, fc, edited: true, kind, ...extra };
    }
  }

  // ── 新建：addToolboxLayer 通用落图（去重/自检/列表刷新/缩放）+ 同类互斥（手册 §4.2 骨架）──
  const L = addToolboxLayer({ name: labelName, kind: 'polygon', fc, paint });
  for (const hid of enforceMutualExclusion(L.id)) { const hl = getLayer(hid); if (hl) renderLayer(hl); }   // 互斥：关其他分析层+点层，保 Range
  if (!silent) {
    selectLayer(L.id);
    showLayerManager();
    document.dispatchEvent(new CustomEvent('layer:selected', { detail: L.id }));
  }
  return { layerId: L.id, layerName: labelName, featureCount: extra.featureCount ?? fc.features.length, fc, kind, ...extra };
}

/** EMC 委托唯一接口（手册 §4.1 契约）。EMC buffer 固定 kind:'emotion'（步 7 委托层传入）。 */
export async function generateBufferForAI(opts = {}) {
  return _execute(opts, { editLayerId: opts.editLayerId || '', silent: opts.silent ?? true });
}

async function generateBuffer() {
  const dlg = dialogEl();
  const p = readParams(dlg);
  if (p.distance <= 0) { toast.error('缓冲距离需 > 0'); return; }
  if (p.kind === 'emotion' && !p.center) { toast.error('请先选择缓冲中心（地点搜索/地图取点/图层要素/手输坐标）'); return; }
  if (p.kind === 'emotion' && !p.emoLayerFc) { toast.error('请选择圈内聚合的情绪点层'); return; }

  const btn = dlg.querySelector('#buf-generate');
  const orig = btn.textContent;
  btn.disabled = true; btn.textContent = '生成中…';

  try {
    const params = p.kind === 'emotion'
      ? p
      : { ...p, sourceLayer: dlg.querySelector('#buf-layer').value };
    const r = await _execute(params, { editLayerId: dlg.dataset.editLayerId, silent: false });
    closeParamPanel();
    if (p.kind === 'emotion') {
      const aggTxt = r.aggregated ? `，圈内 ${r.pointCount} 点·极性 ${Number(r.polarityIndex).toFixed(2)}` : '';
      toast.success(`${r.edited ? '已更新' : '已生成'}缓冲圈：${r.layerName}（约 ${Number(r.areaKm2).toFixed(2)} km²${aggTxt}）`);
    } else {
      toast.success(r.edited ? `已更新缓冲区：${p.distance}m · ${r.featureCount} 个`
        : `已生成 ${r.featureCount} 个缓冲区，总覆盖 ${Number(r.coveredAreaKm2 || 0).toFixed(2)} km²`);
    }
  } catch (e) {
    console.error('[buffer]', e);
    toast.error(`缓冲分析失败：${e.message || e}（确认后端已启动：uvicorn api.main:app --port 8000）`);
  } finally {
    btn.disabled = false; btn.textContent = orig;
  }
}

// ── 中心输入 · 四路 ──

/** a. 地点搜索（debounce 300ms + 候选下拉，镜像 search-bar 模式） */
function bindCenterSearch(dlg) {
  const input = dlg.querySelector('#buf-center-search');
  const hits = dlg.querySelector('#buf-center-hits');
  if (!input || !hits) return;
  let timer = null;
  input.addEventListener('input', () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (!q) { hits.hidden = true; hits.innerHTML = ''; return; }
    timer = setTimeout(() => {
      searchPlaces(q, 8).then((res) => {
        if (input.value.trim() !== q) return;   // 过期响应丢弃
        const list = (res && res.hits) || [];
        hits.innerHTML = list.length
          ? list.map((h, i) => `<button type="button" class="buf-hit" data-i="${i}">${h.name}<span class="buf-hit-addr">${h.address || h.zone_name || ''}</span></button>`).join('')
          : '<div class="buf-hit-empty">无匹配地点</div>';
        hits._hits = list;
        hits.hidden = false;
      }).catch(() => { hits.innerHTML = '<div class="buf-hit-empty">搜索失败</div>'; hits.hidden = false; });
    }, 300);
  });
  hits.addEventListener('click', (e) => {
    const b = e.target.closest('.buf-hit');
    if (!b || !hits._hits) return;
    const h = hits._hits[Number(b.dataset.i)];
    if (!h) return;
    input.value = h.name;
    hits.hidden = true;
    _setCenter({ name: h.name, lng: h.lng, lat: h.lat }, h.name);
  });
}

/** b. 地图取点（进入取点态：crosshair + map.once click；Esc 取消） */
function bindCenterPick(dlg) {
  const btn = dlg.querySelector('#buf-pick-btn');
  if (!btn) return;
  const cancel = (e) => { if (e.key === 'Escape' && _picking) exitPick(); };
  const exitPick = () => {
    const m = getMap();
    if (m) m.getCanvas().style.cursor = '';
    _picking = false;
    btn.textContent = '进入取点';
    document.removeEventListener('keydown', cancel);
  };
  btn.addEventListener('click', () => {
    const m = getMap();
    if (!m) return;
    if (_picking) { exitPick(); return; }
    _picking = true;
    btn.textContent = '取点中…点击地图（Esc 取消）';
    m.getCanvas().style.cursor = 'crosshair';
    document.addEventListener('keydown', cancel);
    m.once('click', (e) => {
      const { lng, lat } = e.lngLat;
      exitPick();
      const r6 = (v) => Math.round(v * 1e6) / 1e6;
      _setCenter({ name: `取点(${r6(lng)},${r6(lat)})`, lng, lat });
    });
  });
}

/** c. 图层要素（点取 coordinates；面取 polyCentroid） */
function bindCenterFeature(dlg) {
  const layerSel = dlg.querySelector('#buf-center-layer');
  const featSel = dlg.querySelector('#buf-center-feature');
  if (!layerSel || !featSel) return;
  layerSel.addEventListener('change', () => populateCenterFeatures(layerSel.value));
  featSel.addEventListener('change', () => {
    const l = layerSel.value ? getLayer(layerSel.value) : null;
    const f = l && l.fc ? l.fc.features[Number(featSel.value)] : null;
    if (!f) return;
    const g = f.geometry || {};
    const nm = (f.properties && (f.properties.name || f.properties.Name || f.properties.NAME)) || '要素';
    const coord = g.type === 'Point' ? g.coordinates : polyCentroid(f);
    if (!coord) { toast.error('该要素无法取中心点'); return; }
    _setCenter({ name: nm, lng: coord[0], lat: coord[1] }, nm);
  });
}

/** d. 手输坐标（lng/lat 两个 number input） */
function bindCenterCoord(dlg) {
  const lngEl = dlg.querySelector('#buf-center-lng');
  const latEl = dlg.querySelector('#buf-center-lat');
  if (!lngEl || !latEl) return;
  const update = () => {
    const lng = Number(lngEl.value); const lat = Number(latEl.value);
    if (!isFinite(lng) || !isFinite(lat) || !lngEl.value || !latEl.value) return;
    if (Math.abs(lng) > 180 || Math.abs(lat) > 90) return;
    _setCenter({ name: `坐标(${lng},${lat})`, lng, lat });
  };
  lngEl.addEventListener('input', update);
  latEl.addEventListener('input', update);
}

export function initBufferTool() {
  const dlg = dialogEl();
  if (!dlg) return;

  // 模式胶囊（覆盖范围/圈内情绪）→ 显隐切换（镜像 constrainParams）
  dlg.querySelector('#buf-kind').addEventListener('click', (e) => {
    const b = e.target.closest('.buf-cap');
    if (!b) return;
    dlg.querySelectorAll('#buf-kind .buf-cap').forEach((x) => x.classList.remove('is-sel'));
    b.classList.add('is-sel');
    constrainKind(dlg);
  });

  // 中心输入方式胶囊（四路显隐）
  dlg.querySelector('#buf-center-mode').addEventListener('click', (e) => {
    const b = e.target.closest('.buf-cap');
    if (!b) return;
    dlg.querySelectorAll('#buf-center-mode .buf-cap').forEach((x) => x.classList.remove('is-sel'));
    b.classList.add('is-sel');
    dlg.querySelectorAll('[data-cmode-pane]').forEach((p) => { p.hidden = p.dataset.cmodePane !== b.dataset.cmode; });
  });
  bindCenterSearch(dlg);
  bindCenterPick(dlg);
  bindCenterFeature(dlg);
  bindCenterCoord(dlg);

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
    slider.value = clampSlider(Number(num.value) || 0);
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
