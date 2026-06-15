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
    UPLOAD_MAX_FILE_SIZE_MB, UPLOAD_MAX_GEOJSON_VERTICES,
    UPLOAD_MAX_SHAPEFILE_FEATURES, UPLOAD_SIMPLIFY_TOLERANCE,
    UPLOAD_PARSE_TIMEOUT_SEC,
    DEFAULT_BOUNDARY_STYLE, LAYER_PALETTE,
)
from core.export import export_to_csv
from core.map_engine import (
    create_base_map, add_point_layer, add_boundary_layer,
    add_heatmap_layer, add_multiple_boundary_layers,
    add_selection_marker,
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
    inject_fullscreen_css, hud_button_style_css,
    render_title_bar, render_legend_overlay,
    render_data_summary_overlay,
    render_polarity_stats, render_polarity_chart,
    inject_theme_css,
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
from apps.app_console import show_console_page

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

    # ── 限制提示 ──
    with st.expander('分级渲染说明', expanded=False):
        st.markdown(f'''
        | 数据量 | 渲染模式 | 点样式 |
        |--------|----------|--------|
        | < 5k | S·标准 | 100m 半径，情绪颜色清晰 |
        | 5k–20k | M·密集 | 60m 半径，半透明描边 |
        | 20k–50k | L·紧凑 | 30m 微点，无描边 |
        | 50k–100k | XL·热力 | 自动切换热力图 |
        | > 100k | XXL·抽样 | 分层抽样 + 热力图 |
        > 文件限制: {UPLOAD_MAX_FILE_SIZE_MB} MB / 最多 {MAX_DISPLAY_POINTS:,} 点同时渲染
        ''')

    if file_size > LARGE_FILE_WARN_MB:
        st.warning(f'文件较大 ({file_size:.0f} MB)，地图将自动采样显示。')
    if st.button('[确认加载]', use_container_width=True, type='primary'):
        st.session_state['folder_key'] = '[DATA] processed（处理结果）'
        st.session_state['file_choice'] = file_choice
        st.session_state['file_path'] = os.path.join(folder_path, file_choice)
        st.session_state['_load_triggered'] = True
        st.session_state['_all_layers_hidden'] = False
        register_layer(
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
@st.dialog('[TB] 数据表格', width='small')
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
# A 功能：分析范围设置（弹窗）
# ═══════════════════════════════════════════════════════════

# ── 辅助函数 ──

@track("MOD_APP.F_017", track_args=False)
def _get_default_style(index: int) -> dict:
    """获取第 index 个图层的默认样式。

    前 8 个使用 LAYER_PALETTE 色板自动差异化，
    超出则用 HSL 色相环均匀分布颜色。
    默认: 20px 线宽 + 不填充面。
    """
    color = DEFAULT_BOUNDARY_STYLE["line_color"][:]
    fill_c = DEFAULT_BOUNDARY_STYLE["fill_color"][:]

    if index < len(LAYER_PALETTE):
        color = LAYER_PALETTE[index][:]
        fill_c = LAYER_PALETTE[index] + [80]
    else:
        # HSL 色相均匀分布
        import colorsys
        hue = (index * 0.618033988749895) % 1.0  # 黄金角
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
    """解析上传的矢量文件为 GeoJSON dict。

    支持: .geojson / .json / .gpkg / .kml
    注意: .shp/.shx/.dbf 等多文件需由调用方先保存后用 _load_shp_from_dir() 加载
    """
    import json
    with TrackContext("MOD_APP.D_020", action="parse_vector", file_name=uploaded_file.name):
        try:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            if file_size_mb > UPLOAD_MAX_FILE_SIZE_MB * 2:
                st.error(f"[ERR] 文件过大 ({file_size_mb:.1f} MB > {UPLOAD_MAX_FILE_SIZE_MB * 2} MB)")
                return None

            content = uploaded_file.read()

            # 尝试 GeoJSON
            try:
                geojson = json.loads(content.decode("utf-8"))
                if "type" in geojson and geojson["type"] in ("FeatureCollection", "Feature"):
                    return geojson
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

            # .gpkg 或单文件矢量：通过 geopandas 加载
            if uploaded_file.name.lower().endswith(('.gpkg', '.kml', '.kmz')):
                import tempfile
                suffix = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                try:
                    import geopandas as gpd
                    gdf = gpd.read_file(tmp_path, rows=UPLOAD_MAX_SHAPEFILE_FEATURES + 1)
                    if len(gdf) > UPLOAD_MAX_SHAPEFILE_FEATURES:
                        st.warning(f"[WARN] 要素数过多，仅加载前 {UPLOAD_MAX_SHAPEFILE_FEATURES} 个")
                        gdf = gdf.head(UPLOAD_MAX_SHAPEFILE_FEATURES)
                    if gdf.crs and gdf.crs.to_epsg() != 4326:
                        gdf = gdf.to_crs(epsg=4326)
                    return json.loads(gdf[['geometry']].to_json())
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

            st.error(f"[ERR] 无法识别文件格式: {uploaded_file.name}")
            return None
        except Exception as e:
            trace_error("MOD_APP.D_020", f"解析异常: {e}")
            st.error(f"[ERR] 文件解析失败: {e}")
            return None


def _load_shp_from_dir(dir_path: str) -> dict | None:
    """从包含 .shp/.shx/.dbf 的目录中加载 Shapefile。

    用于处理 st.file_uploader 多文件上传后的 SHP 加载。
    """
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
        # 只用 geometry 列转 GeoJSON，避免 Timestamp 等类型序列化失败
        return json.loads(gdf[['geometry']].to_json())
    except Exception as e:
        trace_error("MOD_APP.D_020", f"Shapefile加载失败: {e}")
        st.error(f"[ERR] Shapefile 加载失败: {e}")
        return None


@track("MOD_APP.F_009", track_args=False)
@st.dialog('[RNG] 分析范围', width='medium')
def show_range_dialog():
    """A 功能弹窗：加载矢量范围 + 多图层管理 + 样式编辑 (Kepler 风格)。"""
    # ── 关闭控制：只有点击"确认范围"后才关闭 ──
    if st.session_state.get("_range_confirmed"):
        del st.session_state["_range_confirmed"]
        return

    # 初始化
    if "polygon_layers" not in st.session_state:
        st.session_state.polygon_layers = []
    if "layer_history_names" not in st.session_state:
        st.session_state.layer_history_names = []

    # ── 上传区 ──
    col_up, col_btn = st.columns([4, 1])
    with col_up:
        uploaded_files = st.file_uploader(
            "选择矢量文件",
            type=["geojson", "json", "gpkg", "shp", "shx", "dbf", "prj", "cpg", "zip", "kml"],
            accept_multiple_files=True,
            key="scope_uploader",
            help="GeoJSON / Shapefile (.shp+.shx+.dbf 多选 或 .zip) / KML",
            label_visibility="collapsed",
        )
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
                    with open(saved_path, 'wb') as fh:
                        fh.write(f.read())
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
                        for w in safety["warnings"]:
                            st.warning(w)
                        geojson = safety["geojson"]
                        shp_name = os.path.splitext(saved_shp_files[0].name)[0]
                        if not any(l["name"] == shp_name for l in st.session_state.polygon_layers):
                            style = _get_default_style(len(st.session_state.polygon_layers))
                            st.session_state.polygon_layers.append({
                                "name": shp_name, "geojson": geojson,
                                "visible": True, "style": style,
                            })
                            if shp_name not in st.session_state.layer_history_names:
                                st.session_state.layer_history_names.append(shp_name)
                            loaded_count += 1
                            st.toast(f"[OK] {shp_name}")
                    else:
                        st.error(safety["error"])

            for f in other_files:
                geojson = _parse_vector_file(f)
                if geojson is None:
                    continue
                safety = validate_upload_safety(geojson, file_size_mb=f.size / (1024 * 1024),
                                                max_vertices=UPLOAD_MAX_GEOJSON_VERTICES,
                                                max_features=UPLOAD_MAX_SHAPEFILE_FEATURES,
                                                max_file_mb=UPLOAD_MAX_FILE_SIZE_MB,
                                                simplify_tolerance=UPLOAD_SIMPLIFY_TOLERANCE)
                if not safety["safe"]:
                    st.error(safety["error"])
                    continue
                for w in safety["warnings"]:
                    st.warning(w)
                geojson = safety["geojson"]
                name = os.path.splitext(f.name)[0].replace(".shp", "").replace(".SHP", "")
                if any(l["name"] == name for l in st.session_state.polygon_layers):
                    st.info(f"[INFO] {name} 已存在")
                    continue
                style = _get_default_style(len(st.session_state.polygon_layers))
                st.session_state.polygon_layers.append({
                    "name": name, "geojson": geojson,
                    "visible": True, "style": style,
                })
                if name not in st.session_state.layer_history_names:
                    st.session_state.layer_history_names.append(name)
                loaded_count += 1
                st.toast(f"[OK] {name}")

            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass
            if loaded_count > 0:
                st.success(f"已加载 {loaded_count} 个范围图层")

    # ── 图层列表 ──
    if st.session_state.polygon_layers:
        st.caption(f"已加载 {len(st.session_state.polygon_layers)} 个图层")
        for idx, layer in enumerate(st.session_state.polygon_layers):
            _render_layer_row(layer, idx)
    else:
        st.caption("上传文件后点击「加载」")

    # ── 历史名称 ──
    if st.session_state.layer_history_names:
        with st.expander("历史范围"):
            names = "  |  ".join(st.session_state.layer_history_names)
            st.caption(names)

    # ── 底部操作栏 ──
    visible_layers = [l for l in st.session_state.polygon_layers if l.get("visible", True)]
    st.divider()
    col_ok, col_clr, _ = st.columns([1.5, 1, 3])
    with col_ok:
        if st.button("确认范围", type="primary", use_container_width=True,
                     disabled=not visible_layers):
            st.session_state.selected_ranges = [l["name"] for l in visible_layers]
            st.session_state.analysis_layers = visible_layers
            st.session_state._range_confirmed = True
            st.rerun()
    with col_clr:
        if st.button("清空", use_container_width=True, key="clear_all"):
            st.session_state.polygon_layers.clear()
            st.session_state.selected_ranges = []
            st.session_state.analysis_layers = []
            st.rerun()


@track("MOD_APP.F_019", track_args=False)
def _render_layer_row(layer: dict, idx: int):
    """渲染单个图层的横条控件：名称 + Switch + 样式按钮 + 移除。

    图层数据: {name, geojson, visible, style, file_name}
    """
    style = layer.get("style", _get_default_style(idx))
    color = style.get("line_color", [255, 140, 0])
    color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

    with st.container():
        # ── CSS class for layer row ──
        st.markdown(f"""
        <style>
        .layer-row-{idx} {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-left: 4px solid {color_hex};
            border-radius: 8px;
            padding: 0.6rem 0.8rem;
            margin-bottom: 0.4rem;
        }}
        </style>
        """, unsafe_allow_html=True)

        col_name, col_switch, col_style_btn, col_remove = st.columns([3, 1, 1, 0.6])

        with col_name:
            st.markdown(
                f'<span style="color:{color_hex};font-weight:600;">{layer["name"]}</span>',
                unsafe_allow_html=True
            )

        with col_switch:
            visible = st.toggle(
                f"##vis_{idx}",
                value=layer.get("visible", True),
                label_visibility="collapsed",
                key=f"vis_toggle_{idx}",
                help="显示/隐藏此图层",
            )
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
            if st.button("X", key=f"remove_{idx}", help=f"移除 {layer['name']}", use_container_width=True):
                st.session_state.polygon_layers.pop(idx)
                st.rerun()

        # ── 样式编辑面板（展开时显示）──
        if st.session_state.get(style_key, False):
            _render_style_editor(layer, style, idx)


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


@track("MOD_APP.F_020", track_args=False)
def _render_style_editor(layer: dict, style: dict, idx: int):
    """紧凑样式编辑：线宽 + 颜色选择 + 填充。"""
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
            border-radius: 6px;
            padding: 0.5rem 0.75rem;
            margin: 0.25rem 0 0.4rem 0.8rem;
        }}
        </style>
        <div class="style-panel-{idx}">""", unsafe_allow_html=True)

        # ── 线宽 ──
        line_width = st.slider(
            "线宽", 1, 30, style.get("line_width", 20),
            key=f"linewidth_{idx}", step=1
        )

        # ── 颜色 selectbox ──
        names = [n for n, _ in _COLOR_PRESETS_LIST]
        default_idx = names.index(default_name) if default_name in names else 0
        chosen = st.selectbox(
            "颜色", names, index=default_idx, key=f"fillcolor_{idx}"
        )

        new_rgb = dict(_COLOR_PRESETS_LIST).get(chosen, [255, 140, 0])

        layer["style"] = {
            "line_color": list(new_rgb),
            "line_width": line_width,
            "fill": False,
            "fill_color": list(new_rgb) + [80],
            "fill_opacity": 0.3,
        }

        st.markdown("</div>", unsafe_allow_html=True)


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
            # 脱敏：清空个人身份信息列
            if 'comments' in df_relevant.columns:
                df_relevant['comments'] = ''
            safe_print('[OK] 数据脱敏完成')
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
                    register_layer(
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
                            register_layer(
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


@track("MOD_APP.F_013", track_args=False)
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
                register_layer(
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
                        register_layer(
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
                    safe_print(f'[ERR] show_analysis_dialog 分析出错: {e}')
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



def _add_boundary_if_exists(deck):
    """叠加所有已确认的分析范围图层到地图。

    优先使用 polygon_layers（新 A 功能），
    回退到旧的 _boundary_color / _boundary_weight 方式（向后兼容）。
    """
    try:
        # 新方式：多图层
        layers = st.session_state.get("analysis_layers", [])
        if layers:
            add_multiple_boundary_layers(deck, layers)
            return

        # 旧方式：单一边界（向后兼容）
        geojson = get_boundary_geojson()
        if geojson:
            color = st.session_state.get('_boundary_color', '#d97d5c')
            weight = st.session_state.get('_boundary_weight', 15)
            add_boundary_layer(deck, geojson_data=geojson,
                             name='分析范围', color=color, weight=weight)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# 选中点详情卡片
# ═══════════════════════════════════════════════════════════
@track("MOD_APP.F_012", track_args=False)
def _render_selection_detail():
    """渲染地图点击选中点的详情卡片（地图上方）。"""
    # ── 检测 pydeck 选择事件 ──
    selection = st.session_state.get('selection')
    if not selection or not isinstance(selection, dict):
        return

    objects = selection.get('objects', {})
    if not objects or not isinstance(objects, dict):
        return

    # ── pydeck selection.objects 结构: {"ScatterplotLayer": [{...}]} ──
    point_data = None
    for layer_name, items in objects.items():
        if items and isinstance(items, list) and len(items) > 0:
            point_data = items[0]
            break

    if point_data is None:
        return

    tooltip_str = point_data.get('tooltip', '')
    lat = point_data.get('lat')
    lon = point_data.get('lon')

    if not tooltip_str and lat is None:
        return

    # ── 保存选中状态到 session ──
    with TrackContext("MOD_APP.D_022", action="selection_detected",
                      lat=lat, lon=lon):
        st.session_state['_selected_point'] = {
            'lat': lat,
            'lon': lon,
            'tooltip': tooltip_str,
        }

    # ── 渲染详情卡片 ──
    sel = st.session_state.get('_selected_point')
    if not sel:
        return

    st.divider()
    st.markdown('### [SEL] 选中点详情')

    # 金色轮廓提示
    st.markdown(
        '<span style="color:#FFD700;font-size:0.85rem;">'
        '金色圆环 = 选中的情绪点</span>',
        unsafe_allow_html=True)

    # 坐标
    if sel.get('lat') and sel.get('lon'):
        st.caption(f'坐标: {sel["lat"]:.6f}, {sel["lon"]:.6f}')

    # 解析 tooltip 字段逐行展示
    raw_tooltip = sel.get('tooltip', '')
    if raw_tooltip:
        st.divider()
        lines = raw_tooltip.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, _, val = line.partition(':')
                st.markdown(f'**{key.strip()}**: {val.strip()}')
            else:
                st.text(line)

    # ── 清除选中按钮 ──
    if st.button('[清除选中]', key='clear_selection', use_container_width=True):
        st.session_state.pop('_selected_point', None)
        st.session_state.pop('selection', None)
        st.rerun()


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════
@track("MOD_APP.F_002", track_args=False)
def main():
    # ── session_state 初始化（所有页面共享，必须在路由判断前）──
    for k, v in {
        '_map_style': 'carto_light',
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
    # ── Dialog 尺寸: TB表格 2/3 宽度居中 ──
    st.markdown("""
    <style>
    [data-testid="stDialog"] {max-width:66vw!important;margin:0 auto!important;}
    </style>""", unsafe_allow_html=True)

    # ── 覆盖 pydeck pickable 图层的 cursor: pointer ──
    # deck.gl 对 pickable 图层默认设 cursor: pointer（"小手"），
    # 这里恢复为默认箭头，仅拖拽时由 deck.gl 自动设 grabbing。
    st.markdown("""
    <style>
    #vg-tooltip-element,
    canvas[data-testid="stDeckGlJsonChart"] {
        cursor: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Kepler 风格 HUD ──
    # (CSS定位在 hud_button_style_css)
    # 左上角: [*]  右侧竖排: [R] [D] [A] [H]
    # 底部左下: [M] [OV] [TB] [LY]
    fc = st.session_state.get('file_choice', '')
    btn_dis = st.session_state.get('current_df') is None

    if fc:
        render_title_bar(f'情绪地图 v1.0 "{fc}"')

    # 左上角: 设置
    if st.button('[*]', help='设置与调试', key='s'): show_settings_dialog()

    # ── 右侧工具栏 (从上到下) ──
    if st.button('[R]', help='分析范围', key='rng'): show_range_dialog()
    if st.button('[D]', help='数据加载', key='d'): show_data_source_dialog()
    if st.button('[A]', help='分析引擎', key='a'): show_analysis_dialog()

    # 热力图切换
    heat_on = st.session_state.get('_heatmap_mode', False)
    heat_label = '[H]' if not heat_on else '[H*]'
    if st.button(heat_label, help='热力图', key='heat_toggle'):
        st.session_state['_heatmap_mode'] = not heat_on
        st.rerun()

    # ── 底部左下角 ──
    current_style = st.session_state.get('_map_style', 'carto_light')
    style_label = MAP_STYLE_LABELS.get(current_style, 'CartoDB')
    if st.button('[M]', help=f'底图: {style_label}', key='lbl'):
        show_basemap_dialog()
    if st.button('[OV]', help='数据概览', key='o', disabled=btn_dis): show_overview_dialog()
    if st.button('[TB]', help='数据表格', key='t', disabled=btn_dis): show_table_dialog()
    if st.button('[LY]', help='图层控制', key='ly'): show_layer_dialog()

    # ── 选中点详情卡片 ──
    _render_selection_detail()

    if not btn_dis:
        render_legend_overlay(mode='point')

    # ── 数据加载 + 地图 ──
    fp = st.session_state.get('file_path', '')
    if not fp or not os.path.exists(fp):
        center = st.session_state.get('_map_center', None)
        zoom = st.session_state.get('_map_zoom', None)
        _ms = st.session_state.get('_map_style', 'carto_light')
        deck = create_base_map(center=center, zoom_start=zoom, map_style=_ms)
        if st.session_state.get('selected_ranges'):
            _add_boundary_if_exists(deck)
        deck.tooltip = {
            'html': '<b>{tooltip}</b>',
            'style': {
                'backgroundColor': 'rgba(20,20,40,0.92)',
                'color': '#e0e0e0',
                'borderRadius': '6px',
                'padding': '8px 12px',
                'fontSize': '12px',
                'maxWidth': '320px',
                'whiteSpace': 'pre-line',
            },
        }
        st.pydeck_chart(deck, use_container_width=True,
                       selection_mode='single-object', on_select='rerun')
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
                    # 散点模式 — 分级渲染
                    geo = data.get('geo_data')
                    props = geo['features'] if geo else df_display.to_dict('records')
                    _deck, _meta = add_point_layer(
                        deck, data['lats'], data['lons'], data['scores'],
                        props_list=props, n_total=total_rows, return_meta=True)
                    _tier_label, _tier_idx, _sampled = _meta
                    # 记录渲染模式供 UI 提示
                    st.session_state['_render_tier'] = _tier_label
                    st.session_state['_render_sampled'] = _sampled
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
        # ── 叠加选中点轮廓 ──
        sel_pt = st.session_state.get('_selected_point')
        if sel_pt and sel_pt.get('lat') and sel_pt.get('lon'):
            add_selection_marker(deck, sel_pt['lat'], sel_pt['lon'])

        deck.tooltip = {
            'html': '<b>{tooltip}</b>',
            'style': {
                'backgroundColor': 'rgba(20,20,40,0.92)',
                'color': '#e0e0e0',
                'borderRadius': '6px',
                'padding': '8px 12px',
                'fontSize': '12px',
                'maxWidth': '320px',
                'whiteSpace': 'pre-line',
            },
        }
        render_data_summary_overlay(n=n, area_label=area_label,
                                     range_label=range_label, date_label=date_label)

        # ── 渲染模式指示 ──
        _tier = st.session_state.get('_render_tier', '')
        _sampled = st.session_state.get('_render_sampled', 0)
        if _tier:
            _mode_text = f'渲染: {_tier}'
            if _sampled:
                _mode_text += f' (采样 {_sampled} 点)'
            st.caption(_mode_text)

        st.pydeck_chart(deck, use_container_width=True,
                       selection_mode='single-object', on_select='rerun')

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
register_track_id("MOD_APP.F_010", "底图切换弹窗")
register_track_id("MOD_APP.F_011", "情绪分析弹窗")
register_track_id("MOD_APP.F_013", "图层控制弹窗（[LY]）")
register_track_id("MOD_APP.D_010", "图层控制：单个图层圆点点击切换 visible")
register_track_id("MOD_APP.D_011", "图层控制：[全部打开] 批量显示所有图层")
register_track_id("MOD_APP.D_012", "图层控制：[全部关闭] 批量隐藏所有图层")
register_track_id("MOD_APP.D_013", "主数据点层：_all_layers_hidden 隐藏主数据")
register_track_id("MOD_APP.F_017", "A功能：获取图层默认样式（自动差异化配色）")
register_track_id("MOD_APP.F_018", "A功能：解析上传矢量文件（GeoJSON/Shapefile/KML）")
register_track_id("MOD_APP.F_019", "A功能：渲染单图层横条控件（名称+Switch+样式按钮）")
register_track_id("MOD_APP.F_020", "A功能：渲染样式编辑面板（线宽/颜色/填充/不透明度）")
register_track_id("MOD_APP.D_020", "A功能：解析矢量文件决策点")
register_track_id("MOD_APP.D_021", "A功能：安全阈值校验 + 自动简化决策点")
register_track_id("MOD_APP.F_012", "选中点详情卡片渲染（pydeck selection 事件 → 详情面板）")
register_track_id("MOD_APP.D_022", "pydeck selection 事件检测与选中状态保存决策点")


if __name__ == '__main__':
    main()
