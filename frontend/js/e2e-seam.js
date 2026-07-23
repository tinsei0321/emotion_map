// ═══ e2e-seam.js — E2E 测试专用 ═══
// 仅 index.html 在 ?e2e=1 时 dynamic-import 此文件（生产永不加载，main.js 零 test 代码）。
// tests/browser/ 经 window.__emcTest.loadPoints(fc) 注入 fixture 点层，供 zonal_stats/compare 聚合。
// 复用 Import 的点层装载逻辑（splitByGeometry + detectColorMode + L2 极性拆分 + addLayer/renderLayer）。
import { renderLayer, getMap } from './map.js';
import { addLayer, addGroup } from './state.js';
import { splitByGeometry, detectColorMode } from './import.js';
import { hasImport, hasRange, hasAnalysis, hasVisibleEmotionLayer } from './ai_qa/cpd-state.js';

window.__emcTest = {
  ready() { const m = getMap(); return !!(m && m.isStyleLoaded && m.isStyleLoaded()); },   // map style 加载完（仅参考；地图底图 404 时永 false，loadPoints 容忍之）
  loadPoints(fc) {
    const { points } = splitByGeometry(fc);
    if (!points.features.length) return { ok: false, reason: 'no points' };
    const { fc: pfc, colorMode } = detectColorMode(points);
    const base = 'e2e_points';
    // renderLayer 容忍失败（底图 style 未加载时 addSource 抛错，但 addLayer 已入 state——
    // zonal_stats/compare 只需 state 可见点层，不依赖地图渲染）。
    const safe = (fn) => { try { fn(); } catch (e) { /* map 未就绪，忽略——state 层仍可用 */ } };
    if (colorMode === 'polarity') {
      const pos = [], neu = [], neg = [];
      for (const f of pfc.features) {
        const pol = f.properties && f.properties.polarity;
        if (pol === 'Very Positive' || pol === 'Positive') pos.push(f);
        else if (pol === 'Very Negative' || pol === 'Negative') neg.push(f);
        else neu.push(f);
      }
      const group = addGroup({ name: 'L2 · e2e', fc: pfc }); group.srcName = base;
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
};

// CPD G1 谓词暴露（用例 10·A1 谓词真值测试）：把死信号/谓词盲区（M2 无情绪层撒谎）从评审发现变测试发现。
// emc_helpers.read_predicate(page, "() => window.__cpdPredicates.hasVisibleEmotionLayer()")。
window.__cpdPredicates = { hasImport, hasRange, hasAnalysis, hasVisibleEmotionLayer };
console.log('[e2e] window.__emcTest.loadPoints ready (e2e-seam.js)');
