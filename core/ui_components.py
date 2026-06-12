"""
Streamlit UI 组件 — HUD / 弹窗 / 图例 / CSS
══════════════════════════════════════════════════════════════
可复用的 UI 渲染函数，被 apps/ 下的所有 Streamlit 应用共享。
"""
import streamlit as st
import altair as alt


def inject_fullscreen_css():
    """注入全覆盖地图 CSS（零留白 + 按钮浮动 + Leaflet 控件）"""
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
    .leaflet-control-attribution a{display:none!important}
    .leaflet-control-scale-line{background:rgba(0,0,0,0.5)!important;
        color:#fff!important;border-color:rgba(255,255,255,0.25)!important;
        font-size:10px!important;padding:2px 6px!important;}
    </style>
    <script>
    function fixIframeSize(){
        var f=document.querySelector('iframe[title*="streamlit_folium"]');
        if(f){f.style.position='fixed';f.style.top='0px';f.style.left='0px';
        f.style.width=window.innerWidth+'px';f.style.height=window.innerHeight+'px';f.style.zIndex='0';}
    }
    window.addEventListener('resize',fixIframeSize);
    setTimeout(fixIframeSize,500);setTimeout(fixIframeSize,2000);
    document.addEventListener('error',function(e){
        if(e.target&&e.target.tagName==='IMG'&&e.target.classList.contains('leaflet-tile')){
            console.warn('[MAP] 天地图瓦片加载失败，请检查网络连接或 API Key');
        }
    },true);
    </script>
    """, unsafe_allow_html=True)


def hud_button_style_css():
    """HUD 按钮统一样式 + 定位（8 键全覆盖）"""
    st.markdown("""
    <style>
    .st-key-d button,.st-key-lbl button,.st-key-leg button,.st-key-s button,
    .st-key-o button,.st-key-t button,.st-key-rng button,.st-key-a button{
        width:44px!important;height:44px!important;border-radius:10px!important;
        font-size:1.1rem!important;padding:0!important;
        background:rgba(30,30,30,0.75)!important;color:#fff!important;
        border:1px solid rgba(255,255,255,0.15)!important;
        backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
        transition:background 0.2s;
    }
    .st-key-d button:hover,.st-key-lbl button:hover,.st-key-leg button:hover,
    .st-key-s button:hover,.st-key-o button:hover,.st-key-t button:hover,
    .st-key-rng button:hover,.st-key-a button:hover{
        background:rgba(255,107,53,0.3)!important;
    }
    [data-testid="stAppViewContainer"] button{
        position:relative!important;z-index:10000!important;
    }
    /* 左侧三功能按钮 — 纵向排列 */
    .st-key-rng{position:fixed!important;top:calc(50% - 72px)!important;
        left:14px!important;z-index:9999!important;}
    .st-key-d{position:fixed!important;top:calc(50% - 22px)!important;
        left:14px!important;z-index:9999!important;}
    .st-key-a{position:fixed!important;top:calc(50% + 28px)!important;
        left:14px!important;z-index:9999!important;}
    /* 底部工具栏 */
    .st-key-s{position:fixed!important;bottom:50px!important;
        left:14px!important;z-index:9999!important;}
    .st-key-lbl{position:fixed!important;bottom:50px!important;
        left:64px!important;z-index:9999!important;}
    .st-key-leg{position:fixed!important;bottom:50px!important;
        left:114px!important;z-index:9999!important;}
    /* 右侧工具按钮 */
    .st-key-o{position:fixed!important;top:calc(50% - 50px)!important;
        right:14px!important;z-index:9999!important;}
    .st-key-t{position:fixed!important;top:calc(50% + 2px)!important;
        right:14px!important;z-index:9999!important;}
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
        <div style="position:fixed;bottom:12px;left:50%;transform:translateX(-50%);z-index:9998;pointer-events:none;
        background:rgba(0,0,0,0.55);padding:8px 12px;border-radius:8px;color:#fff;
        font-size:0.8rem;line-height:1.6;backdrop-filter:blur(4px);">
        <span style="color:#1a7a1a;">●</span> 非常正面 Very Positive<br>
        <span style="color:#28a745;">●</span> 正面 Positive<br>
        <span style="color:#6c757d;">●</span> 中性 Neutral<br>
        <span style="color:#e8590c;">●</span> 负面 Negative<br>
        <span style="color:#dc3545;">●</span> 非常负面 Very Negative</div>""",
            unsafe_allow_html=True)

    elif mode == 'hotcold':
        st.markdown("""
        <div style="position:fixed;bottom:12px;left:50%;transform:translateX(-50%);z-index:9998;pointer-events:none;
        background:rgba(0,0,0,.6);padding:10px 14px;border-radius:8px;">
        <b style="color:#fff;">[MAP] 冷热分布</b><br>
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
                '<div style="position:fixed;bottom:12px;left:50%;transform:translateX(-50%);z-index:9998;pointer-events:none;'
                'background:rgba(0,0,0,.6);padding:10px 14px;border-radius:8px;">'
                f'<b style="color:#fff;">[POL] 极性分布</b><br>{"".join(parts)}</div>',
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
    score_mean = round(float(df['score'].mean()), 2) if 'score' in df.columns else 0.0

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


def render_polarity_chart(df, height=200):
    """渲染 Altair 极性柱状图（五级制，按情绪强度排序）。

    参数:
        df: 含 'polarity' 列的 DataFrame
        height: 图表高度（像素）
    """
    pol_order = ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']
    pol_colors = ['#dc3545', '#e8590c', '#6c757d', '#28a745', '#1a7a1a']
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('polarity:N', title=None, sort=pol_order),
        y=alt.Y('count()', title=None),
        color=alt.Color('polarity:N', scale=alt.Scale(
            domain=pol_order, range=pol_colors), legend=None)
    ).properties(height=height)
    st.altair_chart(chart, width='stretch')


def render_empty_state_overlay():
    """数据未加载时的空状态引导 — 地图中央半透明提示卡片"""
    st.markdown("""
    <div style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
    z-index:9998;pointer-events:none;
    background:rgba(0,0,0,0.55);padding:20px 32px;border-radius:12px;
    backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
    border:1px solid rgba(255,255,255,0.12);">
    <p style="color:#fff;font-size:1rem;margin:0;text-align:center;
    font-weight:500;letter-spacing:0.02em;">
    点击 <span style="color:#ff6b35;font-weight:700;">[D]</span> 选择数据文件开始探索
    </p></div>
    """, unsafe_allow_html=True)


def render_data_summary_overlay(n: int, area_label: str = '',
                                 range_label: str = '', date_label: str = ''):
    """数据加载后的左上角摘要浮层"""
    parts = [f'📍 {n} 条记录']
    if area_label:
        parts.append(f'📐 {area_label}')
    if range_label:
        parts.append(f'{range_label}')
    if date_label:
        parts.append(f'📅 {date_label}')
    line = ' &nbsp; '.join(parts)
    st.markdown(f"""
    <div style="position:fixed;top:54px;left:14px;z-index:9999;pointer-events:none;
    background:rgba(0,0,0,0.45);padding:5px 14px;border-radius:8px;
    backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
    border:1px solid rgba(255,255,255,0.10);">
    <span style="color:#fff;font-size:0.78rem;line-height:1.5;">
    {line}
    </span></div>
    """, unsafe_allow_html=True)
