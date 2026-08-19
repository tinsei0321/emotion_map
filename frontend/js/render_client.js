// ═══ render_client.js — dsh 显示屏客户端（PT-CB6 P + P+）═══
// 后端 SSE /api/v1/render/stream 推 render spec → 取数 → scheme 受管样式解析（权威在此）→
// 复用现有 addToolboxLayer / defaultPaint 铺层。
// 红线：不改任何既有 js；本文件为纯新增 ES module。
import { addToolboxLayer, defaultPaint } from './toolbox/shared.js';

const PREFIX = '[dsh] ';
// 同一页面会话内按 spec_id 去重：SSE 断线重连会重放 backlog，若不去重会导致
// 同一批图层反复“删除→重建→缩放”，表现为图层在 8~9 个之间循环跳动。
const _seenSpecIds = new Set();
const SCHEMES = {
  // sequential 计数着色（复用社区面按件数分层机制：_count_norm + countStops·勿用 piToNorm）
  community_choropleth_v1: 'community_choropleth_v1',
  // 点层 circle 样式照旧（needsAnalysis 单色橙）
  point_default_v1: 'point_default_v1',
};

function _resolveScheme(spec) {
  const style = spec.style || {};
  if (style.scheme) return style.scheme;
  // 旧 token 字段兼容读（不再产出）
  if (style.token === 'point') return SCHEMES.point_default_v1;
  if (style.token === 'choropleth') return SCHEMES.community_choropleth_v1;
  return '';
}

function _attachMeta(layer, spec) {
  if (!layer) return;
  layer.origin = spec.origin || {};
  layer.usage = (spec.caliber_lite && spec.caliber_lite.usage) || '';
  layer.data_nature = (spec.caliber_lite && spec.caliber_lite.data_nature) || '';
  if (layer.usage === 'analysis_output') {
    console.warn(`[dsh] 「${spec.ui && spec.ui.name}」为结论层（analysis_output）——仅显示·禁作分析输入`);
  }
}

async function _loadData(spec) {
  const data = spec.data || {};
  if (data.dataset_id) {
    const r = await fetch('/api/v1/render/dataset/' + encodeURIComponent(data.dataset_id));
    const j = await r.json();
    if (!j || !j.ok) {
      console.warn('[dsh] dataset 取数失败:', data.dataset_id, (j && j.hint) || '');
      return null;
    }
    return j.geojson;
  }
  if (data.geojson) return data.geojson;
  return null;
}

/** 计数型 sequential 归一：每 feature 写 _count_norm = log1p(count)/log1p(max)。 */
function _normCommunityCount(fc, valueField) {
  let max = 0;
  for (const f of (fc.features || [])) {
    const n = Number((f.properties || {})[valueField]) || 0;
    if (n > max) max = n;
  }
  const denom = Math.log1p(max) || 1;
  return {
    ...fc,
    features: (fc.features || []).map((f) => {
      const props = { ...(f.properties || {}) };
      const n = Number(props[valueField]) || 0;
      props._count_norm = Math.log1p(n) / denom;
      return { ...f, properties: props };
    }),
  };
}

async function _apply(spec) {
  if (!spec || !spec.ui || !spec.ui.name) return;
  const scheme = _resolveScheme(spec);
  if (!SCHEMES[scheme]) {
    console.warn('[dsh] 未知 scheme 拒渲染:', scheme, '词表:', Object.keys(SCHEMES).join(','));
    return;
  }

  const fc = await _loadData(spec);
  if (!fc || !fc.features || !fc.features.length) {
    console.warn('[dsh] render spec 无可渲染数据:', spec.spec_id);
    return;
  }

  const zoom = spec.ui.zoom_to !== false;
  const nature = (spec.caliber_lite && spec.caliber_lite.data_nature) || 'real';
  const natureBadge = nature === 'demo' ? '[演示] ' : (nature === 'real' ? '[真实] ' : '');
  const name = PREFIX + natureBadge + spec.ui.name;

  if (scheme === SCHEMES.point_default_v1) {
    const paint = { _ui: { tool: 'dsh-render' }, radius: 7, color: '#ff9000', opacity: 0.9 };
    const L = addToolboxLayer({ name, kind: 'point', fc, paint, colorMode: 'needsAnalysis', fit: zoom });
    _attachMeta(L, spec);
    return;
  }

  if (scheme === SCHEMES.community_choropleth_v1) {
    const valueField = (spec.style && spec.style.value_field) || 'point_count';
    const normalized = _normCommunityCount(fc, valueField);
    const paint = defaultPaint('zonal', 'polygon', 'count');
    const L = addToolboxLayer({ name, kind: 'polygon', fc: normalized, paint, fit: zoom });
    _attachMeta(L, spec);
    return;
  }
}

function _connect() {
  const es = new EventSource('/api/v1/render/stream');
  es.addEventListener('spec', (e) => {
    try {
      const spec = JSON.parse(e.data);
      if (!spec || !spec.spec_id || _seenSpecIds.has(spec.spec_id)) return;
      _seenSpecIds.add(spec.spec_id);
      _apply(spec);
    } catch (err) {
      console.warn('[dsh] render spec 解析失败:', err);
    }
  });
  es.onopen = () => console.log('[dsh] render stream 已连接');
  es.onerror = () => console.warn('[dsh] render stream 连接中断（浏览器自动重连）');
}

_connect();
