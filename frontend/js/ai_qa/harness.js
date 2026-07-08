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
    const intent = diagnose.intent || 'emotion_analysis';
    if (intent === 'general') {
      ctx.context = '【intent=通用问答】直接简洁作答即可，不要 4×5 归因、不要演示逻辑链、不要引导情绪场景。\n\n' + (ctx.context || '');
      const draft = await stages.finalStep(ctx, hooks, '');
      if (hooks.onFinalDone) hooks.onFinalDone(draft);
      return { ok: true, rounds: 0, final: draft, review: { pass: true, degraded: true, skipped: 'general' }, degraded: false, diagnose };
    }
    if (intent === 'gis_operation') {
      ctx.context = '【intent=纯GIS操作】用 geo 工具（extract_feature/clip/filter_attr/overlay/merge/buffer）完成操作，出口=新图层（自动落地图）。不要 4×5 归因报告、不受尺度范式约束；操作完成后简述产出了什么图层即 answer。\n\n' + (ctx.context || '');
    }
    // 硬缺口短路：不硬答，直接出"请求上传"为结论
    if (diagnose.data_plan && diagnose.data_plan.strategy === 'request_upload') {
      const tpl = buildRequestUploadText(diagnose);
      if (hooks.onFinalDone) hooks.onFinalDone(tpl);
      return { ok: true, rounds: 0, final: tpl, review: { pass: true, degraded: true }, degraded: false, diagnose };
    }
  }

  while (round <= MAX_ROUNDS) {
    if (hooks.onRound) hooks.onRound(round);
    if (hooks.onRoundStart) hooks.onRoundStart(round);
    const toolHistoryText = toolHistory.length ? toolHistory.join('\n') : '';

    const step = await stages.agentStep(ctx, hooks, round, toolHistoryText);
    if (!step) { degraded = true; break; }   // 解析失败：break + 仍走 finalStep 回退

    if (hooks.onThought) hooks.onThought(step.thought, round);
    if (hooks.onAction) hooks.onAction(step.action, round);

    if (step.action.type === 'answer') break;

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
    return { ok: true, rounds: round, final: draft, review: { pass: true, degraded: true, skipped: 'gis_operation' }, degraded };
  }

  // 审查
  let review = null;
  try {
    review = await stages.reviewStep(ctx, draft, toolHistoryText);
  } catch (e) {
    review = { pass: true, degraded: true, degraded_reason: String(e && e.message || e) };
  }
  if (hooks.onReview) hooks.onReview(review);

  // 不达标 → revise 重写（最多 1 轮，不递归）
  let final = draft;
  if (review && !review.pass && !review.degraded && review.revise_hints) {
    if (hooks.onReviseStart) hooks.onReviseStart();
    try {
      const revised = await stages.reviseStep(ctx, draft, review.revise_hints, toolHistoryText, hooks);
      if (revised && revised.trim()) {
        final = revised;
        if (hooks.onReviseDone) hooks.onReviseDone(revised);
      }
    } catch (e) {
      // revise 失败：保留 draft，不阻塞
    }
  }
  return { ok: true, rounds: round, final, review, degraded };
}
