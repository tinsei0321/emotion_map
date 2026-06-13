"""
Design System — 情绪地图 v1.0
══════════════════════════════════════════════════════════════
独立 Streamlit 设计系统展示页，不依赖主应用数据加载。

启动:
    python -m streamlit run apps/app_design_system.py

功能:
  - Light/Dark 主题实时切换
  - 色彩色板 / 字体层级 / 间距圆角 / 阴影效果
  - 组件展示 (HUD按钮、弹窗、图例、情绪圆点、Badge、Toast等)
"""
import streamlit as st
import json
import os

# ── 页面配置 ─────────────────────────────────────────────
st.set_page_config(
    page_title="Design System — Emotion Map",
    page_icon=":art:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 路径 ──────────────────────────────────────────────────
HERE = os.path.dirname(__file__)
TOKENS_JSON = os.path.join(HERE, '..', 'design', 'tokens.json')


# ── 加载 Token ────────────────────────────────────────────
@st.cache_data
def load_tokens():
    with open(TOKENS_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


def flatten_theme(tokens_data, theme_name):
    """展平指定主题的 token 为 {key: value} 字典"""
    theme = tokens_data.get('theme', {}).get(theme_name, {})
    result = {}

    def _walk(obj, prefix=''):
        for k, v in obj.items():
            # camelCase → kebab-case
            import re
            kebab = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', k).lower()
            full = f'{prefix}-{kebab}' if prefix else kebab
            if isinstance(v, dict):
                _walk(v, full)
            else:
                result[full] = str(v)
    _walk(theme)
    return result


def inject_theme(theme_name):
    """注入当前主题的 CSS 变量"""
    tokens = load_tokens()
    theme_tokens = flatten_theme(tokens, theme_name)

    # 基础 token（与主题无关）
    base_tokens = {}
    for section in ['typography', 'spacing', 'radius', 'shadow', 'effect']:
        if section in tokens:
            obj = tokens[section]
            import re
            def _walk(obj, prefix=''):
                for k, v in obj.items():
                    kebab = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', k).lower()
                    full = f'{prefix}-{kebab}' if prefix else kebab
                    if isinstance(v, dict):
                        _walk(v, full)
                    else:
                        base_tokens[full] = str(v)
            _walk(obj, section)

    css_lines = [':root {']
    for key, value in sorted(base_tokens.items()):
        css_lines.append(f'  --{key}: {value};')
    for key, value in sorted(theme_tokens.items()):
        css_lines.append(f'  --{key}: {value};')
    css_lines.append('}')

    st.markdown(f'<style>{"".join(css_lines)}</style>', unsafe_allow_html=True)


# ── 通用样式注入 ──────────────────────────────────────────
def inject_design_system_css():
    st.markdown("""
    <style>
    /* 页面基础样式 */
    .ds-section { margin-bottom: 0.8rem; }
    /* 紧凑标题 */
    .stApp h3 { margin: 0.5rem 0 0.3rem 0 !important; font-size: 1.05rem !important; }
    .stApp h4 { margin: 0.4rem 0 0.2rem 0 !important; font-size: 0.9rem !important; }
    .stApp h5 { margin: 0.3rem 0 0.15rem 0 !important; font-size: 0.8rem !important; }
    .ds-color-grid { display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 8px 0; }
    .ds-color-swatch {
        width: 58px; height: 40px; border-radius: 5px;
        display: flex; flex-direction: column; justify-content: flex-end;
        padding: 3px 5px; box-sizing: border-box;
        font-size: 0.5rem; font-family: monospace; color: #fff; line-height: 1.15;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .ds-color-swatch.light-swatch {
        color: #1a1a1a; text-shadow: none;
        border: 1px solid rgba(0,0,0,0.1);
    }
    .ds-font-sample { margin: 1px 0; padding: 1px 0; border-bottom: 1px solid rgba(128,128,128,0.12); line-height: 1.3; }
    .ds-spacing-bar { display: inline-block; height: 14px; background: var(--color-brand-primary); border-radius: 2px; margin-right: 6px; vertical-align: middle; opacity: 0.7; }
    .ds-radius-box { display: inline-block; width: 36px; height: 36px; background: var(--color-brand-primary); margin-right: 8px; opacity: 0.7; }
    .ds-shadow-card { width: 72px; height: 48px; background: var(--color-neutral-100); border-radius: 6px; display: inline-flex; align-items: center; justify-content: center; margin: 4px 8px 4px 0; font-size: 0.6rem; color: var(--color-functional-text-on-dark); }
    .ds-component-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin: 4px 0 8px 0; }
    .ds-hud-btn { width: 36px; height: 36px; border-radius: 8px; background: var(--component-hud-button-background); color: var(--component-hud-button-color); border: var(--component-hud-button-border); backdrop-filter: var(--component-hud-button-backdrop-filter); display: inline-flex; align-items: center; justify-content: center; font-size: 0.9rem; cursor: pointer; transition: var(--component-hud-button-transition); }
    .ds-hud-btn:hover { background: var(--component-hud-button-hover-background); }
    .ds-hud-btn.disabled { opacity: var(--component-hud-button-disabled-opacity); cursor: var(--component-hud-button-disabled-cursor); }
    .ds-dialog { max-width: 420px; border-radius: var(--component-dialog-border-radius); background: var(--component-dialog-background); border: var(--component-dialog-border); padding: 14px 24px; backdrop-filter: var(--component-dialog-backdrop-filter); color: var(--component-dialog-color); font-size: 0.875rem; }
    .ds-dialog-title { font-size: 1.05rem; font-weight: var(--component-dialog-title-font-weight); margin-bottom: 6px; }
    .ds-dialog-divider { height: 1px; background: var(--component-dialog-divider-color); margin: 8px 0; }
    .ds-legend-box { display: inline-block; border-radius: var(--component-legend-border-radius); background: var(--component-legend-background); padding: 6px 10px; color: var(--component-legend-color); font-size: 0.7rem; line-height: 1.4; backdrop-filter: var(--component-legend-backdrop-filter); }
    .ds-emotion-dot { display: inline-block; width: 20px; height: 20px; border-radius: 50%; position: relative; margin: 3px 6px; }
    .ds-emotion-dot::before { content: ''; position: absolute; top: -2px; left: -2px; width: 24px; height: 24px; border-radius: 50%; opacity: 0.18; }
    .ds-emotion-dot::after { content: ''; position: absolute; top: 4px; left: 4px; width: 12px; height: 12px; border-radius: 50%; border: 2px solid #fff; opacity: 0.92; }
    .ds-badge { display: inline-block; border-radius: 10px; padding: 1px 6px; font-size: 0.6rem; font-weight: 600; text-transform: uppercase; }
    .ds-toast { display: inline-block; border-radius: 6px; background: var(--component-toast-background); padding: 6px 14px; color: var(--component-toast-color); font-size: 0.75rem; backdrop-filter: var(--component-toast-backdrop-filter); margin: 3px; }
    .ds-spinner { display: inline-block; width: 18px; height: 18px; border: 2.5px solid rgba(128,128,128,0.2); border-top-color: var(--component-spinner-color); border-radius: 50%; animation: ds-spin 0.8s linear infinite; }
    @keyframes ds-spin { to { transform: rotate(360deg); } }
    .ds-table { width: 100%; border-collapse: collapse; font-size: 0.7rem; }
    .ds-table th { background: var(--component-data-table-header-background); color: var(--component-data-table-header-color); font-weight: 600; padding: 4px 8px; text-align: left; border-bottom: 1px solid var(--component-data-table-border-color); }
    .ds-table td { padding: 4px 8px; border-bottom: 1px solid var(--component-data-table-border-color); }
    .ds-table tr:hover td { background: var(--component-data-table-row-hover-background); }
    .ds-title-bar-sample { display: inline-block; border-radius: 16px; background: var(--component-title-bar-background); padding: 3px 12px; color: var(--component-title-bar-color); font-size: 0.8rem; font-weight: 600; text-shadow: var(--component-title-bar-text-shadow); backdrop-filter: var(--component-title-bar-backdrop-filter); }
    .ds-data-overlay-sample { display: inline-block; border-radius: 6px; background: var(--component-data-overlay-background); padding: 4px 10px; color: var(--component-data-overlay-color); font-size: 0.7rem; border: var(--component-data-overlay-border); backdrop-filter: var(--component-data-overlay-backdrop-filter); }
    </style>
    """, unsafe_allow_html=True)


# ── 侧边栏导航 ────────────────────────────────────────────
def render_sidebar():
    st.sidebar.markdown("<h3 style='margin-bottom:2px;'>Design System</h3>", unsafe_allow_html=True)
    st.sidebar.caption("Emotion Map v1.0")

    # 主题切换
    st.sidebar.markdown("<small style='opacity:0.6;'>Theme</small>", unsafe_allow_html=True)
    current_theme = st.session_state.get('theme', 'dark')
    new_theme = st.sidebar.radio(
        "Select theme mode",
        options=['dark', 'light'],
        index=0 if current_theme == 'dark' else 1,
        format_func=lambda x: f"[*] {x.capitalize()}" if x == current_theme else f"   {x.capitalize()}",
        key="theme_selector",
        label_visibility="collapsed"
    )
    if new_theme != current_theme:
        st.session_state.theme = new_theme
        st.rerun()

    # 导航区块（紧凑列表）
    st.sidebar.markdown("<hr style='margin:6px 0;opacity:0.12;'>", unsafe_allow_html=True)
    sections = [
        "Color Palette",
        "Typography",
        "Spacing & Radius",
        "Shadow & Effects",
        "Components",
    ]
    st.sidebar.markdown(
        "<small>" + "<br>".join(f"&bull; {s}" for s in sections) + "</small>",
        unsafe_allow_html=True
    )

    st.sidebar.markdown("<hr style='margin:6px 0;opacity:0.12;'>", unsafe_allow_html=True)
    st.sidebar.caption("Auto-generated from design/tokens.json")
    st.sidebar.caption("Run: python design/generate_css.py")


# ── 颜色色板区块 ──────────────────────────────────────────
def render_color_palette():
    st.subheader("Color Palette")

    tokens = load_tokens()
    theme_name = st.session_state.get('theme', 'dark')
    color_data = tokens['theme'][theme_name]['color']

    # 品牌色
    st.markdown("#### Brand Colors")
    brand = color_data['brand']
    st.markdown('<div class="ds-color-grid">', unsafe_allow_html=True)
    for name, hex_val in brand.items():
        is_light_bg = theme_name == 'light' and 'primary' in name.lower()
        swatch_class = 'ds-color-swatch light-swatch' if is_light_bg else 'ds-color-swatch'
        st.markdown(
            f'<div class="{swatch_class}" style="background:{hex_val};">'
            f'{hex_val}<br><small>color-brand-{_kebab(name)}</small></div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 情绪五色
    st.markdown("#### Emotion Colors")
    emotion = color_data['emotion']
    emotion_labels = {
        'veryPositive': 'Very Positive', 'positive': 'Positive',
        'neutral': 'Neutral', 'negative': 'Negative', 'veryNegative': 'Very Negative'
    }
    st.markdown('<div class="ds-color-grid">', unsafe_allow_html=True)
    for name, hex_val in emotion.items():
        label = emotion_labels.get(name, name)
        st.markdown(
            f'<div class="ds-color-swatch" style="background:{hex_val};">'
            f'{hex_val}<br><small>{label}</small></div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 中性色阶
    st.markdown("#### Neutral Scale")
    neutral = color_data['neutral']
    st.markdown('<div class="ds-color-grid">', unsafe_allow_html=True)
    for key in sorted(neutral.keys(), key=lambda x: int(x)):
        hex_val = neutral[key]
        is_light = int(key) < 400
        swatch_class = 'ds-color-swatch light-swatch' if is_light else 'ds-color-swatch'
        st.markdown(
            f'<div class="{swatch_class}" style="background:{hex_val};">'
            f'{hex_val}<br><small>neutral-{key}</small></div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 语义色
    st.markdown("#### Semantic Colors")
    semantic = color_data['semantic']
    st.markdown('<div class="ds-color-grid">', unsafe_allow_html=True)
    for name, hex_val in semantic.items():
        st.markdown(
            f'<div class="ds-color-swatch" style="background:{hex_val};">'
            f'{hex_val}<br><small>{name}</small></div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 功能色
    st.markdown("#### Functional Colors")
    functional = color_data['functional']
    st.markdown('<div class="ds-color-grid">', unsafe_allow_html=True)
    for name, hex_val in functional.items():
        bg = hex_val if hex_val.startswith('#') else '#666'
        st.markdown(
            f'<div class="ds-color-swatch" style="background:{bg};">'
            f'{hex_val}<br><small>{_kebab(name)}</small></div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def _kebab(name):
    import re
    return re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', name).lower()


# ── 字体层级区块 ──────────────────────────────────────────
def render_typography():
    st.subheader("Typography")

    tokens = load_tokens()
    typo = tokens['typography']

    st.markdown("#### Font Families")
    st.markdown(f"- Sans: `{typo['fontFamily']['sans']}`")
    st.markdown(f"- Mono: `{typo['fontFamily']['mono']}`")

    st.markdown("#### Font Sizes")
    sizes = typo['fontSize']
    for name in ['xs', 'sm', 'base', 'lg', 'xl', '2xl', '3xl']:
        size = sizes[name]
        st.markdown(
            f'<div class="ds-font-sample" style="font-size:{size};">'
            f'<code>{size}</code> — The quick brown fox jumps over the lazy dog (字体层级 {name})'
            f'</div>',
            unsafe_allow_html=True)

    st.markdown("#### Font Weights")
    weights = typo['fontWeight']
    weight_names = {'normal': 'Regular', 'medium': 'Medium', 'semibold': 'Semibold', 'bold': 'Bold'}
    for name in ['normal', 'medium', 'semibold', 'bold']:
        w = weights[name]
        st.markdown(
            f'<div class="ds-font-sample" style="font-weight:{w};">'
            f'<code>{w}</code> — {weight_names[name]} ({name})'
            f'</div>',
            unsafe_allow_html=True)

    st.markdown("#### Line Heights")
    lh = typo['lineHeight']
    for name in ['tight', 'normal', 'relaxed']:
        val = lh[name]
        st.markdown(
            f'<div style="line-height:{val};margin:4px 0;">'
            f'<code>{val}</code> — line-height {name}: The quick brown fox jumps over the lazy dog. '
            f'This is a second line to demonstrate line height spacing.'
            f'</div>',
            unsafe_allow_html=True)


# ── 间距与圆角区块 ────────────────────────────────────────
def render_spacing_radius():
    st.subheader("Spacing & Radius")

    tokens = load_tokens()
    spacing = tokens['spacing']
    radius = tokens['radius']

    st.markdown("#### Spacing Scale")
    spacer_keys = ['0', 'px', '1', '2', '3', '4', '5', '6', '8', '10', '12', '16']
    for key in spacer_keys:
        val = spacing[key]
        width_px = int(val.replace('px', '')) * 2 if 'px' in val else int(val) * 2
        st.markdown(
            f'<div style="margin:2px 0;">'
            f'<span class="ds-spacing-bar" style="width:{max(width_px, 4)}px;"></span>'
            f'<code>spacing-{key}</code> = {val}'
            f'</div>',
            unsafe_allow_html=True)

    st.markdown("#### Border Radius")
    radius_keys = ['none', 'sm', 'md', 'lg', 'xl', 'full']
    for key in radius_keys:
        val = radius[key]
        st.markdown(
            f'<div style="margin:4px 0;">'
            f'<span class="ds-radius-box" style="border-radius:{val};"></span>'
            f'<code>radius-{key}</code> = {val}'
            f'</div>',
            unsafe_allow_html=True)


# ── 阴影与效果区块 ────────────────────────────────────────
def render_shadow_effects():
    st.subheader("Shadow & Effects")

    tokens = load_tokens()
    shadow = tokens['shadow']
    effect = tokens['effect']

    st.markdown("#### Shadows")
    theme_name = st.session_state.get('theme', 'dark')
    bg = '#333' if theme_name == 'dark' else '#f5f5f5'
    for name in ['sm', 'md', 'lg', 'glow', 'text']:
        val = shadow[name]
        st.markdown(
            f'<div>'
            f'<div class="ds-shadow-card" style="box-shadow:{val};background:{bg};">'
            f'{name}'
            f'</div>'
            f'<code>shadow-{name}</code> = {val}'
            f'</div>',
            unsafe_allow_html=True)

    st.markdown("#### Backdrop Blur")
    blur = effect['backdropBlur']
    for name in ['sm', 'md', 'lg']:
        val = blur[name]
        st.markdown(f"- `effect-backdrop-blur-{name}` = {val}")

    st.markdown("#### Transitions")
    trans = effect['transition']
    for name in ['fast', 'normal', 'slow']:
        val = trans[name]
        st.markdown(
            f'<div style="transition:{val};padding:4px 8px;background:var(--color-brand-primary);'
            f'border-radius:4px;display:inline-block;margin:2px;cursor:pointer;" '
            f'onmouseover="this.style.opacity=0.6" onmouseout="this.style.opacity=1">'
            f'{name}: {val}'
            f'</div>',
            unsafe_allow_html=True)

    st.markdown("#### Opacity Values")
    op = effect['opacity']
    for name, val in op.items():
        st.markdown(f"- `effect-opacity-{name}` = {val}")


# ── 组件展示区块 ──────────────────────────────────────────
def render_components():
    st.subheader("Components")

    # HUD 按钮
    st.markdown("#### HUD Buttons")
    st.markdown('<div class="ds-component-row">', unsafe_allow_html=True)
    st.markdown('<div class="ds-hud-btn" title="Normal">D</div>', unsafe_allow_html=True)
    st.markdown('<div class="ds-hud-btn" title="Hover">S</div>', unsafe_allow_html=True)
    st.markdown('<div class="ds-hud-btn disabled" title="Disabled">X</div>', unsafe_allow_html=True)
    st.markdown(
        '<small style="color:var(--color-functional-text-tertiary);">'
        'Normal | Hover (see CSS) | Disabled</small>',
        unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 弹窗
    st.markdown("#### Dialog")
    st.markdown("""
    <div class="ds-dialog">
        <div class="ds-dialog-title">Dialog Title</div>
        <p>This is a sample dialog body with semi-transparent background and backdrop blur. It adapts to light and dark themes automatically.</p>
        <div class="ds-dialog-divider"></div>
        <div style="text-align:right;">
            <span style="background:var(--color-neutral-600);color:#fff;padding:6px 16px;border-radius:6px;margin-right:8px;cursor:pointer;">Cancel</span>
            <span style="background:var(--color-brand-primary);color:#fff;padding:6px 16px;border-radius:6px;cursor:pointer;">Confirm</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 图例
    st.markdown("#### Legend")
    tokens = load_tokens()
    theme_name = st.session_state.get('theme', 'dark')
    color_data = tokens['theme'][theme_name]['color']
    evp = color_data['emotion']['veryPositive']
    epo = color_data['emotion']['positive']
    ene = color_data['emotion']['neutral']
    eng = color_data['emotion']['negative']
    evn = color_data['emotion']['veryNegative']
    gh0 = color_data['gradient']['hotcold0']
    gh1 = color_data['gradient']['hotcold1']
    gh2 = color_data['gradient']['hotcold2']
    gh3 = color_data['gradient']['hotcold3']
    gh4 = color_data['gradient']['hotcold4']

    st.markdown("##### Point Legend")
    st.markdown(f"""
    <div class="ds-legend-box">
    <span style="color:{evp};">●</span> Very Positive<br>
    <span style="color:{epo};">●</span> Positive<br>
    <span style="color:{ene};">●</span> Neutral<br>
    <span style="color:{eng};">●</span> Negative<br>
    <span style="color:{evn};">●</span> Very Negative
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### Hot/Cold Gradient Legend")
    st.markdown(f"""
    <div class="ds-legend-box">
    <b>[MAP] Cold/Hot Distribution</b><br>
    <span style="display:inline-block;width:120px;height:10px;border-radius:5px;
    background:linear-gradient(90deg,{gh0},{gh1},{gh2},{gh3},{gh4});"></span><br>
    <span style="font-size:0.7rem;color:var(--component-legend-label-color);">Cold (Sparse)</span>
    <span style="font-size:0.7rem;color:var(--component-legend-label-color);float:right;margin-left:40px;">Hot (Dense)</span>
    </div>
    """, unsafe_allow_html=True)

    # 标题栏
    st.markdown("#### Title Bar")
    st.markdown('<div class="ds-title-bar-sample">Data File: simulated_20260613_规划范围_L1_result_csv.csv</div>', unsafe_allow_html=True)

    # 数据摘要浮层
    st.markdown("#### Data Summary Overlay")
    st.markdown(f"""
    <div class="ds-data-overlay-sample">
    [OK] 1,234 records &nbsp; [AREA] Xiling &nbsp; 500m radius &nbsp; [DATE] 2026-06-12
    </div>
    """, unsafe_allow_html=True)

    # 情绪圆点
    st.markdown("#### Emotion Dots (Map Markers)")
    emotion_colors_vals = color_data['emotion']
    st.markdown('<div class="ds-component-row">', unsafe_allow_html=True)
    for name, hex_val in emotion_colors_vals.items():
        st.markdown(
            f'<div style="text-align:center;margin:0 12px;">'
            f'<div style="width:26px;height:26px;border-radius:50%;background:{hex_val};'
            f'display:inline-block;position:relative;box-shadow:0 0 8px {hex_val}44;">'
            f'<div style="position:absolute;top:6px;left:6px;width:14px;height:14px;'
            f'border-radius:50%;background:{hex_val};border:2px solid #fff;opacity:0.92;"></div>'
            f'</div>'
            f'<br><small>{_kebab(name)}</small></div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Badge
    st.markdown("#### Badge")
    semantic_colors = color_data['semantic']
    for name, hex_val in semantic_colors.items():
        st.markdown(
            f'<span class="ds-badge" style="background:{hex_val}22;color:{hex_val};'
            f'border:1px solid {hex_val}44;margin:2px;">{name}</span>',
            unsafe_allow_html=True)
    st.markdown(
        '<span class="ds-badge" style="background:var(--color-brand-primary)22;'
        'color:var(--color-brand-primary);border:1px solid var(--color-brand-primary)44;margin:2px;">'
        'new</span>',
        unsafe_allow_html=True)

    # Toast
    st.markdown("#### Toast Notifications")
    st.markdown(f"""
    <div class="ds-component-row">
    <div class="ds-toast">
    <span style="color:{color_data['semantic']['success']};">[OK]</span> Operation completed successfully
    </div>
    <div class="ds-toast">
    <span style="color:{color_data['semantic']['error']};">[ERR]</span> Failed to load data
    </div>
    <div class="ds-toast">
    <span style="color:{color_data['semantic']['warning']};">[WARN]</span> Low disk space
    </div>
    <div class="ds-toast">
    <span style="color:{color_data['semantic']['info']};">[INFO]</span> New update available
    </div>
    </div>
    """, unsafe_allow_html=True)

    # Spinner
    st.markdown("#### Loading Spinner")
    st.markdown('<div class="ds-component-row"><div class="ds-spinner"></div> <span style="margin-left:8px;">Loading data...</span></div>', unsafe_allow_html=True)

    # 数据表格
    st.markdown("#### Data Table")
    st.markdown("""
    <table class="ds-table">
    <thead><tr><th>ID</th><th>Content</th><th>Polarity</th><th>Score</th></tr></thead>
    <tbody>
    <tr><td>001</td><td>Sample data row one</td><td><span style="color:var(--color-emotion-positive);">Positive</span></td><td>0.85</td></tr>
    <tr><td>002</td><td>Sample data row two</td><td><span style="color:var(--color-emotion-neutral);">Neutral</span></td><td>0.50</td></tr>
    <tr><td>003</td><td>Sample data row three</td><td><span style="color:var(--color-emotion-negative);">Negative</span></td><td>0.22</td></tr>
    </tbody>
    </table>
    """, unsafe_allow_html=True)


# ── 主页面 ────────────────────────────────────────────────
def main():
    # 初始化 theme
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'

    theme_name = st.session_state.theme

    # 注入主题 CSS
    inject_theme(theme_name)
    inject_design_system_css()

    # 背景色适应
    bg = '#0d0d0d' if theme_name == 'dark' else '#fafafa'
    fg = '#e0e0e0' if theme_name == 'dark' else '#1a1a1a'
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg}; }}
    html, body, .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, div, label, li {{
        color: {fg} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # 侧边栏
    render_sidebar()

    # 主内容
    st.title("Design System — Emotion Map v1.0")
    st.caption(f"Current theme: **{theme_name.capitalize()}** | Toggle theme in the sidebar")

    # 渲染各个展示区块（紧凑间距）
    render_color_palette()
    st.markdown("<hr style='margin:0.6rem 0;opacity:0.15;'>", unsafe_allow_html=True)

    render_typography()
    st.markdown("<hr style='margin:0.6rem 0;opacity:0.15;'>", unsafe_allow_html=True)

    render_spacing_radius()
    st.markdown("<hr style='margin:0.6rem 0;opacity:0.15;'>", unsafe_allow_html=True)

    render_shadow_effects()
    st.markdown("<hr style='margin:0.6rem 0;opacity:0.15;'>", unsafe_allow_html=True)

    render_components()

    # 页脚
    st.markdown("<hr style='margin:0.8rem 0;opacity:0.15;'>", unsafe_allow_html=True)
    st.caption("Design System — Auto-generated from design/tokens.json | Run: python design/generate_css.py")


if __name__ == '__main__':
    main()
