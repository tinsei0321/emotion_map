// ═══ grid-tool.js — Grid 空间聚合工具（标准网格 + 指定单元） ═══
// 三步导航：①分析类型（组卡片）②数据选择+网格参数 ③显示样式。
// 分析类型：聚合域组(标准网格 square + 指定单元 zonal)；热点 Gi* / Moran's I 占位(dev)。
// 数据联动：L1(无极性,舆论热度 grid-warm) / L2(有极性,综合 terrain-9 / 积极 green-3 / 消极 red-3 / 中性 blue-3)。
// 极性在②网格参数（仅 L2），③色板随极性自动（只读预览）。
// G 按钮打开（editLayerId）→ 回填参数 + 原地更新（layer id 稳定，镜像 B「继续编辑」）。
// 后端：square→/spatial/grid(square, EPSG:4546 snap-to-grid)；zonal→/spatial/aggregate(点→面域)。
// 注：polarity_index 值域 -2~+2。_grid_norm 用对称拉伸 0.5+sign(pi)×min(1,|pi|/p95)×0.5（p95=|pi|95分位），
// 铺满 terrain-9 深红/深绿（线性 (pi+2)/4 只到中段=无张力根因）；与 terrain 后端 _norm 同公式保配色一致。
import { getLayers, addLayer, getLayer, selectLayer, setLayerVisible, HEATMAP_RAMPS, rampDisplaySegs, deriveTimeTag } from './state.js';
import { renderLayer, fitBoundsTo, reorderAllZ, removeLayerFromMap, setView3D } from './map.js';
import { renderLayerList, refreshLegend, showLayerManager } from './sidebar.js';
import { fcBBox } from './import.js';
import { runGrid, runAggregate } from './api.js';
import { toast } from './toast.js';
import { openParamPanel, closeParamPanel } from './param-panel.js';

const dialogEl = () => document.getElementById('grid-dialog');
const DEFAULTS = { analysis: 'square', level: 'L1', cellSize: 400, polarity: 'overall', mode: '2d', maxHeight: 2000, extrusionOpacity: 0.9 };

// ── ① 分析类型（组卡片：聚合域 = 标准/指定；热点 Gi*；Moran's I） ──
const DEFAULT_ANALYSIS = 'square';
const ANALYSIS_TYPES = {
  square:  { label: '标准网格', group: 'aggregate', desc: '固定方格单元（50/200/400/1000m）空间聚合。' },
  zonal:   { label: '指定单元', group: 'aggregate', desc: '按行政区划/更新单元/控规/用地等面域聚合。' },
  hotspot: { label: '热点 Gi*', group: 'hotspot', dev: true, desc: 'Getis-Ord Gi* 热点分析（开发中）。' },
  moran:   { label: "Moran's I", group: 'moran', dev: true, desc: "Moran's I 空间自相关（开发中）。" },
};
const ANALYSIS_GROUPS = [
  { key: 'aggregate', label: '聚合域（2D/3D）', order: ['square', 'zonal'] },
  { key: 'hotspot',   label: '热点 Gi*',        order: ['hotspot'] },
  { key: 'moran',     label: "Moran's I",        order: ['moran'] },
];

// ── 极性 → 字段 / 色带 ──
// L1（无极性）：舆论热度 grid-warm（低暗红→高金黄）。
// L2 综合：polarity_index(-2~2)归一化 terrain-9 发散；积极/消极/中性：占比 green-3/red-3/blue-3（高值深色）。
const L1_RAMP = 'grid-warm';
const POLARITY_RAMP = { overall: 'terrain-9', positive: 'green-3', negative: 'red-3', neutral: 'blue-3' };
const POLARITY_FIELD = { overall: '_grid_norm', positive: '_grid_h_pos', negative: '_grid_h_neg', neutral: '_grid_h_neu' };
// L2 极性网格高度字段（=颜色 field，同源=该极性点数；颜色+高度都表达"该极性聚合程度"）。L1/L2综合用 _grid_h 总热度。
const POLARITY_HF = { positive: '_grid_h_pos', negative: '_grid_h_neg', neutral: '_grid_h_neu' };
const POLARITY_LABEL = { overall: '综合', positive: '积极', negative: '消极', neutral: '中性' };
const POLARITY_NAME = {
  overall: '综合（红蓝绿发散）', positive: '积极（绿）', negative: '消极（红）', neutral: '中性（蓝）',
};

/** HEATMAP_RAMPS[key].stops 去 density 0 透明首段，归一化到 0~1（方格 fill 不能透明）。 */
function normStops(rampKey) {
  const all = HEATMAP_RAMPS[rampKey].stops.filter(([d]) => d > 0);
  const dMin = all[0][0], dMax = all[all.length - 1][0];
  const span = dMax - dMin || 1;
  return all.map(([d, c]) => [(d - dMin) / span, c]);
}

/** 层级 + 极性 → {field, stops, rampKey, name}。 */
function gridStyle(level, polarity) {
  if (level !== 'L2') {
    return { field: '_grid_h', stops: normStops(L1_RAMP), rampKey: L1_RAMP, name: '舆论热度·点数（暗红→金黄）' };
  }
  const rampKey = POLARITY_RAMP[polarity] || 'terrain-9';
  return { field: POLARITY_FIELD[polarity] || '_grid_norm', stops: normStops(rampKey), rampKey, name: POLARITY_NAME[polarity] };
}

// ── 数据源收集（点层：L2 group 合并极性子层 + L1/L2 单点层） ──
function collectSources() {
  const sources = [];
  for (const l of getLayers()) {
    if (l.kind === 'group' && l.children && l.children.length) {
      let merged = [];
      for (const cid of l.children) {
        const child = getLayer(cid);
        if (child && child.fc && child.fc.features.length) merged = merged.concat(child.fc.features);
      }
      if (merged.length) sources.push({
        value: `group:${l.id}`, label: l.name, level: 'L2', srcName: l.srcName || l.name,
        fc: { type: 'FeatureCollection', features: merged },
      });
    } else if (l.kind === 'point' && l.fc && l.fc.features.length &&
               (l.colorMode === 'l2-positive' || l.colorMode === 'l2-negative' || l.colorMode === 'l2-neutral' ||
                l.colorMode === 'confidence')) {
      sources.push({
        value: `layer:${l.id}`, label: l.name, srcName: l.srcName || l.name,
        level: l.colorMode === 'confidence' ? 'L1' : 'L2', fc: l.fc,
      });
    }
  }
  return sources;
}

// ── 面域层（指定单元用） ──
function collectPolygonLayers() {
  return getLayers().filter((l) => l.kind === 'polygon' && l.fc && l.fc.features && l.fc.features.length);
}
function detectNameCols(fc) {
  if (!fc || !fc.features || !fc.features.length) return [];
  const props = fc.features[0].properties || {};
  const keys = Object.keys(props);
  const PRIORITY = ['name', 'NAME', 'Name', '区名', '街道', '社区', '行政区', '单元'];
  return PRIORITY.filter((k) => keys.includes(k))
    .concat(keys.filter((k) => !PRIORITY.includes(k) && typeof props[k] === 'string'));
}

// ── 预处理：归一化字段写进每格 properties（MapLibre 表达式不能"求和再除"） ──
function _centroid(geom) {
  const ring = (geom && (geom.coordinates && geom.coordinates[0]) || geom.coordinates) || [];
  let minLng = Infinity, maxLng = -Infinity, minLat = Infinity, maxLat = -Infinity;
  for (const [lng, lat] of ring) {
    if (lng < minLng) minLng = lng; if (lng > maxLng) maxLng = lng;
    if (lat < minLat) minLat = lat; if (lat > maxLat) maxLat = lat;
  }
  if (!isFinite(minLng)) return null;
  return [(minLng + maxLng) / 2, (minLat + maxLat) / 2];
}
/** pi(-2~2) → _grid_norm(0~1) 固定分段映射，对齐 valenceOf 5 级阈值：
 *  pi=0→0.5(中性)、pi=±0.15→0.4/0.6(中性边)、pi=±1→0/1(深色饱和)。
 *  替 p95 对称拉伸——后者数据相关（依赖 pi 95 分位）致色带边界无法对齐判断阈值=颜色不准根因。
 *  与 terrain 后端 _pi_to_norm 同公式（grid/terrain 配色一致）。 */
function piToNorm(pi) {
  if (pi == null) return 0.5;
  if (pi <= -1) return 0.0;
  if (pi <= -0.15) return 0.4 * (pi + 1) / 0.85;
  if (pi < 0.15) return 0.4 + 0.2 * (pi + 0.15) / 0.3;
  if (pi < 1) return 0.6 + 0.4 * (pi - 0.15) / 0.85;
  return 1.0;
}

function preprocessGrid(fc) {
  let hasPolarity = false;
  const counts = [], countsPos = [], countsNeg = [], countsNeu = [];
  for (const f of fc.features) {
    if (!f.properties) f.properties = {};
    const p = f.properties;
    const pc = p.point_count || 0;
    if (p.polarity_index != null) {
      hasPolarity = true;
    } else {
      p._grid_norm = p.score_mean != null ? p.score_mean : 0.5;   // 非极性即时 fallback
    }
    const np = (p.n_positive || 0) + (p.n_very_positive || 0);
    const nn = (p.n_negative || 0) + (p.n_very_negative || 0);
    const ne = p.n_neutral || 0;
    p._grid_pos = pc > 0 ? np / pc : 0;   // 极性占比（综合判断/兼容）
    p._grid_neg = pc > 0 ? nn / pc : 0;
    p._grid_neu = pc > 0 ? ne / pc : 0;
    p._grid_n_pos = np;                    // 分极性点数（L2 极性网格 颜色+高度源 = 该极性聚合程度）
    p._grid_n_neg = nn;
    p._grid_n_neu = ne;
    if (f.geometry && f.geometry.type === 'Polygon') p._center = _centroid(f.geometry);
    counts.push(pc); countsPos.push(np); countsNeg.push(nn); countsNeu.push(ne);
  }
  // 高度：低位线性 + offset+sqrt。pc=1→50m, pc=2→100m(接近趴地但区分，替旧"1-2 都=0")；pc≥3 offset+sqrt 起跳(~237m)→满高。
  // 长尾数据(1→73)：低位小且区分(1≠2) + 3 起跳阈值 + sqrt 高位鹤立(用户要的梯度)。
  // _grid_h=总热度(L1+L2综合)；_grid_h_pos/neg/neu=分极性点数高度(L2 极性网格，各自 max)。
  // L1 T1(max=73, 2000m)：1→50/2→100/3→237/6→475/12→751/34→1343/44→1538/73→2000。
  const HEIGHT_OFFSET = 2, HEIGHT_GAMMA = 0.5, LOW_UNIT = 0.025;
  const heightOf = (val, maxVal) => {
    if (val <= 0) return 0;
    if (val <= HEIGHT_OFFSET) return val * LOW_UNIT;            // pc=1→0.025(50m), pc=2→0.05(100m)：低位区分
    const denom = Math.max(maxVal - HEIGHT_OFFSET, 1);
    return Math.min(1, Math.pow((val - HEIGHT_OFFSET) / denom, HEIGHT_GAMMA));  // pc≥3：offset+sqrt 起跳→满高
  };
  const maxOf = (arr) => { arr.sort((a, b) => a - b); return arr.length ? arr[arr.length - 1] : 0; };
  const maxAll = maxOf(counts), maxPos = maxOf(countsPos), maxNeg = maxOf(countsNeg), maxNeu = maxOf(countsNeu);
  for (const f of fc.features) {
    const p = f.properties;
    p._grid_h = heightOf(p.point_count || 0, maxAll);
    p._grid_h_pos = heightOf(p._grid_n_pos || 0, maxPos);
    p._grid_h_neg = heightOf(p._grid_n_neg || 0, maxNeg);
    p._grid_h_neu = heightOf(p._grid_n_neu || 0, maxNeu);
    const pi = p.polarity_index;
    if (pi != null) p._grid_norm = piToNorm(pi);
  }
  return hasPolarity;
}

/** L2 极性网格：过滤掉该极性点数为 0 的格（不渲染无该极性的空格）。综合/L1 不动。
 *  在 preprocessGrid 后调用——_grid_h_pos 等已基于全量 max 算好（0 点格不影响 max），过滤仅剔除渲染。 */
function filterPolarityZero(fc, level, polarity) {
  if (level !== 'L2' || !polarity || polarity === 'overall') return;
  const nField = { positive: '_grid_n_pos', negative: '_grid_n_neg', neutral: '_grid_n_neu' }[polarity];
  if (!nField || !fc.features) return;
  fc.features = fc.features.filter((f) => (f.properties && (f.properties[nField] || 0)) > 0);
}

// ── 渲染 ──
function renderAnalysisCards(dlg) {
  const wrap = dlg.querySelector('#grid-analysis');
  if (!wrap) return;
  wrap.innerHTML = ANALYSIS_GROUPS.map((g) => {
    const cards = g.order.map((key) => {
      const t = ANALYSIS_TYPES[key];
      if (!t) return '';
      return `<button class="hm-analysis-card${key === DEFAULT_ANALYSIS ? ' is-opt-sel' : ''}${t.dev ? ' is-placeholder' : ''}" data-analysis="${key}" type="button" title="${t.desc}"><span class="hm-ac-name">${t.label}</span></button>`;
    }).join('');
    return `<div class="hm-tier" data-tier="${g.key}"><div class="hm-tier-label">${g.label}</div><div class="hm-tier-cards">${cards}</div></div>`;
  }).join('');
}

function populateSources(srcs, level) {
  const sel = document.getElementById('grid-source');
  if (!sel) return;
  const filtered = level ? srcs.filter((s) => s.level === level) : srcs;
  sel.innerHTML = filtered.length
    ? filtered.map((s) => `<option value="${s.value}">${s.label}</option>`).join('')
    : `<option value="" disabled>（${level || '该层级'}无情绪点图层，先导入 ${level || 'L1/L2'} 数据）</option>`;
}

function constrainLevelOptions(srcs) {
  const sel = document.getElementById('grid-level');
  if (!sel) return;
  const present = new Set(srcs.map((s) => s.level));
  const FIXED = ['L1', 'L2', 'L3', 'L4'];
  let firstAvailable = null;
  sel.innerHTML = FIXED.map((lv) => {
    const has = present.has(lv);
    if (has && !firstAvailable) firstAvailable = lv;
    return `<option value="${lv}" ${has ? '' : 'disabled'}>${lv}${has ? '' : '（无数据）'}</option>`;
  }).join('');
  sel.value = firstAvailable || 'L1';
}

function populatePolygonLayers() {
  const sel = document.getElementById('grid-polygon-layer');
  if (!sel) return;
  const polys = collectPolygonLayers();
  sel.innerHTML = polys.length
    ? polys.map((l) => `<option value="${l.id}">${l.name}</option>`).join('')
    : '<option value="" disabled>（暂无面域图层，先导入行政区划/单元面域）</option>';
}

function populateNameCols(fc) {
  const sel = document.getElementById('grid-name-col');
  if (!sel) return;
  const cols = detectNameCols(fc);
  sel.innerHTML = '<option value="">（不显示名称）</option>' + cols.map((c) => `<option value="${c}">${c}</option>`).join('');
}

function renderRampPreview(dlg, level, polarity) {
  const wrap = dlg.querySelector('#grid-ramp-preview');
  if (!wrap) return;
  const style = gridStyle(level, polarity);
  const ramp = HEATMAP_RAMPS[style.rampKey];
  const segs = ramp ? rampDisplaySegs(style.rampKey, ramp) : style.stops.map(([, c]) => c);
  const segHtml = segs.map((c) => `<span class="hm-style-seg" style="background:${c}"></span>`).join('');
  // .hm-style-preview = 只读色板预览容器（CSS：flex row + .hm-style-bar flex:1/height:18px + .hm-style-seg height:100%）
  // 纯色带，不显示文字名（与 heatmap 色带一致：heatmap .hm-style-name 也是 display:none）
  wrap.innerHTML = `<div class="hm-style-preview"><span class="hm-style-bar">${segHtml}</span></div>`;
}

/** 随 analysis + level 切 square/zonal/polarity 显隐 + 色板预览。 */
function constrainParams(dlg) {
  const analysis = selectedAnalysis(dlg);
  const level = dlg.querySelector('#grid-level')?.value || 'L1';
  setHidden(dlg, '#grid-cell-section', analysis !== 'square');
  setHidden(dlg, '#grid-zonal-section', analysis !== 'zonal');
  setHidden(dlg, '#grid-namecol-section', analysis !== 'zonal');
  setHidden(dlg, '#grid-polarity-section', level !== 'L2');
  renderRampPreview(dlg, level, selectedPolarity(dlg));
}

function selectedAnalysis(dlg) {
  return dlg.querySelector('.hm-analysis-card.is-opt-sel')?.dataset.analysis || DEFAULT_ANALYSIS;
}
function selectedPolarity(dlg) {
  return dlg.querySelector('#grid-polarity .buf-cap.is-sel')?.dataset.polarity || 'overall';
}
function setHidden(dlg, sel, hidden) { const el = dlg.querySelector(sel); if (el) el.hidden = hidden; }

// ── 参数回填 / 读取 ──
function applyParams(dlg, p) {
  const analysis = p.analysis || DEFAULTS.analysis;
  dlg.querySelectorAll('.hm-analysis-card').forEach((c) => c.classList.toggle('is-opt-sel', c.dataset.analysis === analysis));
  // level 不在此设（由 constrainLevelOptions 默认 + 编辑态 seed.level 在 openGridDialog 设），保持联动递进
  const cell = p.cellSize ?? DEFAULTS.cellSize;
  const numEl = dlg.querySelector('#grid-cell-num'); if (numEl) numEl.value = cell;
  const slider = dlg.querySelector('#grid-cell');
  if (slider) slider.value = Math.min(Number(slider.max), Math.max(Number(slider.min), cell));
  const pol = p.polarity || DEFAULTS.polarity;
  dlg.querySelectorAll('#grid-polarity .buf-cap').forEach((c) => c.classList.toggle('is-sel', c.dataset.polarity === pol));
  const mode = p.mode || DEFAULTS.mode;
  dlg.querySelectorAll('#grid-mode .buf-cap').forEach((c) => c.classList.toggle('is-sel', c.dataset.mode === mode));
  const mh = p.maxHeight ?? DEFAULTS.maxHeight;
  const mhEl = dlg.querySelector('#grid-extrusion-scale'); if (mhEl) mhEl.value = mh;
  const mhVal = dlg.querySelector('#grid-extrusion-val'); if (mhVal) mhVal.textContent = `${Math.round(mh)} m`;
  const eo = p.extrusionOpacity ?? DEFAULTS.extrusionOpacity;
  const eoEl = dlg.querySelector('#grid-extrusion-opacity'); if (eoEl) eoEl.value = eo;
  const eoVal = dlg.querySelector('#grid-extrusion-opacity-val'); if (eoVal) eoVal.textContent = `${Math.round(Number(eo) * 100)}%`;
}

function readParams(dlg) {
  return {
    analysis: selectedAnalysis(dlg),
    level: dlg.querySelector('#grid-level').value,
    source: dlg.querySelector('#grid-source').value,
    cellSize: Number(dlg.querySelector('#grid-cell-num').value) || DEFAULTS.cellSize,
    polygonLayer: dlg.querySelector('#grid-polygon-layer').value,
    nameCol: dlg.querySelector('#grid-name-col').value,
    polarity: selectedPolarity(dlg),
    mode: dlg.querySelector('#grid-mode .buf-cap.is-sel')?.dataset.mode || DEFAULTS.mode,
    maxHeight: Number(dlg.querySelector('#grid-extrusion-scale').value),
    extrusionOpacity: Number(dlg.querySelector('#grid-extrusion-opacity')?.value ?? 1),
  };
}

export function openGridDialog(layerId, preset = null) {
  const dlg = dialogEl();
  if (!dlg) return;

  let seed = null;
  if (layerId) {
    const lyr = getLayer(layerId);
    if (lyr && lyr.paint && lyr.paint._ui && lyr.paint._ui.tool === 'grid') seed = lyr.paint._ui;
  }
  renderAnalysisCards(dlg);
  const srcs = collectSources();
  constrainLevelOptions(srcs);          // 设 L1-L4 选项 + firstAvailable 默认选中
  populatePolygonLayers();
  if (seed && seed.level) dlg.querySelector('#grid-level').value = seed.level;   // 编辑态 level
  // 预设范围（Range tab 按钮）：analysis 走 preset（默认 zonal）；否则 seed 或 DEFAULTS
  const params = seed || (preset ? { ...DEFAULTS, analysis: preset.analysis || 'zonal' } : DEFAULTS);
  applyParams(dlg, params);   // 回填 analysis/cell/polarity/mode/extrusion（含卡片选中态）
  populateSources(srcs, dlg.querySelector('#grid-level').value);   // 点层按当前 level 过滤（联动递进）

  // 编辑态：回填点层 / 面域层（触发 name_col 填充）
  if (seed) {
    if (seed.source && dlg.querySelector(`#grid-source option[value="${seed.source}"]`))
      dlg.querySelector('#grid-source').value = seed.source;
    if (seed.polygonLayer && dlg.querySelector(`#grid-polygon-layer option[value="${seed.polygonLayer}"]`)) {
      dlg.querySelector('#grid-polygon-layer').value = seed.polygonLayer;
      const poly = getLayer(seed.polygonLayer);
      if (poly && poly.fc) populateNameCols(poly.fc);
      if (seed.nameCol) dlg.querySelector('#grid-name-col').value = seed.nameCol;
    }
  } else if (preset && preset.polygonLayer) {
    // 预设范围：预选面域层 + name_col（populatePolygonLayers 后 option 已就绪）
    if (dlg.querySelector(`#grid-polygon-layer option[value="${preset.polygonLayer}"]`))
      dlg.querySelector('#grid-polygon-layer').value = preset.polygonLayer;
    const poly = getLayer(preset.polygonLayer);
    if (poly && poly.fc) populateNameCols(poly.fc);
    if (preset.nameCol && dlg.querySelector(`#grid-name-col option[value="${preset.nameCol}"]`))
      dlg.querySelector('#grid-name-col').value = preset.nameCol;
  }
  constrainParams(dlg);
  dlg.dataset.editLayerId = layerId || '';

  if (!srcs.length) toast.info('请先导入 L1/L2 情绪点数据');
  const genBtn = dlg.querySelector('#grid-generate');
  if (genBtn) genBtn.textContent = layerId ? '调整' : '生成';   // 编辑态=「调整」，新建态=「生成」
  openParamPanel('grid');
}

async function generateGrid() {
  const dlg = dialogEl();
  const p = readParams(dlg);
  const type = ANALYSIS_TYPES[p.analysis];
  if (!type || type.dev) { toast.info(`${type?.label || '该分析'}（开发中）`); return; }

  const src = collectSources().find((s) => s.value === p.source);
  if (!src || !src.fc || !src.fc.features || !src.fc.features.length) {
    toast.error('请先选择一个有效的情绪点图层'); return;
  }

  const btn = dlg.querySelector('#grid-generate');
  btn.disabled = true; btn.textContent = '生成中…';

  try {
    let fc, paint;
    const analysisLabel = { square: '标准网格', zonal: '指定单元' }[p.analysis];
    const polLabel = p.level === 'L2' ? (POLARITY_LABEL[p.polarity] || '综合') : '热度';
    const modeLabel = p.mode === '3d' ? '3D' : '2D';
    const sizeTag = p.analysis === 'square' ? `${p.cellSize}m` : '面域';

    if (p.analysis === 'square') {
      // square：后端 create_square_grid 聚合（EPSG:4546 米制精确）+ MapLibre fill/fill-extrusion 自创渲染
      if (p.cellSize <= 0) { toast.error('方格边长需 > 0'); return; }
      const res = await runGrid({ geojson: src.fc, grid_type: 'square', cell_size: p.cellSize, unit: 'm' });
      if (!res || !res.success || !res.geojson) throw new Error((res && res.message) || '后端返回异常');
      fc = JSON.parse(JSON.stringify(res.geojson));
      if (!fc.features || !fc.features.length) { toast.error('聚合结果为空'); return; }
      if (fc.features.length > 2000) toast.info(`已生成 ${fc.features.length} 个格，数量较多；3D 渲染可能偏慢`, 4500);
      preprocessGrid(fc);   // _grid_*（极性归一化，MapLibre 着色）+ _grid_h/_grid_h_pos…（offset+sqrt 高度）
      filterPolarityZero(fc, p.level, p.polarity);   // L2 极性网格去该极性点数=0 的格（不渲染空格）
      const style = gridStyle(p.level, p.polarity);
      paint = { fillOn: true, _ui: { tool: 'grid', analysis: 'square', level: p.level, source: p.source,
                                     cellSize: p.cellSize, polarity: p.polarity, mode: p.mode, heightField: (p.level === 'L2' && POLARITY_HF[p.polarity]) ? POLARITY_HF[p.polarity] : '_grid_h', maxHeight: p.maxHeight, extrusionOpacity: p.extrusionOpacity },
                gridField: style.field, gridStops: style.stops, fillOpacity: p.extrusionOpacity };   // 显式 fillOpacity 绕开 addLayer 默认 0.3（修 2D 首次透明）
    } else {
      // zonal：后端精确面域聚合 + MapLibre 渲染（deck.gl GridLayer 是方格聚合，不适合固定面域 zonal）
      const poly = getLayer(p.polygonLayer);
      if (!poly || !poly.fc || !poly.fc.features || !poly.fc.features.length) {
        toast.error('请先选择一个有效的聚合面域图层'); return;
      }
      const res = await runAggregate({ points_geojson: src.fc, polygons_geojson: poly.fc, agg_cols: ['score'], name_col: p.nameCol || null });
      if (!res || !res.success || !res.geojson) throw new Error((res && res.message) || '后端返回异常');
      fc = JSON.parse(JSON.stringify(res.geojson));   // 深拷贝（preprocessGrid 原地写 _grid_*，防污染共享对象）
      if (!fc.features || !fc.features.length) { toast.error('聚合结果为空'); return; }
      if (fc.features.length > 2000) toast.info(`已生成 ${fc.features.length} 个面域，数量较多`, 4500);
      const hasPolarity = preprocessGrid(fc);
      filterPolarityZero(fc, p.level, p.polarity);   // L2 极性网格去该极性点数=0 的格（不渲染空格）
      if (!hasPolarity && p.level === 'L2') toast.info('该点层缺少极性字段，按分数比例近似降级', 4500);
      const style = gridStyle(p.level, p.polarity);
      paint = { fillOn: true, _ui: { tool: 'grid', analysis: 'zonal', level: p.level, source: p.source,
                                     polygonLayer: p.polygonLayer, nameCol: p.nameCol,
                                     polarity: p.polarity, mode: p.mode, heightField: (p.level === 'L2' && POLARITY_HF[p.polarity]) ? POLARITY_HF[p.polarity] : '_grid_h', maxHeight: p.maxHeight, extrusionOpacity: p.extrusionOpacity },
                gridField: style.field, gridStops: style.stops, fillOpacity: p.extrusionOpacity };   // 显式 fillOpacity 绕开 addLayer 默认 0.3（修 2D 首次透明）
    }

    // 命名新规：时间·极性/类型·分析类型·方格参数·文件名（2D/3D 进图层标签，不进文件名）
    const tPrefix = deriveTimeTag(src.fc) ? `${deriveTimeTag(src.fc)}·` : '';
    const labelName = `${tPrefix}${polLabel}·${analysisLabel}·${sizeTag}·${src.srcName}`;
    const editId = dlg.dataset.editLayerId;
    const editLyr = editId ? getLayer(editId) : null;
    let L;
    if (editLyr) {
      // 编辑态（要素按钮）：原地更新当前层——不新建、不关其他层（layer id 稳定）
      editLyr.fc = fc; editLyr.paint = paint; editLyr.name = labelName; editLyr.srcName = src.srcName;
      renderLayer(editLyr);
      L = editLyr;
    } else {
      // 新建态：addLayer + 独占显示（关其他可见层，仿 heatmap generateHeatmap:775）
      L = addLayer({ name: labelName, kind: 'polygon', fc, paint });
      L.srcName = src.srcName;
      renderLayer(L);
      for (const other of [...getLayers()]) {
        if (other.id === L.id || other.kind === 'group') continue;
        if (other.visible) { setLayerVisible(other.id, false); renderLayer(other); }   // 独占显示：关其他所有可见层（generateGrid 与 setViewMode 场景独立，勿耦合）
      }
    }
    const bb = fcBBox(fc); if (bb) fitBoundsTo(bb);
    setView3D(p.mode === '3d');   // fitBounds 后设 pitch（3D→倾斜+暗底图 / 2D→复原），防被打断
    selectLayer(L.id);            // 选中（Overview 内容跟随）但不强制弹右栏（工具生成不自动开 Overview/Table）
    renderLayerList(); refreshLegend(); reorderAllZ(); showLayerManager();
    document.dispatchEvent(new CustomEvent('layers:changed'));
    closeParamPanel();
    toast.success(`已${editLyr ? '调整' : '生成'} ${analysisLabel} · ${polLabel} · ${modeLabel}`);
  } catch (e) {
    console.error('[grid]', e);
    toast.error(`网格分析失败：${e.message || e}（确认后端已启动：双击 start.bat）`);
  } finally {
    btn.disabled = false; btn.textContent = dlg.dataset.editLayerId ? '调整' : '生成';
  }
}

export function initGridTool() {
  const dlg = dialogEl();
  if (!dlg) return;

  // ① 分析类型组卡片（dev 类型 toast 不选中）
  dlg.querySelector('#grid-analysis').addEventListener('click', (e) => {
    const b = e.target.closest('.hm-analysis-card');
    if (!b) return;
    const key = b.dataset.analysis;
    const type = ANALYSIS_TYPES[key];
    if (type?.dev) { toast.info(`${type.label}（开发中）`); return; }
    dlg.querySelectorAll('.hm-analysis-card').forEach((x) => x.classList.remove('is-opt-sel'));
    b.classList.add('is-opt-sel');
    constrainParams(dlg);
  });

  // ② 数据层级 → 联动递进：level 变 → 点层重新按 level 过滤 + 重置选中 → 切极性/参数/色板
  dlg.querySelector('#grid-level').addEventListener('change', () => {
    populateSources(collectSources(), dlg.querySelector('#grid-level').value);
    constrainParams(dlg);
  });

  // 方格边长：输入 ↔ 滑块 ↔ preset
  const num = dlg.querySelector('#grid-cell-num');
  const slider = dlg.querySelector('#grid-cell');
  const clamp = (n) => Math.max(Number(slider.min), Math.min(Number(slider.max), n));
  num.addEventListener('input', () => { slider.value = clamp(Number(num.value) || 0); });
  slider.addEventListener('input', () => { num.value = slider.value; });
  dlg.querySelector('#grid-presets').addEventListener('click', (e) => {
    const b = e.target.closest('.buf-preset'); if (!b) return;
    num.value = b.dataset.cell; slider.value = clamp(Number(b.dataset.cell));
  });

  // 面域层 → name_col 联动
  dlg.querySelector('#grid-polygon-layer').addEventListener('change', () => {
    const poly = getLayer(dlg.querySelector('#grid-polygon-layer').value);
    if (poly && poly.fc) populateNameCols(poly.fc);
  });

  // 极性胶囊（仅 L2）→ 色板预览
  dlg.querySelector('#grid-polarity').addEventListener('click', (e) => {
    const b = e.target.closest('.buf-cap'); if (!b) return;
    dlg.querySelectorAll('#grid-polarity .buf-cap').forEach((x) => x.classList.remove('is-sel'));
    b.classList.add('is-sel');
    renderRampPreview(dlg, dlg.querySelector('#grid-level').value, b.dataset.polarity);
  });

  // 模式胶囊
  dlg.querySelector('#grid-mode').addEventListener('click', (e) => {
    const b = e.target.closest('.buf-cap'); if (!b) return;
    dlg.querySelectorAll('#grid-mode .buf-cap').forEach((x) => x.classList.remove('is-sel'));
    b.classList.add('is-sel');
  });

  // 最大柱高 live label（绝对米；3D 柱体高度 = _grid_h × maxHeight）
  dlg.querySelector('#grid-extrusion-scale').addEventListener('input', (e) => {
    dlg.querySelector('#grid-extrusion-val').textContent = `${Math.round(Number(e.target.value))} m`;
  });

  // 3D 透明度 live label
  dlg.querySelector('#grid-extrusion-opacity').addEventListener('input', (e) => {
    dlg.querySelector('#grid-extrusion-opacity-val').textContent = `${Math.round(Number(e.target.value) * 100)}%`;
  });

  dlg.querySelector('#grid-generate')?.addEventListener('click', generateGrid);
}
