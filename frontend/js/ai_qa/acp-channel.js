// ═══ acp-channel.js — ACP 事件通道（壳对话框架事件化·S3 + 引擎发射层·S4）═══
// 契约：docs/acp-contract-v1.md v1.1（四动词/五族事件/过程-内容分层红线）。
// S3 形态：emitter 把 legacy hooks 调用翻译成 ACP 事件投上 bus（壳=ACP 客户端）。
// S4 形态：createEngineEmitter——引擎侧原生发射：msg.delta/tool.begin/tool.end/error 四族按
//   tests/acp_schema/schemas/*.schema.json wire 格式造事件（附在信封 wire 字段·S6 pytest 可验），
//   bus 载荷与 S3 emitter 逐字段向后兼容（渲染订阅零改动）。legacy emitter 退役为兼容层。
// 分层：process lane=ACP 五族（过程可见性）/ content lane=render 族（渲染语义·非 ACP）。
// 预留：bus 暴露（shell._acp）——BrainAdapter 降级形态未来直注远端事件（provenance:'synthesized'），壳渲染零改动。

/** 事件 family 常量（process lane=ACP v1.1 §二 五族；render=内容通道族·契约 §五-3 分层注记）。 */
export const ACP_FAMILY = {
  MSG_DELTA: 'msg.delta',
  TOOL_BEGIN: 'tool.begin',
  TOOL_END: 'tool.end',
  TURN: 'turn',
  ERROR: 'error',
  RENDER: 'render',   // content lane（非 ACP·过程-内容分层红线——渲染语义不走 ACP 五族）
};

let _turnSeq = 0;

/**
 * 建一条 ACP 事件通道（每 send 一轮一条）。
 * 返回 { bus, emitter, turn_id }：
 *   bus.on(family, fn) 订阅（family='*' 收全部）·bus.emit(evt) 投递；
 *   emitter 持 14 个 legacy hooks 方法（签名与 harness 调用面逐字一致）。
 */
export function createAcpChannel() {
  const turn_id = `turn-${Date.now().toString(36)}-${(++_turnSeq).toString(36)}`;
  const subs = new Map();   // family -> Set<fn>

  function on(family, fn) {
    if (!subs.has(family)) subs.set(family, new Set());
    subs.get(family).add(fn);
    return () => subs.get(family).delete(fn);
  }

  function emit(evt) {
    const full = { turn_id, ts: Date.now(), ...evt };
    if (!full.lane) full.lane = (full.family === ACP_FAMILY.RENDER) ? 'content' : 'process';
    for (const fn of (subs.get(full.family) || [])) { try { fn(full); } catch (_) { /* 订阅异常不阻塞投递 */ } }
    for (const fn of (subs.get('*') || [])) { try { fn(full); } catch (_) { /* 同上 */ } }
    return full;
  }

  const bus = { on, emit };

  const emitter = {
    // ── S3 legacy 翻译层（退役为兼容层·S4 引擎路径改用 createEngineEmitter）──
    // ── process lane：msg.delta（reason/content 两型·v1.1 §5-1 provenance=real 轻循环直发）──
    onReason: (token, round) => emit({ family: ACP_FAMILY.MSG_DELTA, kind: 'reason', token, round: round || 0, provenance: 'real' }),
    onFinal: (token) => emit({ family: ACP_FAMILY.MSG_DELTA, kind: 'content', token, provenance: 'real' }),
    // ── process lane：tool.begin/end（工具条目起止·v1.1 §5-2 载荷结构模式由消费方解）──
    onThought: (thought, round) => emit({ family: ACP_FAMILY.TOOL_BEGIN, sub: 'thought', thought, round }),
    onAction: (action, round) => emit({ family: ACP_FAMILY.TOOL_BEGIN, sub: 'call', name: action && action.name, params: (action && action.params) || {}, action, round }),   // action 全量随行（trace 保真·type 字段不丢）
    // S5：第三参 followup_cues（可选·契约 v1.1 §5-3 tool.end 载荷）——legacy 两参签名不变·S4 引擎发射层透传
    onObservation: (observation, round, followup_cues) => emit({ family: ACP_FAMILY.TOOL_END, observation, round, followup_cues }),
    // ── process lane：turn 生命周期（四动词 step/seal·diagnose 归 step 相位）──
    onDiagnose: (card) => emit({ family: ACP_FAMILY.TURN, verb: 'step', phase: 'diagnose', card }),
    onRoundStart: (round) => emit({ family: ACP_FAMILY.TURN, verb: 'step', phase: 'round.start', round }),
    onRound: (round) => emit({ family: ACP_FAMILY.TURN, verb: 'step', phase: 'round.tick', round }),
    onFinalDone: (text) => emit({ family: ACP_FAMILY.TURN, verb: 'seal', text }),
    // ── process lane：error 族（语义化错误码+hint·契约 §二）──
    onDegraded: (text) => emit({ family: ACP_FAMILY.ERROR, kind: 'degraded', hint: text }),
    // ── content lane：render 族（渲染语义·契约分层红线·不进 ACP）──
    onAskUser: (action, round) => emit({ family: ACP_FAMILY.RENDER, kind: 'ask_user', action, round }),
    onResultStruct: (struct) => emit({ family: ACP_FAMILY.RENDER, kind: 'result.struct', struct }),
    onOutletCard: (cards) => emit({ family: ACP_FAMILY.RENDER, kind: 'outlet.card', cards }),
    onDefense: (defense) => emit({ family: ACP_FAMILY.RENDER, kind: 'defense', defense }),
  };

  return { bus, emitter, turn_id };
}

// ── S4 引擎侧发射层 ────────────────────────────────────────────────
// 四族 wire 造型（schema 必填字段对齐·additionalProperties 纪律）：
//   msg_delta {kind,delta,session_id,turn_id,seq?} / tool_begin {toolcall_id,verb,session_id,turn_id,params_summary?}
//   tool_end {toolcall_id,verb,session_id,turn_id,result_summary?,caliber?} / error {code,message,session_id,hint?,turn_id?}
// turn/render 族 wire schema 未定稿（S2 增补在途）——bus 直发不带 wire。
// followup_cues 同理不入 wire（tool_end schema additionalProperties:false·S2 增补后随载荷结构模式入）——bus 载荷照带。
// session 语义 v1 不建（S3 设计决策 2）——session_id 用稳定占位 'emc-shell'，BrainAdapter 阶段再补真实 session 对象。

const _WIRE_SESSION = 'emc-shell';

/** 引擎发射器：14 个 legacy hooks 签名（harness/stages 调用面零改动）→ wire 造型 ACP 事件 + bus 信封。 */
export function createEngineEmitter(channel) {
  const bus = channel.bus, turn_id = channel.turn_id;
  let _seq = 0, _tcSeq = 0, _lastTc = null;   // msg.delta 序号 / toolcall 配对状态

  const _wireDelta = (kind, token) => {
    const delta = String(token == null ? '' : token);
    return delta ? { kind, delta, session_id: _WIRE_SESSION, turn_id, seq: _seq++ } : null;   // 空串不造型（minLength:1）
  };
  const _summary = (obs) => {
    try {
      const s = typeof obs === 'string' ? obs : JSON.stringify(obs);
      return (s && s.slice(0, 200)) || null;
    } catch (_) { return null; }
  };

  return {
    // ── msg.delta：wire kind/delta/seq（v1.1 §5-1 provenance=real 轻循环直发）──
    onReason: (token, round) => bus.emit({ family: ACP_FAMILY.MSG_DELTA, kind: 'reason', token, round: round || 0, provenance: 'real', wire: _wireDelta('reason', token) }),
    onFinal: (token) => bus.emit({ family: ACP_FAMILY.MSG_DELTA, kind: 'content', token, provenance: 'real', wire: _wireDelta('content', token) }),
    // ── tool.begin/end：wire toolcall_id/verb 配对（observation 回填最近一次 call 的 id/verb）──
    onThought: (thought, round) => bus.emit({ family: ACP_FAMILY.TOOL_BEGIN, sub: 'thought', thought, round, provenance: 'real' }),
    onAction: (action, round) => {
      const verb = action && action.name;
      let wire = null;
      if (verb) {
        const toolcall_id = `tc-${turn_id}-${++_tcSeq}`;
        let params_summary = null;
        try { params_summary = JSON.stringify((action && action.params) || {}).slice(0, 120) || null; } catch (_) { params_summary = null; }
        wire = { toolcall_id, verb, session_id: _WIRE_SESSION, turn_id };
        if (params_summary) wire.params_summary = params_summary;
        _lastTc = { toolcall_id, verb };
      }
      return bus.emit({ family: ACP_FAMILY.TOOL_BEGIN, sub: 'call', name: verb, params: (action && action.params) || {}, action, round, toolcall_id: wire && wire.toolcall_id, provenance: 'real', wire });
    },
    // S5：第三参 followup_cues（契约 v1.1 §5-3）——bus 载荷照带·wire 不带（schema 未增补）
    onObservation: (observation, round, followup_cues) => {
      let wire = null;
      if (_lastTc) {
        wire = { toolcall_id: _lastTc.toolcall_id, verb: _lastTc.verb, session_id: _WIRE_SESSION, turn_id };
        const rs = _summary(observation);
        if (rs) wire.result_summary = rs;
        _lastTc = null;   // 一次配对一对（后续 observation 无 call 可归则不造型）
      }
      return bus.emit({ family: ACP_FAMILY.TOOL_END, observation, round, followup_cues, toolcall_id: wire && wire.toolcall_id, provenance: 'real', wire });
    },
    // ── turn 生命周期（wire 未定稿·bus 直发·载荷与 S3 逐字兼容）──
    onDiagnose: (card) => bus.emit({ family: ACP_FAMILY.TURN, verb: 'step', phase: 'diagnose', card, provenance: 'real' }),
    onRoundStart: (round) => bus.emit({ family: ACP_FAMILY.TURN, verb: 'step', phase: 'round.start', round, provenance: 'real' }),
    onRound: (round) => bus.emit({ family: ACP_FAMILY.TURN, verb: 'step', phase: 'round.tick', round, provenance: 'real' }),
    onFinalDone: (text) => bus.emit({ family: ACP_FAMILY.TURN, verb: 'seal', text, provenance: 'real' }),
    // ── error：wire 语义化错误码（degraded=解析失败兑底）──
    onDegraded: (text) => bus.emit({ family: ACP_FAMILY.ERROR, kind: 'degraded', hint: text, wire: { code: 'DEGRADED_PARSE', message: '模型输出未能解析为可执行动作', session_id: _WIRE_SESSION, turn_id } }),
    // ── content lane：render 族（渲染语义·分层红线·不进 ACP）──
    onAskUser: (action, round) => bus.emit({ family: ACP_FAMILY.RENDER, kind: 'ask_user', action, round }),
    onResultStruct: (struct) => bus.emit({ family: ACP_FAMILY.RENDER, kind: 'result.struct', struct }),
    onOutletCard: (cards) => bus.emit({ family: ACP_FAMILY.RENDER, kind: 'outlet.card', cards }),
    onDefense: (defense) => bus.emit({ family: ACP_FAMILY.RENDER, kind: 'defense', defense }),
  };
}

/** 入参是否 ACP 通道（{bus, turn_id}）——harness 发射层入口的判别器。 */
export function isAcpChannel(x) {
  return !!(x && x.bus && typeof x.bus.emit === 'function' && typeof x.turn_id === 'string');
}
