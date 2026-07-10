// ═══ range-presets.js — 预设范围按钮（行政区/街道/社区/更新单元/用地筛选）═══
// Range tab 顶部渲染分组胶囊：
//  available=true  → 点击载入面域 + 预填 grid-tool「指定单元」做极性+归因聚合
//  available=false → 点击触发文件选择 → 解析(shp/kml/geojson)→WGS84→上传→激活→自动载入
// 用户上传的矢量按 manifest.file 名落到 DATA/boundaries/presets/（规范化 .geojson 存储）。
import { fetchRangePresets, fetchRangePreset, uploadRangePreset } from './api.js';
import { invalidateGeoCatalog } from './ai_qa/tools.js';   // 上传激活新预设后失效 AI 目录缓存 → 当轮 AI 可见
import { addLayer, getLayers, removeLayer } from './state.js';
import { renderLayer, fitBoundsTo, reorderAllZ, removeLayerFromMap } from './map.js';
import { renderLayerList, refreshLegend } from './sidebar.js';
import { openGridDialog } from './grid-tool.js';
import { landuseColorForFc } from './landuse_colors.js';   // 用地预设 → 制图规范附录B 标准色（读 DLMC 落色）
import { toast } from './toast.js';
import { SIZE_BLOCK } from './dialog.js';
import {
  groupFiles, detectGroupType, parseGroup, reprojectFC, readPrj,
  splitByGeometry, fcBBox,
} from './import.js';

const MOUNT_ID = 'range-presets';
let _uploadInput = null;   // 共用 hidden file input（missing 按钮触发）

/** 初始化：建文件选择器 + 首渲染。由 main.js 调用。 */
export async function initRangePresets() {
  _uploadInput = document.createElement('input');
  _uploadInput.type = 'file';
  _uploadInput.accept = '.geojson,.json,.kml,.shp,.dbf,.shx,.prj,.cpg,.zip';
  _uploadInput.hidden = true;
  document.body.appendChild(_uploadInput);
  await renderRangePresets();
}

/** 拉取 manifest → 渲染分组胶囊 + 绑定点击。可重复调用（上载后刷新）。 */
export async function renderRangePresets() {
  const mount = document.getElementById(MOUNT_ID);
  if (!mount) return;
  let groups = [];
  try { groups = await fetchRangePresets(); }
  catch (e) { mount.innerHTML = '<div class="rp-empty">预设范围加载失败（确认后端已启动）</div>'; return; }
  if (!groups || !groups.length) { mount.innerHTML = '<div class="rp-empty">暂无预设范围</div>'; return; }

  mount.innerHTML = groups.map((g) => `
    <div class="rp-group">
      <div class="rp-group-label">${g.group}</div>
      <div class="rp-items">
        ${g.items.map((it) => `
          <div class="rp-item-split${it.available ? '' : ' is-missing'}">
            <button class="rp-item-main" type="button" data-id="${it.id}" data-action="${it.available ? 'load' : 'upload'}"
                    title="${it.available ? '载入并分析' : '上传矢量文件激活：' + it.file}">
              <span class="rp-item-label">${it.label}</span>
              <span class="rp-item-tag">${it.available ? '可用' : '待上传'}</span>
            </button>
            <button class="rp-item-plus" type="button" data-id="${it.id}" data-action="upload"
                    title="${it.available ? '重新上传范围（替换）' : '上传范围：' + it.file}" aria-label="上传或替换范围">
              <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            </button>
          </div>`).join('')}
      </div>
    </div>`).join('');

  // 主按钮：可用→载入分析；待上传→上传。"+" 按钮：始终上传/替换（已上传范围的永久重传入口）。
  const flat = [];
  for (const g of groups) for (const it of g.items) flat.push(it);
  mount.querySelectorAll('[data-action]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const item = flat.find((x) => x.id === btn.dataset.id);
      if (!item) return;
      if (btn.dataset.action === 'upload') triggerUpload(item);
      else loadPresetRange(item);   // action === 'load'（仅 available 时）
    });
  });
}

/** 载入预设面域 → addLayer polygon + fitBounds；若有情绪点 → 预填 grid-tool zonal。 */
async function loadPresetRange(item) {
  try {
    const res = await fetchRangePreset(item.id);
    if (!res || !res.available || !res.geojson) { toast.info('该预设范围文件未就绪'); return; }
    const fc = res.geojson;
    const name = `范围·${item.label}`;
    // 替换语义：点"+"重传后不堆叠——移除同名旧预设层再新建（分析层独立不受影响）
    for (const l of getLayers()) {
      if (l.name === name) { removeLayer(l.id); removeLayerFromMap(l.id); }
    }
    // 用地预设(land_*) = 制图规范附录B 标准色（优先读要素 DLMC 落色，label 回退；fillOpacity 0.6 让规范色清晰可辨，否则 addLayer 默认 0.15 几乎看不见）。
    const _isLand = item.id.startsWith('land_');
    const L = addLayer({
      name, kind: 'polygon', fc,
      // 行政区 = 中性参考边界（非数据）浅灰 #d8d8d8；用地预设 = 标准色；其余 preset 不指定 → addLayer 按 PRESET_COLORS 自动配。
      paint: {
        lineWidth: _isLand ? 1 : 2,
        fillOn: true,
        fillOpacity: _isLand ? 0.6 : 0.15,
        color: item.id === 'admin_district' ? '#d8d8d8' : (_isLand ? landuseColorForFc(fc, item.label) : undefined),
      },
    });
    L.srcName = name;
    renderLayer(L);
    renderLayerList(); refreshLegend(); reorderAllZ();
    const bb = fcBBox(fc); if (bb) fitBoundsTo(bb);
    if (hasEmotionPoints()) {
      openGridDialog(null, {
        analysis: 'zonal', polygonLayer: L.id,
        nameCol: item.nameField || res.nameField || null,
      });
    } else {
      toast.success(`已载入「${item.label}」面域`);
      toast.info('请先导入情绪点数据，再用「网格·指定单元」分析', 5000);
    }
  } catch (e) {
    console.error('[preset-load]', e);
    toast.error(`载入预设失败：${e.message || e}`);
  }
}

/** 触发文件选择 → 解析 → 上传 → 刷新 → 自动载入。 */
function triggerUpload(item) {
  if (!_uploadInput) return;
  _uploadInput.value = '';
  _uploadInput.onchange = async (e) => {
    const fs = e.target.files;
    if (!fs || !fs.length) return;
    await uploadPresetFile(item, fs);
  };
  _uploadInput.click();
}

async function uploadPresetFile(item, fileList) {
  const arr = Array.from(fileList);
  const total = arr.reduce((s, f) => s + (f.size || 0), 0);
  if (total > SIZE_BLOCK) {   // 浏览器解析 + 代理 POST 大文件会 OOM/超时；超大矢量走服务端 ingest
    toast.error(`文件过大（${(total / 1024 / 1024).toFixed(0)} MB > ${SIZE_BLOCK / 1024 / 1024} MB）。请走服务端：放进 DATA/boundaries/presets/ 或用 SCRIPT/ingest_landuse_preset.py`, 6000);
    return;
  }
  const base = arr[0].name.replace(/\.[^.]+$/, '');
  try {
    const groups = groupFiles(arr);
    if (!groups.length) { toast.error('无法识别文件'); return; }
    const type = detectGroupType(groups[0]);
    if (!type) { toast.error(`${base}：无法识别格式`); return; }
    const prj = type === 'shapefile' ? await readPrj(groups[0]) : null;
    let fc = await parseGroup(groups[0], type);
    const r = reprojectFC(fc, { prjWkt: prj });
    fc = (r && r._crsWarn) ? r.fc : r;
    const { polygons } = splitByGeometry(fc);
    if (!polygons.features.length) { toast.error(`${base}：未含面域几何`); return; }
    const res = await uploadRangePreset(item.id, polygons);
    toast.success(res.message || `已激活「${item.label}」`);
    invalidateGeoCatalog();                           // 失效 AI 目录缓存：下一轮问答即可用新预设，不必刷新页面
    await renderRangePresets();                       // 刷新按钮态
    await loadPresetRange({ ...item, available: true });   // 自动载入
  } catch (e) {
    console.error('[preset-upload]', e);
    toast.error(`上传失败：${e.message || e}`);
  }
}

/** 是否存在可分析的情绪点层（L2 三极性 / L1 confidence）。 */
function hasEmotionPoints() {
  return getLayers().some((l) => l.kind === 'point' && l.fc && l.fc.features && l.fc.features.length &&
    (l.colorMode === 'l2-positive' || l.colorMode === 'l2-negative' ||
     l.colorMode === 'l2-neutral' || l.colorMode === 'confidence'));
}
