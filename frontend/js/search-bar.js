// ═══ search-bar.js — 地点搜索栏状态机（Phase 2）═══
// 手写状态机，不用 maplibre-gl-geocoder。
// 6 态：collapsed → expanded → focused → suggesting → history → navigating
//   collapsed  --click toggle--> expanded --focus input--> focused
//   focused + 输入≥1字 + debounce 300ms --> suggesting（调 searchPlaces）
//   focused + 空输入                --> history（localStorage 最近 8 条）
//   suggesting --↑↓高亮/Enter--> navigating：flyTo + marker/popup + 入历史
// 收起：仅 pointerdown-outside + Esc（绝不用 blur，防 150ms 形变期误触）。
// Ctrl+K 全局展开+聚焦。
// 坐标一律 WGS84（服务端 core/geocode.py 已转高德 GCJ-02，红线 #2）。

import { getMap } from './map.js';
import { searchPlaces } from './api.js';
import { showPointPopup, expandPointPopup, collapsePointPopup } from './popup.js';
import { subscribe as subscribeGeoLoader } from './geocode-loader.js';

const HISTORY_KEY = 'emotion-map:search-history';
const HISTORY_MAX = 8;
const DEBOUNCE_MS = 300;

let _el = null;          // .search-bar 容器
let _input = null;
let _results = null;     // .sb-results <ul>
let _ringCircle = null;  // .sb-ring circle（地点反查进度环）
let _state = 'collapsed';
let _hits = [];          // 当前联想结果
let _hitsFor = '';       // 产生当前 _hits 的 query（Enter 陈旧守卫）
let _active = -1;        // ↑↓ 高亮索引
let _debounce = null;
let _marker = null;      // 选中结果的标记（navigating 态）
let _popup = null;       // 选中结果 popup

// ── 工具 ──

function _MagnifierSvg() {
  // 16×16 放大镜（与 toolbar svg 风格一致：stroke currentColor）
  const ns = 'http://www.w3.org/2000/svg';
  const s = document.createElementNS(ns, 'svg');
  s.setAttribute('width', '16'); s.setAttribute('height', '16');
  s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('fill', 'none');
  s.setAttribute('stroke', 'currentColor'); s.setAttribute('stroke-width', '2.2');
  s.setAttribute('stroke-linejoin', 'round'); s.setAttribute('stroke-linecap', 'round');
  const c = document.createElementNS(ns, 'circle');
  c.setAttribute('cx', '11'); c.setAttribute('cy', '11'); c.setAttribute('r', '7');
  const l = document.createElementNS(ns, 'line');
  l.setAttribute('x1', '21'); l.setAttribute('y1', '21'); l.setAttribute('x2', '16.65');
  l.setAttribute('y2', '16.65');
  s.appendChild(c); s.appendChild(l);
  return s;
}

function _ProgressRingSvg() {
  // 32×32 进度环（外圈，r=14 stroke=2）：stroke-dashoffset 驱动填充百分比。
  // transform:rotate(-90deg) 由 CSS 给，使进度从 12 点起。色由 CSS（灰→完成绿）。
  const ns = 'http://www.w3.org/2000/svg';
  const s = document.createElementNS(ns, 'svg');
  s.setAttribute('class', 'sb-ring');
  s.setAttribute('viewBox', '0 0 32 32');
  s.setAttribute('fill', 'none');
  s.setAttribute('aria-hidden', 'true');
  const c = document.createElementNS(ns, 'circle');
  c.setAttribute('cx', '16'); c.setAttribute('cy', '16'); c.setAttribute('r', '13');
  c.setAttribute('stroke-width', '4');
  c.setAttribute('stroke-linecap', 'round');
  s.appendChild(c);
  return s;
}

function _setState(s) {
  _state = s;
  if (!_el) return;
  _el.classList.toggle('is-collapsed', s === 'collapsed');
  _el.classList.toggle('is-focused', s === 'focused' || s === 'suggesting' || s === 'history');
}

function _loadHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []; }
  catch (_) { return []; }
}

function _pushHistory(hit) {
  const h = _loadHistory().filter((x) => !(x.name === hit.name && Math.abs(x.lng - hit.lng) < 1e-4));
  h.unshift({ name: hit.name, lng: hit.lng, lat: hit.lat, zone_name: hit.zone_name || '', category: hit.category || '' });
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(h.slice(0, HISTORY_MAX))); } catch (_) {}
}

/** 删单条历史（按 name+lng 身份），存盘后重渲染。 */
function _removeHistory(idx) {
  const hit = _hits[idx];
  if (!hit) return;
  const h = _loadHistory().filter((x) => !(x.name === hit.name && Math.abs(x.lng - hit.lng) < 1e-4));
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(h)); } catch (_) {}
  _showHistory();
}

/** 清空全部历史，存盘后重渲染空态。 */
function _clearHistory() {
  try { localStorage.removeItem(HISTORY_KEY); } catch (_) {}
  _showHistory();
}

// ── 渲染下拉 ──

function _hideResults() {
  if (_results) _results.hidden = true;
  _results.innerHTML = '';
  _active = -1;
  _hits = [];
  _hitsFor = '';
}

function _hl(name, q) {
  // 高亮 name 中命中 q 的子串（小写不敏感；拼音查询 q 不在 name 内则不高亮）
  const e = _esc(name);
  if (!q) return e;
  const i = name.toLowerCase().indexOf(q.toLowerCase());
  if (i < 0) return e;
  return _esc(name.slice(0, i)) + '<mark>' + _esc(name.slice(i, i + q.length)) + '</mark>' + _esc(name.slice(i + q.length));
}

function _row(hit, idx, q, isHistory) {
  const li = document.createElement('li');
  if (isHistory) li.className = 'sb-hist-row';
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'sb-item' + (isHistory ? ' sb-hist-item' : '');
  btn.dataset.idx = String(idx);

  // 行 1：名称 + 匹配类型标签
  const topRow = document.createElement('span'); topRow.className = 'sb-item-top';
  const nm = document.createElement('span'); nm.className = 'sb-item-name'; nm.innerHTML = _hl(hit.name, q);
  topRow.appendChild(nm);

  const tier = _scoreTier(hit.score);
  if (tier) {
    const tag = document.createElement('span'); tag.className = 'sb-tier-tag';
    tag.textContent = tier; topRow.appendChild(tag);
  }
  btn.appendChild(topRow);

  // 行 2：zone 色点 + zone_name · address/category
  const subRow = document.createElement('span'); subRow.className = 'sb-item-sub-row';
  if (hit.zone_name) {
    const dot = document.createElement('span'); dot.className = 'sb-zone-dot';
    if (hit.zone_color) dot.style.backgroundColor = hit.zone_color;
    subRow.appendChild(dot);
    const zn = document.createElement('span'); zn.className = 'sb-zone-name'; zn.textContent = hit.zone_name;
    subRow.appendChild(zn);
  }
  const extra = hit.address || hit.category || '';
  if (extra && extra !== hit.zone_name) {
    if (subRow.children.length) {
      const sep = document.createElement('span'); sep.className = 'sb-sub-sep'; sep.textContent = '\xB7';
      subRow.appendChild(sep);
    }
    const ex = document.createElement('span'); ex.className = 'sb-sub-extra'; ex.textContent = extra;
    subRow.appendChild(ex);
  }
  if (subRow.children.length) btn.appendChild(subRow);

  btn.addEventListener('mouseenter', () => { _active = idx; _renderActive(); });
  btn.addEventListener('click', (e) => { e.preventDefault(); _navigate(idx); });
  li.appendChild(btn);
  if (isHistory) {
    // 单条删除「×」：与 .sb-item 同级（非嵌套，合规）；点击只删不导航、不收起。
    const x = document.createElement('button');
    x.type = 'button';
    x.className = 'sb-hist-x';
    x.title = '删除该条';
    x.setAttribute('aria-label', '删除该条历史');
    x.textContent = '×';
    x.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); _removeHistory(idx); });
    li.appendChild(x);
  }
  return li;
}

function _scoreTier(score) {
  if (score >= 300) return '精确';   // 精确
  if (score >= 250) return '前缀';   // 前缀
  if (score >= 220) return '拼音';   // 拼音
  if (score >= 180) return '子串';   // 子串
  return '';                                  // fuzzy 不标
}

function _renderActive() {
  _results.querySelectorAll('.sb-item').forEach((b, i) => {
    b.classList.toggle('is-active', i === _active);
  });
}

function _showLoading() {
  _results.innerHTML = '';
  const li = document.createElement('li'); li.className = 'sb-loading';
  const sp = document.createElement('span'); sp.className = 'sb-spinner';
  li.appendChild(sp);
  li.appendChild(document.createTextNode('搜索中...'));
  _results.appendChild(li);
  _results.hidden = false;
}

function _showHistory() {
  _hitsFor = '';                                 // 历史非 query 匹配，Enter 守卫按新词处理
  _setState('history');
  _results.innerHTML = '';
  const hist = _loadHistory();
  if (!hist.length) {
    const e = document.createElement('li'); e.className = 'sb-empty';
    e.innerHTML = '<div class="sb-empty-title">暂无历史搜索</div><div class="sb-empty-hint">输入地点名称开始搜索</div>';
    _results.appendChild(e);
  } else {
    const t = document.createElement('li'); t.className = 'sb-section sb-section-hist';
    const lbl = document.createElement('span'); lbl.textContent = '历史'; t.appendChild(lbl);
    const clr = document.createElement('button');
    clr.type = 'button'; clr.className = 'sb-hist-clear'; clr.textContent = '清除';
    clr.title = '清除全部历史';
    clr.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); _clearHistory(); });
    t.appendChild(clr);
    _results.appendChild(t);
    _hits = hist;
    hist.forEach((h, i) => _results.appendChild(_row(h, i, '', true)));
  }
  _results.hidden = false;
  _active = -1;
}

function _showSuggestions(query) {
  searchPlaces(query, 10).then((res) => {
    if (_input.value.trim() !== query) return;   // 过期响应丢弃
    _hitsFor = query;                              // 标记当前 _hits 对应的 query（Enter 守卫）
    _setState('suggesting');
    _results.innerHTML = '';
    const hits = (res && res.hits) || [];
    _hits = hits;
    if (!hits.length) {
      const e = document.createElement('li'); e.className = 'sb-empty';
      e.innerHTML = '<div class="sb-empty-title">无匹配地点</div><div class="sb-empty-hint">试试其他关键词，或搜索商圈名、类别</div>';
      _results.appendChild(e);
    } else {
      hits.forEach((h, i) => _results.appendChild(_row(h, i, query)));
    }
    _results.hidden = false;
    _active = hits.length ? 0 : -1;
    _renderActive();
  }).catch((e) => {
    _setState('suggesting');
    _results.innerHTML = '';
    const li = document.createElement('li'); li.className = 'sb-empty';
    li.innerHTML = '<div class="sb-empty-title">搜索失败</div><div class="sb-empty-hint">' + (e.message || '网络错误') + '</div>';
    _results.appendChild(li);
    _results.hidden = false;
  });
}

// ── 导航（选中结果）──

let _markerEl = null;      // 标记 DOM 元素（自定义红大头针）
let _markerActive = false;
let _pointTooltip = null;  // 标记 hover tooltip
let _curHit = null;        // 当前导航的 hit（tooltip 用）

function _hidePointTooltip() {
  if (_pointTooltip) { _pointTooltip.remove(); _pointTooltip = null; }
}

function _setMarkerActive(on) {
  _markerActive = on;
  if (_markerEl) _markerEl.classList.toggle('is-active', on);
}

function _pushpinSvg() {
  // 红色大头针（22×30，anchor bottom：尖端贴坐标）
  return '<svg class="search-pin" width="22" height="30" viewBox="0 0 24 32" xmlns="http://www.w3.org/2000/svg">'
    + '<path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 20 12 20s12-11 12-20C24 5.4 18.6 0 12 0z" fill="#e53935" stroke="#b71c1c" stroke-width="1"/>'
    + '<circle cx="12" cy="12" r="5" fill="#ffffff"/></svg>';
}

function _clearMarker() {
  if (_marker) { _marker.remove(); _marker = null; }
  if (_popup) { _popup.remove(); _popup = null; }
  _hidePointTooltip();
  _markerEl = null;
  _markerActive = false;
}

function _navigate(idx) {
  const hit = _hits[idx];
  if (!hit) return;
  const map = getMap();
  _input.value = hit.name;
  _hideResults();
  _pushHistory(hit);
  _setState('navigating');
  _curHit = hit;
  if (!map) return;
  map.flyTo({ center: [hit.lng, hit.lat], zoom: 16, essential: true });   // WGS84 直接用（红线 #2 服务端已转）
  _clearMarker();
  // 自定义红色大头针标记（一次一个：_clearMarker 已清旧）
  const el = document.createElement('div');
  el.className = 'search-marker';
  el.innerHTML = _pushpinSvg();
  el.addEventListener('mouseenter', () => {
    if (!_curHit) return;
    if (!_pointTooltip) _pointTooltip = new maplibregl.Popup({ closeButton: false, closeOnClick: false, className: 'point-tooltip', offset: 34 });
    _pointTooltip.setHTML('<div class="pt-name">' + _esc(_curHit.name) + '</div>')
      .setLngLat([_curHit.lng, _curHit.lat]).addTo(map);
  });
  el.addEventListener('mouseleave', _hidePointTooltip);
  el.addEventListener('click', (e) => {
    e.stopPropagation();   // 不冒泡到 map（防 map-click 收起）
    if (_markerActive) { _setMarkerActive(false); collapsePointPopup(); }
    else { _setMarkerActive(true); expandPointPopup(); }
  });
  _markerEl = el;
  _marker = new maplibregl.Marker({ element: el, anchor: 'bottom' }).setLngLat([hit.lng, hit.lat]).addTo(map);
  _setMarkerActive(true);          // 导航后放大凸出
  showPointPopup(hit);             // Point 卡展开
}

async function _enterNavigate() {
  // Enter 跳旧结果 bug 修复：若当前联想不对应输入（陈旧/空），先即时取新结果首条再导航
  const q = _input.value.trim();
  if (!q) return;
  if (q !== _hitsFor) {
    try {
      const res = await searchPlaces(q, 10);
      _hits = (res && res.hits) || [];
      if (!_hits.length) return;
      _hitsFor = q; _active = 0;
      _navigate(0);
    } catch (_) { /* 静默，用户可重试 */ }
    return;
  }
  _navigate(_active >= 0 ? _active : 0);
}

function _esc(s) {
  return String(s || '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

// ── 展开 / 收起 ──

function _expand() {
  _setState('focused');
  _el.classList.remove('is-collapsed');
  // 形变期内不抢焦点（避免 150ms 过渡中 layout 抖动）；下一帧再聚焦
  requestAnimationFrame(() => _input.focus());
  if (_input.value.trim()) _queueSearch();
  else _showHistory();
}

function _collapse() {
  _setState('collapsed');
  _hideResults();
  _input.blur();
  _input.value = '';
}

function _queueSearch() {
  const q = _input.value.trim();
  if (_debounce) clearTimeout(_debounce);
  if (!q) { _showHistory(); return; }
  // P5: 输入即显示 loading spinner（不等 debounce）
  _showLoading();
  _debounce = setTimeout(() => _showSuggestions(q), DEBOUNCE_MS);
}

// ── 初始化 ──

export function initSearchBar() {
  const host = document.getElementById('map');
  if (!host || _el) return;

  _el = document.createElement('div');
  _el.className = 'search-bar is-collapsed';
  _el.setAttribute('role', 'search');

  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'sb-toggle';
  toggle.title = '搜索地点 (Ctrl+K)';
  toggle.setAttribute('aria-label', '搜索地点');
  toggle.appendChild(_MagnifierSvg());
  toggle.appendChild(_ProgressRingSvg());
  _ringCircle = toggle.querySelector('.sb-ring circle');

  _input = document.createElement('input');
  _input.type = 'text';
  _input.className = 'sb-input';
  _input.placeholder = '搜索地点';
  _input.setAttribute('aria-label', '搜索地点');
  _input.autocomplete = 'off';

  const kbd = document.createElement('span');
  kbd.className = 'sb-kbd'; kbd.textContent = 'Ctrl K';

  _results = document.createElement('ul');
  _results.className = 'sb-results';
  _results.hidden = true;

  _el.appendChild(toggle);
  _el.appendChild(_input);
  _el.appendChild(kbd);
  _el.appendChild(_results);
  host.appendChild(_el);

  // toggle：折叠→展开；已展开→聚焦输入
  toggle.addEventListener('click', (e) => {
    e.preventDefault();
    if (_state === 'collapsed') _expand();
    else _input.focus();
  });

  _input.addEventListener('focus', () => {
    if (_state === 'collapsed') _setState('focused');
    if (!_input.value.trim()) _showHistory();
  });
  _input.addEventListener('input', () => {
    _queueSearch();
  });
  _input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { e.preventDefault(); _collapse(); return; }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (!_hits.length) return;
      _active = (_active + 1) % _hits.length; _renderActive();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (!_hits.length) return;
      _active = (_active - 1 + _hits.length) % _hits.length; _renderActive();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      _enterNavigate();
    }
  });

  // 收起：pointerdown 落在搜索栏以外 → 收（绝不用 blur，防形变期误触）
  document.addEventListener('pointerdown', (ev) => {
    if (_state === 'collapsed') return;
    if (_el.contains(ev.target)) return;
    _collapse();
  });

  // Ctrl+K 全局展开+聚焦；Esc 收
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
      e.preventDefault();
      if (_state === 'collapsed') _expand();
      else _input.select();
    }
  });

  // Point 卡外部信号（popup.js 派发）：collapse→缩标记；hide→移除标记
  document.addEventListener('point:collapse', () => _setMarkerActive(false));
  document.addEventListener('point:hide', () => _clearMarker());

  // 加载进度环（geocode-loader 统一驱动，多 kind 分色）：dashoffset = C·(1 - p/100)；
  // 环色 inline 由 loader 给（反查蓝/生成青/完成橙），显隐由 CSS 类 is-ring-loading/done/fade 控制。
  const RING_C = 2 * Math.PI * 13;
  subscribeGeoLoader(({ progress, phase, color }) => {
    if (!_el) return;
    _el.classList.toggle('is-ring-loading', phase === 'loading');
    _el.classList.toggle('is-ring-done', phase === 'done');
    _el.classList.toggle('is-ring-fade', phase === 'fade');
    if (_ringCircle) {
      _ringCircle.style.strokeDasharray = String(RING_C);
      _ringCircle.style.strokeDashoffset = String(RING_C * (1 - Math.max(0, Math.min(100, progress)) / 100));
      if (color) _ringCircle.style.stroke = color;
    }
  });
}
