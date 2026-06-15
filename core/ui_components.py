"""
Streamlit UI 组件 — HUD / 弹窗 / 图例 / CSS
══════════════════════════════════════════════════════════════
可复用的 UI 渲染函数，被 apps/ 下的所有 Streamlit 应用共享。

Design Token 引用: 所有视觉属性来源于 design/tokens.json
  - 修改设计值请在 tokens.json 中修改, 运行 python design/generate_css.py 重新生成
  - 代码中勿硬编码颜色/尺寸/间距, 使用下方导入的 Token 常量
"""
import streamlit as st
import streamlit.components.v1 as components
import altair as alt

from core.tracker import track, TrackContext, trace_log, trace_error, register_track_id

# ── Design Token 导入 ─────────────────────────────────────
# token source: design/tokens.json → design/tokens.py (auto-generated)
from design.tokens import (
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_SECONDARY,
    COLOR_EMOTION_VERY_POSITIVE,
    COLOR_EMOTION_POSITIVE,
    COLOR_EMOTION_NEUTRAL,
    COLOR_EMOTION_NEGATIVE,
    COLOR_EMOTION_VERY_NEGATIVE,
    COLOR_FUNCTIONAL_OVERLAY_DARK,
    COLOR_FUNCTIONAL_OVERLAY_MEDIUM,
    COLOR_FUNCTIONAL_OVERLAY_LIGHT,
    COLOR_FUNCTIONAL_BORDER_LIGHT,
    COLOR_FUNCTIONAL_BORDER_MEDIUM,
    COLOR_FUNCTIONAL_BORDER_STRONG,
    COLOR_FUNCTIONAL_TEXT_ON_DARK,
    COLOR_FUNCTIONAL_TEXT_SECONDARY,
    COLOR_FUNCTIONAL_TEXT_TERTIARY,
    COLOR_FUNCTIONAL_GLOW_CYAN,
    COMPONENT_HUD_BUTTON_WIDTH,
    COMPONENT_HUD_BUTTON_HEIGHT,
    COMPONENT_HUD_BUTTON_BORDER_RADIUS,
    COMPONENT_HUD_BUTTON_BACKGROUND,
    COMPONENT_HUD_BUTTON_BACKDROP_FILTER,
    COMPONENT_HUD_BUTTON_COLOR,
    COMPONENT_HUD_BUTTON_BORDER,
    COMPONENT_HUD_BUTTON_HOVER_BACKGROUND,
    COMPONENT_HUD_BUTTON_FONT_SIZE,
    COMPONENT_HUD_BUTTON_Z_INDEX,
    COMPONENT_HUD_BUTTON_TRANSITION,
    COMPONENT_DIALOG_BACKGROUND,
    COMPONENT_DIALOG_BORDER,
    COMPONENT_DIALOG_BORDER_RADIUS,
    COMPONENT_DIALOG_PADDING,
    COMPONENT_DIALOG_BACKDROP_FILTER,
    COMPONENT_DIALOG_COLOR,
    COMPONENT_DIALOG_FONT_SIZE,
    COMPONENT_DIALOG_TITLE_FONT_WEIGHT,
    COMPONENT_LEGEND_BOTTOM,
    COMPONENT_LEGEND_RIGHT,
    COMPONENT_LEGEND_BACKGROUND,
    COMPONENT_LEGEND_PADDING,
    COMPONENT_LEGEND_BORDER_RADIUS,
    COMPONENT_LEGEND_COLOR,
    COMPONENT_LEGEND_FONT_SIZE,
    COMPONENT_LEGEND_LINE_HEIGHT,
    COMPONENT_LEGEND_Z_INDEX,
    COMPONENT_LEGEND_POINTER_EVENTS,
    COMPONENT_LEGEND_BACKDROP_FILTER,
    COMPONENT_LEGEND_TITLE_FONT_SIZE,
    COMPONENT_LEGEND_TITLE_FONT_WEIGHT,
    COMPONENT_LEGEND_LABEL_COLOR,
    COMPONENT_LEGEND_LABEL_FONT_SIZE,
    COMPONENT_LEGEND_GRADIENT_BAR_WIDTH,
    COMPONENT_LEGEND_GRADIENT_BAR_HEIGHT,
    COMPONENT_TITLE_BAR_TOP,
    COMPONENT_TITLE_BAR_BORDER_RADIUS,
    COMPONENT_TITLE_BAR_BACKGROUND,
    COMPONENT_TITLE_BAR_PADDING,
    COMPONENT_TITLE_BAR_FONT_SIZE,
    COMPONENT_TITLE_BAR_FONT_WEIGHT,
    COMPONENT_TITLE_BAR_COLOR,
    COMPONENT_TITLE_BAR_TEXT_SHADOW,
    COMPONENT_TITLE_BAR_BACKDROP_FILTER,
    COMPONENT_TITLE_BAR_Z_INDEX,
    COMPONENT_TITLE_BAR_POINTER_EVENTS,
    COMPONENT_DATA_OVERLAY_TOP,
    COMPONENT_DATA_OVERLAY_LEFT,
    COMPONENT_DATA_OVERLAY_BACKGROUND,
    COMPONENT_DATA_OVERLAY_PADDING,
    COMPONENT_DATA_OVERLAY_BORDER_RADIUS,
    COMPONENT_DATA_OVERLAY_COLOR,
    COMPONENT_DATA_OVERLAY_FONT_SIZE,
    COMPONENT_DATA_OVERLAY_LINE_HEIGHT,
    COMPONENT_DATA_OVERLAY_BORDER,
    COMPONENT_DATA_OVERLAY_BACKDROP_FILTER,
    COMPONENT_DATA_OVERLAY_Z_INDEX,
    COMPONENT_DATA_OVERLAY_POINTER_EVENTS,
    COLOR_CHART_POLARITY_VERY_NEGATIVE,
    COLOR_CHART_POLARITY_NEGATIVE,
    COLOR_CHART_POLARITY_NEUTRAL,
    COLOR_CHART_POLARITY_POSITIVE,
    COLOR_CHART_POLARITY_VERY_POSITIVE,
    COLOR_GRADIENT_HOTCOLD0,
    COLOR_GRADIENT_HOTCOLD1,
    COLOR_GRADIENT_HOTCOLD2,
    COLOR_GRADIENT_HOTCOLD3,
    COLOR_GRADIENT_HOTCOLD4,
    COLOR_GRADIENT_POS1,
    COLOR_GRADIENT_NEG1,
    COLOR_NEUTRAL_0,
    COLOR_NEUTRAL_700,
    TYPOGRAPHY_FONT_WEIGHT_MEDIUM,
    TYPOGRAPHY_FONT_WEIGHT_BOLD,
    TYPOGRAPHY_LETTER_SPACING_WIDE,
    EFFECT_BACKDROP_BLUR_SM,
    EFFECT_BACKDROP_BLUR_MD,
    EFFECT_BACKDROP_BLUR_LG,
)


@track("MOD_UI.F_001", track_args=False)
def inject_theme_css():
    """注入 Design Token CSS 变量（支持 Light/Dark 双主题）

    从 design/tokens.css 读取编译好的 CSS 变量并注入到 Streamlit 页面。
    包含 :root 基础 token、默认暗色主题、prefers-color-scheme 媒体查询、
    [data-theme] 手动切换选择器。
    """
    import os
    tokens_css_path = os.path.join(os.path.dirname(__file__), '..', 'design', 'tokens.css')
    if os.path.exists(tokens_css_path):
        with open(tokens_css_path, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


@track("MOD_UI.F_002", track_args=False)
def inject_fullscreen_css():
    """注入全覆盖地图 CSS（零留白 + 按钮浮动 + Leaflet 控件）"""

    # CSS 样式（通过 st.markdown 注入，innerHTML 渲染 CSS 是有效的）
    st.markdown("""
    <style>
    html, body, #root, [data-testid="stAppViewContainer"] {
        margin:0!important;padding:0!important;overflow:hidden!important;
        width:100vw!important;height:100vh!important;
    }
    header[data-testid="stHeader"]{display:none!important}
    [data-testid="stSidebar"]{display:none!important}
    footer{display:none!important}
    [data-testid="stStatusWidget"]{display:none!important}
    [data-testid="stDeployButton"]{display:none!important}
    .appview-block-container{padding:0!important}
    .main>div:first-child{padding:0!important}
    [data-testid="stAppViewContainer"]>section{padding:0!important}
    [data-testid="stVerticalBlock"]{gap:0!important}
    section[data-testid="stAppViewContainer"]>section>div{
        transform:none!important;filter:none!important;
        perspective:none!important;will-change:auto!important;}
    /* ── Dialog: 禁止点击外部关闭 ──
       只有按钮/确定操作才关闭弹窗，点击遮罩层无效。 */
    div[data-testid="stDialog"]{pointer-events:none!important;}
    div[data-testid="stDialog"] > div{pointer-events:auto!important;}
    /* 弹窗强制上下左右居中 */
    div[data-testid="stDialog"]{
        display:flex!important;align-items:center!important;justify-content:center!important;
    }
    /* 弹窗小倒角 */
    [data-testid="stDialog"] div[data-testid="stVerticalBlock"]{
        border-radius:2px!important;
    }

    /* ═══ geojson.io 全局控件样式 ═══ */
    /* Primary: 蓝色填充 (确认/上传/显示 等正向操作) */
    button[kind="primary"]{
        background:#007afc!important;border-color:#007afc!important;color:#fff!important;
    }
    button[kind="primary"]:hover{
        background:#0060c7!important;border-color:#0060c7!important;
    }
    /* Secondary/Danger: 白底+灰框 (取消等反向操作) */
    button[kind="secondary"],button[kind="danger"]{
        background:#fff!important;border:1px solid #d4d4d4!important;color:#525252!important;
    }
    button[kind="secondary"]:hover,button[kind="danger"]:hover{
        background:#f5f5f5!important;
    }
    /* Toggle + Checkbox: 蓝色主题 */
    [data-testid="stToggle"] input,[data-testid="stCheckbox"] input,
    input[type="checkbox"]{accent-color:#007afc!important;}
    [data-testid="stCheckbox"] label div:first-child{border-radius:2px!important;}
    /* Toggle 背景也蓝色 */
    [data-testid="stToggle"] div[role="switch"][aria-checked="true"]{{
        background:#007afc!important;
    }}

    /* 表单控件焦点: 蓝色 */
    input:focus,select:focus,[data-testid="stSelectbox"]:focus *,
    [data-testid="stTextInput"] input:focus{{outline-color:#007afc!important;}}
    [data-testid="stSelectbox"] div[role="listbox"]:focus,
    div[data-baseweb="select"]:focus > div{{border-color:#007afc!important;}}

    /* Tooltip: 增加阴影 */
    [data-testid="stTooltip"] > div,.stTooltip > div,div[role="tooltip"]{{
        box-shadow:0 2px 8px rgba(0,0,0,0.15)!important;
    }}

    iframe[title*="streamlit_folium"]{
        position:fixed!important;top:0!important;left:0!important;
        width:100vw!important;height:100vh!important;
        z-index:0!important;border:none!important;
    }
    iframe[title*="deck.gl"]{
        position:fixed!important;top:0!important;left:0!important;
        width:100vw!important;height:100vh!important;
        z-index:0!important;border:none!important;
    }
    /* pydeck canvas — Streamlit 用 canvas 渲染 deck.gl，非 iframe */
    canvas[data-testid="stDeckGlJsonChart"]{
        width:100vw!important;height:100vh!important;
    }
    [data-testid="stDeckGlJsonChart"]{
        width:100vw!important;height:100vh!important;
        position:fixed!important;top:0!important;left:0!important;
        z-index:0!important;
    }
    .leaflet-control-attribution a{display:none!important}
    .leaflet-control-scale-line{background:rgba(0,0,0,0.5)!important;
        color:#fff!important;border-color:rgba(255,255,255,0.25)!important;
        font-size:10px!important;padding:2px 6px!important;}
    </style>
    """, unsafe_allow_html=True)

    # JavaScript（通过 components.html 零高度 iframe 注入，确保脚本正常执行）
    # 注意：components.html 创建独立 iframe，必须用 parent.* 访问父文档中的 Folium iframe
    components.html("""
    <script>
    function fixIframeSize(){
        var iframes=parent.document.querySelectorAll('iframe[title*="streamlit_folium"], iframe[title*="deck.gl"]');
        iframes.forEach(function(f){
            f.style.position='fixed';f.style.top='0px';f.style.left='0px';
            f.style.width=parent.window.innerWidth+'px';f.style.height=parent.window.innerHeight+'px';f.style.zIndex='0';
        });
    }
    parent.window.addEventListener('resize',fixIframeSize);
    setTimeout(fixIframeSize,500);setTimeout(fixIframeSize,2000);
    parent.document.addEventListener('error',function(e){
        if(e.target&&e.target.tagName==='IMG'&&e.target.classList.contains('leaflet-tile')){
            console.warn('[MAP] 天地图瓦片加载失败，请检查网络连接或 API Key');
        }
    },true);
    /* 阻止 Streamlit dialog 点击外部关闭 */
    parent.document.addEventListener('click',function(e){
        var dlg=parent.document.querySelector('[data-testid="stDialog"]');
        if(dlg && !dlg.contains(e.target)){
            e.stopPropagation();e.stopImmediatePropagation();
        }
    },true);
    </script>
    """, height=0, width=0)


@track("MOD_UI.F_012", track_args=False)
def render_toolbar_shell():
    """双层顶栏 — geojson.io 风格:
       标题栏 (48px 深蓝底) + 工具栏 (44px 白底方按钮)。
    """
    st.markdown("""
    <div style="
        position:fixed;top:0;left:0;right:0;height:48px;
        background:#1a2940;z-index:9499;pointer-events:none;
        display:flex;align-items:center;padding:0 18px;
    "><span style="color:#ffffff;font-size:1rem;font-weight:600;
        letter-spacing:0.02em;">宜昌市情绪地图 v1.0</span></div>
    <div style="
        position:fixed;top:48px;left:0;right:0;height:44px;
        background:#ffffff;border-bottom:1px solid #e5e5e5;
        z-index:9499;pointer-events:none;
    "></div>
    """, unsafe_allow_html=True)


@track("MOD_UI.F_003", track_args=False)
def hud_button_style_css():
    """工具栏按钮 — geojson.io 风格: 36px 方按钮, 白底, hover 天蓝。"""
    # ── 按钮设计语言 ──
    # 方形按钮: S×S px, 间距 G px, 圆角 R px
    # 长条按钮: 宽度=2*S, 高度=S (如 Import/Export)
    # 定位规则: 从左到右 left=12 + Σ(prev_w + G)  或从右到左 right=12 + Σ(prev_w + G)
    S = 36           # square size (px)
    R = 4            # border-radius (px)
    G = 8            # button gap (px)
    FS = "0.75rem"   # font size
    BLUE = "#007afc" # geojson.io brand blue
    TOOLBAR_TOP = "52px"  # top of toolbar buttons (48px title + 4px padding)

    st.markdown(f"""
    <style>
    /* ═══ 工具栏方按钮 ═══ */
    .st-key-tb_import button,.st-key-tb_export button,
    .st-key-tb_analysis button,
    .st-key-tb_layers button,.st-key-tb_range button,
    .st-key-tb_overview button,.st-key-tb_table button,
    .st-key-tb_basemap button,.st-key-tb_settings button,
    .st-key-tb_heat button,.st-key-tb_m button {{
        width:{S}px!important;height:{S}px!important;min-width:{S}px!important;max-width:{S}px!important;
        min-height:{S}px!important;max-height:{S}px!important;
        border-radius:{R}px!important;
        font-size:{FS}!important;font-weight:700!important;
        padding:0!important;margin:0!important;
        line-height:{S}px!important;
        background:#ffffff!important;color:#525252!important;
        border:none!important;
        transition:all 150ms cubic-bezier(.4,0,.2,1);
    }}
    /* inner text bold */
    .st-key-tb_import button p,.st-key-tb_export button p,
    .st-key-tb_analysis button p,
    .st-key-tb_layers button p,.st-key-tb_range button p,
    .st-key-tb_overview button p,.st-key-tb_table button p,
    .st-key-tb_basemap button p,.st-key-tb_settings button p,
    .st-key-tb_heat button p,.st-key-tb_m button p{{
        font-weight:700!important;
    }}

    .st-key-tb_import button:hover,.st-key-tb_export button:hover,
    .st-key-tb_analysis button:hover,
    .st-key-tb_layers button:hover,.st-key-tb_range button:hover,
    .st-key-tb_overview button:hover,.st-key-tb_table button:hover,
    .st-key-tb_basemap button:hover,.st-key-tb_settings button:hover,
    .st-key-tb_heat button:hover,.st-key-tb_m button:hover {{
        background:#d4d4d4!important;color:#171717!important;
    }}

    /* ── 工具栏第二层按钮定位 (top=48+4=52) ── */
    /* 左侧组: [R] [LY] [A] [OV] [TB] */
    .st-key-tb_range{{position:fixed!important;top:{TOOLBAR_TOP}!important;
        left:{12}px!important;z-index:9600!important;}}
    .st-key-tb_layers{{position:fixed!important;top:{TOOLBAR_TOP}!important;
        left:{12+S+G}px!important;z-index:9600!important;}}
    .st-key-tb_analysis{{position:fixed!important;top:{TOOLBAR_TOP}!important;
        left:{12+(S+G)*2}px!important;z-index:9600!important;}}
    .st-key-tb_overview{{position:fixed!important;top:{TOOLBAR_TOP}!important;
        left:{12+(S+G)*3}px!important;z-index:9600!important;}}
    .st-key-tb_table{{position:fixed!important;top:{TOOLBAR_TOP}!important;
        left:{12+(S+G)*4}px!important;z-index:9600!important;}}

    /* 中央: [H] */
    .st-key-tb_heat{{position:fixed!important;top:{TOOLBAR_TOP}!important;
        left:50%!important;transform:translateX(-50%)!important;z-index:9600!important;}}

    /* 右侧组: [Import] [Export] */
    .st-key-tb_import{{position:fixed!important;top:{TOOLBAR_TOP}!important;
        right:{12+2*S+G}px!important;z-index:9600!important;}}
    .st-key-tb_export{{position:fixed!important;top:{TOOLBAR_TOP}!important;
        right:{12}px!important;z-index:9600!important;}}

    /* Import + Export: 长条矩形 (2*S × S) */
    .st-key-tb_import button,.st-key-tb_export button{{
        width:{2*S}px!important;min-width:{2*S}px!important;max-width:{2*S}px!important;
    }}

    /* ═══ 左侧面板内部按钮样式 ═══ */
    .st-key-pnl_data_btn button,.st-key-pnl_layers_btn button{{
        width:100%!important;height:28px!important;padding:0 12px!important;
        text-align:left!important;font-size:0.75rem!important;font-weight:600!important;
        color:#525252!important;background:transparent!important;border:none!important;
        border-radius:0!important;
    }}
    .st-key-pnl_data_btn button:hover,.st-key-pnl_layers_btn button:hover{{
        background:#f5f5f5!important;
    }}
    /* 面板内 toggle 靠右对齐 */
    .st-key-pnl_all_tgl,.st-key-pnl_lyr_0,.st-key-pnl_lyr_1,
    .st-key-pnl_lyr_2,.st-key-pnl_lyr_3,.st-key-pnl_lyr_4,
    .st-key-pnl_lyr_5,.st-key-pnl_lyr_6,.st-key-pnl_lyr_7{{
        display:flex!important;justify-content:flex-end!important;
    }}

    /* ═══ 左下角: 底图 [M] ═══ */
    .st-key-tb_m{{position:fixed!important;bottom:12px!important;
        left:12px!important;z-index:9600!important;}}

    /* ═══ 右下角: 热力图 [H] ═══ */
    .st-key-tb_heat{{position:fixed!important;bottom:12px!important;
        right:12px!important;z-index:9600!important;}}
    </style>
    """, unsafe_allow_html=True)


@track("MOD_UI.F_004", track_args=False)
def render_hud_button(key: str, label: str, help_text: str,
                      disabled=False, top=None, bottom=None,
                      left=None, right=None):
    """
    渲染一个 HUD 按钮并注入定位 CSS。

    参数:
        key: Streamlit button key（决定 CSS class）
        label: 按钮文字
        help_text: hover 提示
        disabled: 是否禁用
        top/bottom/left/right: CSS 定位值（如 'calc(50% - 22px)'）

    Token: z-index 引用 COMPONENT_HUD_BUTTON_Z_INDEX (design/tokens.json)
    """
    zi = COMPONENT_HUD_BUTTON_Z_INDEX  # token: component.hudButton.zIndex
    css = ''
    if top:
        css += f'top:{top}!important;'
    if bottom:
        css += f'bottom:{bottom}!important;'
    if left:
        css += f'left:{left}!important;'
    if right:
        css += f'right:{right}!important;'

    if css:
        st.markdown(
            f'<style>.st-key-{key}{{position:fixed!important;{css}z-index:{zi}!important;}}</style>',
            unsafe_allow_html=True)

    return st.button(label, help=help_text, key=key, disabled=disabled)


@track("MOD_UI.F_005", track_args=False)
def render_legend_overlay(mode='point', **kwargs):
    """渲染图例叠加层（右下角），使用 CSS 变量支持双主题。

    mode='point':   点状图图例（正面/中性/负面）
    mode='hotcold': 冷热分布渐变条
    mode='polarity':极性分布（正面/负面独立）
    """
    if mode == 'point':
        st.markdown("""
        <div style="position:fixed;
        bottom:var(--component-legend-bottom);
        right:var(--component-legend-right);
        z-index:var(--component-legend-z-index);
        pointer-events:var(--component-legend-pointer-events);
        background:var(--component-legend-background);
        padding:8px 12px;
        border-radius:var(--component-legend-border-radius);
        color:var(--component-legend-color);
        font-size:0.8rem;
        line-height:var(--component-legend-line-height);
        backdrop-filter:var(--component-legend-backdrop-filter);">
        <span style="color:var(--color-emotion-very-positive);">●</span> 非常积极<br>
        <span style="color:var(--color-emotion-positive);">●</span> 积极<br>
        <span style="color:var(--color-emotion-neutral);">●</span> 中性<br>
        <span style="color:var(--color-emotion-negative);">●</span> 消极<br>
        <span style="color:var(--color-emotion-very-negative);">●</span> 非常消极</div>""",
            unsafe_allow_html=True)

    elif mode == 'hotcold':
        st.markdown("""
        <div style="position:fixed;
        bottom:var(--component-legend-bottom);
        right:var(--component-legend-right);
        z-index:var(--component-legend-z-index);
        pointer-events:var(--component-legend-pointer-events);
        background:var(--component-legend-background);
        padding:var(--component-legend-padding);
        border-radius:var(--component-legend-border-radius);">
        <b style="color:var(--component-legend-color);">[MAP] Cold/Hot Distribution</b><br>
        <span style="display:inline-block;
        width:var(--component-legend-gradient-bar-width);
        height:var(--component-legend-gradient-bar-height);
        border-radius:5px;
        background:linear-gradient(90deg,var(--color-gradient-hotcold0),var(--color-gradient-hotcold1),var(--color-gradient-hotcold2),var(--color-gradient-hotcold3),var(--color-gradient-hotcold4));"></span><br>
        <span style="font-size:var(--component-legend-label-font-size);color:var(--component-legend-label-color);">Cold (Sparse)</span>
        <span style="font-size:var(--component-legend-label-font-size);color:var(--component-legend-label-color);float:right;">Hot (Dense)</span></div>""",
            unsafe_allow_html=True)

    elif mode == 'polarity':
        pos_n = kwargs.get('pos_n', 0)
        neg_n = kwargs.get('neg_n', 0)
        parts = []
        if kwargs.get('show_pos', True):
            parts.append(
                f'<span style="color:var(--color-gradient-pos1);">■</span>'
                f'<span style="font-size:var(--component-legend-font-size);color:var(--color-functional-text-secondary);"> Positive({pos_n})</span><br>')
        if kwargs.get('show_neg', True):
            parts.append(
                f'<span style="color:var(--color-gradient-neg1);">■</span>'
                f'<span style="font-size:var(--component-legend-font-size);color:var(--color-functional-text-secondary);"> Negative({neg_n})</span><br>')
        if parts:
            st.markdown(
                f'<div style="position:fixed;'
                f'bottom:var(--component-legend-bottom);'
                f'right:var(--component-legend-right);'
                f'z-index:var(--component-legend-z-index);'
                f'pointer-events:var(--component-legend-pointer-events);'
                f'background:var(--component-legend-background);'
                f'padding:var(--component-legend-padding);'
                f'border-radius:var(--component-legend-border-radius);">'
                f'<b style="color:var(--component-legend-color);">[POL] Polarity Distribution</b><br>{"".join(parts)}</div>',
                unsafe_allow_html=True)


@track("MOD_UI.F_013", track_args=False)
def render_side_panel(visible_layers: list = None, selected_ranges: list = None,
                      file_name: str = '', n_records: int = 0):
    """左侧信息面板 — HTML <details> 可折叠，纯展示（开关通过 LY 弹窗控制）。"""
    visible_layers = visible_layers or []
    selected_ranges = selected_ranges or []
    all_layers = st.session_state.get('layers', [])

    _LEVEL_LABEL = {
        'L0': '原始采集数据 L0', 'L1': '城市情绪数据 L1',
        'L2': '情绪地图数据 L2', 'L3': '语义增强数据 L3', 'L4': '多维归因数据 L4',
    }

    has_content = selected_ranges or all_layers or file_name or n_records
    if not has_content:
        return

    # ── 数据段 ──
    data_rows = ''
    if selected_ranges:
        rng_text = ', '.join(selected_ranges[:3])
        if len(selected_ranges) > 3:
            rng_text += f' +{len(selected_ranges) - 3}'
        data_rows += f'<div style="font-size:0.72rem;color:#737373;padding:2px 14px;">范围 <span style="color:#171717;">{rng_text}</span></div>'
    if visible_layers:
        for lyr in visible_layers[:5]:
            lvl = lyr.get('level', '')
            lvl_full = _LEVEL_LABEL.get(lvl, lvl)
            n = lyr.get('n_records', 0)
            count = f'{n:,} 条' if n else ''
            data_rows += f'<div style="font-size:0.72rem;color:#737373;padding:2px 14px;"><span style="color:#171717;">{lvl_full} &middot; {count}</span></div>'
    elif n_records:
        data_rows += f'<div style="font-size:0.72rem;color:#737373;padding:2px 14px;"><span style="color:#171717;">{n_records:,} 条</span></div>'
    if file_name:
        data_rows += f'<div style="font-size:0.68rem;color:#a3a3a3;padding:2px 14px 5px 14px;word-break:break-all;">文件 {file_name}</div>'

    # ── 图层段 ──
    layer_rows = ''
    for lyr in all_layers:
        lvl = lyr.get('level', '')
        name = lyr.get('name', '')
        vis = lyr.get('visible', True)
        dot = '<span style="color:#007afc;">●</span>' if vis else '<span style="color:#d4d4d4;">○</span>'
        layer_rows += (
            f'<div style="font-size:0.7rem;color:#737373;padding:2px 14px;">'
            f'{dot} [{lvl}] {name[:30]}</div>'
        )

    st.markdown(f"""
    <div style="position:fixed;
    top:100px;left:8px;width:260px;
    max-height:calc(100vh - 116px);overflow-y:auto;
    background:#ffffff;border:1px solid #e5e5e5;border-radius:4px;
    box-shadow:0 1px 3px 0 rgb(0 0 0/.1),0 1px 2px -1px rgb(0 0 0/.1);
    z-index:9400;font-family:Inter,Open Sans,sans-serif;">
    <details open style="border-bottom:1px solid #e5e5e5;">
    <summary style="padding:8px 14px;font-size:0.75rem;font-weight:600;color:#525252;cursor:pointer;outline:none;">数据一览</summary>
    <div style="padding-bottom:4px;">{data_rows}</div>
    </details>
    <details open>
    <summary style="padding:8px 14px;font-size:0.75rem;font-weight:600;color:#525252;cursor:pointer;outline:none;">图层一览</summary>
    <div style="padding-bottom:4px;">{layer_rows}</div>
    </details>
    </div>
    """, unsafe_allow_html=True)


@track("MOD_UI.F_006", track_args=False)
def render_title_bar(text: str):
    """渲染居中浮动标题 — 白色底胶囊形，始终显示。"""
    # geojson.io 风格：品牌名左对齐，16px 粗体
    st.markdown(
        f'<div style="position:fixed;'
        f'top:20px;left:18px;'
        f'z-index:9800;pointer-events:none;">'
        f'<span style="font-size:1rem;'
        f'font-weight:700;'
        f'color:#171717;">'
        f'{text}</span></div>',
        unsafe_allow_html=True)


@track("MOD_UI.F_007", track_args=False)
def render_polarity_stats(df, show_score=True):
    """渲染五列极性 Metric 统计（五级制：非常正面/正面/中性/负面/非常负面）。

    参数:
        df: 含 'polarity' 列（可选 'score' 列）的 DataFrame
        show_score: 是否显示均分信息

    返回:
        (total, vpos, pos, neu, neg, vneg, score_mean)
    """
    total = len(df)
    vpos = int((df['polarity'] == 'Very Positive').sum())
    pos = int((df['polarity'] == 'Positive').sum())
    neu = int((df['polarity'] == 'Neutral').sum())
    neg = int((df['polarity'] == 'Negative').sum())
    vneg = int((df['polarity'] == 'Very Negative').sum())
    score_col = next((c for c in ['l2_score', 'score'] if c in df.columns), None)
    score_mean = round(float(df[score_col].mean()), 2) if score_col else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('非常正面', vpos)
    c2.metric('正面', pos)
    c3.metric('中性', neu)
    c4.metric('负面', neg)
    c5.metric('非常负面', vneg)

    parts = [f'共 {total} 条']
    if show_score and 'score' in df.columns:
        parts.append(f'均分 {score_mean}')
    parts.append(f'需干预 {neg + vneg} 条 ({(neg+vneg)/total*100:.1f}%)')
    parts.append(f'标杆 {vpos} 条 ({vpos/total*100:.1f}%)')
    st.caption(' | '.join(parts))

    return total, vpos, pos, neu, neg, vneg, score_mean


@track("MOD_UI.F_008", track_args=False)
def render_polarity_chart(df, height=200):
    """渲染 Altair 极性柱状图（五级制，按情绪强度排序）。

    参数:
        df: 含 'polarity' 列的 DataFrame
        height: 图表高度（像素）
    """
    pol_order = ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']
    # token: chart.polarityVeryNegative .. chart.polarityVeryPositive (design/tokens.json)
    pol_colors = [
        COLOR_CHART_POLARITY_VERY_NEGATIVE,  # '#B92D2D'
        COLOR_CHART_POLARITY_NEGATIVE,       # '#C4956A'
        COLOR_CHART_POLARITY_NEUTRAL,        # '#C0C0C0'
        COLOR_CHART_POLARITY_POSITIVE,       # '#5DADE2'
        COLOR_CHART_POLARITY_VERY_POSITIVE,  # '#78DC32'
    ]
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('polarity:N', title=None, sort=pol_order),
        y=alt.Y('count()', title=None),
        color=alt.Color('polarity:N', scale=alt.Scale(
            domain=pol_order, range=pol_colors), legend=None)
    ).properties(height=height)
    st.altair_chart(chart, width='stretch')


@track("MOD_UI.F_009", track_args=False)
def render_empty_state_overlay():
    """数据未加载时的空状态引导，使用 CSS 变量支持双主题。"""
    st.markdown("""
    <div style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
    z-index:var(--component-legend-z-index);
    pointer-events:var(--component-legend-pointer-events);
    background:var(--component-dialog-background);
    padding:var(--component-dialog-padding);
    border-radius:var(--component-dialog-border-radius);
    backdrop-filter:var(--component-dialog-backdrop-filter);
    -webkit-backdrop-filter:var(--component-dialog-backdrop-filter);
    border:var(--component-dialog-border);">
    <p style="color:var(--component-dialog-color);
    font-size:var(--component-dialog-font-size);margin:0;text-align:center;
    font-weight:var(--typography-font-weight-medium);
    letter-spacing:var(--typography-letter-spacing-wide);">
    Click <span style="color:var(--color-brand-primary);
    font-weight:var(--typography-font-weight-bold);">[D]</span> to select a data file
    </p></div>
    """, unsafe_allow_html=True)


@track("MOD_UI.F_010", track_args=False)
def render_data_panel(range_names: list = None, data_layers: list = None,
                      file_name: str = '', n_records: int = 0):
    """左上角数据信息面板 — 表格对齐：载入范围 / DATA / 载入文件。"""

    _LEVEL_LABEL = {
        'L0': '原始采集数据L0',
        'L1': '城市情绪数据L1',
        'L2': '情绪地图数据L2',
        'L3': '语义增强数据L3',
        'L4': '多维归因数据L4',
    }

    range_names = range_names or []
    data_layers = data_layers or []
    rows = []

    # ── 第一行：载入范围 ──
    if range_names:
        rng_text = ', '.join(range_names[:3])
        if len(range_names) > 3:
            rng_text += f' +{len(range_names) - 3}'
        rows.append(
            f'<div style="margin-bottom:3px">'
            f'<span style="display:inline-block;width:52px;color:#8B929A;'
            f'font-size:0.65rem;vertical-align:top;">载入范围</span>'
            f'<span style="color:#C8CCD2;">{rng_text}</span>'
            f'</div>'
        )

    # ── 第二行：DATA ──
    if data_layers:
        for lyr in data_layers[:3]:
            lvl = lyr.get('level', '')
            lvl_full = _LEVEL_LABEL.get(lvl, lvl)
            n = lyr.get('n_records', 0)
            count_str = f'{n:,} 条' if n else ''
            rows.append(
                f'<div style="margin-bottom:3px">'
                f'<span style="display:inline-block;width:52px;color:#8B929A;'
                f'font-size:0.65rem;vertical-align:top;">DATA</span>'
                f'<span style="color:#C8CCD2;">{lvl_full} &middot; {count_str}</span>'
                f'</div>'
            )
    elif n_records:
        rows.append(
            f'<div style="margin-bottom:3px">'
            f'<span style="display:inline-block;width:52px;color:#8B929A;'
            f'font-size:0.65rem;vertical-align:top;">DATA</span>'
            f'<span style="color:#C8CCD2;">{n_records:,} 条</span>'
            f'</div>'
        )

    # ── 第三行：载入文件 ──
    if file_name:
        rows.append(
            f'<div>'
            f'<span style="display:inline-block;width:52px;color:#8B929A;'
            f'font-size:0.65rem;vertical-align:top;">载入文件</span>'
            f'<span style="color:#9CA3AF;word-break:break-all;">{file_name}</span>'
            f'</div>'
        )

    if not rows:
        return

    body = '\n'.join(rows)
    st.markdown(f"""
    <div style="position:fixed;
    top:12px;left:12px;
    z-index:9800;
    pointer-events:none;
    background:rgba(20,24,32,0.58);
    padding:10px 14px;
    border-radius:8px;
    border:1px solid rgba(255,255,255,0.07);
    backdrop-filter:blur(14px);
    -webkit-backdrop-filter:blur(14px);
    font-size:0.7rem;
    line-height:1.45;
    max-width:210px;">
    {body}
    </div>
    """, unsafe_allow_html=True)

@track("MOD_UI.F_011", track_args=False)
def show_toast(message: str, duration_ms: int = 2000):
    """居中 Toast 通知，自动淡出。st.empty() 确保每次新建 DOM 元素。"""
    st.empty().markdown(f"""
    <div style="
        position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
        z-index:999999;background:rgba(36,39,48,0.94);color:#D3D8E0;
        padding:6px 24px;border-radius:100px;font-size:0.82rem;
        font-weight:500;pointer-events:none;white-space:nowrap;
        animation:toastIn 0.15s ease,toastOut 0.4s ease {duration_ms}ms forwards;
    ">{message}</div>
    <style>
    @keyframes toastIn{{from{{opacity:0;transform:translate(-50%,-50%) scale(0.9)}}to{{opacity:1;transform:translate(-50%,-50%) scale(1)}}}}
    @keyframes toastOut{{to{{opacity:0}}}}
    </style>
    """, unsafe_allow_html=True)


# ── 追踪 ID 注册表 ──
register_track_id("MOD_UI.F_001", "注入 Design Token CSS 变量")
register_track_id("MOD_UI.F_002", "注入全覆盖地图 CSS + JS")
register_track_id("MOD_UI.F_003", "工具栏 + 底部按钮 CSS")
register_track_id("MOD_UI.F_012", "渲染顶部工具栏底条")
register_track_id("MOD_UI.F_013", "渲染左侧信息面板")
register_track_id("MOD_UI.F_004", "渲染 HUD 按钮")
register_track_id("MOD_UI.F_005", "渲染图例叠加层")
register_track_id("MOD_UI.F_006", "渲染标题栏")
register_track_id("MOD_UI.F_007", "渲染极性统计面板")
register_track_id("MOD_UI.F_008", "渲染极性分布图表")
register_track_id("MOD_UI.F_009", "渲染空状态引导页")
register_track_id("MOD_UI.F_010", "渲染左上角数据信息面板")
register_track_id("MOD_UI.F_011", "渲染居中 Toast 通知")
