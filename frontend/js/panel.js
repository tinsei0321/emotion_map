// ═══ panel.js — right panel: Overview (per-layer 3-tier) + Table ═══
import {
  POLARITY_ORDER, POLARITY_LABEL, emotionColors,
  layerLevel, focusLayer, polarityStats, confidenceStats, CONFIDENCE_RAMP,
  getLayer, getChildren,
  L2_POSITIVE, L2_NEGATIVE, L2_NEUTRAL_COLOR,
  DOMAIN_BAR_COLOR, ELEMENT_BAR_COLOR, POL_MATRIX_TIERS,
  EMOTION_TYPE_COLORS, EMOTION_TYPE_ORDER,
  EMOTION_MACRO_ORDER, EMOTION_MACRO_MAP,
  HEATMAP_RAMPS, HOTNESS_RAMP, computeHotness, hotnessBuckets, rampDisplaySegs, deriveTimeTag, KEYWORD_TABLE,
} from './state.js';
import { geomStats, DOMAIN_LABEL, ELEMENT_LABEL } from './popup.js';
import { easeBackFromCell, fitBoundsTo } from './map.js';
import { highlightCellSet, clearHighlightCellSet, toggleStickyHighlight, resetHighlightCellSet } from './tip-popup.js';

let _infoTipInit = false;
/** "i" 浮动 tooltip 单例（position:fixed，append body）—— 浮于全屏最上层，不被右栏 overflow 裁切（修任务1 bug）。
 *  事件委托 document：任意 .info-i（含未来动态渲染的）hover → 读 data-tip → 按 getBoundingClientRect 定位其上方（放不下翻下方）。 */
function _initInfoTip() {
  if (_infoTipInit) return;
  _infoTipInit = true;
  const tip = document.createElement('div');
  tip.id = 'info-i-tip';
  document.body.appendChild(tip);
  const show = (el) => {
    tip.textContent = el.dataset.tip || '';
    if (!tip.textContent) return;
    const r = el.getBoundingClientRect();
    tip.classList.add('is-show');
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    const vw = window.innerWidth;
    let left = r.left + r.width / 2 - tw / 2;
    let top = r.top - th - 6;                    // 默认上方
    if (top < 8) top = r.bottom + 6;             // 上方放不下 → 下方
    left = Math.max(8, Math.min(left, vw - tw - 8));
    tip.style.left = Math.round(left) + 'px';
    tip.style.top = Math.round(top) + 'px';
  };
  const hide = () => tip.classList.remove('is-show');
  document.addEventListener('mouseover', (e) => { const el = e.target.closest && e.target.closest('.info-i'); if (el) show(el); });
  document.addEventListener('mouseout', (e) => { if (e.target.closest && e.target.closest('.info-i')) hide(); });
}

export function initPanel() {
  _initInfoTip();
  document.querySelectorAll('.ptab').forEach((tab) => {
    tab.addEventListener('click', () => activateTab(tab.dataset.tab));
  });
  // 双层 sub-Tab（图层总览|单元深读）切换
  document.querySelectorAll('.ov-subtab').forEach((tab) => {
    tab.addEventListener('click', () => activateOvTab(tab.dataset.ovtab));
  });
  // 数据分析 hover/click → 地图同步高亮（饼图 slice / 矩阵格 / 关键词 统一设计语言）。
  // 悬停=试探（瞬时，leave 回 sticky/清）；点击=锁定 sticky（再点/点异项切换释放）。
  const pane = document.getElementById('overview-pane');
  if (pane) {
    pane.addEventListener('mouseover', (e) => {
      if (!_overviewLayer) return;
      const sl = e.target.closest('.ov-pie-slice');
      if (sl) { highlightCellSet(_cellsByPolarity(_overviewLayer.fc.features, sl.dataset.pol), _overviewLayer); return; }
      const mx = e.target.closest('.mx-cell[data-dom]');
      if (mx) { highlightCellSet(_cellsByBucket(_overviewLayer.fc.features, mx.dataset.dom, mx.dataset.elm), _overviewLayer); return; }
      const kw = e.target.closest('.ov-kw-item');
      if (kw) { const r = _topKeywordCells(_overviewLayer.fc.features, kw.dataset.topic, 10); if (r.cells.length) highlightCellSet(r.cells, _overviewLayer); return; }
    });
    pane.addEventListener('mouseout', (e) => {
      if (e.target.closest('.ov-pie-slice') || e.target.closest('.mx-cell[data-dom]') || e.target.closest('.ov-kw-item')) clearHighlightCellSet();
    });
    pane.addEventListener('click', (e) => {
      if (!_overviewLayer) return;
      // 饼图 slice → 锁定/释放该极性主导格
      const sl = e.target.closest('.ov-pie-slice');
      if (sl) {
        const cells = _cellsByPolarity(_overviewLayer.fc.features, sl.dataset.pol);
        const locked = toggleStickyHighlight(cells, _overviewLayer, 'pol:' + sl.dataset.pol);
        const svg = sl.closest('svg');
        if (svg) svg.querySelectorAll('.ov-pie-slice').forEach((s) => s.classList.remove('is-sticky'));
        if (locked) sl.classList.add('is-sticky');
        return;
      }
      // 矩阵格 → 锁定/释放该 domain×element 桶
      const mx = e.target.closest('.mx-cell[data-dom]');
      if (mx) {
        const cells = _cellsByBucket(_overviewLayer.fc.features, mx.dataset.dom, mx.dataset.elm);
        const locked = toggleStickyHighlight(cells, _overviewLayer, 'mx:' + mx.dataset.dom + '|' + mx.dataset.elm);
        const mtx = mx.closest('.ov-matrix');
        if (mtx) mtx.querySelectorAll('.mx-cell.is-sticky').forEach((c) => c.classList.remove('is-sticky'));
        if (locked) mx.classList.add('is-sticky');
        return;
      }
      // 关键词 → top-N 最强聚集格 sticky + fitBounds（再点释放）
      const kw = e.target.closest('.ov-kw-item');
      if (kw) {
        const r = _topKeywordCells(_overviewLayer.fc.features, kw.dataset.topic, 10);
        if (r.cells.length) {
          const key = 'kw:' + kw.dataset.topic;
          const locked = toggleStickyHighlight(r.cells, _overviewLayer, key);
          const wrap = kw.closest('.ov-keywords');
          if (wrap) wrap.querySelectorAll('.ov-kw-item.is-sticky').forEach((x) => x.classList.remove('is-sticky'));
          if (locked) { kw.classList.add('is-sticky'); if (r.bb) fitBoundsTo(r.bb, 120, 15); }
        }
        return;
      }
      // issue 行点击 → cell:selected 深读（地图随之定位）
      const el = e.target.closest('[data-cell-idx]');
      if (!el) return;
      const idx = Number(el.dataset.cellIdx);
      const L = _overviewLayer;
      const f = L && L.fc && L.fc.features && L.fc.features[idx];
      if (!f) return;
      document.dispatchEvent(new CustomEvent('cell:selected', { detail: { feature: f, layer: L } }));
    });
    // 进入单元深读 → 同步取消饼图/矩阵/关键词的 sticky 选中态（任务9：上一层 sticky 同步取消）
    document.addEventListener('cell:selected', () => {
      pane.querySelectorAll('.is-sticky').forEach((el) => el.classList.remove('is-sticky'));
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
    resetHighlightCellSet();   // 回「图层总览」→ 清单元聚焦橙柱（任务9）
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
/** 标题板块：单行关键信息「数据类型·极性·时间点·分析类型·主要参数」（不显文件名）。
 *  L2 综合标准网格 → "L2·综合·T3·标准网格·400m"；非分析层同范式按类型给。 */
const LEVEL_SHORT = { L0: 'L0', L1: 'L1', L2: 'L2', range: 'Range' };
function tier1(layer, lv) {
  const ui = (layer.paint && layer.paint._ui) || {};
  const analysis = isAnalysisLayer(layer);
  const parts = [];
  parts.push(LEVEL_SHORT[lv] || lv || '—');
  // 极性/语义
  if (analysis) parts.push(POLARITY_LABEL[ui.polarity] || '综合');
  else if (lv === 'L1') parts.push('热度');
  else if (lv === 'L2') parts.push('情绪');
  else if (lv === 'range') parts.push('范围');
  // 时间点
  const t = deriveTimeTag(layer.fc);
  if (t) parts.push(t);
  // 分析类型 + 主要参数
  if (analysis) {
    parts.push(ui.tool === 'terrain' ? '情绪地形' : (ui.analysis === 'zonal' ? '指定单元' : '标准网格'));
    if (ui.tool !== 'terrain' && ui.analysis === 'square' && ui.cellSize) parts.push(ui.cellSize + 'm');
    if (ui.tool === 'terrain' && ui.radius) parts.push(ui.radius + 'm');
  } else if (lv === 'range') {
    parts.push(rangeAreaLabel(layer));
  } else {
    parts.push(`${layer.fc.features.length} 条`);
  }
  return `<div class="ov-tier ov-t1"><div class="ov-t1-name">${parts.join('·')}</div></div>`;
}

// ── 分析层（grid/zonal/terrain）故事化：极性分布 + 4×5 矩阵 + Top 问题 + 治理要素 ──
const DOMAIN_ORDER = ['urban_planning', 'urban_renewal', 'urban_operation', 'urban_governance'];
const ELEMENT_ORDER = ['facility', 'environment', 'service', 'culture', 'event'];
let _overviewLayer = null;   // setOverview 写入；行点击时回查 feature

function isAnalysisLayer(layer) {
  const ui = layer && layer.paint && layer.paint._ui;
  return !!(layer && layer.kind === 'polygon' && ui && (ui.tool === 'grid' || ui.tool === 'terrain'));
}

/** pi → 发散色（积极=绿 / 消极=红 / 中性=蓝，活泼高级；透明度随 |pi|）。
 *  参考 Material 600：绿 #43A047、红 #E53935、蓝 #1E88E5。中性用蓝（非灰）。 */
function _piColor(pi) {
  if (pi == null || isNaN(pi)) return 'transparent';
  const a = Math.min(1, Math.abs(pi) / 1.2);   // /1.2 让中等值也较饱和
  if (pi > 0.15) return `rgba(67, 160, 71, ${0.32 + a * 0.58})`;    // 积极 绿
  if (pi < -0.15) return `rgba(229, 57, 53, ${0.32 + a * 0.58})`;   // 消极 红
  return `rgba(30, 136, 229, ${0.22 + a * 0.46})`;                  // 中性 蓝
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

/** 桶内格（含 domain D 点 && 含 element E 点，按 n_dom_D+n_elem_E 降序 Top30）——矩阵格 hover/click → 地图同步。
 *  用"含"替旧"domain_top 众数主导"，让矩阵桶覆盖关键 POI：关键 POI cell domain_top 多为 operation，
 *  但含 planning/renewal 点（各 247/374 cell），改"含"后这些 cell 进规划/更新桶，演示讲解可指向关键 POI。 */
function _cellsByBucket(feats, d, e, limit = 30) {
  return feats.map((f) => {
    const p = f.properties || {};
    return { f, sc: (p['n_dom_' + d] || 0) + (p['n_elem_' + e] || 0) };
  }).filter((x) => x.sc > 0).sort((a, b) => b.sc - a.sc).slice(0, limit).map((x) => x.f);
}

function _matrixHtml(cell) {
  const head = `<div class="mx-cell mx-head"></div>` +
    ELEMENT_ORDER.map((e) => `<div class="mx-cell mx-head" title="${ELEMENT_LABEL[e] || e}">${(ELEMENT_LABEL[e] || e).slice(0, 2)}</div>`).join('');
  const rows = DOMAIN_ORDER.map((d) => {
    const cells = ELEMENT_ORDER.map((e) => {
      const c = cell[d + '|' + e];
      const lbl = `${DOMAIN_LABEL[d] || d} × ${ELEMENT_LABEL[e] || e}`;
      if (!c) return `<div class="mx-cell mx-empty" title="${lbl}：无"></div>`;
      const pi = c.piCnt ? c.piSum / c.piCnt : null;
      return `<div class="mx-cell" data-dom="${d}" data-elm="${e}" style="background:${_piColor(pi)}" title="${lbl}：${c.n} 单元 · 极性 ${pi != null ? pi.toFixed(2) : '—'}（悬停/点击 → 地图同步）">${c.n}</div>`;
    }).join('');
    return `<div class="mx-rowlabel" title="${DOMAIN_LABEL[d] || d}">${DOMAIN_LABEL[d] || d}</div>${cells}`;
  }).join('');
  return `<div class="ov-matrix">${head}${rows}</div>`;
}

/** 极性 → 该极性点数 property 字段。 */
const _POL_FIELDS = { 'Very Negative': 'n_very_negative', 'Negative': 'n_negative', 'Neutral': 'n_neutral', 'Positive': 'n_positive', 'Very Positive': 'n_very_positive' };

/** feature 的主导极性（n_* 最大桶）——饼图 slice → 地图高亮用。 */
function _dominantPolarityOf(f) {
  const p = f.properties || {};
  let best = null, bestN = -1;
  for (const [key, fld] of Object.entries(_POL_FIELDS)) {
    const n = p[fld] || 0;
    if (n > bestN) { bestN = n; best = key; }
  }
  return best;
}
/** 饼图 slice → 地图高亮格：格被选中当且仅当「该极性点数 > 阈值（积极/消极>10、中性>1）**且** 该极性占比 > 40%」。
 *  避免选中所有相关格（过多失意义）；阈值/比例常量化便于调。 */
const POL_SELECT_MIN = { pos: 10, neg: 10, neu: 1 };
const POL_SELECT_RATIO = 0.4;
const _POLKEY_SIGN = { 'Very Positive': 'pos', 'Positive': 'pos', 'Neutral': 'neu', 'Negative': 'neg', 'Very Negative': 'neg' };
function _cellsByPolarity(feats, polKey) {
  const fld = _POL_FIELDS[polKey];
  const min = POL_SELECT_MIN[_POLKEY_SIGN[polKey] || 'neu'];
  const out = [];
  for (const f of feats) {
    const p = f.properties || {};
    const n = p[fld] || 0;
    const pc = p.point_count || 0;
    if (n > min && (pc > 0 ? n / pc : 0) > POL_SELECT_RATIO) out.push(f);
  }
  return out;
}

/** 5 极性饼图（SVG path arc；悬停 pop-out + 地图同步高亮主导格）。
 *  slice 载 data-pol + --dx/--dy（pop-out 径向位移，CSS :hover/.is-sticky 触发）。 */
function _polarPieHtml(agg, total) {
  if (!total) return '';
  const SEGS = [
    ['Very Negative', L2_NEGATIVE['Very Negative']],
    ['Negative', L2_NEGATIVE['Negative']],
    ['Neutral', L2_NEUTRAL_COLOR],
    ['Positive', L2_POSITIVE['Positive']],
    ['Very Positive', L2_POSITIVE['Very Positive']],
  ];
  const cx = 50, cy = 50, r = 38;
  let a = -Math.PI / 2;
  const paths = [];
  for (const [key, color] of SEGS) {
    const n = agg[key] || 0;
    if (n <= 0) continue;
    const sweep = (n / total) * Math.PI * 2;
    const a0 = a, a1 = a + sweep, am = (a0 + a1) / 2;
    const x0 = cx + r * Math.cos(a0), y0 = cy + r * Math.sin(a0);
    const x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1);
    const large = sweep > Math.PI ? 1 : 0;
    const dx = Math.cos(am) * 5, dy = Math.sin(am) * 5;
    paths.push(`<path class="ov-pie-slice" data-pol="${key}" fill="${color}" style="--dx:${dx.toFixed(1)}px;--dy:${dy.toFixed(1)}px" d="M${cx} ${cy} L${x0.toFixed(2)} ${y0.toFixed(2)} A${r} ${r} 0 ${large} 1 ${x1.toFixed(2)} ${y1.toFixed(2)} Z"><title>${POLARITY_LABEL[key]} · ${n}（${(n / total * 100).toFixed(0)}%）</title></path>`);
    a = a1;
  }
  const lg = SEGS.filter(([k]) => (agg[k] || 0) > 0).map(([k, c]) =>
    `<span class="ov-pie-lg"><span class="ov-pie-dot" style="background:${c}"></span>${POLARITY_LABEL[k]}<i>${agg[k]}</i></span>`).join('');
  return `<div class="ov-pie-block"><div class="ov-pie"><svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">${paths.join('')}</svg></div>
    <div class="ov-pie-legend">${lg}</div></div>`;
}

/** 通用横条图（4 领域 / 5 要素）：全称 label + 加粗 + 指定色 + 数字入条，track 填满到右沿。
 *  item 2 综合 4 领域用 DOMAIN_BAR_COLOR；item 5 单极性 4 领域 + 4 要素各用其色。 */
function _barsHtml(feats, kind, color) {
  const order = kind === 'element' ? ELEMENT_ORDER : DOMAIN_ORDER;
  const labelOf = kind === 'element' ? ((k) => ELEMENT_LABEL[k] || k) : ((k) => DOMAIN_LABEL[k] || k);
  const field = kind === 'element' ? 'element_top' : 'domain_top';
  const m = {};
  for (const f of feats) { const v = (f.properties || {})[field]; if (v) m[v] = (m[v] || 0) + 1; }
  const entries = order.filter((k) => m[k]).map((k) => [k, m[k]]);
  if (!entries.length) return `<div class="ov-placeholder muted">无${kind === 'element' ? '要素' : '治理领域'}数据</div>`;
  const max = Math.max(...entries.map((x) => x[1]));
  return entries.map(([k, n]) =>
    `<div class="ov-dbar"><span class="ov-dbar-label">${labelOf(k)}</span>
      <span class="ov-dbar-track"><span class="ov-dbar-fill" style="width:${(n / max) * 100}%;background:${color}">${n}</span></span></div>`
  ).join('');
}
/** 综合 4 领域柱（#4876FF，全称加粗）。 */
function _domainBarsCompact(feats) { return _barsHtml(feats, 'domain', DOMAIN_BAR_COLOR); }
/** 单极性 4 要素柱（#836FFF）。 */
function _elementBars(feats) { return _barsHtml(feats, 'element', ELEMENT_BAR_COLOR); }

/** 单极性网格层（L2 grid 且 polarity !== 'overall'）。 */
function _isSinglePol(ui) {
  return !!(ui && ui.tool === 'grid' && ui.level === 'L2' && ui.polarity && ui.polarity !== 'overall');
}

/** 单极性归因矩阵：只显该极性分布，格色按本矩阵 count 三级（high#6A5ACD/mid#7B68EE/low#8470FF）。
 *  不再用 _piColor（极性色）—— 单极性层极性已定，矩阵强调"哪些 domain×element 桶最多"。 */
function _singlePolMatrixHtml(cell) {
  // 三分位梯度：按本矩阵实际 count 分布取 1/3、2/3 分位赋 high/mid/low，保证三色各占约 1/3 格。
  // 修旧 bug：n/max>0.66 阈值在长尾数据（如 max=591、余皆<33%·max）下 mid 永空，全矩阵仅深浅两色。
  const ns = Object.values(cell).map((c) => c.n || 0).filter((n) => n > 0).sort((a, b) => a - b);
  const tierColor = (n) => {
    if (!n || n <= 0 || !ns.length) return POL_MATRIX_TIERS.low;
    if (ns.length < 3) return n >= ns[ns.length - 1] ? POL_MATRIX_TIERS.high : POL_MATRIX_TIERS.low;
    let i = 0; while (i < ns.length && ns[i] < n) i++;   // n 在排序数组中的分位
    const q = i / (ns.length - 1);
    return q > 2 / 3 ? POL_MATRIX_TIERS.high : q > 1 / 3 ? POL_MATRIX_TIERS.mid : POL_MATRIX_TIERS.low;
  };
  const head = `<div class="mx-cell mx-head"></div>` +
    ELEMENT_ORDER.map((e) => `<div class="mx-cell mx-head" title="${ELEMENT_LABEL[e] || e}">${(ELEMENT_LABEL[e] || e).slice(0, 2)}</div>`).join('');
  const rows = DOMAIN_ORDER.map((d) => {
    const cells = ELEMENT_ORDER.map((e) => {
      const c = cell[d + '|' + e];
      const lbl = `${DOMAIN_LABEL[d] || d} × ${ELEMENT_LABEL[e] || e}`;
      if (!c) return `<div class="mx-cell mx-empty" title="${lbl}：无"></div>`;
      return `<div class="mx-cell" data-dom="${d}" data-elm="${e}" style="background:${tierColor(c.n)}" title="${lbl}：${c.n} 单元（悬停/点击 → 地图同步）">${c.n}</div>`;
    }).join('');
    return `<div class="mx-rowlabel" title="${DOMAIN_LABEL[d] || d}">${DOMAIN_LABEL[d] || d}</div>${cells}`;
  }).join('');
  return `<div class="ov-matrix">${head}${rows}</div>`;
}

/** 单极性关键词：该极性 Top10 主题词 + 右侧聚集地点（顿号横排，省空间）。
 *  词来自点的 topic_top（数据层提炼，performance_config.TOPIC_TABLE）；count=point_count 加权；
 *  地点=_topKeywordCells 按 topic 筛出的格 place_name Top8（去重）。 */
const _POL_SIGN = { positive: 'pos', negative: 'neg', neutral: 'neu' };
/** 主题词→极性 + 用户词序（与 performance_config.TOPIC_TABLE 同源；前端按 topic 聚合后分极性 + 定序）。 */
const TOPIC_POLARITY = {
  '网红': 'pos', '夜经济': 'pos', '滨江步道': 'pos', '15分钟生活区': 'pos', '文化活动': 'pos',
  '老街新生': 'pos', '加装电梯': 'pos', '绿道成网': 'pos', '一路绿波': 'pos', '微更新活化': 'pos',
  '停车难': 'neg', '噪音': 'neg', '堵车': 'neg', '底商空置冷清': 'neg', '红绿灯': 'neg',
  '施工扰民': 'neg', '没电梯': 'neg', '办事难': 'neg', '内涝积水': 'neg', '垃圾乱扔': 'neg',
  '口袋公园': 'neu', '业态': 'neu', '社区服务配套': 'neu', '物业': 'neu', '老街改造': 'neu',
  '盼电梯': 'neu', '规划绿地': 'neu', '业态调整': 'neu', '盼BRT': 'neu', '社区营造': 'neu',
};
const TOPIC_ORDER = {
  pos: ['网红', '夜经济', '滨江步道', '15分钟生活区', '文化活动', '老街新生', '加装电梯', '绿道成网', '一路绿波', '微更新活化'],
  neg: ['停车难', '噪音', '堵车', '底商空置冷清', '红绿灯', '施工扰民', '没电梯', '办事难', '内涝积水', '垃圾乱扔'],
  neu: ['口袋公园', '业态', '社区服务配套', '物业', '老街改造', '盼电梯', '规划绿地', '业态调整', '盼BRT', '社区营造'],
};
function _singlePolKeywordsHtml(feats, polarity) {
  const sign = _POL_SIGN[polarity] || 'pos';
  const rank = _keywordRank(feats)[sign] || [];
  if (!rank.length) return `<div class="ov-placeholder muted">无该极性关键词数据</div>`;
  const max = Math.max(1, ...rank.map((x) => x.n));
  const rows = rank.map((it) => {
    const r = _topKeywordCells(feats, it.topic, 10);
    const locs = r.cells.map((f) => {
      const p = f.properties || {};
      return p.place_name || p.area_seed || p.spatial_hotspot || p.zone || '';
    }).filter((x) => x && x !== 'general')
      .filter((x, i, arr) => arr.indexOf(x) === i)
      .slice(0, 8);
    const locHtml = locs.length
      ? `<div class="ov-kw-locs">${locs.join('、')}</div>`
      : `<div class="ov-kw-locs muted">—</div>`;
    return `<div class="ov-kw-item ov-kw-sp" data-topic="${it.topic}" data-sign="${sign}" title="${it.topic}（${it.n} 点）· 点击定位最强聚集">
      <span class="ov-kw-fill" style="width:${Math.max(20, (it.n / max) * 100)}%"></span>
      <div class="ov-kw-left"><span class="ov-kw-word">${it.topic}</span>
        <span class="ov-kw-num">${it.n}</span></div>
      ${locHtml}
    </div>`;
  }).join('');
  return `<div class="ov-keywords ov-keywords-sp">${rows}</div>`;
}

/** 单极性 Overview body：极性点数总览 + (4 领域 + 4 要素 横条) + 归因矩阵 + 关键词。 */
/** 反查 _ui.source（group:{gid}）的城市情绪总量 = group 全部极性子层点数之和。layer: 源/反查失败 → null。 */
function _cityTotalOf(ui) {
  const src = ui && ui.source;
  if (!src) return null;
  const m = String(src).match(/^group:(.+)$/);
  if (!m) return null;
  const g = getLayer(m[1]);
  if (!g) return null;
  let n = 0;
  for (const c of getChildren(g.id)) n += (c.fc && c.fc.features && c.fc.features.length) || 0;
  return n || null;
}

/** 单极性 Overview body：极性点数总览 + (4 领域 + 4 要素 横条) + 归因矩阵 + 关键词。 */
function _singlePolBody(feats, ui) {
  const pol = ui.polarity;
  const polLabel = POLARITY_LABEL[{ positive: 'Positive', negative: 'Negative', neutral: 'Neutral' }[pol]] || '极性';
  // 该极性点数 = Σ（主级 + 非常级）；neutral 无非常级。修旧 bug：只算主级桶漏 Very Negative 致 vn>total。
  let total = 0;
  for (const f of feats) {
    const p = f.properties || {};
    if (pol === 'positive') total += (p.n_positive || 0) + (p.n_very_positive || 0);
    else if (pol === 'negative') total += (p.n_negative || 0) + (p.n_very_negative || 0);
    else total += p.n_neutral || 0;
  }
  const cell = _matrix4x5(feats);
  const cityTotal = _cityTotalOf(ui);
  const yPct = (cityTotal && total) ? Math.round(total / cityTotal * 100) : null;
  const countLine = total
    ? `<div class="ov-count-line">偏<b>${polLabel}</b>的情绪点数为 <b>${total}</b> 个${yPct != null ? `，占城市情绪总量的 <b>${yPct}%</b>` : ''}</div>` : '';
  return `${countLine}
    <div class="ov-tier-sub">极性总览<span class="info-i" data-tip="本层为单极性聚合。4 领域（蓝 #4876FF）+ 4 要素（紫 #836FFF）分布；横条长度 = 该层该类计数。">i</span></div>
    <div class="ov-overview-row ov-ov-bars-row"><div class="ov-domain-chart">${_domainBarsCompact(feats)}</div><div class="ov-domain-chart">${_elementBars(feats)}</div></div>
    <div class="ov-tier-sub">归因矩阵<span class="info-i" data-tip="单极性矩阵：颜色按本矩阵数量三级（深紫最多 → 浅紫最少），强调该极性问题集中在哪些领域×要素。悬停/点击 → 地图同步。">i</span></div>${_singlePolMatrixHtml(cell)}
    <div class="ov-tier-sub">关键词 Top10<span class="info-i" data-tip="该极性高频城市关键词（左 1/3：词+次数）及其代表性地点 Top5（右 2/3）。点击词 → 定位最强聚集。">i</span></div>${_singlePolKeywordsHtml(feats, pol)}`;
}

/** 关键词频次排名：按点的 topic_top（数据层提炼）聚合 point_count → {sign: [{topic, n}]}。
 *  按 TOPIC_ORDER 用户词序优先 + 频次排序，每极性 Top10。替旧"4×5 桶映射"。 */
function _keywordRank(feats) {
  const m = {};   // topic -> n (point_count 加权)
  for (const f of feats) {
    const p = f.properties || {};
    const t = p.topic_top;
    if (!t) continue;
    m[t] = (m[t] || 0) + (p.point_count || 0);
  }
  const bySign = { pos: [], neu: [], neg: [] };
  for (const [t, n] of Object.entries(m)) {
    const sign = TOPIC_POLARITY[t];
    if (!sign) continue;   // 未登记 topic 忽略（长尾）
    bySign[sign].push({ topic: t, n });
  }
  // 按数据频次降序（需求4：数据与指定排序冲突时按数据，从高到低、从上到下）
  const sorted = (sign) => bySign[sign].sort((a, b) => b.n - a.n).slice(0, 10);
  return { pos: sorted('pos'), neu: sorted('neu'), neg: sorted('neg') };
}

/** sign → 极性标题。 */
const KW_SIGN_HEAD = { pos: '正面/积极', neu: '中性/期盼', neg: '负面/消极' };

/** 综合·网格关键词 HTML：正/中/负三列，每条 = 主题词 + 次数（整卡填充，词白字/数字深灰）；点击 → 定位该词最强聚集。 */
function _keywordsHtml(feats) {
  const { pos, neu, neg } = _keywordRank(feats);
  if (!pos.length && !neu.length && !neg.length) return `<div class="ov-placeholder muted">无关键词数据</div>`;
  const col = (items, sign) => {
    if (!items.length) return `<div class="ov-kw-col"><div class="ov-kw-col-head">${KW_SIGN_HEAD[sign]}</div><div class="ov-placeholder muted">—</div></div>`;
    const max = Math.max(1, ...items.map((x) => x.n));
    const rows = items.map((it) =>
      `<div class="ov-kw-item" data-topic="${it.topic}" data-sign="${sign}" title="${it.topic}（${it.n} 点）· 点击定位最强聚集">
        <span class="ov-kw-fill" style="width:${Math.max(15, (it.n / max) * 100)}%"></span>
        <span class="ov-kw-word">${it.topic}</span>
        <span class="ov-kw-num">${it.n}</span>
      </div>`).join('');
    return `<div class="ov-kw-col"><div class="ov-kw-col-head">${KW_SIGN_HEAD[sign]}</div>${rows}</div>`;
  };
  return `<div class="ov-keywords">${col(pos, 'pos')}${col(neu, 'neu')}${col(neg, 'neg')}</div>`;
}

/** 该主题词(topic)下 point_count top-N（默认 10）的格 + 其 bbox（zoom 用）。 */
function _topKeywordCells(feats, topic, n = 10) {
  const scored = feats
    .filter((f) => (f.properties || {}).topic_top === topic)
    .map((f) => ({ f, sc: (f.properties || {}).point_count || 0 }))
    .filter((x) => x.sc > 0)
    .sort((a, b) => b.sc - a.sc)
    .slice(0, n);
  const cells = scored.map((x) => x.f);
  let bb = null;
  for (const f of cells) {
    const fb = _featBBox(f);
    if (!fb) continue;
    bb = bb ? [Math.min(bb[0], fb[0]), Math.min(bb[1], fb[1]), Math.max(bb[2], fb[2]), Math.max(bb[3], fb[3])] : fb;
  }
  return { cells, bb };
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

/** T2 数据属性：3 行紧凑（文件名 / 样式·计数·尺寸 / 坐标系·格式），无板块标题字。
 *  坐标系按层来源给：分析层产物=WGS84（后端 4326）；导入层取 layer.crsInfo（投影时 import 标注）。 */
function _crsOf(layer) {
  if (isAnalysisLayer(layer)) return 'WGS84 (EPSG:4326)';
  return layer.crsInfo || 'WGS84 (EPSG:4326)';
}
function _fmtOf(layer) {
  const ext = guessExt(layer.srcName || layer.name || '');
  if (ext) return ext;
  return isAnalysisLayer(layer) ? 'GeoJSON' : '—';
}
function tier2(layer, lv) {
  const ui = (layer.paint && layer.paint._ui) || {};
  const feats = layer.fc.features;
  const fname = layer.srcName || layer.name || '—';
  let style, count, size;
  if (isAnalysisLayer(layer)) {
    style = ui.tool === 'terrain' ? '情绪地形' : (ui.mode === '3d' ? '3D 网格' : '2D 网格');
    count = `${feats.length} 单元`;
    size = ui.tool === 'terrain' ? `${ui.radius ?? 300}m 半径` : (ui.analysis === 'zonal' ? '面域' : `${ui.cellSize ?? 400}m`);
  } else if (layer.kind === 'heatmap') {
    style = '热力图'; count = `${feats.length} 点`; size = `${(layer.paint && layer.paint.radius) ?? 300}m 半径`;
  } else if (lv === 'range') {
    style = '范围面域'; count = `${feats.length} 面`; size = rangeAreaLabel(layer);
  } else if (lv === 'L1') {
    style = '情绪点（热度）'; count = `${feats.length} 条`; size = '强度×置信度';
  } else if (lv === 'L2') {
    style = '情绪点（极性）'; count = `${feats.length} 条`; size = '5 级极性';
  } else {
    style = '数据点'; count = `${feats.length} 条`; size = '—';
  }
  return `<div class="ov-tier ov-t2"><div class="ov-attr">
    <div class="ov-attr-line ov-ellipsis" title="${fname}">文件名：${fname}</div>
    <div class="ov-attr-line">${style} · ${count} · ${size}</div>
    <div class="ov-attr-line">${_crsOf(layer)} · ${_fmtOf(layer)}</div>
  </div></div>`;
}

/** T3 展示（flex:1 >50%）：治理/分析结论 */
function tier3(layer, lv) {
  let body;
  if (isAnalysisLayer(layer)) {
    const feats = layer.fc.features;
    const ui = (layer.paint && layer.paint._ui) || {};
    // 单极性网格层（L2 grid · polarity !== overall）→ 独立 Overview（item 5）
    if (_isSinglePol(ui)) {
      body = _singlePolBody(feats, ui);
    } else {
      // 综合：极性分布（饼图 + 图例横排一行）+ 4 领域柱（全称加粗 #4876FF，次行）+ 矩阵 + 关键词（item 2 排版）
      const agg = { 'Very Positive': 0, Positive: 0, Neutral: 0, Negative: 0, 'Very Negative': 0 };
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
      const total = agg['Very Positive'] + agg.Positive + agg.Neutral + agg.Negative + agg['Very Negative'];
      const cell = _matrix4x5(feats);
      const pieHtml = total ? _polarPieHtml(agg, total) : '';
      const domHtml = _domainBarsCompact(feats);
      const posN = agg['Very Positive'] + agg['Positive'];
      const negN = agg['Negative'] + agg['Very Negative'];
      const neuN = agg['Neutral'];
      const countLine = total
        ? `<div class="ov-count-line">共 <b>${total}</b> 条 · 积极 <b>${posN}</b> · 消极 <b>${negN}</b> · 中性 <b>${neuN}</b></div>` : '';
      const overviewRow = (pieHtml || domHtml)
        ? `<div class="ov-tier-sub">数据总览<span class="info-i" data-tip="饼图悬停/点击某极性 → 地图同步高亮该极性主导的网格；矩阵、关键词同理。点击锁定，再次点击释放。">i</span></div>
           ${countLine}
           ${pieHtml ? `<div class="ov-overview-row ov-ov-pie-row">${pieHtml}</div>` : ''}
           ${domHtml ? `<div class="ov-overview-row ov-ov-dom-row"><div class="ov-domain-chart">${domHtml}</div></div>` : ''}` : '';
      body = `${overviewRow}
        <div class="ov-tier-sub">归因矩阵<span class="info-i" data-tip="4 大治理领域 × 5 要素 的情绪归因矩阵。悬停/点击某格 → 地图同步高亮该领域×要素交集的网格。">i</span></div>${_matrixHtml(cell)}
        <div class="ov-tier-sub">关键词Top10<span class="info-i" data-tip="按各要素正/中/负情绪点数排名的高频城市关键词。点击某词 → 地图定位并高亮其最强聚集的若干柱体。">i</span></div>${_keywordsHtml(feats)}`;
    }
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
  return `<div class="ov-tier ov-t3">${body}</div>`;
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
