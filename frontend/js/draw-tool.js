// ═══ draw-tool.js — 多边形/矩形绘制（移植 geojson.io 自实现 handler）═══
// 不引第三方库。geojson.io 用 Deck.gl 渲染 + 自写 handler（app/lib/handlers/polygon.ts,
// rectangle.ts）；这里移植其交互逻辑到 MapLibre：Deck pickMultipleObjects→queryRenderedFeatures，
// map.unproject 同义。Mode 状态机存 state.js（中立枢纽，避免 popup↔draw-tool 环依赖）。
// 结果落 kind:'polygon' 图层（categoryOf='range'），复用 range popup（面积/周长）。
//
// geojson.io 不变式（已移植）：① ring 末位=跟随光标的"橡皮筋"临时点，mousemove 更新，完成时剥除；
// ② 多边形三种完成——点起点顶点 / 双击 / 回车；③ closePolygon 剥临时点+首点闭合；
// ④ 矩形 mousedown→drag 4 角→mouseup，Shift 锁正方形；⑤ e6 坐标精度。
import { addLayer, setMode, getMode, isDrawActive } from './state.js';
import { renderLayer, fitBoundsTo, reorderAllZ } from './map.js';
import { renderLayerList, refreshLegend, showLayerManager } from './sidebar.js';
import { showRangePopup } from './popup.js';
import { fcBBox } from './import.js';
import { toast } from './toast.js';

const MODE = { NONE: 'NONE', DRAW_POLYGON: 'DRAW_POLYGON', DRAW_RECTANGLE: 'DRAW_RECTANGLE' };
const DRAW_SRC = 'draw-src';
const DRAW_FILL = 'draw-fill';
const DRAW_LINE = 'draw-line';
const DRAW_VERTS = 'draw-verts';
const DRAW_COLOR = '#4FC3F7';   // 天蓝（与 buffer 默认同色，白底图上醒目）
const HINT_POLY = '点击添加顶点 — 双击 / 回车 / 点起点完成（Esc 取消）';
const HINT_RECT = '按下并拖拽绘制矩形 — Shift 锁正方形（Esc 取消）';

let _map = null;
let _mode = MODE.NONE;
let _verts = [];          // 多边形：已落顶点 [[lng,lat],...]（WGS84，e6）
let _rectFirst = null;    // 矩形：起点 {x,y}（像素）

// ── e6 坐标精度（geojson.io geometry.ts e6）──
const e6 = (v) => Math.round(v * 1e6) / 1e6;
const ll2coord = (ll) => [e6(ll.lng), e6(ll.lat)];   // {lng,lat} → [lng,lat]
const coord2e6 = (c) => [e6(c[0]), e6(c[1])];

function source() { return _map && _map.getSource(DRAW_SRC); }

// ── 临时层（绘制中）── fill/line/circle 各自按几何类型自动过滤同一 source ──
function addDrawLayers() {
  if (!_map || source()) return;
  _map.addSource(DRAW_SRC, { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
  _map.addLayer({ id: DRAW_FILL, type: 'fill', source: DRAW_SRC,
    paint: { 'fill-color': DRAW_COLOR, 'fill-opacity': 0.12 } });
  _map.addLayer({ id: DRAW_LINE, type: 'line', source: DRAW_SRC,
    paint: { 'line-color': DRAW_COLOR, 'line-width': 2, 'line-opacity': 0.9 } });
  _map.addLayer({ id: DRAW_VERTS, type: 'circle', source: DRAW_SRC,
    paint: {
      'circle-radius': ['case', ['get', 'first'], 6, 4],
      'circle-color': '#ffffff',
      'circle-stroke-color': DRAW_COLOR,
      'circle-stroke-width': 2,
    } });
}

function removeDrawLayers() {
  if (!_map) return;
  [DRAW_VERTS, DRAW_LINE, DRAW_FILL].forEach((id) => { if (_map.getLayer(id)) _map.removeLayer(id); });
  if (_map.getSource(DRAW_SRC)) _map.removeSource(DRAW_SRC);
}

// 多边形临时数据：轮廓线（含光标橡皮筋）+ 进行中填充 + 已落顶点（首点高亮）
function setPolygonTemp(cursorCoord) {
  const src = source(); if (!src) return;
  const feats = [];
  const lineCoords = _verts.slice();
  if (cursorCoord) lineCoords.push(cursorCoord);
  if (lineCoords.length >= 2) feats.push({ type: 'Feature', geometry: { type: 'LineString', coordinates: lineCoords }, properties: {} });
  if (_verts.length >= 2) {
    const ring = cursorCoord ? [..._verts, cursorCoord, _verts[0]] : [..._verts, _verts[0]];
    feats.push({ type: 'Feature', geometry: { type: 'Polygon', coordinates: [ring] }, properties: {} });
  }
  _verts.forEach((v, i) => feats.push({ type: 'Feature', geometry: { type: 'Point', coordinates: v }, properties: { first: i === 0 } }));
  src.setData({ type: 'FeatureCollection', features: feats });
}

// 矩形临时数据：4 角闭合多边形
function setRectangleTemp(cornersCoord) {
  const src = source(); if (!src || !cornersCoord || cornersCoord.length < 4) return;
  const ring = [...cornersCoord, cornersCoord[0]];
  src.setData({ type: 'FeatureCollection', features: [{ type: 'Feature', geometry: { type: 'Polygon', coordinates: [ring] }, properties: {} }] });
}

// ── 辅助 ──
function pixDist(a, b) {   // a,b=[lng,lat] → 屏幕像素距离
  const pa = _map.project(a), pb = _map.project(b);
  return Math.hypot(pa.x - pb.x, pa.y - pb.y);
}

// 点回起点顶点判定（geojson.io polygon.ts:83-116 的 pickMultipleObjects → queryRenderedFeatures）
function clickedFirstVertex(point) {
  if (_verts.length < 3) return false;
  const fs = _map.queryRenderedFeatures(point, { layers: [DRAW_VERTS] });
  return fs.some((f) => f.properties && f.properties.first);
}

// 矩形 4 角（像素）→ [lng,lat]；Shift 锁正方形（geojson.io rectangle.ts:39-55）
function rectCorners(firstPx, curPx, shift) {
  let x = curPx.x, y = curPx.y;
  if (shift) {
    const dx = x - firstPx.x, dy = y - firstPx.y;
    const size = Math.max(Math.abs(dx), Math.abs(dy));
    x = firstPx.x + Math.sign(dx || 1) * size;
    y = firstPx.y + Math.sign(dy || 1) * size;
  }
  const px = [firstPx, { x, y: firstPx.y }, { x, y }, { x: firstPx.x, y }];
  return px.map((p) => coord2e6(_map.unproject(p).toArray()));
}

function rectNonZero(cornersCoord) {
  const px = cornersCoord.map((c) => _map.project(c));
  return Math.abs(px[2].x - px[0].x) >= 3 && Math.abs(px[2].y - px[0].y) >= 3;
}

// ── 完成 / 提交 ──
function finishPolygon() {
  if (_verts.length < 3) { toast.info('多边形至少需要 3 个顶点'); return; }
  const ring = [..._verts, _verts[0]];
  commit({ type: 'Polygon', coordinates: [ring] }, '多边形', _verts.length);
}

function commit(geom, label, n) {
  const modeSnap = _mode;
  const fc = { type: 'FeatureCollection', features: [{ type: 'Feature', geometry: geom, properties: { name: `绘制${label}` } }] };
  const paint = { color: DRAW_COLOR, fillOn: true, fillOpacity: 0.15, lineWidth: 2, lineStyle: 'solid', _ui: { tool: 'draw', mode: modeSnap, shape: label } };
  const L = addLayer({ name: `绘制${label} · ${n}顶点`, kind: 'polygon', fc, paint });
  exitDraw();   // 清临时层 + mode NONE + 按钮 + 光标 + 提示
  renderLayer(L);
  const bb = fcBBox(fc); if (bb) fitBoundsTo(bb);
  renderLayerList(); refreshLegend(); reorderAllZ(); showLayerManager();
  document.dispatchEvent(new CustomEvent('layers:changed'));
  document.dispatchEvent(new CustomEvent('layer:selected', { detail: L.id }));
  showRangePopup(fc.features[0], L);
  toast.success(`已绘制${label}（${n} 顶点）`);
}

function cancelDraw() { exitDraw(); toast.info('已取消绘制'); }

// ── 事件 handler（顶部 mode guard：stopDraw 后的残余事件无效）──
function onClick(e) {
  if (_mode !== MODE.DRAW_POLYGON) return;
  if (clickedFirstVertex(e.point)) { finishPolygon(); return; }   // 点起点 → 完成
  _verts.push(ll2coord(e.lngLat));
  setPolygonTemp(ll2coord(e.lngLat));   // 光标暂置刚落的顶点，mousemove 后跟随
}

function onDblClick(e) {
  if (_mode !== MODE.DRAW_POLYGON) return;
  if (e.preventDefault) e.preventDefault();   // 防御：合成事件可能无 preventDefault
  // 双击前的两次 click 各加一个同位顶点 → 剥除尾部近似重复点（geojson.io splice(-3,2) 等效）
  while (_verts.length >= 2 && pixDist(_verts[_verts.length - 1], _verts[_verts.length - 2]) < 3) _verts.pop();
  finishPolygon();
}

function onMouseMove(e) {
  if (_mode === MODE.DRAW_POLYGON) {
    setPolygonTemp(ll2coord(e.lngLat));
  } else if (_mode === MODE.DRAW_RECTANGLE && _rectFirst) {
    setRectangleTemp(rectCorners(_rectFirst, e.point, e.originalEvent.shiftKey));
  }
}

function onMouseDown(e) {
  if (_mode !== MODE.DRAW_RECTANGLE || e.originalEvent.button !== 0) return;
  _rectFirst = { x: e.point.x, y: e.point.y };
  const c = ll2coord(e.lngLat);
  setRectangleTemp([c, c, c, c]);   // 退化矩形，等拖拽
}

function onMouseUp(e) {
  if (_mode !== MODE.DRAW_RECTANGLE || !_rectFirst) return;
  const corners = rectCorners(_rectFirst, e.point, e.originalEvent.shiftKey);
  _rectFirst = null;
  if (!rectNonZero(corners)) { toast.info('按下并拖拽绘制矩形'); return; }
  const ring = [...corners, corners[0]];
  commit({ type: 'Polygon', coordinates: [ring] }, '矩形', 4);
}

function onKeyDown(e) {
  if (!isDrawActive()) return;
  const t = e.target;
  if (t && /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
  if (e.key === 'Escape') { cancelDraw(); }
  else if (e.key === 'Enter' && _mode === MODE.DRAW_POLYGON) { finishPolygon(); }
}

function bindHandlers() {
  _map.on('click', onClick);
  _map.on('dblclick', onDblClick);
  _map.on('mousemove', onMouseMove);
  _map.on('mousedown', onMouseDown);
  _map.on('mouseup', onMouseUp);
}
function unbindHandlers() {
  if (!_map) return;
  _map.off('click', onClick);
  _map.off('dblclick', onDblClick);
  _map.off('mousemove', onMouseMove);
  _map.off('mousedown', onMouseDown);
  _map.off('mouseup', onMouseUp);
}

// ── 提示条（动态挂 #map，仿 geojson.io mode_hints 左上角）──
function hintEl() { return document.getElementById('draw-hint'); }
function showHint(shape) {
  let el = hintEl();
  if (!el) {
    el = document.createElement('div');
    el.id = 'draw-hint'; el.className = 'draw-hint';
    const mapEl = document.getElementById('map');
    if (mapEl) mapEl.appendChild(el); else document.body.appendChild(el);
  }
  el.textContent = shape === 'rectangle' ? HINT_RECT : HINT_POLY;
  el.hidden = false;
}
function hideHint() { const el = hintEl(); if (el) el.hidden = true; }

function deactivateButtons() {
  document.querySelectorAll('.draw-tool[aria-pressed="true"]').forEach((b) => {
    b.setAttribute('aria-pressed', 'false');
    b.classList.remove('is-active');
  });
}

// ── 对外 ──
export function startDraw(shape) {   // 'polygon' | 'rectangle'
  if (!_map) return;
  const mode = shape === 'rectangle' ? MODE.DRAW_RECTANGLE : MODE.DRAW_POLYGON;
  if (isDrawActive()) {
    if (getMode() === mode) { exitDraw(); return; }   // 同工具再点 = 收起
    stopDraw();   // 切形状 → 先清场
  }
  _mode = mode; setMode(mode);
  _verts = []; _rectFirst = null;
  addDrawLayers();
  if (_map.doubleClickZoom) _map.doubleClickZoom.disable();
  _map.getCanvas().style.cursor = 'crosshair';
  bindHandlers();
  showHint(shape);
}

export function stopDraw() {
  unbindHandlers();
  removeDrawLayers();
  if (_map) {
    if (_map.doubleClickZoom) _map.doubleClickZoom.enable();
    _map.getCanvas().style.cursor = '';
  }
  _mode = MODE.NONE; setMode(MODE.NONE);
  _verts = []; _rectFirst = null;
  hideHint();
}

/** stopDraw + 释放按钮激活态——用于面向用户的退出（提交/取消/toggle off）。
 *  切形状时只用 stopDraw（不清新按钮，toolbar 已把新按钮置 active）。 */
function exitDraw() { stopDraw(); deactivateButtons(); }

export function initDrawTool(map) {
  _map = map;
  document.addEventListener('keydown', onKeyDown);
}
