// ═══ heatmap-tool.js — HeatMap 三阶引导：①分析类型 / ②数据源 / ③显示样式 ═══
// v3 (2026-06-19): kepler 配色语言；7 大类喜怒哀乐愁急盼；样式按 ①+② 联动；analysis-card hover infopanel
import {
  getLayers, getChildren, addLayer, removeLayer, getLayer, setLayerVisible, selectLayer,
  HEATMAP_RAMPS, HEATMAP_RAMP_KEYS,
  EMOTION_TYPE_COLORS, EMOTION_TYPE_ORDER,
  EMOTION_MACRO, EMOTION_MACRO_ORDER, EMOTION_MACRO_MAP, macroOfPolarity,
  getHeatmapForSource, setHeatmapForSource, removeHeatmapSource,
} from './state.js';
import { renderLayer, removeLayerFromMap } from './map.js';
import { toast } from './toast.js';

const DIALOG_ID = 'heatmap-dialog';

// 默认值（与 state.js heatmap paint defaults 对齐）
const DEFAULTS = {
  radiusM: 300, opacity: 70, intensity: 1.0,
  weightField: 'emotion_intensity', curve: 'linear',
  intensityMin: 0, minzoom: 0, maxzoom: 22,
};

// ── ① 分析类型预设（3 排分组：总体情况 / 类型细分 / 多维归因）──
// tier 决定 ①排版分组 + ②类型/表现胶囊是否启用（overall 禁用、segment 启用）。
const DEFAULT_ANALYSIS = 'terrain';
const ANALYSIS_PRESETS = {
  terrain: { label: '情绪地形（2D/3D）', tier: 'overall',
    desc: '综合情绪密度/强度表达。L1=综合舆情热度（2D 彩虹）；L2=正负面情绪高低洼地（3D 地形，红洼/蓝中/绿高）。',
    preview: 'assets/analysis-previews/terrain.svg' },
  grid:    { label: '情绪网格（2D/3D）', tier: 'overall',
    desc: '小尺度网格聚合。L1=2D 网格/3D 柱体（暖色）；L2=3D 柱体，按特性显积极/消极/中性高点分布。',
    preview: 'assets/analysis-previews/grid.svg' },
  positive:{ label: '积极', tier: 'segment',
    desc: '类型细分：只看积极情绪密度（仅 L2）。胶囊色（喜→乐）渐变 7 段。',
    preview: 'assets/analysis-previews/positive.svg' },
  negative:{ label: '消极', tier: 'segment',
    desc: '类型细分：只看消极情绪密度（仅 L2）。胶囊色（怒→哀→愁）渐变 7 段。',
    preview: 'assets/analysis-previews/negative.svg' },
  neutral: { label: '中性', tier: 'segment',
    desc: '类型细分：只看中性情绪密度（仅 L2）。胶囊色（急→盼）渐变 7 段。',
    preview: 'assets/analysis-previews/classify.svg' },
  factor:      { label: '情绪因子', tier: 'attribution',
    desc: '多维归因：4 应用 × 5 因子 = 20 视角，"消极因何而起"。待后续批次。',
    preview: 'assets/analysis-previews/factor.svg', placeholder: true },
  attribution: { label: '要素归因', tier: 'attribution',
    desc: '多维归因：按空间要素归因。待后续批次。',
    preview: 'assets/analysis-previews/factor.svg', placeholder: true },
};
const ANALYSIS_TIERS = [
  { key: 'overall',     label: '总体情况', order: ['terrain', 'grid'] },
  { key: 'segment',     label: '类型细分', order: ['positive', 'negative', 'neutral'] },
  { key: 'attribution', label: '多维归因', order: ['factor', 'attribution'] },
];

// ── ③ 自动色板（按 analysis + level + 特性）—— 色板随类型自动选定，用户不再手选 ──
// 返回 { ramp, name, dev?, tip, buttons:[{dim,label,dev?}] }：
//   ramp  = HEATMAP_RAMPS key；name = ③只读预览标签；buttons = 生成按钮（2D/3D 拆分）。
function computeStyle(analysis, level, polarity) {
  if (analysis === 'terrain') {
    if (level === 'L1') return { ramp: 'rainbow', name: '综合彩虹',
      tip: 'L1 综合舆情热度（2D 彩虹），体现密度与关注度，不暗示极性。',
      buttons: [{ dim: '2d', label: '生成 2D 彩虹图' }] };
    return { ramp: 'terrain-9', name: '红蓝绿地形（9 段）', dev: true,
      tip: 'L2 3D 情绪地形：山顶积极绿 / 山腰中性蓝 / 山底消极红。',
      buttons: [{ dim: '3d', label: '生成 3D 地形图', dev: true }] };
  }
  if (analysis === 'grid') {
    // 网格聚合渲染（binning）本次未实现，2D/3D 均占位待后续批次
    if (level === 'L1') return { ramp: 'grid-warm', name: '网格暖色', dev: true,
      tip: 'L1 小尺度舆情热度：2D 色块网格 / 3D 网格柱体（聚合渲染待开发）。',
      buttons: [{ dim: '2d', label: '生成 2D 网格图', dev: true }, { dim: '3d', label: '生成 3D 柱体图', dev: true }] };
    const ramp = { ALL: 'terrain-9', P: 'green-3', N: 'red-3', O: 'blue-3' }[polarity] || 'terrain-9';
    const nm = { ALL: '综合（红蓝绿 9 段）', P: '积极（绿 3 段）', N: '消极（红 3 段）', O: '中性（蓝 3 段）' }[polarity] || '综合';
    return { ramp, name: nm, dev: true,
      tip: 'L2 3D 网格柱体：积极/消极/中性各自高点的空间分布。',
      buttons: [{ dim: '3d', label: '生成 3D 柱体图', dev: true }] };
  }
  if (analysis === 'positive') return { ramp: 'positive', name: '积极（喜→乐）',
    tip: '类型细分：积极情绪密度（仅 L2）。', buttons: [{ dim: '2d', label: '生成 2D 积极图' }] };
  if (analysis === 'negative') return { ramp: 'negative', name: '消极（怒→哀→愁）',
    tip: '类型细分：消极情绪密度（仅 L2）。', buttons: [{ dim: '2d', label: '生成 2D 消极图' }] };
  if (analysis === 'neutral')  return { ramp: 'neutral',  name: '中性（急→盼）',
    tip: '类型细分：中性情绪密度（仅 L2）。', buttons: [{ dim: '2d', label: '生成 2D 中性图' }] };
  // factor / attribution：占位
  return { ramp: null, name: '待开发', dev: true, tip: '多维归因，后续批次开发。', buttons: [] };
}

// ── infopanel：analysis-card hover 弹出 Kepler 风格看板（预览图 + 标题 + 描述 + 标签）──
let _infoPanelEl = null;
function ensureInfoPanel() {
  if (_infoPanelEl) return _infoPanelEl;
  const dlg = document.getElementById(DIALOG_ID);
  const el = document.createElement('div');
  el.className = 'hm-infopanel';
  el.id = 'hm-infopanel';
  el.innerHTML = `
    <div class="hm-infopanel-preview"><img alt="" id="hm-infopanel-img"></div>
    <div class="hm-infopanel-body">
      <div class="hm-infopanel-title" id="hm-infopanel-title"></div>
      <div class="hm-infopanel-shortdesc" id="hm-infopanel-shortdesc"></div>
      <div class="hm-infopanel-desc" id="hm-infopanel-desc"></div>
      <div class="hm-infopanel-tags" id="hm-infopanel-tags"></div>
    </div>`;
  (dlg || document.body).appendChild(el);
  _infoPanelEl = el;
  return el;
}
function showInfoPanel(card, key) {
  const p = ANALYSIS_PRESETS[key];
  if (!p) return;
  const el = ensureInfoPanel();
  const img = el.querySelector('#hm-infopanel-img');
  const title = el.querySelector('#hm-infopanel-title');
  const shortDesc = el.querySelector('#hm-infopanel-shortdesc');
  const desc = el.querySelector('#hm-infopanel-desc');
  const tags = el.querySelector('#hm-infopanel-tags');

  img.src = p.preview || '';
  img.onerror = () => { img.style.display = 'none'; };
  img.onload = () => { img.style.display = 'block'; };
  title.textContent = p.label;
  shortDesc.textContent = p.shortDesc || '';
  desc.textContent = p.desc || '';
  tags.innerHTML = (p.tags || []).map((t) =>
    `<span class="hm-infopanel-tag">${t}</span>`
  ).join('');

  // 定位：弹窗右侧 +8px，上端对齐
  const dlg = document.getElementById(DIALOG_ID);
  const r = dlg.getBoundingClientRect();
  el.classList.add('is-show');
  const ew = el.offsetWidth;
  let left = r.right + 8;
  let top = r.top;
  if (left + ew > window.innerWidth - 8) left = Math.max(8, r.left - ew - 8);
  // 下溢保护
  const eh = el.offsetHeight;
  if (top + eh > window.innerHeight - 8) top = Math.max(8, window.innerHeight - eh - 8);
  el.style.left = left + 'px';
  el.style.top = top + 'px';
}
function hideInfoPanel() { if (_infoPanelEl) _infoPanelEl.classList.remove('is-show'); }

/** 渲染 ① 分析类型卡（2 列） */
function renderAnalysisCards(dlg) {
  const wrap = dlg.querySelector('#hm-analysis');
  if (!wrap) return;
  // 3 排分组（总体情况 / 类型细分 / 多维归因），每排一个标题 + 卡片网格
  wrap.innerHTML = ANALYSIS_TIERS.map((tier) => {
    const cards = tier.order.map((key) => {
      const p = ANALYSIS_PRESETS[key];
      if (!p) return '';
      return `<button class="hm-analysis-card${key === DEFAULT_ANALYSIS ? ' is-opt-sel' : ''}${p.placeholder ? ' is-placeholder' : ''}" data-analysis="${key}" data-tier="${tier.key}" type="button">
        <span class="hm-ac-name">${p.label}</span>
        <span class="hm-info hm-info-card" data-analysis-key="${key}">i</span>
      </button>`;
    }).join('');
    return `<div class="hm-tier" data-tier="${tier.key}">
      <div class="hm-tier-label">${tier.label}</div>
      <div class="hm-tier-cards">${cards}</div>
    </div>`;
  }).join('');
}

/** 当前选中的分析类型 key */
function selectedAnalysis(dlg) {
  return dlg.querySelector('.hm-analysis-card.is-opt-sel')?.dataset?.analysis || DEFAULT_ANALYSIS;
}
/** 当前分析类型所属 tier（overall/segment/attribution） */
function selectedTier(dlg) {
  const key = selectedAnalysis(dlg);
  return ANALYSIS_PRESETS[key]?.tier || 'overall';
}

function dialogEl() { return document.getElementById(DIALOG_ID); }

/** 收集可用数据源（同 v2，保留 group 合并 + 极性 child 映射） */
function collectSources() {
  const sources = [];
  for (const l of getLayers()) {
    if (l.kind === 'group' && l.children && l.children.length) {
      const childByPolarity = {};
      let merged = [];
      for (const cid of l.children) {
        const child = getLayer(cid);
        if (child && child.fc && child.fc.features.length) {
          childByPolarity[child.colorMode] = child;
          merged = merged.concat(child.fc.features);
        }
      }
      if (merged.length) {
        sources.push({
          value: `group:${l.id}`, label: l.name, level: 'L2',
          fc: { type: 'FeatureCollection', features: merged },
          sourceKey: `group:${l.id}`, group: l, childByPolarity,
        });
      }
    } else if (l.kind === 'point' && l.fc && l.fc.features.length &&
               (l.colorMode === 'l2-positive' || l.colorMode === 'l2-negative' || l.colorMode === 'l2-neutral' ||
                l.colorMode === 'confidence')) {
      sources.push({
        value: `layer:${l.id}`, label: l.name,
        level: l.colorMode === 'confidence' ? 'L1' : 'L2',
        fc: l.fc, sourceKey: `layer:${l.id}`,
      });
    }
  }
  return sources;
}

/** 取 feature 的小类（emotion_type 真实值优先，缺失按极性兜底） */
function emotionTypeOf(f) {
  const p = (f && f.properties) || {};
  const et = p.emotion_type;
  if (et) return et;
  const pol = p.polarity;
  if (pol === 'Very Positive' || pol === 'Positive') return '喜悦满意';
  if (pol === 'Very Negative') return '愤怒';
  if (pol === 'Negative') return '不满抱怨';
  return '期待建议';
}

/** 小类 → 大类（先查 EMOTION_MACRO_MAP，再按 polarity 兜底） */
function macroOfFeature(f) {
  const t = emotionTypeOf(f);
  if (EMOTION_MACRO_MAP[t]) return EMOTION_MACRO_MAP[t];
  return macroOfPolarity((f.properties || {}).polarity);
}

/** 统计当前 fc 的小类计数（动态归纳） */
function typeCountsFor(fc) {
  const counts = {};
  if (!fc || !fc.features) return counts;
  for (const f of fc.features) {
    const t = emotionTypeOf(f);
    counts[t] = (counts[t] || 0) + 1;
  }
  return counts;
}

/** 渲染大类胶囊（7 类固定；每个胶囊带 data-tip 供 hover popup 使用）。
 *  禁用条件：非 L2（无情绪字段），或 tier=overall/attribution（总体/归因不涉及类型细分）。 */
function renderMacroChips(dlg, level) {
  const wrap = dlg.querySelector('#hm-macros');
  if (!wrap) return;
  const tier = selectedTier(dlg);
  if (level !== 'L2' || tier !== 'segment') {
    const why = level !== 'L2' ? `${level || '当前层级'} 无情绪分类字段（仅 L2）` : '总体/归因分析不涉及类型细分';
    wrap.innerHTML = `<div class="hm-hint hm-empty">${why}</div>`;
    return;
  }
  wrap.innerHTML = EMOTION_MACRO_ORDER.map((k) => {
    const m = EMOTION_MACRO[k];
    const tip = `${k} · ${m.desc}`.replace(/"/g, '&quot;');
    return `<label class="hm-macro-chip" data-macro="${k}" data-polarity="${m.polarity}" data-tip="${tip}" style="--chip-color:${m.color}">
      <input type="checkbox" />
      <span class="hm-macro-name">${k}</span>
    </label>`;
  }).join('');
}

/** 渲染小类胶囊（按当前 fc 动态归纳）。
 *  v5：L1/L3/L4 无 emotion_type 字段 → 渲染禁用提示，不显示胶囊。 */
function renderTypeChips(dlg, fc, level) {
  const wrap = dlg.querySelector('#hm-types');
  if (!wrap) return;
  if (level !== 'L2' || selectedTier(dlg) !== 'segment') {
    wrap.innerHTML = `<div class="hm-hint hm-empty">总体/归因分析或非 L2，无类型/表现筛选</div>`;
    updateFoldCount(dlg, 'type');
    return;
  }
  const counts = typeCountsFor(fc);
  const types = Object.keys(counts);
  types.sort((a, b) => {
    const ia = EMOTION_TYPE_ORDER.indexOf(a), ib = EMOTION_TYPE_ORDER.indexOf(b);
    if (ia !== -1 && ib !== -1) return ia - ib;
    if (ia !== -1) return -1;
    if (ib !== -1) return 1;
    return counts[b] - counts[a];
  });
  wrap.innerHTML = types.map((t) => {
    const c = EMOTION_TYPE_COLORS[t] || '#888888';
    const macro = EMOTION_MACRO_MAP[t] || '';
    const n = counts[t] || 0;
    return `<label class="hm-type-chip is-on" data-type="${t}" data-macro="${macro}" style="--chip-color:${c}">
      <input type="checkbox" checked />
      <span class="hm-type-dot"></span>
      <span class="hm-type-name">${t}</span>
      <span class="hm-type-count">${n}</span>
    </label>`;
  }).join('');
  updateFoldCount(dlg, 'type');
}

/** 渲染 ③ 只读色板预览（色板随 analysis+level+特性自动；用户不再手选）。
 *  显示当前自动选定色板的离散分段条 + 名称 + i 说明。 */
function renderStylePreview(dlg) {
  const wrap = dlg.querySelector('#hm-styles');
  if (!wrap) return;
  const analysis = selectedAnalysis(dlg);
  const level = dlg.querySelector('#hm-level').value;
  const polarity = dlg.querySelector('#hm-subset').value;
  const st = computeStyle(analysis, level, polarity);
  // 占位（factor/attribution）
  if (!st.buttons.length) {
    wrap.innerHTML = `<div class="hm-hint">${st.name}（后续批次）</div>`;
    renderGenerateButtons(dlg, st);
    return;
  }
  const ramp = st.ramp ? HEATMAP_RAMPS[st.ramp] : null;
  const segs = ramp ? ramp.stops.filter(([d]) => d > 0).map(([, c]) => c) : ['#ccc'];
  const segHtml = segs.map((c) => `<span class="hm-style-seg" style="background:${c}"></span>`).join('');
  const tip = st.tip.replace(/"/g, '&quot;');
  wrap.innerHTML = `<div class="hm-style-preview">
    <span class="hm-style-bar">${segHtml}</span>
    <span class="hm-style-name">${st.name}</span>
    ${st.dev ? '<span class="hm-style-dev-tag">3D 待开发</span>' : ''}
    <span class="hm-info" data-tip="${tip}">i</span>
  </div>`;
  renderGenerateButtons(dlg, st);
}

/** 渲染生成按钮区（按 computeStyle.buttons 动态拆 2D/3D；单/双按钮）。 */
function renderGenerateButtons(dlg, st) {
  const foot = dlg.querySelector('#hm-generate-row');
  if (!foot) return;
  if (!st.buttons.length) {
    foot.innerHTML = `<button class="sec-btn" disabled>该分析待开发</button>`;
    return;
  }
  foot.innerHTML = st.buttons.map((b, i) =>
    `<button class="sec-btn${i === 0 ? ' is-primary' : ''}${b.dev ? ' is-dev' : ''}"
       data-dim="${b.dim}" data-ramp="${st.ramp || ''}" ${b.dev ? 'disabled' : ''} type="button">
       ${b.label}${b.dev ? '（待开发）' : ''}</button>`).join('');
}

/** 选大类胶囊 → 自动选/取消其下小类（传导）。
 *  v4：大类全空 = 小类全空（与用户直觉对齐：取消全部大类 = 一个都不要）。
 *      想全部展示 → 极性下拉切回"综合"。 */
function applyMacroToTypes(dlg) {
  const onMacros = new Set(
    [...dlg.querySelectorAll('.hm-macro-chip.is-on')].map((el) => el.dataset.macro)
  );
  dlg.querySelectorAll('.hm-type-chip').forEach((chip) => {
    const macro = chip.dataset.macro;
    const on = onMacros.has(macro);
    chip.classList.toggle('is-on', on);
    const cb = chip.querySelector('input'); if (cb) cb.checked = on;
  });
  updateFoldCount(dlg, 'type');
}

/** 选极性 → 自动选大类（传导：积极=喜+乐 / 消极=怒+哀+愁 / 中性=急+盼 / 综合=全选） */
function applyPolarityToMacros(dlg, polarity) {
  const target =
    polarity === 'P' ? new Set(['喜', '乐'])
    : polarity === 'N' ? new Set(['怒', '哀', '愁'])
    : polarity === 'O' ? new Set(['急', '盼'])
    : new Set(EMOTION_MACRO_ORDER);   // ALL
  dlg.querySelectorAll('.hm-macro-chip').forEach((chip) => {
    const on = target.has(chip.dataset.macro);
    chip.classList.toggle('is-on', on);
    const cb = chip.querySelector('input'); if (cb) cb.checked = on;
  });
  updateFoldCount(dlg, 'macro');
  applyMacroToTypes(dlg);
}

/** 更新折叠区计数 */
function updateFoldCount(dlg, kind) {
  if (kind === 'macro') {
    const all = dlg.querySelectorAll('.hm-macro-chip').length;
    const on = dlg.querySelectorAll('.hm-macro-chip.is-on').length;
    const cnt = dlg.querySelector('#hm-macro-cnt');
    if (cnt) cnt.textContent = on === all ? '全选' : `${on}/${all}`;
  } else {
    const all = dlg.querySelectorAll('.hm-type-chip').length;
    const on = dlg.querySelectorAll('.hm-type-chip.is-on').length;
    const cnt = dlg.querySelector('#hm-type-cnt');
    if (cnt) cnt.textContent = on === all ? '全选' : `${on}/${all}`;
  }
}

/** 当前可用的数据层级 */
function availableLevels(sources) {
  const order = ['L1', 'L2', 'L3', 'L4'];
  const present = new Set(sources.map((s) => s.level).filter(Boolean));
  return order.filter((lv) => present.has(lv));
}

/** 根据 level + polarity（ALL/P/N/O）解析出 {fc, sourceKey, label} */
function resolveSource(sources, level, polarity) {
  const src = sources.find((s) => s.level === level);
  if (!src) return null;
  if (level === 'L2') {
    const pol = polarity || 'ALL';
    if (pol === 'P') {
      const child = src.childByPolarity && src.childByPolarity['l2-positive'];
      if (child && child.fc) return { fc: child.fc, sourceKey: `${src.sourceKey}#P`, label: `${src.label} · 积极` };
    } else if (pol === 'N') {
      const child = src.childByPolarity && src.childByPolarity['l2-negative'];
      if (child && child.fc) return { fc: child.fc, sourceKey: `${src.sourceKey}#N`, label: `${src.label} · 消极` };
    } else if (pol === 'O') {
      const child = src.childByPolarity && src.childByPolarity['l2-neutral'];
      if (child && child.fc) return { fc: child.fc, sourceKey: `${src.sourceKey}#O`, label: `${src.label} · 中性` };
    }
    return { fc: src.fc, sourceKey: `${src.sourceKey}#ALL`, label: `${src.label} · 综合` };
  }
  return { fc: src.fc, sourceKey: src.sourceKey, label: src.label };
}

/** 按 analysis + level 约束"特性"下拉（原极性）：
 *   - terrain（总体）：始终综合，不可选
 *   - grid（总体）：L1 综合（不可选）；L2 综合/积极/消极/中性 4 选
 *   - positive/negative/neutral（细分）：锁定 积极/消极/中性
 *   - attribution：综合，不可选
 *   - 非 L2：仅综合 */
function constrainPolarityOptions(dlg, level, analysis) {
  const sel = dlg.querySelector('#hm-subset');
  if (!sel) return;
  const opts = sel.querySelectorAll('option');
  const tier = ANALYSIS_PRESETS[analysis]?.tier || 'overall';
  const allOff = (val) => { opts.forEach((o) => { const ok = o.value === val; o.disabled = !ok; o.hidden = !ok; }); };
  const allOn = () => { opts.forEach((o) => { o.disabled = false; o.hidden = false; }); };

  let locked = null;   // 锁定值（不可切换）
  if (analysis === 'positive') locked = 'P';
  else if (analysis === 'negative') locked = 'N';
  else if (analysis === 'neutral') locked = 'O';
  else if (tier === 'overall' || tier === 'attribution') {
    // 总体/归因：grid+L2 可 4 选，其余综合不可选
    if (analysis === 'grid' && level === 'L2') { allOn(); sel.disabled = false; if (!['ALL', 'P', 'N', 'O'].includes(sel.value)) sel.value = 'ALL'; return; }
    locked = 'ALL';
  }

  if (locked) {
    allOff(locked);
    sel.value = locked;
    sel.disabled = true;   // 锁死（值固定，不可切换）
    return;
  }
  // 类型细分但未命中 locked（理论上不出现）：非 L2 仅综合
  if (level !== 'L2') { allOff('ALL'); sel.value = 'ALL'; sel.disabled = false; return; }
  allOn();
  sel.disabled = false;
}

/** 按当前 ① 约束数据下拉。
 *  v4：始终列 L1/L2/L3/L4 四项；无数据 → disabled 灰显（结构始终可见，避免用户误以为某层级"消失了"）。
 *  分析类型为积极/消极/归类时，非 L2 项强制 disabled（这些分析只属 L2 字段）。 */
function constrainLevelOptions(dlg, sources, analysis) {
  const sel = dlg.querySelector('#hm-level');
  if (!sel) return;
  const present = new Set(sources.map((s) => s.level));
  const onlyL2 = analysis === 'positive' || analysis === 'negative' || analysis === 'classify';
  const FIXED = ['L1', 'L2', 'L3', 'L4'];
  const cur = sel.value;
  let firstAvailable = null;
  sel.innerHTML = FIXED.map((lv) => {
    const has = present.has(lv);
    const ok = has && (!onlyL2 || lv === 'L2');
    if (ok && !firstAvailable) firstAvailable = lv;
    const tag = !has ? '（无数据）' : (!ok ? '（仅 L2 适用）' : '');
    return `<option value="${lv}" ${ok ? '' : 'disabled'}>${lv}${tag}</option>`;
  }).join('');
  // 选中：L1 优先（有数据且未被 onlyL2 排除时默认选 L1），否则取第一个可用项
  const target = firstAvailable || 'L2';
  sel.value = target;
}

/** 打开核密度分析（KDE）弹窗。
 *  v5：layerId 可选 — 当从 H 要素按钮点击进来时传入该热力图层 id，
 *      弹窗的所有参数会从 layer.paint._ui + layer.paint 反推恢复（"以当初参数继续编辑"语义），
 *      而不是回到默认值。 */
export function openHeatmapDialog(layerId) {
  const dlg = dialogEl();
  if (!dlg) return;
  if (dlg.open) dlg.close();

  const sources = collectSources();
  if (!sources.length) { toast.error('请先导入 L2 情绪数据'); return; }

  // 反推种子（编辑模式）：从已有热力图层的 paint 抓 _ui + 参数
  let seed = null;
  if (layerId) {
    const lyr = getLayer(layerId);
    if (lyr && lyr.kind === 'heatmap' && lyr.paint) {
      seed = { ...(lyr.paint._ui || {}), paint: lyr.paint, layerId };
    }
  }
  const initAnalysis = (seed && seed.analysisKey) || DEFAULT_ANALYSIS;

  // ① 分析类型卡（套种子选中态）
  renderAnalysisCards(dlg);
  if (seed && seed.analysisKey) {
    dlg.querySelectorAll('.hm-analysis-card').forEach((c) => c.classList.toggle('is-opt-sel', c.dataset.analysis === seed.analysisKey));
  }

  // ② 数据下拉（按 ① 约束 + 套种子值）
  constrainLevelOptions(dlg, sources, initAnalysis);
  if (seed && seed.level) dlg.querySelector('#hm-level').value = seed.level;
  const defaultLevel = dlg.querySelector('#hm-level').value;

  // ② 极性下拉（按 ① 约束 + 套种子值）
  constrainPolarityOptions(dlg, defaultLevel, initAnalysis);
  const initPolarity = (seed && seed.polarity) || 'ALL';
  dlg.querySelector('#hm-subset').value = initPolarity;

  // ② 大类 + 小类胶囊（L1/L3/L4 渲染禁用提示）
  renderMacroChips(dlg, defaultLevel);
  applyPolarityToMacros(dlg, initPolarity);
  const resolved0 = resolveSource(sources, defaultLevel, initPolarity);
  renderTypeChips(dlg, resolved0 ? resolved0.fc : { features: [] }, defaultLevel);
  // 编辑模式：按种子的 typesFilter 还原小类勾选；否则按大类传导
  if (seed && Array.isArray(seed.paint.typesFilter)) {
    const want = new Set(seed.paint.typesFilter);
    dlg.querySelectorAll('.hm-type-chip').forEach((chip) => {
      const on = want.has(chip.dataset.type);
      chip.classList.toggle('is-on', on);
      const cb = chip.querySelector('input'); if (cb) cb.checked = on;
    });
    updateFoldCount(dlg, 'type');
  } else {
    applyMacroToTypes(dlg);
  }

  // 折叠区默认展开（v3：类型 + 表现 默认打开）
  const macroFold = dlg.querySelector('#hm-macro-fold');
  const typeFold = dlg.querySelector('#hm-type-fold');
  if (macroFold) macroFold.open = true;
  if (typeFold) typeFold.open = true;

  // ③ 只读色板预览 + 生成按钮（编辑模式：色板由 analysis+level+特性自动，无需选种）
  renderStylePreview(dlg);

  // 高级参数（编辑模式：从 seed.paint 恢复；否则走默认值）
  const sp = (seed && seed.paint) || {};
  const nPts = resolved0 && resolved0.fc ? resolved0.fc.features.length : 0;
  const autoRadius = sp.radius ?? (nPts < 1000 ? 500 : nPts < 10000 ? 300 : 150);
  const radiusInput = dlg.querySelector('#hm-radius');
  const radiusVal = dlg.querySelector('#hm-radius-val');
  if (radiusInput) { radiusInput.value = autoRadius; radiusInput.min = 50; radiusInput.max = 2000; radiusInput.step = 10; }
  if (radiusVal) radiusVal.textContent = `${autoRadius} m`;
  dlg.dataset.unit = 'm';

  dlg.querySelector('#hm-opacity').value = sp.opacity ?? DEFAULTS.opacity;
  dlg.querySelector('#hm-opacity-val').textContent = `${Math.round((sp.opacity ?? DEFAULTS.opacity) * 100)}%`;
  dlg.querySelector('#hm-weight-field').value = sp.weightField ?? DEFAULTS.weightField;
  dlg.querySelector('#hm-intensity').value = sp.intensity ?? DEFAULTS.intensity;
  dlg.querySelector('#hm-intensity-val').textContent = (sp.intensity ?? DEFAULTS.intensity).toFixed(1);
  dlg.querySelector('#hm-curve').value = sp.weightCurve ?? DEFAULTS.curve;
  updateCurveHint(dlg);
  dlg.querySelector('#hm-int-min').value = sp.intensityMin ?? DEFAULTS.intensityMin;
  dlg.querySelector('#hm-int-min-val').textContent = (sp.intensityMin ?? DEFAULTS.intensityMin).toFixed(2);
  const mz = sp.minzoom ?? DEFAULTS.minzoom;
  dlg.querySelector('#hm-minzoom').value = mz;
  dlg.querySelector('#hm-minzoom-val').textContent = String(mz);
  const xz = sp.maxzoom ?? DEFAULTS.maxzoom;
  dlg.querySelector('#hm-maxzoom').value = xz;
  dlg.querySelector('#hm-maxzoom-val').textContent = String(xz);

  const adv = dlg.querySelector('#hm-advanced');
  if (adv && adv.tagName === 'DETAILS') adv.open = false;

  // 记住正在编辑的图层 id（覆盖模式会删旧+添新，届时替换）
  dlg.dataset.editLayerId = layerId || '';

  dlg.showModal();
}

function updateCurveHint(dlg) {
  const hints = {
    'linear': '当前：值越高 → 权重越高 → 颜色越热（推荐配 emotion_intensity）',
    'linear-inverse': '当前：值越低 → 权重越高 → 颜色越热（配 score 看消极）',
    'exponential': '当前：值越高 → 权重急剧升高 → 热点更集中',
    'exponential-inverse': '当前：值越低 → 权重急剧升高 → 热点更集中',
  };
  const v = dlg.querySelector('#hm-curve').value;
  const el = dlg.querySelector('#hm-curve-hint');
  if (el) el.textContent = hints[v] || '';
}

function closeDialog() {
  hideInfoPanel();
  const dlg = dialogEl();
  if (dlg) dlg.close();
}

/** 按选中小类 + 强度阈值过滤 features。
 *  v5：selectedTypes 语义见 getSelectedTypes。
 *    - null：跳过 type 过滤（L1 无字段）
 *    - 数组：按数组过滤（空数组 = 一个都不留，generateHeatmap 提前拦截） */
function filterFc(fc, selectedTypes, intensityMin) {
  if (!fc || !fc.features) return { type: 'FeatureCollection', features: [] };
  const needTypeFilter = Array.isArray(selectedTypes);
  const needIntensityFilter = intensityMin > 0;
  if (!needTypeFilter && !needIntensityFilter) return fc;
  const set = needTypeFilter ? new Set(selectedTypes) : null;
  const features = fc.features.filter((f) => {
    const p = f.properties || {};
    if (needTypeFilter && !set.has(emotionTypeOf(f))) return false;
    if (needIntensityFilter && Number(p.emotion_intensity ?? 0) < intensityMin) return false;
    return true;
  });
  return { type: 'FeatureCollection', features };
}

/** 收集当前选中的小类。
 *  v5：返回值语义
 *    - null = 无小类胶囊（L1/L3/L4 没有 emotion_type 字段，不参与过滤）
 *    - []   = 用户全部取消（明确"一个都不要"，generateHeatmap 拦截）
 *    - 其他 = 选中的小类数组（filterFc 按数组过滤） */
function getSelectedTypes(dlg) {
  const all = [...dlg.querySelectorAll('.hm-type-chip')];
  if (!all.length) return null;
  return all.filter((el) => el.querySelector('input').checked).map((el) => el.dataset.type);
}

/** 生成热力图 —— 由生成按钮（#hm-generate-row 内）触发，按钮自带 dim/ramp/dev。
 *  v6：色板随 analysis+level+特性自动（computeStyle），不再从 ③手选 style-btn 读。 */
function generateHeatmap(btn) {
  const dlg = dialogEl();
  if (!dlg) return;

  const analysisKey = selectedAnalysis(dlg);
  const preset = ANALYSIS_PRESETS[analysisKey];
  const dim = btn ? btn.dataset.dim : '2d';
  const rampKey = btn ? btn.dataset.ramp : '';
  const isDev = btn ? btn.classList.contains('is-dev') : true;

  // 占位拦截：dev 按钮（3D / 网格聚合）/ 占位分析类型
  if (isDev || dim === '3d') { toast.info('该表达（3D / 网格聚合）待后续批次开发，UI 已就位'); return; }
  if (preset && preset.placeholder) { toast.info(`${preset.label} 待后续批次`); return; }

  const level = dlg.querySelector('#hm-level').value;
  const polarity = dlg.querySelector('#hm-subset').value;
  const radius = Number(dlg.querySelector('#hm-radius').value);
  const opacity = Number(dlg.querySelector('#hm-opacity').value) / 100;
  const weightField = dlg.querySelector('#hm-weight-field').value;
  const intensity = Number(dlg.querySelector('#hm-intensity').value);
  const weightCurve = dlg.querySelector('#hm-curve').value;
  const intensityMin = Number(dlg.querySelector('#hm-int-min').value);
  const minzoom = Number(dlg.querySelector('#hm-minzoom').value);
  const maxzoom = Number(dlg.querySelector('#hm-maxzoom').value);
  const selectedTypes = getSelectedTypes(dlg);

  const sources = collectSources();
  const resolved = resolveSource(sources, level, level === 'L2' ? polarity : null);
  if (!resolved) { toast.error('请选择有效数据'); return; }
  const sourceKey = resolved.sourceKey;

  // v5：null = L1/L3/L4 无类型字段，跳过此项校验；空数组 = 用户取消所有小类，明确拦截。
  if (Array.isArray(selectedTypes) && selectedTypes.length === 0) {
    toast.error('未选中任何"表现"小类，请至少勾选一项（或在"类型"中选大类自动传导）');
    return;
  }

  const beforeN = (resolved.fc && resolved.fc.features ? resolved.fc.features.length : 0);
  const fc = filterFc(resolved.fc, selectedTypes, intensityMin);
  // 调试日志：让用户在 DevTools 看到实际过滤效果（小类→落图）
  // eslint-disable-next-line no-console
  console.info('[HeatMap] filter', {
    level, polarity, intensityMin,
    selectedTypes, typeCount: selectedTypes ? selectedTypes.length : 'N/A (no field)',
    beforeN, afterN: fc.features.length,
  });
  if (!fc.features.length) {
    toast.error(`筛选后无数据点（源 ${beforeN} 点 → 0）。请放宽小类勾选或强度阈值。`);
    return;
  }

  const oldId = getHeatmapForSource(sourceKey);
  if (oldId) { removeLayerFromMap(oldId); removeLayer(oldId); removeHeatmapSource(sourceKey); }

  const ramp = HEATMAP_RAMPS[rampKey];
  const rampName = ramp ? ramp.name : '自定义';
  // 类型标签：null（L1 无字段）→ [全数据]；全选 → [全类型]；否则列出选中小类
  const allTypes = [...dlg.querySelectorAll('.hm-type-chip')].map((el) => el.dataset.type);
  let typeLabel;
  if (selectedTypes === null) typeLabel = '[全数据]';
  else if (selectedTypes.length === allTypes.length && allTypes.length > 0) typeLabel = '[全类型]';
  else typeLabel = `[${selectedTypes.join('/')}]`;
  const radiusLabel = `${radius}m`;

  const layer = addLayer({
    name: `HeatMap · ${rampName} ${typeLabel} ${radiusLabel}`,
    kind: 'heatmap',
    colorMode: 'heatmap-negative',
    fc,
    paint: {
      unit: 'm', radius, opacity, intensity, weightField, weightCurve, rampKey,
      typesFilter: selectedTypes, intensityMin,
      minzoom: minzoom > 0 ? minzoom : undefined,
      maxzoom: maxzoom < 22 ? maxzoom : undefined,
      // v5/v6：持久化 UI 原始选择，供 H 要素按钮再次打开时反推参数（"继续编辑"语义）
      _ui: {
        analysisKey, dim,
        level, polarity, rampKey,
        macroFilter: [...dlg.querySelectorAll('.hm-macro-chip.is-on')].map((el) => el.dataset.macro),
      },
    },
  });
  setHeatmapForSource(sourceKey, layer.id);
  renderLayer(layer);

  // bug⑤ fix：不再"独占隐藏其他图层"——旧策略会把已存在的 L1 彩虹等热力图隐藏，
  // 且开关眼睛表象"无效"（实为被新层遮挡/状态混乱）。同 sourceKey 的旧热力图已在上方
  // removeLayer 覆盖；不同源的图层保持共存，交由图层管理（眼睛/分组）控制显隐。
  selectLayer(layer.id);
  document.dispatchEvent(new CustomEvent('layers:changed'));
  document.dispatchEvent(new CustomEvent('layer:selected', { detail: layer.id }));
  toast.success(`已生成热力图：${rampName} · ${radiusLabel} · ${fc.features.length} 点`);

  closeDialog();
}

/** 初始化弹窗事件（仅一次） */
export function initHeatmapTool() {
  const dlg = dialogEl();
  if (!dlg) return;

  // 关闭
  dlg.querySelectorAll('[data-close]').forEach((btn) => btn.addEventListener('click', closeDialog));
  dlg.addEventListener('click', (e) => { if (e.target === dlg) closeDialog(); });

  // ① 分析类型卡：选卡 + 套约束 + 重算 ②③
  dlg.querySelector('#hm-analysis')?.addEventListener('click', (e) => {
    const card = e.target.closest('.hm-analysis-card');
    if (!card) return;
    e.stopPropagation();
    const key = card.dataset.analysis;
    dlg.querySelectorAll('.hm-analysis-card').forEach((c) => c.classList.remove('is-opt-sel'));
    card.classList.add('is-opt-sel');
    const sources = collectSources();
    constrainLevelOptions(dlg, sources, key);
    const lv = dlg.querySelector('#hm-level').value;
    constrainPolarityOptions(dlg, lv, key);
    const polNow = dlg.querySelector('#hm-subset').value;
    const resolved = resolveSource(sources, lv, polNow);
    renderMacroChips(dlg, lv);
    // 传导：极性 → 大类 → 小类（对所有分析类型生效，renderMacroChips 之后执行以免被清空）
    applyPolarityToMacros(dlg, polNow);
    renderTypeChips(dlg, resolved ? resolved.fc : { features: [] }, lv);
    applyMacroToTypes(dlg);
    renderStylePreview(dlg);
  });

  // analysis-card 上的 i：hover 弹 infopanel
  dlg.querySelector('#hm-analysis')?.addEventListener('mouseover', (e) => {
    const i = e.target.closest('.hm-info-card');
    if (!i) return;
    const card = i.closest('.hm-analysis-card');
    showInfoPanel(card, i.dataset.analysisKey);
  });
  dlg.querySelector('#hm-analysis')?.addEventListener('mouseout', (e) => {
    if (e.target.closest('.hm-info-card')) hideInfoPanel();
  });

  // ② 数据下拉切换 → 重算特性约束 + 小类 + ③
  dlg.querySelector('#hm-level')?.addEventListener('change', (e) => {
    const lv = e.target.value;
    const an = selectedAnalysis(dlg);
    constrainPolarityOptions(dlg, lv, an);
    const sources = collectSources();
    const polNow = dlg.querySelector('#hm-subset').value;
    const resolved = resolveSource(sources, lv, polNow);
    renderMacroChips(dlg, lv);
    // 传导：极性 → 大类 → 小类（对所有分析类型生效，renderMacroChips 之后执行以免被清空）
    applyPolarityToMacros(dlg, polNow);
    renderTypeChips(dlg, resolved ? resolved.fc : { features: [] }, lv);
    applyMacroToTypes(dlg);
    renderStylePreview(dlg);
  });

  // ② 极性下拉切换 → 传导大类 → 传导小类 → 重算 ③
  dlg.querySelector('#hm-subset')?.addEventListener('change', (e) => {
    const lv = dlg.querySelector('#hm-level').value;
    const polarity = e.target.value;
    applyPolarityToMacros(dlg, polarity);
    const sources = collectSources();
    const resolved = resolveSource(sources, lv, polarity);
    renderTypeChips(dlg, resolved ? resolved.fc : { features: [] }, lv);
    applyMacroToTypes(dlg);
    renderStylePreview(dlg);
  });

  // ② 大类胶囊点击 toggle + 传导小类 + 更新计数
  dlg.querySelector('#hm-macros')?.addEventListener('click', (e) => {
    const chip = e.target.closest('.hm-macro-chip');
    if (!chip) return;
    const cb = chip.querySelector('input');
    requestAnimationFrame(() => {
      chip.classList.toggle('is-on', cb.checked);
      updateFoldCount(dlg, 'macro');
      applyMacroToTypes(dlg);
    });
  });

  // ② 小类胶囊点击 toggle + 更新计数
  dlg.querySelector('#hm-types')?.addEventListener('click', (e) => {
    const chip = e.target.closest('.hm-type-chip');
    if (!chip) return;
    const cb = chip.querySelector('input');
    requestAnimationFrame(() => {
      chip.classList.toggle('is-on', cb.checked);
      updateFoldCount(dlg, 'type');
    });
  });

  // ③ 只读色板预览，不可点选（色板随 analysis+level+特性自动）。
  // 生成按钮（#hm-generate-row）委托：点击 → generateHeatmap(该按钮)
  dlg.querySelector('#hm-generate-row')?.addEventListener('click', (e) => {
    const btn = e.target.closest('.sec-btn[data-dim]');
    if (!btn || btn.disabled) return;
    generateHeatmap(btn);
  });

  // 高级参数实时显示
  dlg.querySelector('#hm-radius')?.addEventListener('input', (e) => {
    dlg.querySelector('#hm-radius-val').textContent = e.target.value + ' m';
  });
  dlg.querySelector('#hm-opacity')?.addEventListener('input', (e) => {
    dlg.querySelector('#hm-opacity-val').textContent = e.target.value + '%';
  });
  dlg.querySelector('#hm-intensity')?.addEventListener('input', (e) => {
    dlg.querySelector('#hm-intensity-val').textContent = Number(e.target.value).toFixed(1);
  });
  dlg.querySelector('#hm-int-min')?.addEventListener('input', (e) => {
    dlg.querySelector('#hm-int-min-val').textContent = Number(e.target.value).toFixed(2);
  });
  dlg.querySelector('#hm-curve')?.addEventListener('change', () => updateCurveHint(dlg));
  dlg.querySelector('#hm-minzoom')?.addEventListener('input', (e) => {
    dlg.querySelector('#hm-minzoom-val').textContent = e.target.value;
  });
  dlg.querySelector('#hm-maxzoom')?.addEventListener('input', (e) => {
    dlg.querySelector('#hm-maxzoom-val').textContent = e.target.value;
  });

  // 生成按钮由 #hm-generate-row 委托（上方已绑），这里不再绑 #hm-generate。

  // 通用 i tooltip（覆盖 .hm-info[data-tip] 与原 .hm-info > .hm-tip 两种写法）
  initInfoTooltip();
}

let _infoTipInit = false;
function initInfoTooltip() {
  if (_infoTipInit) return;
  _infoTipInit = true;
  const tip = document.createElement('div');
  tip.className = 'hm-tooltip';
  tip.id = 'hm-tooltip';
  const dlg = document.getElementById(DIALOG_ID);
  (dlg || document.body).appendChild(tip);

  const show = (info) => {
    if (info.classList.contains('hm-info-card')) return;   // analysis-card 走 infopanel，不走小 tooltip
    const text = info.dataset.tip
      || info.querySelector?.('.hm-tip')?.textContent
      || '';
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
    // 触发源：.hm-info（i 图标）或 .hm-macro-chip[data-tip]（大类胶囊整体悬停）
    const info = e.target.closest('.hm-info, .hm-macro-chip[data-tip]');
    if (info) show(info);
  });
  document.addEventListener('mouseout', (e) => {
    if (e.target.closest('.hm-info, .hm-macro-chip[data-tip]')) hide();
  });
}
