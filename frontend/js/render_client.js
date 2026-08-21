// ═══ render_client.js — dsh 显示屏客户端（PT-CB6 P + P+）═══
// 后端 SSE /api/v1/render/stream 推 render spec → 取数 → scheme 受管样式解析（权威在此）→
// 复用现有 addToolboxLayer / defaultPaint 铺层。
// 红线：不改任何既有 js；本文件为纯新增 ES module。
import { addToolboxLayer, countNorm } from './toolbox/shared.js';
import { getLayers, removeLayer, HEATMAP_RAMPS } from './state.js';
import { removeLayerFromMap } from './map.js';
import { countStops, piToNorm, polarityStops } from './grid-tool.js';

const PREFIX = '[dsh] ';
// 同一页面会话内按 spec_id 去重：SSE 断线重连会重放 backlog，若不去重会导致
// 同一批图层反复“删除→重建→缩放”，表现为图层在 8~9 个之间循环跳动。
const _seenSpecIds = new Set();
const SCHEMES = {
  // sequential 计数着色（复用社区面按件数分层机制：_count_norm + countStops·勿用 piToNorm）
  community_choropleth_v1: 'community_choropleth_v1',
  // 点层 circle 样式照旧（needsAnalysis 单色橙）
  point_default_v1: 'point_default_v1',
  // 范围/边界面层：浅填充描边（defaultPaint 非 zonal 兜底同款·非数据编码）
  boundary_fill_v1: 'boundary_fill_v1',
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

/** 计数型 sequential 归一：每 feature 写 _count_norm（C2-3：公式单源 shared.js countNorm·与 buildZonalFc 同款）。 */
function _normCommunityCount(fc, valueField) {
  let max = 0;
  for (const f of (fc.features || [])) {
    const n = Number((f.properties || {})[valueField]) || 0;
    if (n > max) max = n;
  }
  // PT-CB11 B3-6 全零可观测：归一恒零即告警（字段断裂嫌疑=properties 缺该字段/字段名错配/真全零）——下次断裂 30 秒定位
  if ((fc.features || []).length && max === 0) {
    console.warn('[dsh] choropleth 归一全零（字段断裂嫌疑）: value_field =', valueField,
      '| 要素数 =', fc.features.length, '| 请核对要素 properties 是否含此字段（值缺失/字段名错配）');
  }
  return {
    ...fc,
    features: (fc.features || []).map((f) => {
      const props = { ...(f.properties || {}) };
      const n = Number(props[valueField]) || 0;
      props._count_norm = countNorm(n, max);
      return { ...f, properties: props };
    }),
  };
}

/** PT-CB7 T1：铺新层前移除所有 [dsh] 前缀既有层（治异名 spec 叠层残留）。
 *  移除失败仅 log 不阻塞新层铺设（A9：具体捕获+console.warn，不静默吞错）。 */
function _clearDshLayers() {
  let removed = 0;
  for (const l of getLayers()) {
    if (typeof l.name !== 'string' || !l.name.startsWith(PREFIX)) continue;
    try {
      removeLayerFromMap(l.id);
      removeLayer(l.id);
      removed += 1;
    } catch (err) {
      console.warn('[dsh] 图层清理单项失败（继续铺新层）:', l.name, err);
    }
  }
  return removed;
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

  // PT-CB7 T1：同会话内 [dsh] 图层只保留最新一张（D-R1 语义裁定·见主执行前审计）
  _clearDshLayers();

  if (scheme === SCHEMES.point_default_v1) {
    const paint = { _ui: { tool: 'dsh-render' }, radius: 7, color: '#ff9000', opacity: 0.9 };
    const L = addToolboxLayer({ name, kind: 'point', fc, paint, colorMode: 'needsAnalysis', fit: zoom });
    _attachMeta(L, spec);
    return;
  }

  if (scheme === SCHEMES.boundary_fill_v1) {
    // 范围/边界面：浅填充描边（与 defaultPaint('', 'polygon') 兜底同款·不渲染数据编码）
    const paint = { fillOn: true, lineWidth: 2, fillOpacity: 0.2 };
    const L = addToolboxLayer({ name, kind: 'polygon', fc, paint, fit: zoom });
    _attachMeta(L, spec);
    return;
  }

  if (scheme === SCHEMES.community_choropleth_v1) {
    const valueField = (spec.style && spec.style.value_field) || 'point_count';
    const isPolarity = valueField.includes('polarity') || valueField === 'score_mean';
    // PT-CB11 C3②：语义 + rampKey 透传——参数面板色带编辑器据此分组排序/如实回显当前色带。
    const rampHint = (spec.style && spec.style.ramp_hint) || '';
    const rampKey = HEATMAP_RAMPS[rampHint] ? rampHint : '';
    let normalized;
    let paint;
    if (isPolarity) {
      normalized = {
        ...fc,
        features: (fc.features || []).map((f) => {
          const props = { ...(f.properties || {}) };
          const pi = Number(props[valueField]);
          props._grid_norm = (pi != null && !Number.isNaN(pi)) ? piToNorm(pi) : 0.5;
          return { ...f, properties: props };
        }),
      };
      // PT-CB8 F4 修复：显式构造纯样式画笔（禁 _ui.tool 标记）——borrowed defaultPaint('zonal') 带
      // 「zonal 工具归属」标记会把要素按钮点击路由进 zonal 分析对话框（该层无分析上下文→空面板）。
      // gridField/gridStops 保留（数据驱动着色·与工具归属无关）。
      paint = { fillOn: true, fillOpacity: 0.72, lineWidth: 1, lineOpacity: 0.6,
                gridField: '_grid_norm',
                gridStops: polarityStops('overall', rampKey || undefined) || [],
                semantic: 'polarity', ...(rampKey ? { rampKey } : {}), valueField };   // valueField：B3-4 悬停 tip 取原始值字段名
    } else {
      normalized = _normCommunityCount(fc, valueField);
      // PT-CB8 色板透传：spec.style.ramp_hint 命中受管词表（HEATMAP_RAMPS）则用之，
      // 否则回落默认 grid-warm（countStops 默认反转·低浅高深）。面板手选色带由此通道生效。
      const palette = HEATMAP_RAMPS[rampHint] ? rampHint : '';
      paint = { fillOn: true, fillOpacity: 0.72, lineWidth: 1, lineOpacity: 0.6,
                gridField: '_count_norm', gridStops: countStops(palette), zeroIsNoData: true,
                semantic: 'count', ...(palette ? { rampKey: palette } : {}), valueField };   // valueField：B3-4 悬停 tip 取原始值字段名
    }


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

// ── PT-CB11 A-4b/A-4c：版本角标 + 服务更新横幅 ─────────────────────
//  A-4b：fetch /api/v1/version → #map 左下角（左下控件上方）v<commit前7位> 小字角标；
//        服务不可达/无 commit 静默降级不显示（A9：catch 即退·不 warn 刷屏）。
//  A-4c：commit 与 localStorage 上次记录不同 → 黄底横幅「服务已更新·建议硬刷新」，
//        点击关闭；首访只记录不打扰。
async function _initVersionBadge() {
  let info;
  try {
    const r = await fetch('/api/v1/version');
    info = await r.json();
  } catch (err) {
    return;   // 静默降级（后端未起/端点不存在）
  }
  if (!info || !info.commit) return;

  const mapEl = document.getElementById('map');
  if (mapEl && !document.getElementById('emc-version-badge')) {
    const b = document.createElement('div');
    b.id = 'emc-version-badge';
    b.textContent = `v${String(info.commit).slice(0, 7)}`;
    b.title = `commit ${info.commit} · 分支 ${info.branch || '?'} · 启动 ${info.startup || '?'}`;
    b.style.cssText = 'position:absolute;left:10px;bottom:96px;z-index:12;'
      + 'font:10px/1.5 ui-monospace,Consolas,monospace;color:#5a6b7e;'
      + 'background:rgba(255,255,255,0.72);padding:1px 6px;border-radius:3px;';
    mapEl.appendChild(b);
  }

  const KEY = 'emc_version_commit';
  const prev = localStorage.getItem(KEY);
  if (prev !== info.commit) {
    if (prev !== null && !document.getElementById('emc-version-banner')) {
      const bar = document.createElement('div');
      bar.id = 'emc-version-banner';
      bar.textContent = '服务已更新·建议硬刷新（Ctrl+Shift+R）';
      bar.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:9999;'
        + 'background:#fff3cd;color:#664d03;text-align:center;cursor:pointer;'
        + 'font:13px/34px system-ui,sans-serif;';
      bar.addEventListener('click', () => bar.remove());
      document.body.appendChild(bar);
    }
    localStorage.setItem(KEY, info.commit);
  }
}

_initVersionBadge();
