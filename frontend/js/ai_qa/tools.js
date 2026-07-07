// ═══ tools.js — Agent Loop 工具集（查询型 + 操作型，直调主窗口函数）═══
// 还原单窗口后，tools 直调 map/state/panel（删跨窗口协议）。每个 tool 返回 {observation, data?}：
//   observation = 给 LLM 看的摘要字符串（入 tool_history）；data = 结构化（前端可选用于渲染）。
import { getLayers, getSelectedLayer } from '../state.js';
import { fitBoundsTo } from '../map.js';
import { activateTab, setOverview } from '../panel.js';
import { DOMAIN_LABEL, ELEMENT_LABEL } from '../popup.js';
import { generateGridForAI } from '../grid-tool.js';

let _lastGrid = null;   // 最近生成聚合层（ensure_zone/query 优先用）

function isAnalysis(l) {
  const ui = l && l.paint && l.paint._ui;
  return !!(l && l.kind === 'polygon' && ui && (ui.tool === 'grid' || ui.tool === 'terrain'));
}
function activeAnalysis() {
  if (_lastGrid && _lastGrid.layerId) {
    const l = getLayers().find((x) => x.id === _lastGrid.layerId);
    if (l) return l;
  }
  const sel = getSelectedLayer();
  if (sel && isAnalysis(sel)) return sel;
  return getLayers().find((l) => isAnalysis(l) && l.fc && l.fc.features && l.fc.features.length) || null;
}
function fitToFeature(f) {
  const g = f && f.geometry;
  if (!g) return;
  const rings = g.type === 'Polygon' ? g.coordinates[0]
    : (g.type === 'MultiPolygon' ? g.coordinates.flatMap((p) => p[0]) : null);
  if (!rings || !rings.length) return;
  let mnX = Infinity, mxX = -Infinity, mnY = Infinity, mxY = -Infinity;
  for (const [x, y] of rings) { if (x < mnX) mnX = x; if (x > mxX) mxX = x; if (y < mnY) mnY = y; if (y > mxY) mxY = y; }
  if (isFinite(mnX)) fitBoundsTo([mnX, mnY, mxX, mxY]);
}
function pi(f) { return Number((f.properties || {}).polarity_index); }

function sortZones(feats, crit) {
  if (crit === 'worst') return feats.slice().sort((a, b) => pi(a) - pi(b));
  if (crit === 'best') return feats.slice().sort((a, b) => pi(b) - pi(a));
  if (crit.startsWith('domain:')) {
    const d = crit.split(':')[1];
    return feats.slice().sort((a, b) => {
      const pa = String((a.properties || {}).domain_top || '').includes(d) ? 1 : 0;
      const pb = String((b.properties || {}).domain_top || '').includes(d) ? 1 : 0;
      return (pb - pa) || (Math.abs(pi(b)) - Math.abs(pi(a)));
    });
  }
  if (crit.startsWith('element:')) {
    const e = crit.split(':')[1];
    return feats.slice().sort((a, b) => {
      const pa = String((a.properties || {}).element_top || '').includes(e) ? 1 : 0;
      const pb = String((b.properties || {}).element_top || '').includes(e) ? 1 : 0;
      return (pb - pa) || (Math.abs(pi(b)) - Math.abs(pi(a)));
    });
  }
  return feats.slice().sort((a, b) => Math.abs(pi(b)) - Math.abs(pi(a)));
}

/** buildContext：grounding 摘要（panel send + query_layers 共用）。 */
export function buildContext() {
  const layers = getLayers();
  const an = activeAnalysis();
  const parts = [];
  const loaded = layers
    .filter((l) => l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length)
    .map((l) => `${l.name}(${l.fc.features.length}条)`).join('、');
  parts.push('已加载图层：' + (loaded || '（无）'));
  if (!an) {
    parts.push('（暂无聚合层——区域级问题建议先 ensure_zone 生成）');
    return parts.join('\n');
  }
  const feats = an.fc.features;
  parts.push(`当前分析层：${an.name}（${feats.length} 个聚合单元）`);
  const agg = { 'Very Positive': 0, Positive: 0, Neutral: 0, Negative: 0, 'Very Negative': 0 };
  for (const f of feats) {
    const p = f.properties || {};
    agg['Very Positive'] += p.n_very_positive || 0;
    agg.Positive += p.n_positive || 0;
    agg.Neutral += p.n_neutral || 0;
    agg.Negative += p.n_negative || 0;
    agg['Very Negative'] += p.n_very_negative || 0;
  }
  parts.push(`极性计数：非常积极${agg['Very Positive']} / 积极${agg.Positive} / 中性${agg.Neutral} / 消极${agg.Negative} / 非常消极${agg['Very Negative']}`);
  const top = feats
    .map((f) => f.properties || {})
    .filter((p) => p.polarity_index != null && !isNaN(p.polarity_index))
    .sort((a, b) => Math.abs(b.polarity_index) - Math.abs(a.polarity_index))
    .slice(0, 8);
  if (top.length) {
    parts.push('高张力区域：\n' + top.map((p) => {
      const name = p.name || p.issue_label || '未命名';
      const dom = DOMAIN_LABEL[p.domain_top] || p.domain_top || '?';
      const elm = ELEMENT_LABEL[p.element_top] || p.element_top || '?';
      return `  - ${name}：极性 ${Number(p.polarity_index).toFixed(2)}，${dom}×${elm}，问题=${p.issue_label || '—'}，${p.point_count || 0}点`;
    }).join('\n'));
  }
  return parts.join('\n');
}

export const TOOLS = {
  /** 查当前已加载的图层/数据。 */
  query_layers() {
    const an = activeAnalysis();
    const loaded = getLayers()
      .filter((l) => l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length)
      .map((l) => `${l.name}(${l.fc.features.length}条)`).join('、');
    return { observation: `已加载图层：${loaded || '（无）'}\n当前分析层：${an ? an.name + '（' + an.fc.features.length + ' 单元）' : '暂无聚合层（区域级问题建议 ensure_zone）'}` };
  },

  /** 按维度排序找区域（地图同步飞到）。 */
  query_zone_stats(params = {}) {
    const an = activeAnalysis();
    if (!an || !an.fc) return { observation: '暂无聚合层（建议先 ensure_zone 生成）' };
    const crit = params.criteria || 'worst';
    const top = Math.min(Math.max(Number(params.top) || 3, 1), 10);
    let feats = an.fc.features
      .filter((f) => { const p = f.properties || {}; return p.polarity_index != null && !isNaN(p.polarity_index); });
    if (!feats.length) return { observation: '聚合层无极性数据' };
    feats = sortZones(feats, crit).slice(0, top);
    const found = feats.map((f) => {
      const p = f.properties || {};
      return { name: p.name || p.issue_label || '未命名', pi: Number(p.polarity_index).toFixed(2),
        dom: DOMAIN_LABEL[p.domain_top] || p.domain_top || '?', elm: ELEMENT_LABEL[p.element_top] || p.element_top || '?',
        pc: p.point_count || 0, issue: p.issue_label || '—' };
    });
    feats.forEach((f) => fitToFeature(f));
    const label = { worst: '情绪最差', best: '情绪最好' }[crit] || crit;
    return {
      observation: `${label} Top${top}：\n` + found.map((x) => `  - ${x.name}：极性${x.pi}，${x.dom}×${x.elm}，${x.pc}点，问题=${x.issue}`).join('\n'),
      data: { found },
    };
  },

  /** 查 4×5 归因（全局或某区域）。 */
  query_attribution(params = {}) {
    const an = activeAnalysis();
    if (!an || !an.fc) return { observation: '暂无聚合层' };
    const zone = (params.zone || '').trim();
    let feats = an.fc.features
      .filter((f) => { const p = f.properties || {}; return p.polarity_index != null && !isNaN(p.polarity_index); });
    if (zone) feats = feats.filter((f) => { const nm = (f.properties || {}).name || ''; return nm === zone || nm.includes(zone) || zone.includes(nm); });
    feats = feats.sort((a, b) => Math.abs(pi(b)) - Math.abs(pi(a))).slice(0, 8);
    if (!feats.length) return { observation: zone ? `未找到「${zone}」的归因数据` : '无归因数据' };
    const rows = feats.map((f) => {
      const p = f.properties || {};
      return `  - ${p.name || p.issue_label || '未命名'}：极性${Number(p.polarity_index).toFixed(2)}，${DOMAIN_LABEL[p.domain_top] || p.domain_top}×${ELEMENT_LABEL[p.element_top] || p.element_top}，${p.point_count || 0}点，问题=${p.issue_label || '—'}`;
    });
    return { observation: (zone ? `「${zone}」及相近区域归因` : '高张力区域归因') + '：\n' + rows.join('\n') };
  },

  /** 查关键词/热门话题（按 issue_label 聚合近似）。 */
  query_keywords(params = {}) {
    const an = activeAnalysis();
    if (!an || !an.fc) return { observation: '暂无聚合层' };
    const pol = params.polarity || 'overall';
    let feats = an.fc.features;
    if (pol !== 'overall') feats = feats.filter((f) => {
      const v = Number((f.properties || {}).polarity_index);
      return pol === 'positive' ? v > 0.15 : v < -0.15;
    });
    const kw = {};
    feats.forEach((f) => {
      const p = f.properties || {};
      const k = p.issue_label || '';
      if (k) kw[k] = (kw[k] || 0) + (p.point_count || 1);
    });
    const top = Object.entries(kw).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([k, v]) => `${k}(${v})`).join('、');
    return { observation: `${pol === 'overall' ? '综合' : pol === 'positive' ? '积极' : '消极'}关键词/问题 Top：${top || '（无）'}` };
  },

  /** 生成/确保聚合域（无则生成，有则复用）。 */
  async ensure_zone(params = {}) {
    const existing = activeAnalysis();
    if (existing && existing.fc && existing.fc.features && existing.fc.features.length) {
      return { observation: `复用现有聚合层「${existing.name}」（${existing.fc.features.length} 单元）` };
    }
    try {
      const r = await generateGridForAI({
        analysis: params.analysis === 'zonal' ? 'zonal' : 'square',
        cellSize: Number(params.cell_size) || undefined,
        polarity: params.polarity || 'overall',
        mode: params.mode === '3d' ? '3d' : '2d',
        silent: true,
      });
      _lastGrid = { layerId: r && (r.layerId || r.id) };
      return { observation: `已生成聚合层「${r.layerName}」（${r.featureCount} 单元）` };
    } catch (e) {
      return { observation: '聚合层生成失败：' + (e && e.message ? e.message : e) };
    }
  },

  /** 定位区域到地图（飞到+高亮）。 */
  focus_zones(params = {}) {
    const names = Array.isArray(params.names) ? params.names : [];
    let n = 0;
    names.filter(Boolean).forEach((nm) => {
      for (const l of getLayers()) {
        if (!isAnalysis(l) || !l.fc) continue;
        const f = l.fc.features.find((ff) => { const n2 = (ff.properties || {}).name || ''; return n2 === nm || n2.includes(nm) || nm.includes(n2); });
        if (f) { fitToFeature(f); document.dispatchEvent(new CustomEvent('cell:selected', { detail: { feature: f, layer: l } })); n++; break; }
      }
    });
    return { observation: `已定位 ${n}/${names.length} 个区域` };
  },

  /** 展开 Overview 归因面板。 */
  open_attribution() {
    const an = activeAnalysis();
    if (!an) return { observation: '暂无聚合层' };
    activateTab('overview');
    setOverview(an);
    return { observation: '已展开 Overview 归因面板（4×5 矩阵 + 关键词）' };
  },

  /** 深读某区域明细。 */
  inspect_zone(params = {}) {
    const an = activeAnalysis();
    const name = (params.name || '').trim();
    if (!an || !name) return { observation: '缺区域名或暂无聚合层' };
    const f = an.fc.features.find((ff) => { const nm = (ff.properties || {}).name || ''; return nm === name || nm.includes(name) || name.includes(nm); });
    if (!f) return { observation: `未找到「${name}」` };
    fitToFeature(f);
    document.dispatchEvent(new CustomEvent('cell:selected', { detail: { feature: f, layer: an } }));
    const p = f.properties || {};
    return { observation: `「${name}」深读：极性${Number(p.polarity_index).toFixed(2)}，${DOMAIN_LABEL[p.domain_top] || p.domain_top}×${ELEMENT_LABEL[p.element_top] || p.element_top}，${p.point_count || 0}点，问题=${p.issue_label || '—'}` };
  },
};
