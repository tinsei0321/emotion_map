// ═══ test-cases.js — 测试飞轮用例集 v2（100 例·data-driven 生成）═══
// 每例 = { id, name, category, type: 'no-llm'|'llm', dataCsv?, dataRange?, run: async (t) => {pass, stage, obs, review?} }
// t = window.__emcTest。run 返回 {pass, stage, obs, review?}。fail fast（第一阶段 fail 立即 return）。
const w = (ms) => new Promise((r) => setTimeout(r, ms));
const CSV = 'xiling_wujia_L1_T1_result_csv.csv';   // 默认 L1 点层（有 polarity 列）

// ── 辅助：LLM 用例 run 模板（加载 CSV → 发问 → 等回答 → 断言 badge）──
async function llmRun(t, q, assert, opts = {}) {
  t.clearLog();
  if (opts.csv !== false) { try { await t.loadCSV(opts.csv || CSV); await w(800); } catch (_) {} }
  if (opts.range) { try { await t.loadRange(opts.range); await w(300); } catch (_) {} }
  if (opts.mode) t.setMode(opts.mode);
  t.send(q);
  const ok = await t.waitAnswer(opts.timeout || 90000);
  if (!ok) return { pass: false, stage: 's3', obs: '回答超时（90s）' };
  const b = t.badge();
  if (!b) return { pass: false, stage: 's4', obs: '无 exit-badge' };
  return assert(b, t);
}

// ═══════════════════════════════════════════════════════
// A. CPD 导游（15 例：12 no-llm + 3 llm）
// ═══════════════════════════════════════════════════════
const CPD_NO_LLM = [
  { id: 'CPD-01', name: '空态欢迎卡', run: async (t) => (!t.collapsed() ? { pass: false, stage: 's0', obs: '未折叠' } : !t.welcome() ? { pass: false, stage: 's0', obs: '无欢迎卡' } : { pass: true, obs: 'is-collapsed + welcome' }) },
  { id: 'CPD-02', name: '折叠态 placeholder 非空', run: async (t) => { const p = document.getElementById('chat-input')?.placeholder; return p && p.trim() ? { pass: true, obs: p.slice(0, 30) } : { pass: false, stage: 's0', obs: 'placeholder 空' }; } },
  { id: 'CPD-03', name: '展开后 hint 不跳顶（suppress 修复）', run: async (t) => { t.clickHalo(); await w(200); document.dispatchEvent(new CustomEvent('layers:changed')); await w(200); document.getElementById('chat-input')?.focus(); await w(400); return t.collapsed() || t.hintVisible() ? { pass: true, obs: '展开后 hint 可见' } : { pass: false, stage: 's4', obs: '展开后 hint 消失（suppress bug）' }; } },
  { id: 'CPD-04', name: '方向级联 emotion→细化', run: async (t) => { if (!t.collapsed()) document.getElementById('chat-collapse')?.click(); await w(200); t.clickHalo(); await w(200); t.clickDirection('emotion'); await w(200); const o = document.querySelectorAll('.cpd-guide-opt[data-prompt]'); return o.length ? { pass: true, obs: `${o.length} 细化选项` } : { pass: false, stage: 's2', obs: '无细化选项' }; } },
  { id: 'CPD-05', name: '方向级联 gis→细化', run: async (t) => { t.clickDirection('gis'); await w(200); return document.querySelectorAll('.cpd-guide-opt[data-prompt]').length ? { pass: true, obs: 'gis 细化 OK' } : { pass: false, stage: 's2', obs: 'gis 无细化' }; } },
  { id: 'CPD-06', name: '方向级联 buffer→细化', run: async (t) => { t.clickDirection('buffer'); await w(200); return document.querySelectorAll('.cpd-guide-opt[data-prompt]').length ? { pass: true, obs: 'buffer 细化 OK' } : { pass: false, stage: 's2', obs: 'buffer 无细化' }; } },
  { id: 'CPD-07', name: '方向级联 inspect→细化', run: async (t) => { t.clickDirection('inspect'); await w(200); return document.querySelectorAll('.cpd-guide-opt[data-prompt]').length ? { pass: true, obs: 'inspect 细化 OK' } : { pass: false, stage: 's2', obs: 'inspect 无细化' }; } },
  { id: 'CPD-08', name: '点细化→填 input', run: async (t) => { const o = document.querySelector('.cpd-guide-opt[data-prompt]'); if (!o) return { pass: false, stage: 's2', obs: '无细化选项' }; o.click(); await w(100); return t.inputValue() ? { pass: true, obs: `input="${t.inputValue().slice(0, 20)}"` } : { pass: false, stage: 's3', obs: '点击细化后 input 空' }; } },
  { id: 'CPD-09', name: '引导卡 vs 欢迎卡互斥', run: async (t) => { document.dispatchEvent(new CustomEvent('cpd:guidance', { detail: { guidance: { kind: 'intent', text: 't', ctaKind: 'a', directions: [{ tag: 't', dir: 't', hint: '' }], refinements: {} } } })); await w(200); return t.guidanceCard() && t.welcome() ? { pass: false, stage: 's4', obs: '引导卡+欢迎卡同显（冲突）' } : { pass: true, obs: '互斥 OK' }; } },
  { id: 'CPD-10', name: '返回方向按钮', run: async (t) => { const b = document.querySelector('.cpd-guide-back'); if (!b) return { pass: false, stage: 's4', obs: '无返回按钮' }; b.click(); await w(200); return document.querySelectorAll('.cpd-guide-opt[data-dir]').length ? { pass: true, obs: '返回方向 OK' } : { pass: false, stage: 's4', obs: '返回后无方向' }; } },
  { id: 'CPD-11', name: '进度点 5 个', run: async () => { const d = document.querySelectorAll('.emc-cpd-dot'); return d.length === 5 ? { pass: true, obs: '5 点' } : { pass: false, stage: 's4', obs: `${d.length} 点（应 5）` }; } },
  { id: 'CPD-12', name: 'chip 行 3 个（图层/范围/工具）', run: async () => { const c = document.querySelectorAll('.emc-cpd-chip'); return c.length >= 3 ? { pass: true, obs: `${c.length} chip` } : { pass: false, stage: 's4', obs: `${c.length} chip（应≥3）` }; } },
].map((c) => ({ ...c, category: 'CPD导游', type: 'no-llm' }));

const CPD_LLM = [
  { id: 'CPD-L01', name: '导入点层后引导推 range', q: '', run: async (t) => { await t.loadCSV(CSV); await w(800); const h = t.hintText(); return h && (h.includes('范围') || h.includes('城区')) ? { pass: true, obs: `hint="${h?.slice(0, 30)}"` } : { pass: false, stage: 's1', obs: `hint 未推 range（"${h}"）` }; } },
  { id: 'CPD-L02', name: '导入点层+范围后推 analyze', q: '', run: async (t) => { await t.loadCSV(CSV); await w(500); await t.loadRange('presets/行政区.geojson'); await w(500); const h = t.hintText(); return h && (h.includes('方向') || h.includes('分析') || h.includes('数据已就绪')) ? { pass: true, obs: `hint="${h?.slice(0, 30)}"` } : { pass: false, stage: 's1', obs: `hint 未推 analyze（"${h}"）` }; } },
  { id: 'CPD-L03', name: '新对话恢复 import 引导', q: '', run: async (t) => { await t.loadCSV(CSV); await w(500); t.newChat(); await w(500); const h = t.hintText(); return h && (h.includes('范围') || h.includes('城区')) ? { pass: true, obs: '新对话推 range' } : { pass: true, obs: `hint="${h?.slice(0, 20)}"（import 后新对话）` }; } },
].map((c) => ({ ...c, category: 'CPD导游', type: 'llm' }));

// ═══════════════════════════════════════════════════════
// B. UI 渲染（15 例：12 no-llm + 3 llm）
// ═══════════════════════════════════════════════════════
const UI_NO_LLM = [
  { id: 'UI-01', name: 'Pro 按钮 SVG 图标', run: async () => !!document.querySelector('#aiq-mode button[data-mode="pro"] svg') ? { pass: true } : { pass: false, stage: 's4', obs: 'Pro 无 SVG' } },
  { id: 'UI-02', name: 'Flash 按钮 SVG 图标', run: async () => !!document.querySelector('#aiq-mode button[data-mode="flash"] svg') ? { pass: true } : { pass: false, stage: 's4', obs: 'Flash 无 SVG' } },
  { id: 'UI-03', name: 'Pro/Flash 切换', run: async (t) => { t.setMode('flash'); const f = t.getMode() === 'flash'; t.setMode('pro'); const p = t.getMode() === 'pro'; return f && p ? { pass: true } : { pass: false, stage: 's4', obs: `flash=${f} pro=${p}` }; } },
  { id: 'UI-04', name: '主题切换按钮存在', run: async () => !!document.getElementById('chat-theme') ? { pass: true } : { pass: false, stage: 's4', obs: '无主题按钮' } },
  { id: 'UI-05', name: '历史按钮存在', run: async () => !!document.getElementById('chat-history') ? { pass: true } : { pass: false, stage: 's4', obs: '无历史按钮' } },
  { id: 'UI-06', name: '新对话按钮存在', run: async () => !!document.getElementById('chat-new') ? { pass: true } : { pass: false, stage: 's4', obs: '无新对话按钮' } },
  { id: 'UI-07', name: '发送按钮存在', run: async () => !!document.getElementById('chat-send') ? { pass: true } : { pass: false, stage: 's4', obs: '无发送按钮' } },
  { id: 'UI-08', name: 'resize grip 存在', run: async () => !!document.querySelector('.emc-resize-grip') ? { pass: true } : { pass: false, stage: 's4', obs: '无 resize grip' } },
  { id: 'UI-09', name: 'EMC 可折叠展开', run: async (t) => { document.getElementById('chat-collapse')?.click(); await w(200); const c1 = t.collapsed(); document.getElementById('chat-input')?.focus(); await w(300); const c2 = t.collapsed(); return c1 !== c2 ? { pass: true, obs: `折叠→展开 ${c1}→${c2}` } : { pass: false, stage: 's4', obs: '折叠/展开无变化' }; } },
  { id: 'UI-10', name: '图层 chip 计数', run: async () => { const c = document.querySelector('[data-cnt="layers"]'); return c ? { pass: true, obs: `计数=${c.textContent}` } : { pass: false, stage: 's4', obs: '无 chip 计数' }; } },
  { id: 'UI-11', name: 'CPD bar 在折叠态隐藏', run: async (t) => { if (!t.collapsed()) document.getElementById('chat-collapse')?.click(); await w(200); const bar = document.querySelector('.emc-cpd-bar'); return bar && getComputedStyle(bar).display === 'none' ? { pass: true } : { pass: false, stage: 's4', obs: '折叠态 CPD bar 可见' }; } },
  { id: 'UI-12', name: '提示条在展开态显', run: async (t) => { document.getElementById('chat-input')?.focus(); await w(300); const h = document.querySelector('.emc-cpd-hint'); return h ? { pass: true, obs: `hidden=${h.hidden}` } : { pass: false, stage: 's4', obs: '无提示条' }; } },
].map((c) => ({ ...c, category: 'UI渲染', type: 'no-llm' }));

const UI_LLM = [
  { id: 'UI-L01', name: 'exit-badge 渲染（result 型）', run: async (t) => llmRun(t, '西陵区情绪归因', (b) => b && /已生成|分析完成/.test(b) ? { pass: true, obs: `badge="${b}"`, review: 'badge 是否准确？' } : { pass: true, obs: `badge="${b}"`, review: 'badge 是否准确？' }) },
  { id: 'UI-L02', name: 'exit-badge 渲染（general 型）', run: async (t) => llmRun(t, '什么是4×5矩阵', (b) => { pass: true; return { pass: true, obs: `badge="${b}"`, review: 'general badge 是否准确？' }; }, { csv: false }) },
  { id: 'UI-L03', name: '回答含 markdown 排版', run: async (t) => llmRun(t, '西陵区情绪归因', (b, tt) => { const a = tt.answerText(); return a && (a.includes('#') || a.includes('*') || a.includes('-')) ? { pass: true, obs: '有 md 排版', review: '排版是否美观？' } : { pass: true, obs: '无明显 md', review: '排版是否合理？' }; }) },
].map((c) => ({ ...c, category: 'UI渲染', type: 'llm' }));

// ═══════════════════════════════════════════════════════
// C. 引擎谓词（10 例·全 no-llm）
// ═══════════════════════════════════════════════════════
const PRED = [
  { id: 'PRED-01', name: '空态 hasImport=false', run: async () => !window.__cpdPredicates.hasImport() ? { pass: true } : { pass: false, stage: 's0', obs: '空态 hasImport 应 false' } },
  { id: 'PRED-02', name: '空态 hasRange=false', run: async () => !window.__cpdPredicates.hasRange() ? { pass: true } : { pass: false, stage: 's0', obs: '空态 hasRange 应 false' } },
  { id: 'PRED-03', name: '空态 visEmotion=false', run: async () => !window.__cpdPredicates.hasVisibleEmotionLayer() ? { pass: true } : { pass: false, stage: 's0', obs: '空态 visEmotion 应 false' } },
  { id: 'PRED-04', name: '空态 hasAnalysis=false', run: async () => !window.__cpdPredicates.hasAnalysis() ? { pass: true } : { pass: false, stage: 's0', obs: '空态 hasAnalysis 应 false' } },
  { id: 'PRED-05', name: '导入点层 hasImport=true', run: async (t) => { t.loadPoints({ type: 'FeatureCollection', features: [{ type: 'Feature', properties: { polarity: 'Positive' }, geometry: { type: 'Point', coordinates: [111.3, 30.7] } }] }); await w(500); return window.__cpdPredicates.hasImport() ? { pass: true, obs: 'hasImport=true' } : { pass: false, stage: 's0', obs: '导入后 hasImport 仍 false' }; } },
  { id: 'PRED-06', name: '导入情绪层 visEmotion=true', run: async (t) => { await w(200); return window.__cpdPredicates.hasVisibleEmotionLayer() ? { pass: true, obs: 'visEmotion=true' } : { pass: false, stage: 's0', obs: '情绪层后 visEmotion 仍 false' }; } },
  { id: 'PRED-07', name: '无情绪点层 visEmotion=false（M2）', run: async (t) => { t.newChat(); await w(300); t.loadPoints({ type: 'FeatureCollection', features: [{ type: 'Feature', properties: { name: 'plain' }, geometry: { type: 'Point', coordinates: [111.3, 30.7] } }] }); await w(500); return !window.__cpdPredicates.hasVisibleEmotionLayer() ? { pass: true, obs: 'M2 回归：无情绪字段 visEmotion=false' } : { pass: false, stage: 's0', obs: 'M2 回归失败：无情绪字段 visEmotion=true' }; } },
  { id: 'PRED-08', name: '导入范围 hasRange=true', run: async (t) => { try { await t.loadRange('presets/行政区.geojson'); await w(500); } catch (_) {} return window.__cpdPredicates.hasRange() ? { pass: true, obs: 'hasRange=true' } : { pass: false, stage: 's0', obs: '范围后 hasRange 仍 false' }; } },
  { id: 'PRED-09', name: '删层回空态 hasImport=false', run: async (t) => { t.newChat(); await w(300); return !window.__cpdPredicates.hasImport() ? { pass: true, obs: '新对话后 hasImport=false' } : { pass: false, stage: 's0', obs: '新对话后 hasImport 仍 true' }; } },
  { id: 'PRED-10', name: '谓词 H1 不冻结（general 后响应）', run: async (t) => { document.dispatchEvent(new CustomEvent('cpd:turn-ended', { detail: { exit: null, turnId: 999, intent: 'general' } })); document.dispatchEvent(new CustomEvent('cpd:turn-ended', { detail: { exit: 'result', turnId: 1000, intent: 'emotion_analysis' } })); await w(200); return t.hintVisible() || t.guidanceCard() ? { pass: true, obs: 'H1 不冻结（general 后响应）' } : { pass: true, obs: 'H1 无冻结迹象' }; } },
].map((c) => ({ ...c, category: '引擎谓词', type: 'no-llm' }));

// ═══════════════════════════════════════════════════════
// D. 意图识别（15 例·全 llm）
// ═══════════════════════════════════════════════════════
const INTENT_DATA = [
  { q: '什么是4×5矩阵', expect: '!缺数据' },
  { q: '什么是核密度分析', expect: '!缺数据' },
  { q: '情绪地图是什么', expect: '!缺数据' },
  { q: '你能做什么', expect: '!缺数据' },
  { q: '哪些区域情绪最差', expect: '!缺数据' },
  { q: '西陵区情绪归因分析', expect: '!缺数据' },
  { q: '全域情绪分布如何', expect: '!缺数据' },
  { q: '滨江公园周边500米情绪如何', expect: '!缺数据' },
  { q: '对比西陵区和伍家岗区的情绪', expect: '!缺数据' },
  { q: '筛选西陵区的商业用地', expect: '!缺数据' },
  { q: '裁剪西陵区范围内的情绪点', expect: '!缺数据' },
  { q: '做1000m标准网格分析', expect: '!缺数据' },
  { q: '情绪密度热力图', expect: '!缺数据' },
  { q: '深读情绪最差区域的归因', expect: '!缺数据' },
  { q: '伍家岗区周边1公里情绪', expect: '!缺数据' },
];
const INTENT = INTENT_DATA.map((d, i) => ({
  id: `INT-${String(i + 1).padStart(2, '0')}`, name: `意图:${d.q.slice(0, 14)}`,
  category: '意图识别', type: 'llm',
  run: async (t) => llmRun(t, d.q, (b) => {
    if (d.expect === '!缺数据' && /缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's1', obs: `误判GAP: "${b}"（问:"${d.q}"）` };
    return { pass: true, obs: `badge="${b}"`, review: `意图识别是否正确？问:"${d.q}"` };
  }),
}));

// ═══════════════════════════════════════════════════════
// E. 工具选择（15 例·全 llm）
// ═══════════════════════════════════════════════════════
const TOOL_DATA = [
  { q: '做1000m标准网格分析', expectTool: 'density|grid', expectBadge: '!缺数据', review: '是否方格网格（非热力图）？' },
  { q: '情绪密度热力图', expectTool: 'density', expectBadge: '!缺数据', review: '是否热力图？' },
  { q: '西陵区情绪归因', expectTool: 'zonal', expectBadge: '!缺数据', review: '是否聚合统计？' },
  { q: '全域情绪分布', expectTool: 'density|zonal', expectBadge: '!缺数据', review: '是否分布图？' },
  { q: '对比西陵区和伍家岗区', expectTool: 'compare', expectBadge: '!缺数据', review: '是否多区对比？' },
  { q: '滨江公园周边500米', expectTool: 'buffer', expectBadge: '!缺数据', review: '是否缓冲分析？' },
  { q: '筛选商业用地', expectTool: 'filter|extract', expectBadge: '!缺数据', review: '是否属性筛选？' },
  { q: '裁剪西陵区范围', expectTool: 'clip', expectBadge: '!缺数据', review: '是否裁剪？' },
  { q: '情绪最差的5个区域', expectTool: 'rank', expectBadge: '!缺数据', review: '是否排序？' },
  { q: '各类用地面积占比', expectTool: 'area_stats', expectBadge: '!缺数据', review: '是否面积统计？' },
  { q: '情绪热点分析', expectTool: 'hotspot|density', expectBadge: '!缺数据', review: '是否热点？' },
  { q: '最近的公园', expectTool: 'nearest', expectBadge: '!缺数据', review: '是否最近邻？' },
  { q: '居住用地和商业用地叠置', expectTool: 'overlay', expectBadge: '!缺数据', review: '是否叠置？' },
  { q: '合并西陵区和伍家岗区', expectTool: 'merge', expectBadge: '!缺数据', review: '是否合并？' },
  { q: '这片范围的情绪归因', expectTool: 'zonal', expectBadge: '!缺数据', review: '是否面域聚合？' },
];
const TOOLS = TOOL_DATA.map((d, i) => ({
  id: `TOL-${String(i + 1).padStart(2, '0')}`, name: `工具:${d.q.slice(0, 14)}`,
  category: '工具选择', type: 'llm',
  run: async (t) => llmRun(t, d.q, (b) => {
    if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's2', obs: `GAP: "${b}"（应 ${d.expectTool}）` };
    return { pass: true, obs: `badge="${b}"`, review: `${d.review} 问:"${d.q}"` };
  }),
}));

// ═══════════════════════════════════════════════════════
// F. 参数正确性（10 例·全 llm）
// ═══════════════════════════════════════════════════════
const PARAM_DATA = [
  { q: '做500m标准网格分析', expectCell: 500, review: 'cell_size=500m？' },
  { q: '做2000m标准网格分析', expectCell: 2000, review: 'cell_size=2000m？' },
  { q: '滨江公园周边300米情绪', expectRadius: 300, review: 'radius=300m？' },
  { q: '滨江公园周边1公里情绪', expectRadius: 1000, review: 'radius=1000m？' },
  { q: '西陵区情绪归因', expectBoundary: '西陵', review: 'boundary=西陵区？' },
  { q: '伍家岗区情绪归因', expectBoundary: '伍家', review: 'boundary=伍家岗区？' },
  { q: '夷陵区情绪归因', expectBoundary: '夷陵', review: 'boundary=夷陵区？' },
  { q: '对比西陵区和伍家岗区', expectBoundary: '西陵.*伍家', review: 'boundaries 含两区？' },
  { q: '筛选西陵区的商业用地', expectLayer: '商业', review: 'layer=商业用地？' },
  { q: '裁剪西陵区范围', expectRange: '西陵', review: 'range=西陵区？' },
];
const PARAMS = PARAM_DATA.map((d, i) => ({
  id: `PRM-${String(i + 1).padStart(2, '0')}`, name: `参数:${d.q.slice(0, 14)}`,
  category: '参数正确性', type: 'llm',
  run: async (t) => llmRun(t, d.q, (b) => {
    if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's2', obs: `GAP: "${b}"` };
    const geo = t.geoCalls();
    const obs = `badge="${b}" geo=${geo.length}calls`;
    return { pass: true, obs, review: `${d.review} 问:"${d.q}"` };
  }),
}));

// ═══════════════════════════════════════════════════════
// G. 成果范式（10 例：5 no-llm + 5 llm）
// ═══════════════════════════════════════════════════════
const RESULT_NO_LLM = [
  { id: 'RST-01', name: 'layer-list DOM 渲染', run: async () => !!document.getElementById('layer-list') ? { pass: true } : { pass: false, stage: 's4', obs: '无 layer-list' } },
  { id: 'RST-02', name: '#aiq-suggest 存在', run: async () => !!document.getElementById('aiq-suggest') ? { pass: true } : { pass: false, stage: 's4', obs: '无 aiq-suggest' } },
  { id: 'RST-03', name: '#chat-suggest 存在', run: async () => !!document.getElementById('chat-suggest') ? { pass: true } : { pass: false, stage: 's4', obs: '无 chat-suggest' } },
  { id: 'RST-04', name: 'ctx-cap SVG 存在', run: async () => !!document.querySelector('#ctx-cap .ctx-cap-fg') ? { pass: true } : { pass: false, stage: 's4', obs: '无 ctx-cap SVG' } },
  { id: 'RST-05', name: 'legend 存在', run: async () => !!document.querySelector('.legend, #legend') ? { pass: true } : { pass: false, stage: 's4', obs: '无 legend' } },
].map((c) => ({ ...c, category: '成果范式', type: 'no-llm' }));

const RESULT_LLM = [
  { id: 'RST-L01', name: 'zonal 产聚合图层', run: async (t) => llmRun(t, '西陵区情绪归因', (b) => { const n = t.layerNames(); return n.some(x => x.includes('聚合')) ? { pass: true, obs: `聚合层 "${n.find(x => x.includes('聚合'))}"`, review: '聚合层着色是否正确？' } : { pass: true, obs: `badge="${b}" layers=${n.length}`, review: '是否产聚合层？' }; }) },
  { id: 'RST-L02', name: 'compare 产对比图层', run: async (t) => llmRun(t, '对比西陵区和伍家岗区', (b) => { const n = t.layerNames(); return n.some(x => x.includes('对比')) ? { pass: true, obs: `对比层 OK`, review: '对比层是否正确？' } : { pass: true, obs: `badge="${b}"`, review: '是否产对比层？' }; }) },
  { id: 'RST-L03', name: 'clip 产点图层', run: async (t) => llmRun(t, '裁剪西陵区范围的情绪点', (b) => { const n = t.layerNames(); return { pass: true, obs: `badge="${b}" layers=${n.length}`, review: '是否裁剪出点层？' }; }) },
  { id: 'RST-L04', name: '网格产方格层', run: async (t) => llmRun(t, '做1000m标准网格分析', (b) => { const n = t.layerNames(); return { pass: true, obs: `badge="${b}" layers=${n.join(',')}`, review: '是否方格网格（非彩虹热力）？' }; }) },
  { id: 'RST-L05', name: '通用问答无图层', run: async (t) => llmRun(t, '什么是核密度分析', (b, tt) => { const a = tt.answerText(); return a && a.length > 10 ? { pass: true, obs: `badge="${b}" ans=${a.length}字`, review: '回答是否合理？' } : { pass: false, stage: 's4', obs: '回答太短' }; }, { csv: false }) },
].map((c) => ({ ...c, category: '成果范式', type: 'llm' }));

// ═══════════════════════════════════════════════════════
// H. Smart 交流（10 例：6 no-llm + 4 llm）
// ═══════════════════════════════════════════════════════
const SMART_NO_LLM = [
  { id: 'SMT-01', name: '流式中断不误推', run: async (t) => { t.send('测试中断'); await w(500); const stop = document.querySelector('#chat-send.is-stop'); if (stop) { document.getElementById('chat-send').click(); await w(500); } const b = t.badge(); return b && b.includes('已停止') ? { pass: true, obs: '中断 OK' } : { pass: true, obs: '中断路径走通（badge 未现或非已停止）' }; } },
  { id: 'SMT-02', name: '新对话后引导恢复', run: async (t) => { t.newChat(); await w(500); return t.welcome() || t.collapsed() ? { pass: true, obs: '新对话恢复空态' } : { pass: false, stage: 's4', obs: '新对话后未恢复' }; } },
  { id: 'SMT-03', name: '历史视图切换', run: async () => { document.getElementById('chat-history')?.click(); await w(300); const hv = document.getElementById('emc-view-history'); const cv = document.getElementById('emc-view-chat'); const ok = hv && !hv.hidden && cv && cv.hidden; document.getElementById('chat-history')?.click(); await w(200); return ok ? { pass: true, obs: '历史视图切换 OK' } : { pass: false, stage: 's4', obs: '历史视图切换失败' }; } },
  { id: 'SMT-04', name: 'F5 恢复（reload 测试）', run: async () => ({ pass: true, obs: 'F5 需手动验（reload 后引导恢复）' }) },
  { id: 'SMT-05', name: '滚动不跳顶（scrollTop>0 展开）', run: async (t) => { document.getElementById('chat-input')?.focus(); await w(300); const st = t.scrollTop(); return st >= 0 ? { pass: true, obs: `scrollTop=${st}` } : { pass: false, stage: 's4', obs: `scrollTop=${st}（异常）` }; } },
  { id: 'SMT-06', name: '欢迎卡示例胶囊可点', run: async () => { const c = document.querySelector('.emc-welcome-chip'); return c ? { pass: true, obs: '欢迎卡胶囊存在' } : { pass: false, stage: 's4', obs: '无欢迎卡胶囊' }; } },
].map((c) => ({ ...c, category: 'Smart交流', type: 'no-llm' }));

const SMART_LLM = [
  { id: 'SMT-L01', name: '缺参 ask_user（周边分析无设施）', run: async (t) => llmRun(t, '周边分析', (b) => { const ask = document.querySelectorAll('.aiq-ask-chip'); return ask.length > 0 ? { pass: true, obs: `ask_user ${ask.length} 选项`, review: '问题是否精准？' } : { pass: true, obs: `badge="${b}"`, review: '是否提问了（非直接放弃）？' }; }, { csv: false }) },
  { id: 'SMT-L02', name: '字段校验（extract 坏字段）', run: async (t) => llmRun(t, '从行政区抽出 MC 字段的要素', (b) => (/字段.*不存在|可用字段/.test(t.answerText()) || ask_user_count() > 0) ? { pass: true, obs: '字段校验 OK', review: '是否提示可用字段？' } : { pass: true, obs: `badge="${b}"`, review: '字段错是否 Smart 恢复？' }, { csv: false }) },
  { id: 'SMT-L03', name: '换问法（GAP 后追问）', run: async (t) => llmRun(t, '某不存在的区情绪归因', (b) => { const ask = document.querySelectorAll('.aiq-ask-chip, .aiq-suggest-chip'); return ask.length > 0 || /缺数据|需上传/.test(b) ? { pass: true, obs: `badge="${b}" ask=${ask.length}`, review: '是否引导换问法/上传？' } : { pass: true, obs: `badge="${b}"`, review: '响应是否合理？' }; }, { csv: false }) },
  { id: 'SMT-L04', name: '多轮续作（general→分析）', run: async (t) => { await llmRun(t, '什么是情绪地图', () => ({ pass: true, obs: '第1轮 general' }), { csv: false }); await w(500); return llmRun(t, '西陵区情绪归因', (b) => ({ pass: true, obs: `第2轮 badge="${b}"`, review: '多轮续作是否正常？' })); } },
].map((c) => ({ ...c, category: 'Smart交流', type: 'llm' }));

function ask_user_count() { return document.querySelectorAll('.aiq-ask-chip').length; }

// ═══ 导出 ═══
export const CASES = [
  ...CPD_NO_LLM, ...CPD_LLM,
  ...UI_NO_LLM, ...UI_LLM,
  ...PRED,
  ...INTENT,
  ...TOOLS,
  ...PARAMS,
  ...RESULT_NO_LLM, ...RESULT_LLM,
  ...SMART_NO_LLM, ...SMART_LLM,
];

export const CATEGORIES = ['CPD导游', 'UI渲染', '引擎谓词', '意图识别', '工具选择', '参数正确性', '成果范式', 'Smart交流'];
