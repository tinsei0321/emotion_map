"""
Streamlit UI 组件 — HUD / 弹窗 / 图例 / CSS
══════════════════════════════════════════════════════════════
可复用的 UI 渲染函数，被 apps/ 下的所有 Streamlit 应用共享。
"""
import streamlit as st


def inject_fullscreen_css():
    """注入全覆盖地图 CSS（零留白 + 按钮浮动）"""
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
    iframe[title*="streamlit_folium"]{
        position:fixed!important;top:0!important;left:0!important;
        width:100vw!important;height:100vh!important;
        z-index:0!important;border:none!important;
    }
    </style>
    <script>
    function fixIframeSize(){
        var f=document.querySelector('iframe[title*="streamlit_folium"]');
        if(f){f.style.position='fixed';f.style.top='0px';f.style.left='0px';
        f.style.width=window.innerWidth+'px';f.style.height=window.innerHeight+'px';f.style.zIndex='0';}
    }
    window.addEventListener('resize',fixIframeSize);
    setTimeout(fixIframeSize,500);setTimeout(fixIframeSize,2000);
    </script>
    """, unsafe_allow_html=True)


def hud_button_style_css():
    """HUD 按钮统一样式"""
    st.markdown("""
    <style>
    .st-key-d button,.st-key-lbl button,.st-key-leg button,.st-key-s button,
    .st-key-o button,.st-key-t button,.st-key-hm button{
        width:44px!important;height:44px!important;border-radius:10px!important;
        font-size:1.2rem!important;padding:0!important;
        background:rgba(30,30,30,0.75)!important;color:#fff!important;
        border:1px solid rgba(255,255,255,0.15)!important;
        backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
    }
    [data-testid="stAppViewContainer"] button{
        position:relative!important;z-index:10000!important;
    }
    </style>
    """, unsafe_allow_html=True)


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
    """
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
            f'<style>.st-key-{key}{{position:fixed!important;{css}z-index:9999!important;}}</style>',
            unsafe_allow_html=True)

    return st.button(label, help=help_text, key=key, disabled=disabled)


def render_legend_overlay(mode='point', **kwargs):
    """
    渲染图例叠加层（右下角）。

    mode='point':   点状图图例（正面/中性/负面）
    mode='hotcold': 冷热分布渐变条
    mode='polarity':极性分布（正面/负面独立）
    """
    if mode == 'point':
        st.markdown("""
        <div style="position:fixed;bottom:28px;right:14px;z-index:9999;pointer-events:none;
        background:rgba(0,0,0,0.55);padding:8px 12px;border-radius:8px;color:#fff;
        font-size:0.8rem;line-height:1.6;backdrop-filter:blur(4px);">
        <span style="color:#28a745;">●</span> 正面 Positive<br>
        <span style="color:#6c757d;">●</span> 中性 Neutral<br>
        <span style="color:#dc3545;">●</span> 负面 Negative</div>""",
            unsafe_allow_html=True)

    elif mode == 'hotcold':
        st.markdown("""
        <div style="position:fixed;bottom:28px;right:14px;z-index:9999;pointer-events:none;
        background:rgba(0,0,0,.6);padding:10px 14px;border-radius:8px;">
        <b style="color:#fff;">📊 冷热分布</b><br>
        <span style="display:inline-block;width:120px;height:10px;border-radius:5px;
        background:linear-gradient(90deg,#cce5ff,#ffffb2,#fdae61,#f46d43,#a50026);"></span><br>
        <span style="font-size:.7rem;color:#aaa;">冷(稀疏)</span>
        <span style="font-size:.7rem;color:#aaa;float:right;">热(密集)</span></div>""",
            unsafe_allow_html=True)

    elif mode == 'polarity':
        pos_n = kwargs.get('pos_n', 0)
        neg_n = kwargs.get('neg_n', 0)
        parts = []
        if kwargs.get('show_pos', True):
            parts.append(
                '<span style="color:#238b45;">■</span>'
                f'<span style="font-size:.75rem;color:#ccc;"> 正面({pos_n})</span><br>')
        if kwargs.get('show_neg', True):
            parts.append(
                '<span style="color:#636363;">■</span>'
                f'<span style="font-size:.75rem;color:#ccc;"> 负面({neg_n})</span><br>')
        if parts:
            st.markdown(
                '<div style="position:fixed;bottom:28px;right:14px;z-index:9999;pointer-events:none;'
                'background:rgba(0,0,0,.6);padding:10px 14px;border-radius:8px;">'
                f'<b style="color:#fff;">😊😞 极性分布</b><br>{"".join(parts)}</div>',
                unsafe_allow_html=True)


def render_title_bar(text: str):
    """渲染居中浮动标题"""
    st.markdown(
        f'<div style="position:fixed;top:16px;left:0;right:0;text-align:center;'
        f'z-index:9999;pointer-events:none;">'
        f'<span style="font-size:0.95rem;font-weight:600;color:#fff;'
        f'text-shadow:0 1px 3px rgba(0,0,0,0.7);'
        f'background:rgba(0,0,0,0.4);padding:4px 16px;border-radius:20px;'
        f'backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);">'
        f'{text}</span></div>',
        unsafe_allow_html=True)
