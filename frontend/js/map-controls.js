// ═══ map-controls.js — bottom-left unified cluster + one-segment scale bar ═══
// Cluster (one maplibregl-ctrl-group, geojson.io style): reset / 2D-3D / + / − / north.
// Anchored to #map via addControl('bottom-left') → rides along when the left panel
// folds (same logic as the old native NavigationControl; #map is a flex child that
// grows leftward as --left-w → 0). No --left-w reading needed.
//
// Design language: buttons reuse .maplibregl-ctrl-group button (32×32 white, token
// radius, gray-100 hover) so the whole cluster + the existing zoom buttons share ONE
// hover token → "deepen hover gray" stays a one-line global change (per user rule).
//
// No emoji (CLAUDE.md rule 1): SVG glyphs + ASCII/letters only.

// Fixed pitch per view mode (industry-standard: Mapbox nav / Google Earth city = 60).
// Center + zoom are PRESERVED on toggle (non-jarring; matches Google/Mapbox 2D-3D UX).
const PITCH_2D = 0;
const PITCH_3D = 60;
const TOGGLE_DURATION = 600;   // ms — smooth easeTo
const RESET_DURATION = 800;

// Home view (mirrors map.js YICHANG) — reset target when no data is loaded.
const HOME = { center: [111.286, 30.708], zoom: 12 };

// ── SVG glyphs (currentColor → inherits button color) ──
const ICON_RESET =
  '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true">' +
  '<circle cx="8" cy="8" r="3.2"/><circle cx="8" cy="8" r="0.9" fill="currentColor" stroke="none"/>' +
  '<line x1="8" y1="0.8" x2="8" y2="3.4"/><line x1="8" y1="12.6" x2="8" y2="15.2"/>' +
  '<line x1="0.8" y1="8" x2="3.4" y2="8"/><line x1="12.6" y1="8" x2="15.2" y2="8"/></svg>';

const ICON_NORTH =
  '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">' +
  '<path d="M8 1.5 L11.8 13 L8 10 L4.2 13 Z" fill="currentColor"/></svg>';

// ── geometry helpers ──
function metersPerPixel(map) {
  // Standard Web Mercator ground resolution at the map center, PITCH-INDEPENDENT.
  // (Scale bars show nominal map scale — same as Mapbox/MapLibre native ScaleControl.
  // Using screen unproject would mis-read under 3D tilt, since pitched pixels cover
  // more ground near the horizon than at the view center.)
  const lat = map.getCenter().lat;
  const zoom = map.getZoom();
  return (40075016.686 * Math.abs(Math.cos((lat * Math.PI) / 180))) /
    (256 * Math.pow(2, zoom));
}

/** Pick a "nice" round distance whose pixel width lands in [MIN, MAX] px. */
function niceSegment(mpp) {
  const CANDIDATES = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000];
  const MIN_PX = 60, MAX_PX = 120;
  let chosen = CANDIDATES[0];
  for (const c of CANDIDATES) {
    const px = c / mpp;
    if (px <= MAX_PX) chosen = c;        // largest that still fits under MAX
    if (px >= MIN_PX && px <= MAX_PX) { chosen = c; break; }  // ideal band
  }
  let px = chosen / mpp;
  if (px > MAX_PX) px = MAX_PX;
  if (px < MIN_PX) px = MIN_PX;
  const text = chosen >= 1000 ? (chosen / 1000) + ' km' : chosen + ' m';
  return { px: Math.round(px), text };
}

function featureBounds(fc) {
  let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity;
  for (const f of (fc.features || [])) {
    const c = f.geometry && f.geometry.coordinates;
    if (!c) continue;
    if (f.geometry.type === 'Point') {
      minLng = Math.min(minLng, c[0]); maxLng = Math.max(maxLng, c[0]);
      minLat = Math.min(minLat, c[1]); maxLat = Math.max(maxLat, c[1]);
    }
  }
  if (minLng === Infinity) return null;
  return [[minLng, minLat], [maxLng, maxLat]];
}

// ── build DOM ──
function makeButton(cls, innerHTML, title) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = cls;
  b.title = title;
  b.setAttribute('aria-label', title);
  b.innerHTML = innerHTML;
  return b;
}

/**
 * Build the unified bottom-left control cluster + scale bar as ONE MapLibre control
 * (single addControl call → deterministic DOM order: buttons on top, scale below).
 *
 * @param {maplibregl.Map} map
 * @param {() => object|null} getFC  accessor for current emotion FeatureCollection
 *   (reset uses it to fitBounds to the data; null → fall back to HOME).
 */
export function initControls(map, { getFC } = {}) {
  // root wrapper — owns layout of group + scale; inherits maplibregl-ctrl margins.
  const root = document.createElement('div');
  root.className = 'maplibregl-ctrl emotion-controls-root';

  // ── cluster group (5 buttons, shares geojson.io ctrl-group styling) ──
  const group = document.createElement('div');
  group.className = 'maplibregl-ctrl-group emotion-nav-ctrl';

  const btnReset = makeButton('emotion-ctrl-reset', ICON_RESET, '复位定位 / Reset view');
  const btnView = makeButton('emotion-ctrl-view', '2D', '切换 2D / 3D 视图');
  // plain emotion-* classes (no maplibregl-ctrl-zoom-*) so MapLibre's background-icon
  // CSS doesn't double up with our text "+" / "−".
  const btnZoomIn = makeButton('emotion-ctrl-zoom-in', '+', '放大 / Zoom in');
  const btnZoomOut = makeButton('emotion-ctrl-zoom-out', '−', '缩小 / Zoom out');
  const btnNorth = makeButton('emotion-ctrl-compass', ICON_NORTH, '复北 / Reset north');
  group.append(btnReset, btnView, btnZoomIn, btnZoomOut, btnNorth);

  // ── one-segment scale bar (white, auto-adaptive) ──
  const scale = document.createElement('div');
  scale.className = 'emotion-scale-ctrl';
  scale.innerHTML = '<div class="emotion-scale"><span class="emotion-scale-label">—</span></div>';

  root.append(group, scale);

  // ── behaviors ──
  // zoom +/- and reset-north: functionally equivalent to the removed native NavigationControl.
  btnZoomIn.addEventListener('click', () => map.zoomIn());
  btnZoomOut.addEventListener('click', () => map.zoomOut());
  btnNorth.addEventListener('click', () => map.resetNorth());

  // 2D/3D: preserve center + zoom, animate pitch (0 ⇄ 60) + bearing 0.
  const syncViewLabel = () => {
    const is3D = map.getPitch() > 0.5;
    btnView.textContent = is3D ? '3D' : '2D';
    btnView.classList.toggle('is-active', is3D);
    btnView.setAttribute('aria-pressed', String(is3D));
  };
  btnView.addEventListener('click', () => {
    const to3D = map.getPitch() <= 0.5;
    map.easeTo({
      pitch: to3D ? PITCH_3D : PITCH_2D,
      bearing: 0,
      duration: TOGGLE_DURATION,
    });
  });
  // keep label synced if pitch changes by other means (drag, reset, programmatic).
  map.on('pitchend', syncViewLabel);
  syncViewLabel();

  // reset: one-click locate + ensure layers framed. Fit to data if loaded, else HOME.
  btnReset.addEventListener('click', () => {
    const fc = getFC && getFC();
    const bounds = fc ? featureBounds(fc) : null;
    if (bounds) {
      map.fitBounds(bounds, { padding: 40, pitch: 0, bearing: 0, duration: RESET_DURATION });
    } else {
      map.flyTo({
        center: HOME.center, zoom: HOME.zoom, pitch: 0, bearing: 0, duration: RESET_DURATION,
      });
    }
  });

  // scale: recompute on any move (covers pan / zoom / pitch).
  const label = scale.querySelector('.emotion-scale-label');
  const bar = scale.querySelector('.emotion-scale');
  const updateScale = () => {
    const mpp = metersPerPixel(map);
    if (!isFinite(mpp) || mpp <= 0) return;
    const { px, text } = niceSegment(mpp);
    bar.style.width = px + 'px';
    label.textContent = text;
  };
  map.on('move', updateScale);
  updateScale();

  // expose as a MapLibre control (plain object with onAdd/onRemove is sufficient).
  const control = {
    onAdd() { return root; },
    onRemove() { /* DOM removed by MapLibre; listeners die with the map */ },
    getDefaultPosition() { return 'bottom-left'; },
  };
  map.addControl(control, 'bottom-left');

  return { root, control };
}
