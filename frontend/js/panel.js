// ═══ panel.js — right panel: Overview (per-layer 3-tier) + Table ═══
import {
  POLARITY_ORDER, POLARITY_LABEL, emotionColors,
  layerLevel, focusLayer, polarityStats, confidenceStats, CONFIDENCE_RAMP,
  L2_POSITIVE, L2_NEGATIVE, L2_NEUTRAL_COLOR,
} from './state.js';
import { geomStats } from './popup.js';

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

// ── Overview: per-selected-layer 3-tier (摘要 / 属性 / 展示) ────────────────
const LEVEL_NAME = { range: '范围', L0: 'L0 · 原始', L1: 'L1 · 治理', L2: 'L2 · 分析' };

/** Render Overview for a selected layer (or empty state if null). */
export function setOverview(layer) {
  const pane = document.getElementById('overview-pane');
  if (!pane) return;
  if (!layer) { pane.innerHTML = emptyState(); return; }
  // Overview recognizes the BIG level: an L2 child → its parent group's aggregate.
  const focus = focusLayer(layer) || layer;
  const lv = layerLevel(focus);
  pane.innerHTML = tier1(focus, lv) + tier2(focus, lv) + tier3(focus, lv);
}

function emptyState() {
  return `<div class="ov-empty">
    <div class="ov-empty-title">未加载数据</div>
    <div class="ov-empty-hint">点工具栏 <b>Import</b> 导入文件，或拖放文件到地图</div>
  </div>`;
}

/** T1 摘要：文件名+类型 / 图层名 / 数据类型 / 数量或面积 */
function tier1(layer, lv) {
  const ext = guessExt(layer.name);
  const qty = lv === 'range' ? rangeAreaLabel(layer) : `${layer.fc.features.length} 条`;
  return `<div class="ov-tier ov-t1">
    <div class="ov-t1-name" title="${layer.name}">${layer.name}</div>
    <div class="ov-t1-meta">
      <span>${ext || '数据'}</span><i>·</i><span>${LEVEL_NAME[lv] || '—'}</span><i>·</i><span>${qty}</span>
    </div>
  </div>`;
}

/** T2 属性：图例/参数（随数据类型） */
function tier2(layer, lv) {
  let body;
  if (lv === 'range') {
    const p = layer.paint || {};
    body = `<div class="ov-props">
      <div class="ov-prop"><span>轮廓色</span><span class="ov-swatch" style="background:${p.color || '#0c1c2e'}"></span></div>
      <div class="ov-prop"><span>线宽</span><span>${p.lineWidth ?? 2} px</span></div>
      <div class="ov-prop"><span>面域填充</span><span>${p.fillOn ? '开' : '关'}</span></div>
    </div>`;
  } else if (lv === 'L0') {
    body = `<div class="ov-props"><div class="ov-prop"><span>图例</span><span class="ov-swatch" style="background:#a3a3a3"></span> 灰色（原始）</div>
      <div class="ov-prop"><span>下一步</span><span class="ov-tag-blue">需治理</span></div></div>`;
  } else if (lv === 'L1') {
    const p = layer.paint || {};
    const ramp = p.ramp || CONFIDENCE_RAMP;
    body = `<div class="ov-props">
      <div class="ov-prop"><span>置信度色带</span><span class="ov-ramp-legend" style="background:linear-gradient(90deg,${ramp.join(',')})"></span></div>
      <div class="ov-prop"><span>透明度</span><span>${Math.round((p.opacity ?? 0.75) * 100)}%</span></div>
      <div class="ov-prop"><span>下一步</span><span class="ov-tag-blue">可分析</span></div>
    </div>`;
  } else { // L2 — dual palette (Positive green / Negative orange-red / Neutral blue)
    body = `<div class="ov-props">
      <div class="ov-prop"><span>积极色板</span><span><span class="ov-swatch" style="background:${L2_POSITIVE['Very Positive']}"></span><span class="ov-swatch" style="background:${L2_POSITIVE['Positive']}"></span></span></div>
      <div class="ov-prop"><span>消极色板</span><span><span class="ov-swatch" style="background:${L2_NEGATIVE['Negative']}"></span><span class="ov-swatch" style="background:${L2_NEGATIVE['Very Negative']}"></span></span></div>
      <div class="ov-prop"><span>中性</span><span class="ov-swatch" style="background:${L2_NEUTRAL_COLOR}"></span></div>
    </div>`;
  }
  return `<div class="ov-tier ov-t2"><div class="ov-tier-head">数据属性</div>${body}</div>`;
}

/** T3 展示（flex:1 >50%）：治理/分析结论 */
function tier3(layer, lv) {
  let body;
  if (lv === 'range') {
    const st = rangeStats(layer);
    body = `<div class="ov-stats">
      <div class="ov-stat"><span class="ov-stat-n">${st.area.toFixed(2)}</span><span class="ov-stat-l">面积 km²</span></div>
      <div class="ov-stat"><span class="ov-stat-n">${st.perimeter.toFixed(2)}</span><span class="ov-stat-l">周长 km</span></div>
      <div class="ov-stat"><span class="ov-stat-n">${st.vertices}</span><span class="ov-stat-l">顶点</span></div>
    </div>${spatialPlaceholder()}`;
  } else if (lv === 'L0') {
    body = `<div class="ov-placeholder">需先治理（L0→L1）后展示分析结论</div>${spatialPlaceholder()}`;
  } else if (lv === 'L1') {
    const { buckets, total, mean } = confidenceStats(layer.fc);
    const max = Math.max(1, ...buckets);
    const ramp = (layer.paint && layer.paint.ramp) || CONFIDENCE_RAMP;
    const bars = buckets.map((n, i) =>
      `<div class="hbar-row"><span class="hbar-label">${(i * 0.2).toFixed(1)}–${((i + 1) * 0.2).toFixed(1)}</span>
        <span class="hbar-track"><span class="hbar-fill" style="width:${(n / max) * 100}%;background:${ramp[i]}"></span></span>
        <span class="hbar-n">${n}</span></div>`).join('');
    body = `<div class="ov-tier-sub">置信度分布</div><div class="hchart">${bars}</div>
      <div class="ov-mean">均值 ${mean.toFixed(2)} · 共 ${total} 条</div>${spatialPlaceholder()}`;
  } else { // L2 — polarity distribution (aggregate of all sub-layers)
    const { stats, total, scoreMean } = polarityStats(layer.fc);
    const max = Math.max(1, ...POLARITY_ORDER.map((p) => stats[p] || 0));
    const colorOf = (p) => p === 'Very Positive' ? L2_POSITIVE['Very Positive']
      : p === 'Positive' ? L2_POSITIVE['Positive']
      : p === 'Neutral' ? L2_NEUTRAL_COLOR
      : p === 'Negative' ? L2_NEGATIVE['Negative']
      : L2_NEGATIVE['Very Negative'];
    const bars = POLARITY_ORDER.map((p) => {
      const n = stats[p] || 0;
      return `<div class="hbar-row"><span class="hbar-label">${POLARITY_LABEL[p]}</span>
        <span class="hbar-track"><span class="hbar-fill" style="width:${(n / max) * 100}%;background:${colorOf(p)}"></span></span>
        <span class="hbar-n">${n}</span></div>`;
    }).join('');
    body = `<div class="ov-tier-sub">极性分布</div><div class="hchart">${bars}</div>
      <div class="ov-mean">均分 ${scoreMean.toFixed(2)} · 共 ${total} 条</div>${spatialPlaceholder()}`;
  }
  return `<div class="ov-tier ov-t3"><div class="ov-tier-head">数据展示</div>${body}</div>`;
}

/** Placeholder for spatial-analysis conclusions (hotspot / Moran / grid) — filled when Analysis wiring lands. */
function spatialPlaceholder() {
  return `<div class="ov-tier-sub muted">空间分析（热点 Gi* · Moran's I · 网格聚合）待 Analysis 接线</div>`;
}

// ── helpers ──
function guessExt(name) {
  const i = name.lastIndexOf('.');
  return i >= 0 ? name.slice(i + 1).toUpperCase() : '';
}
function rangeAreaLabel(layer) {
  const st = rangeStats(layer);
  return `${st.area.toFixed(2)} km²`;
}
function rangeStats(layer) {
  let area = 0, perimeter = 0, vertices = 0;
  for (const f of layer.fc.features) {
    const s = geomStats(f.geometry);
    area += s.area || 0; perimeter += s.perimeter || 0; vertices += s.vertices || 0;
  }
  return { area, perimeter, vertices };
}

// ── Table tab (kept; geojson.io-style) ──
export function setTable(fc, maxRows = 200) {
  const colors = emotionColors();
  const tbl = document.getElementById('data-table');
  if (!tbl) return;
  const feats = fc.features.slice(0, maxRows);
  const head = `<thead><tr><th>极性</th><th>分数</th><th>文本</th><th>位置</th><th>ID</th></tr></thead>`;
  const body = `<tbody>${feats.map((f) => {
    const p = f.properties || {};
    const pol = p.polarity || 'Neutral';
    const c = colors[pol] || colors['Neutral'];
    const txt = (p.text || '').replace(/[<>]/g, '');
    const loc = (p.location || '').replace(/[<>]/g, '');
    return `<tr><td><span class="td-dot" style="background:${c}"></span>${POLARITY_LABEL[pol] || pol}</td>
      <td>${(p.score ?? 0).toFixed(2)}</td><td>${txt}</td><td>${loc}</td><td>${p.id_e || ''}</td></tr>`;
  }).join('')}</tbody>`;
  tbl.innerHTML = head + body;
}
