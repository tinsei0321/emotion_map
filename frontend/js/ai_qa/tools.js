// ═══ tools.js — Agent Loop 工具集（查询型 + 操作型，直调主窗口函数）═══
// ═══ 范围来源注册机制（CB-14·用户准则）═══
// 范围参数必须锚定「明确来源」，不做自由语义猜测。来源机制可增补（非固定枚举）：
//  ① 用户绘制（地图手绘 polygon）  ② 临时上传范围（含需剪裁）  ③ 固化库范围（预设面域·可剪裁）  ④ 未来可增补
// 固化库行政区划（admin_district preset）只识别【真实行政区划】——法定功能区（小溪塔/龙泉/东部产业新区/
// 生物产业园等）不在白名单 → 锚定失败 → 诚实 request_upload（EMC 不硬识别不可信的范围）。
// RANGE_SOURCES 为可扩展注册表：新增来源类型 = 追加条目 + 判定函数（见 _RANGE_SOURCE_OF）。
const FIXED_ADMIN_DISTRICTS = ['西陵区', '伍家岗区', '猇亭区', '点军区'];   // 固化库真实行政区划（宜昌·可增补·法定功能区不预置）
// 还原单窗口后，tools 直调 map/state/panel（删跨窗口协议）。每个 tool 返回 {observation, data?}：
//   observation = 给 LLM 看的摘要字符串（入 tool_history）；data = 结构化（前端可选用于渲染）。
import { getLayers, getLayer, getSelectedLayer, addGroup, removeLayer, setLayerVisible, _isAILayer } from '../state.js';
import * as data_registry from '../data_registry.js';   // R3：registry 来源标注（治 C2）
import { fitBoundsTo, renderLayer, reorderAllZ, removeLayerFromMap, getMap } from '../map.js';
import { activateTab, setOverview } from '../panel.js';
import { DOMAIN_LABEL, ELEMENT_LABEL } from '../popup.js';
import { generateGridForAI } from '../grid-tool.js';   // density/ensure_zone 委托（piToNorm 已随迁 toolbox 模块·步 7 prune）
import { generateHeatmapForAI, generateTerrainForAI, generateTerrain3DForAI } from '../heatmap-tool.js';   // 工作机制重构：density 委托 Toolbox（2D 彩虹/3D 地形·P1.5 切 setTerrain 连续曲面）
// ── 步 7 emc-delegate：12 GIS 工具委托 Toolbox 统一工具集层（手册 v2.2 §6 步 7；模块名 = 手册 §1 架构）──
import { generateBufferForAI } from '../buffer-tool.js';   // buffer 委托固定 kind:'emotion'（§5.7/D3）
import { generateZonalForAI, generateCompareForAI } from '../toolbox/zonal-tool.js';
import { generateAreaStatsForAI } from '../toolbox/area-stats-tool.js';
import { generateRankForAI } from '../toolbox/rank-tool.js';
import { generateOverlayForAI, generateClipForAI, generateExtractForAI, generateMergeForAI, generateFilterForAI } from '../toolbox/vector-tool.js';
import { generateNearestForAI } from '../toolbox/nearest-tool.js';
import { generateHotspotForAI } from '../toolbox/hotspot-tool.js';
import { renderLayerList, refreshLegend } from '../sidebar.js';
import { fcBBox, profileFields } from '../import.js';
import { resolveRole, isRenderContract, isInternalField } from '../field_dictionary.js';   // P2/P3 字段语义层·规则标注 + _fieldSamples 语义过滤
import { resolveBoundaryInput } from './boundary-resolve.js';   // 中文地名→GeoJSON（治 compare 中文名错配 5.115）
import { getCurState, CPD_STEPS } from './cpd-state.js';   // CPD Phase 2b：curState 语境 hint（不动路由）
// ── Toolbox 统一工具集层 · 步 1：共享基建抽取至 toolbox/shared.js（手册 §3.2 去向表）——
// import 别名保内部调用点零改动；re-export 保 tools.js 导出面兼容。
import { renderNote as _renderNote, scaleRadius as _scaleRadius, clampM as _clampM,
  toolContentSig as _toolContentSig, addToolboxLayer } from '../toolbox/shared.js';
export { buildZonalFc, defaultPaint, renderNote, scaleRadius, clampM, toolContentSig,
  addToolboxLayer, resolveBoundaryGeo, SCALE_TABLE, geoPost } from '../toolbox/shared.js';

let _lastGrid = null;   // 最近生成聚合层（ensure_zone/query 优先用）

// ── GIS 工具骨干（POST /api/v1/geo/*）═══════════════════════════════════════
let _geoCatalogPromise = null;
const _DOMAIN_CN2EN = { '规划': 'urban_planning', '更新': 'urban_renewal', '运营': 'urban_operation', '治理': 'urban_governance' };

/** GET /api/v1/geo/catalog（模块级缓存，buildContext 增列「边界/时点/工具」用）。 */
export function getGeoCatalog() {
  if (_geoCatalogPromise) return _geoCatalogPromise;
  _geoCatalogPromise = fetch('/api/v1/geo/catalog')
    .then((r) => (r.ok ? r.json() : null))
    .catch(() => null)
    .then((c) => { _buildUsageBlocked(c); return c || null; });
  return _geoCatalogPromise;
}

/** 上传/激活新边界预设后失效目录缓存 → 下一轮 AI 即可见新预设（不必刷新页面）。 */
export function invalidateGeoCatalog() { _geoCatalogPromise = null; _usageBlocked = null; }

// PT-CB2 T2·铁律7 前置守卫：catalog 投影——结论层（usage=analysis_output）id→label 集合。
// 数据源=后端 /geo/catalog（manifest 单一权威的投影，非第二份名单）；catalog 未就绪时跳过→后端
// validate_input_usage 权威兜底。覆盖通道：① preset_id 直传；② 已加载 preset 层（l.presetId 标记）。
let _usageBlocked = null;
function _buildUsageBlocked(cat) {
  _usageBlocked = null;
  if (!cat || !Array.isArray(cat.boundaries)) return;
  const m = new Map();
  for (const b of cat.boundaries) {
    if (b && b.usage === 'analysis_output') m.set(b.id, b.label || b.id);
  }
  _usageBlocked = m;
}
function _guardUsageRef(v) {
  if (typeof v !== 'string' || v === '' || _usageBlocked === null) return;
  const label = _usageBlocked.get(v);
  if (label != null) {
    throw new Error(`「${label}」(${v}) 是分析结论层（usage=analysis_output），不能作空间操作输入（结论不当原料·铁律7）。请改用分析原料层（usage=input）或上传标准边界资料`);
  }
}

/** GET /api/v1/aiqa/wisdom（模块级缓存，buildContext 增列 L2 答问智慧用）。 */
export function getWisdom() {
  if (_wisdomPromise) return _wisdomPromise;
  _wisdomPromise = fetch('/api/v1/aiqa/wisdom')
    .then((r) => (r.ok ? r.json() : null))
    .catch(() => null)
    .then((w) => (w && w.wisdom_text) || '');
  return _wisdomPromise;
}
let _wisdomPromise = null;

// ── P2 字段语义层 · 字段卡片缓存 + LLM 推断接线 ─────────────────────────────
// _fieldCardCache：layerId → {field:{role,dtype,samples,source,confidence}}。懒加载——
// 首次问询（buildContext/_fieldSamples）调 getFieldCard 算一次，后续命中缓存（图层移除时由 layers:changed 清）。
const _fieldCardCache = new Map();

// WS1 F1.6：localStorage 持久层（跨重载/跨 send·字段签名=列名集·值变不触发重推断·治 buildContext 隐式 profile_fields LLM）
const _FIELDCARD_LS = 'emc_fieldcard_';
function _fieldSig(fc) { try { return Object.keys(profileFields(fc)).sort().join(','); } catch (e) { return ''; } }
function _lsGetCard(layerId, sig) {
  try { const raw = localStorage.getItem(_FIELDCARD_LS + layerId); if (!raw) return null;
    const o = JSON.parse(raw); return (o && o.sig === sig) ? o.cards : null; } catch (e) { return null; }
}
function _lsSetCard(layerId, sig, cards) {
  try { localStorage.setItem(_FIELDCARD_LS + layerId, JSON.stringify({ sig, cards })); } catch (e) {}
}

/** POST /api/v1/aiqa/profile_fields：为规则 miss 的字段调 LLM 推断 role。
 *  复用后端 chat_with_fallback 韧性链；失败/降级返 {fields:{},degraded:True} 不抛（AI 仍可用规则命中的字段）。 */
async function fetchProfileFields(body) {
  try {
    const r = await fetch('/api/v1/aiqa/profile_fields', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error((j && (j.detail || j.error)) || ('HTTP ' + r.status));
    return j;   // {fields:{field:{role,confidence,reason}}, degraded?}
  } catch (e) {
    return { fields: {}, degraded: true, degraded_reason: String((e && e.message) || e) };
  }
}

/** POST /api/v1/run：执行 agent 生成的 Python（run_python 工具后端，照 fetchProfileFields 范式）。
 *  返 {ok, stdout, error, figs}；figs=[{id,name,dataUri}]（图片 base64，前端 _figCache 缓存供 {{fig:ID}} 渲染）。
 *  失败抛 Error（run_python 工具内 catch 归一为 observation，不向 harness 抛）。 */
async function fetchRun(body) {
  const r = await fetch('/api/v1/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((j && (j.detail || j.error)) || ('HTTP ' + r.status));
  return j;
}

/** 字段卡片（P2）：profile → 规则标注（resolveRole）→ miss 调 /aiqa/profile_fields → 缓存。
 *  返 {field:{role,dtype,samples,source:'rule'|'llm'|'rule-miss',confidence}}。
 *  物理列名不改（只读 fc.properties）。LLM 全不可用→miss 字段标 rule-miss 不抛（降级）。 */
/** 字段卡片（P2 · Layer Manifest 最小版 5.211）：profile → 规则标注（resolveRole）→ miss 调 /aiqa/profile_fields → 缓存。
 *  返 {field:{role,dtype,samples,source:'rule'|'llm'|'rule-miss',confidence}}。物理列名不改（只读 fc.properties）。LLM 全不可用→miss 字段标 rule-miss 不抛（降级）。
 *  Layer Manifest 最小版（5.211）：_fieldCardCache 存 **Promise**（非值）→ 并发首次（layers:changed 预计算 + buildContext 同帧调）
 *  命中同一 Promise·不重复 LLM。调用方 await 不变。 */
export async function getFieldCard(layerId, fc, layerKind = 'point') {
  if (layerId && _fieldCardCache.has(layerId)) return _fieldCardCache.get(layerId);   // Promise·await 得值
  // WS1 F1.6：localStorage 持久层命中（签名匹配）→ 包成 resolved Promise·与 Map 同形
  if (layerId) {
    const ls = _lsGetCard(layerId, _fieldSig(fc));
    if (ls) { const _rp = Promise.resolve(ls); _fieldCardCache.set(layerId, _rp); return _rp; }
  }
  const _p = (async () => {
    const profile = profileFields(fc);
    const cards = {};
    const miss = {};
    for (const field of Object.keys(profile)) {
      const p = profile[field];
      const role = resolveRole(field);
      if (role) {
        cards[field] = { role, dtype: p.dtype, samples: p.samples, source: 'rule', confidence: 1.0 };
      } else {
        miss[field] = p;   // 规则 miss → 交 LLM
      }
    }
    if (Object.keys(miss).length) {
      const inferred = await fetchProfileFields({ fields: miss, layer_kind: layerKind });
      const inf = (inferred && inferred.fields) || {};
      for (const field of Object.keys(miss)) {
        const p = profile[field];
        const card = inf[field];
        if (card && card.role) {
          cards[field] = { role: card.role, dtype: p.dtype, samples: p.samples, source: 'llm', confidence: card.confidence || 0.5, reason: card.reason || '' };
        } else {
          cards[field] = { role: null, dtype: p.dtype, samples: p.samples, source: 'rule-miss', confidence: 0 };
        }
      }
    }
    if (layerId) _lsSetCard(layerId, _fieldSig(fc), cards);   // WS1 F1.6：持久化（列名签名·下次直接命中 LS）
    return cards;
  })();
  if (layerId) _fieldCardCache.set(layerId, _p);   // 首次即存 Promise·并发命中同一（并发安全）
  return _p;
}
/** Layer Manifest 最小版（5.211）：新可见层导入即预计算 fieldCard（fire-and-forget·首次 diagnose 命中缓存·治首字延迟·C9 根治）。
 *  监听 layers:changed（addLayer/addResultLayer 派发）→ 无缓存的可见层 getFieldCard 预热。失败静默（buildContext 时重试）。 */
document.addEventListener('layers:changed', () => {
  for (const l of getLayers()) {
    if (l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length && !_fieldCardCache.has(l.id)) {   // WS2 F2.4：去 visible·hidden 层也预热（对齐 buildContext）
      getFieldCard(l.id, l.fc, l.kind || 'point').catch(() => {});   // fire-and-forget·失败静默
    }
  }
});
// R2-full（registry 完整性兜底·CB-09）：layers:changed 时·未显式注册的层 → 自动注册 source='tool'。
// 显式入口（upload/preset/draw/toolbox-tool）在 dispatch 前已注册→此跳过；覆盖 heatmap-tool/grid-tool/map.js 等直调 addLayer 路径·registry 即完整。
document.addEventListener('layers:changed', () => {
  for (const l of getLayers()) {
    if (l.kind === 'group' || !l.fc || !l.fc.features || !l.fc.features.length) continue;
    if (!data_registry.getByLayerId(l.id)) data_registry.register({ name: l.name, kind: l.kind, source: 'tool', fc: l.fc, layerId: l.id });
  }
});

// geoFetch 已删（步 7·手册 §3.2：由 api.js geoPost 取代）；_LAYER_REF_KEYS 随迁——
// $n/命名引用预解析在各委托层内联（ref() 保留：run_python inputs 与委托层同用）。
const _stepResults = [];      // 本轮工具产物 fc（按产出序，单调），供 $n 显式引用
const _resultIdByStep = [];   // 结果层 id（与 _stepResults 平行，单调），供 ref('$n') 标消费
export function resetStepResults() { _stepResults.length = 0; _resultIdByStep.length = 0; _registry.length = 0; _figCache.clear(); }
const _curResultIds = [];     // 本轮"存活"的结果层 id（沉浸聚焦用：关其余、留本轮、缩放并集）
const _consumedIds = new Set(); // 被后续工具引用消费掉的中间结果层 id（$n 或命名引用），addResultLayer 移除它们、保未消费的最终结果
const _keepIds = new Set();   // 显式保留（keep:true）的结果层 id——用户要求保留/属展示结果的层，即使被引用消费也豁免清理（显式意图覆盖默认启发式）
const _registry = [];   // ① artifact registry：本轮所有产物 {id,name,tool,round,t}（带 provenance，供 formatRegistry 注入/对账审计）

// figId → dataUri 缓存（run_python 产图，panel.js _renderFigs 读此替换 {{fig:ID}}）。
// 图是单轮产物，resetStepResults 清；不入 _registry（非图层，getArtifacts 只认 fc.features 非空层）。
const _figCache = new Map();
/** 取图 dataUri（panel.js _renderFigs 调）。 */
export function getFig(id) { return _figCache.get(id); }
/** 清 fig 缓存（resetStepResults 调，防跨轮累积）。 */
export function clearFigCache() { _figCache.clear(); }
let _curTool = null, _curRound = 0;   // harness 每轮 setToolContext 注入当前工具/轮次（addResultLayer 读入 registry）
export function setToolContext({ tool, round } = {}) { _curTool = tool || null; _curRound = round || 0; }
export function resetCurrentResults() { _curResultIds.length = 0; _consumedIds.clear(); _keepIds.clear(); }
/** 图层引用解析：① `$n` → 第 n 个工具产物（显式变量，最稳）；② 图层名（精确/唯一包含）；③ 原样（preset_id）。
 *  $n **和命名**引用本轮 EMC 结果时都把该步结果标为"已消费"（中间产物）→ addResultLayer 收尾移除它；
 *  未被任何后续工具引用的并列结果（如 居住+商业）保留为最终结果。 */
function ref(v) {
  if (typeof v === 'string' && /^\$\d+$/.test(v.trim())) {
    const idx = Number(v.trim().slice(1)) - 1;
    const fc = _stepResults[idx];
    if (fc) {
      if (_resultIdByStep[idx]) _consumedIds.add(_resultIdByStep[idx]);   // $n 引用 → 标中间产物
      return fc;   // 多步链中间结果：排序/呈现类设计内用法，不拦（主手裁决 08-19）
    }
  }
  if (typeof v === 'string' && v) {
    _guardUsageRef(v);   // PT-CB2 T2：preset_id 直传 → 结论层拒绝（铁律7）
    const all = getLayers().filter((x) => x.fc && x.fc.features && x.fc.features.length);
    // 1. 精确匹配 layer id
    let l = all.find((x) => x.id === v);
    // 2. 精确匹配 name
    if (!l) l = all.find((x) => x.name === v);
    // 3. 唯一包含匹配 name
    if (!l) {
      const inc = all.filter((x) => x.name && x.name.includes(v));
      if (inc.length === 1) l = inc[0];
    }
    if (l) {
      // 复审修复 H1（Codex 审计）：已加载层的拒绝改判 l.presetUsage（加载时随层持久·range-presets 4 处写入），
      // 不依赖 _usageBlocked 缓存——getGeoCatalog 当前无调用方，catalog 路径守卫运行时不生效。
      if (l.presetUsage === 'analysis_output') {
        throw new Error(`「${l.name || l.presetId}」(${l.presetId}) 是分析结论层（usage=analysis_output），不能作空间操作输入（结论不当原料·铁律7）。请改用分析原料层（usage=input）或上传标准边界资料`);
      }
      if (l.presetId) _guardUsageRef(l.presetId);   // catalog 就绪时的增强前置（可选·未就绪静默）
      if (_resultIdByStep.includes(l.id)) _consumedIds.add(l.id);
      return l.fc;
    }
    // CB-05 ROOTCAUSE: 匹配失败返 null（非原值 v）→ 工具层提前拦截 + 列可用层·防无效引用传后端爆炸
    return null;
  }
  return v;
}


/** pre_filter 容错：字符串 'field/op/value'（或 | 分隔）或对象 → 后端 {field,op,value}。 */
function normPreFilter(pf) {
  if (!pf) return undefined;
  let o = pf;
  if (typeof pf === 'string') {
    const parts = pf.split(/[/|]/).map((s) => s.trim()).filter(Boolean);
    if (parts.length < 3) return undefined;
    o = { field: parts[0], op: parts[1], value: parts.slice(2).join('/') };
  }
  if (!o || !o.field || !o.op) return undefined;
  if (o.op === 'in' && typeof o.value === 'string') o.value = o.value.split(',').map((s) => s.trim()).filter(Boolean);
  return o;
}

const _ERR = (name, e) => ({ observation: '[ERR] ' + name + ' 失败：' + ((e && e.message) || e) });

// DENSITY_RAMP 已退场（Phase 2）：density 委托主 Toolbox generateHeatmapForAI/generateGridForAI/generateTerrainForAI，
// 套用 HEATMAP_RAMPS 固定色段，不再自造 KDE 色带。原 const 已删（端点 /api/v1/geo/density 后端保留 + 标 deprecated）。
const _fmtPi = (v) => (v !== '' && v != null && !isNaN(v) ? Number(v).toFixed(2) : '?');
// P2-2（CB-19c·Codex 建议）：boundaryLabel 从 dict 提取 features[0].properties.name（治 String(dict) → "[object Object]"·LLM 转述不可读·PRM-07 偶发 fail 方差源）
const _boundaryLabel = (b) => {
  if (b == null) return undefined;
  if (typeof b === 'string') return b;
  if (typeof b === 'object' && Array.isArray(b.features) && b.features.length) {
    const p = b.features[0].properties || {};
    return String(p.name || p.MC || p.NAME || '').trim() || undefined;
  }
  return String(b);
};
const _fmtRow = (row) => {
  const dom = DOMAIN_LABEL[row.domain_top] || row.domain_top || '?';
  const elm = ELEMENT_LABEL[row.element_top] || row.element_top || '?';
  // P3-4（CB-19）：place_name 优先——rank-on-grid（无 name）也能锚到 POI 落点（工具出口统一·LLM grounding）
  const loc = row.place_name || row.name || '未命名';
  return `  - ${loc}：极性 ${_fmtPi(row.polarity_index)}，${row.point_count || 0}点，${dom}×${elm}，问题=${row.issue_label || '—'}`;
};


function isAnalysis(l) {
  const ui = l && l.paint && l.paint._ui;
  return !!(l && l.kind === 'polygon' && ui && (ui.tool === 'grid' || ui.tool === 'terrain' || ui.tool === 'zonal'));
}
function activeAnalysis() {
  if (_lastGrid && _lastGrid.layerId) {
    const l = getLayers().find((x) => x.id === _lastGrid.layerId);
    if (l) return l;
  }
  const sel = getSelectedLayer();
  if (sel && isAnalysis(sel)) return sel;
  return getLayers().find((l) => isAnalysis(l) && l.fc && l.fc.features && l.fc.features.length) || null;
}

/** 指代解析（NL 预处理·几 ms·非 LLM·5.212）：检测问句指代词 → 标注当前聚焦对象/上轮结果。
 *  让 diagnose Flash 知"这边/刚才"指代·不靠猜（grounding 显式关联）。保守：对象不存在不标（不误导）。 */
export function resolveCoref(question, priorTurn) {
  const q = String(question || '');
  const bits = [];
  if (/(这边|这个区|这里|此地|该区|这个)/.test(q)) {   // 空间指代 → activeAnalysis / selectedLayer
    const an = activeAnalysis();
    const sel = !an && getSelectedLayer && getSelectedLayer();   // an 已优先 analysis sel·无 an 才看普通 sel
    const focus = (an && an.name && `分析层「${an.name}」`) || (sel && sel.name && `选中层「${sel.name}」`);
    if (focus) bits.push(`「这边/这个区」→ 当前${focus}`);
  }
  if (/(刚才|上次|上轮|那个|之前)/.test(q) && priorTurn) {   // 时序指代 → priorTurn（上轮已做）
    const done = priorTurn.done;
    if (done && done !== '（无工具调用）') bits.push(`「刚才」→ 上轮 ${String(done).slice(0, 60)}`);
  }
  return bits.length ? `【指代解析】${bits.join('；')}。据此关联用户指代·勿再追问已可推断的对象。` : '';
}
// _buildZonalFc 已迁 toolbox/shared.js（步 1·手册 §3.2），本文件经 import 别名 _buildZonalFc 使用。
// _zonalToLayer/_compareToLayer 已迁 toolbox/zonal-tool.js（步 7·合成逻辑入模块 _execute）。
// _resolveBoundaryGeo wrapper 已删（步 7）：rank/area_stats 合成随迁模块；中文名预解析由委托层 resolveBoundaryInput 内联（§3.3①）。

// _rankToLayer/_areaStatsToLayer/_nearestToLayer 已迁 toolbox/{rank,area-stats,nearest}-tool.js（步 7·手册 §3.2）。

function fitToFeature(f) {
  const g = f && f.geometry;
  if (!g) return;
  const rings = g.type === 'Polygon' ? g.coordinates[0]
    : (g.type === 'MultiPolygon' ? g.coordinates.flatMap((p) => p[0]) : null);
  if (!rings || !rings.length) return;
  let mnX = Infinity, mxX = -Infinity, mnY = Infinity, mxY = -Infinity;
  for (const [x, y] of rings) { if (x < mnX) mnX = x; if (x > mxX) mxX = x; if (y < mnY) mnY = y; if (y > mxY) mxY = y; }
  if (isFinite(mnX)) fitBoundsTo([mnX, mnY, mxX, mxY]);
}

/** AI 工具产出的图层统一归入「EmotionMap Copilot」组（复用 state.addGroup；组卡片由 sidebar 现有逻辑渲染）。
 *  必传空 fc：组会被 focusLayer() 当作 Overview 焦点（tier1 读 group.fc.features），无 fc 则崩溃。 */
function _aiGroup() {
  const existing = getLayers().find((l) => l.kind === 'group' && l.name === 'EmotionMap Copilot');
  return existing || addGroup({ name: 'EmotionMap Copilot', fc: { type: 'FeatureCollection', features: [] } });
}

/** 多 bbox 并集 → [minX,minY,maxX,maxY]（供多结果同屏缩放）。 */
function _unionBBox(ids) {
  let u = null;
  for (const id of ids) {
    const l = getLayer(id);
    const b = l && l.fc ? fcBBox(l.fc) : null;
    if (!b) continue;
    if (!u) u = [b[0], b[1], b[2], b[3]];
    else { u[0] = Math.min(u[0], b[0]); u[1] = Math.min(u[1], b[1]); u[2] = Math.max(u[2], b[2]); u[3] = Math.max(u[3], b[3]); }
  }
  return u;
}
/** 沉浸聚焦：隐藏除本轮结果外的全部图层（含 Range/点/旧结果）。
 *   AI 结果是 R-group（enforceMutualExclusion 不动它），故不走互斥，直关。
 *   不 selectLayer/dispatch layer:selected：AI 结果是 polygon 无归因数据，强制 Overview 追随会触发
 *   refreshOverview→tier1 在 group(曾无 fc)上崩溃（bug1）。用户只要缩放+关其余。 */
function focusOnlyResults() {
  const keep = new Set(_curResultIds);
  for (const l of getLayers()) {
    if (l.kind === 'group') continue;                  // 组容器无可见性
    const want = keep.has(l.id);
    if (want && !l.visible) { setLayerVisible(l.id, true); renderLayer(l); }
    else if (!want && l.visible && _isAILayer(l)) { setLayerVisible(l.id, false); renderLayer(l); }
  }
}

// _toolContentSig / _defaultPaint / _renderNote / _SCALE_TABLE / _scaleRadius / _clampM
// 已迁 toolbox/shared.js（步 1·手册 §3.2），本文件经 import 别名使用；main.js 同语义 _contentSig 本次不动（手册 §3.2 注）。

/** 把 geo 工具产出的 GeoJSON 落地图为新图层（统一回写，复用 range-presets/grid-tool 范式）。
 * 替换语义：同名旧结果层先移除再新建（防重复堆叠）。name=图层名，kind=point|polygon。
 * keep=true → 显式保留（用户要求/展示结果），即使被后续工具引用消费也豁免清理。
 * 点层自动按 polarity 上色（addLayer 默认 colorMode）；面层需传 paint.fillOn 才可见。
 * 沉浸聚焦：每生成一个结果 → 关其余、留本轮所有结果、缩放至并集（maxZoom 16 防过度放大）。 */
export function addResultLayer({ name, kind = 'polygon', fc, paint, keep, fields }) {
  if (!fc || !fc.features || !fc.features.length) return null;
  // 消费式收尾：移除被引用消费的中间结果层，但 _keepIds（显式保留）豁免——显式意图覆盖默认清理。
  // 未消费的并列最终结果（如 居住+商业）保留；$n/命名引用走 _stepResults 的 fc，不依赖图层存活。
  // （原顺序为先签名去重后收尾：二者作用不同层集、移除幂等，最终态一致；去重 + srcId 挂层现由 addToolboxLayer 内部完成）
  for (let i = _curResultIds.length - 1; i >= 0; i--) {
    if (_consumedIds.has(_curResultIds[i]) && !_keepIds.has(_curResultIds[i])) { removeLayerFromMap(_curResultIds[i]); removeLayer(_curResultIds[i]); _curResultIds.splice(i, 1); }
  }
  // 工作机制：注入 _ui.tool（from setToolContext 的 _curTool）——让 EMC 产物带工具身份，Toolbox 编辑面板（按 _ui.tool 回填参数）对 EMC buffer/overlay/clip 等生效
  let _paint = paint;
  if (_curTool) {
    if (!_paint) _paint = { _ui: { tool: _curTool } };
    else if (!_paint._ui) _paint = { ..._paint, _ui: { tool: _curTool } };
    else if (!_paint._ui.tool) _paint._ui.tool = _curTool;
  }
  // 通用落图（手册 §3.3②：去重/用地标准色/addLayer/renderLayer/落图自检/列表刷新）；fit=false——缩放由下方并集统一做（保持原行为）
  const L = addToolboxLayer({ name, kind, fc, paint: _paint, parentId: _aiGroup().id, fit: false });
  if (!L) return null;
  _registry.push({ id: L.id, name, tool: _curTool, round: _curRound, t: Date.now(), fields });   // ① registry（provenance 由 harness setToolContext 注入；fields 可选字段简表，P3 formatRegistry 用）
  if (keep) _keepIds.add(L.id);              // 显式保留登记（覆盖消费式清理）
  _curResultIds.push(L.id);                 // 登记本轮存活结果（沉浸聚焦）
  _stepResults.push(fc);   // 登记 $n 引用（ref 解析）
  _resultIdByStep.push(L.id);   // 与 _stepResults 平行：ref('$n') 据此标消费
  focusOnlyResults();
  const bb = _unionBBox(_curResultIds); if (bb) fitBoundsTo(bb, 100, 16);
  document.dispatchEvent(new CustomEvent('layers:changed'));
  return L;
}

/** ② getArtifacts：当前存活的 EMC 产物（registry 里 id 仍在 getLayers 的），带 provenance。 */
export function getArtifacts() {
  const live = new Set(getLayers().filter((l) => l.fc && l.fc.features && l.fc.features.length).map((l) => l.id));
  return _registry.filter((a) => live.has(a.id));
}
/** 字段简表（formatRegistry 用）：同步 resolveRole 标 role（**不调 LLM**），返 `[字段: f1:role1, …]`。
 *  承重（5.74 对账）：方括号包裹——_extractClaimedLayers verbRe 字符类排除 [ ]，故字段段不会被误抽成层名；
 *  字段段禁入图层名与 {{show:}}（showRe 不排除方括号会误吞）。 */
function _fieldBrief(fc, maxFields = 5) {
  const feats = fc && fc.features;
  if (!feats || !feats.length) return '';
  const sample = feats.slice(0, 5);
  const seen = [];
  for (const f of sample) {
    for (const k of Object.keys(f.properties || {})) {
      if (isInternalField(k) || isRenderContract(resolveRole(k))) continue;   // 过滤内部/渲染契约
      if (!seen.includes(k)) seen.push(k);
      if (seen.length >= maxFields) break;
    }
    if (seen.length >= maxFields) break;
  }
  if (!seen.length) return '';
  const parts = seen.map((k) => `${k}:${resolveRole(k) || '?'}`);
  return `[字段: ${parts.join(', ')}${seen.length >= maxFields ? '…' : ''}]`;
}
/** 5.217/5.218 优化专用极简 grounding（只层名+kind·~200 token·大幅减 token 提速）。
 *  区别 buildContext（完整·diagnose 用）：优化只需层标识·极简。 */
export function buildOptimizeContext() {
  const loaded = getLayers()
    .filter((l) => l.visible && l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length)
    .map((l) => `${l.name}(${_kindTag(l)})`).join(' | ');
  return loaded ? `可见图层：${loaded}` : '（无可见图层）';
}

/** formatRegistry：产出图层清单（注入 finalStep/review/revise prompt，让模型 ground 在真值，禁编不在列表的层）。
 *  P3：每条后追加 `[字段: f:role, …]` 段——优先读 registry 存的 fields；缺则反查 getLayer(id).fc 同步标 role。 */
export function formatRegistry() {
  const a = getArtifacts();
  if (!a.length) return '（暂无 EMC 产出图层）';
  return a.map((x) => {
    let s = `${x.name}${x.tool ? `（${x.tool}${x.round ? '·第' + x.round + '轮' : ''}）` : ''}`;
    let brief = x.fields;
    if (!brief) {
      const l = getLayer(x.id);
      if (l && l.fc) brief = _fieldBrief(l.fc);
    }
    if (brief) s += brief;
    return s;
  }).join('、');
}

/** 轮末兜底清理：移除本轮被标记消费、却因后续工具失败（addResultLayer 未再触发）而残留的中间结果层。
 *  _keepIds（显式保留）豁免。EMC 组最终留：未被消费的最终结果 + 显式保留层。 */
export function cleanupConsumedResults() {
  let removed = false;
  for (let i = _curResultIds.length - 1; i >= 0; i--) {
    if (_consumedIds.has(_curResultIds[i]) && !_keepIds.has(_curResultIds[i])) {
      removeLayerFromMap(_curResultIds[i]); removeLayer(_curResultIds[i]); _curResultIds.splice(i, 1); removed = true;
    }
  }
  if (removed) { renderLayerList(); refreshLegend(); reorderAllZ(); document.dispatchEvent(new CustomEvent('layers:changed')); }
}
function pi(f) { return Number((f.properties || {}).polarity_index); }

function sortZones(feats, crit) {
  if (crit === 'worst') return feats.slice().sort((a, b) => pi(a) - pi(b));
  if (crit === 'best') return feats.slice().sort((a, b) => pi(b) - pi(a));
  if (crit.startsWith('domain:')) {
    const d = crit.split(':')[1];
    return feats.slice().sort((a, b) => {
      const pa = String((a.properties || {}).domain_top || '').includes(d) ? 1 : 0;
      const pb = String((b.properties || {}).domain_top || '').includes(d) ? 1 : 0;
      return (pb - pa) || (Math.abs(pi(b)) - Math.abs(pi(a)));
    });
  }
  if (crit.startsWith('element:')) {
    const e = crit.split(':')[1];
    return feats.slice().sort((a, b) => {
      const pa = String((a.properties || {}).element_top || '').includes(e) ? 1 : 0;
      const pb = String((b.properties || {}).element_top || '').includes(e) ? 1 : 0;
      return (pb - pa) || (Math.abs(pi(b)) - Math.abs(pi(a)));
    });
  }
  return feats.slice().sort((a, b) => Math.abs(pi(b)) - Math.abs(pi(a)));
}

/** 格式化 geo catalog → grounding 段（边界 preset / 时点 / GIS 工具清单）。 */
function formatGeoCatalog(cat) {
  if (!cat) return '';
  const out = [];
  const pls = (cat.point_layers || []).filter((p) => p.available !== false);
  if (pls.length) out.push('【可用地层】' + pls.map((p) => {
    const samp = p.samples || {};
    const cards = p.field_cards || {};   // P3：后端 _point_layer_overview 规则标注的 role
    const samples = Object.keys(samp).map((k) => {
      const role = cards[k] && cards[k].role;
      return role ? `${k}[${role}]:${samp[k]}` : `${k}:${samp[k]}`;
    }).join(' / ');
    return `${p.label || p.id}${samples ? `（${samples}）` : ''}`;
  }).join('；'));
  const bds = (cat.boundaries || []).filter((b) => b.available !== false);
  if (bds.length) out.push('【可用边界】' + bds.map((b) => `${b.label || b.id}(按字段 ${b.name_field || 'name'} 抽取/筛选某区某单元)`).join('、'));
  const tls = (cat.tools || []).map((t) => t.name).filter(Boolean);
  if (tls.length) out.push('【可用 GIS 工具】' + tls.join('/') + '（结果自动落地图为新图层）');
  return out.join('\n');
}

/** DataEye（P3 升级）：层的字段 + 类型 + role + 2 样本值。格式 `field=dtype:role:sample`。
 *  role 经 getFieldCard（规则→LLM 推断）标注；过滤渲染契约（_level/_ui 等），保留自产契约
 *  （polarity_index/point_count 等，AI 写 where 要用）+ 未登记内部字段（isInternalField 兜底）。
 *  给模型真实值参照 → 写 where（field/op/value）命中率显著升，不再盲猜字段值。 */
function _dtypeTag(dtype) {
  if (dtype === 'number') return 'num';
  if (dtype === 'datetime') return 'dt';
  if (dtype === 'boolean') return 'bool';
  return 'cat';   // string → categorical
}
async function _fieldSamples(fc, maxFields = 12, layerId = null) {
  const feats = fc && fc.features;
  if (!feats || !feats.length) return '';
  const cards = await getFieldCard(layerId, fc);
  // 2c 修复：语义关键字段（role 命中 element/polarity/domain/...）强制纳入 + 给全 unique 值分布，
  // 让 LLM 看到真实值域——治「误判 element 无 environment / 极性全中性」式误 GAP。
  // 根因：旧 maxFields=6 把后置的 element/polarity 截断了，LLM 压根没看到这些字段。
  const VALUE_ROLES = new Set(['element', 'polarity', 'domain', 'score', 'emotion_type', 'emotion_intensity', 'land_use_class', 'hotspot']);
  const uniq = (field) => {
    const s = new Set();
    for (const f of feats) { const v = f.properties && f.properties[field]; if (v != null && v !== '') s.add(String(v)); }
    return [...s];
  };
  const keys = [];
  for (const k of Object.keys(cards)) {
    if (isInternalField(k) || isRenderContract(cards[k].role)) continue;   // 过滤内部/渲染契约
    if (keys.includes(k)) continue;
    const role = cards[k].role;
    if ((role && VALUE_ROLES.has(role)) || keys.length < maxFields) keys.push(k);   // 关键字段强制纳入（不受 maxFields 限）
  }
  return keys.map((k) => {
    const c = cards[k];
    const role = c.role || '?';
    if (role && VALUE_ROLES.has(role)) {
      const uv = uniq(k);
      if (uv.length) return `${k}=${_dtypeTag(c.dtype)}:${role}:${uv.slice(0, 8).join('|').slice(0, 80)}`;   // 全 unique 值分布
    }
    const vals = (c.samples || []).slice(0, 2);
    if (!vals.length) return `${k}=${_dtypeTag(c.dtype)}:${role}`;
    return `${k}=${_dtypeTag(c.dtype)}:${role}:${vals.join('|').slice(0, 24)}`;
  }).join('/');
}

/** 面层 boundary 优先级（层名启发式）：行政/片区/范围类 = boundary 首选；用地类显式标可作 boundary；
 *  分析网格（grid/terrain）单列——防 merge/clip/overlay/area_stats 多面层候选时 Flash 选错对象（如把「合并行政区」错配到「用地_商业」）。 */
const _BOUNDARY_NAME_RE = /(行政区|行政区划|片区|范围|边界|核心|主城|中心城区|建成区|社区|街道|乡镇)/;
const _LANDUSE_NAME_RE = /(用地|landuse)/;
function _polyRole(l) {
  const ui = l.paint && l.paint._ui;
  if (ui && (ui.tool === 'grid' || ui.tool === 'terrain')) return '分析网格';
  const n = l.name || '';
  if (_BOUNDARY_NAME_RE.test(n)) return 'boundary首选';
  if (_LANDUSE_NAME_RE.test(n)) return '用地·可作boundary';
  return '可作boundary';
}
/** 层类型中文标签（grounding 用）：点/线/热力直接标；面层按 _polyRole 标 boundary 优先级。 */
const _kindTag = (l) => {
  const k = l.kind;
  if (k === 'point') return '点层';
  if (k === 'line') return '线层';
  if (k === 'heatmap') return '热力层';
  if (k === 'polygon') return '面层·' + _polyRole(l);
  return k || '层';
};

/** D4：boundary 层子要素枚举（治可见性缺口·D2 可派生规则的燃料）。
 *  对 boundary首选 面层，找 name 字段（categorical·≤20 unique·值含地名后缀 或 字段名似 name/MC/名称）→ 返全 distinct 值串。
 *  让 diagnose 看见「行政区·含:西陵区/伍家岗区/…」→ 配合 D2 判 strategy=ready，治假 GAP（04-llm INT-002~007 根因）。 */
const _PLACE_NAME_RE = /(区|街道|社区|镇|乡|片|园|路|广场|中心|村|工业园|管委会)$/;
/** 找 boundary首选 层的 name 字段 + 全 distinct 值（D4 枚举 + D1 派生判定共用·单一 name 定位逻辑）。 */
function _boundaryNames(l) {
  if (_polyRole(l) !== 'boundary首选') return null;
  const feats = l.fc && l.fc.features;
  if (!feats || !feats.length) return null;
  let best = null;
  for (const k of Object.keys(feats[0].properties || {})) {
    if (isInternalField(k) || isRenderContract(resolveRole(k))) continue;
    const vals = new Set();
    for (const f of feats) {
      const v = f.properties && f.properties[k];
      if (v == null || v === '') continue;
      vals.add(String(v));
      if (vals.size > 20) break;   // 高基数·非 name 字段
    }
    const n = vals.size;
    if (n > 0 && n <= 20) {
      const arr = [...vals];
      const placeLike = arr.filter((v) => _PLACE_NAME_RE.test(v)).length;
      const fieldLikeName = /name|MC|名|名称/i.test(k);
      if (fieldLikeName || (placeLike >= Math.min(3, n) && placeLike >= n / 2)) {
        if (!best || arr.length > best.values.length) best = { field: k, values: arr };   // 多候选取值最多者
      }
    }
  }
  return best;
}
/** D4：boundary 层子要素枚举串（注入 grounding·D2 可派生规则的燃料）。 */
function _boundaryEnum(l) {
  const b = _boundaryNames(l);
  return b && b.values.length ? `·含:${b.values.join('/')}` : '';
}
/** D1：派生数据判定器（代码确定性·治假 GAP 兜底·Smart/Dumb 铁律：代码可知不问 LLM）。
 *  扫已加载 boundary首选 层 name distinct 值，与问句字符串匹配 → 命中即返 {name, layer, field}。
 *  harness post-diagnose 调用：问句提"西陵区"+行政区已加载 → 强制 data_plan.strategy=ready（覆盖 request_upload）。 */
export function deriveAvailable(question, layers) {
  const q = String(question || '');
  if (!q) return null;
  // CB-12 P0-a + P1'（glm组/Codex）：模糊匹配——剥「区/市/县/街道」后缀后双向包含（问句"西陵"↔值"西陵区"）
  //   P1'：原始值精确优先（防"西陵路"误匹配"西陵区"·glm组 发现 2）·stripped 兜底
  const _strip = (s) => String(s || '').replace(/[区市县街道镇]$/g, '').trim();
  for (const l of layers || []) {
    const b = _boundaryNames(l);
    if (!b || !b.values || !b.values.length) continue;
    // P1'（PRM-08）：双字段——_boundaryNames 只找 1 个字段（可能 MC 代码）·补扫 name/NAME 字段（中文名）
    const _nameVals = [];
    for (const f of (l.fc && l.fc.features || []).slice(0, 200)) {   // CB-12（glm）：30→200·防大图层要素 >30 时双字段扫描漏区（PRM-08 "伍家岗" 执行侧）
      const p = f.properties || {};
      for (const k of ['name', 'NAME', '名称']) {
        if (p[k] != null) _nameVals.push(String(p[k]));
      }
    }
    const _allVals = [...new Set([...(b.values || []), ..._nameVals])];
    // CB-12 统一词边界（Codex 方案·修 2 bug）：两循环都过词边界·分隔语义修正——
    //   匹配 = 值后首字符 ∈ 分隔类（区/内/范围/的/标点/空白/结尾）·跳过 = ∈ 块词（路/山/公园/大道…）
    const _sepRe = /^[\s，。；、的区内范围边界]$/;   // 分隔类（合法区域边界·含"范围"字面·"西陵范围内"应匹配）
    const _blockRe = /^(路|山|街|公园|广场|大道|车站|码头|桥)/;   // 块词（误匹配·跳过）
    const _validAfter = (val, qq) => {
      const _idx = qq.indexOf(val);
      if (_idx < 0) return false;
      const _after = qq.slice(_idx + val.length, _idx + val.length + 2);
      const _first = _after.slice(0, 1);
      return _sepRe.test(_first) || !_blockRe.test(_after);   // 分隔符 → 匹配；块词 → 跳过；其他（如"范围内"首字"范"非块词）→ 匹配
    };
    // CB-14（用户准则）：固化库行政区划只识别真实行政区划——层来源 preset + 层名含"行政区" → 值必须在 FIXED_ADMIN_DISTRICTS
    //   白名单；法定功能区（小溪塔/龙泉等）不在白名单 → 跳过（不识别→诚实 request_upload·EMC 不硬猜不可信范围）。
    //   用户上传层（upload）不受白名单限制（用户主动提供的范围皆可信）。
    const _reg = data_registry.getByLayerId(l.id);
    const _isFixedAdmin = _reg && _reg.source === 'preset' && /行政区/.test(l.name || '');
    const _inAdminWhitelist = (nm) => { if (!_isFixedAdmin) return true; return FIXED_ADMIN_DISTRICTS.some((d) => nm === d || nm.includes(d) || d.includes(nm)); };
    for (const nm of _allVals) {
      if (!nm) continue;
      if (!_inAdminWhitelist(nm)) continue;   // 固化库行政区划白名单过滤（法定功能区跳过）
      if (q.includes(nm) && _validAfter(nm, q)) return { name: nm, layer: l.name, field: b.field };   // 原始值精确优先（过词边界）
    }
    for (const nm of _allVals) {
      if (!nm) continue;
      if (!_inAdminWhitelist(nm)) continue;   // 固化库行政区划白名单过滤（法定功能区跳过）
      const _qStrip = _strip(q), _nmStrip = _strip(nm);
      // CB-12 回退（glm组）：阈值 3→2（"西陵/伍家"2 字区名 stripped 匹配恢复·a04a714 改 3 致 2 字区名失效→while-loop 退化）
      //   词边界用原始 q（非 _qStrip·防 _strip 剥"大道"的"道"致"大"单字漏拦块词）
      if (_nmStrip && _nmStrip.length >= 2 && (_qStrip.includes(_nmStrip) || _nmStrip.includes(_qStrip)) && _validAfter(_nmStrip, q)) {
        return { name: nm, layer: l.name, field: b.field };   // stripped 兜底（≥2 字·词边界防误匹配）
      }
    }
  }
  return null;
}

/** buildContext：grounding 摘要（panel send + query_layers 共用）。 */
export async function buildContext() {
  const _SOURCE_TAG = { upload: '上传', preset: '预设', tool: '工具产物', draw: '绘制' };   // R3：registry 来源 → 中文 tag（治 C2「上传了哪些数据」答错）
  const layers = getLayers();
  const an = activeAnalysis();
  const parts = [];
  // CPD Phase 2b：curState 语境 hint（仅丰富 LLM 语境，不参与路由裁定/不动 diagnose）。
  const _cs = getCurState();
  const _csl = CPD_STEPS.find((s) => s.id === _cs);
  parts.push(`引导阶段：${_cs}${_csl ? '·' + _csl.label : ''}（用户所处进度，仅供参考，不改变工具选型）`);
  const loaded = (await Promise.all(layers
    .filter((l) => l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length)   // CB-0528：去 visible·已加载即列（含 hidden·眼睛关仍可用）
    .map(async (l) => {
      const cnt = l.fc.features.length;
      const fs = await _fieldSamples(l.fc, 12, l.id);   // DataEye（P3）：字段+类型+role+样本值（关键字段全值·治误判缺数据 2c）
      const _re = data_registry.getByLayerId(l.id);   // R3：查 registry 来源
      const _src = _re ? (_SOURCE_TAG[_re.source] || '') : '';
      return `${l.name}(id:${l.id},${cnt}条,${_kindTag(l)}${_src ? ',' + _src : ''}${_boundaryEnum(l)}${fs ? ',字段:' + fs : ''}${l.visible ? '' : ',隐藏'})`;
    }))).join('、');
  parts.push('已加载图层（标 来源：上传/预设/工具产物/绘制·眼睛开关不影响 EMC 可用·隐藏层仍可分析）：' + (loaded || '（无）'));
  // 数据内容摘要（5.223·系统全字段值域识别·Flash 知有什么/值域/缺什么·Layer Manifest 完整版）
  const _ptLayers = layers.filter((l) => l.kind === 'point' && l.fc && l.fc.features && l.fc.features.length);   // CB-0528：去 visible·含 hidden（眼睛关仍摘要给 Flash）
  const _summ = [];
  for (const pl of _ptLayers.slice(0, 3)) {
    const cards = await getFieldCard(pl.id, pl.fc);
    const feats = pl.fc.features;
    const lines = [];
    for (const [field, card] of Object.entries(cards)) {
      if (isInternalField(field) || isRenderContract(card.role)) continue;
      const role = card.role || '?';
      const vals = feats.map((f) => (f.properties || {})[field]).filter((v) => v != null && v !== '');
      if (!vals.length) continue;
      if (card.dtype === 'number') {
        const nums = vals.map(Number).filter((n) => !isNaN(n));
        if (nums.length) { const mn = Math.min(...nums), mx = Math.max(...nums), mean = (nums.reduce((a, b) => a + b, 0) / nums.length).toFixed(2);
          lines.push(`${field}(${role})数值${mn}~${mx}均${mean}`); }
      } else if (card.dtype === 'datetime' || /time|date|timestamp|时|日/i.test(field)) {
        const uniq = [...new Set(vals)].sort();
        lines.push(`${field}(${role})时间${uniq[0]}~${uniq[uniq.length - 1]}(${uniq.length}值)`);
      } else {
        const _c = {}; for (const v of vals) { const k = String(v); _c[k] = (_c[k] || 0) + 1; }
        const top = Object.entries(_c).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k, v]) => `${k}(${v})`).join('/');
        if (top) lines.push(`${field}(${role})${top}`);
      }
    }
    if (lines.length) _summ.push(`${pl.name}(${feats.length}点): ${lines.slice(0, 8).join(' | ')}`);
  }
  if (_summ.length) parts.push('数据内容摘要（字段值域·知有什么）:\n' + _summ.join('\n'));
  parts.push('EMC 分析能力（可生成·勿判缺数据需上传）：密度热力图（2D 彩虹/3D·可按极性筛：综合/积极/消极/中性）/ 网格聚合（任意尺度）/ 情绪地形 / 区域聚合统计 / 排序 / 缓冲 / 叠置 / 裁取 / 抽取 / 筛选 / 合并 / 邻近 / 聚集热点 / 面积统计 / 区域对比。L2 已含 polarity（积极/中性/消极）·要"消极/积极热力图"直接生成（density.params.polarity=overall|positive|negative|neutral·综合=彩虹·极性=对应色板）·勿判"缺极性点"。');
  // 数据纪律（CB-0528 修）：已加载层（含 hidden）均可用——防"用未加载层"，但眼睛关≠未加载（hidden 层 fc 仍有效·EMC 可用）
  const wisdom = await getWisdom();
  if (wisdom) parts.push(wisdom);
  if (!an) {
    parts.push('（暂无聚合层——zonal/rank 类区域统计建议先 ensure_zone 生成；merge/clip/overlay/area_stats 可直接用上方已加载的面层作 boundary）');
    return parts.join('\n');
  }
  const feats = an.fc.features;
  parts.push(`当前分析层：${an.name}（${feats.length} 个聚合单元）`);
  const agg = { 'Very Positive': 0, Positive: 0, Neutral: 0, Negative: 0, 'Very Negative': 0 };
  for (const f of feats) {
    const p = f.properties || {};
    agg['Very Positive'] += p.n_very_positive || 0;
    agg.Positive += p.n_positive || 0;
    agg.Neutral += p.n_neutral || 0;
    agg.Negative += p.n_negative || 0;
    agg['Very Negative'] += p.n_very_negative || 0;
  }
  parts.push(`极性计数：非常积极${agg['Very Positive']} / 积极${agg.Positive} / 中性${agg.Neutral} / 消极${agg.Negative} / 非常消极${agg['Very Negative']}`);
  const top = feats
    .map((f) => f.properties || {})
    .filter((p) => p.polarity_index != null && !isNaN(p.polarity_index))
    .sort((a, b) => Math.abs(b.polarity_index) - Math.abs(a.polarity_index))
    .slice(0, 8);
  if (top.length) {
    parts.push('高张力区域：\n' + top.map((p) => {
      const name = p.name || p.issue_label || '未命名';
      const dom = DOMAIN_LABEL[p.domain_top] || p.domain_top || '?';
      const elm = ELEMENT_LABEL[p.element_top] || p.element_top || '?';
      return `  - ${name}：极性 ${Number(p.polarity_index).toFixed(2)}，${dom}×${elm}，问题=${p.issue_label || '—'}，${p.point_count || 0}点`;
    }).join('\n'));
  }
  return parts.join('\n');
}

/** 数据可见纪律（工作机制重构）：EMC 只用 Layers 中【当前显示】的情绪点层，registry 未显示层一律禁用
 *  （防默认 'yichang_l2_t1' 致"只传 L1·T1 却跑 L2"的用错数据）。与 heatmap/grid collectSources 同源，但强制 visible 过滤。 */
export function pickVisiblePointLayer() {
  // CB-0528：已加载点层不论 visible（眼睛关仍可用·数据在）；优先 visible，无 visible fallback 全部已加载
  // （治"上传后眼睛关·EMC 判缺数据"老 bug·眼睛是显示控制非数据可用性）
  const _all = getLayers().filter((l) => l.fc && l.fc.features && l.fc.features.length);
  const vis = _all.filter((l) => l.visible);
  const pool = vis.length ? vis : _all;
  for (const l of pool) {   // L2 group（多极性子层合并）优先
    if (l.kind === 'group' && l.children && l.children.length) {
      const merged = [];
      for (const cid of l.children) { const c = getLayer(cid); if (c && c.fc && c.fc.features.length) merged.push(...c.fc.features); }
      if (merged.length) return { fc: { type: 'FeatureCollection', features: merged }, name: l.name, level: 'L2', sourceKey: `group:${l.id}` };
    }
  }
  const pts = pool.filter((l) => l.kind === 'point');
  const l2 = pts.find((l) => l.colorMode && String(l.colorMode).startsWith('l2-'));
  if (l2) return { fc: l2.fc, name: l2.name, level: 'L2', sourceKey: `layer:${l2.id}` };
  const l1 = pts.find((l) => l.colorMode === 'confidence');
  if (l1) return { fc: l1.fc, name: l1.name, level: 'L1', sourceKey: `layer:${l1.id}` };
  // WS2 F2.0：兜底——任意已加载点层（colorMode='polarity' 上传点层 / needsAnalysis 等）。
  // 飞轮点数据走 L2-group 分支测不出，但用户独立上传 polarity 点层正中此（致 density/zonal 等判"缺数据"）。
  const anyPt = pts[0];
  if (anyPt) return { fc: anyPt.fc, name: anyPt.name, level: anyPt.colorMode === 'confidence' ? 'L1' : 'L2', sourceKey: `layer:${anyPt.id}` };
  return null;
}
/** 工具入参 layer 解析：显式 params.layer 优先（geoFetch ref() 解析图层名/$n/preset_id/GeoJSON），否则用可见层 fc。 */
function resolvePointLayer(params) {
  if (params.layer) return params.layer;
  const vl = pickVisiblePointLayer();
  return vl ? vl.fc : null;
}
/** CB-10 P0-1/B007：图层类型一致性 guard——clip 需点层、overlay/extract 需面层。
 *  传错类型（面层走 clip / 点层走 overlay）→ observation 报「图层类型不匹配」·防止后端空结果/静默错配放大。 */
function _checkGeomType(value, want, toolName) {
  if (!value) return null;
  let l = null;
  if (typeof value === 'string') {
    l = getLayers().find((x) => x.id === value) || getLayers().find((x) => x.name === value);
  }
  const geom = l ? l.kind : null;   // 已加载图层有 kind
  if (l && geom && geom !== want) {
    return `[ERR] ${toolName} 图层类型不匹配：目标「${l.name}」是${geom === 'point' ? '点层' : '面层'}·但 ${toolName} 需${want === 'point' ? '点层' : '面层'}（${want === 'point' ? '裁剪点数据' : '面层叠置/提取'}）。`;
  }
  return null;
}
function _ERR_NO_VISIBLE_PT() {
  return { observation: '[ERR] 无已加载的情绪点层——请先在 Layers 上传/加载情绪点数据（眼睛开关不影响 EMC 可用·hidden 层仍可分析）' };
}
/** 补注册 Toolbox 委托产物（generateHeatmapForAI/generateGridForAI/generateTerrainForAI 经 addLayer 入 getLayers，
 *  但绕过 addResultLayer）——补 _registry(provenance)/_stepResults($n 引用)/_curResultIds，让多步链可 $n 引用 + formatRegistry 显 provenance + 5.74 对账完整。 */
function _registerToolboxLayer(layerId, fc, name) {
  if (!layerId) return;
  // B srcId：density 委托产物层补 srcId（generateHeatmapForAI 创建时未设，与 addResultLayer 对齐）
  const _tl = getLayers().find((x) => x.id === layerId);
  if (_tl && !_tl.srcId) _tl.srcId = _toolContentSig(fc);
  _registry.push({ id: layerId, name, tool: _curTool, round: _curRound, t: Date.now() });
  _curResultIds.push(layerId);
  _stepResults.push(fc);
  _resultIdByStep.push(layerId);
}
/** 委托产物 EMC 簿记（手册 v2.2 §2 C4/§6 步 7·density :1305-1311 范式提取）：
 *  _registerToolboxLayer（registry/$n/_curResultIds/srcId）+ keep 登记 + consumed 清理（addResultLayer
 *  同则·_keepIds 豁免）+ AI 组 parentId + focusOnlyResults（沉浸聚焦·v2.2 建议 1）+ 并集缩放 +
 *  layers:changed 补发（parentId 晚于模块内 dispatch）。返层对象（observation 侧 _renderNote 消费）。 */
function _adoptToolboxResult(layerId, fc, name, { keep = false } = {}) {
  if (!layerId) return null;
  _registerToolboxLayer(layerId, fc, name);
  if (keep) _keepIds.add(layerId);
  for (let i = _curResultIds.length - 1; i >= 0; i--) {
    if (_consumedIds.has(_curResultIds[i]) && !_keepIds.has(_curResultIds[i])) { removeLayerFromMap(_curResultIds[i]); removeLayer(_curResultIds[i]); _curResultIds.splice(i, 1); }
  }
  const L = getLayers().find((x) => x.id === layerId);
  if (L && !L.parentId) {
    L.parentId = _aiGroup().id;
    // 补 group.children（getChildren 用此字段·addLayer 无 parentId 时未 push·5.221 治 Layers 组卡数=0）
    const _g = getLayers().find((x) => x.id === L.parentId);
    if (_g && _g.kind === 'group' && !_g.children.includes(L.id)) _g.children.push(L.id);
  }
  focusOnlyResults();
  const bb = _unionBBox(_curResultIds); if (bb) fitBoundsTo(bb, 100, 16);
  document.dispatchEvent(new CustomEvent('layers:changed'));
  return L || null;
}

export const TOOLS = {
  /** 查当前已加载的图层/数据（数据可见纪律：只列 visible 层，与 pickVisiblePointLayer/buildContext 同源——
   *  防 round0 observation 列不可见层致 LLM 误调，被 resolvePointLayer 拒浪费一轮）。 */
  query_layers() {
    const an = activeAnalysis();
    const _ST = { upload: '上传', preset: '预设', tool: '工具产物', draw: '绘制' };
    const loaded = getLayers()
      .filter((l) => l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length)   // WS2 F2.4：去 visible·hidden 层也可用
      .map((l) => { const _re = data_registry.getByLayerId(l.id); const _s = _re ? (_ST[_re.source] || '') : ''; return `${l.name}(${l.fc.features.length}条,${_kindTag(l)}${_s ? ',' + _s : ''}${l.visible ? '' : ',隐藏'})`; }).join('、');
    return { observation: `已加载图层（标来源）：${loaded || '（无）'}（眼睛开关不影响 EMC 可用·hidden 层仍可分析）\n当前分析层：${an ? an.name + '（' + an.fc.features.length + ' 单元）' : '暂无聚合层（zonal/rank 用 ensure_zone；面层可作 boundary）'}` };
  },

  /** 按维度排序找区域（地图同步飞到）。 */
  query_zone_stats(params = {}) {
    const an = activeAnalysis();
    if (!an || !an.fc) return { observation: '暂无聚合层（建议先 ensure_zone 生成）' };
    const crit = params.criteria || 'worst';
    const top = Math.min(Math.max(Number(params.top) || 3, 1), 10);
    let feats = an.fc.features
      .filter((f) => { const p = f.properties || {}; return p.polarity_index != null && !isNaN(p.polarity_index); });
    if (!feats.length) return { observation: '聚合层无极性数据' };
    feats = sortZones(feats, crit).slice(0, top);
    const found = feats.map((f) => {
      const p = f.properties || {};
      return { name: p.name || p.issue_label || '未命名', pi: Number(p.polarity_index).toFixed(2),
        dom: DOMAIN_LABEL[p.domain_top] || p.domain_top || '?', elm: ELEMENT_LABEL[p.element_top] || p.element_top || '?',
        pc: p.point_count || 0, issue: p.issue_label || '—' };
    });
    feats.forEach((f) => fitToFeature(f));
    const label = { worst: '情绪最差', best: '情绪最好' }[crit] || crit;
    return {
      observation: `${label} Top${top}：\n` + found.map((x) => `  - ${x.name}：极性${x.pi}，${x.dom}×${x.elm}，${x.pc}点，问题=${x.issue}`).join('\n'),
      data: { found },
    };
  },

  /** 查 4×5 归因（全局或某区域）。 */
  query_attribution(params = {}) {
    const an = activeAnalysis();
    if (!an || !an.fc) return { observation: '暂无聚合层' };
    const zone = (params.zone || '').trim();
    let feats = an.fc.features
      .filter((f) => { const p = f.properties || {}; return p.polarity_index != null && !isNaN(p.polarity_index); });
    if (zone) feats = feats.filter((f) => { const nm = (f.properties || {}).name || ''; return nm === zone || nm.includes(zone) || zone.includes(nm); });
    feats = feats.sort((a, b) => Math.abs(pi(b)) - Math.abs(pi(a))).slice(0, 8);
    if (!feats.length) return { observation: zone ? `未找到「${zone}」的归因数据` : '无归因数据' };
    const rows = feats.map((f) => {
      const p = f.properties || {};
      return `  - ${p.name || p.issue_label || '未命名'}：极性${Number(p.polarity_index).toFixed(2)}，${DOMAIN_LABEL[p.domain_top] || p.domain_top}×${ELEMENT_LABEL[p.element_top] || p.element_top}，${p.point_count || 0}点，问题=${p.issue_label || '—'}`;
    });
    return { observation: (zone ? `「${zone}」及相近区域归因` : '高张力区域归因') + '：\n' + rows.join('\n') };
  },

  /** 查关键词/热门话题（按 issue_label 聚合近似）。 */
  query_keywords(params = {}) {
    const an = activeAnalysis();
    if (!an || !an.fc) return { observation: '暂无聚合层' };
    const pol = params.polarity || 'overall';
    let feats = an.fc.features;
    if (pol !== 'overall') feats = feats.filter((f) => {
      const v = Number((f.properties || {}).polarity_index);
      return pol === 'positive' ? v > 0.15 : v < -0.15;
    });
    const kw = {};
    feats.forEach((f) => {
      const p = f.properties || {};
      const k = p.issue_label || '';
      if (k) kw[k] = (kw[k] || 0) + (p.point_count || 1);
    });
    const top = Object.entries(kw).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([k, v]) => `${k}(${v})`).join('、');
    return { observation: `${pol === 'overall' ? '综合' : pol === 'positive' ? '积极' : '消极'}关键词/问题 Top：${top || '（无）'}` };
  },

  /** 生成/确保聚合域（无则生成，有则复用）。 */
  async ensure_zone(params = {}) {
    const existing = activeAnalysis();
    if (existing && existing.fc && existing.fc.features && existing.fc.features.length) {
      return { observation: `复用现有聚合层「${existing.name}」（${existing.fc.features.length} 单元）` };
    }
    try {
      const r = await generateGridForAI({
        analysis: params.analysis === 'zonal' ? 'zonal' : 'square',
        cellSize: Number(params.cell_size) || undefined,
        polarity: params.polarity || 'overall',
        mode: params.mode === '3d' ? '3d' : '2d',
        silent: true,
      });
      if (r && r.layerId) _adoptToolboxResult(r.layerId, r.fc, r.layerName, { keep: true });   // 5.223 入 EMC 组（与 density 一致·治网格没入）
      _lastGrid = { layerId: r && (r.layerId || r.id) };
      return { observation: `已生成聚合层「${r.layerName}」（${r.featureCount} 单元）` };
    } catch (e) {
      return { observation: '聚合层生成失败：' + (e && e.message ? e.message : e) };
    }
  },

  /** 定位区域到地图（飞到+高亮）。 */
  focus_zones(params = {}) {
    const names = Array.isArray(params.names) ? params.names : [];
    let n = 0;
    names.filter(Boolean).forEach((nm) => {
      for (const l of getLayers()) {
        if (!isAnalysis(l) || !l.fc) continue;
        const f = l.fc.features.find((ff) => { const n2 = (ff.properties || {}).name || ''; return n2 === nm || n2.includes(nm) || nm.includes(n2); });
        if (f) { fitToFeature(f); document.dispatchEvent(new CustomEvent('cell:selected', { detail: { feature: f, layer: l } })); n++; break; }
      }
    });
    return { observation: `已定位 ${n}/${names.length} 个区域` };
  },

  /** 展开 Overview 归因面板。 */
  open_attribution() {
    const an = activeAnalysis();
    if (!an) return { observation: '暂无聚合层' };
    activateTab('overview');
    setOverview(an);
    return { observation: '已展开 Overview 归因面板（4×5 矩阵 + 关键词）' };
  },

  /** 深读某区域明细。 */
  inspect_zone(params = {}) {
    const an = activeAnalysis();
    const name = (params.name || '').trim();
    if (!an || !name) return { observation: '缺区域名或暂无聚合层' };
    const f = an.fc.features.find((ff) => { const nm = (ff.properties || {}).name || ''; return nm === name || nm.includes(name) || name.includes(nm); });
    if (!f) return { observation: `未找到「${name}」` };
    fitToFeature(f);
    document.dispatchEvent(new CustomEvent('cell:selected', { detail: { feature: f, layer: an } }));
    const p = f.properties || {};
    return { observation: `「${name}」深读：极性${Number(p.polarity_index).toFixed(2)}，${DOMAIN_LABEL[p.domain_top] || p.domain_top}×${ELEMENT_LABEL[p.element_top] || p.element_top}，${p.point_count || 0}点，问题=${p.issue_label || '—'}` };
  },

  /** L4 深度归因（A1·lazy enrichment）：某簇 rule 底（issue_label/attribution/suggestion）+ 簇文本 → /aiqa/deep_attribution
   *  → 政策→情绪→项目闭环（deep_attribution/policy_link/project_link/blind_spot）。低置信/LLM 断→后端回退规则底（degraded）。
   *  sample_texts 当前按 domain+element 语义过滤活动点层（空间精确过滤待 refinement）。EMC 深读归因时触发，非 eager。 */
  async deep_read_attribution(params = {}) {
    const an = activeAnalysis();
    const name = (params.name || '').trim();
    if (!an || !name) return { observation: '缺区域名或暂无聚合层（先 zonal_stats/grid 生成聚合层）' };
    const f = an.fc.features.find((ff) => { const nm = (ff.properties || {}).name || ''; return nm === name || nm.includes(name) || name.includes(nm); });
    if (!f) return { observation: `未找到「${name}」` };
    const p = f.properties || {};
    const domain = p.domain_top || '';
    const element = p.element_top || '';
    const polIdx = Number(p.polarity_index || 0);
    const polarity = polIdx > 0.05 ? 'positive' : (polIdx < -0.05 ? 'negative' : 'neutral');
    const rule_suggestion = [p.issue_label, p.attribution, p.suggestion].filter(Boolean).join('；');
    // sample_texts + L4 种子：活动点层按 domain+element 语义过滤取 ≤8 条（MVP 语义代理；空间过滤待 refinement）
    // 同时计数 policy_seed/project_seed/aspect_primary（Sim ermawu_l3l4 富归因数据携带；普通 L2 无则空）
    const ptLayer = getLayers().find((l) => l.kind === 'point' && l.fc && l.visible !== false);
    const sample_texts = [];
    const _policy = {}, _project = {}, _aspect = {};
    if (ptLayer && (domain || element)) {
      for (const ft of (ptLayer.fc.features || [])) {
        const pp = ft.properties || {};
        if ((!domain || pp.domain === domain) && (!element || pp.element === element)) {
          if (pp.text) sample_texts.push(String(pp.text).slice(0, 120));
          if (pp.policy_seed) { const k = String(pp.policy_seed); _policy[k] = (_policy[k] || 0) + 1; }
          if (pp.project_seed) { const k = String(pp.project_seed); _project[k] = (_project[k] || 0) + 1; }
          if (pp.aspect_primary) { const k = String(pp.aspect_primary); _aspect[k] = (_aspect[k] || 0) + 1; }
        }
        if (sample_texts.length >= 8) break;
      }
    }
    const _top = (d, n) => Object.entries(d).sort((a, b) => b[1] - a[1]).slice(0, n).map(([k]) => k);
    const policy_seed_hint = _top(_policy, 2).join('；');
    const project_seed_hint = _top(_project, 2).join('；');
    const aspect_hint = _top(_aspect, 3).join('、');
    try {
      const r = await fetch('/api/v1/aiqa/deep_attribution', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain, element, polarity, zone_name: name, sample_texts, rule_suggestion, policy_seed_hint, project_seed_hint, aspect_hint }),
      });
      const j = r.ok ? await r.json() : null;
      if (!j) return { observation: `[ERR] deep_attribution 调用失败: ${r.status}` };
      const parts = [`「${name}」L4 深度归因（${DOMAIN_LABEL[domain] || domain}×${ELEMENT_LABEL[element] || element}）：${j.deep_attribution}`];
      if (j.policy_link) parts.push(`政策锚：${j.policy_link}`);
      if (j.project_link) parts.push(`落点项目：${j.project_link}`);
      if (j.blind_spot) parts.push(`官方盲区：${j.blind_spot}`);
      if (aspect_hint) parts.push(`簇 aspect：${aspect_hint}`);   // Sim 数据预提取的 aspect 分布
      parts.push(`置信度=${Number(j.confidence || 0).toFixed(2)}${j.degraded ? '（回退规则底·' + String(j.degraded_reason || '').slice(0, 40) + '）' : '（LLM 深化）'}`);
      return { observation: parts.join('\n'), data: { deep_attribution: j } };
    } catch (e) { return { observation: `[ERR] deep_attribution 异常: ${(e && e.message) || e}` }; }
  },

  // ── GIS 工具骨干（POST /api/v1/geo/*，结构化/归因/排序结论主干）─────────────
  /** 宏/中观结论主干：按边界聚合点层，得每单元极性/点数/4×5 归因+排序。 */
  async zonal_stats(params = {}) {
    if (!params.boundary) return { observation: '[ERR] zonal_stats 需 boundary（preset_id）' };
    // CB-20（两组预检·B 兜底）：boundary 空对象/无 features → 诚实 request_upload（治 A 未覆盖路径·LLM 忠实文案素材）
    if (typeof params.boundary === 'object' && params.boundary !== null && !(Array.isArray(params.boundary.features) && params.boundary.features.length)) {
      return { observation: '需上传标准边界资料：boundary 为空/无法解析（EMC 不硬猜不可信范围·CB-14）' };
    }
    const _layer = resolvePointLayer(params);
    if (!_layer) return _ERR_NO_VISIBLE_PT();
    let boundary;
    try {
      boundary = await resolveBoundaryInput(params.boundary);   // 中文地名(西陵区)→GeoJSON；preset_id 直通（§3.3① 委托层预解析，模块不碰中文名）
    } catch (e) {
      // PRM-07（CB-19）：法定功能区黑名单拒识 → 诚实 request_upload 文案（非 ERR·flywheel test-cases:339 判 PASS）
      if (String(e.message || e).includes('法定功能区')) {
        return { observation: `需上传标准边界资料：${e.message}` };
      }
      return _ERR('zonal_stats', e);
    }
    try {
      const r = await generateZonalForAI({ layer: ref(_layer), boundary: ref(boundary), boundaryLabel: _boundaryLabel(params.boundary),
        range: params.range ? ref(params.range) : undefined, pre_filter: normPreFilter(params.pre_filter),
        top_n: params.top_n != null ? Number(params.top_n) : undefined, as: params.as });
      const rows = r.rows || [];
      if (!rows.length) return { observation: `按行政区聚合后无结果（可能该范围无情绪点覆盖）` };
      const _zL = r.layerId ? _adoptToolboxResult(r.layerId, r.fc, r.layerName, { keep: true }) : null;
      return { observation: `区域情绪聚合完成，共 ${rows.length} 个单元，按极性排序：\n` + rows.map(_fmtRow).join('\n') + _renderNote(_zL), data: { rows, sort_by: r.sortBy, layerId: r.layerId } };
    } catch (e) { return _ERR('zonal_stats', e); }
  },

  /** 区域对比（≥2 区并排）：复用 zonal_stats 逐区聚合（不造 geo 端点，守委托 Toolbox 红线）。
   *  boundaries=数组 或 "|,，、" 分隔字符串；上限 4 区防滥用。后端 zonal_stats 已 resolve_field_alias，
   *  compare 继承规范名（polarity_index/score_mean 等），不重复 alias 逻辑（守 emc-aggregate-column-alias-silent-zero）。 */
  async compare_regions(params = {}) {
    let bs = params.boundaries != null ? params.boundaries : params.boundary;
    if (typeof bs === 'string') bs = bs.split(/[|,，、]/).map((s) => s.trim()).filter(Boolean);
    if (!Array.isArray(bs) || bs.length < 2) return { observation: '[ERR] compare_regions 需 boundaries（≥2 个 preset_id，数组或 "|," 分隔）' };
    const _layer = resolvePointLayer(params);
    if (!_layer) return _ERR_NO_VISIBLE_PT();
    const pf = normPreFilter(params.pre_filter);
    const boundaries = [];
    for (const b of bs.slice(0, 4)) {
      try {
        const _g = await resolveBoundaryInput(b);   // 中文名(西陵区)→GeoJSON；preset_id 直通（§3.3① 委托层预解析）
        if (typeof _g === 'string') _guardUsageRef(_g);   // PT-CB2 T2：compare 边界不经 ref() 的直传位 → 补挂铁律7 守卫
        boundaries.push({ label: b, geo: _g });
      } catch (e) {
        // PRM-07（CB-19）：法定功能区黑名单拒识 → 诚实 request_upload（非 ERR）
        if (String(e.message || e).includes('法定功能区')) {
          return { observation: `需上传标准边界资料：${e.message}` };
        }
        throw e;
      }
    }
    try {
      const r = await generateCompareForAI({ layer: ref(_layer), boundaries, pre_filter: pf, as: params.as });
      const results = r.comparison || [];
      const lines = results.map((x) => {
        if (x.err) return `- ${x.boundary}：[ERR] ${x.err.slice(0, 80)}`;
        if (!x.row) return `- ${x.boundary}：无结果（preset_id 无效或该区无点）`;
        return `- ${x.boundary}：${_fmtRow(x.row)}`;
      });
      const _ok = r.okCount;
      if (_ok < 2) return { observation: `区域对比仅 ${_ok}/${results.length} 区有结果（${results.map((x) => x.boundary).join('、')}）——确认 boundaries 为有效 preset_id（行政区/单元）后重试\n` + lines.join('\n') };
      const _cL = r.layerId ? _adoptToolboxResult(r.layerId, r.fc, r.layerName, { keep: true }) : null;   // P1-extend：多区合并聚合图层（choropleth 红绿·activeAnalysis 可认）
      return { observation: `区域对比（${results.length} 区并排，按极性/归因）：\n` + lines.join('\n') + _renderNote(_cL), data: { comparison: results, layerId: r.layerId } };
    } catch (e) { return _ERR('compare_regions', e); }
  },

  /** Top N 排序（最差/最好/按 domain·element 占比）。 */
  async rank(params = {}) {
    let by = params.by || 'worst';
    if (by.startsWith('domain:')) { const cn = by.split(':')[1]; by = 'domain:' + (_DOMAIN_CN2EN[cn] || cn); }
    const _layer = resolvePointLayer(params);
    if (!_layer) return _ERR_NO_VISIBLE_PT();
    try {
      const r = await generateRankForAI({ layer: ref(_layer), by, top_n: Number(params.top_n) || 5,
        boundary: params.boundary ? ref(params.boundary) : undefined,
        boundaryLabel: params.boundary ? _boundaryLabel(params.boundary) : undefined,
        layerRef: typeof params.layer === 'string' ? params.layer : undefined,
        range: params.range ? ref(params.range) : undefined, pre_filter: normPreFilter(params.pre_filter), as: params.as });
      const rows = r.rows || [];
      if (!rows.length) return { observation: `排序无结果` };
      const _rk = r.layerId ? _adoptToolboxResult(r.layerId, r.fc, r.layerName, { keep: true }) : null;
      return { observation: `区域排序前 ${rows.length} 名：\n` + rows.map(_fmtRow).join('\n') + (_rk ? `\n已在地图上高亮显示前 ${rows.length} 名区域（极性着色）` : '') + _renderNote(_rk), data: { rows, by, layerId: r.layerId } };
    } catch (e) { return _ERR('rank', e); }
  },

  /** 按属性筛选（用地/极性/domain/element/时点）。 */
  async filter_attr(params = {}) {
    const pf = normPreFilter(params.pre_filter);
    if (!pf) return { observation: '[ERR] filter_attr 需 pre_filter（field/op/value）' };
    const _layer = resolvePointLayer(params);
    if (!_layer) return _ERR_NO_VISIBLE_PT();
    try {
      const r = await generateFilterForAI({ layer: ref(_layer), pre_filter: pf,
        range: params.range ? ref(params.range) : undefined, as: params.as });
      const feats = (r.fc && r.fc.features) || [];
      const _fL = r.layerId ? _adoptToolboxResult(r.layerId, r.fc, r.layerName, { keep: !!params.keep }) : null;   // 名=内容（值/字段·模块 C6 沿用）
      const sample = feats.slice(0, 3).map((f) => {
        const p = f.properties || {};
        return '{' + Object.keys(p).slice(0, 5).map((k) => `${k}=${p[k]}`).join(', ') + '}';
      });
      // CB-09 P0-4 v2·工具观测诚实化
      if (r.count === 0) {
        return { observation: `属性筛选完成，但无匹配要素，未生成新图层。`, data: { count: 0, layerId: null } };
      }
      return { observation: `按属性筛选命中 ${r.count} 个要素${r.truncated ? '（数量较多已截断）' : ''}，已生成图层「${r.layerName}」${_fL ? '（' + feats.length + ' 个要素）' : ''}，包含：${sample.join('、') || '（无属性）'}` + _renderNote(_fL), data: { count: r.count, layerId: r.layerId } };
    } catch (e) { return _ERR('filter_attr', e); }
  },

  /** 按几何裁剪（某区/某公园范围内的点），结果落地图为新点图层。 */
  async clip(params = {}) {
    if (!params.range) return { observation: '[ERR] clip 需 range（preset_id|geojson）' };
    // CB-10 P0-1/B007：面层走 clip → 报「图层类型不匹配」（防止空结果 + 误导 LLM 以为是裁剪成功）
    const _typeBad = _checkGeomType(params.layer, 'point', 'clip');
    if (_typeBad) return { observation: _typeBad };
    const _layer = resolvePointLayer(params);
    if (!_layer) return _ERR_NO_VISIBLE_PT();
    try {
      const r = await generateClipForAI({ layer: ref(_layer), range: ref(params.range),
        rangeLabel: typeof params.range === 'string' ? params.range : undefined,
        pre_filter: normPreFilter(params.pre_filter), as: params.as });
      const feats = (r.fc && r.fc.features) || [];
      const L = r.layerId ? _adoptToolboxResult(r.layerId, r.fc, r.layerName, { keep: !!params.keep }) : null;   // 名=范围（如「西陵区」·模块 C6 沿用）
      const sample = feats.slice(0, 3).map((f) => { const p = f.properties || {}; return p.name || p.issue_label || '未命名'; });
      // CB-09 P0-4 v2·工具观测诚实化：count=0 时不说"已生成图层"
      if (r.count === 0) {
        return { observation: `裁剪完成，但指定范围内无匹配点数据，未生成新图层。`, data: { count: 0, layerId: null } };
      }
      return { observation: `已在指定范围内裁出 ${r.count} 个情绪点${r.truncated ? '（数量较多已截断）' : ''}，生成图层「${r.layerName}」${L ? '（' + feats.length + ' 个点）' : ''}。包含：${sample.join('、') || '（无）'}` + _renderNote(L), data: { count: r.count, layerId: r.layerId } };
    } catch (e) { return _ERR('clip', e); }
  },
  /** 从面边界按属性抽单要素为独立面图层（裁出某区/某单元），结果落地图。 */
  async extract_feature(params = {}) {
    if (!params.layer) return { observation: '[ERR] extract_feature 需 layer（preset_id|geojson）' };
    // CB-10 P0-1/B007：点层走 extract_feature → 报「图层类型不匹配」（从面层抽要素才用 extract）
    const _typeBad = _checkGeomType(params.layer, 'polygon', 'extract_feature');
    if (_typeBad) return { observation: _typeBad };
    // B（v1.6）：前置字段校验——getFieldCard 查 where.field 是否存在·不存在时自纠正（治 LLM 猜字段名降智）。
    const _where = params.where ? normPreFilter(params.where) : null;
    const _field = _where && _where.field;
    if (_field && !isInternalField(_field)) {
      const _layerObj = getLayers().find((l) => l.name === params.layer || l.id === params.layer);
      if (_layerObj && _layerObj.fc) {
        try {
          const cards = await getFieldCard(_layerObj.id, _layerObj.fc, 'polygon');
          if (cards && !cards[_field]) {
            // 字段自纠正：LLM 常猜 MC（训练数据）但实际字段是 name 等 → 找 boundary_name/name role 字段 + 值匹配
            const _candidates = Object.entries(cards)
              .filter(([f, c]) => !isInternalField(f) && (c.role === 'boundary_name' || c.role === 'name' || f.toLowerCase() === 'name'))
              .map(([f]) => f);
            let _corrected = false;
            for (const _alt of _candidates) {
              const _featVals = new Set((_layerObj.fc.features || []).map((ft) => String((ft.properties || {})[_alt] || '')).filter(Boolean));
              if (_featVals.has(String(_where.value))) {
                params.where = `${_alt}/${_where.op}/${_where.value}`;   // 自纠正
                _corrected = true;
                break;
              }
            }
            if (!_corrected) {
              const _avail = Object.keys(cards).filter((f) => !isInternalField(f)).slice(0, 8).join('、');
              return { observation: `字段「${_field}」不存在${_avail ? `，可用字段：${_avail}` : ''}。请用可用字段重试，或告诉我你要抽取什么内容。` };
            }
          }
        } catch (_) { /* getFieldCard 失败（LLM 不可用/降级）→ 校验降级 skip·不阻塞 */ }
      }
    }
    try {
      const r = await generateExtractForAI({ layer: ref(params.layer),
        sourceLabel: params.layer != null ? String(params.layer) : undefined,   // 空命中命名兜底=原始 layer 串（[object Object]/$n 逐字·C6）
        where: params.where ? (normPreFilter(params.where) || params.where) : undefined, as: params.as });
      const feats = (r.fc && r.fc.features) || [];
      const labels = r.labels || [];
      const L = r.layerId ? _adoptToolboxResult(r.layerId, r.fc, r.layerName, { keep: !!params.keep }) : null;   // 名=要素名（如「西陵区·伍家岗区」/「商业服务业用地」·模块 C6 沿用）
      // CB-09 P0-4 v2·工具观测诚实化：count=0 时不说"已生成图层"
      if (r.count === 0) {
        return { observation: `抽取完成，但面层中无匹配要素（where 条件可能过窄或字段名有误），未生成新图层。`, data: { count: 0, layerId: null } };
      }
      return { observation: `已从面层中抽取出 ${r.count} 个要素，生成图层「${r.layerName}」${L ? '（' + feats.length + ' 个面）' : ''}：${labels.slice(0, 5).join('、') || '（无）'}` + _renderNote(L), data: { count: r.count, layerId: r.layerId } };
    } catch (e) { return _ERR('extract_feature', e); }
  },

  /** 各类用地/各单元面积占比。 */
  async area_stats(params = {}) {
    if (!params.boundary) return { observation: '[ERR] area_stats 需 boundary' };
    try {
      const r = await generateAreaStatsForAI({ boundary: ref(params.boundary), boundaryLabel: _boundaryLabel(params.boundary),
        group_by: params.group_by, as: params.as });
      const rows = r.rows || [];
      const _as = r.layerId ? _adoptToolboxResult(r.layerId, r.fc, r.layerName, { keep: true }) : null;   // A1：choropleth 着色面层（解析不到 boundary 降级纯表格）
      const total = r.totalAreaKm2 != null ? `（总 ${Number(r.totalAreaKm2).toFixed(1)} km²）` : '';
      const seg = rows.map((row) => {
        const label = row[params.group_by] || row.name || '组';
        const share = row.share != null ? (Number(row.share) * 100).toFixed(1) + '%' : '?';
        const area = row.area_km2 != null ? Number(row.area_km2).toFixed(1) + '平方公里' : '?';
        return `${label} 占${share}（${area}）`;
      });
      return { observation: `面积统计${total}：${seg.join('、') || '（无）'}` + (_as ? `，已生成着色图层「${_as.name}」（面积和占比已标注到地图要素）` : '') + _renderNote(_as), data: { rows, layerId: r.layerId } };
    } catch (e) { return _ERR('area_stats', e); }
  },

  /** 合并/dissolve。 */
  async merge(params = {}) {
    // CB-11：boundary（单层 dissolve）或 layers（多图层 concat）二选一
    if (!params.boundary && !params.layers) return { observation: '[ERR] merge 需 boundary（单层）或 layers（多图层）二选一' };
    try {
      const _r = await generateMergeForAI({
        ...(params.boundary ? { boundary: ref(params.boundary), boundaryLabel: _boundaryLabel(params.boundary) } : {}),
        ...(params.layers ? { layers: (params.layers || []).map(ref) } : {}),
        by: params.by, as: params.as });
      const feats = (_r.fc && _r.fc.features) || [];
      const total = _r.totalAreaKm2 != null ? _r.totalAreaKm2 : feats.reduce((a, f) => a + (Number((f.properties || {}).area_km2) || 0), 0);
      const _mL = _r.layerId ? _adoptToolboxResult(_r.layerId, _r.fc, _r.layerName, { keep: !!params.keep }) : null;   // 名=边界（如「西陵区」·模块 C6 沿用）
      // CB-09 P0-4 v2·工具观测诚实化
      if (_r.count === 0) {
        return { observation: `合并完成，但无可合并要素，未生成新图层。`, data: { count: 0, layerId: null } };
      }
      const _modeTxt = params.layers ? `合并 ${params.layers.length} 个图层` : '合并';
      // CB-11 问题 4：observation 列被合并图层名（若为 $n 引用则解析成裁剪产物名）+ _source_layer 范围来源·让 finalStep 知是否已裁剪
      const _srcLayers = (params.layers || []).map((l, i) => {
        const _nm = typeof l === 'string' ? l : (l && l.name) || `图层${i + 1}`;
        return _nm;
      }).join('、');
      return { observation: `${_modeTxt}（来源：${_srcLayers}）后得到 ${_r.count} 个要素，总面积 ${total.toFixed(1)} 平方公里，已生成图层「${_r.layerName}」${_mL ? '（' + feats.length + ' 个面）' : ''}${_r.message ? '（' + _r.message + '）' : ''}` + _renderNote(_mL), data: { count: _r.count, layerId: _r.layerId } };
    } catch (e) { return _ERR('merge', e); }
  },

  /** 设施缓冲区（传 layer/可见点层时后端焊圈内点情绪聚合，消除 buffer→zonal 断点）。
   *  承重① 数据可见纪律：不硬默认 'yichang_l2_t1'——显式 layer 优先，否则用可见点层名交后端聚合（防"只传 L1·T1 却跑 L2"）。
   *  承重② 主 Toolbox dialog 流不破：buffer 产物注入 _ui 元数据（distance 关键 + dissolve/样式 + sourceLayer 尽力解析），
   *    让侧栏 B 按钮打开 Toolbox 编辑面板时回填真实半径，而非 DEFAULTS(1000m) 重做全然不同的 buffer。 */
  async buffer(params = {}) {
    if (!params.center) return { observation: '[ERR] buffer 需 center' };
    const _vl = params.layer ? null : pickVisiblePointLayer();          // 无显式 layer → 可见点层（visible 纪律）
    try {
      const r = await generateBufferForAI({ kind: 'emotion',   // D3：EMC 委托固定 emotion（§5.7）
        center: ref(params.center), centerName: typeof params.center === 'string' ? params.center : undefined,
        radius: _clampM(Number(params.radius_m) || _scaleRadius(params.center) || 500),   // A3 尺度表：缺省按对象尺度推断（社区250/区500/主城1000），显式值钳制
        layer: params.layer ? ref(params.layer) : (_vl ? _vl.name : undefined),   // 可见点层名交后端解析聚合（不再硬默认 L2）
        agg_cols: params.agg_cols, range: params.range ? ref(params.range) : undefined,
        pre_filter: normPreFilter(params.pre_filter), as: params.as });
      const _aggTxt = r.aggregated ? `，圈内 ${r.pointCount} 点·极性 ${Number(r.polarityIndex).toFixed(2)}` : '';
      const _bL = r.layerId ? _adoptToolboxResult(r.layerId, r.fc, r.layerName, { keep: !!params.keep }) : null;   // 名=对象+半径（如「滨江公园·500m」·模块 C6 沿用；_ui 显式 kind:'emotion'·§4.3）
      return { observation: `已生成 ${r.radiusM} 米缓冲区，覆盖 ${r.featureCount} 个设施范围（约 ${Number(r.areaKm2).toFixed(2)} 平方公里）${_aggTxt}，生成图层「${r.layerName}」` + _renderNote(_bL), data: { radius_m: r.radiusM, layerId: r.layerId, aggregated: r.aggregated } };
    } catch (e) { return _ERR('buffer', e); }
  },

  /** 叠置（交/并/差/对称差）。 */
  async overlay(params = {}) {
    if (!params.layer_a || !params.layer_b) return { observation: '[ERR] overlay 需 layer_a + layer_b' };
    // CB-10 P0-1/B007：点层走 overlay → 报「图层类型不匹配」（防止后端空结果 + 误导）
    const _typeBad = _checkGeomType(params.layer_a, 'polygon', 'overlay') || _checkGeomType(params.layer_b, 'polygon', 'overlay');
    if (_typeBad) return { observation: _typeBad };
    try {
      const _lab = (x) => (typeof x === 'string' ? x : (x && x.name) || '图层');
      const r = await generateOverlayForAI({ layer_a: ref(params.layer_a), layer_b: ref(params.layer_b),
        layer_a_label: _lab(params.layer_a), layer_b_label: _lab(params.layer_b),
        how: params.how || 'intersection', as: params.as });
      const feats = (r.fc && r.fc.features) || [];
      const total = r.totalAreaKm2 != null ? r.totalAreaKm2 : feats.reduce((a, f) => a + (Number((f.properties || {}).area_km2) || 0), 0);
      const _oL = r.layerId ? _adoptToolboxResult(r.layerId, r.fc, r.layerName, { keep: !!params.keep }) : null;   // 名=操作语义+两源（如「交·商业用地与西陵区」·模块 C6 沿用）
      // CB-09 P0-4 v2·工具观测诚实化：count=0 时不说"已生成图层"——从源头切断 LLM 误判
      if (r.count === 0) {
        return { observation: `叠置分析完成，但两图层无重叠区域（${_lab(params.layer_a)} ∩ ${_lab(params.layer_b)} = ∅），未生成新图层。`, data: { count: 0, layerId: null } };
      }
      return { observation: `叠置分析完成，得到 ${r.count} 个面，总面积 ${total.toFixed(1)} 平方公里，已生成图层「${r.layerName}」${_oL ? '（' + feats.length + ' 个面）' : ''}${r.message ? '（' + r.message + '）' : ''}` + _renderNote(_oL), data: { count: r.count, layerId: r.layerId } };
    } catch (e) { return _ERR('overlay', e); }
  },

  /** 最近邻。 */
  async nearest(params = {}) {
    if (!params.target) return { observation: '[ERR] nearest 需 target' };
    const _layer = resolvePointLayer(params);
    if (!_layer) return _ERR_NO_VISIBLE_PT();
    try {
      const r = await generateNearestForAI({ layer: ref(_layer), target: ref(params.target),
        targetLabel: typeof params.target === 'string' ? params.target : undefined,
        k: Number(params.k) || 1, as: params.as });
      const rows = r.rows || [];
      if (!rows.length) return { observation: '最近邻无结果' };
      const lines = rows.map((row) => `${row.name || row.issue_label || '点'}(${row.distance != null ? Number(row.distance).toFixed(0) + 'm' : '?'})`);
      const _nr = r.layerId ? _adoptToolboxResult(r.layerId, r.fc, r.layerName, { keep: true }) : null;   // A1：连线层
      return { observation: `最近邻(k=${r.k})：${lines.join('、')}` + (_nr ? ` → 已生成连线层「${_nr.name}」（${rows.length} 条连线·距离入属性）` : '') + _renderNote(_nr), data: { rows, layerId: r.layerId } };
    } catch (e) { return _ERR('nearest', e); }
  },

  /** 查地点（CB-15 P1·C）：中文名/POI 名 → search 坐标 → reverse 近邻。治 LLM 不可见地点。查询型·无图层副作用。 */
  async lookup_place(params = {}) {
    if (!params.q && (params.lng == null || params.lat == null)) return { observation: '[ERR] lookup_place 需 q（地名/POI 名）或坐标(lng,lat)' };
    try {
      let _pt = null;
      if (params.lng != null && params.lat != null) {
        _pt = { lng: Number(params.lng), lat: Number(params.lat), name: '坐标' };
      } else {
        const _s = await fetch(`/api/v1/place/search?q=${encodeURIComponent(String(params.q))}&limit=3`).then((r) => r.json());
        const _hits = (_s && _s.hits) || [];
        if (!_hits.length) return { observation: `未找到地点「${params.q}」（本地 4310 POI + 高德均未命中·请换名或指定坐标）` };
        _pt = _hits[0];
      }
      const _rev = await fetch(`/api/v1/reverse-geocode?lng=${_pt.lng}&lat=${_pt.lat}`).then((r) => r.json());
      const _near = ((_rev && _rev.nearest_pois) || []).slice(0, 5);
      const _nearTxt = _near.length ? _near.map((n) => `${n.name}${n.dist_m != null ? '(' + Math.round(n.dist_m) + 'm)' : ''}`).join('、') : '无';
      const rows = [{
        name: _pt.name, lng: Number(_pt.lng).toFixed(5), lat: Number(_pt.lat).toFixed(5),
        category: _pt.category || _pt.baidu_level1 || '', nearest: _nearTxt,
      }];
      return { observation: `地点「${_pt.name}」@(${Number(_pt.lng).toFixed(5)}, ${Number(_pt.lat).toFixed(5)})，近邻：${_nearTxt}`, data: { rows } };
    } catch (e) { return _ERR('lookup_place', e); }
  },

  /** 批量地名/项目名 → 点位图层（CB-22d·知识问答→地图标记）。
   *  主路径 = search_place（本地 POI + 高德逆地理兜底·业界标准）·绝不强行匹配：
   *    tier-1 点：search_place 命中 → 点要素（source=local/amap）
   *    tier-2 面：未命中但为已知片区/行政区名（面 preset）→ 面要素（source=preset·名称标注）
   *    tier-3 文字：聚合类无地点 → 文字列出「未匹配坐标」（诚实出口·不 request_upload）
   *  渲染 = addToolboxLayer kind:point 显式 circle 样式（defaultPaint 无 point 分支）。
   *  并发：上限 50 名·并发 ≤10·单请求 5s 超时·总预算兜底（防 55 名挂死）。
   *  匹配结果属性 {name, source, match_type} 供 finalStep 可读标注（溯源铁律·防 LLM 自创地址）。 */
  async generate_point_layer(params = {}) {
    // CB-22d P0-0-2：names 鲁棒化——标量/拼接串 split（中文逗号/顿号/半角逗号/空格）→ 逐名数组
    const _raw = Array.isArray(params.names) ? params.names.join(',') : (params.names ? String(params.names) : '');
    const _names = _raw.split(/[,，、;；\s]+/).map((s) => s.trim()).filter(Boolean);
    if (!_names.length) return { observation: '[ERR] generate_point_layer 需 names（要标到地图的项目/地点名列表·可让我从上一轮回答提取）' };
    try {
      const _MAX = 50, _CONC = 10, _TO = 20000;   // P0-0-3：冷加载 12s > 旧 5s abort·提至 20s 防首用必全失败
      const _list = _names.slice(0, _MAX);
      const _picked = new Array(_list.length).fill(null);   // {name, lng, lat, source, match_type, address, category}
      const _unmatched = [];
      let _idx = 0;
      // CB-22d P0-1：聚合名检测——用户想法「无地点描述就放弃」（像人思维）·污水厂网一体示范区/其他项目类不强匹配
      // 聚合名检测（用户想法「无地点描述就放弃」）：含「示范区/其他项目/一批」等聚合词 + 无已知具体地名 → 放弃·不查 API。
      //   容忍引号（污水"厂网一体"示范区）·去除引号后判；「葛洲坝片区」含具体地名葛洲坝 → 不放弃（有地点描述）。
      const _isAggregate = (nm) => {
        const c = nm.replace(/["'“”]/g, '');
        if (!/示范区|其他项目|一批|个片区|个小区|整体|综合整治/.test(c)) return false;
        return !/(西陵|伍家岗|夷陵|猇亭|点军|葛洲坝|西坝|二马路|红星路|土门|小溪塔)/.test(c);
      };
      // 并发限流 worker（Promise.all + 分桶·防 55 名顺序挂死）
      async function _worker() {
        while (true) {
          const i = _idx++;
          if (i >= _list.length) return;
          const nm = String(_list[i]).trim();
          if (_isAggregate(nm)) { _unmatched.push(nm); continue; }   // 聚合名→放弃·不查 API
          try {
            const _ac = new AbortController(); const _t = setTimeout(() => _ac.abort(), _TO);
            // CB-22d P0-1：amap_first=true——高德 API 优先解析（成熟·不造轮子）·未命中落本地 A0 分词双路兜底
            const _s = await fetch(`/api/v1/place/search?q=${encodeURIComponent(nm)}&limit=3&amap_first=true`, { signal: _ac.signal }).then((r) => r.json()).finally(() => clearTimeout(_t));
            const _hits = (_s && _s.hits) || [];
            if (_hits.length && _hits[0] && _hits[0].lng != null) {
              _picked[i] = { name: nm, lng: Number(_hits[0].lng), lat: Number(_hits[0].lat),
                source: _hits[0].source || 'local', match_type: 'point',
                address: _hits[0].address || '', category: _hits[0].category || _hits[0].baidu_level1 || '',
                note: _hits[0].note || '' };   // CB-22e P1.4：amap 命中透传「高德 POI·近似位置」（置信标注）
            } else {
              _unmatched.push(nm);
            }
          } catch (_) { _unmatched.push(nm); }
        }
      }
      await Promise.all(Array.from({ length: Math.min(_CONC, _list.length) }, () => _worker()));
      const _hits = _picked.filter(Boolean);
      const _hitN = _hits.length;
      // 落图（仅有点命中才产图层·全未命中走 tier-3 文字）
      let _layerInfo = '';
      if (_hitN > 0) {
        const _fc = { type: 'FeatureCollection', features: _hits.map((h, i) => ({
          type: 'Feature',
          properties: { name: h.name, source: h.source, match_type: h.match_type, address: h.address || '', category: h.category || '', note: h.note || '', _order: i },
          geometry: { type: 'Point', coordinates: [h.lng, h.lat] },
        })) };
        const _circle = { _ui: { tool: 'generate_point_layer' }, 'circle-radius': 7, 'circle-color': '#ff9000', 'circle-stroke-width': 1.5, 'circle-stroke-color': '#fff' };
        const _L = addToolboxLayer({ name: params.as || '项目点位', kind: 'point', fc: _fc, paint: _circle });
        _layerInfo = _L ? ` → 已生成图层「${_L.name}」(${_hitN} 点)` : '（落图失败）';
      }
      const _src = _hits.reduce((a, h) => { a[h.source] = (a[h.source] || 0) + 1; return a; }, {});
      const _srcTxt = Object.entries(_src).map(([k, v]) => `${k}${v}`).join('、') || '—';
      // CB-22e P1.4：来源行 amap 标注——若存在 amap 命中·追加一次括号说明（防 LLM 自创精度·finalStep 如实表述）
      const _amapNote = _src.amap ? '（amap 为高德解析·近似位置）' : '';
      const _obs = `地点标记：命中 ${_hitN}/${_list.length}${_layerInfo}（来源：${_srcTxt}${_amapNote}）`;
      const _unmatchedTxt = _unmatched.length ? `\n未匹配到坐标（诚实列出·不编造）：${_unmatched.join('、')}` : '';
      const _tip = _hitN > 0 ? '\n已命中项目 → 点位图层（橙色点·可点击查看名称/来源）。未命中项目 → 已文字列出·未生成坐标（聚合类/无地点描述的项目不强匹配·如需要可上传项目坐标数据）。' : '\n全部未匹配到坐标 → 已文字列出·未生成图层（避免编造坐标）。聚合类/无地点描述的项目（如「污水厂网一体示范区」）不硬匹配地点·如需更准位置可上传项目坐标数据。';
      return { observation: _obs + _unmatchedTxt + _tip, data: { rows: _hits, count: _hitN, unmatched: _unmatched, source: _src } };
    } catch (e) { return _ERR('generate_point_layer', e); }
  },

  /** Gi* 热点识别 → 落图层（hot/tend_hot/ns/tend_cold/cold 五档·纯橙系显著性符号层·弃极性色·与 KDE 解耦）。 */
  async hotspot(params = {}) {
    const _layer = resolvePointLayer(params);
    if (!_layer) return _ERR_NO_VISIBLE_PT();
    try {
      const r = await generateHotspotForAI({ layer: ref(_layer), value_col: params.value_col || 'score',
        invert: params.invert !== false, range: params.range ? ref(params.range) : undefined,
        pre_filter: normPreFilter(params.pre_filter), as: params.as,
        threshold: params.threshold, soft_threshold: params.soft_threshold });
      const tally = r.tally || {};
      const _CLS_CN = { hot: '显著聚集(95%)', tend_hot: '倾向聚集(84%)', ns: '不显著', tend_cold: '倾向冷区(84%)', cold: '显著冷区(95%)' };
      const dist = Object.keys(tally).length ? Object.entries(tally).map(([k, v]) => `${_CLS_CN[k] || k}:${v}`).join('、') : `${r.featureCount}要素`;
      const _hL = r.layerId ? _adoptToolboxResult(r.layerId, r.fc, r.layerName, { keep: !!params.keep }) : null;   // class→极性重映射由模块完成（_CLS_POL 随迁·§5.6）
      return { observation: `热点分析：${dist}${r.truncated ? '（已截断）' : ''}（纯橙系显著性五档·hot/tend_hot 深橙·ns 灰·tend_cold/cold 浅橙·弃红绿极性色）→ 已生成图层「${r.layerName}」${_hL ? '(' + r.featureCount + '点)' : ''}` + _renderNote(_hL), data: { count: r.count, tally, layerId: r.layerId } };
    } catch (e) { return _ERR('hotspot', e); }
  },

  /** 分布热度分析 → 委托主 Toolbox（工作机制重构·站在巨人肩膀上）：
   *   2D→generateHeatmapForAI（彩虹热力图，固定 HEATMAP_RAMPS）；3D→generateGridForAI（网格聚合，terrain-9/grid-warm，可切 2D/3D）。
   *   不再自造 /api/v1/geo/density + DENSITY_RAMP（已弃用；端点保留向后兼容）。数据走 Layers 可见层（pickVisiblePointLayer）。 */
  async density(params = {}) {
    const _vl = params.layer ? null : pickVisiblePointLayer();
    if (!params.layer && !_vl) return _ERR_NO_VISIBLE_PT();
    const _srcKey = params.layer ? undefined : _vl.sourceKey;   // 显式 layer → generateXxx 自动选源；否则传可见 sourceKey
    const _mode = params.mode === 'terrain' ? 'terrain' : params.mode === '3d' ? '3d' : params.mode === '2d' ? '2d' : (() => {   // 5.222 视角默认：2D 视角(pitch≤1)→2d 热力图·3D(pitch>1)→3d 网格柱
      try { const _m = getMap(); return (_m && _m.getPitch() > 1) ? '3d' : '2d'; } catch (_) { return '2d'; }
    })();
    try {
      let r;
      if (_mode === 'terrain') {
        // 热点图 P1.5（B1 审计修复）：EMC density mode=terrain 切 generateTerrain3DForAI（setTerrain 连续曲面）·
        //   替代旧 generateTerrainForAI（fill-extrusion 千层饼·retired.md 已登记退役）
        r = await generateTerrain3DForAI({ source: _srcKey, polarity: params.polarity, silent: true });   // 3D KDE DEM 连续曲面（仅 L2）
      } else if (_mode === '3d') {
        r = await generateGridForAI({
          analysis: 'square', cellSize: _clampM(Number(params.cell_size) || _scaleRadius(params.range) || 600),   // A3 尺度表
          polarity: params.polarity || 'overall', mode: '3d', source: _srcKey, silent: true,
        });
      } else {
        r = await generateHeatmapForAI({
          source: _srcKey, level: params.level || (params.layer ? undefined : _vl.level),
          analysis: params.analysis, polarity: params.polarity,                     // CB-04 analysis（色板）+ polarity（筛选）；analysis 缺省时 generateHeatmapForAI 由 polarity 推导
          radius: _clampM(Number(params.radius) || _scaleRadius(params.range) || 300),   // A3 尺度表
          weightField: params.weightField || 'emotion_intensity', silent: true,
        });
      }
      // 补 EMC provenance/$n/AI 组 + 沉浸聚焦（v2.2 另案落地：density 迁移 _adoptToolboxResult，与 12 委托工具同则；
      // 组 A 遗留「density 委托丢 focusOnlyResults」修复——observation 不变，仅图面行为与全员工具对齐）。
      _adoptToolboxResult(r.layerId, r.fc, params.as || r.layerName);
      const _dName = params.as || r.layerName;
      const _modeLabel = { '2d': '热力图(2D彩虹)', '3d': '网格聚合(3D·固定色段)', terrain: '情绪地形(3D KDE 等值面)' }[_mode];
      // CB-09 D016：observation 参数自述 + 单位明确（治 LLM 锚定"点"+300m 致矛盾结论·DeepSeek 微调2）
      const _unit = _mode === 'terrain' ? '层等值面' : (_mode === '3d' ? '网格单元' : '点');
      const _param = _mode === '3d' ? `(cell_size=${_clampM(Number(params.cell_size) || _scaleRadius(params.range) || 600)}m)` : (_mode === '2d' ? `(radius=${_clampM(Number(params.radius) || _scaleRadius(params.range) || 300)}m)` : '');
      return {
        observation: `${_modeLabel}：${r.featureCount} ${_unit}${_param} → 已生成图层「${_dName}」（套用 Toolbox 固定色段，可切 2D/3D）` + _renderNote(getLayer(r.layerId)),
        data: { layerId: r.layerId, mode: _mode, count: r.featureCount },
      };
    } catch (e) { return _ERR('density', e); }
  },

  /** run_python：自由执行 Python（geo 工具覆盖不到的灵活分析/出图兜底）。
   *  出图用 matplotlib（Agg），plt.savefig('fig.png') 自动捕获；取图层用 inputs[{layer,as}] 注入变量。
   *  产图片不入地图（不调 addResultLayer），observation 用「图片」不用图层词（避 5.74 对账 verbRe 污染）。 */
  async run_python(params = {}) {
    const code = (params.code || '').toString().trim();
    if (!code) return { observation: '[ERR] run_python 需 code' };
    const inputs = Array.isArray(params.inputs) ? params.inputs : [];
    const dataRefs = {};
    for (const inp of inputs) {
      if (!inp || !inp.layer || !inp.as) continue;
      const fc = ref(inp.layer);   // $n / 已加载图层名 → fc；preset_id 返字符串则跳过（data_refs 须 GeoJSON dict）
      if (fc && fc.features) dataRefs[inp.as] = fc;
    }
    try {
      const r = await fetchRun({
        code,
        data_refs: dataRefs,
        timeout: Number(params.timeout) || 30,
      });
      if (!r.ok) {
        return { observation: '[ERR] 代码执行失败：' + String(r.error || '未知错误').slice(-200) };
      }
      const figList = Array.isArray(r.figs) ? r.figs : [];
      for (const f of figList) {
        if (f && f.id && f.dataUri) _figCache.set(f.id, f.dataUri);   // panel.js _renderFigs 据此替换 {{fig:ID}}
      }
      const outTail = (r.stdout || '').slice(-400).trim();
      const figLine = figList.length
        ? `\n已生成图片：${figList.map((f) => f.name).join(', ')}（在结论里用 {{fig:${figList[0].id}}} 引用）`
        : '';
      return {
        observation: '代码执行成功。' + (outTail ? `\n输出末尾：\n${outTail}` : '') + figLine,
        data: { figs: figList.map((f) => ({ id: f.id, name: f.name })), hasImage: figList.length > 0 },
      };
    } catch (e) {
      return { observation: '[ERR] run_python：' + String((e && e.message) || e) };
    }
  },
};
