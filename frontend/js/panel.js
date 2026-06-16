// ═══ panel.js — right editor panel: tabs, collapse, overview, detail card ═══
import { POLARITY_ORDER, POLARITY_LABEL } from './state.js';

export function initPanel() {
  // Tab switching
  document.querySelectorAll('.ptab').forEach((tab) => {
    tab.addEventListener('click', () => activateTab(tab.dataset.tab));
  });

  // Collapse
  const panel = document.getElementById('right-panel');
  const collapseBtn = document.getElementById('panel-collapse');
  const expandBtn = document.getElementById('panel-expand');
  collapseBtn.addEventListener('click', () => {
    panel.classList.add('collapsed');
    expandBtn.hidden = false;
    document.body.classList.add('panel-collapsed');
  });
  expandBtn.addEventListener('click', () => {
    panel.classList.remove('collapsed');
    expandBtn.hidden = true;
    document.body.classList.remove('panel-collapsed');
  });
}

export function activateTab(name) {
  document.querySelectorAll('.ptab').forEach((t) =>
    t.classList.toggle('is-active', t.dataset.tab === name));
  document.querySelectorAll('.tab-pane').forEach((p) =>
    p.classList.toggle('is-active', p.dataset.pane === name));
}

/** Fill overview tab: 5 polarity stat cells + mini bar chart + score mean. */
export function setOverview({ stats, total, scoreMean }) {
  const grid = document.getElementById('polarity-stats');
  const colors = readColors();
  const max = Math.max(1, ...POLARITY_ORDER.map((p) => stats[p] || 0));

  let html = '';
  for (const pol of POLARITY_ORDER) {
    const n = stats[pol] || 0;
    html += `<div class="stat-cell">
      <div class="n"><span class="swatch" style="background:${colors[pol]}"></span>${n}</div>
      <div class="l">${POLARITY_LABEL[pol]}</div>
    </div>`;
  }
  grid.innerHTML = html;

  // mini bar chart (no Chart.js dependency in Phase 1)
  let bars = '';
  for (const pol of POLARITY_ORDER) {
    const n = stats[pol] || 0;
    bars += `<div class="barchart-row">
      <span class="barchart-label">${POLARITY_LABEL[pol]}</span>
      <span class="barchart-track"><span class="barchart-fill" style="width:${(n / max) * 100}%;background:${colors[pol]}"></span></span>
      <span class="barchart-n">${n}</span>
    </div>`;
  }
  const wrap = document.querySelector('.chart-wrap');
  wrap.innerHTML = `<div class="barchart">${bars}</div>`;

  document.getElementById('score-mean').textContent = `均分 ${scoreMean.toFixed(2)}`;
  document.getElementById('record-count').textContent = `共 ${total} 条`;
}

/** Fill detail card from a clicked feature (revives SHELVED F_014). */
export function fillDetail(feature, colors) {
  const p = feature.properties || {};
  const pol = p.polarity || 'Neutral';
  document.getElementById('detail-empty').hidden = true;
  const card = document.getElementById('detail-card');
  card.hidden = false;

  const badge = document.getElementById('d-polarity');
  badge.textContent = POLARITY_LABEL[pol] || pol;
  badge.style.background = colors[pol] || colors['Neutral'];

  document.getElementById('d-score').textContent = (p.score ?? 0).toFixed(2);
  document.getElementById('d-location').textContent = p.location ? `📍 ${p.location}` : '';
  document.getElementById('d-text').textContent = p.text || '';

  const tags = document.getElementById('d-tags');
  tags.innerHTML = p.category ? `<span class="detail-tag">${p.category}</span>` : '';

  document.getElementById('d-keywords').textContent =
    Array.isArray(p.keywords) && p.keywords.length ? `关键词: ${p.keywords.join('、')}` : '';
  document.getElementById('d-id').textContent = p.id_e || '';

  activateTab('detail');
}

function readColors() {
  const g = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  return {
    'Very Positive': g('--geojson-color-emotion-very-positive') || '#78DC32',
    'Positive':      g('--geojson-color-emotion-positive')      || '#5DADE2',
    'Neutral':       g('--geojson-color-emotion-neutral')       || '#C0C0C0',
    'Negative':      g('--geojson-color-emotion-negative')      || '#C4956A',
    'Very Negative': g('--geojson-color-emotion-very-negative') || '#B92D2D',
  };
}
