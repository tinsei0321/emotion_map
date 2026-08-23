// ═══ acp-mock-peer.js — ACP mock 对端（S3 主体·壳自给自足）═══
// 用途：S4 原生事件发射器（引擎侧）未到时，模拟「远端引擎」产出 ACP 事件流直注 bus——
//   复用 S3 注入点 shell._acp（BrainAdapter 降级形态预演·壳渲染零改动）。
// 造型：msg_delta / tool_begin / tool_end / error 四族按 tests/acp_schema/schemas/*.schema.json
//   wire 格式造事件（必填字段逐一对齐），经 wireToBus 参考适配器翻译为 bus 载荷——
//   S4/BrainAdapter 接远端时的适配层蓝本（wire=跨进程格式·bus=壳内信封·两层职责分开）。
// turn/render 族 wire schema 未定稿（v1.1 bus 内部族）——直接给 bus 载荷。
// 诚实性：mock 事件一律 provenance:'synthesized'（契约 v1.1 §5-1——防误把模拟进度当真思考流）。
// 启用：URL 带 ?acp-mock=1 或 window.__EMC_ACP_MOCK__=true（默认零副作用·生产链路不激活）。
// 红线：本模块不承载渲染语义之外的新契约——render 族载荷与 acp-channel.js emitter 同形。

/** mock 是否启用（URL 参数 / window 旗标·module 加载时求值一次）。 */
export function isAcpMockOn() {
  try {
    if (typeof window !== 'undefined' && window.__EMC_ACP_MOCK__) return true;
    if (typeof location !== 'undefined' && new URLSearchParams(location.search).has('acp-mock')) return true;
  } catch (_) { /* 非浏览器环境（node 单测）一律关 */ }
  return false;
}

const _sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ── wire→bus 参考适配器 ────────────────────────────────────────────────
// wire 事件（schema 造型）→ bus envelope 载荷（acp-channel.js emitter 同形）。
// 字段映射：delta→token / verb→name+action.name / result_summary→observation；
// provenance 覆写 synthesized（mock 诚实性·与 emitter 的 real 相对）。
export function wireToBusAdapter(bus, sessionId, turnId) {
  let _seq = 0;
  return {
    // wire: {kind:'reason'|'content', delta, session_id, turn_id, seq?}
    msgDelta(wire, round = 0) {
      bus.emit({ family: 'msg.delta', kind: wire.kind, token: wire.delta, round, provenance: 'synthesized', wire_seq: _seq++ });
    },
    // wire: {toolcall_id, verb, session_id, turn_id, params_summary?}
    toolBegin(wire, round = 0) {
      const params = {}; if (wire.params_summary) params.summary = wire.params_summary;
      bus.emit({ family: 'tool.begin', sub: 'call', name: wire.verb, params,
        action: { type: 'tool', name: wire.verb, params }, round,
        toolcall_id: wire.toolcall_id, provenance: 'synthesized' });
    },
    // wire: {toolcall_id, verb, session_id, turn_id, result_summary?, followup_cues?}
    toolEnd(wire, round = 0) {
      bus.emit({ family: 'tool.end', observation: wire.result_summary || '', round,
        followup_cues: Array.isArray(wire.followup_cues) ? wire.followup_cues : undefined,
        toolcall_id: wire.toolcall_id, provenance: 'synthesized' });
    },
    // wire: {code, message, session_id, hint?, turn_id?}
    error(wire) {
      bus.emit({ family: 'error', code: wire.code, hint: wire.hint || wire.message, provenance: 'synthesized' });
    },
  };
}

/** 把文本切成 n 字一片的 token 流（模拟逐 token 流式）。 */
function _chunk(text, n = 6) {
  const out = [];
  for (let i = 0; i < text.length; i += n) out.push(text.slice(i, i + n));
  return out;
}

/**
 * 跑一轮 mock 对端剧本（直注 bus·不经 orchestrate/emitter）。
 * @param acp   createAcpChannel() 返回值（bus 注入点·buildHooks 已在其上接好渲染订阅）
 * @param ctx   send() 组装的上下文（question/signal 消费·其余不碰）
 * @returns orchestrate 同形结果（exit/diagnose/newLayerCount）——send 尾部逻辑零改动
 */
export async function runAcpMockPeer(acp, ctx) {
  const bus = acp.bus;
  const sid = 'mock-session', tid = acp.turn_id;
  const w = wireToBusAdapter(bus, sid, tid);
  const q = (ctx && ctx.question) || '';
  const delay = (typeof window !== 'undefined' && Number(window.__EMC_ACP_MOCK_DELAY__)) || 40;
  const aborted = () => !!(ctx && ctx.signal && ctx.signal.aborted);

  // ① 诊断卡（turn 族·bus 直发——wire schema 未定稿族）
  bus.emit({ family: 'turn', verb: 'step', phase: 'diagnose',
    card: { template: 'knowledge_qa', intent: 'knowledge_qa', rag: true, degraded: false,
      scale: '社区单元', method: ['知识检索', '综合归纳'], provenance: 'synthesized' } });
  await _sleep(delay); if (aborted()) return { exit: 'gap', diagnose: null, newLayerCount: 0 };
  bus.emit({ family: 'turn', verb: 'step', phase: 'round.start', round: 1 });

  // ② 工具轮：thought（bus 直发）→ rag_query（wire tool_begin）→ 结果（wire tool_end）
  bus.emit({ family: 'tool.begin', sub: 'thought', thought: '先检索知识库口径，再组织回答', round: 1, provenance: 'synthesized' });
  await _sleep(delay); if (aborted()) return { exit: 'gap', diagnose: null, newLayerCount: 0 };
  w.toolBegin({ toolcall_id: 'tc-mock-1', verb: 'rag_query', session_id: sid, turn_id: tid,
    params_summary: `query=${q.slice(0, 40)}` }, 1);
  await _sleep(delay * 2); if (aborted()) return { exit: 'gap', diagnose: null, newLayerCount: 0 };
  w.toolEnd({ toolcall_id: 'tc-mock-1', verb: 'rag_query', session_id: sid, turn_id: tid,
    result_summary: '命中 3 条口径卡（mock）',
    followup_cues: ['要对比其他维度的口径情况吗？（可换用相邻维度数据交叉验证）', '这些口径的适用范围是什么？（可用 kb_facts 精确查）'] }, 1);

  // ③ 思考流（wire msg_delta reason·逐 token）
  for (const tok of _chunk('根据口径卡，该项目库信息已入库，下面按口径汇总数量与投资额。')) {
    if (aborted()) return { exit: 'gap', diagnose: null, newLayerCount: 0 };
    w.msgDelta({ kind: 'reason', delta: tok, session_id: sid, turn_id: tid }, 1);
    await _sleep(delay);
  }

  // ④ 出口三段式（render 族·content lane·bus 直发）
  bus.emit({ family: 'render', kind: 'result.struct',
    struct: { insight: '（mock）口径内项目可直接问答，投资额按入库口径统计。', points: ['mock 对端事件流已贯通', 'provenance=synthesized 全程标记'] } });

  // ⑤ 正文流（wire msg_delta content·逐 token）→ ⑥ 定稿（turn seal）
  const finalMd = `**（mock 对端·synthesized）** 已收到问题「${q.slice(0, 30)}」——此回答由 S3 mock 对端按 ACP wire schema 造事件、经 bus 直注渲染，用于 S4 后端未到时壳链路自验。`;
  for (const tok of _chunk(finalMd, 8)) {
    if (aborted()) return { exit: 'gap', diagnose: null, newLayerCount: 0 };
    w.msgDelta({ kind: 'content', delta: tok, session_id: sid, turn_id: tid });
    await _sleep(delay);
  }
  bus.emit({ family: 'turn', verb: 'seal', text: finalMd });
  return { exit: 'final', diagnose: { intent: 'knowledge_qa', rag: true, degraded: false }, newLayerCount: 0 };
}
