// ═══ stages.js — Agent Loop 阶段（agentStep / diagnoseStep / optimizeStep / finalStep / deliberateStep）═══
// 阶段：agentStep（ReAct 每轮 reasoning + {thought,action}）/ diagnoseStep（问题理解卡）/ optimizeStep（NL 优化）
//      / finalStep（草稿 markdown）/ deliberateStep（Pro 研判·执行前）。
// ctx.model = 'pro' | 'flash'（思考深度开关，后端别名解析到 V4 真实 ID）。
// CB-09 D022：删旧 reviewStep/reviseStep（LLM 审查+重写 5-15s·假阳性高）→ 质量防线移至 harness.applyQualityDefense（代码·不调 LLM·<20ms）。
import { streamChat, streamFcDiagnose } from './api.js';
import { DOMAIN_KW } from './emc-patterns.js';   // CB-10 分歧2 词表集中

/** 入参别名规整：模型常把 invert 写成 inverse、as 写成 output_layer、radius_m 写成 radius，
 *  导致执行报错→空转→退化为叙述。此处统一规整为各工具的规范入参名，模型怎么写都能执行。
 *  仅收编实测出现的漂移别名，保守不过度映射（避免误伤合法字段）。 */
/** 通用参数别名（所有工具生效）。radius_meters/buffer_radius/distance→radius_m 留此（皆 buffer 语义，不冲突 density 的 radius）。
 *  `radius→radius_m` 曾在此全局生效→误伤 density（规范名即 radius，被改名后丢失）·CB-04 P1b 移到 _TOOL_ALIAS.buffer。 */
const _PARAM_ALIAS = {
  inverse: 'invert', output_layer: 'as', output: 'as', layer_name: 'as', named: 'as', name: 'as',
  radius_meters: 'radius_m', buffer_radius: 'radius_m', distance: 'radius_m',
  value: 'value_col', column: 'value_col', field_name: 'field',
  top: 'top_n', limit: 'top_n', n: 'top_n',
  // P1 扩（实测漂移别名；保守映射，避跨工具冲突——where/filter 不映射：extract_feature 用 where、其余用 pre_filter）
  point: 'center', center_point: 'center',
  zone: 'boundary', region: 'boundary',
  regions: 'boundaries', areas: 'boundaries',
  sort: 'by', sort_by: 'by', criteria: 'by',
  target_layer: 'target', target_poi: 'target',
  mode: 'how',
};
/** 工具专属别名（仅对该 tool 生效·CB-04 治 P1b）。key = tool name（SKILL_DEFS[*].tool / harness 传 def.tool）。 */
const _TOOL_ALIAS = {
  buffer: { radius: 'radius_m' },          // buffer 规范名 radius_m；Flash 填 radius → 映射（不波及 density）
  density: { bandwidth_m: 'radius', cell_size_m: 'cell_size', value_col: 'weightField' },  // CB-04 P1a：旧 prompt 漂移别名收编
};
export function normalizeParams(name, params) {
  if (!params || typeof params !== 'object') return {};
  const alias = { ..._PARAM_ALIAS, ...(_TOOL_ALIAS[name] || {}) };   // 通用 + 工具专属（CB-04 按工具区分·治 P1b 全局 radius→radius_m 误伤 density）
  const out = {};
  for (const k of Object.keys(params)) {
    const canon = alias[k] || k;
    out[canon] = params[k];
  }
  return out;
}

/** P1 技能槽位镜像（前端校验用，与后端 ai_qa/paradigm.py TEMPLATE_REGISTRY 的 tool/category/required_slots/optional_defaults 同步）。
 *  仿 field_dictionary 两份字典模式：改后端必同步此处。仅校验/填默认所需字段，不含 voice/triggers（那些只进 prompt）。 */
export const SKILL_DEFS = {
  concept:  { tool: null,          category: 'concept',  required_slots: [],                     optional_defaults: {} },
  density:  { tool: 'density',     category: 'single',   required_slots: [],                     optional_defaults: { mode: '2d', radius: 300, weightField: 'emotion_intensity', cell_size: 600, polarity: 'overall' } },
  // 承重（数据可见纪律）：rank/buffer/clip/zonal 不硬默认 layer——该默认经 validateParams 合并后绕过
  // resolvePointLayer 的 visible 过滤，致"只传 L1·T1 却跑 L2"（5.92 Track 1 核心保证漏）。改走可见点层选源（同 density）。
  rank:     { tool: 'rank',        category: 'single',   required_slots: [],                     optional_defaults: { by: 'worst', top_n: 5 } },
  buffer:   { tool: 'buffer',      category: 'single',   required_slots: ['center'],              optional_defaults: { radius_m: 500, agg_cols: ['score'] } },
  lookup_place: { tool: 'lookup_place', category: 'single', required_slots: [],                    optional_defaults: {} },   // CB-15 P1：查地点（q 或坐标）
  clip:     { tool: 'clip',        category: 'single',   required_slots: ['range'],               optional_defaults: {} },
  overlay:  { tool: 'overlay',     category: 'single',   required_slots: ['layer_a', 'layer_b'],  optional_defaults: { how: 'intersection' } },
  zonal:           { tool: 'zonal_stats',     category: 'single', required_slots: ['boundary'],          optional_defaults: { agg_cols: ['score'] } },
  compare:         { tool: 'compare_regions', category: 'single', required_slots: ['boundaries'],        optional_defaults: {} },
  extract_feature: { tool: 'extract_feature', category: 'single', required_slots: ['layer'],             optional_defaults: {} },
  area_stats:      { tool: 'area_stats',      category: 'single', required_slots: ['boundary'],          optional_defaults: {} },
  merge:           { tool: 'merge',           category: 'single', required_slots: [],                     optional_defaults: {} },   // CB-11：boundary|layers 二选一（one-of·tools.js guard 校验）
  nearest:         { tool: 'nearest',         category: 'single', required_slots: ['target'],            optional_defaults: { k: 1 } },
  hotspot:         { tool: 'hotspot',         category: 'single', required_slots: [],                    optional_defaults: { value_col: 'score' } },
  filter_attr:     { tool: 'filter_attr',     category: 'single', required_slots: ['pre_filter'],        optional_defaults: {} },
  multi:    { tool: null,          category: 'multi',    required_slots: [],                     optional_defaults: {} },
  unknown:  { tool: null,          category: 'unknown',  required_slots: [],                     optional_defaults: {} },
};

/** E1 多步链注册表（纯前端·chain_id 由 harness _deriveChainId 派生·不进 diagnose prompt·非 Flash 选）。
 *  标准 multi 链走 runChainPath（0 中间 LLM 轮·确定性执行）·治 C3 多步超时（INT-008~017）。
 *  steps 的 params 模板：{占位} 由 runChainPath._resolveChainParams 从 diagnose.params/问句填；
 *  $n 前序产物引用（tools.js ref 自动解析·addResultLayer 已推 _stepResults）。
 *  list 顺序 = _deriveChainId 匹配优先级（先具体后泛·同 B_TRACK_PARADIGM 范式）。 */
export const CHAIN_REGISTRY = [
  { chain_id: 'extract_overlay', name: '区内某类用地',
    triggers: [/区.{0,6}(的|内)?.{0,8}用地/, /用地.{0,4}里/],
    steps: [
      { tool: 'extract_feature', params: { layer: 'admin_district', where: '{question}' } },
      { tool: 'overlay', params: { layer_a: '$1', layer_b: '{land}' } },
    ] },
  { chain_id: 'clip_density', name: '范围密度',
    // CB-12（glm/Codex）：触发器放宽——加「裁剪…热力/密度」+「先/再/然后…热力/密度」顺序模式（原触发器间距 ≤4 字·不匹配"先裁剪…再生成热力图"）
    triggers: [/范围.{0,4}密度/, /区.{0,4}(热力|密度分布|分布)/, /(?:裁|剪裁|裁剪).{0,20}(热力|密度|分布)/, /(?:先|然后|再|接着).{0,15}(热力|密度)/],
    steps: [
      { tool: 'clip', params: { range: '{boundary}' } },
      { tool: 'density', params: { layer: '$1' } },
    ] },
];

/** P1 单技能路径参数校验：按 SKILL_DEFS[skill].required_slots 查缺槽、optional_defaults 补默认（用户值覆盖默认）。
 *  返 {ok, missing:[...], params}。镜像 tools.js 各工具 guard 范式——缺不可默认槽→harness 走 EXIT_GAP 诚实兜底（不赌博自纠）。 */
export function validateParams(skill, params) {
  const def = SKILL_DEFS[skill];
  const merged = { ...((def && def.optional_defaults) || {}), ...(params || {}) };
  // CB-09 DeepSeek 微调3：density mode='3d'（grid）时 radius 无意义·合并后剔除（治 LLM 锚定 300m 致矛盾结论）
  if (skill === 'density' && merged.mode === '3d') delete merged.radius;
  const missing = ((def && def.required_slots) || []).filter((k) => merged[k] == null || merged[k] === '');
  return { ok: !missing.length, missing, params: merged };
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
    template: (() => {
      const _t = (typeof obj.template === 'string' && obj.template) ? obj.template.trim().toLowerCase() : 'unknown';
      return SKILL_DEFS[_t] ? _t : 'unknown';   // 非 SKILL 模板归一 unknown（路由跳过落 while-loop；Flash gate 计为 miss）
    })(),
    params: (obj.params && typeof obj.params === 'object' && !Array.isArray(obj.params)) ? obj.params : {},
    chain: (() => {   // CB-09 D009+D012（5.237）Phase C：Pro 产的复合链 {name,steps:[{tool,params}]}·runChainPath 动态消费
      const ch = obj.chain;
      if (!ch || !Array.isArray(ch.steps)) return null;
      // 合法性校验：step.tool ∈ SKILL_DEFS + params 对象·过滤无效步·<2 有效步→null（落 _deriveChainId/while-loop）
      const valid = ch.steps.filter((s) => s && typeof s.tool === 'string' && SKILL_DEFS[s.tool]
        && (!s.params || typeof s.params === 'object'));
      return valid.length >= 2 ? { name: ch.name || '复合链', steps: valid } : null;
    })(),
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
    if (obj && (obj.scale || obj.domain_lens || obj.data_plan || obj.template)) return normalizeCard(obj);
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
      model: ctx.model, domainLens: ctx.domainLens,
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
      layerMeta: ctx.layerMeta || null,   // CB-09 5.242：{has_point,has_polygon} 喂 select_candidates 数据感知过滤
      onReason: (t) => { hooks.onReason && hooks.onReason(t, 0); },
    });
  return parseDiagnoseCard(acc.token);   // null = 解析失败（harness 降级，不抛）
}

/** v2 function calling 诊断（5.243·D041）：单次 LLM + function calling·非流式 JSON。
 *  替代旧 diagnoseStep（三阶段 SSE + select_candidates + FILL_CARD/PLAN）。
 *  返兼容 orchestrate 的 diagnose 对象——经 _normalizeFcDiagnose 补全为 normalizeCard 等价结构。
 *  - template = skill name（从 tool name 反映射·治 zonal_stats→zonal / compare_regions→compare）
 *  - params = JSON.parse(tool_calls[0].function.arguments)
 *  - plans = content 字段的 plans[] JSON（CPD 素材·rank=2+）
 *  - 补全 data_plan/domain_lens/scale/outlet/method 等（默认值·兼容下游消费者）
 *  失败（网络/无 tool_calls/解析错误）→ 返 { degraded:true }·harness 降级处理 */
// tool name → skill name 反映射（contracts 中 tool≠skill 的两个）
const _TOOL_TO_SKILL = { zonal_stats: 'zonal', compare_regions: 'compare' };

export async function fcDiagnoseStep(ctx, hooks) {
  const messages = [...(ctx.history || []), { role: 'user', content: ctx.question }];
  if (hooks.onReason) hooks.onReason('诊断中…', 0);   // Hotfix R2 S7：触发 reason 区·FC reason 流式填充
  // AbortController 用户取消联动；超时由 streamFcDiagnose 内部管（12s·含 reason 生成·略宽于旧 9s 非流式）
  const _ac = new AbortController();
  const _timer = setTimeout(() => _ac.abort(new Error('FC 单轮超时(12s)')), 12000);
  // 用户取消信号联动
  if (ctx.signal) {
    if (ctx.signal.aborted) _ac.abort();
    else ctx.signal.addEventListener('abort', () => _ac.abort(), { once: true });
  }
  try {
    // Hotfix R2 S7：FC 流式——streamFcDiagnose 消费 SSE·hooks.onReason 渐进显示诊断思考（不再"卡住"）
    const data = await streamFcDiagnose(messages, ctx.context || '', hooks.onReason, { signal: _ac.signal, timeout: 12000 });
    // 5c：更新用量统计
    if (data.usage && typeof window !== 'undefined') {
      try { window._emcLastUsage = data.usage; } catch (_) { /* 观测·失败不阻塞 */ }
    }
    const tc = data.tool_calls && data.tool_calls[0];
    if (!tc || !tc.function) {
      console.warn('[FC] 无 tool_calls');
      return { degraded: true, _fc: true, _fcError: 'no_tool_calls' };
    }
    // 解析 arguments（JSON 字符串 → 对象）
    let params = {};
    try {
      params = JSON.parse(tc.function.arguments || '{}');
    } catch (e) {
      console.warn('[FC] arguments 解析失败:', tc.function.arguments);
      return { degraded: true, _fc: true, _fcError: 'arguments_parse_fail' };
    }
    // 解析 plans[]（content 字段·容错 D067）
    let plans = [];
    if (data.plans) { plans = _parsePlans(data.plans); }
    // ISSUE 1 修复：tool name → skill name 反映射
    const toolName = tc.function.name;
    const skillName = _TOOL_TO_SKILL[toolName] || toolName;
    // CB-09 D057 修订：解析所有 tool_calls（不再只取[0]）供 orchestrator 顺序执行
    const _allToolCalls = (data.tool_calls || []).map((t) => {
      let _p = {};
      try { _p = JSON.parse((t.function && t.function.arguments) || '{}'); } catch (_) {}
      return { name: t.function && t.function.name, params: _p };
    }).filter((t) => t.name);
    console.log('[FC] all tool_calls:', _allToolCalls.map((t) => t.name).join(' → '));
    // v3 C2/C3 修复：补全为 normalizeCard 等价结构 + data gate + domain_lens A+B
    const diag = _normalizeFcDiagnose(skillName, params, plans, toolName, ctx.question, ctx.layerMeta, data.plans);
    diag._allToolCalls = _allToolCalls;
    return diag;
  } catch (e) {
    const aborted = e && e.name === 'AbortError';
    console.warn('[FC] 异常:', aborted ? '用户取消/超时' : String(e));
    return { degraded: true, _fc: true, _fcError: aborted ? 'aborted' : String(e) };
  } finally {
    clearTimeout(_timer);   // 5b：清理 timeout
  }
}

/** v3 C2/C3 + G1 修复：FC diagnose 补全为 normalizeCard 等价结构 + 数据 gate + domain_lens A+B + 尺度判定。
 *  C2：工具需点层但 ctx.layerMeta.has_point=false → strategy='request_upload'（治 5.242 回归）。
 *  C3：domain_lens A+B 混合（先 parse FC content 的 [domain_lens:xxx]·空则关键词推导兜底）。
 *  G1（glm组 修正）：去三字段硬编码（scale:'macro'/decision_type:'操作'/outlet:'生成图层'）——"一竿子插到底"根因。
 *      scale 从 FC content [scale:xxx] 解析（A 部·router build_fc_sys_prompt 已教）→ 词法兜底（B 部）→ 默认 macro 作最后防线。 */
function _normalizeFcDiagnose(skillName, params, plans, toolName, question, layerMeta, fcContent) {
  const _EMOTION_TOOLS = new Set(['zonal_stats', 'rank', 'density', 'hotspot']);
  const intent = _EMOTION_TOOLS.has(toolName) ? 'emotion_analysis' : 'gis_operation';
  // v3 C2：执行前 data gate——工具需点层但无点层 → request_upload（非硬跑失败·治 5.242 回归）
  const _NEEDS_POINT = /^(density|hotspot|rank|zonal_stats|clip|buffer|nearest)$/.test(toolName);   // v3.1 P1-1：补 zonal_stats（SCAN 发现·需点层聚合）
  const _noPoint = layerMeta && layerMeta.has_point === false;
  const _strategy = (_NEEDS_POINT && _noPoint) ? 'request_upload' : 'ready';
  // v3 C3：domain_lens A+B 混合
  const domain_lens = _deriveDomainLens(question || '', fcContent || '');
  // G1：scale 三源解析（A 部标签 → B 部词法 → 默认 macro 最后防线）
  const scale = _deriveScale(question || '', fcContent || '');
  // G1：outlet 随 scale+intent 差异化（宏观=结构性分布结论·中微观=归因排序·微观=落点·GIS=生成图层）
  const outlet = intent === 'emotion_analysis'
    ? (scale === 'micro' ? '地图定位' : (scale === 'meso' ? '报告结论' : '结构性分布结论'))
    : '生成图层';
  // G1：decision_type 按意图派生（情绪分析→评价·纯 GIS→操作）
  const decision_type = intent === 'emotion_analysis' ? '评价' : '操作';
  return {
    template: skillName,
    params,
    plans,
    degraded: false,
    intent,
    _fc: true,
    domain_lens,                  // v3 C3：A+B 混合推导（非恒空 []）
    scale,
    decision_type,
    outlet,
    data_plan: {
      needed: [],
      available: [],
      gap: _strategy === 'request_upload' ? ['情绪点数据'] : [],
      strategy: _strategy,        // v3 C2：数据不匹配→request_upload（非恒 ready）
    },
    method: [toolName + '()'],
  };
}

/** G1：尺度判定三源解析（A 部标签 → B 部词法 → 默认 macro 最后防线）。
 *  A：parse FC content [scale:xxx]（router build_fc_sys_prompt 指令产·仿 domain_lens A 部模式）。
 *  B：A 空 → 词法兜底（分布/整体/覆盖→macro；哪区最差/原因/归因→meso；街/点/小区→micro）。
 *  兜底失败才落默认 macro（保留现状作为最后防线·与 glm组 论证一致·去硬编码最坏情况=与旧行为一致无回归）。 */
export function _deriveScale(question, fcContent) {
  if (fcContent) {
    const m = String(fcContent).match(/\[scale:(macro|meso|micro)\]/);
    if (m) return m[1];
  }
  const q = String(question || '');
  if (/(分布|整体|全域|覆盖|大致|总体|哪些地方)/.test(q)) return 'macro';
  if (/(哪.*最差|哪里.*最差|原因|为什么|归因|排序|哪个区域|哪几个区|对比|比较)/.test(q)) return 'meso';
  if (/(这条街|这个点|这个小区|哪个点位|公园里|点位|附近哪)/.test(q)) return 'micro';
  return 'macro';   // 最后防线（与旧硬编码一致·无回归）
}

/** v3 C3：domain_lens A+B 混合推导。
 *  A：先 parse FC content 里的 [domain_lens:xxx] 标签（LLM 自主判领域·router system prompt 指令产）。
 *  B：A 空（LLM 常不产 content·R2）→ 关键词推导兜底（确定性·不依赖 LLM）。
 *  A+B 都空 → 默认 urban_renewal（情绪分析主场景）或不输出。 */
function _deriveDomainLens(question, fcContent) {
  // A：parse FC content [domain_lens:xxx]
  if (fcContent) {
    const m = String(fcContent).match(/\[domain_lens:(urban_planning|urban_renewal|urban_operation|urban_governance)\]/);
    if (m) return [m[1]];
  }
  // B：关键词推导兜底（词表集中 emc-patterns.DOMAIN_KW·CB-10 分歧2）
  const hits = [];
  for (const [domain, kws] of Object.entries(DOMAIN_KW)) {
    if (kws.some((kw) => question.includes(kw))) { hits.push(domain); break; }   // 取首个命中·最多 1 个
  }
  return hits.length ? hits : [];   // v3.1 P2-4：不硬填默认（空更诚实·下游处理空 domain_lens）
}

/** v2 plans[] 容错解析（D067）：JSON.parse + 字段校验·解析失败=空 plans·不崩溃。 */
function _parsePlans(content) {
  if (!content) return [];
  const _clean = String(content).replace(/\[domain_lens:[\w]+\]\s*/g, '').trim();
  try {
    const parsed = JSON.parse(_clean);
    const arr = Array.isArray(parsed) ? parsed : (parsed.plans || []);
    if (!Array.isArray(arr)) return [];
    return arr.filter((p) => p && typeof p.rank === 'number' && p.tool).map((p) => ({
      rank: p.rank,
      label: String(p.label || p.tool),
      tool: String(p.tool),
      params: p.params || {},
      confidence: ['high', 'medium', 'low'].includes(p.confidence) ? p.confidence : 'medium',
      rationale: String(p.rationale || ''),
    }));
  } catch (e) {
    return [];
  }
}

/** 5.215 Prompt 优化（Flash 流式·把用户 NL 优化成具体/实操/逻辑清晰 prompt·不增维度·梳理已有要素）。 */
export async function optimizeStep(ctx, hooks, userInput) {
  const messages = [{ role: 'user', content: userInput }];
  let acc = '';
  await streamChat(messages, ctx.context,
    (tok) => { acc += tok; if (hooks.onOptimize) hooks.onOptimize(acc); },
    (err) => { throw new Error(err); },
    { phase: 'optimize', signal: ctx.signal, model: 'flash' });
  return acc;
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
      model: (ctx.answerModel === 'pro' ? 'flash' : (ctx.answerModel || 'flash')), domainLens: ctx.domainLens,   // CB-12：pro 停用·最终守卫强制 flash（防 answerModel 残留）
      onReason: (t) => { hooks.onReason && hooks.onReason(t, 0); },
    });
  return final;
}

/** deliberateStep（Pro 研判·执行前·Step 3·用户工作流阶段 G+H）：Pro 基于用户问题 + diagnose(template/method) + 将执行参数，
 *  研判"工具+参数是否真能回答用户真实意图 + 数据局限/口径注意事项"。返研判文本（harness 注入 finalStep context，提升结论质量）。
 *  返 null = 空/失败（harness try/catch 兜底，不阻塞执行）。承重：不改 diagnose prompt（保 eval）；新 prompt 不破 eval（eval 只测 diagnose 路由）。 */
export async function deliberateStep(ctx, diagnose, params) {
  const messages = [
    { role: 'system', content: '你是情绪地图的研判员。基于用户问题、已诊断的意图（template/method）、将执行的参数、当前已加载图层，研判：(1) 这个工具+参数是否真能回答用户的真实意图？(2) 有无数据局限或口径（统计范围）需在结论中标注？简要输出 1-2 句研判结论，供最终回答参考。不要重复执行工具，不要编造数据或具体数字。' },
    { role: 'user', content: `问题：${ctx.question || ''}\n诊断：template=${(diagnose && diagnose.template) || '?'}，method=${(((diagnose && diagnose.method) || []).join(' → ')) || '?'}\n将执行参数：${JSON.stringify(params || {})}` },
  ];
  let out = '';
  await streamChat(messages, ctx.context,
    (tok) => { out += tok; },
    (err) => { throw new Error(err); },
    { phase: 'deliberate', signal: ctx.signal, model: ctx.model, domainLens: ctx.domainLens });
  return out.trim() || null;
}
