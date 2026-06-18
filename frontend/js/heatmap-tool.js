// ═══ heatmap-tool.js — HeatMap parameter dialog + generation + source overwrite ═══
// v2 (2026-06-18): 默认地理米 + 类型筛选 + 强度阈值 + 中立色带
import {
  getLayers, getChildren, addLayer, removeLayer, getLayer, setLayerVisible, selectLayer,
  HEATMAP_RAMPS, HEATMAP_RAMP_KEYS,
  EMOTION_TYPE_COLORS, EMOTION_TYPE_ORDER,
  getHeatmapForSource, setHeatmapForSource, removeHeatmapSource,
} from './state.js';
import { renderLayer, removeLayerFromMap } from './map.js';
import { toast } from './toast.js';

const DIALOG_ID = 'heatmap-dialog';

// 默认值（与 state.js heatmap paint defaults 对齐）
const DEFAULTS = {
  radiusM: 300,         // 地理米（半径固定地理米，无 px）
  opacity: 70,
  intensity: 1.0,
  weightField: 'emotion_intensity',
  curve: 'linear',
  rampKey: 'rainbow',
  intensityMin: 0,
  blurFactor: 1.0,
  minzoom: 0,
  maxzoom: 22,
};

function dialogEl() { return document.getElementById(DIALOG_ID); }

/** Collect available L2 data sources for the dropdown. */
function collectSources() {
  const sources = [];
  for (const l of getLayers()) {
    if (l.kind === 'group' && l.children && l.children.length) {
      // Bug 3 fix: L2 group 整体作为一个 source（不再把每个 child 各列一次）。
      // 合并所有 children 的 features；保留 group 引用 + 各极性 child 映射，供阶段 1 两层选择（P/N/PN/Neutral）。
      const childByPolarity = {};
      let merged = [];
      for (const cid of l.children) {
        const child = getLayer(cid);
        if (child && child.fc && child.fc.features.length) {
          childByPolarity[child.colorMode] = child;   // 'l2-positive'|'l2-neutral'|'l2-negative'
          merged = merged.concat(child.fc.features);
        }
      }
      if (merged.length) {
        sources.push({
          value: `group:${l.id}`,
          label: l.name,
          level: 'L2',
          fc: { type: 'FeatureCollection', features: merged },
          sourceKey: `group:${l.id}`,
          group: l,
          childByPolarity,
        });
      }
    } else if (l.kind === 'point' && l.fc && l.fc.features.length &&
               (l.colorMode === 'l2-positive' || l.colorMode === 'l2-negative' || l.colorMode === 'l2-neutral' ||
                l.colorMode === 'confidence')) {
      // 独立点图层（L1 confidence 或未归组的 L2 点）
      sources.push({
        value: `layer:${l.id}`,
        label: l.name,
        level: l.colorMode === 'confidence' ? 'L1' : 'L2',
        fc: l.fc,
        sourceKey: `layer:${l.id}`,
      });
    }
  }
  return sources;
}

/** 取 feature 的情绪类型。
 *  真实 emotion_type 优先（不限预定义集合——支持"按数据动态归纳"）；
 *  无 emotion_type 字段时用 polarity 派生兜底。 */
function emotionTypeOf(f) {
  const p = (f && f.properties) || {};
  const et = p.emotion_type;
  if (et) return et;
  const pol = p.polarity;
  if (pol === 'Very Positive' || pol === 'Positive') return '喜悦满意';
  if (pol === 'Very Negative') return '愤怒';
  if (pol === 'Negative') return '不满抱怨';
  return '期待建议';   // Neutral / 未知
}

/** 统计数据中实际出现的情绪类型 → 计数（动态归纳，不固定类型数量）。 */
function typeCountsFor(fc) {
  const counts = {};
  if (!fc || !fc.features) return counts;
  for (const f of fc.features) {
    const t = emotionTypeOf(f);
    counts[t] = (counts[t] || 0) + 1;
  }
  return counts;
}

/** 渲染情绪类型 chip（按数据动态归纳，不固定类型数量）。
 *  排序：预定义类型按既定顺序在前，未知类型按计数降序追加。 */
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
    const n = counts[t] || 0;
    return `<label class="hm-type-chip is-on" data-type="${t}" style="--chip-color:${c}">
      <input type="checkbox" checked />
      <span class="hm-type-dot"></span>
      <span class="hm-type-name">${t}</span>
      <span class="hm-type-count">${n}</span>
    </label>`;
  }).join('');
}

/** 收集类型筛选当前值（数组；全选返回 null = 不过滤） */
function getSelectedTypes(dlg) {
  const all = [...dlg.querySelectorAll('#hm-types .hm-type-chip')];
  if (!all.length) return null;
  const sel = all.filter((el) => el.querySelector('input').checked).map((el) => el.dataset.type);
  if (sel.length === all.length) return null;  // 全选 = 不过滤
  return sel;
}

/** 当前可用的数据层级（从 sources 去重，保持 L1<L2<L3<L4 顺序）。 */
function availableLevels(sources) {
  const order = ['L1', 'L2', 'L3', 'L4'];
  const present = new Set(sources.map((s) => s.level).filter(Boolean));
  return order.filter((lv) => present.has(lv));
}

/** 根据 level + subset 解析出 {fc, sourceKey, label}。
 *  - L1 → 该 level 第一个 source 的 fc（confidence 层，无极性）
 *  - L2 + PN → group 合并 fc（含 P/Neutral/N 全部点）
 *  - L2 + P  → childByPolarity['l2-positive'].fc
 *  - L2 + N  → childByPolarity['l2-negative'].fc
 *  无匹配返回 null。 */
function resolveSource(sources, level, subset) {
  const src = sources.find((s) => s.level === level);
  if (!src) return null;
  if (level === 'L2') {
    const sub = subset || 'PN';
    if (sub === 'P') {
      const child = src.childByPolarity && src.childByPolarity['l2-positive'];
      if (child && child.fc) return { fc: child.fc, sourceKey: `${src.sourceKey}#P`, label: `${src.label} · 积极` };
    } else if (sub === 'N') {
      const child = src.childByPolarity && src.childByPolarity['l2-negative'];
      if (child && child.fc) return { fc: child.fc, sourceKey: `${src.sourceKey}#N`, label: `${src.label} · 消极` };
    }
    return { fc: src.fc, sourceKey: `${src.sourceKey}#PN`, label: `${src.label} · 综合` };
  }
  return { fc: src.fc, sourceKey: src.sourceKey, label: src.label };
}

/** Open the HeatMap parameter dialog. */
export function openHeatmapDialog() {
  const dlg = dialogEl();
  if (!dlg) return;
  // Bug 1 fix: dialog 仍处 open 态时二次 showModal() 抛 InvalidStateError → 先关再开
  if (dlg.open) dlg.close();

  const sources = collectSources();
  if (!sources.length) {
    toast.error('请先导入 L2 情绪数据');
    return;
  }

  // 第一行：数据层级（从可用 sources 推断）。默认优先 L1→L2→…（availableLevels 已按层级排序）
  const levels = availableLevels(sources);
  const defaultLevel = levels[0] || '';
  const levelSelect = dlg.querySelector('#hm-level');
  levelSelect.innerHTML = levels.map((lv) =>
    `<option value="${lv}" ${lv === defaultLevel ? 'selected' : ''}>${lv}</option>`).join('')
    + (levels.length === 0 ? '<option value="">— 无数据 —</option>' : '');

  // 第二行：极性子集（仅 L2 启用）
  const subsetSelect = dlg.querySelector('#hm-subset');
  subsetSelect.disabled = defaultLevel !== 'L2';
  subsetSelect.value = 'PN';

  // 类型 chips（按当前 level+subset 的 fc 动态计数）
  const resolved0 = resolveSource(sources, defaultLevel, 'PN');
  renderTypeChips(dlg, resolved0 ? resolved0.fc : { features: [] });

  // Build ramp buttons — 默认 rainbow
  const rampList = dlg.querySelector('#hm-ramps');
  rampList.innerHTML = HEATMAP_RAMP_KEYS.map((key) => {
    const ramp = HEATMAP_RAMPS[key];
    const grad = ramp.stops.slice(1).map(([, c]) => c).join(',');
    const sel = key === DEFAULTS.rampKey ? ' is-sel' : '';
    return `<button class="hm-ramp-btn${sel}" data-ramp="${key}" title="${ramp.name}">
      <span class="hm-ramp-bar" style="background:linear-gradient(90deg, ${grad})"></span>
      ${ramp.name}
    </button>`;
  }).join('');

  // 单位（固定地理米）
  setUnit(dlg);

  // Reset defaults
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

  // 高级折叠区默认收起
  const adv = dlg.querySelector('#hm-advanced');
  if (adv && adv.tagName === 'DETAILS') adv.open = false;

  // Show
  dlg.showModal();
}

/** 设置半径 slider 为地理米模式（v2.1：去掉 px 切换，半径只用地理米）。
 *  注意：不能重写 #hm-radius-label.textContent —— 该 div 内嵌 #hm-radius-val 子 span，
 *  textContent 赋值会销毁子节点，导致第二次 openHeatmapDialog 时 querySelector('#hm-radius-val')
 *  返回 null 抛 TypeError（Bug 1/2 根因）。label 文案固定，单位由 val 文字体现。 */
function setUnit(dlg) {
  const radius = dlg.querySelector('#hm-radius');
  const val = dlg.querySelector('#hm-radius-val');
  if (!radius || !val) return;
  radius.min = 50; radius.max = 2000; radius.step = 10;
  radius.value = DEFAULTS.radiusM;
  val.textContent = `${DEFAULTS.radiusM} m`;
  dlg.dataset.unit = 'm';
}

function updateCurveHint(dlg) {
  const hints = {
    'linear': '当前：值越高 → 权重越高 → 颜色越热（推荐配 emotion_intensity）',
    'linear-inverse': '当前：值越低 → 权重越高 → 颜色越热（配 score 看消极）',
    'exponential': '当前：值越高 → 权重急剧升高 → 热点更集中',
    'exponential-inverse': '当前：值越低 → 权重急剧升高 → 热点更集中',
  };
  const v = dlg.querySelector('#hm-curve').value;
  dlg.querySelector('#hm-curve-hint').textContent = hints[v] || '';
}

/** Close the dialog. */
function closeDialog() {
  const dlg = dialogEl();
  if (dlg) dlg.close();
}

/** 按类型/强度过滤 features，返回新的 FeatureCollection。 */
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

/** Generate heatmap from dialog parameters. */
function generateHeatmap() {
  const dlg = dialogEl();
  if (!dlg) return;

  const level = dlg.querySelector('#hm-level').value;
  const subset = dlg.querySelector('#hm-subset').value;
  const rampKey = dlg.querySelector('#hm-ramps').querySelector('.is-sel')?.dataset?.ramp || DEFAULTS.rampKey;
  const radius = Number(dlg.querySelector('#hm-radius').value);
  const opacity = Number(dlg.querySelector('#hm-opacity').value) / 100;
  const weightField = dlg.querySelector('#hm-weight-field').value;
  const intensity = Number(dlg.querySelector('#hm-intensity').value);
  const weightCurve = dlg.querySelector('#hm-curve').value;
  const intensityMin = Number(dlg.querySelector('#hm-int-min').value);
  const minzoom = Number(dlg.querySelector('#hm-minzoom').value);
  const maxzoom = Number(dlg.querySelector('#hm-maxzoom').value);
  const unit = 'm';   // v2.1：半径固定地理米（去 px 切换）
  const selectedTypes = getSelectedTypes(dlg);

  // Resolve source by level + subset
  const sources = collectSources();
  const resolved = resolveSource(sources, level, level === 'L2' ? subset : null);
  if (!resolved) { toast.error('请选择有效数据层级'); return; }

  const sourceKey = resolved.sourceKey;

  // 按类型 + 强度过滤源数据
  const fc = filterFc(resolved.fc, selectedTypes, intensityMin);
  if (!fc.features.length) {
    toast.error('筛选后无数据点。请放宽情绪类型或强度阈值。');
    return;
  }

  // Remove old heatmap for same source (overwrite)
  const oldId = getHeatmapForSource(sourceKey);
  if (oldId) {
    removeLayerFromMap(oldId);
    removeLayer(oldId);
    removeHeatmapSource(sourceKey);
  }

  // Build ramp name
  const ramp = HEATMAP_RAMPS[rampKey];
  const rampName = ramp ? ramp.name : '自定义';

  // 名称带筛选信息（用户能看出当前热力图内容）
  const typeLabel = selectedTypes ? `[${selectedTypes.join('/')}]` : '[全类型]';
  const radiusLabel = unit === 'm' ? `${radius}m` : `${radius}px`;

  // Create heatmap layer
  const layer = addLayer({
    name: `HeatMap · ${rampName} ${typeLabel} ${radiusLabel}`,
    kind: 'heatmap',
    colorMode: 'heatmap-negative',
    fc,
    paint: {
      unit,
      radius,
      opacity,
      intensity,
      weightField,
      weightCurve,
      rampKey,
      typesFilter: selectedTypes,
      intensityMin,
      minzoom: minzoom > 0 ? minzoom : undefined,
      maxzoom: maxzoom < 22 ? maxzoom : undefined,
    },
  });

  // Track source → layer mapping
  setHeatmapForSource(sourceKey, layer.id);

  // Render
  renderLayer(layer);

  // 生成后独占显示新热力图：隐藏所有其他图层（含不同源热力图，保留数据可重开）。
  // 替换/删除规则：
  //   ① 同 sourceKey（两层都同）+ 新参数 → 上面的覆盖逻辑已 removeLayer 旧热力图（=替换）
  //   ② 第一层同 + 第二层不同 → sourceKey 不同（resolveSource 带 #P/#N/#PN）→ 视为不同数据源
  //   ③ 不同数据源 → 添加新热力图 + 隐藏其他热力图（关闭不删，可重开眼睛）
  // （setLayerVisible 后必须 renderLayer 才会真正从 map 移除图层）
  for (const l of [...getLayers()]) {
    if (l.id === layer.id) continue;
    if (l.visible) { setLayerVisible(l.id, false); renderLayer(l); }
  }

  // 选中新热力图 → 右端栏 Overview 切到它（否则还指向被隐藏的旧点层，显示空/错）
  selectLayer(layer.id);
  document.dispatchEvent(new CustomEvent('layers:changed'));
  document.dispatchEvent(new CustomEvent('layer:selected', { detail: layer.id }));
  toast.success(`已生成热力图：${rampName} · ${radiusLabel} · ${fc.features.length} 点`);

  closeDialog();
}

/** Initialize the HeatMap dialog: wire events. */
export function initHeatmapTool() {
  const dlg = dialogEl();
  if (!dlg) return;

  // Close button
  dlg.querySelectorAll('[data-close]').forEach((btn) => {
    btn.addEventListener('click', closeDialog);
  });

  // Close on backdrop click
  dlg.addEventListener('click', (e) => {
    if (e.target === dlg) closeDialog();
  });

  // 第一行 level 切换 → 启用/禁用第二行 subset + 重算类型 chips
  dlg.querySelector('#hm-level')?.addEventListener('change', (e) => {
    const lv = e.target.value;
    const subsetSel = dlg.querySelector('#hm-subset');
    subsetSel.disabled = lv !== 'L2';
    if (lv === 'L2') subsetSel.value = 'PN';
    const sources = collectSources();
    const resolved = resolveSource(sources, lv, lv === 'L2' ? subsetSel.value : null);
    renderTypeChips(dlg, resolved ? resolved.fc : { features: [] });
  });

  // 第二行 subset 切换 → 重算类型 chips
  dlg.querySelector('#hm-subset')?.addEventListener('change', (e) => {
    const lv = dlg.querySelector('#hm-level').value;
    const sources = collectSources();
    const resolved = resolveSource(sources, lv, e.target.value);
    renderTypeChips(dlg, resolved ? resolved.fc : { features: [] });
  });

  // 类型 chip 点击 toggle
  dlg.querySelector('#hm-types')?.addEventListener('click', (e) => {
    const chip = e.target.closest('.hm-type-chip');
    if (!chip) return;
    const cb = chip.querySelector('input');
    // 让 label 默认行为切 checkbox；这里只同步 is-on 类
    requestAnimationFrame(() => {
      chip.classList.toggle('is-on', cb.checked);
    });
  });

  // Ramp selection
  dlg.querySelector('#hm-ramps')?.addEventListener('click', (e) => {
    const btn = e.target.closest('.hm-ramp-btn');
    if (!btn) return;
    dlg.querySelectorAll('.hm-ramp-btn').forEach((b) => b.classList.remove('is-sel'));
    btn.classList.add('is-sel');
  });

  // Live value display: radius（地理米）
  dlg.querySelector('#hm-radius')?.addEventListener('input', (e) => {
    dlg.querySelector('#hm-radius-val').textContent = e.target.value + ' m';
  });

  // Live value display: opacity
  dlg.querySelector('#hm-opacity')?.addEventListener('input', (e) => {
    dlg.querySelector('#hm-opacity-val').textContent = e.target.value + '%';
  });

  // Live value display: intensity
  dlg.querySelector('#hm-intensity')?.addEventListener('input', (e) => {
    dlg.querySelector('#hm-intensity-val').textContent = Number(e.target.value).toFixed(1);
  });

  // Live: 强度阈值
  dlg.querySelector('#hm-int-min')?.addEventListener('input', (e) => {
    dlg.querySelector('#hm-int-min-val').textContent = Number(e.target.value).toFixed(2);
  });

  // Curve hint update
  dlg.querySelector('#hm-curve')?.addEventListener('change', () => updateCurveHint(dlg));

  // Zoom range live display
  dlg.querySelector('#hm-minzoom')?.addEventListener('input', (e) => {
    dlg.querySelector('#hm-minzoom-val').textContent = e.target.value;
  });
  dlg.querySelector('#hm-maxzoom')?.addEventListener('input', (e) => {
    dlg.querySelector('#hm-maxzoom-val').textContent = e.target.value;
  });

  // Generate button
  dlg.querySelector('#hm-generate')?.addEventListener('click', generateHeatmap);

  // ⓘ tooltip：body 级 fixed 定位，绕开 dialog overflow 裁剪。只初始化一次。
  initInfoTooltip();
}

let _infoTipInit = false;
function initInfoTooltip() {
  if (_infoTipInit) return;
  _infoTipInit = true;
  const tip = document.createElement('div');
  tip.className = 'hm-tooltip';
  tip.id = 'hm-tooltip';
  // 挂到 #heatmap-dialog（非 body）：原生 dialog 经 showModal() 进入浏览器 top layer，
  // body 级元素无论 z-index 多高都会被 dialog 遮挡；挂到 dialog 内则随 dialog 进 top layer。
  // .app-dialog 无 overflow/持续 transform，故 position:fixed 不被裁剪、定位准确。
  const dlg = document.getElementById('heatmap-dialog');
  (dlg || document.body).appendChild(tip);

  const show = (info) => {
    const src = info.querySelector('.hm-tip');
    if (!src) return;
    tip.textContent = src.textContent;
    tip.classList.add('is-show');
    // 先显示才能测 offsetHeight；定位到 ⓘ 上方居中，上方不够则下方
    const r = info.getBoundingClientRect();
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    let left = r.left + r.width / 2 - tw / 2;
    let top = r.top - th - 8;
    if (top < 8) top = r.bottom + 8;            // 上方不够 → 下方
    left = Math.max(8, Math.min(left, window.innerWidth - tw - 8));   // 左右不出屏
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  };
  const hide = () => tip.classList.remove('is-show');

  // 事件委托：覆盖所有 .hm-info（含动态生成）
  document.addEventListener('mouseover', (e) => {
    const info = e.target.closest('.hm-info');
    if (info) show(info);
  });
  document.addEventListener('mouseout', (e) => {
    if (e.target.closest('.hm-info')) hide();
  });
}
