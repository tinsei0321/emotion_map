"""
Emotion Map Viewer v2.0
══════════════════════════════════════════════════════════════
重构目标：
  1. 地图为主体（左侧 70%），数据/调试面板（右侧 30%）
  2. 保留全部现有功能 + 天地图底图
  3. 调试 UI 代码用 # ── DEBUG ── 标记，方便后期定位
  4. 模块化架构，每个功能独立函数，便于扩展

未来可扩展模块建议：
  □ 极性筛选器（Positive/Neutral/Negative 切换显示）
  □ 热力图图层（folium.HeatMap）
  □ POI 聚合统计面板
  □ 时间序列分析（如有时间字段）
  □ 暗色模式 / 自定义主题
  □ 导出当前视图为 PNG
  □ 多文件对比模式
  □ 搜索 & 定位功能（按 POI 名称搜索）

启动方式：
  streamlit run streamlit_app_v2.py
══════════════════════════════════════════════════════════════
"""

import os
import json
from collections import Counter

import pandas as pd
import streamlit as st

# ═══════════════════════════════════════════════════════════
# 全局配置
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title='情绪地图L2_test',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── DEBUG ── 调试开关（发布时改为 False）
DEBUG_MODE = True
# ── DEBUG END ──

# 天地图 Key（获取：https://console.tianditu.gov.cn → 创建应用 → 浏览器端）
TIANDITU_KEY = '4d4dc85287c003c8a18d5520b8920796'

# 数据文件夹配置
BASE_DIRS = {
    '📂 processed（处理结果）': 'data/processed',
    '📂 raw（原始数据）': 'data/raw',
}

# 情绪颜色映射
COLOR_MAP = {'Positive': '#28a745', 'Neutral': '#6c757d', 'Negative': '#dc3545'}
FOLIUM_COLOR_MAP = {'Positive': 'green', 'Neutral': 'gray', 'Negative': 'red'}


# ═══════════════════════════════════════════════════════════
# 模块 A：数据加载
# ═══════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def load_csv(file_path: str) -> pd.DataFrame:
    """加载 CSV/TSV 文件（带缓存）"""
    sep = '\t' if file_path.endswith('.tsv') else ','
    return pd.read_csv(file_path, sep=sep)


@st.cache_data(show_spinner=False)
def load_geojson(file_path: str) -> dict:
    """加载 GeoJSON/JSON 文件（带缓存）"""
    with open(file_path, encoding='utf-8') as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════
# 模块 B：地图渲染引擎
# ═══════════════════════════════════════════════════════════

def _add_tianditu_tiles(folium_map, show_labels: bool = True):
    """为 Folium 地图添加天地图底图 + 中文注记"""
    folium_map.add_child(
        __import__('folium').TileLayer(
            tiles=(
                'https://t0.tianditu.gov.cn/img_w/wmts?'
                'SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0'
                '&LAYER=img&STYLE=default&TILEMATRIXSET=w'
                '&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}'
                f'&tk={TIANDITU_KEY}'
            ),
            attr='天地图',
            name='天地图影像',
            max_zoom=18,
        )
    )
    if show_labels:
        folium_map.add_child(
            __import__('folium').TileLayer(
                tiles=(
                    'https://t0.tianditu.gov.cn/cva_w/wmts?'
                    'SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0'
                    '&LAYER=cva&STYLE=default&TILEMATRIXSET=w'
                    '&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}'
                    f'&tk={TIANDITU_KEY}'
                ),
                attr='天地图',
                name='天地图注记',
                overlay=True,
                show=True,
                max_zoom=18,
            )
        )


def render_csv_map(df: pd.DataFrame, map_height: int = 700) -> dict | None:
    """
    为含 lon/lat 列的 CSV DataFrame 生成 Folium 地图。
    返回 gdf 供后续面板使用，失败返回 None。
    """
    import folium
    from streamlit_folium import st_folium

    # 识别坐标列
    lon_col = next((c for c in ['lon', 'longitude', 'lng'] if c in df.columns), None)
    lat_col = next((c for c in ['lat', 'latitude'] if c in df.columns), None)

    if not lon_col or not lat_col:
        st.warning('未找到经纬度列（需要 lon/lat）')
        return None

    center_lat = df[lat_col].mean()
    center_lon = df[lon_col].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        control_scale=True,
        tiles=None,
    )
    _add_tianditu_tiles(m, show_labels=st.session_state.get('show_labels', True))

    import random
    for _, row in df.iterrows():
        polarity = str(row.get('polarity', 'Neutral'))
        color = FOLIUM_COLOR_MAP.get(polarity, 'blue')

        id_val = str(row.get('id_e', row.get('id', '')))
        seed = hash(id_val) % 10000
        rng = random.Random(seed)
        lat = float(row[lat_col]) + rng.uniform(-0.0003, 0.0003)
        lon = float(row[lon_col]) + rng.uniform(-0.0003, 0.0003)

        tooltip_parts = []
        for col in ['id_e', 'poi', 'comments', 'score', 'polarity']:
            if col in df.columns:
                tooltip_parts.append(f"<b>{col}:</b> {row[col]}")
        tooltip_html = '<br>'.join(tooltip_parts) if tooltip_parts else f'点 {id_val}'

        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            color=color,
            weight=2,
            tooltip=folium.Tooltip(tooltip_html, max_width=300),
        ).add_to(m)

    st_folium(m, width=None, height=map_height, key='csv_map')
    return {'center': (center_lat, center_lon)}


def render_geojson_map(data: dict, map_height: int = 700) -> dict | None:
    """
    为 GeoJSON FeatureCollection 生成 Folium 地图。
    支持热点模式（show_heatmap=True）。
    """
    import folium
    from streamlit_folium import st_folium
    import geopandas as gpd

    data_copy = {k: v for k, v in data.items() if k != 'crs'}
    gdf = gpd.GeoDataFrame.from_features(data_copy['features'])

    center_lat = gdf.geometry.y.mean()
    center_lon = gdf.geometry.x.mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        control_scale=True,
        tiles=None,
    )
    _add_tianditu_tiles(m, show_labels=st.session_state.get('show_labels', True))

    # ── 热点模式 ──
    if st.session_state.get('show_heatmap'):
        from folium.plugins import HeatMap
        lats = [f['geometry']['coordinates'][1] for f in data['features']]
        lons = [f['geometry']['coordinates'][0] for f in data['features']]
        scores = [float(f['properties'].get('score', 0.5)) for f in data['features']]
        mode = st.session_state.get('hm_mode', 'hotcold')
        radius = st.session_state.get('hm_radius', 15)
        blur = st.session_state.get('hm_blur', 10)
        min_op = st.session_state.get('hm_min_opacity', 0.4)

        if mode == 'hotcold':
            hdata = [[lat, lon, s] for lat, lon, s in zip(lats, lons, scores)]
            HeatMap(hdata, radius=radius, blur=blur, min_opacity=min_op,
                    gradient={0.2: '#0000ff', 0.4: '#00ffff', 0.5: '#00ff00',
                              0.7: '#ffff00', 0.9: '#ff0000'}).add_to(m)
            _render_hm_legend('hotcold')
        else:
            pos_data = [[lat, lon, s] for lat, lon, s in zip(lats, lons, scores) if s >= 0.7]
            neg_data = [[lat, lon, 1 - s] for lat, lon, s in zip(lats, lons, scores) if s <= 0.3]
            if pos_data:
                HeatMap(pos_data, radius=radius, blur=blur, min_opacity=min_op,
                        gradient={0.4: '#a5d6a7', 0.7: '#4caf50', 1.0: '#1b5e20'},
                        name='正面聚集').add_to(m)
            if neg_data:
                HeatMap(neg_data, radius=radius, blur=blur, min_opacity=min_op,
                        gradient={0.4: '#ef9a9a', 0.7: '#f44336', 1.0: '#b71c1c'},
                        name='负面聚集').add_to(m)
            _render_hm_legend('polarity')
    else:
        # ── 点状模式 ──
        import random
        for feature in data['features']:
            props = feature['properties']
            coords = feature['geometry']['coordinates']
            polarity = str(props.get('polarity', 'Neutral'))
            color = FOLIUM_COLOR_MAP.get(polarity, 'blue')

            seed = hash(str(props.get('id_e', ''))) % 10000
            rng = random.Random(seed)
            lat = coords[1] + rng.uniform(-0.0003, 0.0003)
            lon = coords[0] + rng.uniform(-0.0003, 0.0003)

            tooltip_parts = []
            for key in ['id_e', 'poi', 'comments', 'score', 'polarity']:
                if key in props:
                    tooltip_parts.append(f"<b>{key}:</b> {props[key]}")
            tooltip_html = '<br>'.join(tooltip_parts)

            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                color=color,
                weight=2,
                tooltip=folium.Tooltip(tooltip_html, max_width=300),
            ).add_to(m)

    map_key = 'geojson_map'
    # ── DEBUG ──
    if DEBUG_MODE and st.session_state.get('show_heatmap'):
        st.caption(f'🔥 热力图: key={map_key}, 模式={st.session_state.get("hm_mode")}, '
                   f'半径={st.session_state.get("hm_radius")}, '
                   f'数据点={len(data["features"])}')
    # ── DEBUG END ──
    st_folium(m, width=None, height=map_height, key=map_key)
    return {'gdf': gdf, 'center': (center_lat, center_lon), 'n_features': len(data['features'])}


# ═══════════════════════════════════════════════════════════
# 模块 C：弹窗对话框（概览 / 数据表）
# ═══════════════════════════════════════════════════════════

def _panel_coord_dup_analysis(df_or_gdf, geom_col=None):
    """坐标重复度分析（通用，支持 DataFrame 和 GeoDataFrame）"""
    if geom_col is not None:
        coords_list = [(round(g.x, 5), round(g.y, 5)) for g in geom_col]
    else:
        lon_c = next((c for c in ['lon', 'longitude', 'lng'] if c in df_or_gdf.columns), None)
        lat_c = next((c for c in ['lat', 'latitude'] if c in df_or_gdf.columns), None)
        if not lon_c or not lat_c:
            return
        coords_list = [
            (round(r[lon_c], 5), round(r[lat_c], 5))
            for _, r in df_or_gdf.iterrows()
        ]

    coord_counter = Counter(coords_list)
    unique_coords = len(coord_counter)
    total_points = len(coords_list)
    dup_ratio = (1 - unique_coords / total_points) * 100 if total_points > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric('总点数', total_points)
    c2.metric('唯一坐标', unique_coords)
    c3.metric('重复率', f'{dup_ratio:.1f}%')

    if dup_ratio > 0:
        st.caption(f'平均每个坐标堆积 {total_points/unique_coords:.1f} 个点')

    return coord_counter

@st.dialog('📊 数据概览', width='large')
def show_overview_dialog(df, map_meta, file_choice):
    """以模态弹窗展示数据概览：统计、图表、坐标分析"""

    st.caption(f'文件: `{file_choice}` | 共 **{len(df)}** 条记录')

    has_polarity = 'polarity' in df.columns
    has_score = 'score' in df.columns

    # ── 情绪统计 ──
    if has_polarity or has_score:
        st.subheader('情绪分析', divider='gray')
        if has_polarity:
            pos = (df['polarity'] == 'Positive').sum()
            neu = (df['polarity'] == 'Neutral').sum()
            neg = (df['polarity'] == 'Negative').sum()
            total = len(df)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric('总数', total)
            c2.metric('😊 正面', pos, delta=f'{pos/total*100:.0f}%' if total else '')
            c3.metric('😐 中性', neu)
            c4.metric('😞 负面', neg)

        if has_score:
            st.caption(
                f"得分 — 均值: **{df['score'].mean():.2f}** | "
                f"中位数: **{df['score'].median():.2f}** | "
                f"标准差: **{df['score'].std():.2f}**"
            )

        if has_polarity:
            import altair as alt
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('polarity:N', title=None, sort=['Positive', 'Neutral', 'Negative']),
                y=alt.Y('count()', title=None),
                color=alt.Color(
                    'polarity:N',
                    scale=alt.Scale(
                        domain=['Positive', 'Neutral', 'Negative'],
                        range=['#28a745', '#6c757d', '#dc3545']
                    ),
                    legend=None
                )
            ).properties(height=200)
            st.altair_chart(chart, width='stretch')

    # ── 坐标重复度 ──
    if map_meta:
        st.subheader('坐标分析', divider='gray')
        gdf = map_meta.get('gdf')
        if gdf is not None:
            _panel_coord_dup_analysis(gdf, geom_col=gdf.geometry)
        else:
            _panel_coord_dup_analysis(df)

    # ── POI 分布 ──
    if 'poi' in df.columns:
        st.subheader('POI 分布', divider='gray')
        poi_counts = df['poi'].value_counts().head(15)
        c1, c2 = st.columns([3, 2])
        with c1:
            st.dataframe(
                poi_counts.reset_index().set_axis(['POI', '数量'], axis=1),
                width='stretch',
                hide_index=True,
            )
        with c2:
            import altair as alt
            poi_chart = alt.Chart(
                poi_counts.reset_index().set_axis(['POI', '数量'], axis=1)
            ).mark_bar().encode(
                y=alt.Y('POI:N', sort='-x', title=None),
                x=alt.X('数量:Q', title=None),
                color=alt.value('#4a90d9'),
            ).properties(height=300)
            st.altair_chart(poi_chart, width='stretch')


@st.dialog('📋 数据表格', width='large')
def show_table_dialog(df, file_choice):
    """以模态弹窗展示完整数据表格"""
    st.caption(f'文件: `{file_choice}` | 共 **{len(df)}** 条记录')

    # 搜索过滤
    search = st.text_input('🔍 搜索（任意列匹配）', placeholder='输入关键词过滤...')
    display_df = df
    if search:
        mask = display_df.astype(str).apply(
            lambda row: row.str.contains(search, case=False, na=False).any(), axis=1
        )
        display_df = display_df[mask]
        st.caption(f'筛选结果: {len(display_df)} / {len(df)} 条')

    cols_to_hide = [c for c in ['lon', 'lat', 'longitude', 'latitude', 'geometry'] if c in df.columns]
    show_cols = [c for c in display_df.columns if c not in cols_to_hide]

    st.dataframe(display_df[show_cols], width='stretch', height=500)

    # 下载
    st.download_button(
        '⬇ 下载筛选结果为 CSV',
        display_df.to_csv(index=False).encode('utf-8'),
        file_name=file_choice,
        mime='text/csv',
    )


# ═══════════════════════════════════════════════════════════
# 模块 C-extra：数据源 & 设置弹窗
# ═══════════════════════════════════════════════════════════

@st.dialog('🔥 热点分析', width='small')
def show_heatmap_dialog():
    """弹窗：热点图参数设置"""
    st.caption('设置热点图参数后点击生成')

    mode = st.radio('热点模式', ['🔥 冷热分布', '😊😞 极性分布'],
                    help='冷热分布=情绪聚集热点；极性分布=正/负面情绪分别聚类')
    radius = st.slider('搜索半径 (px)', 5, 40, st.session_state.get('hm_radius', 15),
                       help='点的影响范围，越大越平滑')
    blur = st.slider('模糊度', 3, 30, st.session_state.get('hm_blur', 10),
                     help='值越大边缘越柔和')
    min_opacity = st.slider('最小透明度', 0.1, 1.0,
                            st.session_state.get('hm_min_opacity', 0.4), 0.05,
                            help='低密度区域透明度')

    if st.button('✅ 生成热点图', use_container_width=True, type='primary'):
        st.session_state['hm_mode'] = 'hotcold' if '冷热' in mode else 'polarity'
        st.session_state['hm_radius'] = radius
        st.session_state['hm_blur'] = blur
        st.session_state['hm_min_opacity'] = min_opacity
        st.session_state['show_heatmap'] = True
        st.rerun()

    if st.button('↩ 恢复点状图', use_container_width=True):
        st.session_state['show_heatmap'] = False
        st.rerun()

@st.dialog('📂 数据源', width='small')
def show_data_source_dialog():
    """弹窗：选择数据文件夹和文件"""
    folder_key = st.selectbox(
        '数据文件夹', list(BASE_DIRS.keys()),
        index=list(BASE_DIRS.keys()).index(
            st.session_state.get('folder_key', list(BASE_DIRS.keys())[0])
        ),
    )
    folder_path = BASE_DIRS[folder_key]

    if not os.path.exists(folder_path):
        st.warning(f'文件夹不存在: `{folder_path}`')
        return

    files = sorted([
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ])
    if not files:
        st.info('文件夹为空')
        return

    current_file = st.session_state.get('file_choice', files[0])
    default_idx = files.index(current_file) if current_file in files else 0
    file_choice = st.selectbox('选择文件', files, index=default_idx)

    st.caption(f'路径: `{os.path.join(folder_path, file_choice)}`')

    if st.button('✅ 确认加载', use_container_width=True, type='primary'):
        st.session_state['folder_key'] = folder_key
        st.session_state['file_choice'] = file_choice
        st.session_state['file_path'] = os.path.join(folder_path, file_choice)
        st.rerun()


@st.dialog('⚙ 更多设置', width='small')
def show_settings_dialog():
    """弹窗：其他设置和调试信息"""
    st.caption('注记和图例已移至左侧 HUD 按钮直接操作')

    # ── DEBUG ──
    if DEBUG_MODE:
        st.divider()
        st.caption('🛠 调试信息（仅开发可见）')
        if st.session_state.get('file_path'):
            st.write(f'- 文件: `{os.path.basename(st.session_state["file_path"])}`')
        st.write(f'- Session keys: `{list(st.session_state.keys())}`')
    # ── DEBUG END ──


# ═══════════════════════════════════════════════════════════
# 模块 D：主渲染流程
# ═══════════════════════════════════════════════════════════

def _render_default_map():
    """渲染默认天地图背景（无数据时）"""
    import folium
    from streamlit_folium import st_folium
    m = folium.Map(location=[30.708, 111.286], zoom_start=12,
                   control_scale=True, tiles=None)
    TIANDITU_KEY = '4d4dc85287c003c8a18d5520b8920796'
    folium.TileLayer(
        tiles=f'https://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile'
              f'&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w'
              f'&FORMAT=tiles&TILEMATRIX={{z}}&TILEROW={{y}}&TILECOL={{x}}&tk={TIANDITU_KEY}',
        attr='天地图', name='天地图影像', max_zoom=18).add_to(m)
    if st.session_state.get('show_labels', True):
        folium.TileLayer(
            tiles=f'https://t0.tianditu.gov.cn/cva_w/wmts?SERVICE=WMTS&REQUEST=GetTile'
                  f'&VERSION=1.0.0&LAYER=cva&STYLE=default&TILEMATRIXSET=w'
                  f'&FORMAT=tiles&TILEMATRIX={{z}}&TILEROW={{y}}&TILECOL={{x}}&tk={TIANDITU_KEY}',
            attr='天地图', name='天地图注记', overlay=True, show=True, max_zoom=18).add_to(m)
    st_folium(m, width=None, height=700, key='default_map')


def _render_legend_overlay():
    """渲染图例叠加层（热力图模式下自动隐藏）"""
    if st.session_state.get('show_heatmap'):
        return  # 热力图有自己的图例
    if not st.session_state.get('show_legend', True):
        return
    st.markdown("""
    <div style="position:fixed;bottom:28px;right:14px;z-index:9999;pointer-events:none;
    background:rgba(0,0,0,0.55);padding:8px 12px;border-radius:8px;color:#fff;
    font-size:0.8rem;line-height:1.6;backdrop-filter:blur(4px);">
    <span style="color:#28a745;">●</span> 正面 Positive<br>
    <span style="color:#6c757d;">●</span> 中性 Neutral<br>
    <span style="color:#dc3545;">●</span> 负面 Negative
    </div>
    """, unsafe_allow_html=True)


def _render_hm_legend(mode):
    """渲染热点图专属图例"""
    if mode == 'hotcold':
        st.markdown("""
        <div style="position:fixed;bottom:28px;right:14px;z-index:9999;pointer-events:none;
        background:rgba(0,0,0,0.55);padding:8px 12px;border-radius:8px;">
        <span style="font-size:0.8rem;color:#fff;">🔥 冷热分布</span><br>
        <span style="display:inline-block;width:80px;height:8px;border-radius:4px;
        background:linear-gradient(90deg,#0000ff,#00ffff,#00ff00,#ffff00,#ff0000);"></span>
        <span style="font-size:0.7rem;color:#aaa;float:right;">热→</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="position:fixed;bottom:28px;right:14px;z-index:9999;pointer-events:none;
        background:rgba(0,0,0,0.55);padding:8px 12px;border-radius:8px;">
        <span style="font-size:0.8rem;color:#fff;">😊😞 极性分布</span><br>
        <span style="color:#4caf50;">■</span><span style="font-size:0.7rem;color:#ccc;"> 正面聚集</span><br>
        <span style="color:#f44336;">■</span><span style="font-size:0.7rem;color:#ccc;"> 负面聚集</span>
        </div>
        """, unsafe_allow_html=True)


def main():
    """主渲染入口 — 整页地图 + 顶部按钮栏"""

    # ── 初始化 session_state ──
    defaults = {
        'show_labels': True,
        'show_legend': True,
        'show_heatmap': False,
        'hm_mode': 'hotcold',
        'hm_radius': 15,
        'hm_blur': 10,
        'hm_min_opacity': 0.4,
        'folder_key': list(BASE_DIRS.keys())[0],
        'file_choice': '',
        'file_path': '',
        'current_df': None,
        'current_map_meta': None,
        'current_file_choice': '',
        'data_loaded': False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ═══════════════════════════════════════════════════
    # 零留白全页地图 CSS（自适应铺满 + 按钮居中）
    # ═══════════════════════════════════════════════════
    st.markdown("""
    <style>
    html, body, #root, [data-testid="stAppViewContainer"] {
        margin: 0 !important; padding: 0 !important;
        overflow: hidden !important;
        width: 100vw !important; height: 100vh !important;
    }
    header[data-testid="stHeader"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    footer { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    [data-testid="stDeployButton"] { display: none !important; }
    .appview-block-container { padding: 0 !important; }
    .main > div:first-child { padding: 0 !important; }
    .st-emotion-cache-zq5wmm { padding: 0 !important; }
    [data-testid="stAppViewContainer"] > section { padding: 0 !important; }
    .main { padding-bottom: 0 !important; }
    [data-testid="stVerticalBlock"] { gap: 0 !important; }
    [data-testid="stAppViewContainer"] {
        clip: auto !important; clip-path: none !important;
    }

    /* 移除 Streamlit transform，保证 fixed 相对视口 */
    section[data-testid="stAppViewContainer"] > section > div,
    section[data-testid="stAppViewContainer"] > section > div > div,
    section[data-testid="stAppViewContainer"] > section > div > div > div {
        transform: none !important;
        filter: none !important;
        perspective: none !important;
        will-change: auto !important;
    }

    /* 地图 iframe 铺满视口（JS 辅助确保尺寸） */
    iframe[title="streamlit_folium\\.st_folium"] {
        position: fixed !important;
        top: 0 !important; left: 0 !important;
        width: 100vw !important; height: 100vh !important;
        min-width: 100vw !important; min-height: 100vh !important;
        max-width: 100vw !important; max-height: 100vh !important;
        z-index: 0 !important;
        border: none !important;
        margin: 0 !important; padding: 0 !important;
    }

    /* 按钮防消失 + 统一样式 */
    [data-testid="stAppViewContainer"] button {
        position: relative !important;
        z-index: 10000 !important;
    }
    /* 所有 HUD 按钮统一样式 */
    .st-key-d button, .st-key-lbl button, .st-key-leg button, .st-key-s button,
    .st-key-o button, .st-key-t button, .st-key-hm button {
        width: 44px !important; height: 44px !important;
        border-radius: 10px !important; font-size: 1.2rem !important;
        padding: 0 !important;
        background: rgba(30,30,30,0.75) !important;
        color: #fff !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }
    /* 📂 数据源：左侧居中 */
    .st-key-d { position: fixed !important; top: calc(50% - 22px) !important;
        left: 14px !important; z-index: 9999 !important; }
    /* ⚙ 设置：左下 */
    .st-key-s { position: fixed !important; bottom: 50px !important;
        left: 14px !important; z-index: 9999 !important; }
    /* 🏷 注记 + 🎨 图例：左下横排，与 ⚙ 对齐 */
    .st-key-lbl { position: fixed !important; bottom: 50px !important;
        left: 64px !important; z-index: 9999 !important; }
    .st-key-leg { position: fixed !important; bottom: 50px !important;
        left: 114px !important; z-index: 9999 !important; }
    /* 📊 📋 数据面板：右侧居中 */
    .st-key-o { position: fixed !important; top: calc(50% - 50px) !important;
        right: 14px !important; z-index: 9999 !important; }
    .st-key-t { position: fixed !important; top: calc(50% + 2px) !important;
        right: 14px !important; z-index: 9999 !important; }
    /* 🔥 热点图：右中下方 */
    .st-key-hm { position: fixed !important; top: calc(50% + 54px) !important;
        right: 14px !important; z-index: 9999 !important; }

    /* 隐藏 Leaflet 链接，仅保留天地图 */
    .leaflet-control-attribution a { display: none !important; }
    /* 比例尺美化：半透明毛玻璃 */
    .leaflet-control-scale-line {
        background: rgba(0,0,0,0.5) !important;
        color: #fff !important;
        border-color: rgba(255,255,255,0.25) !important;
        font-size: 10px !important;
        padding: 2px 6px !important;
    }
    </style>

    <script>
    // 自适应：窗口大小变化时强制 iframe 填满
    function fixIframeSize() {
        var f = document.querySelector('iframe[title*="streamlit_folium"]');
        if (f) {
            f.style.position = 'fixed';
            f.style.top = '0px'; f.style.left = '0px';
            f.style.width = window.innerWidth + 'px';
            f.style.height = window.innerHeight + 'px';
            f.style.zIndex = '0';
        }
    }
    window.addEventListener('resize', fixIframeSize);
    // 延迟执行确保 DOM 就绪
    setTimeout(fixIframeSize, 500);
    setTimeout(fixIframeSize, 2000);
    </script>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════
    # HUD 按钮（扁平排列，CSS 独立定位）
    # ═══════════════════════════════════════════════════
    file_choice = st.session_state.get('file_choice', '')
    btn_disabled = st.session_state.get('current_df') is None

    # ── 标题 ──
    if file_choice:
        st.markdown(
            f'<div style="position:fixed;top:16px;left:0;right:0;text-align:center;'
            f'z-index:9999;pointer-events:none;">'
            f'<span style="font-size:0.95rem;font-weight:600;color:#fff;'
            f'text-shadow:0 1px 3px rgba(0,0,0,0.7);'
            f'background:rgba(0,0,0,0.4);padding:4px 16px;border-radius:20px;'
            f'backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);">'
            f'情绪地图L2_test "{file_choice}"</span></div>',
            unsafe_allow_html=True)

    # ── 📂 数据源（左中）──
    if st.button('📂', help='选择数据源', key='d'):
        show_data_source_dialog()

    # ── ⚙ 设置（左下）──
    if st.button('⚙', help='更多设置', key='s'):
        show_settings_dialog()

    # ── 🏷 注记 + 🎨 图例（右下横排）──
    show_lbl = st.session_state.get('show_labels', True)
    if st.button('注' if show_lbl else '🚫',
                 help='注记: 开' if show_lbl else '注记: 关', key='lbl'):
        st.session_state['show_labels'] = not show_lbl
        st.rerun()
    show_leg = st.session_state.get('show_legend', True)
    if st.button('🎨' if show_leg else '⬜',
                 help='图例: 开' if show_leg else '图例: 关', key='leg'):
        st.session_state['show_legend'] = not show_leg
        st.rerun()

    # ── 📊 📋 数据面板（右中）──
    if st.button('📊', help='数据概览', key='o', disabled=btn_disabled):
        show_overview_dialog(
            st.session_state['current_df'],
            st.session_state['current_map_meta'],
            st.session_state['current_file_choice'])
    if st.button('📋', help='数据表格', key='t', disabled=btn_disabled):
        show_table_dialog(
            st.session_state['current_df'],
            st.session_state['current_file_choice'])
    if st.button('🔥', help='热点分析', key='hm', disabled=btn_disabled):
        show_heatmap_dialog()

    # ═══════════════════════════════════════════════════
    # 数据加载 + 地图渲染
    # ═══════════════════════════════════════════════════
    file_path = st.session_state.get('file_path', '')

    if not file_path or not os.path.exists(file_path):
        # 默认天地图背景
        _render_default_map()
        # 图例
        _render_legend_overlay()
        # 居中可点击按钮
        _, c_btn, _ = st.columns([3, 2, 3])
        with c_btn:
            st.markdown('<div style="height:30vh"></div>', unsafe_allow_html=True)
            if st.button('📂 选择数据文件', help='打开数据源', use_container_width=True,
                         type='primary', key='hero_btn'):
                show_data_source_dialog()
        return

    file_choice = st.session_state['file_choice']
    ext = file_choice.lower().split('.')[-1]

    try:
        df = None
        geo_data = None
        map_meta = None

        if ext in ('csv', 'tsv'):
            df = load_csv(file_path)
        elif ext in ('json', 'geojson'):
            geo_data = load_geojson(file_path)
            if isinstance(geo_data, dict) and geo_data.get('type') == 'FeatureCollection':
                import geopandas as gpd
                data_copy = {k: v for k, v in geo_data.items() if k != 'crs'}
                gdf = gpd.GeoDataFrame.from_features(data_copy['features'])
                df = pd.DataFrame(gdf.drop(columns=['geometry']))
            else:
                df = None

        if df is not None:
            st.session_state['current_df'] = df
            st.session_state['current_file_choice'] = file_choice
            st.session_state['data_loaded'] = True
        else:
            st.session_state['data_loaded'] = False

        if ext in ('csv', 'tsv') and df is not None:
            map_meta = render_csv_map(df, map_height=700)
        elif geo_data is not None and geo_data.get('type') == 'FeatureCollection':
            result = render_geojson_map(geo_data, map_height=700)
            if result:
                map_meta = result
        elif ext in ('json', 'geojson') and df is None:
            st.json(geo_data)
        elif df is None and ext not in ('json', 'geojson'):
            st.info(f'无法渲染 .{ext} 文件')

        st.session_state['current_map_meta'] = map_meta
        _render_legend_overlay()

    except Exception as e:
        import traceback
        st.error(f'❌ 加载失败: {e}')

        # ── DEBUG ──
        if DEBUG_MODE:
            with st.expander('🔍 错误详情 (DEBUG)', expanded=True):
                st.code(traceback.format_exc())
        # ── DEBUG END ──


# ═══════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════
if __name__ == '__main__':
    main()
