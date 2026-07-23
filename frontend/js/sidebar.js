// ═══ sidebar.js — left panel: collapse/expand, drag, import trigger, layer manager ═══
import { token, getLayers, getLayer, setLayerVisible, removeLayer, layerLevel, layerDisplayColor, levelPointColor, freezeCategoryOrder, selectLayer, getSelectedLayerId, getSelectedLayer, reorderLayers, addLayer, getChildren, categoryOf, CATEGORY_LABEL, applyGroupOrder, reorderGroupSegment, isCollapsed, toggleCollapsed, isGroupFold, toggleGroupFold, getGroupOrder, enforceMutualExclusion, CONFIDENCE_RAMP, L2_POSITIVE, L2_NEGATIVE, L2_NEUTRAL_COLOR, HOTNESS_RAMP } from './state.js';
import { renderLayer, removeLayerFromMap, reorderAllZ, restackZ, toggleGridViewMode, getGridViewMode, fitToLayer } from './map.js';
import { toast } from './toast.js';
import { openSettingsPopover, closeSettingsPopover, openSettingsLayerId, isOpen } from './settings.js';
import { closeParamPanel } from './param-panel.js';
import { openHeatmapDialog } from './heatmap-tool.js';
import { openBufferDialog } from './buffer-tool.js';
import { openGridDialog } from './grid-tool.js';
import { relayoutFloats } from './ai_qa/cpd-state.js';   // CPD ③④：抽屉+浮层自适应 EMC 宽度

/** 工具层（heatmap/grid/buffer/terrain）要素按钮 toggle-close 判定：
 *  param-panel 开着 + 当前激活 tab 对应该工具 + 该对话框正编辑此层 → true（再点应关闭）。
 *  与 point/line/range 的 settings popover toggle（isOpen && openSettingsLayerId===id）同设计语言。 */
function isToolPanelEditing(tool, id) {
  const panel = document.getElementById('param-panel');
  if (!panel || !panel.classList.contains('is-open')) return false;
  const tab = { heatmap: 'heatmap', grid: 'grid', buffer: 'buffer', terrain: 'heatmap' }[tool];
  const activeTab = panel.querySelector('.pp-tab.is-active')?.dataset.ppTab;
  if (activeTab !== tab) return false;
  const dlg = document.getElementById(`${tab}-dialog`);
  return !!dlg && dlg.dataset.editLayerId === id;
}

const expandedWidth = { left: 0, right: 0 };

let _onFiles = null;       // (FileList) => void — registered by main.js pipeline (Import)
let _onRangeFiles = null;   // (FileList) => void — registered by main.js pipeline (Range upload)

function readVarPx(name) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return parseFloat(v) || 0;
}
function setSideVar(side, px) {
  document.documentElement.style.setProperty(side === 'left' ? '--left-w' : '--right-w', `${px}px`);
}
function clamp(px, min, max) { return Math.max(min, Math.min(max, px)); }

function togglePanel(side) {
  const varName = side === 'left' ? '--left-w' : '--right-w';
  const cur = readVarPx(varName);
  const gutter = document.querySelector(`.gutter-${side}`);
  if (cur > 1) {
    expandedWidth[side] = cur;
    setSideVar(side, 0);
    if (gutter) gutter.classList.add('is-hidden');
  } else {
    const def = side === 'left'
      ? parseFloat(token('--geojson-layout-left-panel-width')) || 300
      : parseFloat(token('--geojson-layout-right-panel-width')) || 340;
    const w = expandedWidth[side] || def;
    setSideVar(side, w);
    if (gutter) gutter.classList.remove('is-hidden');
  }
  const btn = document.querySelector(`.collapse-btn[data-side="${side}"]`);
  if (btn) {
    const folded = readVarPx(varName) < 1;
    btn.textContent = (side === 'left') ? (folded ? '›' : '‹') : (folded ? '‹' : '›');
  }
}

function initDrag(gutter, side) {
  const min = parseFloat(token(side === 'left' ? '--geojson-layout-left-panel-min' : '--geojson-layout-right-panel-min')) || 220;
  const max = parseFloat(token(side === 'left' ? '--geojson-layout-left-panel-max' : '--geojson-layout-right-panel-max')) || 520;
  const varName = side === 'left' ? '--left-w' : '--right-w';
  gutter.addEventListener('mousedown', (e) => {
    e.preventDefault();
    document.body.classList.add('dragging');
    const start = e.clientX;
    const startW = readVarPx(varName);
    const move = (ev) => {
      const dx = ev.clientX - start;
      const viewCap = window.innerWidth - 220;
      const w = clamp(side === 'left' ? startW + dx : startW - dx, min, Math.min(max, viewCap));
      setSideVar(side, w);
    };
    const up = () => {
      document.body.classList.remove('dragging');
      expandedWidth[side] = readVarPx(varName);
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', up);
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
  });
}

// ── EMC 纵向拖拽（gutter-emc → --emc-h）+ resize 重算 ────────────────────
//   复用 readVarPx 思路；读 #emc-panel.offsetHeight（px，不受 var 单位影响）。
//   手动拖拽 = 写 --emc-h-user 基线 + 标 window._emcUserBaseline（panel.js setEmcMode 据此回退）。
function initVDrag(gutter) {
  if (!gutter) return;
  gutter.addEventListener('mousedown', (e) => {
    e.preventDefault();
    const panel = document.getElementById('emc-panel');
    if (!panel) return;
    document.body.classList.add('dragging');
    const startY = e.clientY;
    const startH = panel.offsetHeight;
    const move = (ev) => {
      const win = window.innerHeight;
      const min = 320;                       // EMC 下限（= panel.js EMC_MIN；低于此 chat-messages 塌缩→空白）
      const max = win - win / 3;             // 上层最小 1/3 窗口高 → EMC 上限
      const h = Math.max(min, Math.min(max, startH - (ev.clientY - startY)));
      document.documentElement.style.setProperty('--emc-h', `${h}px`);
      document.documentElement.style.setProperty('--emc-h-user', `${h}px`);
      window._emcUserBaseline = true;
    };
    const up = () => {
      document.body.classList.remove('dragging');
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', up);
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
  });
}

function initEmcResize() {
  let raf = 0;
  window.addEventListener('resize', () => {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      const panel = document.getElementById('emc-panel');
      if (!panel) return;
      const win = window.innerHeight;
      const min = 320;                       // = panel.js EMC_MIN
      const max = win - win / 3;
      const h = Math.max(min, Math.min(max, panel.offsetHeight));
      document.documentElement.style.setProperty('--emc-h', `${h}px`);
    });
  });
}

// ── Import trigger ────────────────────────────────────────────────────────
// Both toolbar Import and left-panel Import are identical: open the NATIVE file
// picker (no submenu). Does NOT switch the left panel to sections — that only
// happens after a successful load (showLayerManager). 1:1 geojson.io.
export function openImport() {
  if (readVarPx('--left-w') < 1) setLeftMode('import');   // expand folded panel for context
  const input = document.getElementById('import-input');
  if (input) { input.value = ''; input.click(); }
}

/** After a successful load: switch left panel to sections + activate the Layers
 *  tab so the layer manager is visible. Called by main.js runImport. */
export function showLayerManager() {
  const panel = document.getElementById('left-panel');
  if (panel) panel.classList.add('is-drawer-open');   // CPD Phase 2b：导入后自动展开抽屉显图层
  setLeftMode('sections');
  setActiveTab('layers');
}

/** Expand the right panel if folded (used when a layer is selected → show Overview). */
export function openRightPanel() {
  if (readVarPx('--right-w') < 1) togglePanel('right');
}

/** Show + color the legend block(s) for visible layers. The ramp/outline color
 *  tracks the SELECTED layer's paint (or the first visible layer of that type),
 *  so the legend stays in sync when a layer's color is edited. */
export function refreshLegend() {
  const vis = getLayers().filter((l) => l.visible);
  const sel = getSelectedLayer();
  const has = (pred) => vis.some(pred);

  // polarity (L2) — 5-color gradient bar (VP lime → P teal → Neutral blue → N orange → VN dark red)
  // 仅 point 层（L2 情绪点）触发；polygon/line 即便误带 polarity colorMode 也不显（防范围/缓冲层误弹极性图例）
  const l2 = vis.find((l) => l.kind === 'point' && (l.colorMode === 'l2-positive' || l.colorMode === 'l2-neutral' || l.colorMode === 'l2-negative' || l.colorMode === 'polarity'));
  sethidden('legend-polarity', !l2);
  if (l2) {
    const items = [
      ['非常积极', L2_POSITIVE['Very Positive']],
      ['积极',     L2_POSITIVE['Positive']],
      ['中性',     L2_NEUTRAL_COLOR],
      ['消极',     L2_NEGATIVE['Negative']],
      ['非常消极', L2_NEGATIVE['Very Negative']],
    ];
    const rows = document.getElementById('legend-l2-rows');
    if (rows) rows.innerHTML = items.map(([label, color]) =>
      `<div class="legend-row"><span class="dot" style="background:${color};border-color:${color}"></span>${label}</div>`).join('');
  }

  // confidence (L1) — ramp colored from the focus layer's paint.ramp
  const conf = (sel && sel.colorMode === 'confidence' && sel.visible) ? sel : vis.find((l) => l.colorMode === 'confidence');
  sethidden('legend-confidence', !conf);
  if (conf) {
    // L1 热度值 3 段离散色带（浅橙→橙→深橙红）
    const rampEl = document.querySelector('#legend-confidence .legend-ramp');
    if (rampEl) rampEl.innerHTML = HOTNESS_RAMP.map((c) => `<span class="legend-heat-seg" style="background:${c}"></span>`).join('');
  }

  // range — 矩形线框+面域填充，实时同步 focus range 层的线色/填充态；名称=层实际名。
  // range = 上传/行政边界等「纯面/线」（无 _ui.tool）；任何 _ui.tool 标记的层都是 EMC/Toolbox 分析产物
  //   （grid/terrain/buffer/overlay/area_stats/merge…），不是 range，不应显 range 假图例（承重：density 死码一并收掉）。
  const isRange = (l) => (l.kind === 'polygon' || l.kind === 'line')
    && !(l.paint && l.paint._ui && l.paint._ui.tool);
  const range = (sel && isRange(sel) && sel.visible) ? sel : vis.find(isRange);
  sethidden('legend-range', !range);
  if (range) {
    const p = range.paint || {};
    const color = p.color || '#0c1c2e';
    const dot = document.querySelector('#legend-range .range-dot');
    if (dot) {
      dot.style.borderColor = color;                                  // 线框 = 线色
      const fillPct = Math.round((p.fillOpacity ?? 0.15) * 100);
      dot.style.background = p.fillOn                                 // 填充态：fillOn→线色@fillOpacity；否则仅线框
        ? `color-mix(in srgb, ${color} ${fillPct}%, transparent)` : 'transparent';
    }
    const nameEl = document.querySelector('#legend-range .range-name');
    if (nameEl) nameEl.textContent = range.name || range.srcName || '范围';
  }

  // grid/terrain/density — 横向色带 + 极性标题（参考 Kepler/Martin 连续色带图例）
  const grid = vis.find((l) => l.kind === 'polygon' && l.paint && l.paint._ui
    && (l.paint._ui.tool === 'grid' || l.paint._ui.tool === 'terrain' || l.paint._ui.tool === 'density'));
  sethidden('legend-grid', !grid);
  if (grid) {
    const ui = grid.paint._ui;
    const pol = ui.terrainPol || ui.polarity;   // terrain 存 terrainPol；grid 存 polarity
    const isTerrain = ui.tool === 'terrain';
    const isDensity = ui.tool === 'density';
    const polLabel = isDensity ? '情绪得分密度' : ({ overall: '综合', positive: '积极', negative: '消极', neutral: '中性' }[pol] || (isTerrain ? '地形' : '网格'));
    const tEl = document.getElementById('legend-grid-title');
    if (tEl) tEl.textContent = `${isTerrain ? '情绪地形' : isDensity ? '情绪密度' : '网格'} · ${polLabel}`;
    const rampEl = document.getElementById('legend-grid-ramp');
    const stops = grid.paint.gridStops || [];
    if (rampEl && stops.length) {
      rampEl.style.background = '';   // 清旧 linear-gradient（#legend-grid-ramp 已是 .legend-heat-ramp flex 容器）
      rampEl.innerHTML = stops.map(([, c]) => `<span class="legend-heat-seg" style="background:${c}"></span>`).join('');
    }
    // 标签：L2 综合发散（terrain-9 红→蓝→绿）= 消极/中性/积极；单色占比 / L1 热度 = 低/高
    const labEl = document.querySelector('#legend-grid .legend-ramp-labels');
    if (labEl) {
      const isOverall = grid.paint._ui.polarity === 'overall' && grid.paint._ui.level === 'L2';
      labEl.innerHTML = isOverall
        ? '<span>消极</span><span>中性</span><span>积极</span>'
        : '<span>低</span><span>高</span>';
    }
  }
}
function sethidden(id, hidden) { const el = document.getElementById(id); if (el) el.hidden = hidden; }

// ── Layer manager (left panel) ────────────────────────────────────────────
const KIND_LABEL = { point: '点', line: '线', polygon: '面', heatmap: 'H' };
const eyeOpen = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>';
const eyeOff = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
// drag grip = three horizontal bars (movable hint), revealed on hover/drag
const GRIP = '<span class="layer-grip" title="拖拽排序"><svg viewBox="0 0 16 16" width="12" height="12"><line x1="3" y1="4" x2="13" y2="4"/><line x1="3" y1="8" x2="13" y2="8"/><line x1="3" y1="12" x2="13" y2="12"/></svg></span>';

let _dragId = null;   // id of the layer row being dragged
let _dragCat = null;  // category of the group card being dragged (inter-category reorder)
let _dragGroupId = null;  // id of the group card being dragged (same-category multi-group reorder, e.g. L2 T1/T2/T3)

/** Level → next-action tag (blue). L0 需治理；L1/L2/range 无标记。 */
function levelTag(l) {
  const lv = layerLevel(l);
  if (lv === 'L0') return '<span class="layer-tag is-action">需治理</span>';
  return '';
}

/** Hint letter between 要素按钮 and name: R (range) / L0·L1·L2 (point), colored by the layer's display color.
 *  网格聚合(grid)/情绪地形(terrain)：升为 "L1·G"/"L2·E"——L 前缀着该 level 情绪点层色（L1 橙/L2 teal），字母保持工具色。 */
function hintChip(l) {
  const isBuffer = !!(l && l.paint && l.paint._ui && l.paint._ui.tool === 'buffer');
  const isGrid = !!(l && l.paint && l.paint._ui && l.paint._ui.tool === 'grid');
  const isTerrain = !!(l && l.paint && l.paint._ui && l.paint._ui.tool === 'terrain');
  const lv = layerLevel(l);
  if (isGrid || isTerrain) {
    const letter = isGrid ? 'G' : 'E';
    const lvText = lv === 'L1' ? 'L1' : lv === 'L2' ? 'L2' : 'L·';
    return `<span class="layer-hint"><b class="layer-hint-lv" style="color:${levelPointColor(lv)}">${lvText}</b>·${letter}</span>`;
  }
  const text = isBuffer ? 'B' : (lv === 'range' ? 'R' : (lv || 'L0'));
  return `<span class="layer-hint" style="color:${layerDisplayColor(l)}">${text}</span>`;
}

/** grid 层数据签名（同 map.js gridSig）：同 analysis/level/source/cellSize/polarity/polygonLayer 的 2D/3D 互为配对。 */
function gridSigOf(ui) {
  return ui ? [ui.analysis, ui.level, ui.source, ui.cellSize, ui.polarity, ui.polygonLayer].join('|') : '';
}

/** 视角按钮（仅工具层 grid/terrain 有 mode）：可交互，点击切 2D/3D（替左下角工具条按钮）。
 *  字面=当前视角状态（2D/3D），设计参考要素按钮（.layer-kind）。 */
function modeChip(l) {
  const ui = l && l.paint && l.paint._ui;
  if (ui && (ui.tool === 'grid' || ui.tool === 'terrain') && (ui.mode === '2d' || ui.mode === '3d')) {
    return `<button class="layer-view" data-viewmode="${l.id}" title="切换 2D/3D 视角">${ui.mode === '3d' ? '3D' : '2D'}</button>`;
  }
  return '';
}

/** Group header row. Real L2 group (virtual=false, eye→toggleGroupEye) or virtual category
 *  card (virtual=true, eye→toggleCategoryEye). Always draggable (inter-category reorder);
 *  chev toggles collapse for its category. */
function groupRowHtml(g, members, cat, collapsed, virtual) {
  const anyVis = members.length > 0 && members.some((c) => c.visible);
  const idAttr = g.id ? ` data-id="${g.id}"` : '';
  const collCls = collapsed ? ' is-collapsed' : '';
  const eyeAttr = virtual ? `data-category-eye="${cat}"` : `data-group-eye="${g.id}"`;
  return `<div class="layer-group${collCls}"${idAttr} data-cat="${cat}" draggable="true" title="拖拽排序 / 点击箭头折叠">
    ${GRIP}
    <button class="layer-eye" ${eyeAttr} title="${anyVis ? '隐藏全部' : '显示全部'}">${anyVis ? eyeOpen : eyeOff}</button>
    <span class="layer-group-name">${g.name}</span>
    <span class="layer-group-count">${members.length}</span>
    <span class="layer-group-chev" data-collapse-cat="${cat}">&#9662;</span>
  </div>`;
}

/** 网格聚合大组内的子卡（标准网格/指定单元）：缩进 + 折叠 chev + 名称 + 计数。
 *  无 eye（外层组卡 eye 已统管整类显隐）；双击 / 点 chev 折叠该子卡（_groupFold 合成 id grid-square/grid-zonal）。 */
function subGroupRowHtml(subId, label, members, folded) {
  const collCls = folded ? ' is-collapsed' : '';
  return `<div class="layer-subgroup${collCls}" data-subid="${subId}" title="双击折叠/展开 · ${label}">
    <span class="layer-subgroup-chev" data-collapse-sub="${subId}">&#9662;</span>
    <span class="layer-subgroup-name">${label}</span>
    <span class="layer-subgroup-count">${members.length}</span>
  </div>`;
}

/** A single layer row (standalone or indented child; both draggable within their category). */
function layerRowHtml(l, openId, selId, isChild, cat) {
  const kindEl = (l.kind === 'point' || l.kind === 'polygon' || l.kind === 'heatmap')
    ? `<button class="layer-kind${openId === l.id ? ' is-active' : ''}" data-feat="${l.id}" title="要素设置">${KIND_LABEL[l.kind]}</button>`
    : `<span class="layer-kind is-disabled" title="线暂未开放设置">${KIND_LABEL[l.kind] || '层'}</span>`;
  const sel = selId === l.id ? ' is-selected' : '';
  const childCls = isChild ? ' is-child' : '';
  return `<div class="layer-row${sel}${childCls}${l.visible ? '' : ' is-off'}" data-id="${l.id}" data-cat="${cat}" draggable="true">
    <button class="layer-eye" data-eye="${l.id}" title="${l.visible ? '隐藏' : '显示'}">${l.visible ? eyeOpen : eyeOff}</button>
    ${kindEl}
    ${hintChip(l)}
    ${modeChip(l)}
    <span class="layer-name" title="${l.name}">${l.name}</span>
    ${levelTag(l)}
    ${GRIP}
    <button class="layer-del" data-del="${l.id}" title="删除">&times;</button>
  </div>`;
}

/** Re-render the layer list, aggregated into category group cards (render-layer aggregation:
 *  _layers structure untouched; grouping is a UI projection in _groupOrder order). */
export function renderLayerList() {
  const list = document.getElementById('layer-list');
  if (!list) return;
  applyGroupOrder();
  restackZ();   // 无条件同步 map z-order == _layers 序（安全网：applyGroupOrder 返 false 时也同步，修新极性网格 z 漂移）
  const all = getLayers();
  if (!all.length) { list.innerHTML = '<div class="layer-empty">尚未导入数据</div>'; return; }
  const openId = openSettingsLayerId();
  const selId = getSelectedLayerId();
  const byId = new Map(all.map((l) => [l.id, l]));
  const top = all.filter((l) => !l.parentId);   // groups + standalone layers
  // 配对去重：同 gridSig 的 2D/3D 合并显示一条（不论可见性——避免眼睛关闭后 2D/3D 都隐藏却分裂两条）。
  // 每组选一个代表（可见优先；都隐藏取最后一个=最近切 mode），其余 skipIds 跳过。
  const _grids = all.filter((l) => l.kind === 'polygon' && l.paint && l.paint._ui && l.paint._ui.tool === 'grid');
  const skipIds = new Set();
  const _sigGroups = new Map();
  for (const l of _grids) {
    const sig = gridSigOf(l.paint._ui);
    if (!_sigGroups.has(sig)) _sigGroups.set(sig, []);
    _sigGroups.get(sig).push(l);
  }
  for (const [sig, arr] of _sigGroups) {
    if (arr.length < 2) continue;                          // 无配对（单层），不去重
    const lastMode = getGridViewMode(sig);
    const rep = arr.find((g) => g.visible)                 // 1. 可见优先（当前视角层）
      || (lastMode ? arr.find((g) => g.paint._ui.mode === lastMode) : null)   // 2. 最近切的 mode（隐藏/切回时）
      || arr[arr.length - 1];                              // 3. 兜底取最后
    for (const g of arr) if (g !== rep) skipIds.add(g.id);
  }

  // bucket top-level items by category (preserve _layers order within each bucket)
  const buckets = new Map();
  for (const l of top) {
    const cat = categoryOf(l);
    if (!buckets.has(cat)) buckets.set(cat, []);
    buckets.get(cat).push(l);
  }

  // 钉底：range 恒在 ai（AI 工作区）之上，二者显示在最末（与 state.applyGroupOrder 的 _layers 钉底一致）。
  const _rawOrder = getGroupOrder();
  const _catOrder = _rawOrder.filter((c) => c !== 'range' && c !== 'ai');
  if (_rawOrder.includes('range')) _catOrder.push('range');
  if (_rawOrder.includes('ai')) _catOrder.push('ai');
  let html = '';
  for (const cat of _catOrder) {
    const items = buckets.get(cat);
    if (!items || !items.length) continue;
    const collapsed = isCollapsed(cat);
    if (cat === 'l2' || cat === 'ai') {
      // real L2 groups first (own cards + children); any stray standalone l2 → one virtual card
      const groups = items.filter((g) => g.kind === 'group');
      const stray = items.filter((g) => g.kind !== 'group');
      for (const g of groups) {
        const kids = (g.children || []).map((cid) => byId.get(cid)).filter((c) => c && !skipIds.has(c.id));
        const gfold = isGroupFold(g.id);   // 真 L2 组单独折叠（双击该组只折该组，不波及其他 L2 组）
        html += groupRowHtml(g, kids, cat, gfold, false);
        if (!gfold) for (const c of kids) html += layerRowHtml(c, openId, selId, true, cat);
      }
      if (stray.length) {
        html += groupRowHtml({ id: null, name: CATEGORY_LABEL[cat] }, stray, cat, collapsed, true);
        if (!collapsed) for (const l of stray) { if (skipIds.has(l.id)) continue; html += layerRowHtml(l, openId, selId, true, cat); }
      }
    } else {
      html += groupRowHtml({ id: null, name: CATEGORY_LABEL[cat] }, items, cat, collapsed, true);
      if (!collapsed) {
        if (cat === 'grid') {
          // 网格聚合大组内拆「标准网格/指定单元」两张子卡（按 _ui.analysis 分桶；2px 间隔，各可双击折叠）
          const sq = items.filter((l) => l.paint && l.paint._ui && l.paint._ui.analysis === 'square');
          const zo = items.filter((l) => l.paint && l.paint._ui && l.paint._ui.analysis === 'zonal');
          const rest = items.filter((l) => !(l.paint && l.paint._ui && (l.paint._ui.analysis === 'square' || l.paint._ui.analysis === 'zonal')));
          if (sq.length) { const f = isGroupFold('grid-square'); html += subGroupRowHtml('grid-square', '标准网格', sq, f); if (!f) for (const l of sq) { if (skipIds.has(l.id)) continue; html += layerRowHtml(l, openId, selId, true, cat); } }
          if (zo.length) { const f = isGroupFold('grid-zonal'); html += subGroupRowHtml('grid-zonal', '指定单元', zo, f); if (!f) for (const l of zo) { if (skipIds.has(l.id)) continue; html += layerRowHtml(l, openId, selId, true, cat); } }
          for (const l of rest) { if (skipIds.has(l.id)) continue; html += layerRowHtml(l, openId, selId, true, cat); }
        } else {
          for (const l of items) { if (skipIds.has(l.id)) continue; html += layerRowHtml(l, openId, selId, true, cat); }
        }
      }
    }
  }
  list.innerHTML = html;

  // wire button events (eye / del / feat / group-eye / category-eye / collapse)
  list.querySelectorAll('[data-eye]').forEach((b) =>
    b.addEventListener('click', (e) => { e.stopPropagation(); toggleEye(b.dataset.eye); }));
  list.querySelectorAll('[data-del]').forEach((b) =>
    b.addEventListener('click', (e) => { e.stopPropagation(); deleteLayer(b.dataset.del); }));
  list.querySelectorAll('[data-group-eye]').forEach((b) =>
    b.addEventListener('click', (e) => { e.stopPropagation(); toggleGroupEye(b.dataset.groupEye); }));
  list.querySelectorAll('[data-category-eye]').forEach((b) =>
    b.addEventListener('click', (e) => { e.stopPropagation(); toggleCategoryEye(b.dataset.categoryEye); }));
  list.querySelectorAll('[data-collapse-cat]').forEach((b) =>
    b.addEventListener('click', (e) => { e.stopPropagation(); toggleCollapsed(b.dataset.collapseCat); renderLayerList(); }));
  // 视角按钮（2D/3D 切换，替左下角工具条按钮）：点击 → toggleGridViewMode(该层) → 针对该 sig 切（不论可见）→ layers:changed → 重绘
  list.querySelectorAll('[data-viewmode]').forEach((b) =>
    b.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleGridViewMode(b.dataset.viewmode);
    }));
  list.querySelectorAll('[data-feat]').forEach((b) =>
    b.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = b.dataset.feat;
      const l = getLayer(id);
      if (!l) return;
      // 工具层要素按钮 toggle-close：再点同一层按钮 → 关 param-panel（与 point/line/range 的 settings popover toggle 同设计语言）
      if (l.kind === 'heatmap') { if (isToolPanelEditing('heatmap', id)) closeParamPanel(); else openHeatmapDialog(id); return; }
      if (l.paint && l.paint._ui && l.paint._ui.tool === 'buffer') { if (isToolPanelEditing('buffer', id)) closeParamPanel(); else openBufferDialog(id); return; }
      if (l.paint && l.paint._ui && l.paint._ui.tool === 'grid') { if (isToolPanelEditing('grid', id)) closeParamPanel(); else openGridDialog(id); return; }
      if (l.paint && l.paint._ui && l.paint._ui.tool === 'terrain') { if (isToolPanelEditing('terrain', id)) closeParamPanel(); else openHeatmapDialog(id); return; }
      if (isOpen() && openSettingsLayerId() === id) closeSettingsPopover();
      else {
        openSettingsPopover(l, b);
        selectLayer(id);
        document.dispatchEvent(new CustomEvent('layer:selected', { detail: id }));
      }
      renderLayerList();
    }));

  // row click → select（单击图层行：弹右栏 Overview/Table）
  list.querySelectorAll('.layer-row').forEach((row) =>
    row.addEventListener('click', () => selectLayerRow(row.dataset.id)));
  // row dblclick → 缩放至本图层（双击：fitToLayer；与单击叠加=选中后飞过去，不互斥）
  list.querySelectorAll('.layer-row').forEach((row) =>
    row.addEventListener('dblclick', () => {
      const l = getLayer(row.dataset.id);
      if (!l || l.kind === 'group' || !l.fc || !l.fc.features.length) return;
      fitToLayer(l);
      toast.info(`缩放至：${l.name}`);
    }));
  // 双击 group card 折叠：真 group（data-id）→ 只折叠该组；虚拟 group（无 data-id）→ 折叠整个 category
  list.querySelectorAll('.layer-group').forEach((grp) =>
    grp.addEventListener('dblclick', (e) => {
      if (e.target.closest('.layer-eye, .layer-group-chev')) return;
      const cat = grp.dataset.cat;
      const gid = grp.dataset.id;
      if (!cat) return;
      if (gid) toggleGroupFold(gid); else toggleCollapsed(cat);
      renderLayerList();
    }));
  // 子卡（标准网格/指定单元）chev + 双击折叠（_groupFold 合成 id grid-square/grid-zonal）
  list.querySelectorAll('[data-collapse-sub]').forEach((b) =>
    b.addEventListener('click', (e) => { e.stopPropagation(); toggleGroupFold(b.dataset.collapseSub); renderLayerList(); }));
  list.querySelectorAll('.layer-subgroup').forEach((sg) =>
    sg.addEventListener('dblclick', (e) => { e.stopPropagation(); const sid = sg.dataset.subid; if (sid) { toggleGroupFold(sid); renderLayerList(); } }));

  // drag → reorder (dual flavor: group-card = inter-category; layer-row = within-category)
  list.querySelectorAll('[draggable]').forEach((el) => {
    el.addEventListener('dragstart', (e) => {
      if (el.classList.contains('layer-group')) { _dragCat = el.dataset.cat; _dragGroupId = el.dataset.id || null; _dragId = null; }
      else { _dragId = el.dataset.id; _dragCat = null; _dragGroupId = null; }
      el.classList.add('is-dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', _dragId || _dragCat);
    });
    el.addEventListener('dragend', () => { el.classList.remove('is-dragging'); clearDropHints(); _dragId = null; _dragCat = null; _dragGroupId = null; });
    el.addEventListener('dragover', (e) => { e.preventDefault(); el.classList.add('is-drop-over'); });
    el.addEventListener('dragleave', () => el.classList.remove('is-drop-over'));
    el.addEventListener('drop', (e) => {
      e.preventDefault(); e.stopPropagation();
      const tIsGroup = el.classList.contains('layer-group');
      const tCat = el.dataset.cat;
      const tId = el.dataset.id;
      let moved = false;
      if (_dragCat && tIsGroup) {
        const rect = el.getBoundingClientRect();
        const before = (e.clientY - rect.top) <= rect.height / 2;
        if (_dragCat !== tCat) {
          reorderGroupSegment(_dragCat, tCat, before);   // 跨 category：移整段
        } else if (_dragGroupId && el.dataset.id && _dragGroupId !== el.dataset.id) {
          // 同 category 多 group（如多个 L2 组 T1/T2/T3）：按 group id 重排 _layers
          const ls = getLayers();
          const idx = ls.findIndex((x) => x.id === el.dataset.id);
          const toId = before ? el.dataset.id : (ls[idx + 1] ? ls[idx + 1].id : null);
          reorderLayers(_dragGroupId, toId);
          freezeCategoryOrder(tCat);   // 手动 within-cat 重排 → 冻结，防 applyGroupOrder 覆盖
        }
        reorderAllZ();
        moved = true;
      } else if (_dragGroupId && !tIsGroup) {
        // group 拖到 layer-row（目标 group 的子层）→ 找父 group 整组重排（覆盖 group 展开时 drop 到子层）
        const tLayer = getLayer(tId);
        const tgtGroupId = tLayer && tLayer.parentId;
        if (tgtGroupId && tgtGroupId !== _dragGroupId) {
          const ls = getLayers();
          const gidx = ls.findIndex((x) => x.id === tgtGroupId);
          const toId = gidx >= 0 ? (ls[gidx + 1] ? ls[gidx + 1].id : null) : null;
          reorderLayers(_dragGroupId, toId);
          reorderAllZ();
          moved = true;
        }
      } else if (_dragId && !tIsGroup && _dragId !== tId) {
        // layer drag → within same category only (cross-category move deferred)
        const src = getLayer(_dragId);
        if (src && categoryOf(src) === tCat) {
          const rect = el.getBoundingClientRect();
          const after = (e.clientY - rect.top) > rect.height / 2;
          const ls = getLayers();
          const idx = ls.findIndex((x) => x.id === tId);
          const toId = after ? (ls[idx + 1] ? ls[idx + 1].id : null) : tId;
          reorderLayers(_dragId, toId);
          freezeCategoryOrder(tCat);   // 手动 within-cat 重排 → 冻结，防 applyGroupOrder 覆盖
          reorderAllZ();
          moved = true;
        }
      }
      _dragId = null; _dragCat = null; _dragGroupId = null;
      clearDropHints();
      renderLayerList();
      if (moved) toast.info('图层顺序已更新');
    });
  });

  // refresh the Layers header eye (aggregate visibility across all layers)
  const _hdr = document.getElementById('layers-toggle-all');
  if (_hdr) {
    const _renderable = getLayers().filter((l) => l.kind !== 'group');
    const _anyVis = _renderable.length > 0 && _renderable.some((l) => l.visible);
    _hdr.innerHTML = _anyVis ? eyeOpen : eyeOff;
    _hdr.title = _anyVis ? '隐藏全部图层' : '显示全部图层';
    // 区2 工具栏漏斗：可见图层 / 全部图层（只更新计数 span，保留漏斗 svg 不被 textContent 冲掉）
    const _funnel = document.getElementById('lp-funnel');
    if (_funnel) {
      const _vis = _renderable.filter((l) => l.visible).length;
      const _fc = _funnel.querySelector('.lp-funnel-count');
      if (_fc) _fc.textContent = `${_vis}/${_renderable.length}`;
    }
  }
}

function clearDropHints() {
  document.querySelectorAll('.layer-row.is-drop-over, .layer-group.is-drop-over').forEach((r) => r.classList.remove('is-drop-over'));
}

/** Select a layer row → 选中 + 弹右栏 + 按"当前面板状态"路由（Overview/Table/折叠默认 Overview）。
 *  承重④：侧栏列表入口（区别于地图要素点击的 layer:selected 不自动弹栏）。 */
function selectLayerRow(id) {
  const l = getLayer(id);
  if (!l) return;
  const wasFolded = readVarPx('--right-w') < 1;   // 展开前判折叠态（供 main.js 路由）
  selectLayer(id);
  openRightPanel();   // 折叠则展开
  renderLayerList();
  document.dispatchEvent(new CustomEvent('layer:selected', { detail: { id, wasFolded } }));
}

/** 开某层为可见后，应用互斥规则 + 选中追随（视野-数据-结论同步：Overview 跟随当前可见层）。 */
function _applyExclusiveOn(id) {
  const hidden = enforceMutualExclusion(id);
  for (const hid of hidden) { const hl = getLayer(hid); if (hl) renderLayer(hl); }
  selectLayer(id);
}

function toggleEye(id) {
  const l = getLayer(id);
  if (!l) return;
  setLayerVisible(id, !l.visible);
  renderLayer(l);
  if (l.visible) _applyExclusiveOn(id);   // 开层 → 互斥 + Overview 追随
  renderLayerList();
  refreshLegend();   // legend syncs with visibility (hidden layer → legend hides)
  document.dispatchEvent(new CustomEvent('layers:changed'));   // 显隐 → popup/Overview 同步
  toast.info(`${l.visible ? '显示' : '隐藏'}图层：${l.name}`);
}

/** L2 group eye: toggle ALL children at once (any hidden → show all; all visible → hide all). */
function toggleGroupEye(groupId) {
  const children = getLayers().filter((l) => l.parentId === groupId);
  if (!children.length) return;
  const showAll = !children.some((c) => c.visible);
  for (const c of children) {
    setLayerVisible(c.id, showAll);
    renderLayer(c);
  }
  if (showAll && children[0]) _applyExclusiveOn(children[0].id);   // 同源极性组开 → 互斥(保兄弟)+追随
  renderLayerList();
  refreshLegend();
  document.dispatchEvent(new CustomEvent('layers:changed'));   // 组显隐 → popup/Overview 同步
  toast.info(`${showAll ? '显示' : '隐藏'}全部子图层`);
}

/** Virtual category eye: toggle every layer in the category at once
 *  (any hidden → show all; all visible → hide all). */
function toggleCategoryEye(cat) {
  const members = getLayers().filter((l) => categoryOf(l) === cat);
  if (!members.length) return;
  const showAll = !members.some((c) => c.visible);
  for (const l of members) {
    setLayerVisible(l.id, showAll);
    renderLayer(l);
  }
  if (showAll && members[0]) _applyExclusiveOn(members[0].id);   // 按互斥规则保留首个，余被关
  renderLayerList();
  refreshLegend();
  document.dispatchEvent(new CustomEvent('layers:changed'));   // 组显隐 → popup/Overview 同步
  toast.info(`${showAll ? '显示' : '隐藏'}${CATEGORY_LABEL[cat] || ''}分组`);
}

/** Layers header eye: toggle ALL layers at once (any hidden → show all; all visible → hide all). */
function toggleAllLayers() {
  const layers = getLayers().filter((l) => l.kind !== 'group');
  if (!layers.length) return;
  const showAll = !layers.some((l) => l.visible);
  for (const l of layers) {
    setLayerVisible(l.id, showAll);
    renderLayer(l);
  }
  if (showAll && layers[0]) _applyExclusiveOn(layers[0].id);
  renderLayerList();
  refreshLegend();
  document.dispatchEvent(new CustomEvent('layers:changed'));   // 显隐 → popup/Overview 同步
  toast.info(`${showAll ? '显示' : '隐藏'}全部图层`);
}

function deleteLayer(id) {
  const l = getLayer(id);
  if (!l) return;
  if (openSettingsLayerId() === id) closeSettingsPopover();
  if (l.kind === 'group') {
    // remove children's map layers first, then state-cascade the group
    for (const cid of [...(l.children || [])]) removeLayerFromMap(cid);
    removeLayer(id);
  } else {
    const pid = l.parentId;
    removeLayerFromMap(id);
    removeLayer(id);
    if (pid) {   // child removed → drop the group if now empty
      const p = getLayer(pid);
      if (p && p.kind === 'group' && (!p.children || !p.children.length)) removeLayer(pid);
    }
  }
  renderLayerList();
  document.dispatchEvent(new CustomEvent('layers:changed'));
  toast.success(`已删除：${l.name}`);
}

/** Build a heatmap layer from L2 negative points (VN+N). Kepler-style density overlay:
 *  maps density through HEATMAP_NEGATIVE_STOPS, weights by score (more negative = hotter).
 *  First variant = 'negative' (积极/综合 待后续).
 *  v2: 废弃直接生成逻辑，统一转调 HeatMap 弹窗（避免旧入口与新入口并存导致 Bug 1）。 */
export function createHeatmap(variant = 'negative') {
  openHeatmapDialog();
}

// ── 工具栏 i 信息图标 tooltip（独立于 KDE 弹窗内的 #hm-tooltip）──
// 挂 body、触发 .tool-info[data-tip]，hover 显示应用场景简介；click 不冒泡到 .tool-row。
let _toolTipInit = false;
function initToolInfoTooltip() {
  if (_toolTipInit) return;
  _toolTipInit = true;
  const tip = document.createElement('div');
  tip.className = 'tool-tooltip';
  document.body.appendChild(tip);
  const show = (info) => {
    const text = info.dataset.tip || '';
    if (!text) return;
    tip.textContent = text;
    tip.classList.add('is-show');
    const r = info.getBoundingClientRect();
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    let left = r.left + r.width / 2 - tw / 2;
    let top = r.top - th - 8;
    if (top < 8) top = r.bottom + 8;
    left = Math.max(8, Math.min(left, window.innerWidth - tw - 8));
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  };
  const hide = () => tip.classList.remove('is-show');
  document.addEventListener('mouseover', (e) => {
    const info = e.target.closest('.tool-info');
    if (info) show(info);
  });
  document.addEventListener('mouseout', (e) => {
    if (e.target.closest('.tool-info')) hide();
  });
  // 点 i 仅看介绍，不触发所在 .tool-row（避免误开工具弹窗）
  document.addEventListener('click', (e) => {
    if (e.target.closest('.tool-info')) e.stopPropagation();
  }, true);
}

// ── 左端栏三区：tab 互斥切换 ───────────────────────────────────────────────
// 替代原 .lp-section 加法式手风琴：同一时刻仅一个 tab 高亮、仅一个 .lp-pane 显示。
let _activeTab = 'layers';
function setActiveTab(name) {
  _activeTab = name;
  document.querySelectorAll('.lp-tab').forEach((t) => {
    const on = t.dataset.tab === name;
    t.classList.toggle('is-active', on);
    t.setAttribute('aria-selected', on ? 'true' : 'false');
  });
  document.querySelectorAll('.lp-pane').forEach((p) => { p.hidden = p.dataset.pane !== name; });
  // 区2 文件夹 title 随当前页更新（上载语义提示）
  const up = document.getElementById('lp-upload');
  if (up) {
    up.title = (name === 'range') ? '上载范围文件（面/线；不含 CSV/点）'
      : (name === 'layers') ? '上载数据文件（点/线/面）'
      : '工具箱暂无上载入口';
  }
}

export function initSidebar({ onFiles, onRangeFiles } = {}) {
  _onFiles = onFiles;
  _onRangeFiles = onRangeFiles;

  document.querySelectorAll('.collapse-btn').forEach((btn) =>
    btn.addEventListener('click', () => togglePanel(btn.dataset.side)));
  document.querySelectorAll('.gutter:not(.gutter-emc)').forEach((g) => initDrag(g, g.dataset.side));
  initVDrag(document.getElementById('gutter-emc'));
  initEmcResize();
  // 区1 选择栏：tab 互斥切换（替代原加法式手风琴 .lp-section .open）
  document.querySelectorAll('.lp-tab').forEach((t) =>
    t.addEventListener('click', () => setActiveTab(t.dataset.tab)));
  setActiveTab(_activeTab);   // 初始同步（默认 layers，高亮 + 显示对应 pane）
  // 区2 工具栏：文件夹按当前 tab 触发上载（Range→范围 / Layers→数据 / Toolbox→提示）
  document.getElementById('lp-upload')?.addEventListener('click', () => {
    if (_activeTab === 'range') document.getElementById('range-input')?.click();
    else if (_activeTab === 'layers') document.getElementById('import-input')?.click();
    else toast.info('工具箱暂无上载入口');
  });
  // 区2 占位按钮（待开发）：+ 新建图层 / 方片叠加=图层分组视图
  document.getElementById('lp-add')?.addEventListener('click', () => toast.info('新建图层（待开发）'));
  document.getElementById('lp-group')?.addEventListener('click', () => toast.info('图层分组/视图（待开发）'));

  // clear-all trash at the 区2 toolbar (id 不变，从原 Layers 段头迁入)
  document.getElementById('layers-clear')?.addEventListener('click', () => {
    const layers = getLayers();
    if (!layers.length) { toast.info('没有可删除的图层'); return; }
    closeSettingsPopover();
    for (const l of layers) { removeLayer(l.id); removeLayerFromMap(l.id); }
    renderLayerList();
    document.dispatchEvent(new CustomEvent('layers:changed'));
    toast.success('已清空全部图层');
  });

  // header eye: toggle visibility of ALL layers at once
  document.getElementById('layers-toggle-all')?.addEventListener('click', toggleAllLayers);

  // popover closed via outside-click/Escape → clear the kind marker's active state
  document.addEventListener('layer-settings:closed', renderLayerList);

  // CPD Phase 2b：EMC chip 唤出左栏抽屉（同 tab 再点 → 关；外部点 / Esc → 关）
  document.addEventListener('cpd:focus-tab', (e) => {
    const tab = e.detail;
    if (tab === 'import') return openImport();   // CPD G1：光环 import CTA 闭环（复用 openImport）
    if (tab !== 'layers' && tab !== 'range' && tab !== 'toolbox') return;
    const panel = document.getElementById('left-panel');
    if (!panel) return;
    if (panel.classList.contains('is-drawer-open') && _activeTab === tab) {
      panel.classList.remove('is-drawer-open');   // 同 tab 再点 → 关（toggle）
      return;
    }
    relayoutFloats();                             // CPD ③④：打开前定位抽屉 + param-panel 浮层（自适应 EMC 宽度）
    panel.classList.add('is-drawer-open');
    setLeftMode('sections');                       // 切到三区模式（非 import 空态）
    setActiveTab(tab);
  });
  // 抽屉外部点击 → 关（点抽屉内 / EMC / param-panel 伴生不关）
  document.addEventListener('pointerdown', (e) => {
    const panel = document.getElementById('left-panel');
    if (!panel || !panel.classList.contains('is-drawer-open')) return;
    if (panel.contains(e.target)) return;
    if (e.target.closest('#emc-panel')) return;
    if (e.target.closest('#param-panel')) return;   // param-panel 伴生不关
    panel.classList.remove('is-drawer-open');
  });
  // Esc → 关抽屉
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') document.getElementById('left-panel')?.classList.remove('is-drawer-open');
  });

  // Analysis 段已移除（整合入数据库）；以下为 Toolbox 工具入口
  document.getElementById('tool-heatmap')?.addEventListener('click', () => openHeatmapDialog());
  document.getElementById('tool-buffer')?.addEventListener('click', () => openBufferDialog());
  document.getElementById('tool-grid')?.addEventListener('click', () => openGridDialog());
  document.getElementById('tool-attribution')?.addEventListener('click', () => {
    toast.info('多维归因分析（Toolbox 独立工具，开发中）');
  });
  initToolInfoTooltip();

  // Import: native file picker (multi). Both the panel button and toolbar route here.
  const input = document.getElementById('import-input');
  if (input) {
    input.setAttribute('multiple', '');
    input.addEventListener('change', (e) => {
      const fs = e.target.files;
      if (fs && fs.length && _onFiles) _onFiles(fs);
      e.target.value = '';
    });
  }
  // Left-panel Import = native <label>→<input> (no JS; avoids double picker).

  // Range upload: native file picker — drops CSV/points upstream (main.js runRangeImport).
  const rangeInput = document.getElementById('range-input');
  if (rangeInput) {
    rangeInput.addEventListener('change', (e) => {
      const fs = e.target.files;
      if (fs && fs.length && _onRangeFiles) _onRangeFiles(fs);
      e.target.value = '';
    });
  }

  // Page-level drag-drop onto the map (1:1 geojson.io). Also keeps the dropzone hint.
  const mapEl = document.getElementById('map');
  const dz = document.getElementById('dropzone');
  if (dz) dz.addEventListener('click', () => openImport());
  if (mapEl) {
    mapEl.addEventListener('dragover', (e) => { e.preventDefault(); });
    mapEl.addEventListener('drop', (e) => {
      e.preventDefault();
      if (e.dataTransfer.files && e.dataTransfer.files.length && _onFiles) {
        _onFiles(e.dataTransfer.files);
      }
    });
  }

  renderLayerList();
  refreshLegend();
}

export function setLeftMode(mode) {
  if (readVarPx('--left-w') < 1) togglePanel('left');
  document.querySelectorAll('.lp-mode').forEach((m) => { m.hidden = (m.dataset.mode !== mode); });
}
