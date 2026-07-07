// ═══ harness.js — Agent Loop 编排器（ReAct：Thought→Action→Observation 循环 + 审查→修订）═══
// 模型每轮自主思考 + 决定动作 + 看结果再想，多轮（上限 MAX_ROUNDS）直到 action='answer'，
// 出草稿 → Flash 审查员按六条 checklist 审查 → 不达标带 hints 自动 revise 重写 1 轮。
// 降级：agent_step 解析失败不再裸显 raw，break loop 仍走 finalStep 出一次性 answer。
import * as stages from './stages.js';
import { TOOLS } from './tools.js';

const MAX_ROUNDS = 8;
const OBS_TRUNC = 200;      // observation 注入 history 截断长度
const PARAMS_TRUNC = 80;    // action params 摘要截断长度

/** 压缩单轮历史摘要（注入下轮 / final / review prompt，降 token 提注意力）。 */
function compressHistory(round, thought, action, obs) {
  const paramsStr = action.params ? JSON.stringify(action.params).slice(0, PARAMS_TRUNC) : '';
  const obsShort = obs && obs.length > OBS_TRUNC ? obs.slice(0, OBS_TRUNC) + '…' : (obs || '');
  return `第${round}轮 | thought: ${thought || ''} | 动作: ${action.name}(${paramsStr}) | 观察: ${obsShort}`;
}

/**
 * Agent Loop 一次问答。
 * @param ctx    {question, context(grounding), contextTokens, signal, model}
 * @param hooks  渲染回调（panel.js 实现）：
 *   onReason(tok, round)       — reasoning 思考链增量（round 标识所属轮，0=最终/修订阶段）
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
