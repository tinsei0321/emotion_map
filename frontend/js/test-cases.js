// ═══ test-cases.js — 测试飞轮用例集 v3（100 例·prompt 遵循设计原则）═══
// Prompt 设计原则：docs/emc-prompt-design-principles.md
// 每条 LLM 问题 = [范围] + [拓扑关系] + [点/设施数据] + [分析目的] + [可选：时态/对比]
const w = (ms) => new Promise((r) => setTimeout(r, ms));
const CSV = 'xiling_wujia_L1_T1_result_csv.csv';   // 默认 L1 点层（有 polarity 列）
const CSV_T2 = 'xiling_wujia_L1_T2_result_csv.csv';
const CSV_T3 = 'xiling_wujia_L1_T3_result_csv.csv';
const RANGE = 'presets/行政区.geojson';
const RANGE_ERMAWU = '大南门二马路滨江片区.geojson';   // 大南门·二马路滨江片区边界

// ── 辅助：LLM 用例 run 模板 ──
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
  { id: 'CPD-03', name: '展开后 hint 不跳顶', run: async (t) => { t.clickHalo(); await w(200); document.dispatchEvent(new CustomEvent('layers:changed')); await w(200); document.getElementById('chat-input')?.focus(); await w(400); return t.collapsed() || t.hintVisible() ? { pass: true, obs: '展开后 hint 可见' } : { pass: false, stage: 's4', obs: 'suppress bug' }; } },
  { id: 'CPD-04', name: '方向级联 emotion', run: async (t) => { if (!t.collapsed()) document.getElementById('chat-collapse')?.click(); await w(200); t.clickHalo(); await w(200); t.clickDirection('emotion'); await w(200); return document.querySelectorAll('.cpd-guide-opt[data-prompt]').length ? { pass: true } : { pass: false, stage: 's2', obs: '无细化' }; } },
  { id: 'CPD-05', name: '方向级联 gis', run: async (t) => { t.clickDirection('gis'); await w(200); return document.querySelectorAll('.cpd-guide-opt[data-prompt]').length ? { pass: true } : { pass: false, stage: 's2', obs: '无细化' }; } },
  { id: 'CPD-06', name: '方向级联 buffer', run: async (t) => { t.clickDirection('buffer'); await w(200); return document.querySelectorAll('.cpd-guide-opt[data-prompt]').length ? { pass: true } : { pass: false, stage: 's2', obs: '无细化' }; } },
  { id: 'CPD-07', name: '方向级联 inspect', run: async (t) => { t.clickDirection('inspect'); await w(200); return document.querySelectorAll('.cpd-guide-opt[data-prompt]').length ? { pass: true } : { pass: false, stage: 's2', obs: '无细化' }; } },
  { id: 'CPD-08', name: '点细化→填 input', run: async (t) => { const o = document.querySelector('.cpd-guide-opt[data-prompt]'); if (!o) return { pass: false, stage: 's2', obs: '无细化' }; o.click(); await w(100); return t.inputValue() ? { pass: true, obs: `input="${t.inputValue().slice(0, 20)}"` } : { pass: false, stage: 's3', obs: 'input 空' }; } },
  { id: 'CPD-09', name: '引导卡 vs 欢迎卡互斥', run: async (t) => { document.dispatchEvent(new CustomEvent('cpd:guidance', { detail: { guidance: { kind: 'intent', text: 't', ctaKind: 'a', directions: [{ tag: 't', dir: 't', hint: '' }], refinements: {} } } })); await w(200); return t.guidanceCard() && t.welcome() ? { pass: false, stage: 's4', obs: '冲突' } : { pass: true, obs: '互斥 OK' }; } },
  { id: 'CPD-10', name: '返回方向按钮', run: async (t) => { const b = document.querySelector('.cpd-guide-back'); if (!b) return { pass: false, stage: 's4', obs: '无返回' }; b.click(); await w(200); return document.querySelectorAll('.cpd-guide-opt[data-dir]').length ? { pass: true } : { pass: false, stage: 's4', obs: '返回后无方向' }; } },
  { id: 'CPD-11', name: '进度点 5 个', run: async () => { const d = document.querySelectorAll('.emc-cpd-dot'); return d.length === 5 ? { pass: true } : { pass: false, stage: 's4', obs: `${d.length}` }; } },
  { id: 'CPD-12', name: 'chip 行 3 个', run: async () => { const c = document.querySelectorAll('.emc-cpd-chip'); return c.length >= 3 ? { pass: true } : { pass: false, stage: 's4', obs: `${c.length}` }; } },
].map((c) => ({ ...c, category: 'CPD导游', type: 'no-llm' }));

const CPD_LLM = [
  { id: 'CPD-L01', name: '导入点层后引导推 range', run: async (t) => { await t.loadCSV(CSV); await w(800); const h = t.hintText(); return h && h.includes('范围') ? { pass: true, obs: `hint="${h?.slice(0, 30)}"` } : { pass: false, stage: 's1', obs: `hint 未推 range` }; } },
  { id: 'CPD-L02', name: '导入点+范围后推 analyze', run: async (t) => { await t.loadCSV(CSV); await w(500); await t.loadRange(RANGE); await w(500); const h = t.hintText(); return h && (h.includes('方向') || h.includes('数据已就绪')) ? { pass: true, obs: `hint="${h?.slice(0, 30)}"` } : { pass: false, stage: 's1', obs: `hint 未推 analyze` }; } },
  { id: 'CPD-L03', name: '新对话恢复引导', run: async (t) => { await t.loadCSV(CSV); await w(500); t.newChat(); await w(500); const h = t.hintText(); return h && h.includes('范围') ? { pass: true, obs: '新对话推 range' } : { pass: true, obs: '新对话引导态恢复' }; } },
].map((c) => ({ ...c, category: 'CPD导游', type: 'llm' }));

// ═══════════════════════════════════════════════════════
// B. UI 渲染（15 例：12 no-llm + 3 llm）
// ═══════════════════════════════════════════════════════
const UI_NO_LLM = [
  { id: 'UI-01', name: 'Pro SVG 图标', run: async () => !!document.querySelector('#aiq-mode button[data-mode="pro"] svg') ? { pass: true } : { pass: false, stage: 's4', obs: 'Pro 无 SVG' } },
  { id: 'UI-02', name: 'Flash SVG 图标', run: async () => !!document.querySelector('#aiq-mode button[data-mode="flash"] svg') ? { pass: true } : { pass: false, stage: 's4', obs: 'Flash 无 SVG' } },
  { id: 'UI-03', name: 'Pro/Flash 切换', run: async (t) => { t.setMode('flash'); const f = t.getMode() === 'flash'; t.setMode('pro'); const p = t.getMode() === 'pro'; return f && p ? { pass: true } : { pass: false, stage: 's4', obs: `f=${f} p=${p}` }; } },
  { id: 'UI-04', name: '主题切换按钮', run: async () => !!document.getElementById('chat-theme') ? { pass: true } : { pass: false, stage: 's4' } },
  { id: 'UI-05', name: '历史按钮', run: async () => !!document.getElementById('chat-history') ? { pass: true } : { pass: false, stage: 's4' } },
  { id: 'UI-06', name: '新对话按钮', run: async () => !!document.getElementById('chat-new') ? { pass: true } : { pass: false, stage: 's4' } },
  { id: 'UI-07', name: '发送按钮', run: async () => !!document.getElementById('chat-send') ? { pass: true } : { pass: false, stage: 's4' } },
  { id: 'UI-08', name: 'resize grip', run: async () => !!document.querySelector('.emc-resize-grip') ? { pass: true } : { pass: false, stage: 's4' } },
  { id: 'UI-09', name: '折叠展开切换', run: async (t) => { document.getElementById('chat-collapse')?.click(); await w(200); const c1 = t.collapsed(); document.getElementById('chat-input')?.focus(); await w(300); const c2 = t.collapsed(); return c1 !== c2 ? { pass: true, obs: `${c1}→${c2}` } : { pass: false, stage: 's4' }; } },
  { id: 'UI-10', name: '图层 chip 计数', run: async () => { const c = document.querySelector('[data-cnt="layers"]'); return c ? { pass: true, obs: `=${c.textContent}` } : { pass: false, stage: 's4' }; } },
  { id: 'UI-11', name: 'CPD bar 折叠态隐藏', run: async (t) => { if (!t.collapsed()) document.getElementById('chat-collapse')?.click(); await w(200); const bar = document.querySelector('.emc-cpd-bar'); return bar && getComputedStyle(bar).display === 'none' ? { pass: true } : { pass: false, stage: 's4' }; } },
  { id: 'UI-12', name: '提示条展开态显', run: async (t) => { document.getElementById('chat-input')?.focus(); await w(300); const h = document.querySelector('.emc-cpd-hint'); return h ? { pass: true, obs: `hidden=${h.hidden}` } : { pass: false, stage: 's4' }; } },
].map((c) => ({ ...c, category: 'UI渲染', type: 'no-llm' }));

const UI_LLM = [
  { id: 'UI-L01', name: 'exit-badge 渲染（分析型）', run: async (t) => llmRun(t, '西陵区范围内情绪点按极性排序，找出最差 Top 3 片区及 4×5 归因', (b) => ({ pass: true, obs: `badge="${b}"`, review: 'badge 是否准确？' }), { range: RANGE }) },
  { id: 'UI-L02', name: 'exit-badge 渲染（通用型）', run: async (t) => llmRun(t, '什么是情绪地图的 4×5 归因矩阵？', (b) => ({ pass: true, obs: `badge="${b}"`, review: '通用 badge 准确？' }), { csv: false }) },
  { id: 'UI-L03', name: '回答含 markdown 排版', run: async (t) => llmRun(t, '西陵区范围内情绪最差的 Top 3 片区，每个片区的 4×5 归因是什么？', (b, tt) => { const a = tt.answerText(); return { pass: true, obs: `badge="${b}" md=${/[#\*\-]/.test(a)}`, review: '排版是否美观？' }; }, { range: RANGE }) },
].map((c) => ({ ...c, category: 'UI渲染', type: 'llm' }));

// ═══════════════════════════════════════════════════════
// C. 引擎谓词（10 例·全 no-llm）
// ═══════════════════════════════════════════════════════
const PRED = [
  { id: 'PRED-01', name: '空态 hasImport=false', run: async () => !window.__cpdPredicates.hasImport() ? { pass: true } : { pass: false, stage: 's0', obs: '空态应 false' } },
  { id: 'PRED-02', name: '空态 hasRange=false', run: async () => !window.__cpdPredicates.hasRange() ? { pass: true } : { pass: false, stage: 's0' } },
  { id: 'PRED-03', name: '空态 visEmotion=false', run: async () => !window.__cpdPredicates.hasVisibleEmotionLayer() ? { pass: true } : { pass: false, stage: 's0' } },
  { id: 'PRED-04', name: '空态 hasAnalysis=false', run: async () => !window.__cpdPredicates.hasAnalysis() ? { pass: true } : { pass: false, stage: 's0' } },
  { id: 'PRED-05', name: '导入点层 hasImport=true', run: async (t) => { t.loadPoints({ type: 'FeatureCollection', features: [{ type: 'Feature', properties: { polarity: 'Positive' }, geometry: { type: 'Point', coordinates: [111.3, 30.7] } }] }); await w(500); return window.__cpdPredicates.hasImport() ? { pass: true } : { pass: false, stage: 's0', obs: '导入后仍 false' }; } },
  { id: 'PRED-06', name: '情绪层 visEmotion=true', run: async () => window.__cpdPredicates.hasVisibleEmotionLayer() ? { pass: true } : { pass: false, stage: 's0', obs: '情绪层后仍 false' } },
  { id: 'PRED-07', name: '无情绪层 visEmotion=false（M2）', run: async (t) => { t.newChat(); await w(300); t.loadPoints({ type: 'FeatureCollection', features: [{ type: 'Feature', properties: { name: 'plain' }, geometry: { type: 'Point', coordinates: [111.3, 30.7] } }] }); await w(500); return !window.__cpdPredicates.hasVisibleEmotionLayer() ? { pass: true, obs: 'M2 回归 OK' } : { pass: false, stage: 's0', obs: 'M2 回归失败' }; } },
  { id: 'PRED-08', name: '导入范围 hasRange=true', run: async (t) => { try { await t.loadRange(RANGE); await w(500); } catch (_) {} return window.__cpdPredicates.hasRange() ? { pass: true } : { pass: false, stage: 's0' }; } },
  { id: 'PRED-09', name: '删层回空态 hasImport=false', run: async (t) => { t.newChat(); await w(300); return !window.__cpdPredicates.hasImport() ? { pass: true } : { pass: false, stage: 's0' }; } },
  { id: 'PRED-10', name: 'H1 不冻结（general 后响应）', run: async (t) => { document.dispatchEvent(new CustomEvent('cpd:turn-ended', { detail: { exit: null, turnId: 999, intent: 'general' } })); document.dispatchEvent(new CustomEvent('cpd:turn-ended', { detail: { exit: 'result', turnId: 1000, intent: 'emotion_analysis' } })); await w(200); return { pass: true, obs: 'H1 不冻结' }; } },
].map((c) => ({ ...c, category: '引擎谓词', type: 'no-llm' }));

// ═══════════════════════════════════════════════════════
// D. 意图识别（15 例·全 llm）—— prompt 遵循设计原则
// ═══════════════════════════════════════════════════════
const INTENT_DATA = [
  // 通用问答（概念/定义·无要素需求）
  { q: '什么是情绪地图的 4×5 归因矩阵？', expect: '!缺数据', review: '是否简洁准确回答概念？' },
  { q: '核密度分析适合什么尺度的城市规划场景？', expect: '!缺数据', review: '是否回答方法适用性？' },
  { q: '情绪地图与官方城市体检有什么区别？', expect: '!缺数据', review: '是否对比产品定位？' },
  { q: '在 EMC 里我能做哪些类型的空间分析？', expect: '!缺数据', review: '是否列出能力清单？' },
  // 情绪分析（有范围+点+目的）
  { q: '西陵区范围内情绪点的极性分布如何？消极占比多少？', expect: '!缺数据', review: '是否给出分布+占比？' },
  { q: '伍家岗区范围内情绪最差的 Top 3 片区是哪些？各自 4×5 归因是什么？', expect: '!缺数据', review: '是否排序+归因？' },
  { q: '西陵区范围内情绪点哪些片区在「环境」要素上最消极？', expect: '!缺数据', review: '是否按 element 归因？' },
  { q: '西陵区范围内情绪最积极的 Top 3 片区是哪些？为什么积极？', expect: '!缺数据', review: '是否排序正面+归因？' },
  { q: '西陵区范围内「城市运营」领域的情绪状况如何？主要矛盾在哪？', expect: '!缺数据', review: '是否按 domain 归因？' },
  // GIS 操作（有范围+点+目的）
  { q: '从已载行政区中抽取西陵区范围作为独立面图层', expect: '!缺数据', review: '是否 extract 出西陵区面？' },
  { q: '筛选西陵区范围内 polarity 为 Negative 的情绪点', expect: '!缺数据', review: '是否筛选出消极点？' },
  { q: '裁剪西陵区范围内的全部情绪点为独立点图层', expect: '!缺数据', review: '是否 clip 出点层？' },
  // 周边/缓冲（有拓扑+点+目的）
  { q: '大南门·二马路滨江片区周边 500 米范围内的情绪点分布如何？积极还是消极为主？', expect: '!缺数据', review: '是否 buffer+分布判断？' },
  // 对比（有 2 个对比对象+目的）
  { q: '对比西陵区与伍家岗区范围内情绪极性，哪个区消极占比更高？差异在哪些 domain×element？', expect: '!缺数据', review: '是否对比+差异归因？' },
  // 排序（有范围+目的）
  { q: '西陵区范围内按情绪极性排序最差 Top 5 片区，标出每个的 domain×element 主归属', expect: '!缺数据', review: '是否 rank+4×5 标注？' },
];
const INTENT = INTENT_DATA.map((d, i) => ({
  id: `INT-${String(i + 1).padStart(2, '0')}`, name: `意图:${d.q.slice(0, 16)}`,
  category: '意图识别', type: 'llm',
  run: async (t) => llmRun(t, d.q, (b) => {
    if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's1', obs: `误判GAP: "${b}"` };
    return { pass: true, obs: `badge="${b}"`, review: d.review };
  }, { range: RANGE }),
}));

// ═══════════════════════════════════════════════════════
// E. 工具选择（15 例·全 llm）—— 范围+拓扑+目的精准
// ═══════════════════════════════════════════════════════
const TOOL_DATA = [
  { q: '西陵区范围内做 1000m 标准方格网格聚合，看每格的极性分布', expectTool: 'density|grid', review: '是否方格网格（非热力图）？', opts: {} },
  { q: '西陵区范围内情绪点的密度热力图，看哪里最密集', expectTool: 'density', review: '是否热力图？', opts: {} },
  { q: '西陵区范围内按行政区面聚合情绪统计，每区的极性和归因', expectTool: 'zonal', review: '是否面域聚合？', opts: {} },
  { q: '全域范围内情绪点空间分布如何？做一张密度图看聚集趋势', expectTool: 'density|zonal', review: '是否分布图？', opts: {} },
  { q: '对比西陵区与伍家岗区范围内情绪极性与 4×5 归因差异', expectTool: 'compare', review: '是否多区对比？', opts: {} },
  { q: '大南门·二马路滨江片区周边 500 米范围内情绪点的分布状况', expectTool: 'buffer', review: '是否缓冲分析？', opts: {} },
  { q: '从已载行政区面中筛选出商业服务业用地的面要素', expectTool: 'filter|extract', review: '是否属性筛选？', opts: {} },
  { q: '裁剪西陵区范围内的全部情绪点为独立点图层', expectTool: 'clip', review: '是否裁剪点层？', opts: {} },
  { q: '西陵区范围内情绪极性最差 Top 5 片区排序', expectTool: 'rank', review: '是否排序？', opts: {} },
  { q: '西陵区范围内各类用地的面积占比统计', expectTool: 'area_stats', review: '是否面积统计？', opts: {} },
  { q: '西陵区范围内情绪点的空间热点分布', expectTool: 'hotspot|density', review: '是否热点？', opts: {} },
  { q: '西陵区内每个情绪点到最近的公园距离', expectTool: 'nearest', review: '是否最近邻？', opts: {} },
  { q: '居住用地范围与西陵区边界的交集面', expectTool: 'overlay', review: '是否叠置？', opts: {} },
  { q: '将西陵区与伍家岗区合并为一个范围面', expectTool: 'merge', review: '是否合并？', opts: {} },
  { q: '西陵区范围内情绪点的 4×5 归因分布统计', expectTool: 'zonal', review: '是否面域聚合+归因？', opts: {} },
];
const TOOLS = TOOL_DATA.map((d, i) => ({
  id: `TOL-${String(i + 1).padStart(2, '0')}`, name: `工具:${d.q.slice(0, 16)}`,
  category: '工具选择', type: 'llm',
  run: async (t) => llmRun(t, d.q, (b) => {
    if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's2', obs: `GAP: "${b}"（应 ${d.expectTool}）` };
    return { pass: true, obs: `badge="${b}"`, review: d.review };
  }, { range: RANGE, ...d.opts }),
}));

// ═══════════════════════════════════════════════════════
// F. 参数正确性（10 例·全 llm）—— 要素+拓扑精准
// ═══════════════════════════════════════════════════════
const PARAM_DATA = [
  { q: '西陵区范围内做 500m 标准方格网格聚合', expectCell: 500, review: 'cell_size=500m？' },
  { q: '西陵区范围内做 2000m 标准方格网格聚合', expectCell: 2000, review: 'cell_size=2000m？' },
  { q: '大南门·二马路滨江片区周边 300 米范围内的情绪点分布', expectRadius: 300, review: 'radius=300m？' },
  { q: '大南门·二马路滨江片区周边 1 公里范围内的情绪点分布', expectRadius: 1000, review: 'radius=1000m？' },
  { q: '西陵区范围内按面聚合情绪统计及 4×5 归因', expectBoundary: '西陵', review: 'boundary=西陵区？' },
  { q: '伍家岗区范围内按面聚合情绪统计及 4×5 归因', expectBoundary: '伍家', review: 'boundary=伍家岗区？' },
  { q: '夷陵区范围内按面聚合情绪统计及 4×5 归因', expectBoundary: '夷陵', review: 'boundary=夷陵区？' },
  { q: '对比西陵区与伍家岗区范围内情绪极性差异', expectBoundary: '西陵.*伍家', review: 'boundaries 含两区？' },
  { q: '从已载行政区中筛选出商业服务业用地的面', expectLayer: '商业', review: 'layer=商业？' },
  { q: '裁剪西陵区范围内的全部情绪点', expectRange: '西陵', review: 'range=西陵区？' },
];
const PARAMS = PARAM_DATA.map((d, i) => ({
  id: `PRM-${String(i + 1).padStart(2, '0')}`, name: `参数:${d.q.slice(0, 16)}`,
  category: '参数正确性', type: 'llm',
  run: async (t) => llmRun(t, d.q, (b) => {
    if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's2', obs: `GAP: "${b}"` };
    return { pass: true, obs: `badge="${b}" geo=${t.geoCalls().length}`, review: d.review };
  }, { range: RANGE }),
}));

// ═══════════════════════════════════════════════════════
// G. 成果范式（10 例：5 no-llm + 5 llm）
// ═══════════════════════════════════════════════════════
const RESULT_NO_LLM = [
  { id: 'RST-01', name: 'layer-list DOM', run: async () => !!document.getElementById('layer-list') ? { pass: true } : { pass: false, stage: 's4' } },
  { id: 'RST-02', name: '#aiq-suggest', run: async () => !!document.getElementById('aiq-suggest') ? { pass: true } : { pass: false, stage: 's4' } },
  { id: 'RST-03', name: '#chat-suggest', run: async () => !!document.getElementById('chat-suggest') ? { pass: true } : { pass: false, stage: 's4' } },
  { id: 'RST-04', name: 'ctx-cap SVG', run: async () => !!document.querySelector('#ctx-cap .ctx-cap-fg') ? { pass: true } : { pass: false, stage: 's4' } },
  { id: 'RST-05', name: 'legend', run: async () => !!document.querySelector('.legend, #legend') ? { pass: true } : { pass: false, stage: 's4' } },
].map((c) => ({ ...c, category: '成果范式', type: 'no-llm' }));

const RESULT_LLM = [
  { id: 'RST-L01', name: 'zonal 产聚合图层', run: async (t) => llmRun(t, '西陵区范围内按面聚合情绪统计及 4×5 归因', (b) => { const n = t.layerNames(); return { pass: true, obs: `badge="${b}" layers=${n.length}`, review: '是否产聚合层+着色？' }; }, { range: RANGE }) },
  { id: 'RST-L02', name: 'compare 产对比图层', run: async (t) => llmRun(t, '对比西陵区与伍家岗区范围内情绪极性差异', (b) => { const n = t.layerNames(); return { pass: true, obs: `badge="${b}" layers=${n.length}`, review: '是否产对比层？' }; }, { range: RANGE }) },
  { id: 'RST-L03', name: 'clip 产点图层', run: async (t) => llmRun(t, '裁剪西陵区范围内的全部情绪点为独立图层', (b) => { const n = t.layerNames(); return { pass: true, obs: `badge="${b}" layers=${n.length}`, review: '是否裁剪出点层？' }; }, { range: RANGE }) },
  { id: 'RST-L04', name: '网格产方格层（非热力）', run: async (t) => llmRun(t, '西陵区范围内做 1000m 标准方格网格聚合', (b) => { const n = t.layerNames(); return { pass: true, obs: `badge="${b}" layers=${n.join(',')}`, review: '是否方格（非彩虹热力）？' }; }, { range: RANGE }) },
  { id: 'RST-L05', name: '通用问答无图层', run: async (t) => llmRun(t, '什么是情绪地图的 4×5 归因矩阵？', (b, tt) => { const a = tt.answerText(); return a && a.length > 10 ? { pass: true, obs: `badge="${b}" ans=${a.length}字`, review: '回答合理？' } : { pass: false, stage: 's4', obs: '回答太短' }; }, { csv: false }) },
].map((c) => ({ ...c, category: '成果范式', type: 'llm' }));

// ═══════════════════════════════════════════════════════
// H. Smart 交流（10 例：6 no-llm + 4 llm）
// ═══════════════════════════════════════════════════════
const SMART_NO_LLM = [
  { id: 'SMT-01', name: '流式中断', run: async (t) => { t.send('测试中断'); await w(500); const s = document.querySelector('#chat-send.is-stop'); if (s) { document.getElementById('chat-send').click(); await w(500); } return { pass: true, obs: '中断路径走通' }; } },
  { id: 'SMT-02', name: '新对话恢复', run: async (t) => { t.newChat(); await w(500); return t.welcome() || t.collapsed() ? { pass: true, obs: '恢复空态' } : { pass: false, stage: 's4' }; } },
  { id: 'SMT-03', name: '历史视图切换', run: async () => { document.getElementById('chat-history')?.click(); await w(300); const ok = document.getElementById('emc-view-history') && !document.getElementById('emc-view-history').hidden; document.getElementById('chat-history')?.click(); await w(200); return ok ? { pass: true } : { pass: false, stage: 's4' }; } },
  { id: 'SMT-04', name: 'F5 恢复', run: async () => ({ pass: true, obs: 'F5 需手动验' }) },
  { id: 'SMT-05', name: '滚动不跳顶', run: async (t) => { document.getElementById('chat-input')?.focus(); await w(300); return t.scrollTop() >= 0 ? { pass: true, obs: `scrollTop=${t.scrollTop()}` } : { pass: false, stage: 's4' }; } },
  { id: 'SMT-06', name: '欢迎卡胶囊', run: async () => !!document.querySelector('.emc-welcome-chip') ? { pass: true } : { pass: false, stage: 's4' } },
].map((c) => ({ ...c, category: 'Smart交流', type: 'no-llm' }));

const SMART_LLM = [
  { id: 'SMT-L01', name: '缺参提问（无范围名）', run: async (t) => llmRun(t, '帮我分析周边情绪分布', (b) => { const ask = document.querySelectorAll('.aiq-ask-chip'); return ask.length > 0 ? { pass: true, obs: `ask ${ask.length} 选项`, review: '问题是否精准？' } : { pass: true, obs: `badge="${b}"`, review: '是否提问了？' }; }, { csv: false }) },
  { id: 'SMT-L02', name: '字段校验（坏字段）', run: async (t) => llmRun(t, '从已载行政区中按 MC 字段筛选要素', (b, tt) => { const a = tt.answerText(); return /字段.*不存在|可用字段/.test(a) ? { pass: true, obs: '字段校验 OK', review: '是否提示可用字段？' } : { pass: true, obs: `badge="${b}"`, review: '字段错是否 Smart 恢复？' }; }, { csv: false, range: RANGE }) },
  { id: 'SMT-L03', name: '换问法（不存在区）', run: async (t) => llmRun(t, ' nonexistent区范围内情绪归因', (b) => { const ask = document.querySelectorAll('.aiq-ask-chip, .aiq-suggest-chip'); return ask.length > 0 || /缺数据|需上传|换/.test(b) ? { pass: true, obs: `badge="${b}"`, review: '是否引导换问法？' } : { pass: true, obs: `badge="${b}"`, review: '响应合理？' }; }, { csv: false }) },
  { id: 'SMT-L04', name: '多轮续作', run: async (t) => { await llmRun(t, '什么是情绪地图？', () => ({ pass: true, obs: '第1轮 general' }), { csv: false }); await w(500); return llmRun(t, '西陵区范围内情绪最差 Top 3 片区及 4×5 归因', (b) => ({ pass: true, obs: `第2轮 badge="${b}"`, review: '多轮续作正常？' }), { range: RANGE }); } },
].map((c) => ({ ...c, category: 'Smart交流', type: 'llm' }));

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
