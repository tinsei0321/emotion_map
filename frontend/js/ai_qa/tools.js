// ═══ tools.js — 执行层 · 工具表（语义化 + 协议化 RPC）═══
// 每个 tool = request(type, params) → {ok, note, data}（经 protocol 发给主窗口 ai_qa_host.js 执行）。
// 语义化重命名（对齐情绪地图数据流）：ensure_zone / rank_zones / open_attribution / inspect_zone。
// conclude 不是 tool（是 stage 切换，harness 在 execute 后进 answer）。
import { request, REQ } from './protocol.js';

export const TOOLS = {
  /** 确保有聚合域（无则按问题选标准/指定单元生成；主窗口复用最近生成层）。 */
  async ensure_zone(params = {}) {
    const r = await request(REQ.ENSURE_ZONE, {
      analysis: params.analysis === 'zonal' ? 'zonal' : 'square',
      cell_size: Number(params.cell_size) || 500,
      polarity: params.polarity || 'overall',
      mode: params.mode === '3d' ? '3d' : '2d',
    });
    return {
      ok: !!r.ok,
      note: r.note || (r.ok ? '已就绪聚合层' : '聚合层生成失败'),
      data: r.data || {},
    };
  },

  /** 按维度排序找区域并定位（主窗口飞到 + 高亮 + 回传 found 列表）。 */
  async rank_zones(params = {}) {
    const r = await request(REQ.RANK_ZONES, {
      criteria: params.criteria || 'worst',
      top: Math.min(Math.max(Number(params.top) || 3, 1), 10),
    });
    return {
      ok: !!r.ok,
      note: r.note || '',
      data: r.data || {},
    };
  },

  /** 展开 Overview 归因面板（4×5 矩阵 + 关键词）。 */
  async open_attribution() {
    const r = await request(REQ.OPEN_ATTRIBUTION, {});
    return { ok: !!r.ok, note: r.note || '' };
  },

  /** 深读某聚合域的极性/归因/关键词明细（主窗口触发 cell:selected 深读）。 */
  async inspect_zone(params = {}) {
    const r = await request(REQ.INSPECT_ZONE, { name: params.name || '' });
    return { ok: !!r.ok, note: r.note || '', data: r.data || {} };
  },
};

/** 把 tool 执行结果序列化为 observation 文本（喂给 answer 阶段 LLM，含真实区域/极性/归因）。 */
export function observationFromResults(results) {
  if (!results || !results.length) return '（无前置操作）';
  return results.map((o) => {
    let s = `【${o.label || o.tool}】${o.ok ? '完成' : '未成'}：${o.note || ''}`;
    const d = o.data || {};
    if (Array.isArray(d.found) && d.found.length) {
      s += '\n' + d.found.map((x) =>
        `  - ${x.name}：极性指数 ${x.pi}，${x.dom || '?'}×${x.elm || '?'}，${x.pc || 0} 点`).join('\n');
    }
    if (d.layerName) s += `（层：${d.layerName}，${d.featureCount || 0} 单元）`;
    if (d.detail) s += '\n' + d.detail;
    return s;
  }).join('\n');
}
