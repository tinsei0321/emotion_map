"""
情绪地图主应用 v3 — 与 streamlit_app_v2 完全一致，基于模块化架构
══════════════════════════════════════════════════════════════
启动: python -m streamlit run apps/app_main.py
"""
# 地址
# 本地访问：http://localhost:8501
# 网络访问：http://192.168.123.104:8501


import os, sys
from collections import Counter
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import (
    FOLDER_OPTIONS, TIANDITU_IMG_URL, TIANDITU_CVA_URL,
    FOLIUM_COLOR_MAP, DEFAULT_CENTER, DEFAULT_ZOOM,
)
from core.map_engine import create_base_map, add_point_layer
from core.data_loader import load_emotion_data

st.set_page_config(page_title='情绪地图L2_test', layout='wide')
DEBUG_MODE = True

# ═══════════════════════════════════════════════════════════
# 坐标重复度分析
# ═══════════════════════════════════════════════════════════
def _panel_coord_dup_analysis(df_or_gdf, geom_col=None):
    if geom_col is not None:
        coords_list = [(round(g.x, 5), round(g.y, 5)) for g in geom_col]
    else:
        lc = next((c for c in ['lon','longitude','lng'] if c in df_or_gdf.columns), None)
        pc = next((c for c in ['lat','latitude'] if c in df_or_gdf.columns), None)
        if not lc or not pc: return
        coords_list = [(round(r[lc],5), round(r[pc],5)) for _,r in df_or_gdf.iterrows()]
    coord_counter = Counter(coords_list)
    unique = len(coord_counter); total = len(coords_list)
    dup_ratio = (1 - unique/total)*100 if total>0 else 0
    c1,c2,c3 = st.columns(3)
    c1.metric('总点数', total); c2.metric('唯一坐标', unique)
    c3.metric('重复率', f'{dup_ratio:.1f}%')
    if dup_ratio>0: st.caption(f'平均每个坐标堆积 {total/unique:.1f} 个点')
    return coord_counter


# ═══════════════════════════════════════════════════════════
# 弹窗：数据源
# ═══════════════════════════════════════════════════════════
@st.dialog('📂 数据源', width='small')
def show_data_source_dialog():
    keys = list(FOLDER_OPTIONS.keys())
    folder_key = st.selectbox('数据文件夹', keys,
        index=keys.index(st.session_state.get('folder_key', keys[0])))
    folder_path = FOLDER_OPTIONS[folder_key]
    if not os.path.exists(folder_path): st.warning(f'不存在: {folder_path}'); return
    files = sorted([f for f in os.listdir(folder_path)
                    if os.path.isfile(os.path.join(folder_path, f))])
    if not files: st.info('空'); return
    cur = st.session_state.get('file_choice', files[0])
    idx = files.index(cur) if cur in files else 0
    file_choice = st.selectbox('选择文件', files, index=idx)
    st.caption(f'路径: `{os.path.join(folder_path, file_choice)}`')
    if st.button('✅ 确认加载', use_container_width=True, type='primary'):
        st.session_state['folder_key'] = folder_key
        st.session_state['file_choice'] = file_choice
        st.session_state['file_path'] = os.path.join(folder_path, file_choice)
        st.rerun()


# ═══════════════════════════════════════════════════════════
# 弹窗：数据概览
# ═══════════════════════════════════════════════════════════
@st.dialog('📊 数据概览', width='large')
def show_overview_dialog():
    df = st.session_state.get('current_df')
    map_meta = st.session_state.get('current_map_meta')
    file_choice = st.session_state.get('current_file_choice', '')
    if df is None: return

    st.caption(f'文件: `{file_choice}` | 共 **{len(df)}** 条记录')

    has_pol = 'polarity' in df.columns; has_sc = 'score' in df.columns

    if has_pol or has_sc:
        st.subheader('情绪分析', divider='gray')
        if has_pol:
            pos = (df['polarity'] == 'Positive').sum()
            neu = (df['polarity'] == 'Neutral').sum()
            neg = (df['polarity'] == 'Negative').sum(); total = len(df)
            c1,c2,c3,c4 = st.columns(4)
            c1.metric('总数', total)
            c2.metric('😊 正面', pos, delta=f'{pos/total*100:.0f}%' if total else '')
            c3.metric('😐 中性', neu); c4.metric('😞 负面', neg)
        if has_sc:
            st.caption(f"得分 — 均值: **{df['score'].mean():.2f}** | "
                       f"中位数: **{df['score'].median():.2f}** | "
                       f"标准差: **{df['score'].std():.2f}**")
        if has_pol:
            import altair as alt
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('polarity:N', title=None, sort=['Positive','Neutral','Negative']),
                y=alt.Y('count()', title=None),
                color=alt.Color('polarity:N', scale=alt.Scale(
                    domain=['Positive','Neutral','Negative'],
                    range=['#28a745','#6c757d','#dc3545']), legend=None)
            ).properties(height=200)
            st.altair_chart(chart, width='stretch')

    if map_meta:
        st.subheader('坐标分析', divider='gray')
        gdf = map_meta.get('gdf')
        if gdf is not None: _panel_coord_dup_analysis(gdf, geom_col=gdf.geometry)
        else: _panel_coord_dup_analysis(df)

    if 'poi' in df.columns:
        st.subheader('POI 分布', divider='gray')
        poi_counts = df['poi'].value_counts().head(15)
        c1,c2 = st.columns([3,2])
        with c1: st.dataframe(poi_counts.reset_index().set_axis(['POI','数量'], axis=1),
                              width='stretch', hide_index=True)
        with c2:
            import altair as alt
            poi_chart = alt.Chart(poi_counts.reset_index().set_axis(['POI','数量'], axis=1)
                ).mark_bar().encode(y=alt.Y('POI:N', sort='-x', title=None),
                x=alt.X('数量:Q', title=None), color=alt.value('#4a90d9')
                ).properties(height=300)
            st.altair_chart(poi_chart, width='stretch')

    st.download_button('⬇ 下载 CSV', df.to_csv(index=False).encode('utf-8'),
                       file_name=file_choice, mime='text/csv')


# ═══════════════════════════════════════════════════════════
# 弹窗：数据表格
# ═══════════════════════════════════════════════════════════
@st.dialog('📋 数据表格', width='large')
def show_table_dialog():
    df = st.session_state.get('current_df')
    fc = st.session_state.get('current_file_choice', '')
    if df is None: return
    st.caption(f'文件: `{fc}` | 共 **{len(df)}** 条记录')
    search = st.text_input('🔍 搜索（任意列匹配）', placeholder='输入关键词过滤...')
    disp = df
    if search:
        mask = disp.astype(str).apply(lambda r: r.str.contains(search, case=False, na=False).any(), axis=1)
        disp = disp[mask]; st.caption(f'筛选结果: {len(disp)} / {len(df)} 条')
    ch = [c for c in ['lon','lat','longitude','latitude','geometry'] if c in df.columns]
    sc = [c for c in disp.columns if c not in ch]
    st.dataframe(disp[sc], width='stretch', height=500)
    st.download_button('⬇ 下载筛选结果为 CSV', disp.to_csv(index=False).encode('utf-8'),
                       file_name=fc, mime='text/csv')


# ═══════════════════════════════════════════════════════════
# 弹窗：设置
# ═══════════════════════════════════════════════════════════
@st.dialog('⚙ 更多设置', width='small')
def show_settings_dialog():
    st.caption('注记和图例已移至左下 HUD 按钮直接操作')
    if DEBUG_MODE:
        st.divider(); st.caption('🛠 调试信息')
        fp = st.session_state.get('file_path','')
        if fp: st.write(f'文件: `{os.path.basename(fp)}`')
        st.write(f'Session: `{list(st.session_state.keys())}`')


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════
def main():
    for k,v in {
        'show_labels':True,'show_legend':True,
        'folder_key':list(FOLDER_OPTIONS.keys())[0],
        'file_choice':'','file_path':'',
        'current_df':None,'current_map_meta':None,
        'current_file_choice':'','data_loaded':False,
    }.items():
        if k not in st.session_state: st.session_state[k] = v

    st.markdown("""<style>
    html,body,#root,[data-testid="stAppViewContainer"]{
        margin:0!important;padding:0!important;overflow:hidden!important;
        width:100vw!important;height:100vh!important;}
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
    iframe[title="streamlit_folium\\.st_folium"]{
        position:fixed!important;top:0!important;left:0!important;
        width:100vw!important;height:100vh!important;
        min-width:100vw!important;min-height:100vh!important;
        z-index:0!important;border:none!important;
        margin:0!important;padding:0!important;}
    [data-testid="stAppViewContainer"] button{
        position:relative!important;z-index:10000!important;}
    .st-key-d button,.st-key-lbl button,.st-key-leg button,.st-key-s button,
    .st-key-o button,.st-key-t button{
        width:44px!important;height:44px!important;border-radius:10px!important;
        font-size:1.2rem!important;padding:0!important;
        background:rgba(30,30,30,0.75)!important;color:#fff!important;
        border:1px solid rgba(255,255,255,0.15)!important;
        backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);}
    .st-key-d{position:fixed!important;top:calc(50% - 22px)!important;
        left:14px!important;z-index:9999!important;}
    .st-key-s{position:fixed!important;bottom:50px!important;
        left:14px!important;z-index:9999!important;}
    .st-key-lbl{position:fixed!important;bottom:50px!important;
        left:64px!important;z-index:9999!important;}
    .st-key-leg{position:fixed!important;bottom:50px!important;
        left:114px!important;z-index:9999!important;}
    .st-key-o{position:fixed!important;top:calc(50% - 50px)!important;
        right:14px!important;z-index:9999!important;}
    .st-key-t{position:fixed!important;top:calc(50% + 2px)!important;
        right:14px!important;z-index:9999!important;}
    .leaflet-control-attribution a{display:none!important}
    .leaflet-control-scale-line{background:rgba(0,0,0,0.5)!important;
        color:#fff!important;border-color:rgba(255,255,255,0.25)!important;
        font-size:10px!important;padding:2px 6px!important;}
    </style>
    <script>function fixIframeSize(){var f=document.querySelector(
    'iframe[title*="streamlit_folium"]');if(f){f.style.position='fixed';
    f.style.top='0px';f.style.left='0px';
    f.style.width=window.innerWidth+'px';f.style.height=window.innerHeight+'px';
    f.style.zIndex='0';}}
    window.addEventListener('resize',fixIframeSize);
    setTimeout(fixIframeSize,500);setTimeout(fixIframeSize,2000);</script>
    """, unsafe_allow_html=True)

    # ── HUD ──
    fc = st.session_state.get('file_choice', '')
    btn_dis = st.session_state.get('current_df') is None

    if fc:
        st.markdown(f'<div style="position:fixed;top:16px;left:0;right:0;'
            f'text-align:center;z-index:9999;pointer-events:none;">'
            f'<span style="font-size:0.95rem;font-weight:600;color:#fff;'
            f'text-shadow:0 1px 3px rgba(0,0,0,0.7);'
            f'background:rgba(0,0,0,0.4);padding:4px 16px;border-radius:20px;'
            f'backdrop-filter:blur(4px);">情绪地图L2_test "{fc}"</span></div>',
            unsafe_allow_html=True)

    if st.button('📂', help='选择数据源', key='d'): show_data_source_dialog()
    if st.button('⚙', help='更多设置', key='s'): show_settings_dialog()

    sl = st.session_state.get('show_labels', True)
    if st.button('注' if sl else '🚫', help='注记: 开' if sl else '注记: 关', key='lbl'):
        st.session_state['show_labels'] = not sl; st.rerun()
    sg = st.session_state.get('show_legend', True)
    if st.button('🎨' if sg else '⬜', help='图例: 开' if sg else '图例: 关', key='leg'):
        st.session_state['show_legend'] = not sg; st.rerun()

    if st.button('📊', help='数据概览', key='o', disabled=btn_dis): show_overview_dialog()
    if st.button('📋', help='数据表格', key='t', disabled=btn_dis): show_table_dialog()

    if st.session_state.get('show_legend', True) and not btn_dis:
        st.markdown('<div style="position:fixed;bottom:28px;right:14px;z-index:9999;'
            'pointer-events:none;background:rgba(0,0,0,0.55);padding:8px 12px;'
            'border-radius:8px;color:#fff;font-size:0.8rem;line-height:1.6;'
            'backdrop-filter:blur(4px);">'
            '<span style="color:#28a745;">●</span> 正面 Positive<br>'
            '<span style="color:#6c757d;">●</span> 中性 Neutral<br>'
            '<span style="color:#dc3545;">●</span> 负面 Negative</div>',
            unsafe_allow_html=True)

    # ── 数据加载 + 地图 ──
    import folium; from streamlit_folium import st_folium
    fp = st.session_state.get('file_path', '')
    if not fp or not os.path.exists(fp):
        m = create_base_map(show_labels=st.session_state.get('show_labels', True))
        st_folium(m, width=None, height=700, key='default_map')
        _,c,_ = st.columns([3,2,3])
        with c:
            st.markdown('<div style="height:30vh"></div>', unsafe_allow_html=True)
            if st.button('📂 选择数据文件', type='primary', use_container_width=True):
                show_data_source_dialog()
        return

    data = load_emotion_data(fp)
    if not data:
        st.error('无法加载数据'); st.stop()

    df = data['df']
    st.session_state['current_df'] = df
    st.session_state['current_file_choice'] = fc
    st.session_state['data_loaded'] = True

    m = create_base_map(data['lats'], data['lons'],
                        show_labels=st.session_state.get('show_labels', True))

    geo = data.get('geo_data')
    if geo:
        add_point_layer(m, data['lats'], data['lons'], data['scores'],
                       props_list=geo['features'])
    else:
        add_point_layer(m, data['lats'], data['lons'], data['scores'],
                       props_list=df.to_dict('records'))

    st_folium(m, width=None, height=700, key='geojson_map')


if __name__ == '__main__':
    main()
