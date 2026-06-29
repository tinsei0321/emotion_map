// ═══ api.js — FastAPI backend bridge ═══
// Same-origin: fetches go to /api/v1/* on the frontend server (:8080), which
// serve.py reverse-proxies to the uvicorn backend (:8000). No cross-origin hop
// → no CORS / browser-extension / proxy interference (fix: export "Failed to fetch").
//   GET  /api/v1/points          → emotion points GeoJSON (?bbox=) [stub]
//   POST /api/v1/analyze         → run analysis (run_analysis_task)
//   POST /api/v1/governance      → L0→L1 pipeline (run_governance_pipeline)
//   POST /api/v1/spatial/buffer  → buffer (覆盖范围, EPSG:4546)
//   POST /api/v1/spatial/grid    → square/hex grid aggregation (EPSG:4546, snap-to-grid)

const BASE = '/api/v1';

export async function fetchPoints() {
  // Phase 2: const r = await fetch(`${BASE}/points`); return r.json();
  return null;  // Phase 1 uses sample data
}

export async function fetchStats() {
  return null;
}

export async function runAnalyze(payload) {
  const r = await fetch(`${BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`分析失败: ${r.status}`);
  return r.json();
}

export async function runGovernance(payload) {
  const r = await fetch(`${BASE}/governance`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`治理失败: ${r.status}`);
  return r.json();
}

export async function runBuffer(payload) {
  // payload: { geojson: FeatureCollection, distance: number, unit: 'm'|'km', dissolve: bool }
  const r = await fetch(`${BASE}/spatial/buffer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    let detail = `缓冲失败: ${r.status}`;
    try { const j = await r.json(); detail = j.detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return r.json();
}

export async function runGrid(payload) {
  // payload: { geojson: FeatureCollection, grid_type:'hex'|'square', cell_size:number, unit:'m'|'km', resolution?:0-15 }
  // → { success, geojson, feature_count, message }（注意字段是 geojson，非 buffer_geojson）
  const r = await fetch(`${BASE}/spatial/grid`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    let detail = `网格聚合失败: ${r.status}`;
    try { const j = await r.json(); detail = j.detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return r.json();
}

export async function runAggregate(payload) {
  // payload: { points_geojson, polygons_geojson, agg_cols?, name_col? }
  // → { success, geojson, feature_count, message }（指定单元聚合：点 → 面域统计）
  const r = await fetch(`${BASE}/spatial/aggregate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    let detail = `空间聚合失败: ${r.status}`;
    try { const j = await r.json(); detail = j.detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return r.json();
}

export async function runTerrain(payload) {
  // payload: { geojson, polarity:'overall'|'positive'|'negative'|'neutral', bandwidth_m, cell_m, levels }
  // → { success, geojson, feature_count, message }（情绪地形 KDE 等值面 mesh：密度×强度）
  const r = await fetch(`${BASE}/spatial/terrain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    let detail = `情绪地形生成失败: ${r.status}`;
    try { const j = await r.json(); detail = j.detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return r.json();
}

export async function runExport(payload) {
  // payload: { geojson, format:'geojson'|'csv'|'shp', crs, geom_csv, desensitize, filename } → Blob
  const r = await fetch(`${BASE}/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    let detail = `导出失败: ${r.status}`;
    try { const j = await r.json(); detail = j.detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return r.blob();
}

// ── 地点搜索 / 地理编码（Phase 2；同源 GET，高德 Key 只在服务端 core/geocode.py）──
//   GET /api/v1/place/search?q=&limit=   → { success, query, hits:[{name,lng,lat,category,zone_name,address,source}], source }
//   GET /api/v1/geocode?q=               → { success, lng, lat, formatted_address, source }
//   GET /api/v1/reverse-geocode?lng=&lat= → { success, zone_id, zone_name, nearest_poi, formatted_address, source }
//   坐标一律 WGS84（高德 GCJ-02 已在服务端 core/geocode.py 转好，红线 #2）。

export async function searchPlaces(q, limit = 10) {
  const url = `${BASE}/place/search?q=${encodeURIComponent(q)}&limit=${limit}`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`地点搜索失败: ${r.status}`);
  return r.json();
}

export async function geocodeAddress(q) {
  const url = `${BASE}/geocode?q=${encodeURIComponent(q)}`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`地理编码失败: ${r.status}`);
  return r.json();
}

export async function reverseGeocode(lng, lat) {
  const url = `${BASE}/reverse-geocode?lng=${lng}&lat=${lat}`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`逆地理编码失败: ${r.status}`);
  return r.json();
}
