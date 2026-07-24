// ═══ import.js — geojson.io-style import pipeline (vanilla JS port) ═══
// Flow: groupFiles → detectGroupType → [dialog picks type + per-format config +
//       source CRS] → parseGroup → reprojectFC → splitByGeometry → detectPolarity → layers.
//
// Parser libs (CDN globals, loaded in index.html): csv2geojson, shpjs, proj4,
// fflate (to zip shapefile sidecars for shpjs). KML/GPX via dynamic ESM import of
// @tmcw/togeojson. TopoJSON via topojson-client. CSV WKT/polyline kinds via
// wellknown / @mapbox/polyline (best-effort; degrade gracefully if CDN blocked).

import { FIELD_SYNONYMS, POLARITY_ORDER } from './state.js';
import { findKeyByRole } from './field_dictionary.js';   // P1 字段语义层·按 role 找列（替代 pickKey+FIELD_SYNONYMS）

// ── Format table (drives the confirm-dialog dropdown) ──────────────────────
export const FILE_TYPES = [
  { id: 'geojson', label: 'GeoJSON', exts: ['.geojson', '.json'] },
  { id: 'topojson', label: 'TopoJSON', exts: ['.topojson'] },
  { id: 'csv', label: 'CSV', exts: ['.csv'] },
  { id: 'kml', label: 'KML', exts: ['.kml'] },
  { id: 'gpx', label: 'GPX', exts: ['.gpx'] },
  { id: 'shapefile', label: 'Shapefile', exts: ['.shp', '.dbf', '.shx', '.prj', '.cpg', '.zip'] },
];

const extOf = (name) => { const i = name.lastIndexOf('.'); return i >= 0 ? name.slice(i).toLowerCase() : ''; };

/** 动态加载 ESM 依赖（CDN esm.sh；wellknown/polyline 等无 UMD 构建的库走此通道）。失败抛错。 */
async function loadEsm(spec) {
  try {
    const mod = await import('https://esm.sh/' + spec);
    return mod.default || mod;
  } catch (e) {
    throw new Error('依赖加载失败：' + spec + '（CDN 不可达）');
  }
}

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
  if (ext === '.topojson') return 'topojson';
  if (ext === '.csv') return 'csv';
  if (ext === '.kml') return 'kml';
  if (ext === '.gpx') return 'gpx';
  if (ext === '.zip') return 'shapefile';
  return null;
}

// ── Parsers ────────────────────────────────────────────────────────────────
async function parseGeoJSON(text) {
  const obj = JSON.parse(text);
  if (obj && obj.type === 'Topology' && window.topojson) {
    return normalizeFC(window.topojson.feature(obj, Object.keys(obj.objects)[0]));
  }
  if (obj && (obj.type === 'FeatureCollection' || obj.type === 'Feature' || /^Multi/.test(obj.type) || obj.type === 'GeometryCollection')) {
    return normalizeFC(obj);
  }
  throw new Error('不是合法的 GeoJSON / TopoJSON');
}

async function parseTopoJSON(text) {
  if (!window.topojson) throw new Error('TopoJSON 解析库未加载（CDN 不可达）');
  const obj = JSON.parse(text);
  if (!obj || obj.type !== 'Topology') throw new Error('不是合法的 TopoJSON');
  const layers = Object.keys(obj.objects || {});
  if (!layers.length) throw new Error('TopoJSON 无几何对象');
  // 合并所有 object 层为一个 FeatureCollection（多图层时一并导入）。
  const merged = [];
  for (const k of layers) {
    try { merged.push(...(window.topojson.feature(obj, k)).features || []); } catch (e) { /* skip bad layer */ }
  }
  return normalizeFC({ type: 'FeatureCollection', features: merged });
}

/**
 * CSV parser — 接弹窗配置 cfg（1:1 geojson.io CSV 导入弹窗）。
 * cfg: { kind, delimiter, latfield, lonfield, wktField, geojsonField, polylineField, inferTypes }
 *   kind: 'coords' | 'wkt' | 'geojson' | 'polyline'
 */
async function parseCSV(text, cfg = {}) {
  const kind = cfg.kind || 'coords';
  const delimiter = cfg.delimiter || 'auto';

  if (kind === 'wkt') {
    const col = cfg.wktField;
    if (!col) throw new Error('WKT 列未指定');
    const wk = await loadEsm('wellknown@0.5.0');   // default = (wkt) → geometry
    const rows = dsvRows(text, delimiter);
    const feats = rows.body.map((r) => {
      const wkt = r[col];
      if (!wkt || !String(wkt).trim()) return null;
      const geom = wk(String(wkt).trim());
      return geom ? { type: 'Feature', geometry: geom, properties: { ...r } } : null;
    }).filter(Boolean);
    return postCsv(normalizeFC({ type: 'FeatureCollection', features: feats }), cfg);
  }
  if (kind === 'geojson') {
    const col = cfg.geojsonField;
    if (!col) throw new Error('GeoJSON 列未指定');
    const rows = dsvRows(text, delimiter);
    const feats = rows.body.map((r) => {
      const raw = r[col];
      if (!raw || !String(raw).trim()) return null;
      try {
        const g = JSON.parse(String(raw));
        return { type: 'Feature', geometry: g, properties: { ...r } };
      } catch (e) { return null; }
    }).filter(Boolean);
    return postCsv(normalizeFC({ type: 'FeatureCollection', features: feats }), cfg);
  }
  if (kind === 'polyline') {
    const col = cfg.polylineField;
    if (!col) throw new Error('折线列未指定');
    const pl = await loadEsm('@mapbox/polyline@1.2.0');   // default = { decode, encode }
    const rows = dsvRows(text, delimiter);
    const feats = rows.body.map((r) => {
      const enc = r[col];
      if (!enc || !String(enc).trim()) return null;
      try {
        const coords = pl.decode(String(enc).trim());
        // polyline.decode → [[lat,lng],...]；GeoJSON 要 [lng,lat]
        const g = { type: 'LineString', coordinates: coords.map(([la, lo]) => [lo, la]) };
        return { type: 'Feature', geometry: g, properties: { ...r } };
      } catch (e) { return null; }
    }).filter(Boolean);
    return postCsv(normalizeFC({ type: 'FeatureCollection', features: feats }), cfg);
  }

  // kind === 'coords' —— csv2geojson 原生支持 latfield/lonfield/delimiter
  if (!window.csv2geojson) throw new Error('CSV 解析库未加载');
  const opts = {};
  if (cfg.latfield) opts.latfield = cfg.latfield;
  if (cfg.lonfield) opts.lonfield = cfg.lonfield;
  if (delimiter && delimiter !== 'auto') opts.delimiter = resolveDelim(delimiter);   // '\\t' → '\t'
  return new Promise((resolve, reject) => {
    window.csv2geojson.csv2geojson(text, opts, (err, fc) => {
      if (err) return reject(new Error('CSV 缺少经纬度列或格式有误（可在「解析方式」改 WKT / GeoJSON 列）'));
      resolve(postCsv(normalizeFC(fc), cfg));
    });
  });
}

/** Infer types + 清理：csv 本只含字符串；勾选后将 number/boolean/null 推断。 */
function postCsv(fc, cfg) {
  if (cfg.inferTypes) coercePropertyTypes(fc);
  return fc;
}
function coercePropertyTypes(fc) {
  const BOOL = { true: true, false: false };
  for (const f of fc.features) {
    const p = f.properties || (f.properties = {});
    for (const k of Object.keys(p)) {
      const v = p[k];
      if (typeof v !== 'string') continue;
      const s = v.trim();
      if (s === '') { p[k] = null; continue; }
      const low = s.toLowerCase();
      if (low === 'true' || low === 'false') { p[k] = BOOL[low]; continue; }
      if (/^-?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(s)) { const n = Number(s); if (Number.isFinite(n)) { p[k] = n; continue; } }
    }
  }
}

// ── P2 字段语义层 · 字段画像（profile）─────────────────────────────────────
// profileFields：纯读 fc.properties（不 mutate），产 {field: {dtype, samples, stats}}。
// 供 tools.js getFieldCard 规则标注 + miss 字段调 /aiqa/profile_fields 推断 role 用。
// dtype ∈ {number, string, boolean, datetime}——datetime 靠正则+Date.parse 判（值不转换，只标 dtype）。
const _DT_PATTERNS = [
  /^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?/,   // ISO YYYY-MM-DD[T ]HH:MM[:SS]
  /^\d{4}-\d{2}-\d{2}$/,                            // YYYY-MM-DD
  /^\d{4}\/\d{1,2}\/\d{1,2}/,                       // YYYY/MM/DD
  /^\d{4}-\d{2}$/,                                  // YYYY-MM
];
function _looksDatetime(s) {
  if (typeof s !== 'string') return false;
  for (const re of _DT_PATTERNS) if (re.test(s)) return Number.isFinite(Date.parse(s));
  return false;
}
function _profileStats(dtype, a) {
  if (dtype === 'number' && a.nums.length) {
    let mn = a.nums[0], mx = a.nums[0], sum = 0;
    for (const n of a.nums) { if (n < mn) mn = n; if (n > mx) mx = n; sum += n; }
    return { min: mn, max: mx, mean: Math.round((sum / a.nums.length) * 1e4) / 1e4 };
  }
  if (dtype === 'datetime' && a.dts.length) {
    const ts = a.dts.map((s) => Date.parse(s)).filter((t) => Number.isFinite(t));
    if (ts.length) return { min: new Date(Math.min(...ts)).toISOString(), max: new Date(Math.max(...ts)).toISOString() };
  }
  // string / boolean → 样本去重计数近似（前 20 feature 的样本，标注 approximate）
  return { distinct: a.samples.length, approximate: true };
}
/** 字段画像：{field: {dtype, samples[], stats}}。采样前 20 feature，samples 前 3 去重（截 24 字符）。 */
export function profileFields(fc) {
  const out = {};
  const feats = fc && fc.features;
  if (!feats || !feats.length) return out;
  const sample = feats.slice(0, 20);
  const acc = {};
  for (const f of sample) {
    const p = f.properties || {};
    for (const k of Object.keys(p)) {
      let a = acc[k];
      if (!a) a = acc[k] = { samples: [], nonNull: 0, num: 0, dt: 0, bool: 0, nums: [], dts: [] };
      const v = p[k];
      if (v === null || v === undefined || v === '') continue;
      a.nonNull += 1;
      const s = String(v);
      if (a.samples.length < 3 && !a.samples.includes(s)) a.samples.push(s.slice(0, 24));
      if (typeof v === 'boolean') { a.bool += 1; continue; }
      if (typeof v === 'number') { a.num += 1; if (a.nums.length < 50) a.nums.push(v); continue; }
      if (_looksDatetime(s)) { a.dt += 1; if (a.dts.length < 50) a.dts.push(s); }
    }
  }
  for (const k of Object.keys(acc)) {
    const a = acc[k];
    const dtype = a.nonNull
      ? (a.bool > a.nonNull / 2 ? 'boolean'
        : a.num > a.nonNull / 2 ? 'number'
        : a.dt > a.nonNull / 2 ? 'datetime'
        : 'string')
      : 'string';
    out[k] = { dtype, samples: a.samples, stats: _profileStats(dtype, a) };
  }
  return out;
}

/** 轻量 DSV 解析（仅用于 WKT/GeoJSON/polyline 列模式；coords 模式走 csv2geojson）。
 *  返回 { header:string[], body: Row[] }，Row = { [col]: string }。*/
export function dsvRows(text, delimiter) {
  const delim = resolveDelim(delimiter);
  const lines = text.replace(/\r\n/g, '\n').split('\n').filter((l) => l.length);
  if (!lines.length) return { header: [], body: [] };
  const header = splitLine(lines[0], delim);
  const body = [];
  for (let i = 1; i < lines.length; i++) {
    const cells = splitLine(lines[i], delim);
    const row = {};
    header.forEach((h, j) => { row[h] = cells[j] != null ? cells[j] : ''; });
    body.push(row);
  }
  return { header, body };
}
function resolveDelim(d) {
  if (d === ';' || d === '\\t' || d === '\t') return d === '\\t' || d === '\t' ? '\t' : ';';
  if (d === '|') return '|';
  return ',';
}
function splitLine(line, delim) {
  // 简单 CSV 切分（支持双引号包裹）
  const out = [];
  let cur = '', inQ = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (inQ) {
      if (ch === '"' && line[i + 1] === '"') { cur += '"'; i++; }
      else if (ch === '"') inQ = false;
      else cur += ch;
    } else if (ch === '"') inQ = true;
    else if (ch === delim) { out.push(cur); cur = ''; }
    else cur += ch;
  }
  out.push(cur);
  return out;
}

/** 读 CSV 表头（供弹窗填充列下拉）。返回 { delimiter, columns }。 */
export function csvHeader(text) {
  const cand = [',', ';', '\t', '|'];
  const first = text.replace(/\r\n/g, '\n').split('\n')[0] || '';
  let best = ',', bestN = 0;
  for (const d of cand) { const n = splitLine(first, d).length; if (n > bestN) { bestN = n; best = d; } }
  return { delimiter: best, columns: splitLine(first, best) };
}
const LAT_RE = /^(lat|latitude|纬度|y)$/i;
const LON_RE = /^(lon|lng|longitude|经度|x)$/i;
/** 猜纬度/经度列名（供弹窗默认值）。 */
export function guessLatLon(columns) {
  let lat = '', lon = '';
  for (const c of columns) { if (!lat && LAT_RE.test(c.trim())) lat = c; if (!lon && LON_RE.test(c.trim())) lon = c; }
  if (!lat || !lon) {
    for (const c of columns) {
      if (!lat && /lat|纬度/i.test(c)) lat = c;
      if (!lon && /lon|lng|经度/i.test(c)) lon = c;
    }
  }
  return { lat, lon };
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

async function parseGPX(text) {
  let mod;
  try {
    mod = await import('https://esm.sh/@tmcw/togeojson@5.8.1');
  } catch (e) {
    throw new Error('GPX 解析库加载失败（CDN 不可达）');
  }
  const dom = new DOMParser().parseFromString(text, 'text/xml');
  return normalizeFC(mod.gpx(dom));   // 含 wpt(rte/points)/trk(trkpt)/rte
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

/**
 * @param group   {kind, files}
 * @param type    FILE_TYPES id
 * @param config  { csv?:{...}, crs?:{...} }  （crs 由 main.js 在 reprojectFC 阶段用）
 */
export async function parseGroup(group, type, config = {}) {
  switch (type) {
    case 'geojson':    return parseGeoJSON(await group.files[0].text());
    case 'topojson':   return parseTopoJSON(await group.files[0].text());
    case 'csv':        return parseCSV(await group.files[0].text(), config.csv || {});
    case 'kml':        return parseKML(await group.files[0].text());
    case 'gpx':        return parseGPX(await group.files[0].text());
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
// 3-degree Gauss-Kruger CM 111E). 弹窗显式选择（opts.crs）优先于 .prj / 启发式。
const EPSG_CGCS2000_111E = '+proj=tmerc +lat_0=0 +lon_0=111 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs';
const WGS84 = '+proj=longlat +datum=WGS84 +no_defs';
const looksProjected = ([x, y]) => Math.abs(x) > 180 || Math.abs(y) > 90;

// 源 CRS 预设表（供弹窗下拉；src 字段 = reprojectFC 的 opts.crs 形态）。
export const CRS_PRESETS = [
  { id: 'auto',       label: '自动检测（.prj 优先，否则投影启发式）',                 src: { type: 'auto' } },
  { id: 'wgs84',      label: 'WGS84 (EPSG:4326) · 地理坐标',                          src: { type: 'none' } },
  { id: 'gcj02',      label: 'GCJ-02 火星坐标 · 社交媒体',                            src: { type: 'gcj02' } },
  { id: 'cgcs2000-111', label: 'CGCS2000 / 3°带 CM111°E · 宜昌',                      src: { type: 'proj', def: EPSG_CGCS2000_111E } },
  { id: 'cgcs2000-108', label: 'CGCS2000 / 3°带 CM108°E',                             src: { type: 'proj', def: '+proj=tmerc +lat_0=0 +lon_0=108 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs' } },
  { id: 'cgcs2000-114', label: 'CGCS2000 / 3°带 CM114°E',                             src: { type: 'proj', def: '+proj=tmerc +lat_0=0 +lon_0=114 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs' } },
  { id: 'cgcs2000-geo', label: 'CGCS2000 (EPSG:4490) · 地理坐标',                     src: { type: 'proj', def: '+proj=longlat +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +no_defs' } },
  { id: 'xian80-111', label: '西安80 / 3°带 CM111°E',                                 src: { type: 'proj', def: '+proj=tmerc +lat_0=0 +lon_0=111 +k=1 +x_0=500000 +y_0=0 +a=6378140 +b=6356755.288157528 +units=m +no_defs' } },
  { id: 'beijing54-111', label: '北京54 / 3°带 CM111°E',                              src: { type: 'proj', def: '+proj=tmerc +lat_0=0 +lon_0=111 +k=1 +x_0=500000 +y_0=0 +a=6378245 +b=6356863.018773047 +units=m +no_defs' } },
  { id: 'mercator',   label: 'Web Mercator (EPSG:3857)',                              src: { type: 'proj', def: '+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +no_defs' } },
  { id: 'custom',     label: '自定义…（EPSG / proj4）',                               src: { type: 'custom' } },
];

// 常见 EPSG → proj4 速查（自定义 EPSG 输入用；未命中则要求填 proj4 字符串）。
const EPSG_TO_PROJ = {
  4326: '+proj=longlat +datum=WGS84 +no_defs',
  4490: '+proj=longlat +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +no_defs',
  3857: '+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +no_defs',
  // CGCS2000 / 3°带 Gauss-Kruger（无带号前缀，CM = zone×3°）：4513=CM75 ... 4546≈CM111(宜昌近似)
  4513: '+proj=tmerc +lat_0=0 +lon_0=75 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4514: '+proj=tmerc +lat_0=0 +lon_0=78 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4515: '+proj=tmerc +lat_0=0 +lon_0=81 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4516: '+proj=tmerc +lat_0=0 +lon_0=84 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4517: '+proj=tmerc +lat_0=0 +lon_0=87 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4518: '+proj=tmerc +lat_0=0 +lon_0=90 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4519: '+proj=tmerc +lat_0=0 +lon_0=93 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4520: '+proj=tmerc +lat_0=0 +lon_0=96 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4521: '+proj=tmerc +lat_0=0 +lon_0=99 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4522: '+proj=tmerc +lat_0=0 +lon_0=102 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4523: '+proj=tmerc +lat_0=0 +lon_0=105 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4524: '+proj=tmerc +lat_0=0 +lon_0=108 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4525: '+proj=tmerc +lat_0=0 +lon_0=111 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4526: '+proj=tmerc +lat_0=0 +lon_0=114 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  // 带号前缀变体（4534-4554 系列，y_0 含带号；CM111≈4534/4546 依变体）
  4546: '+proj=tmerc +lat_0=0 +lon_0=111 +k=1 +x_0=37500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4534: '+proj=tmerc +lat_0=0 +lon_0=111 +k=1 +x_0=37500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
  4538: '+proj=tmerc +lat_0=0 +lon_0=111 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
};

/** 把弹窗的 CRS 选择（presetId + 自定义输入）解析为 reprojectFC 的 opts.crs。
 *  custom: { epsg?, proj? }（presetId==='custom' 时生效）。
 *  返回 { type:'auto'|'none'|'gcj02'|'proj', def? }。 */
export function resolveCrsChoice(presetId, custom) {
  const p = CRS_PRESETS.find((x) => x.id === presetId) || CRS_PRESETS[0];
  if (p.src.type === 'custom') {
    if (custom && custom.proj && custom.proj.trim()) return { type: 'proj', def: custom.proj.trim() };
    if (custom && custom.epsg) {
      const code = Number(String(custom.epsg).replace(/[^\d]/g, ''));
      const def = EPSG_TO_PROJ[code];
      if (def) return { type: 'proj', def };
    }
    return { type: 'auto' };   // 自定义但没填有效值 → 退自动
  }
  return p.src;
}

/** 廉价「检测到」提示文（弹窗展示用；不保证精确）。fc 可为 null。 */
export function guessCrsLabel(fc, prjWkt) {
  if (prjWkt) return '已读取 .prj（默认「自动」即用之；可手动覆盖）';
  if (!fc || !fc.features || !fc.features.length) return '导入后按坐标范围判断';
  const s = firstCoord(fc);
  if (!s) return '导入后按坐标范围判断';
  if (looksProjected(s)) return '坐标为大数 → 疑似投影（CGCS2000 3°带等），建议手动选择';
  return '坐标为经纬度 → 疑似 WGS84 / GCJ-02';
}

/**
 * reprojectFC(fc, opts) —— 把任意源 CRS 的 FC 变换到 WGS84/EPSG:4326。
 * opts: { prjWkt?, crs? }；crs 来自弹窗（resolveCrsChoice），优先级高于 prjWkt / 启发式。
 * 返回 fc，或 { _crsWarn:true, fc }（变换失败/库缺失，调用方按 WGS84 容错）。
 */
export function reprojectFC(fc, opts = {}) {
  if (!fc.features.length) return fc;
  const sample = firstCoord(fc);
  if (!sample) return fc;

  const crs = opts.crs;
  const projected = looksProjected(sample);

  // 1) 弹窗显式 CRS 优先
  if (crs && crs.type === 'gcj02') {
    try { walkCoords(fc, (c) => { const w = gcj02ToWgs84(c[0], c[1]); c[0] = w.lon; c[1] = w.lat; }); return fc; }
    catch (e) { return { _crsWarn: true, fc }; }
  }
  if (crs && crs.type === 'none') return fc;            // 用户声明已为 WGS84
  let srcDef = null;
  if (crs && crs.type === 'proj' && crs.def) srcDef = crs.def;
  // 2) auto / 未指定 → .prj 优先，投影启发式兜底
  if (!srcDef && opts.prjWkt) srcDef = opts.prjWkt;     // proj4 解析 WKT
  if (!srcDef && projected) srcDef = EPSG_CGCS2000_111E;
  if (!srcDef) return fc;                               // 地理坐标，无需变换

  if (!window.proj4) return { _crsWarn: true, fc };
  try {
    window.proj4.defs('__src', srcDef);
    walkCoords(fc, (c) => { const [x, y] = window.proj4('__src', WGS84, c); c[0] = x; c[1] = y; });
    return fc;
  } catch (e) {
    return { _crsWarn: true, fc };
  }
}

/** GCJ-02 → WGS-84（单步逆变换近似，误差数米；社交媒体偏移修正用）。
 *  入参 lon/lat 为度；海外点原样返回。 */
function gcj02ToWgs84(lon, lat) {
  if (outOfChina(lon, lat)) return { lon, lat };
  const PI = Math.PI;
  const A = 6378245.0;
  const EE = 0.00669342162296594323;
  let dLat = transformLat(lon - 105.0, lat - 35.0);
  let dLon = transformLon(lon - 105.0, lat - 35.0);
  const radLat = lat * PI / 180.0;
  let magic = Math.sin(radLat);
  magic = 1 - EE * magic * magic;
  const sqrtMagic = Math.sqrt(magic);
  dLat = (dLat * 180.0) / ((A * (1 - EE)) / (magic * sqrtMagic) * PI / 180.0);
  dLon = (dLon * 180.0) / (A / sqrtMagic * Math.cos(radLat) * PI / 180.0);
  return { lon: lon - dLon, lat: lat - dLat };
}
function outOfChina(lng, lat) {
  return !(lng > 73.66 && lng < 135.05 && lat > 3.86 && lat < 53.55);
}
function transformLat(x, y) {
  const PI = Math.PI;
  let ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x));
  ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0;
  ret += (20.0 * Math.sin(y * PI) + 40.0 * Math.sin(y / 3.0 * PI)) * 2.0 / 3.0;
  ret += (160.0 * Math.sin(y / 12.0 * PI) + 320.0 * Math.sin(y * PI / 30.0)) * 2.0 / 3.0;
  return ret;
}
function transformLon(x, y) {
  const PI = Math.PI;
  let ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x));
  ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0;
  ret += (20.0 * Math.sin(x * PI) + 40.0 * Math.sin(x / 3.0 * PI)) * 2.0 / 3.0;
  ret += (150.0 * Math.sin(x / 12.0 * PI) + 300.0 * Math.sin(x / 30.0 * PI)) * 2.0 / 3.0;
  return ret;
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
  // P1: 用 findKeyByRole 按角色找列（替代 pickKey+FIELD_SYNONYMS，收敛到 field_dictionary）
  // ⑤② 拆 role：score（情绪得分）与 confidence（数据置信度）分离——不再混找一个，免 conflates。
  const polKey = findKeyByRole(sample, 'polarity');
  const scoreKey = findKeyByRole(sample, 'score');        // 情绪得分（score/得分/评分）
  const confKey = findKeyByRole(sample, 'confidence');    // 数据置信度（l1_confidence/l2_confidence/置信度）

  if (polKey) {                                   // L2 polarity
    for (const f of pointFC.features) {
      const p = f.properties || (f.properties = {});
      p.polarity = canonicalPolarity(p[polKey]);
      // score 优先 scoreKey（情绪得分），次 confKey（兼容旧 L2 带 l2_confidence 作 score 代理），末 scoreFor
      const _sk = scoreKey || confKey;
      if (!p.polarity && _sk) p.polarity = polarityFromScore(Number(p[_sk]));
      if (_sk && p[_sk] != null) p.score = Number(p[_sk]);
      if (p.score == null) p.score = scoreFor(p.polarity);
      if (!p.polarity) p.polarity = 'Neutral';
      const tk = findKeyByRole(p, 'text'); if (tk && !p.text) p.text = p[tk];
      const lk = findKeyByRole(p, 'location'); if (lk && !p.location) p.location = p[lk];
    }
    return { fc: pointFC, colorMode: 'polarity', needsAnalysis: false };
  }
  if (confKey) {                                  // L1 confidence (orange ramp)
    for (const f of pointFC.features) {
      const p = f.properties || (f.properties = {});
      const v = Number(p[confKey]);
      p.score = Number.isFinite(v) ? Math.max(0, Math.min(1, v)) : 0.5;
      const tk = findKeyByRole(p, 'text'); if (tk && !p.text) p.text = p[tk];
      const lk = findKeyByRole(p, 'location'); if (lk && !p.location) p.location = p[lk];
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
