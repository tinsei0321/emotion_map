// ═══ data_registry.js — 统一数据注册表（数据元信息唯一真相源）═══
// CB-09 C2 治本：身份/来源/字段元信息原散落 6 处（_layers/srcName·srcId/_registry/
// _fieldCardCache/_srcIndex/layerMeta），无单一真相源 → buildContext 重拼自由文本·不标来源
// → LLM 猜错（"没上传"）+ 推理螺旋。本模块统一为 registry·buildContext 直查 → 接地可靠。
//
// 与 _layers 共存（D3）：registry 管"有什么数据/身份/来源/字段"·_layers（state.js）管"怎么渲染"。
// 不替代 _layers·渲染路径不动·只动元信息/接地路径。
//
// uid = {source}/{hash6}/{ts(ms)}（CB-09 定·可读+去重+跨会话唯一）。
// source ∈ preset|upload|tool|draw（代码路径决定·非 LLM/内容推断·铁律）。

const _registry = new Map();       // uid → entry
const _byLayerId = new Map();      // layerId → uid（渲染层引用·nullable）
const _byDedup = new Map();        // `${source}:${hash}` → uid（去重键）

/** 内容短哈希（6 char base36·去重键·非加密）。采样 count + 前 8 feature 几何类型 + 属性键集 + 末几何·稳定且区分。 */
function _hash(fc) {
  if (!fc || !fc.features || !fc.features.length) return 'empty0';
  const f = fc.features;
  const last = f.length > 8 ? f[f.length - 1] : null;
  const sig = JSON.stringify({
    n: f.length,
    g: f.slice(0, 8).map((x) => (x.geometry && x.geometry.type) || '').join(','),
    k: f.slice(0, 8).map((x) => Object.keys(x.properties || {}).sort().join('|')).join(';'),
    l: last ? ((last.geometry && last.geometry.type) || '') : '',
  });
  let h = 5381;
  for (let i = 0; i < sig.length; i++) h = ((h << 5) + h + sig.charCodeAt(i)) | 0;
  return (h >>> 0).toString(36).padStart(6, '0').slice(-6);
}

function _uid(source, hash) {
  return `${source}/${hash}/${Date.now()}`;
}

/**
 * 注册一个数据条目。所有数据入口（upload/preset/tool/draw）必调。
 * 去重：同 source + 同内容 hash → 复用既有 uid（isDup=true·调用方应跳过 addLayer·不堆叠）。
 * @returns {{uid: string, isDup: boolean}}
 */
export function register({ name, kind, source, fc, layerId = null, parentId = null, toolChain = [] }) {
  const hash = _hash(fc);
  const dedupKey = `${source}:${hash}`;
  const exist = _byDedup.get(dedupKey);
  if (exist) {
    // 去重命中：复用 uid。若新 layerId 不同·补挂（同内容多渲染层共享 uid）。
    if (layerId && !_byLayerId.has(layerId)) _byLayerId.set(layerId, exist);
    return { uid: exist, isDup: true };
  }
  const uid = _uid(source, hash);
  const entry = {
    uid, layerId, name, kind, source, fc,
    fields: null,                  // getFieldCard 结果缓存于此（updateFields）·替代 _fieldCardCache
    hash, createdAt: Date.now(),
    parentId, toolChain: toolChain || [],
    visible: true,
  };
  _registry.set(uid, entry);
  _byDedup.set(dedupKey, uid);
  if (layerId) _byLayerId.set(layerId, uid);
  return { uid, isDup: false };
}

/** 补挂渲染层 id（register 时 layerId 未定·addLayer 后补）。 */
export function attachLayerId(uid, layerId) {
  const e = _registry.get(uid);
  if (!e) return;
  e.layerId = layerId;
  _byLayerId.set(layerId, uid);
}

export function get(uid) { return _registry.get(uid) || null; }
export function getByLayerId(layerId) { const u = _byLayerId.get(layerId); return u ? _registry.get(u) : null; }
export function all() { return Array.from(_registry.values()); }
export function query({ source, kind } = {}) {
  return all().filter((e) =>
    (!source || e.source === source) && (!kind || e.kind === kind));
}

/** 缓存字段元信息（getFieldCard 结果·替代 _fieldCardCache）。 */
export function updateFields(uid, fields) {
  const e = _registry.get(uid);
  if (e) e.fields = fields;
}
export function updateFieldsByLayerId(layerId, fields) {
  const u = _byLayerId.get(layerId);
  if (u) updateFields(u, fields);
}
export function getFields(uid) { const e = _registry.get(uid); return e ? e.fields : null; }
export function getFieldsByLayerId(layerId) { const u = _byLayerId.get(layerId); return u ? getFields(u) : null; }

/** 镜像 _layers.visible（眼睛开关·hidden 也登记·不影响 EMC 可用）。 */
export function setVisible(layerId, visible) {
  const u = _byLayerId.get(layerId);
  if (u) { const e = _registry.get(u); if (e) e.visible = visible; }
}

/** 移除条目（层移除时调·连带清字段缓存 + 反索引）。 */
export function remove(uid) {
  const e = _registry.get(uid);
  if (!e) return;
  _registry.delete(uid);
  _byDedup.delete(`${e.source}:${e.hash}`);
  for (const [lid, u] of _byLayerId) if (u === uid) _byLayerId.delete(lid);
}
export function removeByLayerId(layerId) {
  const u = _byLayerId.get(layerId);
  if (u) remove(u);
}

/** 调试可观测：一行看清全部数据（DeepSeek §2.2 理由4）。 */
export function dump() {
  console.table(all().map((e) => ({ uid: e.uid, name: e.name, kind: e.kind, source: e.source, feats: e.fc && e.fc.features ? e.fc.features.length : 0, visible: e.visible })));
}

/** 重置（测试/换会话）。 */
export function _reset() { _registry.clear(); _byLayerId.clear(); _byDedup.clear(); }
