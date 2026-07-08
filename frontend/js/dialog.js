// ═══ dialog.js — Import 解析配置弹窗（1:1 geojson.io + 源坐标系选择）═══
// 按格式自适应渲染配置区：
//   • CSV      → 文件格式 + 解析方式(Kind) + 分隔符 + 经/纬列(或 WKT/GeoJSON/折线列) + 类型推断
//   • GeoJSON/TopoJSON/KML/GPX/Shapefile → 文件格式
//   • 所有格式 → 源坐标系(CRS)选择区（自动检测/手动覆盖）+ 目标 WGS84
// onConfirm(selected: { type, config }[]) —— config = { csv?, crs }
// 复用 Export modal 的 .app-dialog / .btn / .select / .form-label（dialog.css）。

import { FILE_TYPES, CRS_PRESETS, resolveCrsChoice, csvHeader, guessLatLon } from './import.js';

export const SIZE_WARN = 10 * 1024 * 1024;    // 10 MB → warn inline
export const SIZE_BLOCK = 200 * 1024 * 1024;  // 200 MB → block Import / preset upload（>此值走服务端 ingest）

const DELIM_OPTS = [
  { v: ',', l: '逗号  ,' },
  { v: ';', l: '分号  ;' },
  { v: '\\t', l: 'Tab' },
  { v: '|', l: '竖线  |' },
];
const KIND_OPTS = [
  { v: 'coords',   l: '坐标列', en: 'Coordinates' },
  { v: 'wkt',      l: 'WKT 列', en: 'WKT Column' },
  { v: 'geojson',  l: 'GeoJSON 列', en: 'GeoJSON Column' },
  { v: 'polyline', l: '编码折线', en: 'Encoded polylines' },
];

let _root = null;

function root() {
  if (_root) return _root;
  _root = document.getElementById('modal-import');
  if (!_root) {
    _root = document.createElement('dialog');
    _root.id = 'modal-import';
    _root.className = 'app-dialog imp-dialog';
    document.body.appendChild(_root);
  }
  return _root;
}

function fmtSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}
function groupSize(group) {
  return group.files.reduce((s, f) => s + (f.size || 0), 0);
}
function groupName(group) {
  if (group.kind === 'bundle') {
    const shp = group.files.find((f) => /\.shp$/i.test(f.name));
    return (shp ? shp.name : group.files[0].name).replace(/\.[^.]+$/, '');
  }
  return group.files[0].name;
}

/** 廉价读取文件前 8KB 文本（够表头/首坐标采样）。 */
function headText(file) {
  return file.slice(0, 8192).text();
}

/** 首个 [num,num] 坐标（geojson/topojson 文本正则）。null=未命中。 */
function firstCoordFromGeoJSON(text) {
  const m = text.match(/\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]/);
  return m ? [Number(m[1]), Number(m[2])] : null;
}
/** 首个 <coordinates>x,y 文本（kml/gpx）。 */
function firstCoordFromXml(text) {
  const m = text.match(/<coordinates>\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*[,<]/);
  return m ? [Number(m[1]), Number(m[2])] : null;
}
const looksProjected = ([x, y]) => Math.abs(x) > 180 || Math.abs(y) > 90;

/** 为某组算「检测到」提示文（廉价，基于 probe.sample 采样首坐标）。 */
function detectLabel(group, type, probe) {
  if (type === 'shapefile') {
    const hasPrj = group.files.some((f) => /\.prj$/i.test(f.name));
    return hasPrj ? '已含 .prj → 默认「自动」即用之' : '无 .prj → 按投影启发式（建议手动选择）';
  }
  const s = probe && probe.sample;
  if (s) return looksProjected(s) ? '首坐标为大数 → 疑似投影，建议手动选择' : '首坐标为经纬度 → 疑似 WGS84 / GCJ-02';
  if (type === 'csv') return '按经纬度列数值判断（大数=投影）';
  return '导入后按坐标范围判断';
}

/**
 * @param groups        from import.groupFiles
 * @param detectedTypes from import.detectGroupType per group
 * @param onConfirm(selected[{type,config}])  chosen format + config per group
 * @param onCancel()
 */
export async function openImportDialog({ groups, detectedTypes, onConfirm, onCancel }) {
  const dlg = root();

  // ── 预读：CSV 表头 + 各组首坐标采样（廉价，并行）──
  const probes = await Promise.all(groups.map(async (g, i) => {
    const type = detectedTypes[i];
    try {
      if (type === 'csv') {
        const info = csvHeader(await headText(g.files[0]));
        // 采样第二行（首数据行）的经纬度数值判断投影
        const sample = await sampleCsvCoord(g.files[0], info);
        return { type, csvInfo: info, sample };
      }
      if (type === 'geojson' || type === 'topojson') {
        return { type, sample: firstCoordFromGeoJSON(await headText(g.files[0])) };
      }
      if (type === 'kml' || type === 'gpx') {
        return { type, sample: firstCoordFromXml(await headText(g.files[0])) };
      }
    } catch (e) { /* ignore probe errors */ }
    return { type };
  }));

  const totalSize = groups.reduce((s, g) => s + groupSize(g), 0);
  const blocked = totalSize >= SIZE_BLOCK;

  // ── body: 每组一块 ──
  const rows = groups.map((g, i) => groupHtml(g, i, detectedTypes[i], probes[i])).join('');
  const warning = totalSize >= SIZE_WARN
    ? `<div class="imp-warn">${blocked ? '文件过大（>' + fmtSize(SIZE_BLOCK) + '），无法导入。' : '文件较大（' + fmtSize(totalSize) + '），解析可能较慢。'}</div>`
    : '';

  dlg.innerHTML = `
    <div class="dialog-head">
      <span class="dialog-title">导入 ${groupName(groups[0])}${groups.length > 1 ? ' 等 ' + groups.length + ' 项' : ''}</span>
      <button class="dialog-close" data-close>&times;</button>
    </div>
    <div class="dialog-body imp-body">${rows}${warning}</div>
    <div class="dialog-foot">
      <button class="btn btn-secondary" data-close>取消</button>
      <button class="btn btn-primary" id="imp-go" ${blocked ? 'disabled' : ''}>导入</button>
    </div>`;

  // ── 交互绑定 ──
  // 格式切换 → 显隐 CSV 配置区；同步「检测到」文案
  dlg.querySelectorAll('.imp-format').forEach((sel) => {
    sel.addEventListener('change', () => {
      const grp = sel.closest('.imp-group');
      const idx = Number(grp.dataset.idx);
      grp.querySelector('.imp-cfg-csv').hidden = sel.value !== 'csv';
      refreshDetect(grp, probes[idx], sel.value);
    });
  });
  // CSV Kind 切换 → 显隐对应列选择行
  dlg.querySelectorAll('.imp-kind').forEach((wrap) => {
    wrap.addEventListener('change', (e) => {
      if (e.target.name !== 'kind') return;
      const grp = wrap.closest('.imp-group');
      const kind = e.target.value;
      grp.querySelector('.imp-cols-coords').hidden = kind !== 'coords';
      grp.querySelector('.imp-cols-wkt').hidden = kind !== 'wkt';
      grp.querySelector('.imp-cols-geojson').hidden = kind !== 'geojson';
      grp.querySelector('.imp-cols-polyline').hidden = kind !== 'polyline';
    });
  });
  // CRS 预设切换 → 自定义输入区显隐
  dlg.querySelectorAll('.imp-crs-sel').forEach((sel) => {
    sel.addEventListener('change', () => {
      const grp = sel.closest('.imp-group');
      grp.querySelector('.imp-crs-custom').hidden = sel.value !== 'custom';
    });
  });

  const close = () => { dlg.close(); if (onCancel) onCancel(); };
  dlg.querySelectorAll('[data-close]').forEach((b) => b.addEventListener('click', close));
  dlg.addEventListener('cancel', close, { once: true });

  dlg.querySelector('#imp-go').addEventListener('click', () => {
    if (blocked) return;
    const selected = groups.map((g, i) => collectGroup(dlg.querySelector(`.imp-group[data-idx="${i}"]`)));
    dlg.close();
    if (onConfirm) onConfirm(selected);
  });

  if (!dlg.open) dlg.showModal();
}

/** 渲染单组 HTML。 */
function groupHtml(group, idx, type, probe) {
  const isBundle = group.kind === 'bundle';
  const opts = FILE_TYPES.map(
    (t) => `<option value="${t.id}" ${t.id === type ? 'selected' : ''}>${t.label}</option>`
  ).join('');
  const fileList = isBundle
    ? `<ul class="imp-files">${group.files.map((f) => `<li>${f.name}</li>`).join('')}</ul>`
    : '';
  const meta = isBundle
    ? `<span class="imp-meta">组合文件 · ${group.files.length} 个</span>`
    : `<span class="imp-meta">${fmtSize(groupSize(group))}</span>`;

  const csvBlock = type === 'csv' ? csvCfgHtml(probe) : '';
  const crsBlock = crsHtml(probe, type, group);

  return `
    <div class="imp-group" data-idx="${idx}">
      <div class="imp-name">${groupName(group)} ${meta}</div>
      ${fileList}
      <div class="imp-section">
        <span class="form-label">文件格式 / Format</span>
        <select class="select imp-format">${opts}</select>
      </div>
      <div class="imp-cfg-csv" ${type === 'csv' ? '' : 'hidden'}>${csvBlock}</div>
      ${crsBlock}
    </div>`;
}

/** CSV 解析配置区（1:1 geojson.io 截图）。 */
function csvCfgHtml(probe) {
  const info = probe && probe.csvInfo;
  const cols = (info && info.columns) || [];
  const guess = guessLatLon(cols);
  const detDelim = info && info.delimiter;
  const defDelim = detDelim === '\t' ? '\\t' : (detDelim || ',');

  const delimOpts = DELIM_OPTS.map((d) => `<option value="${d.v}" ${d.v === defDelim ? 'selected' : ''}>${d.l}</option>`).join('');
  const kindRadios = KIND_OPTS.map((k, i) => `
    <label class="imp-kind-opt"><input type="radio" name="kind" value="${k.v}" ${i === 0 ? 'checked' : ''} /> <span>${k.l}<span class="imp-en"> ${k.en}</span></span></label>`).join('');

  const colOpts = (sel) => cols.length
    ? `<option value="">（自动）</option>` + cols.map((c) => `<option value="${esc(c)}" ${c === sel ? 'selected' : ''}>${esc(c)}</option>`).join('')
    : `<option value="">（读取表头中…）</option>`;

  return `
    <div class="imp-cfg">
      <div class="imp-section">
        <span class="form-label">解析方式 / Kind</span>
        <div class="imp-kind">${kindRadios}</div>
      </div>
      <div class="imp-cols imp-cols-coords">
        <div class="imp-col">
          <span class="form-label">分隔符 / Delimiter</span>
          <select class="select imp-delim">${delimOpts}</select>
        </div>
        <div class="imp-col">
          <span class="form-label">纬度列 / Latitude</span>
          <select class="select imp-lat">${colOpts(guess.lat)}</select>
        </div>
        <div class="imp-col">
          <span class="form-label">经度列 / Longitude</span>
          <select class="select imp-lon">${colOpts(guess.lon)}</select>
        </div>
      </div>
      <div class="imp-cols imp-cols-wkt" hidden>
        <span class="form-label">WKT 列</span>
        <select class="select imp-wkt">${colOpts('')}</select>
      </div>
      <div class="imp-cols imp-cols-geojson" hidden>
        <span class="form-label">GeoJSON 列</span>
        <select class="select imp-geojson">${colOpts('')}</select>
      </div>
      <div class="imp-cols imp-cols-polyline" hidden>
        <span class="form-label">折线列 / Polyline</span>
        <select class="select imp-polyline">${colOpts('')}</select>
      </div>
      <label class="imp-infer"><input type="checkbox" class="imp-infertypes" checked /> <span>类型推断 / Infer types</span></label>
      <div class="imp-infer-hint">CSV 本身只含字符串。勾选后将数字、布尔、空值自动推断。</div>
    </div>`;
}

/** 源坐标系选择区（所有格式通用）。 */
function crsHtml(probe, type, group) {
  const det = detectLabel(group, type, probe);
  const opts = CRS_PRESETS.map((c) => `<option value="${c.id}">${c.label}</option>`).join('');
  return `
    <div class="imp-crs">
      <div class="imp-crs-head">
        <span class="form-label">源坐标系 / Source CRS</span>
        <span class="imp-crs-det" data-det>检测到：${det}</span>
      </div>
      <select class="select imp-crs-sel">${opts}</select>
      <div class="imp-crs-custom" hidden>
        <input class="input imp-crs-epsg" placeholder="EPSG 代码，如 4546" />
        <input class="input imp-crs-proj" placeholder="或 proj4 字符串，如 +proj=tmerc +lon_0=111 ..." />
      </div>
      <div class="imp-crs-tgt">→ 目标坐标系：WGS84 (EPSG:4326) · 与底图一致</div>
    </div>`;
}

/** 格式切换后刷新「检测到」文案。 */
function refreshDetect(grp, probe, type) {
  const det = grp.querySelector('[data-det]');
  if (!det) return;
  det.textContent = '检测到：' + detectLabel(grp, type, probe);
}

/** 采样 CSV 首数据行的经/纬度数值（廉价；返回 [lon,lat] 或 null）。 */
async function sampleCsvCoord(file, info) {
  if (!info || !info.columns.length) return null;
  const guess = guessLatLon(info.columns);
  if (!guess.lat || !guess.lon) return null;
  const text = await headText(file);
  const lines = text.replace(/\r\n/g, '\n').split('\n');
  if (lines.length < 2) return null;
  const delim = info.delimiter;
  const header = lines[0].split(delim);
  const li = header.indexOf(guess.lat);
  const lo = header.indexOf(guess.lon);
  if (li < 0 || lo < 0) return null;
  const cells = lines[1].split(delim);
  const la = Number(cells[li]);
  const lo2 = Number(cells[lo]);
  if (!Number.isFinite(la) || !Number.isFinite(lo2)) return null;
  return [lo2, la];   // [lon, lat]
}

/** 收集单组的 { type, config }。 */
function collectGroup(grp) {
  const type = grp.querySelector('.imp-format').value;
  const config = {};
  if (type === 'csv') {
    const kind = grp.querySelector('input[name="kind"]:checked')?.value || 'coords';
    config.csv = {
      kind,
      delimiter: grp.querySelector('.imp-delim')?.value || ',',
      latfield: selVal(grp, '.imp-lat'),
      lonfield: selVal(grp, '.imp-lon'),
      wktField: selVal(grp, '.imp-wkt'),
      geojsonField: selVal(grp, '.imp-geojson'),
      polylineField: selVal(grp, '.imp-polyline'),
      inferTypes: grp.querySelector('.imp-infertypes')?.checked ?? true,
    };
  }
  const crsPreset = grp.querySelector('.imp-crs-sel').value;
  const custom = crsPreset === 'custom' ? {
    epsg: grp.querySelector('.imp-crs-epsg')?.value || '',
    proj: grp.querySelector('.imp-crs-proj')?.value || '',
  } : null;
  config.crs = resolveCrsChoice(crsPreset, custom);
  return { type, config };
}
function selVal(grp, sel) {
  const v = grp.querySelector(sel)?.value || '';
  return v;
}
function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
