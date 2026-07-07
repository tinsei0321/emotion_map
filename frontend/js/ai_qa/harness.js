// ═══ harness.js — Harness 编排器（STAGES 阶段注册表 + Review 闭环）═══
// 一次问答 = think → execute → answer(draft) → review → (fail 则 answer 重写一次) → 最终呈现。
// 形态无关、阶段可插拔：未来加 reflect（深闭环）/ RAG / 规则库，只需在 STAGES 插一项或在本流程加钩子。
import * as stages from './stages.js';

/**
 * 端到端编排一次问答。
 * @param ctx    {question, context(grounding), contextTokens, signal, enableReview}
 * @param hooks  渲染回调（panel.js 实现）：
 *   onReason(tok)            — Pro 思考链增量（think/answer 阶段）
 *   onFraming(text)          — 解题面板 STEP① 问题定性
 *   onMapping(text)          — 解题面板 STEP② 框架映射
 *   onPlan(steps[])          — STEP③ 路径规划 + 执行轨道
 *   onStepState(id,status,note) — 执行轨道逐步状态（running/done/error）
 *   onObservation(text)      — STEP④ 执行观察
 *   onDraft(tok)             — 结论初稿增量（markdown）
 *   onDraftReset()           — revise 前清空初稿区
 *   onReview(result)         — 审查结果 {pass,checks[],revise_hints}
 *   onRevise(round, hints)   — 修订标记
 *   onReviewError(msg)       — 审查失败（不阻塞）
 *   onDegraded(text)         — think 解析失败降级（当文字回答）
 *   onFinal(text, meta)      — 最终结论 + {revised, review}
 * @returns {Promise<{ok, degraded?, plan?, observation?, draft?, review?, revised?}>}
 */
export async function orchestrate(ctx, hooks = {}) {
  // ── Stage 1 · THINK ──
  const t = await stages.think(ctx, hooks);
  if (!t.ok) return { ok: false, degraded: true, text: t.raw };
  const { plan } = t;

  // ── Stage 2 · EXECUTE ──
  const observation = await stages.execute(ctx, hooks, plan);

  // ── Stage 3 · ANSWER（初稿）──
  let draft = await stages.answer(ctx, hooks, observation, '');

  // ── Stage 4 · REVIEW（+ Revise 最多 1 轮）──
  let reviewResult = null;
  let revised = false;
  if (ctx.enableReview !== false) {
    try {
      reviewResult = await stages.review(ctx, hooks, draft, observation);
      if (!reviewResult.pass && reviewResult.revise_hints) {
        revised = true;
        if (hooks.onRevise) hooks.onRevise(1, reviewResult.revise_hints);
        if (hooks.onDraftReset) hooks.onDraftReset();
        draft = await stages.answer(ctx, hooks, observation, reviewResult.revise_hints);
      }
    } catch (e) {
      if (hooks.onReviewError) hooks.onReviewError(e && e.message ? e.message : String(e));
    }
  }

  if (hooks.onFinal) hooks.onFinal(draft, { revised, review: reviewResult });
  return { ok: true, plan, observation, draft, review: reviewResult, revised };
}
