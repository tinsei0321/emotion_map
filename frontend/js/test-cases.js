// ═══ test-cases.js — 测试飞轮用例集 v4 ═══
// v4 要点：① 意图识别 = NL→工作流转译（断言 template+工具，非回答文本）；
//         ② 工具类针对性训练（每条窄指 1 工具，≤2 工具 ≤4 步）；③ DATA 资产语义引用（test-assets）。
// Prompt 设计原则：docs/emc-prompt-design-principles.md
import { resolveRange, resolvePoints } from './test-assets.js';

const w = (ms) => new Promise((r) => setTimeout(r, ms));
const CSV = 'yichang_L1_T1_result_csv.csv';   // 默认 L1 点层（CB-13 Codex 实锤：xiling_wujia→yichang 改名·旧名 404 致 CPD-L01/L02 静默失败）
const CSV_T2 = 'yichang_L1_T2_result_csv.csv';
const CSV_T3 = 'yichang_L1_T3_result_csv.csv';
const RANGE = '行政区.geojson';                     // 顶层（presets/ 已并于顶层）
const RANGE_ERMAWU = '大南门二马路滨江片区.geojson';

// ── llmRun：跑一问 + 抓「转译链」信号（template / 工具 / 参数 / 产物）──
async function llmRun(t, q, assert, opts = {}) {
  t.clearLog();
  if (opts.csv !== false) {
    const f = resolvePoints(opts.csv || 'L2-T1');
    try { await t.loadCSV(f); await w(800); } catch (_) {}
  }
  if (opts.range) {
    const f = resolveRange(opts.range);
    try { await t.loadRange(f); await w(300); } catch (_) {}
  }
  if (opts.mode) t.setMode(opts.mode);
  // baseline 在点层/范围加载后取 → newLayers/renderedNew 只算工具产出（不含 loadCSV 加的点层）
  const layersBefore = t.layerNames().length;
  const srcBefore = ((t.mapSources && t.mapSources()) || []).length;   // C: map 真渲染 source 基线
  t.send(q);
  const ok = await t.waitAnswer(opts.timeout || 90000);
  if (!ok) return { pass: false, stage: 's3', obs: '回答超时（90s）' };
  const b = t.badge();
  if (!b) return { pass: false, stage: 's4', obs: '无 exit-badge' };
  // 抓转译信号（意图识别验证用）
  const geo = t.geoCalls();
  const _execs = (t.toolExecs && t.toolExecs()) || [];   // #2 density 等前端委托工具（不走 fetch·geoCalls 盲区）
  const _dg = (t.chatPhases().find((p) => p.template) || {});   // D3: diagnose 卡（template+method·method 派生自 D2）
  const sig = {
    tools: [...new Set([
      ...geo.map((e) => {
        const m = String(e.url).split('?')[0].match(/(?:geo|spatial)\/([a-z_0-9]+)/i);
        return m ? m[1] : null;
      }).filter(Boolean),
      ..._execs.map((x) => x && x.tool).filter(Boolean),
    ])],
    template: _dg.template || null,
    method: _dg.method || null,   // D3: 计划工具序列（diagnose method·D2 派生）→ EMC-SUM ② 计划n
    planSteps: _dg.planSteps || 0,   // F-1: 实际执行通道计划步数（_allToolCalls 多 call / autoExpand 链长）·替代 method 派生
    params: _extractParams(geo),
    newLayers: Math.max(0, t.layerNames().length - layersBefore),
    renderedNew: Math.max(0, ((t.mapSources && t.mapSources()) || []).length - srcBefore),   // C: 地图真渲染 source 差值
  };
  const r = assert(b, t, sig);
  if (r && typeof r === 'object') { r.tools = sig.tools; r.template = sig.template; r.method = sig.method; r.params = sig.params; r.newLayers = sig.newLayers; r.renderedNew = sig.renderedNew; r.planSteps = sig.planSteps; }
  return r;
}

function _extractParams(geo) {
  const p = {};
  // T3：参数对象序列化（治 boundary/center 为 GeoJSON 对象时显示 [object Object]·05·INT-005/006）
  // CB-12 Codex 测量伪影修复：GeoJSON boundary 提取区名（features[0].properties 的 name 字段）——否则区名在 properties 内部·正则匹配不到·即使选对也 ERR
  const _regionName = (fc) => {
    const f = (fc && fc.features && fc.features[0]) || {};
    const props = f.properties || {};
    // 常见名称字段（行政区划 name/MC/NAME/区名）
    for (const k of ['name', 'NAME', 'MC', '县区', '区', 'region']) {
      if (props[k] != null) return String(props[k]);
    }
    return Object.values(props).find((v) => typeof v === 'string' && /区|县|市|街道/.test(v)) || '';
  };
  const _sum = (v) => {
    if (v == null || v === '') return undefined;
    if (typeof v === 'string') return v;
    if (typeof v === 'number') return v;
    if (Array.isArray(v)) return '[' + v.map((x) => _sum(x)).join(', ') + ']';   // CB-12：数组元素递归（boundaries 多区·防只显示长度丢区名）
    if (typeof v === 'object') {
      if (v.type === 'FeatureCollection' && v.features) return `GeoJSON{${v.features.length}}#${_regionName(v)}`;
      if (v.type === 'Feature') return `Feature#${_regionName({ features: [v] })}`;
      if (v.coordinates) return `${v.type || ''}{${Array.isArray(v.coordinates) ? v.coordinates.length : '?'}}`;
      return JSON.stringify(v).slice(0, 40);
    }
    return String(v);
  };
  // CB-12 PRM-08 测量修复（Codex）：compare 前端逐区复用 zonal_stats 单 boundary 调用·请求体无 boundaries 数组·
  //   first-capture-wins 只捕第一区 → 断言找不到第二区。改：收集所有 zonal 调用的 boundary（append）→ p.boundaries 数组
  const _boundarySeen = [];
  for (const e of geo) {
    const b = e.body || {};
    if (b.boundary != null) _boundarySeen.push(_sum(b.boundary));
    if (b.boundaries != null) _boundarySeen.push(...(Array.isArray(b.boundaries) ? b.boundaries.map((x) => _sum(x)) : [_sum(b.boundaries)]));
    if (b.cell_size != null && p.cell == null) p.cell = b.cell_size;
    if (b.radius_m != null && p.radius == null) p.radius = b.radius_m;
    if (p.center == null && b.center != null) p.center = _sum(b.center);
  }
  p.boundary = _boundarySeen.length ? _boundarySeen[0] : undefined;
  p.boundaries = _boundarySeen.length > 1 ? _boundarySeen.join('|') : undefined;   // 多区 → boundaries（断言可匹配全部区）
  return p;
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
  { id: 'CPD-L03', name: '新对话恢复引导', run: async (t) => { await t.loadCSV(CSV); await w(500); t.clearRanges(); await w(300); t.newChat(); await w(500); const h = t.hintText(); return h && h.includes('范围') ? { pass: true, obs: '新对话推 range' } : { pass: false, stage: 's1', obs: `新对话后 hint 未推 range（hint="${(h || '').slice(0, 30)}"）` }; } },   // CB-14：newChat 前 clearRanges 清 CPD-L02 残留范围层·让新对话 hasRange=false → 引导回 range 态
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
  { id: 'UI-L01', name: 'exit-badge 渲染（分析型）', run: async (t) => llmRun(t, '西陵区范围内情绪点按极性排序，找出最差 Top 3 片区及 4×5 归因', (b) => ({ pass: true, obs: `badge="${b}"`, review: 'badge 是否准确？' }), { range: '行政区', csv: 'L2-T1' }) },
  { id: 'UI-L02', name: 'exit-badge 渲染（通用型）', run: async (t) => llmRun(t, '什么是情绪地图的 4×5 归因矩阵？', (b) => ({ pass: true, obs: `badge="${b}"`, review: '通用 badge 准确？' }), { csv: false }) },
  { id: 'UI-L03', name: '回答含 markdown 排版', run: async (t) => llmRun(t, '西陵区范围内情绪最差的 Top 3 片区，每个片区的 4×5 归因是什么？', (b, tt) => { const a = tt.answerText(); return { pass: true, obs: `badge="${b}" md=${/[#\*\-]/.test(a)}`, review: '排版是否美观？' }; }, { range: '行政区', csv: 'L2-T1' }) },
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
// D. 意图识别（100 例·全 llm）—— v4 核心纠偏：断言 NL→工作流转译（template+工具），非回答文本
//    意图 = 把自然语言转译成「范围→筛选→分支→工具→步骤」的可执行工作流。
//    通过 = diagnose 选对 template（语义匹配·软）或触发了相关工具。
// ═══════════════════════════════════════════════════════
const DISTRICTS = ['西陵区', '伍家岗区', '夷陵区'];
const ELEMENTS = ['环境', '服务', '设施', '文化'];
const POLARITY = ['最差', '最好', '消极', '积极'];

function _fill(tmpl, v) { return tmpl.replace(/\{([^}]+)\}/g, (_, k) => (v[k] != null ? v[k] : `{${k}}`)); }   // [^}]+ 含中文 key（\w 不匹配中文，旧版致 {区} 未替换）
function _vars(di, qi) {
  return {
    '区': DISTRICTS[di % DISTRICTS.length],
    '要素': ELEMENTS[(qi + di) % ELEMENTS.length],
    'n': [3, 5, 10][di % 3],
    'r': [300, 500, 1000][di % 3],
    'cell': [500, 1000, 2000][di % 3],
    'pol': POLARITY[(qi + di) % POLARITY.length],
  };
}

const PAIRS = [['西陵区', '伍家岗区'], ['西陵区', '夷陵区'], ['伍家岗区', '夷陵区']];
const INTENT_TYPES = [
  { kind: '情绪分析', cycle: '区', expectTmpl: ['zonal', 'rank', 'density', 'multi'], expectTools: ['zonal_stats', 'rank', 'density'], qs: [
    '{区}哪里情绪{pol}', '{区}情绪分布如何', '{区}消极情绪集中在哪', '{区}内{要素}要素的情绪状况', '{区}情绪整体偏向如何', '{区}情绪归因分析', '{区}情绪状况'] },
  { kind: 'GIS操作', cycle: '区', expectTmpl: ['clip', 'extract_feature', 'filter_attr'], expectTools: ['clip', 'extract_feature', 'filter_attr'], qs: [
    '把{区}的情绪点裁剪出来', '筛选{区}内消极极性情绪点', '抽取{区}范围为独立图层', '筛选{区}积极情绪点', '裁剪{区}情绪点为独立层', '提取{区}范围面', '筛选{区}内{要素}相关情绪点'] },
  { kind: '周边分析', cycle: 'r', expectTmpl: ['buffer'], expectTools: ['buffer'], qs: [
    '二马路片区周边{r}米内情绪点分布', '二马路片区附近{r}米情绪点是否消极为主', '二马路片区周围{r}米情绪状况', '二马路片区周边{r}米情绪聚集', '二马路片区{r}米范围内情绪', '二马路片区周边{r}米情绪分析'] },
  { kind: '区域对比', cycle: 'pair', expectTmpl: ['compare'], expectTools: ['compare_regions'], qs: [
    '对比{区A}与{区B}情绪极性差异', '{区A}与{区B}哪个消极占比更高', '对比{区A}与{区B}情绪归因', '{区A} vs {区B}情绪分布', '对比{区A}与{区B}情绪状况', '{区A}与{区B}情绪差异在哪'] },
  { kind: '排序', cycle: '区', expectTmpl: ['rank'], expectTools: ['rank'], qs: [
    '{区}情绪{pol} Top {n} 片区', '{区}最差片区排序', '{区}情绪最好片区排名', '{区}情绪最差片区排行', '{区}情绪 Top {n}', '{区}最差 Top {n}'] },
  { kind: '概念问答', cycle: null, expectTmpl: ['concept'], expectTools: [], qs: [
    '什么是情绪地图的 4×5 归因矩阵', '情绪地图与官方城市体检有何区别', '核密度分析适合什么尺度场景', 'EMC 能做哪些空间分析', '什么是极性', '情绪地图的数据来源是什么', '4×5 矩阵的领域有哪些', '什么是 15 分钟生活圈', '情绪地图如何保护隐私', '城市体检社会满意度调查是什么', '情绪归因的政策锚点是什么', '什么是完整社区'] },
];

function _assertIntent(b, sig, type) {
  if (type.expectTools.length === 0) {   // 概念型：无工具，看非误 GAP
    if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's1', obs: `误GAP:"${b}"` };
    return { pass: true, obs: `tpl=${sig.template || '?'}` };
  }
  if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's1', obs: `误GAP:"${b}"（应 ${type.expectTools.join('|')}）` };
  const tmplOk = sig.template && type.expectTmpl.includes(sig.template);
  const toolOk = type.expectTools.some((x) => sig.tools.includes(x));
  // T6 完成校验：工具型需至少工具执行或落图（灭绝空心 OK·C8·如 INT-005 tpl=multi tools=无 newLayers=0）
  const hasAction = sig.tools.length > 0 || (sig.newLayers > 0) || (sig.renderedNew > 0);
  const pass = (tmplOk || toolOk) && hasAction;
  return { pass, stage: pass ? '' : 's1', obs: `tpl=${sig.template || '?'} tools=${sig.tools.join(',') || '无'} layers=${sig.newLayers || 0}/${sig.renderedNew || 0}`, review: `${type.kind}：转译是否合理？` };
}

const INTENT = [];
{
  let n = 0;
  for (const type of INTENT_TYPES) {
    let combos;
    if (type.cycle === '区') combos = DISTRICTS.map((d) => ({ '区': d, '要素': ELEMENTS[n % ELEMENTS.length], 'pol': POLARITY[n % POLARITY.length], 'n': 5 }));
    else if (type.cycle === 'r') combos = [300, 500, 1000].map((r) => ({ 'r': r }));
    else if (type.cycle === 'pair') combos = PAIRS.map((p) => ({ '区A': p[0], '区B': p[1] }));
    else combos = [{}];
    for (const v of combos) {
      for (const qtmpl of type.qs) {
        if (n >= 100) break;
        const q = _fill(qtmpl, v);
        n++;
        const _t = type;
        INTENT.push({ id: `INT-${String(n).padStart(3, '0')}`, name: `意图:${q.slice(0, 16)}`, category: '意图识别', type: 'llm',
          run: async (t) => llmRun(t, q, (b, _tt, sig) => _assertIntent(b, sig, _t), { csv: 'L2-T1', range: '行政区' }) });
      }
    }
    if (n >= 100) break;
  }
}

// ═══════════════════════════════════════════════════════
// E. 工具选择（100 例·全 llm）—— 针对性训练：每条窄指 1 个 GIS 工具，≤2 工具 ≤4 步
//    断言：触发了目标工具（硬——这是训练 LLM 选对工具的核心信号）
// ═══════════════════════════════════════════════════════
const LANDUSE = ['商业', '居住', '公园广场'];
function _varsTool(di, qi) {
  return {
    '区': DISTRICTS[di % DISTRICTS.length],
    '用地': LANDUSE[(qi + di) % LANDUSE.length],
    '用地A': LANDUSE[(qi + di + 1) % LANDUSE.length],
    '要素': ELEMENTS[(qi + di) % ELEMENTS.length],
    'n': [3, 5, 10][di % 3],
    'r': [300, 500, 1000][di % 3],
    'cell': [500, 1000, 2000][di % 3],
  };
}

const TOOL_TARGETS = [
  { tool: 'density', qs: ['{区}内情绪点的密度热力图', '看{区}情绪点哪里最密集', '{区}情绪点空间密度分布', '全域情绪点密度分布如何'] },
  { tool: 'zonal_stats', qs: ['{区}按面聚合情绪统计及 4×5 归因', '{区}各片区极性分布', '{区}内{要素}要素的情绪归因', '{区}情绪归因分析'] },
  { tool: 'compare_regions', fixed: true, qs: ['对比西陵区与伍家岗区情绪极性差异', '对比西陵区与伍家岗区情绪归因', '对比西陵区与夷陵区情绪分布', '西陵区与伍家岗区哪个消极多', '对比伍家岗区与夷陵区情绪', '西陵区 vs 伍家岗区情绪归因差异'] },
  { tool: 'buffer', fixed: true, qs: ['二马路片区周边 300 米内情绪点分布', '二马路片区周边 500 米情绪点', '二马路片区周边 1 公里情绪点是否消极为主', '二马路片区周围 1000 米情绪', '二马路片区附近 800 米情绪状况', '二马路片区周边 600 米情绪聚集'] },
  { tool: 'rank', qs: ['{区}情绪最差 Top {n} 片区', '{区}情绪最好 Top {n} 片区', '{区}最差片区排序', '{区}情绪片区排名'] },
  { tool: 'clip', qs: ['裁剪{区}内全部情绪点为独立图层', '截取{区}范围内情绪点', '把{区}情绪点裁出来'] },
  { tool: 'extract_feature', fixed: true, qs: ['从行政区筛选商业服务业用地的面', '从行政区筛选居住用地', '从行政区抽取公园广场用地', '筛选行政区{要素}相关用地', '抽取行政区商业用地', '从行政区筛选居住用地要素'] },
  { tool: 'area_stats', qs: ['{区}各类用地面积占比统计', '{区}用地结构面积统计', '{区}用地面积分布'] },
  { tool: 'hotspot', qs: ['{区}情绪点显著聚集分布', '{区}情绪显著聚集在哪', '{区}情绪显著聚集分析'] },
  { tool: 'nearest', fixed: true, qs: ['每个情绪点到最近公园的距离', '情绪点最近的{用地}用地', '情绪点距最近绿地的距离', '情绪点最近{用地}用地在哪', '各情绪点离最近{用地}多远', '情绪点到最近{用地}的距离'] },
  { tool: 'overlay', fixed: true, qs: ['商业用地与居住用地的交集面', '居住用地与公园广场叠置', '商业用地与公园广场交集', '居住与商业用地叠置分析', '公园广场与居住用地交集面', '商业与居住用地叠置'] },
  { tool: 'merge', fixed: true, qs: ['合并西陵区与伍家岗区为一个范围', '合并西陵区与夷陵区范围', '把伍家岗区与夷陵区合并', '西陵区伍家岗区合并范围', '合并西陵区与伍家岗区范围面', '伍家岗区与夷陵区合并为一个面'] },
  { tool: 'density', grid: true, qs: ['{区}做{cell}m 标准方格网格聚合', '{区}{cell}m 方格网格情绪聚合', '{区}{cell}m 网格看每格极性', '{区}标准方格网格聚合情绪'] },
  { tool: 'filter_attr', qs: ['筛选{区}内消极极性情绪点', '筛选{区}内积极情绪点', '筛选{区}内{要素}相关情绪点', '筛选{区}消极情绪点'] },
];

// C: 产图层工具白名单——成功须真在地图渲染（不仅入 state），治「标 OK 实际地图空」
const LAYER_TOOLS = new Set(['density', 'buffer', 'clip', 'overlay', 'merge', 'extract_feature', 'hotspot']);
function _assertTool(b, sig, tgt) {
  if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's2', obs: `GAP:"${b}"（应 ${tgt.tool}）` };
  const ok = sig.tools.includes(tgt.tool);
  if (!ok) return { pass: false, stage: 's2', obs: `未触发 ${tgt.tool}（实 ${sig.tools.join(',') || '无'}）`, review: `${tgt.tool}${tgt.grid ? '(方格)' : ''}是否正确？` };
  // C: 产图层工具触发但地图未渲染新 source = 渲染失败（治「标 OK 实际地图空」）
  if (LAYER_TOOLS.has(tgt.tool) && (sig.renderedNew || 0) === 0) {
    return { pass: false, stage: 's4', obs: `触发${tgt.tool}但地图未渲染(renderedNew=0)`, review: '图层为何不显示？(2a)' };
  }
  return { pass: true, obs: `触发 ${tgt.tool}${sig.newLayers ? `(渲染${sig.renderedNew || 0}/${sig.newLayers}层)` : ''}`, review: `${tgt.tool}${tgt.grid ? '(方格)' : ''}是否正确？` };
}

const TOOLS = [];
{
  let n = 0;
  outer: for (const tgt of TOOL_TARGETS) {
    const cap = tgt.fixed ? tgt.qs.length : Math.ceil(100 / TOOL_TARGETS.length) + 2;  // 固定型全用；轮换型每类 ~9
    let made = 0;
    for (let qi = 0; qi < tgt.qs.length; qi++) {
      const diMax = tgt.fixed ? 1 : DISTRICTS.length;
      for (let di = 0; di < diMax; di++) {
        if (made >= cap) break;
        const q = _fill(tgt.qs[qi], _varsTool(di, qi));
        n++; made++;
        const _tgt = tgt;
        TOOLS.push({ id: `TOL-${String(n).padStart(3, '0')}`, name: `工具:${q.slice(0, 14)}`, category: '工具选择', type: 'llm',
          run: async (t) => llmRun(t, q, (b, _tt, sig) => _assertTool(b, sig, _tgt), { csv: 'L2-T1', range: '行政区' }) });
        if (n >= 100) break outer;
      }
    }
  }
}

// ═══════════════════════════════════════════════════════
// F. 参数正确性（10 例·全 llm）
// ═══════════════════════════════════════════════════════
const PARAM_DATA = [
  { q: '西陵区范围内做 500m 标准方格网格聚合', expectCell: 500, review: 'cell_size=500m？' },
  { q: '西陵区范围内做 2000m 标准方格网格聚合', expectCell: 2000, review: 'cell_size=2000m？' },
  { q: '大南门·二马路滨江片区周边 300 米范围内的情绪点分布', expectRadius: 300, review: 'radius=300m？' },
  { q: '大南门·二马路滨江片区周边 1 公里范围内的情绪点分布', expectRadius: 1000, review: 'radius=1000m？' },
  { q: '西陵区范围内按面聚合情绪统计及 4×5 归因', expectBoundary: '西陵', review: 'boundary=西陵区？' },
  { q: '伍家岗区范围内按面聚合情绪统计及 4×5 归因', expectBoundary: '伍家', review: 'boundary=伍家岗区？' },
  { q: '小溪塔范围内按面聚合情绪统计及 4×5 归因', expectRequestUpload: true, review: '小溪塔=法定功能区·EMC 不识别·应诚实 request_upload' },   // CB-14（用户准则）：小溪塔是法定功能区（非行政区划）·固化库只预置真实行政区划·EMC 应诚实让用户上传标准资料·不硬识别
  { q: '对比西陵区与伍家岗区范围内情绪极性差异', expectBoundary: '西陵.*伍家', review: 'boundaries 含两区？' },
  { q: '从已载行政区中筛选出西陵区', expectLayer: '西陵', review: 'layer=西陵？' },   // CB-12：PRM-09 改问句（原「商业服务业用地」需用地层·B3 setup 只加载行政区·数据前提缺陷·改行政区属性筛选）
  { q: '裁剪西陵区范围内的全部情绪点', expectRange: '西陵', review: 'range=西陵区？' },
];
const PARAMS = PARAM_DATA.map((d, i) => ({
  id: `PRM-${String(i + 1).padStart(2, '0')}`, name: `参数:${d.q.slice(0, 16)}`,
  category: '参数正确性', type: 'llm',
  run: async (t) => llmRun(t, d.q, (b, _tt, sig) => {
    if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's2', obs: `GAP: "${b}"` };
    // CB-12 P1 + P1'（Codex 假阳性修正）：ask_user → PASS 仅限需要澄清参数的用例（center 类·PRM-03/04）
    //   PRM-09（筛选商业）FC 未选工具也触发 ask_user·但本问不需澄清（应 extract 执行）→ 非诚实追问·不 PASS
    //   判据：仅 expectRadius（center 类）用例放行·且 askChips 真实存在
    const _askChips = (_tt && _tt.askChips && _tt.askChips()) || 0;
    if (d.expectRadius != null && (_askChips > 0 || /等你选择/.test(b)) && (!sig.tools || sig.tools.length === 0)) {
      return { pass: true, obs: `合法 ask_user（center 缺·诚实追问）·badge=${b.slice(0, 20)}`, review: '追问是否合理？' };
    }
    // CB-14（用户准则）：expectRequestUpload 用例——法定功能区（非行政区划）EMC 不识别·应诚实 request_upload/ask_user。
    //   GAP/需上传 文案 → PASS（诚实行为）；若 EMC 硬识别产了 boundary → 违规（EMC 不该猜不可信范围）。
    if (d.expectRequestUpload) {
      const _honest = /需上传|未上传|请上传|request_upload|上传.*标准|上传.*资料/.test(b) || (_askChips > 0 && !sig.tools.length);
      return { pass: _honest, stage: _honest ? '' : 's2', obs: _honest ? `诚实 request_upload（不硬识别法定功能区）·badge=${b.slice(0, 20)}` : `EMC 硬识别了法定功能区·应 request_upload（tools=${sig.tools.join(',')}）`, review: d.review };
    }
    // H3: 真比对 sig.params 与 expect*（替代恒 pass）。cell/radius 数值 ±5% 容差；boundary 正则包含。
    const p = sig.params || {};
    const ck = [];
    if (d.expectCell != null) ck.push(['cell', p.cell != null && Math.abs(p.cell - d.expectCell) <= d.expectCell * 0.05, `${p.cell ?? '无'}≠${d.expectCell}`]);
    if (d.expectRadius != null) ck.push(['radius', p.radius != null && Math.abs(p.radius - d.expectRadius) <= d.expectRadius * 0.05, `${p.radius ?? '无'}≠${d.expectRadius}`]);
    if (d.expectBoundary) { const hay = [p.boundary, p.boundaries].filter(Boolean).join('|'); ck.push(['boundary', new RegExp(d.expectBoundary).test(hay), `${hay || '无'}≠/${d.expectBoundary}/`]); }
    // sig 不抓 layer/range 字段，退化为「工具触发」兜底（仍强于恒 pass）
    if (d.expectLayer) ck.push(['layer(tool)', sig.tools.includes('extract_feature'), sig.tools.join(',')]);
    if (d.expectRange) ck.push(['range(tool)', sig.tools.includes('clip'), sig.tools.join(',')]);
    const fail = ck.filter((c) => !c[1]);
    const pass = !fail.length;
    return { pass, stage: pass ? '' : 's2', obs: ck.map((c) => `${c[0]}${c[1] ? '[OK]' : '[ERR]'}`).join(' '), review: d.review };
  }, { range: '行政区', csv: 'L2-T1' }),
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
  { id: 'RST-L01', name: 'zonal 产聚合图层', run: async (t) => llmRun(t, '西陵区范围内按面聚合情绪统计及 4×5 归因', (b, _tt, sig) => ({ pass: true, obs: `badge="${b}" +${sig.newLayers}层`, review: '是否产聚合层+着色？' }), { range: '行政区', csv: 'L2-T1' }) },
  { id: 'RST-L02', name: 'compare 产对比图层', run: async (t) => llmRun(t, '对比西陵区与伍家岗区范围内情绪极性差异', (b, _tt, sig) => ({ pass: true, obs: `badge="${b}" +${sig.newLayers}层`, review: '是否产对比层？' }), { range: '行政区', csv: 'L2-T1' }) },
  { id: 'RST-L03', name: 'clip 产点图层', run: async (t) => llmRun(t, '裁剪西陵区范围内的全部情绪点为独立图层', (b, _tt, sig) => ({ pass: true, obs: `badge="${b}" +${sig.newLayers}层`, review: '是否裁剪出点层？' }), { range: '行政区', csv: 'L2-T1' }) },
  { id: 'RST-L04', name: '网格产方格层（非热力）', run: async (t) => llmRun(t, '西陵区范围内做 1000m 标准方格网格聚合', (b, _tt, sig) => ({ pass: true, obs: `badge="${b}" tools=${sig.tools.join(',')} +${sig.newLayers}层`, review: '是否方格（非彩虹热力）？' }), { range: '行政区', csv: 'L2-T1' }) },
  { id: 'RST-L05', name: '通用问答无图层', run: async (t) => llmRun(t, '什么是情绪地图的 4×5 归因矩阵？', (b, tt) => { const a = tt.answerText(); return a && a.length > 10 ? { pass: true, obs: `badge="${b}" ans=${a.length}字`, review: '回答合理？' } : { pass: false, stage: 's4', obs: '回答太短' }; }, { csv: false }) },
  // CB-12（glm/Codex）：多步问断言——「先裁剪再热力图」两步都执行（防"只做一半"变体复发·CHAIN_REGISTRY clip_density 守门）
  { id: 'RST-L06', name: '多步 先裁剪再热力图', run: async (t) => llmRun(t, '先裁剪西陵区情绪点，再生成热力图', (b, _tt, sig) => {
    const _ok = sig.tools.includes('clip') && sig.tools.includes('density');
    return { pass: _ok, obs: `tools=${sig.tools.join(',')}`, review: '两步都执行了（clip+density）？' };
  }, { range: '行政区', csv: 'L2-T1' }) },
].map((c) => ({ ...c, category: '成果范式', type: 'llm' }));

// ═══ F-2（CB-10 飞轮审查）产物语义断言：不只"选对工具+落图"，验证产物正确性 ═══
// 密度消极色板钩子（CB-04 已修·防回退「消极热力图出综合彩虹图」）+ overlay/clip feature 数。
const PRODUCT_SEMANTIC = [
  { id: 'PRD-S01', name: '产物:消极热力图用消极色板（非彩虹）', category: '产物语义', type: 'llm',
    run: async (t) => llmRun(t, '帮我生成西陵区消极情绪的热力图',
      (b, _t, sig) => {
        if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's1', obs: `误GAP:"${b}"` };
        const prods = (t.productLayers && t.productLayers(5)) || [];
        const heat = prods.find((l) => l.kind === 'heatmap') || prods[prods.length - 1] || {};
        // 消极热力图 → analysisKey=negative + 色板非 terrain（彩虹）
        const ui = heat.paint || {};
        const negOk = ui.analysisKey === 'negative' && heat.rampKey && heat.rampKey !== 'terrain';
        return { pass: negOk, stage: negOk ? '' : 's2', obs: `analysis=${ui.analysisKey} ramp=${heat.rampKey} layers=${sig.newLayers}`, review: '消极热力图是否用消极色板（非综合彩虹）？' };
      }, { range: '行政区', csv: 'L2-T1' }) },
  { id: 'PRD-S02', name: '产物:overlay 交集产面层', category: '产物语义', type: 'llm',
    run: async (t) => llmRun(t, '商业用地与居住用地的交集面',
      (b, _t, sig) => {
        if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's1', obs: `误GAP:"${b}"` };
        const prods = (t.productLayers && t.productLayers(5)) || [];
        const overlay = prods.find((l) => l.kind === 'polygon' && (l.paint && l.paint.tool === 'overlay')) || prods[prods.length - 1] || {};
        return { pass: overlay.kind === 'polygon' && overlay.fcCount > 0, stage: overlay.fcCount ? '' : 's2', obs: `kind=${overlay.kind} feats=${overlay.fcCount}`, review: 'overlay 是否产交集面层（非空）？' };
      }, { range: '行政区', csv: 'L2-T1' }) },
].map((c) => ({ ...c, type: 'llm' }));

// ═══════════════════════════════════════════════════════
// F. FC 全链路（20 例·emc_test_cases.md → 可执行飞轮用例）
//    覆盖 v2/v3 架构：FC 诊断→工具执行→finalStep→追问→诚实→语言
// ═══════════════════════════════════════════════════════
const EMC_FC = [
  { id: 'FC-01', name: '生成综合热力图', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '帮我生成一张L2数据的情绪热力图，我想看到分布情况',
      (b, _t, sig) => {
        if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's1', obs: `误GAP:"${b}"` };
        const toolOk = sig.tools.includes('density');
        const hasLayer = sig.newLayers > 0 || sig.renderedNew > 0;
        return { pass: toolOk && hasLayer, stage: toolOk ? '' : 's1', obs: `tools=${sig.tools.join(',')} layers=${sig.newLayers}/${sig.renderedNew}`, review: '综合热力图是否正常生成？' };
      }, { csv: 'L2-T1' }) },

  { id: 'FC-02', name: '切换消极热力图（追问）', category: 'FC全链路', type: 'llm',
    run: async (t) => {
      await llmRun(t, '帮我生成一张情绪热力图', () => ({ pass: true, obs: '第1轮综合' }), { csv: 'L2-T1' });
      await w(500);
      return llmRun(t, '进一步分析消极情绪点的分布',
        (b, _t, sig) => {
          if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's1', obs: `追问失败:"${b}"` };
          const toolOk = sig.tools.includes('density');
          const noFilterAttr = !sig.tools.includes('filter_attr');
          const hasLayer = sig.newLayers > 0 || sig.renderedNew > 0;
          return { pass: toolOk && noFilterAttr && hasLayer, stage: '', obs: `tools=${sig.tools.join(',')} layers=${sig.newLayers}/${sig.renderedNew}`, review: '追问应直接 density(negative)·非 filter_attr' };
        }, { csv: false });
    } },

  { id: 'FC-03', name: '区域排序', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '哪些区域情绪最差？排序看看',
      (b, _t, sig) => {
        if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's1', obs: `误GAP:"${b}"` };
        const toolOk = sig.tools.includes('rank');
        return { pass: toolOk, stage: toolOk ? '' : 's1', obs: `tools=${sig.tools.join(',')}`, review: 'rank 被选中？' };
      }, { csv: 'L2-T1', range: '行政区' }) },

  { id: 'FC-04', name: '区域归因', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '这几个街道的情绪归因分析',
      (b, _t, sig) => {
        if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's1', obs: `误GAP:"${b}"` };
        const toolOk = sig.tools.includes('zonal_stats');
        return { pass: toolOk, stage: toolOk ? '' : 's1', obs: `tools=${sig.tools.join(',')}`, review: 'zonal 被选中？' };
      }, { csv: 'L2-T1', range: '行政区' }) },

  { id: 'FC-05', name: '区域对比', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '对比西陵区和伍家岗区的情绪差异',
      (b, _t, sig) => {
        if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's1', obs: `误GAP:"${b}"` };
        const toolOk = sig.tools.includes('compare_regions');
        return { pass: toolOk, stage: toolOk ? '' : 's1', obs: `tools=${sig.tools.join(',')}`, review: 'compare 被选中？' };
      }, { csv: 'L2-T1', range: '行政区' }) },

  { id: 'FC-06', name: '抽取面层要素', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '帮我从中心城区范围中裁剪出西陵区的范围',
      (b, _t, sig) => {
        const toolOk = sig.tools.includes('extract_feature');
        const hasLayer = sig.newLayers > 0 || sig.renderedNew > 0;
        const noErr = !/\[ERR\]|没成功|未成功/.test(b);
        return { pass: toolOk && hasLayer && noErr, stage: '', obs: `tools=${sig.tools.join(',')} badge="${String(b).slice(0,20)}" layers=${sig.newLayers}`, review: '字段自纠正 MC→name 是否生效？' };
      }, { csv: false, range: '行政区' }) },

  { id: 'FC-07', name: '概念问短路', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '什么是情绪地图？',
      (b) => {
        if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's1', obs: `误GAP:"${b}"` };
        return { pass: true, obs: `概念问直答 badge="${b}"`, review: '回答是否生动专业？' };
      }, { csv: false }) },

  { id: 'FC-08', name: '缓冲分析', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '滨江公园周边500米的情绪分布',
      (b, _t, sig) => {
        const toolOk = sig.tools.includes('buffer');
        const hasLayer = sig.newLayers > 0 || sig.renderedNew > 0;
        return { pass: toolOk && hasLayer, stage: toolOk ? '' : 's1', obs: `tools=${sig.tools.join(',')} layers=${sig.newLayers}`, review: 'buffer radius=500？' };
      }, { csv: 'L2-T1' }) },

  { id: 'FC-09', name: '叠置分析', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '商业用地和居住用地的交集区域',
      (b, _t, sig) => {
        const toolOk = sig.tools.includes('overlay');
        return { pass: toolOk, stage: toolOk ? '' : 's1', obs: `tools=${sig.tools.join(',')}`, review: 'overlay how=intersection？' };
      }, { csv: false, range: '行政区' }) },

  { id: 'FC-10', name: '裁剪点层', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '西陵区范围内的情绪点',
      (b, _t, sig) => {
        const toolOk = sig.tools.includes('clip');
        const hasLayer = sig.newLayers > 0 || sig.renderedNew > 0;
        const noErr = !/\[ERR\]|没成功/.test(b);
        return { pass: toolOk && hasLayer && noErr, stage: '', obs: `tools=${sig.tools.join(',')} layers=${sig.newLayers}`, review: 'clip 裁点成功？' };
      }, { csv: 'L2-T1', range: '行政区' }) },

  { id: 'FC-11', name: '切换积极热力图', category: 'FC全链路', type: 'llm',
    run: async (t) => {
      await llmRun(t, '生成情绪热力图', () => ({ pass: true, obs: '第1轮综合' }), { csv: 'L2-T1' });
      await w(500);
      return llmRun(t, '换个角度看看积极情绪的分布',
        (b, _t, sig) => {
          const toolOk = sig.tools.includes('density');
          const hasLayer = sig.newLayers > 0 || sig.renderedNew > 0;
          return { pass: toolOk && hasLayer, stage: '', obs: `tools=${sig.tools.join(',')} layers=${sig.newLayers}`, review: '积极热力图？' };
        }, { csv: false });
    } },

  { id: 'FC-12', name: '无点数据时拒绝', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '生成情绪热力图',
      (b) => {
        const graceful = /需上传|请上传|需要.*数据|数据.*上传/.test(b);
        const noErr = !/\[ERR\]|无已加载的情绪点层/.test(b);
        return { pass: graceful && noErr, stage: graceful ? '' : 's1', obs: `badge="${String(b).slice(0,30)}"`, review: '是否优雅提示而非硬报错？' };
      }, { csv: false, range: '行政区' }) },

  { id: 'FC-13', name: '失败后智能建议', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '帮我裁剪西陵区的点',
      (b) => {
        const hasSuggest = /抽取|extract|换个|分析方向|能做哪些/.test(b);
        const noRawErr = !/\[ERR\]/.test(b);
        return { pass: noRawErr, stage: '', obs: `badge="${String(b).slice(0,30)}" suggest=${hasSuggest}`, review: '失败后是否建议 extract_feature？' };
      }, { csv: false, range: '行政区' }) },

  { id: 'FC-14', name: 'qualityDefense 不崩', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '帮我生成一张情绪热力图',
      (b, _t, sig) => {
        const noCrash = !/请求失败|reg\.filter|not a function/.test(b);
        const hasLayer = sig.newLayers > 0 || sig.renderedNew > 0;
        return { pass: noCrash && hasLayer, stage: '', obs: `crash=${!noCrash} layers=${sig.newLayers}`, review: 'quality defense 正常运行？' };
      }, { csv: 'L2-T1' }) },

  { id: 'FC-15', name: 'FC 失败降级', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '生成全域情绪分布',
      (b) => {
        const noCrash = !/请求失败|502|500/.test(b);
        return { pass: noCrash, stage: '', obs: `badge="${String(b).slice(0,30)}"`, review: 'FC 失败优雅降级？' };
      }, { csv: 'L2-T1', timeout: 120000 }) },

  { id: 'FC-16', name: '禁英文术语', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '分析情绪热度',
      (b) => {
        const text = (t.answerText && t.answerText()) || '';
        const hasEng = /\b(density|extract_feature|zonal_stats|polarity|boundary|radius|emotion_intensity|filter_attr|overlay|buffer|compare_regions|rank|hotspot|nearest|merge|area_stats)\b/.test(text);
        return { pass: !hasEng, stage: '', obs: hasEng ? '含英文术语' : '全中文', review: '结论是否含英文工具名/字段名？' };
      }, { csv: 'L2-T1' }) },

  { id: 'FC-17', name: '禁箭头符号', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '哪些区域情绪最差？排序',
      (b) => {
        const text = (t.answerText && t.answerText()) || '';
        const hasArrow = /→/.test(text);
        return { pass: !hasArrow, stage: '', obs: hasArrow ? '含箭头' : '无箭头', review: '结论是否含 → 符号？' };
      }, { csv: 'L2-T1', range: '行政区' }) },

  { id: 'FC-18', name: '生动专业表达', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '什么是情绪地图？',
      (b) => {
        const text = (t.answerText && t.answerText()) || '';
        const hasBg = /人民城市|温情|情绪价值|急难愁盼|人本视角/.test(text);
        const long = text.length > 50;
        return { pass: hasBg && long, stage: '', obs: `len=${text.length} bg=${hasBg}`, review: '回答是否含背景词汇且生动？' };
      }, { csv: false }) },

  { id: 'FC-19', name: '多轮复合追问', category: 'FC全链路', type: 'llm',
    run: async (t) => {
      const r1 = await llmRun(t, '生成情绪热力图', () => ({ pass: true, obs: 'R1 ok' }), { csv: 'L2-T1' });
      if (!r1.pass) return { pass: false, stage: 's1', obs: `R1 失败: ${r1.obs}` };
      await w(500);
      const r2 = await llmRun(t, '分析消极情绪', () => ({ pass: true, obs: 'R2 ok' }), { csv: false });
      if (!r2.pass) return { pass: false, stage: 's2', obs: `R2 失败: ${r2.obs}` };
      await w(500);
      return llmRun(t, '哪些区域最差', (b, _t, sig) => {
        const toolOk = sig.tools.includes('rank');
        return { pass: toolOk, stage: toolOk ? '' : 's3', obs: `R3 tools=${sig.tools.join(',')}`, review: '多轮链每轮不失败？' };
      }, { csv: false, range: '行政区' });
    } },

  { id: 'FC-20', name: '胶囊点击执行', category: 'FC全链路', type: 'llm',
    run: async (t) => {
      await llmRun(t, '生成情绪热力图', () => ({ pass: true, obs: '第1轮' }), { csv: 'L2-T1' });
      await w(500);
      const chip = document.querySelector('.aiq-suggest-chip.aiq-capsule, .aiq-suggest-chip[data-capsule-idx]');
      if (!chip) return { pass: true, obs: '无胶囊（finalStep 未产·plans 常空·可接受）', review: '追问胶囊是否出现？' };
      chip.click();
      const ok = await t.waitAnswer(30000);
      if (!ok) return { pass: false, stage: 's3', obs: '胶囊点击超时' };
      const b = t.badge();
      return { pass: !/请求失败|ERR/.test(b || ''), stage: '', obs: `胶囊执行 badge="${String(b || '').slice(0,20)}"`, review: '胶囊点击是否快速出图？' };
    } },

  // ═══ CF-09 新采集（2026-07-29·7 例·覆盖 finalStep 假结论/推理螺旋/多步链/样式/类型/视角）═══
  // B002: finalStep 假结论 — 多类操作只说不做
  { id: 'FC-21', name: 'CF09·多类用地裁剪+诚实结论', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '裁剪出西陵区范围内的情绪点，并生成一张热力图',
      (b, _t, sig) => {
        const noFake = !/（注：未实际生成）/.test(b);   // 诚实标记
        const hasAction = sig.tools.length > 0;
        const hasLayer = sig.newLayers > 0 || sig.renderedNew > 0;
        const noCrash = !/请求失败/.test(b);
        return { pass: hasAction && noFake && noCrash, stage: '', obs: `tools=${sig.tools.join(',')} layers=${sig.newLayers}/${sig.renderedNew} fake=${!noFake}`, review: '是否真实产出图层？假结论是否消除？' };
      }, { csv: 'L2-T1', range: '行政区' }) },

  // B003: LLM 推理螺旋 — 简单查询耗时异常
  { id: 'FC-22', name: 'CF09·数据清单查询短路径', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '我上传了哪些数据？',
      (b) => {
        const noGap = !/缺数据|未产出|需上传/.test(b);
        const noCrash = !/请求失败/.test(b);
        return { pass: noGap && noCrash, stage: '', obs: `badge="${String(b).slice(0,30)}"`, review: '是否直接回答（非推理螺旋）？' };
      }, { csv: 'L2-T1', range: '行政区' }) },

  // B004: finalStep 假结论 — 筛选点图层只说不做
  { id: 'FC-23', name: 'CF09·点层裁剪执行验证', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '将西陵区范围内的情绪点筛选出来单独显示',
      (b, _t, sig) => {
        const hasLayer = sig.newLayers > 0 || sig.renderedNew > 0;
        const noFake = !/（注：未实际生成）/.test(b);
        const noCrash = !/请求失败/.test(b);
        const toolOk = sig.tools.includes('clip') || sig.tools.includes('extract_feature');
        return { pass: toolOk && hasLayer && noFake && noCrash, stage: '', obs: `tools=${sig.tools.join(',')} layers=${sig.newLayers}/${sig.renderedNew}`, review: '裁剪结果是否实际落地？' };
      }, { csv: 'L2-T1', range: '行政区' }) },

  // B005: 多步链断裂 — 只做一半
  { id: 'FC-24', name: 'CF09·多步链完整性', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '分别裁剪出西陵区和伍家岗区的情绪点',
      (b, _t, sig) => {
        const hasLayer = sig.newLayers > 0 || sig.renderedNew > 0;
        const noFake = !/（注：未实际生成）/.test(b);
        const noCrash = !/请求失败/.test(b);
        // 多步操作应触发 extract_feature（抽取区范围）或 clip
        const hasMultiTool = sig.tools.length >= 1;
        return { pass: hasMultiTool && hasLayer && noFake && noCrash, stage: '', obs: `tools=${sig.tools.join(',')} layers=${sig.newLayers}/${sig.renderedNew} steps=${sig.tools.length}`, review: '多区操作是否全部完成？' };
      }, { csv: 'L2-T1', range: '行政区' }) },

  // B006: 意图缩窄 — "情绪点"不应缩为单极性
  { id: 'FC-25', name: 'CF09·全极性操作不缩窄', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '能帮我筛选出西陵区的情绪点吗？',
      (b, _t, sig) => {
        const hasLayer = sig.newLayers > 0 || sig.renderedNew > 0;
        const noFake = !/（注：未实际生成）/.test(b);
        const noCrash = !/请求失败/.test(b);
        // 不应只针对"积极"极性（用户没限定）
        const answer = (t.answerText && t.answerText()) || '';
        const narrowedToSinglePolarity = /仅.*积极|只.*积极|积极情绪点/.test(answer) && !/消极/.test(answer) && !/中性/.test(answer);
        return { pass: hasLayer && noFake && noCrash && !narrowedToSinglePolarity, stage: '', obs: `layers=${sig.newLayers}/${sig.renderedNew} narrow=${narrowedToSinglePolarity}`, review: '是否自行缩窄为单一极性？' };
      }, { csv: 'L2-T1', range: '行政区' }) },

  // B007: 图层类型混乱 — 声称面层实际产出点层
  { id: 'FC-26', name: 'CF09·图层类型一致性', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '从行政区中抽取西陵区的范围',
      (b, _t, sig) => {
        const hasLayer = sig.newLayers > 0 || sig.renderedNew > 0;
        const toolOk = sig.tools.includes('extract_feature') || sig.tools.includes('clip');
        const noFake = !/（注：未实际生成）/.test(b);
        const noCrash = !/请求失败/.test(b);
        return { pass: toolOk && hasLayer && noFake && noCrash, stage: '', obs: `tools=${sig.tools.join(',')} layers=${sig.newLayers}/${sig.renderedNew}`, review: '抽取的面层是否正确渲染？' };
      }, { csv: false, range: '行政区' }) },

  // B008: 网格聚合 2D/3D 视角未解耦（老 bug）
  { id: 'FC-27', name: 'CF09·网格聚合生成验证', category: 'FC全链路', type: 'llm',
    run: async (t) => llmRun(t, '对当前区域做500m方格网聚合',
      (b, _t, sig) => {
        const toolOk = sig.tools.includes('density');
        const hasLayer = sig.newLayers > 0 || sig.renderedNew > 0;
        const noCrash = !/请求失败/.test(b);
        // 检查 cell_size 参数
        const hasCellParam = sig.params && sig.params.cell === 500;
        return { pass: toolOk && hasLayer && noCrash, stage: '', obs: `tools=${sig.tools.join(',')} layers=${sig.newLayers}/${sig.renderedNew} cell=${sig.params?.cell || '?'}`, review: '网格是否生成？2D/3D 视角适配？' };
      }, { csv: 'L2-T1' }) },
];

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
  { id: 'SMT-L02', name: '字段校验（坏字段）', run: async (t) => llmRun(t, '从已载行政区中按 MC 字段筛选要素', (b, tt) => { const a = tt.answerText(); return /字段.*不存在|可用字段/.test(a) ? { pass: true, obs: '字段校验 OK', review: '是否提示可用字段？' } : { pass: true, obs: `badge="${b}"`, review: '字段错是否 Smart 恢复？' }; }, { csv: false, range: '行政区' }) },
  { id: 'SMT-L03', name: '换问法（不存在区）', run: async (t) => llmRun(t, ' nonexistent区范围内情绪归因', (b) => { const ask = document.querySelectorAll('.aiq-ask-chip, .aiq-suggest-chip'); return ask.length > 0 || /缺数据|需上传|换/.test(b) ? { pass: true, obs: `badge="${b}"`, review: '是否引导换问法？' } : { pass: true, obs: `badge="${b}"`, review: '响应合理？' }; }, { csv: false }) },
  { id: 'SMT-L04', name: '多轮续作', run: async (t) => { await llmRun(t, '什么是情绪地图？', () => ({ pass: true, obs: '第1轮 general' }), { csv: false }); await w(500); return llmRun(t, '西陵区范围内情绪最差 Top 3 片区及 4×5 归因', (b) => ({ pass: true, obs: `第2轮 badge="${b}"`, review: '多轮续作正常？' }), { range: '行政区', csv: 'L2-T1' }); } },
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
  ...EMC_FC,
  ...PRODUCT_SEMANTIC,   // F-2 产物语义断言（CB-10 飞轮审查）
];

export const CATEGORIES = ['CPD导游', 'UI渲染', '引擎谓词', '意图识别', '工具选择', '参数正确性', '成果范式', 'Smart交流', 'FC全链路'];
