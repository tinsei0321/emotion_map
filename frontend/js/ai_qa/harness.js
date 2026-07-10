// ═══ harness.js — Agent Loop 编排器（ReAct：Thought→Action→Observation 循环 + 审查→修订）═══
// 模型每轮自主思考 + 决定动作 + 看结果再想，多轮（上限 MAX_ROUNDS）直到 action='answer'，
// 出草稿 → Flash 审查员按七条 checklist 审查 → 不达标带 hints 自动 revise 重写 1 轮。
// 前置：DIAGNOSE 问题理解卡（认知层）→ 注入 ctx.context 导工具选型 + 结论颗粒度；硬缺口短路请求上传。
// 降级：agent_step 解析失败不再裸显 raw，break loop 仍走 finalStep 出一次性 answer。
import * as stages from './stages.js';
import { TOOLS } from './tools.js';
import { getLayers } from '../state.js';

const MAX_ROUNDS = 8;
const OBS_TRUNC = 200;      // observation 注入 history 截断长度
const PARAMS_TRUNC = 80;    // action params 摘要截断长度
const REVIEW_ENABLED = false;   // 审查机制总开关：false=暂关 Flash 审查员（效果待优化，下轮重构审查 agent）；诚实门 _verifyClaims 仍保留

/** 当前地图图层状态摘要（附入每轮 history，让 LLM 感知操作是否已生效、避免盲目重试）。 */
function _mapState() {
  const ls = getLayers().filter((l) => l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length);
  const recent = ls.slice(-3).reverse().map((l) => l.name).join('/');
  return `地图:${ls.length}层${recent ? '[' + recent + ']' : ''}`;
}

/** 压缩单轮历史摘要（注入下轮 / final / review prompt，降 token 提注意力）。 */
function compressHistory(round, thought, action, obs) {
  const paramsStr = action.params ? JSON.stringify(action.params).slice(0, PARAMS_TRUNC) : '';
  const obsShort = obs && obs.length > OBS_TRUNC ? obs.slice(0, OBS_TRUNC) + '…' : (obs || '');
  return `第${round}轮 | thought: ${thought || ''} | 动作: ${action.name}(${paramsStr}) | 观察: ${obsShort} | ${_mapState()}`;
}

const _DOMAIN_LABEL = { urban_planning: '城市规划', urban_renewal: '城市更新', urban_operation: '城市运营', urban_governance: '城市治理' };

/** diagnose 卡 → 一行摘要（注入 ctx.context，让后续 agent/final/review 都看到）。 */
function formatDiagnoseSummary(d) {
  const dom = (d.domain_lens || []).map((k) => _DOMAIN_LABEL[k] || k).join('/') || '?';
  const strat = (d.data_plan && d.data_plan.strategy) || 'ready';
  const method = (d.method || []).join(' → ') || '—';
  return `【已诊断】scale=${d.scale || '?'} | domain=${dom} | outlet=${d.outlet || '?'} | strategy=${strat} | method=${method}`;
}

/** 上一轮 trace 蒸馏（ctx.priorTurn）→ 一行摘要，注入 ctx.context 顶部，所有 phase 可见，供续作承接。
 *  多轮连续性：补 5.51 之前只回灌 trace.final 的失忆——上轮 intent/method/已做/缺口结构化带回。 */
function formatPriorTurn(p) {
  if (!p) return '';
  const parts = ['【上一轮上下文】'];
  if (p.intent) parts.push(`intent=${p.intent}`);
  if (p.method) parts.push(`method=${p.method}`);
  if (p.done && p.done !== '（无工具调用）') parts.push(`已做=${p.done}`);
  if (p.gap) parts.push(`缺口=${p.gap}`);
  if (p.strategy) parts.push(`strategy=${p.strategy}`);
  return parts.join(' | ');
}

/** 硬缺口（request_upload）→ 请求上传结论文本（说清需要什么/为何/格式）。 */
function buildRequestUploadText(d) {
  const dp = d.data_plan || {};
  const needed = (dp.needed || []).join('、') || '所需专业数据';
  const gap = (dp.gap || []).join('、') || '关键数据维度';
  return '## 需要您补充数据才能严谨作答\n\n'
    + `本问需要 **${needed}** 才能给出可靠结论，当前情绪地图数据中尚缺：**${gap}**。\n\n`
    + '**为何必需**：情绪地图覆盖市民主观感受（极性/4×5 归因），但本问还涉及上述专业数据维度，'
    + '缺它则结论会偏离，故不硬答。\n\n'
    + '**建议上传**：Shapefile / GeoJSON（投影 EPSG:4326，或注明所用坐标系），'
    + '在范围选择里加载后即可纳入分析；上传后重提此问即可。\n\n'
    + '> 若暂无此数据，可在下方说明——我将基于现有情绪数据给出**标注了口径局限**的参考性结论。';
}

/** A1 产物验证 gate：抽取草稿里声称"已生成/加载"的图层名，对照地图实际图层；谎报→返 hints 注入 revise。 */
function _verifyClaims(draft) {
  if (!draft) return { ok: true };
  const re = /(?:已生成|已加载|已裁出|裁出了|生成了|已创建|新建了|产出了)\s*[「]?([^\n「」，。：:]{2,15})[」]?\s*(?:的?图层|层|面)/g;
  const claims = [];
  let m;
  while ((m = re.exec(draft)) !== null) claims.push(m[1].trim());
  if (!claims.length) return { ok: true };
  const actual = getLayers().map((l) => l.name).filter(Boolean);
  const missing = claims.filter((c) => !actual.some((a) => a === c || a.includes(c) || c.includes(a)));
  if (!missing.length) return { ok: true };
  return { ok: false, hints: `诚实检查：回答声称已生成/加载「${missing.join('、')}」图层，但地图实际图层为[${actual.join('、') || '无'}]。请补做（调 geo 工具生成缺失图层）或纠正陈述（改为"尝试未成功/未生成"）。严禁谎报已做。` };
}

/** 跑一次 revise（产物验证或 review 不达标触发；最多 1 轮）。返修订后文本或 null。 */
async function _reviseOnce(ctx, hooks, draft, hints, toolHistoryText) {
  if (!hints) return null;
  if (hooks.onReviseStart) hooks.onReviseStart();
  try {
    const revised = await stages.reviseStep(ctx, draft, hints, toolHistoryText, hooks);
    if (revised && revised.trim()) {
      if (hooks.onReviseDone) hooks.onReviseDone(revised);
      return revised;
    }
  } catch (e) { /* revise 失败保留 draft */ }
  return null;
}

const _GEO_TOOLS = ['extract_feature', 'overlay', 'clip', 'filter_attr', 'merge', 'buffer', 'zonal_stats', 'rank', 'area_stats', 'nearest', 'hotspot'];
/** F3：诊断 method 里规划的 geo 工具步骤数。数组元素用 ' → ' 拼接后按 →/，/；/换行 分句，
 *  每句首个工具名计 1 步；**不**按 ASCII 逗号分（工具实参含逗号，如 ($1,land)）。 */
function _plannedGeoSteps(method) {
  const m = Array.isArray(method) ? method.join(' → ') : (method || '');
  return m.split(/[→，；;\n]/).reduce((n, clause) => {
    const mm = clause.match(/([a-z_]+)\s*\(/i);
    return (mm && _GEO_TOOLS.includes(mm[1])) ? n + 1 : n;
  }, 0);
}
/** F3：历轮实际执行的 geo 工具步数（toolHistory 每行 = 一轮一个动作，匹配 "动作: tool("）。 */
function _executedGeoSteps(toolHistory) {
  let n = 0;
  for (const line of (toolHistory || [])) {
    const m = String(line).match(/动作:\s*([a-z_]+)\s*\(/i);
    if (m && _GEO_TOOLS.includes(m[1])) n++;
  }
  return n;
}

/**
 * Agent Loop 一次问答。
 * @param ctx    {question, context(grounding), contextTokens, signal, model}
 * @param hooks  渲染回调（panel.js 实现）：
 *   onReason(tok, round)       — reasoning 思考链增量（round 标识所属轮，0=最终/修订阶段）
 *   onDiagnose(card)           — 问题理解卡（DIAGNOSE 前置步；{degraded:true}=降级）
 *   onRoundStart(round)        — 每轮开始（Pro 模式新建 reasoning 分段块）
 *   onThought(text, round)     — 第 round 轮 thought
 *   onAction(action, round)    — 第 round 轮 action
 *   onObservation(text, round) — 第 round 轮工具观察
 *   onFinal(tok)               — 草稿结论增量
 *   onFinalDone(text)          — 草稿完成
 *   onReview(review)           — 审查结果 {pass, scores, revise_hints, degraded?}
 *   onReviseStart()            — 开始重写
 *   onRevise(tok)              — 修订结论增量
 *   onReviseDone(text)         — 修订完成
 *   onDegraded(text)           — finalStep 也失败时的最终降级
 * @returns {Promise<{ok, degraded?, rounds?, final?, review?, revised?}>}
 */
export async function orchestrate(ctx, hooks = {}) {
  const toolHistory = [];   // 每轮压缩摘要（注入下轮 prompt）
  let round = 1;
  let degraded = false;
  let forcedContinues = 0;   // F3 完整性 gate 强制续做计数（max 1，防 agent 0 工具就 answer）

  // 多轮连续性：上一轮 trace 蒸馏注入 ctx.context 顶部（diagnose 及后续 phase 均可见，供续作承接）
  const _prior = formatPriorTurn(ctx.priorTurn);
  if (_prior) ctx.context = _prior + '\n\n' + (ctx.context || '');

  // 认知前置步：DIAGNOSE 问题理解卡（失败/降级不阻塞，照走 agent loop）
  let diagnose = null;
  try {
    diagnose = await stages.diagnoseStep(ctx, hooks);
  } catch (e) { diagnose = null; }
  diagnose = diagnose || { degraded: true };
  if (hooks.onDiagnose) hooks.onDiagnose(diagnose);
  if (!diagnose.degraded) {
    // 注入下游：卡摘要前插 ctx.context，所有后续 phase 都看到（导工具选型 + 结论颗粒度）
    ctx.context = formatDiagnoseSummary(diagnose) + '\n\n' + (ctx.context || '');
    // intent 分流（A 通用→短路直接答；B 纯操作→agent loop 走 geo 工具；C 情绪→原路径）
    let intent = diagnose.intent || 'emotion_analysis';
    // 矛盾守卫（normalizeCard 之外的最后防线）：仍判 general 却带纯几何 geo method = 误标，
    // 改 gis_operation（同步写回 diagnose 供 loop/trace/priorTurn 用），避免 general 短路致无工具半截回答。
    if (intent === 'general' && /extract_feature|overlay|clip|filter_attr|merge|buffer/.test((diagnose.method || []).join(' '))) {
      intent = 'gis_operation';
      diagnose.intent = 'gis_operation';
      ctx.context = '【intent 修正】诊断卡标 general，但 method 含 GIS 操作工具——按纯 GIS 操作处理，走 geo 工具产出图层，勿文字作答。\n\n' + (ctx.context || '');
    }
    if (ctx.resume) {
      // 续作：跳过 general/request_upload 短路，强制 agent loop 续跑上轮 method（上轮缺口数据现多已就位）
      ctx.context = '【续作上一轮】用户在追问/续做上一轮任务。承接上一轮 intent+method，从断点续做（上轮【缺口】数据若已上传则继续执行原 method 剩余步骤）；勿当全新问题、勿在 method 未完成前 answer。\n\n' + (ctx.context || '');
      if (ctx.priorTurn && ctx.priorTurn.intent === 'gis_operation') {
        ctx.context = '【intent=纯GIS操作】用 geo 工具（extract_feature/clip/filter_attr/overlay/merge/buffer）完成操作，出口=新图层（自动落地图）。\n\n' + (ctx.context || '');
      }
    } else {
      if (intent === 'general') {
        ctx.context = '【intent=通用问答】直接简洁作答即可，不要 4×5 归因、不要演示逻辑链、不要引导情绪场景。\n\n' + (ctx.context || '');
        const draft = await stages.finalStep(ctx, hooks, '');
        if (hooks.onFinalDone) hooks.onFinalDone(draft);
        if (hooks.onReview) hooks.onReview({ pass: true, degraded: true, degraded_reason: '通用问答·跳过审查' });   // 清「审查中…」占位
        return { ok: true, rounds: 0, final: draft, review: { pass: true, degraded: true, skipped: 'general' }, degraded: false, diagnose };
      }
      if (intent === 'gis_operation') {
        ctx.context = '【intent=纯GIS操作】用 geo 工具（extract_feature/clip/filter_attr/overlay/merge/buffer）完成操作，出口=新图层（自动落地图）。不要 4×5 归因报告、不受尺度范式约束；操作完成后简述产出了什么图层即 answer。\n\n' + (ctx.context || '');
      }
      // 硬缺口短路：不硬答，直接出"请求上传"为结论
      if (diagnose.data_plan && diagnose.data_plan.strategy === 'request_upload') {
        const tpl = buildRequestUploadText(diagnose);
        if (hooks.onFinalDone) hooks.onFinalDone(tpl);
        if (hooks.onReview) hooks.onReview({ pass: true, degraded: true, degraded_reason: '数据缺口·跳过审查' });   // 清「审查中…」占位
        return { ok: true, rounds: 0, final: tpl, review: { pass: true, degraded: true }, degraded: false, diagnose };
      }
    }
  }

  while (round <= MAX_ROUNDS) {
    if (hooks.onRound) hooks.onRound(round);
    if (hooks.onRoundStart) hooks.onRoundStart(round);
    let toolHistoryText = toolHistory.length ? toolHistory.join('\n') : '';
    // A3：上一步失败 → 头部加换法重试提示（避免重复同样失败调用）
    if (toolHistory.length && /\[ERR\]|失败|错误/.test(toolHistory[toolHistory.length - 1])) {
      toolHistoryText = '⚠️ 上一步工具失败（见观察末尾）。换参数（字段名/preset/range）或换工具重试，勿重复同样失败调用。\n\n' + toolHistoryText;
    }

    const step = await stages.agentStep(ctx, hooks, round, toolHistoryText);
    if (!step) { degraded = true; break; }   // 解析失败：break + 仍走 finalStep 回退

    if (hooks.onThought) hooks.onThought(step.thought, round);
    if (step.action.type === 'answer') {
      // F3 完整性 gate（计划 vs 已执行，max 1）：纯 GIS 操作 + 诊断有 ≥2 步 geo 计划，却执行步数 < 计划步数就 answer = 半截，强制续做。
      // 仅 gis_operation 触发（情绪问不受此约束）；按步数比对，工具等价替换(clip↔overlay)不会误判（步数够即放行）。
      if (diagnose.intent === 'gis_operation' && forcedContinues < 1) {
        const _planned = _plannedGeoSteps(diagnose.method);
        const _executed = _executedGeoSteps(toolHistory);
        if (_planned >= 2 && _executed < _planned) {
          forcedContinues++;
          toolHistory.push(`⚠️ 完整性检查：此问判为纯 GIS 操作，诊断计划含 ${_planned} 个 geo 步骤，但你只执行了 ${_executed} 个就要 answer——这是半截回答。请继续完成剩余步骤产出全部应有图层，全部完成后再 answer；本轮禁止 answer。`);
          if (hooks.onObservation) hooks.onObservation(`[完整性] 计划 ${_planned} 步 / 已执行 ${_executed} 步，继续执行…`, round);
          round++;
          continue;
        }
      }
      if (hooks.onAction) hooks.onAction(step.action, round);
      break;
    }
    if (hooks.onAction) hooks.onAction(step.action, round);

    // 执行工具（直调主窗口）
    const fn = TOOLS[step.action.name];
    let obs = '';
    if (fn) {
      try {
        const r = await fn(step.action.params || {});
        obs = (r && r.observation) || '（无观察）';
      } catch (e) {
        obs = '工具执行失败：' + (e && e.message ? e.message : e);
      }
    } else {
      obs = `未知工具：${step.action.name}`;
    }
    if (hooks.onObservation) hooks.onObservation(obs, round);

    toolHistory.push(compressHistory(round, step.thought, step.action, obs));
    round++;
  }

  // 草稿结论（agent 决定 answer / 达上限 / 降级回退 都走这里）
  const toolHistoryText = toolHistory.length ? toolHistory.join('\n') : '';
  let draft = '';
  try {
    draft = await stages.finalStep(ctx, hooks, toolHistoryText);
  } catch (e) {
    if (hooks.onDegraded) hooks.onDegraded('');
    return { ok: false, degraded: true, rounds: round };
  }
  if (hooks.onFinalDone) hooks.onFinalDone(draft);

  // intent=纯GIS操作：跳过情绪审查（review 的尺度/4×5 标准不适用于操作类回答）
  const _intent = diagnose && !diagnose.degraded ? (diagnose.intent || 'emotion_analysis') : 'emotion_analysis';
  if (_intent === 'gis_operation') {
    // A1：操作类易谎报，产物验证 gate（跳 review 但不跳诚实检查）
    const verify = _verifyClaims(draft);
    if (!verify.ok) {
      const revised = await _reviseOnce(ctx, hooks, draft, verify.hints, toolHistoryText);
      if (revised) draft = revised;
    }
    return { ok: true, rounds: round, final: draft, review: { pass: true, degraded: true, skipped: 'gis_operation' }, degraded };
  }

  // 审查（REVIEW_ENABLED=false 时跳过 Flash 审查员，仅留诚实门 _verifyClaims）
  let review = null;
  if (REVIEW_ENABLED) {
    try {
      review = await stages.reviewStep(ctx, draft, toolHistoryText);
    } catch (e) {
      review = { pass: true, degraded: true, degraded_reason: String(e && e.message || e) };
    }
  } else {
    review = { pass: true, degraded: true, degraded_reason: '审查机制暂关·重构中' };
  }
  if (hooks.onReview) hooks.onReview(review);

  // 不达标 或 谎报（A1 产物验证）→ revise 重写（最多 1 轮，不递归）
  let final = draft;
  const verify = _verifyClaims(draft);
  const reviseHints = [review && !review.pass && !review.degraded && review.revise_hints, !verify.ok ? verify.hints : null].filter(Boolean).join('\n');
  if (reviseHints) {
    const revised = await _reviseOnce(ctx, hooks, draft, reviseHints, toolHistoryText);
    if (revised) final = revised;
  }
  return { ok: true, rounds: round, final, review, degraded };
}
