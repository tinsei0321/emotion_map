// ═══ stages.js — Agent Loop 阶段（agentStep / finalStep / reviewStep / reviseStep）═══
// 四阶段：agentStep（ReAct 每轮 reasoning + {thought,action}）/ finalStep（草稿 markdown）
//       / reviewStep（Flash 审查员 JSON）/ reviseStep（审查未过重写 markdown）。
// ctx.model = 'pro' | 'flash'（思考深度开关，后端别名解析到 V4 真实 ID）；review 固定 flash。
import { streamChat } from './api.js';

/** 入参别名规整：模型常把 invert 写成 inverse、as 写成 output_layer、radius_m 写成 radius，
 *  导致执行报错→空转→退化为叙述。此处统一规整为各工具的规范入参名，模型怎么写都能执行。
 *  仅收编实测出现的漂移别名，保守不过度映射（避免误伤合法字段）。 */
const _PARAM_ALIAS = {
  inverse: 'invert', output_layer: 'as', output: 'as', layer_name: 'as', named: 'as',
  radius: 'radius_m', radius_meters: 'radius_m', buffer_radius: 'radius_m',
  value: 'value_col', column: 'value_col', field_name: 'field',
  top: 'top_n', limit: 'top_n', n: 'top_n',
};
function normalizeParams(name, params) {
  if (!params || typeof params !== 'object') return {};
  const out = {};
  for (const k of Object.keys(params)) {
    const canon = _PARAM_ALIAS[k] || k;
    out[canon] = params[k];
  }
  return out;
}

/** 容错解析 agent_step 的 {thought, action}。
 *  返回值三态：
 *    { thought, action:{type:'tool'|'answer'|'ask_user', name?, params?, question?, options?} }  — 正常
 *    { narrated:true, text }   — 模型只写了说明文字没给动作（harness 走修复通道，绝不裸输）
 *    null                       — 输入为空
 *  抗格式漂移：兼容多种 DeepSeek 实测漂移 schema，统一归一为 {type:'tool',name,params}。
 *  这是「代码块泄漏」的根治点——解析不再返畸形 action 致 8 轮空转→onDegraded 裸输。 */
export function parseAgentStep(raw) {
  if (!raw) return null;
  let s = raw;
  // 1. strip markdown fence ```json ... ``` / ``` ... ```
  const fence = s.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fence) s = fence[1];
  // 2. 截取首末花括号
  const start = s.indexOf('{');
  const end = s.lastIndexOf('}');
  if (start < 0 || end < 0 || end <= start) return { narrated: true, text: raw };   // 无 JSON = 纯叙述
  let candidate = s.slice(start, end + 1);
  // 3. 去尾逗号（}, ] 前的逗号）
  candidate = candidate.replace(/,(\s*[}\]])/g, '$1');

  let obj = null;
  try {
    obj = JSON.parse(candidate);
  } catch (_) {
    // 4. 二次：正则提取 action 子对象（容错模型加前后解释/嵌套）
    const am = candidate.match(/"action"\s*:\s*(\{[\s\S]*?\})\s*[,}]/);
    if (am) {
      try {
        const action = JSON.parse(am[1]);
        const tm = candidate.match(/"thought"\s*:\s*"((?:[^"\\]|\\.)*)"/);
        obj = { thought: tm ? tm[1] : '', action };
      } catch (__) { obj = null; }
    }
  }
  if (!obj) return { narrated: true, text: raw };

  const thought = obj.thought || obj.reasoning || '';

  // ── 归一化 action：兼容漂移 schema ────────────────────────────
  let action = obj.action;
  // drift: action 是字符串（{action:"query_layers", arguments:{}}）
  if (typeof action === 'string') {
    if (action === 'answer') return { thought, action: { type: 'answer' } };
    action = { type: 'tool', name: action, params: obj.arguments || obj.params || obj.parameters || {} };
  }
  // drift: {tool:"x", params|parameters|arguments}
  if (!action && obj.tool) action = { type: 'tool', name: obj.tool, params: obj.params || obj.parameters || obj.arguments || {} };
  if (!action && obj.tool_name) action = { type: 'tool', name: obj.tool_name, params: obj.params || obj.parameters || {} };
  // drift: 顶层本身就是 action（{type:"tool"|"answer"|"ask_user", ...}）
  if (!action && (obj.type === 'tool' || obj.type === 'answer' || obj.type === 'ask_user')) action = obj;
  // drift: 顶层裸 ask_user（{ask_user:{question,options}} 无 action 外层）—— 收编，防被下方 !action 叙述兜底吞掉
  if (!action && obj.ask_user) action = { type: 'ask_user', ...(typeof obj.ask_user === 'object' && obj.ask_user ? obj.ask_user : {}) };
  if (!action) return { narrated: true, text: raw };

  // ── answer 识别（放宽）──────────────────────────────────────
  const isAnswer = action.type === 'answer'
    || action.name === 'answer' || action.tool === 'answer'
    || obj.answer === true;
  if (isAnswer) return { thought, action: { type: 'answer' } };

  // ── ask_user 识别（P1 主动问澄清：范围/时点/domain 模糊时问一句，带 options 胶囊）──
  const _isAsk = action.type === 'ask_user'
    || action.name === 'ask_user' || action.tool === 'ask_user'
    || !!obj.ask_user || obj.type === 'ask_user';
  if (_isAsk) {
    const _askObj = (typeof obj.ask_user === 'object' && obj.ask_user) || {};
    const _q = String(action.question || _askObj.question || '').trim() || '请补充一点信息，我接着分析';
    let _opts = action.options || _askObj.options || [];
    if (typeof _opts === 'string') _opts = _opts.split(/[|,，、]/).map((s) => s.trim()).filter(Boolean);
    if (!Array.isArray(_opts)) _opts = [];
    const options = _opts.map((o) => typeof o === 'string' ? o : (o && (o.label || o.text || o.name || o.value)))   // 兼容 {label/value} 对象 schema
      .filter((o) => typeof o === 'string' && o.trim()).map((o) => o.trim()).slice(0, 6);
    return { thought, action: { type: 'ask_user', question: _q, options } };
  }

  // ── tool 归一 ────────────────────────────────────────────────
  const name = action.name || action.tool || action.tool_name;
  const params = normalizeParams(name, action.params || action.parameters || action.arguments || {});
  if (!name) return { narrated: true, text: raw };
  return { thought, action: { type: 'tool', name, params } };
}

/** 归一化 diagnose 卡（补默认值，防字段缺失）。 */
function normalizeCard(obj) {
  const dp = obj.data_plan || {};
  const dom = Array.isArray(obj.domain_lens) ? obj.domain_lens : (obj.domain_lens ? [obj.domain_lens] : []);
  // intent 仲裁（覆盖 flash 模型的不一致标注）：以 outlet/decision_type 强信号为准，不盲信 intent 字段。
  // 曾出现 intent=general 却同时填 outlet=生成图层/decision_type=操作/method=extract→clip 的自相矛盾卡——
  // 旧逻辑只补空 intent、不纠错标，致 harness 误走 general 短路→无工具半截回答（"回答一半停住"根因）。
  const looksOperation = obj.outlet === '生成图层' || obj.outlet === '执行操作' || obj.decision_type === '操作';
  const looksGeneral = obj.decision_type === '通用问答' || obj.decision_type === '定义'
    || (dom.length > 0 && dom.every((d) => d === 'general'));
  let intent;
  if (looksOperation) intent = 'gis_operation';          // 操作出口/决策=强信号，压倒 general 误标
  else if (looksGeneral) intent = 'general';
  else {                                                  // 信号不明：采信模型 stated intent，否则情绪分析兜底
    const stated = String(obj.intent || '').toLowerCase();
    intent = (stated === 'gis_operation' || stated === 'general') ? stated : 'emotion_analysis';
  }
  return {
    intent,
    domain_lens: dom,
    scale: obj.scale || 'macro',
    decision_type: obj.decision_type || '',
    outlet: obj.outlet || '',
    data_plan: {
      needed: dp.needed || [], available: dp.available || [], gap: dp.gap || [],
      strategy: dp.strategy || 'ready',
    },
    method: Array.isArray(obj.method) ? obj.method : (obj.method ? [obj.method] : []),
  };
}

/** 容错解析 diagnose 的 6 字段问题理解卡；失败返回 null（harness 降级，不阻塞）。 */
export function parseDiagnoseCard(raw) {
  if (!raw) return null;
  let s = raw;
  const fence = s.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fence) s = fence[1];
  const start = s.indexOf('{');
  const end = s.lastIndexOf('}');
  if (start < 0 || end < 0 || end <= start) return null;
  let candidate = s.slice(start, end + 1);
  candidate = candidate.replace(/,(\s*[}\]])/g, '$1');
  try {
    const obj = JSON.parse(candidate);
    if (obj && (obj.scale || obj.domain_lens || obj.data_plan)) return normalizeCard(obj);
  } catch (_) { /* fall through */ }
  // 兜底：正则抠 scale/strategy（模型把卡裹在解释里时），尽量救回 strategy 驱动数据自检
  const scale = candidate.match(/"scale"\s*:\s*"(\w+)"/);
  const strat = candidate.match(/"strategy"\s*:\s*"(\w+)"/);
  if (scale || strat) {
    return normalizeCard({ scale: scale ? scale[1] : undefined, data_plan: { strategy: strat ? strat[1] : 'ready' } });
  }
  return null;
}

/** Agent Loop 一轮：流式 reasoning + content({thought,action} JSON)。null=解析失败降级。 */
export async function agentStep(ctx, hooks, round, toolHistory) {
  const messages = [...(ctx.history || []), { role: 'user', content: ctx.question }];
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

/** 问题诊断（DIAGNOSE 认知前置步）：流式 reasoning + content(JSON 卡)。null=解析失败降级。 */
export async function diagnoseStep(ctx, hooks) {
  const messages = [...(ctx.history || []), { role: 'user', content: ctx.question }];
  const acc = { token: '' };
  await streamChat(messages, ctx.context,
    (tok) => { acc.token += tok; },
    (err) => { throw new Error(err); },
    {
      phase: 'diagnose', signal: ctx.signal, model: 'flash',
      onReason: (t) => { hooks.onReason && hooks.onReason(t, 0); },
    });
  return parseDiagnoseCard(acc.token);   // null = 解析失败（harness 降级，不抛）
}

/** 草稿结论：基于 tool_history 流式出 markdown + [ref:]。 */
export async function finalStep(ctx, hooks, toolHistory) {
  const messages = [...(ctx.history || []), { role: 'user', content: ctx.question }];
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
  const messages = [...(ctx.history || []), { role: 'user', content: ctx.question }];
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
