// ═══ panel.js — right panel: Overview (per-layer 3-tier) + Table ═══
import {
  POLARITY_ORDER, POLARITY_LABEL, emotionColors,
  layerLevel, focusLayer, polarityStats, confidenceStats, CONFIDENCE_RAMP,
  getLayer, getChildren, getLayers,
  L2_POSITIVE, L2_NEGATIVE, L2_NEUTRAL_COLOR,
  DOMAIN_BAR_COLOR, ELEMENT_BAR_COLOR, POL_MATRIX_TIERS,
  EMOTION_TYPE_COLORS, EMOTION_TYPE_ORDER,
  EMOTION_MACRO_ORDER, EMOTION_MACRO_MAP,
  HEATMAP_RAMPS, HOTNESS_RAMP, computeHotness, hotnessBuckets, rampDisplaySegs, deriveTimeTag, KEYWORD_TABLE,
} from './state.js';
import { geomStats, DOMAIN_LABEL, ELEMENT_LABEL } from './popup.js';
import { easeBackFromCell, fitBoundsTo, renderLayer } from './map.js';
import { POLARITY_GRID, polarityStops } from './grid-tool.js';
import { highlightCellSet, clearHighlightCellSet, toggleStickyHighlight, resetHighlightCellSet, setStickyProvider } from './tip-popup.js';
import { loadDistricts, classifyPointsByDistrict, polyCentroid } from './district-stats.js';

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
  // 注册 sticky provider：tip-popup 在 layers:changed（含 2D/3D 切换）时回调 → 按当前可见分析层重派生
  // sticky features + key，实现柱体高亮 ⇄ 网格高亮 随视角自动转换（跨切换保持）。
  setStickyProvider(() => {
    if (!_sticky) return null;
    const layer = _currentVisibleAnalysisLayer() || _overviewLayer;
    if (!layer || !layer.fc || !layer.fc.features) return null;
    const feats = layer.fc.features;
    if (_sticky.type === 'mx') return { features: _cellsByBucket(feats, _sticky.dom, _sticky.elm), layer, key: 'mx:' + _sticky.dom + '|' + _sticky.elm };
    if (_sticky.type === 'kw') { const r = _topKeywordCells(feats, _sticky.topic, 10); return { features: r.cells, layer, key: 'kw:' + _sticky.topic }; }
    if (_sticky.type === 'pol') return { features: _cellsByPolarity(feats, _sticky.pol), layer, key: 'pol:' + _sticky.pol };
    return null;
  });
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
      if (sl) { _clearSync(); highlightCellSet(_cellsByPolarity(_overviewLayer.fc.features, sl.dataset.pol), _overviewLayer); return; }
      const mx = e.target.closest('.mx-cell[data-dom]');
      if (mx) {
        if (_polarityState) {   // 极性深读：矩阵 hover → 地图高亮该桶 + 填 #ov-block-kw 副本关键词（替图层总览关键词联动）
          highlightCellSet(_cellsByBucket(_overviewLayer.fc.features, mx.dataset.dom, mx.dataset.elm), _overviewLayer);
          _renderBlockKeywordsFor(_polarityState.layer, _polarityState.pol, mx.dataset.dom, mx.dataset.elm);
          return;
        }
        _clearSync(); highlightCellSet(_cellsByBucket(_overviewLayer.fc.features, mx.dataset.dom, mx.dataset.elm), _overviewLayer); _syncFromMatrix(mx.dataset.dom, mx.dataset.elm); return;
      }
      const kw = e.target.closest('.ov-kw-item');
      if (kw && !kw.classList.contains('ov-kw-block')) {   // 极性深读的 block 关键词卡无 topic，跳过联动
        _clearSync(); const r = _topKeywordCells(_overviewLayer.fc.features, kw.dataset.topic, 10); if (r.cells.length) highlightCellSet(r.cells, _overviewLayer); _syncFromKeyword(kw.dataset.topic); return;
      }
    });
    pane.addEventListener('mouseout', (e) => {
      if (e.target.closest('.ov-pie-slice') || e.target.closest('.mx-cell[data-dom]') || e.target.closest('.ov-kw-item')) { clearHighlightCellSet(); _clearSync(); }
    });
    pane.addEventListener('click', (e) => {
      if (!_overviewLayer) return;
      // 饼图 slice → 锁定/释放该极性主导格
      const sl = e.target.closest('.ov-pie-slice');
      if (sl) {
        const pol = sl.dataset.pol;
        const cells = _cellsByPolarity(_overviewLayer.fc.features, pol);
        const locked = toggleStickyHighlight(cells, _overviewLayer, 'pol:' + pol);
        _clearStickySync();
        const svg = sl.closest('svg');
        if (svg) svg.querySelectorAll('.ov-pie-slice').forEach((s) => s.classList.remove('is-sticky'));
        if (locked) { sl.classList.add('is-sticky'); _sticky = { type: 'pol', pol }; }
        else _sticky = null;
        return;
      }
      // 矩阵格 → 锁定/释放该 domain×element 桶（选中后关联关键词卡片持久高亮，直到取消）
      const mx = e.target.closest('.mx-cell[data-dom]');
      if (mx) {
        const dom = mx.dataset.dom, elm = mx.dataset.elm;
        const cells = _cellsByBucket(_overviewLayer.fc.features, dom, elm);
        const locked = toggleStickyHighlight(cells, _overviewLayer, 'mx:' + dom + '|' + elm);
        _clearStickySync();
        const mtx = mx.closest('.ov-matrix');
        if (mtx) mtx.querySelectorAll('.mx-cell.is-sticky').forEach((c) => c.classList.remove('is-sticky'));
        if (locked) { mx.classList.add('is-sticky'); _sticky = { type: 'mx', dom, elm }; _applyStickySync('mx', dom, elm); }
        else _sticky = null;
        return;
      }
      // 关键词 → top-N 最强聚集格 sticky + fitBounds（再点释放）
      const kw = e.target.closest('.ov-kw-item');
      if (kw) {
        const topic = kw.dataset.topic;
        const r = _topKeywordCells(_overviewLayer.fc.features, topic, 10);
        if (r.cells.length) {
          const locked = toggleStickyHighlight(r.cells, _overviewLayer, 'kw:' + topic);
          _clearStickySync();
          const wrap = kw.closest('.ov-keywords');
          if (wrap) wrap.querySelectorAll('.ov-kw-item.is-sticky').forEach((x) => x.classList.remove('is-sticky'));
          if (locked) { kw.classList.add('is-sticky'); _sticky = { type: 'kw', topic }; _applyStickySync('kw', topic); if (r.bb) fitBoundsTo(r.bb, 120, 15); }
          else _sticky = null;
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
      _clearSync();
      _clearStickySync();
      _sticky = null;
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
    _clearPolarityView();   // 清空焦点 → 还原可能残留的极性 paint
    toggleOvSubtabs(false); activateOvTab('layer', { silent: true });
    pane.innerHTML = emptyState();
    return;
  }
  const focus = focusLayer(layer) || layer;
  _overviewLayer = focus;
  const lv = layerLevel(focus);
  pane.innerHTML = tier1(focus, lv) + tier2(focus, lv) + tier3(focus, lv);
  toggleOvSubtabs(isOverallGrid((focus.paint && focus.paint._ui) || {}));   // 仅 L2·综合·标准网格 有极性深读 → 显 sub-Tab
  if (focus.id !== _lastOverviewLayerId) activateOvTab('layer');   // 换层 → 回图层总览 + 还原旧层极性 paint + zoom out
  _lastOverviewLayerId = focus.id;
  // L1 点层（热度分布）→ 异步填数据总览（area_tag 计数 + per-组团 PIP 缓存）；L1 网格层不跑 PIP
  if (!isAnalysisLayer(focus) && lv === 'L1') _fillL1DataOverview(focus);
  // 选中态跨重渲保持 DOM .is-sticky + 持久联动（地图 HL 由 tip-popup sticky provider 在 layers:changed 时重套）
  if (_sticky) _reapplyStickyDOM(focus);
}

/** 双层 sub-Tab 切换：name='layer'|'polarity'。
 *  silent（初始化/换层）不 zoom；切到「极性深读」→ 渲染极性 Tab 条 + 默认积极 + paint 切到积极视图。
 *  切回「图层总览」→ 还原综合 paint + 清 polarity filter + easeBackFromCell 抬高视野。 */
export function activateOvTab(name, opts) {
  const silent = opts && opts.silent;
  document.querySelectorAll('.ov-subtab').forEach((b) => b.classList.toggle('is-active', b.dataset.ovtab === name));
  document.querySelectorAll('.ov-subpane').forEach((p) => p.classList.toggle('is-active', p.dataset.ovpane === name));
  if (name === 'polarity') {
    _renderPolarityDeepRead();
  } else if (!silent) {
    _clearPolarityView();          // 回图层总览 → 还原综合 paint
    resetHighlightCellSet();
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

/** 单元深读占位提示（已移除；保留极性深读占位用）。 */
function polEmptyHint(msg, hint) {
  return `<div class="ov-empty"><div class="ov-empty-title">${msg || '该层无极性深读'}</div><div class="ov-empty-hint">${hint || '选 <b>L2·综合·标准网格</b> 层查看极性深读'}</div></div>`;
}

// ── 极性深读（替原单元深读）：L2 综合·标准网格 的子层级；3 极性 Tab + paint 就地切换 + 动态矩阵块关键词 ──
// 综合 grid 生成时已备份 paint._ui._overallPaint（grid-tool generateGrid）；切极性 = 改 gridField/gridStops +
// 加 filter(藏零计数格) + renderLayer。零新图层、不触发 refreshOverview 抢焦点、Range 自动保留。
let _polarityState = null;   // { layer, pol } 当前极性深读目标层 + 激活极性；null = 未在极性深读
const _POL_TAB = [
  { key: 'positive', label: '积极', color: '#0d6b2e' },
  { key: 'neutral',  label: '中性', color: '#1A3A8C' },
  { key: 'negative', label: '消极', color: '#d8552f' },
];

/** L2 综合 grid 判定（tool=grid/level=L2/polarity=overall）—— 仅此类层有极性深读。 */
export function isOverallGrid(ui) {
  return !!(ui && ui.tool === 'grid' && ui.level === 'L2' && (!ui.polarity || ui.polarity === 'overall'));
}

/** paint 就地切到指定极性视图（改 gridField/gridStops/heightField + filter 藏零计数格 + renderLayer）。 */
function _applyPolarityView(layer, pol) {
  const g = POLARITY_GRID[pol];
  if (!g || !layer || !layer.paint || !layer.paint._ui) return;
  layer.paint.gridField = g.field;
  layer.paint._ui.heightField = g.field;   // 柱体高度同源切到该极性（颜色+高度一致，深色=高柱）
  const st = polarityStops(pol);
  if (st && st.length) layer.paint.gridStops = st;
  layer.paint._polarityFilter = ['>', ['get', g.nField], 0];
  renderLayer(layer);
}

/** 还原综合态 paint（回图层总览 / 换层 / 删层 时调）。层已删则只清状态。 */
function _clearPolarityView() {
  const st = _polarityState;
  if (!st) return;
  const layer = st.layer;
  if (layer && layer.paint && layer.paint._ui && layer.paint._ui._overallPaint) {
    const ov = layer.paint._ui._overallPaint;
    layer.paint.gridField = ov.gridField;
    layer.paint.gridStops = ov.gridStops;
    layer.paint._ui.heightField = ov.heightField || '_grid_h';
    delete layer.paint._polarityFilter;
    renderLayer(layer);
  }
  _polarityState = null;
}

/** 渲染极性深读 pane：极性 Tab 条 + 默认积极的（极性总览 + 归因矩阵 + 关键词/热门话题）。 */
function _renderPolarityDeepRead() {
  const pane = document.getElementById('ov-polarity-pane');
  if (!pane) return;
  const layer = _overviewLayer;
  if (!layer || !isAnalysisLayer(layer) || !isOverallGrid(layer.paint && layer.paint._ui)) {
    _polarityState = null;
    pane.innerHTML = polEmptyHint();
    return;
  }
  const keep = _polarityState && _polarityState.layer && _polarityState.layer.id === layer.id;
  const pol = keep ? (_polarityState.pol || 'positive') : 'positive';
  _polarityState = { layer, pol };
  _applyPolarityView(layer, pol);
  pane.innerHTML = _polarityTabBarHtml(pol) + _polarityBodyHtml(layer, pol);
  _wirePolarityTabs(layer);
}

function _polarityTabBarHtml(pol) {
  const tabs = _POL_TAB.map((t) =>
    `<button class="ov-pol-tab${t.key === pol ? ' is-active' : ''}" data-pol="${t.key}" type="button" style="--pol-c:${t.color}" role="tab">${t.label}</button>`).join('');
  return `<div class="ov-pol-tabs" role="tablist">${tabs}</div>`;
}

/** 极性 Tab click：切极性（paint + body 就地换；Tab 条不动避抖）。 */
function _wirePolarityTabs(layer) {
  const pane = document.getElementById('ov-polarity-pane');
  if (!pane) return;
  pane.querySelectorAll('.ov-pol-tab').forEach((b) =>
    b.addEventListener('click', () => {
      const pol = b.dataset.pol;
      if (!pol || (_polarityState && _polarityState.pol === pol)) return;
      _polarityState = { layer, pol };
      _applyPolarityView(layer, pol);
      pane.querySelectorAll('.ov-pol-tab').forEach((t) => t.classList.toggle('is-active', t.dataset.pol === pol));
      const body = pane.querySelector('.ov-pol-body');
      if (body) body.outerHTML = _polarityBodyHtml(layer, pol);
    }));
}

/** 极性深读 body：极性总览 count + 按极性重计的归因矩阵 + 关键词/热门话题（默认 hint，hover 块动态填）。 */
function _polarityBodyHtml(layer, pol) {
  const feats = (layer.fc && layer.fc.features) || [];
  const nField = (POLARITY_GRID[pol] || {}).nField;
  let total = 0;
  for (const f of feats) total += ((f.properties || {})[nField] || 0);
  const polLabel = { positive: '积极', negative: '消极', neutral: '中性' }[pol] || '极性';
  const countLine = total
    ? `<div class="ov-count-line">偏<b>${polLabel}</b>情绪点 <b>${total}</b> 个</div>`
    : `<div class="ov-count-line muted">该极性无情绪点数据</div>`;
  const cell = _matrix4x5ByPolarity(feats, pol);
  const kwHint = `<div class="ov-block-kw-hint">悬停 / 点击矩阵块查看该维度关键词<span class="info-i" data-tip="极性深读关键词对应每个矩阵块的情绪点评论，随悬停/选中动态变化。本数据为<b>演示模拟副本</b>（深度解读·极性·关键词群），正式管线接入后替换。">i</span></div>`;
  return `<div class="ov-pol-body">
    <div class="ov-tier-sub">极性总览</div>${countLine}
    <div class="ov-tier-sub">归因矩阵${_unit('个单元')}<span class="info-i" data-tip="按当前极性重计：每块 = 该 domain×element 下该极性情绪点数之和。颜色按本矩阵数量三级（深紫最多→浅紫最少）。悬停/点击 → 下方关键词动态切换 + 地图同步高亮该桶单元。">i</span></div>${_matrixIntro(`通过空间聚合，按<b>${polLabel}</b>极性重计 4×5 归因（数字 = 该维度 ${polLabel} 情绪点数）：`)}${_singlePolMatrixHtml(cell)}
    <div class="ov-tier-sub">关键词/热门话题</div>${kwHint}
    <div class="ov-block-kw" id="ov-block-kw"><div class="ov-placeholder muted">悬停矩阵块查看该维度 ${polLabel} 关键词</div></div>
  </div>`;
}

/** 按极性重计 4×5：块 count = Σ 单元格 n_<pol>（综合 fc 已带 n_positive/n_negative/n_neutral）。 */
function _matrix4x5ByPolarity(feats, pol) {
  const nField = (POLARITY_GRID[pol] || {}).nField;
  const cell = {};
  if (!nField) return cell;
  for (const f of feats) {
    const p = f.properties || {};
    if (!p.domain_top || !p.element_top) continue;
    const k = p.domain_top + '|' + p.element_top;
    if (!cell[k]) cell[k] = { n: 0, piSum: 0, piCnt: 0 };
    cell[k].n += (p[nField] || 0);
  }
  return cell;
}

/** 副本加载（fetch DATA/performance/polarity_deepread_keywords.json；缓存 + 失败不重试）。 */
let _demoKwCache = null;
function _loadDemoKw() {
  if (_demoKwCache !== null) return Promise.resolve(_demoKwCache);
  return fetch('/DATA/performance/polarity_deepread_keywords.json', { cache: 'no-store' })
    .then((r) => (r.ok ? r.json() : null))
    .then((j) => { _demoKwCache = j || false; return _demoKwCache; })
    .catch(() => { _demoKwCache = false; return false; });
}

/** 把指定 (极性, domain×element) 的副本关键词渲染进 #ov-block-kw。T = 综合 layer timeTag（缺退 T3）。 */
function _renderBlockKeywordsFor(layer, pol, dom, elm) {
  const el = document.getElementById('ov-block-kw');
  if (!el) return;
  const T = (layer && (layer.timeTag || deriveTimeTag(layer.fc))) || 'T3';
  _loadDemoKw().then((kw) => {
    if (!kw || !kw[T] || !kw[T][pol]) { el.innerHTML = `<div class="ov-placeholder muted">副本缺失 ${T}/${pol}（演示数据未就绪）</div>`; return; }
    const words = kw[T][pol][dom + '|' + elm] || [];
    el.innerHTML = words.length
      ? `<div class="ov-block-kw-list">${words.map((w) => `<div class="ov-kw-item ov-kw-block"><span class="ov-kw-word">${w}</span></div>`).join('')}</div>`
      : `<div class="ov-placeholder muted">该维度无高频关键词</div>`;
  });
}

/** Overview 单元模式（已废弃——单元深读改极性深读；保留空函数防 main.js 旧调用报错，下版本清）。 */
export function setCellOverview(_feature, _layer) { /* removed: 单元深读 → 极性深读 */ }

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
/** 矩阵行（domain）单元总计：{domain: n}（行标签下 "(N)" 用）。 */
function _domainTotals(cell) {
  const m = {};
  for (const d of DOMAIN_ORDER) m[d] = 0;
  for (const k in cell) { const d = k.split('|')[0]; m[d] = (m[d] || 0) + (cell[k].n || 0); }
  return m;
}
/** 矩阵列（element）单元总计：{element: n}（列头下 "(N)" 用，单极性矩阵）。 */
function _elementTotals(cell) {
  const m = {};
  for (const e of ELEMENT_ORDER) m[e] = 0;
  for (const k in cell) { const e = k.split('|')[1]; m[e] = (m[e] || 0) + (cell[k].n || 0); }
  return m;
}
/** 板块题头右侧单位标注（细体、同题头色）。 */
const _unit = (t) => `<span class="ov-unit">（单位：${t}）</span>`;
/** 归因矩阵标题下的一句话总结（解释这部分数据在干嘛，避免观众一头雾水）。 */
const _matrixIntro = (html) => `<div class="ov-matrix-intro">${html}</div>`;
/** L1 网格 4 维度数据条（带占比%）：复用 _barsHtml 结构 + 行尾占比，用于 L1 网格矩阵上方。 */
function _l1DomainBarsHtml(feats) {
  const m = {};
  for (const f of feats) { const d = (f.properties || {}).domain_top; if (d) m[d] = (m[d] || 0) + 1; }
  const entries = DOMAIN_ORDER.filter((d) => m[d]).map((d) => [d, m[d]]);
  if (!entries.length) return `<div class="ov-placeholder muted">无治理领域数据</div>`;
  const total = feats.length || 1;
  const max = Math.max(...entries.map((x) => x[1]));
  return entries.map(([d, n]) => {
    const pct = Math.round(n / total * 100);
    return `<div class="ov-dbar"><span class="ov-dbar-label">${DOMAIN_LABEL[d] || d}</span>
      <span class="ov-dbar-track"><span class="ov-dbar-fill" style="width:${(n / max) * 100}%;background:${DOMAIN_BAR_COLOR}">${n}</span></span>
      <span class="ov-dbar-pct">${pct}%</span></div>`;
  }).join('');
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

function _matrixHtml(cell, withTotals = true) {
  const domTotals = _domainTotals(cell);
  const elmTotals = _elementTotals(cell);
  const head = `<div class="mx-cell mx-head"></div>` +
    ELEMENT_ORDER.map((e) => {
      const lbl = (ELEMENT_LABEL[e] || e).slice(0, 2);
      return `<div class="mx-cell mx-head" title="${ELEMENT_LABEL[e] || e}">${lbl}${withTotals ? `<span class="mx-rowcount">(${elmTotals[e]})</span>` : ''}</div>`;
    }).join('');
  const rows = DOMAIN_ORDER.map((d) => {
    const cells = ELEMENT_ORDER.map((e) => {
      const c = cell[d + '|' + e];
      const lbl = `${DOMAIN_LABEL[d] || d} × ${ELEMENT_LABEL[e] || e}`;
      if (!c) return `<div class="mx-cell mx-empty" title="${lbl}：无"></div>`;
      const pi = c.piCnt ? c.piSum / c.piCnt : null;
      return `<div class="mx-cell" data-dom="${d}" data-elm="${e}" style="background:${_piColor(pi)}" title="${lbl}：${c.n} 单元 · 极性 ${pi != null ? pi.toFixed(2) : '—'}（悬停/点击 → 地图同步）">${c.n}</div>`;
    }).join('');
    const lbl = DOMAIN_LABEL[d] || d;
    return `<div class="mx-rowlabel" title="${lbl}">${lbl}${withTotals ? `<span class="mx-rowcount">(${domTotals[d]})</span>` : ''}</div>${cells}`;
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

/** L1 网格聚合层（grid tool × L1 level）→ 独立 Overview（仅矩阵 + 4 维柱，无单元深读/关键词/数据总览）。
 *  导出给 main.js：L1 网格无单元深读，cell:selected 不切深读 tab。 */
export function isL1Grid(ui) {
  return !!(ui && ui.tool === 'grid' && ui.level === 'L1');
}

/** 单极性归因矩阵：只显该极性分布，格色按本矩阵 count 三级（high#6A5ACD/mid#7B68EE/low#8470FF）。
 *  不再用 _piColor（极性色）—— 单极性层极性已定，矩阵强调"哪些 domain×element 桶最多"。 */
function _singlePolMatrixHtml(cell) {
  // 三分位梯度：按本矩阵实际 count 分布取 1/3、2/3 分位赋 high/mid/low，保证三色各占约 1/3 格。
  // 修旧 bug：n/max>0.66 阈值在长尾数据（如 max=591、余皆<33%·max）下 mid 永空，全矩阵仅深浅两色。
  const ns = Object.values(cell).map((c) => c.n || 0).filter((n) => n > 0).sort((a, b) => a - b);
  const domTotals = _domainTotals(cell);
  const elmTotals = _elementTotals(cell);
  const tierColor = (n) => {
    if (!n || n <= 0 || !ns.length) return POL_MATRIX_TIERS.low;
    if (ns.length < 3) return n >= ns[ns.length - 1] ? POL_MATRIX_TIERS.high : POL_MATRIX_TIERS.low;
    let i = 0; while (i < ns.length && ns[i] < n) i++;   // n 在排序数组中的分位
    const q = i / (ns.length - 1);
    return q > 2 / 3 ? POL_MATRIX_TIERS.high : q > 1 / 3 ? POL_MATRIX_TIERS.mid : POL_MATRIX_TIERS.low;
  };
  const head = `<div class="mx-cell mx-head"></div>` +
    ELEMENT_ORDER.map((e) => `<div class="mx-cell mx-head" title="${ELEMENT_LABEL[e] || e}">${(ELEMENT_LABEL[e] || e).slice(0, 2)}<span class="mx-rowcount">(${elmTotals[e]})</span></div>`).join('');
  const rows = DOMAIN_ORDER.map((d) => {
    const cells = ELEMENT_ORDER.map((e) => {
      const c = cell[d + '|' + e];
      const lbl = `${DOMAIN_LABEL[d] || d} × ${ELEMENT_LABEL[e] || e}`;
      if (!c) return `<div class="mx-cell mx-empty" title="${lbl}：无"></div>`;
      return `<div class="mx-cell" data-dom="${d}" data-elm="${e}" style="background:${tierColor(c.n)}" title="${lbl}：${c.n} 单元（悬停/点击 → 地图同步）">${c.n}</div>`;
    }).join('');
    return `<div class="mx-rowlabel" title="${DOMAIN_LABEL[d] || d}">${DOMAIN_LABEL[d] || d}<span class="mx-rowcount">(${domTotals[d]})</span></div>${cells}`;
  }).join('');
  return `<div class="ov-matrix">${head}${rows}</div>`;
}

/** 单极性关键词：该极性 Top10 主题词 + 右侧聚集地点（顿号横排，省空间）。
 *  词来自点的 topic_top（数据层提炼，performance_config.TOPIC_TABLE）；count=point_count 加权；
 *  地点=_topKeywordCells 按 topic 筛出的格 place_name Top8（去重）。 */
const _POL_SIGN = { positive: 'pos', negative: 'neg', neutral: 'neu' };
/** 主题词→极性 + 用户词序（与 performance_config.TOPIC_TABLE 同源；改 TOPIC_TABLE 必须同步此处，否则新词会被 _keywordRank 丢弃）。 */
const TOPIC_POLARITY = {
  // positive（13）：含点军 3 词 楚超火爆/卷桥河露营/江南绿肺
  '网红': 'pos', '夜经济': 'pos', '滨江步道': 'pos', '大南门': 'pos', '楚超火爆': 'pos',
  '老街新生': 'pos', '文化活动': 'pos', '加装电梯': 'pos', '卷桥河露营': 'pos', '绿道成网': 'pos',
  '江南绿肺': 'pos', '长江夜游': 'pos', '西坝不夜岛': 'pos',
  // negative（9）：占道停车/收费不合理（收费缩zone降权，仍在表）
  '停车难': 'neg', '噪音': 'neg', '堵车': 'neg', '占道停车': 'neg', '底商空置冷清': 'neg',
  '红绿灯': 'neg', '施工扰民': 'neg', '没电梯': 'neg', '收费不合理': 'neg',
  // neutral（10）
  '口袋公园': 'neu', '业态': 'neu', '社区服务配套': 'neu', '物业': 'neu', '老街改造': 'neu',
  '盼电梯': 'neu', '规划绿地': 'neu', '业态调整': 'neu', '盼BRT': 'neu', '社区营造': 'neu',
};
const TOPIC_ORDER = {
  pos: ['网红', '夜经济', '滨江步道', '大南门', '楚超火爆', '老街新生', '文化活动', '加装电梯', '卷桥河露营', '绿道成网', '江南绿肺', '长江夜游', '西坝不夜岛'],
  neg: ['停车难', '噪音', '堵车', '占道停车', '底商空置冷清', '红绿灯', '施工扰民', '没电梯', '收费不合理'],
  neu: ['口袋公园', '业态', '社区服务配套', '物业', '老街改造', '盼电梯', '规划绿地', '业态调整', '盼BRT', '社区营造'],
};

/** Feature 4 语义映射：topic → 1-3 个 domain×element 语义块（覆盖数据扫描的反直觉关联）。
 *  仅"哪个词↔哪格"的联动对应关系查此表；矩阵色/数仍走数据（_matrix4x5/_matrixHtml）。
 *  key 同 DOMAIN_ORDER/ELEMENT_ORDER。改 TOPIC_TABLE 须同步 TOPIC_POLARITY/ORDER + 此表。 */
const TOPIC_MATRIX_MAP = {
  // positive（13）
  '网红': [['urban_operation', 'service'], ['urban_operation', 'culture'], ['urban_renewal', 'culture']],
  '夜经济': [['urban_operation', 'event'], ['urban_planning', 'event']],
  '滨江步道': [['urban_planning', 'environment']],
  '大南门': [['urban_renewal', 'culture'], ['urban_renewal', 'service'], ['urban_operation', 'culture']],
  '楚超火爆': [['urban_operation', 'event']],
  '老街新生': [['urban_renewal', 'culture']],
  '文化活动': [['urban_renewal', 'culture'], ['urban_operation', 'culture'], ['urban_planning', 'culture']],
  '加装电梯': [['urban_renewal', 'facility']],
  '卷桥河露营': [['urban_planning', 'environment']],
  '绿道成网': [['urban_planning', 'environment']],
  '江南绿肺': [['urban_planning', 'environment'], ['urban_renewal', 'environment']],
  '长江夜游': [['urban_planning', 'event'], ['urban_operation', 'event']],
  '西坝不夜岛': [['urban_planning', 'event'], ['urban_operation', 'event']],
  // negative（9）
  '停车难': [['urban_governance', 'facility'], ['urban_planning', 'facility']],
  '噪音': [['urban_planning', 'environment'], ['urban_operation', 'event'], ['urban_renewal', 'environment']],
  '堵车': [['urban_governance', 'event']],
  '占道停车': [['urban_governance', 'facility'], ['urban_governance', 'environment'], ['urban_renewal', 'environment']],
  '底商空置冷清': [['urban_operation', 'service']],
  '红绿灯': [['urban_governance', 'facility']],
  '施工扰民': [['urban_renewal', 'environment']],
  '没电梯': [['urban_renewal', 'facility']],
  '收费不合理': [['urban_operation', 'service']],
  // neutral（10）
  '口袋公园': [['urban_planning', 'environment']],
  '业态': [['urban_operation', 'service'], ['urban_operation', 'culture']],
  '社区服务配套': [['urban_renewal', 'facility'], ['urban_renewal', 'service']],
  '物业': [['urban_renewal', 'service']],
  '老街改造': [['urban_renewal', 'environment']],
  '盼电梯': [['urban_renewal', 'facility']],
  '规划绿地': [['urban_planning', 'environment']],
  '业态调整': [['urban_operation', 'service']],
  '盼BRT': [['urban_planning', 'facility'], ['urban_governance', 'facility']],
  '社区营造': [['urban_renewal', 'culture']],
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
  // 极性总览只留总结一句（4 领域 + 5 要素统计已并入归因矩阵行/列标签）。
  return `${countLine ? `<div class="ov-tier-sub">极性总览</div>${countLine}` : ''}
    <div class="ov-tier-sub">归因矩阵${_unit('个单元')}<span class="info-i" data-tip="单极性矩阵：颜色按本矩阵数量三级（深紫最多 → 浅紫最少），强调该极性问题集中在哪些领域×要素。悬停/点击 → 地图同步。行/列标签下数字 = 该领域/要素单元总数。">i</span></div>${_matrixIntro(`通过空间聚合分析，共生成 <b>${feats.length}</b> 个${polLabel}标准单元（${ui.cellSize || 400}m），在<b>"4维度×5要素"</b>归因统计中，结果如下（数字代表该维度的单元数量）：`)}${_singlePolMatrixHtml(cell)}
    <div class="ov-tier-sub">关键词 Top10<span class="info-i" data-tip="该极性高频城市关键词（左 1/3：词+次数）及其代表性地点 Top5（右 2/3）。点击词 → 定位最强聚集。">i</span></div>${_singlePolKeywordsHtml(feats, pol)}`;
}

// ── L1 数据总览（治理产出率 + 中心城区/8 组团 分布）──
// L0 评论 → L1 情绪点（一条评论+地理等属性 = 一个情绪点）。产出率按 T ∈ {0.10,0.11,0.12}（治理产出渐升）。
// 中心城区计数：用 L1 数据自带 area_tag 字段（core/central_outer=中心城区，outside_cc=外）→ 零 PIP、瞬时、随数据公式化重算。
// 8 组团分布：射线法 PIP（heavy → 缓存到 layer._tuanCls 仅算一次 + bbox 预筛）。
const _L1_RATE = { T1: 0.10, T2: 0.11, T3: 0.12 };
const _L1_RATE_DEFAULT = 0.11;
function _l1RateOf(layer) {
  const t = deriveTimeTag(layer.fc);
  return _L1_RATE[t] || _L1_RATE_DEFAULT;
}
const _CC_AREA_TAGS = new Set(['core', 'central_outer']);
/** L1 点层 area_tag 计数：{total, cc}（cc = 中心城区 = core+central_outer，等价 text 非空）。零 PIP。 */
function _l1AreaTagCount(feats) {
  let total = 0, cc = 0;
  for (const f of feats) { total++; if (_CC_AREA_TAGS.has((f.properties || {}).area_tag)) cc++; }
  return { total, cc };
}

/** L1 网格层 Overview body：仅归因矩阵（引言 + 4 维柱带占比 + 灰线分隔 + 矩阵 withTotals=false + 无关键词）。
 *  数据总览已迁至 L1 点层（热度分布）→ 网格层不再跑 PIP，2D/3D/选中零开销（修卡顿）。 */
function _l1GridBody(feats, ui, layer) {
  const cell = _matrix4x5(feats);
  const cs = (ui && ui.cellSize) || 400;
  const intro = _matrixIntro(`通过空间聚合分析，共生成 <b>${feats.length}</b> 个标准单元（${cs}m），<b>"4维度×5要素"</b>归因统计如下（数字代表该维度的单元数量）：`);
  return `<div class="ov-tier-sub">归因矩阵${_unit('个单元')}<span class="info-i" data-tip="L1 网格 4 大治理领域 × 5 要素归因矩阵。上方 4 领域条 = 各领域单元数及占比（L1 不并入矩阵，独立显示）。悬停/点击矩阵格 → 地图同步。数据总览见 L1·热度分布图层。">i</span></div>
    ${intro}
    <div class="ov-overview-row ov-ov-dom-row"><div class="ov-domain-chart">${_l1DomainBarsHtml(feats)}</div></div>
    <div class="ov-matrix-sep"></div>${_matrixHtml(cell, false)}`;
}

/** L1 点层（热度分布）数据总览占位 HTML（双段总结 + 紫饼图 + 8 组团横条；异步填充）。 */
function _l1PointDataOverviewHtml(layer) {
  return `<div class="ov-tier-sub">数据总览${_unit('个点')}<span class="info-i" data-tip="L0 评论经治理产出 L1 情绪点（一条评论+地理等属性=一个情绪点）；产出率按时间点 T 在 10~12% 间（治理产出渐升）。中心城区计数用 L1 数据 area_tag 字段（core/central_outer）。数字随载入的 L1 数据公式化重算。">i</span></div>
    <div id="ov-l1-data" class="ov-l1-data"><div class="ov-placeholder muted">分布计算中…</div></div>`;
}

/** 通用饼图（SVG arc；segs=[{label,color,n}]），图例在右。 */
function _simplePieHtml(segs, total) {
  if (!total) return '';
  const cx = 50, cy = 50, r = 38;
  let a = -Math.PI / 2;
  const paths = [];
  for (const s of segs) {
    if (s.n <= 0) continue;
    const sweep = (s.n / total) * Math.PI * 2;
    const a0 = a, a1 = a + sweep;
    const x0 = cx + r * Math.cos(a0), y0 = cy + r * Math.sin(a0);
    const x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1);
    const large = sweep > Math.PI ? 1 : 0;
    paths.push(`<path fill="${s.color}" d="M${cx} ${cy} L${x0.toFixed(2)} ${y0.toFixed(2)} A${r} ${r} 0 ${large} 1 ${x1.toFixed(2)} ${y1.toFixed(2)} Z"><title>${s.label} · ${s.n}（${(s.n / total * 100).toFixed(0)}%）</title></path>`);
    a = a1;
  }
  const lg = segs.filter((s) => s.n > 0).map((s) =>
    `<span class="ov-pie-lg"><span class="ov-pie-dot" style="background:${s.color}"></span>${s.label}<i>${s.n}</i></span>`).join('');
  return `<div class="ov-pie-block"><div class="ov-pie"><svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">${paths.join('')}</svg></div>
    <div class="ov-pie-legend">${lg}</div></div>`;
}

// L1 紫色系（饼图 1 + 组团横条 3 档，统一设计语言；与单极性矩阵 POL_MATRIX_TIERS 同源）
const _L1_PURPLE = { cc: '#A020F0', out: '#D8BFD8' };           // 中心城区范围 / 中心城区以外
const _L1_TUAN_TIERS = ['#A020F0', '#9370DB', '#D8BFD8'];        // 组团横条 3 档（多→少）

/** 组团计数 → 3 档色（按 max/min 均分 3 组：上 1/3 深、中 1/3 中、下 1/3 浅）。 */
function _tuanTierColor(n, min, max) {
  if (!n || max === min) return _L1_TUAN_TIERS[0];
  const step = (max - min) / 3;
  return n >= min + step * 2 ? _L1_TUAN_TIERS[0] : n >= min + step ? _L1_TUAN_TIERS[1] : _L1_TUAN_TIERS[2];
}

/** 8 组团横条 HTML（与 4 维度数据条同款、压缩高度/字号）。counts={组团:n}, order=[组团...]. */
function _tuanBarsHtml(counts, order) {
  const entries = order.map((t) => [t, counts[t] || 0]).filter((x) => x[1] > 0);
  if (!entries.length) return `<div class="ov-placeholder muted">组团分布无落点</div>`;
  const vals = entries.map((x) => x[1]);
  const max = Math.max(...vals), min = Math.min(...vals);
  return entries.map(([t, n]) =>
    `<div class="ov-dbar ov-dbar-tuan"><span class="ov-dbar-label">${t}</span>
      <span class="ov-dbar-track"><span class="ov-dbar-fill" style="width:${(n / max) * 100}%;background:${_tuanTierColor(n, min, max)}">${n}</span></span></div>`).join('');
}

/** 异步填充 L1 点层数据总览（area_tag 计数 + per-组团 PIP 缓存 + 紫饼图 + 8 组团横条）。setOverview 渲染后调。 */
async function _fillL1DataOverview(layer) {
  const el = document.getElementById('ov-l1-data');
  if (!el) return;
  const feats = (layer.fc && layer.fc.features) || [];
  const { total: l1, cc: ccCount } = _l1AreaTagCount(feats);
  const rate = _l1RateOf(layer);
  const l0 = l1 ? Math.round(l1 / rate) : 0;
  const ratePct = Math.round(rate * 100);
  const ccPct = l1 ? Math.round(ccCount / l1 * 100) : 0;
  const summary =
    `<div class="ov-l1-summary">共采集评论数量 <b>${l0}</b> 条（L0 原始数据），通过数据治理与地理信息匹配，得到城市情绪点数共 <b>${l1}</b> 个（L1 数据），占比约为 <b>${ratePct}%</b>。</div>
     <div class="ov-l1-summary">其中，中心城区共 <b>${ccCount}</b> 个，占比为 <b>${ccPct}%</b>。</div>`;
  // 饼图 1（全域）：中心城区范围 vs 中心城区以外（紫色系，与 L2 综合饼图同尺寸 187px）
  const pie1 = _simplePieHtml(
    [{ label: '中心城区范围', color: _L1_PURPLE.cc, n: ccCount },
     { label: '中心城区以外', color: _L1_PURPLE.out, n: l1 - ccCount }],
    l1);
  // 8 组团横条：per-组团 PIP（缓存到 layer._tuanCls 仅算一次，防卡顿；仅对中心城区点分类）
  let tuanHtml;
  const ccPoints = feats.filter((f) => _CC_AREA_TAGS.has((f.properties || {}).area_tag));
  if (!ccPoints.length) {
    tuanHtml = `<div class="ov-placeholder muted">中心城区无落点</div>`;
  } else {
    const ds = await loadDistricts();
    if (!ds) tuanHtml = `<div class="ov-placeholder muted">行政区 preset 未上传（控制台 → 选择栏 → 行政区 先载入一次）</div>`;
    else { if (!layer._tuanCls) layer._tuanCls = classifyPointsByDistrict(ccPoints, ds); tuanHtml = _tuanBarsHtml(layer._tuanCls.perTuan, ds.tuanOrder); }
  }
  el.innerHTML =
    `${summary}
     <div class="ov-l1-pies">
       <div class="ov-l1-pie"><div class="ov-l1-pie-cap">宜昌全域 · 情绪点分布</div>${pie1 || '<div class="ov-placeholder muted">无数据</div>'}</div>
       <div class="ov-l1-pie"><div class="ov-l1-pie-cap">中心城区内 · 8 组团</div>${tuanHtml}</div>
     </div>`;
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

// ── Feature 4：归因矩阵 ↔ 关键词 双向联动（语义查表）──
// 对应关系走 TOPIC_MATRIX_MAP（语义），不扫 layer.features 的 topic×(domain,element)——避免 sim POI 域错配（如 口袋公园→运营×环境 反直觉）。
// 矩阵色/数仍走数据（_matrix4x5/_matrixHtml）。≤5 全高亮（.is-synced 橙底白字）；>5 加权（.is-synced-w 橙 tint）—— "太多意义不大"用加权让主峰突出。
const SYNC_FULL_MAX = 5;
/** topic → [[blockKey,1],...]（均权，复用 _applySync）。blockKey = "dom|elm"。 */
function _topicBlocks(topic) {
  return (TOPIC_MATRIX_MAP[topic] || []).map(([d, e]) => [d + '|' + e, 1]);
}
/** (dom,elm) → [[topic,1],...]（均权，反扫 TOPIC_MATRIX_MAP）。 */
function _blockTopics(dom, elm) {
  const key = dom + '|' + elm;
  const out = [];
  for (const [t, blocks] of Object.entries(TOPIC_MATRIX_MAP)) {
    if (blocks.some(([d, e]) => d + '|' + e === key)) out.push([t, 1]);
  }
  return out;
}
/** 应用同步高亮：entries=[[key,count],...]（已降序）；selectorOf(key)→DOM selector。
 *  sticky=true 用持久类（.is-synced-sticky[-w]，mouseout 不清，仅 sticky 取消时清）。
 *  ≤5 全高亮；>5 删最浅档（drop 底部 1/3 长尾，只显中+高档）+ alpha 梯度。
 *  地图聚合域高亮（highlightCellSet）不受此影响——仍全部网格/柱体。 */
function _applySync(entries, selectorOf, sticky) {
  const pane = document.getElementById('overview-pane');
  if (!pane || !entries.length) return;
  const cls = sticky ? 'is-synced-sticky' : 'is-synced';
  const clsW = sticky ? 'is-synced-sticky-w' : 'is-synced-w';
  const n = entries.length;
  if (n <= SYNC_FULL_MAX) {
    for (const [key] of entries) {
      const el = pane.querySelector(selectorOf(key));
      if (el) el.classList.add(cls);
    }
    return;
  }
  // >5：drop 底部 1/3（最浅档），仅高亮前 2/3（中+高），按频次赋 alpha 梯度（0.5~1.0）
  const keep = Math.max(SYNC_FULL_MAX, Math.ceil(n * 2 / 3));
  const kept = entries.slice(0, keep);
  const maxC = Math.max(1, ...kept.map((x) => x[1]));
  for (const [key, count] of kept) {
    const el = pane.querySelector(selectorOf(key));
    if (!el) continue;
    const alpha = 0.5 + 0.5 * (count / maxC);   // 频次越高 alpha 越大（主峰亮、长尾淡）
    el.style.setProperty('--sync-bg', `rgba(255,144,0,${alpha.toFixed(2)})`);
    el.classList.add(clsW);
  }
}
/** 清瞬时同步高亮（mouseover leave 时；不动 sticky 持久类）。 */
function _clearSync() {
  const pane = document.getElementById('overview-pane');
  if (!pane) return;
  pane.querySelectorAll('.is-synced, .is-synced-w').forEach((el) => {
    el.classList.remove('is-synced', 'is-synced-w');
    el.style.removeProperty('--sync-bg');
  });
}
/** 清持久同步高亮（sticky 取消 / 换选中时）。 */
function _clearStickySync() {
  const pane = document.getElementById('overview-pane');
  if (!pane) return;
  pane.querySelectorAll('.is-synced-sticky, .is-synced-sticky-w').forEach((el) => {
    el.classList.remove('is-synced-sticky', 'is-synced-sticky-w');
    el.style.removeProperty('--sync-bg');
  });
}

// 选中态（sticky）语义记录：跨 2D/3D 切换 setOverview 重渲后，由 _reapplySticky 重新套上 DOM/地图/持久联动。
let _sticky = null;   // {type:'mx'|'kw'|'pol', dom, elm, topic, pol} 或 null

/** 选中矩阵块/关键词 → 给关联方加持久同步高亮（新 feature：选中矩阵块后关键词卡片持久高亮，直到取消选中）。 */
function _applyStickySync(type, a, b) {
  if (type === 'mx') {
    const topics = _blockTopics(a, b);
    if (topics.length) _applySync(topics, (t) => `.ov-kw-item[data-topic="${t}"]`, true);
  } else if (type === 'kw') {
    const blocks = _topicBlocks(a);
    if (blocks.length) _applySync(blocks, (k) => {
      const [d, e] = k.split('|'); return `.mx-cell[data-dom="${d}"][data-elm="${e}"]`;
    }, true);
  }
}

/** 当前可见的分析层（2D/3D 切换后找新 mode 层；不依赖 _overviewLayer，避监听器顺序）。 */
function _currentVisibleAnalysisLayer() {
  for (const l of getLayers()) {
    if (l && l.visible && l.kind === 'polygon' && isAnalysisLayer(l)) return l;
  }
  return null;
}

/** setOverview 重渲后：按 _sticky 重新套 DOM .is-sticky + 持久联动（关键词卡片）。
 *  地图聚合域 HL 不在此处——交由 tip-popup 的 sticky provider（layers:changed 时按可见层重派生）。 */
function _reapplyStickyDOM(layer) {
  if (!_sticky || !isAnalysisLayer(layer)) return;
  if (_sticky.type === 'mx') {
    const el = document.querySelector(`.mx-cell[data-dom="${_sticky.dom}"][data-elm="${_sticky.elm}"]`);
    if (el) el.classList.add('is-sticky');
    _applyStickySync('mx', _sticky.dom, _sticky.elm);
  } else if (_sticky.type === 'kw') {
    const el = document.querySelector(`.ov-kw-item[data-topic="${_sticky.topic}"]`);
    if (el) el.classList.add('is-sticky');
    _applyStickySync('kw', _sticky.topic);
  } else if (_sticky.type === 'pol') {
    const el = document.querySelector(`.ov-pie-slice[data-pol="${_sticky.pol}"]`);
    if (el) el.classList.add('is-sticky');
  }
}
/** hover 矩阵块 → 高亮该块下所有关键词卡片（按 blockToTopics）。 */
function _syncFromMatrix(dom, elm) {
  const topics = _blockTopics(dom, elm);
  if (!topics.length) return;
  _applySync(topics, (t) => `.ov-kw-item[data-topic="${t}"]`);
}
/** hover 关键词 → 高亮其所有矩阵块（查 TOPIC_MATRIX_MAP）。 */
function _syncFromKeyword(topic) {
  const blocks = _topicBlocks(topic);
  if (!blocks.length) return;
  _applySync(blocks, (k) => {
    const [d, e] = k.split('|');
    return `.mx-cell[data-dom="${d}"][data-elm="${e}"]`;
  });
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
    // L1 网格聚合层 → 独立 Overview（双饼图 + 4 维柱在矩阵上方 + 矩阵 + 无关键词）
    if (isL1Grid(ui)) {
      body = _l1GridBody(feats, ui, layer);
    } else if (_isSinglePol(ui)) {
      // 单极性网格层（L2 grid · polarity !== overall）→ 独立 Overview（item 5）
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
      const posN = agg['Very Positive'] + agg['Positive'];
      const negN = agg['Negative'] + agg['Very Negative'];
      const neuN = agg['Neutral'];
      // 量词统一为「个」（=情绪点）；4 维柱已并入归因矩阵行标签，数据总览只留饼图。
      const countLine = total
        ? `<div class="ov-count-line">共 <b>${total}</b> 个 · 积极 <b>${posN}</b> · 消极 <b>${negN}</b> · 中性 <b>${neuN}</b></div>` : '';
      const overviewRow = pieHtml
        ? `<div class="ov-tier-sub">数据总览${_unit('个点')}<span class="info-i" data-tip="饼图悬停/点击某极性 → 地图同步高亮该极性主导的网格；矩阵、关键词同理。点击锁定，再次点击释放。">i</span></div>
           ${countLine}
           <div class="ov-overview-row ov-ov-pie-row">${pieHtml}</div>` : '';
      body = `${overviewRow}
        <div class="ov-tier-sub">归因矩阵${_unit('个单元')}<span class="info-i" data-tip="4 大治理领域 × 5 要素 的情绪归因矩阵。悬停/点击某格 → 地图同步高亮该领域×要素交集的网格。行/列标签下数字 = 该领域/要素单元总数。">i</span></div>${_matrixIntro(`通过空间聚合分析，共生成 <b>${feats.length}</b> 个标准单元（${ui.cellSize || 400}m），<b>"4维度×5要素"</b>归因统计如下（数字代表该维度的单元数量，颜色代表该维度的极性倾向）：`)}${_matrixHtml(cell)}
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
    // 数据总览（迁移自 L1 网格：双段总结 + 紫饼图 + 8 组团横条，异步填充）+ 热度值分布
    const dataOverview = _l1PointDataOverviewHtml(layer);
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
    body = `${dataOverview}<div class="ov-tier-sub">热度值分布</div><div class="hchart">${bars}</div>
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
      // 单元深读→极性深读：行点击切 Overview·极性深读（默认极性；不定位单格，深读非单格级）
      activateTab('overview');
      activateOvTab('polarity');
    });
  });
}
