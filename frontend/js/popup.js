// ═══ popup.js — bottom-right floating detail card (click point/range) ═══
// Replaces the old right-panel "detail" tab. Compact, corner-anchored.
import { POLARITY_LABEL } from './state.js';

const el = () => document.getElementById('feature-popup');

/** Show the popup for a clicked feature (emotion point or range line). */
export function showPopup(feature, colors) {
  const p = feature.properties || {};
  const pol = p.polarity || 'Neutral';
  const popup = el();
  popup.hidden = false;

  const badge = document.getElementById('pp-polarity');
  badge.textContent = POLARITY_LABEL[pol] || pol;
  badge.style.background = colors[pol] || colors['Neutral'];

  document.getElementById('pp-score').textContent = (p.score ?? 0).toFixed(2);
  document.getElementById('pp-text').textContent = p.text || '';

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

export function hidePopup() {
  const popup = el();
  if (popup) popup.hidden = true;
}

export function initPopup() {
  document.getElementById('popup-close').addEventListener('click', hidePopup);
}
