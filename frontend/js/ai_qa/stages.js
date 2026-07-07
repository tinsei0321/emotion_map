// ═══ stages.js — Agent Loop 阶段（agentStep / finalStep / reviewStep / reviseStep）═══
// 四阶段：agentStep（ReAct 每轮 reasoning + {thought,action}）/ finalStep（草稿 markdown）
//       / reviewStep（Flash 审查员 JSON）/ reviseStep（审查未过重写 markdown）。
// ctx.model = 'pro' | 'flash'（思考深度开关，后端别名解析到 V4 真实 ID）；review 固定 flash。
import { streamChat } from './api.js';

/** 容错解析 agent_step 的 {thought, action} JSON；失败返回 null（走降级）。 */
export function parseAgentStep(raw) {
  if (!raw) return null;
  let s = raw;
  // 1. strip markdown fence ```json ... ``` / ``` ... ```
  const fence = s.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fence) s = fence[1];
  // 2. 截取首末花括号
  const start = s.indexOf('{');
  const end = s.lastIndexOf('}');
  if (start < 0 || end < 0 || end <= start) return null;
  let candidate = s.slice(start, end + 1);
  // 3. 去尾逗号（}, ] 前的逗号）
  candidate = candidate.replace(/,(\s*[}\]])/g, '$1');
  // 4. 首次解析
  try {
    const obj = JSON.parse(candidate);
    if (obj && obj.action) return { thought: obj.thought || '', action: obj.action };
  } catch (_) { /* fall through to regex extract */ }
  // 5. 二次：正则提取 action 子对象（容错模型加前后解释/嵌套）
  const am = candidate.match(/"action"\s*:\s*\{([\s\S]*?)\}\s*[,}]/);
  if (am) {
    try {
      const action = JSON.parse('{' + am[1] + '}');
      if (action && action.type) {
        const tm = candidate.match(/"thought"\s*:\s*"((?:[^"\\]|\\.)*)"/);
        return { thought: tm ? tm[1] : '', action };
      }
    } catch (__) { /* give up */ }
  }
  return null;
}

/** Agent Loop 一轮：流式 reasoning + content({thought,action} JSON)。null=解析失败降级。 */
export async function agentStep(ctx, hooks, round, toolHistory) {
  const messages = [{ role: 'user', content: ctx.question }];
  const acc = { token: '' };
  await streamChat(messages, ctx.context,
    (tok) => { acc.token += tok; },
    (err) => { throw new Error(err); },
    {
      phase: 'agent_step', roundN: round, toolHistory, signal: ctx.signal,
      model: ctx.model,
      onReason: (t) => { hooks.onReason && hooks.onReason(t, round); },
    });
  const step = parseAgentStep(acc.token);
  if (!step) {
    if (hooks.onDegraded) hooks.onDegraded(acc.token);
    return null;
  }
  return step;
}

/** 草稿结论：基于 tool_history 流式出 markdown + [ref:]。 */
export async function finalStep(ctx, hooks, toolHistory) {
  const messages = [{ role: 'user', content: ctx.question }];
  let final = '';
  await streamChat(messages, ctx.context,
    (tok) => { final += tok; if (hooks.onFinal) hooks.onFinal(tok); },
    (err) => { throw new Error(err); },
    {
      phase: 'answer', toolHistory, signal: ctx.signal,
      model: ctx.model,
      onReason: (t) => { hooks.onReason && hooks.onReason(t, 0); },
    });
  return final;
}

/** 审查草稿：非流式拿 Flash 审查员 JSON {pass, scores, revise_hints}。失败返回 degraded。 */
export async function reviewStep(ctx, draft, toolHistory) {
  let review = null;
  await streamChat([], ctx.context,
    () => {},
    (err) => { throw new Error(err); },
    {
      phase: 'review', draft, toolHistory, signal: ctx.signal,
      model: 'flash',
      onReview: (r) => { review = r; },
    });
  return review || { pass: true, degraded: true, degraded_reason: '审查员无响应' };
}

/** 修订重写：基于 draft + hints 流式出修订 markdown。 */
export async function reviseStep(ctx, draft, hints, toolHistory, hooks) {
  const messages = [{ role: 'user', content: ctx.question }];
  let revised = '';
  await streamChat(messages, ctx.context,
    (tok) => { revised += tok; if (hooks.onRevise) hooks.onRevise(tok); },
    (err) => { throw new Error(err); },
    {
      phase: 'revise', draft, reviewHints: hints, toolHistory, signal: ctx.signal,
      model: ctx.model,
      onReason: (t) => { hooks.onReason && hooks.onReason(t, 0); },
    });
  return revised;
}
