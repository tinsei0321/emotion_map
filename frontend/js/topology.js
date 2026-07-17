// ═══ topology.js — 3D 项目架构拓扑图（3d-force-graph 驱动）═══
// 引擎：3d-force-graph（vasturiano，d3-force-3d + three.js/WebGL，UMD 全局 ForceGraph3D 需 new）
// 数据：GET /api/v1/topo（节点含 layer/maturity/pipelinePos 字段）
// 视觉：4 色系（Claude 橙主 + 蓝青/绿/暖灰）× 3 档深浅（成熟度成片）+ 默认 overview 3D 分层球。

// ── group 顶层目录 → 色系家族（主程序+EMC=橙 / 架构=蓝青 / 数据=绿 / 文档=暖灰）──
const GROUP_FAMILY = {
  frontend: 'primary', core: 'primary', ai_qa: 'primary',
  api: 'infra', apps: 'infra', SCRIPT: 'infra', '.claude': 'infra',
  module: 'infra', pipeline: 'infra',
  DATA: 'data', SCRAPER: 'data',
  docs: 'doc', design: 'doc', tests: 'doc', memories: 'doc',
  root: 'doc', static: 'doc', task: 'doc',
};
const MATURITY_OPACITY = { mature: 1.0, progressing: 0.8, planned: 0.45, paused: 0.3, rejected: 0.3 };
const MATURITY_LABEL = { mature: '成熟', progressing: '推进中', planned: '计划', paused: '搁置', rejected: '否决' };
const LAYER_LABEL = {
  data: '数据层', tool: '工具层·管道', ui: 'UI 层', infra: '基础设施',
  doc: '文档', harness: 'Harness', pipeline: '数据管道 L0→L4', task: '任务路线图', other: '其他', root: '根',
};
const TYPE_LABEL = { file: '文件', dir: '目录', module: '模块', 'pipeline-stage': '管道阶段', task: '任务' };

// ── 7 预设（默认 overview = 3D 分层球 + 成片）──
const PRESETS = {
  overview: { nodeFilter: () => true, linkFilter: () => true, dagMode: null },
  pipeline: {
    nodeFilter: (n) => n.type === 'pipeline-stage'
      || (n.path && (n.path.startsWith('SCRIPT/') || n.path.startsWith('SCRAPER/') || n.path.startsWith('DATA/')))
      || ['MOD_GOV', 'MOD_ANA', 'MOD_REL', 'MOD_PERF', 'MOD_SCRAPER'].includes(n.id),
    linkFilter: (l) => ['pipeline', 'contains', 'import'].includes(l.type),
    dagMode: 'radialout',
  },
  emc: {
    nodeFilter: (n) => (n.path && (n.path.startsWith('ai_qa/') || n.path.startsWith('frontend/js/ai_qa/')))
      || n.id === 'api/aiqa_routes.py' || ['MOD_AIQA', 'MOD_LLM'].includes(n.id),
    linkFilter: (l) => ['import', 'contains', 'route'].includes(l.type),
    dagMode: null,
  },
  agent_skills: {
    nodeFilter: (n) => n.path && (n.path.startsWith('.claude/agents') || n.path.startsWith('.claude/commands')
      || n.path.startsWith('.claude/hooks') || n.path === '.claude/SKILLS_INDEX.md'),
    linkFilter: () => true, dagMode: null,
  },
  roadmap: {
    nodeFilter: (n) => n.type === 'task',
    linkFilter: (l) => l.type === 'contains', dagMode: 'td',
  },
  module: {
    nodeFilter: (n) => n.type === 'module' || !!n.module,
    linkFilter: (l) => l.type === 'owns' || l.type === 'import', dagMode: null,
  },
  files: { nodeFilter: () => true, linkFilter: () => true, dagMode: null },
};

// ── 运行时状态 ──
let _graph = null, _data = null, _curPreset = 'overview', _selectedId = null, _hoveredId = null;
const _highlightNodes = new Set();
const _cssCache = {};

// ══════════════════════════════════════════════════════════════
// 初始化
// ══════════════════════════════════════════════════════════════
async function init() {
  const el = document.getElementById('topo-graph');
  if (typeof ForceGraph3D === 'undefined') {
    el.innerHTML = '<div class="topo-error">[ERR] 3d-force-graph 本地库加载失败（frontend/vendor/3d-force-graph.min.js）。请确认文件存在。</div>';
    return;
  }
  _graph = new ForceGraph3D(el)
    .backgroundColor('#0d1117')
    .nodeRelSize(3.5)
    .nodeLabel(() => '')                       // 禁用内置 tooltip，用自建 #topo-tip 富信息卡
    .nodeColor((n) => colorOf(n))
    .nodeOpacity((n) => opacityOf(n))
    .nodeVal((n) => valOf(n))
    .linkColor((l) => linkColorOf(l))
    .linkWidth((l) => (l.type === 'pipeline' ? 2.5 : l.type === 'contains' ? 0.3 : 0.8))
    .linkOpacity(0.35)
    .linkDirectionalArrowLength((l) => (l.type === 'contains' || l.type === 'owns' ? 0 : 3))
    .linkDirectionalParticles((l) => (l.type === 'pipeline' ? 4 : 0))
    .linkDirectionalParticleWidth(1.5)
    .linkDirectionalParticleSpeed(0.006)
    .onNodeHover((n, prev) => onHover(n, prev))
    .onNodeClick((n) => showDetail(n))
    .onEngineTick(() => updateTipPos())
    .cooldownTicks(150)
    .nodeVisibility((n) => isVisible(n))
    .linkVisibility((l) => linkVisible(l));

  // 尺寸自适应（修 21:9 屏只显示一半 bug：rAF 等布局稳定 + resize 监听）
  const resize = () => { if (_graph) _graph.width(el.clientWidth).height(el.clientHeight); };
  requestAnimationFrame(resize);
  window.addEventListener('resize', resize);

  await load('overview');
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
      `<div class="topo-error">[ERR] 加载拓扑数据失败: ${e.message}<br><br>请确保后端已启动：<code>py frontend/serve.py 8080</code></div>`;
    return;
  }
  // 预处理 neighbors（hover 高亮 + tip 用）
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
// 预设 / 可见性
// ══════════════════════════════════════════════════════════════
function applyPreset() {
  const p = PRESETS[_curPreset] || PRESETS.overview;
  _highlightNodes.clear();
  _hoveredId = null;
  hideTip();
  _graph.dagMode(p.dagMode || null);
  _graph.nodeVisibility((n) => isVisible(n));
  _graph.linkVisibility((l) => linkVisible(l));
  _graph.graphData(_data);   // 触发重布局
  // 力参数：overview 自由球（charge 大松散），dagMode preset 用默认
  if (!p.dagMode) {
    _graph.d3Force('charge').strength(-45);
    _graph.d3Force('link').distance(35);
  }
  setTimeout(() => { try { _graph.zoomToFit(400, 60); } catch (e) { /* noop */ } }, 700);
}

function isVisible(n) {
  return (PRESETS[_curPreset] || PRESETS.overview).nodeFilter(n);
}
function linkVisible(l) {
  const p = PRESETS[_curPreset] || PRESETS.overview;
  const s = typeof l.source === 'object' ? l.source.id : l.source;
  const t = typeof l.target === 'object' ? l.target.id : l.target;
  if (!isVisible({ id: s }) || !isVisible({ id: t })) return false;
  return p.linkFilter(l);
}

// ══════════════════════════════════════════════════════════════
// 节点视觉：颜色（group→家族 + maturity→深浅）/ 透明度 / 大小
// ══════════════════════════════════════════════════════════════
function colorOf(n) {
  const family = GROUP_FAMILY[n.group] || 'doc';
  const mat = n.maturity || 'progressing';
  return resolveCss(`var(--topo-c-${family}-${mat})`);
}
function opacityOf(n) {
  if (_hoveredId && !_highlightNodes.has(n.id)) return 0.1;   // hover 非邻居暗化
  if (_selectedId && _selectedId === n.id) return 1.0;
  const mat = n.maturity || 'progressing';
  return MATURITY_OPACITY[mat] ?? 0.8;
}
function valOf(n) {
  if (n.type === 'dir') return 3;
  if (n.type === 'module') return 5;
  if (n.type === 'pipeline-stage') return 6;
  if (n.type === 'task') return 2;
  const lines = n.lines || 0;
  return Math.max(2, Math.min(9, 1.5 + Math.log2(lines + 1) * 0.7));
}
function linkColorOf(l) {
  if (l.type === 'pipeline') return '#D97757';
  if (l.type === 'route') return '#7DB5C4';
  return '#6E7681';
}

// ══════════════════════════════════════════════════════════════
// 悬停：高亮邻居 + 富信息 tip 卡片（跟随节点屏幕位置）
// ══════════════════════════════════════════════════════════════
function onHover(node, prev) {
  _highlightNodes.clear();
  _hoveredId = node ? node.id : null;
  if (node) {
    _highlightNodes.add(node.id);
    (node.neighbors || []).forEach((nb) => _highlightNodes.add(nb.id));
    showTip(node);
  } else {
    hideTip();
  }
}

function showTip(n) {
  const tip = document.getElementById('topo-tip');
  const mat = n.maturity || 'progressing';
  const fam = GROUP_FAMILY[n.group] || 'doc';
  const matColor = resolveCss(`var(--topo-c-${fam}-${mat})`);
  tip.innerHTML = `
    <div class="tip-name">${esc(n.name)}</div>
    <div class="tip-path">${esc(n.path || '—')}</div>
    <div class="tip-badges">
      <span class="tip-badge mat-${mat}" style="color:${matColor};border-color:${matColor}">${MATURITY_LABEL[mat] || mat}</span>
      ${n.layer ? `<span class="tip-badge">${esc(LAYER_LABEL[n.layer] || n.layer)}</span>` : ''}
      ${n.module ? `<span class="tip-badge">${esc(n.module)}</span>` : ''}
      ${n.pipelinePos ? `<span class="tip-badge">${esc(n.pipelinePos)}</span>` : ''}
    </div>
    ${n.lines ? `<div class="tip-lines">${n.lines} 行${n.fileType ? ' · ' + n.fileType : ''}</div>` : ''}
    ${n.note ? `<div class="tip-lines">${esc(n.note)}</div>` : ''}
  `;
  tip.hidden = false;
  updateTipPos();
}

function updateTipPos() {
  if (!_hoveredId || !_graph) return;
  const node = _data && _data.nodes.find((n) => n.id === _hoveredId);
  if (!node) return;
  const tip = document.getElementById('topo-tip');
  if (tip.hidden) return;
  try {
    const coords = _graph.graph2ScreenCoords(node.x, node.y, node.z);
    const canvas = document.getElementById('topo-graph');
    const rect = canvas.getBoundingClientRect();
    const mainRect = document.getElementById('topo-main').getBoundingClientRect();
    // graph2ScreenCoords 返回相对 canvas 的坐标 → 转 #topo-main 绝对定位
    let x = rect.left - mainRect.left + coords.x + 14;
    let y = rect.top - mainRect.top + coords.y - 8;
    // 边界翻转（防溢出右侧）
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    if (x + tw > mainRect.width - 8) x = rect.left - mainRect.left + coords.x - tw - 14;
    if (y + th > mainRect.height - 8) y = mainRect.height - th - 8;
    if (y < 8) y = 8;
    tip.style.left = x + 'px';
    tip.style.top = y + 'px';
  } catch (e) { /* noop */ }
}

function hideTip() {
  document.getElementById('topo-tip').hidden = true;
}

// ══════════════════════════════════════════════════════════════
// 点击：详情抽屉（docs 区 marked + DOMPurify 渲染 md）
// ══════════════════════════════════════════════════════════════
function showDetail(n) {
  _selectedId = n.id;
  const d = document.getElementById('topo-detail');
  d.hidden = false;
  document.getElementById('td-name').textContent = n.name;
  document.getElementById('td-path').textContent = n.path || '—';
  const rows = [
    ['类型', TYPE_LABEL[n.type] || n.type],
    ['架构层', LAYER_LABEL[n.layer] || n.layer || '—'],
    ['成熟度', MATURITY_LABEL[n.maturity] || n.maturity || '—'],
    ['模块', n.module || '—'],
    ['管线阶段', n.pipelinePos || '—'],
    ['文件类型', n.fileType || '—'],
    ['行数', n.lines != null ? n.lines : '—'],
  ];
  if (n.note) rows.push(['说明', n.note]);
  document.getElementById('td-grid').innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${esc(String(v))}</dd>`).join('');
  renderDocs(n);
}

async function renderDocs(n) {
  const docsEl = document.getElementById('td-docs');
  const docs = n.docs || [];
  if (!docs.length) { docsEl.innerHTML = ''; return; }
  docsEl.innerHTML = '<div class="topo-sec-title" style="margin-top:10px">相关文档</div>';
  for (const doc of docs) {
    const wrap = document.createElement('div');
    wrap.className = 'topo-doc-md';
    wrap.textContent = '加载中…';
    docsEl.appendChild(wrap);
    try {
      const r = await fetch(`../${doc}`);
      const txt = await r.text();
      const html = window.marked ? marked.parse(txt, { gfm: true, breaks: true }) : `<pre>${esc(txt)}</pre>`;
      wrap.innerHTML = window.DOMPurify ? DOMPurify.sanitize(html) : html;
    } catch (e) {
      wrap.textContent = '(加载失败: ' + doc + ')';
    }
  }
}

// ══════════════════════════════════════════════════════════════
// 侧栏渲染
// ══════════════════════════════════════════════════════════════
function renderLegend() {
  const used = new Map();
  _data.nodes.forEach((n) => { used.set(n.layer, (used.get(n.layer) || 0) + 1); });
  const order = ['ui', 'infra', 'tool', 'pipeline', 'data', 'doc', 'harness', 'task', 'other', 'root'];
  document.getElementById('topo-legend-layer').innerHTML = order
    .filter((l) => used.has(l))
    .map((l) => {
      const fam = (l === 'ui' || l === 'infra') ? 'primary' : (l === 'data') ? 'data' : (l === 'tool' || l === 'pipeline' || l === 'harness') ? 'infra' : 'doc';
      const c = resolveCss(`var(--topo-c-${fam}-mature)`);
      return `<li><span class="st" style="background:${c}"></span>${LAYER_LABEL[l] || l} <span class="count">(${used.get(l)})</span></li>`;
    }).join('');
}

function renderLatest() {
  const el = document.getElementById('topo-latest');
  if (!_data.latest) { el.textContent = '—'; return; }
  el.innerHTML = `<b>${_data.latest.id}</b> ${esc(_data.latest.title)}<br><span class="ts">${esc(_data.latest.ts || '')}</span>`;
}

function updateStats() {
  const s = _data.stats || {};
  document.getElementById('topo-stats').textContent =
    `${s.nodes || 0} 节点 / ${s.links || 0} 边`;
}

// ══════════════════════════════════════════════════════════════
// 工具
// ══════════════════════════════════════════════════════════════
function resolveCss(v) {
  if (!v) return '#6E7681';
  if (!v.startsWith('var(')) return v;
  if (_cssCache[v]) return _cssCache[v];
  const m = v.match(/var\((--[\w-]+)\)/);
  if (!m) return '#6E7681';
  const hex = getComputedStyle(document.documentElement).getPropertyValue(m[1]).trim();
  const out = hex || '#6E7681';
  _cssCache[v] = out;
  return out;
}
function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function wireUI() {
  document.querySelectorAll('.topo-preset').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.topo-preset').forEach((b) => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      load(btn.dataset.view);
    });
  });
  document.getElementById('topo-refresh').addEventListener('click', () => load(_curPreset, true));
  document.getElementById('topo-close').addEventListener('click', () => window.close());
  document.getElementById('topo-detail-close').addEventListener('click', () => {
    document.getElementById('topo-detail').hidden = true;
    _selectedId = null;
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.getElementById('topo-detail').hidden = true;
      _selectedId = null;
      _hoveredId = null;
      _highlightNodes.clear();
      hideTip();
    }
  });
}

init();
