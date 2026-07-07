// ═══ api.js — chat → 后端 /api/v1/chat（SSE 流式，agent loop）═══
// 两阶段：agent_step（每轮 reasoning + {thought,action} JSON）/ answer（最终结论 markdown）。
const BASE = '/api/v1';

/**
 * SSE 流式问答（agent_step / answer / revise 流式；review 单帧 JSON）。
 * @param opts {onReason, onReview, model, contextTokens, signal, phase, toolHistory, roundN, draft, reviewHints}
 */
export async function streamChat(messages, context, onToken, onError, opts = {}) {
  const { onReason, onReview, model, contextTokens, signal } = opts;
  const body = { messages, context };
  if (model) body.model = model;
  if (contextTokens && contextTokens.length) body.context_tokens = contextTokens;
  if (opts.phase) body.phase = opts.phase;
  if (opts.toolHistory) body.tool_history = opts.toolHistory;
  if (opts.roundN) body.round_n = opts.roundN;
  if (opts.draft) body.draft = opts.draft;
  if (opts.reviewHints) body.review_hints = opts.reviewHints;
  const r = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  });
  if (!r.ok) {
    let detail = `问答失败: ${r.status}`;
    try { const j = await r.json(); detail = j.detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  const reader = r.body.getReader();
  const dec = new TextDecoder();
  let buf = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf('\n\n')) >= 0) {
      const chunk = buf.slice(0, i);
      buf = buf.slice(i + 2);
      const line = chunk.split('\n').find((l) => l.startsWith('data:'));
      if (!line) continue;
      const data = line.slice(5).trim();
      if (data === '[DONE]') return;
      try {
        const obj = JSON.parse(data);
        if (obj.error) { if (onError) onError(obj.error); return; }
        if (obj.review !== undefined && onReview) { onReview(obj.review); return; }
        if (obj.reason && onReason) onReason(obj.reason);
        if (obj.token) onToken(obj.token);
      } catch (_) { /* skip malformed */ }
    }
  }
}
