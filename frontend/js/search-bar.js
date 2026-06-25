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

const HISTORY_KEY = 'emotion-map:search-history';
const HISTORY_MAX = 8;
const DEBOUNCE_MS = 300;

let _el = null;          // .search-bar 容器
let _input = null;
let _results = null;     // .sb-results <ul>
let _state = 'collapsed';
let _hits = [];          // 当前联想结果
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

// ── 渲染下拉 ──

function _hideResults() {
  if (_results) _results.hidden = true;
  _results.innerHTML = '';
  _active = -1;
  _hits = [];
}

function _row(hit, idx, sub) {
  const li = document.createElement('li');
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'sb-item';
  btn.dataset.idx = String(idx);
  const nm = document.createElement('span'); nm.className = 'sb-item-name'; nm.textContent = hit.name;
  const sp = document.createElement('span'); sp.className = 'sb-item-sub'; sp.textContent = sub || '';
  btn.appendChild(nm); btn.appendChild(sp);
  btn.addEventListener('mouseenter', () => { _active = idx; _renderActive(); });
  btn.addEventListener('click', (e) => { e.preventDefault(); _navigate(idx); });
  li.appendChild(btn);
  return li;
}

function _renderActive() {
  _results.querySelectorAll('.sb-item').forEach((b, i) => {
    b.classList.toggle('is-active', i === _active);
  });
}

function _showHistory() {
  _setState('history');
  _results.innerHTML = '';
  const hist = _loadHistory();
  if (!hist.length) {
    const e = document.createElement('li'); e.className = 'sb-empty';
    e.textContent = '暂无历史搜索'; _results.appendChild(e);
  } else {
    const t = document.createElement('li'); t.className = 'sb-section'; t.textContent = '历史';
    _results.appendChild(t);
    _hits = hist;
    hist.forEach((h, i) => _results.appendChild(_row(h, i, h.zone_name || h.category || '')));
  }
  _results.hidden = false;
  _active = -1;
}

function _showSuggestions(query) {
  searchPlaces(query, 10).then((res) => {
    if (_input.value.trim() !== query) return;   // 过期响应丢弃
    _setState('suggesting');
    _results.innerHTML = '';
    const hits = (res && res.hits) || [];
    _hits = hits;
    if (!hits.length) {
      const e = document.createElement('li'); e.className = 'sb-empty';
      e.textContent = '无匹配地点'; _results.appendChild(e);
    } else {
      hits.forEach((h, i) => {
        const sub = h.zone_name || h.address || h.category || '';
        _results.appendChild(_row(h, i, sub));
      });
    }
    _results.hidden = false;
    _active = hits.length ? 0 : -1;
    _renderActive();
  }).catch((e) => {
    _setState('suggesting');
    _results.innerHTML = '';
    const li = document.createElement('li'); li.className = 'sb-empty';
    li.textContent = '搜索失败：' + (e.message || '网络错误');
    _results.appendChild(li);
    _results.hidden = false;
  });
}

// ── 导航（选中结果）──

function _clearMarker() {
  if (_marker) { _marker.remove(); _marker = null; }
  if (_popup) { _popup.remove(); _popup = null; }
}

function _navigate(idx) {
  const hit = _hits[idx];
  if (!hit) return;
  const map = getMap();
  _input.value = hit.name;
  _hideResults();
  _pushHistory(hit);
  _setState('navigating');
  if (map) {
    map.flyTo({ center: [hit.lng, hit.lat], zoom: 16, essential: true });   // WGS84 直接用（红线 #2 服务端已转）
    _clearMarker();
    const lngLat = [hit.lng, hit.lat];
    _popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 18, className: 'place-chip' })
      .setHTML('<span class="pc-zone">' + _esc(hit.name) + '</span>'
        + (hit.zone_name ? '<span class="pc-poi">' + _esc(hit.zone_name) + '</span>' : ''))
      .setLngLat(lngLat).addTo(map);
    _marker = new maplibregl.Marker().setLngLat(lngLat).addTo(map);
  }
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
      _navigate(_active >= 0 ? _active : 0);
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
}
