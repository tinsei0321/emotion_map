// ═══ ai_qa/result-struct.js — 出口三段式·结果结构化纯函数（P0·确定性组装）═══
// 聚合 diagnose(方法/数据) + toolHistory(流程) + registry(结果) + draft(观点)
// → 三段 JSON { insight, points }。纯函数不调 LLM·不解析 finalStep markdown
// （结论段独立聚合·glm 第三轮 B2——LLM markdown 解析脆弱·finalStep 正文只进观点段）。
// 观点：draft 提取 `> **观点：**` 块（无标记 → 首段首句；空 → null 不显卡·Codex R2 兜底）。

/** 出口三段式结构化入口：{ question, diagnose, toolHistory, toolHistoryText, registryText, draft, scale, rows } */
export function buildResultStruct({ question, diagnose, toolHistory, toolHistoryText, registryText, draft, scale, rows }) {
  return {
    insight: _extractInsight(draft),
    points: _buildPoints({ question, diagnose, toolHistory, toolHistoryText, registryText, scale, rows }),
  };
}

/** ① 观点：从 finalStep markdown 提取 `> **观点：**` 引用块（模板软扩约定锚点）。
 *  W3 审计保守化（P0 审计 Codex/glm）：无标记 → **null 不显卡**（删首段首句兜底——
 *  finalStep 三句骨架①是动作句·首段首句大概率"我裁出…→落到地图"·动作描述冒充观点比无卡更糟·用户最在意观点=干货）。 */
function _extractInsight(draft) {
  if (!draft || typeof draft !== 'string') return null;
  // 整块捕获：`> **观点：** xxx` 或 `> **观点：**\n> 续行`（防多行引用残留·W2 审计）
  const m = draft.match(/^>\s*\*\*观点：\*\*\s*([\s\S]*?)(?=\n\n|\n\s*[^>]|$)/m);
  if (m) {
    const text = m[1].replace(/^\s*>\s*/gm, '').trim();   // 去续行的 `> ` 前缀
    if (text) return text;
  }
  return null;   // 无观点标记 → 不显卡（保守·不取动作描述当观点）
}

/** ② 4 要点：方法 / 数据 / 结果 / 结论（确定性模板·不解析 draft 正文）。 */
function _buildPoints({ question, diagnose, toolHistory, toolHistoryText, registryText, scale, rows }) {
  return {
    method: _methodOf(diagnose),
    data: _dataOf(diagnose),
    result: _resultOf(registryText, toolHistory),
    conclusion: _conclusionOf({ question, toolHistory, toolHistoryText, registryText, scale, rows }),
  };
}

function _methodOf(diagnose) {
  const d = diagnose || {};
  if (Array.isArray(d.method) && d.method.length) return d.method.join('、');
  if (d.template) return d.template;
  return '空间聚合分析';
}

function _dataOf(diagnose) {
  const d = diagnose || {};
  const plan = d.data_plan;
  if (!plan) return '情绪点数据（L1/L2）';
  if (Array.isArray(plan.available) && plan.available.length) return plan.available.join('、');
  if (Array.isArray(plan) && plan.length) return plan.join('、');
  return '情绪点数据（L1/L2）';
}

function _resultOf(registryText, toolHistory) {
  const parts = [];
  if (registryText && registryText.trim()) parts.push(registryText.trim());
  if (toolHistory && toolHistory.length) parts.push(`共 ${toolHistory.length} 步分析`);
  return parts.join('；') || '本次分析未产出图层';
}

/** 结论段 = 确定性学术论述（W1 审计：从 rows 确定性取数值+地名·非 toolHistory 执行日志·缺失降级"暂无数据"）。
 *  学术句式："数据显示 X 区极性指数 -0.6（N 条样本）·为全域最差·归因集中于 A×B"——P1 可加"综合研判/建议优先"句式深化。 */
function _conclusionOf({ question, toolHistory, toolHistoryText, registryText, scale, rows }) {
  const parts = [];
  if (scale) parts.push(`本分析为${_scaleCN(scale)}研究`);
  if (Array.isArray(rows) && rows.length) {
    const top = _topRow(rows);
    const loc = _pick(top, ['place_name', 'name', 'district', 'unit']);
    const pi = _pickNum(top, ['polarity_index', 'polarity', 'score_mean', 'score']);
    const cnt = _pickNum(top, ['point_count', 'n', 'total_points', 'count']);
    const issue = _pick(top, ['issue_label', 'domain_top', 'element_top', 'attribution']);
    const locS = loc ? `${loc}` : '关注区域';
    const piS = pi != null ? `极性指数 ${pi}` : '极性指数暂无数据';
    const cntS = cnt != null ? `${cnt} 条样本` : '样本数暂无数据';
    const issueS = issue ? `归因集中于 ${issue}` : '归因暂无数据';
    parts.push(`数据显示 ${locS} ${piS}（${cntS}）·${issueS}`);
  } else if (toolHistory && toolHistory.length) {
    parts.push(`共执行 ${toolHistory.length} 步空间分析`);
  }
  if (registryText && registryText.trim()) parts.push(`产出图层：${registryText.trim()}`);
  return parts.length ? parts.join('。') + '。' : '本次分析未产出可描述的确定性结果。';
}

/** 取 rows 中最有代表性的行（含极性字段的第一行·无则首行）。 */
function _topRow(rows) {
  return rows.find((r) => r && typeof r === 'object' && _pickNum(r, ['polarity_index', 'polarity', 'score_mean', 'score']) != null) || rows[0] || {};
}

/** 从行取首个存在的字符串字段。 */
function _pick(row, keys) {
  for (const k of keys) {
    const v = row[k];
    if (v != null && String(v).trim() && String(v) !== '暂无数据') return String(v).trim();
  }
  return null;
}

/** 从行取首个存在的数值字段（容错字符串数字）。 */
function _pickNum(row, keys) {
  for (const k of keys) {
    const v = row[k];
    if (v == null) continue;
    const n = Number(v);
    if (!Number.isNaN(n)) return n;
  }
  return null;
}

function _scaleCN(scale) {
  return scale === 'macro' ? '宏观（面域分布）' : scale === 'meso' ? '中观（单元归因）' : '微观（落点识别）';
}
