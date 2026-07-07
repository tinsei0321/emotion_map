// ═══ stages.js — Agent Loop 阶段（agentStep / finalStep）═══
// 两阶段：agentStep（ReAct 每轮 reasoning + {thought,action}）/ finalStep（最终结论 markdown）。
// ctx.model = 'pro' | 'flash'（思考深度开关，后端别名解析到 V4 真实 ID）。
import { streamChat } from './api.js';

/** 容错解析 agent_step 的 {thought, action} JSON；失败返回 null（走降级）。 */
export function parseAgentStep(raw) {
  if (!raw) return null;
  const s = raw.indexOf('{');
  const e = raw.lastIndexOf('}');
  if (s < 0 || e < 0 || e <= s) return null;
  try {
    const obj = JSON.parse(raw.slice(s, e + 1));
    if (!obj || !obj.action) return null;
    return { thought: obj.thought || '', action: obj.action };
  } catch (_) {
    return null;
  }
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
      onReason: (t) => { hooks.onReason && hooks.onReason(t); },
    });
  const step = parseAgentStep(acc.token);
  if (!step) {
    if (hooks.onDegraded) hooks.onDegraded(acc.token);
    return null;
  }
  return step;
}

/** 最终结论：基于 tool_history 流式出 markdown + [ref:]。 */
export async function finalStep(ctx, hooks, toolHistory) {
  const messages = [{ role: 'user', content: ctx.question }];
  let final = '';
  await streamChat(messages, ctx.context,
    (tok) => { final += tok; if (hooks.onFinal) hooks.onFinal(tok); },
    (err) => { throw new Error(err); },
    {
      phase: 'answer', toolHistory, signal: ctx.signal,
      model: ctx.model,
      onReason: (t) => { hooks.onReason && hooks.onReason(t); },
    });
  return final;
}
