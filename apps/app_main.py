"""
情绪地图 v1.0 — 地图浏览器 + 分析控制台
══════════════════════════════════════════════════════════════
启动: python launch.py                    # 一键启动
      python -m streamlit run apps/app_main.py

页面: 默认 = 地图浏览器
      ?page=console&file=xxx  = 分析控制台（自动加载结果）
"""
# 本地访问：http://localhost:8501


import os, sys
from collections import Counter
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import (
    FOLDER_OPTIONS, TIANDITU_IMG_URL, TIANDITU_CVA_URL,
    FOLIUM_COLOR_MAP, DEFAULT_CENTER, DEFAULT_ZOOM, RAW_DIR, PROCESSED_DIR,
)
from core.map_engine import create_base_map, add_point_layer
from core.data_loader import load_emotion_data
from SCRIPT.emotion_analysis_v1 import create_analyzer, run_pipeline, run_analysis_task

st.set_page_config(page_title='情绪地图 v1.0', layout='wide')
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
@st.dialog('[DATA] 数据源', width='small')
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
            total = len(df)
            # 五级极性统计
            vpos = (df['polarity'] == 'Very Positive').sum()
            pos = (df['polarity'] == 'Positive').sum()
            neu = (df['polarity'] == 'Neutral').sum()
            neg = (df['polarity'] == 'Negative').sum()
            vneg = (df['polarity'] == 'Very Negative').sum()
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric('🟢 非常正面', vpos)
            c2.metric('✅ 正面', pos)
            c3.metric('➖ 中性', neu)
            c4.metric('⚠️ 负面', neg)
            c5.metric('🔴 非常负面', vneg)
            st.caption(f"需干预 (负面+非常负面): **{neg + vneg}** 条 ({(neg+vneg)/total*100:.1f}%) | "
                       f"标杆 (非常正面): **{vpos}** 条 ({vpos/total*100:.1f}%)")
        if has_sc:
            st.caption(f"得分 — 均值: **{df['score'].mean():.2f}** | "
                       f"中位数: **{df['score'].median():.2f}** | "
                       f"标准差: **{df['score'].std():.2f}**")
        if has_pol:
            import altair as alt
            pol_order = ['Very Negative','Negative','Neutral','Positive','Very Positive']
            pol_colors = ['#dc3545','#e8590c','#6c757d','#28a745','#1a7a1a']
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('polarity:N', title=None, sort=pol_order),
                y=alt.Y('count()', title=None),
                color=alt.Color('polarity:N', scale=alt.Scale(
                    domain=pol_order, range=pol_colors), legend=None)
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
# 弹窗：运行情绪分析
# ═══════════════════════════════════════════════════════════
@st.dialog('🔬 运行情绪分析', width='large')
def show_analysis_dialog():
    st.markdown('选择原始情绪DATA文件并运行情绪分析引擎，结果自动加载到地图。')

    # ── 选择文件 ──
    raw_files = []
    if os.path.exists(RAW_DIR):
        raw_files = sorted([f for f in os.listdir(RAW_DIR)
                           if os.path.isfile(os.path.join(RAW_DIR, f))
                           and f.lower().endswith(('.csv', '.tsv', '.json', '.geojson'))])
    if not raw_files:
        st.warning(f'`{RAW_DIR}/` 中没有可分析的文件。请先将原始数据放入该目录。')
        return

    file_choice = st.selectbox('📄 原始情绪DATA文件（L1）', raw_files,
                               help=f'来自 {RAW_DIR}/')
    st.caption(f'路径: `{os.path.join(RAW_DIR, file_choice)}`')

    st.divider()

    # ── 选择引擎 ──
    engine_choice = st.radio(
        '🧠 分析引擎',
        ['L2 · SnowNLP粗粒度分析 (离线)', 'L3 · LLM 细粒度语义解析 (需 API Key)', 'L4 · 语料库 + LLM 多维归因处理 (需语料库 和 API Key)'],
        help='L2 轻量免费; L3 需接入大模型 API; L4 需情绪语料库和大模型API'
    )

    api_key = ''
    if 'LLM' in engine_choice:
        api_key = st.text_input('🔑 API Key',
                                type='password',
                                placeholder='sk-...',
                                help='DeepSeek/Qwen/GLM 等模型的 API Key')

    st.divider()

    # ── 执行 ──
    c1, c2 = st.columns([1, 3])
    with c1:
        run_clicked = st.button('🚀 开始分析', type='primary',
                                use_container_width=True)
    with c2:
        if run_clicked:
            engine_type = 'llm' if 'LLM' in engine_choice else 'snownlp'
            kwargs = {}
            if api_key:
                kwargs['api_key'] = api_key
            engine = create_analyzer(engine_type, **kwargs)

            # ── 执行分析 ──
            run_success = False
            result_df = None

            with st.status(f'[{engine.phase}] {engine.name} 分析中…', expanded=True) as status:
                try:
                    input_path = os.path.join(RAW_DIR, file_choice)
                    df = run_pipeline(input_path, engine)

                    if df is not None and not df.empty:
                        base_name = os.path.splitext(file_choice)[0]
                        from core.export import export_to_csv, export_to_geojson
                        os.makedirs(PROCESSED_DIR, exist_ok=True)
                        csv_path = os.path.join(PROCESSED_DIR,
                                                f'{base_name}_{engine.phase}_result_csv.csv')
                        export_to_csv(df, csv_path)
                        if 'lon' in df.columns and 'lat' in df.columns:
                            geojson_path = os.path.join(PROCESSED_DIR,
                                f'{base_name}_{engine.phase}_result_geojson.geojson')
                            export_to_geojson(df, geojson_path)
                        status.update(label=f'分析完成！{len(df)} 条数据', state='complete')

                        st.session_state['folder_key'] = list(FOLDER_OPTIONS.keys())[0]
                        st.session_state['file_choice'] = os.path.basename(csv_path)
                        st.session_state['file_path'] = csv_path
                        st.session_state['current_df'] = df
                        st.session_state['current_file_choice'] = os.path.basename(csv_path)
                        st.session_state['data_loaded'] = True
                        run_success = True
                        result_df = df
                        result_csv = csv_path
                    else:
                        status.update(label='分析失败', state='error')
                        st.error('请检查数据文件格式（需含 comments 列）')
                except Exception as e:
                    status.update(label='分析出错', state='error')
                    st.exception(e)

            # ── 结果子面板（状态条外部，自动可见）──
            if run_success and result_df is not None:
                st.divider()
                st.subheader('分析结果预览')
                df = result_df
                total = len(df)
                vpos = int((df['polarity'] == 'Very Positive').sum())
                pos_ = int((df['polarity'] == 'Positive').sum())
                neu_ = int((df['polarity'] == 'Neutral').sum())
                neg_ = int((df['polarity'] == 'Negative').sum())
                vneg = int((df['polarity'] == 'Very Negative').sum())

                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric('非常正面', vpos)
                m2.metric('正面', pos_)
                m3.metric('中性', neu_)
                m4.metric('负面', neg_)
                m5.metric('非常负面', vneg)
                st.caption(
                    f"共 {total} 条 | 均分 {df['score'].mean():.2f} | "
                    f"需干预 {neg_ + vneg} 条 ({(neg_+vneg)/total*100:.1f}%)"
                )

                # ── 跳转按钮 ──
                _, btn_col, _ = st.columns([1, 2, 1])
                with btn_col:
                    st.link_button(
                        '打开分析控制台查看详细报告',
                        url=f'/?page=console&file={result_csv.replace(chr(92), "/")}',
                        type='primary',
                        use_container_width=True,
                    )


# ═══════════════════════════════════════════════════════════
# 页面：分析控制台（?page=console）
# ═══════════════════════════════════════════════════════════

def show_console_page():
    st.title('情绪分析控制台')
    st.caption('从地图浏览器跳转而来')

    # ── 读取 URL 参数 ──
    auto_file = st.query_params.get('file', None)
    auto_loaded_df = None
    auto_loaded_stats = None
    auto_loaded_score = 0.0
    auto_loaded_n = 0
    is_auto_mode = False

    if auto_file and os.path.exists(auto_file):
        try:
            data = load_emotion_data(auto_file)
            if data:
                auto_loaded_df = data['df']
                auto_loaded_n = data['n_points']
                if 'polarity' in auto_loaded_df.columns:
                    auto_loaded_stats = {
                        'Very Positive': int((auto_loaded_df['polarity'] == 'Very Positive').sum()),
                        'Positive':      int((auto_loaded_df['polarity'] == 'Positive').sum()),
                        'Neutral':       int((auto_loaded_df['polarity'] == 'Neutral').sum()),
                        'Negative':      int((auto_loaded_df['polarity'] == 'Negative').sum()),
                        'Very Negative': int((auto_loaded_df['polarity'] == 'Very Negative').sum()),
                    }
                if 'score' in auto_loaded_df.columns:
                    auto_loaded_score = round(float(auto_loaded_df['score'].mean()), 2)
                is_auto_mode = True
        except Exception:
            pass

    # ── 侧边栏 ──
    with st.sidebar:
        if is_auto_mode:
            st.success(f'已加载: {os.path.basename(auto_file)}')
            st.caption(f'{auto_loaded_n} 条数据')
        st.divider()
        st.subheader('新文件分析')
        engine_choice = st.selectbox(
            '选择引擎',
            ['L2 · SnowNLP', 'L3 · LLM 语义增强', 'L4 · 多维归因', '全管道 L2-L3-L4'],
        )
        api_key = ''
        corpus_path = ''
        if 'L3' in engine_choice or 'L4' in engine_choice:
            api_key = st.text_input('API Key', type='password', placeholder='sk-...')
        if 'L4' in engine_choice or '全管道' in engine_choice:
            corpus_path = st.text_input('语料库路径', placeholder='data/corpus/v1.json')
        enable_keywords = st.checkbox('提取关键词 (jieba)', value=True)
        st.divider()
        st.caption('v1.0')
        st.markdown('[返回地图浏览器](/)')

    # ── 模式 A: 自动加载 ──
    if is_auto_mode and auto_loaded_df is not None:
        st.caption(f'文件: `{auto_file}` | {auto_loaded_n} 条记录')
        if auto_loaded_stats:
            with st.expander(f'分析结果 · {auto_loaded_n} 条数据', expanded=True):
                stats = auto_loaded_stats
                neg = stats['Negative']; vneg = stats['Very Negative']
                pos = stats['Positive']; vpos = stats['Very Positive']
                total = auto_loaded_n
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric('非常正面', vpos)
                m2.metric('正面', pos)
                m3.metric('中性', stats['Neutral'])
                m4.metric('负面', neg)
                m5.metric('非常负面', vneg)
                st.caption(
                    f"均分 {auto_loaded_score} | "
                    f"需干预 {neg + vneg} 条 ({(neg+vneg)/total*100:.1f}%) | "
                    f"标杆 {vpos} 条 ({vpos/total*100:.1f}%)"
                )
                import altair as alt
                pol_order = ['Very Negative','Negative','Neutral','Positive','Very Positive']
                pol_colors = ['#dc3545','#e8590c','#6c757d','#28a745','#1a7a1a']
                chart = alt.Chart(auto_loaded_df).mark_bar().encode(
                    x=alt.X('polarity:N', title=None, sort=pol_order),
                    y=alt.Y('count()', title=None),
                    color=alt.Color('polarity:N', scale=alt.Scale(domain=pol_order, range=pol_colors), legend=None)
                ).properties(height=250)
                st.altair_chart(chart, width='stretch')
                with st.expander('查看数据表（前 100 行）'):
                    cols = [c for c in auto_loaded_df.columns if c not in ['geometry']]
                    st.dataframe(auto_loaded_df[cols].head(100), width='stretch')

        st.subheader('导出', divider='gray')
        d1, d2, _ = st.columns(3)
        if os.path.exists(auto_file):
            with open(auto_file, 'rb') as f:
                d1.download_button('下载 CSV', f.read(), file_name=os.path.basename(auto_file),
                                   mime='text/csv', use_container_width=True)
        geojson_path = auto_file.replace('_csv.csv', '_geojson.geojson')
        if os.path.exists(geojson_path):
            with open(geojson_path, 'rb') as f:
                d2.download_button('下载 GeoJSON', f.read(), file_name=os.path.basename(geojson_path),
                                   mime='application/geo+json', use_container_width=True)
        st.divider()

    # ── 模式 B: 分析新文件 ──
    st.subheader('选择新数据文件', divider='gray')
    tab1, tab2 = st.tabs(['从 raw 目录选择', '上传新文件'])
    new_file_selected = False
    input_path = ''

    with tab1:
        raw_files = []
        if os.path.exists(RAW_DIR):
            raw_files = sorted([
                f for f in os.listdir(RAW_DIR)
                if os.path.isfile(os.path.join(RAW_DIR, f))
                and f.lower().endswith(('.csv', '.tsv', '.json', '.geojson'))
                and '_result_' not in f
            ])
        if raw_files:
            file_choice = st.selectbox('原始数据文件', raw_files, key='console_raw')
            input_path = os.path.join(RAW_DIR, file_choice)
            st.caption(f'`{input_path}`')
            new_file_selected = True
        else:
            st.info('无可用原始文件')

    with tab2:
        uploaded = st.file_uploader('上传文件', type=['csv', 'tsv', 'json', 'geojson'])
        if uploaded:
            os.makedirs(RAW_DIR, exist_ok=True)
            save_path = os.path.join(RAW_DIR, uploaded.name)
            with open(save_path, 'wb') as f:
                f.write(uploaded.getbuffer())
            st.success('已保存')
            input_path = save_path
            new_file_selected = True

    if new_file_selected and input_path:
        st.divider()
        output_name = st.text_input('输出文件名',
            value=os.path.splitext(os.path.basename(input_path))[0])
        if st.button('开始分析', type='primary'):
            eng_type = 'snownlp'; is_full = False
            if 'L3' in engine_choice: eng_type = 'llm'
            elif 'L4' in engine_choice: eng_type = 'corpus'
            elif '全管道' in engine_choice: is_full = True
            with st.status('分析中...', expanded=True) as status:
                result = run_analysis_task(
                    file_path=input_path, engine_type=eng_type,
                    output_name=output_name, api_key=api_key,
                    corpus_path=corpus_path, enable_keywords=enable_keywords,
                    full_pipeline=is_full,
                )
                if result['success']:
                    status.update(label=f'完成！{result["n_points"]} 条', state='complete')
                    st.rerun()
                else:
                    status.update(label='失败', state='error')
                    st.error(result['message'])


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════
def main():
    # ── 路由：?page=console → 分析控制台 ──
    page = st.query_params.get('page', None)
    if page == 'console':
        show_console_page()
        return

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
    .st-key-o button,.st-key-t button,.st-key-a button{
        width:44px!important;height:44px!important;border-radius:10px!important;
        font-size:1.2rem!important;padding:0!important;
        background:rgba(30,30,30,0.75)!important;color:#fff!important;
        border:1px solid rgba(255,255,255,0.15)!important;
        backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);}
    .st-key-d{position:fixed!important;top:calc(50% - 22px)!important;
        left:14px!important;z-index:9999!important;}
    .st-key-a{position:fixed!important;top:calc(50% + 26px)!important;
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
            f'backdrop-filter:blur(4px);">情绪地图 v1.0 "{fc}"</span></div>',
            unsafe_allow_html=True)

    if st.button('[DATA]', help='选择数据源', key='d'): show_data_source_dialog()
    if st.button('🔬', help='运行情绪分析', key='a'): show_analysis_dialog()
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
            '<span style="color:#1a7a1a;">●</span> 非常正面<br>'
            '<span style="color:#28a745;">●</span> 正面<br>'
            '<span style="color:#6c757d;">●</span> 中性<br>'
            '<span style="color:#e8590c;">●</span> 负面<br>'
            '<span style="color:#dc3545;">●</span> 非常负面</div>',
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
            if st.button('[DATA] 选择数据文件', type='primary', use_container_width=True):
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
