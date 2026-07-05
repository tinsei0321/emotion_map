// ═══ district-stats.js — L1 数据总览：中心城区「8 组团」分布（point-in-polygon）═══
// 拉取「行政区」preset（DATA/boundaries/presets/行政区.geojson，经 /api/v1/range/preset），
// 对 L1 源点做射线法 point-in-polygon 分类 → 8 组团分布（横条图用）。
// 组团名严格按用户定义（绝不能错：名与范围对应）；9 preset MC → 8 组团（生物产业园+龙泉绿心 合并为「高新区·生物产业园」）。
// 中心城区内外计数不经此模块（用 L1 数据自带 area_tag 字段，零 PIP）—— per-组团 才需 PIP（结果缓存到 layer._tuanCls）。
import { fetchRangePreset } from './api.js';

// 8 组团 → preset MC（polygon 来源）。高新区·生物产业园 = 生物产业园 + 龙泉绿心 合并。
const _TUAN_MAP = {
  '西陵': ['西陵区'],
  '伍家岗': ['伍家岗区'],
  '点军': ['点军区'],
  '小溪塔': ['小溪塔'],
  '高新区·生物产业园': ['生物产业园', '龙泉绿心'],
  '龙泉': ['龙泉'],
  '猇亭': ['猇亭区'],
  '白洋·顾家店': ['白洋'],
};
const _TUAN_ORDER = Object.keys(_TUAN_MAP);
const _MC_TO_TUAN = {};
for (const [t, mcs] of Object.entries(_TUAN_MAP)) for (const m of mcs) _MC_TO_TUAN[m] = t;

export function tuanOrder() { return _TUAN_ORDER.slice(); }

let _districtCache = null;   // {tuanOrder, byTuan:{组团:[{geometry,bbox}]}}

/** 加载行政区 preset（一次缓存），按组团聚合 polygon + 预算 bbox。返 {tuanOrder, byTuan} 或 null。 */
export async function loadDistricts() {
  if (_districtCache) return _districtCache;
  try {
    const res = await fetchRangePreset('admin_district');
    if (!res || !res.available || !res.geojson) return null;
    const nameField = res.nameField || 'MC';
    const byTuan = {};
    for (const t of _TUAN_ORDER) byTuan[t] = [];
    for (const f of (res.geojson.features || [])) {
      const mc = String((f.properties || {})[nameField] ?? '');
      const tuan = _MC_TO_TUAN[mc];
      if (!tuan || !f.geometry) continue;
      const bbox = _geomBBox(f.geometry);
      if (!bbox) continue;
      byTuan[tuan].push({ geometry: f.geometry, bbox });
    }
    _districtCache = { tuanOrder: _TUAN_ORDER, byTuan };
    return _districtCache;
  } catch (e) { return null; }
}

/** 几何 bbox [minLng,minLat,maxLng,maxLat]（外环；MultiPolygon 全并集）。 */
function _geomBBox(geom) {
  let coords = [];
  if (geom.type === 'Polygon') coords = (geom.coordinates || [])[0] || [];
  else if (geom.type === 'MultiPolygon') for (const p of (geom.coordinates || [])) coords.push(...((p || [])[0] || []));
  else return null;
  if (!coords.length) return null;
  let mnx = Infinity, mxx = -Infinity, mny = Infinity, mxy = -Infinity;
  for (const [x, y] of coords) { if (x < mnx) mnx = x; if (x > mxx) mxx = x; if (y < mny) mny = y; if (y > mxy) mxy = y; }
  return [mnx, mny, mxx, mxy];
}

/** 射线法 point-in-ring。pt=[x,y], ring=[[x,y],...]。 */
function _inRing([x, y], ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) inside = !inside;
  }
  return inside;
}
/** point-in-polygon（带洞）；MultiPolygon 任一组成命中即命中。 */
function _inPoly(pt, geom) {
  if (!geom) return false;
  if (geom.type === 'Polygon') {
    const rings = geom.coordinates || [];
    if (!_inRing(pt, rings[0])) return false;
    return !rings.slice(1).some((h) => _inRing(pt, h));
  }
  if (geom.type === 'MultiPolygon') {
    return (geom.coordinates || []).some((poly) => _inPoly(pt, { type: 'Polygon', coordinates: poly }));
  }
  return false;
}
function _inBBox([x, y], b) { return b && x >= b[0] && x <= b[2] && y >= b[1] && y <= b[3]; }

/** 点坐标 [lng,lat]（Point feature）。非点返 null。 */
function _pointCoord(f) {
  const g = f && f.geometry;
  if (g && g.type === 'Point' && Array.isArray(g.coordinates)) return g.coordinates;
  return null;
}

/**
 * per-组团 分类（射线法 + bbox 预筛）。返 {perTuan:{组团:n}, inTuan:n, total:n}。
 * 命中任一成员 polygon 即计入该组团；不在任何组团 polygon 内的点不计入 perTuan（=中心城区以外）。
 * heavy → 调用方按 layer.id 缓存到 layer._tuanCls，避免每次 setOverview 重跑（曾致 L1 网格卡顿）。
 */
export function classifyPointsByDistrict(points, preload) {
  const out = { perTuan: {}, inTuan: 0, total: 0 };
  const order = (preload && preload.tuanOrder) || _TUAN_ORDER;
  for (const t of order) out.perTuan[t] = 0;
  if (!preload) return out;
  for (const p of points) {
    const c = _pointCoord(p);
    if (!c) continue;
    out.total++;
    let hit = null;
    for (const t of order) {
      for (const g of preload.byTuan[t]) {
        if (!_inBBox(c, g.bbox)) continue;        // bbox 预筛：明显在多边形外直接跳过
        if (_inPoly(c, g.geometry)) { hit = t; break; }
      }
      if (hit) break;
    }
    if (hit) { out.perTuan[hit]++; out.inTuan++; }
  }
  return out;
}

/** Polygon/MultiPolygon 质心 [lng,lat]（外环顶点平均，演示用近似）—— 保留供 grid 兜底。 */
export function polyCentroid(f) {
  const g = f && f.geometry;
  if (!g) return null;
  let ring = null;
  if (g.type === 'Polygon') ring = (g.coordinates || [])[0];
  else if (g.type === 'MultiPolygon') ring = ((g.coordinates || [])[0] || [])[0];
  if (!ring || !ring.length) return null;
  let sx = 0, sy = 0;
  for (const [x, y] of ring) { sx += x; sy += y; }
  return [sx / ring.length, sy / ring.length];
}
