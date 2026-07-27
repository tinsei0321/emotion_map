// ═══ api.js — chat → 后端 /api/v1/chat（SSE 流式，agent loop）═══
// 两阶段：agent_step（每轮 reasoning + {thought,action} JSON）/ answer（最终结论 markdown）。
const BASE = '/api/v1';

/**
 * SSE 流式问答（diagnose / agent_step / answer / optimize 流式）。
 * @param opts {onReason, model, contextTokens, signal, phase, toolHistory, roundN, domainLens}
 */
let _lastUsage = null;
let _callCount = 0, _totalPrompt = 0, _totalCompletion = 0;
/** 最近一次流式的 usage（{prompt_tokens, completion_tokens, total_tokens}）；容量圆圈用。 */
export function getLastUsage() { return _lastUsage; }
/** 本次问答的 LLM 调用统计（用时/用量戳用）。send 开始时 resetCallStats()。 */
export function resetCallStats() { _callCount = 0; _totalPrompt = 0; _totalCompletion = 0; }
export function getCallStats() {
  const tot = _totalPrompt + _totalCompletion;
  return { calls: _callCount, prompt: _totalPrompt, completion: _totalCompletion, total: tot };
}

export async function streamChat(messages, context, onToken, onError, opts = {}) {
  _callCount++;
  const { onReason, model, contextTokens, signal } = opts;
  const body = { messages, context };
  if (model) body.model = model;
  if (contextTokens && contextTokens.length) body.context_tokens = contextTokens;
  if (opts.phase) body.phase = opts.phase;
  if (opts.toolHistory) body.tool_history = opts.toolHistory;
  if (opts.roundN) body.round_n = opts.roundN;
  if (opts.domainLens && opts.domainLens.length) body.domain_lens = opts.domainLens;
  if (opts.layerMeta) body.layer_meta = opts.layerMeta;   // CB-09 5.242：{has_point,has_polygon}→select_candidates 数据感知
  // CB-06 P0-B：per-call timeout（45s·慢轮 abort → harness P0-A 降级·治 Flash 过度思考卡死·最坏等 45s 非数十秒）
  const _timeout = 45000;   // CB-09 D019：finalStep 极瘦（17KB→0.9KB）后统一 45s（CB-07 Layer 2 升 60s 因 prompt 大·已不再需）
  const _ac = new AbortController();
  const _timer = setTimeout(() => _ac.abort(new Error(`LLM 单轮超时(${_timeout / 1000}s)`)), _timeout);
  if (signal) {
    if (signal.aborted) { clearTimeout(_timer); _ac.abort(signal.reason); }
    else signal.addEventListener('abort', () => { clearTimeout(_timer); _ac.abort(signal.reason); }, { once: true });
  }
  try {
    const r = await fetch(`${BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: _ac.signal,
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
          if (obj.usage) { _lastUsage = obj.usage; _totalPrompt += obj.usage.prompt_tokens || 0; _totalCompletion += obj.usage.completion_tokens || 0; if (opts.onUsage) opts.onUsage(obj.usage); }
          if (obj.reason && onReason) onReason(obj.reason);
          if (obj.token) onToken(obj.token.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, ''));   // 5.222 过滤控制符（DEL 等·治"删除符号"Bug 3）
        } catch (_) { /* skip malformed */ }
      }
    }
  } finally {
    clearTimeout(_timer);   // CB-06 P0-B：流式结束/出错/超时 都清 timer
  }
}
