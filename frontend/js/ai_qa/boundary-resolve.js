// ═══ boundary-resolve.js — boundary 入参归一（preset_id | 中文名 | GeoJSON）═══
// 治 compare/zonal 中文地名↔preset_id 错配（5.115）：LLM 把问句里的"西陵区"当地名填进 boundaries，
// 但 preset 的 id 是英文（admin_district），地名只是该 preset 内 feature 的 nameField 属性值。
// 本模块把中文名解析成单 feature GeoJSON dict（后端 resolve_boundary 已支持 dict 路径），
// 让 compare_regions 复用 zonal_stats 不造 geo 端点（守 emc-compare-skill），与 district-stats.js 同范式。
import { fetchRangePresets, fetchRangePreset } from '../api.js';

// 仅在「面域型」preset 里查地名（情绪对比的对象是行政区/街道/社区/更新单元）。
// 跳过用地型（land_*）—— 那是用地筛选面，不是情绪归因的面域。
const _AREA_PRESET_PREFIXES = ['admin_', 'renewal_'];

let _indexPromise = null;   // 惰性建索引：{ byName: Map(key→feature), ids: Set(preset_id) }

// 行政区划常见尾缀：索引时同时收「全名」与「去尾缀」（西陵区→西陵），兼容用户/LLM 省略尾缀。
function _nameKeys(name) {
  const keys = [name];
  const stripped = name.replace(/(区|街道|社区|镇|乡|村)$/, '');
  if (stripped && stripped !== name) keys.push(stripped);
  return keys;
}

async function _buildIndex() {
  const groups = await fetchRangePresets();
  const items = [];
  for (const g of (groups || [])) for (const it of (g.items || [])) items.push(it);
  const ids = new Set(items.map((it) => it.id));   // 全部 preset_id（直通判定用）
  const areaItems = items.filter((it) =>
    _AREA_PRESET_PREFIXES.some((p) => it.id.startsWith(p)) && it.available !== false);
  const byName = new Map();   // 归一键 → { type:'Feature', geometry, properties:{name} }
  for (const it of areaItems) {
    let res;
    try { res = await fetchRangePreset(it.id); } catch (_) { continue; }   // 该 preset 文件未上传→跳
    if (!res || !res.available || !res.geojson) continue;
    const nf = res.nameField || 'name';
    for (const f of (res.geojson.features || [])) {
      const raw = String((f.properties || {})[nf] ?? '').trim();
      if (!raw || !f.geometry) continue;
      const feat = { type: 'Feature', geometry: f.geometry, properties: { name: raw } };   // 精简属性 + 显式 name（zonal_stats polygon_name_col='name'）
      for (const key of _nameKeys(raw)) {
        if (!byName.has(key)) byName.set(key, feat);   // 首写优先，避同名冲突
      }
    }
  }
  return { byName, ids };
}

function _index() {
  if (!_indexPromise) {
    // 建失败清空，下次调用重试（preset 后上传也能恢复）。
    _indexPromise = _buildIndex().catch((e) => { _indexPromise = null; throw e; });
  }
  return _indexPromise;
}

/** 把 boundary 入参归一为 preset_id(str) | GeoJSON(dict) | 原样。
 *  - 非字符串（已是 GeoJSON dict）/ null → 原样。
 *  - 命中 preset_id → 原样 str（走后端 load_preset）。
 *  - 命中面域 preset 内 feature 名 → 单 feature GeoJSON dict（含 properties.name）。
 *  - 未命中 → 原样交后端（保留报错可观测性，不静默吞）。
 *  模块级缓存：首次 compare 付拉取成本，之后命中内存索引。 */
export async function resolveBoundaryInput(b) {
  if (b == null || typeof b !== 'string') return b;
  let idx;
  try { idx = await _index(); } catch (_) { return b; }   // 索引建失败→原样（不阻断主链）
  if (idx.ids.has(b)) return b;
  const hit = idx.byName.get(b.trim());
  if (hit) return { type: 'FeatureCollection', features: [hit] };
  return b;
}
