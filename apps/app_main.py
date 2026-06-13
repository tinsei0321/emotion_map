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
import re as _re
import streamlit as st
import pandas as pd
import altair as alt
import folium
from streamlit_folium import st_folium

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import (
    FOLDER_OPTIONS, TIANDITU_IMG_URL, TIANDITU_CVA_URL,
    FOLIUM_COLOR_MAP, DEFAULT_CENTER, DEFAULT_ZOOM, RAW_DIR, PROCESSED_DIR,
)
from core.map_engine import create_base_map, add_point_layer, add_boundary_layer
from core.data_loader import load_emotion_data
from core.range_selector import (
    load_boundaries, get_available_ranges, filter_by_range,
    save_uploaded_file, get_active_boundary_path, list_boundary_files,
    get_boundary_geojson, DEFAULT_RANGE, get_boundary_crs_info,
)
from core.ui_components import (
    inject_fullscreen_css, hud_button_style_css,
    render_title_bar, render_legend_overlay,
    render_data_summary_overlay,
    render_polarity_stats, render_polarity_chart,
)
from SCRIPT.emotion_analysis_v1 import (
    create_analyzer, run_pipeline, run_analysis_task, _safe_print,
)

st.set_page_config(page_title='情绪地图 v1.0', layout='wide')
DEBUG_MODE = True

# ═══════════════════════════════════════════════════════════
# 坐标重复度分析
# ═══════════════════════════════════════════════════════════
def _panel_coord_dup_analysis(df_or_gdf, geom_col=None):
    if geom_col is not None:
        coords_list = [(round(g.x, 5), round(g.y, 5)) for g in geom_col]
    else:
        lc = next((c for c in ['lon','longitude','lng','lon_gcj02'] if c in df_or_gdf.columns), None)
        pc = next((c for c in ['lat','latitude','lat_gcj02'] if c in df_or_gdf.columns), None)
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
    if st.button('[确认加载]', use_container_width=True, type='primary'):
        st.session_state['folder_key'] = folder_key
        st.session_state['file_choice'] = file_choice
        st.session_state['file_path'] = os.path.join(folder_path, file_choice)
        st.session_state['_data_confirmed'] = True


# ═══════════════════════════════════════════════════════════
# 弹窗：数据概览
# ═══════════════════════════════════════════════════════════
@st.dialog('[OV] 数据概览', width='large')
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
            render_polarity_stats(df, show_score=False)
            render_polarity_chart(df, height=200)
        if has_sc:
            st.caption(f"得分 — 均值: **{df['score'].mean():.2f}** | "
                       f"中位数: **{df['score'].median():.2f}** | "
                       f"标准差: **{df['score'].std():.2f}**")

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
            poi_chart = alt.Chart(poi_counts.reset_index().set_axis(['POI','数量'], axis=1)
                ).mark_bar().encode(y=alt.Y('POI:N', sort='-x', title=None),
                x=alt.X('数量:Q', title=None), color=alt.value('#4a90d9')
                ).properties(height=300)
            st.altair_chart(poi_chart, width='stretch')

    st.download_button('[下载] CSV', df.to_csv(index=False).encode('utf-8'),
                       file_name=file_choice, mime='text/csv')


# ═══════════════════════════════════════════════════════════
# 弹窗：数据表格
# ═══════════════════════════════════════════════════════════
@st.dialog('[TB] 数据表格', width='large')
def show_table_dialog():
    df = st.session_state.get('current_df')
    fc = st.session_state.get('current_file_choice', '')
    if df is None: return
    st.caption(f'文件: `{fc}` | 共 **{len(df)}** 条记录')
    search = st.text_input('[*] 搜索（任意列匹配）', placeholder='输入关键词过滤...')
    disp = df
    if search:
        mask = disp.astype(str).apply(lambda r: r.str.contains(search, case=False, na=False).any(), axis=1)
        disp = disp[mask]; st.caption(f'筛选结果: {len(disp)} / {len(df)} 条')
    ch = [c for c in ['lon','lat','longitude','latitude','geometry'] if c in df.columns]
    sc = [c for c in disp.columns if c not in ch]
    st.dataframe(disp[sc], width='stretch', height=500)
    st.download_button('[下载] 筛选结果为 CSV', disp.to_csv(index=False).encode('utf-8'),
                       file_name=fc, mime='text/csv')


# ═══════════════════════════════════════════════════════════
# 弹窗：设置
# ═══════════════════════════════════════════════════════════
@st.dialog('[*] 设置与调试', width='small')
def show_settings_dialog():
    st.caption('调试信息面板')
    st.divider()
    fp = st.session_state.get('file_path', '')
    if fp:
        st.write(f'当前文件: `{os.path.basename(fp)}`')
    else:
        st.write('当前文件: (未加载)')
    st.write(f'文件夹: `{st.session_state.get("folder_key", "—")}`')
    st.write(f'Session keys: `{list(st.session_state.keys())}`')
    st.caption(f'DEBUG_MODE = {DEBUG_MODE}')


# ═══════════════════════════════════════════════════════════
# 弹窗：范围选择
# ═══════════════════════════════════════════════════════════
@st.dialog('[RNG] 分析范围', width='small')
def show_range_dialog():
    if st.session_state.get('_range_just_set'):
        del st.session_state['_range_just_set']
        return

    st.caption('分析范围由 `data/boundaries/` 目录定义。')

    # ── 上传（放在前面，上传完成后 Streamlit 自动重跑对话框）──
    upload_key = f'up_{st.session_state.get("_upload_seq", 0)}'
    uploaded = st.file_uploader(
        '上传矢量文件', key=upload_key,
        type=['geojson', 'json', 'gpkg', 'shp', 'shx', 'dbf', 'prj', 'cpg', 'zip'],
        accept_multiple_files=True,
        help='GeoJSON 选 1 个；Shapefile 按住 Ctrl 多选 .shp/.shx/.dbf',
    )
    if uploaded:
        try:
            save_uploaded_file(uploaded)
            st.session_state['_upload_seq'] = st.session_state.get('_upload_seq', 0) + 1
            # 不调 st.rerun()——Streamlit 上传完成后自动重跑对话框
        except Exception as e:
            st.error(f'保存失败: {e}')

    st.divider()

    # ── 文件列表（上传处理之后读取，保证新鲜）──
    files = list_boundary_files()
    if files:
        path = get_active_boundary_path()
        ranges = load_boundaries(path)
        names = list(ranges.keys())
        crs_info = get_boundary_crs_info()
        st.success(f'{files[0]}  |  {len(names)} 区域  |  {crs_info["note"] if crs_info else ""}')
    else:
        names = []
        st.info('暂无矢量文件')

    # ── 范围选择 ──
    if names:
        selected = st.multiselect(
            '目标区域', options=names, default=names,
            help='默认全选',
        ) or names

        if st.button('[确认范围]', type='primary', use_container_width=True):
            st.session_state['selected_ranges'] = selected
            st.session_state['_range_just_set'] = True
            st.rerun()


# ═══════════════════════════════════════════════════════════
# 弹窗：运行情绪分析
# ═══════════════════════════════════════════════════════════
@st.dialog('[ANA] 运行情绪分析', width='large')
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

    file_choice = st.selectbox('[FILE] 原始情绪DATA文件（L1）', raw_files,
                               help=f'来自 {RAW_DIR}/')
    st.caption(f'路径: `{os.path.join(RAW_DIR, file_choice)}`')

    st.divider()

    # ── 选择引擎 ──
    engine_choice = st.radio(
        '[ENG] 分析引擎',
        ['L2 · SnowNLP粗粒度分析 (离线)', 'L3 · LLM 细粒度语义解析 (需 API Key)', 'L4 · 语料库 + LLM 多维归因处理 (需语料库 和 API Key)'],
        help='L2 轻量免费; L3 需接入大模型 API; L4 需情绪语料库和大模型API'
    )

    api_key = ''
    if 'LLM' in engine_choice:
        api_key = st.text_input('[KEY] API Key',
                                type='password',
                                placeholder='sk-...',
                                help='DeepSeek/Qwen/GLM 等模型的 API Key')

    st.divider()

    # ── 执行 ──
    run_clicked = st.button('[开始分析]', type='primary',
                             use_container_width=True)

    if run_clicked:
        engine_type = 'llm' if 'LLM' in engine_choice else 'snownlp'
        input_path = os.path.join(RAW_DIR, file_choice)
        base_name = os.path.splitext(file_choice)[0]

        with st.status('分析中...', expanded=True) as status:
            try:
                result = run_analysis_task(
                    file_path=input_path,
                    engine_type=engine_type,
                    output_name=base_name,
                    api_key=api_key,
                )
                if result['success']:
                    status.update(
                        label=f'[OK] 分析完成！{result["n_points"]} 条数据',
                        state='complete')
                    # 设置 session_state 使地图加载结果
                    st.session_state['folder_key'] = list(FOLDER_OPTIONS.keys())[1]  # processed
                    st.session_state['file_choice'] = os.path.basename(result['csv_path'])
                    st.session_state['file_path'] = result['csv_path']
                    st.session_state['current_df'] = result['df']
                    st.session_state['current_file_choice'] = os.path.basename(result['csv_path'])
                    st.session_state['data_loaded'] = True
                    run_success = True
                    result_df = result['df']
                    result_csv = result['csv_path']
                else:
                    status.update(label='[WARN] 分析失败', state='error')
                    st.error(f'分析失败: {result["message"][:200]}')
                    run_success = False
                    result_df = None
                    result_csv = None
            except Exception as e:
                status.update(label='[ERR] 分析出错', state='error')
                st.error(f'分析失败: {str(e)[:200]}')
                _safe_print(f'[ERR] show_analysis_dialog 分析出错: {e}')
                run_success = False
                result_df = None
                result_csv = None

        # ── 结果子面板（共享极性统计函数）──
        if run_success and result_df is not None:
            st.divider()
            st.subheader('分析结果预览')
            if 'polarity' in result_df.columns:
                render_polarity_stats(result_df, show_score=True)
                render_polarity_chart(result_df, height=200)
            else:
                st.caption(f'共 {len(result_df)} 条数据（无极性列）')

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

def _parse_console_params():
    """解析 URL 参数，返回自动加载模式的数据上下文。

    返回 dict:
        auto_file, auto_loaded_df, auto_loaded_n, auto_loaded_score,
        auto_loaded_stats, is_auto_mode
    """
    result = {
        'auto_file': None,
        'auto_loaded_df': None,
        'auto_loaded_n': 0,
        'auto_loaded_score': 0.0,
        'auto_loaded_stats': None,
        'is_auto_mode': False,
    }

    auto_file = st.query_params.get('file', None)
    if not auto_file or not os.path.exists(auto_file):
        return result

    try:
        data = load_emotion_data(auto_file)
        if data:
            auto_loaded_df = data['df']
            auto_loaded_stats = None
            auto_loaded_score = 0.0
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

            result.update({
                'auto_file': auto_file,
                'auto_loaded_df': auto_loaded_df,
                'auto_loaded_n': data['n_points'],
                'auto_loaded_score': auto_loaded_score,
                'auto_loaded_stats': auto_loaded_stats,
                'is_auto_mode': True,
            })
    except Exception:
        _safe_print(f'[WARN] 无法加载自动文件: {auto_file}')

    return result


def _render_console_sidebar(params: dict):
    """渲染分析控制台侧边栏，返回引擎配置。

    返回 dict:
        engine_choice, api_key, corpus_path, enable_keywords
    """
    with st.sidebar:
        if params['is_auto_mode']:
            st.success(f'已加载: {os.path.basename(params["auto_file"])}')
            st.caption(f'{params["auto_loaded_n"]} 条数据')
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

    return {
        'engine_choice': engine_choice,
        'api_key': api_key,
        'corpus_path': corpus_path,
        'enable_keywords': enable_keywords,
    }


def _render_auto_loaded_view(params: dict):
    """模式 A: 展示自动加载的分析结果（含极性统计/图表/导出/数据表）。"""
    auto_file = params['auto_file']
    auto_loaded_df = params['auto_loaded_df']
    auto_loaded_n = params['auto_loaded_n']
    auto_loaded_score = params['auto_loaded_score']
    auto_loaded_stats = params['auto_loaded_stats']

    if auto_loaded_df is None:
        return

    st.caption(f'文件: `{auto_file}` | {auto_loaded_n} 条记录')
    if auto_loaded_stats and 'polarity' in auto_loaded_df.columns:
        with st.expander(f'分析结果 · {auto_loaded_n} 条数据', expanded=True):
            render_polarity_stats(auto_loaded_df, show_score=True)
            render_polarity_chart(auto_loaded_df, height=250)
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


def _render_new_analysis_view(engine_cfg: dict):
    """模式 B: 选择新文件并运行分析（文件选择 + 分析触发）。"""
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
            engine_choice = engine_cfg['engine_choice']
            if 'L3' in engine_choice: eng_type = 'llm'
            elif 'L4' in engine_choice: eng_type = 'corpus'
            elif '全管道' in engine_choice: is_full = True
            with st.status('分析中...', expanded=True) as status:
                result = run_analysis_task(
                    file_path=input_path, engine_type=eng_type,
                    output_name=output_name, api_key=engine_cfg['api_key'],
                    corpus_path=engine_cfg['corpus_path'],
                    enable_keywords=engine_cfg['enable_keywords'],
                    full_pipeline=is_full,
                )
                if result['success']:
                    status.update(label=f'完成！{result["n_points"]} 条', state='complete')
                    st.rerun()
                else:
                    status.update(label='失败', state='error')
                    st.error(result['message'])


def _add_boundary_if_exists(m):
    """如果存在边界文件，叠加到地图。"""
    try:
        geojson = get_boundary_geojson()
        if geojson:
            add_boundary_layer(m, geojson_data=geojson, name='分析范围')
    except Exception:
        pass


def show_console_page():
    """分析控制台主入口 — 委托给 4 个子函数处理。"""
    st.title('情绪分析控制台')
    st.caption('从地图浏览器跳转而来')

    # 1. 解析 URL 参数
    params = _parse_console_params()

    # 2. 渲染侧边栏
    engine_cfg = _render_console_sidebar(params)

    # 3. 模式 A: 自动加载结果
    if params['is_auto_mode']:
        _render_auto_loaded_view(params)

    # 4. 模式 B: 手动分析新文件
    _render_new_analysis_view(engine_cfg)


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════
def main():
    # ── session_state 初始化（所有页面共享，必须在路由判断前）──
    for k, v in {
        'show_labels': True, 'show_legend': True,
        'folder_key': '[DATA] raw（原始数据）',
        'file_choice': '', 'file_path': '',
        'current_df': None, 'current_map_meta': None,
        'current_file_choice': '', 'data_loaded': False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Dialog 确认标记检测 ──
    if st.session_state.get('_data_confirmed'):
        st.session_state['_data_confirmed'] = False
        st.rerun()

    # ── 路由：?page=console → 分析控制台 ──
    page = st.query_params.get('page', None)
    if page == 'console':
        show_console_page()
        return

    # ── CSS 注入（统一由 ui_components 管理）──
    inject_fullscreen_css()
    hud_button_style_css()

    # ── HUD ──
    fc = st.session_state.get('file_choice', '')
    btn_dis = st.session_state.get('current_df') is None

    if fc:
        render_title_bar(f'情绪地图 v1.0 "{fc}"')

    if st.button('R', help='[R] 分析范围 | 选择分析区域', key='rng'): show_range_dialog()
    if st.button('D', help='[D] 数据源 | 选择情绪数据文件 (CSV/GeoJSON)', key='d'): show_data_source_dialog()
    if st.button('A', help='[A] 分析引擎 | 运行 L2/L3/L4 情绪分析管道', key='a'): show_analysis_dialog()
    if st.button('[*]', help='设置与调试', key='s'): show_settings_dialog()

    sl = st.session_state.get('show_labels', True)
    if st.button('[LB]', help='注记: 开' if sl else '注记: 关', key='lbl'):
        st.session_state['show_labels'] = not sl; st.rerun()
    sg = st.session_state.get('show_legend', True)
    if st.button('[LG]', help='图例: 开' if sg else '图例: 关', key='leg'):
        st.session_state['show_legend'] = not sg; st.rerun()

    if st.button('[OV]', help='数据概览', key='o', disabled=btn_dis): show_overview_dialog()
    if st.button('[TB]', help='数据表格', key='t', disabled=btn_dis): show_table_dialog()

    if st.session_state.get('show_legend', True) and not btn_dis:
        render_legend_overlay(mode='point')

    # ── 数据加载 + 地图 ──
    fp = st.session_state.get('file_path', '')
    if not fp or not os.path.exists(fp):
        m = create_base_map(show_labels=st.session_state.get('show_labels', True))
        if st.session_state.get('selected_ranges'):
            _add_boundary_if_exists(m)
        st_folium(m, width=None, height=700, key='default_map')
        return

    with st.spinner('加载数据中...'):
        data = load_emotion_data(fp)
    if not data:
        st.error('无法加载数据，请检查文件格式或重新选择数据源')
        return

    df = data['df']
    st.session_state['current_df'] = df
    st.session_state['current_file_choice'] = fc
    st.session_state['data_loaded'] = True
    st.toast('[OK] 数据加载成功')

    with st.spinner('渲染地图中...'):
        m = create_base_map(data['lats'], data['lons'],
                            show_labels=st.session_state.get('show_labels', True))

        # 叠加范围边界
        _add_boundary_if_exists(m)

        geo = data.get('geo_data')
        if geo:
            add_point_layer(m, data['lats'], data['lons'], data['scores'],
                           props_list=geo['features'])
        else:
            add_point_layer(m, data['lats'], data['lons'], data['scores'],
                           props_list=df.to_dict('records'))

    # ── 数据摘要浮层（左上角）──
    n = len(df)
    ranges = st.session_state.get('selected_ranges', [])
    area_label = ranges[0] if ranges else ''
    range_label = f'共 {len(ranges)} 区' if len(ranges) > 1 else ''
    date_label = ''
    m_date = _re.search(r'(\d{8})', fc)
    if m_date:
        date_label = m_date.group(1)
    render_data_summary_overlay(n=n, area_label=area_label,
                                 range_label=range_label, date_label=date_label)

    st_folium(m, width=None, height=700, key='geojson_map')


if __name__ == '__main__':
    main()
