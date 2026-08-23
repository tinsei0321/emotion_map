// ═══ acp-channel.js — ACP 事件通道（壳对话框架事件化·S3）═══
// 契约：docs/acp-contract-v1.md v1.1（四动词/五族事件/过程-内容分层红线）。
// 形态：harness 仍调 14 个 legacy hooks 签名（eval-anchor 红线·引擎零改动）——
//   emitter 把 hooks 调用翻译成 ACP 事件投上 bus；panel 渲染器订阅 bus（壳=ACP 客户端）。
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
