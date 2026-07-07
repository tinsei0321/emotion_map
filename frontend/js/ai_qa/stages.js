// ═══ stages.js — Harness 四阶段（think/execute/answer/review）═══
// 每阶段是独立函数（未来加 reflect/RAG 等 Stage 在此注册即可）。harness.js orchestrate 按序编排。
// 形态无关：不依赖 DOM（panel.js 通过 hooks 回调渲染）。
import { streamChat, reviewChat } from './api.js';
import { TOOLS, observationFromResults } from './tools.js';

/** 容错解析 think 阶段 JSON（{framing, mapping, steps[]}）；失败返回 null 走降级。 */
export function parseThink(raw) {
  if (!raw) return null;
  const s = raw.indexOf('{');
  const e = raw.lastIndexOf('}');
  if (s < 0 || e < 0 || e <= s) return null;
  try {
    const obj = JSON.parse(raw.slice(s, e + 1));
    if (!obj || !Array.isArray(obj.steps)) return null;
    return { framing: obj.framing || '', mapping: obj.mapping || '', steps: obj.steps };
  } catch (_) {
    return null;
  }
}

// ── Stage 1 · THINK：Pro 流式出 reasoning + {framing,mapping,steps[]} JSON ──
export async function think(ctx, hooks) {
  const messages = [{ role: 'user', content: ctx.question }];
  const acc = { token: '' };
  await streamChat(messages, ctx.context,
    (tok) => { acc.token += tok; },
    (err) => { throw new Error(err); },
    {
      phase: 'think', signal: ctx.signal,
      onReason: (t) => { hooks.onReason && hooks.onReason(t); },
    });
  const plan = parseThink(acc.token);
  if (!plan) {
    if (hooks.onDegraded) hooks.onDegraded(acc.token);   // 降级：当文字回答
    return { ok: false, degraded: true, raw: acc.token };
  }
  if (hooks.onFraming) hooks.onFraming(plan.framing);
  if (hooks.onMapping) hooks.onMapping(plan.mapping);
  if (hooks.onPlan) hooks.onPlan(plan.steps);
  return { ok: true, plan };
}

// ── Stage 2 · EXECUTE+OBSERVE：按 steps 逐个跑 TOOLS（协议驱动主窗口）──
export async function execute(ctx, hooks, plan) {
  const results = [];
  for (const step of plan.steps || []) {
    if (!step || step.tool === 'conclude') continue;
    if (hooks.onStepState) hooks.onStepState(step.id, 'running', '');
    const fn = TOOLS[step.tool];
    let r;
    try {
      r = fn ? await fn(step.params || {}) : { ok: false, note: `未知操作：${step.tool}` };
    } catch (e) {
      r = { ok: false, note: '失败（' + (e && e.message ? e.message : String(e)) + ')' };
    }
    const note = r.note || (r.ok ? '完成' : '跳过');
    if (hooks.onStepState) hooks.onStepState(step.id, r.ok ? 'done' : 'error', note);
    results.push({ tool: step.tool, label: step.label || step.tool, ok: r.ok, note, data: r.data || {} });
  }
  const observation = observationFromResults(results);
  if (hooks.onObservation) hooks.onObservation(observation);
  return observation;
}

// ── Stage 3 · ANSWER：基于 observation 出结论初稿（可带 reviewFeedback 修订）──
export async function answer(ctx, hooks, observation, reviewFeedback = '') {
  const messages = [{ role: 'user', content: ctx.question }];
  let draft = '';
  await streamChat(messages, ctx.context,
    (tok) => { draft += tok; if (hooks.onDraft) hooks.onDraft(tok); },
    (err) => { throw new Error(err); },
    {
      phase: 'answer', observation, reviewFeedback, signal: ctx.signal,
      onReason: (t) => { hooks.onReason && hooks.onReason(t); },
    });
  return draft;
}

// ── Stage 4 · REVIEW：Flash 审查 draft → {pass, checks[], revise_hints} ──
export async function review(ctx, hooks, draft, observation) {
  const messages = [{ role: 'user', content: ctx.question }];
  const result = await reviewChat(messages, ctx.context, draft, observation);
  if (hooks.onReview) hooks.onReview(result);
  return result || { pass: true, checks: [], revise_hints: '' };
}
