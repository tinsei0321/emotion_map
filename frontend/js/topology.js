// ═══ topology.js — 3D 项目架构拓扑图（自建标签层版，弃 CSS2DRenderer 避累积 bug）═══
// 标签：自建 #topo-labels DOM + graph2ScreenCoords 锚定（切 preset 清空重建，无累积）
import * as THREE from '../vendor/three.module.js';

const GROUP_FAMILY = {
  frontend: 'primary', core: 'primary', ai_qa: 'primary',
  api: 'infra', apps: 'infra', SCRIPT: 'infra', '.claude': 'infra',
  module: 'infra', pipeline: 'infra',
  DATA: 'data', SCRAPER: 'data',
  docs: 'doc', design: 'doc', tests: 'doc', memories: 'doc',
  root: 'doc', static: 'doc', task: 'doc',
};
const MATURITY_LABEL = { mature: '成熟', progressing: '推进中', planned: '计划', paused: '搁置', rejected: '否决' };
const LAYER_LABEL = {
  data: '数据层', tool: '工具层·管道', ui: 'UI 层', infra: '基础设施',
  doc: '文档', harness: 'Harness', pipeline: '数据管道 L0→L4', task: '任务路线图', other: '其他', root: '根',
};
const TYPE_LABEL = { file: '文件', dir: '目录', module: '模块', 'pipeline-stage': '管道阶段', task: '任务' };

const PRESETS = {
  overview: { nodeFilter: () => true, linkFilter: () => true, dagMode: null },
  pipeline: {
    nodeFilter: (n) => n.type === 'pipeline-stage'
      || (n.path && (n.path.startsWith('SCRIPT/') || n.path.startsWith('SCRAPER/') || n.path.startsWith('DATA/')))
      || ['MOD_GOV', 'MOD_ANA', 'MOD_REL', 'MOD_PERF', 'MOD_SCRAPER'].includes(n.id),
    linkFilter: (l) => ['pipeline', 'pipeline-dep', 'import'].includes(l.type), dagMode: 'radialout',
  },
  emc: {
    nodeFilter: (n) => (n.path && (n.path.startsWith('ai_qa/') || n.path.startsWith('frontend/js/ai_qa/')))
      || n.id === 'api/aiqa_routes.py' || ['MOD_AIQA', 'MOD_LLM'].includes(n.id),
    linkFilter: (l) => ['import', 'route'].includes(l.type), dagMode: null,
  },
  agent_skills: {
    nodeFilter: (n) => n.path && (n.path.startsWith('.claude/agents') || n.path.startsWith('.claude/commands')
      || n.path.startsWith('.claude/hooks') || n.path === '.claude/SKILLS_INDEX.md'),
    linkFilter: () => true, dagMode: null,
  },
  roadmap: { nodeFilter: (n) => n.type === 'task', linkFilter: (l) => ['task-dep'].includes(l.type), dagMode: 'td' },
  module: { nodeFilter: (n) => n.type === 'module' || !!n.module, linkFilter: (l) => ['owns', 'import'].includes(l.type), dagMode: null },
  files: { nodeFilter: () => true, linkFilter: (l) => l.type !== 'contains', dagMode: null },
};

let _graph = null, _data = null, _curPreset = 'overview', _selectedId = null, _hoveredId = null, _loaded = false;
let _legendLock = null, _legendHover = null;
let _lastClick = { id: null, t: 0 };
let _labelNodes = [];
const _cssCache = {};

async function init() {
  const el = document.getElementById('topo-graph');
  if (typeof ForceGraph3D === 'undefined' || typeof THREE === 'undefined') {
    el.innerHTML = '<div class="topo-error">[ERR] 3d-force-graph 或 three.js 加载失败。请确认 frontend/vendor/ 下库存在。</div>';
    return;
  }
  _graph = new ForceGraph3D(el)
    .backgroundColor('#0d1117')
    .nodeThreeObjectExtend(false)
    .nodeThreeObject((n) => buildNode(n))
    .nodeLabel(() => '')
    .linkColor(() => '#ffffff')
    .linkWidth((l) => (l.type === 'pipeline' ? 2.5 : 0))
    .linkOpacity(0.5)
    .linkVisibility((l) => l.type !== 'contains' && linkVisible(l))
    .linkDirectionalParticles((l) => (l.type === 'pipeline' ? 4 : 0))
    .linkDirectionalParticleWidth(1.5)
    .linkDirectionalParticleSpeed(0.006)
    .linkMaterial((l) => (l.style === 'dashed'
      ? new THREE.LineDashedMaterial({ color: 0xffffff, dashSize: 2, gapSize: 1.2, transparent: true, opacity: 0.42 })
      : null))
    .linkPositionUpdate((lineObj, opts, l) => {
      if (l.style === 'dashed') {
        lineObj.geometry.setFromPoints([opts.start, opts.end]);
        lineObj.computeLineDistances();
        return true;
      }
      return false;
    })
    .onNodeHover((n, prev) => onHover(n, prev))
    .onNodeClick((n) => onNodeClick(n))
    .onBackgroundClick(() => onBackgroundClick())
    .onEngineTick(() => { updateTipPos(); updateLabels(); })
    .cooldownTicks(150)
    .nodeVisibility((n) => isVisible(n));

  const scene = _graph.scene();
  scene.add(new THREE.AmbientLight(0xffffff, 0.65));
  const dl = new THREE.DirectionalLight(0xffffff, 0.85); dl.position.set(200, 400, 200); scene.add(dl);

  const resize = () => { if (_graph) _graph.width(el.clientWidth).height(el.clientHeight); };
  requestAnimationFrame(resize);
  window.addEventListener('resize', resize);

  await load('overview');
  wireUI();
}

// ═══ 节点几何（只球 mesh，标签在自建 DOM 层）═══
function buildNode(n) {
  const color = colorOf(n);
  const r = nodeRadius(n);
  const core = isCore(n);
  if (n.maturity === 'mature') {
    return new THREE.Mesh(new THREE.SphereGeometry(r, 18, 14),
      new THREE.MeshStandardMaterial({ color, metalness: core ? 0.6 : 0.25, roughness: core ? 0.3 : 0.55 }));
  } else if (n.maturity === 'progressing') {
    return new THREE.Mesh(new THREE.IcosahedronGeometry(r, 0),
      new THREE.MeshBasicMaterial({ color, wireframe: true }));
  } else if (n.maturity === 'planned') {
    return new THREE.Mesh(new THREE.IcosahedronGeometry(r * 0.85, 0),
      new THREE.MeshBasicMaterial({ color, wireframe: true, transparent: true, opacity: 0.5 }));
  }
  return new THREE.Mesh(new THREE.SphereGeometry(r, 12, 10),
    new THREE.MeshStandardMaterial({ color, transparent: true, opacity: 0.5 }));
}
function nodeRadius(n) {
  let r;
  if (n.type === 'dir') r = 6;
  else if (n.type === 'module') r = 11;
  else if (n.type === 'pipeline-stage') r = 13;
  else if (n.type === 'task') r = 4;
  else r = Math.max(3.5, Math.min(9, 2 + Math.log2((n.lines || 0) + 1) * 0.9));
  if (isCore(n)) r *= 1.25;
  return r;
}
function isCore(n) {
  return ['module', 'pipeline-stage'].includes(n.type) || (n.inDegree || 0) >= 5;
}
function showLabel(n) {
  // 只核心节点常显字（module/pipeline-stage + 高入度）；其余 hover/click 的 #topo-tip 显示
  return ['module', 'pipeline-stage'].includes(n.type) || (n.inDegree || 0) >= 8;
}
function colorOf(n) {
  return resolveCss(`var(--topo-c-${GROUP_FAMILY[n.group] || 'doc'})`);
}
function shortName(n) {
  const p = n.name || n.id;
  return p.length > 22 ? p.slice(0, 20) + '…' : p;
}

// ═══ 自建标签层（#topo-labels DOM + graph2ScreenCoords 锚定，切 preset 清空重建避累积）═══
function renderLabels() {
  const cont = document.getElementById('topo-labels');
  if (!cont || !_data) return;
  cont.innerHTML = '';
  _labelNodes = _data.nodes.filter((n) => showLabel(n));
  _labelNodes.forEach((n) => {
    const div = document.createElement('div');
    div.className = 'node-label' + (isCore(n) ? ' is-core' : '');
    div.textContent = shortName(n);
    div.style.display = 'none';
    cont.appendChild(div);
    n._labelDiv = div;
  });
}
function updateLabels() {
  if (!_graph || !_labelNodes.length) return;
  _labelNodes.forEach((n) => {
    const div = n._labelDiv;
    if (!div) return;
    if (!isVisible(n)) { div.style.display = 'none'; return; }
    try {
      const co = _graph.graph2ScreenCoords(n.x, n.y, n.z);
      div.style.display = 'block';
      div.style.left = co.x + 'px';
      div.style.top = (co.y - 10) + 'px';
    } catch (e) { div.style.display = 'none'; }
  });
}

// ═══ load / preset ═══
async function load(view, refresh = false) {
  if (refresh) { location.reload(); return; }
  _curPreset = view;
  document.getElementById('topo-stats').textContent = '加载中…';
  const url = `/api/v1/topo?view=${view}`;
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    _data = await r.json();
  } catch (e) {
    document.getElementById('topo-graph').innerHTML =
      `<div class="topo-error">[ERR] 加载拓扑数据失败: ${e.message}<br><br>请确保后端已启动：<code>py frontend/serve.py 8080</code></div>`;
    return;
  }
  const idMap = new Map(_data.nodes.map((n) => [n.id, n]));
  _data.nodes.forEach((n) => { n.neighbors = []; });
  _data.links.forEach((l) => {
    const s = idMap.get(typeof l.source === 'object' ? l.source.id : l.source);
    const t = idMap.get(typeof l.target === 'object' ? l.target.id : l.target);
    if (s && t) { s.neighbors.push(t); t.neighbors.push(s); }
  });
  if (!_loaded) { _graph.graphData(_data); _loaded = true; }
  applyPreset();
  renderLegend();
  renderLatest();
  updateStats();
  bindLegendItems();
}
function applyPreset() {
  const p = PRESETS[_curPreset] || PRESETS.overview;
  _legendLock = null; _legendHover = null; _hoveredId = null;
  hideTip();
  _graph.dagMode(p.dagMode || null);
  _graph.nodeVisibility((n) => isVisible(n));
  _graph.linkVisibility((l) => l.type !== 'contains' && linkVisible(l));
  _graph.d3VelocityDecay(0.35);
  if (!p.dagMode) {
    _graph.d3Force('charge').strength(-42);
    _graph.d3Force('link').distance(52);
  }
  _graph.d3ReheatSimulation();
  renderLabels();
  setTimeout(() => { try { _graph.zoomToFit(400, 60); } catch (e) {} }, 900);
}
function isVisible(n) { return (PRESETS[_curPreset] || PRESETS.overview).nodeFilter(n); }
function linkVisible(l) {
  const p = PRESETS[_curPreset] || PRESETS.overview;
  const s = typeof l.source === 'object' ? l.source.id : l.source;
  const t = typeof l.target === 'object' ? l.target.id : l.target;
  if (!isVisible({ id: s }) || !isVisible({ id: t })) return false;
  return p.linkFilter(l);
}

// ═══ hover / click / 空白 ═══
function onHover(node, prev) {
  if (prev && prev.__threeObj) prev.__threeObj.scale.set(1, 1, 1);
  _hoveredId = node ? node.id : null;
  if (node && node.__threeObj) node.__threeObj.scale.set(1.6, 1.6, 1.6);
  if (node) showTip(node); else hideTip();
}
function onNodeClick(n) {
  const now = Date.now();
  if (_lastClick.id === n.id && now - _lastClick.t < 300) {
    _lastClick = { id: null, t: 0 };
    zoomToCluster(n);
  } else {
    _lastClick = { id: n.id, t: now };
    showDetail(n);
  }
}
function zoomToCluster(n) {
  const key = n.module || n.group || n.layer;
  if (!key) return;
  _graph.zoomToFit(800, 80, (nn) => (nn.module || nn.group || nn.layer) === key);
}
function onBackgroundClick() {
  document.getElementById('topo-detail').hidden = true;
  _selectedId = null;
  if (_legendLock) { _legendLock = null; applyLegendHighlight(); updateLegendLockCSS(); }
}

// ═══ 图例高亮 ═══
function applyLegendHighlight() {
  if (!_data) return;
  const active = _legendLock || _legendHover;
  _data.nodes.forEach((n) => {
    const obj = n.__threeObj;
    if (!obj) return;
    const match = active && matchLegend(n, active);
    obj.traverse((o) => {
      if (o.material) {
        o.material.transparent = !match || !!_hoveredId;
        o.material.opacity = match ? 1 : (active ? 0.1 : 1);
      }
    });
    if (!(_hoveredId && n.id === _hoveredId)) {
      obj.scale.set(match ? 1.3 : 1, match ? 1.3 : 1, match ? 1.3 : 1);
    }
  });
}
function matchLegend(n, active) {
  if (active.kind === 'layer') return n.layer === active.val;
  if (active.kind === 'maturity') return n.maturity === active.val;
  if (active.kind === 'family') return (GROUP_FAMILY[n.group] || 'doc') === active.val;
  return false;
}
function readLegendItem(li) {
  if (li.dataset.layer) return { kind: 'layer', val: li.dataset.layer };
  if (li.dataset.maturity) return { kind: 'maturity', val: li.dataset.maturity };
  if (li.dataset.family) return { kind: 'family', val: li.dataset.family };
  return null;
}
function updateLegendLockCSS() {
  document.querySelectorAll('.topo-legend li').forEach((li) => {
    const item = readLegendItem(li);
    li.classList.toggle('is-locked', !!(_legendLock && item && _legendLock.kind === item.kind && _legendLock.val === item.val));
  });
}
function bindLegendItems() {
  document.querySelectorAll('.topo-legend li').forEach((li) => {
    if (li._bound) return;
    li._bound = true;
    li.addEventListener('mouseenter', () => { _legendHover = readLegendItem(li); applyLegendHighlight(); });
    li.addEventListener('mouseleave', () => { _legendHover = null; applyLegendHighlight(); });
    li.addEventListener('click', (e) => {
      e.stopPropagation();
      const item = readLegendItem(li);
      if (!item) return;
      _legendLock = (_legendLock && _legendLock.kind === item.kind && _legendLock.val === item.val) ? null : item;
      applyLegendHighlight();
      updateLegendLockCSS();
    });
  });
}

// ═══ tip / detail ═══
function showTip(n) {
  const tip = document.getElementById('topo-tip');
  const mat = n.maturity || 'progressing';
  const fam = GROUP_FAMILY[n.group] || 'doc';
  const c = resolveCss(`var(--topo-c-${fam})`);
  tip.innerHTML = `
    <div class="tip-name">${esc(n.name)}</div>
    <div class="tip-path">${esc(n.path || '—')}</div>
    <div class="tip-badges">
      <span class="tip-badge" style="color:${c};border-color:${c}">${MATURITY_LABEL[mat] || mat}</span>
      ${n.layer ? `<span class="tip-badge">${esc(LAYER_LABEL[n.layer] || n.layer)}</span>` : ''}
      ${n.module ? `<span class="tip-badge">${esc(n.module)}</span>` : ''}
      ${n.inDegree ? `<span class="tip-badge">入度 ${n.inDegree}</span>` : ''}
      ${n.orphan ? `<span class="tip-badge" style="color:#F97583;border-color:#F97583">孤立</span>` : ''}
    </div>
    ${n.lines ? `<div class="tip-lines">${n.lines} 行${n.fileType ? ' · ' + n.fileType : ''}</div>` : ''}
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
    const co = _graph.graph2ScreenCoords(node.x, node.y, node.z);
    const rect = document.getElementById('topo-graph').getBoundingClientRect();
    const m = document.getElementById('topo-main').getBoundingClientRect();
    let x = rect.left - m.left + co.x + 14, y = rect.top - m.top + co.y - 8;
    if (x + tip.offsetWidth > m.width - 8) x = rect.left - m.left + co.x - tip.offsetWidth - 14;
    if (y + tip.offsetHeight > m.height - 8) y = m.height - tip.offsetHeight - 8;
    if (y < 8) y = 8;
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  } catch (e) {}
}
function hideTip() { document.getElementById('topo-tip').hidden = true; }

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
    ['入度', n.inDegree != null ? n.inDegree : '—'],
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
    } catch (e) { wrap.textContent = '(加载失败: ' + doc + ')'; }
  }
}

// ═══ 侧栏 ═══
function renderLegend() {
  const used = new Map();
  _data.nodes.forEach((n) => { used.set(n.layer, (used.get(n.layer) || 0) + 1); });
  const order = ['ui', 'infra', 'tool', 'pipeline', 'data', 'doc', 'harness', 'task', 'other', 'root'];
  document.getElementById('topo-legend-layer').innerHTML = order
    .filter((l) => used.has(l))
    .map((l) => {
      const fam = (l === 'ui' || l === 'infra') ? 'primary' : (l === 'data') ? 'data' : (l === 'tool' || l === 'pipeline' || l === 'harness') ? 'infra' : 'doc';
      const c = resolveCss(`var(--topo-c-${fam})`);
      return `<li data-layer="${l}"><span class="st" style="background:${c}"></span>${LAYER_LABEL[l] || l} <span class="count">(${used.get(l)})</span></li>`;
    }).join('');
}
function renderLatest() {
  const el = document.getElementById('topo-latest');
  if (!_data.latest) { el.textContent = '—'; return; }
  const b = _data.build || {};
  const todos = _data.todoBrief || [];
  el.innerHTML = `
    <div class="tip-build"><b>${b.commit || '----'}</b> · ${b.python ? 'py ' + b.python : ''}<br><span class="ts">${esc(b.commitTime || b.builtAt || '')}</span></div>
    <b>${_data.latest.id}</b> ${esc(_data.latest.title)}<br><span class="ts">${esc(_data.latest.ts || '')}</span>
    ${todos.length ? '<ul class="tip-todo">' + todos.map((t) => `<li>${t.state} ${esc(t.title)}</li>`).join('') + '</ul>' : ''}
  `;
}
function updateStats() {
  const s = _data.stats || {};
  document.getElementById('topo-stats').textContent = `${s.nodes || 0} 节点 / ${s.links || 0} 边`;
}

function toggleFullscreen() {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen().catch(() => {});
  else document.exitFullscreen();
}
function resolveCss(v) {
  if (!v) return '#8B8B8B';
  if (!v.startsWith('var(')) return v;
  if (_cssCache[v]) return _cssCache[v];
  const m = v.match(/var\((--[\w-]+)\)/);
  if (!m) return '#8B8B8B';
  const hex = getComputedStyle(document.documentElement).getPropertyValue(m[1]).trim();
  const out = hex || '#8B8B8B';
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
  document.querySelectorAll('#topo-actionbar button').forEach((btn) => {
    btn.addEventListener('click', () => {
      const act = btn.dataset.act;
      if (act === 'reset') { _graph.zoomToFit(400, 60); _legendLock = null; applyLegendHighlight(); updateLegendLockCSS(); }
      else if (act === 'fullscreen') toggleFullscreen();
      else if (act === 'refresh') load(_curPreset, true);
      else if (act === 'close') window.close();
    });
  });
  document.getElementById('topo-detail-close').addEventListener('click', () => {
    document.getElementById('topo-detail').hidden = true;
    _selectedId = null;
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.getElementById('topo-detail').hidden = true;
      _selectedId = null; _hoveredId = null; _legendLock = null;
      applyLegendHighlight(); updateLegendLockCSS(); hideTip();
    }
  });
  document.addEventListener('fullscreenchange', () => {
    document.body.classList.toggle('is-fs', !!document.fullscreenElement);
  });
}

init();
