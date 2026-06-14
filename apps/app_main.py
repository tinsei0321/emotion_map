"""
情绪地图 v1.0 — 地图浏览器 + 分析控制台
══════════════════════════════════════════════════════════════
启动: py launch.py                    # 一键启动
      python -m streamlit run apps/app_main.py

页面: 默认 = 地图浏览器
      ?page=console&file=xxx  = 分析控制台（自动加载结果）
"""
# 本地访问：http://localhost:8501


import os, sys
from collections import Counter
import re as _re
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import altair as alt
import pydeck as pdk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import (
    FOLDER_OPTIONS, DEFAULT_CENTER, DEFAULT_ZOOM, RAW_DIR, PROCESSED_DIR,
    MAX_DISPLAY_POINTS, MAX_TABLE_ROWS, LARGE_FILE_WARN_MB,
    BOUNDARY_SHP,
)
from core.export import export_to_csv
from core.map_engine import create_base_map, add_point_layer, add_boundary_layer, add_heatmap_layer, MAP_STYLE_LABELS, MAP_STYLE_PREVIEW_COLORS
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
    inject_theme_css,
)
from SCRIPT.emotion_analysis_v1 import (
    create_analyzer, run_pipeline, run_analysis_task, _safe_print,
)
from SCRIPT.data_governance import (
    step1_load_and_transform,
    step4_run_l2_analysis,
)
from SCRIPT.relevance_filter import keyword_prefilter, _build_text_for_classification
from core.tracker import track, TrackContext, trace_log, trace_error, trace_warn, register_track_id

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
@track("MOD_APP.F_005", track_args=False)
@st.dialog('[DATA] 数据源', width='small')
def show_data_source_dialog():
    """数据源选择弹窗 — 仅列出 PROCESSED_DIR 中的 L1/L2 结果文件。"""
    folder_path = PROCESSED_DIR
    st.caption(f'数据目录: `{PROCESSED_DIR}`')
    if not os.path.exists(folder_path):
        st.warning(f'不存在: {folder_path}')
        return
    files = sorted([f for f in os.listdir(folder_path)
                    if os.path.isfile(os.path.join(folder_path, f))])
    if not files:
        st.info('暂无数据文件。请先生成 L1 模拟数据：`python SCRIPT/generate_l1_mock.py`')
        return
    cur = st.session_state.get('file_choice', files[0])
    idx = files.index(cur) if cur in files else 0
    file_choice = st.selectbox('选择文件', files, index=idx)
    file_size = os.path.getsize(os.path.join(folder_path, file_choice)) / (1024 * 1024)
    st.caption(f'大小: {file_size:.1f} MB | 路径: `{os.path.join(folder_path, file_choice)}`')
    if file_size > LARGE_FILE_WARN_MB:
        st.warning(f'文件较大 ({file_size:.0f} MB)，地图将自动采样显示。')
    if st.button('[确认加载]', use_container_width=True, type='primary'):
        st.session_state['folder_key'] = '[DATA] processed（处理结果）'
        st.session_state['file_choice'] = file_choice
        st.session_state['file_path'] = os.path.join(folder_path, file_choice)
        st.session_state['_load_triggered'] = True
        st.session_state['_all_layers_hidden'] = False
        _register_layer(
            name=file_choice,
            file_path=os.path.join(folder_path, file_choice),
            level='L1',
            range_label='processed',
            color='#48C9B0',
        )
        st.rerun()


# ═══════════════════════════════════════════════════════════
# 弹窗：数据概览
# ═══════════════════════════════════════════════════════════
@track("MOD_APP.F_006", track_args=False)
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
                x=alt.X('数量:Q', title=None), color=alt.value('#5DADE2')
                ).properties(height=300)
            st.altair_chart(poi_chart, width='stretch')

    st.download_button('[下载] CSV', df.to_csv(index=False).encode('utf-8'),
                       file_name=file_choice, mime='text/csv')


# ═══════════════════════════════════════════════════════════
# 弹窗：数据表格
# ═══════════════════════════════════════════════════════════
@track("MOD_APP.F_007", track_args=False)
@st.dialog('[TB] 数据表格', width='large')
def show_table_dialog():
    processed_files = []
    if os.path.exists(PROCESSED_DIR):
        processed_files = sorted([f for f in os.listdir(PROCESSED_DIR)
                                  if os.path.isfile(os.path.join(PROCESSED_DIR, f))
                                  and f.lower().endswith(('.csv', '.tsv'))])
    df = st.session_state.get('current_df')
    fc = st.session_state.get('current_file_choice', '')
    if processed_files:
        choice = st.selectbox('选择数据文件', processed_files,
                             index=processed_files.index(fc) if fc in processed_files else 0)
        if choice != fc:
            fp = os.path.join(PROCESSED_DIR, choice)
            data = load_emotion_data(fp)
            if data:
                df = data['df']
                fc = choice
    if df is None: return
    st.caption(f'文件: `{fc}` | 共 **{len(df)}** 条记录')
    search = st.text_input('[*] 搜索（任意列匹配）', placeholder='输入关键词过滤...')
    disp = df
    if search:
        mask = disp.astype(str).apply(lambda r: r.str.contains(search, case=False, na=False).any(), axis=1)
        disp = disp[mask]; st.caption(f'筛选结果: {len(disp)} / {len(df)} 条')
    ch = [c for c in ['lon','lat','longitude','latitude','geometry'] if c in df.columns]
    sc = [c for c in disp.columns if c not in ch]
    if len(disp) > MAX_TABLE_ROWS:
        disp = disp.head(MAX_TABLE_ROWS)
        st.caption(f'表格仅显示前 {MAX_TABLE_ROWS} 行（共 {len(df)} 行）')
    st.dataframe(disp[sc], width='stretch', height=500)
    st.download_button('[下载] 筛选结果为 CSV', disp.to_csv(index=False).encode('utf-8'),
                       file_name=fc, mime='text/csv')


# ═══════════════════════════════════════════════════════════
# 弹窗：设置
# ═══════════════════════════════════════════════════════════
@track("MOD_APP.F_008", track_args=False)
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
@track("MOD_APP.F_009", track_args=False)
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

        # ── 边界样式调节 ──
        st.divider()
        st.caption('边界线样式')

        # 粗细选择
        line_weight = st.slider(
            '线宽', min_value=1, max_value=20,
            value=st.session_state.get('_boundary_weight', 4),
            step=1, help='边界线粗细（像素）'
        )

        # 颜色选择
        boundary_colors = {
            '蓝色': '#5DADE2',
            '青蓝 (Kepler)': '#1DBAD4',
            '活力橙': '#d97d5c',
            '自然绿': '#48C9B0',
            '警示红': '#E06050',
            '白色': '#FFFFFF',
            '亮黄': '#F0A050',
        }
        color_name = st.selectbox(
            '颜色', options=list(boundary_colors.keys()),
            index=list(boundary_colors.keys()).index(
                st.session_state.get('_boundary_color_name', '活力橙')
            )
        )

        if st.button('[确认范围]', type='primary', use_container_width=True):
            st.session_state['selected_ranges'] = selected
            st.session_state['_boundary_weight'] = line_weight
            st.session_state['_boundary_color'] = boundary_colors[color_name]
            st.session_state['_boundary_color_name'] = color_name
            st.session_state['_range_just_set'] = True
            st.rerun()


# ═══════════════════════════════════════════════════════════
# 弹窗：数据治理
# ═══════════════════════════════════════════════════════════
@track("MOD_APP.F_003", track_args=False)
@st.dialog('[GV] 数据治理', width='large')
def show_governance_dialog():
    """数据治理弹窗：L0原始数据 → L1城市情绪DATA

    治理步骤 (v1.0 关键词模式):
      1. 坐标转换 (GCJ-02 → WGS84 → CGCS2000)
      2. 范围过滤 (规划范围 Polygon 内)
      3. 相关性筛选 (关键词粗筛)
      4. 数据脱敏 → 导出 L1 CSV

    注意: v2.0 LLM 批量分类模式请通过 CLI 运行:
      python SCRIPT/data_governance.py
    """
    # ── 区域1: 选择 L0 文件 ──
    raw_files = sorted([
        f for f in os.listdir(RAW_DIR)
        if f.endswith('.csv') and '_result_' not in f.lower()
    ]) if os.path.exists(RAW_DIR) else []
    if not raw_files:
        st.warning(f'`{RAW_DIR}/` 中没有可治理的 L0 文件。请先采集原始数据。')
        return

    file_choice = st.selectbox('[L0] 原始数据文件', raw_files)
    input_path = os.path.join(RAW_DIR, file_choice)
    file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
    st.caption(f'大小: {file_size_mb:.1f} MB | 路径: `{input_path}`')

    # ── 区域2: 治理步骤说明 ──
    with st.expander('[步骤说明] 治理管道详情 (v1.0 关键词模式)'):
        st.markdown(
            '1. 坐标转换 GCJ-02 -> WGS84 -> CGCS2000 EPSG:4546\n'
            '2. 范围过滤 (规划边界 Polygon point-in-polygon)\n'
            '3. 相关性筛选 (关键词正负信号评分)\n'
            '4. 数据脱敏 + 导出 L1 CSV\n\n'
            '[INFO] v2.0 LLM 批量分类模式（更精准）请通过 CLI 运行:\n'
            '`python SCRIPT/data_governance.py`'
        )

    # ── 区域3: [开始数据治理] ──
    if st.button('[开始数据治理]', type='primary', use_container_width=True):
        with st.status('治理中...', expanded=True) as status:
            progress = st.progress(0, text='准备...')

            # Step 1: 坐标转换
            status.update(label='[1/4] 坐标转换...')
            progress.progress(0.25, text='GCJ-02 -> WGS84 -> CGCS2000')
            df = step1_load_and_transform(input_path)
            input_n = len(df)

            # Step 2: 范围过滤
            status.update(label='[2/4] 范围过滤...')
            progress.progress(0.5, text='Point-in-Polygon')
            boundary_path = get_active_boundary_path()
            if boundary_path and os.path.exists(boundary_path):
                df_filtered = step2_filter_by_boundary(df, boundary_path)
            elif os.path.exists(BOUNDARY_SHP):
                df_filtered = step2_filter_by_boundary(df, BOUNDARY_SHP)
            else:
                _safe_print('[WARN] 无边界文件，跳过范围过滤')
                progress.progress(0.5, text='[WARN] 跳过范围过滤（无边界文件）')
                df_filtered = df

            # Step 3: 关键词粗筛
            status.update(label='[3/4] 相关性筛选...')
            progress.progress(0.75, text='关键词粗筛')
            df_filtered['_kw_pass'] = df_filtered.apply(
                lambda row: keyword_prefilter(_build_text_for_classification(row)) == 'pass',
                axis=1)
            df_relevant = df_filtered[df_filtered['_kw_pass']].copy()
            df_relevant['relevance'] = 'relevant'
            df_relevant['filter_layer'] = 'keyword'
            df_relevant.drop(columns=['_kw_pass'], inplace=True, errors='ignore')

            # Step 4: 脱敏+导出 L1
            status.update(label='[4/4] 脱敏+导出 L1...')
            progress.progress(0.9, text='导出 L1 CSV')
            df_relevant = anonymize_dataframe(df_relevant)
            output_name = os.path.splitext(file_choice)[0].replace('_raw', '')
            # 添加范围后缀（与 data_governance.py v2.0 命名一致）
            output_name = f'{output_name}_规划范围'
            l1_path = os.path.join(PROCESSED_DIR, f'{output_name}_L1_result_csv.csv')
            export_to_csv(df_relevant, l1_path)

            status.update(label=f'[OK] L1 治理完成: {len(df_relevant)} 条', state='complete')
            progress.progress(1.0, text=f'L1: {len(df_relevant)} 条 ({input_n} → {len(df_relevant)})')

            # 记录结果
            st.session_state['_governance_done'] = True
            st.session_state['_governance_result'] = {
                'input_n': input_n,
                'l1_n': len(df_relevant),
                'l1_path': l1_path,
                'output_name': output_name,
            }
            # 保持向后兼容
            st.session_state['governance_completed'] = True
            st.session_state['governance_last_stats'] = {
                'input_file': file_choice,
                'input_n': input_n,
                'output_n': len(df_relevant),
                'relevant_n': len(df_relevant),
                'irrelevant_n': input_n - len(df_relevant),
                'time_elapsed': '—',
                'output_path': l1_path,
            }

        # ── 区域4: 结果面板 ──
        if st.session_state.get('_governance_done'):
            r = st.session_state['_governance_result']
            c1, c2, c3 = st.columns(3)
            c1.metric('输入', r['input_n'])
            c2.metric('L1 输出', r['l1_n'])
            c3.metric('过滤率', f"{(1 - r['l1_n'] / max(r['input_n'], 1)) * 100:.1f}%")
            st.caption(f"输出: `{r['l1_path']}`")

            col_map, col_l2 = st.columns(2)
            with col_map:
                if st.button('[加载到地图]', type='primary', use_container_width=True):
                    st.session_state['file_path'] = r['l1_path']
                    st.session_state['file_choice'] = os.path.basename(r['l1_path'])
                    st.session_state['_load_triggered'] = True
                    _register_layer(
                        name=os.path.basename(r['l1_path']),
                        file_path=r['l1_path'],
                        level='L1',
                        range_label='当前范围',
                        color='#48C9B0'
                    )
                    st.rerun()
            with col_l2:
                if st.button('[运行 L2 情绪分析]', use_container_width=True,
                            help='对刚生成的 L1 数据运行 SnowNLP 情绪分析'):
                    with st.status('L2 分析中...', expanded=True) as l2_status:
                        l2_result = step4_run_l2_analysis(r['l1_path'], r['output_name'])
                        if l2_result['success']:
                            l2_status.update(label=f'[OK] L2 完成: {l2_result["n_points"]} 条', state='complete')
                            st.session_state['folder_key'] = list(FOLDER_OPTIONS.keys())[1]
                            st.session_state['file_choice'] = os.path.basename(l2_result['csv_path'])
                            st.session_state['file_path'] = l2_result['csv_path']
                            st.session_state['current_df'] = l2_result['df']
                            st.session_state['data_loaded'] = True
                            _register_layer(
                                name=os.path.basename(l2_result['csv_path']),
                                file_path=l2_result['csv_path'],
                                level='L2',
                                range_label='分析结果',
                                color='#48C9B0',
                            )
                            st.rerun()
                        else:
                            l2_status.update(label='[ERR] L2 失败', state='error')
                            st.error(l2_result['message'])


# ═══════════════════════════════════════════════════════════
# 弹窗：图层控制
# ═══════════════════════════════════════════════════════════
@track("MOD_APP.F_004", track_args=True)
def _register_layer(name, file_path, level='L1', range_label='', color='#48C9B0'):
    """注册或更新一个图层到 session_state['layers']。

    参数:
        name: 图层显示名称
        file_path: 数据文件路径（用于去重和加载）
        level: 数据层级标签 (L0/L1/L2/L3/L4)
        range_label: 范围/来源标签
        color: 图层颜色标识
    """
    layers = st.session_state.get('layers', [])
    # 去重：同路径已存在则更新
    for lyr in layers:
        if lyr['file_path'] == file_path:
            lyr['name'] = name
            lyr['level'] = level
            lyr['range_label'] = range_label
            lyr['color'] = color
            return
    layers.append({
        'name': name,
        'file_path': file_path,
        'level': level,
        'range_label': range_label,
        'color': color,
        'visible': True,
    })
    st.session_state['layers'] = layers


# ═══════════════════════════════════════════════════════════
# 弹窗：底图切换
# ═══════════════════════════════════════════════════════════
@track("MOD_APP.F_010", track_args=False)
@st.dialog('[Map] 底图切换', width='small')
def show_basemap_dialog():
    """底图切换弹窗：单选切换底图样式，即刻生效。"""
    current = st.session_state.get('_map_style', 'carto_dark')

    st.caption('点击底图样式即刻切换，地图自动刷新')

    options = list(MAP_STYLE_LABELS.keys())

    # ── 颜色预览条（顶部快速视觉扫描）──
    swatch_parts = []
    for key in options:
        color = MAP_STYLE_PREVIEW_COLORS.get(key, 'var(--color-neutral-300)')
        is_active = (key == current)
        border = (
            'var(--color-brand-primary)'
            if is_active
            else 'var(--color-functional-border-light)'
        )
        shadow = 'var(--shadow-glow)' if is_active else 'none'
        tooltip = MAP_STYLE_LABELS.get(key, key)
        if is_active:
            tooltip += ' (current)'
        swatch_parts.append(
            f'<span style="display:inline-block;'
            f'width:44px;height:22px;'
            f'border-radius:var(--radius-sm);'
            f'background:{color};'
            f'border:2px solid {border};'
            f'box-shadow:{shadow};'
            f'margin-right:6px;'
            f'transition:border-color var(--effect-transition-fast),'
            f'box-shadow var(--effect-transition-fast);"'
            f'title="{tooltip}"></span>'
        )

    st.markdown(
        f'<div style="display:flex;align-items:center;'
        f'padding:2px 0 12px 0;">'
        f'{"".join(swatch_parts)}'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── 单选控件（唯一交互入口，取代原来的静态列表 + 隐藏 selectbox）──
    choice = st.radio(
        '底图样式',
        options=options,
        format_func=lambda k: MAP_STYLE_LABELS.get(k, k),
        index=options.index(current) if current in options else 0,
        label_visibility='collapsed',
    )

    if choice != current:
        st.session_state['_map_style'] = choice
        st.rerun()


@track("MOD_APP.F_011", track_args=False)
@st.dialog('[LY] 图层控制', width='small')
def show_layer_dialog():
    """图层控制弹窗：checkbox 控制图层显示/隐藏。

    每行: 颜色圆点 + 图层名 + checkbox
    底部: [全部打开] [全部关闭]
    """
    layers = st.session_state.get('layers', [])

    if not layers:
        st.info('暂无注册图层。\n\n通过 [D] 加载数据后，图层自动注册到此列表。')
        return

    st.caption(f'共 {len(layers)} 个图层')
    st.divider()

    for i, lyr in enumerate(layers):
        col_dot, col_name, col_check = st.columns([0.3, 3.7, 0.8])
        with col_dot:
            st.markdown(
                f'<span style="color:{lyr["color"]};font-size:1.2rem;">●</span>',
                unsafe_allow_html=True)
        with col_name:
            st.caption(f'{lyr["name"]}  `{lyr.get("level","")}`')
        with col_check:
            checked = st.checkbox('', value=lyr.get('visible', True),
                                  key=f'lyr_{i}',
                                  label_visibility='collapsed')
            if checked != lyr.get('visible', True):
                layers[i]['visible'] = checked
                st.session_state['layers'] = layers
                # ── 同步主数据层可见性 ──
                if lyr['file_path'] == st.session_state.get('file_path', ''):
                    st.session_state['_all_layers_hidden'] = not checked

    st.divider()
    # ── 确定按钮（红色，凸显重要性）──
    st.markdown("""
    <style>
    button[kind="danger"] {
        background-color: #E06050 !important;
        border-color: #C0392B !important;
        color: #fff !important;
    }
    button[kind="danger"]:hover {
        background-color: #C0392B !important;
    }
    </style>
    """, unsafe_allow_html=True)
    if st.button('[确定]', key='lyr_confirm', type='primary',
                use_container_width=True):
        st.rerun()
    st.caption('— 批量操作 —')
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button('[全部打开]', use_container_width=True, key='lyr_all_on'):
            for lyr in layers:
                lyr['visible'] = True
            st.session_state['layers'] = layers
            st.session_state['_all_layers_hidden'] = False
            st.rerun()
    with bc2:
        if st.button('[全部关闭]', use_container_width=True, key='lyr_all_off'):
            for lyr in layers:
                lyr['visible'] = False
            st.session_state['layers'] = layers
            st.session_state['_all_layers_hidden'] = True
            st.rerun()


# ═══════════════════════════════════════════════════════════
# 弹窗：运行情绪分析
# ═══════════════════════════════════════════════════════════
@track("MOD_APP.F_011", track_args=False)
@st.dialog('[ANA] 运行情绪分析', width='large')
def show_analysis_dialog():
    st.markdown('选择已完成治理的 L1 数据文件并运行情绪分析引擎，结果自动加载到地图。')

    # ── 选择文件（仅从 PROCESSED_DIR 选择 L1 文件）──
    l1_files = []
    if os.path.exists(PROCESSED_DIR):
        l1_files = sorted([f for f in os.listdir(PROCESSED_DIR)
                          if os.path.isfile(os.path.join(PROCESSED_DIR, f))
                          and f.lower().endswith(('.csv', '.tsv', '.json', '.geojson'))
                          and not f.lower().endswith('.geojson')
                          and '_L2_result' not in f
                          and '_L3_result' not in f
                          and '_L4_result' not in f])  # 仅 L1 文件，排除 L2/L3/L4 结果

    if not l1_files:
        st.warning(f'`{PROCESSED_DIR}/` 中没有可分析的 L1 文件。请先生成 L1 模拟数据：`python SCRIPT/generate_l1_mock.py`')
        return

    source_dir = PROCESSED_DIR
    source_label = 'PROCESSED_DIR (L1)'

    file_choice = st.selectbox('[FILE] 待分析数据文件', l1_files,
                               help=f'仅 L1 治理后数据 (不含 _L2/L3/L4_result)。来自 {source_label}: {source_dir}/')
    st.caption(f'路径: `{os.path.join(source_dir, file_choice)}`')

    # ── 输入数据校验 ──
    input_path = os.path.join(source_dir, file_choice)
    try:
        sample = pd.read_csv(input_path, nrows=1)
        has_l1_markers = ('relevance' in sample.columns or 'in_scope' in sample.columns)
        if not has_l1_markers:
            st.warning('[WARN] 所选文件缺少 L1 治理标记列（relevance/in_scope）。建议使用 `generate_l1_mock.py` 生成标准 L1 数据。')
        n_rows = len(pd.read_csv(input_path))
        if n_rows > 10000:
            st.info(f'文件包含 {n_rows:,} 条记录。分析可能需要较长时间。')
    except Exception as e:
        st.warning(f'无法预览文件: {e}')

    # ── L1 数据概览（折叠，默认收起）──
    with st.expander('[L1 数据概览]', expanded=False):
        gov_result = st.session_state.get('_governance_result')
        if gov_result:
            c1, c2 = st.columns(2)
            c1.metric('最近 L1 输出', gov_result['l1_n'])
            c2.metric('输入', gov_result['input_n'])
            st.caption(f"路径: `{gov_result['l1_path']}`")
        else:
            st.caption('暂无治理记录。使用 `python SCRIPT/generate_l1_mock.py` 生成 L1 模拟数据。')

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

    # ── 文件变更检测：新文件重置分析状态 ──
    if st.session_state.get('_last_analyzed_file', '') != file_choice:
        st.session_state['_analysis_done'] = False
        st.session_state['_last_analyzed_file'] = ''
        st.session_state['_last_analysis_result'] = None
        st.session_state['_analysis_show_results'] = False

    # ── 执行 ──
    analysis_done = st.session_state.get('_analysis_done', False) and \
                    st.session_state.get('_last_analyzed_file', '') == file_choice
    btn_label = '[在地图上显示]' if analysis_done else '[开始分析]'
    run_clicked = st.button(btn_label, type='primary',
                             use_container_width=True)

    if run_clicked:
        if analysis_done:
            # ── 模式 B: 加载到地图 ──
            saved = st.session_state.get('_last_analysis_result')
            if saved:
                st.session_state['folder_key'] = list(FOLDER_OPTIONS.keys())[1]
                st.session_state['file_choice'] = os.path.basename(saved['csv_path'])
                st.session_state['file_path'] = saved['csv_path']
                st.session_state['current_df'] = saved['df']
                st.session_state['current_file_choice'] = os.path.basename(saved['csv_path'])
                st.session_state['data_loaded'] = True
                _register_layer(
                    name=os.path.basename(saved['csv_path']),
                    file_path=saved['csv_path'],
                    level='L2',
                    range_label='分析结果',
                    color='#48C9B0',
                )
                st.success(f'已加载 {saved["n_points"]} 条数据到地图。关闭对话框查看。')
        else:
            # ── 模式 A: 运行分析 ──
            engine_type = 'llm' if 'LLM' in engine_choice else 'snownlp'
            _input_path = os.path.join(source_dir, file_choice)
            _base_name = os.path.splitext(file_choice)[0]
            _base_name = _base_name.replace('_raw', '').replace('_RAW', '')
            file_size_mb = os.path.getsize(_input_path) / (1024 * 1024)

            progress_bar = st.progress(0, text='准备分析...')

            def update_progress(step, total, message):
                progress_bar.progress(step / total, text=message)

            with st.status('分析中...', expanded=True) as status:
                status.update(label=f'文件: {_base_name} ({file_size_mb:.0f} MB)')

                try:
                    result = run_analysis_task(
                        file_path=_input_path,
                        engine_type=engine_type,
                        output_name=_base_name,
                        api_key=api_key,
                        progress_callback=update_progress,
                    )
                    if result['success']:
                        progress_bar.progress(1.0, text=f'[OK] {result["n_points"]} 条完成')
                        status.update(
                            label=f'[OK] 分析完成！{result["n_points"]} 条数据',
                            state='complete')
                        # 保存结果 + 自动加载到地图 + 标记完成
                        st.session_state['_analysis_done'] = True
                        st.session_state['_last_analyzed_file'] = file_choice
                        st.session_state['_last_analysis_result'] = result
                        st.session_state['_analysis_show_results'] = True
                        # 自动加载到地图
                        st.session_state['folder_key'] = list(FOLDER_OPTIONS.keys())[1]
                        st.session_state['file_choice'] = os.path.basename(result['csv_path'])
                        st.session_state['file_path'] = result['csv_path']
                        st.session_state['current_df'] = result['df']
                        st.session_state['current_file_choice'] = os.path.basename(result['csv_path'])
                        st.session_state['data_loaded'] = True
                        _register_layer(
                            name=os.path.basename(result['csv_path']),
                            file_path=result['csv_path'],
                            level='L2',
                            range_label='分析结果',
                            color='#48C9B0',
                        )
                        st.rerun()  # 刷新对话框，按钮变为"[在地图上显示]"
                    else:
                        progress_bar.progress(1.0, text='[WARN] 分析失败')
                        status.update(label='[WARN] 分析失败', state='error')
                        st.error(f'分析失败: {result["message"][:200]}')
                except Exception as e:
                    progress_bar.progress(1.0, text='[ERR] 分析失败')
                    status.update(label='[ERR] 分析出错', state='error')
                    st.error(f'分析失败: {str(e)[:200]}')
                    _safe_print(f'[ERR] show_analysis_dialog 分析出错: {e}')
                    trace_error("MOD_APP.F_011", f'分析执行异常: {str(e)[:200]}')

    # ── 结果子面板（分析完成后持久显示）──
    if analysis_done and st.session_state.get('_analysis_show_results'):
        saved = st.session_state.get('_last_analysis_result')
        if saved and saved.get('df') is not None:
            result_df = saved['df']
            result_csv = saved['csv_path']
            st.divider()
            st.subheader('分析结果预览')
            if 'polarity' in result_df.columns:
                render_polarity_stats(result_df, show_score=True)
                render_polarity_chart(result_df, height=200)
            else:
                st.caption(f'共 {len(result_df)} 条数据（无极性列）')

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
    tab1, tab2 = st.tabs(['从 processed 目录选择 (L1)', '上传新文件'])
    new_file_selected = False
    input_path = ''
    source_dir = PROCESSED_DIR

    with tab1:
        l1_files = []
        if os.path.exists(PROCESSED_DIR):
            l1_files = sorted([
                f for f in os.listdir(PROCESSED_DIR)
                if os.path.isfile(os.path.join(PROCESSED_DIR, f))
                and f.lower().endswith(('.csv', '.tsv', '.json', '.geojson'))
                and not f.lower().endswith('.geojson')
                and '_L2_result' not in f
                and '_L3_result' not in f
                and '_L4_result' not in f  # 仅 L1 文件，排除 L2/L3/L4 结果
            ])
        if l1_files:
            file_choice = st.selectbox('L1 治理后数据', l1_files, key='console_l1',
                                       help='仅 L1 文件，不含 _L2/L3/L4_result')
            input_path = os.path.join(PROCESSED_DIR, file_choice)
            st.caption(f'`{input_path}`')
            new_file_selected = True
            source_dir = PROCESSED_DIR
        else:
            st.info('无可用 L1 文件。请先生成 L1 模拟数据：`python SCRIPT/generate_l1_mock.py`')

    with tab2:
        uploaded = st.file_uploader('上传文件', type=['csv', 'tsv', 'json', 'geojson'])
        if uploaded:
            os.makedirs(PROCESSED_DIR, exist_ok=True)
            save_path = os.path.join(PROCESSED_DIR, uploaded.name)
            with open(save_path, 'wb') as f:
                f.write(uploaded.getbuffer())
            st.success('已保存')
            input_path = save_path
            new_file_selected = True

    if new_file_selected and input_path:
        st.divider()
        # 规范化输出名称：移除 _raw 后缀
        _default_name = os.path.splitext(os.path.basename(input_path))[0]
        _default_name = _default_name.replace('_raw', '').replace('_RAW', '')
        output_name = st.text_input('输出文件名', value=_default_name)
        # ── 文件变更检测：新文件重置分析状态 ──
        current_file_key = f'{input_path}|{output_name}'
        if st.session_state.get('_console_last_analyzed', '') != current_file_key:
            st.session_state['_console_analysis_done'] = False
            st.session_state['_console_last_result'] = None
        # ── 判断分析是否已完成 ──
        analysis_done = st.session_state.get('_console_analysis_done', False)
        btn_label = '[在地图上显示]' if analysis_done else '[开始分析]'
        if st.button(btn_label, type='primary', use_container_width=True):
            if analysis_done:
                # ── 模式 B: 加载到地图 ──
                result = st.session_state.get('_console_last_result')
                if result:
                    st.session_state['folder_key'] = list(FOLDER_OPTIONS.keys())[1]  # processed
                    st.session_state['file_choice'] = os.path.basename(result['csv_path'])
                    st.session_state['file_path'] = result['csv_path']
                    st.session_state['current_df'] = result['df']
                    st.session_state['current_file_choice'] = os.path.basename(result['csv_path'])
                    st.session_state['data_loaded'] = True
                    _register_layer(
                        name=os.path.basename(result['csv_path']),
                        file_path=result['csv_path'],
                        level='L2',
                        range_label='分析结果',
                        color='#48C9B0',
                    )
                    st.success(f'已加载 {result["n_points"]} 条数据到地图。切换至地图浏览器查看。')
            else:
                # ── 模式 A: 运行分析 ──
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
                        _register_layer(
                            name=os.path.basename(result['csv_path']),
                            file_path=result['csv_path'],
                            level='L2',
                            range_label='分析结果',
                            color='#48C9B0',
                        )
                        # ── 保存分析状态 ──
                        st.session_state['_console_analysis_done'] = True
                        st.session_state['_console_last_analyzed'] = current_file_key
                        st.session_state['_console_last_result'] = result
                        st.rerun()
                    else:
                        status.update(label='失败', state='error')
                        st.error(result['message'])


def _add_boundary_if_exists(deck):
    """如果存在边界文件，叠加到地图。"""
    try:
        geojson = get_boundary_geojson()
        if geojson:
            color = st.session_state.get('_boundary_color', '#d97d5c')
            weight = st.session_state.get('_boundary_weight', 15)
            add_boundary_layer(deck, geojson_data=geojson,
                             name='分析范围', color=color, weight=weight)
    except Exception:
        pass


@track("MOD_APP.F_001", track_args=False)
def show_console_page():
    """分析控制台主入口 — 委托给 4 个子函数处理。"""
    components.html(
        '<script>window.parent.document.title = "情绪地图v1.0：情绪控制台";</script>',
        height=0, width=0)
    st.title('情绪地图v1.0：情绪控制台')

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
@track("MOD_APP.F_002", track_args=False)
def main():
    # ── session_state 初始化（所有页面共享，必须在路由判断前）──
    for k, v in {
        '_map_style': 'carto_dark',
        'folder_key': '[DATA] processed（处理结果）',
        'file_choice': '', 'file_path': '',
        'current_df': None, 'current_map_meta': None,
        'current_file_choice': '', 'data_loaded': False,
        'layers': [],
        'governance_completed': False,
        'governance_last_stats': None,
        '_governance_done': False,
        '_governance_result': None,
        '_all_layers_hidden': False,
        '_boundary_weight': 15,
        '_boundary_color': '#d97d5c',
        '_boundary_color_name': '活力橙',
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── 强制清除：每次新鲜页面加载时不自动重载旧数据 ──
    if '_load_triggered' not in st.session_state:
        st.session_state['_load_triggered'] = False
        st.session_state['file_path'] = ''
        st.session_state['current_df'] = None
        st.session_state['data_loaded'] = False

    # ── 崩溃恢复：上次加载大文件导致页面异常，自动清除残留 ──
    if st.session_state.get('_data_crashed', False):
        st.session_state['file_path'] = ''
        st.session_state['current_df'] = None
        st.session_state['_data_crashed'] = False
        st.warning('上次加载数据量过大导致页面异常，已自动清除。请选择较小的数据文件。')

    # ── 路由分发 ──
    page = st.query_params.get('page', None)
    if page == 'console':
        show_console_page()
        return

    # ── 注入 Design Token CSS 变量（必须在其他 CSS 之前）──
    inject_theme_css()

    # ── CSS 注入（统一由 ui_components 管理）──
    inject_fullscreen_css()
    hud_button_style_css()

    # ── HUD ──
    fc = st.session_state.get('file_choice', '')
    btn_dis = st.session_state.get('current_df') is None

    if fc:
        render_title_bar(f'情绪地图 v1.0 "{fc}"')

    # 左侧数据管道列
    if st.button('[R]', help='[R] 分析范围 | 选择分析区域', key='rng'): show_range_dialog()
    if st.button('[D]', help='[D] 数据加载 | 选择数据文件 (CSV/GeoJSON)', key='d'): show_data_source_dialog()
    # [DISABLED] GV 按钮 — L0 数据治理功能已关闭，仅使用预生成的 L1 数据
    # if st.button('[GV]', help='[GV] 数据治理 | L0原始数据→L1城市情绪DATA', key='gv'): show_governance_dialog()
    if st.button('[A]', help='[A] 分析引擎 | 运行 L2/L3/L4 情绪分析管道', key='a'): show_analysis_dialog()

    # 底部地图控制栏
    if st.button('[*]', help='设置与调试', key='s'): show_settings_dialog()

    # ── 底图切换 ──
    current_style = st.session_state.get('_map_style', 'carto_dark')
    style_label = MAP_STYLE_LABELS.get(current_style, 'CartoDB 深色')
    if st.button('[Map]', help=f'底图: {style_label} | 点击切换底图', key='lbl'):
        show_basemap_dialog()
    if st.button('[LY]', help='[LY] 图层 | 切换地图图层显示', key='ly'): show_layer_dialog()
    # ── 热力图切换 ──
    heat_on = st.session_state.get('_heatmap_mode', False)
    heat_label = '[H]' if not heat_on else '[H*]'
    if st.button(heat_label, help='[H] 热力图 | 切换热力图/散点视图', key='heat_toggle'):
        st.session_state['_heatmap_mode'] = not heat_on
        st.rerun()

    # 右侧工具按钮
    if st.button('[OV]', help='数据概览', key='o', disabled=btn_dis): show_overview_dialog()
    if st.button('[TB]', help='数据表格', key='t', disabled=btn_dis): show_table_dialog()

    if not btn_dis:
        render_legend_overlay(mode='point')

    # ── 数据加载 + 地图 ──
    fp = st.session_state.get('file_path', '')
    if not fp or not os.path.exists(fp):
        center = st.session_state.get('_map_center', None)
        zoom = st.session_state.get('_map_zoom', None)
        _ms = st.session_state.get('_map_style', 'carto_dark')
        deck = create_base_map(center=center, zoom_start=zoom, map_style=_ms)
        if st.session_state.get('selected_ranges'):
            _add_boundary_if_exists(deck)
        st.pydeck_chart(deck, use_container_width=True, height=700)
        return

    # ── 数据加载安全守卫 ──
    file_size_mb = os.path.getsize(fp) / (1024 * 1024)
    if file_size_mb > LARGE_FILE_WARN_MB:
        st.warning(f'文件过大 ({file_size_mb:.0f} MB)，地图仅显示采样点。')

    # ── 加载数据（含异常保护，崩溃自动清除 session state）──
    try:
        with st.spinner('加载数据中...'):
            data = load_emotion_data(fp)
        if not data:
            st.error('无法加载数据，请检查文件格式或重新选择数据源')
            return

        df = data['df']
        total_rows = len(df)

        # ── 大数据采样（地图渲染用，完整数据保留在 data['df'] 中）──
        if total_rows > MAX_DISPLAY_POINTS:
            import random as _random
            sample_idx = _random.Random(42).sample(range(total_rows), MAX_DISPLAY_POINTS)
            df_display = df.iloc[sample_idx].reset_index(drop=True)
            st.info(f'数据共 {total_rows} 条，地图显示采样 {MAX_DISPLAY_POINTS} 条。完整数据请在数据表格中查看。')
        else:
            df_display = df

        st.session_state['current_df'] = df_display
        st.session_state['_total_rows'] = total_rows
        st.session_state['current_file_choice'] = fc
        st.session_state['data_loaded'] = True
        st.toast('[OK] 数据加载成功')
        st.session_state['_load_triggered'] = False

        with st.spinner('渲染地图中...'):
            center = st.session_state.get('_map_center', None)
            zoom = st.session_state.get('_map_zoom', None)
            _ms = st.session_state.get('_map_style', 'carto_dark')
            deck = create_base_map(data['lats'], data['lons'],
                                center=center, zoom_start=zoom, map_style=_ms)

            # 叠加范围边界
            _add_boundary_if_exists(deck)

            # ── 叠加可见图层 ──
            layers = st.session_state.get('layers', [])
            for lyr in layers:
                if not lyr.get('visible', True):
                    continue
                fp_layer = lyr.get('file_path', '')
                if not fp_layer or not os.path.exists(fp_layer):
                    continue
                # 跳过当前已加载的主数据（避免重复渲染）
                if fp_layer == fp:
                    continue
                layer_data = load_emotion_data(fp_layer)
                if layer_data:
                    add_point_layer(deck, layer_data['lats'], layer_data['lons'],
                                   layer_data['scores'],
                                   props_list=layer_data['df'].to_dict('records'))

            # ── 渲染主数据层（受 _all_layers_hidden / _heatmap_mode 控制）──
            if not st.session_state.get('_all_layers_hidden', False):
                if st.session_state.get('_heatmap_mode', False):
                    # 热力图模式
                    add_heatmap_layer(deck, data['lats'], data['lons'],
                                     scores=data['scores'],
                                     radius=30, intensity=0.6, opacity=0.75,
                                     max_points=MAX_DISPLAY_POINTS)
                else:
                    # 散点模式
                    geo = data.get('geo_data')
                    if geo:
                        add_point_layer(deck, data['lats'], data['lons'], data['scores'],
                                       props_list=geo['features'])
                    else:
                        add_point_layer(deck, data['lats'], data['lons'], data['scores'],
                                       props_list=df_display.to_dict('records'))
            else:
                trace_log("MOD_APP.D_013", detail='main data layer hidden by _all_layers_hidden')

        # ── 数据摘要浮层（左上角）──
        n = len(df_display)
        ranges = st.session_state.get('selected_ranges', [])
        area_label = ranges[0] if ranges else ''
        range_label = f'共 {len(ranges)} 区' if len(ranges) > 1 else ''
        date_label = ''
        m_date = _re.search(r'(\d{8})', fc)
        if m_date:
            date_label = m_date.group(1)
        render_data_summary_overlay(n=n, area_label=area_label,
                                     range_label=range_label, date_label=date_label)

        st.pydeck_chart(deck, use_container_width=True, height=700)

    except Exception as e:
        trace_error("MOD_APP.F_002", f'主流程数据加载异常: {str(e)[:200]}')
        st.session_state['_data_crashed'] = True
        st.session_state['file_path'] = ''
        st.session_state['current_df'] = None
        st.error(f'加载失败: {e}。数据已清除，请重新选择文件。')
        st.rerun()

# ── 追踪 ID 注册表 ──
register_track_id("MOD_APP.F_001", "分析控制台子页面（?page=console）")
register_track_id("MOD_APP.F_002", "主应用入口（地图浏览器 + 路由分发）")
register_track_id("MOD_APP.F_003", "数据治理弹窗（L0→L1 治理管道）")
register_track_id("MOD_APP.F_004", "注册/更新图层到 session_state")
register_track_id("MOD_APP.F_005", "数据源选择弹窗")
register_track_id("MOD_APP.F_006", "数据概览弹窗")
register_track_id("MOD_APP.F_007", "数据表格弹窗")
register_track_id("MOD_APP.F_008", "设置与调试弹窗")
register_track_id("MOD_APP.F_009", "分析范围选择弹窗")
register_track_id("MOD_APP.F_010", "图层控制弹窗")
register_track_id("MOD_APP.F_011", "情绪分析弹窗")
register_track_id("MOD_APP.D_010", "图层控制：单个图层圆点点击切换 visible")
register_track_id("MOD_APP.D_011", "图层控制：[全部打开] 批量显示所有图层")
register_track_id("MOD_APP.D_012", "图层控制：[全部关闭] 批量隐藏所有图层")
register_track_id("MOD_APP.D_013", "主数据点层：_all_layers_hidden 隐藏主数据")


if __name__ == '__main__':
    main()
