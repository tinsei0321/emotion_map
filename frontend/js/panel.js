// ═══ panel.js — right panel: Overview (per-layer 3-tier) + Table ═══
import {
  POLARITY_ORDER, POLARITY_LABEL, emotionColors,
  layerLevel, focusLayer, polarityStats, confidenceStats, CONFIDENCE_RAMP,
  L2_POSITIVE, L2_NEGATIVE, L2_NEUTRAL_COLOR,
  EMOTION_TYPE_COLORS, EMOTION_TYPE_ORDER,
  EMOTION_MACRO_ORDER, EMOTION_MACRO_MAP,
  HEATMAP_RAMPS, HOTNESS_RAMP, computeHotness, hotnessBuckets, rampDisplaySegs,
} from './state.js';
import { geomStats, DOMAIN_LABEL, ELEMENT_LABEL } from './popup.js';
import { easeBackFromCell } from './map.js';

export function initPanel() {
  document.querySelectorAll('.ptab').forEach((tab) => {
    tab.addEventListener('click', () => activateTab(tab.dataset.tab));
  });
  // 双层 sub-Tab（图层总览|单元深读）切换
  document.querySelectorAll('.ov-subtab').forEach((tab) => {
    tab.addEventListener('click', () => activateOvTab(tab.dataset.ovtab));
  });
  // 图层总览 issue 项点击 → 深读该单元（cell:selected 统一驱动 zoom + 内容 + 切 sub-Tab）
  const pane = document.getElementById('overview-pane');
  if (pane) {
    pane.addEventListener('click', (e) => {
      const el = e.target.closest('[data-cell-idx]');
      if (!el) return;
      const idx = Number(el.dataset.cellIdx);
      const L = _overviewLayer;
      const f = L && L.fc && L.fc.features && L.fc.features[idx];
      if (!f) return;
      document.dispatchEvent(new CustomEvent('cell:selected', { detail: { feature: f, layer: L } }));
    });
  }
}

export function activateTab(name) {
  document.querySelectorAll('.ptab').forEach((t) =>
    t.classList.toggle('is-active', t.dataset.tab === name));
  document.querySelectorAll('.tab-pane').forEach((p) =>
    p.classList.toggle('is-active', p.dataset.pane === name));
}

// ── Overview: per-selected-layer 3-tier (摘要 / 属性 / 展示) ────────────────
const LEVEL_NAME = { range: '范围', L0: 'L0 · 原始', L1: 'L1 · 治理', L2: 'L2 · 分析' };

let _lastOverviewLayerId = null;   // 识别"换层" → 重置 sub-tab 到图层总览（同层重绘不抖动）

/** Render Overview for a selected layer (or empty state if null).
 *  分析层 = 双层 sub-Tab（图层总览|单元深读）：渲染进 #ov-layer-pane，sub-Tab 可见性按是否分析层切换。
 *  换层（id 变）→ 回「图层总览」sub-tab；同层重绘（paint/visible）→ 保当前 sub-tab 不抖动。 */
export function setOverview(layer) {
  const pane = document.getElementById('ov-layer-pane');
  if (!pane) return;
  if (!layer) {
    _overviewLayer = null; _lastOverviewLayerId = null;
    toggleOvSubtabs(false); activateOvTab('layer', { silent: true });
    pane.innerHTML = emptyState();
    return;
  }
  const focus = focusLayer(layer) || layer;
  _overviewLayer = focus;
  const lv = layerLevel(focus);
  pane.innerHTML = tier1(focus, lv) + tier2(focus, lv) + tier3(focus, lv);
  toggleOvSubtabs(isAnalysisLayer(focus));
  if (focus.id !== _lastOverviewLayerId) activateOvTab('layer');   // 换层 → 回图层总览 + zoom out（若此前在单元深读）
  _lastOverviewLayerId = focus.id;
}

/** 双层 sub-Tab 切换：name='layer'|'cell'。
 *  silent（初始化/换层）不 zoom；否则切到「图层总览」→ easeBackFromCell 抬高视野（"切回上层 zoom out"）。
 *  切到「单元深读」若无内容 → 占位提示（点击网格/柱体后才有深读）。 */
export function activateOvTab(name, opts) {
  const silent = opts && opts.silent;
  document.querySelectorAll('.ov-subtab').forEach((b) => b.classList.toggle('is-active', b.dataset.ovtab === name));
  document.querySelectorAll('.ov-subpane').forEach((p) => p.classList.toggle('is-active', p.dataset.ovpane === name));
  if (name === 'cell') {
    const cp = document.getElementById('ov-cell-pane');
    if (cp && !cp.innerHTML.trim()) cp.innerHTML = cellEmptyHint();
  } else if (!silent) {
    easeBackFromCell();
  }
}

function toggleOvSubtabs(show) {
  const el = document.getElementById('ov-subtabs');
  if (el) el.hidden = !show;
}

function emptyState() {
  return `<div class="ov-empty">
    <div class="ov-empty-title">未加载数据</div>
    <div class="ov-empty-hint">点工具栏 <b>Import</b> 导入文件，或拖放文件到地图</div>
  </div>`;
}

/** 单元深读 sub-Tab 在未选单元时的占位提示。 */
function cellEmptyHint() {
  return `<div class="ov-empty">
    <div class="ov-empty-title">未选中单元</div>
    <div class="ov-empty-hint">点击地图上的 <b>网格 / 柱体</b> 查看该单元的归因深读</div>
  </div>`;
}

/** Overview 单元模式：点击网格/柱体/地形环 → 显示该单元的 4×5 归因深读（识别问题）。
 *  覆盖 setOverview 的层聚合视图；cell:cleared 时由 refreshOverview() 回退。 */
export function setCellOverview(feature, layer) {
  const pane = document.getElementById('ov-cell-pane');
  if (!pane || !feature) return;
  const p = feature.properties || {};
  const ui = (layer && layer.paint && layer.paint._ui) || {};
  const isTerrain = ui.tool === 'terrain';
  const typeWord = isTerrain ? '地形环' : (ui.mode === '3d' ? '柱体' : '网格');
  const pi = p.polarity_index;
  const valence = pi == null ? '中性' : (pi > 0.15 ? '偏积极' : pi < -0.15 ? '偏消极' : '中性');
  const valColor = pi == null ? L2_NEUTRAL_COLOR : (pi > 0.15 ? L2_POSITIVE['Positive'] : pi < -0.15 ? L2_NEGATIVE['Negative'] : L2_NEUTRAL_COLOR);
  const dom = DOMAIN_LABEL[p.domain_top] || p.domain_top || '—';
  const elm = ELEMENT_LABEL[p.element_top] || p.element_top || '—';
  const sizeBit = isTerrain ? '' : `<i>·</i><span>${ui.cellSize ? ui.cellSize + 'm' : ''}</span>`;

  // 同类对比 + 分位：该单元在其 domain×element 桶的均值，及其极性在图层的分位（指向 4×5，递进到微观）。
  const feats = (layer && layer.fc && layer.fc.features) || [];
  const bucket = _matrix4x5(feats)[(p.domain_top || '') + '|' + (p.element_top || '')];
  const meanPi = bucket && bucket.piCnt ? bucket.piSum / bucket.piCnt : null;
  let pct = null;
  if (pi != null && !isNaN(pi)) {
    const all = feats.map((f) => (f.properties || {}).polarity_index).filter((x) => x != null && !isNaN(x));
    if (all.length) pct = Math.round(100 * all.filter((x) => x < pi).length / all.length);
  }

  pane.innerHTML =
    // T1：issue 标题 + domain×element（该单元在 4×5 中的定位）+ 单元类型
    `<div class="ov-tier ov-t1">
       <div class="ov-t1-name" title="${p.issue_label || ''}">${p.issue_label || '情绪聚集区'}</div>
       <div class="ov-t1-meta"><span>${dom} × ${elm}</span><i>·</i><span>${typeWord}</span>${sizeBit}</div>
     </div>`
    // T2：情绪聚类（极性 badge + 综合指数 + 点数/分数/置信度/强度）
    + `<div class="ov-tier ov-t2"><div class="ov-tier-head">情绪聚类</div><div class="ov-props">
        <div class="ov-prop"><span>极性</span><span><span class="ov-swatch" style="background:${valColor}"></span>${valence}</span></div>
        ${pi != null ? `<div class="ov-prop"><span>综合指数</span><span>${Number(pi).toFixed(2)}</span></div>` : ''}
        <div class="ov-prop"><span>情绪点数</span><span>${p.point_count ?? 0}</span></div>
        ${p.score_mean != null ? `<div class="ov-prop"><span>平均分数</span><span>${Number(p.score_mean).toFixed(2)}</span></div>` : ''}
        ${!isTerrain && p.l1_confidence_mean != null ? `<div class="ov-prop" title="L1 治理阶段 LLM 判断的数据相关性置信度（0~1）"><span>置信度</span><span>${Number(p.l1_confidence_mean).toFixed(2)}</span></div>` : ''}
        ${isTerrain && p.emotion_intensity_mean != null ? `<div class="ov-prop"><span>强度均值</span><span>${Number(p.emotion_intensity_mean).toFixed(2)}</span></div>` : ''}
      </div></div>`
    // T3：问题识别 = 归因链 + 同类对比(分位条) + 建议
    + `<div class="ov-tier ov-t3"><div class="ov-tier-head">问题识别</div>
        <div class="ov-cell-attr">${p.attribution || ''}</div>
        ${pi != null && pct != null ? `<div class="ov-cell-where">图层 <b>${dom}×${elm}</b> 桶共 ${bucket ? bucket.n : 0} 单元（均值 <b>${meanPi != null ? meanPi.toFixed(2) : '—'}</b>）；本单元极性超过图层 <b>${pct}%</b> 的单元。
           <div class="ov-pct-track" title="红=偏消极 · 绿=偏积极；三角标 = 本单元位置"><div class="ov-pct-marker" style="left:${pct}%"></div></div></div>` : ''}
        <div class="ov-tier-sub">建议</div>
        <div class="ov-cell-sug">${p.suggestion || ''}</div>
      </div>`;
}

/** T1 摘要：目的(加粗标题) / 数据类型 / 数量；文件名另起一行弱化。
 *  全局规则：Overview 必带数据源文件名。目的 = name 去掉尾部 ' · {src}'；
 *  文件名行仅当标题不是裸文件名时显示（L0/边界 name===src 不重复）。 */
function tier1(layer, lv) {
  const ui = (layer.paint && layer.paint._ui) || {};
  const isAnalysis = layer.kind === 'polygon' && (ui.tool === 'grid' || ui.tool === 'terrain');
  const analysisWord = isAnalysis ? (ui.tool === 'terrain' ? '情绪地形' : (ui.mode === '3d' ? '3D 网格' : '网格聚合')) : null;
  const ext = guessExt(layer.name);
  const ui2 = (layer.paint && layer.paint._ui) || {};
  const isAnalysis2 = layer.kind === 'polygon' && (ui2.tool === 'grid' || ui2.tool === 'terrain');
  const qty = isAnalysis2 ? `${layer.fc.features.length} 单元` : (lv === 'range' ? rangeAreaLabel(layer) : `${layer.fc.features.length} 条`);
  const name = layer.name || '';
  const src = layer.srcName || '';
  let purpose = name;
  if (src && name.endsWith(' · ' + src)) purpose = name.slice(0, name.length - (' · ' + src).length);
  const srcLine = (src && purpose !== src) ? `<div class="ov-t1-src">文件名：${src}</div>` : '';
  const midBadge = isAnalysis2 ? (analysisWord || '分析') : (LEVEL_NAME[lv] || '—');
  return `<div class="ov-tier ov-t1">
    <div class="ov-t1-name" title="${name}">${purpose}</div>
    ${srcLine}
    <div class="ov-t1-meta">
      <span>${ext || '数据'}</span><i>·</i><span>${midBadge}</span><i>·</i><span>${qty}</span>
    </div>
  </div>`;
}

// ── 分析层（grid/zonal/terrain）故事化：极性分布 + 4×5 矩阵 + Top 问题 + 治理要素 ──
const DOMAIN_ORDER = ['urban_planning', 'urban_governance', 'urban_renewal', 'urban_operation'];
const ELEMENT_ORDER = ['facility', 'environment', 'service', 'culture', 'event'];
let _overviewLayer = null;   // setOverview 写入；行点击时回查 feature

function isAnalysisLayer(layer) {
  const ui = layer && layer.paint && layer.paint._ui;
  return !!(layer && layer.kind === 'polygon' && ui && (ui.tool === 'grid' || ui.tool === 'terrain'));
}

/** pi → 红/绿/灰（绿=积极、红=消极、灰=中性；透明度随 |pi|）。 */
function _piColor(pi) {
  if (pi == null || isNaN(pi)) return 'transparent';
  const a = Math.min(1, Math.abs(pi));
  if (pi > 0.15) return `rgba(78, 180, 50, ${0.18 + a * 0.55})`;
  if (pi < -0.15) return `rgba(201, 42, 32, ${0.18 + a * 0.55})`;
  return `rgba(160, 160, 170, ${0.12 + a * 0.3})`;
}

/** 4×5 归因矩阵：{(domain|element): {n, piSum, piCnt}}。 */
function _matrix4x5(feats) {
  const cell = {};
  for (const f of feats) {
    const p = f.properties || {};
    if (!p.domain_top || !p.element_top) continue;
    const k = p.domain_top + '|' + p.element_top;
    if (!cell[k]) cell[k] = { n: 0, piSum: 0, piCnt: 0 };
    cell[k].n++;
    if (p.polarity_index != null && !isNaN(p.polarity_index)) { cell[k].piSum += p.polarity_index; cell[k].piCnt++; }
  }
  return cell;
}

/** Top N 问题聚集 feature（按 |polarity_index| 降序，过滤无极性者）。 */
function _topIssueFeatures(feats, n) {
  return feats.filter((f) => { const pi = (f.properties || {}).polarity_index; return pi != null && !isNaN(pi); })
    .sort((a, b) => Math.abs((b.properties || {}).polarity_index) - Math.abs((a.properties || {}).polarity_index))
    .slice(0, n);
}

function _matrixHtml(cell) {
  const head = `<div class="mx-cell mx-head"></div>` +
    ELEMENT_ORDER.map((e) => `<div class="mx-cell mx-head" title="${ELEMENT_LABEL[e] || e}">${(ELEMENT_LABEL[e] || e).slice(0, 2)}</div>`).join('');
  const rows = DOMAIN_ORDER.map((d) => {
    const cells = ELEMENT_ORDER.map((e) => {
      const c = cell[d + '|' + e];
      if (!c) return `<div class="mx-cell mx-empty" title="${DOMAIN_LABEL[d] || d} × ${ELEMENT_LABEL[e] || e}：无"></div>`;
      const pi = c.piCnt ? c.piSum / c.piCnt : null;
      return `<div class="mx-cell" style="background:${_piColor(pi)}" title="${DOMAIN_LABEL[d] || d} × ${ELEMENT_LABEL[e] || e}：${c.n} 单元 · 极性 ${pi != null ? pi.toFixed(2) : '—'}">${c.n}</div>`;
    }).join('');
    return `<div class="mx-rowlabel" title="${DOMAIN_LABEL[d] || d}">${DOMAIN_LABEL[d] || d}</div>${cells}`;
  }).join('');
  return `<div class="ov-matrix">${head}${rows}</div>`;
}

/** 极性占比 donut（CSS conic-gradient）+ 图例。图层总览总结向（替极性柱状）。 */
function _polarDonut(agg, total) {
  if (!total) return '';
  const segs = [
    [agg['Very Negative'], L2_NEGATIVE['Very Negative']],
    [agg['Negative'], L2_NEGATIVE['Negative']],
    [agg['Neutral'], L2_NEUTRAL_COLOR],
    [agg['Positive'], L2_POSITIVE['Positive']],
    [agg['Very Positive'], L2_POSITIVE['Very Positive']],
  ];
  let acc = 0;
  const stops = [];
  for (const [n, c] of segs) {
    if (n > 0) {
      const a = acc / total * 100, b = (acc + n) / total * 100;
      stops.push(`${c} ${a.toFixed(2)}% ${b.toFixed(2)}%`);
      acc += n;
    }
  }
  const lg = segs.filter(([n]) => n > 0).map(([n, c]) =>
    `<span class="ov-lg"><span class="ov-lg-dot" style="background:${c}"></span>${n}</span>`).join('');
  return `<div class="ov-donut" style="background:conic-gradient(${stops.join(',')})"></div>
    <div class="ov-donut-legend">${lg}</div>`;
}

/** 单 feature bbox（Polygon/MultiPolygon）→ [minLng,minLat,maxLng,maxLat]。 */
function _featBBox(f) {
  const g = f && f.geometry; if (!g) return null;
  let coords = [];
  if (g.type === 'Polygon') coords = g.coordinates[0] || [];
  else if (g.type === 'MultiPolygon') for (const poly of g.coordinates) coords.push(...(poly[0] || []));
  else return null;
  let mnX = Infinity, mxX = -Infinity, mnY = Infinity, mxY = -Infinity;
  for (const [x, y] of coords) { if (x < mnX) mnX = x; if (x > mxX) mxX = x; if (y < mnY) mnY = y; if (y > mxY) mxY = y; }
  if (!isFinite(mnX)) return null;
  return [mnX, mnY, mxX, mxY];
}

/** 治理要素（domain）分布横向柱。 */
function _domainBars(feats) {
  const m = {};
  for (const f of feats) { const d = (f.properties || {}).domain_top; if (d) m[d] = (m[d] || 0) + 1; }
  const entries = DOMAIN_ORDER.filter((d) => m[d]).map((d) => [d, m[d]]);
  if (!entries.length) return `<div class="ov-placeholder muted">无治理要素数据</div>`;
  const max = Math.max(...entries.map((x) => x[1]));
  const bars = entries.map(([d, n]) =>
    `<div class="hbar-row"><span class="hbar-label">${DOMAIN_LABEL[d] || d}</span>
      <span class="hbar-track"><span class="hbar-fill" style="width:${(n / max) * 100}%;background:#4285F4"></span></span>
      <span class="hbar-n">${n}</span></div>`).join('');
  return `<div class="hchart">${bars}</div>`;
}

/** T2 属性：图例/参数（随数据类型） */
function tier2(layer, lv) {
  let body;
  if (isAnalysisLayer(layer)) {
    const ui = layer.paint._ui;
    const feats = layer.fc.features;
    const polLabel = { overall: '综合', positive: '积极', negative: '消极', neutral: '中性' }[ui.polarity] || ui.polarity || '—';
    const sizeTxt = ui.tool === 'terrain' ? 'KDE 等值面' : (ui.analysis === 'zonal' ? '指定单元' : `${ui.cellSize || 400}m 方格`);
    const pis = feats.map((f) => f.properties && f.properties.polarity_index).filter((x) => x != null && !isNaN(x));
    const piMean = pis.length ? (pis.reduce((a, b) => a + b, 0) / pis.length).toFixed(2) : '—';
    body = `<div class="ov-props">
      <div class="ov-prop"><span>层级</span><span>${ui.level || '—'}</span></div>
      <div class="ov-prop"><span>极性</span><span>${polLabel}</span></div>
      <div class="ov-prop"><span>单元</span><span>${sizeTxt}</span></div>
      <div class="ov-prop"><span>模式</span><span>${ui.mode === '3d' ? '3D' : '2D'}</span></div>
      ${ui.maxHeight ? `<div class="ov-prop"><span>最大柱高</span><span>${Math.round(ui.maxHeight)} m</span></div>` : ''}
      <div class="ov-prop"><span>单元数</span><span>${feats.length}</span></div>
      <div class="ov-prop"><span>平均极性</span><span>${piMean}</span></div>
    </div>`;
  } else if (layer.kind === 'heatmap') {
    const p = layer.paint || {};
    const rampName = (HEATMAP_RAMPS[p.rampKey] && HEATMAP_RAMPS[p.rampKey].name) || '—';
    const _hmRamp = (p.rampStops) ? { stops: p.rampStops } : HEATMAP_RAMPS[p.rampKey];
    const rampSegs = rampDisplaySegs(p.rampKey, _hmRamp).map((c) => `<span class="ov-ramp-seg" style="background:${c}"></span>`).join('');
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
  if (isAnalysisLayer(layer)) {
    const feats = layer.fc.features;
    // 极性分布：聚合单元无逐条 polarity，按 n_* 计数汇总（与 popup 同源）
    const agg = { 'Very Positive': 0, Positive: 0, Neutral: 0, Negative: 0, 'Very Negative': 0 };
    let total = 0;
    const sms = [];
    for (const f of feats) {
      const p = f.properties || {};
      agg['Very Positive'] += p.n_very_positive || 0;
      agg.Positive += p.n_positive || 0;
      agg.Neutral += p.n_neutral || 0;
      agg.Negative += p.n_negative || 0;
      agg['Very Negative'] += p.n_very_negative || 0;
      if (p.score_mean != null && !isNaN(p.score_mean)) sms.push(p.score_mean);
    }
    total = agg['Very Positive'] + agg.Positive + agg.Neutral + agg.Negative + agg['Very Negative'];
    const scoreMean = sms.length ? sms.reduce((a, b) => a + b, 0) / sms.length : 0;
    // 4×5 矩阵 + Top 问题 + 治理分布
    const cell = _matrix4x5(feats);
    const top = _topIssueFeatures(feats, 5);
    const issueHtml = top.length
      ? `<ol class="ov-issuelist">${top.map((f, i) => {
          const p = f.properties || {};
          const name = (p.name || p.issue_label || '聚集区').toString().replace(/[<>]/g, '');
          const dom = DOMAIN_LABEL[p.domain_top] || p.domain_top || '—';
          const elm = ELEMENT_LABEL[p.element_top] || p.element_top || '—';
          const idx = feats.indexOf(f);
          const strong = p.polarity_index != null && Math.abs(p.polarity_index) > 0.5;
          return `<li class="ov-issue-item" data-cell-idx="${idx}" title="点击深读该单元（地图随之定位）">
            <span class="oi-rank">${i + 1}</span>
            <span class="oi-name">${name}</span>
            <span class="oi-tag" style="background:${_piColor(p.polarity_index)};color:${strong ? '#fff' : '#404040'}">${Number(p.polarity_index).toFixed(2)}</span>
            <span class="oi-dom">${dom}×${elm}</span>
          </li>`;
        }).join('')}</ol>`
      : `<div class="ov-placeholder muted">无极性数据（L1 热度层无极性指数）</div>`;
    const donutHtml = total ? _polarDonut(agg, total) : '';
    body = `${donutHtml ? `<div class="ov-donut-row">${donutHtml}</div>
        <div class="ov-mean">均分 ${scoreMean.toFixed(2)} · 共 ${total} 条</div>` : ''}
      <div class="ov-tier-sub">4×5 归因矩阵 <span class="ov-tier-hint">绿=积极 · 红=消极</span></div>${_matrixHtml(cell)}
      <div class="ov-tier-sub">Top 5 问题聚集 <span class="ov-tier-hint">点击深读</span></div>${issueHtml}
      <div class="ov-tier-sub">治理要素分布</div>${_domainBars(feats)}`;
  } else if (layer.kind === 'heatmap') {
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

// ── Table tab ── point 层 = geojson.io 风格；分析层（grid/zonal/terrain）= 可排序「问题清单」。
let _issueSort = { key: 'polarity_index', dir: 'desc' };   // 默认按 |极性| 降序（最大张力优先）

export function setTable(fc, layer, maxRows = 200) {
  const tbl = document.getElementById('data-table');
  if (!tbl) return;
  if (layer && isAnalysisLayer(layer)) { _renderIssueTable(tbl, layer, maxRows); return; }
  const colors = emotionColors();
  const feats = (fc && fc.features || []).slice(0, maxRows);
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

/** 分析层「问题清单」可排序表：点表头排序，点行飞到单元 + cell:selected 深读。 */
function _renderIssueTable(tbl, layer, maxRows) {
  const feats = (layer.fc && layer.fc.features) || [];
  const rows = feats.map((f, idx) => ({ f, idx, p: f.properties || {} }));
  const k = _issueSort.key;
  const dir = _issueSort.dir === 'asc' ? 1 : -1;
  rows.sort((a, b) => {
    const va = a.p[k], vb = b.p[k];
    if (k === 'polarity_index' && typeof va === 'number' && typeof vb === 'number')
      return (Math.abs(va) - Math.abs(vb)) * dir;   // 极性按 |值| 排（最大张力优先）
    if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir;
    return String(va ?? '').localeCompare(String(vb ?? '')) * dir;
  });
  const shown = rows.slice(0, maxRows);
  const cols = [
    { key: '_rank', label: '#' },
    { key: 'name', label: '名称' },
    { key: 'point_count', label: '点数' },
    { key: 'polarity_index', label: '极性指数' },
    { key: '_domElm', label: '治理要素' },
    { key: 'issue_label', label: '问题识别' },
  ];
  const arrow = (c) => c.key === k ? (dir > 0 ? ' ▲' : ' ▼') : '';
  const head = `<thead><tr>${cols.map((c) =>
    `<th class="${c.key === k ? 'is-sorted' : ''}" data-sort="${c.key}">${c.label}${arrow(c)}</th>`).join('')}</tr></thead>`;
  const bodyHtml = shown.map((r, i) => {
    const dom = DOMAIN_LABEL[r.p.domain_top] || r.p.domain_top || '—';
    const elm = ELEMENT_LABEL[r.p.element_top] || r.p.element_top || '—';
    const pi = r.p.polarity_index;
    const name = (r.p.name || '').toString().replace(/[<>]/g, '') || '—';
    const issue = (r.p.issue_label || '').toString().replace(/[<>]/g, '') || '—';
    const strong = pi != null && !isNaN(pi) && Math.abs(pi) > 0.5;
    return `<tr data-cell-idx="${r.idx}">
      <td>${i + 1}</td>
      <td>${name}</td>
      <td>${r.p.point_count ?? 0}</td>
      <td>${pi != null && !isNaN(pi) ? `<span class="td-pi" style="background:${_piColor(pi)};color:${strong ? '#fff' : '#404040'}">${pi.toFixed(2)}</span>` : '—'}</td>
      <td>${dom}×${elm}</td>
      <td>${issue}</td>
    </tr>`;
  }).join('');
  tbl.innerHTML = head + `<tbody>${bodyHtml}</tbody>`;

  tbl.querySelectorAll('th[data-sort]').forEach((th) => {
    th.addEventListener('click', () => {
      const key = th.dataset.sort;
      if (key === '_rank' || key === '_domElm') return;
      if (_issueSort.key === key) _issueSort.dir = _issueSort.dir === 'asc' ? 'desc' : 'asc';
      else { _issueSort.key = key; _issueSort.dir = 'desc'; }
      _renderIssueTable(tbl, layer, maxRows);
    });
  });
  tbl.querySelectorAll('tbody tr[data-cell-idx]').forEach((tr) => {
    tr.addEventListener('click', () => {
      const idx = Number(tr.dataset.cellIdx);
      const f = layer.fc.features[idx];
      if (!f) return;
      document.dispatchEvent(new CustomEvent('cell:selected', { detail: { feature: f, layer } }));
    });
  });
}
