// ═══ e2e-seam.js — E2E 测试专用 ═══
// 仅 index.html 在 ?e2e=1 时 dynamic-import 此文件（生产永不加载，main.js 零 test 代码）。
// tests/browser/ 经 window.__emcTest.loadPoints(fc) 注入 fixture 点层，供 zonal_stats/compare 聚合。
// 复用 Import 的点层装载逻辑（splitByGeometry + detectColorMode + L2 极性拆分 + addLayer/renderLayer）。
import { renderLayer, getMap, removeLayerFromMap } from './map.js';
import { addLayer, addGroup, getLayers, removeLayer } from './state.js';
import { splitByGeometry, detectColorMode, dsvRows } from './import.js';
import { hasImport, hasRange, hasAnalysis, hasVisibleEmotionLayer } from './ai_qa/cpd-state.js';
import { TOOLS, resetStepResults, resetCurrentResults } from './ai_qa/tools.js';   // 步 7 observation 快照基线（手册 v2.2·修订 6）：TOOLS 直调 + 状态重置
import { applyQualityDefense, _setLastToolRowsForTest, _buildOutletCardForTest, composeGapCard } from './ai_qa/harness.js';   // G0 R9 单测 + Wave 1 出口卡直测 + ③w5 措辞断言

// v1.7 测试飞轮：fetch 拦截 — 抓 /chat + /geo 请求供分阶段断言（fail fast）。
const _origFetch = window.fetch.bind(window);
window._testFetchLog = [];
// H1: template 信号从 diagnose:done 事件取（panel.js onDiagnose 派发），不再抓 /chat 请求体（其无 diagnose 字段·C1 断链根因）。
window._testDiagnoseLog = [];
document.addEventListener('diagnose:done', (e) => { window._testDiagnoseLog.push(e.detail); });
// #2 tool:executed 信号（density 等前端委托工具不走 fetch·geoCalls 抓不到 → harness 派发此事件补观测）
window._testToolExecLog = [];
document.addEventListener('tool:executed', (e) => { window._testToolExecLog.push(e.detail); });
window.fetch = async function (...args) {
  const url = typeof args[0] === 'string' ? args[0] : ((args[0] && args[0].url) || '');
  const opts = args[1] || {};
  const entry = { url, method: opts.method || 'GET', body: null, status: null, ts: Date.now() };
  try { entry.body = opts.body ? JSON.parse(opts.body) : null; } catch (_) { entry.body = opts.body ? String(opts.body).slice(0, 200) : null; }
  window._testFetchLog.push(entry);
  const r = await _origFetch(...args);
  entry.status = r.status;
  return r;
};

// renderLayer 容忍失败（底图 style 未加载时 addSource 抛错，但 addLayer 已入 state——
// zonal_stats/compare 只需 state 可见点层，不依赖地图渲染）。loadPoints/loadRange/addTestLayer 共用。
const safe = (fn) => { try { fn(); } catch (e) { /* map 未就绪，忽略——state 层仍可用 */ } };

window.__emcTest = {
  ready() { const m = getMap(); return !!(m && m.isStyleLoaded && m.isStyleLoaded()); },   // map style 加载完（仅参考；地图底图 404 时永 false，loadPoints 容忍之）
  loadPoints(fc) {
    const { points } = splitByGeometry(fc);
    if (!points.features.length) return { ok: false, reason: 'no points' };
    const { fc: pfc, colorMode } = detectColorMode(points);
    const base = 'e2e_points';
    // T9 例间清层：清旧 e2e_points 层 + 残留点层/group（治每例堆叠·K3 C1·+ FC-12 跨例点层残留 has_point 假阳）。
    // 保留 polygon（range/boundary·部分用例先加载范围再加载点·核清会误删范围）。
    for (const l of getLayers().slice()) {
      if (l.srcName === base || l.kind === 'point' || l.kind === 'group') { try { removeLayerFromMap(l.id); } catch (_) {} removeLayer(l.id); }
    }
    if (colorMode === 'polarity') {
      const pos = [], neu = [], neg = [];
      for (const f of pfc.features) {
        const pol = f.properties && f.properties.polarity;
        if (pol === 'Very Positive' || pol === 'Positive') pos.push(f);
        else if (pol === 'Very Negative' || pol === 'Negative') neg.push(f);
        else neu.push(f);
      }
      const group = addGroup({ name: '测试数据 · 情绪点', fc: pfc }); group.srcName = base;
      const paint = { opacity: 0.8 };
      const fcOf = (a) => ({ type: 'FeatureCollection', features: a });
      if (pos.length) { const L = addLayer({ name: `积极·${base}`, kind: 'point', parentId: group.id, colorMode: 'l2-positive', fc: fcOf(pos), paint }); L.srcName = base; safe(() => renderLayer(L)); }
      if (neu.length) { const L = addLayer({ name: `中性·${base}`, kind: 'point', parentId: group.id, colorMode: 'l2-neutral', fc: fcOf(neu), paint }); L.srcName = base; safe(() => renderLayer(L)); }
      if (neg.length) { const L = addLayer({ name: `消极·${base}`, kind: 'point', parentId: group.id, colorMode: 'l2-negative', fc: fcOf(neg), paint }); L.srcName = base; safe(() => renderLayer(L)); }
    } else {
      const L = addLayer({ name: base, kind: 'point', fc: pfc }); L.srcName = base; safe(() => renderLayer(L));
    }
    document.dispatchEvent(new CustomEvent('layers:changed'));
    return { ok: true };
  },
  // ── v1.7 测试飞轮 helpers ──
  clearLog() { window._testFetchLog = []; window._testDiagnoseLog = []; window._testToolExecLog = []; },
  chatPhases() {
    // H1: template 来自 diagnose:done 事件累积（每问一句 diagnose 一次），替代抓请求体。
    // F-1（CB-10 飞轮审查）：+planSteps = 实际执行通道计划步数（_allToolCalls 多 call / autoExpand 链长）·替代 method 派生（FC 单工具下恒 1·漂移）
    return (window._testDiagnoseLog || []).map((card) => ({
      phase: 'diagnose', template: card && card.template, method: (card && card.method) || null,
      planSteps: (card && Array.isArray(card._allToolCalls) && card._allToolCalls.length) || 0,
    }));   // D3: +method（D2 派生）供 EMC-SUM ② 计划n
  },
  geoCalls() { return window._testFetchLog.filter((e) => /\/(geo|spatial)\//.test(e.url)); },   // 含 /spatial/（grid 等走此路径，否则漏抓）
  toolExecs() { return (window._testToolExecLog || []).slice(); },   // #2 tool:executed 事件（前端委托工具如 density·补 geoCalls 盲区）
  send(text) {
    const i = document.getElementById('chat-input'); if (i) i.value = text;
    const b = document.getElementById('chat-send'); if (b) b.click();
  },
  async waitAnswer(timeout = 90000) {
    const s = Date.now();
    while (Date.now() - s < timeout) {
      if (document.querySelector('.aiq-exit-badge') && !document.querySelector('.chat-cursor')) return true;
      await new Promise((r) => setTimeout(r, 500));
    }
    return false;
  },
  badge() { const b = document.querySelector('.aiq-exit-badge'); return b ? b.textContent.trim() : null; },
  collapsed() { return document.getElementById('emc-panel').classList.contains('is-collapsed'); },
  welcome() { return !!document.querySelector('.emc-welcome'); },
  hintVisible() { const h = document.querySelector('.emc-cpd-hint'); return !!(h && !h.hidden); },
  hintText() { const h = document.querySelector('.emc-cpd-hint-text'); return h ? h.textContent : null; },
  guidanceCard() { return !!document.querySelector('.cpd-guide-card'); },
  inputValue() { const i = document.getElementById('chat-input'); return i ? i.value : ''; },
  scrollTop() { const l = document.getElementById('chat-messages'); return l ? l.scrollTop : -1; },
  layerCount() { return document.querySelectorAll('#layer-list .layer-row').length; },
  layerNames() { return [...document.querySelectorAll('#layer-list .layer-name')].map((e) => e.textContent.trim()).filter(Boolean); },
  mapSources() { try { const m = getMap(); const s = m && m.getStyle() && m.getStyle().sources; return s ? Object.keys(s) : []; } catch (_) { return []; } },   // C: map 真渲染的 source（验图层不只是入 state）
  /** F-2（CB-10 飞轮审查）：产物语义断言读口——返回最后 N 个产物图层（含 paint._ui/kind/feature 数）。
   *  断言据此验证产物正确性（density 色板钩子 analysisKey/rampKey、overlay feature 数、clip point_count、merge 几何）。 */
  productLayers(limit = 5) {
    return getLayers().slice().filter((l) => l.kind !== 'group' && l.fc && l.fc.features).slice(-limit).map((l) => ({
      name: l.name, kind: l.kind, srcName: l.srcName || '', fcCount: (l.fc.features || []).length,
      paint: (l.paint && l.paint._ui) || null, rampKey: (l.paint && l.paint.rampKey) || null,
      colorMode: l.colorMode || null,
    }));
  },
  async injectFixture(name) {
    const fc = await fetch(`/tests/browser/fixtures/${name}.geojson`).then((r) => r.json());
    return this.loadPoints(fc);
  },
  clickHalo() { const a = document.querySelector('.emc-input-area'); if (a) a.click(); },
  clickDirection(dir) { const b = document.querySelector(`.cpd-guide-opt[data-dir="${dir}"]`); if (b) b.click(); },
  answerText() { const as = document.querySelectorAll('.aiq-answer'); return as.length ? as[as.length - 1].innerText.trim().slice(0, 300) : ''; },
  askChips() { return document.querySelectorAll('.aiq-ask-chip').length; },   // CB-12 P1：ask_user 选项胶囊数（诚实追问判定）
  getMode() { const b = document.querySelector('#aiq-mode button.is-active'); return b ? b.dataset.mode : null; },
  setMode(m) { const b = document.querySelector(`#aiq-mode button[data-mode="${m}"]`); if (b) b.click(); },
  newChat() { document.getElementById('chat-new')?.click(); },
  clearRanges() {
    // CB-14（CPD-L03）：清残留范围层（e2e_range polygon·跨用例污染）——让新对话后 hasRange=false → 引导回 range 态。
    //   loadPoints 故意保留 polygon（部分用例先加载范围再加载点）·故 CPD 顺序用例需显式清。
    for (const l of getLayers().slice()) {
      if (l.srcName === 'e2e_range' || (l.kind === 'polygon' && l.paint && l.paint._ui && l.paint._ui.tool)) {
        try { removeLayerFromMap(l.id); } catch (_) {} removeLayer(l.id);
      }
    }
    document.dispatchEvent(new CustomEvent('layers:changed'));
  },
  async loadCSV(path) {
    // T1 修（2026-07-24）：① pool processed→performance ② 复用产品 dsvRows 解引号（治 text 含逗号致列错位/丢行）
    //   ③ polarity 精确列名（^polarity$·非 polarity_hint 子串）+ 保留原始五档值交 loadPoints→detectColorMode 拆分（治 :119 二档塌缩 Very→Neutral）
    const txt = await fetch('/DATA/performance/' + path).then((r) => r.text());
    const { header, body } = dsvRows(txt);
    const find = (re) => header.findIndex((h) => re.test((h || '').trim()));
    const li = find(/^(lon|lng|longitude|经度)$/i), ai = find(/^(lat|latitude|纬度)$/i);
    if (li < 0 || ai < 0) return { ok: false, reason: 'CSV 缺 lon/lat 列' };
    const pi = find(/^polarity$/i), si = find(/^(score|emotion_intensity)$/i);
    const ti = find(/^text$/i), di = find(/^domain$/i), ei = find(/^element$/i);
    const hl = header[li], ha = header[ai], g = (i) => (i >= 0 ? header[i] : '');
    const feats = [];
    for (const row of body) {
      const lon = parseFloat(row[hl]); const lat = parseFloat(row[ha]);
      if (!isFinite(lon) || !isFinite(lat)) continue;
      const props = {};
      if (pi >= 0) props.polarity = row[g(pi)] || '';   // 保留原始极性（Very Positive 等）→ detectColorMode 五档拆分
      if (si >= 0) props.score = parseFloat(row[g(si)]) || 0;
      if (ti >= 0) props.text = (row[g(ti)] || '').slice(0, 200);
      if (di >= 0) props.domain = row[g(di)] || '';
      if (ei >= 0) props.element = row[g(ei)] || '';
      feats.push({ type: 'Feature', properties: props, geometry: { type: 'Point', coordinates: [lon, lat] } });
    }
    if (!feats.length) return { ok: false, reason: 'CSV 无有效点' };
    return this.loadPoints({ type: 'FeatureCollection', features: feats });
  },
  async loadRange(name) {
    const label = name.split('/').pop().replace('.geojson', '');
    // 防重复：同名范围已加载则跳过（治飞轮每例重复 loadRange 堆叠行政区层·Bug2）
    if (getLayers().some((l) => l.kind === 'polygon' && l.srcName === 'e2e_range' && l.name === label)) {
      return { ok: true, count: 0, reused: true };
    }
    const fc = await fetch('/DATA/boundaries/' + name).then((r) => r.json());
    const { polygons } = splitByGeometry(fc);
    if (polygons.features.length) {
      const L = addLayer({ name: label, kind: 'polygon', fc: polygons, paint: { fillOn: false, lineWidth: 1.5, fillOpacity: 0.1 } });
      L.srcName = 'e2e_range';
      safe(() => renderLayer(L));
    }
    document.dispatchEvent(new CustomEvent('layers:changed'));
    return { ok: true, count: polygons.features.length };
  },
  // ── 步 7 observation 快照基线（手册 v2.2·修订 6/E-③）：TOOLS 直调 + 状态重置 + 层读取 ──
  TOOLS,
  getLayers,
  applyQualityDefense,   // G0 R9 单测：构造 toolHistory 无 clip + 结论声称已裁剪 → 断言「未在工具执行记录」标注出现
  composeGapCard,        // ③w5（Codex/glm P2）：措辞断言——零工具尝试（failedObs=0）不含「图层」字眼·防回归
  // CB-16 Wave 1 出口卡直测：设 rows 缓存（模拟 macro zonal/rank 产物）+ 直调 _maybeBuildOutletCard（门放宽·newLayerCount=0 也出卡）
  setOutletRows(rows) { _setLastToolRowsForTest(rows); return true; },
  async buildOutletCardForTest(diagnose, ctx, newLayerCount) { return _buildOutletCardForTest(diagnose, ctx, newLayerCount); },
  resetToolState() { resetStepResults(); resetCurrentResults(); },
  /** 步 8：存量产物模拟（legacy 无 kind _ui 的编辑回填 color 判据测试）。 */
  addTestLayer(name, kind, fc, paint) {
    const L = addLayer({ name, kind, fc, paint });
    safe(() => renderLayer(L));
    document.dispatchEvent(new CustomEvent('layers:changed'));
    return L.id;
  },
};

// CPD G1 谓词暴露（用例 10·A1 谓词真值测试）：把死信号/谓词盲区（M2 无情绪层撒谎）从评审发现变测试发现。
// emc_helpers.read_predicate(page, "() => window.__cpdPredicates.hasVisibleEmotionLayer()")。
window.__cpdPredicates = { hasImport, hasRange, hasAnalysis, hasVisibleEmotionLayer };
console.log('[e2e] window.__emcTest.loadPoints ready (e2e-seam.js)');
