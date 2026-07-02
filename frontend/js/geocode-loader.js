// ═══ geocode-loader.js — 全局加载指示器（统一放大镜外环 · 多 kind 分色）═══
// 驱动「搜索放大镜外圈进度环」（search-bar.js 订阅）。所有异步读取/生成统一到此环，
// 按 kind 分色区分；完成统一橙色。以后新增读取接入 track(<kind>, p) 即可（search-bar 自动显色）。
//
// kind → 加载色（完成统一 DONE_COLOR 橙）：
//   geocode     地点反查(popup/tip reverseGeocode)         蓝 #4285F4
//   generation  生成地图(网格/缓冲/地形，后端 API)          青 #1abc9c
//
// 单 HTTP 无真实进度 → 模拟（类 NProgress）：
//   start（任一 kind inflight）→ 10%→90% 渐近爬升；
//   done（全部 kind inflight 结束）→ 跳 100%（橙）→ 停 1s → 淡出 300ms → reset 0/idle。
//   多 kind 并存 → 环色按 KIND_PRIORITY 取最高者（生成 > 反查）。

const KIND_COLORS = { geocode: '#4285F4', generation: '#1abc9c' };
const DONE_COLOR = '#F5A623';                       // 读取成功（统一橙；替原绿 #3DBA3D，线宽不变）
const KIND_PRIORITY = ['generation', 'geocode'];    // 多 kind 并存时环色优先级（生成色优先显）

const _subs = new Set();
const _inflight = {};        // kind → inflight count
let _progress = 0;
let _phase = 'idle';         // 'idle' | 'loading' | 'done' | 'fade'
let _simTimer = null;
let _holdTimer = null;
let _fadeTimer = null;

const SIM_TICK_MS = 90;
const HOLD_MS = 1000;
const FADE_MS = 320;

function _activeKinds() { return KIND_PRIORITY.filter((k) => (_inflight[k] || 0) > 0); }

function _color() {
  if (_phase === 'done') return DONE_COLOR;
  const k = _activeKinds()[0];
  return k ? KIND_COLORS[k] : 'var(--geojson-color-text-tertiary, #999)';
}

function _emit() {
  const snap = { progress: _progress, phase: _phase, color: _color(), kinds: _activeKinds() };
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
  _holdTimer = setTimeout(() => {                 // 橙停留 1s → 淡出
    _phase = 'fade';
    _emit();
    _fadeTimer = setTimeout(() => {               // 淡出 300ms → reset
      _progress = 0;
      _phase = 'idle';
      _emit();
    }, FADE_MS);
  }, HOLD_MS);
}

/** 包裹一个异步 promise，纳入加载指示（按 kind 分色）；返回原 promise 结果。
 *  kind ∈ {'geocode','generation', ...}（新 kind 自动入 KIND_COLORS 即可分色，未注册退灰）。 */
export function track(kind, p) {
  _inflight[kind] = (_inflight[kind] || 0) + 1;
  if (_phase !== 'loading') {                       // idle/done/fade →（重）入 loading
    _clearTimers();
    _phase = 'loading';
    _progress = 10;                                 // 初始小填充，避免空环→满环闪跳
    _startSim();
  }
  _emit();                                          // 新 kind 加入即刷色（可能切生成色）
  return Promise.resolve(p).finally(() => {
    _inflight[kind] = Math.max(0, (_inflight[kind] || 0) - 1);
    if (_activeKinds().length === 0 && _phase === 'loading') _toDone();
    else _emit();                                   // 仍有 kind 在跑 → 仅刷色/进度
  });
}

/** 地点反查（popup/tip-popup reverseGeocode）接入。 */
export function trackGeocode(p) { return track('geocode', p); }

/** 生成地图（grid/buffer/terrain 后端 API）接入。 */
export function trackGeneration(p) { return track('generation', p); }

/** 订阅加载状态变化。返回取消订阅函数。fn 收 { progress, phase, color, kinds }。 */
export function subscribe(fn) {
  _subs.add(fn);
  return () => _subs.delete(fn);
}
