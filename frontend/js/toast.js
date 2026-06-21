// ═══ toast.js — global capsule toast (geojson.io-style, extra-rounded) ═══
// Fires on ANY result event: import success/fail, layer toggle/delete, analysis,
// basemap switch — not just Import. Plain DOM, no dependency.
//
//   import { toast } from './toast.js';
//   toast.success('Imported 312 points');
//   toast.error('无法识别文件类型');

const ICONS = {
  success: '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
  error:   '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"><path d="M7 7l10 10M17 7L7 17"/></svg>',
  info:    '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"><path d="M12 8h.01M11 12h1v5h1"/></svg>',
};

let _container = null;

function container() {
  if (_container) return _container;
  _container = document.getElementById('toast-container');
  if (!_container) {
    _container = document.createElement('div');
    _container.id = 'toast-container';
    document.body.appendChild(_container);
  }
  return _container;
}

function show(message, type = 'info', ms = 2000) {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.setAttribute('role', type === 'error' ? 'alert' : 'status');
  el.innerHTML = `<span class="toast-icon">${ICONS[type] || ICONS.info}</span><span class="toast-msg"></span>`;
  el.querySelector('.toast-msg').textContent = message;

  const c = container();
  c.appendChild(el);
  // entrance on next frame (for transition)
  requestAnimationFrame(() => el.classList.add('show'));

  const dismiss = () => {
    el.classList.remove('show');
    el.addEventListener('transitionend', () => el.remove(), { once: true });
    // safety: remove even if transitionend doesn't fire
    setTimeout(() => el.remove(), 400);
  };
  el.addEventListener('click', dismiss);
  setTimeout(dismiss, ms);
}

export const toast = {
  success: (m, ms) => show(m, 'success', ms),
  error:   (m, ms) => show(m, 'error', ms ?? 2000),
  info:    (m, ms) => show(m, 'info', ms),
};
