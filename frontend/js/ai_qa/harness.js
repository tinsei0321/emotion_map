// ═══ harness.js — Agent Loop 编排器（ReAct：Thought→Action→Observation 循环 + 质量防线）═══
// 模型每轮自主思考 + 决定动作 + 看结果再想，多轮（上限 MAX_ROUNDS）直到 action='answer'，
// 出草稿 → applyQualityDefense 三层代码防线（L1 产物验证 + R 规则 + L3 降级·不调 LLM·CB-09 D023 取代旧 R+R）。
// 前置：DIAGNOSE 问题理解卡（认知层）→ 注入 ctx.context 导工具选型 + 结论颗粒度；硬缺口短路请求上传。
// 降级：agent_step 解析失败不再裸显 raw，break loop 仍走 finalStep 出一次性 answer。
import * as stages from './stages.js';
import { TOOLS, setToolContext, formatRegistry, getArtifacts, deriveAvailable, resetStepResults, resetCurrentResults, resolveCoref } from './tools.js';
import { getLayers } from '../state.js';

const MAX_ROUNDS_GIS = 10;      // intent-aware 轮数上限（P0 降温）：B 纯GIS操作=10（保多步完整性，如3次overlay需8轮：1查询+6执行+1answer）
const MAX_ROUNDS_OTHER = 4;    // A 通用 / C 情绪=4（远紧于 16，配合 temp 0.4 降概率链 p^N）

// v3 H6：前端 _validateFcParams 已删除——信赖后端 validate_tool_call（router fc_diagnose 调·D062）。
// 后端在返回 tool_calls 前已校验 + 修正参数（enum 外→默认值替代·required 缺→补默认）·前端不重复。

// CB-05 ROOTCAUSE：tool name → skill name 映射（同 stages.js·harness 内复用）
const _TOOL_TO_SKILL = { zonal_stats: 'zonal', compare_regions: 'compare' };

/** CB-05 ROOTCAUSE 方案 4：追问时从上轮 plans[] 匹配当前意图·跳 FC 复用正确参数。
 *  匹配规则：问句含极性词（消极/积极/中性）→ 找 plans 中 polarity 匹配的 density/rank plan。
 *  返匹配的 plan {tool, params} 或 null（无匹配 → 走正常 FC）。 */
function _matchPlanToQuestion(question, plans) {
  if (!question || !Array.isArray(plans)) return null;
  const q = question.toLowerCase();
  // 极性匹配
  const _POL_MAP = [
    { kw: ['消极', '负面', 'negative', '差'], polarity: 'negative' },
    { kw: ['积极', '正面', 'positive', '好'], polarity: 'positive' },
    { kw: ['中性', 'neutral', '客观'], polarity: 'neutral' },
    { kw: ['综合', '总体', 'overall', '全部'], polarity: 'overall' },
  ];
  for (const pm of _POL_MAP) {
    if (pm.kw.some((k) => q.includes(k))) {
      // 找 plans 中 density/rank 且 polarity 匹配的
      const hit = plans.find((p) =>
        p && p.tool && /^(density|rank)$/i.test(p.tool) &&
        p.params && (p.params.polarity === pm.polarity || p.params.analysis === pm.polarity)
      );
      if (hit) return hit;
    }
  }
  return null;
}

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

// ⑤④ Flash template 命中率遥测 + 80% gate（self-protection）。
// diagnose 后记 template 命中(非 unknown)/未中(unknown)，落 localStorage 跨会话累积（clearChat 不重置）。
// gate 语义（承重·零冷启动回归）：冷启动(samples<MIN)放行保当前 fast-path；成熟后命中率≥GATE 放行；
// B1-2b 松 gate 0.8→0.6：misses 仅计 unknown（Flash 没出任何 template），故 0.6 = "Flash 真坏（>40% unknown）"才退 while-loop，
//   非"路由不完美"即退。runTemplatePath 自带 ask_user/gap 恢复兜底；保 fast path 作单技能默认（治超时#1·省 agent 多轮）。
const _TPL_STATS_KEY = 'ai_qa_template_stats_v1';
const _TPL_MIN_SAMPLES = 10;
const _TPL_HIT_RATE_GATE = 0.6;

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
function _esc(s) {   // 转义 HTML + 反引号（防 marked 把动态值 needed/gap/failedObs 当代码块渲染）
  return String(s == null ? '' : s).replace(/[&<>"'`]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;', '`': '&#96;' }[c]));
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

/** A1 产物验证 gate：抽取草稿里声称"已生成/加载"的图层名，对照地图实际图层；谎报→返 missing + hints。
 *  CB-09 D023：失败动作从「LLM revise」改为「代码 inline 标注」（applyQualityDefense L1）·hints 保留供日志。 */
function _verifyClaims(draft) {
  if (!draft) return { ok: true, missing: [] };
  const claims = _extractClaimedLayers(draft);   // CB-09 5.242 S7：单一正则源（与 while-loop 漂移检测同源·治两套正则不一致 missing 检测）
  if (!claims.length) return { ok: true, missing: [] };
  const actual = getLayers().filter((l) => (l._renderState || 'ok') === 'ok').map((l) => l.name).filter(Boolean);   // E3：渲染失败层（_renderState≠ok·入列表但地图未真渲染）不计实际产出（治假完成·同 orchestrate :690 对账口径）
  const missing = claims.filter((c) => !actual.some((a) => a === c || a.includes(c) || c.includes(a)));
  if (!missing.length) return { ok: true, missing: [] };
  return { ok: false, missing, hints: `诚实检查：回答声称已生成/加载「${missing.join('、')}」图层，但地图实际图层为[${actual.join('、') || '无'}]。` };
}

/** CB-09 D023 质量防线（三层全代码·不调 LLM·<20ms）：取代旧 R+R（reviewStep+reviseStep·LLM 重写 5-15s·假阳性高·CB-05 起已默认关）。
 *  L1 _verifyClaims（产物验证·声称图层不在地图→代码标注）+ L2 结构化规则（R1/R2/R3/R4/R7·draft 级）+ L3 降级渲染（_composeDegradedConclusion）。
 *  R5/R6/R8（胶囊级·参数合法/工具可达/多样性）随轮次2 胶囊绑定工具集落地——当前追问胶囊是静态 {tag,text} prompt 串（panel.js _followUps）·无 tool+params 可校验。
 *  入参 opts: {toolHistoryText, obsOk, skipL1}——skipL1=true 跳过产物验证（while-loop 路径 _extractClaimedLayers 对账已标注 missing·防双重标注）。
 *  返 {final, degraded, fixes}——fixes 供 episode 自成长（D024·取代旧 review verdicts）。 */
function applyQualityDefense(draft, opts) {
  const _opts = opts || {};
  let final = draft || '';
  const fixes = [];
  let degrade = false;
  const _isNonEmpty = (s) => String(s).replace(/[#\s\-*`>]/g, '').length;
  const reg = (typeof getArtifacts === 'function' ? getArtifacts() : []) || [];   // v3.1 P0：formatRegistry() 返字符串·getArtifacts() 返数组（治 reg.filter 崩溃）
  const realLayers = reg.filter((r) => r.tool && r.tool !== 'query_layers').map((r) => r.name).filter(Boolean);

  // CB-09 D020 追问胶囊：先剥离 {{capsule:...}} 标记 → cleanDraft（下游 R1-R7 跑净文本）·capsules 待 R5/R6/R8 校验
  const _cap = _extractCapsules(final);
  final = _cap.cleanDraft;
  let capsules = _cap.capsules;

  // L1 产物验证（skipL1=false·_verifyClaims missing → inline 标注「（注：未实际生成）」·复用 :826 函数替换范式防 $ 语义）
  if (!_opts.skipL1) {
    const claims = _verifyClaims(final);
    if (!claims.ok && claims.missing && claims.missing.length) {
      for (const m of claims.missing) {
        const re = new RegExp(m.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
        final = final.replace(re, () => m + '（注：未实际生成）');
      }
      fixes.push({ rule: 'L1', action: 'annotate-false-claims', missing: claims.missing });
    }
  }

  // R1 非空结论（硬拦截·去格式符后 <10 字符 → L3 降级·防 finalStep 空答）
  if (_isNonEmpty(final) < 10) { degrade = true; fixes.push({ rule: 'R1', action: 'empty-degrade' }); }

  // R2 图层按钮存在（obs OK + 有产出层 + draft 无 {{show:}} → 自动追加·代码补·治"图出但结论没按钮"）
  if (_opts.obsOk && realLayers.length && !/\{\{show:/.test(final)) {
    const btns = realLayers.map((n) => `{{show:${n}}}`).join('\n');
    final += `\n\n**已产出图层**（点击查看）：\n${btns}`;
    fixes.push({ rule: 'R2', action: 'append-buttons' });
  }

  // R3 参数一致性（标记·不拦截）：draft 引用数值 vs toolHistory observation 的 cell_size/radius·差异记 fixes
  if (_opts.toolHistoryText) {
    const _draftNums = String(final).match(/\d{2,5}\s*(?:米|m)\b/g) || [];
    const _obsNums = String(_opts.toolHistoryText).match(/\d{2,5}\s*(?:米|m)\b/g) || [];
    if (_draftNums.length && _obsNums.length) {
      const _diff = _draftNums.filter((n) => !_obsNums.includes(n));
      if (_diff.length) fixes.push({ rule: 'R3', action: 'param-mismatch', values: _diff.slice(0, 3) });
    }
  }

  // R4 状态不矛盾（硬拦截）：obsOK 却说「失败」/ obsERR 却说「已生成」→ L3 降级（治"图出但请求失败"矛盾·CB-07 同源）
  if (_opts.obsOk && /请求失败|未成功生成|生成失败|未能生成/.test(final)) { degrade = true; fixes.push({ rule: 'R4', action: 'ok-says-fail' }); }
  if (_opts.obsOk === false && /已生成|已产出|生成了|已创建/.test(final)) { degrade = true; fixes.push({ rule: 'R4', action: 'err-says-ok' }); }

  // R7 结论三句骨架（>800 字 → 截断·代码兜底·prompt 已约束 brevity·此为真失控拦截）
  if (final.length > 800) {
    final = final.slice(0, 800) + '\n\n…（结论已截断·详见上方图层）';
    fixes.push({ rule: 'R7', action: 'truncate' });
  }

  // R5/R6/R8 追问胶囊校验（CB-09 D020·capsule 绑定工具集）：R5 schema 硬剔 / R6 可达性软标 / R8 多样性记 episode
  if (capsules.length) {
    capsules = capsules.filter((c) => {
      const def = stages.SKILL_DEFS[c.skill];
      if (!def || !def.tool) { fixes.push({ rule: 'R5', action: 'drop-invalid-capsule', label: c.label, reason: 'skill-no-tool' }); return false; }
      if (c.level !== 'L1' && c.level !== 'L2') { fixes.push({ rule: 'R5', action: 'drop-invalid-capsule', label: c.label, reason: 'bad-level' }); return false; }
      const v = stages.validateParams(c.skill, c.params || {});
      if (!v.ok) { fixes.push({ rule: 'R5', action: 'drop-invalid-capsule', label: c.label, reason: 'missing:' + v.missing.join(',') }); return false; }
      return true;
    });
    const _lyrs = getLayers();
    const _hasAny = _lyrs.length > 0;
    const _POINT_SKILLS = new Set(['density', 'buffer', 'hotspot', 'rank', 'nearest', 'extract_feature', 'filter_attr']);
    const _BOUNDARY_SKILLS = new Set(['zonal', 'compare', 'area_stats', 'merge', 'clip']);
    capsules.forEach((c) => {
      let exe = true;
      if (c.skill === 'overlay') exe = _lyrs.length >= 2;
      else if (_POINT_SKILLS.has(c.skill) || _BOUNDARY_SKILLS.has(c.skill)) exe = _hasAny;
      c.executable = exe;
      if (!exe) fixes.push({ rule: 'R6', action: 'mark-unexecutable', label: c.label, skill: c.skill });
    });
    if (!capsules.some((c) => c.level === 'L2')) fixes.push({ rule: 'R8', action: 'no-l2-capsule' });
  }

  // L3 降级渲染（R1/R4 触发 → 跳 LLM 结论·展示 observation + 图层按钮·复用 CB-07 _composeDegradedConclusion）
  if (degrade) {
    final = _composeDegradedConclusion(_opts.toolHistoryText);
    fixes.push({ rule: 'L3', action: 'degrade' });
    capsules = [];   // 降级（空答/矛盾）→ 丢胶囊（LLM 已混乱·胶囊可疑）·降级卡自有图层按钮
  }

  return { final, degraded: degrade, fixes, capsules };
}

/** ⑤ 抽草稿里"声称产出的图层名"（保守：{{show:X}} 模板 + 强措辞"动词+名+图层类后缀"），供对账。
 *  不抽弱引用（bullet/加粗），避免把地名/归因词误判为图层名。 */
function _extractClaimedLayers(draft) {
  if (!draft) return [];
  const names = new Set();
  let m;
  const showRe = /\{\{show:([^}]+)\}\}/g;   // {{show:X}} 最明确（LLM 引用要显示的图层）
  while ((m = showRe.exec(draft)) !== null) names.add(m[1].trim());
  const verbRe = /(?:生成|产出|得到|裁出|裁剪|新建|构建|输出)[：:]?\s*[`「\*]*([^\n\s`「」\*，。：:()（）\[\]]{3,20})[`」\*]*\s*(?:的)?(?:图层|层|面|点|网格|热度|分布|聚合)/g;
  while ((m = verbRe.exec(draft)) !== null) names.add(m[1].trim());
  return [...names].filter((n) => n && n.length >= 2 && !/^(图层|面|点|网格|分布|热度|清单|列表|数据|结果|图层组|边界)$/.test(n));
}

/** CB-09 D020 抽草稿里的追问胶囊 {{capsule:label|level|skill|k=v|...}} → 剥离标记 + 结构化。
 *  格式同 chart spec（| 分隔·flat key=val·无嵌套花括号·避 .format() 吞蚀 + JSON }冲突）。
 *  兼容 1~2 花括号（.format 后 {{capsule}}→{capsule}）；数值/bool 串强转。返 {cleanDraft, capsules:[{label,level,skill,params}]}。 */
function _extractCapsules(draft) {
  if (!draft) return { cleanDraft: '', capsules: [] };
  const capsules = [];
  const cleanDraft = String(draft).replace(/\{{1,2}capsule:([^|}]+)\|([Ll][12])\|([a-z_]+)((?:\|[^|}]+=[^|}]*)*)\}{1,2}/g, (_, label, level, skill, paramStr) => {
    const params = {};
    if (paramStr) {
      paramStr.split('|').forEach((kv) => {
        const i = kv.indexOf('=');
        if (i > 0) {
          const k = kv.slice(0, i).trim();
          let v = kv.slice(i + 1).trim();
          if (/^-?\d+$/.test(v)) v = Number(v);
          else if (v === 'true') v = true;
          else if (v === 'false') v = false;
          if (k) params[k] = v;
        }
      });
    }
    capsules.push({ label: label.trim(), level: level.toUpperCase(), skill: skill.trim(), params });
    return '';   // 剥离标记（下游 R1-R7 跑净文本）
  });
  return { cleanDraft: cleanDraft.replace(/\n{3,}/g, '\n\n'), capsules };
}

/** P1 编排·单技能路径：diagnose 选定 single 技能 → 填参 → 直接调 TOOLS[tool] → finalStep（**不进 while-loop、0 次 agentStep LLM**，p^N→p²）。
 *  缺不可默认槽/工具失败/空命中 → EXIT_GAP 诚实兜底（不赌博自纠，与降 p^N 初衷一致）。finalStep draft 过 applyQualityDefense（CB-09 D023·代码防线·取代旧 _verifyClaims+_reviseOnce）。 */
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

/** P1：deliberateStep 仅真数据缺口/降级触发（strategy≠ready）。去 method≥3 过触发（多步不再叠 Pro 研判·治串行 LLM 致超时）。
 *  仅 Pro 模式生效（harness.js:810 ctx.model==='pro' 守卫）；Flash 默认不进 deliberate。WS1 F1.2。 */
function _needsDeliberate(diagnose) {
  if (!diagnose || diagnose.degraded) return false;   // 降级诊断（可能概念问/诊断失败）不研判
  if (diagnose._forceDeliberate) return true;   // CB-09 D020 L2 胶囊：强制 Pro 确认 params（跨工具单步须研判）
  const strat = diagnose.data_plan && diagnose.data_plan.strategy;
  return !!(strat && strat !== 'ready');   // 仅真数据缺口/降级（去 method>=3 过触发）
}

/** CB-07 Layer 3：finalStep 超时/网络错的零 LLM 降级结论（基于 formatRegistry + toolHistory·治"图出但请求失败"矛盾）。 */
function _composeDegradedConclusion(toolHistoryText) {
  const _reg = (typeof getArtifacts === 'function' ? getArtifacts() : []) || [];   // v3.1 P0：同上·getArtifacts() 返数组
  const _layers = _reg.filter((r) => r.tool && r.tool !== 'query_layers').map((r) => `{{show:${r.name}}}`).join('\n');
  const _rawObs = (toolHistoryText || '').split('\n').filter((l) => /已生成|产出|单元|点|层/.test(l)).slice(-1)[0] || '';
  // Hotfix R2 S4：去「第N轮·动作: tool(params) →」原始前缀（治降级结论泄 density({...}) "代码块"·只留人读 observation）
  const _lastObs = (_rawObs.replace(/^第\d+轮·动作:[^→]*→\s*/, '').trim()) || _rawObs || '地图已生成分析图层。';
  return [
    '## 分析图已生成',
    '',
    _lastObs,
    _layers ? `\n**已产出图层**（点击查看）：\n${_layers}` : '',
    '\n详细结论暂未生成·可点击上方图层查看结果，或稍候/简化问题重试。',
  ].filter(Boolean).join('\n');
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
  // A-短期（v1.6）：density 网格语义兜底——question 含"网格/方格/grid/标准格"且不含"热力/密度"→ mode='3d'（方格网格·非热力图）。
  // diagnose(Flash) 偶尔不把"网格"映射 mode='3d'，harness 层兜底（不动 prompt）。cell_size 从 question 抽取（"1000m"→1000）。
  if (skill === 'density' && params.mode === '2d' && /网格|方格|标准格|grid/i.test(ctx.question || '') && !/热力|密度|heatmap/i.test(ctx.question || '')) {
    params.mode = '3d';
  }
  if (skill === 'density') {
    const _m = (ctx.question || '').match(/(\d+)\s*[米m]\b/i);
    if (_m && Number(_m[1]) >= 50) params.cell_size = Number(_m[1]);
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
    console.time('[emc-timing] tool:' + def.tool);   // WS1 F1.7：工具执行计时
    r = await TOOLS[def.tool](params);
    console.timeEnd('[emc-timing] tool:' + def.tool);
    obs = (r && r.observation) || '[ERR] 工具无观察返回';
    if (r && r.data && r.data.layerId) newLayerCount = 1;
  } catch (e) {
    obs = `[ERR] ${def.tool} 异常：${(e && e.message) || e}`;
  }
  // #2 tool:executed 观测信号：density 等前端委托工具不走 fetch（飞轮 geoCalls 抓不到），派发事件供 e2e-seam 观测。
  //   纯观测·不改控制流/出口/prompt；tool=skill 名（与 /geo/<name> 抽取一致）。
  if (hooks.onObservation) hooks.onObservation(obs, 1);   // CB-05 A5：工具出图后 UI 信号（runTemplatePath 原漏·地图已出但 dock dots 不停·DeepSeek 发现）
  try { document.dispatchEvent(new CustomEvent('tool:executed', { detail: { tool: skill, implTool: def.tool, layerId: (r && r.data && r.data.layerId) || null, ok: !/\[ERR\]|失败|错误/.test(obs), ts: Date.now() } })); } catch (_) { /* 观测信号失败不影响主流程 */ }
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
      // CB-09 5.242 S3：clip 失败 + 有面层（无点）→ 智能建议 extract_feature 替代（非误导"上传点数据"）
      const _hasPoly = getLayers().some((l) => l.kind === 'polygon' && l.fc && l.fc.features && l.fc.features.length);
      const _suggestExtract = def.tool === 'clip' && /无可见.*点|无已加载的情绪点层/.test(obs) && _hasPoly;
      const ask = recoverable
        ? { type: 'ask_user',
            question: _suggestExtract
              ? `${def.tool} 需要点层（裁点）·但当前只有面层。若要从面层中提取要素（如裁出西陵区），请选下方「抽取」·或上传点数据做点裁剪。`
              : `${def.tool} 没成功：${obs.replace(/^\[ERR\]\s*[^：]*：?/, '').slice(0, 140) || '返回可恢复错误'}。请按可用字段/数据重试，或说明你的具体需求。`,
            options: _suggestExtract
              ? ['用「抽取」(extract_feature) 从面层提取要素', '我来上传点数据后重试', '换一个分析方向']
              : ['我来指定正确的字段/值重试', '换一个分析方向', '看现有数据能做哪些分析？'] }
        : { type: 'ask_user',
            question: `「${_lbl}」范围内未聚合到足够的情绪点数据（可能该区无 L2 点层覆盖，或范围与数据不重叠）。要怎么处理？`,
            options: ['换一个区域重试（请指定：如伍家岗区 / 西陵区）', '我已上传该区域数据，请重新分析', '先看全域情绪分布如何？'] };
      if (hooks.onAskUser) hooks.onAskUser(ask, 1);
      return { ok: true, rounds: 1, ask, diagnose, exit: 'ask', newLayerCount };
    }
    const gapText = composeGapCard(diagnose, [obs.slice(0, 200)]);
    if (hooks.onFinalDone) hooks.onFinalDone(gapText);
    _recordSkip('tool_failed');   // ⑤④ execSkips 遥测
    return { ok: true, rounds: 1, final: gapText, defense: { degraded: true, skipped: 'template-tool-failed' }, degraded: true, diagnose, exit: 'gap', newLayerCount };
  }
  // 4. finalStep（Pro 写解题一句话 + 短结论 + {{show}}）
  if (hooks.onRound) hooks.onRound(1);
  const toolHistoryText = toolHistory.join('\n');
  // CB-09 P0-4：执行结果摘要注入 finalStep context——LLM 须基于实际执行结果写结论，非基于"计划已执行"推定
  const _execSummary = newLayerCount > 0
    ? `工具 ${def.tool} 执行成功，产出了 ${newLayerCount} 个新图层——请如实描述产出。`
    : `工具 ${def.tool} 已调用但**未产出新图层**（范围与数据可能不重叠或无可匹配要素）——结论必须如实说明"未生成图层"，严禁编造图层名或数据量。`;
  ctx.context = `【单技能路径·${_execSummary}】基于上述工具观察直接出结论，勿重选工具、勿重复执行、勿再调 geo 工具。\n【地图实际产出图层】${formatRegistry()}（严禁声称生成不在此列表的图层）\n\n` + (ctx.context || '');
  let draft;
  try {
    console.time('[emc-timing] finalStep');   // WS1 F1.7：finalStep 计时
    draft = await stages.finalStep(ctx, hooks, toolHistoryText);
    console.timeEnd('[emc-timing] finalStep');
  } catch (e) {
    if (ctx.signal && ctx.signal.aborted) throw e;   // 用户取消 → 传播
    draft = _composeDegradedConclusion(toolHistoryText);   // CB-07 Layer 3：finalStep 超时/网络 → 零 LLM 降级结论（图已出·非"请求失败"矛盾）
  }
  // 5. CB-09 D023 质量防线（L1 产物验证 + R1/R2/R3/R4/R7·代码·不调 LLM）取代旧 _verifyClaims+_reviseOnce
  const _qd = applyQualityDefense(draft, { obsOk: true, toolHistoryText, skipL1: false });
  draft = _qd.final;
  // v2 D068：plans[]→追问胶囊已禁用（打断自动执行流·后续 CPD 专题统一设计）
  // const _planCapsules = _plansToCapsules(ctx.plans);
  const _planCapsules = [];
  const _allCapsules = [...(_qd.capsules || []), ..._planCapsules];
  if (hooks.onFinalDone) hooks.onFinalDone(draft);
  if (hooks.onDefense) hooks.onDefense({ degraded: _qd.degraded, fixes: _qd.fixes, skipped: 'single-template', capsules: _allCapsules });
  return { ok: true, rounds: 1, final: draft, defense: { degraded: _qd.degraded, fixes: _qd.fixes, skipped: 'single-template', capsules: _allCapsules }, degraded: false, diagnose, exit: 'result', newLayerCount };
}

/** v2 D068 辅助：FC plans[] rank=2+ → 胶囊格式（复用 runCapsule 执行路径）。
 *  plan {rank,label,tool,params,confidence} → capsule {label,level,skill,params}
 *  level 映射：同工具=L1·跨工具=L2（runCapsule 据此决定是否 deliberate） */
function _plansToCapsules(plans) {
  if (!Array.isArray(plans)) return [];
  const _executedTool = (plans.find((p) => p.rank === 1) || {}).tool;
  return plans.filter((p) => p.rank >= 2 && p.tool && p.tool !== _executedTool).slice(0, 3).map((p) => ({
    label: p.label || p.tool,
    level: p.tool === _executedTool ? 'L1' : 'L2',
    skill: p.tool,
    params: p.params || {},
  }));
}

/** CB-09 D020 追问胶囊执行路径（L1 直达 / L2 轻判·跳 diagnose Flash）：合成 synthDiagnose → 复用 runTemplatePath 全套出口+防线。
 *  L1（同工具换参）：_forceDeliberate=false → runTemplatePath 不触发 deliberate → 0 LLM 中间轮（<2s 出图）。
 *  L2（跨工具单步）：_forceDeliberate=true → Pro 模式下 deliberateStep 确认 params 再执行（5-8s）；Flash 退化直接执行。
 *  skill 无效（concept/unknown）→ composeGapCard 兜底。params 已 R5 校验（产时）+ validateParams（执行时）双保险。
 *  CB-09 D031（5.239 CPD 收尾）：胶囊点击跳 Flash 直执 = CPD「选项点击直执」核心·追问胶囊系统实现 CPD 意图（非另造对话框）。 */
async function runCapsule(ctx, hooks, capsule) {
  const skill = capsule && capsule.skill;
  const def = stages.SKILL_DEFS[skill];
  if (!def || !def.tool) {
    const gapText = composeGapCard({ intent: 'emotion_analysis', template: skill }, ['胶囊工具不可执行：' + skill]);
    if (hooks.onFinalDone) hooks.onFinalDone(gapText);
    return { ok: true, rounds: 0, final: gapText, defense: { degraded: true, fixes: [], skipped: 'capsule-bad-skill', capsules: [] }, degraded: true, diagnose: { degraded: true, intent: 'emotion_analysis', _capsule: true }, exit: 'gap', newLayerCount: 0 };
  }
  const synthDiagnose = {
    template: skill,
    params: (capsule.params && typeof capsule.params === 'object') ? capsule.params : {},
    degraded: false,
    intent: skill === 'concept' ? 'general' : (/^(clip|extract_feature|overlay|merge|buffer|filter_attr|area_stats)$/.test(skill) ? 'gis_operation' : 'emotion_analysis'),   // CB-09 5.242 S6：按 skill 推导（非硬编码 emotion_analysis·治 gis 胶囊误注入 emotion intent）
    domain_lens: [],
    scale: 'macro',
    data_plan: { needed: [], available: [], gap: [], strategy: 'ready' },
    method: [],
    _capsule: true,
    _forceDeliberate: capsule.level === 'L2',
  };
  return await runTemplatePath(ctx, hooks, synthDiagnose);
}

/** E1（5.210）：多步链确定性执行（0 中间 LLM 轮·治 C3 多步超时）。类比 runTemplatePath 循环 chain.steps；
 *  复用 $n（_stepResults·工具内 ref 自动解析）+ setToolContext + runTemplatePath 出口范式（失败 ask/gap·成功 finalStep+_verifyClaims）。
 *  链中断（步失败）→ ask_user；零图层 → ask_user；成功 → finalStep 出结论。chain 来自 stages.CHAIN_REGISTRY。 */
async function runChainPath(ctx, hooks, diagnose, chain) {
  resetStepResults();   // 清 $n 引用（新一轮）
  const toolHistory = []; let newLayerCount = 0; const failedObs = []; let hasRows = false;   // CB-09 5.242 S9：hasRows（分析型链步产 rows 非 layer·治 zonal→rank 链误判失败）
  for (let i = 0; i < chain.steps.length; i++) {
    const step = chain.steps[i];
    if (hooks.onRoundStart) hooks.onRoundStart(i + 1);
    setToolContext({ tool: step.tool, round: i + 1 });
    const params = _resolveChainParams(step.params, diagnose && diagnose.params, ctx.question);
    let r = null;
    try { r = await TOOLS[step.tool](params); }   // 工具内 addResultLayer 自动推 _stepResults → 后序 $n 可解析
    catch (e) { failedObs.push(`${step.tool}: ${(e && e.message) || e}`); break; }   // 链中断
    const obs = (r && r.observation) || '[ERR] 工具无观察返回';
    if (/\[ERR\]|失败|错误/.test(obs)) { failedObs.push(`${step.tool}: ${obs.slice(0, 80)}`); break; }   // 步失败中断
    if (r && r.data && r.data.layerId) newLayerCount++;
    if (r && r.data && Array.isArray(r.data.rows) && r.data.rows.length) hasRows = true;
    toolHistory.push(`第${i + 1}轮·动作: ${step.tool}(${JSON.stringify(params).slice(0, 120)}) → ${obs}`);
    if (hooks.onObservation) hooks.onObservation(obs, i + 1);
    try { document.dispatchEvent(new CustomEvent('tool:executed', { detail: { tool: step.tool, layerId: (r && r.data && r.data.layerId) || null, ok: !/\[ERR\]|失败/.test(obs), ts: Date.now() } })); } catch (_) { /* 观测信号失败不阻塞 */ }
  }
  // 链中断/零图层 → ask_user（守 Smart 不放弃·同 runTemplatePath :345-356）·S9：hasRows（分析型链步）非空不算失败
  if (failedObs.length || (newLayerCount === 0 && !hasRows)) {
    const _tried = failedObs.slice(0, 2).map((f) => String(f).split(':')[0]).join('、');
    const ask = { type: 'ask_user',
      question: `${chain.name}（${chain.steps.map((s) => s.tool).join('→')}）没跑通${_tried ? `（${_tried} 失败）` : '（未产出图层）'}——可能是范围与数据不匹配。要怎么处理？`,
      options: ['换个区域/范围重试（请指定）', '我已上传所需数据，请重新分析', '用现有数据能做哪些分析？'] };
    if (hooks.onAskUser) hooks.onAskUser(ask, chain.steps.length);
    _recordSkip('chain_failed');
    return { ok: true, rounds: chain.steps.length, ask, diagnose, exit: 'ask', newLayerCount };
  }
  // finalStep + 对账（同 runTemplatePath :362-375）
  if (hooks.onRound) hooks.onRound(chain.steps.length);
  const toolHistoryText = toolHistory.join('\n');
  // CB-09 P0-4：多步链执行结果摘要——告知 LLM 实际完成了几步、产出多少图层
  const _chainExecSummary = `多步链 ${chain.steps.map((s) => s.tool).join(' → ')} 已全部执行完成，共产出 ${newLayerCount} 个新图层——请如实描述每步产出。`;
  ctx.context = `【多步链路径·${_chainExecSummary}】基于上述工具观察直接出结论，勿重选工具、勿重复执行、勿再调 geo 工具。\n【地图实际产出图层】${formatRegistry()}（严禁声称生成不在此列表的图层）\n\n` + (ctx.context || '');
  let draft;
  try {
    draft = await stages.finalStep(ctx, hooks, toolHistoryText);
  } catch (e) {
    if (ctx.signal && ctx.signal.aborted) throw e;   // 用户取消 → 传播
    draft = _composeDegradedConclusion(toolHistoryText);   // CB-07 Layer 3：finalStep 超时/网络 → 零 LLM 降级结论（图已出·非"请求失败"矛盾）
  }
  // CB-09 D023 质量防线（L1 + R 规则·代码·取代旧 _verifyClaims+_reviseOnce）
  const _qd = applyQualityDefense(draft, { obsOk: true, toolHistoryText, skipL1: false });
  draft = _qd.final;
  if (hooks.onFinalDone) hooks.onFinalDone(draft);
  if (hooks.onDefense) hooks.onDefense({ degraded: _qd.degraded, fixes: _qd.fixes, skipped: 'chain', capsules: _qd.capsules || [] });
  return { ok: true, rounds: chain.steps.length, final: draft, defense: { degraded: _qd.degraded, fixes: _qd.fixes, skipped: 'chain', capsules: _qd.capsules || [] }, degraded: false, diagnose, exit: 'result', newLayerCount };
}
/** E1：chain step params 模板 → 实参。{占位} 填值（问句/diagnose.params）；$n 原样（工具内 ref 解析）。 */
function _resolveChainParams(template, diagnoseParams, question) {
  const out = {};
  for (const k of Object.keys(template || {})) {
    const v = template[k];
    if (typeof v === 'string' && /^\{(\w+)\}$/.test(v.trim())) {
      out[k] = _fillChainSlot(v.trim().slice(1, -1), diagnoseParams, question);
    } else { out[k] = v; }   // $n / 字面值（$n 工具内 ref 解析）
  }
  return out;
}
/** E1：{question}→抽区名（extract_feature where 用）；{boundary}/{land}→diagnose.params。 */
function _fillChainSlot(key, diagnoseParams, question) {
  if (key === 'question') {
    const m = (question || '').match(/(西陵|伍家岗|夷陵|点军|猇亭)区?/);
    return m ? m[1] + '区' : (question || '');
  }
  if (diagnoseParams && diagnoseParams[key] != null) return diagnoseParams[key];
  return '';
}
/** E1（5.210）：问句 + diagnose → 标准多步链（CHAIN_REGISTRY triggers 匹配·首个命中·顺序即优先级·同 B_TRACK_PARADIGM 范式）。未命中 null（落 while-loop ReAct 兜底）。 */
function _deriveChainId(question, diagnose) {
  const q = String(question || '');
  for (const c of stages.CHAIN_REGISTRY) {
    if (c.triggers.some((t) => t.test(q))) return c;
  }
  return null;
}

const _GEO_TOOLS = ['extract_feature', 'overlay', 'clip', 'filter_attr', 'merge', 'buffer', 'zonal_stats', 'rank', 'area_stats', 'nearest', 'hotspot', 'ensure_zone'];   // CB-09 D015（5.242 补 ensure_zone·F3 完整性 gate 统计）
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

/** D2（5.207）：diagnose 卡 template+params → 计划工具序列（代码确定性·非 LLM 兜底）。
 *  Flash 偶发输出 method；未输出时按 template 派生，让 _plannedGeoSteps(F3 完整性 gate)/
 *  formatDiagnoseSummary/_needsDeliberate 皆有源（Smart/Dumb 铁律：代码可知不靠 LLM）。
 *  元素格式 'tool()' 兼容 _plannedGeoSteps 的 `tool(` 匹配。
 *  single→[tool()]；multi→params.chain 元素补()；concept/unknown→[]。 */
function deriveDiagnoseMethod(template, params) {
  if (!template || template === 'concept' || template === 'unknown') return [];
  if (template === 'multi') {
    const chain = (params && params.chain) || [];
    return Array.isArray(chain) ? chain.map((t) => (String(t).includes('(') ? String(t) : String(t) + '()')) : [];
  }
  const def = stages.SKILL_DEFS[template];
  return def && def.tool ? [def.tool + '()'] : [];
}

/**
 * Agent Loop 一次问答。
 * @param ctx    {question, context(grounding), contextTokens, signal, model}
 * @param hooks  渲染回调（panel.js 实现）：
 *   onReason(tok, round)       — reasoning 思考链增量（round 标识所属轮，0=最终阶段）
 *   onDiagnose(card)           — 问题理解卡（DIAGNOSE 前置步；{degraded:true}=降级）
 *   onRoundStart(round)        — 每轮开始（Pro 模式新建 reasoning 分段块）
 *   onThought(text, round)     — 第 round 轮 thought
 *   onAction(action, round)    — 第 round 轮 action
 *   onAskUser(action, round)   — 第 round 轮 ask_user（主动问澄清，渲染问题+选项胶囊，挂起 loop）
 *   onObservation(text, round) — 第 round 轮工具观察
 *   onFinal(tok)               — 草稿结论增量
 *   onFinalDone(text)          — 草稿完成
 *   onDefense(defense)         — 质量防线结果 {degraded, fixes, skipped}（CB-09 D023·取代旧 onReview/onRevise*）
 *   onDegraded(text)           — finalStep 也失败时的最终降级
 * @returns {Promise<{ok, degraded?, rounds?, final?, defense?}>}
 */
export async function orchestrate(ctx, hooks = {}) {
  if (ctx && ctx.capsule) return runCapsule(ctx, hooks, ctx.capsule);   // CB-09 D020 胶囊点击跳 diagnose Flash·直达 runCapsule（L1 0 轮/L2 Pro 确认）
  // ══ 编排器·确定性裁定（Smart Agent/Dumb Tool 内核 · CLAUDE.md「AI·Copilot 开发内核」铁律3：不调 LLM、只接线）══
  // 流程：Smart·计划（diagnose 意图卡）→ 编排器分流（短路 / plan-once-execute / ReAct 兜底）→ Dumb·执行（SKILL/TOOLS 纯参数化）→ 三态出口代码裁定（result/gap/concept）。详见 docs/copilot-architecture.md。
  const toolHistory = [];   // 每轮压缩摘要（注入下轮 prompt）
  let round = 1;
  let degraded = false;
  let forcedContinues = 0;   // F3 完整性 gate 强制续做计数（max 1，防 agent 0 工具就 answer）
  let successObs = 0;        // 三态出口：成功观察数（非失败）
  let newLayerCount = 0;     // 三态出口：本轮新生成图层数（工具 data.layerId 计）
  let hasRows = false;        // 三态出口：本轮分析型产出行数（zonal/rank 等·非图层）
  let narrations = 0;        // 叙述检测：模型只写说明没给动作的轮数（>1 视失败）
  let answered = false;      // 模型是否 deliberate `answer`（概念问等可零工具直答；_hardFail 不得覆盖它）
  let narratedAnswer = false; // 模型持续叙述（prose 作答，常见于概念问）——叙述≠失败，交 finalStep 出结论，不落 GAP
  const failedObs = [];      // 失败观察摘要（EXIT_GAP 卡展示「已尝试」用）
  ctx.answerModel = ctx.model || 'flash';  // B1-2a：答案跟随用户选择（Pro用Pro、Flash用Flash）；复杂任务 diagnose 后不降级
  const _deadline = Date.now() + 30000;   // WS1 F1.5：单问总预算 30s（while-loop 守卫·超时强制作答；原 75s 远超设计 6-11s 致用户感 60s+）

  // 多轮连续性：近 2-3 轮 trace 蒸馏注入 ctx.context 顶部（B2：5.51 单轮 priorTurn → 多轮滚动 turnHistory，意图收敛轨迹）
  const _histCtx = formatTurnHistory(ctx.turnHistory) || formatPriorTurn(ctx.priorTurn);
  if (_histCtx) ctx.context = _histCtx + '\n\n' + (ctx.context || '');

  // P0 降温：_quickIntent 轻量预判——高置信通用/概念问跳 diagnose 直 finalStep（省整轮 diagnose LLM + 7字段卡）
  if (!ctx.resume && _quickIntent(ctx.question) === 'general') {
    ctx.context = '【intent=通用问答·快速预判】直接简洁作答，不要 4×5 归因、不要演示逻辑链、不要引导情绪场景。\n\n## 情绪地图背景（概念问时参考·灵活改写勿照抄）\n随着"人民城市"理念的深入实践，城市建设正在从"见物"向"见人"转变。城市规划行业从"造城"到"营城"的理念升华，要求从"地上建城"到"城上建城、依城养城、以城兴城"。宜昌市委、市政府多次强调要关注城市的"温情治理"、"情绪价值"和"年轻范"，明确提出"打造精致温暖的现代化活力之城"、"激发城市年轻活力"等发展目标。\n\n情绪地图正是这一理念的技术实践——把居民在社交媒体、12345热线等平台表达的情感（开心、愤怒、抱怨、期盼等）精准定位到地理坐标，构建一个可展示、可交互的"城市心情"动态地图。它让人直观看到哪个区域居民幸福感高、哪里抱怨集中，并揭示情绪背后老百姓的"急难愁盼"（设施不足、环境不好、文化不显、治理不优），从而用数据替代直觉，为城市"规划、更新、运营、治理"四大领域提供"人本视角"的科学决策依据。\n\n城市情绪是城市中所有个体情绪状况的集合，是居民在工作、生活、娱乐等场景中内心需求的直接表征。情绪地图基于多源城市情绪数据（社交媒体、App数据）与时空信息（地理信息、建成环境数据）的叠加融合，构建一套反映城市情绪时空分布及其与建成环境关联的可视化分析工具。\n\n' + (ctx.context || '');
    const draft = await stages.finalStep(ctx, hooks, '');
    if (hooks.onFinalDone) hooks.onFinalDone(draft);
    if (hooks.onDefense) hooks.onDefense({ degraded: false, skipped: 'quick-general' });
    return { ok: true, rounds: 0, final: draft, defense: { degraded: false, skipped: 'quick-general' }, degraded: false, diagnose: { degraded: true, intent: 'general', quick: true } };
  }

  // 指代解析（NL 预处理·5.212·几 ms·非 LLM）：检测"这边/刚才"→ grounding 显式标注聚焦对象·让 diagnose 不靠猜
  const _coref = resolveCoref(ctx.question, ctx.priorTurn);
  if (_coref) ctx.context = _coref + '\n\n' + (ctx.context || '');
  // CB-09 5.242：结构化 layer_meta（{has_point,has_polygon}）喂 select_candidates → _filter_by_context 激活（解 context=None 数据盲·治「剪裁面层误路由 clip」类问题）
  const _ls = getLayers();
  ctx.layerMeta = {
    has_point: _ls.some((l) => l.kind === 'point' && l.fc && l.fc.features && l.fc.features.length),
    has_polygon: _ls.some((l) => l.kind === 'polygon' && l.fc && l.fc.features && l.fc.features.length),
  };
  // v2 D065：数据变化检测——图层数/字段变了 → 清空上轮 plans（CPD 跨轮复用失效·需重新 FC）
  const _dataSig = _ls.map((l) => `${l.id}:${(l.fc && l.fc.features || []).length}:${l.kind}`).join('|');
  if (ctx.priorTurn && ctx.priorTurn._dataSig && ctx.priorTurn._dataSig !== _dataSig) {
    if (ctx.plans) ctx.plans = null;   // 清空 plans·CPD 选项失效
    if (hooks.onObservation) hooks.onObservation('[数据变化] 已更新图层·建议重新分析', 0);
  }
  ctx._dataSig = _dataSig;   // 存入 trace → turnHistory（跨轮对比用）
  // 【Smart·计划阶段】v2 function calling 诊断（5.243·D041）：单次 LLM + FC + 契约 Schema
  // 替代旧三阶段（select_candidates → FILL_CARD/PLAN → dispatch SSE）
  // FC 失败（网络/无 tool_calls）→ degraded·harness 降级走旧 SSE diagnose 或 while-loop

  // CB-05 ROOTCAUSE 方案 4：追问时 plans[] 优先匹配（跳 FC·复用上轮正确参数·治层引用幻觉）
  if (ctx.resume && ctx.priorTurn && Array.isArray(ctx.priorTurn.plans) && ctx.priorTurn.plans.length) {
    const _matched = _matchPlanToQuestion(ctx.question, ctx.priorTurn.plans);
    if (_matched) {
      console.info('[plans] 追问匹配上轮 plan·跳 FC·直接执行:', _matched.tool, _matched.params);
      const _synthDiag = {
        template: _TOOL_TO_SKILL[_matched.tool] || _matched.tool,
        params: _matched.params || {},
        degraded: false, intent: 'emotion_analysis', _fc: true, _plansReuse: true,
        domain_lens: [], scale: 'macro', decision_type: '操作', outlet: '生成图层',
        data_plan: { needed: [], available: [], gap: [], strategy: 'ready' },
        method: [(_matched.tool || '') + '()'],
      };
      return await runTemplatePath(ctx, hooks, _synthDiag);
    }
  }

  // L0 数据门：先用代码检查数据是否满足提问的最小要求——缺数据直接告诉用户，不浪费 LLM 调用
  const _dataGap = _dataGate(ctx.question, ctx.layerMeta);
  if (_dataGap) {
    const _gapText = buildRequestUploadText({ data_plan: { needed: [_dataGap], gap: [_dataGap], strategy: 'request_upload' } });
    if (hooks.onFinalDone) hooks.onFinalDone(_gapText);
    if (hooks.onDefense) hooks.onDefense({ degraded: false, skipped: 'data-gate' });
    return { ok: true, rounds: 0, final: _gapText, defense: { degraded: false, skipped: 'data-gate' }, degraded: false, diagnose: { degraded: true, _dataGate: true }, exit: 'gap', newLayerCount: 0 };
  }

  let diagnose = null;
  try {
    console.time('[emc-timing] fcDiagnose');   // WS1 F1.7：per-phase 计时（定位真实瓶颈）
    diagnose = await stages.fcDiagnoseStep(ctx, hooks);
    console.timeEnd('[emc-timing] fcDiagnose');
  } catch (e) { diagnose = null; }
  // P0：FC 诊断失败 → 不入旧 SSE（旧预选工具常选错·对面层数据必失败），直接走 while-loop 兜底
  if (!diagnose || diagnose.degraded) {
    console.warn('[FC] 诊断失败·不入旧 SSE', diagnose?._fcError || '');
    diagnose = { degraded: true, _fcError: diagnose?._fcError || 'fc_failed' };
    // L2 确定性恢复：FC 失败 → 尝试用关键词+数据状态构造 diagnose（不调 LLM）
    const _recovered = _deterministicRecover(ctx);
    if (_recovered) {
      diagnose = _recovered;
      if (hooks.onObservation) hooks.onObservation('[恢复] FC 失败 → 确定性匹配 → 直执行', 0);
      console.log('[recover] matched:', diagnose.template, JSON.stringify(diagnose.params || {}).slice(0, 120));
    }
  }
  // v2 D068：FC 产出的 plans[] 存入 ctx.plans·供 finalStep（追问胶囊）+ CPD（选项展示）共享
  if (diagnose.plans && diagnose.plans.length) {
    ctx.plans = diagnose.plans;
  }
  // v3 H6：前端 _validateFcParams 已删——信赖后端 validate_tool_call（router fc_diagnose 已校验）。
  // D2（5.207）：method 确定性派生兜底——Flash 偶发输出 method；未输出时按 template 派生，
  // 让 _plannedGeoSteps(F3 完整性 gate)/formatDiagnoseSummary/_needsDeliberate 皆有源。
  if (!diagnose.degraded && (!Array.isArray(diagnose.method) || diagnose.method.length === 0)) {
    diagnose.method = deriveDiagnoseMethod(diagnose.template, diagnose.params);
  }
  // domain_lens 结构化数组回传后端：post-diagnose step（answer/agent_step/diagnose）据此注入
  // 命中领域完整权威语境。过滤 'general'（通用问答无需领域权威）。_quickIntent 路径跳过 diagnose
  // → 此处未设 → 各 step 读 undefined → 不注入（正确，通用问答无需领域权威）。
  ctx.domainLens = Array.isArray(diagnose.domain_lens)
    ? diagnose.domain_lens.filter((k) => k && k !== 'general') : [];
  // B1-2a：复杂任务（strategy≠ready / method≥3 步）且用户 pro 模式 → 答案升 pro reasoner（复用 _needsDeliberate 复杂度门控）
  if (ctx.model === 'pro' && _needsDeliberate(diagnose)) ctx.answerModel = 'pro';
  // R1-D1 派生判定器（代码确定性·治假 GAP·Smart/Dumb 铁律：代码可知不问 LLM）：问句区名属已加载 boundary 子要素 → 强制 strategy=ready（挡 :488 假 GAP 短路）
  // D1 扩覆盖（5.206·治 s1 残余·INT-003/004/006）：request_upload + strategy 缺失（unknown·diagnose 未明确完备性）→ 派生判定·代码可知区名即 ready
  if (!diagnose.degraded && diagnose.data_plan && (diagnose.data_plan.strategy === 'request_upload' || !diagnose.data_plan.strategy)) {
    const _deriv = deriveAvailable(ctx.question, getLayers());
    if (_deriv) {
      diagnose.data_plan.strategy = 'ready';
      if (hooks.onObservation) hooks.onObservation(`[派生] 「${_deriv.name}」属已加载「${_deriv.layer}」(${_deriv.field}) 子要素 → clip/extract 可派生，strategy=ready`, 0);
    }
  }
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
        if (hooks.onDefense) hooks.onDefense({ degraded: false, skipped: 'general' });
        return { ok: true, rounds: 0, final: draft, defense: { degraded: false, skipped: 'general' }, degraded: false, diagnose };
      }
      if (intent === 'gis_operation') {
        ctx.context = '【intent=纯GIS操作】用 geo 工具（extract_feature/clip/filter_attr/overlay/merge/buffer）完成操作，出口=新图层（自动落地图）。不要 4×5 归因报告、不受尺度范式约束；操作完成后简述产出了什么图层即 answer。\n\n' + (ctx.context || '');
      }
      // 硬缺口短路：不硬答，直接出"请求上传"为结论
      if (diagnose.data_plan && diagnose.data_plan.strategy === 'request_upload') {
        const tpl = buildRequestUploadText(diagnose);
        if (hooks.onFinalDone) hooks.onFinalDone(tpl);
        if (hooks.onDefense) hooks.onDefense({ degraded: false, skipped: 'request_upload' });
        return { ok: true, rounds: 0, final: tpl, defense: { degraded: false, skipped: 'request_upload' }, degraded: false, diagnose };
      }
    }
  }

  // 【Dumb·执行阶段】P1 编排：
  // D057：_allToolCalls 有多个条目 → 直接批量执行（0 LLM 中间轮·L2 恢复/FC 多工具共用）
  if (!diagnose.degraded && Array.isArray(diagnose._allToolCalls) && diagnose._allToolCalls.length > 1) {
    return await runAllToolCalls(ctx, hooks, { ...diagnose });
  }
  // CB-09：单工具执行后，代码自动检测是否需要补全剩余步骤（不依赖 LLM 产出 plans）
  if (!ctx.resume && !diagnose.degraded && diagnose.template) {
    const _tdef = stages.SKILL_DEFS[diagnose.template];
    if (_tdef && _tdef.category === 'single' && _tplHitRateReady()) {
      const _result = await runTemplatePath(ctx, hooks, diagnose);
      // 代码自动扩展：检测多目标空间裁剪模式 → 生成剩余 overlay 步骤
      if (_result && _result.exit === 'result' && !_result.degraded && _result.newLayerCount > 0) {
        const _expanded = _autoExpandOverlays(ctx, hooks, diagnose, _result);
        if (_expanded) return _expanded;
      }
      return _result;
    }
    if (diagnose.chain) return await runChainPath(ctx, hooks, diagnose, diagnose.chain);  // CB-09 D009+D012（5.237）Phase C: Pro 产复合链优先·不受 Flash hit-rate gate（Pro 非 Flash）
    if (diagnose.template === 'multi' && _tplHitRateReady()) {                     // E1（5.210）：Flash multi 固定链分流（治 C3 多步超时）
      const _chain = _deriveChainId(ctx.question, diagnose);
      if (_chain) return await runChainPath(ctx, hooks, diagnose, _chain);          // 命中 → 0 LLM 轮确定性链（治 C3）
    }                                                                              // 未命中落 while-loop（ReAct 兜底）
  }

  // P0 降温：intent-aware 轮数上限（diagnose 后定）。B=6 多目标完整性，A/C=4 降概率链。
  // CB-06 L1：生成类请求（生成/出图/网格/方格/分析图）缩轮到 2-3（漏网 while-loop 也少浪费·DeepSeek）
  const _IS_GEN = /生成|出图|做图|热力图|网格|方格|分析图|画图|画一个|分布图|聚合图/.test(ctx.question || '');
  const maxRounds = (!diagnose.degraded && diagnose.intent === 'gis_operation')
    ? (_IS_GEN ? 3 : MAX_ROUNDS_GIS)
    : (_IS_GEN ? 2 : MAX_ROUNDS_OTHER);
  // Track 1 query-first：round 0 注入数据 schema 探查 observation（零 LLM，复用 TOOLS.query_layers）——
  // manifesto "先 query 后操作" 的代码落地：schema 本已在 ctx.context（buildContext send 时注入），
  // 此处把已加载层名+计数作为一条 observation 推入 toolHistory，迫使 round1 agentStep 的 thought "看见"数据，免盲目调错工具/字段/层。
  if (!ctx.resume) {
    try { toolHistory.push(`第0轮·数据探查：${TOOLS.query_layers({}).observation}`); }
    catch (e) { /* query_layers 无 data 不计 newLayerCount、无副作用，失败静默不阻塞主流程 */ }
  }
  while (round <= maxRounds) {
    if (Date.now() > _deadline) {   // B1-2c 预算守卫：超 75s 强制作答（narratedAnswer=true → post-loop 走 finalStep 出已执行结果，非 GAP/超时无答）
      toolHistory.push('⚠️ 已达单问预算（75s），用已执行步骤的结果作答，不再续轮。');
      narratedAnswer = true;
      break;
    }
    if (hooks.onRound) hooks.onRound(round);
    if (hooks.onRoundStart) hooks.onRoundStart(round);
    let toolHistoryText = toolHistory.length ? toolHistory.join('\n') : '';
    // A3：上一步失败 → 头部加换法重试提示（避免重复同样失败调用）
    if (toolHistory.length && /\[ERR\]|失败|错误/.test(toolHistory[toolHistory.length - 1])) {
      toolHistoryText = '⚠️ 上一步工具失败（见观察末尾）。换参数（字段名/preset/range）或换工具重试，勿重复同样失败调用。\n\n' + toolHistoryText;
    }

    // CB-06 P0-A：agent_step throw（LLM 超时/网络·非用户取消）→ 降级·不丢图·不"请求失败"（复用 _deadline 降级范式 :628）
    let step;
    try {
      step = await stages.agentStep(ctx, hooks, round, toolHistoryText);
    } catch (e) {
      if (ctx.signal && ctx.signal.aborted) throw e;   // 用户主动取消 → 传播（panel 显"已停止"·不降级）
      toolHistory.push(`⚠️ 第${round}轮 LLM 调用失败（${(e && e.message) || e}）——用已执行步骤的结果作答，不再续轮。`);
      narratedAnswer = true; degraded = true; break;   // LLM 超时/网络错 → 降级走 finalStep 出已执行结果（图+结论·非"请求失败"丢图）
    }
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
    // CB-06 P1-C：生成类 + 工具已产出 + Flash 还 query_* 验证 → 早终止（图已出·不容忍纠结·break finalStep）
    if (_IS_GEN && newLayerCount > 0 && step.action.type === 'tool' && /^query_/.test(step.action.name || '')) {
      if (hooks.onObservation) hooks.onObservation('[早终止] 分析图已生成·无需 query 验证·直接出结论', round);
      break;
    }

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
    // CB-06 L2：生成类 + 工具产出图层 → toolHistory 追加完成信号（系统级·治 Flash 不知"任务完成"·DeepSeek）
    if (_IS_GEN && newLayerCount > 0) {
      toolHistory[toolHistory.length - 1] += '\n[系统] 已生成用户要求的分析图层。如无进一步操作需求，请直接 answer——勿再 query/verify 验证。';
    }
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

  // CB-09 P0-4 治本（v2）：零图层+零分析行 → 跳过 LLM finalStep，直接用确定性诚实结论。
  // 根因：v1 只在 context 加提示，LLM 仍会忽略。治本：不调 LLM——零产出时无内容需"总结"。
  if (newLayerCount === 0 && !hasRows) {
    const _honestText = composeGapCard(diagnose, failedObs)
      + '\n\n---\n**诚实结论**：本轮未产出新图层。'
      + '\n\n请尝试：① 换一种问法（更具体地指定范围和目标）② 确认所需数据已加载（点开 Layers 面板检查）③ 缩小分析范围后重试。';
    if (hooks.onFinalDone) hooks.onFinalDone(_honestText);
    if (hooks.onDefense) hooks.onDefense({ degraded: true, skipped: 'zero-output' });
    _recordSkip('zero_output');
    return { ok: true, rounds: round, final: _honestText, defense: { degraded: true, skipped: 'zero-output' }, degraded: true, diagnose, exit: 'gap', newLayerCount };
  }

  // ④ 注入 registry 真值清单 + 执行结果摘要（finalStep 共用同 ctx.context）：
  //   CB-09 P0-4——LLM 须基于实际执行结果写结论，非基于 plan 推定（治 finalStep 假结论 B002/B004/B005）
  const _loopExecSummary = newLayerCount > 0
    ? `本轮共产出 ${newLayerCount} 个新图层——请如实描述产出。`
    : `本轮**未产出任何新图层**——结论必须如实说明"未生成图层"，严禁编造图层名或声称已产出。`;
  ctx.context = `【${_loopExecSummary}】【地图实际产出图层】${formatRegistry()}（严禁声称生成不在此列表的图层；任务未完成改述"未生成/未产出"，不得编造图层名与数字）\n\n` + (ctx.context || '');
  try {
    draft = await stages.finalStep(ctx, hooks, toolHistoryText);
  } catch (e) {
    if (hooks.onDegraded) hooks.onDegraded('');
    return { ok: false, degraded: true, rounds: round };
  }
  // CB-09 D022 finalStep 防漂移（代码兜底·删 LLM revise）：action-JSON / ```围栏 = 格式漂移，直接走 drift 卡（不再 _reviseOnce 重写）。
  // EMC 结论设计上无代码块（图表走内联 {chart}/{fig} 指令，勿围栏）；drift = 模型失序 → 代码拦截 + 引导重试。
  const _driftRe = /^\s*(?:```(?:json)?\s*)?\{[\s\S]*"(?:thought|action)"[\s\S]*\}\s*```?\s*$/i;
  const _hasFence = /```/.test(draft);
  if (_driftRe.test(draft.trim()) || _hasFence) {
    const _driftText = '## 未能生成可读结论\n\n模型在最终回答阶段输出了代码块/工具调用指令而非可读结论，已拦截未显示。\n\n**建议**：换一种问法或缩小范围（指定某区、某类用地、某时点）后重试。';
    if (hooks.onFinalDone) hooks.onFinalDone(_driftText);
    if (hooks.onDefense) hooks.onDefense({ degraded: true, fixes: [{ rule: 'drift', action: 'intercept' }], skipped: 'drift' });
    return { ok: false, degraded: true, rounds: round, final: _driftText, defense: { degraded: true, skipped: 'drift' }, diagnose, exit: 'drift' };
  }
  // ⑤ pre-finalStep 结构化对账（intent 无关，P0b 宽容版）：missing<=2 → 保 draft + 自动标注（体验>正确性，不丢整答案）；missing>=3 大面积谎报 → 退 gap
  const _claimed = _extractClaimedLayers(draft);
  if (_claimed.length) {
    const _actualNames = getLayers().filter((l) => l.name && (l._renderState || 'ok') === 'ok').map((l) => l.name);   // E3：渲染失败层（_renderState≠ok·入列表但地图未真渲染）不计"实际产出"→ 声称的若渲染失败=missing→EXIT_PARTIAL 标注（治假完成制度化）
    const _missing = _claimed.filter((c) => !_actualNames.some((a) => a === c || a.includes(c) || c.includes(a)));
    if (_missing.length >= 3) {
      const _gapText = composeGapCard(diagnose, failedObs) + '\n\n---\n**⚠️ 诚实拦截**：草稿声称已生成「' + _missing.map(_esc).join('、') + '」等图层，但地图实际图层为 [' + (_actualNames.map(_esc).join('、') || '无') + ']，大面积谎报，请用 geo 工具真正生成后再回答。';
      if (hooks.onFinalDone) hooks.onFinalDone(_gapText);
      if (hooks.onDefense) hooks.onDefense({ degraded: true, skipped: 'drift' });
      return { ok: false, degraded: true, rounds: round, final: _gapText, defense: { degraded: true, skipped: 'drift' }, diagnose, exit: 'drift' };
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
  // CB-05 A4 空答案检测（代码门·防"只说不做"·工具已产出但结论过短 → 补引导·补 _verifyClaims 漏的纯叙述无工具）
  if (newLayerCount > 0 && draft.replace(/[#\s\-*]/g, '').length < 20) {
    draft = `## 地图已产出图层\n\n工具已执行（地图已更新），但结论文本过短。请查看地图/EMC 组的产出图层，或换一种问法。\n\n${draft}`;
  }
  if (hooks.onFinalDone) hooks.onFinalDone(draft);

  // EXIT_PARTIAL 裁定（体验>正确性·四态出口第四态）：仅对账少量 missing（_isPartialMissing）= 真"做成一部分"。
  //   软缺口 strategy=fallback_annotated 用替代数据仍可完整作答 → 走正常质量防线 + EXIT_RESULT，不属此态。
  if (_isPartialMissing) {
    const _pIntent = diagnose && !diagnose.degraded ? (diagnose.intent || 'emotion_analysis') : 'emotion_analysis';
    if (_pIntent === 'gis_operation') {
      // CB-09 D023：_extractClaimedLayers 已标注 missing → skipL1:true 防双重；R2/R4/R7 仍跑
      const _pQd = applyQualityDefense(draft, { obsOk: newLayerCount > 0, toolHistoryText, skipL1: true });
      draft = _pQd.final;
    }
    if (hooks.onDefense) hooks.onDefense({ degraded: true, skipped: 'partial' });
    return { ok: true, rounds: round, final: draft, defense: { degraded: true, skipped: 'partial' }, degraded: true, diagnose, exit: 'partial', newLayerCount };
  }

  // intent=纯GIS操作：质量防线（L1+R 规则·代码兜底·_extractClaimedLayers 已标注→skipL1:true）
  const _intent = diagnose && !diagnose.degraded ? (diagnose.intent || 'emotion_analysis') : 'emotion_analysis';
  if (_intent === 'gis_operation') {
    const _gQd = applyQualityDefense(draft, { obsOk: successObs > 0 || newLayerCount > 0, toolHistoryText, skipL1: true });
    draft = _gQd.final;
    return { ok: true, rounds: round, final: draft, defense: { degraded: _gQd.degraded, fixes: _gQd.fixes, skipped: 'gis_operation', capsules: _gQd.capsules || [] }, degraded, diagnose, exit: 'result', newLayerCount };
  }

  // CB-09 D023 质量防线（删旧 R+R·reviewStep/REVIEW_ENABLED/_reviseOnce 全去）：L1+R1/R2/R3/R4/R7+L3 代码兜底
  // _extractClaimedLayers 对账（:864）已标注 missing → skipL1:true；R2/R3/R4/R7 仍跑
  const _fQd = applyQualityDefense(draft, { obsOk: successObs > 0 || newLayerCount > 0, toolHistoryText, skipL1: true });
  const final = _fQd.final;
  if (hooks.onDefense) hooks.onDefense({ degraded: _fQd.degraded, fixes: _fQd.fixes, skipped: 'result', capsules: _fQd.capsules || [] });
  return { ok: true, rounds: round, final, defense: { degraded: _fQd.degraded, fixes: _fQd.fixes, skipped: 'result', capsules: _fQd.capsules || [] }, degraded, diagnose, exit: 'result', newLayerCount };
}

/** L0 数据门：提问需要什么类型的数据 → 比对已加载数据 → 缺什么直接告诉用户。
 *  纯代码，不调 LLM，<1ms。只做"显然缺数据"的判断——不确定就放行。 */
function _dataGate(question, layerMeta) {
  const q = question || '';
  const lm = layerMeta || {};
  // 用地/面层查询 → 需要 polygon 面层（不只是行政区边界）
  if (/用地|地块|土地/.test(q) && !lm.has_polygon) return '用地面层数据（如商业用地、居住用地等 Shapefile/GeoJSON）';
  // 情绪点查询 → 需要 point 数据
  if (/情绪点|点位/.test(q) && !lm.has_point) return '情绪点数据（含极性字段的点图层）';
  return null;
}

/** L2 确定性恢复：FC 失败 → 用关键词 + 已加载数据状态构造 diagnose。
 *  纯代码，不调 LLM，<10ms。只覆盖高置信度模式，不确定就返回 null。 */
function _deterministicRecover(ctx) {
  const q = ctx.question || '';
  const _polys = getLayers().filter(l => l.kind === 'polygon' && l.fc && l.fc.features && l.fc.features.length);
  if (!_polys.length) return null;
  const _regionM = /(.{1,6})(?:区|市|县|街道|镇)/.exec(q);
  const _region = _regionM ? _regionM[1].trim() : '';

  // 模式A：有用地关键词 + 有区名 → extract_feature(区边界) + overlay 链
  const _landuseKWs = ['商业', '居住', '公园', '绿地', '工业', '广场', '办公', '教育', '医疗'];
  const _mentionedLU = _landuseKWs.filter(kw => q.includes(kw));
  if (_mentionedLU.length >= 2 && _region) {
    const _boundary = _polys.find(l =>
      l.name.includes(_region) ||
      (l.fc.features || []).some(f => Object.values(f.properties || {}).some(v => String(v).includes(_region))));
    const _matched = [];
    if (_boundary) {
      for (const kw of _mentionedLU) {
        const found = _polys.find(l => l.name.includes(kw) && l.id !== _boundary.id && !_matched.some(m => m.id === l.id));
        if (found) _matched.push(found);
      }
    }
    if (_matched.length >= 1) {
      const _bRef = _boundary ? _boundary.fc : _region;
      const _tcs = _matched.map(lu => ({
        name: "overlay",
        params: { layer_a: _bRef, layer_b: lu.id, how: "intersection",
                  as: lu.name.replace(/\.(geo)?json/i, "").replace(/^用地_/, "") + "_" + _region }
      }));
      if (/合并/.test(q) && _tcs.length >= 2) {
        let _chainAs = _tcs[0].params.as;
        for (let i = 1; i < _tcs.length; i++) {
          _tcs.push({ name: "overlay", params: { layer_a: _chainAs, layer_b: _tcs[i].params.as, how: "union", as: "merged_final_" + i } });
          _chainAs = _tcs[_tcs.length - 1].params.as;
        }
      }
      return { template: 'overlay', degraded: false, _fc: true, _recover: true,
        params: {}, method: ['overlay()'], intent: 'gis_operation',
        data_plan: { needed: [], available: [], gap: [], strategy: 'ready' },
        domain_lens: [], scale: 'macro', decision_type: '操作', outlet: '生成图层', plans: [],
        _allToolCalls: _tcs };
    }
  }

  // 模式B：有情绪点 + 有区名 + "分析/情绪/消极/积极" → zonal_stats
  if (_region && /分析|情绪|消极|积极|归因/.test(q)) {
    const _hasPoint = (ctx.layerMeta && ctx.layerMeta.has_point) ||
      getLayers().some(l => l.kind === 'point' && l.fc && l.fc.features && l.fc.features.length);
    if (_hasPoint) {
      const _bLayer = _polys.find(l => l.name.includes(_region));
      const _boundary = _bLayer ? _bLayer.name : (_region + '区');
      return { template: 'zonal', degraded: false, _fc: true, _recover: true,
        params: { boundary: _boundary, polarity: /消极|负面|negative/i.test(q) ? 'negative' : (/积极|正面|positive/i.test(q) ? 'positive' : 'overall') },
        method: ['zonal_stats()'], intent: 'emotion_analysis',
        data_plan: { needed: [], available: [], gap: [], strategy: 'ready' },
        domain_lens: [], scale: 'macro', decision_type: '操作', outlet: '表格', plans: [] };
    }
  }

  return null;
}

/** CB-09 代码自动扩展：检测"X区内Y1+Y2+Y3"模式 → 生成 overlay 步骤。 */
async function _autoExpandOverlays(ctx, hooks, diagnose, firstResult) {
  const q = ctx.question || '';
  const _LANDUSE = ['商业', '居住', '公园', '绿地', '工业', '广场', '办公', '教育', '医疗', '用地'];
  const _mentioned = _LANDUSE.filter((kw) => q.includes(kw));
  if (_mentioned.length < 2) return null;
  // 找已加载的匹配面层（排除第一步刚产出的边界层）
  const _polyLayers = getLayers().filter((l) => l.kind === 'polygon' && l.fc && l.fc.features && l.fc.features.length);
  const _firstLayerName = diagnose.params && (diagnose.params.as || diagnose.params.name || '');
  const _matches = _polyLayers.filter((l) =>
    _mentioned.some((kw) => l.name.includes(kw)) && l.name !== _firstLayerName
  );
  if (_matches.length < 1) return null;
  // 找第一步产出的边界图层名
  const _boundaryName = _firstLayerName || (_polyLayers.find((l) => l.name.includes('范围') || l.name.includes('边界') || l.name.includes('西陵')) || {}).name;
  if (!_boundaryName) return null;
  // 找边界层对象：传 GeoJSON（非字符串 → ref() 直返，不触发消费）——否则首个 overlay 会把边界标"已消费"→移除→后续 overlay 全失败
  const _boundaryLayer = _polyLayers.find(l => l.name === _boundaryName || (l.name && l.name.includes(_boundaryName)));
  const _bRef = _boundaryLayer ? _boundaryLayer.fc : _boundaryName;
  // 生成 overlay tool_calls
  const _extraTCs = _matches.map((l) => ({
    name: 'overlay',
    params: { layer_a: _bRef, layer_b: l.id, how: 'intersection', as: l.name.replace(/\.(geo)?json/i, '').replace(/^用地_/, '') + '_' + _boundaryName }
  }));
  console.log('[autoExpand]', _mentioned.join('+'), '→', _extraTCs.length, 'overlays using boundary:', _boundaryName);
  const _diag = { ...diagnose, _allToolCalls: _extraTCs };
  return await runAllToolCalls(ctx, hooks, _diag);
}

/** CB-09 D057 修订：LLM 输出多个 tool_calls → 确定性顺序执行·0 LLM 中间轮。 */
async function runAllToolCalls(ctx, hooks, diagnose) {
  resetStepResults();        // 清 _stepResults/_resultIdByStep/_registry（防上轮残留致 ref() 误标消费）
  resetCurrentResults();     // 清 _curResultIds/_consumedIds/_keepIds（防 focusOnlyResults 误隐藏）
  const tcs = diagnose._allToolCalls;
  const toolHistory = []; let newLayerCount = 0; const failedSteps = [];
  console.log('[runAllToolCalls] start:', tcs.length, tcs.map((t) => t.name).join(' → '));
  for (let i = 0; i < tcs.length; i++) {
    const tc = tcs[i];
    if (hooks.onRoundStart) hooks.onRoundStart(i + 1);
    setToolContext({ tool: tc.name, round: i + 1 });
    let r = null;
    try { r = await TOOLS[tc.name](tc.params || {}); }
    catch (e) { toolHistory.push(`第${i + 1}步: ${tc.name} → 异常: ${(e && e.message) || e}`); failedSteps.push(i + 1); continue; }
    const obs = (r && r.observation) || '[ERR]';
    if (r && r.data && r.data.layerId) newLayerCount++;
    else failedSteps.push(i + 1);   // 无图层产出 = 失败
    toolHistory.push(`第${i + 1}步: ${tc.name}(${JSON.stringify(tc.params || {}).slice(0, 80)}) → ${obs}`);
    if (hooks.onObservation) hooks.onObservation(obs, i + 1);
    document.dispatchEvent(new CustomEvent('tool:executed', { detail: { tool: tc.name, layerId: (r && r.data && r.data.layerId) || null, ok: !/\[ERR\]|失败/.test(obs), ts: Date.now() } }));
  }
  // 零图层守护
  if (newLayerCount === 0) {
    const _t = `## 执行完成\n\n已按计划执行 ${tcs.length} 个步骤（${tcs.map((t) => t.name).join(' → ')}），但均未产出新图层。`;
    if (hooks.onFinalDone) hooks.onFinalDone(_t);
    return { ok: true, rounds: tcs.length, final: _t, defense: { degraded: true, skipped: 'multi-zero' }, degraded: true, diagnose, exit: 'result', newLayerCount: 0 };
  }
  // finalStep
  if (hooks.onRound) hooks.onRound(tcs.length);
  const _failNote = failedSteps.length ? `⚠️ 失败步骤: ${failedSteps.map((n) => `第${n}步(${tcs[n-1].name})`).join('、')}——这些步骤未产出图层，结论必须如实说明"未生成"，严禁声称成功。` : '';
  ctx.context = _failNote + '\n【多步执行·已完成 ' + tcs.length + ' 步·成功 ' + newLayerCount + ' 层】\n【地图实际产出图层】' + formatRegistry() + '（严禁声称不在此列表的图层）\n\n' + (ctx.context || '');
  let draft;
  try { draft = await stages.finalStep(ctx, hooks, toolHistory.join('\n')); }
  catch (e) { draft = `## 执行完成\n\n已按计划执行 ${tcs.length} 个步骤，共产出 ${newLayerCount} 个图层。`; }
  const _qd = applyQualityDefense(draft, { obsOk: newLayerCount > 0, toolHistoryText: toolHistory.join('\n'), skipL1: false });
  if (hooks.onFinalDone) hooks.onFinalDone(_qd.final);
  return { ok: true, rounds: tcs.length, final: _qd.final, defense: { degraded: _qd.degraded, fixes: _qd.fixes, skipped: 'multi-tool' }, degraded: false, diagnose, exit: 'result', newLayerCount };
}

/** CB-09 自动模式：确定性遍历 plans[] 剩余步骤·顺序执行·复用 runTemplatePath。
 *  ctx.plans 中 rank=1 已被初始 orchestrate 消费，此函数执行 rank=2+ 的全部剩余步骤。
 *  每步成/败都记录；全部跑完后调一次 finalStep 出综合结论。 */
export async function executePlans(ctx, hooks, diagnose, plans) {
  const remaining = (plans || []).filter((p) => p.rank >= 2 && p.tool);
  if (!remaining.length) return null;
  const toolHistory = []; let newLayerCount = 0;
  for (let i = 0; i < remaining.length; i++) {
    const p = remaining[i];
    const def = stages.SKILL_DEFS[p.tool];
    if (!def || !def.tool) continue;
    if (hooks.onRoundStart) hooks.onRoundStart(i + 1);
    setToolContext({ tool: def.tool, round: i + 1 });
    let r = null;
    try { r = await TOOLS[def.tool](p.params || {}); }
    catch (e) { toolHistory.push(`自动-第${i + 1}步: ${def.tool}(${JSON.stringify(p.params || {}).slice(0, 80)}) → 执行异常: ${(e && e.message) || e}`); continue; }
    const obs = (r && r.observation) || '[ERR] 无观察返回';
    if (r && r.data && r.data.layerId) newLayerCount++;
    toolHistory.push(`自动-第${i + 1}步: ${def.tool}(${JSON.stringify(p.params || {}).slice(0, 80)}) → ${obs}`);
    if (hooks.onObservation) hooks.onObservation(obs, i + 1);
    document.dispatchEvent(new CustomEvent('tool:executed', { detail: { tool: def.tool, layerId: (r && r.data && r.data.layerId) || null, ok: !/\[ERR\]|失败/.test(obs), ts: Date.now() } }));
  }
  // CB-09 P0-4 v2：零图层守护——跳过 LLM finalStep，直接用诚实结论
  if (newLayerCount === 0) {
    const _honestText = `## 自动执行完成\n\n已按计划执行 ${remaining.length} 个步骤（${remaining.map((p) => p.tool).join(' → ')}），但**均未产出新图层**。\n\n可能原因：图层间无空间重叠，或参数引用的图层名/ID 未正确对应。请检查 Layers 面板确认数据已加载。`;
    if (hooks.onFinalDone) hooks.onFinalDone(_honestText);
    if (hooks.onDefense) hooks.onDefense({ degraded: true, skipped: 'auto-zero' });
    return { ok: true, rounds: remaining.length, final: _honestText, defense: { degraded: true, skipped: 'auto-zero' }, degraded: true, diagnose, exit: 'result', newLayerCount: 0 };
  }
  // 综合结论
  if (hooks.onRound) hooks.onRound(remaining.length);
  ctx.context = `【自动模式·已完成 ${remaining.length} 步】已执行: ${remaining.map((p) => p.tool).join(' → ')}。共产出 ${newLayerCount} 个新图层。\n【地图实际产出图层】${formatRegistry()}（严禁声称生成不在此列表的图层）\n\n` + (ctx.context || '');
  let draft;
  try { draft = await stages.finalStep(ctx, hooks, toolHistory.join('\n')); }
  catch (e) { draft = `## 自动执行完成\n\n已按计划执行 ${remaining.length} 个步骤，共产出 ${newLayerCount} 个图层。详情见地图。`; }
  const _qd = applyQualityDefense(draft, { obsOk: newLayerCount > 0, toolHistoryText: toolHistory.join('\n'), skipL1: false });
  if (hooks.onFinalDone) hooks.onFinalDone(_qd.final);
  if (hooks.onDefense) hooks.onDefense({ degraded: _qd.degraded, fixes: _qd.fixes, skipped: 'auto-exec', capsules: _qd.capsules || [] });
  return { ok: true, rounds: remaining.length, final: _qd.final, defense: { degraded: _qd.degraded, fixes: _qd.fixes, skipped: 'auto-exec' }, degraded: false, diagnose, exit: 'result', newLayerCount };
}
