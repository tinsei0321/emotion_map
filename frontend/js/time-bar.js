// ═══ time-bar.js — 全局时间轴 · 时间按钮 + Martin 风展开卡片 ════════════════════════════
// 底部居中圆按钮（对齐顶部居中搜索按钮，同中轴线）→ 点击向上展开卡片：
//   头部(当前片+✕) + 粒度胶囊条(只显 manifest 存在的 period) + body(阶段=停点条 / 日=月历 / 周·月=占位)。
// 选片 → applyTime(period, sliceKey) → 换源所有时间感知点/面层 + Overview 追随。
// play/滑动条/lerp 动画 = A3（timeline.js 接管 grid 演进）。
//
// 设计语言镜像 .search-bar（search-bar.css）+ capsule-button-design-language：
//   无线框 + 阴影 + 白底 + hover 灰 + 选中蓝 + 圆角；过渡 var(--geojson-transition)。
// 承重：paint-inplace-swap-view（applyTime 走 setData 不重建层）；tool-no-auto-overview（time-bar 不抢焦点）。
// 详见 plan 07-19-cb-lovely-quiche.md。

import { applyTime, availablePeriods, slicesForPeriod, periodLabel, isManifestReady, loadManifest } from './time-source.js';
import { renderSlice, play as playGrid, stop as stopGrid, isBound as gridBound, renderSliceToMap, getBoundSliceKeys } from './timeline.js';
import { getMapB } from './map.js';

let _btn = null;          // .time-bar 圆按钮
let _card = null;         // .tb-card 展开卡片
let _isOpen = false;
let _period = null;       // 当前粒度（phase/day/...）
let _sliceKey = null;     // 当前选中片 key
let _cal = { y: 2026, m: 0 };   // 月历游标（日粒度用）
let _isPlaying = false;         // play 按钮态（▶/⏸）
let _compareB = null;           // 批4 compare：mapB 的 grid 片 key（Step 3 默认末片；Step 4 用户挑）

// 批4 compare：mapB grid 镜像就绪 → 设片B（默认末片）；退出 → 清。mapA 片A 走既有 renderSlice。
document.addEventListener('compare:mapBready', () => {
  const mapB = getMapB();
  const keys = getBoundSliceKeys();
  if (!mapB || !keys.length) return;
  if (_compareB === null || !keys.includes(_compareB)) _compareB = keys[keys.length - 1];   // 默认末片
  renderSliceToMap(mapB, _compareB);
});
document.addEventListener('compare:exit', () => { _compareB = null; });

const ICON_PLAY = '<svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M7 5v14l12-7z"/></svg>';
const ICON_PAUSE = '<svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>';

const CAL_WEEKS = ['日', '一', '二', '三', '四', '五', '六'];
const CAL_MONTHS = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];

/** 启动注入（main.js 调一次）：建圆按钮 + 卡片壳，挂 #map。卡片内容 manifest 就绪后填。 */
export function initTimeBar() {
  const host = document.getElementById('map');
  if (!host || _btn) return;

  _btn = document.createElement('button');
  _btn.type = 'button';
  _btn.className = 'time-bar';
  _btn.title = '时间轴';
  _btn.setAttribute('aria-label', '时间轴');
  _btn.innerHTML = '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 9h18M8 2v4M16 2v4"/><path d="M8 14l2.5 2.5L16 11"/></svg>';
  _btn.addEventListener('click', _toggle);

  _card = document.createElement('div');
  _card.className = 'tb-card';
  _card.hidden = true;

  host.appendChild(_btn);
  host.appendChild(_card);
}

async function _ensureState() {
  if (!isManifestReady()) { try { await loadManifest(); } catch (e) { /* ignore */ } }
  const periods = availablePeriods();
  if (!_period || !periods.includes(_period)) _period = periods[0] || null;
  if (_period) {
    const slices = slicesForPeriod(_period);
    if (!_sliceKey || !slices.some((s) => s.key === _sliceKey)) _sliceKey = slices[0] && slices[0].key;
  }
}

async function _toggle() {
  _isOpen ? _closeCard() : await _openCard();
}
async function _openCard() {
  await _ensureState();
  if (!_period) return;   // manifest 空 → 不开
  _isOpen = true;
  _btn.classList.add('is-open');
  _card.hidden = false;
  _render();
}
function _closeCard() {
  _stopPlay();
  _isOpen = false;
  _btn.classList.remove('is-open');
  _card.hidden = true;
}

/** 全卡片重渲（period 切换 / 外部 time:changed 后调）。 */
function _render() {
  if (!_card || !_period) return;
  const slices = slicesForPeriod(_period);
  const periods = availablePeriods();
  _card.innerHTML = `
    <div class="tb-head">
      <span class="tb-cur">${_sliceLabel(slices) || '—'}</span>
      <button class="tb-x" type="button" title="收起" aria-label="收起"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg></button>
    </div>
    <div class="tb-periods">${periods.map((p) => `<button class="tb-p ${p === _period ? 'is-active' : ''}" data-period="${p}" type="button">${periodLabel(p)}</button>`).join('')}</div>
    <div class="tb-body">${_renderBody(slices)}</div>
    ${slices.length > 1 ? `<div class="tb-foot"><button class="tb-play" type="button" title="播放/暂停" aria-label="播放/暂停">${_isPlaying ? ICON_PAUSE : ICON_PLAY}</button><input class="tb-slider" type="range" min="0" max="${slices.length - 1}" step="1" value="${_sliceIndex(slices)}" aria-label="时间滑动"><span class="tb-slider-i">${_sliceIndex(slices) + 1}/${slices.length}</span></div>` : ''}`;
  _card.querySelector('.tb-x').addEventListener('click', _closeCard);
  _card.querySelectorAll('.tb-p').forEach((b) => b.addEventListener('click', () => _setPeriod(b.dataset.period)));
  _wireBody(slices);
  const _sl = _card.querySelector('.tb-slider');
  if (_sl) _sl.addEventListener('input', () => { const s = slices[Number(_sl.value)]; if (s) _pick(s.key); });
  const _pl = _card.querySelector('.tb-play');
  if (_pl) _pl.addEventListener('click', _togglePlay);
}

function _sliceLabel(slices) {
  const s = slices.find((x) => x.key === _sliceKey);
  return s ? s.label : _sliceKey;
}
function _sliceIndex(slices) {
  const i = slices.findIndex((x) => x.key === _sliceKey);
  return i < 0 ? 0 : i;
}

/** body：阶段→停点条；日→月历；周/月/季/年/自选→占位（待数据接入）。 */
function _renderBody(slices) {
  if (_period === 'phase') {
    return `<div class="tb-stops">${slices.map((s, i) => `<button class="tb-stop ${s.key === _sliceKey ? 'is-active' : ''}" data-key="${s.key}" data-i="${i}" type="button"><span class="tb-stop-k">${s.key}</span><span class="tb-stop-l">${(s.label || '').replace(/^T\d\s*·\s*/, '')}</span></button>`).join('')}</div>`;
  }
  if (_period === 'day') return _renderCalendar(slices);
  return `<div class="tb-empty">该粒度（${periodLabel(_period)}）数据待接入</div>`;
}

// ── 月历（日粒度）──
function _renderCalendar(slices) {
  const sliceSet = new Set(slices.map((s) => s.key));
  if (slices.length && !_cal._init) { const [y, m] = slices[0].key.split('-').map(Number); _cal = { y, m: m - 1, _init: true }; }
  const { y, m } = _cal;
  const firstDay = new Date(y, m, 1).getDay();
  const daysInMonth = new Date(y, m + 1, 0).getDate();
  const cells = [];
  for (let i = 0; i < firstDay; i++) cells.push('<td class="tb-cal-blank"></td>');
  for (let d = 1; d <= daysInMonth; d++) {
    const key = `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    const has = sliceSet.has(key);
    const sel = key === _sliceKey;
    cells.push(`<td class="tb-cal-d ${has ? 'is-data' : ''} ${sel ? 'is-active' : ''}" data-key="${has ? key : ''}">${d}</td>`);
  }
  const rows = [];
  for (let i = 0; i < cells.length; i += 7) rows.push('<tr>' + cells.slice(i, i + 7).join('') + '</tr>');
  return `
    <div class="tb-cal">
      <div class="tb-cal-nav">
        <button class="tb-cal-a" data-d="-1" type="button" aria-label="上月"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M15 6l-6 6 6 6"/></svg></button>
        <span class="tb-cal-title">${y}年 ${CAL_MONTHS[m]}</span>
        <button class="tb-cal-a" data-d="1" type="button" aria-label="下月"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M9 6l6 6-6 6"/></svg></button>
      </div>
      <table class="tb-cal-grid"><thead><tr>${CAL_WEEKS.map((w) => `<th>${w}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table>
    </div>`;
}

function _wireBody(slices) {
  if (_period === 'phase') {
    _card.querySelectorAll('.tb-stop').forEach((b) => b.addEventListener('click', () => _pick(b.dataset.key)));
  } else if (_period === 'day') {
    _card.querySelectorAll('.tb-cal-a').forEach((b) => b.addEventListener('click', () => { const m = _cal.m + Number(b.dataset.d); _cal.m = m; if (_cal.m < 0) { _cal.m = 11; _cal.y--; } if (_cal.m > 11) { _cal.m = 0; _cal.y++; } _render(); }));
    _card.querySelectorAll('.tb-cal-d.is-data').forEach((b) => b.addEventListener('click', () => _pick(b.dataset.key)));
  }
}

// ── 选片 / 切粒度 ──

/** 选片：applyTime 换源（点层）+ renderSlice（grid，若 timeline 已绑）+ 刷新高亮。 */
function _pick(key) {
  if (!key || key === _sliceKey) return;
  _stopPlay();                    // 用户选片 → 停播
  _sliceKey = key;
  applyTime(_period, key, gridBound());   // grid 绑定时 silent（renderSlice 驱动 grid Overview，避抢刷）
  renderSlice(key);               // grid 跟随（timeline 未绑则 no-op）
  _syncActive();
}

// ── 播放（grid lerp 平滑演进 + 点层片边界离散换源）──
function _togglePlay() { _isPlaying ? _stopPlay() : _startPlay(); }
function _startPlay() {
  const slices = slicesForPeriod(_period);
  if (!slices.length) return;
  const fromK = _sliceKey || slices[0].key;
  const toK = slices[slices.length - 1].key;
  _isPlaying = true; _setIcon(true);
  playGrid(fromK, toK, _onPlaySlice, _onPlayDone);
}
function _stopPlay() {
  if (!_isPlaying) return;
  _isPlaying = false;
  stopGrid();
  _setIcon(false);
}
function _onPlaySlice(key) {            // 片边界：点层换源 + UI 跟随
  _sliceKey = key;
  applyTime(_period, key, gridBound());  // grid 绑定时 silent（_renderFrame 驱动 grid Overview，避抢刷）
  _syncActive();
}
function _onPlayDone() { _isPlaying = false; _setIcon(false); }
function _setIcon(playing) {
  const b = _card && _card.querySelector('.tb-play');
  if (b) b.innerHTML = playing ? ICON_PAUSE : ICON_PLAY;
}

function _setPeriod(p) {
  if (p === _period) return;
  _stopPlay();
  _period = p;
  const slices = slicesForPeriod(p);
  _sliceKey = slices[0] && slices[0].key;   // 切粒度 → 回到该片首片
  _render();
  if (_sliceKey) applyTime(_period, _sliceKey);
}

/** 只刷 active 高亮（避免选片重渲整卡，保 hover/动画态）。 */
function _syncActive() {
  if (!_card) return;
  const slices = slicesForPeriod(_period);
  const cur = _card.querySelector('.tb-cur');
  if (cur) cur.textContent = _sliceLabel(slices) || '—';
  _card.querySelectorAll('.tb-stop,.tb-cal-d').forEach((b) => {
    b.classList.toggle('is-active', b.dataset.key === _sliceKey && !!b.dataset.key);
  });
  const sl = _card.querySelector('.tb-slider');
  if (sl) sl.value = _sliceIndex(slices);
  const sli = _card.querySelector('.tb-slider-i');
  if (sli) sli.textContent = (_sliceIndex(slices) + 1) + '/' + slices.length;
}
