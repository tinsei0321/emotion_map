// ═══ tools.js — Agent Loop 工具集（查询型 + 操作型，直调主窗口函数）═══
// 还原单窗口后，tools 直调 map/state/panel（删跨窗口协议）。每个 tool 返回 {observation, data?}：
//   observation = 给 LLM 看的摘要字符串（入 tool_history）；data = 结构化（前端可选用于渲染）。
import { getLayers, getLayer, getSelectedLayer, addLayer, addGroup, removeLayer, setLayerVisible } from '../state.js';
import { fitBoundsTo, renderLayer, reorderAllZ, removeLayerFromMap } from '../map.js';
import { activateTab, setOverview } from '../panel.js';
import { DOMAIN_LABEL, ELEMENT_LABEL } from '../popup.js';
import { generateGridForAI } from '../grid-tool.js';
import { renderLayerList, refreshLegend } from '../sidebar.js';
import { fcBBox, profileFields } from '../import.js';
import { resolveRole, isRenderContract, isInternalField } from '../field_dictionary.js';   // P2/P3 字段语义层·规则标注 + _fieldSamples 语义过滤
import { landuseLayerPaint } from '../landuse_colors.js';   // 用地层自动附标准色（EMC 产物也走此）

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
    .then((c) => c || null);
  return _geoCatalogPromise;
}

/** 上传/激活新边界预设后失效目录缓存 → 下一轮 AI 即可见新预设（不必刷新页面）。 */
export function invalidateGeoCatalog() { _geoCatalogPromise = null; }

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
export async function getFieldCard(layerId, fc, layerKind = 'point') {
  if (layerId && _fieldCardCache.has(layerId)) return _fieldCardCache.get(layerId);
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
  if (layerId) _fieldCardCache.set(layerId, cards);
  return cards;
}

/** POST /api/v1/geo/<path> 取 JSON；失败抛 Error(.detail)。 */
const _LAYER_REF_KEYS = ['layer', 'range', 'layer_a', 'layer_b', 'boundary', 'center', 'target'];
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
      return fc;
    }
  }
  if (typeof v === 'string' && v) {
    const all = getLayers().filter((x) => x.fc && x.fc.features && x.fc.features.length);
    let l = all.find((x) => x.name === v);
    if (!l) {
      const inc = all.filter((x) => x.name && x.name.includes(v));
      if (inc.length === 1) l = inc[0];   // 唯一包含才匹配，避免歧义
    }
    if (l) {
      if (_resultIdByStep.includes(l.id)) _consumedIds.add(l.id);   // 命名引用本轮 EMC 结果 = 中间产物被消费 → 收尾移除
      return l.fc;
    }
  }
  return v;
}
async function geoFetch(path, body) {
  const b = {};
  for (const k of Object.keys(body || {})) b[k] = _LAYER_REF_KEYS.includes(k) ? ref(body[k]) : body[k];
  const r = await fetch('/api/v1/geo/' + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(b),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((j && (j.detail || j.error)) || ('HTTP ' + r.status));
  return j;
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

/** 核密度(KDE)离散分段色带（5 段，浅粉→深红热力；色值取自 tokens.json gradient.neg 反向，单源勿散用；遵 ramp-discrete-segments，禁连续渐变）。
 *  density 面层经 map.js isTool(density) 复用 grid 色带 fill 管线，按 feature._level(0..1) 落色。 */
const DENSITY_RAMP = [[0, '#FADBD8'], [0.25, '#E6B0AA'], [0.5, '#C0392B'], [0.75, '#922B21'], [1.0, '#641E16']];
const _fmtPi = (v) => (v !== '' && v != null && !isNaN(v) ? Number(v).toFixed(2) : '?');
const _fmtRow = (row) => {
  const dom = DOMAIN_LABEL[row.domain_top] || row.domain_top || '?';
  const elm = ELEMENT_LABEL[row.element_top] || row.element_top || '?';
  return `  - ${row.name || '未命名'}：极性 ${_fmtPi(row.polarity_index)}，${row.point_count || 0}点，${dom}×${elm}，问题=${row.issue_label || '—'}`;
};


function isAnalysis(l) {
  const ui = l && l.paint && l.paint._ui;
  return !!(l && l.kind === 'polygon' && ui && (ui.tool === 'grid' || ui.tool === 'terrain'));
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
    else if (!want && l.visible) { setLayerVisible(l.id, false); renderLayer(l); }
  }
}

/** 把 geo 工具产出的 GeoJSON 落地图为新图层（统一回写，复用 range-presets/grid-tool 范式）。
 * 替换语义：同名旧结果层先移除再新建（防重复堆叠）。name=图层名，kind=point|polygon。
 * keep=true → 显式保留（用户要求/展示结果），即使被后续工具引用消费也豁免清理。
 * 点层自动按 polarity 上色（addLayer 默认 colorMode）；面层需传 paint.fillOn 才可见。
 * 沉浸聚焦：每生成一个结果 → 关其余、留本轮所有结果、缩放至并集（maxZoom 16 防过度放大）。 */
export function addResultLayer({ name, kind = 'polygon', fc, paint, keep, fields }) {
  if (!fc || !fc.features || !fc.features.length) return null;
  for (const l of getLayers()) {
    if (l.name === name) { removeLayerFromMap(l.id); removeLayer(l.id); }
  }
  // 消费式收尾：移除被引用消费的中间结果层，但 _keepIds（显式保留）豁免——显式意图覆盖默认清理。
  // 未消费的并列最终结果（如 居住+商业）保留；$n/命名引用走 _stepResults 的 fc，不依赖图层存活。
  for (let i = _curResultIds.length - 1; i >= 0; i--) {
    if (_consumedIds.has(_curResultIds[i]) && !_keepIds.has(_curResultIds[i])) { removeLayerFromMap(_curResultIds[i]); removeLayer(_curResultIds[i]); _curResultIds.splice(i, 1); }
  }
  // 用地层自动附制图规范标准色（任何 EMC 工具产物：extract/clip/filter/overlay/merge/buffer…）。
  // kind=polygon 且检测为用地（有 DLMC 或层名含用地关键词）→ 标准色覆盖默认 paint 的 color/fillOpacity。
  let _paint = paint;
  if (kind === 'polygon') {
    const _lu = landuseLayerPaint(fc, name);
    if (_lu) _paint = { ...(paint || {}), ..._lu };
  }
  // 工作机制：注入 _ui.tool（from setToolContext 的 _curTool）——让 EMC 产物带工具身份，Toolbox 编辑面板（按 _ui.tool 回填参数）对 EMC buffer/overlay/clip 等生效
  if (_curTool) {
    if (!_paint) _paint = { _ui: { tool: _curTool } };
    else if (!_paint._ui) _paint = { ..._paint, _ui: { tool: _curTool } };
    else if (!_paint._ui.tool) _paint._ui.tool = _curTool;
  }
  const L = addLayer({ name, kind, fc, paint: _paint, parentId: _aiGroup().id });
  L.srcName = name;
  _registry.push({ id: L.id, name, tool: _curTool, round: _curRound, t: Date.now(), fields });   // ① registry（provenance 由 harness setToolContext 注入；fields 可选字段简表，P3 formatRegistry 用）
  if (keep) _keepIds.add(L.id);              // 显式保留登记（覆盖消费式清理）
  _curResultIds.push(L.id);                 // 登记本轮存活结果（沉浸聚焦）
  renderLayer(L);
  renderLayerList(); refreshLegend(); reorderAllZ();
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
async function _fieldSamples(fc, maxFields = 6, layerId = null) {
  const feats = fc && fc.features;
  if (!feats || !feats.length) return '';
  const cards = await getFieldCard(layerId, fc);
  const keys = [];
  for (const k of Object.keys(cards)) {
    if (isInternalField(k) || isRenderContract(cards[k].role)) continue;   // 过滤内部/渲染契约
    if (!keys.includes(k)) { keys.push(k); if (keys.length >= maxFields) break; }
  }
  return keys.map((k) => {
    const c = cards[k];
    const role = c.role || '?';
    const vals = (c.samples || []).slice(0, 2);
    if (!vals.length) return `${k}=${_dtypeTag(c.dtype)}:${role}`;
    return `${k}=${_dtypeTag(c.dtype)}:${role}:${vals.join('|').slice(0, 24)}`;
  }).join('/');
}

/** buildContext：grounding 摘要（panel send + query_layers 共用）。 */
export async function buildContext() {
  const layers = getLayers();
  const an = activeAnalysis();
  const parts = [];
  const loaded = (await Promise.all(layers
    .filter((l) => l.visible && l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length)
    .map(async (l) => {
      const cnt = l.fc.features.length;
      const fs = await _fieldSamples(l.fc, 6, l.id);   // DataEye（P3）：字段+类型+role+样本值（供 AI 写 where 有真实值参照）
      return `${l.name}(${cnt}条${fs ? ',字段:' + fs : ''})`;
    }))).join('、');
  parts.push('已加载图层（仅 Layers 当前显示·EMC 只用可见层，未显示层禁用）：' + (loaded || '（无）'));
  // 数据可见纪律：不注入 registry catalog 全量（formatGeoCatalog）——未显示层一律不准用，防"只传 L1·T1 却跑 L2"
  const wisdom = await getWisdom();
  if (wisdom) parts.push(wisdom);
  if (!an) {
    parts.push('（暂无聚合层——区域级问题建议先 ensure_zone 生成）');
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
  const vis = getLayers().filter((l) => l.visible && l.fc && l.fc.features && l.fc.features.length);
  for (const l of vis) {   // L2 group（多极性子层合并）优先
    if (l.kind === 'group' && l.children && l.children.length) {
      const merged = [];
      for (const cid of l.children) { const c = getLayer(cid); if (c && c.fc && c.fc.features.length) merged.push(...c.fc.features); }
      if (merged.length) return { fc: { type: 'FeatureCollection', features: merged }, name: l.name, level: 'L2', sourceKey: `group:${l.id}` };
    }
  }
  const pts = vis.filter((l) => l.kind === 'point');
  const l2 = pts.find((l) => l.colorMode && String(l.colorMode).startsWith('l2-'));
  if (l2) return { fc: l2.fc, name: l2.name, level: 'L2', sourceKey: `layer:${l2.id}` };
  const l1 = pts.find((l) => l.colorMode === 'confidence');
  if (l1) return { fc: l1.fc, name: l1.name, level: 'L1', sourceKey: `layer:${l1.id}` };
  return null;
}
/** 工具入参 layer 解析：显式 params.layer 优先（geoFetch ref() 解析图层名/$n/preset_id/GeoJSON），否则用可见层 fc。 */
function resolvePointLayer(params) {
  if (params.layer) return params.layer;
  const vl = pickVisiblePointLayer();
  return vl ? vl.fc : null;
}
function _ERR_NO_VISIBLE_PT() {
  return { observation: '[ERR] 无可见的情绪点层——EMC 只用 Layers 当前显示的数据，请先加载/上传情绪点（registry 未显示层一律禁用）' };
}

export const TOOLS = {
  /** 查当前已加载的图层/数据。 */
  query_layers() {
    const an = activeAnalysis();
    const loaded = getLayers()
      .filter((l) => l.kind !== 'group' && l.fc && l.fc.features && l.fc.features.length)
      .map((l) => `${l.name}(${l.fc.features.length}条)`).join('、');
    return { observation: `已加载图层：${loaded || '（无）'}\n当前分析层：${an ? an.name + '（' + an.fc.features.length + ' 单元）' : '暂无聚合层（区域级问题建议 ensure_zone）'}` };
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

  // ── GIS 工具骨干（POST /api/v1/geo/*，结构化/归因/排序结论主干）─────────────
  /** 宏/中观结论主干：按边界聚合点层，得每单元极性/点数/4×5 归因+排序。 */
  async zonal_stats(params = {}) {
    if (!params.boundary) return { observation: '[ERR] zonal_stats 需 boundary（preset_id）' };
    const _layer = resolvePointLayer(params);
    if (!_layer) return _ERR_NO_VISIBLE_PT();
    const body = { layer: _layer, boundary: params.boundary };
    if (params.range) body.range = params.range;
    const pf = normPreFilter(params.pre_filter); if (pf) body.pre_filter = pf;
    if (params.top_n != null) body.top_n = Number(params.top_n);
    try {
      const r = await geoFetch('zonal_stats', body);
      const rows = r.rows || [];
      if (!rows.length) return { observation: `面域聚合（boundary=${params.boundary}）无结果` };
      return { observation: `面域聚合 ${rows.length} 单元（boundary=${params.boundary}，按 |${r.sort_by || 'polarity_index'}| 降序）：\n` + rows.map(_fmtRow).join('\n'), data: { rows, sort_by: r.sort_by } };
    } catch (e) { return _ERR('zonal_stats', e); }
  },

  /** Top N 排序（最差/最好/按 domain·element 占比）。 */
  async rank(params = {}) {
    let by = params.by || 'worst';
    if (by.startsWith('domain:')) { const cn = by.split(':')[1]; by = 'domain:' + (_DOMAIN_CN2EN[cn] || cn); }
    const _layer = resolvePointLayer(params);
    if (!_layer) return _ERR_NO_VISIBLE_PT();
    const body = { layer: _layer, by, top_n: Number(params.top_n) || 5 };
    if (params.boundary) body.boundary = params.boundary;
    if (params.range) body.range = params.range;
    const pf = normPreFilter(params.pre_filter); if (pf) body.pre_filter = pf;
    try {
      const r = await geoFetch('rank', body);
      const rows = r.rows || [];
      if (!rows.length) return { observation: `排序（by=${by}）无结果` };
      return { observation: `排序 Top${rows.length}（by=${by}）：\n` + rows.map(_fmtRow).join('\n'), data: { rows, by } };
    } catch (e) { return _ERR('rank', e); }
  },

  /** 按属性筛选（用地/极性/domain/element/时点）。 */
  async filter_attr(params = {}) {
    const pf = normPreFilter(params.pre_filter);
    if (!pf) return { observation: '[ERR] filter_attr 需 pre_filter（field/op/value）' };
    const _layer = resolvePointLayer(params);
    if (!_layer) return _ERR_NO_VISIBLE_PT();
    const body = { layer: _layer, pre_filter: pf };
    if (params.range) body.range = params.range;
    try {
      const r = await geoFetch('filter_attr', body);
      const feats = (r.geojson && r.geojson.features) || [];
      const _fName = params.as || String(pf.value || pf.field || '属性筛选');   // 名=内容（值/字段），勿用「筛选·」工程前缀
      const _fL = addResultLayer({ name: _fName, kind: 'point', fc: r.geojson, keep: !!params.keep });
      const sample = feats.slice(0, 3).map((f) => {
        const p = f.properties || {};
        return '{' + Object.keys(p).slice(0, 5).map((k) => `${k}=${p[k]}`).join(', ') + '}';
      });
      return { observation: `属性筛选命中 ${r.count} 个要素${r.truncated ? '（已截断）' : ''} → 已生成图层「${_fName}」${_fL ? '(' + feats.length + '点)' : ''}，示例：${sample.join(' | ') || '（无属性）'}`, data: { count: r.count, layerId: _fL && _fL.id } };
    } catch (e) { return _ERR('filter_attr', e); }
  },

  /** 按几何裁剪（某区/某公园范围内的点），结果落地图为新点图层。 */
  async clip(params = {}) {
    if (!params.range) return { observation: '[ERR] clip 需 range（preset_id|geojson）' };
    const _layer = resolvePointLayer(params);
    if (!_layer) return _ERR_NO_VISIBLE_PT();
    const body = { layer: _layer, range: params.range };
    const pf = normPreFilter(params.pre_filter); if (pf) body.pre_filter = pf;
    try {
      const r = await geoFetch('clip', body);
      const feats = (r.geojson && r.geojson.features) || [];
      const name = params.as || (typeof params.range === 'string' ? params.range : '范围裁剪');   // 名=范围（如「西陵区」），勿用「裁剪·」
      const L = addResultLayer({ name, kind: 'point', fc: r.geojson, keep: !!params.keep });
      const sample = feats.slice(0, 3).map((f) => { const p = f.properties || {}; return p.name || p.issue_label || '未命名'; });
      return { observation: `裁剪命中 ${r.count} 个要素${r.truncated ? '（已截断）' : ''}（range=${params.range}）→ 已生成图层「${name}」${L ? '(' + feats.length + '点)' : ''}，示例：${sample.join('、') || '（无）'}`, data: { count: r.count, layerId: L && L.id } };
    } catch (e) { return _ERR('clip', e); }
  },
  /** 从面边界按属性抽单要素为独立面图层（裁出某区/某单元），结果落地图。 */
  async extract_feature(params = {}) {
    if (!params.layer) return { observation: '[ERR] extract_feature 需 layer（preset_id|geojson）' };
    const body = { layer: params.layer };
    if (params.where) body.where = normPreFilter(params.where) || params.where;   // 归一：字符串/对象 + in 多值逗号切分（"MC/in/西陵区,伍家岗区"→list）
    try {
      const r = await geoFetch('extract_feature', body);
      const feats = (r.geojson && r.geojson.features) || [];
      const _nm = (f) => { const p = f.properties || {}; return p.name || p[r.name_field] || Object.values(p).find((v) => typeof v === 'string') || '未命名'; };
      const labels = feats.map(_nm);
      const name = params.as || (labels.slice(0, 2).join('·') || params.layer);   // 名=要素名（如「西陵区·伍家岗区」/「商业服务业用地」）
      const L = addResultLayer({ name, kind: 'polygon', fc: r.geojson, paint: { fillOn: true, lineWidth: 2, fillOpacity: 0.2 }, keep: !!params.keep });
      return { observation: `属性抽取命中 ${r.count} 个面要素（layer=${params.layer}${params.where ? ', where=' + params.where : ''}）→ 已生成图层「${name}」${L ? '(' + feats.length + '面)' : ''}：${labels.slice(0, 5).join('、') || '（无）'}`, data: { count: r.count, layerId: L && L.id } };
    } catch (e) { return _ERR('extract_feature', e); }
  },

  /** 各类用地/各单元面积占比。 */
  async area_stats(params = {}) {
    if (!params.boundary) return { observation: '[ERR] area_stats 需 boundary' };
    const body = { boundary: params.boundary };
    if (params.group_by) body.group_by = params.group_by;
    try {
      const r = await geoFetch('area_stats', body);
      const rows = r.rows || [];
      const total = r.total_area_km2 != null ? `（总 ${Number(r.total_area_km2).toFixed(1)} km²）` : '';
      const seg = rows.map((row) => {
        const label = row[params.group_by] || row.name || '组';
        const share = row.share != null ? (Number(row.share) * 100).toFixed(1) + '%' : '?';
        const area = row.area_km2 != null ? Number(row.area_km2).toFixed(1) + 'km²' : '?';
        return `${label} ${share}(${area})`;
      });
      return { observation: `面积统计${total}：${seg.join('、') || '（无）'}`, data: { rows } };
    } catch (e) { return _ERR('area_stats', e); }
  },

  /** 合并/dissolve。 */
  async merge(params = {}) {
    if (!params.boundary) return { observation: '[ERR] merge 需 boundary' };
    const body = { boundary: params.boundary };
    if (params.by) body.by = params.by;
    try {
      const r = await geoFetch('merge', body);
      const feats = (r.geojson && r.geojson.features) || [];
      const total = feats.reduce((a, f) => a + (Number((f.properties || {}).area_km2) || 0), 0);
      const _mName = params.as || String(params.boundary || '合并范围');   // 名=边界（如「西陵区」），勿用「合并·」
      const _mL = addResultLayer({ name: _mName, kind: 'polygon', fc: r.geojson, paint: { fillOn: true, lineWidth: 2, fillOpacity: 0.2 }, keep: !!params.keep });
      return { observation: `合并得 ${r.count} 个面，总面积 ${total.toFixed(1)} km² → 已生成图层「${_mName}」${_mL ? '(' + feats.length + '面)' : ''}`, data: { count: r.count, layerId: _mL && _mL.id } };
    } catch (e) { return _ERR('merge', e); }
  },

  /** 设施缓冲区（传 layer 时后端焊圈内点情绪聚合，消除 buffer→zonal 断点）。 */
  async buffer(params = {}) {
    if (!params.center) return { observation: '[ERR] buffer 需 center' };
    const body = { center: params.center, radius_m: Number(params.radius_m) || 500 };
    if (params.layer) body.layer = params.layer;                       // P1 聚合：传点层 → 后端焊圈内情绪统计
    if (params.agg_cols) body.agg_cols = params.agg_cols;
    if (params.range) body.range = params.range;
    const pf = normPreFilter(params.pre_filter); if (pf) body.pre_filter = pf;
    try {
      const r = await geoFetch('buffer', body);
      const feats = (r.geojson && r.geojson.features) || [];
      const _p0 = (feats[0] && feats[0].properties) || {};
      const area = Number(_p0.area_km2) || 0;
      const _agg = _p0.point_count != null;                            // 后端聚合成功则 properties 含 point_count
      const _bName = params.as || `${typeof params.center === 'string' ? params.center : '设施'}·${body.radius_m}m`;   // 名=对象+半径（如「滨江公园·500m」）
      const _bL = addResultLayer({ name: _bName, kind: 'polygon', fc: r.geojson, paint: { fillOn: true, lineWidth: 2, fillOpacity: 0.2 }, keep: !!params.keep });
      const _aggTxt = _agg ? `，圈内 ${_p0.point_count} 点·极性 ${Number(_p0.polarity_index).toFixed(2)}` : '';
      return { observation: `缓冲区 radius=${r.radius_m || body.radius_m}m，得 ${feats.length} 个面（约 ${area.toFixed(2)} km²）${_aggTxt} → 已生成图层「${_bName}」`, data: { radius_m: r.radius_m, layerId: _bL && _bL.id, aggregated: _agg } };
    } catch (e) { return _ERR('buffer', e); }
  },

  /** 叠置（交/并/差/对称差）。 */
  async overlay(params = {}) {
    if (!params.layer_a || !params.layer_b) return { observation: '[ERR] overlay 需 layer_a + layer_b' };
    const body = { layer_a: params.layer_a, layer_b: params.layer_b, how: params.how || 'intersection' };
    try {
      const r = await geoFetch('overlay', body);
      const feats = (r.geojson && r.geojson.features) || [];
      const total = feats.reduce((a, f) => a + (Number((f.properties || {}).area_km2) || 0), 0);
      const _howCN = { intersection: '交', union: '并', difference: '差', symmetric_difference: '对称差' }[body.how] || body.how;
      const _lab = (x) => (typeof x === 'string' ? x : (x && x.name) || '图层');
      const _oName = params.as || `${_howCN}·${_lab(params.layer_a)}与${_lab(params.layer_b)}`;   // 名=操作语义+两源（如「交·商业用地与西陵区」），勿用「叠置·intersection」
      const _oL = addResultLayer({ name: _oName, kind: 'polygon', fc: r.geojson, paint: { fillOn: true, lineWidth: 2, fillOpacity: 0.25 }, keep: !!params.keep });
      return { observation: `叠置(${r.how || body.how}) 得 ${r.count} 个面，总面积 ${total.toFixed(1)} km² → 已生成图层「${_oName}」${_oL ? '(' + feats.length + '面)' : ''}${r.message ? '（' + r.message + '）' : ''}`, data: { count: r.count, layerId: _oL && _oL.id } };
    } catch (e) { return _ERR('overlay', e); }
  },

  /** 最近邻。 */
  async nearest(params = {}) {
    if (!params.target) return { observation: '[ERR] nearest 需 target' };
    const _layer = resolvePointLayer(params);
    if (!_layer) return _ERR_NO_VISIBLE_PT();
    const body = { layer: _layer, target: params.target, k: Number(params.k) || 1 };
    try {
      const r = await geoFetch('nearest', body);
      const rows = r.rows || [];
      if (!rows.length) return { observation: '最近邻无结果' };
      const lines = rows.map((row) => `${row.name || row.issue_label || '点'}(${row.distance != null ? Number(row.distance).toFixed(0) + 'm' : '?'})`);
      return { observation: `最近邻(k=${body.k})：${lines.join('、')}`, data: { rows } };
    } catch (e) { return _ERR('nearest', e); }
  },

  /** Gi* 热点识别 → 落图层（hot/cold/ns 点，离散色：hot=负面聚集=红 / cold=正面聚集=绿 / ns=灰）。 */
  async hotspot(params = {}) {
    const _layer = resolvePointLayer(params);
    if (!_layer) return _ERR_NO_VISIBLE_PT();
    const body = { layer: _layer, value_col: params.value_col || 'score', invert: params.invert !== false };
    if (params.range) body.range = params.range;
    const pf = normPreFilter(params.pre_filter); if (pf) body.pre_filter = pf;
    try {
      const r = await geoFetch('hotspot', body);
      const feats = (r.geojson && r.geojson.features) || [];
      // hotspot class → 极性色槽（复用离散 5 色极性色带，零 map.js 改动；class 原值保留供弹窗/观察）
      const _CLS_POL = { hot: 'Very Negative', cold: 'Very Positive', ns: 'Neutral' };
      const renderFc = {
        type: 'FeatureCollection',
        features: feats.map((f) => {
          const props = { ...(f.properties || {}) };
          const cls = props.hotspot || props.class || props.gi_class || 'ns';
          props.polarity = _CLS_POL[cls] || 'Neutral';
          return { ...f, properties: props };
        }),
      };
      const _hName = params.as || '情绪热点(Gi*)';
      const _hL = addResultLayer({ name: _hName, kind: 'point', fc: renderFc, keep: !!params.keep });
      const tally = {};
      feats.forEach((f) => {
        const p = f.properties || {};
        const cls = p.hotspot || p.class || p.gi_class || 'ns';
        tally[cls] = (tally[cls] || 0) + 1;
      });
      const _CLS_CN = { hot: '显著热点(负面聚集)', cold: '显著冷点(正面聚集)', ns: '不显著' };
      const dist = Object.keys(tally).length ? Object.entries(tally).map(([k, v]) => `${_CLS_CN[k] || k}:${v}`).join('、') : `${feats.length}要素`;
      return { observation: `热点分析：${dist}${r.truncated ? '（已截断）' : ''}（hot=红/cold=绿/ns=灰）→ 已生成图层「${_hName}」${_hL ? '(' + feats.length + '点)' : ''}`, data: { count: r.count, tally, layerId: _hL && _hL.id } };
    } catch (e) { return _ERR('hotspot', e); }
  },

  /** 核密度(KDE)栅格 → 落面层（2D 密度面，离散分段色带）。"核密度/密度分析"的标准出口=新图层。 */
  async density(params = {}) {
    const body = {
      layer: params.layer || 'yichang_l2_t1',
      bandwidth_m: Number(params.bandwidth_m) || 800,
      cell_size_m: Number(params.cell_size_m) || 300,
    };
    body.value_col = params.value_col || 'score';   // 始终发，默认 score（情绪得分密度，色深=高分聚集=偏正面）；后端缺该列自动回退纯点密度
    if (params.range) body.range = params.range;
    const pf = normPreFilter(params.pre_filter); if (pf) body.pre_filter = pf;
    try {
      const r = await geoFetch('density', body);
      const feats = (r.geojson && r.geojson.features) || [];
      const _dName = params.as || '情绪核密度';
      const _dL = addResultLayer({
        name: _dName, kind: 'polygon', fc: r.geojson, keep: !!params.keep,
        paint: { fillOn: true, _ui: { tool: 'density', gridField: '_level', gridStops: DENSITY_RAMP, extrusionOpacity: 0.72, mode: '3d', heightField: '_level', maxHeight: 1500 } },
      });
      let hi = 0, md = 0;
      feats.forEach((f) => { const b = (f.properties || {})._band; if (b >= 3) hi++; else if (b === 2) md++; });
      const _wCol = r.weighted_by ? `·按${r.weighted_by}加权` : '·纯点计数';
      const _cellNote = (r.actual_cell_m && r.actual_cell_m > body.cell_size_m) ? `（请求${body.cell_size_m}m超上限，实际${Math.round(r.actual_cell_m)}m）` : '';
      return {
        observation: `核密度(KDE)：${feats.length} 个密度格（bandwidth=${body.bandwidth_m}m·cell=${body.cell_size_m}m${_wCol}）${_cellNote}${r.truncated ? '（已截断）' : ''}，高密度区 ${hi}、中区 ${md} → 已生成图层「${_dName}」${_dL ? '(' + feats.length + '面)' : ''}`,
        data: { count: r.count, layerId: _dL && _dL.id, hi, md, weighted_by: r.weighted_by, actual_cell_m: r.actual_cell_m },
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
