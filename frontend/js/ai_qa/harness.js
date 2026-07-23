// ═══ harness.js — Agent Loop 编排器（ReAct：Thought→Action→Observation 循环 + 审查→修订）═══
// 模型每轮自主思考 + 决定动作 + 看结果再想，多轮（上限 MAX_ROUNDS）直到 action='answer'，
// 出草稿 → Flash 审查员按七条 checklist 审查 → 不达标带 hints 自动 revise 重写 1 轮。
// 前置：DIAGNOSE 问题理解卡（认知层）→ 注入 ctx.context 导工具选型 + 结论颗粒度；硬缺口短路请求上传。
// 降级：agent_step 解析失败不再裸显 raw，break loop 仍走 finalStep 出一次性 answer。
import * as stages from './stages.js';
import { TOOLS, setToolContext, formatRegistry } from './tools.js';
import { getLayers } from '../state.js';

const MAX_ROUNDS_GIS = 6;      // intent-aware 轮数上限（P0 降温）：B 纯GIS操作=6（保多目标完整性，如"西陵+伍家岗居住+商业"需多步）
const MAX_ROUNDS_OTHER = 4;    // A 通用 / C 情绪=4（远紧于 16，配合 temp 0.4 降概率链 p^N）

/** P0 降温：轻量 intent 预判——高置信通用/概念问跳 diagnose 直 finalStep（省整轮 diagnose LLM + 7字段卡）。
 *  规划思维 A 赛道"快速分流"：概念解释/方法咨询/日常问候→general 直答；含 geo 动词/地名→落 diagnose。
 *  返 'general'→短路；null→落原 diagnose（保守，宁落不误断）。 */
function _quickIntent(q) {
  if (!q) return null;
  const s = String(q);
  // 概念/方法咨询词优先（即使含 geo 词，"什么是核密度分析"仍判 general 定义类，免漏断）
  if (['什么是', '是什么', '含义', '意思', '解释', '区别', '定义', '为什么', '是指', '如何理解', '有哪些方法'].some(w => s.includes(w))) return 'general';
  // geo 动词（请求做分析，非定义）→ 落 diagnose
  if (['核密度', '密度分析', '热力', '热点', '裁出', '裁剪', '缓冲', '叠加', '叠置', '聚合', '网格', '排序', '最近邻', '可达性', '出图', '生成图'].some(v => s.includes(v))) return null;
  // 宜昌地名（空间指代）→ 落 diagnose（可能 B/C）
  if (['西陵', '伍家岗', '点军', '夷陵', '猇亭', '宜昌', '滨江', '奥体', '二马路', '大南门', 'cbd'].some(p => s.toLowerCase().includes(p.toLowerCase()))) return null;
  // 日常问候/闲聊 → general
  if (['今天', '星期', '几点', '你好', '谢谢', '你是谁', '能做什么', '你能', '帮助'].some(w => s.includes(w))) return 'general';
  return null;   // 模糊 → 落 diagnose
}
const OBS_TRUNC = 200;      // observation 注入 history 截断长度
const PARAMS_TRUNC = 80;    // action params 摘要截断长度
// 审查质量门（5.70 重启）：默认开——仅审 emotion_analysis(C) 答案（general 短路、gis_operation 早 return、EXIT_GAP 早 return，本就不进审查）。
// 聚焦客观质量杠杆（data_driven/actionable/scale_paradigm_fit/professional），主观项(layout/concise/structure)只 warn 不 fail。
// verdict 经 episode 入 L3 → 喂活自成长闭环。运行时杀开关：浏览器 console 跑 localStorage.setItem('emcReviewOff','1') 即关。
const REVIEW_ENABLED = (() => { try { return !localStorage.getItem('emcReviewOff'); } catch (e) { return true; } })();

// ⑤④ Flash template 命中率遥测 + 80% gate（self-protection）。
// diagnose 后记 template 命中(非 unknown)/未中(unknown)，落 localStorage 跨会话累积（clearChat 不重置）。
// gate 语义（承重·零冷启动回归）：冷启动(samples<MIN)放行保当前 fast-path；成熟后命中率≥80% 放行；
// <80%（Flash 经 ≥MIN 次验证系统性不可靠）退 while-loop（更稳健：query-first + 多轮 + 对账）。
const _TPL_STATS_KEY = 'ai_qa_template_stats_v1';
const _TPL_MIN_SAMPLES = 10;
const _TPL_HIT_RATE_GATE = 0.8;

function _loadTplStats() {
  let s;
  try { s = JSON.parse(localStorage.getItem(_TPL_STATS_KEY) || '') || { hits: 0, misses: 0 }; }
  catch (_) { s = { hits: 0, misses: 0 }; }
  // ⑤④ execSkips 分桶（向后兼容：旧 {hits,misses} 无 skips → 填默认）
  if (!s.skips) s.skips = { missing_slot: 0, tool_failed: 0 };
  return s;
}
function _saveTplStats(s) {
  try { localStorage.setItem(_TPL_STATS_KEY, JSON.stringify(s)); } catch (_) { /* 隐私模式禁用 localStorage 静默 */ }
}
/** diagnose 成功后记 Flash template 命中/未中（'unknown'=miss）。degraded 不计（diagnose 自身失败≠Flash template 不可靠）。 */
function _recordTplResult(template) {
  const s = _loadTplStats();
  if (template === 'unknown') s.misses += 1; else s.hits += 1;
  _saveTplStats(s);
}
/** ⑤④ runTemplatePath 执行 skip 遥测（另一轴：不污染 hits/misses gate）。reason ∈ {missing_slot, tool_failed}。 */
function _recordSkip(reason) {
  const s = _loadTplStats();
  if (s.skips[reason] != null) s.skips[reason] += 1;
  _saveTplStats(s);
}
/** gate：冷启动放行（samples<MIN，保当前 fast-path 零回归）；成熟后命中率≥GATE 放行，<GATE（Flash 经验证不可靠）退 while-loop。 */
function _tplHitRateReady() {
  const s = _loadTplStats();
  const n = s.hits + s.misses;
  if (n < _TPL_MIN_SAMPLES) return true;
  return s.hits / n >= _TPL_HIT_RATE_GATE;
}
/** 遥测读取（footer 显示累积命中率 + gate 状态 + execSkips）。 */
export function getTemplateStats() {
  const s = _loadTplStats();
  const n = s.hits + s.misses;
  const skips = s.skips || { missing_slot: 0, tool_failed: 0 };
  return { hits: s.hits, misses: s.misses, samples: n, rate: n > 0 ? s.hits / n : 0, gateReady: _tplHitRateReady(), skips };
}

/** 当前地图图层状态摘要（附入每轮 history，让 LLM 感知操作是否已生效、避免盲目重试）。 */
function _mapState() {
  const ls = getLayers().filter((l) => l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length);
  const recent = ls.slice(-3).reverse().map((l) => l.name).join('/');
  return `地图:${ls.length}层${recent ? '[' + recent + ']' : ''}`;
}

/** 压缩单轮历史摘要（注入下轮 / final / review prompt，降 token 提注意力）。 */
function compressHistory(round, thought, action, obs) {
  const paramsStr = action.params ? JSON.stringify(action.params).slice(0, PARAMS_TRUNC) : '';
  const obsShort = obs && obs.length > OBS_TRUNC ? obs.slice(0, OBS_TRUNC) + '…' : (obs || '');
  return `第${round}轮 | thought: ${thought || ''} | 动作: ${action.name}(${paramsStr}) | 观察: ${obsShort} | ${_mapState()}`;
}

const _DOMAIN_LABEL = { urban_planning: '城市规划', urban_renewal: '城市更新', urban_operation: '城市运营', urban_governance: '城市治理' };

/** diagnose 卡 → 一行摘要（注入 ctx.context，让后续 agent/final/review 都看到）。 */
function formatDiagnoseSummary(d) {
  const dom = (d.domain_lens || []).map((k) => _DOMAIN_LABEL[k] || k).join('/') || '?';
  const strat = (d.data_plan && d.data_plan.strategy) || 'ready';
  const method = (d.method || []).join(' → ') || '—';
  return `【已诊断】scale=${d.scale || '?'} | domain=${dom} | outlet=${d.outlet || '?'} | strategy=${strat} | method=${method}`;
}

/** 上一轮 trace 蒸馏（ctx.priorTurn）→ 一行摘要，注入 ctx.context 顶部，所有 phase 可见，供续作承接。
 *  多轮连续性：补 5.51 之前只回灌 trace.final 的失忆——上轮 intent/method/已做/缺口结构化带回。 */
function formatPriorTurn(p) {
  if (!p) return '';
  const parts = ['【上一轮上下文】'];
  if (p.intent) parts.push(`intent=${p.intent}`);
  if (p.method) parts.push(`method=${p.method}`);
  if (p.done && p.done !== '（无工具调用）') parts.push(`已做=${p.done}`);
  if (p.gap) parts.push(`缺口=${p.gap}`);
  if (p.strategy) parts.push(`strategy=${p.strategy}`);
  return parts.join(' | ');
}

/** 多轮滚动记忆（ctx.turnHistory，最近 2-3 轮）→ 注入 ctx.context 顶部，显意图收敛轨迹（旧→新）。
 *  B2 做厚：5.51 单轮 priorTurn → 多轮（oldest 蒸馏 → newest 详细），让 LLM 承接"先问全域→缩到某区→聚焦某要素"。
 *  单轮时退为 formatPriorTurn 行为（向后兼容）。 */
function formatTurnHistory(turns) {
  if (!turns || !turns.length) return '';
  if (turns.length === 1) return formatPriorTurn(turns[0]);
  const lines = [`【近 ${turns.length} 轮上下文（意图收敛轨迹，旧→新）】`];
  turns.forEach((p, i) => {
    const isLast = i === turns.length - 1;
    const done = (p.done && p.done !== '（无工具调用）') ? p.done : '';
    if (isLast) {
      const d = [];
      if (p.intent) d.push(`intent=${p.intent}`);
      if (p.method) d.push(`method=${p.method}`);
      if (done) d.push(`已做=${done}`);
      if (p.gap) d.push(`缺口=${p.gap}`);
      lines.push(`  · 最近一轮：${d.join(' | ')}`);
    } else {
      lines.push(`  · 第${i + 1}轮：intent=${p.intent || '?'}${done ? ' | 已做=' + done.slice(0, 60) : ''}${p.gap ? ' | 缺口=' + String(p.gap).slice(0, 40) : ''}`);
    }
  });
  return lines.join('\n');
}

/** 硬缺口（request_upload）→ 请求上传结论文本（说清需要什么/为何/格式）。 */
function buildRequestUploadText(d) {
  const dp = d.data_plan || {};
  const needed = _esc((dp.needed || []).join('、') || '所需专业数据');
  const gap = _esc((dp.gap || []).join('、') || '关键数据维度');
  return '## 需要您补充数据才能严谨作答\n\n'
    + `本问需要 **${needed}** 才能给出可靠结论，当前情绪地图数据中尚缺：**${gap}**。\n\n`
    + '**为何必需**：情绪地图覆盖市民主观感受（极性/4×5 归因），但本问还涉及上述专业数据维度，'
    + '缺它则结论会偏离，故不硬答。\n\n'
    + '**建议上传**：Shapefile / GeoJSON（投影 EPSG:4326，或注明所用坐标系），'
    + '在范围选择里加载后即可纳入分析；上传后重提此问即可。\n\n'
    + '> 若暂无此数据，可在下方说明——我将基于现有情绪数据给出**标注了口径（=统计范围）局限**的参考性结论。';
}

/** HTML 转义动态文本：diagnose.data_plan 字段 / 对账 _missing 图层名经 composeGapCard/composePartialCard
 *  拼进 markdown，最终经 renderAnswer→marked.parse→innerHTML 入 DOM；marked v12 不净化 HTML，故此处逐项转义防注入。 */
function _esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/** EXIT_GAP 缺数据/做不成卡（确定性组装，不走 LLM——杜绝"模型又口头讲一遍"）。
 *  触发：intent∈{B,C} 且零成功观察+零新图层（含全失败/全叙述/解析塌）。
 *  内容：缺什么/为何/已尝试但失败的/引导上传或换问法。绝不编造、绝不纯计划文。 */
function composeGapCard(diagnose, failedObs) {
  const dp = (diagnose && diagnose.data_plan) || {};
  const needed = _esc((dp.needed || []).filter(Boolean).join('、'));
  const gap = _esc((dp.gap || []).filter(Boolean).join('、'));
  const strategy = dp.strategy;
  const _needsTool = (failedObs || []).some((f) => /缺现成工具|阻止 run_python/.test(String(f)));
  let head;
  if (_needsTool) {
    head = '## 这个分析缺现成工具——建议后续开发对应 Toolbox 工具\n\nEMC 只用成熟 geo/Toolbox 工具、不临场写代码。当前 Toolbox 还没覆盖这类分析。\n\n**下一步**：告诉我想要的工具能力（如某类可视化/空间统计），我纳入 Toolbox 开发计划；或换用已有 geo 工具组合、换问法。';
  } else if (strategy === 'request_upload' || gap || needed) {
    head = '## 还差关键数据——补齐后我就能严谨作答\n\n'
      + (needed ? `本问需要 **${needed}** 才能给出可靠结论。` : '当前情绪地图数据尚不足以完成此分析。')
      + (gap ? `\n\n**缺失**：${gap}。` : '');
  } else {
    head = '## 这次没跑通——我没能生成可用的图层\n\n我试了几个操作，但都没能产出可用的图层或结论。咱们换个思路：';
  }
  const fails = (failedObs || []).filter(Boolean).slice(0, 4);
  const failTxt = fails.length ? '\n\n**已尝试但未成功**：\n' + fails.map((f) => '- ' + _esc(f)).join('\n') : '';
  const guide = '\n\n**下一步建议**：\n'
    + '- 上传所需矢量数据（Shapefile / GeoJSON，EPSG:4326 或注明坐标系），在范围选择加载后重提此问；\n'
    + '- 或换一种问法 / 缩小范围（指定某区、某类用地、某时点）后重试。\n\n'
    + '> 在没有可靠数据或未生成图层前，我不会凭空编造结论。补充后我将继续完成分析。';
  return head + failTxt + guide;
}

/** EXIT_PARTIAL 做成一部分卡（确定性组装·引导式语气，体验>正确性，不让 LLM 自创出口文案）。
 *  触发：对账发现少量声称图层未实际生成（1-2 个，_isPartialMissing=true）。（注：软缺口 strategy=fallback_annotated 用替代数据仍可完整作答，走 EXIT_RESULT + 口径卡，不触发本卡。）
 *  doneParts: 已做成要点（string[]｜null——null 时不重复，draft 本身即结论段）；
 *  gapParts: 未完成/未生成/缺什么（string[]｜null 时取 diagnose.data_plan.gap）。
 *  三段：已为你完成 → ⚠️ 局限标注 → 下一步引导。绝不伪装成 EXIT_RESULT。 */
function composePartialCard(diagnose, doneParts, gapParts, existingLine) {
  const dp = (diagnose && diagnose.data_plan) || {};
  const done = (doneParts || []).filter(Boolean);
  const gap = (gapParts || dp.gap || []).filter(Boolean);
  const needed = (dp.needed || []).filter(Boolean);
  let s = '## 已为你完成一部分\n\n';
  if (done.length) {
    s += '**已完成的结论**：\n' + done.map((d) => '- ' + _esc(d)).join('\n') + '\n\n';
  } else {
    s += '上面的结论，是基于现有数据能给出的部分。\n\n';
  }
  if (gap.length) s += '**⚠️ 局限标注**：以下未生成或未覆盖——「' + gap.map(_esc).join('、') + '」。\n\n';
  if (existingLine) s += '**地图现有图层**：' + _esc(existingLine) + '。\n\n';
  s += '**下一步**：';
  if (needed.length) s += '上传 **' + needed.map(_esc).join('、') + '** 后重提此问，我将补全完整分析；';
  s += '或换一种问法 / 缩小范围（指定某区、某类用地、某时点）后重试。\n\n';
  s += '> 这是标注了口径（=统计范围）局限的参考性结论——在数据补全前，我不会假装已完整做成。';
  return s;
}

/** A1 产物验证 gate：抽取草稿里声称"已生成/加载"的图层名，对照地图实际图层；谎报→返 hints 注入 revise。 */
function _verifyClaims(draft) {
  if (!draft) return { ok: true };
  const re = /(?:已生成|已加载|已裁出|裁出了|生成了|已创建|新建了|产出了)\s*[「]?([^\n「」，。：:]{2,15})[」]?\s*(?:的?图层|层|面)/g;
  const claims = [];
  let m;
  while ((m = re.exec(draft)) !== null) claims.push(m[1].trim());
  if (!claims.length) return { ok: true };
  const actual = getLayers().map((l) => l.name).filter(Boolean);
  const missing = claims.filter((c) => !actual.some((a) => a === c || a.includes(c) || c.includes(a)));
  if (!missing.length) return { ok: true };
  return { ok: false, hints: `诚实检查：回答声称已生成/加载「${missing.join('、')}」图层，但地图实际图层为[${actual.join('、') || '无'}]。请补做（调 geo 工具生成缺失图层）或纠正陈述（改为"尝试未成功/未生成"）。严禁谎报已做。` };
}

/** ⑤ 抽草稿里"声称产出的图层名"（保守：{{show:X}} 模板 + 强措辞"动词+名+图层类后缀"），供对账。
 *  不抽弱引用（bullet/加粗），避免把地名/归因词误判为图层名。 */
function _extractClaimedLayers(draft) {
  if (!draft) return [];
  const names = new Set();
  let m;
  const showRe = /\{\{show:([^}]+)\}\}/g;   // {{show:X}} 最明确（LLM 引用要显示的图层）
  while ((m = showRe.exec(draft)) !== null) names.add(m[1].trim());
  const verbRe = /(?:生成|产出|得到|裁出|裁剪|新建|构建|输出)[：:]?\s*[`「\*]*([^\n\s`「」\*，。：:()（）\[\]]{2,20})[`」\*]*\s*(?:的)?(?:图层|层|面|点|网格|热度|分布|聚合)/g;
  while ((m = verbRe.exec(draft)) !== null) names.add(m[1].trim());
  return [...names].filter((n) => n && n.length >= 2 && !/^(图层|面|点|网格|分布|热度|清单|列表|数据|结果|图层组|边界)$/.test(n));
}

/** 跑一次 revise（产物验证或 review 不达标触发；最多 1 轮）。返修订后文本或 null。 */
async function _reviseOnce(ctx, hooks, draft, hints, toolHistoryText) {
  if (!hints) return null;
  if (hooks.onReviseStart) hooks.onReviseStart();
  try {
    const revised = await stages.reviseStep(ctx, draft, hints, toolHistoryText, hooks);
    if (revised && revised.trim()) {
      if (hooks.onReviseDone) hooks.onReviseDone(revised);
      return revised;
    }
  } catch (e) { /* revise 失败保留 draft */ }
  return null;
}

/** P1 编排·单技能路径：diagnose 选定 single 技能 → 填参 → 直接调 TOOLS[tool] → finalStep（**不进 while-loop、0 次 agentStep LLM**，p^N→p²）。
 *  缺不可默认槽/工具失败/空命中 → EXIT_GAP 诚实兜底（不赌博自纠，与降 p^N 初衷一致）。finalStep draft 仍过 _verifyClaims+_reviseOnce（5.74 对账保留）。 */
/** P2（Smart·v1.4）：缺必填槽 → 构造 ask_user 提问（精准选项·引导用户指定，避免模糊地名）。 */
const _SLOT_HINT = {
  boundary: { q: '分析哪个区域？', opts: ['西陵区的情绪归因', '伍家岗区的情绪归因', '夷陵区的情绪归因', '我来输入其他区域'] },
  boundaries: { q: '对比哪些区域（≥2 个）？', opts: ['对比西陵区和伍家岗区', '对比西陵区和夷陵区', '我来指定两个区'] },
  center: { q: '哪个设施/地点？（点地图选点，或输入地名）', opts: ['滨江公园周边', '奥体中心周边', '夷陵广场周边', '我来点地图选/输入地名'] },
  range: { q: '指定哪个范围？', opts: ['西陵区', '伍家岗区', '我来上传范围文件'] },
  layer: { q: '对哪个图层分析？', opts: ['最新载入的图层', '我来指定图层名'] },
  target: { q: '找哪类目标？', opts: ['最近的公园', '最近的学校', '我来指定'] },
  layer_a: { q: '叠置的第一个图层？', opts: ['最新载入的图层', '我来指定'] },
  layer_b: { q: '叠置的第二个图层？', opts: ['范围层', '我来指定'] },
};
function _missingSlotAsk(skill, missing) {
  const m = missing[0];
  const hint = _SLOT_HINT[m] || { q: `这个分析需要：${missing.join('、')}——请补充`, opts: ['我来补充说明'] };
  return { type: 'ask_user', question: `要做「${skill}」分析，还缺「${m}」。${hint.q}`, options: hint.opts };
}

/** P1（v1.5 反思·痛点 1）：deliberateStep 仅低置信/复杂任务触发——strategy≠ready（数据缺口/降级标注）或 method≥3 步（复杂多步）。
 *  简单单技能（ready + <3 步）跳过 → 省 1 轮 Pro LLM（缓解"效率慢"·K3 痛点 1·反思 deliberateStep 叠加）。 */
function _needsDeliberate(diagnose) {
  if (!diagnose || diagnose.degraded) return false;   // 降级诊断（可能概念问/诊断失败）不研判
  const strat = diagnose.data_plan && diagnose.data_plan.strategy;
  const method = diagnose.method || [];
  return (strat && strat !== 'ready') || method.length >= 3;
}

async function runTemplatePath(ctx, hooks, diagnose) {
  const skill = diagnose.template;
  const def = stages.SKILL_DEFS[skill];
  const toolHistory = [];
  let newLayerCount = 0;
  // 1. 校验 + 填默认（diagnose.params 经 normalizeParams 归一别名 → validateParams 补 optional_defaults、查 required_slots；用户值覆盖默认）
  const norm = stages.normalizeParams(def.tool, diagnose.params || {});
  const v = stages.validateParams(skill, norm);
  const params = v.params;
  if (!v.ok) {
    // P2 扩展（Smart·v1.4）：缺必填槽 → ask_user 提问（精准选项·引导用户指定），非直接 GAP 放弃。用户答 → resume 续作。
    const ask = _missingSlotAsk(skill, v.missing);
    if (hooks.onAskUser) hooks.onAskUser(ask, 0);
    _recordSkip('missing_slot');   // ⑤④ execSkips 遥测
    return { ok: true, rounds: 0, ask, diagnose, exit: 'ask', newLayerCount: 0 };
  }
  // 1.5 deliberateStep（Pro 研判·执行前·Step 3·阶段 G+H）：仅 Pro 模式 + 低置信/复杂任务（v1.5 gate 收紧·痛点 1）；
  //     Pro 研判"工具+参数是否回答真实意图 + 数据局限"→ 注入 finalStep context 提升结论质量。失败不阻塞（try/catch）。
  if (ctx.model === 'pro' && _needsDeliberate(diagnose)) {
    try {
      const judg = await stages.deliberateStep(ctx, diagnose, params);
      if (judg) ctx.context = `【研判】${judg}\n\n` + (ctx.context || '');
    } catch (e) { /* 研判失败不阻塞主流程 */ }
  }
  // 2. 执行工具（不调 agentStep；setToolContext 必调以写 registry provenance）
  if (hooks.onRoundStart) hooks.onRoundStart(1);
  setToolContext({ tool: def.tool, round: 1 });
  let obs;
  let r = null;
  try {
    r = await TOOLS[def.tool](params);
    obs = (r && r.observation) || '[ERR] 工具无观察返回';
    if (r && r.data && r.data.layerId) newLayerCount = 1;
  } catch (e) {
    obs = `[ERR] ${def.tool} 异常：${(e && e.message) || e}`;
  }
  toolHistory.push(`第1轮·动作: ${def.tool}(${JSON.stringify(params).slice(0, 120)}) → ${obs}`);
  // 3. 失败/空命中 → EXIT_GAP 诚实兜底（不裸输/不赌博自纠）
  //    P0（v1.4 修误判）：分析型工具（zonal/compare/rank/area_stats·表格型无 layerId）成功=rows 非空，
  //    不再因 newLayerCount=0 误判"未产出图层"（数据齐全却喊缺数据的根因）。
  const failed = /\[ERR\]|失败|错误/.test(obs);
  const recoverable = /字段不存在|可用:|缺.*槽|无可见点|无可见情绪点|未找到|无结果|无匹配/.test(obs);   // 可恢复：字段错/缺参/无数据（换字段/提问可解）
  const analytical = _ANALYTICAL_TOOLS.has(def.tool);
  const hasRows = !!(analytical && r && r.data && Array.isArray(r.data.rows) && r.data.rows.length > 0);
  if (failed || (newLayerCount === 0 && !hasRows)) {
    // P2（Smart·v1.5）：空结果(!failed) 或 可恢复失败(recoverable·字段错/缺参/无数据) → ask_user 提问（反馈失败原因+引导），
    //   不直接 GAP 放弃。守 Smart Agent「失败时交流、不猜不放弃」；硬 ERR（网络/异常·非提问可解）仍走 GAP。
    if (!failed || recoverable) {
      const _lbl = params.boundary || params.layer || params.center || '该范围';
      const ask = recoverable
        ? { type: 'ask_user',
            question: `${def.tool} 没成功：${obs.replace(/^\[ERR\]\s*[^：]*：?/, '').slice(0, 140) || '返回可恢复错误'}。请按可用字段/数据重试，或说明你的具体需求。`,
            options: ['我来指定正确的字段/值重试', '换一个分析方向', '看现有数据能做哪些分析？'] }
        : { type: 'ask_user',
            question: `「${_lbl}」范围内未聚合到足够的情绪点数据（可能该区无 L2 点层覆盖，或范围与数据不重叠）。要怎么处理？`,
            options: ['换一个区域重试（请指定：如伍家岗区 / 西陵区）', '我已上传该区域数据，请重新分析', '先看全域情绪分布如何？'] };
      if (hooks.onAskUser) hooks.onAskUser(ask, 1);
      return { ok: true, rounds: 1, ask, diagnose, exit: 'ask', newLayerCount };
    }
    const gapText = composeGapCard(diagnose, [obs.slice(0, 200)]);
    if (hooks.onFinalDone) hooks.onFinalDone(gapText);
    _recordSkip('tool_failed');   // ⑤④ execSkips 遥测
    return { ok: true, rounds: 1, final: gapText, review: { pass: true, degraded: true, skipped: 'template-tool-failed' }, degraded: true, diagnose, exit: 'gap', newLayerCount };
  }
  // 4. finalStep（Pro 写解题一句话 + 短结论 + {{show}}）
  if (hooks.onRound) hooks.onRound(1);
  const toolHistoryText = toolHistory.join('\n');
  ctx.context = `【单技能路径·已执行 ${def.tool}】基于上述工具观察直接出结论，勿重选工具、勿重复执行、勿再调 geo 工具。\n\n` + (ctx.context || '');
  let draft = await stages.finalStep(ctx, hooks, toolHistoryText);
  // 5. 5.74 对账（gis_operation 风格·跳过 review）
  const claims = _verifyClaims(draft);
  if (!claims.ok) {
    const revised = await _reviseOnce(ctx, hooks, draft, claims.hints, toolHistoryText);
    if (revised) draft = revised;
  }
  if (hooks.onFinalDone) hooks.onFinalDone(draft);
  if (hooks.onReview) hooks.onReview({ pass: true, degraded: true, degraded_reason: '单技能路径·跳过审查' });
  return { ok: true, rounds: 1, final: draft, review: { pass: true, degraded: true, skipped: 'single-template' }, degraded: false, diagnose, exit: 'result', newLayerCount };
}

const _GEO_TOOLS = ['extract_feature', 'overlay', 'clip', 'filter_attr', 'merge', 'buffer', 'zonal_stats', 'rank', 'area_stats', 'nearest', 'hotspot'];
const _ANALYTICAL_TOOLS = new Set(['zonal_stats', 'compare_regions', 'rank', 'area_stats']);   // P0：表格型分析工具（返 rows·无 layerId）→ 成功判定认 rows 非空，不误判 GAP
/** F3：诊断 method 里规划的 geo 工具步骤数。数组元素用 ' → ' 拼接后按 →/，/；/换行 分句，
 *  每句首个工具名计 1 步；**不**按 ASCII 逗号分（工具实参含逗号，如 ($1,land)）。 */
function _plannedGeoSteps(method) {
  const m = Array.isArray(method) ? method.join(' → ') : (method || '');
  return m.split(/[→，；;\n]/).reduce((n, clause) => {
    const mm = clause.match(/([a-z_]+)\s*\(/i);
    return (mm && _GEO_TOOLS.includes(mm[1])) ? n + 1 : n;
  }, 0);
}
/** F3：历轮实际执行的 geo 工具步数（toolHistory 每行 = 一轮一个动作，匹配 "动作: tool("）。 */
function _executedGeoSteps(toolHistory) {
  let n = 0;
  for (const line of (toolHistory || [])) {
    const m = String(line).match(/动作:\s*([a-z_]+)\s*\(/i);
    if (m && _GEO_TOOLS.includes(m[1])) n++;
  }
  return n;
}

/**
 * Agent Loop 一次问答。
 * @param ctx    {question, context(grounding), contextTokens, signal, model}
 * @param hooks  渲染回调（panel.js 实现）：
 *   onReason(tok, round)       — reasoning 思考链增量（round 标识所属轮，0=最终/修订阶段）
 *   onDiagnose(card)           — 问题理解卡（DIAGNOSE 前置步；{degraded:true}=降级）
 *   onRoundStart(round)        — 每轮开始（Pro 模式新建 reasoning 分段块）
 *   onThought(text, round)     — 第 round 轮 thought
 *   onAction(action, round)    — 第 round 轮 action
 *   onAskUser(action, round)   — 第 round 轮 ask_user（主动问澄清，渲染问题+选项胶囊，挂起 loop）
 *   onObservation(text, round) — 第 round 轮工具观察
 *   onFinal(tok)               — 草稿结论增量
 *   onFinalDone(text)          — 草稿完成
 *   onReview(review)           — 审查结果 {pass, scores, revise_hints, degraded?}
 *   onReviseStart()            — 开始重写
 *   onRevise(tok)              — 修订结论增量
 *   onReviseDone(text)         — 修订完成
 *   onDegraded(text)           — finalStep 也失败时的最终降级
 * @returns {Promise<{ok, degraded?, rounds?, final?, review?, revised?}>}
 */
export async function orchestrate(ctx, hooks = {}) {
  // ══ 编排器·确定性裁定（Smart Agent/Dumb Tool 内核 · CLAUDE.md「AI·Copilot 开发内核」铁律3：不调 LLM、只接线）══
  // 流程：Smart·计划（diagnose 意图卡）→ 编排器分流（短路 / plan-once-execute / ReAct 兜底）→ Dumb·执行（SKILL/TOOLS 纯参数化）→ 三态出口代码裁定（result/gap/concept）。详见 docs/copilot-architecture.md。
  const toolHistory = [];   // 每轮压缩摘要（注入下轮 prompt）
  let round = 1;
  let degraded = false;
  let forcedContinues = 0;   // F3 完整性 gate 强制续做计数（max 1，防 agent 0 工具就 answer）
  let successObs = 0;        // 三态出口：成功观察数（非失败）
  let newLayerCount = 0;     // 三态出口：本轮新生成图层数（工具 data.layerId 计）
  let narrations = 0;        // 叙述检测：模型只写说明没给动作的轮数（>1 视失败）
  let answered = false;      // 模型是否 deliberate `answer`（概念问等可零工具直答；_hardFail 不得覆盖它）
  let narratedAnswer = false; // 模型持续叙述（prose 作答，常见于概念问）——叙述≠失败，交 finalStep 出结论，不落 GAP
  const failedObs = [];      // 失败观察摘要（EXIT_GAP 卡展示「已尝试」用）

  // 多轮连续性：近 2-3 轮 trace 蒸馏注入 ctx.context 顶部（B2：5.51 单轮 priorTurn → 多轮滚动 turnHistory，意图收敛轨迹）
  const _histCtx = formatTurnHistory(ctx.turnHistory) || formatPriorTurn(ctx.priorTurn);
  if (_histCtx) ctx.context = _histCtx + '\n\n' + (ctx.context || '');

  // P0 降温：_quickIntent 轻量预判——高置信通用/概念问跳 diagnose 直 finalStep（省整轮 diagnose LLM + 7字段卡）
  if (!ctx.resume && _quickIntent(ctx.question) === 'general') {
    ctx.context = '【intent=通用问答·快速预判】直接简洁作答，不要 4×5 归因、不要演示逻辑链、不要引导情绪场景。\n\n' + (ctx.context || '');
    const draft = await stages.finalStep(ctx, hooks, '');
    if (hooks.onFinalDone) hooks.onFinalDone(draft);
    if (hooks.onReview) hooks.onReview({ pass: true, degraded: true, degraded_reason: '通用问答·快速预判跳过审查' });
    return { ok: true, rounds: 0, final: draft, review: { pass: true, degraded: true, skipped: 'quick-general' }, degraded: false, diagnose: { degraded: true, intent: 'general', quick: true } };
  }

  // 【Smart·计划阶段】认知前置步：DIAGNOSE 问题理解卡（LLM 产意图+method+data_plan；失败/降级不阻塞，照走 agent loop）
  let diagnose = null;
  try {
    diagnose = await stages.diagnoseStep(ctx, hooks);
  } catch (e) { diagnose = null; }
  diagnose = diagnose || { degraded: true };
  // domain_lens 结构化数组回传后端：post-diagnose step（answer/revise/agent_step/review）据此注入
  // 命中领域完整权威语境。过滤 'general'（通用问答无需领域权威）。_quickIntent 路径跳过 diagnose
  // → 此处未设 → 各 step 读 undefined → 不注入（正确，通用问答无需领域权威）。
  ctx.domainLens = Array.isArray(diagnose.domain_lens)
    ? diagnose.domain_lens.filter((k) => k && k !== 'general') : [];
  if (hooks.onDiagnose) hooks.onDiagnose(diagnose);
  if (!diagnose.degraded) {
    _recordTplResult(diagnose.template);   // ⑤④ Flash template 命中率遥测（'unknown'=miss，驱动 80% gate）
    // 注入下游：卡摘要前插 ctx.context，所有后续 phase 都看到（导工具选型 + 结论颗粒度）
    ctx.context = formatDiagnoseSummary(diagnose) + '\n\n' + (ctx.context || '');
    // intent 分流（A 通用→短路直接答；B 纯操作→agent loop 走 geo 工具；C 情绪→原路径）
    let intent = diagnose.intent || 'emotion_analysis';
    // 矛盾守卫（normalizeCard 之外的最后防线）：仍判 general 却带纯几何 geo method = 误标，
    // 改 gis_operation（同步写回 diagnose 供 loop/trace/priorTurn 用），避免 general 短路致无工具半截回答。
    if (intent === 'general' && /extract_feature|overlay|clip|filter_attr|merge|buffer/.test((diagnose.method || []).join(' '))) {
      intent = 'gis_operation';
      diagnose.intent = 'gis_operation';
      ctx.context = '【intent 修正】诊断卡标 general，但 method 含 GIS 操作工具——按纯 GIS 操作处理，走 geo 工具产出图层，勿文字作答。\n\n' + (ctx.context || '');
    }
    if (ctx.resume) {
      // 续作：跳过 general/request_upload 短路，强制 agent loop 续跑上轮 method（上轮缺口数据现多已就位）
      ctx.context = '【续作上一轮】用户在追问/续做上一轮任务。承接上一轮 intent+method，从断点续做（上轮【缺口】数据若已上传则继续执行原 method 剩余步骤）；勿当全新问题、勿在 method 未完成前 answer。\n\n' + (ctx.context || '');
      if (ctx.priorTurn && ctx.priorTurn.intent === 'gis_operation') {
        ctx.context = '【intent=纯GIS操作】用 geo 工具（extract_feature/clip/filter_attr/overlay/merge/buffer）完成操作，出口=新图层（自动落地图）。\n\n' + (ctx.context || '');
      }
    } else {
      if (intent === 'general') {
        ctx.context = '【intent=通用问答】直接简洁作答即可，不要 4×5 归因、不要演示逻辑链、不要引导情绪场景。\n\n' + (ctx.context || '');
        const draft = await stages.finalStep(ctx, hooks, '');
        if (hooks.onFinalDone) hooks.onFinalDone(draft);
        if (hooks.onReview) hooks.onReview({ pass: true, degraded: true, degraded_reason: '通用问答·跳过审查' });   // 清「审查中…」占位
        return { ok: true, rounds: 0, final: draft, review: { pass: true, degraded: true, skipped: 'general' }, degraded: false, diagnose };
      }
      if (intent === 'gis_operation') {
        ctx.context = '【intent=纯GIS操作】用 geo 工具（extract_feature/clip/filter_attr/overlay/merge/buffer）完成操作，出口=新图层（自动落地图）。不要 4×5 归因报告、不受尺度范式约束；操作完成后简述产出了什么图层即 answer。\n\n' + (ctx.context || '');
      }
      // 硬缺口短路：不硬答，直接出"请求上传"为结论
      if (diagnose.data_plan && diagnose.data_plan.strategy === 'request_upload') {
        const tpl = buildRequestUploadText(diagnose);
        if (hooks.onFinalDone) hooks.onFinalDone(tpl);
        if (hooks.onReview) hooks.onReview({ pass: true, degraded: true, degraded_reason: '数据缺口·跳过审查' });   // 清「审查中…」占位
        return { ok: true, rounds: 0, final: tpl, review: { pass: true, degraded: true }, degraded: false, diagnose };
      }
    }
  }

  // 【Dumb·执行阶段】P1 编排：single 技能走 runTemplatePath（0 agentStep LLM 轮·纯参数化执行，p^N→p²）；concept 已被上面 general 短路接走；multi/unknown 落 while-loop（ReAct 兜底）。
  // ⑤④ 80% gate（self-protection）：_tplHitRateReady 冷启动放行保零回归；Flash 经 ≥10 次验证命中率<80%（系统性不可靠）时
  // 退 while-loop（更稳健：query-first + 多轮 + 对账），命中率≥80% 才主导 single 快路径。
  if (!ctx.resume && !diagnose.degraded && diagnose.template) {
    const _tdef = stages.SKILL_DEFS[diagnose.template];
    if (_tdef && _tdef.category === 'single' && _tplHitRateReady()) return await runTemplatePath(ctx, hooks, diagnose);
  }

  // P0 降温：intent-aware 轮数上限（diagnose 后定）。B=6 多目标完整性，A/C=4 降概率链。
  const maxRounds = (!diagnose.degraded && diagnose.intent === 'gis_operation') ? MAX_ROUNDS_GIS : MAX_ROUNDS_OTHER;
  // Track 1 query-first：round 0 注入数据 schema 探查 observation（零 LLM，复用 TOOLS.query_layers）——
  // manifesto "先 query 后操作" 的代码落地：schema 本已在 ctx.context（buildContext send 时注入），
  // 此处把已加载层名+计数作为一条 observation 推入 toolHistory，迫使 round1 agentStep 的 thought "看见"数据，免盲目调错工具/字段/层。
  if (!ctx.resume) {
    try { toolHistory.push(`第0轮·数据探查：${TOOLS.query_layers({}).observation}`); }
    catch (e) { /* query_layers 无 data 不计 newLayerCount、无副作用，失败静默不阻塞主流程 */ }
  }
  while (round <= maxRounds) {
    if (hooks.onRound) hooks.onRound(round);
    if (hooks.onRoundStart) hooks.onRoundStart(round);
    let toolHistoryText = toolHistory.length ? toolHistory.join('\n') : '';
    // A3：上一步失败 → 头部加换法重试提示（避免重复同样失败调用）
    if (toolHistory.length && /\[ERR\]|失败|错误/.test(toolHistory[toolHistory.length - 1])) {
      toolHistoryText = '⚠️ 上一步工具失败（见观察末尾）。换参数（字段名/preset/range）或换工具重试，勿重复同样失败调用。\n\n' + toolHistoryText;
    }

    const step = await stages.agentStep(ctx, hooks, round, toolHistoryText);
    if (!step) { degraded = true; break; }   // 空输出：break（落 EXIT_GAP 兜底，不再裸输）

    // 叙述检测：模型只写说明没给动作 JSON。
    //   diagnose 正常（intent 明确要工具：gis_operation/emotion_analysis）→ 叙述=逃避执行，逼 JSON 至 MAX_ROUNDS 落 gap；
    //   diagnose 降级（intent 未知，可能概念问）→ 两轮叙述视作 prose 作答，交 finalStep（保留原语义）。
    if (step.narrated) {
      narrations++;
      if (step.text) toolHistory.push(`第${round}轮·模型叙述：${String(step.text).slice(0, 800)}`);
      const _narrationLegit = !diagnose || diagnose.degraded;   // 降级诊断（可能概念问）认叙述作答
      // P0c 宽容：narrations>=3（逼工具 2 轮仍叙述）=模型坚持文字答 → 认 narratedAnswer 交 finalStep 出参考答（体验>正确性，不逼到 MAX 落 gap）
      if ((narrations > 1 && _narrationLegit) || narrations >= 3) { narratedAnswer = true; break; }
      toolHistory.push(`⚠️ 第${round}轮：你输出了说明文字而非动作 JSON。${!_narrationLegit ? '此问已判定为需工具执行的任务，严禁只说不做；' : ''}本轮若需工具请只输出严格 JSON {"thought":"...","action":{"type":"tool","name":"工具名","params":{...}}}；若信息已足够，输出 {"action":{"type":"answer"}}；${_narrationLegit ? '若是解释性回答可直接说明。' : '继续只说不做将被强制至 MAX_ROUNDS 后判失败。'}`);
      if (hooks.onObservation) hooks.onObservation(`[格式] 上一轮说明非动作 JSON，已要求重发${!_narrationLegit ? '（任务类必须用工具）' : ''}`, round);
      round++;
      continue;
    }

    if (hooks.onThought) hooks.onThought(step.thought, round);
    // P1 ask_user：模型主动问澄清（关键模糊点）→ 渲染问题 + 选项胶囊，挂起 loop（exit='ask'）。
    //   用户点选项 → 发新消息（send）→ 新 orchestrate（priorTurn 承接）续作，无死锁。
    if (step.action.type === 'ask_user') {
      if (hooks.onAskUser) hooks.onAskUser(step.action, round);   // 不走 onAction（非工具）：步骤卡名由 onAskUser 自定义"问澄清"
      return { ok: true, rounds: round, ask: step.action, diagnose, exit: 'ask', newLayerCount };
    }
    if (step.action.type === 'answer') {
      // F3 完整性 gate（计划 vs 已执行，max 1）：GIS 操作 + 情绪分析（C）+ 诊断有 ≥2 步 geo 计划，却执行步数 < 计划步数就 answer = 半截，强制续做。
      // v1.5 扩 emotion_analysis（痛点 4 假完成·K3 确认）：C 类多步做一部分就报 result 的"假完成"根因。
      // 按步数比对，工具等价替换(clip↔overlay)不会误判（步数够即放行）。
      const _f3Intent = diagnose.intent === 'gis_operation' || diagnose.intent === 'emotion_analysis';
      if (_f3Intent && forcedContinues < 1) {
        const _planned = _plannedGeoSteps(diagnose.method);
        const _executed = _executedGeoSteps(toolHistory);
        if (_planned >= 2 && _executed < _planned) {
          forcedContinues++;
          toolHistory.push(`⚠️ 完整性检查：此问诊断计划含 ${_planned} 个步骤，但你只执行了 ${_executed} 个就要 answer——这是半截回答。请继续完成剩余步骤产出全部应有图层/分析，全部完成后再 answer；本轮禁止 answer。`);
          if (hooks.onObservation) hooks.onObservation(`[完整性] 计划 ${_planned} 步 / 已执行 ${_executed} 步，继续执行…`, round);
          round++;
          continue;
        }
      }
      if (hooks.onAction) hooks.onAction(step.action, round);
      answered = true;   // 模型 deliberate answer（含零工具的概念答）→ _hardFail 不得覆盖、必走 finalStep
      break;
    }
    if (hooks.onAction) hooks.onAction(step.action, round);

    // 执行工具（直调主窗口）
    const fn = TOOLS[step.action.name];
    let obs = '';
    // 工作机制·run_python 收口：缺现成 geo/Toolbox 工具时引导后续开发，不临场写代码（用户铁律）。
    //   ctx.allowCodeViz=true（用户显式要自定义可视化/散点/双轴）才放行；否则拦截计 failedObs → 落 EXIT_GAP 缺工具卡引导。
    if (step.action.name === 'run_python' && !ctx.allowCodeViz) {
      obs = '[ERR] 已阻止 run_python 临场写代码——EMC 只用成熟 geo/Toolbox 工具；此分析缺现成工具，按缺工具处理（引导后续开发），勿再调 run_python';
    } else if (fn) {
      try {
        setToolContext({ tool: step.action.name, round });   // ① 注入 provenance 给 addResultLayer 入 registry
        const r = await fn(step.action.params || {});
        obs = (r && r.observation) || '（无观察）';
        if (r && r.data && r.data.layerId) newLayerCount++;   // 三态出口：产图层计 +1
      } catch (e) {
        obs = '工具执行失败：' + (e && e.message ? e.message : e);
      }
    } else {
      obs = `未知工具：${step.action.name}`;
    }
    const _failed = /失败|\[ERR\]|错误|未知工具/.test(obs);
    if (_failed) failedObs.push(`${step.action.name}：${obs.slice(0, 80)}`);
    else successObs++;   // 三态出口：成功观察计 +1
    if (hooks.onObservation) hooks.onObservation(obs, round);

    toolHistory.push(compressHistory(round, step.thought, step.action, obs));
    round++;
  }

  // 三态出口裁定（反「只说不做」核心）：intent∈{B,C} 且**非 deliberate answer 且非叙述作答** 且零成功观察+零新图层 → EXIT_GAP。
  // 关键：模型主动 `answer`（含零工具的概念/解释问）或**持续叙述作答**都不算失败——必走 finalStep 出真结论
  //   （finalStep 见 compressHistory 全 thought + 叙述原文，续上思考）。GAP 只在 loop 到 MAX_ROUNDS / 空输出
  //   等既未 answer 也未叙述 + 零成功（真失败）时触发。
  const toolHistoryText = toolHistory.length ? toolHistory.join('\n') : '';
  const _exitIntent = diagnose && !diagnose.degraded ? (diagnose.intent || 'emotion_analysis') : 'emotion_analysis';
  const _hardFail = (_exitIntent === 'gis_operation' || _exitIntent === 'emotion_analysis')
    && successObs === 0 && newLayerCount === 0 && !answered && !narratedAnswer;
  if (_hardFail) {
    // P2 扩展（Smart·v1.4）：零成功（全失败）→ ask_user 提问（换问法/范围/上传/看现有），非直接 GAP 放弃。守 Smart「失败时交流、不放弃」。
    const _tried = failedObs.slice(0, 2).map((f) => String(f).split('：')[0]).filter(Boolean).join('、');
    const ask = {
      type: 'ask_user',
      question: `这次没能跑通${_tried ? `（试了 ${_tried} 均未成功）` : ''}——可能是范围与数据不匹配，或缺关键数据。要怎么处理？`,
      options: ['换个问法重试（缩小到某区/某类用地/某时点）', '我已上传所需数据，请重新分析', '用现有数据能做哪些分析？'],
    };
    if (hooks.onAskUser) hooks.onAskUser(ask, round);
    return { ok: true, rounds: round, ask, diagnose, exit: 'ask', newLayerCount };
  }

  // EXIT_RESULT：草稿结论（agent 决定 answer / 达上限 / 降级回退 都走这里）
  let draft = '';
  let _isPartialMissing = false;   // EXIT_PARTIAL：对账发现少量声称图层未实际生成（1-2 个），保 draft+标注后转 partial 出口
  // ④ 注入 registry 真值清单（finalStep/review/revise 共用同 ctx.context）：模型 ground 在实际图层，禁编不在列表的层
  ctx.context = '【地图实际产出图层】' + formatRegistry() + '（严禁声称生成不在此列表的图层；任务未完成改述"未生成/未产出"，不得编造图层名与数字）\n\n' + (ctx.context || '');
  try {
    draft = await stages.finalStep(ctx, hooks, toolHistoryText);
  } catch (e) {
    if (hooks.onDegraded) hooks.onDegraded('');
    return { ok: false, degraded: true, rounds: round };
  }
  // P0a finalStep 防漂移（宽容）：命中先 _reviseOnce 让 Flash 用 markdown 重写（体验>正确性，不直接拦没答案）；revise 失败才退固定卡
  // 拓宽（治"代码块泄漏"老毛病）：不只拦 action-JSON——任意 ``` 围栏都判漂移（EMC 结论设计上无代码块，
  //   图表走内联 {chart}/{fig} 指令，勿围栏），走 _reviseOnce 重写 prose。
  const _driftRe = /^\s*(?:```(?:json)?\s*)?\{[\s\S]*"(?:thought|action)"[\s\S]*\}\s*```?\s*$/i;
  const _hasFence = /```/.test(draft);
  if (_driftRe.test(draft.trim()) || _hasFence) {
    const _hint = _hasFence && !_driftRe.test(draft.trim())
      ? '诚实格式：上一版最终回答输出了代码块（``` 围栏）而非可读 markdown 结论。请基于已完成的探索，用**可读 markdown** 重写结论（禁输出代码块/JSON；图表用内联 {chart:...}/{fig:...} 指令，勿用围栏；若任务未完成改述"未生成/未产出"）。保留已真实完成的结论与数据。'
      : '诚实格式：上一版最终回答输出了工具调用 JSON（含 thought/action 字段）而非可读 markdown 结论。请基于已完成的探索，用**可读 markdown** 重写结论（禁输出 JSON；若任务未完成改述"未生成/未产出"）。保留已真实完成的结论与数据。';
    const _revised = await _reviseOnce(ctx, hooks, draft, _hint, toolHistoryText);
    if (_revised && _revised.trim() && !_driftRe.test(_revised.trim()) && !/```/.test(_revised)) {
      draft = _revised;   // revise 成功且无围栏无 action-JSON → 采用，继续走对账
    } else {
      const _driftText = '## 未能生成可读结论\n\n模型在最终回答阶段输出了代码块/工具调用指令而非可读结论，已拦截未显示。\n\n**建议**：换一种问法或缩小范围（指定某区、某类用地、某时点）后重试。';
      if (hooks.onFinalDone) hooks.onFinalDone(_driftText);
      if (hooks.onReview) hooks.onReview({ pass: true, degraded: true, degraded_reason: 'finalStep 格式漂移·拦截', skipped: 'drift' });
      return { ok: false, degraded: true, rounds: round, final: _driftText, diagnose, exit: 'drift' };
    }
  }
  // ⑤ pre-finalStep 结构化对账（intent 无关，P0b 宽容版）：missing<=2 → 保 draft + 自动标注（体验>正确性，不丢整答案）；missing>=3 大面积谎报 → 退 gap
  const _claimed = _extractClaimedLayers(draft);
  if (_claimed.length) {
    const _actualNames = getLayers().filter((l) => l.name).map((l) => l.name);
    const _missing = _claimed.filter((c) => !_actualNames.some((a) => a === c || a.includes(c) || c.includes(a)));
    if (_missing.length >= 3) {
      const _gapText = composeGapCard(diagnose, failedObs) + '\n\n---\n**⚠️ 诚实拦截**：草稿声称已生成「' + _missing.map(_esc).join('、') + '」等图层，但地图实际图层为 [' + (_actualNames.map(_esc).join('、') || '无') + ']，大面积谎报，请用 geo 工具真正生成后再回答。';
      if (hooks.onFinalDone) hooks.onFinalDone(_gapText);
      if (hooks.onReview) hooks.onReview({ pass: true, degraded: true, degraded_reason: '谎报图层拦截(大面积)', skipped: 'drift' });
      return { ok: false, degraded: true, rounds: round, final: _gapText, diagnose, exit: 'drift' };
    } else if (_missing.length) {
      // 少量 missing（1-2）：保 draft + inline 标注 + composePartialCard 引导段（体验>正确性，不丢整答案），标记走 EXIT_PARTIAL
      let _annotated = draft;
      for (const m of _missing) {
        const _re = new RegExp(m.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
        _annotated = _annotated.replace(_re, () => m + '（注：未实际生成）');   // 函数替换防 replacement 串里 $ 特殊语义
      }
      _annotated += '\n\n---\n' + composePartialCard(diagnose, null, _missing, _actualNames.join('、') || '无');
      draft = _annotated;
      _isPartialMissing = true;
    }
  }
  if (hooks.onFinalDone) hooks.onFinalDone(draft);

  // EXIT_PARTIAL 裁定（体验>正确性·四态出口第四态）：仅对账少量 missing（_isPartialMissing）= 真"做成一部分"。
  //   软缺口 strategy=fallback_annotated 用替代数据仍可完整作答 → 走正常 review + EXIT_RESULT（panel.js renderCaliber 显口径卡），不属此态。
  //   诚实门 _verifyClaims 不被 partial 跳过：gis_operation 先跑产物验证（"已加载/已创建"类谎报 _extractClaimedLayers 抓不到、_verifyClaims 能抓）。
  if (_isPartialMissing) {
    const _pIntent = diagnose && !diagnose.degraded ? (diagnose.intent || 'emotion_analysis') : 'emotion_analysis';
    if (_pIntent === 'gis_operation') {
      const _pv = _verifyClaims(draft);
      if (!_pv.ok) {
        const _pr = await _reviseOnce(ctx, hooks, draft, _pv.hints, toolHistoryText);
        if (_pr) draft = _pr;
      }
    }
    if (hooks.onReview) hooks.onReview({ pass: true, degraded: true, degraded_reason: '部分完成·标注局限·引导补充', skipped: 'partial' });
    return { ok: true, rounds: round, final: draft, review: { pass: true, degraded: true, skipped: 'partial' }, degraded: true, diagnose, exit: 'partial', newLayerCount };
  }

  // intent=纯GIS操作：跳过情绪审查（review 的尺度/4×5 标准不适用于操作类回答）
  const _intent = diagnose && !diagnose.degraded ? (diagnose.intent || 'emotion_analysis') : 'emotion_analysis';
  if (_intent === 'gis_operation') {
    // A1：操作类易谎报，产物验证 gate（跳 review 但不跳诚实检查）
    const verify = _verifyClaims(draft);
    if (!verify.ok) {
      const revised = await _reviseOnce(ctx, hooks, draft, verify.hints, toolHistoryText);
      if (revised) draft = revised;
    }
    return { ok: true, rounds: round, final: draft, review: { pass: true, degraded: true, skipped: 'gis_operation' }, degraded, diagnose, exit: 'result', newLayerCount };
  }

  // 审查（REVIEW_ENABLED=false 时跳过 Flash 审查员，仅留诚实门 _verifyClaims）
  let review = null;
  if (REVIEW_ENABLED) {
    try {
      review = await stages.reviewStep(ctx, draft, toolHistoryText);
    } catch (e) {
      review = { pass: true, degraded: true, degraded_reason: String(e && e.message || e) };
    }
  } else {
    review = { pass: true, degraded: true, degraded_reason: '审查机制暂关·重构中' };
  }
  if (hooks.onReview) hooks.onReview(review);

  // 不达标 或 谎报（A1 产物验证）→ revise 重写（最多 1 轮，不递归）
  let final = draft;
  const verify = _verifyClaims(draft);
  const reviseHints = [review && !review.pass && !review.degraded && review.revise_hints, !verify.ok ? verify.hints : null].filter(Boolean).join('\n');
  if (reviseHints) {
    const revised = await _reviseOnce(ctx, hooks, draft, reviseHints, toolHistoryText);
    if (revised) final = revised;
  }
  return { ok: true, rounds: round, final, review, degraded, diagnose, exit: 'result', newLayerCount };
}
