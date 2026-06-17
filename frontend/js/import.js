// ═══ import.js — geojson.io-style import pipeline (vanilla JS port) ═══
// Flow: groupFiles → detectGroupType → [dialog picks/overrides type] →
//       parseGroup → reprojectFC → splitByGeometry → detectPolarity → layers.
//
// Parser libs (CDN globals, loaded in index.html): csv2geojson, shpjs, proj4,
// fflate (to zip shapefile sidecars for shpjs). KML via dynamic ESM import of
// @tmcw/togeojson (best-effort; degrades gracefully if CDN blocked).

import { FIELD_SYNONYMS, POLARITY_ORDER } from './state.js';

// ── Format table (drives the confirm-dialog dropdown) ──────────────────────
export const FILE_TYPES = [
  { id: 'geojson', label: 'GeoJSON', exts: ['.geojson', '.json'] },
  { id: 'csv', label: 'CSV', exts: ['.csv'] },
  { id: 'kml', label: 'KML', exts: ['.kml'] },
  { id: 'shapefile', label: 'Shapefile', exts: ['.shp', '.dbf', '.shx', '.prj', '.cpg', '.zip'] },
];

const extOf = (name) => { const i = name.lastIndexOf('.'); return i >= 0 ? name.slice(i).toLowerCase() : ''; };

/** Group a FileList into import units: shapefile sidecar bundles (share base
 *  name) become one group; everything else is a single-file group. 1:1 geojson.io groupFiles. */
export function groupFiles(files) {
  const arr = Array.from(files || []);
  const bundles = new Map();   // baseName(lower) -> File[]
  const singles = [];
  for (const f of arr) {
    const m = f.name.match(/^(.+)\.(shp|dbf|shx|prj|cpg)$/i);
    if (m) {
      const base = m[1].toLowerCase();
      if (!bundles.has(base)) bundles.set(base, []);
      bundles.get(base).push(f);
    } else {
      singles.push(f);
    }
  }
  const groups = [];
  for (const fs of bundles.values()) groups.push({ kind: 'bundle', files: fs });
  for (const f of singles) groups.push({ kind: 'single', files: [f] });
  return groups;
}

/** Best-guess type from group (ext sniff; .json defaults to geojson, refined at parse). */
export function detectGroupType(group) {
  if (group.kind === 'bundle') {
    return group.files.some((f) => /\.shp$/i.test(f.name)) ? 'shapefile' : null;
  }
  const ext = extOf(group.files[0].name);
  if (ext === '.geojson' || ext === '.json') return 'geojson';
  if (ext === '.csv') return 'csv';
  if (ext === '.kml') return 'kml';
  if (ext === '.zip') return 'shapefile';
  return null;
}

// ── Parsers ────────────────────────────────────────────────────────────────
async function parseGeoJSON(text) {
  const obj = JSON.parse(text);
  if (obj && obj.type === 'Topology' && window.topojson) {
    return window.topojson.feature(obj, Object.keys(obj.objects)[0]);
  }
  if (obj && (obj.type === 'FeatureCollection' || obj.type === 'Feature' || /^Multi/.test(obj.type) || obj.type === 'GeometryCollection')) {
    return normalizeFC(obj);
  }
  throw new Error('不是合法的 GeoJSON / TopoJSON');
}

function parseCSV(text) {
  if (!window.csv2geojson) throw new Error('CSV 解析库未加载');
  return new Promise((resolve, reject) => {
    window.csv2geojson.csv2geojson(text, (err, fc) => {
      if (err) return reject(new Error('CSV 缺少经纬度列或格式有误'));
      resolve(normalizeFC(fc));
    });
  });
}

async function parseKML(text) {
  let mod;
  try {
    mod = await import('https://esm.sh/@tmcw/togeojson@5.8.1');
  } catch (e) {
    throw new Error('KML 解析库加载失败（CDN 不可达）');
  }
  const dom = new DOMParser().parseFromString(text, 'text/xml');
  return normalizeFC(mod.kml(dom));
}

async function parseShapefile(files) {
  if (!window.shp) throw new Error('Shapefile 解析库未加载');
  const zip = files.find((f) => /\.zip$/i.test(f.name));
  if (zip) {
    const fc = await window.shp(await zip.arrayBuffer());   // shpjs takes ArrayBuffer
    return normalizeFC(fc);
  }
  // 5-file bundle (.shp+.dbf+.prj+.shx+.cpg) → read .shp + .dbf directly via
  // shpjs low-level API (parseShp/parseDbf/combine), no fflate zip needed.
  const shpFile = files.find((f) => /\.shp$/i.test(f.name));
  const dbfFile = files.find((f) => /\.dbf$/i.test(f.name));
  if (!shpFile) throw new Error('Shapefile 缺少 .shp 主文件');

  if (dbfFile && typeof window.shp.parseShp === 'function' && typeof window.shp.parseDbf === 'function') {
    const shpGeo = window.shp.parseShp(await shpFile.arrayBuffer());
    const dbfRows = window.shp.parseDbf(await dbfFile.arrayBuffer());
    // shpjs.combine takes [geometries, properties] (shp FIRST, dbf second) — order matters.
    const combined = typeof window.shp.combine === 'function'
      ? window.shp.combine([shpGeo, dbfRows])
      : manualCombine(shpGeo, dbfRows);
    return normalizeFC(combined);
  }
  // Fallback: zip the sidecars (fflate) and let shpjs parse the zip.
  if (!window.fflate) throw new Error('打包库未加载，请改用 .zip');
  const store = {};
  for (const f of files) {
    const b = new Uint8Array(await f.arrayBuffer());
    store[f.name.split(/[\\/]/).pop()] = b;
  }
  const fc = await window.shp(window.fflate.zipSync(store).buffer);
  return normalizeFC(fc);
}

/** Combine shpjs parseShp geometries + parseDbf rows into a FeatureCollection
 *  (used if shpjs.combine is unavailable). */
function manualCombine(shpGeo, dbfRows) {
  const geoms = Array.isArray(shpGeo) ? shpGeo : [shpGeo];
  const props = Array.isArray(dbfRows) ? dbfRows : (dbfRows && dbfRows.features ? dbfRows.features.map((f) => f.properties) : []);
  const features = geoms.map((g, i) => ({
    type: 'Feature',
    geometry: g.geometry || g,
    properties: props[i] || {},
  }));
  return { type: 'FeatureCollection', features };
}

export async function parseGroup(group, type) {
  switch (type) {
    case 'geojson':    return parseGeoJSON(await group.files[0].text());
    case 'csv':        return parseCSV(await group.files[0].text());
    case 'kml':        return parseKML(await group.files[0].text());
    case 'shapefile':  return parseShapefile(group.files);
    default:           throw new Error('不支持的格式');
  }
}

/** Coerce any geojson-ish object into a clean FeatureCollection. */
function normalizeFC(obj) {
  if (!obj) return { type: 'FeatureCollection', features: [] };
  if (obj.type === 'FeatureCollection') return { type: 'FeatureCollection', features: obj.features || [] };
  if (obj.type === 'Feature') return { type: 'FeatureCollection', features: [obj] };
  if (obj && obj.type && /^Multi|Point|Line|Polygon|GeometryCollection/.test(obj.type)) {
    return { type: 'FeatureCollection', features: [{ type: 'Feature', geometry: obj, properties: {} }] };
  }
  if (Array.isArray(obj)) return { type: 'FeatureCollection', features: obj };
  throw new Error('无法识别的地理数据结构');
}

// ── CRS reprojection → WGS84/EPSG:4326 ─────────────────────────────────────
// proj4 reads the .prj WKT directly (recent versions parse WKT). If no .prj but
// coords look projected (huge numbers), fall back to EPSG:4546 (宜昌 CGCS2000 /
// 3-degree Gauss-Kruger CM 111E). Anything ambiguous → load as-is + warn caller.
// Heuristic fallback (no .prj but coords look projected): CGCS2000 3-degree
// Gauss-Kruger CM 111E with false-easting 500000 (EPSG:4538, 宜昌规划常用).
const EPSG_CGCS2000_111E = '+proj=tmerc +lat_0=0 +lon_0=111 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs';
const WGS84 = '+proj=longlat +datum=WGS84 +no_defs';
const looksProjected = ([x, y]) => Math.abs(x) > 180 || Math.abs(y) > 90;

export function reprojectFC(fc, prjWkt) {
  if (!fc.features.length) return fc;
  const sample = firstCoord(fc);
  if (!sample) return fc;
  const projected = looksProjected(sample);
  if (!projected && !prjWkt) return fc;          // already lon/lat, nothing to do
  if (!window.proj4) return { _crsWarn: true, fc };

  let srcDef = null;
  if (prjWkt) {
    try { window.proj4.defs('__src', prjWkt); srcDef = '__src'; }
    catch (e) { srcDef = null; }
  }
  if (!srcDef && projected) srcDef = EPSG_CGCS2000_111E;  // heuristic fallback (宜昌)
  if (!srcDef) return fc;

  try {
    walkCoords(fc, (coord) => {
      const [x, y] = window.proj4(srcDef, WGS84, coord);
      coord[0] = x; coord[1] = y;
    });
    return fc;
  } catch (e) {
    return { _crsWarn: true, fc };
  }
}

function firstCoord(fc) {
  for (const f of fc.features) {
    const c = findFirstCoord(f.geometry);
    if (c) return c;
  }
  return null;
}
function findFirstCoord(geom) {
  if (!geom || !geom.coordinates) return null;
  const dive = (a) => Array.isArray(a[0]) ? dive(a[0]) : a;
  try { return dive(geom.coordinates); } catch (e) { return null; }
}
function walkCoords(fc, fn) {
  const dive = (a) => {
    if (typeof a[0] === 'number') { fn(a); return; }
    for (const c of a) dive(c);
  };
  for (const f of fc.features) if (f.geometry && f.geometry.coordinates) dive(f.geometry.coordinates);
}

/** Find the .prj text in a shapefile bundle (null for other groups). */
export async function readPrj(group) {
  if (group.kind !== 'bundle') return null;
  const prj = group.files.find((f) => /\.prj$/i.test(f.name));
  return prj ? (await prj.text()) : null;
}

// ── Geometry split: points vs ranges (polygon + line) ─────────────────────
// GIS rule: a CLOSED LineString (first==last) is a polygon ring → classify as
// polygon (renders as an outline-only face, marker shows 面). Open lines stay lines.
export function splitByGeometry(fc) {
  const points = [], lines = [], polygons = [];
  for (const f of fc.features) {
    const t = f.geometry && f.geometry.type;
    if (t === 'Point' || t === 'MultiPoint') points.push(f);
    else if (t === 'Polygon' || t === 'MultiPolygon') polygons.push(f);
    else if (t === 'LineString') {
      if (isClosedRing(f.geometry.coordinates)) polygons.push(toPolygonFeature(f));
      else lines.push(f);
    } else if (t === 'MultiLineString') {
      const rings = f.geometry.coordinates;
      if (rings.length && rings.every(isClosedRing)) polygons.push(toMultiPolygonFeature(f));
      else lines.push(f);
    }
  }
  return {
    points:   { type: 'FeatureCollection', features: points },
    lines:    { type: 'FeatureCollection', features: lines },
    polygons: { type: 'FeatureCollection', features: polygons },
  };
}

function isClosedRing(coords) {
  return Array.isArray(coords) && coords.length >= 4 &&
    coords[0][0] === coords[coords.length - 1][0] &&
    coords[0][1] === coords[coords.length - 1][1];
}
function toPolygonFeature(f) {
  return { type: 'Feature', properties: f.properties || {}, geometry: { type: 'Polygon', coordinates: [f.geometry.coordinates] } };
}
function toMultiPolygonFeature(f) {
  return { type: 'Feature', properties: f.properties || {}, geometry: { type: 'MultiPolygon', coordinates: f.geometry.coordinates.map((c) => [c]) } };
}

// ── Color-mode detection (point layers) ────────────────────────────────────
// Three modes: 'polarity' (L2, 5-color) | 'confidence' (L1, orange ramp) |
// 'needsAnalysis' (grey). Decided by which columns the data carries, so L1
// (l1_confidence, no polarity) and L2 (polarity) both color correctly.
export function detectColorMode(pointFC) {
  if (!pointFC.features.length) return { fc: pointFC, colorMode: 'polarity', needsAnalysis: false };
  const sample = pointFC.features[0].properties || {};
  const polKey = pickKey(sample, FIELD_SYNONYMS.polarity);
  const confKey = pickKey(sample, ['l1_confidence', 'confidence', ...FIELD_SYNONYMS.score]);

  if (polKey) {                                   // L2 polarity
    for (const f of pointFC.features) {
      const p = f.properties || (f.properties = {});
      p.polarity = canonicalPolarity(p[polKey]);
      if (!p.polarity && confKey) p.polarity = polarityFromScore(Number(p[confKey]));
      if (confKey && p[confKey] != null) p.score = Number(p[confKey]);
      if (p.score == null) p.score = scoreFor(p.polarity);
      if (!p.polarity) p.polarity = 'Neutral';
      const tk = pickKey(p, FIELD_SYNONYMS.text); if (tk && !p.text) p.text = p[tk];
      const lk = pickKey(p, FIELD_SYNONYMS.location); if (lk && !p.location) p.location = p[lk];
    }
    return { fc: pointFC, colorMode: 'polarity', needsAnalysis: false };
  }
  if (confKey) {                                  // L1 confidence (orange ramp)
    for (const f of pointFC.features) {
      const p = f.properties || (f.properties = {});
      const v = Number(p[confKey]);
      p.score = Number.isFinite(v) ? Math.max(0, Math.min(1, v)) : 0.5;
      const tk = pickKey(p, FIELD_SYNONYMS.text); if (tk && !p.text) p.text = p[tk];
      const lk = pickKey(p, FIELD_SYNONYMS.location); if (lk && !p.location) p.location = p[lk];
    }
    return { fc: pointFC, colorMode: 'confidence', needsAnalysis: false };
  }
  return { fc: pointFC, colorMode: 'needsAnalysis', needsAnalysis: true };
}

function pickKey(props, candidates) {
  const keys = Object.keys(props);
  for (const c of candidates) {
    const hit = keys.find((k) => k.toLowerCase() === c.toLowerCase());
    if (hit && props[hit] != null && props[hit] !== '') return hit;
  }
  return null;
}
function canonicalPolarity(v) {
  if (v == null) return null;
  const s = String(v).trim();
  const norm = s.toLowerCase();
  if (POLARITY_ORDER.includes(s)) return s;
  const map = {
    '非常积极': 'Very Positive', '积极': 'Positive', '中性': 'Neutral', '消极': 'Negative', '非常消极': 'Very Negative',
    'very positive': 'Very Positive', 'positive': 'Positive', 'neutral': 'Neutral', 'negative': 'Negative', 'very negative': 'Very Negative',
    'pos': 'Positive', 'neg': 'Negative',
  };
  return map[norm] || null;
}
function polarityFromScore(sc) {
  if (Number.isNaN(sc)) return 'Neutral';
  if (sc >= 0.8) return 'Very Positive';
  if (sc >= 0.6) return 'Positive';
  if (sc > 0.4) return 'Neutral';
  if (sc > 0.2) return 'Negative';
  return 'Very Negative';
}
function scoreFor(pol) {
  return pol === 'Very Positive' ? 0.9 : pol === 'Positive' ? 0.7 : pol === 'Neutral' ? 0.5 : pol === 'Negative' ? 0.3 : 0.1;
}

/** bbox [west, south, east, north] for fitBounds; null if empty. */
export function fcBBox(fc) {
  let b = null;
  walkCoords(fc, ([x, y]) => {
    if (!b) b = [x, y, x, y];
    else { if (x < b[0]) b[0] = x; if (y < b[1]) b[1] = y; if (x > b[2]) b[2] = x; if (y > b[3]) b[3] = y; }
  });
  return b;
}
