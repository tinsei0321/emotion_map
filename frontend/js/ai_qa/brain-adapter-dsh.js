// ═══ brain-adapter-dsh.js — BrainAdapter · dsh headless 适配器（壳二期件①·SHELL2(BA)）═══
// 契约：docs/brain-adapter.md v0.1（三形态之「dsh 降级形态」）——headless 无真流式：
//   等待期发进度桩事件（tool.begin 桩 + 周期 ping）·返回后一次性发完整结果。
// 诚实性红线（契约 §三-3）：本适配器发出的全部 msg.delta 恒 provenance:'synthesized'
//   ——渲染为「步进进度」非「思考流」·不伪装逐字流（ACP v1.1 §五-1）。
// 链路：panel send(?engine=dsh) → buildHooks 接渲染订阅 → runDshEngine(shell._acp, ctx)
//   → POST /api/v1/aiqa/dsh_engine（后端 spawn dsh --profile emc-test·stdout 全量返回）
//   → bus 事件流（wire 造型过 tests/acp_schema 校验器）。
// 编排权：引擎层（dsh 自主 agent loop）——本适配器是翻译层非编排层（契约红线·不调 MCP 工具）。

const _WIRE_SESSION = 'emc-shell';   // 与 S4 引擎发射层同源（session 对象 v1 不建·占位）

/** 引擎选择：恒为 codex Harness（2026-08-25 用户令：去掉 light/其他引擎，只保留默认 Codex）。 */
export function getEngineMode() {
  return 'codex';
}

/**
 * 跑一轮 dsh 引擎（headless 降级形态·bus 事件流驱动壳渲染）。
 * @param acp    createAcpChannel() 返回值（buildHooks 已在其上接好渲染订阅）
 * @param ctx    send() 组装的上下文（question/signal 消费·其余不碰）
 * @param deps   测试注入口 {fetchImpl, pingMs}（缺省=window.fetch + 3000ms）
 * @returns orchestrate 同形结果（exit/diagnose/newLayerCount）——send 尾部零改动
 */
export async function runDshEngine(acp, ctx, deps) {
  const bus = acp.bus, turn_id = acp.turn_id;
  const q = (ctx && ctx.question) || '';
  const fetchImpl = (deps && deps.fetchImpl) || ((typeof window !== 'undefined' && window.fetch) || null);
  const pingMs = (deps && deps.pingMs) || 3000;
  const timeoutMs = (deps && deps.timeoutMs) || 630000;   // PT-CB14 修复批回收：总护栏 630s（> 代理 600s > 后端 240s×2 重试）——300s 时代截断实证后同步放宽
  const signal = (ctx && ctx.signal) || null;
  let _seq = 0;
  const wireDelta = (kind, delta) => ({ kind, delta, session_id: _WIRE_SESSION, turn_id, seq: _seq++ });
  const toolcall_id = `tc-${turn_id}-dsh`;
  const verb = 'dsh_brain';

  // ① 诊断卡（dsh 引擎身份显式·降级形态不藏）+ 工具桩（tool.begin·wire 造型）
  bus.emit({ family: 'turn', verb: 'step', phase: 'diagnose',
    card: { template: 'dsh', intent: 'dsh', engine: 'dsh', degraded: false,
      scale: '', method: ['dsh 大脑（headless）', '一次性问答'] } });
  bus.emit({ family: 'turn', verb: 'step', phase: 'round.start', round: 1 });
  bus.emit({ family: 'tool.begin', sub: 'call', name: verb, params: { summary: `query=${q.slice(0, 40)}` },
    action: { type: 'tool', name: verb, params: { question: q } }, round: 1, toolcall_id,
    provenance: 'synthesized',
    wire: { toolcall_id, verb, session_id: _WIRE_SESSION, turn_id, params_summary: `query=${q.slice(0, 120)}` } });

  // ② 等待期进度桩：周期 ping（msg.delta reason·synthesized·「已 Ns」步进·非思考流）
  const t0 = Date.now();
  const pingTimer = setInterval(() => {
    const sec = Math.round((Date.now() - t0) / 1000);
    bus.emit({ family: 'msg.delta', kind: 'reason', token: `（dsh 引擎思考中·已 ${sec}s）\n`, round: 1,
      provenance: 'synthesized', wire: wireDelta('reason', `dsh 思考中 ${sec}s`) });
  }, pingMs);

  // ③ 调后端（spawn dsh headless·无流式·返回后批量发）——fetch 缺省（极端环境）按引擎不可用降级。
  // FIX-04：Promise.race 总超时护栏——后端/代理哑死时主动降级，不无限转 ping。
  let resp = null, fail = null;
  let _watchdog = null;
  try {
    if (!fetchImpl) throw new Error('no fetch');
    const _timeoutP = new Promise((_, rej) => { _watchdog = setTimeout(() => rej(new Error('dsh 前端总超时')), timeoutMs); });
    const r = await Promise.race([fetchImpl('/api/v1/aiqa/dsh_engine', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, timeout_s: 240 }), signal,
    }), _timeoutP]);
    resp = await r.json();
    if (!resp || !resp.ok || !resp.output) fail = (resp && resp.error) || 'dsh 空输出';
  } catch (e) {
    fail = (e && e.name === 'AbortError') ? 'abort' : ((e && e.message) || String(e));
  } finally {
    clearInterval(pingTimer);
    if (_watchdog) clearTimeout(_watchdog);   // 成功/失败均在看门狗（防定时器泄漏）
  }

  // ④a 失败/中止：error 族降级卡（诚实告知·不伪造答案）；中止（用户停止）静默退出
  if (fail) {
    if (fail === 'abort') {
      bus.emit({ family: 'tool.end', observation: '（已停止）', round: 1, toolcall_id, provenance: 'synthesized' });
      return { exit: 'gap', diagnose: null, newLayerCount: 0 };
    }
    bus.emit({ family: 'error', kind: 'degraded', hint: `[dsh引擎] 端点不可用：${String(fail).slice(0, 120)}`,
      provenance: 'synthesized',
      wire: { code: 'DSH_ENGINE_FAIL', message: String(fail).slice(0, 200), session_id: _WIRE_SESSION, turn_id } });
    return { exit: 'gap', diagnose: { intent: 'dsh', engine: 'dsh', degraded: true }, newLayerCount: 0 };
  }

  // ④b 成功：tool.end（耗时/长度摘要）→ msg.delta content 批量（一次性全文·不伪装逐字流）→ seal
  const output = String(resp.output);
  const elapsed = resp.elapsed != null ? resp.elapsed : ((Date.now() - t0) / 1000).toFixed(1);
  bus.emit({ family: 'tool.end', observation: `dsh 返回（${output.length} 字·耗时 ${elapsed}s）`, round: 1,
    toolcall_id, provenance: 'synthesized',
    wire: { toolcall_id, verb, session_id: _WIRE_SESSION, turn_id,
      result_summary: `返回 ${output.length} 字·耗时 ${elapsed}s` } });
  bus.emit({ family: 'msg.delta', kind: 'content', token: output,
    provenance: 'synthesized', wire: wireDelta('content', output.slice(0, 500)) });
  bus.emit({ family: 'turn', verb: 'seal', text: output });
  return { exit: 'final', diagnose: { intent: 'dsh', engine: 'dsh', degraded: false }, newLayerCount: 0 };
}
