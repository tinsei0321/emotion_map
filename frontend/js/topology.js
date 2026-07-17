// ═══ topology.js — 项目架构动态拓扑图（force-graph 驱动）═══
// 引擎：force-graph@1.51.0（vasturiano，UMD 全局 ForceGraph，Obsidian graph view 同款 d3-force + Canvas）
// 数据：GET /api/v1/topo?view=（同源 :8080 → serve.py 反代 → :8000 后端实时扫描）
// 同一张图，6 个预设视图按钮切换过滤 + dagMode 布局。

// ── 领域 → CSS 变量（force-graph Canvas 不读 CSS var，运行时 getComputedStyle 解析缓存）──
const DOMAIN_COLORS = {
  frontend: 'var(--topo-domain-frontend)',
  apps: 'var(--topo-domain-apps)',
  core: 'var(--topo-domain-core)',
  SCRIPT: 'var(--topo-domain-SCRIPT)',
  SCRAPER: 'var(--topo-domain-SCRAPER)',
  DATA: 'var(--topo-domain-DATA)',
  api: 'var(--topo-domain-api)',
  ai_qa: 'var(--topo-domain-ai_qa)',
  docs: 'var(--topo-domain-docs)',
  design: 'var(--topo-domain-design)',
  tests: 'var(--topo-domain-tests)',
  '.claude': 'var(--topo-domain-claude)',
  memories: 'var(--topo-domain-default)',
  static: 'var(--topo-domain-default)',
  root: 'var(--topo-domain-root)',
  module: 'var(--topo-domain-module)',
  pipeline: 'var(--topo-domain-pipeline)',
  task: 'var(--topo-domain-task)',
};

const EDGE_COLORS = {
  import: '#58A6FF',
  pipeline: '#D97757',
  route: '#BC8CFF',
  contains: '#30363d',
  owns: '#6E7681',
};

const STATE_LABEL = {
  done: '✅ 完成', progress: '🔄 进行中', todo: '⬜ 待启动',
  milestone: '◆ 架构转折点', paused: '⏸ 搁置', rejected: '❌ 否决',
  unknown: '—',
};
const STATE_COLOR = { done: '#3FB950', progress: '#D29922', todo: '#6E7681', milestone: '#E3B341' };

// ── 6 个预设视图（同一张图，不同 nodeFilter / linkFilter / dagMode）──
const PRESETS = {
  global: {
    nodeFilter: () => true,
    linkFilter: () => true,
    dagMode: null,
  },
  pipeline: {
    nodeFilter: (n) => n.type === 'pipeline-stage'
      || (n.path && (n.path.startsWith('SCRIPT/') || n.path.startsWith('SCRAPER/')
                     || n.path.startsWith('DATA/')))
      || ['MOD_GOV', 'MOD_ANA', 'MOD_REL', 'MOD_PERF', 'MOD_SCRAPER'].includes(n.id),
    linkFilter: (l) => ['pipeline', 'contains', 'import'].includes(l.type),
    dagMode: 'lr',
    dagLevelDistance: 90,
  },
  emc: {
    nodeFilter: (n) => (n.path && (n.path.startsWith('ai_qa/') || n.path.startsWith('frontend/js/ai_qa/')))
      || n.id === 'api/aiqa_routes.py'
      || ['MOD_AIQA', 'MOD_LLM'].includes(n.id),
    linkFilter: (l) => ['import', 'contains', 'route'].includes(l.type),
    dagMode: null,
  },
  agent_skills: {
    nodeFilter: (n) => (n.path && (n.path.startsWith('.claude/agents') || n.path.startsWith('.claude/commands')
                    || n.path.startsWith('.claude/hooks') || n.path === '.claude/SKILLS_INDEX.md')),
    linkFilter: () => true,
    dagMode: null,
  },
  roadmap: {
    nodeFilter: (n) => n.type === 'task',
    linkFilter: (l) => l.type === 'task-parent' || l.type === 'contains',
    dagMode: 'td',
    dagLevelDistance: 60,
  },
  module: {
    nodeFilter: (n) => n.type === 'module' || !!n.module,
    linkFilter: (l) => l.type === 'owns' || l.type === 'import',
    dagMode: null,
  },
};

// ── 运行时状态 ──
let _graph = null;
let _data = null;
let _curPreset = 'global';
let _selectedId = null;
const _collapsed = new Set();           // 折叠的目录 id
const _highlightNodes = new Set();      // hover 高亮集合（空=无高亮）
const _cssCache = {};                   // CSS var → 实际色值缓存

// ══════════════════════════════════════════════════════════════
// 初始化
// ══════════════════════════════════════════════════════════════
async function init() {
  const el = document.getElementById('topo-graph');
  if (typeof ForceGraph === 'undefined') {
    el.innerHTML = `<div class="topo-error">[ERR] force-graph 本地库加载失败（frontend/vendor/force-graph.min.js）。
请确认文件存在且未被损坏。</div>`;
    return;
  }
  _graph = new ForceGraph(el)
    .backgroundColor('#0d1117')
    .nodeRelSize(5)
    .nodeLabel((n) => nodeTooltip(n))
    .nodeCanvasObjectMode(() => 'replace')
    .nodeCanvasObject((n, ctx, scale) => drawNode(n, ctx, scale))
    .nodePointerAreaPaint((n, color, ctx, scale) => paintHitArea(n, color, ctx, scale))
    .linkColor((l) => linkColorOf(l))
    .linkWidth((l) => (l.type === 'pipeline' ? 3 : l.type === 'contains' ? 0.6 : 1.4))
    .linkDirectionalArrowLength((l) => (l.type === 'contains' || l.type === 'owns' ? 0 : 4))
    .linkDirectionalParticles((l) => (l.type === 'pipeline' ? 4 : 0))
    .linkDirectionalParticleWidth(2.2)
    .linkDirectionalParticleSpeed(0.004)
    .onNodeHover((n) => highlightNeighbors(n))
    .onNodeClick((n) => showDetail(n))
    .cooldownTicks(120)
    .nodeVisibility((n) => isVisible(n))
    .linkVisibility((l) => linkVisible(l));

  await load('global');
  wireUI();
}

async function load(view, refresh = false) {
  _curPreset = view;
  document.getElementById('topo-stats').textContent = '加载中…';
  const url = `/api/v1/topo?view=${view}${refresh ? '&refresh=1' : ''}`;
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    _data = await r.json();
  } catch (e) {
    document.getElementById('topo-graph').innerHTML =
      `<div class="topo-error">[ERR] 加载拓扑数据失败: ${e.message}<br><br>` +
      `请确保后端已启动：<code>py frontend/serve.py 8080</code>（自起 uvicorn :8000 + :8080 反代）。</div>`;
    return;
  }
  // 预处理：每个节点挂 neighbors（O(N) 一次，hover 高亮用）
  const idMap = new Map(_data.nodes.map((n) => [n.id, n]));
  _data.nodes.forEach((n) => { n.neighbors = []; });
  _data.links.forEach((l) => {
    const s = idMap.get(typeof l.source === 'object' ? l.source.id : l.source);
    const t = idMap.get(typeof l.target === 'object' ? l.target.id : l.target);
    if (s && t) { s.neighbors.push(t); t.neighbors.push(s); }
  });
  applyPreset();
  renderLegend();
  renderLatest();
  updateStats();
}

// ══════════════════════════════════════════════════════════════
// 预设 / 可见性 / 折叠
// ══════════════════════════════════════════════════════════════
function applyPreset() {
  const p = PRESETS[_curPreset] || PRESETS.global;
  _collapsed.clear();
  _highlightNodes.clear();
  _graph.dagMode(p.dagMode || null);
  if (p.dagLevelDistance) _graph.dagLevelDistance(p.dagLevelDistance);
  _graph.nodeVisibility((n) => isVisible(n));
  _graph.linkVisibility((l) => linkVisible(l));
  _graph.graphData(_data);   // 触发重布局
  setTimeout(() => { try { _graph.zoomToFit(400, 60); } catch (e) { /* noop */ } }, 600);
}

function isVisible(n) {
  const p = PRESETS[_curPreset] || PRESETS.global;
  if (!p.nodeFilter(n)) return false;
  for (const cid of _collapsed) {
    if (n.id !== cid && n.id.startsWith(cid + '/')) return false;
  }
  return true;
}

function linkVisible(l) {
  const p = PRESETS[_curPreset] || PRESETS.global;
  const s = typeof l.source === 'object' ? l.source.id : l.source;
  const t = typeof l.target === 'object' ? l.target.id : l.target;
  if (!isVisible({ id: s }) || !isVisible({ id: t })) return false;
  return p.linkFilter(l);
}

function toggleCollapse(n) {
  if (_collapsed.has(n.id)) _collapsed.delete(n.id);
  else _collapsed.add(n.id);
  _graph.nodeVisibility((nn) => isVisible(nn));
  _graph.linkVisibility((l) => linkVisible(l));
}

function collapseAll(flag) {
  _collapsed.clear();
  if (flag) _data.nodes.forEach((n) => { if (n.type === 'dir') _collapsed.add(n.id); });
  _graph.nodeVisibility((nn) => isVisible(nn));
  _graph.linkVisibility((l) => linkVisible(l));
}

// ══════════════════════════════════════════════════════════════
// 节点绘制（Canvas 自定义：主体圆 + 目录描边 + 状态角标 + 名）
// ══════════════════════════════════════════════════════════════
function drawNode(n, ctx, scale) {
  const isDim = _highlightNodes.size > 0 && !_highlightNodes.has(n.id);
  const isSelected = _selectedId === n.id;
  const r = nodeRadius(n);
  const color = resolveCss(DOMAIN_COLORS[n.group] || 'var(--topo-domain-default)');

  ctx.globalAlpha = isDim ? 0.12 : 1;

  // 选中/hover 光环（Claude 橙）
  if (isSelected || (!isDim && _highlightNodes.has(n.id))) {
    ctx.beginPath();
    ctx.arc(n.x, n.y, r + 4 / scale, 0, 2 * Math.PI);
    ctx.fillStyle = 'rgba(217,119,87,0.25)';
    ctx.fill();
  }

  // 主体圆
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(n.x, n.y, r, 0, 2 * Math.PI);
  ctx.fill();

  // 目录节点描边（折叠=实线 Claude 橙，展开=虚线灰）
  if (n.type === 'dir') {
    ctx.strokeStyle = _collapsed.has(n.id) ? '#D97757' : '#c9d1d9';
    ctx.lineWidth = (_collapsed.has(n.id) ? 1.8 : 1) / scale;
    if (!_collapsed.has(n.id)) ctx.setLineDash([3 / scale, 2 / scale]);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // 状态角标（右上）
  if (n.state && STATE_COLOR[n.state]) {
    const bx = n.x + r * 0.85, by = n.y - r * 0.85, br = Math.max(2.2, r * 0.42);
    if (n.state === 'milestone') {
      ctx.fillStyle = STATE_COLOR.milestone;
      ctx.beginPath();
      ctx.moveTo(bx, by - br); ctx.lineTo(bx + br, by);
      ctx.lineTo(bx, by + br); ctx.lineTo(bx - br, by);
      ctx.closePath(); ctx.fill();
    } else {
      const sc = STATE_COLOR[n.state];
      ctx.fillStyle = n.state === 'todo' ? '#0d1117' : sc;
      ctx.strokeStyle = sc;
      ctx.lineWidth = 1.4 / scale;
      ctx.beginPath(); ctx.arc(bx, by, br, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
    }
  }

  ctx.globalAlpha = 1;

  // 节点名（缩放足够 / 特殊类型才画，避免拥挤）
  if (scale > 1.6 || ['pipeline-stage', 'module', 'task', 'dir'].includes(n.type)) {
    ctx.fillStyle = isDim ? 'rgba(201,209,217,0.3)' : '#c9d1d9';
    ctx.font = `${Math.max(9, 11 / scale)}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    const label = n.type === 'pipeline-stage' ? n.name : shortName(n);
    ctx.fillText(label, n.x, n.y + r + 3 / scale);
  }
}

function nodeRadius(n) {
  if (n.type === 'dir') return 6;
  if (n.type === 'module') return 7;
  if (n.type === 'pipeline-stage') return 8;
  if (n.type === 'task') return 5;
  // file：按行数微调（10–80 行→3–6）
  const lines = n.lines || 0;
  return Math.max(2.5, Math.min(7, 2.5 + Math.log2(lines + 1) * 0.6));
}

function paintHitArea(n, color, ctx, scale) {
  const r = nodeRadius(n) + 4;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(n.x, n.y, r, 0, 2 * Math.PI);
  ctx.fill();
}

function shortName(n) {
  const p = n.name || n.id;
  return p.length > 22 ? p.slice(0, 20) + '…' : p;
}

function nodeTooltip(n) {
  let s = `${n.name}`;
  if (n.module) s += ` · ${n.module}`;
  if (n.lines) s += ` · ${n.lines} 行`;
  if (n.state && STATE_LABEL[n.state]) s += ` · ${STATE_LABEL[n.state]}`;
  return s;
}

function linkColorOf(l) {
  const base = EDGE_COLORS[l.type] || '#6E7681';
  if (_highlightNodes.size === 0) return base;
  const s = typeof l.source === 'object' ? l.source.id : l.source;
  const t = typeof l.target === 'object' ? l.target.id : l.target;
  return (_highlightNodes.has(s) && _highlightNodes.has(t)) ? base : '#1a2029';
}

// ══════════════════════════════════════════════════════════════
// 交互：hover 高亮 / click 详情
// ══════════════════════════════════════════════════════════════
function highlightNeighbors(n) {
  _highlightNodes.clear();
  if (n) {
    _highlightNodes.add(n.id);
    (n.neighbors || []).forEach((nb) => _highlightNodes.add(nb.id));
  }
}

function showDetail(n) {
  _selectedId = n.id;
  const d = document.getElementById('topo-detail');
  d.hidden = false;
  document.getElementById('td-name').textContent = n.name;
  document.getElementById('td-path').textContent = n.path || '—';
  const typeLabel = {
    file: '文件', dir: '目录', module: '模块', 'pipeline-stage': '管道阶段', task: '任务',
  }[n.type] || n.type;
  const rows = [
    ['类型', typeLabel],
    ['领域', n.group || '—'],
    ['模块', n.module || '—'],
    ['状态', STATE_LABEL[n.state] || '—'],
    ['文件类型', n.fileType || '—'],
    ['行数', n.lines != null ? n.lines : '—'],
  ];
  if (n.note) rows.push(['说明', n.note]);
  document.getElementById('td-grid').innerHTML =
    rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
  const docsEl = document.getElementById('td-docs');
  docsEl.innerHTML = (n.docs || []).length
    ? '<div class="topo-sec-title" style="margin-top:8px">相关文档</div>' +
      n.docs.map((doc) => `<a href="../${doc}" target="_blank">${doc}</a>`).join('<br>')
    : '';
  // 目录节点显示折叠按钮
  const colBtn = document.getElementById('td-collapse');
  colBtn.hidden = n.type !== 'dir';
  if (n.type === 'dir') {
    colBtn.textContent = _collapsed.has(n.id) ? '▸ 展开此目录' : '▾ 折叠此目录';
    colBtn.onclick = () => { toggleCollapse(n); showDetail(n); };
  }
}

// ══════════════════════════════════════════════════════════════
// 侧栏渲染（图例 / 最新动态 / 统计）
// ══════════════════════════════════════════════════════════════
function renderLegend() {
  const used = new Map();
  _data.nodes.forEach((n) => { if (!used.has(n.group)) used.set(n.group, 0); used.set(n.group, used.get(n.group) + 1); });
  const order = [...used.entries()].sort((a, b) => b[1] - a[1]);
  document.getElementById('topo-legend-domain').innerHTML = order.map(([g, cnt]) => {
    const cssVar = DOMAIN_COLORS[g] || 'var(--topo-domain-default)';
    return `<li><span class="st" style="background:${resolveCss(cssVar)}"></span>${g} <span style="color:var(--topo-text-muted)">(${cnt})</span></li>`;
  }).join('');
}

function renderLatest() {
  const el = document.getElementById('topo-latest');
  if (!_data.latest) { el.textContent = '—'; return; }
  el.innerHTML = `<b>${_data.latest.id}</b> ${_data.latest.title}<br><span class="ts">${_data.latest.ts || ''}</span>`;
}

function updateStats() {
  const s = _data.stats || {};
  const cacheHit = _data.cache && _data.cache.hit;
  document.getElementById('topo-stats').innerHTML =
    `${s.nodes || 0} 节点 / ${s.links || 0} 边` +
    (cacheHit ? ' <span class="cache-hit">(cache)</span>' : '');
}

// ══════════════════════════════════════════════════════════════
// 工具：CSS var → 实际色值（缓存）
// ══════════════════════════════════════════════════════════════
function resolveCss(v) {
  if (!v) return '#8b949e';
  if (!v.startsWith('var(')) return v;
  if (_cssCache[v]) return _cssCache[v];
  const m = v.match(/var\((--[\w-]+)\)/);
  if (!m) return '#8b949e';
  const hex = getComputedStyle(document.documentElement).getPropertyValue(m[1]).trim();
  const out = hex || '#8b949e';
  _cssCache[v] = out;
  return out;
}

// ══════════════════════════════════════════════════════════════
// UI 绑定
// ══════════════════════════════════════════════════════════════
function wireUI() {
  document.querySelectorAll('.topo-preset').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.topo-preset').forEach((b) => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      document.getElementById('topo-collapse-all').checked = false;
      load(btn.dataset.view);
    });
  });
  document.getElementById('topo-refresh').addEventListener('click', () => load(_curPreset, true));
  document.getElementById('topo-close').addEventListener('click', () => window.close());
  document.getElementById('topo-detail-close').addEventListener('click', () => {
    document.getElementById('topo-detail').hidden = true;
    _selectedId = null;
  });
  document.getElementById('topo-collapse-all').addEventListener('change', (e) => collapseAll(e.target.checked));
  // ESC 关详情
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.getElementById('topo-detail').hidden = true;
      _selectedId = null;
      _highlightNodes.clear();
    }
  });
}

init();
