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
    section[data-testid="stAppViewContainer"]>section>div,
    section[data-testid="stAppViewContainer"]>section>div>div,
    section[data-testid="stAppViewContainer"]>section>div>div>div{
        transform:none!important;filter:none!important;
        perspective:none!important;will-change:auto!important;}
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
    </script>
    """, height=0, width=0)


@track("MOD_UI.F_003", track_args=False)
def hud_button_style_css():
    """Kepler.gl 风格 HUD — 右侧竖排浮动工具栏 + 底部工具按钮。

    参考 Kepler.gl 源码 theme/base.ts 色板:
      按钮背景: #29323C (Kepler inputBg)
      悬停:     #3A404F (Kepler inputBgdHover)
      文字:     #D3D8E0 (Kepler textColor)
      圆角:     4px   (Kepler 默认)

    布局（从右上到右下）:
      右侧工具栏: [R] [D] [A] [M] [H] [*]  — 竖排居右中
      底部左侧:   [OV] [TB]                   — 数据辅助按钮
    """
    BTN_SIZE = "40px"
    BTN_RADIUS = "4px"
    BTN_BG_GLASS = "rgba(41, 50, 60, 0.28)"   # 极透 — 地图可见
    BTN_HOVER = "rgba(58, 64, 79, 0.94)"       # 鼠标悬停 — 加深
    BTN_COLOR = "#D3D8E0"
    BTN_BORDER = "1px solid rgba(255,255,255,0.06)"
    RIGHT = "12px"

    st.markdown(f"""
    <style>
    /* ── 通用 HUD 按钮样式 ── */
    .st-key-rng button,.st-key-d button,.st-key-a button,
    .st-key-lbl button,.st-key-heat_toggle button,.st-key-s button,
    .st-key-o button,.st-key-t button,.st-key-ly button {{
        width:{BTN_SIZE}!important;height:{BTN_SIZE}!important;
        border-radius:{BTN_RADIUS}!important;
        font-size:0.85rem!important;font-weight:600!important;
        padding:0!important;min-width:0!important;
        background:{BTN_BG_GLASS}!important;
        color:{BTN_COLOR}!important;
        border:{BTN_BORDER}!important;
        transition:background 120ms ease,opacity 120ms ease;
    }}
    /* hover — 加深，清晰可辨 */
    .st-key-rng button:hover,.st-key-d button:hover,.st-key-a button:hover,
    .st-key-lbl button:hover,.st-key-heat_toggle button:hover,.st-key-s button:hover,
    .st-key-o button:hover,.st-key-t button:hover,.st-key-ly button:hover {{
        background:{BTN_HOVER}!important;
    }}
    /* 禁用态 */
    .st-key-o button:disabled,.st-key-t button:disabled {{
        opacity:0.35!important;cursor:not-allowed;
    }}
    /* ── 右侧竖排工具栏 ── */
    .st-key-rng{{position:fixed!important;top:calc(50% - 132px)!important;
        right:{RIGHT}!important;z-index:9000!important;}}
    .st-key-d{{position:fixed!important;top:calc(50% - {88 - 4}px)!important;
        right:{RIGHT}!important;z-index:9000!important;}}
    .st-key-a{{position:fixed!important;top:calc(50% - {44 - 8}px)!important;
        right:{RIGHT}!important;z-index:9000!important;}}
    .st-key-heat_toggle{{position:fixed!important;top:calc(50% - {0 - 12}px)!important;
        right:{RIGHT}!important;z-index:9000!important;}}
    /* ── 左上角: 设置 ── */
    .st-key-s{{position:fixed!important;top:12px!important;
        left:12px!important;z-index:9000!important;}}
    /* ── 底部左下角 ── */
    .st-key-lbl{{position:fixed!important;bottom:12px!important;
        left:12px!important;z-index:9000!important;}}
    .st-key-o{{position:fixed!important;bottom:12px!important;
        left:56px!important;z-index:9000!important;}}
    .st-key-t{{position:fixed!important;bottom:12px!important;
        left:100px!important;z-index:9000!important;}}
    .st-key-ly{{position:fixed!important;bottom:12px!important;
        left:144px!important;z-index:9000!important;}}

    /* ═══ 自定义 Tooltip — 纯 CSS，文本硬编码 ═══
       原因: 浏览器原生 title tooltip 不可定位。JS 注入在 Streamlit iframe 沙箱中不稳定。
       方案: 每个按钮的 ::after 中直接写 content，按位置定义方向。
    */
    .st-key-rng button,.st-key-d button,.st-key-a button,
    .st-key-lbl button,.st-key-heat_toggle button,.st-key-s button,
    .st-key-o button,.st-key-t button,.st-key-ly button {{
        position:relative!important;
    }}
    /* 共享 tooltip 样式 */
    .st-key-rng button::after,.st-key-d button::after,
    .st-key-a button::after,.st-key-lbl button::after,
    .st-key-heat_toggle button::after,.st-key-s button::after,
    .st-key-o button::after,.st-key-t button::after,
    .st-key-ly button::after {{
        position:absolute;
        background:rgba(36,39,48,0.95);color:#D3D8E0;
        padding:4px 10px;border-radius:4px;
        font-size:0.75rem;font-weight:400;
        white-space:nowrap;pointer-events:none;
        opacity:0;transition:opacity 150ms ease;
        z-index:99999;
    }}
    /* hover 显示 */
    .st-key-rng button:hover::after,.st-key-d button:hover::after,
    .st-key-a button:hover::after,.st-key-lbl button:hover::after,
    .st-key-heat_toggle button:hover::after,.st-key-s button:hover::after,
    .st-key-o button:hover::after,.st-key-t button:hover::after,
    .st-key-ly button:hover::after {{
        opacity:1;
    }}
    /* ─ 右侧按钮 — tooltip 向左 ─ */
    .st-key-rng button::after{{content:"分析范围";right:calc(100%+8px);top:50%;transform:translateY(-50%);}}
    .st-key-d button::after{{content:"数据加载";right:calc(100%+8px);top:50%;transform:translateY(-50%);}}
    .st-key-a button::after{{content:"分析引擎";right:calc(100%+8px);top:50%;transform:translateY(-50%);}}
    .st-key-heat_toggle button::after{{content:"热力图";right:calc(100%+8px);top:50%;transform:translateY(-50%);}}
    /* ─ 底部按钮 — tooltip 向上 ─ */
    .st-key-lbl button::after{{content:"底图切换";bottom:calc(100%+6px);left:50%;transform:translateX(-50%);}}
    .st-key-o button::after{{content:"数据概览";bottom:calc(100%+6px);left:50%;transform:translateX(-50%);}}
    .st-key-t button::after{{content:"数据表格";bottom:calc(100%+6px);left:50%;transform:translateX(-50%);}}
    .st-key-ly button::after{{content:"图层控制";bottom:calc(100%+6px);left:50%;transform:translateX(-50%);}}
    /* ─ 左上角 — tooltip 向下 ─ */
    .st-key-s button::after{{content:"设置与调试";top:calc(100%+6px);left:50%;transform:translateX(-50%);}}
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
        <span style="color:var(--color-emotion-very-positive);">●</span> Very Positive<br>
        <span style="color:var(--color-emotion-positive);">●</span> Positive<br>
        <span style="color:var(--color-emotion-neutral);">●</span> Neutral<br>
        <span style="color:var(--color-emotion-negative);">●</span> Negative<br>
        <span style="color:var(--color-emotion-very-negative);">●</span> Very Negative</div>""",
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


@track("MOD_UI.F_006", track_args=False)
def render_title_bar(text: str):
    """渲染居中浮动标题，使用 CSS 变量支持双主题。"""
    st.markdown(
        f'<div style="position:fixed;'
        f'top:var(--component-title-bar-top);left:0;right:0;text-align:center;'
        f'z-index:var(--component-title-bar-z-index);'
        f'pointer-events:var(--component-title-bar-pointer-events);">'
        f'<span style="font-size:var(--component-title-bar-font-size);'
        f'font-weight:var(--component-title-bar-font-weight);'
        f'color:var(--component-title-bar-color);'
        f'text-shadow:var(--component-title-bar-text-shadow);'
        f'background:var(--component-title-bar-background);'
        f'padding:var(--component-title-bar-padding);'
        f'border-radius:var(--component-title-bar-border-radius);'
        f'backdrop-filter:var(--component-title-bar-backdrop-filter);'
        f'-webkit-backdrop-filter:var(--component-title-bar-backdrop-filter);">'
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
def render_data_summary_overlay(n: int, area_label: str = '',
                                 range_label: str = '', date_label: str = ''):
    """数据加载后的左上角摘要浮层，使用 CSS 变量支持双主题。"""
    parts = [f'[OK] {n} records']
    if area_label:
        parts.append(f'[AREA] {area_label}')
    if range_label:
        parts.append(f'{range_label}')
    if date_label:
        parts.append(f'[DATE] {date_label}')
    line = ' &nbsp; '.join(parts)
    st.markdown(f"""
    <div style="position:fixed;
    top:var(--component-data-overlay-top);
    left:var(--component-data-overlay-left);
    z-index:var(--component-data-overlay-z-index);
    pointer-events:var(--component-data-overlay-pointer-events);
    background:var(--component-data-overlay-background);
    padding:var(--component-data-overlay-padding);
    border-radius:var(--component-data-overlay-border-radius);
    backdrop-filter:var(--component-data-overlay-backdrop-filter);
    -webkit-backdrop-filter:var(--component-data-overlay-backdrop-filter);
    border:var(--component-data-overlay-border);">
    <span style="color:var(--component-data-overlay-color);
    font-size:var(--component-data-overlay-font-size);
    line-height:var(--component-data-overlay-line-height);">
    {line}
    </span></div>
    """, unsafe_allow_html=True)

# ── 追踪 ID 注册表 ──
register_track_id("MOD_UI.F_001", "注入 Design Token CSS 变量")
register_track_id("MOD_UI.F_002", "注入全覆盖地图 CSS + JS")
register_track_id("MOD_UI.F_003", "HUD 按钮统一样式 CSS")
register_track_id("MOD_UI.F_004", "渲染 HUD 按钮")
register_track_id("MOD_UI.F_005", "渲染图例叠加层")
register_track_id("MOD_UI.F_006", "渲染标题栏")
register_track_id("MOD_UI.F_007", "渲染极性统计面板")
register_track_id("MOD_UI.F_008", "渲染极性分布图表")
register_track_id("MOD_UI.F_009", "渲染空状态引导页")
register_track_id("MOD_UI.F_010", "渲染数据摘要叠加层")
