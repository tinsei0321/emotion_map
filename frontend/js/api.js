// ═══ api.js — FastAPI backend bridge (Phase 2 wiring; Phase 1 stubs) ═══
// Endpoints (to be added to api/routes.py per migration plan §八):
//   GET  /api/v1/points        → emotion points GeoJSON (?bbox=)
//   GET  /api/v1/points/stats  → polarity stats
//   POST /api/v1/analyze       → run analysis (run_analysis_task)
//   POST /api/v1/governance    → L0→L1 pipeline (run_governance_pipeline)

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
