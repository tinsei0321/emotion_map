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

// ── ① 分析类型预设（6 卡，2 列）；preview = 预览图（assets/analysis-previews/*.svg）──
const DEFAULT_ANALYSIS = 'terrain';
const ANALYSIS_PRESETS = {
  terrain: {
    label: '情绪地形（2D/3D）',
    desc: '一图看城市情绪起伏。L1 = 综合舆情热度（彩虹 2D）；L2 综合 = 红绿渐变（积极凸/消极凹，3D 待开发）。',
    preview: 'assets/analysis-previews/terrain.svg',
  },
  grid: {
    label: '情绪网格（2D/3D）',
    desc: '小尺度网格聚合（街区/社区）。每格 = 范围内点数或平均强度。2D 色块 / 3D 网格柱体。',
    preview: 'assets/analysis-previews/grid.svg',
  },
  positive: {
    label: '积极情绪',
    desc: '只看积极点的密度（仅 L2）。色板：积极绿。识别市民满意/标杆区域。',
    preview: 'assets/analysis-previews/positive.svg',
  },
  negative: {
    label: '消极情绪',
    desc: '只看消极点的密度（仅 L2）。色板：消极红。定位整改优先级与问题片区。',
    preview: 'assets/analysis-previews/negative.svg',
  },
  classify: {
    label: '情绪归类',
    desc: '按 7 大类（喜怒哀乐愁急盼）分别成色，分类热力图（仅 L2）。',
    preview: 'assets/analysis-previews/classify.svg',
  },
  factor: {
    label: '情绪因子',
    desc: '4 应用领域 × 5 因子要素 = 20 个归因视角，看"消极是因为什么"。待后续批次。',
    preview: 'assets/analysis-previews/factor.svg',
    placeholder: true,
  },
};

// ── ③ 显示样式（按 ①+②+level 联动出可选项）──
// 返回 [{ key, name, dim, ramp, dev, tip }]，name = 显示标签，dim = '2d'|'3d'，ramp = HEATMAP_RAMPS key，
// tip = 该样式的 i 悬停说明（含 2D/3D 差异等额外信息）。
function computeStyles(analysis, level, polarity) {
  if (analysis === 'terrain') {
    if (level === 'L1') {
      return [{ key: 'terrain-l1-rainbow', name: '综合彩虹（城市舆情热度，2D）', dim: '2d', ramp: 'rainbow',
        tip: 'L1 综合舆情热度。冷蓝 → 黄 → 暖红，体现密度与关注度，不暗示极性。' }];
    }
    if (level === 'L2' && polarity === 'ALL') {
      return [{ key: 'terrain-l2-rg-3d', name: '红蓝绿地形（3D 高程：积极凸/消极凹）', dim: '3d', ramp: 'diverging-rg', dev: true,
        tip: '3D 综合情绪地形。高地（积极绿凸）/ 洼地（消极红凹），中线蓝为零值。3D 渲染待开发。' }];
    }
    if (level === 'L2' && polarity === 'O') {
      return [{ key: 'terrain-l2-neutral', name: '中性蓝（急/盼）', dim: '2d', ramp: 'neutral',
        tip: '只看中性点。蓝色系色板，与"急（蓝）+ 盼（深蓝）"胶囊色系呼应。' }];
    }
    if (level === 'L2' && polarity === 'P') {
      return [{ key: 'terrain-l2-positive', name: '积极绿', dim: '2d', ramp: 'positive',
        tip: '只看积极点。绿色越深 = 满意度越集中。' }];
    }
    if (level === 'L2' && polarity === 'N') {
      return [{ key: 'terrain-l2-negative', name: '消极红', dim: '2d', ramp: 'negative',
        tip: '只看消极点。红色越深 = 抱怨/焦虑越集中。' }];
    }
    return [{ key: 'terrain-rainbow', name: '综合彩虹', dim: '2d', ramp: 'rainbow', tip: '综合彩虹色板。' }];
  }
  if (analysis === 'grid') {
    return [{ key: 'grid-warm', name: '热力网格（暖色暗红→金黄）', dim: '2d', ramp: 'grid-warm',
      tip: '小尺度网格聚合（街区/社区），每格 = 范围内点数或平均强度。2D = 色块网格；3D = 同色板的网格柱体（柱高表达密度），3D 待开发。' }];
  }
  if (analysis === 'positive') {
    return [{ key: 'positive-l2-green', name: '积极绿', dim: '2d', ramp: 'positive', tip: '只看积极点的密度（仅 L2）。' }];
  }
  if (analysis === 'negative') {
    return [{ key: 'negative-l2-red', name: '消极红', dim: '2d', ramp: 'negative', tip: '只看消极点的密度（仅 L2）。' }];
  }
  if (analysis === 'classify') {
    return [{ key: 'classify-7', name: '7 类分色（喜怒哀乐愁急盼）', dim: '2d', ramp: 'classify-7',
      tip: '按 7 大类（喜怒哀乐愁急盼）分别成色（仅 L2）。色板顺序：黄绿/橙黄/红/紫/蓝紫/蓝/深蓝。' }];
  }
  if (analysis === 'factor') {
    return [{ key: 'factor-tbd', name: '归因矩阵（开发中）', dim: '2d', ramp: 'rainbow', dev: true,
      tip: '4 应用领域 × 5 因子要素 = 20 个归因视角。待后续批次。' }];
  }
  return [];
}

// ── infopanel：analysis-card hover 弹出"图+文"看板（圆角正方形，dialog 右侧 +8px、上端对齐）──
let _infoPanelEl = null;
function ensureInfoPanel() {
  if (_infoPanelEl) return _infoPanelEl;
  const dlg = document.getElementById(DIALOG_ID);
  const el = document.createElement('div');
  el.className = 'hm-infopanel';
  el.id = 'hm-infopanel';
  el.innerHTML = `
    <div class="hm-infopanel-img"><img alt="" id="hm-infopanel-img"></div>
    <div class="hm-infopanel-text" id="hm-infopanel-text"></div>`;
  (dlg || document.body).appendChild(el);
  _infoPanelEl = el;
  return el;
}
function showInfoPanel(card, key) {
  const p = ANALYSIS_PRESETS[key];
  if (!p) return;
  const el = ensureInfoPanel();
  const img = el.querySelector('#hm-infopanel-img');
  const txt = el.querySelector('#hm-infopanel-text');
  img.src = p.preview || '';
  img.onerror = () => { img.style.visibility = 'hidden'; };
  img.onload = () => { img.style.visibility = 'visible'; };
  txt.textContent = p.desc || p.label;
  // 定位：弹窗右侧 +8px，上端对齐（用 dialog 的 rect 而非 card 的 rect，保证锚定一致）
  const dlg = document.getElementById(DIALOG_ID);
  const r = dlg.getBoundingClientRect();
  el.classList.add('is-show');
  // 显示后再测尺寸
  const ew = el.offsetWidth;
  let left = r.right + 8;
  let top = r.top;
  // 右侧不够则换到左侧
  if (left + ew > window.innerWidth - 8) left = Math.max(8, r.left - ew - 8);
  el.style.left = left + 'px';
  el.style.top = top + 'px';
}
function hideInfoPanel() { if (_infoPanelEl) _infoPanelEl.classList.remove('is-show'); }

/** 渲染 ① 分析类型卡（2 列） */
function renderAnalysisCards(dlg) {
  const wrap = dlg.querySelector('#hm-analysis');
  if (!wrap) return;
  wrap.innerHTML = Object.entries(ANALYSIS_PRESETS).map(([key, p]) =>
    `<button class="hm-analysis-card${key === DEFAULT_ANALYSIS ? ' is-opt-sel' : ''}${p.placeholder ? ' is-placeholder' : ''}" data-analysis="${key}" type="button">
      <span class="hm-ac-name">${p.label}</span>
      <span class="hm-info hm-info-card" data-analysis-key="${key}">i</span>
    </button>`).join('');
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

/** 渲染大类胶囊（7 类固定；每个胶囊带 data-tip 供 hover popup 使用） */
function renderMacroChips(dlg) {
  const wrap = dlg.querySelector('#hm-macros');
  if (!wrap) return;
  wrap.innerHTML = EMOTION_MACRO_ORDER.map((k) => {
    const m = EMOTION_MACRO[k];
    const tip = `${k} · ${m.desc}`.replace(/"/g, '&quot;');
    return `<label class="hm-macro-chip" data-macro="${k}" data-polarity="${m.polarity}" data-tip="${tip}" style="--chip-color:${m.color}">
      <input type="checkbox" />
      <span class="hm-macro-name">${k}</span>
    </label>`;
  }).join('');
}

/** 渲染小类胶囊（按当前 fc 动态归纳） */
function renderTypeChips(dlg, fc) {
  const wrap = dlg.querySelector('#hm-types');
  if (!wrap) return;
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

/** 渲染 ③ 显示样式胶囊（按 ①+② 联动）—
 *  v3：色板预览改为"离散色块条"（kepler 风格，无渐变），去掉名称文字（仅保留 i 悬停说明）。
 *  v4：默认选第一个非 dev 项（避免开箱即点"生成"却被 dev 拦截，给人按钮失效感）；末尾刷新生成按钮态。 */
function renderStyles(dlg) {
  const wrap = dlg.querySelector('#hm-styles');
  if (!wrap) return;
  const analysis = dlg.querySelector('.hm-analysis-card.is-opt-sel')?.dataset?.analysis || DEFAULT_ANALYSIS;
  const level = dlg.querySelector('#hm-level').value;
  const polarity = dlg.querySelector('#hm-subset').value;
  const styles = computeStyles(analysis, level, polarity);
  if (!styles.length) {
    wrap.innerHTML = `<div class="hm-hint">当前 ①+② 组合无可用样式</div>`;
    refreshGenerateBtn(dlg);
    return;
  }
  // 默认选中：优先第一个非 dev 项；都是 dev 时退回第一项
  const defIdx = styles.findIndex((s) => !s.dev);
  const selIdx = defIdx >= 0 ? defIdx : 0;
  wrap.innerHTML = styles.map((s, i) => {
    const ramp = HEATMAP_RAMPS[s.ramp];
    // 离散色块：取所有非透明 stop 的颜色，平均切片，每格一个 div（kepler 分段条风格）
    const segs = ramp ? ramp.stops.filter(([d]) => d > 0).map(([, c]) => c) : ['#ccc'];
    const segHtml = segs.map((c) => `<span class="hm-style-seg" style="background:${c}"></span>`).join('');
    const tip = s.tip || (s.name + (s.dev ? '（开发中）' : ''));
    return `<button class="hm-style-btn${i === selIdx ? ' is-bar-sel' : ''}${s.dev ? ' is-dev' : ''}"
              data-style-key="${s.key}" data-dim="${s.dim}" data-ramp="${s.ramp}" type="button">
      <span class="hm-style-bar">${segHtml}</span>
      ${s.dev ? '<span class="hm-style-dev-tag">开发中</span>' : ''}
      <span class="hm-info" data-tip="${tip.replace(/"/g, '&quot;')}">i</span>
    </button>`;
  }).join('');
  refreshGenerateBtn(dlg);
}

/** 刷新"生成热力图"按钮的禁用态/文案：
 *  - 未选样式 → 禁用 + "请选择显示样式"
 *  - 选中样式是 dev → 禁用 + "该样式开发中，暂不可生成"
 *  - 否则 → 启用 + "生成热力图" */
function refreshGenerateBtn(dlg) {
  const gen = dlg.querySelector('#hm-generate');
  if (!gen) return;
  const styleBtn = dlg.querySelector('.hm-style-btn.is-bar-sel');
  if (!styleBtn) {
    gen.disabled = true; gen.textContent = '请选择显示样式'; return;
  }
  if (styleBtn.classList.contains('is-dev')) {
    gen.disabled = true; gen.textContent = '该样式开发中，暂不可生成'; return;
  }
  gen.disabled = false; gen.textContent = '生成热力图';
}

/** 选大类胶囊 → 自动选/取消其下小类（传导） */
function applyMacroToTypes(dlg) {
  const onMacros = new Set(
    [...dlg.querySelectorAll('.hm-macro-chip.is-on')].map((el) => el.dataset.macro)
  );
  // 大类全空：小类全选
  const macroAll = onMacros.size === 0;
  dlg.querySelectorAll('.hm-type-chip').forEach((chip) => {
    const macro = chip.dataset.macro;
    const on = macroAll ? true : onMacros.has(macro);
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

/** 按当前 ② 设置约束极性下拉的可选项（L1 = 仅"综合"；L2 = 4 项全开） */
function constrainPolarityOptions(dlg, level, lockReason) {
  const sel = dlg.querySelector('#hm-subset');
  if (!sel) return;
  const opts = sel.querySelectorAll('option');
  if (level === 'L2') {
    opts.forEach((o) => { o.disabled = false; o.hidden = false; });
    sel.disabled = false;
  } else {
    // 非 L2：仅"综合"可选
    opts.forEach((o) => { const ok = o.value === 'ALL'; o.disabled = !ok; o.hidden = !ok; });
    sel.value = 'ALL';
    sel.disabled = false;   // 还允许查看，但只能选综合
  }
  // 分析类型锁定（积极/消极 → 只能 L2 + 对应极性）
  if (lockReason === 'positive') { sel.value = 'P'; sel.disabled = true; }
  if (lockReason === 'negative') { sel.value = 'N'; sel.disabled = true; }
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
  // 选中：保持当前值（如果可用），否则选第一个可用项
  const target = (present.has(cur) && (!onlyL2 || cur === 'L2')) ? cur : (firstAvailable || 'L2');
  sel.value = target;
}

/** 打开热核分析弹窗 */
export function openHeatmapDialog() {
  const dlg = dialogEl();
  if (!dlg) return;
  if (dlg.open) dlg.close();

  const sources = collectSources();
  if (!sources.length) { toast.error('请先导入 L2 情绪数据'); return; }

  // ① 默认套综合"情绪地形"
  renderAnalysisCards(dlg);

  // ② 数据下拉（按 ① 约束）
  constrainLevelOptions(dlg, sources, DEFAULT_ANALYSIS);
  const defaultLevel = dlg.querySelector('#hm-level').value;

  // ② 极性下拉（按 ① 约束）
  constrainPolarityOptions(dlg, defaultLevel, null);
  dlg.querySelector('#hm-subset').value = 'ALL';

  // ② 大类 + 小类胶囊
  renderMacroChips(dlg);
  applyPolarityToMacros(dlg, 'ALL');
  const resolved0 = resolveSource(sources, defaultLevel, 'ALL');
  renderTypeChips(dlg, resolved0 ? resolved0.fc : { features: [] });
  applyMacroToTypes(dlg);

  // 折叠区默认展开（v3：类型 + 表现 默认打开）
  const macroFold = dlg.querySelector('#hm-macro-fold');
  const typeFold = dlg.querySelector('#hm-type-fold');
  if (macroFold) macroFold.open = true;
  if (typeFold) typeFold.open = true;

  // ③ 显示样式
  renderStyles(dlg);

  // 高级参数默认值
  const nPts = resolved0 && resolved0.fc ? resolved0.fc.features.length : 0;
  const autoRadius = nPts < 1000 ? 500 : nPts < 10000 ? 300 : 150;
  const radiusInput = dlg.querySelector('#hm-radius');
  const radiusVal = dlg.querySelector('#hm-radius-val');
  if (radiusInput) { radiusInput.value = autoRadius; radiusInput.min = 50; radiusInput.max = 2000; radiusInput.step = 10; }
  if (radiusVal) radiusVal.textContent = `${autoRadius} m`;
  dlg.dataset.unit = 'm';

  dlg.querySelector('#hm-opacity').value = DEFAULTS.opacity;
  dlg.querySelector('#hm-opacity-val').textContent = `${DEFAULTS.opacity}%`;
  dlg.querySelector('#hm-weight-field').value = DEFAULTS.weightField;
  dlg.querySelector('#hm-intensity').value = DEFAULTS.intensity;
  dlg.querySelector('#hm-intensity-val').textContent = DEFAULTS.intensity.toFixed(1);
  dlg.querySelector('#hm-curve').value = DEFAULTS.curve;
  updateCurveHint(dlg);
  dlg.querySelector('#hm-int-min').value = DEFAULTS.intensityMin;
  dlg.querySelector('#hm-int-min-val').textContent = DEFAULTS.intensityMin.toFixed(2);
  dlg.querySelector('#hm-minzoom').value = DEFAULTS.minzoom;
  dlg.querySelector('#hm-minzoom-val').textContent = String(DEFAULTS.minzoom);
  dlg.querySelector('#hm-maxzoom').value = DEFAULTS.maxzoom;
  dlg.querySelector('#hm-maxzoom-val').textContent = String(DEFAULTS.maxzoom);

  const adv = dlg.querySelector('#hm-advanced');
  if (adv && adv.tagName === 'DETAILS') adv.open = false;

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

/** 按选中小类 + 强度阈值过滤 features */
function filterFc(fc, selectedTypes, intensityMin) {
  if (!fc || !fc.features) return { type: 'FeatureCollection', features: [] };
  const needTypeFilter = Array.isArray(selectedTypes) && selectedTypes.length > 0;
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

/** 收集当前选中的小类（全选返回 null = 不过滤） */
function getSelectedTypes(dlg) {
  const all = [...dlg.querySelectorAll('.hm-type-chip')];
  if (!all.length) return null;
  const sel = all.filter((el) => el.querySelector('input').checked).map((el) => el.dataset.type);
  if (sel.length === all.length) return null;
  return sel;
}

/** 生成热力图 */
function generateHeatmap() {
  const dlg = dialogEl();
  if (!dlg) return;

  const analysisKey = dlg.querySelector('.hm-analysis-card.is-opt-sel')?.dataset?.analysis || DEFAULT_ANALYSIS;
  const styleBtn = dlg.querySelector('.hm-style-btn.is-bar-sel');
  if (!styleBtn) { toast.error('请选择显示样式'); return; }
  const dim = styleBtn.dataset.dim;
  const rampKey = styleBtn.dataset.ramp;
  const isDev = styleBtn.classList.contains('is-dev');

  if (isDev || dim === '3d') {
    toast.info(`样式"${styleBtn.querySelector('.hm-style-name').textContent}"待后续批次开发，UI 已就位`);
    return;
  }
  if (analysisKey === 'factor') { toast.info('情绪因子归因（4×5 矩阵）待后续批次'); return; }
  if (analysisKey === 'grid') { toast.info('情绪网格聚合渲染待后续批次（4 档格网）'); return; }

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

  const fc = filterFc(resolved.fc, selectedTypes, intensityMin);
  if (!fc.features.length) {
    toast.error('筛选后无数据点。请放宽情绪类型或强度阈值。');
    return;
  }

  const oldId = getHeatmapForSource(sourceKey);
  if (oldId) { removeLayerFromMap(oldId); removeLayer(oldId); removeHeatmapSource(sourceKey); }

  const ramp = HEATMAP_RAMPS[rampKey];
  const rampName = ramp ? ramp.name : '自定义';
  const typeLabel = selectedTypes ? `[${selectedTypes.join('/')}]` : '[全类型]';
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
    },
  });
  setHeatmapForSource(sourceKey, layer.id);
  renderLayer(layer);

  // 独占显示：隐藏其他图层
  for (const l of [...getLayers()]) {
    if (l.id === layer.id) continue;
    if (l.visible) { setLayerVisible(l.id, false); renderLayer(l); }
  }
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
    const lockReason = key === 'positive' ? 'positive' : key === 'negative' ? 'negative' : null;
    const lv = dlg.querySelector('#hm-level').value;
    constrainPolarityOptions(dlg, lv, lockReason);
    if (lockReason === 'positive') applyPolarityToMacros(dlg, 'P');
    else if (lockReason === 'negative') applyPolarityToMacros(dlg, 'N');
    const polNow = dlg.querySelector('#hm-subset').value;
    const resolved = resolveSource(sources, lv, polNow);
    renderTypeChips(dlg, resolved ? resolved.fc : { features: [] });
    applyMacroToTypes(dlg);
    renderStyles(dlg);
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

  // ② 数据下拉切换 → 重算极性约束 + 小类 + ③
  dlg.querySelector('#hm-level')?.addEventListener('change', (e) => {
    const lv = e.target.value;
    const an = dlg.querySelector('.hm-analysis-card.is-opt-sel')?.dataset?.analysis || DEFAULT_ANALYSIS;
    const lockReason = an === 'positive' ? 'positive' : an === 'negative' ? 'negative' : null;
    constrainPolarityOptions(dlg, lv, lockReason);
    const sources = collectSources();
    const polNow = dlg.querySelector('#hm-subset').value;
    const resolved = resolveSource(sources, lv, polNow);
    renderTypeChips(dlg, resolved ? resolved.fc : { features: [] });
    applyMacroToTypes(dlg);
    renderStyles(dlg);
  });

  // ② 极性下拉切换 → 传导大类 → 传导小类 → 重算 ③
  dlg.querySelector('#hm-subset')?.addEventListener('change', (e) => {
    const lv = dlg.querySelector('#hm-level').value;
    const polarity = e.target.value;
    applyPolarityToMacros(dlg, polarity);
    const sources = collectSources();
    const resolved = resolveSource(sources, lv, polarity);
    renderTypeChips(dlg, resolved ? resolved.fc : { features: [] });
    applyMacroToTypes(dlg);
    renderStyles(dlg);
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

  // ③ 显示样式胶囊点击 → 单选（"栏"语义：浅蓝填充无边框）
  dlg.querySelector('#hm-styles')?.addEventListener('click', (e) => {
    const btn = e.target.closest('.hm-style-btn');
    if (!btn) return;
    dlg.querySelectorAll('.hm-style-btn').forEach((b) => b.classList.remove('is-bar-sel'));
    btn.classList.add('is-bar-sel');
    refreshGenerateBtn(dlg);
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

  // 生成
  dlg.querySelector('#hm-generate')?.addEventListener('click', generateHeatmap);

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
