// ═══ protocol.js — chat 窗口 ↔ 主窗口(地图) 的 BroadcastChannel 协议 ═══
// 形态可插拔的关键：chat 是独立窗还是主页面浮窗，都走本协议驱动地图；主窗口 ai_qa_host.js
// 监听执行。tools.js 的每个 tool = request(type,params) → Promise<{ok,data,note}>。
//
// 消息 form（kind 区分语义）：
//   {kind:'request',  id, type, params}     chat→host 请求（需回包）
//   {kind:'response', id, ok, data, note}   host→chat 回包
//   {kind:'notify',   type, params}         chat→host 单向动作（[ref:]定位 / 附件卡）
//   {kind:'push',     type, payload}        host→chat 推送（context grounding / selection / tokens）
//   {kind:'hello' | 'bye'}                  生命周期（chat 启动→host 推 context / chat 关闭）

export const CHANNEL = 'emotion-map-ai';

// 请求类 type（chat→host，需回包）
export const REQ = {
  ENSURE_ZONE: 'ensure_zone',         // 确保有聚合域（无则生成）
  RANK_ZONES: 'rank_zones',           // 按维度排序找区域
  INSPECT_ZONE: 'inspect_zone',       // 深读某区域
  OPEN_ATTRIBUTION: 'open_attribution', // 展开 Overview 归因
};
// 单向通知 type（chat→host，不等回包）
export const NOTIFY = { FOCUS: 'focus' };
// 推送 type（host→chat）
export const PUSH = { CONTEXT: 'context', SELECTION: 'selection', TOKENS: 'tokens' };

let _ch = null;
let _reqSeq = 0;
const _pending = new Map();       // id → resolve
let _pushHandler = null;          // (type, payload) => void

function ch() {
  if (_ch) return _ch;
  _ch = new BroadcastChannel(CHANNEL);
  _ch.onmessage = (ev) => {
    const m = ev.data || {};
    if (m.kind === 'response' && _pending.has(m.id)) {
      const resolve = _pending.get(m.id);
      _pending.delete(m.id);
      resolve(m);                 // {kind:'response', id, ok, data, note}
      return;
    }
    if (m.kind === 'push' && _pushHandler) _pushHandler(m.type, m.payload);
  };
  return _ch;
}

/** 订阅主窗口推送（context grounding / selection / tokens）。panel 启动时调一次。 */
export function onPush(handler) { _pushHandler = handler; }

/** chat → host 请求（等回包）。返回 {ok, data, note}。tools.js 每个 tool 用它。 */
export function request(type, params = {}, timeoutMs = 45000) {
  return new Promise((resolve, reject) => {
    const id = 'r' + (++_reqSeq);
    const timer = setTimeout(() => {
      if (_pending.has(id)) { _pending.delete(id); reject(new Error('主窗口未响应：' + type)); }
    }, timeoutMs);
    _pending.set(id, (m) => { clearTimeout(timer); resolve(m); });
    ch().postMessage({ kind: 'request', id, type, params });
  });
}

/** chat → host 单向动作（[ref:] 点击定位 / 附件卡）。不等回包。 */
export function notify(type, params = {}) {
  try { ch().postMessage({ kind: 'notify', type, params }); } catch (_) {}
}

/** chat 启动握手（主窗口收到 hello → 推送 context/selection）。 */
export function hello() { try { ch().postMessage({ kind: 'hello' }); } catch (_) {} }
/** chat 关闭通知（主窗口可清理状态）。 */
export function bye() { try { ch().postMessage({ kind: 'bye' }); } catch (_) {} }
