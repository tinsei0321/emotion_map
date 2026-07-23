// ═══ map.js — MapLibre GL JS instance, multi-layer registry, basemap switch ═══
import { emotionColors, token, POLARITY_ORDER, getLayers, addLayer, setLayerVisible, reorderLayers, enforceMutualExclusion, CONFIDENCE_RAMP, confidenceColor, L2_POSITIVE, L2_NEGATIVE, L2_NEUTRAL_COLOR, HEATMAP_NEGATIVE_STOPS, HEATMAP_RAMPS, HOTNESS_RAMP, computeHotness, hotnessBuckets } from './state.js';
import { initControls } from './map-controls.js';
import { bindTipPopup } from './tip-popup.js';

// 天地图 Key（非敏感，前端可公开；同 core/config.py TIANDITU_KEY）—— 浏览器端权限类型（验 Referer）。
// 修复底图 404：原引 ../apps/static/tianditu_*.json（随 apps/ Phase 2 退役被删、且从未入 git）→ 404 →
// style 永不加载 → 底图不显示。改为**内联 raster style 对象**（不再依赖外部 JSON 文件，根除路径脆弱）。
const TIANDITU_KEY = '4d4dc85287c003c8a18d5520b8920796';
const _tiandituTiles = (T) => [0, 1, 2, 3].map((s) =>
  `https://t${s}.tianditu.gov.cn/DataServer?T=${T}&x={x}&y={y}&l={z}&tk=${TIANDITU_KEY}`);
// specs = [{id, T}]：img_w 影像 / cia_w 影像注记 / vec_w 矢量 / cva_w 矢量注记（皆 EPSG:3857 Web Mercator）
function _tiandituStyle(specs) {
  const sources = {}, layers = [];
  for (const { id, T } of specs) {
    sources[`tdt-${id}`] = { type: 'raster', tiles: _tiandituTiles(T), tileSize: 256, maxzoom: 18 };
    layers.push({ id: `tdt-${id}`, type: 'raster', source: `tdt-${id}` });
  }
  return { version: 8, sources, layers };
}
export const BASEMAPS = {
  // CARTO GL 矢量素图（kepler/MVP 同款，无注记，CDN 矢量瓦片，细节丰富+缩放清晰+快）
  'positron':    'https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json',
  'dark-matter': 'https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json',
  'voyager':     'https://basemaps.cartocdn.com/gl/voyager-nolabels-gl-style/style.json',
  // 天地图（影像/矢量 raster 瓦片，内联 style 对象；浏览器端 key 验 Referer，CDN 子域 t0-t3 负载均衡）
  'tianditu-img':         _tiandituStyle([{ id: 'img', T: 'img_w' }, { id: 'cia', T: 'cia_w' }]),   // 影像 + 注记
  'tianditu-vec':         _tiandituStyle([{ id: 'vec', T: 'vec_w' }, { id: 'cva', T: 'cva_w' }]),   // 矢量 + 注记
  'tianditu-img-nolabel': _tiandituStyle([{ id: 'img', T: 'img_w' }]),                              // 影像（无注记，干净卫星）
};
export const DEFAULT_BASEMAP = 'tianditu-img-nolabel';   // 初始底图：天地图影像（无注记，干净卫星）
const YICHANG = { center: [111.286, 30.708], zoom: 12 };
const NAVY = '#0c1c2e';
const HIT_WIDTH = 20;           // transparent hit-line width (easy hover/open on thin outlines; visible line stays 2px)

/** Density-adaptive point radius (user spec, L0-L4 uniform): by point count → tier,
 *  and within a tier the radius breathes with zoom (zoom in = bigger).
 *  Cap: 默认最大 ≤10px（密度大可更小，但稀疏档顶 10px——不再 14–18）。
 *    < 500           → 6–10px (sparse, capped at 10)
 *    500 ≤ n < 2000  → 4–7px
 *    ≥ 2000          → 2–4px
 *  Returns [rAtZoom8, rAtZoom14]. */
function densityStops(count) {
  if (count < 500) return [6, 10];
  if (count < 2000) return [4, 7];
  return [2, 4];
}
function densityRadiusExpr(count) {
  const [r8, r14] = densityStops(count);
  return ['interpolate', ['linear'], ['zoom'], 8, r8, 14, r14];
}
function densityRadiusAt(count, zoom) {
  const [r8, r14] = densityStops(count);
  const z = Math.max(8, Math.min(14, zoom));
  return r8 + (r14 - r8) * (z - 8) / 6;
}
/** Effective point radius for the settings slider default: paint.radius override, else density value at the current zoom. */
export function effectivePointRadius(layer) {
  const p = layer.paint || {};
  if (p.radius != null) return p.radius;
  return densityRadiusAt(layer.fc.features.length, map ? map.getZoom() : 11);
}

let map = null;
let _onPointClick = null;
let _selectedLayerId = null;   // which layer the selection halo belongs to (clear on hide/remove)
const _boundPoint = new Set();
const _boundRange = new Set();
let _tooltip = null;
let _currentBasemap = DEFAULT_BASEMAP;   // 当前底图 key（setBasemap 同步）

// ── 3D 暗底图：预载 dark-matter 真实矢量图层（dm-* 前缀），插在底图与数据层之间，pitch>1 时显隐 ──
//  不 setStyle 换底图（旧方案根因：setStyle 重载瓦片新旧交替=空白卡顿）→ 改 addSource/addLayer 预载 +
//  setLayoutProperty 显隐（零 setStyle 操作）。dark-matter 自带 opaque background + 路网/区块纹理 =
//  真"暗色（无注记）"观感（非纯黑遮罩）。数据层在 dm 之上保持亮。dm 层 vector 瓦片首显加载、后缓存。
const DM_BASEMAP_KEY = 'dark-matter';
const _BASEMAP_BG = { 'dark-matter': '#0e0e0e', 'positron': '#ffffff', 'voyager': '#f4f1ea', 'tianditu-img': '#a6c8e0', 'tianditu-vec': '#e8eef4', 'tianditu-img-nolabel': '#a6c8e0' };
let _dark3DOn = false;                    // 当前是否处暗色 3D 态（pitch>1）
let _dmLoaded = false;                    // dark-matter 图层是否已预载
const _dmLayerIds = [];                   // 预载的 dm 图层 id 列表（显隐用）

export function initMap(container = 'map') {
  map = new maplibregl.Map({
    container, style: BASEMAPS[DEFAULT_BASEMAP],
    center: YICHANG.center, zoom: YICHANG.zoom, attributionControl: true,
  });
  initControls(map, { getBBox: mergedBBox });
  // 3D 透视修正：默认垂直 FOV≈36.87°（长焦压缩→3D 柱体远近高差不明显、疑似轴测）。
  // 加宽到 55° → 近高远矮的透视关系接近肉眼；方向光给柱体各面明暗差（立体感）。
  // FOV 属 camera（setStyle 不重置，设一次即可）；light 属 style（setBasemap 切底图会重置）→ style.load 重敷。
  // 光源 position=[r, 方位角°, 极角°]（anchor=viewport：0°=上/北、顺时针；极角 0°=正上、90°=水平）：
  // 方位 45°=东北来光（亮面朝东北、暗面朝西南，默认北朝上视角下四梯度清晰）+ 极角 60°（偏低侧光，强化暗/次暗/亮面划分）。
  if (map.setVerticalFieldOfView) map.setVerticalFieldOfView(55);
  const _onStyleLoad = () => {
    if (map.setLight) map.setLight({ anchor: 'viewport', position: [1.5, 45, 60], color: '#ffffff', intensity: 0.5 });
    _loadDarkMatter();
  };
  map.on('style.load', _onStyleLoad);
  map.on('pitch', _onPitch);   // 3D 视角全局触发暗色遮罩（setView3D / map-controls 等任何 pitch 变化）
  const canvas = map.getCanvas();
  map.on('dragstart', () => canvas.classList.add('is-grabbing'));
  map.on('dragend', () => canvas.classList.remove('is-grabbing'));
  return map;
}

export function getMap() { return map; }

// ═══ 批4 时间对比 · Swipe 卷帘（mapB 第二实例 + manual sync + clip divider）═══════════
// Step 1 scaffold POC：仅 basemap，验证双 map 同步 + 卷帘 mechanics。层渲染/时间 A/B = Step 2/3。
// compare 是 toggle（setCompareMode），进/出不影响默认单 map 体验。不碰 renderLayer/applyTime（additive）。
let _mapB = null;
let _compareOn = false;
let _syncing = false;        // 防 mapA↔mapB move sync 反馈环
let _mapBWrap = null;
let _divider = null;

export function isCompareMode() { return _compareOn; }
export function getMapB() { return _mapB; }

/** 进/出 compare 卷帘模式。进：建 mapB（同 basemap + 同步视图）+ divider（默认 50%）+ 开 mapA→mapB sync。 */
export function setCompareMode(on) {
  if (on) _enterCompare(); else _exitCompare();
}

function _enterCompare() {
  if (!map) return;
  const host = document.getElementById('map');
  if (!host) return;
  if (!_mapBWrap) {
    _mapBWrap = document.createElement('div');
    _mapBWrap.className = 'map-b-wrap';
    host.appendChild(_mapBWrap);
  }
  _mapBWrap.style.display = 'block';
  if (!_mapB) {
    _mapB = new maplibregl.Map({
      container: _mapBWrap,
      style: BASEMAPS[_currentBasemap] || BASEMAPS[DEFAULT_BASEMAP],
      center: map.getCenter(), zoom: map.getZoom(), bearing: map.getBearing(), pitch: map.getPitch(),
      attributionControl: false,
    });
    _mapB.on('move', _syncFromB);
    _mapB.on('style.load', _onMapBStyleLoad);   // basemap 就绪：敷 3D 光 + 镜像 mapA 数据层
  } else {
    _mapB.jumpTo({ center: map.getCenter(), zoom: map.getZoom(), bearing: map.getBearing(), pitch: map.getPitch() });
    _mirrorLayersToMapB();                        // 已加载，直接镜像
  }
  if (!_divider) {
    _divider = document.createElement('div');
    _divider.className = 'swipe-divider';
    host.appendChild(_divider);
    _wireDividerDrag();
  }
  _divider.style.display = 'block';
  _setDivider(50);
  map.on('move', _syncFromA);
  _compareOn = true;
  host.classList.add('is-compare');
}

function _exitCompare() {
  if (map) map.off('move', _syncFromA);
  if (_mapBWrap) _mapBWrap.style.display = 'none';
  if (_divider) _divider.style.display = 'none';
  _compareOn = false;
  const host = document.getElementById('map');
  if (host) host.classList.remove('is-compare');
  document.dispatchEvent(new CustomEvent('compare:exit'));
}

function _syncFromA() {
  if (!_mapB || _syncing) return;
  _syncing = true;
  _mapB.jumpTo({ center: map.getCenter(), zoom: map.getZoom(), bearing: map.getBearing(), pitch: map.getPitch() });
  _syncing = false;
}
function _syncFromB() {
  if (!map || _syncing) return;
  _syncing = true;
  map.jumpTo({ center: _mapB.getCenter(), zoom: _mapB.getZoom(), bearing: _mapB.getBearing(), pitch: _mapB.getPitch() });
  _syncing = false;
}

/** divider 位置 pct(0..100)：mapB clip 到 pct 右侧（左显 mapA / 右显 mapB）。clip-path 同时切视觉+事件。 */
function _setDivider(pct) {
  if (_mapBWrap) _mapBWrap.style.clipPath = `inset(0 0 0 ${pct}%)`;
  if (_divider) _divider.style.left = pct + '%';
}

function _wireDividerDrag() {
  if (!_divider) return;
  let dragging = false;
  _divider.addEventListener('mousedown', (e) => { dragging = true; e.preventDefault(); });
  _divider.addEventListener('touchstart', () => { dragging = true; }, { passive: true });
  const onMove = (clientX) => {
    if (!dragging || !_compareOn) return;
    const host = document.getElementById('map');
    if (!host) return;
    const r = host.getBoundingClientRect();
    const pct = Math.max(0, Math.min(100, ((clientX - r.left) / r.width) * 100));
    _setDivider(pct);
  };
  window.addEventListener('mousemove', (e) => onMove(e.clientX));
  window.addEventListener('mouseup', () => { dragging = false; });
  window.addEventListener('touchmove', (e) => { if (e.touches[0]) onMove(e.touches[0].clientX); }, { passive: true });
  window.addEventListener('touchend', () => { dragging = false; });
}

/** mapB basemap 就绪：敷 3D 光（与 mapA 同）+ 镜像 mapA 数据层（Step 2 同片）。 */
function _onMapBStyleLoad() {
  if (!_mapB) return;
  if (_mapB.setLight) _mapB.setLight({ anchor: 'viewport', position: [1.5, 45, 60], color: '#ffffff', intensity: 0.5 });
  _mirrorLayersToMapB();
}

/** 批4 grid compare 焦点 grid 的 layer id（visible + tool=grid）。无焦点 → null（不镜像）。 */
function _focusedGridId() {
  const all = getLayers();
  const grids = all.filter((l) => l.paint && l.paint._ui && l.paint._ui.tool === 'grid');
  const g = grids.find((l) => l.visible);
  console.log('[compare] _focusedGridId: layers=' + all.length, 'grids=[' + grids.map((l) => l.id + ':vis=' + l.visible).join(',') + ']', '→ ' + (g && g.id));
  return g && g.id;
}

/** Step 3：镜像焦点 grid（+子层 -line/-hit/-extru）到 mapB——批4 grid A/B compare。
 *  points/range 不上 mapB（避免 grid 片B + points 片A 不一致）。非侵入（不动 renderLayer）。
 *  镜像完 dispatch compare:mapBready → time-bar 听 → renderSliceToMap(mapB, 片B)。 */
function _mirrorLayersToMapB() {
  if (!map || !_mapB) return;
  const gridId = _focusedGridId();
  if (!gridId) return;
  const want = (id) => id.startsWith(`lyr-${gridId}`);
  try {
    const bStyle = _mapB.getStyle();
    for (const l of (bStyle.layers || []).slice()) { if (want(l.id)) _mapB.removeLayer(l.id); }
    for (const sid of Object.keys(bStyle.sources || {})) { if (want(sid)) _mapB.removeSource(sid); }
    const aStyle = map.getStyle();
    for (const [sid, spec] of Object.entries(aStyle.sources || {})) { if (want(sid)) { try { _mapB.addSource(sid, spec); } catch (e) { console.warn('[compare] addSource ' + sid + ' 失败:', e.message); } } }
    for (const layerSpec of (aStyle.layers || [])) { if (want(layerSpec.id)) { try { _mapB.addLayer(layerSpec); } catch (e) { console.warn('[compare] addLayer ' + layerSpec.id + ' 失败:', e.message); } } }
    const aSrcs = Object.keys(aStyle.sources || {}).filter(want).length;
    const aLays = (aStyle.layers || []).filter((l) => want(l.id)).length;
    console.log('[compare] mirror grid=' + gridId, 'mapA srcs=' + aSrcs, 'layers=' + aLays, '→ dispatch mapBready');
    if (_compareOn) document.dispatchEvent(new CustomEvent('compare:mapBready', { detail: { gridId } }));
  } catch (e) { console.warn('[compare] mirror 失败', e); }
}

// compare 模式下 mapA 层变化（renderLayer/applyTime 等 dispatch layers:changed）→ 重镜像 mapB（Step 2 同片）
if (typeof document !== 'undefined') {
  document.addEventListener('layers:changed', () => { if (_compareOn && _mapB) _mirrorLayersToMapB(); });
}

export function setBasemap(key) {
  if (!map || !BASEMAPS[key]) return;
  _currentBasemap = key;
  // #map 容器背景随底图（3D 高 pitch/宽 FOV 视口上沿露容器背景；暗底图配白底=刺眼白条）。
  // 3D 暗色态(_dark3DOn)强制深色背景；否则与底图同色。
  map.getContainer().style.background = _dark3DOn ? _BASEMAP_BG[DM_BASEMAP_KEY] : (_BASEMAP_BG[key] || '#ffffff');
  map.setStyle(BASEMAPS[key], {
    transformStyle: (prev, next) => {
      const carrySources = {};
      for (const [id, spec] of Object.entries(prev?.sources || {})) {
        if (id.startsWith('lyr-') || id.startsWith('emotion-') || id.startsWith('dm-')) carrySources[id] = spec;
      }
      // 携带 dm 层 + 数据层（prev 顺序：dm 在数据前 → next: 底图 < dm < 数据），visibility 沿用（3D 态切底图不闪）
      const carryLayers = (prev?.layers || []).filter((l) => l.id.startsWith('lyr-') || l.id.startsWith('emotion-') || l.id.startsWith('dm-'));
      return { ...next, sources: { ...(next.sources || {}), ...carrySources }, layers: [...(next.layers || []), ...carryLayers] };
    },
  });
}

/** 预载 dark-matter 真实矢量图层（fetch style JSON → addSource/addLayer，dm- 前缀避冲突；插在首个数据层前）。
 *  各 addLayer 包 try/catch（跳过依赖 sprite 的符号层等）；visibility 初值 none（2D 不显）。style.load 调一次。 */
async function _loadDarkMatter() {
  if (_dmLoaded || !map) return;
  try {
    const r = await fetch(BASEMAPS[DM_BASEMAP_KEY]);
    if (!r.ok) return;
    const style = await r.json();
    for (const [sid, spec] of Object.entries(style.sources || {})) {
      const id = 'dm-' + sid;
      if (!map.getSource(id)) { try { map.addSource(id, spec); } catch (e) { /* source 冲突跳过 */ } }
    }
    const firstData = (map.getStyle().layers || []).find((l) => l.id.startsWith('lyr-') || l.id.startsWith('emotion-'));
    const beforeId = firstData ? firstData.id : undefined;
    for (const layer of style.layers || []) {
      const id = 'dm-' + layer.id;
      if (map.getLayer(id)) continue;
      const def = { ...layer, id, layout: { ...(layer.layout || {}), visibility: 'none' } };
      if (layer.source) def.source = 'dm-' + layer.source;
      try { map.addLayer(def, beforeId); _dmLayerIds.push(id); } catch (e) { /* 跳过依赖 sprite 的层 */ }
    }
    _dmLoaded = true;
    if (_dark3DOn) _applyDark3D(true);   // 预载完成时若已在 3D 态，立即显
  } catch (e) { console.warn('[map] dark-matter 预载失败', e); }
}

/** pitch 全局监听：pitch>1（任何 3D 触发）→ 显 dm 层 + #map 暗背景；pitch≈0 → 隐 + 还原。仅状态翻转时操作。 */
function _onPitch() {
  if (!map) return;
  const is3d = map.getPitch() > 1;
  if (is3d === _dark3DOn) return;
  _dark3DOn = is3d;
  _applyDark3D(is3d);
}
function _applyDark3D(on) {
  if (!map) return;
  if (_dmLoaded) for (const id of _dmLayerIds) if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none');
  map.getContainer().style.background = on ? _BASEMAP_BG[DM_BASEMAP_KEY] : (_BASEMAP_BG[_currentBasemap] || '#ffffff');
}

const PITCH_3D = 60;   // 3D 俯角（与 map-controls.js PITCH_3D 统一）
const VIEW_EASE_MS = 650;   // 视角切换动画时长（顺滑）

/** 3D 网格视角：on → pitch 倾斜；off → pitch 复原。setViewMode / generateGrid / toggleGridViewMode 共用。
 *  setStyle 不重置 camera（maplibre 保证），故直接 easeTo pitch。底图暗色由 pitch 事件全局驱动
 *  （_onPitch → DARK_OVERLAY 显隐），不在此 setStyle 换底图——任何 pitch>1 的视角切换都会触发暗色遮罩，
 *  且无瓦片重载卡顿。 */
export function setView3D(on) {
  if (!map) return;
  map.easeTo({ pitch: on ? PITCH_3D : 0, bearing: 0, duration: VIEW_EASE_MS });
}

/** grid 层数据签名：同源 2D/3D（同 analysis/level/source/cellSize/polarity/polygonLayer）共享 → 配对，免重复生成、免切换累积。 */
function gridSig(p) {
  const u = p && p._ui;
  if (!u) return '';
  return [u.analysis, u.level, u.source, u.cellSize, u.polarity, u.polygonLayer].join('|');
}
// sig → 最近切换的视角 mode（toggleGridViewMode/setViewMode 记；sidebar 配对去重选代表用，
// 避免都隐藏/切回原 mode 时"取最后"选错代表、视角按钮显错 mode）
const _lastGridMode = new Map();
/** 取该 grid sig 最近切换的视角 mode（无记录返回 undefined）。sidebar renderLayerList 选配对代表用。 */
export function getGridViewMode(sig) { return _lastGridMode.get(sig); }

/** grid 层布局级显隐（不拆源/层）—— 2D/3D 切换用，避免每次 renderLayer 全重建(removeSource+addSource+addLayer)
 *  致的卡顿 + 首帧数据表达式回退（颜色=首色阶/高度=0 再吸附）= 颜色极性闪烁 + 柱高跳动。
 *  返回 false 表示源不在地图（层未渲染过），调用方须走 renderLayer 建。 */
function _gridMapSetVis(layer, visible) {
  if (!map || !layer) return false;
  if (!map.getSource(lyrSrc(layer.id))) return false;   // 源不在地图 → 需 renderLayer 建
  const vis = visible ? 'visible' : 'none';
  for (const sub of [lyrLid(layer.id), lyrExtruLid(layer.id), lyrLineLid(layer.id), lyrHitLid(layer.id)]) {
    if (map.getLayer(sub)) { try { map.setLayoutProperty(sub, 'visibility', vis); } catch (_) {} }
  }
  return true;
}

/** 2D/3D 视图切换：遍历可见 grid 层——mode===target 保持；否则隐藏并按签名找配对 target 层
 *  （无则用同 fc 生成独立层，渲染管线独立：3D→fill-extrusion 柱 / 2D→fill 色块）。
 *  已在地图的配对层用布局显隐切换（免重建闪烁）；仅首次创建走 renderLayer。末尾 setView3D 同步 pitch + 底图。 */
export function setViewMode(target) {
  if (!map) return;
  const grids = getLayers().filter((l) => l.kind === 'polygon' && l.paint && l.paint._ui && l.paint._ui.tool === 'grid');
  for (const l of grids.filter((g) => g.visible)) {
    if (l.paint._ui.mode === target) continue;              // 已是目标模式，保持
    setLayerVisible(l.id, false);
    if (!_gridMapSetVis(l, false)) renderLayer(l);          // 隐藏当前层（已在地图→布局隐，免重建；否则拆）
    const sig = gridSig(l.paint);
    let pair = grids.find((g) => g !== l && g.paint._ui.mode === target && gridSig(g.paint) === sig);
    if (!pair) {                                            // 无配对 → 用同 fc 生成独立 target 层（首次：renderLayer 建源+层）
      const tag = target === '3d' ? '3D' : '2D';
      pair = addLayer({ name: (l.name || '网格').replace(/·\s*[23]D\b/, `· ${tag}`),
                        kind: 'polygon', fc: l.fc,
                        paint: { ...l.paint, _ui: { ...l.paint._ui, mode: target } } });
      pair.srcName = l.srcName;
      setLayerVisible(pair.id, true);
      renderLayer(pair);
    } else {                                                // 有配对 → 显示（已在地图→布局显免重建；否则 renderLayer 建）
      setLayerVisible(pair.id, true);
      if (!_gridMapSetVis(pair, true)) renderLayer(pair);
    }
    reorderLayers(pair.id, l.id);                           // target pair 接替原层 l 顺序位置（保槽位稳定，避免拖拽后切视角跳序）
  }
  restackZ();   // 循环内 reorderLayers(pair,l) 发生在各 pair renderLayer 之后 → reorder 后 map z-order stale，末尾强制重对齐（修切视角后 z 漂移）
  setView3D(target === '3d');
  for (const g of getLayers()) if (g.visible && g.paint && g.paint._ui && g.paint._ui.tool === 'grid') _lastGridMode.set(gridSig(g.paint), g.paint._ui.mode);
  document.dispatchEvent(new CustomEvent('layers:changed'));
}

/** 切指定 grid 层的 2D/3D 视角（图层栏视角按钮用；针对该层 sig，不论该层是否可见）。
 *  隐藏该 sig 当前 mode 层 + 显示/创建 target mode 配对；配对可见性=原层可见性（原隐藏则切 mode 后仍隐藏）。
 *  与 setViewMode 区别：只切该 sig 不波及其他 grid；不依赖该层 visible（修眼睛关闭后视角按钮失效）。 */
export function toggleGridViewMode(layerId) {
  if (!map) return;
  const l = getLayers().find((g) => g.id === layerId);
  if (!l || !l.paint || !l.paint._ui || l.paint._ui.tool !== 'grid') return;
  const target = l.paint._ui.mode === '3d' ? '2d' : '3d';
  const sig = gridSig(l.paint);
  const wasVisible = l.visible;
  const grids = getLayers().filter((g) => g.kind === 'polygon' && g.paint && g.paint._ui && g.paint._ui.tool === 'grid');
  for (const g of grids) if (gridSig(g.paint) === sig) { setLayerVisible(g.id, false); if (!_gridMapSetVis(g, false)) renderLayer(g); }   // 布局隐（已在地图免重建）；否则拆。防 2D/3D 同显混乱
  let pair = grids.find((g) => g.paint._ui.mode === target && gridSig(g.paint) === sig);
  if (!pair) {
    const tag = target === '3d' ? '3D' : '2D';
    pair = addLayer({ name: (l.name || '网格').replace(/·\s*[23]D\b/, `· ${tag}`),
                      kind: 'polygon', fc: l.fc,
                      paint: { ...l.paint, _ui: { ...l.paint._ui, mode: target } } });
    pair.srcName = l.srcName;
  }
  if (wasVisible) {
    setLayerVisible(pair.id, true);   // 原可见 → 配对可见；原隐藏 → 配对仍隐藏（只切 mode）
    for (const hid of enforceMutualExclusion(pair.id)) { const hl = getLayers().find((x) => x.id === hid); if (hl) renderLayer(hl); }   // 边界防护：切视角后维持互斥
  }
  _lastGridMode.set(sig, target);                   // 记该 sig 当前 mode（sidebar 配对代表选择用）
  reorderLayers(pair.id, l.id);                     // target pair 接替原层 l 顺序位置（每次切都 reorder 保槽位稳定，避免拖拽后切视角跳序）
  if (pair.visible) { if (!_gridMapSetVis(pair, true)) renderLayer(pair); }   // 已在地图→布局显免重建；否则 renderLayer 建
  setView3D(getLayers().some((g) => g.visible && g.paint && g.paint._ui && g.paint._ui.mode === '3d'));
  document.dispatchEvent(new CustomEvent('layers:changed'));
}

// 视图按钮（map-controls.js btnView）经事件解耦触发 setViewMode，避免 map ↔ map-controls 循环依赖
if (typeof document !== 'undefined') {
  document.addEventListener('grid:viewmode', (e) => setViewMode(e.detail));
}

export function setClickHandler(fn) { _onPointClick = fn; }

// ── Layer rendering ────────────────────────────────────────────────────────
const lyrSrc = (id) => `lyr-${id}`;
const lyrLid = (id) => `lyr-${id}`;
const lyrLineLid = (id) => `lyr-${id}-line`;
const lyrHitLid = (id) => `lyr-${id}-hit`;
const lyrExtruLid = (id) => `lyr-${id}-extru`;   // grid 3D fill-extrusion sub-layer

/** (Re)render one registry layer. Hidden layers are fully removed (fill + outline + hit). */
export function renderLayer(layer) {
  if (!map) return;
  if (layer.kind === 'group') return;   // group container is not rendered on the map
  const sid = lyrSrc(layer.id);
  const lid = lyrLid(layer.id);
  const lineLid = lyrLineLid(layer.id);
  const hitLid = lyrHitLid(layer.id);
  const extruLid = lyrExtruLid(layer.id);
  for (const l of [hitLid, extruLid, lineLid, lid]) if (map.getLayer(l)) map.removeLayer(l);
  if (map.getSource(sid)) map.removeSource(sid);
  if (!layer.visible || !layer.fc.features.length) {
    if (layer._deckOverlay) layer._deckOverlay.setProps({ layers: [] });   // 隐藏 hotpoint（deck.gl）
    // hiding a point layer → its selection halo must go too
    if (!layer.visible && layer.kind === 'point') clearSelectionHalo(layer.id);
    return;
  }

  // 预处理：L1 confidence 层在 addSource 前把 hotness 写入 properties ——
  // MapLibre source 持有 addSource 时的快照，enrich 在 addSource 之后则 step 表达式
  // ['get','hotness'] 读到 undefined，Chrome 下图层不渲染（regression 根因）。
  if (layer.kind === 'point' && layer.colorMode === 'confidence') {
    const feats = layer.fc.features;
    for (const f of feats) {
      if (!f.properties) f.properties = {};
      if (f.properties.hotness == null) f.properties.hotness = computeHotness(f);
    }
    layer.paint = layer.paint || {};
    layer.paint.hotnessBuckets = hotnessBuckets(feats);
  }
  map.addSource(sid, { type: 'geojson', data: layer.fc });
  if (layer.kind === 'point') {
    addPointPaint(layer, sid, lid);
    bindPointInteractions(layer, lid);
  } else if (layer.kind === 'polygon') {
    addPolygonPaint(layer, sid, lid, lineLid, hitLid);
    const _ui = layer.paint && layer.paint._ui;
    const _tool = _ui && _ui.tool;
    if (_tool === 'grid' || _tool === 'terrain') {
      // 工具层（聚合单元）：悬停 → tip-popup 统一浮动卡（自适应方位），不走 range/terrain dark tooltip
      bindTipPopup(layer, _ui.mode === '3d' ? extruLid : lid);   // 3D=fill-extrusion 柱/环；2D=fill 格
    } else {
      bindRangeInteractions(layer, hitLid, lineLid);
    }
  } else if (layer.kind === 'line') {
    addLinePaint(layer, sid, lid, hitLid);
    bindRangeInteractions(layer, hitLid, lid);
  } else if (layer.kind === 'heatmap') {
    addHeatmapPaint(layer, sid, lid);   // density overlay — no hit layer, no click
  }
  restackZ();   // keep z-order tied to list order (survives toggles)
}

/** Lightweight z-order fix using moveLayer (no re-render). Moves all lyr-* layers
 *  to match list order: list-top = map-top. Called after every renderLayer so
 *  toggling visibility doesn't scramble the stacking. */
export function restackZ() {
  if (!map) return;
  const layers = getLayers();
  for (let i = layers.length - 1; i >= 0; i--) {
    const l = layers[i];
    if (l.kind === 'group') continue;
    const ids = [lyrLid(l.id), lyrLineLid(l.id)];
    if (map.getLayer(lyrExtruLid(l.id))) ids.push(lyrExtruLid(l.id));   // grid 3D 在 line 上、hit 下
    ids.push(lyrHitLid(l.id));
    for (const id of ids) {
      if (map.getLayer(id)) map.moveLayer(id);   // move to top (no beforeId)
    }
  }
}

export function removeLayerFromMap(id) {
  if (!map) return;
  const _layer = getLayers().find((l) => l.id === id);
  if (_layer && _layer._deckOverlay) { map.removeControl(_layer._deckOverlay); _layer._deckOverlay = null; }
  const sid = lyrSrc(id), lid = lyrLid(id), lineLid = lyrLineLid(id), extruLid = lyrExtruLid(id), hitLid = lyrHitLid(id);
  for (const l of [hitLid, extruLid, lineLid, lid]) if (map.getLayer(l)) map.removeLayer(l);
  if (map.getSource(sid)) map.removeSource(sid);
  _boundPoint.delete(id); _boundRange.delete(id);
  clearSelectionHalo();   // a layer going away → selection halo can't stay (resets _selectedLayerId)
  removeHoverRing();
}

/** Remove the selection halo. Pass `id` to clear only if it matches the selected layer
 *  (used when hiding a specific point layer). No arg = clear unconditionally. */
export function clearSelectionHalo(id) {
  if (id != null && _selectedLayerId != null && _selectedLayerId !== id) return;
  _selectedLayerId = null;
  if (!map) return;
  const LAYER = 'emotion-selected-halo', SRC = 'emotion-selected';
  if (map.getLayer(LAYER)) map.removeLayer(LAYER);
  if (map.getSource(SRC)) map.removeSource(SRC);
}

export function applyAllLayers() { for (const layer of getLayers()) renderLayer(layer); }

/** Re-stack so list order = map z-order (list top = map top). Render in reverse
 *  list order → last rendered (list[0]) ends on top. Called after drag-reorder. */
export function reorderAllZ() {
  const layers = getLayers();
  for (let i = layers.length - 1; i >= 0; i--) renderLayer(layers[i]);
}

// ── Paint per kind ────────────────────────────────────────────────────────
function addPointPaint(layer, sid, lid) {
  const count = layer.fc.features.length;
  const p = layer.paint || {};
  // px override (settings slider) else L2 情绪点 3-6px zoom 自适应 / 其他 density-adaptive
  const _isL2 = layer.colorMode === 'l2-positive' || layer.colorMode === 'l2-negative' || layer.colorMode === 'l2-neutral';
  const _l2Radius = ['interpolate', ['linear'], ['zoom'], 8, 3, 14, 6];
  const radius = (p.radius != null) ? p.radius : (_isL2 ? _l2Radius : densityRadiusExpr(count));
  let colorExpr, strokeW, opacity;
  if (layer.colorMode === 'confidence') {
    // L1 热度值 = 情绪强度 × 置信度，3 段动态分位。hotness/buckets 已在 renderLayer
    // addSource 前预处理（写入 properties + paint.hotnessBuckets），此处直接落色。
    const buckets = p.hotnessBuckets || [0.33, 0.66];
    colorExpr = ['step', ['get', 'hotness'], HOTNESS_RAMP[0],
      buckets[0], HOTNESS_RAMP[1], buckets[1], HOTNESS_RAMP[2]];
    strokeW = 0; opacity = p.opacity ?? 0.75;
  } else if (layer.colorMode === 'l2-positive') {
    colorExpr = ['match', ['get', 'polarity'], 'Very Positive', L2_POSITIVE['Very Positive'], 'Positive', L2_POSITIVE['Positive'], L2_POSITIVE['Positive']];
    strokeW = 0; opacity = p.opacity ?? 0.18;
  } else if (layer.colorMode === 'l2-negative') {
    colorExpr = ['match', ['get', 'polarity'], 'Very Negative', L2_NEGATIVE['Very Negative'], 'Negative', L2_NEGATIVE['Negative'], L2_NEGATIVE['Negative']];
    strokeW = 0; opacity = p.opacity ?? 0.18;
  } else if (layer.colorMode === 'l2-neutral') {
    colorExpr = L2_NEUTRAL_COLOR;
    strokeW = 0; opacity = p.opacity ?? 0.18;
  } else if (layer.colorMode === 'needsAnalysis' || layer.needsAnalysis) {
    colorExpr = p.color || '#4a4a4a';   // L0 默认深灰；paint.color（预设色板）可覆盖
    strokeW = 0; opacity = p.opacity ?? 0.80;
  } else {
    // legacy single polarity layer (frozen) — keep 5-color
    const colors = emotionColors();
    colorExpr = ['match', ['get', 'polarity'],
      'Very Positive', colors['Very Positive'], 'Positive', colors['Positive'],
      'Neutral', colors['Neutral'], 'Negative', colors['Negative'],
      'Very Negative', colors['Very Negative'], colors['Neutral']];
    strokeW = 1; opacity = p.opacity ?? 0.9;
  }
  map.addLayer({
    id: lid, type: 'circle', source: sid,
    paint: {
      'circle-radius': radius,
      'circle-color': colorExpr,
      'circle-stroke-color': token('--geojson-feature-point-stroke') || '#ffffff',
      'circle-stroke-width': strokeW,
      'circle-opacity': opacity,
      'circle-stroke-opacity': strokeW ? 0.9 : 0,
    },
  });
}

/** Grid 极性色带 → MapLibre fill-color 表达式。
 *  p.gridField='_grid_norm'|'_grid_pos'|'_grid_neg'；p.gridStops=[[0,c0],...,[1,cN]]（归一化 0~1，无透明）。
 *  返回 interpolate(linear, get(field), ...)；无有效 stops → null（落回单色）。 */
function _gridColorExpr(p) {
  if (!p.gridField || !Array.isArray(p.gridStops) || !p.gridStops.length) return null;
  const stops = [];
  for (const [d, c] of p.gridStops) stops.push(d, c);
  return ['interpolate', ['linear'], ['get', p.gridField], ...stops];
}

/** 就地替换 grid 层 source data（不动 layer/paint/bindings）。
 *  时间轴动画专用：每帧 setData 改 _grid_h/_grid_norm 等属性 → fill-extrusion 高度/颜色重算。
 *  承重：不 removeSource/re-renderLayer（避免重绑 tip/选中、保 paint-in-place）；layer.id 源层名不变。 */
export function updateGridSourceData(layer, fc) {
  if (!map || !layer) return false;
  const sid = lyrSrc(layer.id);
  const src = map.getSource(sid);
  if (!src) return false;
  src.setData(fc);
  return true;
}

function addPolygonPaint(layer, sid, lid, lineLid, hitLid) {
  const p = layer.paint || {};
  const tool = p._ui && p._ui.tool;
  const isTool = tool === 'grid' || tool === 'terrain' || tool === 'density' || tool === 'zonal';   // grid/terrain 共用极性色带+fill-extrusion；density 仅 2D；zonal（P1）行政区聚合 choropleth 2D 着色（无 extrusion）
  const isTool3d = isTool && p._ui.mode === '3d';
  const color = p.color || NAVY;
  const fillExpr = isTool ? _gridColorExpr(p) : null;
  // 高度字段：grid=_grid_h（preprocessGrid 点数幂次 γ=1.3），terrain=_level（后端 KDE 等值面级）。maxHeight 绝对米（默认 1000）。
  const heightField = (p._ui && p._ui.heightField) || '_grid_h';
  const maxHeight = (p._ui && p._ui.maxHeight) || 1000;
  // 极性深读 paint 就地切换：藏零计数格（仅 L2 综合 grid 切极性视图时设；综合/范围层无此字段 → 不过滤）。
  // MapLibre addLayer 的 filter 须为合法数组，不接受 undefined → 仅在 polFilter 非空时条件展开。
  const polFilter = p._polarityFilter || null;
  const filterSpec = polFilter ? { filter: polFilter } : {};

  if (p.fillOn && !isTool3d) {   // 仅 2D 加 fill 色块；3D 跳过（柱体/环 fill-extrusion 自含顶/侧/底面，再加地面色块会"2D 色块+3D 柱体"同显混乱）
    map.addLayer({ id: lid, type: 'fill', source: sid, ...filterSpec,
      paint: { 'fill-color': fillExpr || color, 'fill-opacity': p.fillOpacity ?? (isTool ? (p._ui?.extrusionOpacity ?? 1) : 0.3) } });   // 工具层不透明度统一读 _ui.extrusionOpacity（2D/3D 同控件，默认 1）
  }

  // 工具层 3D：fill-extrusion（实心 + 高度字段×maxHeight 张力 + 颜色同 2D 极性/密度色带）
  // 注：曾读 p.extrusionScale（错位，实际在 _ui）→ 恒 1× 滑块失效；改 maxHeight 绝对值并读 _ui.maxHeight。
  if (isTool3d) {
    map.addLayer({
      id: lyrExtruLid(layer.id), type: 'fill-extrusion', source: sid, ...filterSpec,
      paint: {
        'fill-extrusion-color': fillExpr || color,
        'fill-extrusion-height': ['interpolate', ['linear'], ['get', heightField], 0, 0, 1, maxHeight],
        'fill-extrusion-base': 0,
        'fill-extrusion-opacity': p._ui.extrusionOpacity ?? 1,   // 3D 透明度可调（默认 1 实心）
      },
    });
  }

  // visible outline；3D 去线框（只 2D 加浅灰细线，区分 buffer 实线 / Range 点划线）
  if (!isTool3d) {
    const _isDensity = tool === 'density';
    const lineColor = isTool ? '#666' : color;
    // density 2D 去格线（密网格灰线成莫尔噪点，热力图本不需格线）；grid/terrain 保留 0.5px 浅灰
    const linePaint = { 'line-color': lineColor,
      'line-width': p.lineWidth ?? (isTool ? (_isDensity ? 0 : 0.5) : 1),
      'line-opacity': p.lineOpacity ?? (isTool ? (_isDensity ? 0 : 0.45) : 0.9) };
    const lineLayout = {};
    if (p.lineStyle === 'dashed') {
      linePaint['line-dasharray'] = [2, 1.5];                    // 缓冲面域：短虚线
    } else if (p.lineStyle === 'dashdot') {
      linePaint['line-dasharray'] = [6, 3, 1, 3];                // Range：点划线（线段+点+线段）
      lineLayout['line-cap'] = 'round';                          // round cap 让 1-unit 短段呈圆点（line-cap 属 layout）
    }
    map.addLayer({ id: lineLid, type: 'line', source: sid, ...filterSpec, layout: lineLayout, paint: linePaint });
  }
  // transparent wide hit layer → easy hover/click without thickening the visible outline
  addHitLayer(hitLid, sid, polFilter);
}

function addLinePaint(layer, sid, lid, hitLid) {
  const p = layer.paint || {};
  map.addLayer({ id: lid, type: 'line', source: sid,
    paint: { 'line-color': p.color || NAVY, 'line-width': p.lineWidth ?? 1, 'line-opacity': 0.9 } });
  addHitLayer(hitLid, sid);
}

function addHitLayer(hitLid, sid, filter) {
  const spec = { id: hitLid, type: 'line', source: sid, layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: { 'line-color': '#000', 'line-width': HIT_WIDTH, 'line-opacity': 0 } };
  if (filter) spec.filter = filter;   // 仅极性视图带 filter（MapLibre 拒绝 undefined）
  map.addLayer(spec);
}

/** Heatmap (Kepler-aligned): native MapLibre `type:'heatmap'` = Gaussian KDE (same algo as
 *  deck.gl HeatmapLayer under Kepler). Color maps DENSITY (not polarity); polarity enters via
 *  weight. Full parameter set: Color/Opacity/Radius/Weight/Intensity/Curve/ZoomRange/Unit.
 *
 *  Radius 单位语义（v2）：
 *  - 'm'（默认，GIS 核密度语义）: radius=真实米数，按 zoom 换算成 px，缩放时地理覆盖稳定。
 *    公式 px(z)=meters/mpp(z,lat)，mpp(z,lat)≈156543.03*cos(lat)/2^z。
 *  - 'px'（高级）: 固定屏幕像素，缩放时屏幕半径不变但地理面积随 zoom 漂移。
 *  L2 类型/强度筛选（typesFilter/intensityMin）在 heatmap-tool.js 生成时已过滤 fc，
 *  这里只负责渲染。 */
function addHeatmapPaint(layer, sid, lid) {
  const p = layer.paint || {};
  const unit = p.unit || 'm';                       // 'm' default, 'px' advanced
  const radius = p.radius ?? (unit === 'm' ? 300 : 45);
  const opacity = p.opacity ?? 0.7;
  const intensity = p.intensity ?? 1;
  const weightField = p.weightField || 'emotion_intensity';
  const weightCurve = p.weightCurve || 'linear';
  const rampKey = p.rampKey || 'rainbow';
  const ramp = p.rampStops || (HEATMAP_RAMPS[rampKey] && HEATMAP_RAMPS[rampKey].stops) || HEATMAP_NEGATIVE_STOPS;
  const colorStops = ramp.flat();
  const weightExpr = buildWeightExpression(weightField, weightCurve);

  const paint = {
    'heatmap-radius': radius,
    'heatmap-opacity': opacity,
    'heatmap-intensity': intensity,
    'heatmap-weight': weightExpr,
    'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'], ...colorStops],
  };

  if (unit === 'm') {
    // 地理米 → 各 zoom 下应渲染的 px。宜昌纬度 30.7°N 常量。
    const latRad = 30.7 * Math.PI / 180;
    const cosLat = Math.cos(latRad);
    const mpp = (z) => 156543.03 * cosLat / Math.pow(2, z);
    const pxAt = (z) => radius / mpp(z);
    paint['heatmap-radius'] = ['interpolate', ['linear'], ['zoom'],
      8, pxAt(8),
      10, pxAt(10),
      12, pxAt(12),
      14, pxAt(14),
      16, pxAt(16),
      18, pxAt(18),
      20, pxAt(20),
    ];
  } else if (p.geoRadius) {
    // 向后兼容：旧 px + geoRadius 标志（已弃用，保留以防旧图层）
    paint['heatmap-radius'] = ['interpolate', ['linear'], ['zoom'],
      0, Math.max(2, radius * 0.02),
      8, Math.max(4, radius * 0.3),
      12, Math.max(8, radius * 0.6),
      16, radius,
      20, radius * 1.5,
    ];
  }

  const opts = { id: lid, type: 'heatmap', source: sid, paint };
  if (p.minzoom != null) opts.minzoom = p.minzoom;
  if (p.maxzoom != null && p.maxzoom < 22) opts.maxzoom = p.maxzoom;

  map.addLayer(opts);
}

/* global deck */  // deck.gl standalone UMD（index.html CDN 引入）
/** 热点图（deck.gl）：ScreenGridLayer 屏幕方格聚合 + MapboxOverlay 叠 MapLibre。
 *  bloom 先靠 CSS filter（map canvas）近似；效果不足再引 @luma.gl/postprocessing。 */
function addHotpointLayer(layer, sid, lid) {
  if (typeof deck === 'undefined' || !deck.ScreenGridLayer || !deck.MapboxOverlay) {
    console.error('[Hotpoint] deck.gl 未加载（ScreenGridLayer/MapboxOverlay 缺失），检查 index.html CDN');
    return;
  }
  const p = layer.paint || {};
  const weightField = p.weightField || 'emotion_intensity';
  const rampKey = p.rampKey || 'rainbow';
  const ramp = p.rampStops || (HEATMAP_RAMPS[rampKey] && HEATMAP_RAMPS[rampKey].stops) || HEATMAP_NEGATIVE_STOPS;
  const opacity = p.opacity ?? 0.8;
  const cellSize = Math.max(4, Math.min(40, Math.round((p.radius ?? 100) / 6)));  // radius(m)→cellSize(px) 近似
  // ramp stops 是 [t, '#hex'|'rgba(...)'] 格式 → deck colorRange 需 [[r,g,b],...]（6 色）
  const _toRgb = (c) => {
    if (Array.isArray(c)) return c;
    if (typeof c !== 'string') return [255, 255, 255];
    const m = c.match(/rgba?\(([^)]+)\)/i);
    if (m) { const p = m[1].split(',').map(Number); return [p[0] || 0, p[1] || 0, p[2] || 0]; }
    let h = c.replace('#', '');
    if (h.length === 3) h = h.split('').map((x) => x + x).join('');
    const n = parseInt(h, 16);
    return isNaN(n) ? [255, 255, 255] : [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  };
  const _cols = ramp.map((x) => _toRgb(x[1]));
  const colorRange = [];
  for (let i = 0; i < 6; i++) colorRange.push(_cols[i] || _cols[_cols.length - 1] || [255, 255, 255]);
  const sgl = new deck.ScreenGridLayer({
    id: lid,
    data: layer.fc.features,
    getPosition: (f) => f.geometry.coordinates,
    getWeight: (f) => Number((f.properties || {})[weightField] ?? 0.5),
    cellSize, colorRange, opacity,
    pickable: false,
  });
  if (layer._deckOverlay) {
    layer._deckOverlay.setProps({ layers: [sgl] });
  } else {
    layer._deckOverlay = new deck.MapboxOverlay({ layers: [sgl] });
    map.addControl(layer._deckOverlay);
  }
}

/* global deck */
/** 标准网格（square）：deck.gl 渲染（业界成熟，kepler 同款光影/聚合/分位色）。
 *  2D：GridLayer extruded:false（吃原始点自动聚合色块）。
 *  3D：后端预聚合方格 + ColumnLayer（格中心+高度分位+极色+material 光影）。
 *  GridLayer extruded（方柱 GridCellLayer）在此环境 deck.gl@9.1.0 不渲染，故 3D 改用 ColumnLayer（圆柱，已验证渲染）。 */
// ── deck.gl grid 渲染已弃用（回 MapLibre fill-extrusion：addPolygonPaint grid 分支）──
// grid 工具 square/zonal 都走 addPolygonPaint（fill + fill-extrusion + _gridColorExpr 极性色带）。
// 放弃原因：deck.gl GridLayer extruded（方柱）在 MapLibre+MapboxOverlay 不渲染；ColumnLayer 效果不及 kepler 理想 → 用户决定回自创 fill-extrusion（去透明度+去线框）。
// addHotpointLayer（热点图）仍用 deck.gl ScreenGridLayer（搁置，独立功能）。

/** Build a heatmap-weight expression from field + curve mode.
 *  Modes: linear|exponential × normal|inverse. "inverse" = lower value → higher weight. */
function buildWeightExpression(field, curve) {
  if (field === 'uniform') return 1;
  const get = ['coalesce', ['to-number', ['get', field]], 0.3];
  const inverse = curve.endsWith('-inverse');
  const mode = inverse ? curve.replace('-inverse', '') : curve;

  if (mode === 'exponential') {
    // exponential via pre-computed stops: weight = e^(3*val) mapped over 5 stops
    const stops = inverse
      ? [0, 1, 0.25, 0.7, 0.5, 0.3, 0.75, 0.08, 1, 0.01]
      : [0, 0.01, 0.25, 0.08, 0.5, 0.3, 0.75, 0.7, 1, 1];
    return ['interpolate', ['linear'], get, ...stops];
  }
  // linear: direct mapping or inverse
  if (inverse) {
    return ['interpolate', ['linear'], get,
      0, 1, 0.25, 0.8, 0.5, 0.5, 0.75, 0.2, 1, 0];
  }
  return ['interpolate', ['linear'], get,
    0, 0, 0.25, 0.2, 0.5, 0.5, 0.75, 0.8, 1, 1];
}

// ── Interactions ──────────────────────────────────────────────────────────
function bindPointInteractions(layer, lid) {
  if (_boundPoint.has(layer.id)) return;
  _boundPoint.add(layer.id);
  bindTipPopup(layer, lid, { kind: 'point', colorMode: layer.colorMode });   // 悬停→tip-popup（区域 / 极性+分数 / domain×element）
  const mode = layer.colorMode;
  map.on('mouseenter', lid, (e) => {
    map.getCanvas().classList.add('is-pointer');
  });
  map.on('mouseleave', lid, () => { map.getCanvas().classList.remove('is-pointer'); removeHoverRing(); });
  map.on('click', lid, (e) => {
    const f = e.features && e.features[0]; if (!f) return;
    _selectedLayerId = layer.id;       // remember which layer the halo belongs to
    showSelectionHalo(f);
    if (_onPointClick) _onPointClick(f, emotionColors(), mode);
  });
}

/** Range hover bound to the transparent hit layer; hover widens the visible outline + tooltip.
 *  Click-to-open moved to popup.js central handler (classifyMapClick) so open/collapse share
 *  one decision (no open-then-collapse race); hover behaviour preserved unchanged. */
function bindRangeInteractions(layer, hitLid, outlineLid) {
  if (_boundRange.has(layer.id)) return;
  _boundRange.add(layer.id);
  // 默认线宽 1px，hover 加粗 +1px（→2px）。live 读 layer.paint.lineWidth：settings 调线宽后 hover 同步（不依赖闭包旧值，承重⑩结构不变）。
  const baseW = () => (layer.paint && layer.paint.lineWidth) ?? 1;
  const hoverW = () => baseW() + 1;
  map.on('mouseenter', hitLid, (e) => {
    map.getCanvas().classList.add('is-pointer');
    try { map.setPaintProperty(outlineLid, 'line-width', hoverW()); } catch (_) {}
    showRangeTooltip(e.lngLat, layer.name);
  });
  map.on('mousemove', hitLid, (e) => { if (_tooltip) _tooltip.setLngLat(e.lngLat); });
  map.on('mouseleave', hitLid, () => {
    map.getCanvas().classList.remove('is-pointer');
    try { map.setPaintProperty(outlineLid, 'line-width', baseW()); } catch (_) {}
    hideRangeTooltip();
  });
}

function showRangeTooltip(lngLat, name) {
  if (!_tooltip) _tooltip = new maplibregl.Popup({ closeButton: false, closeOnClick: false, className: 'range-tooltip', offset: 12 });
  _tooltip.setHTML(`<div class="rt-name">${name || '范围'}</div>`).setLngLat(lngLat).addTo(map);
}
function hideRangeTooltip() { if (_tooltip) _tooltip.remove(); }

// ── Point halos ───────────────────────────────────────────────────────────
function showSelectionHalo(feature) {
  const SRC = 'emotion-selected', LAYER = 'emotion-selected-halo';
  if (map.getLayer(LAYER)) map.removeLayer(LAYER);
  if (map.getSource(SRC)) map.removeSource(SRC);
  const r = pointRadiusFor(feature);
  map.addSource(SRC, { type: 'geojson', data: { type: 'Feature', geometry: feature.geometry, properties: {} } });
  map.addLayer({
    id: LAYER, type: 'circle', source: SRC,
    paint: {
      'circle-radius': r + 2,              // ring hugging just outside the point
      'circle-color': 'rgba(0,0,0,0)',     // no fill
      'circle-opacity': 0,
      'circle-stroke-color': '#E8E8E8',    // gray-white
      'circle-stroke-width': 3.5,          // thick
      'circle-stroke-opacity': 0.95,
    },
  });
}
function showHoverRing(feature) {
  const SRC = 'emotion-hover', LAYER = 'emotion-hover-ring';
  if (map.getLayer(LAYER)) map.removeLayer(LAYER);
  if (map.getSource(SRC)) map.removeSource(SRC);
  const ringColor = token('--geojson-feature-selection-halo-color') || '#4285F4';
  const r = pointRadiusFor(feature);
  map.addSource(SRC, { type: 'geojson', data: { type: 'Feature', geometry: feature.geometry, properties: {} } });
  map.addLayer({ id: LAYER, type: 'circle', source: SRC,
    paint: { 'circle-radius': r * 1.6, 'circle-color': 'rgba(0,0,0,0)', 'circle-opacity': 0,
      'circle-stroke-color': ringColor, 'circle-stroke-width': 2, 'circle-stroke-opacity': 0.8 } });
}
function removeHoverRing() {
  const SRC = 'emotion-hover', LAYER = 'emotion-hover-ring';
  if (map.getLayer(LAYER)) map.removeLayer(LAYER);
  if (map.getSource(SRC)) map.removeSource(SRC);
}
function pointRadiusFor(feature) {
  const zoom = map ? map.getZoom() : 11;
  let count = 0;
  const s = feature && feature.source;
  if (s) { const id = s.replace('lyr-', ''); const l = getLayers().find((x) => x.id === id);
    if (l) count = l.fc.features.length; }
  if (!count) { for (const l of getLayers()) if (l.kind === 'point' && l.visible) count += l.fc.features.length; }
  return densityRadiusAt(count || 1, zoom);
}

// ── Helpers ───────────────────────────────────────────────────────────────
function visiblePointCount() {
  let n = 0;
  for (const l of getLayers()) if (l.kind === 'point' && l.visible) n += l.fc.features.length;
  return n || 1;
}
function mergedBBox() {
  let b = null;
  for (const layer of getLayers()) {
    if (!layer.visible) continue;
    for (const f of layer.fc.features) {
      const c = findFirstCoord(f.geometry);
      if (!c) continue;
      if (!b) b = [c[0], c[1], c[0], c[1]];
      else { if (c[0] < b[0]) b[0] = c[0]; if (c[1] < b[1]) b[1] = c[1]; if (c[0] > b[2]) b[2] = c[0]; if (c[1] > b[3]) b[3] = c[1]; }
    }
  }
  return b;
}
function findFirstCoord(geom) {
  if (!geom || !geom.coordinates) return null;
  const dive = (a) => Array.isArray(a[0]) ? dive(a[0]) : a;
  try { return dive(geom.coordinates); } catch (e) { return null; }
}

export function fitBoundsTo(bbox, padding = 100, maxZoom = null) {
  if (!map || !bbox) return;
  const opts = { padding };
  if (maxZoom != null) opts.maxZoom = maxZoom;   // 关键词点击等封顶防过近（停车难 CBD 密集格 bbox 太紧致视野过低）
  try { map.fitBounds([[bbox[0], bbox[1]], [bbox[2], bbox[3]]], opts); } catch (e) {}
}

/** 缩放至本图层：算该层 fc 的 bbox → fitBounds（双击图层行触发）。group 容器无几何，调用方自行过滤。
 *  递归遍历全部坐标（Point/Line/Polygon 通用，Polygon 取所有顶点而非仅首点）。 */
export function fitToLayer(layer, padding = 80) {
  if (!map || !layer || !layer.fc) return;
  let b = null;
  const add = (xy) => {
    if (!xy || typeof xy[0] !== 'number' || typeof xy[1] !== 'number') return;
    if (!b) b = [xy[0], xy[1], xy[0], xy[1]];
    else { if (xy[0] < b[0]) b[0] = xy[0]; if (xy[1] < b[1]) b[1] = xy[1]; if (xy[0] > b[2]) b[2] = xy[0]; if (xy[1] > b[3]) b[3] = xy[1]; }
  };
  const walk = (a) => { if (Array.isArray(a)) { if (typeof a[0] === 'number') add(a); else for (const x of a) walk(x); } };
  for (const f of layer.fc.features) walk(f.geometry && f.geometry.coordinates);
  if (b) fitBoundsTo(b, padding);
}

// ── 单元深读联动 zoom（Task4 D3 + P0 修 stacking）──
// 进入单元层 = 定位质心 + 略微 zoom（固定 _cellModeZoom 一次，clamp [13,15.5]），**不 fitBounds**；
// **同层切格只 pan、不抬 zoom**（_cellModeZoom 复用，避免越点越低 stacking）；
// 切回图层总览 = 恢复进入前视野（zoom out 抬高）。_preCellView/_cellModeZoom 跨多次点格保留，仅"切回"时清。
let _preCellView = null;
let _cellModeZoom = null;

/** 取 feature 质心（Polygon/MultiPolygon 取外环顶点均值；Point 取坐标）。 */
function _featureCentroid(f) {
  const g = f && f.geometry; if (!g) return null;
  if (g.type === 'Point') return Array.isArray(g.coordinates) ? g.coordinates.slice() : null;
  let coords = [];
  if (g.type === 'Polygon') coords = g.coordinates[0] || [];
  else if (g.type === 'MultiPolygon') for (const p of g.coordinates) coords.push(...(p[0] || []));
  else return null;
  if (!coords.length) return null;
  let mx = 0, my = 0; for (const [x, y] of coords) { mx += x; my += y; }
  return [mx / coords.length, my / coords.length];
}

/** 进入/切换单元：首次进入记快照 + 固定 _cellModeZoom；切格只 pan（zoom 不变）。 */
export function easeToCell(feature) {
  if (!map || !feature) return;
  const c = _featureCentroid(feature); if (!c) return;
  if (!_preCellView) {
    _preCellView = { center: map.getCenter(), zoom: map.getZoom(), pitch: map.getPitch() };
    _cellModeZoom = Math.max(13, Math.min(15.5, map.getZoom() + 1));   // 进入单元层固定一次
  }
  try { map.easeTo({ center: c, zoom: _cellModeZoom, duration: 600 }); } catch (e) {}   // 切格 pan 不抬高
}

/** 切回图层总览：恢复进入单元前的视野（zoom out 抬高）。 */
export function easeBackFromCell() {
  if (!map || !_preCellView) return;
  try { map.easeTo({ center: _preCellView.center, zoom: _preCellView.zoom, pitch: _preCellView.pitch, duration: 600 }); } catch (e) {}
  _preCellView = null; _cellModeZoom = null;
}

// ── 地点 tip：极性深读关键词 hover/click → 对应聚合域·3D 柱体上方投射白色细线 + 胶囊（地点名）──
// panel.js 已把 loc.name 解析成真实坐标（点层 POI → 所在 cell._center，数据为准勿猜坐标）。
// Marker anchor bottom 锚 cell 中心；线高 200+i*25（cap 300）自适应 stagger 避胶囊重叠。cap ≤ 8。
const _locTipMarkers = [];

/** 显示地点 tip：anchors = [{name, lng, lat}]（已解析的真实坐标）。cap ≤ 8；线高 stagger 避重叠。 */
export function showLocTips(anchors) {
  clearLocTips();
  if (!map || !anchors || !anchors.length) return;
  anchors.slice(0, 8).forEach((a, i) => {
    if (!a || a.lng == null || a.lat == null) return;
    const len = Math.min(300, 200 + i * 25);   // 自适应高度：第 i 条线高 200/225/250...，胶囊错层避叠
    const el = document.createElement('div');
    el.className = 'loc-tip';
    el.innerHTML = `<div class="loc-tip-cap">${(a.name || '').replace(/[<>]/g, '')}</div><div class="loc-tip-line" style="height:${len}px"></div>`;
    const m = new maplibregl.Marker({ element: el, anchor: 'bottom' })
      .setLngLat([a.lng, a.lat])
      .addTo(map);
    _locTipMarkers.push(m);
  });
}

/** 清全部地点 tip（关键词 leave / 切极性 / 换层 时）。 */
export function clearLocTips() {
  for (const m of _locTipMarkers) m.remove();
  _locTipMarkers.length = 0;
}
