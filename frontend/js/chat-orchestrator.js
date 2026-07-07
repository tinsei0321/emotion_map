// ═══ chat-orchestrator.js — AI 端到端编排器（plan → execute → answer）═══
// 把"AI 出按钮等用户点"升级为"AI 规划→自动执行→同步展示→结论"。
//   阶段1 Plan   ：POST /chat {phase:'plan'} → LLM(JSON mode) 输出 {thinking, steps[]}
//   阶段2 Execute：前端按 steps[] 自动逐步执行 TOOLS（生成图层/聚焦/开Overview），收集 execution_result
//   阶段3 Answer ：POST /chat {phase:'answer', execution_result} → LLM 基于真实结果出结论（流式）
// 编排器只产"步骤执行 + 结果收集"；UI（实现路径/执行轨道/结论）由 chat-panel 通过 hooks 回调渲染。
import { streamChat } from './api.js';
import { getLayers, getLayer } from './state.js';
import { fitBoundsTo } from './map.js';
import { activateTab, setOverview, setTable } from './panel.js';
import { DOMAIN_LABEL, ELEMENT_LABEL } from './popup.js';
import { generateGridForAI } from './grid-tool.js';

// 编排器内部状态：最近一次 generate_grid 结果（focus_zone/open_overview 优先用它）
let _lastGrid = null;

/** 编排器当前可用分析层：最近生成 > 首个 grid 分析层。 */
function activeAnalysis() {
  if (_lastGrid && getLayer(_lastGrid.layerId)) return getLayer(_lastGrid.layerId);
  return getLayers().find((l) => l && l.kind === 'polygon' && l.paint && l.paint._ui
    && (l.paint._ui.tool === 'grid' || l.paint._ui.tool === 'terrain')
    && l.fc && l.fc.features && l.fc.features.length);
}

/** 飞到单个 feature（polygon）的包络盒。 */
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

// ── 工具表：plan 中 steps[].tool → 前端实际操作 ──────────────────────────────
// 每个工具返回 { ok, note, data? }；note 进 execution_result 回喂 answer 阶段。
const TOOLS = {
  async generate_grid(params = {}) {
    const r = await generateGridForAI({
      analysis: params.analysis === 'zonal' ? 'zonal' : 'square',
      cellSize: Number(params.cell_size) || undefined,
      polarity: params.polarity || 'overall',
      mode: params.mode === '3d' ? '3d' : '2d',
      silent: true,   // 编排器自显步骤状态，不发 toast
    });
    _lastGrid = r;
    return { ok: true, note: `已生成分析层「${r.layerName}」（${r.featureCount} 个聚合单元）`,
             data: { layerName: r.layerName, featureCount: r.featureCount, level: r.level } };
  },

  async focus_zone(params = {}) {
    const crit = params.criteria === 'best' ? 'best' : 'worst';
    const top = Math.min(Math.max(Number(params.top) || 3, 1), 10);
    const an = activeAnalysis();
    if (!an || !an.fc || !an.fc.features) return { ok: false, note: '暂无分析层可定位' };
    const feats = an.fc.features
      .filter((f) => f.properties && f.properties.polarity_index != null && !isNaN(f.properties.polarity_index))
      .sort((a, b) => crit === 'best'
        ? (b.properties.polarity_index - a.properties.polarity_index)
        : (a.properties.polarity_index - b.properties.polarity_index))
      .slice(0, top);
    if (!feats.length) return { ok: false, note: '分析层无极性数据，无法按情绪排序' };
    const found = feats.map((f) => {
      const p = f.properties || {};
      return {
        name: p.name || p.issue_label || '未命名',
        pi: Number(p.polarity_index).toFixed(2),
        dom: DOMAIN_LABEL[p.domain_top] || p.domain_top || '?',
        elm: ELEMENT_LABEL[p.element_top] || p.element_top || '?',
        pc: p.point_count || 0,
      };
    });
    feats.forEach((f) => fitToFeature(f));   // 逐个飞过（末个停留聚焦）
    const label = crit === 'worst' ? '情绪最差' : '情绪最好';
    return { ok: true, note: `${label}区域：` + found.map((x) => `${x.name}(极性${x.pi})`).join('、'),
             data: { found } };
  },

  async open_overview() {
    const an = activeAnalysis();
    if (!an) return { ok: false, note: '暂无分析层可展示归因' };
    activateTab('overview');
    setOverview(an);
    return { ok: true, note: '已展开 Overview 归因视图' };
  },

  async open_table() {
    const an = activeAnalysis();
    if (!an || !an.fc) return { ok: false, note: '暂无分析层数据' };
    activateTab('table');
    setTable(an.fc, an);
    return { ok: true, note: '已展开 Table 明细' };
  },
};

/** 容错解析 plan JSON（流末提取首个 {...}；失败返回 null 走降级）。 */
export function parsePlan(raw) {
  if (!raw) return null;
  const s = raw.indexOf('{');
  const e = raw.lastIndexOf('}');
  if (s < 0 || e < 0 || e <= s) return null;
  try {
    const obj = JSON.parse(raw.slice(s, e + 1));
    if (!obj || !Array.isArray(obj.steps)) return null;
    return obj;
  } catch (_) {
    return null;
  }
}

/**
 * 端到端编排一次问答。
 * @param {string} question 用户提问
 * @param {object} hooks
 *   context:grounding 摘要 / deepThink:切 Pro / signal:AbortController /
 *   onReason(tok)：plan 阶段思考链增量 /
 *   onPlan(thinking, steps)：plan 就绪 → 渲染实现路径 + 执行轨道 /
 *   onStepState(id, status, note)：status='running'|'done'|'error'，每步实时状态 /
 *   onAnswer(tok)：answer 阶段结论增量（markdown）
 * @returns {Promise<{ok, degraded?, plan?, executionResult?}>}
 */
export async function orchestrate(question, hooks = {}) {
  const ctx = hooks.context || '';
  const messages = [{ role: 'user', content: question }];
  const planRaw = { acc: '' };

  // ── 阶段1 Plan：LLM 流式输出 {thinking, steps[]} JSON ──
  await streamChat(messages, ctx,
    (tok) => { planRaw.acc += tok; },
    (err) => { throw new Error(err); },
    { phase: 'plan', signal: hooks.signal,
      onReason: (t) => { hooks.onReason && hooks.onReason(t); },
      model: hooks.deepThink ? 'deepseek-reasoner' : undefined });

  const plan = parsePlan(planRaw.acc);
  if (!plan) {
    // 降级：plan 解析失败 → 把 planRaw 当 legacy 文字回答（onAnswer 流给 chat-panel 渲染）
    if (hooks.onAnswer) hooks.onAnswer(planRaw.acc);
    return { ok: false, degraded: true, text: planRaw.acc };
  }
  if (hooks.onPlan) hooks.onPlan(plan.thinking || '', plan.steps || []);

  // ── 阶段2 Execute：前端自动逐步执行 steps（answer 步骤除外）──
  const resultNotes = [];
  for (const step of plan.steps || []) {
    if (!step || step.tool === 'answer') continue;
    if (hooks.onStepState) hooks.onStepState(step.id, 'running', '');
    try {
      const fn = TOOLS[step.tool];
      const r = fn ? await fn(step.params || {}) : { ok: false, note: `未知操作：${step.tool}` };
      const note = (r && r.note) || (r && r.ok ? '完成' : '跳过');
      resultNotes.push(`${step.label || step.tool}：${note}`);
      if (hooks.onStepState) hooks.onStepState(step.id, r && r.ok ? 'done' : 'error', note);
    } catch (e) {
      const msg = e && e.message ? e.message : String(e);
      resultNotes.push(`${(step && step.label) || step.tool}：失败（${msg}）`);
      if (hooks.onStepState) hooks.onStepState(step.id, 'error', msg);
    }
  }

  // ── 阶段3 Answer：执行结果回喂 LLM 出结论（流式 markdown）──
  const executionResult = resultNotes.length ? resultNotes.join('\n') : '（无前置操作）';
  const hasAnswerStep = (plan.steps || []).some((s) => s && s.tool === 'answer');
  if (hasAnswerStep) {
    await streamChat(messages, ctx,
      (tok) => { hooks.onAnswer && hooks.onAnswer(tok); },
      (err) => { throw new Error(err); },
      { phase: 'answer', executionResult, signal: hooks.signal });
  }
  return { ok: true, plan, executionResult };
}

/** 重置编排器内部状态（清空会话时调）。 */
export function resetOrchestrator() {
  _lastGrid = null;
}
