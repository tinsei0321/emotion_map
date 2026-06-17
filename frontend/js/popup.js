// ═══ popup.js — top-right detail card (click point) + collapse-to-capsule ═══
// Anchored top-right of #map (follows the right panel). Two states:
//   • expanded — 4 tiers (极性+分数 / 评论 / 位置·类别·坐标 / ID)
//   • collapsed — shrinks to the polarity-color score capsule (badge w/ score)
// Click empty map → collapse; click capsule → expand; click point → new data.
import { POLARITY_LABEL } from './state.js';

const el = () => document.getElementById('feature-popup');

let _last = null;   // {feature, colors, pol, scoreText, label} — drives collapse/expand

/** Show the popup for a clicked feature (expanded, fresh data). */
export function showPopup(feature, colors) {
  const p = feature.properties || {};
  const pol = p.polarity || 'Neutral';
  const label = POLARITY_LABEL[pol] || pol;
  const scoreText = (p.score ?? 0).toFixed(2);
  _last = { feature, colors, pol, scoreText, label };

  const popup = el();
  popup.hidden = false;
  popup.classList.remove('is-collapsed');   // ensure expanded

  const badge = document.getElementById('pp-polarity');
  badge.textContent = label;
  badge.style.background = colors[pol] || colors['Neutral'];

  document.getElementById('pp-score').textContent = scoreText;

  const textEl = document.getElementById('pp-text');
  textEl.textContent = p.text || '';
  textEl.title = p.text || '';               // hover → full text (.popup-text is line-clamped to 2)

  const kv = document.getElementById('pp-kv');
  const rows = [];
  if (p.location)   rows.push(['位置', p.location]);
  if (p.category)   rows.push(['类别', p.category]);
  if (Array.isArray(p.keywords) && p.keywords.length) rows.push(['关键词', p.keywords.join('、')]);
  if (feature.geometry && feature.geometry.coordinates) {
    const c = feature.geometry.coordinates;
    rows.push(['坐标', Array.isArray(c[0]) ? '线/面' : `${c[1].toFixed(4)}, ${c[0].toFixed(4)}`]);
  }
  kv.innerHTML = rows.map(([k, v]) =>
    `<div class="kv-row"><span class="kv-k">${k}</span><span class="kv-v">${v}</span></div>`).join('');

  document.getElementById('pp-id').textContent = p.id_e ? `ID ${p.id_e}` : '';
}

/** Collapse the popup into the polarity-color score capsule (badge shows the score). */
export function collapsePopup() {
  const popup = el();
  if (!popup || popup.hidden || !_last) return;        // nothing visible to collapse
  document.getElementById('pp-polarity').textContent = _last.scoreText;
  popup.classList.add('is-collapsed');
}

/** Expand a collapsed popup (data still in DOM from the last showPopup). */
export function expandPopup() {
  const popup = el();
  if (!popup || popup.hidden || !_last) return;
  document.getElementById('pp-polarity').textContent = _last.label;
  popup.classList.remove('is-collapsed');
}

export function hidePopup() {
  const popup = el();
  if (popup) popup.hidden = true;
}

export function initPopup(map) {
  const popup = el();
  document.getElementById('popup-close').addEventListener('click', hidePopup);
  // click the collapsed capsule → expand
  popup?.addEventListener('click', () => {
    if (popup.classList.contains('is-collapsed')) expandPopup();
  });
  // click empty map area (no rendered feature) → collapse.
  // Guard: ignore clicks that originate on the popup itself (capsule click = expand).
  // NOTE: when range/boundary layers are added later, narrow queryRenderedFeatures
  // to popup-triggering layers so clicking a range line isn't treated as empty.
  if (map) {
    map.on('click', (e) => {
      const tgt = e.originalEvent && e.originalEvent.target;
      if (tgt && tgt.closest && tgt.closest('#feature-popup')) return;
      const feats = map.queryRenderedFeatures(e.point);
      if (!feats || feats.length === 0) collapsePopup();
    });
  }
}
