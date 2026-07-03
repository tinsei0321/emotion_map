// ═══ dialog.js — Import confirm dialog (geojson.io-style, always shown) ═══
// Adapts to the import payload:
//   • single file → filename + format dropdown
//   • shapefile bundle → "(N files)" + filename list + format (Shapefile)
//   • multiple groups → one row per group, each with its own format dropdown
// Reuses the Export modal's .app-dialog / .btn classes (dialog.css).

import { FILE_TYPES } from './import.js';

export const SIZE_WARN = 10 * 1024 * 1024;    // 10 MB → warn inline
export const SIZE_BLOCK = 200 * 1024 * 1024;  // 200 MB → block Import / preset upload（原 80MB；调高以容正常大文件。>此值走服务端 ingest）

let _root = null;

function root() {
  if (_root) return _root;
  _root = document.getElementById('modal-import');
  if (!_root) {
    _root = document.createElement('dialog');
    _root.id = 'modal-import';
    _root.className = 'app-dialog';
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

/**
 * @param groups        from import.groupFiles
 * @param detectedTypes from import.detectGroupType per group
 * @param onConfirm(selectedTypes:string[])  chosen format per group
 * @param onCancel()
 */
export function openImportDialog({ groups, detectedTypes, onConfirm, onCancel }) {
  const dlg = root();
  const chosen = detectedTypes.slice();

  const totalSize = groups.reduce((s, g) => s + groupSize(g), 0);
  const blocked = totalSize >= SIZE_BLOCK;

  // ── body: one block per group ──
  const rows = groups.map((g, i) => {
    const isBundle = g.kind === 'bundle';
    const opts = FILE_TYPES.map(
      (t) => `<option value="${t.id}" ${t.id === chosen[i] ? 'selected' : ''}>${t.label}</option>`
    ).join('');
    const fileList = isBundle
      ? `<ul class="imp-files">${g.files.map((f) => `<li>${f.name}</li>`).join('')}</ul>`
      : '';
    const meta = isBundle
      ? `<span class="imp-meta">组合文件 · ${g.files.length} 个</span>`
      : `<span class="imp-meta">${fmtSize(groupSize(g))}</span>`;
    return `
      <div class="imp-group">
        <div class="imp-name">${groupName(g)} ${meta}</div>
        ${fileList}
        <div class="imp-format">
          <span class="form-label">文件格式 / Format</span>
          <select class="select" data-idx="${i}">${opts}</select>
        </div>
      </div>`;
  }).join('');

  const warning = totalSize >= SIZE_WARN
    ? `<div class="imp-warn">${blocked ? '文件过大（>' + fmtSize(SIZE_BLOCK) + '），无法导入。' : '文件较大（' + fmtSize(totalSize) + '），解析可能较慢。'}</div>`
    : '';

  dlg.innerHTML = `
    <div class="dialog-head">
      <span class="dialog-title">Import ${groupName(groups[0])}${groups.length > 1 ? ' 等 ' + groups.length + ' 项' : ''}</span>
      <button class="dialog-close" data-close>&times;</button>
    </div>
    <div class="dialog-body">${rows}${warning}</div>
    <div class="dialog-foot">
      <button class="btn btn-secondary" data-close>Cancel</button>
      <button class="btn btn-primary" id="imp-go" ${blocked ? 'disabled' : ''}>Import</button>
    </div>`;

  // capture dropdown choices
  dlg.querySelectorAll('select[data-idx]').forEach((sel) => {
    sel.addEventListener('change', () => { chosen[Number(sel.dataset.idx)] = sel.value; });
  });

  const close = () => { dlg.close(); if (onCancel) onCancel(); };
  dlg.querySelectorAll('[data-close]').forEach((b) => b.addEventListener('click', close));
  dlg.addEventListener('cancel', close, { once: true });

  dlg.querySelector('#imp-go').addEventListener('click', () => {
    if (blocked) return;
    dlg.close();
    if (onConfirm) onConfirm(chosen);
  });

  if (!dlg.open) dlg.showModal();
}
