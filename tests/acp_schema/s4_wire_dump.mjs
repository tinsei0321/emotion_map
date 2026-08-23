// SHELL2(FIX) FIX-08：S4 引擎发射层全 14 方法事件流 dump（fake hooks 驱动·无浏览器依赖）
// 跑法：node tests/acp_schema/s4_wire_dump.mjs → stdout 一行 JSON {events:[...]}
// 供 test_s4_wire.py 用真实 jsonschema 校验器断言——补「S4 主路 wire 过 S6 校验」缺口（C5-1）。
import { createAcpChannel, createEngineEmitter } from 'file:///D:/Github/emotion_map/frontend/js/ai_qa/acp-channel.js';

const ch = createAcpChannel();
const eng = createEngineEmitter(ch);
const events = [];
ch.bus.on('*', (e) => events.push({
  family: e.family, lane: e.lane, provenance: e.provenance || null,
  kind: e.kind || null, verb: e.verb || null, phase: e.phase || null,
  sub: e.sub || null, wire: e.wire || null,
}));

// fake hooks 驱动全 14 个方法（与引擎真实调用面同形）
eng.onDiagnose({ template: 'zonal', intent: 'emotion_analysis' });
eng.onRoundStart(1);
eng.onThought('先看分布', 1);
eng.onAction({ type: 'tool', name: 'zonal_stats', params: { boundary: 'b1' } }, 1);
eng.onObservation('rows=5', 1, ['换个范围对比？']);
eng.onAction({ type: 'tool', name: 'rank', params: {} }, 2);
eng.onObservation({ row_count: 8 }, 2);
eng.onReason('推理中', 1);
eng.onFinal('结论正文');
eng.onResultStruct({ insight: '观点' });
eng.onFinalDone('结论正文');
eng.onAskUser({ question: '哪个区？' }, 3);
eng.onOutletCard([{ kind: 'card' }]);
eng.onDefense({ fixes: [] });
eng.onDegraded('raw token 泄漏面原文');
eng.onRound(1);

process.stdout.write(JSON.stringify({ events }));
