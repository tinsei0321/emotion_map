"""
情绪地图 v1.0 — 弹窗对话框模块
══════════════════════════════════════════════════════════════
从 app_main.py 拆分出来，包含所有 @st.dialog 弹窗函数。

弹窗清单:
  [DATA] 数据源    — show_data_source_dialog()
  [OV]   数据概览  — show_overview_dialog()
  [TB]   数据表格  — show_table_dialog()
  [Export] 导出   — show_export_dialog()
  [*]    设置     — show_settings_dialog()
  [RNG]  分析范围  — show_range_dialog() + helpers
  [GV]   数据治理  — show_governance_dialog()
  [Map]  底图切换  — show_basemap_dialog()
  [LY]   图层控制  — show_layer_dialog()
  [ANA]  情绪分析  — show_analysis_dialog()
"""
import os
from collections import Counter
import streamlit as st
import pandas as pd
import altair as alt

from core.config import (
    FOLDER_OPTIONS, DEFAULT_CENTER, DEFAULT_ZOOM, RAW_DIR, PROCESSED_DIR,
    MAX_DISPLAY_POINTS, MAX_TABLE_ROWS, LARGE_FILE_WARN_MB,
    BOUNDARY_SHP,
    UPLOAD_MAX_FILE_SIZE_MB, UPLOAD_MAX_GEOJSON_VERTICES,
    UPLOAD_MAX_SHAPEFILE_FEATURES, UPLOAD_SIMPLIFY_TOLERANCE,
    UPLOAD_PARSE_TIMEOUT_SEC,
    DEFAULT_BOUNDARY_STYLE, LAYER_PALETTE,
)
from core.export import export_to_csv
from core.map_engine import (
    MAP_STYLE_LABELS, MAP_STYLE_PREVIEW_COLORS,
)
from core.data_loader import load_emotion_data
from core.range_selector import (
    load_boundaries, get_available_ranges, filter_by_range,
    save_uploaded_file, get_active_boundary_path, list_boundary_files,
    get_boundary_geojson, DEFAULT_RANGE, get_boundary_crs_info,
    validate_upload_safety,
)
from core.ui_components import (
    render_polarity_stats, render_polarity_chart,
)
from SCRIPT.emotion_analysis_v1 import (
    create_analyzer, run_pipeline, run_analysis_task, safe_print,
)
from SCRIPT.data_governance import (
    step1_load_and_transform,
    step4_run_l2_analysis,
)
from SCRIPT.relevance_filter import keyword_prefilter, _build_text_for_classification
from core.tracker import track, TrackContext, trace_log, trace_error, trace_warn, register_track_id
from core.utils import safe_print
from core.layer_registry import register_layer


# ═══════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════

def _guess_level(filename: str) -> str:
    """从文件名推断数据层级。"""
    if '_L2_' in filename or 'L2_result' in filename:
        return 'L2'
    if '_L1_' in filename or 'L1_result' in filename:
        return 'L1'
    if '_L0_' in filename or 'raw' in filename.lower():
        return 'L0'
    return 'L1'


def _panel_coord_dup_analysis(df_or_gdf, geom_col=None):
    """坐标重复度分析面板。"""
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
    """数据源选择弹窗。"""
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

    with st.expander('分级渲染说明', expanded=False):
        st.markdown(f'''
        | 数据量 | 渲染模式 | 点样式 |
        |--------|----------|--------|
        | < 5k | S·标准 | 100m 半径 |
        | 5k–20k | M·密集 | 60m 半径 |
        | 20k–50k | L·紧凑 | 30m 微点 |
        | 50k–100k | XL·热力 | 自动切热力图 |
        | > 100k | XXL·抽样 | 分层抽样+热力图 |
        > 文件限制: {UPLOAD_MAX_FILE_SIZE_MB} MB / 最多 {MAX_DISPLAY_POINTS:,} 点
        ''')

    if file_size > LARGE_FILE_WARN_MB:
        st.warning(f'文件较大 ({file_size:.0f} MB)，地图将自动采样显示。')
    if st.button('[确认加载]', use_container_width=True, type='primary'):
        full_path = os.path.join(folder_path, file_choice)
        st.session_state['folder_key'] = '[DATA] processed（处理结果）'
        st.session_state['file_choice'] = file_choice
        st.session_state['file_path'] = full_path
        st.session_state['_load_triggered'] = True
        st.session_state['_all_layers_hidden'] = False
        register_layer(
            name=file_choice, file_path=full_path,
            level=_guess_level(file_choice), kind='data', color='#48C9B0')
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
# 弹窗：Export 导出
# ═══════════════════════════════════════════════════════════

@track("MOD_APP.F_021", track_args=False)
@st.dialog('[Export] 导出数据', width='small')
def show_export_dialog():
    from core.export import get_export_preview, export_boundaries_geojson
    df = st.session_state.get('current_df')
    poly_layers = st.session_state.get('polygon_layers', [])
    preview = get_export_preview(df, poly_layers)

    lines = []
    if preview['n_points']:
        lines.append(f'情绪数据点: {preview["n_points"]:,} 条')
    if preview['n_layers']:
        lines.append(f'边界图层: {preview["n_layers"]} 个 ({preview["n_features"]} 个要素)')
    if lines:
        st.caption(' | '.join(lines))
    else:
        st.caption('暂无数据可导出')

    fmt = st.radio('导出格式', ['CSV (情绪数据)', 'GeoJSON (情绪点)', 'GeoJSON (边界)'],
                   disabled=not df and not poly_layers)

    data, fname, mime = None, '', ''
    with TrackContext("MOD_APP.D_023", action="export", format=fmt):
        if 'CSV' in fmt and df is not None:
            data = df.to_csv(index=False).encode('utf-8')
            fname = 'emotion_data_export.csv'
            mime = 'text/csv'
        elif '情绪点' in fmt and df is not None:
            from core.export import export_to_geojson
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix='.geojson', delete=False)
            try:
                export_to_geojson(df, tmp.name)
                tmp.close()
                with open(tmp.name, 'rb') as f:
                    data = f.read()
                os.unlink(tmp.name)
            except Exception:
                data = None
            fname = 'emotion_points_export.geojson'
            mime = 'application/geo+json'
        elif '边界' in fmt and poly_layers:
            data = export_boundaries_geojson(poly_layers)
            fname = 'boundary_layers_export.geojson'
            mime = 'application/geo+json'

    if data:
        st.download_button('[下载] ' + fname, data=data,
                           file_name=fname, mime=mime,
                           use_container_width=True)
    else:
        st.caption('请先加载数据或边界图层')


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
    from apps.app_main import DEBUG_MODE
    st.caption(f'DEBUG_MODE = {DEBUG_MODE}')


# ═══════════════════════════════════════════════════════════
# 范围选择 — 辅助函数
# ═══════════════════════════════════════════════════════════

_COLOR_PRESETS_LIST = [
    ("活力橙",  [255, 140, 0]),
    ("青蓝",    [0, 200, 255]),
    ("警示红",  [255, 80, 80]),
    ("自然绿",  [80, 255, 120]),
    ("亮黄",    [255, 220, 0]),
    ("紫罗兰",  [180, 130, 255]),
    ("粉红",    [255, 160, 180]),
    ("蓝绿",    [100, 220, 200]),
]


@track("MOD_APP.F_017", track_args=False)
def _get_default_style(index: int) -> dict:
    """获取第 index 个图层的默认样式。"""
    color = DEFAULT_BOUNDARY_STYLE["line_color"][:]
    fill_c = DEFAULT_BOUNDARY_STYLE["fill_color"][:]

    if index < len(LAYER_PALETTE):
        color = LAYER_PALETTE[index][:]
        fill_c = LAYER_PALETTE[index] + [80]
    else:
        import colorsys
        hue = (index * 0.618033988749895) % 1.0
        rgb_01 = colorsys.hsv_to_rgb(hue, 0.7, 1.0)
        color = [int(c * 255) for c in rgb_01]
        fill_c = color + [80]

    return {
        "line_color": color,
        "line_width": DEFAULT_BOUNDARY_STYLE["line_width"],
        "fill": DEFAULT_BOUNDARY_STYLE["fill"],
        "fill_color": fill_c,
        "fill_opacity": DEFAULT_BOUNDARY_STYLE["fill_opacity"],
    }


@track("MOD_APP.F_018", track_args=False)
def _parse_vector_file(uploaded_file) -> dict | None:
    """解析上传的矢量文件为 GeoJSON dict。"""
    import json
    with TrackContext("MOD_APP.D_020", action="parse_vector", file_name=uploaded_file.name):
        try:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            if file_size_mb > UPLOAD_MAX_FILE_SIZE_MB * 2:
                st.error(f"[ERR] 文件过大 ({file_size_mb:.1f} MB > {UPLOAD_MAX_FILE_SIZE_MB * 2} MB)")
                return None
            content = uploaded_file.read()
            try:
                geojson = json.loads(content.decode("utf-8"))
                if "type" in geojson and geojson["type"] in ("FeatureCollection", "Feature"):
                    return geojson
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            if uploaded_file.name.lower().endswith(('.gpkg', '.kml', '.kmz')):
                import tempfile, geopandas as gpd
                suffix = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                try:
                    gdf = gpd.read_file(tmp_path, rows=UPLOAD_MAX_SHAPEFILE_FEATURES + 1)
                    if len(gdf) > UPLOAD_MAX_SHAPEFILE_FEATURES:
                        st.warning(f"[WARN] 要素数过多，仅加载前 {UPLOAD_MAX_SHAPEFILE_FEATURES} 个")
                        gdf = gdf.head(UPLOAD_MAX_SHAPEFILE_FEATURES)
                    if gdf.crs and gdf.crs.to_epsg() != 4326:
                        gdf = gdf.to_crs(epsg=4326)
                    return json.loads(gdf[['geometry']].to_json())
                finally:
                    try: os.unlink(tmp_path)
                    except Exception: pass
            st.error(f"[ERR] 无法识别文件格式: {uploaded_file.name}")
            return None
        except Exception as e:
            trace_error("MOD_APP.D_020", f"解析异常: {e}")
            st.error(f"[ERR] 文件解析失败: {e}")
            return None


def _load_shp_from_dir(dir_path: str) -> dict | None:
    """从包含 .shp/.shx/.dbf 的目录中加载 Shapefile。"""
    import json
    shp_path = None
    for f in os.listdir(dir_path):
        if f.lower().endswith('.shp'):
            shp_path = os.path.join(dir_path, f)
            break
    if not shp_path:
        return None
    try:
        import geopandas as gpd
        gdf = gpd.read_file(shp_path, rows=UPLOAD_MAX_SHAPEFILE_FEATURES + 1)
        if len(gdf) > UPLOAD_MAX_SHAPEFILE_FEATURES:
            st.warning(f"[WARN] 要素数过多，仅加载前 {UPLOAD_MAX_SHAPEFILE_FEATURES} 个")
            gdf = gdf.head(UPLOAD_MAX_SHAPEFILE_FEATURES)
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        return json.loads(gdf[['geometry']].to_json())
    except Exception as e:
        trace_error("MOD_APP.D_020", f"Shapefile加载失败: {e}")
        st.error(f"[ERR] Shapefile 加载失败: {e}")
        return None


@track("MOD_APP.F_019", track_args=False)
def _render_layer_row(layer: dict, idx: int):
    """渲染单个图层的横条控件。"""
    style = layer.get("style", _get_default_style(idx))
    color = style.get("line_color", [255, 140, 0])
    color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

    with st.container():
        st.markdown(f"""
        <style>
        .layer-row-{idx} {{
            display: flex; align-items: center; gap: 0.5rem;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-left: 4px solid {color_hex};
            border-radius: 8px; padding: 0.6rem 0.8rem; margin-bottom: 0.4rem;
        }}
        </style>
        """, unsafe_allow_html=True)

        col_name, col_switch, col_style_btn, col_remove = st.columns([3, 1, 1, 0.6])
        with col_name:
            st.markdown(
                f'<span style="color:{color_hex};font-weight:600;">{layer["name"]}</span>',
                unsafe_allow_html=True)
        with col_switch:
            visible = st.toggle(f"##vis_{idx}", value=layer.get("visible", True),
                              label_visibility="collapsed", key=f"vis_toggle_{idx}")
            if visible != layer.get("visible", True):
                layer["visible"] = visible
        with col_style_btn:
            style_key = f"show_style_{idx}"
            if style_key not in st.session_state:
                st.session_state[style_key] = False
            btn_label = "收起样式" if st.session_state[style_key] else "样式"
            if st.button(btn_label, key=f"style_btn_{idx}", use_container_width=True):
                st.session_state[style_key] = not st.session_state[style_key]
        with col_remove:
            if st.button("X", key=f"remove_{idx}", use_container_width=True):
                st.session_state.polygon_layers.pop(idx)
                st.rerun()

        if st.session_state.get(style_key, False):
            _render_style_editor(layer, style, idx)


@track("MOD_APP.F_020", track_args=False)
def _render_style_editor(layer: dict, style: dict, idx: int):
    """紧凑样式编辑：线宽 + 颜色选择。"""
    cur_color = style.get("line_color", [255, 140, 0])
    default_name = "活力橙"
    for name, rgb in _COLOR_PRESETS_LIST:
        if rgb == list(cur_color[:3]):
            default_name = name
            break

    with st.container():
        st.markdown(f"""
        <style>
        .style-panel-{idx} {{
            background: var(--bg-card, #16213e);
            border: 1px solid var(--border, #2a2a4a);
            border-radius: 6px; padding: 0.5rem 0.75rem;
            margin: 0.25rem 0 0.4rem 0.8rem;
        }}
        </style>
        <div class="style-panel-{idx}">""", unsafe_allow_html=True)

        line_width = st.slider("线宽", 1, 30, style.get("line_width", 20),
                              key=f"linewidth_{idx}", step=1)
        names = [n for n, _ in _COLOR_PRESETS_LIST]
        default_idx = names.index(default_name) if default_name in names else 0
        chosen = st.selectbox("颜色", names, index=default_idx, key=f"fillcolor_{idx}")
        new_rgb = dict(_COLOR_PRESETS_LIST).get(chosen, [255, 140, 0])
        layer["style"] = {
            "line_color": list(new_rgb), "line_width": line_width,
            "fill": False, "fill_color": list(new_rgb) + [80], "fill_opacity": 0.3,
        }
        st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# 弹窗：分析范围
# ═══════════════════════════════════════════════════════════

@track("MOD_APP.F_009", track_args=False)
@st.dialog('[RNG] 分析范围', width='medium')
def show_range_dialog():
    if st.session_state.get("_range_confirmed"):
        del st.session_state["_range_confirmed"]
        return

    if "polygon_layers" not in st.session_state:
        st.session_state.polygon_layers = []
    if "layer_history_names" not in st.session_state:
        st.session_state.layer_history_names = []

    col_up, col_btn = st.columns([4, 1])
    with col_up:
        uploaded_files = st.file_uploader(
            "选择矢量文件",
            type=["geojson", "json", "gpkg", "shp", "shx", "dbf", "prj", "cpg", "zip", "kml"],
            accept_multiple_files=True, key="scope_uploader",
            label_visibility="collapsed")
    with col_btn:
        load_disabled = not uploaded_files
        if st.button("加载", type="primary", use_container_width=True,
                     key="btn_load", disabled=load_disabled):
            import tempfile, shutil
            loaded_count = 0
            tmp_dir = tempfile.mkdtemp(prefix="em_map_")
            saved_shp_files, other_files = [], []

            for f in uploaded_files:
                file_size_mb = f.size / (1024 * 1024)
                if file_size_mb > UPLOAD_MAX_FILE_SIZE_MB:
                    st.error(f"[ERR] {f.name}: 过大 ({file_size_mb:.1f}MB > {UPLOAD_MAX_FILE_SIZE_MB}MB)")
                    continue
                ext = os.path.splitext(f.name)[1].lower()
                if ext in ('.shp', '.shx', '.dbf', '.prj', '.cpg'):
                    saved_path = os.path.join(tmp_dir, f.name)
                    with open(saved_path, 'wb') as fh: fh.write(f.read())
                    saved_shp_files.append(f)
                else:
                    other_files.append(f)

            if saved_shp_files:
                geojson = _load_shp_from_dir(tmp_dir)
                if geojson:
                    safety = validate_upload_safety(geojson, max_vertices=UPLOAD_MAX_GEOJSON_VERTICES,
                                                    max_features=UPLOAD_MAX_SHAPEFILE_FEATURES,
                                                    max_file_mb=UPLOAD_MAX_FILE_SIZE_MB,
                                                    simplify_tolerance=UPLOAD_SIMPLIFY_TOLERANCE)
                    if safety["safe"]:
                        for w in safety["warnings"]: st.warning(w)
                        geojson = safety["geojson"]
                        shp_name = os.path.splitext(saved_shp_files[0].name)[0]
                        if not any(l["name"] == shp_name for l in st.session_state.polygon_layers):
                            style = _get_default_style(len(st.session_state.polygon_layers))
                            st.session_state.polygon_layers.append({
                                "name": shp_name, "geojson": geojson,
                                "visible": True, "style": style})
                            if shp_name not in st.session_state.layer_history_names:
                                st.session_state.layer_history_names.append(shp_name)
                            loaded_count += 1
                            st.toast(f"[OK] {shp_name}")
                    else:
                        st.error(safety["error"])

            for f in other_files:
                geojson = _parse_vector_file(f)
                if geojson is None: continue
                safety = validate_upload_safety(geojson, file_size_mb=f.size / (1024 * 1024),
                                                max_vertices=UPLOAD_MAX_GEOJSON_VERTICES,
                                                max_features=UPLOAD_MAX_SHAPEFILE_FEATURES,
                                                max_file_mb=UPLOAD_MAX_FILE_SIZE_MB,
                                                simplify_tolerance=UPLOAD_SIMPLIFY_TOLERANCE)
                if not safety["safe"]: st.error(safety["error"]); continue
                for w in safety["warnings"]: st.warning(w)
                geojson = safety["geojson"]
                name = os.path.splitext(f.name)[0].replace(".shp", "").replace(".SHP", "")
                if any(l["name"] == name for l in st.session_state.polygon_layers):
                    st.info(f"[INFO] {name} 已存在"); continue
                style = _get_default_style(len(st.session_state.polygon_layers))
                st.session_state.polygon_layers.append({
                    "name": name, "geojson": geojson, "visible": True, "style": style})
                if name not in st.session_state.layer_history_names:
                    st.session_state.layer_history_names.append(name)
                loaded_count += 1
                st.toast(f"[OK] {name}")

            try: shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception: pass
            if loaded_count > 0:
                st.success(f"已加载 {loaded_count} 个范围图层")

    if st.session_state.polygon_layers:
        st.caption(f"已加载 {len(st.session_state.polygon_layers)} 个图层")
        for idx, layer in enumerate(st.session_state.polygon_layers):
            _render_layer_row(layer, idx)
    else:
        st.caption("上传文件后点击「加载」")

    if st.session_state.layer_history_names:
        with st.expander("历史范围"):
            st.caption("  |  ".join(st.session_state.layer_history_names))

    visible_layers = [l for l in st.session_state.polygon_layers if l.get("visible", True)]
    st.divider()
    col_ok, col_clr, _ = st.columns([1.5, 1, 3])
    with col_ok:
        if st.button("确认范围", type="primary", use_container_width=True,
                     disabled=not visible_layers):
            st.session_state.selected_ranges = [l["name"] for l in visible_layers]
            st.session_state.analysis_layers = visible_layers
            st.session_state._range_confirmed = True
            st.session_state['_toast'] = f'[OK] {len(visible_layers)} 个范围已确认'
            st.rerun()
    with col_clr:
        if st.button("清空", use_container_width=True, key="clear_all"):
            st.session_state.polygon_layers.clear()
            st.session_state.selected_ranges = []
            st.session_state.analysis_layers = []
            st.session_state['_toast'] = '[OK] 范围已清空'
            st.rerun()


# ═══════════════════════════════════════════════════════════
# 弹窗：数据治理
# ═══════════════════════════════════════════════════════════

@track("MOD_APP.F_003", track_args=False)
@st.dialog('[GV] 数据治理', width='large')
def show_governance_dialog():
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

    with st.expander('[步骤说明] 治理管道详情 (v1.0 关键词模式)'):
        st.markdown(
            '1. 坐标转换 GCJ-02 -> WGS84 -> CGCS2000 EPSG:4546\n'
            '2. 范围过滤 (规划边界 Polygon point-in-polygon)\n'
            '3. 相关性筛选 (关键词正负信号评分)\n'
            '4. 数据脱敏 + 导出 L1 CSV\n\n'
            '[INFO] v2.0 LLM 批量分类模式（更精准）请通过 CLI 运行:\n'
            '`python SCRIPT/data_governance.py`')

    if st.button('[开始数据治理]', type='primary', use_container_width=True):
        with st.status('治理中...', expanded=True) as status:
            progress = st.progress(0, text='准备...')
            status.update(label='[1/4] 坐标转换...')
            progress.progress(0.25, text='GCJ-02 -> WGS84 -> CGCS2000')
            df = step1_load_and_transform(input_path)
            input_n = len(df)

            status.update(label='[2/4] 范围过滤...')
            progress.progress(0.5, text='Point-in-Polygon')
            boundary_path = get_active_boundary_path()
            if not boundary_path and os.path.exists(BOUNDARY_SHP):
                boundary_path = BOUNDARY_SHP
            if boundary_path and os.path.exists(boundary_path):
                try:
                    ranges = load_boundaries(boundary_path)
                    gdf_filtered = filter_by_range(df, 'lon', 'lat', ranges, None)
                    df_filtered = pd.DataFrame(gdf_filtered) if len(gdf_filtered) > 0 else df.iloc[:0]
                except Exception as _e:
                    safe_print(f'[WARN] 范围过滤失败: {_e}，跳过')
                    df_filtered = df
            else:
                safe_print('[WARN] 无边界文件，跳过范围过滤')
                df_filtered = df

            status.update(label='[3/4] 相关性筛选...')
            progress.progress(0.75, text='关键词粗筛')
            df_filtered['_kw_pass'] = df_filtered.apply(
                lambda row: keyword_prefilter(_build_text_for_classification(row)) == 'pass',
                axis=1)
            df_relevant = df_filtered[df_filtered['_kw_pass']].copy()
            df_relevant['relevance'] = 'relevant'
            df_relevant['filter_layer'] = 'keyword'
            df_relevant.drop(columns=['_kw_pass'], inplace=True, errors='ignore')

            status.update(label='[4/4] 脱敏+导出 L1...')
            progress.progress(0.9, text='导出 L1 CSV')
            if 'comments' in df_relevant.columns:
                df_relevant['comments'] = ''
            output_name = os.path.splitext(file_choice)[0].replace('_raw', '')
            output_name = f'{output_name}_规划范围'
            l1_path = os.path.join(PROCESSED_DIR, f'{output_name}_L1_result_csv.csv')
            export_to_csv(df_relevant, l1_path)

            status.update(label=f'[OK] L1 治理完成: {len(df_relevant)} 条', state='complete')
            progress.progress(1.0, text=f'L1: {len(df_relevant)} 条 ({input_n} -> {len(df_relevant)})')

            st.session_state['_governance_done'] = True
            st.session_state['_governance_result'] = {
                'input_n': input_n, 'l1_n': len(df_relevant),
                'l1_path': l1_path, 'output_name': output_name}
            st.session_state['governance_completed'] = True
            st.session_state['governance_last_stats'] = {
                'input_file': file_choice, 'input_n': input_n,
                'output_n': len(df_relevant), 'relevant_n': len(df_relevant),
                'irrelevant_n': input_n - len(df_relevant),
                'time_elapsed': '—', 'output_path': l1_path}

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
                    register_layer(name=os.path.basename(r['l1_path']),
                                 file_path=r['l1_path'], level='L1', kind='data', color='#48C9B0')
                    st.rerun()
            with col_l2:
                if st.button('[运行 L2 情绪分析]', use_container_width=True):
                    with st.status('L2 分析中...', expanded=True) as l2_status:
                        l2_result = step4_run_l2_analysis(r['l1_path'], r['output_name'])
                        if l2_result['success']:
                            l2_status.update(label=f'[OK] L2 完成: {l2_result["n_points"]} 条', state='complete')
                            st.session_state['folder_key'] = list(FOLDER_OPTIONS.keys())[1]
                            st.session_state['file_choice'] = os.path.basename(l2_result['csv_path'])
                            st.session_state['file_path'] = l2_result['csv_path']
                            st.session_state['current_df'] = l2_result['df']
                            st.session_state['data_loaded'] = True
                            register_layer(name=os.path.basename(l2_result['csv_path']),
                                         file_path=l2_result['csv_path'], level='L2', kind='data', color='#48C9B0')
                            st.rerun()
                        else:
                            l2_status.update(label='[ERR] L2 失败', state='error')
                            st.error(l2_result['message'])


# ═══════════════════════════════════════════════════════════
# 弹窗：底图切换
# ═══════════════════════════════════════════════════════════

@track("MOD_APP.F_010", track_args=False)
@st.dialog('[Map] 底图切换', width='small')
def show_basemap_dialog():
    current = st.session_state.get('_map_style', 'carto_standard')
    st.caption('点击底图样式即刻切换，地图自动刷新')
    options = list(MAP_STYLE_LABELS.keys())

    swatch_parts = []
    for key in options:
        color = MAP_STYLE_PREVIEW_COLORS.get(key, 'var(--color-neutral-300)')
        is_active = (key == current)
        border = 'var(--color-brand-primary)' if is_active else 'var(--color-functional-border-light)'
        shadow = 'var(--shadow-glow)' if is_active else 'none'
        swatch_parts.append(
            f'<span style="display:inline-block;width:44px;height:22px;'
            f'border-radius:var(--radius-sm);background:{color};'
            f'border:2px solid {border};box-shadow:{shadow};margin-right:6px;'
            f'transition:border-color var(--effect-transition-fast);"'
            f'title="{MAP_STYLE_LABELS.get(key, key)}"></span>')

    st.markdown(f'<div style="display:flex;align-items:center;padding:2px 0 12px 0;">'
                f'{"".join(swatch_parts)}</div>', unsafe_allow_html=True)

    choice = st.radio('底图样式', options=options,
                      format_func=lambda k: MAP_STYLE_LABELS.get(k, k),
                      index=options.index(current) if current in options else 0,
                      label_visibility='collapsed')
    if choice != current:
        st.session_state['_map_style'] = choice
        st.session_state['_toast'] = f'[OK] {MAP_STYLE_LABELS.get(choice, choice)}'
        st.rerun()


# ═══════════════════════════════════════════════════════════
# 弹窗：图层控制
# ═══════════════════════════════════════════════════════════

@track("MOD_APP.F_013", track_args=False)
@st.dialog('[LY] 图层控制', width='small')
def show_layer_dialog():
    layers = st.session_state.get('layers', [])
    if not layers:
        st.info('暂无注册图层。\n\n通过 [D] 加载数据后，图层自动注册到此列表。')
        return

    st.caption(f'共 {len(layers)} 个图层')
    st.divider()

    for i, lyr in enumerate(layers):
        level = lyr.get('level', '')
        kind = lyr.get('kind', 'data')
        kind_tag = 'RNG' if kind == 'range' else level
        col_dot, col_name, col_toggle = st.columns([0.3, 3.2, 1.0])
        with col_dot:
            st.markdown(f'<span style="color:{lyr["color"]};font-size:1.2rem;">●</span>',
                       unsafe_allow_html=True)
        with col_name:
            st.caption(f'**[{kind_tag}]** {lyr["name"]}')
        with col_toggle:
            current_val = lyr.get('visible', True)
            new_val = st.toggle('', value=current_val, key=f'lyr_tgl_{i}',
                              label_visibility='collapsed')
            if new_val != current_val:
                layers[i]['visible'] = new_val
                st.session_state['layers'] = layers
                if lyr['file_path'] == st.session_state.get('file_path', ''):
                    st.session_state['_all_layers_hidden'] = not new_val

    st.divider()
    if st.button('[确定]', key='lyr_confirm', type='primary', use_container_width=True):
        st.session_state['_toast'] = '[OK] 图层状态已更新'
        st.rerun()
    st.caption('— 批量操作 —')
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button('[全部打开]', use_container_width=True, key='lyr_all_on'):
            for lyr in layers: lyr['visible'] = True
            st.session_state['layers'] = layers
            st.session_state['_all_layers_hidden'] = False
            st.session_state['_toast'] = '[OK] 全部图层已显示'
            st.rerun()
    with bc2:
        if st.button('[全部关闭]', use_container_width=True, key='lyr_all_off'):
            for lyr in layers: lyr['visible'] = False
            st.session_state['layers'] = layers
            st.session_state['_all_layers_hidden'] = True
            st.session_state['_toast'] = '[OK] 全部图层已隐藏'
            st.rerun()


# ═══════════════════════════════════════════════════════════
# 弹窗：运行情绪分析
# ═══════════════════════════════════════════════════════════

@track("MOD_APP.F_011", track_args=False)
@st.dialog('[ANA] 运行情绪分析', width='large')
def show_analysis_dialog():
    st.markdown('选择已完成治理的 L1 数据文件并运行情绪分析引擎，结果自动加载到地图。')

    l1_files = []
    if os.path.exists(PROCESSED_DIR):
        l1_files = sorted([f for f in os.listdir(PROCESSED_DIR)
                          if os.path.isfile(os.path.join(PROCESSED_DIR, f))
                          and f.lower().endswith(('.csv', '.tsv', '.json', '.geojson'))
                          and not f.lower().endswith('.geojson')
                          and '_L2_result' not in f
                          and '_L3_result' not in f
                          and '_L4_result' not in f])

    if not l1_files:
        st.warning(f'`{PROCESSED_DIR}/` 中没有可分析的 L1 文件。')
        return

    source_dir = PROCESSED_DIR
    file_choice = st.selectbox('[FILE] 待分析数据文件', l1_files)
    st.caption(f'路径: `{os.path.join(source_dir, file_choice)}`')

    input_path = os.path.join(source_dir, file_choice)
    try:
        sample = pd.read_csv(input_path, nrows=1)
        has_l1_markers = ('relevance' in sample.columns or 'in_scope' in sample.columns)
        if not has_l1_markers:
            st.warning('[WARN] 所选文件缺少 L1 治理标记列')
        n_rows = len(pd.read_csv(input_path))
        if n_rows > 10000:
            st.info(f'文件包含 {n_rows:,} 条记录。分析可能需要较长时间。')
    except Exception as e:
        st.warning(f'无法预览文件: {e}')

    with st.expander('[L1 数据概览]', expanded=False):
        gov_result = st.session_state.get('_governance_result')
        if gov_result:
            c1, c2 = st.columns(2)
            c1.metric('最近 L1 输出', gov_result['l1_n'])
            c2.metric('输入', gov_result['input_n'])

    st.divider()

    engine_choice = st.radio(
        '[ENG] 分析引擎',
        ['L2 · SnowNLP粗粒度分析 (离线)',
         'L3 · LLM 细粒度语义解析 (需 API Key)',
         'L4 · 语料库 + LLM 多维归因处理 (需语料库 和 API Key)'])

    api_key = ''
    if 'LLM' in engine_choice:
        api_key = st.text_input('[KEY] API Key', type='password', placeholder='sk-...')

    st.divider()

    if st.session_state.get('_last_analyzed_file', '') != file_choice:
        st.session_state['_analysis_done'] = False
        st.session_state['_last_analyzed_file'] = ''
        st.session_state['_last_analysis_result'] = None
        st.session_state['_analysis_show_results'] = False

    analysis_done = st.session_state.get('_analysis_done', False) and \
                    st.session_state.get('_last_analyzed_file', '') == file_choice
    btn_label = '[在地图上显示]' if analysis_done else '[开始分析]'
    run_clicked = st.button(btn_label, type='primary', use_container_width=True)

    if run_clicked:
        if analysis_done:
            saved = st.session_state.get('_last_analysis_result')
            if saved:
                st.session_state['folder_key'] = list(FOLDER_OPTIONS.keys())[1]
                st.session_state['file_choice'] = os.path.basename(saved['csv_path'])
                st.session_state['file_path'] = saved['csv_path']
                st.session_state['current_df'] = saved['df']
                st.session_state['current_file_choice'] = os.path.basename(saved['csv_path'])
                st.session_state['data_loaded'] = True
                register_layer(name=os.path.basename(saved['csv_path']),
                             file_path=saved['csv_path'], level='L2',
                             range_label='分析结果', color='#48C9B0')
                st.success(f'已加载 {saved["n_points"]} 条数据到地图。关闭对话框查看。')
        else:
            engine_type = 'llm' if 'LLM' in engine_choice else 'snownlp'
            _input_path = os.path.join(source_dir, file_choice)
            _base_name = os.path.splitext(file_choice)[0].replace('_raw', '').replace('_RAW', '')
            file_size_mb = os.path.getsize(_input_path) / (1024 * 1024)

            progress_bar = st.progress(0, text='准备分析...')
            def update_progress(step, total, message):
                progress_bar.progress(step / total, text=message)

            with st.status('分析中...', expanded=True) as status:
                status.update(label=f'文件: {_base_name} ({file_size_mb:.0f} MB)')
                try:
                    result = run_analysis_task(
                        file_path=_input_path, engine_type=engine_type,
                        output_name=_base_name, api_key=api_key,
                        progress_callback=update_progress)
                    if result['success']:
                        progress_bar.progress(1.0, text=f'[OK] {result["n_points"]} 条完成')
                        status.update(label=f'[OK] 分析完成！{result["n_points"]} 条数据', state='complete')
                        st.session_state['_analysis_done'] = True
                        st.session_state['_last_analyzed_file'] = file_choice
                        st.session_state['_last_analysis_result'] = result
                        st.session_state['_analysis_show_results'] = True
                        st.session_state['folder_key'] = list(FOLDER_OPTIONS.keys())[1]
                        st.session_state['file_choice'] = os.path.basename(result['csv_path'])
                        st.session_state['file_path'] = result['csv_path']
                        st.session_state['current_df'] = result['df']
                        st.session_state['current_file_choice'] = os.path.basename(result['csv_path'])
                        st.session_state['data_loaded'] = True
                        register_layer(name=os.path.basename(result['csv_path']),
                                     file_path=result['csv_path'], level='L2',
                                     range_label='分析结果', color='#48C9B0')
                        st.rerun()
                    else:
                        progress_bar.progress(1.0, text='[WARN] 分析失败')
                        status.update(label='[WARN] 分析失败', state='error')
                        st.error(f'分析失败: {result["message"][:200]}')
                except Exception as e:
                    progress_bar.progress(1.0, text='[ERR] 分析失败')
                    status.update(label='[ERR] 分析出错', state='error')
                    st.error(f'分析失败: {str(e)[:200]}')
                    trace_error("MOD_APP.F_011", f'分析执行异常: {str(e)[:200]}')

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
                st.link_button('打开分析控制台查看详细报告',
                             url=f'/?page=console&file={result_csv.replace(chr(92), "/")}',
                             type='primary', use_container_width=True)


# ── 追踪 ID 注册表（从 app_main.py 迁移）──

def _register_dialog_track_ids():
    """注册所有弹窗相关的追踪 ID（在 app_main 启动时调用）。"""
    register_track_id("MOD_APP.F_003", "数据治理弹窗（L0→L1 治理管道）")
    register_track_id("MOD_APP.F_005", "数据源选择弹窗")
    register_track_id("MOD_APP.F_006", "数据概览弹窗")
    register_track_id("MOD_APP.F_007", "数据表格弹窗")
    register_track_id("MOD_APP.F_008", "设置与调试弹窗")
    register_track_id("MOD_APP.F_009", "分析范围选择弹窗")
    register_track_id("MOD_APP.F_010", "底图切换弹窗")
    register_track_id("MOD_APP.F_011", "情绪分析弹窗")
    register_track_id("MOD_APP.F_013", "图层控制弹窗（[LY]）")
    register_track_id("MOD_APP.F_017", "A功能：获取图层默认样式")
    register_track_id("MOD_APP.F_018", "A功能：解析上传矢量文件")
    register_track_id("MOD_APP.F_019", "A功能：渲染单图层横条控件")
    register_track_id("MOD_APP.F_020", "A功能：渲染样式编辑面板")
    register_track_id("MOD_APP.F_021", "Export 导出数据弹窗")
    register_track_id("MOD_APP.D_010", "图层控制：单图层toggle切换")
    register_track_id("MOD_APP.D_011", "图层控制：[全部打开]")
    register_track_id("MOD_APP.D_012", "图层控制：[全部关闭]")
    register_track_id("MOD_APP.D_020", "A功能：解析矢量文件决策点")
    register_track_id("MOD_APP.D_021", "A功能：安全阈值校验")
    register_track_id("MOD_APP.D_023", "Export对话框：导出格式选择")
