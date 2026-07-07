// ═══ panel.js — right panel: Overview (per-layer 3-tier) + Table ═══
import {
  POLARITY_ORDER, POLARITY_LABEL, emotionColors,
  layerLevel, focusLayer, polarityStats, confidenceStats, CONFIDENCE_RAMP,
  getLayer, getChildren, getLayers, isEmotionPointLayer,
  selectLayer, setLayerVisible, enforceMutualExclusion, layerDisplayColor, levelPointColor,
  L2_POSITIVE, L2_NEGATIVE, L2_NEUTRAL_COLOR,
  DOMAIN_BAR_COLOR, ELEMENT_BAR_COLOR, POL_MATRIX_TIERS,
  EMOTION_TYPE_COLORS, EMOTION_TYPE_ORDER,
  EMOTION_MACRO_ORDER, EMOTION_MACRO_MAP,
  HEATMAP_RAMPS, HOTNESS_RAMP, computeHotness, hotnessBuckets, rampDisplaySegs, deriveTimeTag, KEYWORD_TABLE,
} from './state.js';
import { geomStats, DOMAIN_LABEL, ELEMENT_LABEL } from './popup.js';
import { easeBackFromCell, fitBoundsTo, renderLayer, showLocTips, clearLocTips, setView3D, setViewMode } from './map.js';
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
        if (_polarityState) {   // 极性深读：矩阵 hover → 地图试探高亮该桶；无 sticky 时才瞬时显词组（sticky 最高级不被覆盖）
          highlightCellSet(_cellsByBucket(_overviewLayer.fc.features, mx.dataset.dom, mx.dataset.elm), _overviewLayer);
          if (!_polBlockSticky) _renderBlockKw(_polarityState.layer, _polarityState.pol, mx.dataset.dom, mx.dataset.elm);
          return;
        }
        _clearSync(); highlightCellSet(_cellsByBucket(_overviewLayer.fc.features, mx.dataset.dom, mx.dataset.elm), _overviewLayer); _syncFromMatrix(mx.dataset.dom, mx.dataset.elm); return;
      }
      const kw = e.target.closest('.ov-kw-item');
      if (kw) {
        if (_polarityState && _polBlockCurrent) {   // 极性深读关键词
          if (_polWordTipSticky) return;   // sticky 词最高级：hover 不覆盖 tip（全局逻辑）
          const it = _findPolWord(kw.dataset.topic);
          if (it) { const { anchors } = _resolveLocAnchors(_polarityState.layer, it.locs || []); showLocTips(anchors); }
          _highlightPolBlockCell(_polBlockCurrent.dom, _polBlockCurrent.elm, true);
          return;
        }
        if (!kw.classList.contains('ov-kw-block')) {   // 综合：原 top10 联动（极性 block 卡无 topic，跳过）
          _clearSync(); const r = _topKeywordCells(_overviewLayer.fc.features, kw.dataset.topic, 10); if (r.cells.length) highlightCellSet(r.cells, _overviewLayer); _syncFromKeyword(kw.dataset.topic); return;
        }
      }
    });
    pane.addEventListener('mouseout', (e) => {
      // 极性关键词 leave → 清地点 tip（除非 sticky 词）+ 清矩阵块高亮
      if (e.target.closest('.ov-kw-item') && _polarityState) {
        if (!_polWordTipSticky) clearLocTips();
        _highlightPolBlockCell(_polBlockCurrent && _polBlockCurrent.dom, _polBlockCurrent && _polBlockCurrent.elm, false);
        return;
      }
      const onItem = e.target.closest('.ov-pie-slice') || e.target.closest('.mx-cell[data-dom]') || e.target.closest('.ov-kw-item');
      if (!onItem) return;
      clearHighlightCellSet(); _clearSync();
      // 极性矩阵 leave → 还原 sticky 块词组 或 恢复"该极性全部关键词"（无 sticky 时）
      if (_polarityState && e.target.closest('.mx-cell[data-dom]')) {
        if (_polBlockSticky) _renderBlockKw(_polarityState.layer, _polarityState.pol, _polBlockSticky.dom, _polBlockSticky.elm);
        else _renderDefaultKw(_polarityState.layer, _polarityState.pol);
      }
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
      // 矩阵格 → 锁定/释放该 domain×element 桶
      const mx = e.target.closest('.mx-cell[data-dom]');
      if (mx) {
        const dom = mx.dataset.dom, elm = mx.dataset.elm;
        if (_polarityState) {   // 极性深读：toggle sticky 块（词组长显 + 块聚合域橙柱体，再点释放）
          if (_polBlockSticky && _polBlockSticky.dom === dom && _polBlockSticky.elm === elm) {
            _polBlockSticky = null; _polWordTipSticky = null; _renderDefaultKw(_polarityState.layer, _polarityState.pol); resetHighlightCellSet();
          } else {
            _polWordTipSticky = null;   // 切块 → 清词 sticky
            _polBlockSticky = { dom, elm }; _renderBlockKw(_polarityState.layer, _polarityState.pol, dom, elm);
            const cells = _cellsByBucket(_overviewLayer.fc.features, dom, elm);
            toggleStickyHighlight(cells, _overviewLayer, 'polmx:' + dom + '|' + elm);
          }
          return;
        }
        const cells = _cellsByBucket(_overviewLayer.fc.features, dom, elm);
        const locked = toggleStickyHighlight(cells, _overviewLayer, 'mx:' + dom + '|' + elm);
        _clearStickySync();
        const mtx = mx.closest('.ov-matrix');
        if (mtx) mtx.querySelectorAll('.mx-cell.is-sticky').forEach((c) => c.classList.remove('is-sticky'));
        if (locked) { mx.classList.add('is-sticky'); _sticky = { type: 'mx', dom, elm }; _applyStickySync('mx', dom, elm); }
        else _sticky = null;
        return;
      }
      // 关键词 → sticky + 联动
      const kw = e.target.closest('.ov-kw-item');
      if (kw) {
        if (_polarityState && _polBlockCurrent) {   // 极性关键词：toggle sticky 词 + 地点 tip + 词聚合域橙柱体（⊆ 块聚合域）
          const word = kw.dataset.topic;
          const wrap = kw.closest('.ov-keywords');
          if (wrap) wrap.querySelectorAll('.ov-kw-item.is-sticky').forEach((x) => x.classList.remove('is-sticky'));
          if (_polWordTipSticky === word) {
            _polWordTipSticky = null; clearLocTips(); resetHighlightCellSet();   // 释放：清 tip + 词 sticky + 柱体
          } else {
            _polWordTipSticky = word;
            kw.classList.add('is-sticky');
            const it = _findPolWord(word);
            if (it) {
              const { cells, anchors } = _resolveLocAnchors(_polarityState.layer, it.locs || []);
              showLocTips(anchors);
              if (cells.length) toggleStickyHighlight(cells, _overviewLayer, 'polkw:' + word);   // 词聚合域橙（⊆ 块聚合域）
            }
          }
          return;
        }
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
  if (name === 'table') onTableTabActivated();   // 懒渲染：切到 Table 才建表（避免导入冻屏）
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
  // 视角切换（2D↔3D）产生同 fc 新 pair 层（fc 引用相同）→ 极性深读状态迁移到新层：
  // 防 setOverview 误判"换层"切回综合 Tab + 保极性 paint（_applyPolarityView 重敷）。
  if (_polarityState && _polarityState.layer && focus && focus.fc
      && focus.fc === _polarityState.layer.fc && focus.id !== _polarityState.layer.id) {
    _polarityState.layer = focus;
    _applyPolarityView(focus, _polarityState.pol);
    _lastOverviewLayerId = focus.id;   // 视为同层 → 不触发下方 activateOvTab('layer')
  }
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
  if (!st) { return; }
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
  _resetPolKwState();   // 清词区 sticky + 地点 tip
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
  _resetPolKwState();   // 入极性深读：清旧 sticky 词/块 + 地点 tip（保 pol 若同层）
  _polarityState = { layer, pol };
  _applyPolarityView(layer, pol);
  pane.innerHTML = _polarityTabBarHtml(pol) + _polarityBodyHtml(layer, pol);
  _wirePolarityTabs(layer);
  _renderDefaultKw(layer, pol);   // 默认显示该极性全部关键词（多→少）；hover/click 块再切换
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
      _resetPolKwState();   // 切极性：清旧 sticky 词/块 + 地点 tip
      _polarityState = { layer, pol };
      _applyPolarityView(layer, pol);
      pane.querySelectorAll('.ov-pol-tab').forEach((t) => t.classList.toggle('is-active', t.dataset.pol === pol));
      const body = pane.querySelector('.ov-pol-body');
      if (body) body.outerHTML = _polarityBodyHtml(layer, pol);
      _renderDefaultKw(layer, pol);   // 切极性 → 恢复"该极性全部关键词"
    }));
}

/** 极性深读 body：极性总览 count（带占比）+ 按极性数单元的归因矩阵 + 关键词/热门话题（默认 hint，hover 块动态填）。
 *  照搬原 _singlePolBody 呈现（占比 / cellSize 话语 / 单位），仅矩阵口径改"该极性点数>0 的单元数"。 */
function _polarityBodyHtml(layer, pol) {
  const feats = (layer.fc && layer.fc.features) || [];
  const ui = (layer.paint && layer.paint._ui) || {};
  const nField = (POLARITY_GRID[pol] || {}).nField;
  let ptTotal = 0;
  for (const f of feats) ptTotal += ((f.properties || {})[nField] || 0);
  const polLabel = { positive: '积极', negative: '消极', neutral: '中性' }[pol] || '极性';
  const cityTotal = _cityTotalOf(ui);
  const yPct = (cityTotal && ptTotal) ? Math.round(ptTotal / cityTotal * 100) : null;
  const countLine = ptTotal
    ? `<div class="ov-count-line">偏<b>${polLabel}</b>的情绪点数为 <b data-kpi="total">${ptTotal}</b> 个${yPct != null ? `，占城市情绪总量的 <b data-kpi="pct">${yPct}%</b>` : ''}</div>`
    : `<div class="ov-count-line muted">该极性无情绪点数据</div>`;
  const { cell, total: polCellCount } = _matrix4x5ByPolarity(feats, pol);
  const cs = ui.cellSize || 400;
  return `<div class="ov-pol-body">
    <div class="ov-tier-sub">极性总览</div>${countLine}
    <div class="ov-tier-sub">归因矩阵${_unit('个单元')}<span class="info-i" data-tip="按当前极性重计：每块 = 该 domain×element 下该极性点数>0 的单元数（每格计 1，与地图 filter 同口径）。颜色按本矩阵数量三级（深紫最多→浅紫最少）。悬停/点击 → 下方关键词动态切换 + 地图同步高亮该桶单元。">i</span></div>${_matrixIntro(`通过空间聚合，共生成 <b>${polCellCount}</b> 个<b>${polLabel}</b>标准单元（${cs}m），4×5 归因如下（数字 = 该维度 ${polLabel} 单元数）：`)}${_singlePolMatrixHtml(cell)}
    <div class="ov-tier-sub">关键词/热门话题${_unit('个情绪点')}<span class="info-i" data-tip="默认显示该极性下<b>全部</b>关键词/热门话题（按相关点数从多到少）。悬停/点击上方矩阵块 → 切换为该维度关键词（click 锁定长显）；移走 / 取消选中 → 恢复全部。悬停/点击关键词 → 地图投射地点 tip（对应聚合域 3D 柱体）。填充条 = 相对点数占比，右数字 = 相关情绪点数。本数据为<b>演示模拟副本</b>，正式管线接入后替换。">i</span></div>
    <div class="ov-block-kw" id="ov-block-kw"><div class="ov-placeholder muted">加载中…</div></div>
  </div>`;
}

/** 按极性重计 4×5：块 count = "该极性点数>0 的单元数"（每格计 1，与地图 _grid_n_<pol>>0 filter 同口径 = 所见即所计）。
 *  单位"个单元"（非情绪点数）。返回 {cell, total}：total = 该极性单元总数。 */
function _matrix4x5ByPolarity(feats, pol) {
  const nField = (POLARITY_GRID[pol] || {}).nField;
  const cell = {};
  let total = 0;
  if (!nField) return { cell, total };
  for (const f of feats) {
    const p = f.properties || {};
    if (!p.domain_top || !p.element_top) continue;
    if ((p[nField] || 0) <= 0) continue;   // 仅数该极性点数>0 的单元（与地图 filter 同口径）
    const k = p.domain_top + '|' + p.element_top;
    if (!cell[k]) cell[k] = { n: 0, piSum: 0, piCnt: 0 };
    cell[k].n += 1;
    total++;
  }
  return { cell, total };
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

/** 极性深读关键词区状态。
 *  _polBlockCurrent = 当前 #ov-block-kw 显示的块 {dom, elm, items}（供 word hover/click 查 locs）。
 *  _polBlockSticky = sticky 矩阵块 {dom,elm}（长显词组，矩阵 leave 不清）；null=空态。
 *  _polWordTipSticky = sticky 关键词（地点 tip 长显）的 word；null=瞬时。 */
let _polBlockCurrent = null;
let _polBlockSticky = null;
let _polWordTipSticky = null;

/** 把指定 (极性, domain×element) 块的副本关键词渲染进 #ov-block-kw，照搬原 .ov-kw-sp 卡片（fill bar + 词 + 地点 + 数字）。 */
function _renderBlockKw(layer, pol, dom, elm) {
  const el = document.getElementById('ov-block-kw');
  if (!el) return;
  const T = (layer && (layer.timeTag || deriveTimeTag(layer.fc))) || 'T3';
  _loadDemoKw().then((kw) => {
    if (!kw || !kw[T] || !kw[T][pol]) { _polBlockCurrent = null; el.innerHTML = `<div class="ov-placeholder muted">副本缺失 ${T}/${pol}（演示数据未就绪）</div>`; return; }
    const items = kw[T][pol][dom + '|' + elm] || [];
    if (!items.length) { _polBlockCurrent = null; el.innerHTML = `<div class="ov-placeholder muted">该维度无高频关键词</div>`; return; }
    const sorted = items.slice().sort((a, b) => (b.n || 0) - (a.n || 0));
    const max = Math.max(1, ...sorted.map((it) => it.n || 0));
    const sign = { positive: 'pos', neutral: 'neu', negative: 'neg' }[pol] || 'pos';
    _polBlockCurrent = { dom, elm, items: sorted };
    el.innerHTML = `<div class="ov-keywords ov-keywords-sp">${sorted.map((it) => {
      const locs = (it.locs || []).map((l) => l.name).filter(Boolean).slice(0, 4).join('、');
      const locHtml = locs ? `<div class="ov-kw-locs">${locs}</div>` : `<div class="ov-kw-locs muted">—</div>`;
      const sticky = _polWordTipSticky === it.word ? ' is-sticky' : '';
      return `<div class="ov-kw-item ov-kw-sp${sticky}" data-topic="${it.word}" data-sign="${sign}" title="${it.word}（${it.n} 点）· 悬停/点击看地点 tip">
        <span class="ov-kw-fill" style="width:${Math.max(20, (it.n / max) * 100)}%"></span>
        <div class="ov-kw-left"><span class="ov-kw-word">${it.word}</span><span class="ov-kw-num">${it.n}</span></div>
        ${locHtml}
      </div>`;
    }).join('')}</div>`;
  });
}

/** 清空 #ov-block-kw 回 hint（空态：无操作时不残留词组）。 */
function _clearBlockKw() {
  _polBlockCurrent = null;
  const el = document.getElementById('ov-block-kw');
  if (el) el.innerHTML = `<div class="ov-placeholder muted">悬停 / 点击上方矩阵块查看该维度关键词</div>`;
}

/** 默认态：显示该极性【全部】关键词（合并 demo JSON 所有块，按 word 去重 n 求和，降序）。
 *  与块视图(_renderBlockKw)同源 → 块视图即"默认全部"的某块切片，hover/click 块切换连贯。
 *  demo 副本缺失 → 回退 _singlePolKeywordsHtml（cell topic_top 聚合，真实数据）。 */
function _renderDefaultKw(layer, pol) {
  const el = document.getElementById('ov-block-kw');
  if (!el || !layer) return;
  const T = (layer.timeTag || deriveTimeTag(layer.fc)) || 'T3';
  const sign = { positive: 'pos', neutral: 'neu', negative: 'neg' }[pol] || 'pos';
  const cardHtml = (it, max) => {
    const locs = (it.locs || []).map((l) => l && l.name).filter(Boolean).slice(0, 4).join('、');
    const locHtml = locs ? `<div class="ov-kw-locs">${locs}</div>` : `<div class="ov-kw-locs muted">—</div>`;
    const sticky = _polWordTipSticky === it.word ? ' is-sticky' : '';
    return `<div class="ov-kw-item ov-kw-sp${sticky}" data-topic="${it.word}" data-sign="${sign}" title="${it.word}（${it.n} 点）· 悬停/点击看地点 tip">
      <span class="ov-kw-fill" style="width:${Math.max(20, (it.n / max) * 100)}%"></span>
      <div class="ov-kw-left"><span class="ov-kw-word">${it.word}</span><span class="ov-kw-num">${it.n}</span></div>
      ${locHtml}
    </div>`;
  };
  _loadDemoKw().then((kw) => {
    if (!kw || !kw[T] || !kw[T][pol]) {                // 副本缺失 → 回退 cell topic_top 聚合
      _polBlockCurrent = null;
      el.innerHTML = _singlePolKeywordsHtml((layer.fc && layer.fc.features) || [], pol);
      return;
    }
    const merged = new Map();                          // word → {word,n,locs}
    for (const key in kw[T][pol]) {
      for (const it of kw[T][pol][key] || []) {
        if (!merged.has(it.word)) merged.set(it.word, { word: it.word, n: 0, locs: it.locs || [] });
        merged.get(it.word).n += (it.n || 0);
      }
    }
    const sorted = [...merged.values()].sort((a, b) => (b.n || 0) - (a.n || 0));
    if (!sorted.length) { _polBlockCurrent = null; el.innerHTML = `<div class="ov-placeholder muted">该极性无高频关键词</div>`; return; }
    const max = Math.max(1, ...sorted.map((it) => it.n || 0));
    _polBlockCurrent = { dom: null, elm: null, items: sorted };   // 供 word hover/click 查 locs（块联动时被 _renderBlockKw 覆盖）
    el.innerHTML = `<div class="ov-keywords ov-keywords-sp">${sorted.map((it) => cardHtml(it, max)).join('')}</div>`;
  });
}

/** 在 _polBlockCurrent.items 中按 word 找词条（含 locs）。 */
function _findPolWord(word) {
  if (!_polBlockCurrent || !_polBlockCurrent.items) return null;
  return _polBlockCurrent.items.find((it) => it.word === word) || null;
}

/** loc.name → 真实坐标：grid 源点层按 area_seed/spatial_hotspot 含地名找 POI → 最近 cell._center。
 *  **数据为准**（用户 POI 准），绝不用猜测坐标（修"奥体错位"类致命错——硬编码 lngLat 偏移致错 cell）。
 *  locs 元素支持 string 或 {name}。返回 {cells:[features], anchors:[{name,lng,lat}]}；数据无该 POI → 跳过。 */
function _resolveLocAnchors(layer, locs) {
  const out = { cells: [], anchors: [] };
  if (!layer || !locs || !locs.length) return out;
  const ui = (layer.paint && layer.paint._ui) || {};
  const srcId = ui.source || '';
  let pts = [];
  if (srcId.startsWith('group:')) {
    const g = getLayer(srcId.slice(6));
    if (g) for (const cid of (g.children || [])) { const c = getLayer(cid); if (c && c.fc) pts = pts.concat(c.fc.features || []); }
  } else if (srcId.startsWith('layer:')) {
    const c = getLayer(srcId.slice(7)); if (c && c.fc) pts = c.fc.features || [];
  }
  const cells = (layer.fc && layer.fc.features) || [];
  const seenCell = new Set();
  for (const loc of locs.slice(0, 8)) {
    const name = typeof loc === 'string' ? loc : (loc && loc.name);
    if (!name) continue;
    const matches = [];
    for (const p of pts) {
      if (!p || !p.properties || !p.geometry || p.geometry.type !== 'Point') continue;
      const a = p.properties.area_seed || '';
      const h = p.properties.spatial_hotspot || '';
      if ((a && a.includes(name)) || (h && h.includes(name))) matches.push(p);
    }
    if (!matches.length) continue;   // 数据无该 POI → 跳过（不错误指向）
    for (const m of matches.slice(0, 3)) {
      const [lng, lat] = m.geometry.coordinates;
      if (lng == null || lat == null) continue;
      let best = null, bestD = Infinity;
      for (const f of cells) {
        const c = (f.properties || {})._center;
        if (!c) continue;
        const d = (c[0] - lng) ** 2 + (c[1] - lat) ** 2;
        if (d < bestD) { bestD = d; best = f; }
      }
      if (best) {
        const c = best.properties._center;
        const k = c[0].toFixed(5) + ',' + c[1].toFixed(5);
        if (seenCell.has(k)) continue;
        seenCell.add(k);
        out.cells.push(best);
        out.anchors.push({ name, lng: c[0], lat: c[1] });
        if (out.anchors.length >= 8) return out;
      }
    }
  }
  return out;
}

/** 高亮/取消极性深读当前块对应的矩阵格（word hover → block 反向联动）。 */
function _highlightPolBlockCell(dom, elm, on) {
  if (!dom || !elm) return;
  const c = document.querySelector(`#ov-polarity-pane .mx-cell[data-dom="${dom}"][data-elm="${elm}"]`);
  if (c) c.classList.toggle('is-synced', on);
}

/** 重极致性深读瞬时态（切极性/换层/离开时）：清 sticky + 地点 tip + 柱体橙 + 词区。 */
function _resetPolKwState() {
  _polBlockSticky = null;
  _polWordTipSticky = null;
  _polBlockCurrent = null;
  clearLocTips();
  resetHighlightCellSet();
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
        ? `<div class="ov-count-line">共 <b data-kpi="total">${total}</b> 个 · 积极 <b data-kpi="pos">${posN}</b> · 消极 <b data-kpi="neg">${negN}</b> · 中性 <b data-kpi="neu">${neuN}</b></div>` : '';
      const overviewRow = pieHtml
        ? `<div class="ov-tier-sub">数据总览${_unit('个点')}<span class="info-i" data-tip="饼图悬停/点击某极性 → 地图同步高亮该极性主导的网格；矩阵、关键词同理。点击锁定，再次点击释放。">i</span></div>
           ${countLine}
           <div class="ov-overview-row ov-ov-pie-row">${pieHtml}</div>` : '';
      body = `${overviewRow}
        <div class="ov-tier-sub">归因矩阵${_unit('个单元')}<span class="info-i" data-tip="4 大治理领域 × 5 要素 的情绪归因矩阵。悬停/点击某格 → 地图同步高亮该领域×要素交集的网格。行/列标签下数字 = 该领域/要素单元总数。">i</span></div>${_matrixIntro(`通过空间聚合分析，共生成 <b>${feats.length}</b> 个标准单元（${ui.cellSize || 400}m），<b>"4维度×5要素"</b>归因统计如下（数字代表该维度的单元数量，颜色代表该维度的极性倾向）：`)}${_matrixHtml(cell)}
        <div class="ov-tier-sub">关键词Top10${_unit('个情绪点')}<span class="info-i" data-tip="按各要素正/中/负情绪点数排名的高频城市关键词。点击某词 → 地图定位并高亮其最强聚集的若干柱体。">i</span></div>${_keywordsHtml(feats)}`;
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

// ── Table tab ── geojson.io 风格通用属性表：工具条（搜索）+ 表格 + 三点菜单占位。
//    L2 点层列顺序：id → 极性 → 地点 → 评论 → 分数 …（极性第 2 列，便于按极性扫读）。
//    性能铁律：精选列（不铺全部 ~30 key）+ 渲染封顶 200 行 + Table 未激活时懒渲染
//    （2500 点 × 30 列全量 innerHTML 会冻屏；导入时用户在 Overview，更不能后台建表）。
let _baseFeats = [];       // 当前图层全部 features（fc 优先，回退 layer.fc，覆盖分析层）
let _tableCols = [];       // 当前列定义 [{key,label,get?}]
let _tableQuery = '';      // 搜索词（小写）
let _tableDirty = false;   // 数据已更新但表格未渲染（切到 Table 标签时补渲）
let _lastTableLayerId = null;
let _tableEmptyHint = null;  // 层级空态文案（如 L1 网格"待开发"）
let _tableLayer = null;       // 当前表格所显层（行选中地图高亮用）
let _tableSelFeat = null;     // 当前选中行对应 feature（网格行选中态）
let _tblBindInit = false;  // 工具条事件幂等绑定
let _tableRows = [];       // 当前过滤后全部行（虚拟化数据源——全量可滚，只画可见）
let _tblRAF = 0;           // 滚动重渲 rAF 句柄（节流）
const _ROW_H = 33;         // 行高 px 初估（首渲后按 offsetHeight 实测校准；geojson.io HEIGHT=33）
const _OVERSCAN = 4;       // 视口上下额外渲染行数（缓冲，减滚动边缘闪白）

const _COL_LABEL = {
  // L2 点层
  id_e: 'ID', _loc: '地点', text: '评论',
  polarity: '极性', score: '分数', emotion_type: '情绪类型',
  source: '来源', publish_time: '发布时间', created_at: '创建时间',
  emotion_intensity: '情绪强度', l2_confidence: 'L2置信度', l1_confidence: 'L1置信度',
  keywords: '关键词', primary_emotion: '主情绪', domain: '领域', element: '要素',
  like_count: '点赞', comment_count: '评论数', tags: '标签',
  area_seed: '锚点', area_tag: '区域标签', zone: '聚合域', narrative_zone: '叙事区',
  spatial_hotspot: '空间热点', spatial_type: '空间类型', location_mentioned: '提及地点',
  relevance: '相关性', relevance_category: '相关类目', scope: '范围', url: '链接',
  category: '类别', target_type: '目标类型', target_detail: '目标详情',
  // 网格 / 分析层（cell schema）
  name: '名称', point_count: '点数', polarity_index: '极性指数',
  domain_top: '主领域', element_top: '主要素', issue_label: '问题识别',
  topic_top: '话题/关键词', cell_id: '格号',
  n_positive: '积极数', n_negative: '消极数', n_neutral: '中性数',
  n_very_positive: '强积极数', n_very_negative: '强消极数',
  hotness: '热度', _attribution: '归因', _suggestion: '建议',
  // 范围 / 几何层
  area: '面积', perimeter: '周长', vertices: '顶点数',
};
const _DROP_KEYS = new Set([         // 坐标 / 内部噪声 / 重复字段，永不显示
  'x_cgcs2000', 'y_cgcs2000', 'has_location', 'crs', 'intensity',
  'polarity_hint', 'time_label', 'text_length', 'urban_value', 'location',
]);

/** 地点合成：place_name → area_seed → location_mentioned → area_tag → spatial_hotspot → zone（首个非空）。 */
function _locOf(p) {
  return p.place_name || p.area_seed || p.location_mentioned || p.area_tag || p.spatial_hotspot || p.zone || '';
}

// ── 虚拟列（computed，按层 schema 合成；归因/建议为 L4 占位——用户选"现有字段映射占位"，L4 接入后替换）──
const _SUGGEST_BY_DOMAIN = {
  urban_planning: '优化布局 / 增补设施',
  urban_renewal: '纳入更新改造 / 品质提升',
  urban_operation: '加强运维 / 服务保障',
  urban_governance: '专项治理 / 诉求回应',
};
function _attrOf(p) {
  const d = DOMAIN_LABEL[p.domain_top] || p.domain_top;
  const e = ELEMENT_LABEL[p.element_top] || p.element_top;
  return (d && e) ? `${d}×${e}` : (d || e || '');
}
function _sugOf(p) { return _SUGGEST_BY_DOMAIN[p.domain_top] || ''; }

// ── 各层优先列清单（第一观感）；其后按出现顺序追加其余非噪声字段 ──
const _COLS_L1_POINT = ['id_e', '_loc', 'text', 'score', 'keywords', 'primary_emotion', 'source', 'publish_time'];
const _COLS_L2_POINT = ['id_e', 'polarity', '_loc', 'text', 'score', 'emotion_type', 'source', 'publish_time'];
const _COLS_L2_GRID_OVERALL  = ['point_count', 'polarity_index', '_loc', 'topic_top', 'issue_label', '_attribution', '_suggestion'];
const _COLS_L2_GRID_POLARITY = ['point_count', '_loc', 'topic_top', 'issue_label', '_attribution', '_suggestion'];
const _COLS_GENERIC = ['id_e', '_loc', 'text', 'polarity', 'score', 'emotion_type', 'source', 'publish_time'];

function _isGridLayer(layer) {
  const ui = layer && layer.paint && layer.paint._ui;
  return !!(layer && layer.kind === 'polygon' && ui && ui.tool === 'grid');
}

/** 按层类型选优先列 + 网格层默认排序键。返回 { priority, sortKey, emptyHint }。 */
function _layerScheme(layer) {
  if (layer && isEmotionPointLayer(layer)) {
    return { priority: layerLevel(layer) === 'L1' ? _COLS_L1_POINT : _COLS_L2_POINT };
  }
  if (layer && _isGridLayer(layer)) {
    const lv = layerLevel(layer);
    if (lv === 'L1') return { priority: [], emptyHint: 'L1 网格聚合 Table 待开发' };
    if (lv === 'L2') {
      const pol = (layer.paint._ui.polarity) || 'overall';
      return pol === 'overall'
        ? { priority: _COLS_L2_GRID_OVERALL, sortKey: 'point_count' }
        : { priority: _COLS_L2_GRID_POLARITY, sortKey: 'point_count' };
    }
  }
  return { priority: _COLS_GENERIC };   // 范围 / 线 / 其他 → 通用
}

/** 按层构建列：优先列（数据存在 / 虚拟列可合成）→ 其余属性按序追加。返回 { cols, emptyHint }。 */
function _colsFor(layer, feats) {
  const { priority, emptyHint } = _layerScheme(layer);
  if (emptyHint) return { cols: [], emptyHint };
  const keySet = new Set();
  const order = [];
  for (const f of feats) {
    const p = f.properties || {};
    for (const k of Object.keys(p)) {
      if (_DROP_KEYS.has(k) || keySet.has(k)) continue;
      keySet.add(k); order.push(k);
    }
  }
  const VCOLS = {
    _loc: { get: (f) => _locOf(f.properties || {}), avail: feats.some((f) => _locOf(f.properties || {})) },
    _attribution: { get: (f) => _attrOf(f.properties || {}), avail: keySet.has('domain_top') || keySet.has('element_top') },
    _suggestion: { get: (f) => _sugOf(f.properties || {}), avail: keySet.has('domain_top') },
  };
  const cols = [];
  const seen = new Set();
  const pushCol = (k) => {
    if (seen.has(k)) return;
    if (VCOLS[k]) { if (VCOLS[k].avail) { cols.push({ key: k, label: _COL_LABEL[k] || k, get: VCOLS[k].get }); seen.add(k); } return; }
    if (keySet.has(k)) { cols.push({ key: k, label: _COL_LABEL[k] || k }); seen.add(k); }
  };
  for (const k of priority) pushCol(k);
  for (const k of order) pushCol(k);
  return { cols };
}

// ── 列宽（colgroup 驱动；_colWidth 存用户拖拽会话内持久；其余按内容自适应测宽，减少空白）──
const _colWidth = new Map();   // key → px（用户拖拽覆盖；优先级最高）
const _colWcache = new Map();  // key → px（_renderTable 时按内容测宽缓存）
/** 按列内容测宽（采样前 120 行，取最长值×8px+padding，clamp 56~200）；评论固定 300、地点 120。*/
function _measureColWidth(col, feats) {
  const key = col.key;
  if (key === 'text') return 300;          // 评论列固定宽（主信息载体）
  if (key === '_loc') return 120;          // 地点列略宽（地名）
  let maxLen = String(col.label || key).length + 1;
  const sample = feats.length > 120 ? feats.slice(0, 120) : feats;
  for (const f of sample) {
    const len = String(_cellValue(col, f) ?? '').length;
    if (len > maxLen) maxLen = len;
    if (maxLen > 28) break;                // 超长值按上限（列内省略号截断）
  }
  return Math.max(56, Math.min(200, maxLen * 8 + 18));
}
function _colW(key) { return _colWcache.get(key) ?? 110; }

function _cellValue(col, f) {
  if (col.get) return col.get(f);
  return (f.properties && f.properties[col.key]) ?? '';
}

/** 渲染所用 features = 全部 → 搜索过滤。 */
function _visibleFeats() {
  const q = _tableQuery;
  if (!q) return _baseFeats;
  return _baseFeats.filter((f) => _tableCols.some((c) => String(_cellValue(c, f) ?? '').toLowerCase().includes(q)));
}

/** Table 标签当前是否激活（懒渲染判据）。 */
function _tableActive() {
  const p = document.querySelector('.tab-pane[data-pane="table"]');
  return !!(p && p.classList.contains('is-active'));
}

function _updateCount(shownN, totalN) {
  const el = document.getElementById('tbl-count');
  if (!el) return;
  el.textContent = _tableQuery ? `命中 ${shownN} / 共 ${totalN} 条` : `共 ${totalN} 条记录`;
}

function _renderTable() {
  const tbl = document.getElementById('data-table');
  if (!tbl) return;
  const cols = _tableCols;
  if (_tableEmptyHint) {
    tbl.innerHTML = `<tbody><tr><td style="padding:32px 16px;text-align:center;color:#888">${_tableEmptyHint}</td></tr></tbody>`;
    _updateCount(0, 0);
    return;
  }
  const rows = _visibleFeats();
  _tableRows = rows;
  _updateCount(rows.length, _baseFeats.length);
  // colgroup：列宽按内容自适应测宽（用户拖拽优先；评论宽、其余收紧减空白）。table-layout:fixed 严格生效。
  cols.forEach((c) => _colWcache.set(c.key, _colWidth.has(c.key) ? _colWidth.get(c.key) : _measureColWidth(c, _baseFeats)));
  const totalW = cols.reduce((s, c) => s + _colW(c.key), 0);
  const colgroup = `<colgroup>${cols.map((c) => `<col data-col="${c.key}" style="width:${_colW(c.key)}px">`).join('')}</colgroup>`;
  const head = `<thead><tr>${cols.map((c) =>
    `<th data-col="${c.key}"><span class="th-label">${c.label}</span><span class="th-menu-trigger" title="列操作">⋮</span><span class="col-resize" data-col="${c.key}" title="拖拽调整列宽"></span></th>`).join('')}</tr></thead>`;
  if (!cols.length) { tbl.innerHTML = `<tbody><tr><td style="padding:24px;text-align:center;color:#888">暂无数据</td></tr></tbody>`; return; }
  if (!rows.length) { tbl.innerHTML = colgroup + head + `<tbody><tr><td colspan="${cols.length}" style="padding:24px;text-align:center;color:#888">无匹配记录</td></tr></tbody>`; return; }
  // 仅渲 colgroup + 表头 + 空 tbody；行采用虚拟化（_renderVisibleRows 按滚动视口填充）
  tbl.innerHTML = colgroup + head + '<tbody></tbody>';
  tbl.style.minWidth = totalW + 'px';   // 列宽和 > 面板宽 → 水平滚动
  tbl.classList.toggle('is-grid-table', !!(_tableLayer && _isGridLayer(_tableLayer)));   // 网格行可选中
  const wrap = document.querySelector('.tab-pane[data-pane="table"] .table-wrap');
  if (wrap) wrap.scrollTop = 0;
  _renderVisibleRows();
}

/** 虚拟化：只渲染当前滚动视口内的行（+ overscan），上下 spacer 撑出总高 → 万行也不冻屏。
 *  行高首渲后按 offsetHeight 实测校准（_rowPitch），消除 border-collapse 下 1px 漂移。 */
let _rowPitch = _ROW_H;
function _renderVisibleRows() {
  const tbl = document.getElementById('data-table');
  if (!tbl || !_tableRows.length || !_tableCols.length) return;
  const tb = tbl.tBodies[0];
  if (!tb) return;
  const wrap = document.querySelector('.tab-pane[data-pane="table"] .table-wrap');
  const scrollTop = wrap ? wrap.scrollTop : 0;
  const viewH = wrap ? wrap.clientHeight : 600;
  const cols = _tableCols;
  const total = _tableRows.length;
  const start = Math.max(0, Math.floor(scrollTop / _rowPitch) - _OVERSCAN);
  const end = Math.min(total, Math.ceil((scrollTop + viewH) / _rowPitch) + _OVERSCAN);
  const slice = _tableRows.slice(start, end);
  const colors = emotionColors();
  const esc = (v) => String(v).replace(/[<>]/g, (s) => s === '<' ? '&lt;' : '&gt;');
  const cell = (c, f) => {
    const v = _cellValue(c, f);
    if (c.key === 'polarity') {
      const pol = v || 'Neutral';
      const cc = colors[pol] || colors['Neutral'];
      return `<td><span class="td-dot" style="background:${cc}"></span>${POLARITY_LABEL[pol] || pol}</td>`;
    }
    const cls = c.key === 'text' ? ' class="col-text"' : c.key === '_loc' ? ' class="col-loc"' : '';
    return `<td${cls}>${esc(v)}</td>`;
  };
  const rowsHtml = slice.map((f, i) => `<tr class="tbl-row${f === _tableSelFeat ? ' is-selected' : ''}" data-idx="${start + i}">${cols.map((c) => cell(c, f)).join('')}</tr>`).join('');
  const topPad = start * _rowPitch, botPad = Math.max(0, (total - end) * _rowPitch);
  tb.innerHTML =
    `<tr class="tbl-spacer" aria-hidden="true"><td colspan="${cols.length}"><div style="height:${topPad}px"></div></td></tr>` +
    rowsHtml +
    `<tr class="tbl-spacer" aria-hidden="true"><td colspan="${cols.length}"><div style="height:${botPad}px"></div></td></tr>`;
  // 实测行高校准（border-collapse 下 offsetHeight 可能 33/34）
  const firstRow = tb.querySelector('.tbl-row');
  if (firstRow) _rowPitch = firstRow.offsetHeight || _rowPitch;
}

/** 三点菜单（占位）：定位到触发器下方，列动作均标"待开发"。 */
function _openThMenu(trigger) {
  const menu = document.getElementById('th-menu');
  if (!menu) return;
  menu.innerHTML = `
    <div class="th-menu-item"><span>升序排列</span><span class="th-menu-tag">待开发</span></div>
    <div class="th-menu-item"><span>降序排列</span><span class="th-menu-tag">待开发</span></div>
    <div class="th-menu-sep"></div>
    <div class="th-menu-item"><span>隐藏该列</span><span class="th-menu-tag">待开发</span></div>
    <div class="th-menu-item"><span>编辑列</span><span class="th-menu-tag">待开发</span></div>`;
  menu.hidden = false;
  const r = trigger.getBoundingClientRect();
  const mw = menu.offsetWidth || 150;
  menu.style.left = Math.max(8, Math.min(r.right - mw, window.innerWidth - mw - 8)) + 'px';
  menu.style.top = (r.bottom + 4) + 'px';
}

/** 工具条事件幂等绑定：搜索 + 三点菜单（事件委托）+ 滚动虚拟化重渲（rAF 节流）。 */
function _bindToolbar() {
  if (_tblBindInit) return;
  _tblBindInit = true;
  const input = document.getElementById('tbl-search-input');
  if (input) input.addEventListener('input', () => { _tableQuery = (input.value || '').trim().toLowerCase(); _renderTable(); });
  // 数据下拉（自定义）：trigger 开关 / option 选层 / 外部点关闭
  const trig = document.getElementById('tbl-ds-trigger');
  if (trig) trig.addEventListener('click', (e) => { e.stopPropagation(); _toggleDsPanel(); });
  const panel = document.getElementById('tbl-ds-panel');
  if (panel) panel.addEventListener('click', (e) => {
    const opt = e.target.closest('.tbl-ds-opt'); if (!opt) return;
    const l = getLayer(opt.dataset.id);
    if (l) { _loadTableLayer(l); _setDsCurrent(l); _syncMapToLayer(l); }   // 选层 → 表格 + 地图联动
    _toggleDsPanel(false);
  });
  document.addEventListener('click', (e) => { if (!e.target.closest('.tbl-dataset')) _toggleDsPanel(false); });
  const tbl = document.getElementById('data-table');
  if (tbl) {
    // 列宽拖拽：th 右缘 .col-resize mousedown → document mousemove 改 <col> 宽 + 记 _colWidth（会话持久）
    tbl.addEventListener('mousedown', (e) => {
      const handle = e.target.closest('.col-resize');
      if (!handle) return;
      e.preventDefault();
      const key = handle.dataset.col;
      const col = tbl.querySelector(`colgroup col[data-col="${key}"]`);
      if (!col) return;
      const startX = e.clientX;
      const startW = col.offsetWidth || _colW(key);
      const onMove = (ev) => {
        const w = Math.max(40, Math.round(startW + (ev.clientX - startX)));
        col.style.width = w + 'px';
        _colWidth.set(key, w); _colWcache.set(key, w);
        const totalW = _tableCols.reduce((s, c) => s + (_colW(c.key)), 0);
        tbl.style.minWidth = totalW + 'px';
      };
      const onUp = () => { document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); };
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });
    tbl.addEventListener('click', (e) => {
      const menuTrig = e.target.closest('.th-menu-trigger');
      if (menuTrig) { _openThMenu(menuTrig); return; }
      // 网格行选中（仅网格聚合层）→ 地图橙色高亮对应聚合域
      const tr = e.target.closest('tr.tbl-row');
      if (tr && _tableLayer && _isGridLayer(_tableLayer)) _toggleRowSel(Number(tr.dataset.idx));
    });
  }
  // 滚动 → 按视口重渲可见行（虚拟化核心；rAF 节流防抖）
  const wrap = document.querySelector('.tab-pane[data-pane="table"] .table-wrap');
  if (wrap) wrap.addEventListener('scroll', () => {
    if (_tblRAF) return;
    _tblRAF = requestAnimationFrame(() => { _tblRAF = 0; _renderVisibleRows(); });
  }, { passive: true });
  document.addEventListener('click', (e) => {
    const menu = document.getElementById('th-menu');
    if (!menu || menu.hidden) return;
    if (!e.target.closest('.th-menu') && !e.target.closest('.th-menu-trigger')) menu.hidden = true;
  });
}

/** Table 标签被激活时补渲（懒渲染入口；activateTab 在切到 table 时调）。 */
export function onTableTabActivated() {
  if (_tableDirty) { _renderTable(); _tableDirty = false; }
}

/** grid 层数据签名（同 sidebar.gridSigOf / map.gridSig）：同 analysis/level/source/cellSize/polarity/polygonLayer 的 2D/3D 互为配对。*/
function _gridSigOf(ui) { return ui ? [ui.analysis, ui.level, ui.source, ui.cellSize, ui.polarity, ui.polygonLayer].join('|') : ''; }

/** 可制表的已载图层（有 features 的非 group 层）。grid 2D/3D 配对按 gridSig 去重为一个代表
 *  （照搬 sidebar.renderLayerList 逻辑——否则下拉出现两条同一标准网格）。*/
function _tableableLayers() {
  const all = getLayers().filter((l) => l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length);
  const grids = all.filter(_isGridLayer);
  if (grids.length < 2) return all;
  const groups = new Map();
  for (const l of grids) {
    const sig = _gridSigOf(l.paint && l.paint._ui);
    if (!groups.has(sig)) groups.set(sig, []);
    groups.get(sig).push(l);
  }
  const skip = new Set();
  for (const [, arr] of groups) {
    if (arr.length < 2) continue;                         // 无配对（单层），不去重
    const rep = arr.find((g) => g.visible) || arr[arr.length - 1];   // 可见优先；兜底取最后
    for (const g of arr) if (g !== rep) skip.add(g.id);
  }
  return skip.size ? all.filter((l) => !skip.has(l.id)) : all;
}

// L 级徽章 class（彩色：L0 灰 / L1 橙 / L2 蓝 / L3 紫 / L4 绿）
const _LV_BADGE = { L0: 'lv-l0', L1: 'lv-l1', L2: 'lv-l2', L3: 'lv-l3', L4: 'lv-l4' };

/** 极性 chip（复用 Layers 数据标签设计语言：综合/积极/消极/中性，配色呼应情绪点色板）。*/
const _POL_CHIP = {
  overall:  { t: '综合', c: 'chip-overall' },
  positive: { t: '积极', c: 'chip-pos' },
  negative: { t: '消极', c: 'chip-neg' },
  neutral:  { t: '中性', c: 'chip-neu' },
};
/** 拆解层 → {lv, lvCls, lvColor, type, time, pol, file}，供下拉标题 chips 渲染。
 *  选择维度 = L 等级 / 类型 / 时间点 / 极性 → chips 凸显；文件名灰淡化（重名靠 chips 区分）。
 *  极性：grid 用 _ui.polarity；L2 点层=综合（含全极性）；与 Layers 数据标签同口径。*/
function _dsParts(layer) {
  const lv = layerLevel(layer) || 'L2';
  const ui = (layer.paint && layer.paint._ui) || {};
  const file = String(layer.srcName || layer.name || '').replace(/[<>]/g, '') || '';
  const t = layer.timeTag || deriveTimeTag(layer.fc) || '';
  let type = '', time = '', pol = null;
  if (ui.tool === 'grid') {
    type = ui.analysis === 'zonal' ? '指定单元网格' : '标准网格';
    time = t; pol = _POL_CHIP[ui.polarity] || _POL_CHIP.overall;   // overall → 综合 chip
  } else if (ui.tool === 'terrain') { type = '情绪地形'; time = t; }
  else if (layer.kind === 'heatmap') { type = '核密度'; }
  else if (isEmotionPointLayer(layer)) { type = '情绪点'; time = t; pol = _POL_CHIP.overall; }   // L2 点层 = 综合
  else { type = layer.kind === 'polygon' ? '范围' : (layer.kind || '图层'); }
  return { lv, lvColor: levelPointColor(lv), type, time, pol, file };
}
const _dsItemHtml = (p) =>
  `<span class="lv-badge" style="background:${p.lvColor}">${p.lv}</span>` +
  `<span class="ds-type">${p.type}</span>` +
  (p.time ? `<span class="ds-chip ds-time">${p.time}</span>` : '') +
  (p.pol ? `<span class="ds-chip ${p.pol.c}">${p.pol.t}</span>` : '') +
  `<span class="ds-file">${p.file}</span>`;

/** 重建数据下拉（自定义）+ 设当前层。*/
function _refreshDataset(selectLayer) {
  const panel = document.getElementById('tbl-ds-panel');
  const layers = _tableableLayers();
  if (panel) {
    const curId = selectLayer && selectLayer.id;
    panel.innerHTML = layers.length
      ? layers.map((l) => `<button class="tbl-ds-opt${l.id === curId ? ' is-cur' : ''}" data-id="${l.id}" role="option" type="button">${_dsItemHtml(_dsParts(l))}</button>`).join('')
      : `<div class="tbl-ds-empty">（暂无数据图层）</div>`;
  }
  const inList = selectLayer && layers.some((l) => l.id === selectLayer.id);
  _setDsCurrent(inList ? selectLayer : (layers[0] || null));
}

/** 设 trigger 当前显示（富文本标题）+ 同步 panel .is-cur。*/
function _setDsCurrent(layer) {
  const cur = document.getElementById('tbl-ds-cur');
  if (cur) cur.innerHTML = layer ? _dsItemHtml(_dsParts(layer)) : '—';
  const panel = document.getElementById('tbl-ds-panel');
  if (panel) panel.querySelectorAll('.tbl-ds-opt').forEach((o) => o.classList.toggle('is-cur', !!(layer && o.dataset.id === layer.id)));
}

/** 开/关下拉浮层。*/
function _toggleDsPanel(open) {
  const root = document.getElementById('tbl-dataset');
  const panel = document.getElementById('tbl-ds-panel');
  const trig = document.getElementById('tbl-ds-trigger');
  if (!root || !panel) return;
  const willOpen = open == null ? panel.hidden : open;
  panel.hidden = !willOpen;
  root.classList.toggle('open', willOpen);
  if (trig) trig.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
}

/** 载入指定层到表格（列策略 + 排序 + 懒渲染）。不触碰下拉，避免 change→load 递归。*/
function _loadTableLayer(layer) {
  // 换层 → 清行选中 + 地图高亮
  if (!_tableLayer || !layer || _tableLayer.id !== layer.id) {
    if (_tableSelFeat) clearHighlightCellSet();
    _tableSelFeat = null;
  }
  _tableLayer = layer;
  let src = (layer && layer.fc && layer.fc.features) ? layer.fc.features : [];
  const lid = layer && layer.id;
  if (lid !== _lastTableLayerId) {
    _tableQuery = '';
    const inp = document.getElementById('tbl-search-input'); if (inp) inp.value = '';
  }
  _lastTableLayerId = lid;
  const built = _colsFor(layer, src);
  _tableCols = built.cols;
  _tableEmptyHint = built.emptyHint || null;
  const scheme = _layerScheme(layer);
  if (scheme.sortKey && src.length && src[0] && src[0].properties && (scheme.sortKey in src[0].properties)) {
    src = src.slice().sort((a, b) => ((b.properties || {})[scheme.sortKey] || 0) - ((a.properties || {})[scheme.sortKey] || 0));
  }
  _baseFeats = src;
  _tableDirty = true;
  if (_tableActive()) { _renderTable(); _tableDirty = false; }
}

/** 网格行选中 toggle：再点同行取消；选中 → 地图橙色高亮该聚合域（延用 highlightCellSet）。*/
function _toggleRowSel(idx) {
  const feat = _tableRows[idx];
  if (!feat || !_tableLayer) return;
  if (_tableSelFeat === feat) { _tableSelFeat = null; clearHighlightCellSet(); }
  else { _tableSelFeat = feat; clearHighlightCellSet(); highlightCellSet([feat], _tableLayer); }
  _renderVisibleRows();
}

/** 下拉选层 → 地图联动：显该层 + enforceMutualExclusion 关其他（除 Range/同组兄弟）+ 按 type 切 2D/3D + 触 layers:changed。
 *  底层逻辑：Overview/Table 操作联动地图同步显示。照搬 sidebar._applyExclusiveOn 范式。 */
function _syncMapToLayer(l) {
  if (!l) return;
  setLayerVisible(l.id, true);
  const hidden = enforceMutualExclusion(l.id);
  for (const hid of hidden) { const hl = getLayer(hid); if (hl) renderLayer(hl); }
  renderLayer(l);
  selectLayer(l.id);
  _applyViewForLayer(l);
  document.dispatchEvent(new CustomEvent('layers:changed'));   // → refreshOverview 跟切下拉/表格
}

/** 按层类型自动切 2D/3D 视角：点/范围=保持；标准网格=3D 柱体；地形=3D；核密度=2D。 */
function _applyViewForLayer(l) {
  const ui = l && l.paint && l.paint._ui;
  if (!ui) return;                       // point / 范围：不动视角
  if (ui.tool === 'grid') setViewMode('3d');        // 标准网格 → 3D 柱体（按签名找/生 3D 配对 + pitch）
  else if (ui.tool === 'terrain') setView3D(true);   // 情绪地形 → 3D
  else setView3D(false);                             // 核密度(heatmap) → 2D
}

export function setTable(_fc, layer, _maxRows = 500) {
  if (!document.getElementById('data-table')) return;
  _refreshDataset(layer);    // 重建下拉 + 选中焦点层（默认随焦点，用户可下拉手切任意层）
  _loadTableLayer(layer);
  _bindToolbar();
}

// ═══ 时间轴 KPI tween（任务2 · 前置：Overview 原地更新）═══════════════════════════
// 设计：tier1/2/3 仍走 innerHTML 初始渲染（承重不动）；时间轴仅 patch 「可动画 KPI」
// DOM 节点（综合 = count line 4 数 + 饼图 svg/legend；极性 = count line total + 矩阵重渲染）。
// 矩阵/饼图事件均 pane 级委托 → replace innerHTML 不丢联动。计数 <b> 带 data-kpi 便于定位。
// 详见 memory: paint-inplace-swap-view（map 侧 setData 同理）、sticky-hover-priority（tween 不触 sticky）。

/** 综合 layer-overview KPI 快照：从 virtualFeats（per-T 聚合）算 {total,pos,neg,neu,agg(5 级)}。 */
export function overviewKpiFromFeats(feats) {
  const agg = { 'Very Positive': 0, Positive: 0, Neutral: 0, Negative: 0, 'Very Negative': 0 };
  for (const f of feats) {
    const p = f.properties || {};
    agg['Very Positive'] += p.n_very_positive || 0;
    agg.Positive += p.n_positive || 0;
    agg.Neutral += p.n_neutral || 0;
    agg.Negative += p.n_negative || 0;
    agg['Very Negative'] += p.n_very_negative || 0;
  }
  const total = agg['Very Positive'] + agg.Positive + agg.Neutral + agg.Negative + agg['Very Negative'];
  return { total, pos: agg['Very Positive'] + agg.Positive, neg: agg['Negative'] + agg['Very Negative'], neu: agg['Neutral'], agg };
}

/** 极性深读 KPI 快照：复用 _matrix4x5ByPolarity（{cell,total}）。tween 用 cell 重渲染矩阵。 */
export function polarityKpiFromFeats(feats, pol) {
  return _matrix4x5ByPolarity(feats, pol);
}

/** 数字 tween：写四舍五入整数（带千分位）。null/undefined 节点跳过。 */
function _setNum(el, v) { if (el) el.textContent = Math.max(0, Math.round(v)).toLocaleString(); }

const _PIE_SEGS = [
  ['Very Negative', L2_NEGATIVE['Very Negative']],
  ['Negative', L2_NEGATIVE['Negative']],
  ['Neutral', L2_NEUTRAL_COLOR],
  ['Positive', L2_POSITIVE['Positive']],
  ['Very Positive', L2_POSITIVE['Very Positive']],
];
/** 饼图 svg inner（path 列表）—— 抽自 _polarPieHtml 同款几何，供 tween 重绘。 */
function _pieSvgInner(agg, total) {
  if (!total) return '';
  const cx = 50, cy = 50, r = 38;
  let a = -Math.PI / 2;
  const paths = [];
  for (const [key, color] of _PIE_SEGS) {
    const n = agg[key] || 0;
    if (n <= 0) continue;
    const sweep = (n / total) * Math.PI * 2;
    const a0 = a, a1 = a + sweep, am = (a0 + a1) / 2;
    const x0 = cx + r * Math.cos(a0), y0 = cy + r * Math.sin(a0);
    const x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1);
    const large = sweep > Math.PI ? 1 : 0;
    const dx = Math.cos(am) * 5, dy = Math.sin(am) * 5;
    paths.push(`<path class="ov-pie-slice" data-pol="${key}" fill="${color}" style="--dx:${dx.toFixed(1)}px;--dy:${dy.toFixed(1)}px" d="M${cx} ${cy} L${x0.toFixed(2)} ${y0.toFixed(2)} A${r} ${r} 0 ${large} 1 ${x1.toFixed(2)} ${y1.toFixed(2)} Z"><title>${POLARITY_LABEL[key]} · ${Math.round(n)}（${(n / total * 100).toFixed(0)}%）</title></path>`);
    a = a1;
  }
  return paths.join('');
}
function _pieLegendInner(agg, total) {
  if (!total) return '';
  return _PIE_SEGS.filter(([k]) => (agg[k] || 0) > 0).map(([k, c]) =>
    `<span class="ov-pie-lg"><span class="ov-pie-dot" style="background:${c}"></span>${POLARITY_LABEL[k]}<i>${Math.round(agg[k])}</i></span>`).join('');
}

/** 综合 KPI patch：count line 4 数 + 饼图 svg/legend。不重建 tier 结构（承重）。 */
export function paintOverallKpi(kpi) {
  const pane = document.getElementById('ov-layer-pane');
  if (!pane || !kpi) return;
  const line = pane.querySelector('.ov-count-line');
  if (line) {
    _setNum(line.querySelector('[data-kpi="total"]'), kpi.total);
    _setNum(line.querySelector('[data-kpi="pos"]'), kpi.pos);
    _setNum(line.querySelector('[data-kpi="neg"]'), kpi.neg);
    _setNum(line.querySelector('[data-kpi="neu"]'), kpi.neu);
  }
  const svg = pane.querySelector('.ov-pie svg');
  if (svg) svg.innerHTML = _pieSvgInner(kpi.agg, kpi.total);
  const lg = pane.querySelector('.ov-pie-legend');
  if (lg) lg.innerHTML = _pieLegendInner(kpi.agg, kpi.total);
}

/** 极性深读 KPI patch：count line total + 矩阵按 cell 重渲染（tier 分位随当前 cell 分布重算）。
 *  事件委托在 pane → replace .ov-matrix 不丢 hover/click 联动。sticky 同步态 tween 期清（切 T = 新数据）。 */
export function paintPolarityKpi(pol, kpi) {
  const pane = document.getElementById('ov-polarity-pane');
  if (!pane || !kpi) return;
  const line = pane.querySelector('.ov-count-line');
  if (line) _setNum(line.querySelector('[data-kpi="total"]'), kpi.total);
  const mx = pane.querySelector('.ov-matrix');
  if (mx && kpi.cell) {
    const tmp = document.createElement('div');
    tmp.innerHTML = _singlePolMatrixHtml(kpi.cell);
    const fresh = tmp.firstElementChild;
    if (fresh) mx.replaceWith(fresh);
  }
}

/** 关键词淡入（错峰末段）：给关键词容器加 .tl-kw-flash 触发 CSS opacity 动画（0→1）。 */
export function flashOverviewKeywords() {
  const panes = [document.getElementById('ov-layer-pane'), document.getElementById('ov-polarity-pane')];
  for (const p of panes) {
    if (!p) continue;
    const kw = p.querySelector('.ov-keywords, #ov-block-kw');
    if (!kw) continue;
    kw.classList.remove('tl-kw-flash');
    void kw.offsetWidth;   // 强制回流重启动画
    kw.classList.add('tl-kw-flash');
  }
}

/** 综合 4×5 矩阵 cell map（按 domain_top×element_top 数格 + pi 均值）。跨 T：n 不变（scaffold 固定）、pi 变（颜色）。 */
export function overallMatrixFromFeats(feats) { return _matrix4x5(feats); }

/** 把综合矩阵 patch 进 #ov-layer-pane（重渲染 .ov-matrix，事件委托在 pane 不丢联动）。
 *  cell = {key:{n,piSum,piCnt}}；timeline 传 lerped pi（piSum=piAvg, piCnt=1 → pi=piAvg）。 */
export function paintOverallMatrix(cell) {
  const pane = document.getElementById('ov-layer-pane');
  if (!pane || !cell) return;
  const mx = pane.querySelector('.ov-matrix');
  if (!mx) return;
  const tmp = document.createElement('div');
  tmp.innerHTML = _matrixHtml(cell);
  const fresh = tmp.firstElementChild;
  if (fresh) mx.replaceWith(fresh);
}

/** 把综合关键词按 feats 重渲染进 #ov-layer-pane（.ov-keywords；topic_top 在 virtual fc 已随 scaffold 拷贝）。
 *  离散切换（不 lerp）——point_count 跨 T 变 → 词次/排名变。 */
export function paintOverallKeywords(feats) {
  const pane = document.getElementById('ov-layer-pane');
  if (!pane || !feats) return;
  const kw = pane.querySelector('.ov-keywords');
  if (!kw) return;
  const tmp = document.createElement('div');
  tmp.innerHTML = _keywordsHtml(feats);
  const fresh = tmp.firstElementChild;
  if (fresh) kw.replaceWith(fresh);
}
