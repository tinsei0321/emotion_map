// ═══ panel.js — right panel: Overview (per-layer 3-tier) + Table ═══
import {
  POLARITY_ORDER, POLARITY_LABEL, emotionColors,
  layerLevel, focusLayer, polarityStats, confidenceStats, CONFIDENCE_RAMP,
  L2_POSITIVE, L2_NEGATIVE, L2_NEUTRAL_COLOR,
  EMOTION_TYPE_COLORS, EMOTION_TYPE_ORDER,
  EMOTION_MACRO_ORDER, EMOTION_MACRO_MAP,
  HEATMAP_RAMPS, HOTNESS_RAMP, computeHotness, hotnessBuckets, rampDisplaySegs,
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

/** T1 摘要：目的(加粗标题) / 数据类型 / 数量；文件名另起一行弱化。
 *  全局规则：Overview 必带数据源文件名。目的 = name 去掉尾部 ' · {src}'；
 *  文件名行仅当标题不是裸文件名时显示（L0/边界 name===src 不重复）。 */
function tier1(layer, lv) {
  const ext = guessExt(layer.name);
  const qty = lv === 'range' ? rangeAreaLabel(layer) : `${layer.fc.features.length} 条`;
  const name = layer.name || '';
  const src = layer.srcName || '';
  let purpose = name;
  if (src && name.endsWith(' · ' + src)) purpose = name.slice(0, name.length - (' · ' + src).length);
  const srcLine = (src && purpose !== src) ? `<div class="ov-t1-src">文件名：${src}</div>` : '';
  return `<div class="ov-tier ov-t1">
    <div class="ov-t1-name" title="${name}">${purpose}</div>
    ${srcLine}
    <div class="ov-t1-meta">
      <span>${ext || '数据'}</span><i>·</i><span>${LEVEL_NAME[lv] || '—'}</span><i>·</i><span>${qty}</span>
    </div>
  </div>`;
}

/** T2 属性：图例/参数（随数据类型） */
function tier2(layer, lv) {
  let body;
  // 热力图层优先判断（lv 分支会拦截：L1 彩虹热力图 lv=L1，须先走 heatmap 分支）
  if (layer.kind === 'heatmap') {
    const p = layer.paint || {};
    const rampName = (HEATMAP_RAMPS[p.rampKey] && HEATMAP_RAMPS[p.rampKey].name) || '—';
    const rampSegs = rampDisplaySegs(p.rampKey, HEATMAP_RAMPS[p.rampKey]).map((c) => `<span class="ov-ramp-seg" style="background:${c}"></span>`).join('');
    const macroLabel = (p._ui && Array.isArray(p._ui.macroFilter) ? p._ui.macroFilter : (Array.isArray(p.typesFilter) ? [...new Set(p.typesFilter.map((t) => EMOTION_MACRO_MAP[t]).filter(Boolean))] : []));
    const macros = EMOTION_MACRO_ORDER.filter((m) => macroLabel.includes(m));
    const macroTxt = macros.length === EMOTION_MACRO_ORDER.length ? '全（喜怒哀乐愁急盼）' : (macros.length ? macros.join('、') : '—');
    const microTxt = p.typesFilter === null ? '全（无分类字段）' : (Array.isArray(p.typesFilter) && p.typesFilter.length ? p.typesFilter.join('、') : '全部');
    body = `<div class="ov-props">
      <div class="ov-prop"><span>色带</span><span class="ov-ramp-legend ov-ramp-segmented">${rampSegs}</span> ${rampName}</div>
      <div class="ov-prop"><span>半径</span><span>${p.radius ?? 300} m</span></div>
      <div class="ov-prop"><span>权重字段</span><span>${p.weightField || 'emotion_intensity'}</span></div>
      <div class="ov-prop"><span>情绪类型（大类）</span><span>${macroTxt}</span></div>
      <div class="ov-prop"><span>情绪表现（小类）</span><span>${microTxt}</span></div>
      <div class="ov-prop"><span>数据点</span><span>${layer.fc.features.length}</span></div>
    </div>`;
  } else if (lv === 'range') {
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
    const hotSegs = HOTNESS_RAMP.map(c => `<span class="ov-ramp-seg" style="background:${c}"></span>`).join('');
    const buckets = p.hotnessBuckets || [0.33, 0.66];
    body = `<div class="ov-props">
      <div class="ov-prop"><span>热度值色带（3 段）</span><span class="ov-ramp-legend ov-ramp-segmented">${hotSegs}</span></div>
      <div class="ov-prop" title="热度值 = 情绪强度 × 置信度（0~1），按图层分布动态分 3 段"><span>算法</span><span>强度 × 置信度</span></div>
      <div class="ov-prop"><span>分段阈值</span><span>${buckets[0].toFixed(2)} / ${buckets[1].toFixed(2)}</span></div>
      <div class="ov-prop" title="L1 治理阶段 LLM 判断的数据相关性置信度（0~1）"><span>置信度</span><span>相关性（LLM）</span></div>
      <div class="ov-prop"><span>透明度</span><span>${Math.round((p.opacity ?? 0.75) * 100)}%</span></div>
      <div class="ov-prop"><span>数据点</span><span>${layer.fc.features.length}</span></div>
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
  // 热力图层优先（同 tier2：避免 L1 热力图被 L1 情绪点分支拦截）
  if (layer.kind === 'heatmap') {
    const p = layer.paint || {};
    const n = layer.fc.features.length;
    body = `<div class="ov-stats">
      <div class="ov-stat"><span class="ov-stat-n">${n}</span><span class="ov-stat-l">聚合点</span></div>
      <div class="ov-stat"><span class="ov-stat-n">${p.radius ?? 300}</span><span class="ov-stat-l">半径 m</span></div>
      <div class="ov-stat"><span class="ov-stat-n">${(p.intensity ?? 1).toFixed(1)}</span><span class="ov-stat-l">强度系数</span></div>
    </div><div class="ov-placeholder">核密度可视化 · 颜色越深表示该处情绪点越密集/权重越高 · 详见地图热区</div>${spatialPlaceholder()}`;
  } else if (lv === 'range') {
    const st = rangeStats(layer);
    body = `<div class="ov-stats">
      <div class="ov-stat"><span class="ov-stat-n">${st.area.toFixed(2)}</span><span class="ov-stat-l">面积 km²</span></div>
      <div class="ov-stat"><span class="ov-stat-n">${st.perimeter.toFixed(2)}</span><span class="ov-stat-l">周长 km</span></div>
      <div class="ov-stat"><span class="ov-stat-n">${st.vertices}</span><span class="ov-stat-l">顶点</span></div>
    </div>${spatialPlaceholder()}`;
  } else if (lv === 'L0') {
    body = `<div class="ov-placeholder">需先治理（L0→L1）后展示分析结论</div>${spatialPlaceholder()}`;
  } else if (lv === 'L1') {
    // 热度值分布（3 段，按 hotness buckets）—— 与 popup/图例/弹窗色板同步
    const buckets = (layer.paint && layer.paint.hotnessBuckets) || hotnessBuckets(layer.fc.features);
    const hs = layer.fc.features.map(computeHotness);
    const counts = [
      hs.filter((h) => h <= buckets[0]).length,
      hs.filter((h) => h > buckets[0] && h <= buckets[1]).length,
      hs.filter((h) => h > buckets[1]).length,
    ];
    const total = hs.length;
    const mean = total ? hs.reduce((a, b) => a + b, 0) / total : 0;
    const max = Math.max(1, ...counts);
    const labels = ['低', '中', '高'];
    const bars = counts.map((n, i) =>
      `<div class="hbar-row"><span class="hbar-label">${labels[i]}</span>
        <span class="hbar-track"><span class="hbar-fill" style="width:${(n / max) * 100}%;background:${HOTNESS_RAMP[i]}"></span></span>
        <span class="hbar-n">${n}</span></div>`).join('');
    body = `<div class="ov-tier-sub">热度值分布</div><div class="hchart">${bars}</div>
      <div class="ov-mean">均值 ${mean.toFixed(2)} · 共 ${total} 条</div>${spatialPlaceholder()}`;
  } else { // L2 — polarity distribution + emotion type distribution
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

    // Emotion type distribution (if emotion_type field exists in data)
    const etStats = emotionTypeStats(layer.fc);
    let etBars = '';
    if (etStats.total > 0) {
      const etMax = Math.max(1, ...EMOTION_TYPE_ORDER.map((et) => etStats.stats[et] || 0));
      etBars = EMOTION_TYPE_ORDER.filter((et) => (etStats.stats[et] || 0) > 0).map((et) => {
        const n = etStats.stats[et] || 0;
        const bg = EMOTION_TYPE_COLORS[et] || '#95A5A6';
        return `<div class="hbar-row"><span class="hbar-label">${et}</span>
          <span class="hbar-track"><span class="hbar-fill" style="width:${(n / etMax) * 100}%;background:${bg}"></span></span>
          <span class="hbar-n">${n}</span></div>`;
      }).join('');
    }

    body = `<div class="ov-tier-sub">极性分布</div><div class="hchart">${bars}</div>
      <div class="ov-mean">均分 ${scoreMean.toFixed(2)} · 共 ${total} 条</div>
      ${etBars ? `<div class="ov-tier-sub" style="margin-top:12px">情绪类型分布</div><div class="hchart">${etBars}</div>` : ''}
      ${spatialPlaceholder()}`;
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

/** Compute emotion_type distribution from a FeatureCollection. */
function emotionTypeStats(fc) {
  const stats = {};
  let total = 0;
  for (const f of fc.features) {
    const et = f.properties && f.properties.emotion_type;
    if (et) { stats[et] = (stats[et] || 0) + 1; total++; }
  }
  return { stats, total };
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
