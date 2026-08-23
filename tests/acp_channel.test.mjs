// S3 单测：ACP 事件通道 + mock 对端 + S4 引擎发射层（node 直跑·无浏览器依赖）
// 跑法：node tests/acp_channel.test.mjs
// 覆盖：① acp-channel 14 hooks → ACP 事件映射 + 过程/内容分层（process 10 / content 4）
//      ② mock 对端 wireToBus 适配器（wire schema 字段映射·provenance=synthesized）
//      ③ runAcpMockPeer 全剧本（诊断→工具→思考→正文→定稿·turn_id 贯穿）
//      ④ S4 引擎发射器 createEngineEmitter（wire 严格 schema 造型·toolcall 配对·bus 载荷向后兼容）
// 权威：frontend/js/ai_qa/acp-channel.js / acp-mock-peer.js / tests/acp_schema/schemas/*.schema.json
import { createAcpChannel, createEngineEmitter, isAcpChannel, ACP_FAMILY } from 'file:///D:/Github/emotion_map/frontend/js/ai_qa/acp-channel.js';
import { wireToBusAdapter, runAcpMockPeer, isAcpMockOn } from 'file:///D:/Github/emotion_map/frontend/js/ai_qa/acp-mock-peer.js';

let _fail = 0;
function ok(cond, msg) { if (!cond) { _fail++; console.error(`[FAIL] ${msg}`); } else { console.log(`[OK] ${msg}`); } }

// ═══ ① 14 hooks → 事件映射（emitter 路径·harness 零改动的翻译层）═══
{
  const { bus, emitter, turn_id } = createAcpChannel();
  const events = [];
  bus.on('*', (e) => events.push(e));

  // 模拟一轮 harness 调用序（diagnose → round → thought → action → observation → reason → final → struct → seal）
  emitter.onDiagnose({ template: 'zonal', intent: 'emotion_analysis' });
  emitter.onRoundStart(1);
  emitter.onThought('先看分布', 1);
  emitter.onAction({ type: 'tool', name: 'zonal_stats', params: { boundary: 'b1' } }, 1);
  emitter.onObservation('rows=5', 1);
  emitter.onReason('思考中', 1);
  emitter.onFinal('## 结论');
  emitter.onResultStruct({ insight: '观点' });
  emitter.onFinalDone('## 结论');
  emitter.onAskUser({ question: '哪个区？', options: ['西陵', '伍家岗'] }, 2);
  emitter.onOutletCard([{ kind: 'card' }]);
  emitter.onDefense({ fixes: [] });
  emitter.onDegraded('raw');
  emitter.onRound(1);

  const fam = (i) => events[i] && events[i].family;
  ok(events.length === 14, `14 次 hooks → 14 事件（实 ${events.length}）`);
  ok(fam(0) === 'turn' && events[0].phase === 'diagnose' && events[0].card.template === 'zonal', 'onDiagnose→turn.diagnose（card 保真）');
  ok(fam(1) === 'turn' && events[1].phase === 'round.start' && events[1].round === 1, 'onRoundStart→turn round.start');
  ok(fam(2) === 'tool.begin' && events[2].sub === 'thought', 'onThought→tool.begin.thought');
  ok(fam(3) === 'tool.begin' && events[3].sub === 'call' && events[3].name === 'zonal_stats' && events[3].action.type === 'tool', 'onAction→tool.begin.call（action 全量保真·type 不丢）');
  ok(fam(4) === 'tool.end' && events[4].observation === 'rows=5', 'onObservation→tool.end');
  ok(fam(5) === 'msg.delta' && events[5].kind === 'reason' && events[5].provenance === 'real', 'onReason→msg.delta reason·provenance=real');
  ok(fam(6) === 'msg.delta' && events[6].kind === 'content', 'onFinal→msg.delta content');
  ok(fam(7) === 'render' && events[7].kind === 'result.struct' && events[7].lane === 'content', 'onResultStruct→render 族·content lane（分层红线）');
  ok(fam(8) === 'turn' && events[8].verb === 'seal' && events[8].text === '## 结论', 'onFinalDone→turn.seal');
  ok(events[9].kind === 'ask_user' && events[9].lane === 'content', 'onAskUser→render 族（选项胶囊属渲染语义）');
  ok(events[10].kind === 'outlet.card' && events[11].kind === 'defense', 'onOutletCard/onDefense→render 族');
  ok(fam(12) === 'error' && events[12].kind === 'degraded', 'onDegraded→error.degraded');
  ok(fam(13) === 'turn' && events[13].phase === 'round.tick', 'onRound→turn round.tick（no-op 保留事件·防未来消费者）');
  ok(events.every((e) => e.turn_id === turn_id && e.ts > 0), 'turn_id 贯穿 + ts 信封');
  ok(events.filter((e) => e.lane === 'process').length === 10 && events.filter((e) => e.lane === 'content').length === 4, 'process 10 / content 4 分层计数（含 round.tick）');

  // 订阅异常不阻塞投递（契约级稳健性）
  const ch2 = createAcpChannel();
  ch2.bus.on('msg.delta', () => { throw new Error('boom'); });
  let delivered = false;
  ch2.bus.on('msg.delta', () => { delivered = true; });
  ch2.emitter.onFinal('x');
  ok(delivered, '订阅抛错不阻塞后续订阅者');
}

// ═══ ② wireToBus 适配器（wire schema 造型 → bus 载荷·S4/BrainAdapter 适配蓝本）═══
{
  // wire 镜像校验：必填字段/枚举/非空——与 tests/acp_schema/schemas/*.schema.json 逐字段对齐
  const WIRE_REQ = {
    'msg_delta': ['kind', 'delta', 'session_id', 'turn_id'],
    'tool_begin': ['toolcall_id', 'verb', 'session_id', 'turn_id'],
    'tool_end': ['toolcall_id', 'verb', 'session_id', 'turn_id'],
    'error': ['code', 'message', 'session_id'],
  };
  const wireOk = (family, w) => {
    for (const k of WIRE_REQ[family]) {
      const v = w[k];
      if (v === undefined || v === null || v === '') return false;
    }
    if (family === 'msg_delta' && !['reason', 'content'].includes(w.kind)) return false;
    if (family === 'msg_delta' && w.seq !== undefined && !Number.isInteger(w.seq)) return false;
    return true;
  };

  const wires = {
    msg_delta: { kind: 'reason', delta: '先查口径', session_id: 's1', turn_id: 't1', seq: 0 },
    msg_delta_bad_kind: { kind: 'thought', delta: 'x', session_id: 's1', turn_id: 't1' },
    msg_delta_bad_empty: { kind: 'reason', delta: '', session_id: 's1', turn_id: 't1' },
    tool_begin: { toolcall_id: 'tc1', verb: 'rag_query', session_id: 's1', turn_id: 't1', params_summary: 'query=更新' },
    tool_begin_bad: { toolcall_id: 'tc1', session_id: 's1', turn_id: 't1' },   // 缺 verb
    tool_end: { toolcall_id: 'tc1', verb: 'rag_query', session_id: 's1', turn_id: 't1', result_summary: 'rows=3' },
    error: { code: 'MOCK_X', message: '模拟错误', session_id: 's1', hint: '仅测试' },
  };
  ok(wireOk('msg_delta', wires.msg_delta) && wireOk('tool_begin', wires.tool_begin)
    && wireOk('tool_end', wires.tool_end) && wireOk('error', wires.error), 'wire 合法样例过镜像校验（四族必填字段齐）');
  ok(!wireOk('msg_delta', wires.msg_delta_bad_kind) && !wireOk('msg_delta', wires.msg_delta_bad_empty)
    && !wireOk('tool_begin', wires.tool_begin_bad), 'wire 坏样例被镜像校验拦下（kind 枚举/空串/缺 verb）');

  const { bus } = createAcpChannel();
  const got = [];
  bus.on('*', (e) => got.push(e));
  const w = wireToBusAdapter(bus, 's1', 't1');
  w.msgDelta(wires.msg_delta, 1);
  w.toolBegin(wires.tool_begin, 1);
  w.toolEnd(wires.tool_end, 1);
  w.error(wires.error);

  ok(got.length === 4, `适配器 4 族投递（实 ${got.length}）`);
  ok(got[0].family === 'msg.delta' && got[0].token === '先查口径' && got[0].kind === 'reason' && got[0].provenance === 'synthesized',
    'msgDelta：delta→token 映射 + provenance=synthesized');
  ok(got[1].family === 'tool.begin' && got[1].sub === 'call' && got[1].name === 'rag_query' && got[1].action.type === 'tool' && got[1].action.name === 'rag_query',
    'toolBegin：verb→name+action.name（渲染器可消费形）');
  ok(got[2].family === 'tool.end' && got[2].observation === 'rows=3', 'toolEnd：result_summary→observation');
  ok(got[3].family === 'error' && got[3].code === 'MOCK_X' && got[3].hint === '仅测试', 'error：code+hint 语义化');
  ok(got.every((e) => e.provenance === 'synthesized'), 'mock 事件全量 synthesized（诚实性红线）');

  // node 环境（无 window/location）mock 开关必须关——生产链路零副作用
  ok(!isAcpMockOn(), 'isAcpMockOn：非浏览器环境默认关');
}

// ═══ ③ runAcpMockPeer 全剧本（bus 直注·orchestrate 同形返回）═══
{
  const { bus, turn_id } = createAcpChannel();
  const events = [];
  bus.on('*', (e) => events.push(e));
  const res = await runAcpMockPeer({ bus, emitter: null, turn_id }, { question: '宜昌有多少城市更新项目？', signal: null });

  ok(res.exit === 'final' && res.diagnose && res.diagnose.rag === true && res.newLayerCount === 0, '返回 orchestrate 同形结果（exit/diagnose/newLayerCount）');
  const diag = events.find((e) => e.phase === 'diagnose');
  ok(!!diag && diag.card.intent === 'knowledge_qa', '剧本：diagnose 卡先行');
  const tb = events.filter((e) => e.family === 'tool.begin');
  ok(tb.some((e) => e.sub === 'thought') && tb.some((e) => e.name === 'rag_query'), '剧本：thought + rag_query 工具轮');
  ok(events.some((e) => e.family === 'tool.end' && /命中/.test(e.observation || '')), '剧本：tool_end 结果落 observation');
  const reasons = events.filter((e) => e.family === 'msg.delta' && e.kind === 'reason');
  const contents = events.filter((e) => e.family === 'msg.delta' && e.kind === 'content');
  ok(reasons.length >= 5 && contents.length >= 5, `剧本：reason/content 逐 token 流（${reasons.length}/${contents.length} 片）`);
  ok(events.every((e) => e.turn_id === turn_id), '剧本：turn_id 全程贯穿');
  const seal = events.find((e) => e.verb === 'seal');
  ok(!!seal && seal.text.includes('mock 对端'), '剧本：seal 定稿含 mock 标记');
  ok(events.some((e) => e.family === 'render' && e.kind === 'result.struct' && e.lane === 'content'), '剧本：result.struct 走 content lane（分层红线）');
  ok(events.filter((e) => e.lane === 'content').every((e) => e.family === 'render'), '分层：content lane 只承载 render 族');
}

// ═══ ④ S4 引擎发射器（wire 严格造型 + toolcall 配对 + bus 载荷向后兼容）═══
{
  // wire 严格校验：必填齐 + 键集白名单（additionalProperties:false 纪律）+ 字符串非空 + 枚举
  const WIRE_SPEC = {
    msg_delta: { req: ['kind', 'delta', 'session_id', 'turn_id'], opt: ['seq'], enums: { kind: ['reason', 'content'] } },
    tool_begin: { req: ['toolcall_id', 'verb', 'session_id', 'turn_id'], opt: ['params_summary'], enums: {} },
    tool_end: { req: ['toolcall_id', 'verb', 'session_id', 'turn_id'], opt: ['result_summary', 'caliber'], enums: {} },
    error: { req: ['code', 'message', 'session_id'], opt: ['hint', 'turn_id'], enums: {} },
  };
  const wireStrict = (family, w) => {
    if (!w || typeof w !== 'object') return false;
    const spec = WIRE_SPEC[family];
    const keys = Object.keys(w);
    if (!spec.req.every((k) => keys.includes(k))) return false;
    if (!keys.every((k) => spec.req.includes(k) || spec.opt.includes(k))) return false;   // 键集白名单
    for (const k of [...spec.req, ...spec.opt]) {
      if (w[k] !== undefined && typeof w[k] === 'string' && !w[k]) return false;   // minLength:1
    }
    for (const [k, vals] of Object.entries(spec.enums)) if (!vals.includes(w[k])) return false;
    return true;
  };

  const ch = createAcpChannel();
  const eng = createEngineEmitter(ch);
  const events = [];
  ch.bus.on('*', (e) => events.push(e));

  // 与 ① 同序模拟一轮引擎调用（含 S5 第三参 cues）
  eng.onDiagnose({ template: 'zonal', intent: 'emotion_analysis' });
  eng.onRoundStart(1);
  eng.onThought('先看分布', 1);
  eng.onAction({ type: 'tool', name: 'zonal_stats', params: { boundary: 'b1' } }, 1);
  eng.onObservation({ rows: 5 }, 1, ['想对比另一个范围吗？']);
  eng.onReason('思考中', 1);
  eng.onFinal('## 结论');
  eng.onResultStruct({ insight: '观点' });
  eng.onFinalDone('## 结论');
  eng.onAskUser({ question: '哪个区？', options: ['西陵'] }, 2);
  eng.onOutletCard([{ kind: 'card' }]);
  eng.onDefense({ fixes: [] });
  eng.onDegraded('raw');
  eng.onRound(1);

  ok(events.length === 14, `引擎发射器 14 事件（实 ${events.length}）`);
  // bus 载荷向后兼容（渲染订阅零改动的证据）——与 ① legacy 断言同字段
  ok(events[0].family === 'turn' && events[0].phase === 'diagnose' && events[0].card.template === 'zonal' && events[0].provenance === 'real', '引擎路径：diagnose 载荷兼容 + provenance=real');
  ok(events[3].sub === 'call' && events[3].name === 'zonal_stats' && events[3].action.type === 'tool' && events[3].params.boundary === 'b1', '引擎路径：onAction 载荷兼容（name/params/action 全量）');
  ok(events[4].observation && events[4].observation.rows === 5 && String(events[4].followup_cues[0]).includes('对比'), '引擎路径：onObservation 载荷兼容 + cues 透传（bus 层）');
  ok(events[5].kind === 'reason' && events[5].token === '思考中' && events[5].round === 1, '引擎路径：msg.delta reason 载荷兼容');
  ok(events[8].verb === 'seal' && events[8].text === '## 结论', '引擎路径：seal 载荷兼容');
  ok(events[12].family === 'error' && events[12].kind === 'degraded', '引擎路径：error.degraded 载荷兼容');
  ok(events.filter((e) => e.lane === 'content').length === 4, '引擎路径：分层计数不变（content 4）');

  // wire 严格造型（四族 schema 镜像）
  ok(wireStrict('msg_delta', events[5].wire) && wireStrict('msg_delta', events[6].wire), 'wire msg_delta 严格造型（必填+键白名单+枚举+非空）');
  ok(wireStrict('tool_begin', events[3].wire) && wireStrict('tool_end', events[4].wire) && wireStrict('error', events[12].wire), 'wire tool_begin/tool_end/error 严格造型');
  ok(events[5].wire.delta === '思考中' && events[5].wire.seq < events[6].wire.seq, 'wire delta 保真 + seq 单调（跨 reason/content）');
  ok(events[3].wire.toolcall_id === events[4].wire.toolcall_id && events[3].wire.verb === 'zonal_stats' && events[4].wire.verb === 'zonal_stats', 'wire toolcall 配对（begin/end 同 id 同 verb）');
  ok(events[4].wire.result_summary.includes('rows'), 'wire result_summary 摘要（对象观察序列化截断）');
  ok(events[4].wire.followup_cues === undefined, 'wire 不带 followup_cues（schema additionalProperties:false·S2 增补前红线）');
  ok(events[12].wire.code === 'DEGRADED_PARSE' && events[12].wire.message, 'wire error 语义化错误码');
  ok([0, 1, 2, 7, 8, 9, 10, 11, 13].every((i) => events[i].wire === undefined), 'turn/render 族不带 wire（schema 未定稿族·bus 直发）');

  // 边界：空 token 不造型 wire 但 bus 照发（渲染不断流）
  const ch2 = createAcpChannel();
  const eng2 = createEngineEmitter(ch2);
  const edge = [];
  ch2.bus.on('msg.delta', (e) => edge.push(e));
  eng2.onFinal('');
  eng2.onFinal('好');
  ok(edge.length === 2 && edge[0].wire == null && wireStrict('msg_delta', edge[1].wire), '空 token：wire 不造型（minLength 纪律）·bus 照发（载荷兼容优先）');

  // 配对边界：observation 无前置 call → 不造型 wire（诚实：无 id 可归）
  const ch3 = createAcpChannel();
  const eng3 = createEngineEmitter(ch3);
  let orphan = null;
  ch3.bus.on('tool.end', (e) => { orphan = e; });
  eng3.onObservation(' stray obs ', 1);
  ok(orphan && orphan.wire == null && orphan.observation === ' stray obs ', '孤立 observation：wire 不造型·bus 载荷照发');

  // 通道判别器：harness 发射层入口依据
  ok(isAcpChannel(ch3) && !isAcpChannel({}) && !isAcpChannel(null) && !isAcpChannel({ bus: {} }), 'isAcpChannel 判别（channel 真伪）');
}

console.log(_fail ? `\n${_fail} FAIL` : '\nALL PASS');
process.exit(_fail ? 1 : 0);
