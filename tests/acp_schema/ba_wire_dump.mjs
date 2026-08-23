// 壳二期 BA：dsh 适配器事件流 wire dump（供 pytest S6 校验器消费·node 子进程跑·无浏览器依赖）
// 跑法：node tests/acp_schema/ba_wire_dump.mjs  → stdout 一行 JSON {events:[{family,lane,provenance,wire}...]}
// 用 fake fetch 驱动成功+失败两路径（不发真网络）——真实 dsh 链路由 E2E 覆盖。
import { createAcpChannel } from 'file:///D:/Github/emotion_map/frontend/js/ai_qa/acp-channel.js';
import { runDshEngine } from 'file:///D:/Github/emotion_map/frontend/js/ai_qa/brain-adapter-dsh.js';

const out = [];
const collect = (ch) => ch.bus.on('*', (e) => out.push({
  family: e.family, lane: e.lane, provenance: e.provenance || null,
  kind: e.kind || null, verb: e.verb || null, phase: e.phase || null, wire: e.wire || null,
}));

// 成功路径（fake fetch 延迟 40ms → 期间 ping 桩 → 全文批量）
{
  const ch = createAcpChannel();
  collect(ch);
  const fetchImpl = async () => {
    await new Promise((r) => setTimeout(r, 40));
    return { json: async () => ({ ok: true, output: '留改拆是城市更新中对既有建筑的三种处置方式合称。', elapsed: 1.2 }) };
  };
  await runDshEngine(ch, { question: '什么是留改拆？', signal: null }, { fetchImpl, pingMs: 10 });
}
// 失败路径（引擎不可用 → error.degraded）
{
  const ch = createAcpChannel();
  collect(ch);
  const fetchImpl = async () => { throw new Error('boom'); };
  await runDshEngine(ch, { question: 'q', signal: null }, { fetchImpl, pingMs: 10 });
}

process.stdout.write(JSON.stringify({ events: out }));
