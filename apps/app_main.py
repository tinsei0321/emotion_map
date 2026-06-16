"""
情绪地图 v1.0 — 地图浏览器 + 分析控制台
══════════════════════════════════════════════════════════════
启动: py launch.py                    # 一键启动
      python -m streamlit run apps/app_main.py

页面: 默认 = 地图浏览器
      ?page=console&file=xxx  = 分析控制台（自动加载结果）
"""
import os, sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 加载 .env 到环境变量（Streamlit 进程不会自动继承）──
def _load_dotenv():
    """手动加载 .env 文件（无需 python-dotenv 依赖）。"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, _, value = line.partition('=')
                key, value = key.strip(), value.strip()
                if key and key not in os.environ:
                    os.environ[key] = value

_load_dotenv()

from core.config import (
    MAX_DISPLAY_POINTS, LARGE_FILE_WARN_MB,
)
from core.map_engine import (
    create_base_map, add_point_layer, add_boundary_layer,
    add_heatmap_layer, add_multiple_boundary_layers,
)
from core.data_loader import load_emotion_data
from core.range_selector import get_boundary_geojson
from core.ui_components import (
    inject_fullscreen_css, hud_button_style_css,
    render_toolbar_shell, render_side_panel,
    render_legend_overlay,
    inject_theme_css, show_toast,
)
from core.tracker import track, trace_log, trace_error, register_track_id
from apps.app_console import show_console_page

# ── 弹窗模块（从 app_main.py 拆分）──
from apps.app_dialogs import (
    show_data_source_dialog,
    show_overview_dialog,
    show_table_dialog,
    show_export_dialog,
    show_range_dialog,
    show_basemap_dialog,
    show_layer_dialog,
    show_analysis_dialog,
    _register_dialog_track_ids,
)

st.set_page_config(page_title='情绪地图 v1.0', layout='wide')
DEBUG_MODE = True


# ═══════════════════════════════════════════════════════════
# 边界叠加辅助
# ═══════════════════════════════════════════════════════════

def _add_boundary_if_exists(deck):
    """叠加所有已确认的分析范围图层到地图。"""
    try:
        layers = st.session_state.get("analysis_layers", [])
        if layers:
            add_multiple_boundary_layers(deck, layers)
            return
        geojson = get_boundary_geojson()
        if geojson:
            color = st.session_state.get('_boundary_color', '#d97d5c')
            weight = st.session_state.get('_boundary_weight', 15)
            add_boundary_layer(deck, geojson_data=geojson,
                             name='分析范围', color=color, weight=weight)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════

@track("MOD_APP.F_002", track_args=False)
def main():
    # ── session_state 初始化 ──
    for k, v in {
        '_map_style': 'carto_standard',
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

    # ── 强制清除 ──
    if '_load_triggered' not in st.session_state:
        st.session_state['_load_triggered'] = False
        st.session_state['file_path'] = ''
        st.session_state['current_df'] = None
        st.session_state['data_loaded'] = False

    # ── 崩溃恢复 ──
    if st.session_state.get('_data_crashed', False):
        st.session_state['file_path'] = ''
        st.session_state['current_df'] = None
        st.session_state['_data_crashed'] = False
        st.warning('上次加载数据量过大导致页面异常，已自动清除。')

    # ── 路由分发 ──
    page = st.query_params.get('page', None)
    if page == 'console':
        show_console_page()
        return

    # ── 注册弹窗追踪 ID ──
    _register_dialog_track_ids()

    # ── 注入 CSS ──
    inject_theme_css()
    inject_fullscreen_css()
    hud_button_style_css()

    st.markdown("""
    <style>
    canvas[data-testid="stDeckGlJsonChart"] { cursor: auto !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Import 触发数据加载（在工具栏前处理，避免按钮状态滞后）──
    if st.session_state.get('_load_triggered'):
        fp = st.session_state.get('file_path', '')
        if fp and os.path.exists(fp):
            try:
                data = load_emotion_data(fp)
                if data:
                    df = data['df']
                    total = len(df)
                    if total > MAX_DISPLAY_POINTS:
                        import random as _random
                        idx = _random.Random(42).sample(range(total), MAX_DISPLAY_POINTS)
                        df = df.iloc[idx].reset_index(drop=True)
                    st.session_state['current_df'] = df
                    st.session_state['_total_rows'] = total
                    st.session_state['current_file_choice'] = st.session_state.get('file_choice', '')
                    st.session_state['data_loaded'] = True
                    st.session_state['_load_triggered'] = False
            except Exception:
                st.session_state['_load_triggered'] = False

    # ── geojson.io 风格双层顶栏 ──
    render_toolbar_shell()
    fc = st.session_state.get('file_choice', '')
    btn_dis = st.session_state.get('current_df') is None

    # 工具栏按钮
    if st.button('R', key='tb_range', help='分析范围'): show_range_dialog()
    if st.button('LY', key='tb_layers', help='图层控制'): show_layer_dialog()
    if st.button('A', key='tb_analysis', help='情绪分析', disabled=btn_dis): show_analysis_dialog()
    if st.button('OV', key='tb_overview', help='数据概览', disabled=btn_dis): show_overview_dialog()
    if st.button('TB', key='tb_table', help='数据表格', disabled=btn_dis): show_table_dialog()
    if st.button('Import', key='tb_import', help='导入数据'): show_data_source_dialog()
    if st.button('Export', key='tb_export', help='导出数据', disabled=btn_dis): show_export_dialog()
    if st.button('M', key='tb_m', help='切换底图'): show_basemap_dialog()

    heat_on = st.session_state.get('_heatmap_mode', False)
    heat_label = 'H' if not heat_on else 'H*'
    if st.button(heat_label, key='tb_heat', help='热力图切换'):
        st.session_state['_heatmap_mode'] = not heat_on
        new_mode = '热力图' if st.session_state['_heatmap_mode'] else '散点图'
        st.session_state['_toast'] = f'[OK] 已切换至{new_mode}'
        st.rerun()

    if not btn_dis:
        render_legend_overlay(mode='point')

    # ── 数据加载 + 地图 ──
    fp = st.session_state.get('file_path', '')
    _ms = st.session_state.get('_map_style', 'carto_standard')
    center = st.session_state.get('_map_center', None)
    zoom = st.session_state.get('_map_zoom', None)
    data = None
    df_display = None
    total_rows = 0
    has_data_file = bool(fp and os.path.exists(fp))

    if not has_data_file:
        deck = create_base_map(center=center, zoom_start=zoom, map_style=_ms)
        if st.session_state.get('selected_ranges'):
            _add_boundary_if_exists(deck)
    else:
        _need_load = (
            st.session_state.get('_load_triggered', False) or
            not st.session_state.get('data_loaded', False) or
            st.session_state.get('current_file_choice', '') != fc
        )

        if _need_load:
            file_size_mb = os.path.getsize(fp) / (1024 * 1024)
            if file_size_mb > LARGE_FILE_WARN_MB:
                st.warning(f'文件过大 ({file_size_mb:.0f} MB)，地图仅显示采样点。')

            try:
                with st.spinner('加载数据中...'):
                    data = load_emotion_data(fp)
            except Exception as e:
                trace_error("MOD_APP.F_002", f'主流程数据加载异常: {str(e)[:200]}')
                st.session_state['_data_crashed'] = True
                st.session_state['file_path'] = ''
                st.session_state['current_df'] = None
                st.error(f'加载失败: {e}。数据已清除，请重新选择文件。')
                st.rerun()

            if not data:
                st.error('无法加载数据，请检查文件格式')
                st.session_state['data_loaded'] = False
                deck = create_base_map(center=center, zoom_start=zoom, map_style=_ms)
                if st.session_state.get('selected_ranges'):
                    _add_boundary_if_exists(deck)
                has_data_file = False

            df = data['df']
            total_rows = len(df)

            if total_rows > MAX_DISPLAY_POINTS:
                import random as _random
                sample_idx = _random.Random(42).sample(range(total_rows), MAX_DISPLAY_POINTS)
                df_display = df.iloc[sample_idx].reset_index(drop=True)
                st.info(f'数据共 {total_rows} 条，地图显示采样 {MAX_DISPLAY_POINTS} 条。')
            else:
                df_display = df

            st.session_state['current_df'] = df_display
            st.session_state['_total_rows'] = total_rows
            st.session_state['current_file_choice'] = fc
            st.session_state['data_loaded'] = True
            st.session_state['_load_triggered'] = False
            st.session_state['_toast'] = '[OK] 数据加载成功'
        else:
            df_display = st.session_state.get('current_df')
            total_rows = st.session_state.get('_total_rows', 0)
            if df_display is not None:
                data = {
                    'lats': df_display['lat'].tolist() if 'lat' in df_display else [],
                    'lons': df_display['lon'].tolist() if 'lon' in df_display else [],
                    'scores': df_display['score'].tolist() if 'score' in df_display else [0.5]*len(df_display),
                    'df': df_display,
                }

        # ── 构建 deck ──
        with st.spinner('渲染地图中...' if _need_load else None):
            deck = create_base_map(
                data['lats'] if data else None,
                data['lons'] if data else None,
                center=center, zoom_start=zoom, map_style=_ms)

            _add_boundary_if_exists(deck)

            # 叠加可见图层
            layers = st.session_state.get('layers', [])
            for lyr in layers:
                if not lyr.get('visible', True): continue
                fp_layer = lyr.get('file_path', '')
                if not fp_layer or not os.path.exists(fp_layer): continue
                if fp_layer == fp: continue
                layer_data = load_emotion_data(fp_layer)
                if layer_data:
                    add_point_layer(deck, layer_data['lats'], layer_data['lons'],
                                   layer_data['scores'],
                                   props_list=layer_data['df'].to_dict('records'))

            # 主数据层
            if not st.session_state.get('_all_layers_hidden', False) and data:
                if st.session_state.get('_heatmap_mode', False):
                    add_heatmap_layer(deck, data['lats'], data['lons'],
                                     scores=data['scores'],
                                     radius=30, intensity=0.6, opacity=0.75,
                                     max_points=MAX_DISPLAY_POINTS)
                else:
                    geo = data.get('geo_data')
                    props = geo['features'] if geo else df_display.to_dict('records')
                    _deck, _meta = add_point_layer(
                        deck, data['lats'], data['lons'], data['scores'],
                        props_list=props, n_total=total_rows, return_meta=True)
                    _tier_label, _tier_idx, _sampled = _meta
                    st.session_state['_render_tier'] = _tier_label
                    st.session_state['_render_sampled'] = _sampled
            elif st.session_state.get('_all_layers_hidden', False):
                trace_log("MOD_APP.D_013", detail='main data layer hidden by _all_layers_hidden')

        # 数据摘要浮层
        if data and df_display is not None:
            n = len(df_display)
            visible_layers = [lyr for lyr in st.session_state.get('layers', [])
                             if lyr.get('visible', True)]
            render_side_panel(
                visible_layers=visible_layers,
                selected_ranges=st.session_state.get('selected_ranges', []),
                file_name=fc,
                n_records=n if not st.session_state.get('_all_layers_hidden', False) else 0,
            )

            _tier = st.session_state.get('_render_tier', '')
            _sampled = st.session_state.get('_render_sampled', 0)
            if _tier:
                _mode_text = f'渲染: {_tier}'
                if _sampled:
                    _mode_text += f' (采样 {_sampled} 点)'
                st.caption(_mode_text)

    st.pydeck_chart(deck, use_container_width=True)

    # ── 消费 Toast ──
    pending = st.session_state.pop('_toast', None)
    if pending:
        show_toast(pending)


# ── 追踪 ID 注册表 ──
register_track_id("MOD_APP.F_001", "分析控制台子页面（?page=console）")
register_track_id("MOD_APP.F_002", "主应用入口（地图浏览器 + 路由分发）")
register_track_id("MOD_APP.F_004", "注册/更新图层到 session_state")
register_track_id("MOD_APP.D_013", "主数据点层：_all_layers_hidden 隐藏主数据")


if __name__ == '__main__':
    main()
