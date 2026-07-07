// ═══ api.js — chat → 后端 /api/v1/chat（SSE 流式 think/answer + 非流式 review）═══
// 从 frontend/js/api.js 拆出（AI 问答独立子系统；非 AI 问答的 runGrid 等留原 api.js）。
// provider-agnostic：后端默认 DeepSeek Pro；换 provider 改后端 ai_qa/llm.py 一处。

const BASE = '/api/v1';

/**
 * SSE 流式问答（think / answer 阶段）。
 * @param messages  OpenAI 兼容消息数组
 * @param context   主窗口推送的 grounding 摘要
 * @param onToken   (tok) => void  正文增量（think 阶段=JSON content；answer 阶段=markdown 结论）
 * @param onError   (err) => void
 * @param opts      {onReason, model, contextTokens, signal, phase, observation, reviewFeedback}
 *                  onReason → Pro 思考链增量；phase='think'|'answer'。
 */
export async function streamChat(messages, context, onToken, onError, opts = {}) {
  const { onReason, model, contextTokens, signal } = opts;
  const body = { messages, context };
  if (model) body.model = model;
  if (contextTokens && contextTokens.length) body.context_tokens = contextTokens;
  if (opts.phase) body.phase = opts.phase;
  if (opts.observation) body.observation = opts.observation;
  if (opts.reviewFeedback) body.review_feedback = opts.reviewFeedback;
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
        if (obj.reason && onReason) onReason(obj.reason);   // Pro 思考链
        if (obj.token) onToken(obj.token);                  // 正文
      } catch (_) { /* skip malformed */ }
    }
  }
}

/**
 * 非流式审查（review 阶段，Flash json_mode）。
 * @returns {pass, checks[], revise_hints}
 */
export async function reviewChat(messages, context, draftAnswer, observation) {
  const r = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages, context,
      phase: 'review',
      draft_answer: draftAnswer || '',
      observation: observation || '',
    }),
  });
  if (!r.ok) {
    let detail = `审查失败: ${r.status}`;
    try { const j = await r.json(); detail = j.detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return r.json();
}
