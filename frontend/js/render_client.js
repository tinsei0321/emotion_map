// ═══ render_client.js — dsh 显示屏客户端（PT-CB6 P3）═══
// 后端 SSE /api/v1/render/stream 推 render spec → 取数 → 令牌解析（权威在此）→
// 复用现有 addToolboxLayer / defaultPaint / piToNorm 铺层。
// 红线：不改任何既有 js；本文件为纯新增 ES module。
import { addToolboxLayer, defaultPaint } from './toolbox/shared.js';
import { piToNorm, polarityStops } from './grid-tool.js';

const PREFIX = '[dsh] ';

function _attachMeta(layer, spec) {
  if (!layer) return;
  layer.origin = spec.origin || {};
  layer.usage = (spec.caliber_lite && spec.caliber_lite.usage) || '';
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

function _normChoropleth(fc, valueField) {
  return {
    ...fc,
    features: (fc.features || []).map((f) => {
      const props = { ...(f.properties || {}) };
      const raw = props[valueField];
      const num = Number(raw);
      props._grid_norm = (raw != null && raw !== '' && !isNaN(num)) ? piToNorm(num) : 0.5;
      return { ...f, properties: props };
    }),
  };
}

async function _apply(spec) {
  if (!spec || !spec.ui || !spec.ui.name) return;
  const fc = await _loadData(spec);
  if (!fc || !fc.features || !fc.features.length) {
    console.warn('[dsh] render spec 无可渲染数据:', spec.spec_id);
    return;
  }
  const zoom = spec.ui.zoom_to !== false;
  const name = PREFIX + spec.ui.name;
  const kind = spec.kind;

  if (kind === 'point') {
    // 复用现有点层 circle 样式形态（generate_point_layer 同款参数·map.js needsAnalysis 单色分支消费）
    const paint = { _ui: { tool: 'dsh-render' }, radius: 7, color: '#ff9000', opacity: 0.9 };
    const L = addToolboxLayer({ name, kind: 'point', fc, paint, colorMode: 'needsAnalysis', fit: zoom });
    _attachMeta(L, spec);
    return;
  }

  if (kind === 'choropleth') {
    const valueField = (spec.style && spec.style.value_field) || 'polarity_index';
    const normalized = _normChoropleth(fc, valueField);
    let paint = defaultPaint('zonal', 'polygon');
    if (spec.style && spec.style.ramp_hint === 'worst_first') {
      paint = { ...paint, gridStops: polarityStops('overall', undefined, true) };
    }
    const L = addToolboxLayer({ name, kind: 'polygon', fc: normalized, paint, fit: zoom });
    _attachMeta(L, spec);
    return;
  }

  console.warn('[dsh] 未知 spec.kind:', kind);
}

function _connect() {
  const es = new EventSource('/api/v1/render/stream');
  es.addEventListener('spec', (e) => {
    try {
      _apply(JSON.parse(e.data));
    } catch (err) {
      console.warn('[dsh] render spec 解析失败:', err);
    }
  });
  es.onopen = () => console.log('[dsh] render stream 已连接');
  es.onerror = () => console.warn('[dsh] render stream 连接中断（浏览器自动重连）');
}

_connect();
