// ═══ topology.js — 3D 项目架构拓扑图（单图专注版：去 preset / 中文功能名 / 组团虚线框 / 中键平移 / 双击聚焦）═══
import * as THREE from '../vendor/three.module.js';

const GROUP_FAMILY = {
  frontend: 'primary', core: 'primary', ai_qa: 'emc',
  api: 'infra', apps: 'infra', SCRIPT: 'infra', '.claude': 'infra',
  module: 'infra', pipeline: 'infra',
  DATA: 'data', SCRAPER: 'data',
  docs: 'doc', design: 'doc', tests: 'doc', memories: 'doc',
  root: 'doc', static: 'doc', task: 'doc',
};
// group 中文名（组团框 + 节点显示用）
const GROUP_LABEL_ZH = {
  frontend: '前端主界面', core: '基础设施', ai_qa: 'AI 问答·EMC', SCRIPT: '分析管道',
  DATA: '数据层', api: 'API 路由', SCRAPER: '数据采集', docs: '文档',
  '.claude': '开发工具', apps: 'Streamlit 遗留', design: '设计令牌', tests: '测试',
};
// module 中文名（核心节点 label 用，非文件名）
const MODULE_LABEL_ZH = {
  MOD_GOV: '数据治理', MOD_ANA: '情绪分析', MOD_REL: '相关性筛选', MOD_RUN: '分析入口',
  MOD_GEN: 'Mock 生成', MOD_PERF: '城市演示数据', MOD_SCRAPER: '采集爬虫', MOD_GEOCODE: '地理编码',
  MOD_LLM: 'LLM 调用', MOD_AIQA: 'AI 问答技能谱', MOD_SPATIAL: '空间分析', MOD_FIELD: '字段语义',
  MOD_APP: 'Streamlit 应用', MOD_LOADER: '数据加载', MOD_MAP: '地图引擎', MOD_TRANSFORM: '坐标转换',
  MOD_RANGE: '范围选择', MOD_EXPORT: '导出', MOD_MM: '多模态', MOD_UTILS: '工具库',
  MOD_PLACE: 'POI 图层', MOD_UI: 'UI 组件', MOD_TRACKER: '决策追踪',
};
const MATURITY_LABEL = { mature: '成熟', progressing: '推进中', planned: '计划', paused: '搁置', rejected: '否决' };
const LAYER_LABEL = {
  data: '数据层', tool: '工具层·管道', ui: 'UI 层', infra: '基础设施',
  doc: '文档', harness: 'Harness', pipeline: '数据管道 L0→L4', task: '任务路线图', other: '其他', root: '根',
};
const TYPE_LABEL = { file: '文件', dir: '目录', module: '模块', 'pipeline-stage': '管道阶段', task: '任务' };

let _graph = null, _data = null, _selectedId = null, _hoveredId = null, _loaded = false;
let _legendLock = null, _legendHover = null;
let _lastClick = { id: null, t: 0 };
let _labelNodes = [];
let _boxGroups = [];   // [{group, label, nodes, boxDiv, labelDiv}]
const _cssCache = {};
let _domRafPending = false;
/** rAF 批处理 DOM 更新：合并一帧内多次 onEngineTick / ctrl.change 为一次 updateLabels+Boxes+TipPos
 *  （force sim 220 tick 冷却期 + 双击 zoomToFit 相机动画叠加 → 每 tick 直调 DOM 抢帧卡顿；rAF 对齐刷新消除抢帧）。 */
function _scheduleDomUpdate() {
  if (_domRafPending) return;
  _domRafPending = true;
  requestAnimationFrame(() => { _domRafPending = false; updateLabels(); updateBoxes(); updateTipPos(); });
}

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
    .linkVisibility((l) => l.type !== 'contains')
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
    .onEngineTick(() => _scheduleDomUpdate())
    .cooldownTicks(220);

  // 灯光
  const scene = _graph.scene();
  scene.add(new THREE.AmbientLight(0xffffff, 0.65));
  const dl = new THREE.DirectionalLight(0xffffff, 0.85); dl.position.set(200, 400, 200); scene.add(dl);

  // 中键→平移（移除默认中键 dolly/zoom），滚轮缩放保留
  const ctrl = _graph.controls();
  ctrl.mouseButtons = { LEFT: THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.PAN, RIGHT: THREE.MOUSE.PAN };
  ctrl.enableZoom = true;   // 滚轮 zoom
  // 视角变化时同步标签/框/tip（修"拖拽字体不跟随"）
  ctrl.addEventListener('change', () => _scheduleDomUpdate());

  const resize = () => { if (_graph) _graph.width(el.clientWidth).height(el.clientHeight); };
  requestAnimationFrame(resize);
  window.addEventListener('resize', resize);

  await load();
  wireUI();
}

// ═══ 节点几何 ═══
/** 节点几何：颜色=家族（Martin 风 4 宝石色相，CSS var），成熟度=opacity（mature 实心 / progressing 半透 / planned 线框）。
 *  弃光滑/磨砂材质区分（用户反馈"看不出区别"）→ 统一 glossy 球 + opacity 区分成熟度；颜色多色相做主要区分。 */
function buildNode(n) {
  const color = colorOf(n);
  const r = nodeRadius(n);
  const core = isCore(n);
  if (n.maturity === 'planned') {
    return new THREE.Mesh(new THREE.IcosahedronGeometry(r * 0.85, 0),
      new THREE.MeshBasicMaterial({ color, wireframe: true, transparent: true, opacity: 0.4 }));
  }
  const opacity = n.maturity === 'progressing' ? 0.6 : 1.0;   // mature=1.0 / progressing=0.6
  return new THREE.Mesh(new THREE.SphereGeometry(r, 20, 16),
    new THREE.MeshStandardMaterial({ color, metalness: core ? 0.45 : 0.25, roughness: 0.4, transparent: true, opacity }));
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
// 只核心节点常显字（module/pipeline-stage），用中文功能名
function showLabel(n) {
  return ['module', 'pipeline-stage'].includes(n.type);
}
function nodeDisplayName(n) {
  if (n.type === 'pipeline-stage') return n.name;              // _PIPELINE_STAGES name 已含中文（L0 原始采集…）
  if (n.type === 'module') return MODULE_LABEL_ZH[n.id] || n.id;
  return GROUP_LABEL_ZH[n.group] || n.name;
}
function colorOf(n) {
  return resolveCss(`var(--topo-c-${GROUP_FAMILY[n.group] || 'doc'})`);
}
function shortName(n) {
  const p = n.name || n.id;
  return p.length > 22 ? p.slice(0, 20) + '…' : p;
}

// ═══ 自建标签层（graph2ScreenCoords 锚定）═══
function renderLabels() {
  const cont = document.getElementById('topo-labels');
  if (!cont || !_data) return;
  cont.innerHTML = '';
  _labelNodes = _data.nodes.filter((n) => showLabel(n));
  _labelNodes.forEach((n) => {
    const div = document.createElement('div');
    div.className = 'node-label' + (isCore(n) ? ' is-core' : '');
    div.textContent = nodeDisplayName(n);
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
    try {
      const co = _graph.graph2ScreenCoords(n.x, n.y, n.z);
      div.style.display = 'block';
      div.style.left = co.x + 'px';
      div.style.top = (co.y - 10) + 'px';
    } catch (e) { div.style.display = 'none'; }
  });
}

// ═══ 组团虚线框（主要 group 的屏幕 bbox + 中文名）═══
function renderBoxes() {
  const cont = document.getElementById('topo-boxes');
  if (!cont || !_data) return;
  cont.innerHTML = '';
  _boxGroups = [];
  const grouped = {};
  _data.nodes.forEach((n) => {
    if (n.type === 'file' || n.type === 'dir') {
      const g = n.group;
      if (GROUP_LABEL_ZH[g]) {
        (grouped[g] = grouped[g] || []).push(n);
      }
    }
  });
  Object.entries(grouped).forEach(([g, nodes]) => {
    if (nodes.length < 3) return;   // 太小的组不框
    const box = document.createElement('div');
    box.className = 'cluster-box';
    const lab = document.createElement('div');
    lab.className = 'cluster-box-label';
    lab.textContent = `${GROUP_LABEL_ZH[g]} · ${nodes.length}`;
    lab.title = '双击缩放至该组团';
    lab.addEventListener('dblclick', (e) => { e.stopPropagation(); zoomToGroup(g); });
    box.appendChild(lab);
    cont.appendChild(box);
    _boxGroups.push({ group: g, nodes, boxDiv: box, labelDiv: lab });
  });
}
function updateBoxes() {
  if (!_graph || !_boxGroups.length) return;
  _boxGroups.forEach((bg) => {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity, vis = 0;
    bg.nodes.forEach((n) => {
      if (n.x == null) return;
      try {
        const co = _graph.graph2ScreenCoords(n.x, n.y, n.z);
        minX = Math.min(minX, co.x); minY = Math.min(minY, co.y);
        maxX = Math.max(maxX, co.x); maxY = Math.max(maxY, co.y);
        vis++;
      } catch (e) {}
    });
    if (vis < 2) { bg.boxDiv.style.display = 'none'; return; }
    const pad = 24;
    bg.boxDiv.style.display = 'block';
    bg.boxDiv.style.left = (minX - pad) + 'px';
    bg.boxDiv.style.top = (minY - pad) + 'px';
    bg.boxDiv.style.width = (maxX - minX + pad * 2) + 'px';
    bg.boxDiv.style.height = (maxY - minY + pad * 2) + 'px';
  });
}

// ═══ load（无 preset，单图全显）═══
async function load(refresh = false) {
  if (refresh) { location.reload(); return; }
  document.getElementById('topo-stats').textContent = '加载中…';
  try {
    const r = await fetch('/api/v1/topo?view=overview');
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
  if (!_loaded) {
    _graph.graphData(_data);
    _graph.d3VelocityDecay(0.4);
    _graph.d3Force('charge').strength(-60);
    _graph.d3Force('link').distance(66);
    _loaded = true;
  }
  renderLabels();
  renderBoxes();
  renderLegend();
  renderLatest();
  updateStats();
  bindLegendItems();
  setTimeout(() => { try { _graph.zoomToFit(400, 60); } catch (e) {} }, 900);
}

// ═══ hover / 双击聚焦 / 空白 ═══
function onHover(node, prev) {
  if (prev && prev.__threeObj) _setGlow(prev.__threeObj, false);
  _hoveredId = node ? node.id : null;
  if (node && node.__threeObj) _setGlow(node.__threeObj, true);
  if (node) showTip(node); else hideTip();
}
/** 节点高光：scale 放大 1.7 + 白色 halo 边缘发光（additive 球，半径 ×1.55）+ emissive 自发光（lit 材质）。
 *  halo 挂 obj.userData._halo 复用/清理；几何半径从 obj.geometry.parameters.radius 取（球/二十面体均支持）。 */
function _setGlow(obj, on) {
  if (!obj) return;
  obj.scale.set(on ? 1.7 : 1, on ? 1.7 : 1, on ? 1.7 : 1);
  const mat = obj.material;
  if (mat) {
    if (on) {
      if (mat._origEmissive === undefined) mat._origEmissive = mat.emissive ? mat.emissive.getHex() : null;
      if (mat._origEI === undefined) mat._origEI = mat.emissiveIntensity;
      if (mat.emissive) { mat.emissive.setHex(0xffffff); mat.emissiveIntensity = 0.55; }
    } else if (mat._origEmissive !== null && mat.emissive) {
      mat.emissive.setHex(mat._origEmissive); mat.emissiveIntensity = mat._origEI;
    }
  }
  if (on && !obj.userData._halo) {
    const r = (obj.geometry && obj.geometry.parameters && obj.geometry.parameters.radius) || 8;
    const halo = new THREE.Mesh(new THREE.SphereGeometry(r * 1.55, 16, 12),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.22, blending: THREE.AdditiveBlending, depthWrite: false }));
    obj.add(halo);
    obj.userData._halo = halo;
  } else if (!on && obj.userData._halo) {
    obj.remove(obj.userData._halo);
    obj.userData._halo.geometry.dispose();
    obj.userData._halo.material.dispose();
    obj.userData._halo = null;
  }
}
function onNodeClick(n) {
  const now = Date.now();
  if (_lastClick.id === n.id && now - _lastClick.t < 300) {
    _lastClick = { id: null, t: 0 };
    zoomToCluster(n);    // 双击：聚焦该节点所在组团（节点为视角中心）
  } else {
    _lastClick = { id: n.id, t: now };
    showDetail(n);
  }
}
/** 双击节点：zoomToFit 该节点所在组团（filter=同 module/group/layer）——自适应取景，比固定偏移 cameraPosition
 *  视野稳（治"视野常不理想"）。800ms 动画 + 80px padding 留上下文。 */
function zoomToCluster(n) {
  const key = n.module || n.group || n.layer;
  if (!key) return;
  const inCluster = (nn) => (nn.module || nn.group || nn.layer) === key;
  const has = _data.nodes.some((nn) => inCluster(nn) && nn.x != null);
  if (!has) return;
  try { _graph.zoomToFit(800, 80, inCluster); } catch (e) {}
}
/** 双击组团框字体：zoomToFit 该组团（filter=group），居中+放大（pad 40 紧凑些）。 */
function zoomToGroup(group) {
  if (!_data || !_graph) return;
  const inGroup = (nn) => nn.group === group;
  if (!_data.nodes.some(inGroup)) return;
  try { _graph.zoomToFit(800, 40, inGroup); } catch (e) {}
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

// ═══ tip（hover 富信息，显示文件名等具体） ═══
function showTip(n) {
  const tip = document.getElementById('topo-tip');
  const mat = n.maturity || 'progressing';
  const fam = GROUP_FAMILY[n.group] || 'doc';
  const c = resolveCss(`var(--topo-c-${fam})`);
  const dispName = nodeDisplayName(n);
  tip.innerHTML = `
    <div class="tip-name">${esc(dispName)}</div>
    <div class="tip-path">${esc(n.path || '—')}</div>
    <div class="tip-badges">
      <span class="tip-badge" style="color:${c};border-color:${c}">${MATURITY_LABEL[mat] || mat}</span>
      ${n.layer ? `<span class="tip-badge">${esc(LAYER_LABEL[n.layer] || n.layer)}</span>` : ''}
      ${n.module ? `<span class="tip-badge">${esc(n.module)}</span>` : ''}
      ${n.inDegree ? `<span class="tip-badge">入度 ${n.inDegree}</span>` : ''}
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
  document.getElementById('td-name').textContent = nodeDisplayName(n);
  document.getElementById('td-path').textContent = n.path || '—';
  const rows = [
    ['类型', TYPE_LABEL[n.type] || n.type],
    ['文件名', n.name || '—'],
    ['架构层', LAYER_LABEL[n.layer] || n.layer || '—'],
    ['成熟度', MATURITY_LABEL[n.maturity] || n.maturity || '—'],
    ['模块', n.module ? (MODULE_LABEL_ZH[n.module] || n.module) : '—'],
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
  document.querySelectorAll('#topo-actionbar button').forEach((btn) => {
    btn.addEventListener('click', () => {
      const act = btn.dataset.act;
      if (act === 'reset') { _graph.zoomToFit(400, 60); _legendLock = null; applyLegendHighlight(); updateLegendLockCSS(); }
      else if (act === 'fullscreen') toggleFullscreen();
      else if (act === 'refresh') load(true);
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
