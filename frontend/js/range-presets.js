// ═══ range-presets.js — 预设范围按钮（行政区/街道/社区/更新单元/用地筛选）═══
// Range tab 顶部渲染分组胶囊：
//  available=true  → 点击载入面域 + 预填 grid-tool「指定单元」做极性+归因聚合
//  available=false → 点击触发文件选择 → 解析(shp/kml/geojson)→WGS84→上传→激活→自动载入
// 用户上传的矢量按 manifest.file 名落到 DATA/boundaries/presets/（规范化 .geojson 存储）。
import { fetchRangePresets, fetchRangePreset, uploadRangePreset } from './api.js';
import { addLayer, getLayers } from './state.js';
import { renderLayer, fitBoundsTo, reorderAllZ } from './map.js';
import { renderLayerList, refreshLegend } from './sidebar.js';
import { openGridDialog } from './grid-tool.js';
import { toast } from './toast.js';
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
          <button class="rp-item${it.available ? '' : ' is-missing'}" type="button"
                  title="${it.available ? '载入并分析' : '点击上传矢量文件激活：' + it.file}">
            <span class="rp-item-label">${it.label}</span>
            <span class="rp-item-tag">${it.available ? '可用' : '待上传'}</span>
          </button>`).join('')}
      </div>
    </div>`).join('');

  // 用扁平索引回查原 item（避免 dataset 中文转义）
  const flat = [];
  for (const g of groups) for (const it of g.items) flat.push(it);
  mount.querySelectorAll('.rp-item').forEach((btn, i) => {
    btn.addEventListener('click', () => {
      const item = flat[i];
      if (!item) return;
      if (item.available) loadPresetRange(item);
      else triggerUpload(item);
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
    const L = addLayer({
      name, kind: 'polygon', fc,
      paint: { color: '#0c1c2e', lineWidth: 2, fillOn: true },
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
  const base = arr[0].name.replace(/\.[^.]+$/, '');
  try {
    const groups = groupFiles(arr);
    if (!groups.length) { toast.error('无法识别文件'); return; }
    const type = detectGroupType(groups[0]);
    if (!type) { toast.error(`${base}：无法识别格式`); return; }
    const prj = type === 'shapefile' ? await readPrj(groups[0]) : null;
    let fc = await parseGroup(groups[0], type);
    const r = reprojectFC(fc, prj);
    fc = (r && r._crsWarn) ? r.fc : r;
    const { polygons } = splitByGeometry(fc);
    if (!polygons.features.length) { toast.error(`${base}：未含面域几何`); return; }
    const res = await uploadRangePreset(item.id, polygons);
    toast.success(res.message || `已激活「${item.label}」`);
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
