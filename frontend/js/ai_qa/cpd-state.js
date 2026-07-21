// ═══ cpd-state.js — CPD 情境式渐进披露：客户端 curState 推导 ═══
// design-system.md §4 状态机：S0 开场 → S1 选范围 → S2 载图层 → S3 跑分析 → S4 读结论 → S5 收尾。
// **承重：不动 diagnose prompt（保 eval）**——curState 纯客户端从会话状态派生，不进 LLM context 必需项。
// 自动推导落 S0/S2/S3/S4（S1 range-only、S5 导出为瞬态/用户触发，不自动判；进度条 5 点但落在子集）。
//
// 信号：visible layers（state.js getLayers）/ 用户消息（#chat-messages .chat-msg-user）/ 结论卡（.aiq-conclusion）。
// 订阅 layers:changed + layer:selected + chat-messages MutationObserver → recompute → 通知 UI。

import { getLayers } from '../state.js';

export const CPD_STEPS = [
  { id: 'S0', label: '开场' },
  { id: 'S1', label: '选范围' },
  { id: 'S2', label: '载图层' },
  { id: 'S3', label: '分析' },
  { id: 'S4', label: '结论' },
];
const _IDX = Object.fromEntries(CPD_STEPS.map((s, i) => [s.id, i]));

let _cur = 'S0';
const _subs = new Set();

export function getCurState() { return _cur; }
export function getCurStepIdx() { return _IDX[_cur] ?? 0; }

/** 从会话状态派生 curState（纯客户端，不动 diagnose）。 */
export function deriveState() {
  const vis = getLayers().filter((l) => l.visible && l.kind !== 'group');
  const concl = document.querySelectorAll('#chat-messages .aiq-conclusion').length;
  const msgs = document.querySelectorAll('#chat-messages .chat-msg-user').length;
  if (concl) return 'S4';        // 有结论卡
  if (msgs) return 'S3';         // 对话中（无结论）
  if (vis.length) return 'S2';   // 有可见图层
  return 'S0';                   // 空
}

/** 重算并通知（状态变化才派发）。 */
export function recompute() {
  const next = deriveState();
  if (next !== _cur) {
    _cur = next;
    _subs.forEach((fn) => { try { fn(_cur); } catch (_) {} });
  }
  return _cur;
}

export function subscribe(fn) { _subs.add(fn); return () => _subs.delete(fn); }

/** 全局监听：图层/选中/消息变化 → recompute。由 panel.js initChatPanel 调一次。 */
export function initCpdState() {
  document.addEventListener('layers:changed', recompute);
  document.addEventListener('layer:selected', recompute);
  const list = document.getElementById('chat-messages');
  if (list && typeof MutationObserver !== 'undefined' && !list._cpdObs) {
    list._cpdObs = new MutationObserver(() => recompute());
    list._cpdObs.observe(list, { childList: true, subtree: true });
  }
  // CPD ④：#param-panel 显隐（.is-open）→ 自适应定位（紧跟抽屉/EMC 右沿）
  const pp = document.getElementById('param-panel');
  if (pp && typeof MutationObserver !== 'undefined' && !pp._cpdPos) {
    pp._cpdPos = new MutationObserver(() => { if (pp.classList.contains('is-open')) positionFloatingPanels(); });
    pp._cpdPos.observe(pp, { attributes: true, attributeFilter: ['class'] });
  }
  window.addEventListener('resize', relayoutFloats);   // 窗口缩放 → 浮层重排
  recompute();
}

/** CPD ③「自适应位置」铁律：抽屉 left 跟随 EMC 右沿（EMC 拖宽→抽屉右移，不重叠）。
 *  EMC 在 #map、抽屉在 #app-main，但 #app-main left:0=viewport 左，故 left 用 viewport 坐标直传。
 *  top 固定（EMC 暂无纵向移动）。要素按钮/param-panel 弹层同理（④ 扩展）。 */
export function positionDrawer() {
  const emc = document.getElementById('emc-panel');
  const drawer = document.getElementById('left-panel');
  if (!emc || !drawer) return;
  drawer.style.left = (emc.getBoundingClientRect().right + 10) + 'px';
}

/** CPD ④：param-panel（含内嵌 #settings-popover 要素按钮弹层）left 跟随**抽屉**右沿
 *  （抽屉开→锚抽屉；关→锚 EMC）。替代 2b 留下的 `left:var(--left-w)` 错位回归。
 *  #param-panel 在 #app-main（left:0=viewport 左），viewport 坐标直传。 */
export function positionFloatingPanels() {
  const emc = document.getElementById('emc-panel');
  const drawer = document.getElementById('left-panel');
  let anchorRight;
  if (drawer && drawer.classList.contains('is-drawer-open')) anchorRight = drawer.getBoundingClientRect().right;
  else if (emc) anchorRight = emc.getBoundingClientRect().right;
  else return;
  const left = anchorRight + 10;
  const pp = document.getElementById('param-panel');
  if (pp) {
    pp.style.left = left + 'px';
    pp.style.maxWidth = Math.max(280, window.innerWidth - left - 10) + 'px';
  }
}

/** CPD 自适应总编排：EMC 宽/位变 → 重排抽屉 + 所有浮层。 */
export function relayoutFloats() { positionDrawer(); positionFloatingPanels(); }
