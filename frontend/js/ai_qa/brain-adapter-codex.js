// ═══ brain-adapter-codex.js — BrainAdapter · Codex app-server 适配器（PT-CB15 SPIKE·第四引擎）═══
// 契约：docs/brain-adapter.md v0.1（三形态之「Codex 全量形态」）——真流式：
//   后端 /api/v1/aiqa/codex_engine（SSE）逐事件转发 Codex app-server 通知，
//   delta → msg.delta（恒 provenance:'real'·契约 §五-1 全量形态红线）。
// 链路：panel send(?engine=codex) → runCodexEngine(shell._acp, ctx)
//   → POST SSE（后端 core/codex_bridge.py 常驻 app-server·stdio JSONL）→ bus 事件流。
// 编排权：引擎层（Codex agent loop）——本适配器是翻译层非编排层（契约红线·不调 MCP 工具）。
// 与 dsh 版差异：SSE 流式消费（fetch→ReadableStream）非一次性 POST；真 msg.delta 非桩。

const _WIRE_SESSION = 'emc-shell';   // 与 S4 引擎发射层同源（session 对象 v1 不建·占位）

/** 跑一轮 Codex 引擎（全量形态·SSE 真流式→bus 事件流驱动壳渲染）。 */
export async function runCodexEngine(acp, ctx, deps) {
  const bus = acp.bus, turn_id = acp.turn_id;
  const q = (ctx && ctx.question) || '';
  const fetchImpl = (deps && deps.fetchImpl) || ((typeof window !== 'undefined' && window.fetch) || null);
  const timeoutMs = (deps && deps.timeoutMs) || 630000;   // 总护栏（对齐 dsh 版 FIX-04·> 代理 600s）
  const signal = (ctx && ctx.signal) || null;
  let _seq = 0;
  const wireDelta = (kind, delta) => ({ kind, delta, session_id: _WIRE_SESSION, turn_id, seq: _seq++ });
  const toolcallId = (name) => `tc-${turn_id}-${String(name).replace(/[^a-zA-Z0-9_]/g, '').slice(0, 30)}-${_seq}`;

  // ① 诊断卡（codex 引擎身份·全量形态非降级）
  bus.emit({ family: 'turn', verb: 'step', phase: 'diagnose',
    card: { template: 'codex', intent: 'codex', engine: 'codex', degraded: false,
      scale: '', method: ['Codex Harness（app-server）', '真流式逐字'] } });
  bus.emit({ family: 'turn', verb: 'step', phase: 'round.start', round: 1 });

  if (!fetchImpl) {   // fetch 缺省（极端环境）按引擎不可用降级
    bus.emit({ family: 'error', kind: 'degraded', hint: '[codex引擎] 浏览器 fetch 不可用',
      provenance: 'real',
      wire: { code: 'CODEX_NO_FETCH', message: 'fetch unavailable', session_id: _WIRE_SESSION, turn_id } });
    return { exit: 'gap', diagnose: { intent: 'codex', engine: 'codex', degraded: true }, newLayerCount: 0 };
  }

  let fail = null, full = '';
  const t0 = Date.now();
  let watchdog = null;
  try {
    // ② POST SSE + 总超时护栏（Promise.race 同 dsh 版 FIX-04 模式）
    const timeoutP = new Promise((_, rej) => { watchdog = setTimeout(() => rej(new Error('codex 前端总超时')), timeoutMs); });
    const r = await Promise.race([
      fetchImpl('/api/v1/aiqa/codex_engine', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
        body: JSON.stringify({ question: q, timeout_s: 300 }), signal,
      }), timeoutP]);
    if (!r.ok || !r.body) throw new Error(`HTTP ${r.status}`);
    const reader = r.body.getReader();
    const dec = new TextDecoder('utf-8');
    let buf = '';

    // ③ SSE 逐帧解析（event: X\ndata: {...}\n\n）→ bus 事件（真流式·恒 real）
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let sep;
      while ((sep = buf.indexOf('\n\n')) >= 0) {
        const frame = buf.slice(0, sep); buf = buf.slice(sep + 2);
        const evLine = (frame.match(/^event:\s*(.+)$/m) || [])[1] || '';
        const dataLine = (frame.match(/^data:\s*(.+)$/m) || [])[1] || '';
        let evt = null;
        try { evt = JSON.parse(dataLine); } catch (_) { continue; }
        if (!evt) continue;
        if (evLine === 'delta' && evt.delta) {
          full += evt.delta;
          bus.emit({ family: 'msg.delta', kind: evt.kind === 'reason' ? 'reason' : 'content',
            token: evt.delta, round: 1, provenance: 'real',
            wire: wireDelta(evt.kind === 'reason' ? 'reason' : 'content', String(evt.delta).slice(0, 500)) });
        } else if (evLine === 'tool') {
          if (evt.phase === 'begin') {
            const tc = toolcallId(evt.name);
            bus.emit({ family: 'tool.begin', sub: 'call', name: String(evt.name || '').slice(0, 40),
              params: { summary: `server=${evt.server || ''}` }, round: 1, toolcall_id: tc,
              provenance: 'real',
              wire: { toolcall_id: tc, verb: String(evt.name || '').slice(0, 40),
                session_id: _WIRE_SESSION, turn_id, params_summary: `server=${evt.server || ''}` } });
          } else if (evt.phase === 'end') {
            bus.emit({ family: 'tool.end',
              observation: evt.ok ? `${evt.name} 完成` : `${evt.name} 失败${evt.error ? '：' + evt.error : ''}`,
              round: 1, provenance: 'real',
              wire: { toolcall_id: '', verb: String(evt.name || '').slice(0, 40),
                session_id: _WIRE_SESSION, turn_id,
                result_summary: evt.ok ? 'OK' : ('FAIL ' + String(evt.error || '')).slice(0, 120) } });
          }
        } else if (evLine === 'done') {
          bus.emit({ family: 'tool.end', observation: `Codex 完成（${evt.n_delta || 0} delta·耗时 ${evt.elapsed}s）`,
            round: 1, provenance: 'real',
            wire: { toolcall_id: '', verb: 'codex_turn', session_id: _WIRE_SESSION, turn_id,
              result_summary: `${evt.n_delta || 0} delta in ${evt.elapsed}s` } });
        } else if (evLine === 'error') {
          fail = `[codex引擎] ${evt.code || ''} ${evt.message || ''}`.slice(0, 160);
          bus.emit({ family: 'error', kind: 'degraded', hint: fail, provenance: 'real',
            wire: { code: evt.code || 'CODEX_ERR', message: String(evt.message || '').slice(0, 200),
              session_id: _WIRE_SESSION, turn_id } });
        }   // ping：SSE 保活心跳·前端无需渲染
      }
    }
  } catch (e) {
    fail = (e && e.name === 'AbortError') ? 'abort' : ((e && e.message) || String(e));
  } finally {
    if (watchdog) clearTimeout(watchdog);
  }

  // ④ 收口：abort 静默（用户停止非故障）·失败发 error 族（诚实降级·不伪造）·成功 seal
  if (fail === 'abort') {
    bus.emit({ family: 'tool.end', observation: '（已停止）', round: 1, provenance: 'real' });
    return { exit: 'gap', diagnose: { intent: 'codex', engine: 'codex', degraded: false }, newLayerCount: 0 };
  }
  if (fail) {   // error 族事件已发（SSE error 帧）·此处兜底（fetch/解析层失败）
    if (!full) {
      bus.emit({ family: 'error', kind: 'degraded', hint: `[codex引擎] ${String(fail).slice(0, 120)}`,
        provenance: 'real',
        wire: { code: 'CODEX_STREAM_FAIL', message: String(fail).slice(0, 200), session_id: _WIRE_SESSION, turn_id } });
      return { exit: 'gap', diagnose: { intent: 'codex', engine: 'codex', degraded: true }, newLayerCount: 0 };
    }
    // 流中断但已有部分内容：seal 已收内容（诚实·不丢弃）
  }
  bus.emit({ family: 'turn', verb: 'seal', text: full });
  return { exit: 'final', diagnose: { intent: 'codex', engine: 'codex', degraded: false }, newLayerCount: 0 };
}
