// S3 单测：ACP 事件通道 + mock 对端（node 直跑·无浏览器依赖）
// 跑法：node tests/acp_channel.test.mjs
// 覆盖：① acp-channel 14 hooks → ACP 事件映射 + 过程/内容分层（process 10 / content 4）
//      ② mock 对端 wireToBus 适配器（wire schema 字段映射·provenance=synthesized）
//      ③ runAcpMockPeer 全剧本（诊断→工具→思考→正文→定稿·turn_id 贯穿）
// 权威：frontend/js/ai_qa/acp-channel.js / acp-mock-peer.js / tests/acp_schema/schemas/*.schema.json
import { createAcpChannel, ACP_FAMILY } from 'file:///D:/Github/emotion_map/frontend/js/ai_qa/acp-channel.js';
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

console.log(_fail ? `\n${_fail} FAIL` : '\nALL PASS');
process.exit(_fail ? 1 : 0);
