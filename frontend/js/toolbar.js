// ═══ toolbar.js — draw-tool select, Import/Export/M actions, basemap popover ═══
import { setBasemapVeil, getBasemapVeilPct } from './map.js';   // CB-43 底图淡化（地图域控件·popover 属主在此接线）

/**
 * @param {object}  handlers
 * @param {(tool:string)=>void}  handlers.onTool      draw tool selected (select/point/line/...)
 * @param {()=>void}             handlers.onImport    open left sidebar Import
 * @param {({format,desensitize})=>void} handlers.onExport
 * @param {(key:string)=>void}   handlers.onBasemap   basemap key switched
 */
export function initToolbar({ onTool, onImport, onExport, onBasemap } = {}) {
  // ── Draw tools: single-select active group (S/P/L/Po/R/C) ──
  const drawTools = Array.from(document.querySelectorAll('.draw-tool[data-tool]'));
  drawTools.forEach((btn) => {
    btn.addEventListener('click', () => {
      const tool = btn.dataset.tool;
      if (tool === 'more') {                 // dropdown placeholder
        console.log('[toolbar] more-tools (Phase 2)');
        return;
      }
      drawTools.forEach((b) => {
        if (b.dataset.tool !== 'more') {
          b.setAttribute('aria-pressed', 'false');
          b.classList.remove('is-active');
        }
      });
      btn.setAttribute('aria-pressed', 'true');
      btn.classList.add('is-active');
      if (onTool) onTool(tool);
      console.log('[toolbar] tool =', tool, '(Phase 2 wiring)');
    });
  });

  // ── Right group: Import / Export / M / i ──
  document.querySelector('[data-action="import"]')?.addEventListener('click', () => {
    if (onImport) onImport();
  });
  document.querySelector('[data-action="export"]')?.addEventListener('click', () => {
    document.getElementById('modal-export').showModal();
  });
  document.querySelector('[data-action="basemap"]')?.addEventListener('click', (e) => {
    e.stopPropagation();
    togglePopover();
  });
  document.querySelector('[data-action="info"]')?.addEventListener('click', () => {
    document.getElementById('modal-info')?.showModal();
  });
  // 项目架构拓扑图（独立只读页，自包含无 BroadcastChannel，不踩 EMC 独立窗 5.33→5.34 删除的坑）
  document.querySelector('[data-action="topology"]')?.addEventListener('click', () => {
    window.open('topology.html', 'emotion_map_topology',
      'width=1400,height=900,menubar=no,toolbar=no,location=no,status=no,resizable=yes');
  });

  // ── Basemap popover cells（CB-31：不乐观设 is-active，由 basemap:switched 事件统一同步——含不可达回退 DEFAULT 的激活态回滚）──
  document.querySelectorAll('.bm-cell').forEach((cell) => {
    cell.addEventListener('click', () => {
      if (onBasemap) onBasemap(cell.dataset.basemap);
      document.getElementById('basemap-popover').hidden = true;
    });
  });
  // 探活结果标灰（is-blocked 非 disabled 属性→仍可点重试探活）+ 切换/回退同步激活态（单一权威源）
  document.addEventListener('basemap:health', (e) => {
    const { key, health } = e.detail || {};
    document.querySelectorAll(`.bm-cell[data-basemap="${key}"]`).forEach((c) => {
      c.classList.toggle('is-blocked', health === 'blocked');
      c.title = health === 'blocked' ? '当前网络不可达，点击重试' : '';
    });
  });
  document.addEventListener('basemap:switched', (e) => {
    if (e.detail) setActiveBasemap(e.detail.key);
  });
  // close popover on outside click
  document.addEventListener('click', (e) => {
    const pop = document.getElementById('basemap-popover');
    if (pop.hidden) return;
    if (!pop.contains(e.target) && !e.target.closest('[data-action="basemap"]')) pop.hidden = true;
  });

  // ── CB-43 底图淡化（全局总调节器·白罩层不透明度）：滑条拖动=即时预览不落盘(input)、松手持久化(change)；
  //    数字框=Enter/失焦提交并钳制 0-100；双击数值=归零。UI 三件套（滑条/数字/百分比）单向同步自 setBasemapVeil 返回的生效值。 ──
  const veilSlider = document.getElementById('bm-veil-slider');
  const veilNum = document.getElementById('bm-veil-num');
  const veilVal = document.getElementById('bm-veil-val');
  const syncVeilUi = (pct) => {
    if (veilVal) veilVal.textContent = `${pct}%`;
    if (veilSlider && Number(veilSlider.value) !== pct) veilSlider.value = String(pct);
    if (veilNum && Number(veilNum.value) !== pct) veilNum.value = String(pct);
  };
  syncVeilUi(getBasemapVeilPct());   // 初始化：恢复记忆值（map 侧已按存储值敷罩）
  veilSlider?.addEventListener('input', () => { syncVeilUi(setBasemapVeil(veilSlider.value, { live: true })); });
  veilSlider?.addEventListener('change', () => { setBasemapVeil(veilSlider.value); });
  veilNum?.addEventListener('change', () => { syncVeilUi(setBasemapVeil(veilNum.value)); });
  veilNum?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); veilNum.blur(); }   // Enter 即提交（触发 change·钳制在 setBasemapVeil）
  });
  veilVal?.addEventListener('dblclick', () => { syncVeilUi(setBasemapVeil(0)); });

  // ── Modal close buttons (Export + Info) ──
  document.querySelectorAll('[data-close]').forEach((b) =>
    b.addEventListener('click', () => { b.closest('dialog')?.close(); }));
  // 格式切换 → 显隐 CRS（仅 shp）/ 几何表示（仅 csv）行
  const fmtSel = document.getElementById('export-format');
  const syncExportRows = () => {
    const f = fmtSel ? fmtSel.value : 'geojson';
    const crsRow = document.getElementById('export-crs-row');
    const geomRow = document.getElementById('export-geom-row');
    if (crsRow) crsRow.hidden = (f !== 'shp');
    if (geomRow) geomRow.hidden = (f !== 'csv');
  };
  fmtSel?.addEventListener('change', syncExportRows);

  document.getElementById('export-confirm')?.addEventListener('click', () => {
    const format = document.getElementById('export-format').value;
    const desensitize = document.getElementById('export-desensitize').checked;
    const crs = document.getElementById('export-crs')?.value || 'wgs84';
    const geom_csv = document.getElementById('export-geom')?.value || 'wkt';
    const scope = document.getElementById('export-scope')?.value || 'selected';
    if (onExport) onExport({ format, crs, geom_csv, scope, desensitize });
    document.getElementById('modal-export').close();
  });
}

function togglePopover() {
  const pop = document.getElementById('basemap-popover');
  pop.hidden = !pop.hidden;
}

/** Mark the active basemap cell (keeps popover in sync on programmatic switch). */
export function setActiveBasemap(key) {
  document.querySelectorAll('.bm-cell').forEach((c) =>
    c.classList.toggle('is-active', c.dataset.basemap === key));
}
