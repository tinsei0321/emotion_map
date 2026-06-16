// ═══ panel.js — right panel: Overview + Table tabs (geojson.io 1:1) ═══
import { POLARITY_ORDER, POLARITY_LABEL } from './state.js';

export function initPanel() {
  document.querySelectorAll('.ptab').forEach((tab) => {
    tab.addEventListener('click', () => activateTab(tab.dataset.tab));
  });
}

export function activateTab(name) {
  document.querySelectorAll('.ptab').forEach((t) =>
    t.classList.toggle('is-active', t.dataset.tab === name));
  document.querySelectorAll('.tab-pane').forEach((p) =>
    p.classList.toggle('is-active', p.dataset.pane === name));
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

/** Fill Overview info card (file / layers / L1 / L2 / total). */
export function setInfoCard({ file, layers, l1, l2, total }) {
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  set('ov-file', file ?? '—');
  set('ov-layers', layers ?? '—');
  set('ov-l1', l1 ?? '—');
  set('ov-l2', l2 ?? '—');
  set('ov-total', total ?? '—');
}

/** Fill Overview: 5 polarity stat cells + mini bar chart + score mean. */
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
  if (wrap) wrap.innerHTML = `<div class="barchart">${bars}</div>`;

  document.getElementById('score-mean').textContent = `均分 ${(scoreMean ?? 0).toFixed(2)}`;
}

/** Fill Table tab with features as a geojson.io-style table. */
export function setTable(fc, maxRows = 200) {
  const colors = readColors();
  const tbl = document.getElementById('data-table');
  const feats = fc.features.slice(0, maxRows);

  const head = `<thead><tr>
    <th>极性</th><th>分数</th><th>文本</th><th>位置</th><th>ID</th>
  </tr></thead>`;

  const body = `<tbody>${feats.map((f) => {
    const p = f.properties || {};
    const pol = p.polarity || 'Neutral';
    const c = colors[pol] || colors['Neutral'];
    const txt = (p.text || '').replace(/[<>]/g, '');
    const loc = (p.location || '').replace(/[<>]/g, '');
    return `<tr>
      <td><span class="td-dot" style="background:${c}"></span>${POLARITY_LABEL[pol] || pol}</td>
      <td>${(p.score ?? 0).toFixed(2)}</td>
      <td>${txt}</td>
      <td>${loc}</td>
      <td>${p.id_e || ''}</td>
    </tr>`;
  }).join('')}</tbody>`;

  tbl.innerHTML = head + body;
}
