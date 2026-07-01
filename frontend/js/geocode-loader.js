// ═══ geocode-loader.js — 地点反查(reverseGeocode) 全局加载指示器 ═══
// 驱动「搜索放大镜(收起态)外圈进度环」（search-bar.js 订阅）。
//
// 单个 HTTP 请求无真实进度百分比 → 模拟（fake progress，类 NProgress）：
//   start（首个 inflight）→ 进度从 10% 渐近爬向 90%（每 tick 缩小剩余差距的 12%，永不触底）；
//   done（全部 inflight 结束）→ 跳 100%（绿色）→ 停留 1s → 淡出 300ms → reset 0/idle；
//   done/fade 期间新请求到 → 取消淡出，回 loading。
//
// 仅包裹 popup(cell-popup) + tip-popup 的 reverseGeocode（地点反查）；
// 搜索框自身 searchPlaces 不接入（有自己的 spinner），符合「仅地点反查」。

const _subs = new Set();
let _inflight = 0;
let _progress = 0;
let _phase = 'idle';        // 'idle' | 'loading' | 'done' | 'fade'
let _simTimer = null;
let _holdTimer = null;
let _fadeTimer = null;

const SIM_TICK_MS = 90;
const HOLD_MS = 1000;
const FADE_MS = 320;

function _emit() {
  const snap = { progress: _progress, phase: _phase, inflight: _inflight };
  _subs.forEach((fn) => { try { fn(snap); } catch (_e) { /* 订阅者异常忽略，不影响他人 */ } });
}

function _clearTimers() {
  if (_simTimer) { clearInterval(_simTimer); _simTimer = null; }
  if (_holdTimer) { clearTimeout(_holdTimer); _holdTimer = null; }
  if (_fadeTimer) { clearTimeout(_fadeTimer); _fadeTimer = null; }
}

function _startSim() {
  if (_simTimer) return;
  _simTimer = setInterval(() => {
    // 渐近 90%：每 tick +剩余差距的 12%，下限 +0.6（避免后期龟爬）——留 done 跳满
    _progress = Math.min(90, _progress + Math.max(0.6, (90 - _progress) * 0.12));
    _emit();
  }, SIM_TICK_MS);
}

function _toDone() {
  _clearTimers();
  _progress = 100;
  _phase = 'done';
  _emit();
  _holdTimer = setTimeout(() => {                 // 绿停留 1s → 淡出
    _phase = 'fade';
    _emit();
    _fadeTimer = setTimeout(() => {               // 淡出 300ms → reset
      _progress = 0;
      _phase = 'idle';
      _emit();
    }, FADE_MS);
  }, HOLD_MS);
}

/** 包裹一个 reverseGeocode promise，纳入加载指示；返回原 promise 结果。 */
export function trackGeocode(p) {
  _inflight += 1;
  if (_phase !== 'loading') {                       // idle/done/fade →（重）入 loading
    _clearTimers();
    _phase = 'loading';
    _progress = 10;                                 // 初始小填充，避免空环→满环闪跳
    _startSim();
    _emit();
  }
  return Promise.resolve(p).finally(() => {
    _inflight = Math.max(0, _inflight - 1);
    if (_inflight === 0 && _phase === 'loading') _toDone();
  });
}

/** 订阅加载状态变化。返回取消订阅函数。fn 收 { progress, phase, inflight }。 */
export function subscribe(fn) {
  _subs.add(fn);
  return () => _subs.delete(fn);
}
