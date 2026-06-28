// ═══ param-panel.js — B4 左端参数弹出栏编排器 ═══
// 紧贴 #left-panel 右缘的 #param-panel：1:2 分栏（左=样式 #settings-popover / 右=分析 heatmap|buffer）。
// 三入口（要素按钮 / 核密度 / Buffer）各自 populate 后调 openParamPanel()；本模块只管显隐 + 子页签 +
// 关闭交互（X / Escape / outside-click）。apply 链（applyPaint/generateHeatmap/generateBuffer）不在此处。
//
// 解耦：closeParamPanel 只做 UI 显隐并 dispatch `param-panel:closed`；settings.js 监听该事件清理
// _layerId 并转发 `layer-settings:closed`（sidebar 据此 renderLayerList 刷 .is-active）。

const panelEl = () => document.getElementById('param-panel');

/** 打开参数栏。tab 可选：'heatmap' | 'buffer' → 激活对应右栏子页签；不传则保留当前页签。 */
export function openParamPanel(tab) {
  const p = panelEl();
  if (!p) return;
  p.classList.add('is-open');
  p.setAttribute('aria-hidden', 'false');
  if (tab) activateTab(tab);
}

/** 关闭参数栏（仅 UI；下游经 param-panel:closed 自清理）。 */
export function closeParamPanel() {
  const p = panelEl();
  if (!p || !p.classList.contains('is-open')) return;
  p.classList.remove('is-open');
  p.setAttribute('aria-hidden', 'true');
  document.dispatchEvent(new CustomEvent('param-panel:closed'));
}

/** 激活右栏子页签（heatmap / buffer）。 */
function activateTab(tab) {
  const p = panelEl();
  if (!p) return;
  p.querySelectorAll('.pp-tab').forEach((t) => t.classList.toggle('is-active', t.dataset.ppTab === tab));
  p.querySelectorAll('.pp-pane').forEach((pane) => {
    pane.hidden = pane.dataset.ppPane !== tab;
  });
}

/** 一次性绑定：X / 子页签 / outside-click / Escape / 面板内 [data-close]。 */
export function initParamPanel() {
  const p = panelEl();
  if (!p) return;

  // X 关闭
  p.querySelector('#pp-close')?.addEventListener('click', () => closeParamPanel());

  // 子页签切换
  p.querySelectorAll('.pp-tab').forEach((t) => {
    t.addEventListener('click', () => activateTab(t.dataset.ppTab));
  });

  // 面板内 [data-close]（heatmap/buffer 取消按钮）→ 关闭
  p.querySelectorAll('[data-close]').forEach((b) => b.addEventListener('click', () => closeParamPanel()));

  // outside-click 关闭：点在面板外、且不在地图上（保护 pan/zoom）、且非三入口触发器时关闭。
  document.addEventListener('click', (e) => {
    const panel = panelEl();
    if (!panel || !panel.classList.contains('is-open')) return;
    if (panel.contains(e.target)) return;
    if (e.target.closest && e.target.closest('#map')) return;              // 地图交互不关
    if (e.target.closest && e.target.closest('.layer-kind')) return;       // 要素按钮：sidebar 自行开/切
    if (e.target.id === 'tool-heatmap' || e.target.id === 'tool-buffer' || e.target.id === 'tool-grid') return;
    if (e.target.closest && (e.target.closest('#tool-heatmap') || e.target.closest('#tool-buffer') || e.target.closest('#tool-grid'))) return;
    closeParamPanel();
  });

  // Escape 关闭
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    const panel = panelEl();
    if (panel && panel.classList.contains('is-open')) closeParamPanel();
  });
}
