// ═══ api.js — FastAPI backend bridge ═══
// Same-origin: fetches go to /api/v1/* on the frontend server (:8080), which
// serve.py reverse-proxies to the uvicorn backend (:8000). No cross-origin hop
// → no CORS / browser-extension / proxy interference (fix: export "Failed to fetch").
//   GET  /api/v1/points          → emotion points GeoJSON (?bbox=) [stub]
//   POST /api/v1/analyze         → run analysis (run_analysis_task)
//   POST /api/v1/governance      → L0→L1 pipeline (run_governance_pipeline)
//   POST /api/v1/spatial/buffer  → buffer (覆盖范围, EPSG:4546)

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
