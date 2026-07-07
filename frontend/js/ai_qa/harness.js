// ═══ harness.js — Agent Loop 编排器（ReAct：Thought→Action→Observation 循环）═══
// 替代上一轮的线性 think→execute→answer→review。模型每轮自主思考 + 决定动作 + 看结果再想，
// 多轮（上限 MAX_ROUNDS）直到 action='answer'，再出最终结论。Claude Code 式渐进解题。
import * as stages from './stages.js';
import { TOOLS } from './tools.js';

const MAX_ROUNDS = 8;

/**
 * Agent Loop 一次问答。
 * @param ctx    {question, context(grounding), contextTokens, signal}
 * @param hooks  渲染回调（panel.js 实现）：
 *   onReason(tok)             — reasoning 思考链增量（跨轮累积，动态实时）
 *   onThought(text, round)    — 第 round 轮 thought（解题步骤行）
 *   onAction(action, round)   — 第 round 轮 action（同步骤行）
 *   onObservation(text, round)— 第 round 轮工具观察（同步骤行）
 *   onFinal(tok)              — 最终结论增量（markdown）
 *   onFinalDone(text)         — 最终结论完成
 *   onDegraded(text)          — agent_step 解析失败降级
 *   onRound(round)            — 每轮开始（可选，进度提示）
 * @returns {Promise<{ok, degraded?, rounds?, final?}>}
 */
export async function orchestrate(ctx, hooks = {}) {
  const toolHistory = [];   // 每轮摘要字符串（注入下轮 prompt）
  let round = 1;

  while (round <= MAX_ROUNDS) {
    if (hooks.onRound) hooks.onRound(round);
    const toolHistoryText = toolHistory.length ? toolHistory.join('\n') : '';

    const step = await stages.agentStep(ctx, hooks, round, toolHistoryText);
    if (!step) return { ok: false, degraded: true };

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

    // 入 tool_history（下轮 prompt 让模型看到历轮探索）
    const paramsStr = step.action.params ? JSON.stringify(step.action.params) : '';
    toolHistory.push(`第${round}轮 | thought: ${step.thought} | 动作: ${step.action.name}(${paramsStr}) | 观察: ${obs}`);
    round++;
  }

  // 最终结论（agent 决定 answer 或达到轮数上限）
  const toolHistoryText = toolHistory.length ? toolHistory.join('\n') : '';
  const final = await stages.finalStep(ctx, hooks, toolHistoryText);
  if (hooks.onFinalDone) hooks.onFinalDone(final);
  return { ok: true, rounds: round, final };
}
