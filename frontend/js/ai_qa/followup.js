// ═══ followup.js — 追问（followup）纯逻辑（SHELL2(FIX) FIX-09）═══
// 从 panel.js 订阅器/渲染内联逻辑提取的纯函数层——浏览器与 node 均可导入（无 DOM 依赖）·
// 单测面（tests/browser/test_followup_chips.py 的 node dump 驱动）。语义与原内联逐字一致：
//   归一化：非数组→空 / 逐条 String+trim / 滤空串 / 截 3 条；
//   优先级：确定性 cues（tool.end）> LLM 胶囊 > 静态兜底；ask 轮互斥（选项已在答案区）。

/** 归一化 tool.end 载荷的 followup_cues：非数组→[]·逐项 String+trim·滤空·截前 3 条。
 *  PT-CB16 C2-1 兼容：对象形态 cue（followup_actions 两级 schema）取 cue_text——
 *  防对象被 String 化成 [object Object]；action 载荷（tool/params）本层不透传（UI 一键重放归 C2-4 评估件）。 */
export function normalizeFollowupCues(raw) {
  if (!Array.isArray(raw)) return [];
  return raw.map((c) => {
    if (c && typeof c === 'object') return String(c.cue_text || '').trim();
    return String(c == null ? '' : c).trim();
  }).filter(Boolean).slice(0, 3);
}

/** 追问源选择：{kind:'cues'|'capsules'|'static'|'none', items}。
 *  cues=确定性追问线索（items=字符串数组）·capsules=LLM 胶囊（items=胶囊对象数组）·
 *  static=调用方走 _followUps 静态兜底（items=null）·none=ask 互斥不出条。 */
export function pickFollowupSource(trace) {
  if (!trace || trace.exit === 'ask') return { kind: 'none', items: [] };   // ask 轮选项已在答案区·底部不重复
  const cues = normalizeFollowupCues(trace.followupCues);
  if (cues.length) return { kind: 'cues', items: cues };
  const capsules = (trace.defense && Array.isArray(trace.defense.capsules)) ? trace.defense.capsules : [];
  if (capsules.length) return { kind: 'capsules', items: capsules };
  return { kind: 'static', items: null };
}
