import os
import json
from collections import Counter

import pandas as pd
import streamlit as st


# ═══════════════════════════════════════════════════════════
# 页面配置
# ═══════════════════════════════════════════════════════════
st.set_page_config(page_title='Emotion Map Viewer', layout='wide')


# ═══════════════════════════════════════════════════════════
# 辅助函数：CSV 地图可视化
# ═══════════════════════════════════════════════════════════
def _show_csv_map(df):
    """为含有 lon/lat 列的 CSV DataFrame 生成 Folium 地图"""
    try:
        import folium
        from streamlit_folium import st_folium

        # 识别坐标列名
        lon_col = next(
            (c for c in ['lon', 'longitude', 'lng'] if c in df.columns), None
        )
        lat_col = next(
            (c for c in ['lat', 'latitude'] if c in df.columns), None
        )

        if not lon_col or not lat_col:
            st.warning('未找到有效的经纬度列（需要 lon/lat 或 longitude/latitude）')
            st.dataframe(df, width='stretch')
            return

        # 坐标重复度分析
        with st.expander('\U0001f4ca 坐标重复度分析', expanded=False):
            coords_list = [
                (round(r[lon_col], 5), round(r[lat_col], 5))
                for _, r in df.iterrows()
            ]
            coord_counter = Counter(coords_list)
            unique_coords = len(coord_counter)
            total_points = len(coords_list)
            dup_ratio = (1 - unique_coords / total_points) * 100 if total_points > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric('总点数', total_points)
            col2.metric('唯一坐标数', unique_coords)
            col3.metric('重复率', f'{dup_ratio:.0f}%')

            if dup_ratio > 0:
                st.caption(f'平均每个坐标堆积 {total_points/unique_coords:.1f} 个点')
                dup_ranking = sorted(
                    coord_counter.items(), key=lambda x: x[1], reverse=True
                )
                rank_data = []
                for (lon, lat), count in dup_ranking[:10]:
                    rank_data.append({
                        '坐标': f'({lon}, {lat})',
                        '堆积数': count,
                    })
                st.dataframe(
                    pd.DataFrame(rank_data),
                    width='stretch',
                    hide_index=True,
                )

        # 地图中心
        center_lat = df[lat_col].mean()
        center_lon = df[lon_col].mean()

        # 天地图 Key
        TIANDITU_KEY = '4d4dc85287c003c8a18d5520b8920796'
        show_labels = st.sidebar.checkbox('显示中文注记', value=True)

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            control_scale=True,
            tiles=None,
        )

        # 天地图影像底图
        folium.TileLayer(
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
        ).add_to(m)

        if show_labels:
            folium.TileLayer(
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
            ).add_to(m)

        # 颜色映射
        color_map = {'Positive': 'green', 'Neutral': 'gray', 'Negative': 'red'}

        import random
        for _, row in df.iterrows():
            polarity = row.get('polarity', 'Neutral') if 'polarity' in df.columns else 'Neutral'
            color = color_map.get(str(polarity), 'blue')

            # 固定种子随机偏移
            id_val = str(row.get('id_e', row.get('id', '')))
            seed = hash(id_val) % 10000
            rng = random.Random(seed)
            lat = float(row[lat_col]) + rng.uniform(-0.0003, 0.0003)
            lon = float(row[lon_col]) + rng.uniform(-0.0003, 0.0003)

            # 构建 tooltip
            tooltip_parts = []
            if 'id_e' in df.columns:
                tooltip_parts.append(f"<b>ID:</b> {row['id_e']}")
            if 'poi' in df.columns:
                tooltip_parts.append(f"<b>POI:</b> {row['poi']}")
            if 'comments' in df.columns:
                tooltip_parts.append(f"<b>评论:</b> {row['comments']}")
            if 'score' in df.columns:
                tooltip_parts.append(f"<b>得分:</b> {row['score']}")
            if 'polarity' in df.columns:
                tooltip_parts.append(f"<b>极性:</b> {row['polarity']}")
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

        st_folium(m, width=800, height=500, key='csv_emotion_map')

        # 数据表格
        st.subheader('\U0001f4cb 数据表格')
        cols_to_show = [c for c in df.columns if c not in [lon_col, lat_col]]
        st.dataframe(df[cols_to_show], width='stretch')

    except Exception as map_err:
        import traceback
        st.warning(f'地图加载失败: {map_err}')
        st.text(traceback.format_exc())
        st.dataframe(df, width='stretch')


# ═══════════════════════════════════════════════════════════
# 辅助函数：GeoJSON 地图可视化
# ═══════════════════════════════════════════════════════════
def _show_geojson_map(data):
    """为 GeoJSON FeatureCollection 生成 Folium 地图"""
    st.subheader('\U0001f5fa 地图可视化')
    try:
        import folium
        from streamlit_folium import st_folium
        import geopandas as gpd

        # 移除 CRS 字段
        data_copy = {k: v for k, v in data.items() if k != 'crs'}
        gdf = gpd.GeoDataFrame.from_features(data_copy['features'])

        # ── 坐标重复度分析 ──
        with st.expander('\U0001f4ca 坐标重复度分析', expanded=False):
            coords_list = [
                (round(g.x, 5), round(g.y, 5))
                for g in gdf.geometry
            ]
            coord_counter = Counter(coords_list)
            unique_coords = len(coord_counter)
            total_points = len(coords_list)
            dup_ratio = (1 - unique_coords / total_points) * 100 if total_points > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric('总点数', total_points)
            col2.metric('唯一坐标数', unique_coords)
            col3.metric('重复率', f'{dup_ratio:.0f}%')

            if dup_ratio > 0:
                st.caption(f'平均每个坐标堆积 {total_points/unique_coords:.1f} 个点')
                dup_ranking = sorted(
                    coord_counter.items(), key=lambda x: x[1], reverse=True
                )
                rank_data = []
                for (lon, lat), count in dup_ranking:
                    pois = gdf[
                        (gdf.geometry.x.round(5) == lon) &
                        (gdf.geometry.y.round(5) == lat)
                    ]['poi' if 'poi' in gdf.columns else 'id_e'].unique()
                    rank_data.append({
                        '坐标': f'({lon}, {lat})',
                        '堆积数': count,
                        '涉及POI': ', '.join(pois[:4]) + ('...' if len(pois) > 4 else ''),
                    })
                st.dataframe(
                    pd.DataFrame(rank_data),
                    width='stretch',
                    hide_index=True,
                )

        # ── 地图 ──
        center_lat = gdf.geometry.y.mean()
        center_lon = gdf.geometry.x.mean()

        TIANDITU_KEY = '4d4dc85287c003c8a18d5520b8920796'
        show_labels = st.sidebar.checkbox('显示中文注记', value=True)

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            control_scale=True,
            tiles=None,
        )

        folium.TileLayer(
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
        ).add_to(m)

        if show_labels:
            folium.TileLayer(
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
            ).add_to(m)

        color_map = {'Positive': 'green', 'Neutral': 'gray', 'Negative': 'red'}

        import random
        for feature in data['features']:
            props = feature['properties']
            coords = feature['geometry']['coordinates']
            polarity = props.get('polarity', 'Neutral')
            color = color_map.get(str(polarity), 'blue')

            seed = hash(str(props.get('id_e', ''))) % 10000
            rng = random.Random(seed)
            lat = coords[1] + rng.uniform(-0.0003, 0.0003)
            lon = coords[0] + rng.uniform(-0.0003, 0.0003)

            tooltip_parts = []
            if 'id_e' in props:
                tooltip_parts.append(f"<b>ID:</b> {props['id_e']}")
            if 'poi' in props:
                tooltip_parts.append(f"<b>POI:</b> {props['poi']}")
            if 'comments' in props:
                tooltip_parts.append(f"<b>评论:</b> {props['comments']}")
            if 'score' in props:
                tooltip_parts.append(f"<b>得分:</b> {props['score']}")
            tooltip_parts.append(f"<b>极性:</b> {polarity}")
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

        st_folium(m, width=800, height=500, key='geojson_emotion_map')

        # 情绪分析图表
        if 'polarity' in gdf.columns:
            st.subheader('\U0001f4ca 情绪分析概览')
            c1, c2, c3 = st.columns(3)
            c1.metric('总记录数', len(gdf))
            c2.metric('正面', (gdf['polarity'] == 'Positive').sum())
            c3.metric('负面', (gdf['polarity'] == 'Negative').sum())

            import altair as alt
            df_plot = gdf[['polarity']].copy()
            chart = alt.Chart(df_plot).mark_bar().encode(
                x=alt.X('polarity:N', title='情绪极性', sort=['Positive', 'Neutral', 'Negative']),
                y=alt.Y('count()', title='数量'),
                color=alt.Color(
                    'polarity:N',
                    scale=alt.Scale(
                        domain=['Positive', 'Neutral', 'Negative'],
                        range=['#28a745', '#6c757d', '#dc3545']
                    ),
                    legend=None
                )
            ).properties(title='情绪极性分布', height=250)
            st.altair_chart(chart, width='stretch')

        # 数据表格
        st.subheader('\U0001f4cb 数据表格')
        st.dataframe(gdf.drop(columns=['geometry']), width='stretch')

    except Exception as map_err:
        import traceback
        st.warning(f'地图加载失败: {map_err}')
        st.text(traceback.format_exc())
        st.json(data)


# ═══════════════════════════════════════════════════════════
# 页面标题
# ═══════════════════════════════════════════════════════════
st.title('\U0001f5fa Emotion Map Viewer')
st.caption('通用地图可视化工具 — 支持 CSV / GeoJSON / JSON')

# ═══════════════════════════════════════════════════════════
# 侧边栏：数据源选择
# ═══════════════════════════════════════════════════════════
BASE_DIRS = {
    '📂 processed（处理结果）': 'data/processed',
    '📂 raw（原始数据）': 'data/raw',
}

folder_key = st.sidebar.selectbox('选择数据文件夹', list(BASE_DIRS.keys()))
folder_path = BASE_DIRS[folder_key]

if not os.path.exists(folder_path):
    st.warning(f'文件夹不存在: {folder_path}')
else:
    files = sorted([
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ])
    if not files:
        st.info('所选文件夹中没有文件。')
    else:
        file_choice = st.sidebar.selectbox('选择文件', files)
        file_path = os.path.join(folder_path, file_choice)
        st.write('**文件路径:**', file_path)

        ext = file_choice.lower().split('.')[-1]

        try:
            # ═══════════════════════════════════════════════
            # CSV / TSV 处理
            # ═══════════════════════════════════════════════
            if ext in ('csv', 'tsv'):
                sep = '\t' if ext == 'tsv' else ','
                df = pd.read_csv(file_path, sep=sep)

                # ── 情绪分析图表（如果有相关列） ──
                has_emotion_cols = any(
                    c in df.columns for c in ['polarity', 'score']
                )
                if has_emotion_cols:
                    st.subheader('\U0001f4ca 情绪分析概览')

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric('总记录数', len(df))
                    if 'polarity' in df.columns:
                        pos = (df['polarity'] == 'Positive').sum()
                        neu = (df['polarity'] == 'Neutral').sum()
                        neg = (df['polarity'] == 'Negative').sum()
                        c2.metric('正面', pos, delta=f'{pos/len(df)*100:.0f}%' if len(df) > 0 else '')
                        c3.metric('中性', neu)
                        c4.metric('负面', neg)
                    if 'score' in df.columns:
                        st.write(f"评分: 均值 **{df['score'].mean():.2f}** | "
                                 f"中位数 **{df['score'].median():.2f}** | "
                                 f"标准差 **{df['score'].std():.2f}**")

                    # 极性分布柱状图
                    if 'polarity' in df.columns:
                        import altair as alt
                        df_count = (
                            df['polarity'].value_counts()
                            .reset_index()
                        )
                        df_count.columns = ['polarity', 'count']
                        chart = alt.Chart(df_count).mark_bar().encode(
                            x=alt.X('polarity:N', title='情绪极性', sort=['Positive', 'Neutral', 'Negative']),
                            y=alt.Y('count:Q', title='数量'),
                            color=alt.Color(
                                'polarity:N',
                                scale=alt.Scale(
                                    domain=['Positive', 'Neutral', 'Negative'],
                                    range=['#28a745', '#6c757d', '#dc3545']
                                ),
                                legend=None
                            )
                        ).properties(title='情绪极性分布', height=250)
                        st.altair_chart(chart, width='stretch')

                    # 评分直方图
                    if 'score' in df.columns:
                        hist = alt.Chart(df).mark_bar().encode(
                            alt.X('score:Q', bin=alt.Bin(maxbins=20), title='情绪得分'),
                            alt.Y('count()', title='数量'),
                            color=alt.value('#4a90d9')
                        ).properties(title='情绪得分分布', height=250)
                        st.altair_chart(hist, width='stretch')

                # ── 地图可视化（如果有坐标列） ──
                has_coords = any(
                    c in df.columns for c in ['lon', 'lat', 'longitude', 'latitude']
                )
                if has_coords:
                    st.subheader('\U0001f5fa 地图可视化')
                    _show_csv_map(df)
                else:
                    st.subheader('\U0001f4cb 数据表格')
                    st.dataframe(df, width='stretch')

                # 下载按钮
                st.download_button(
                    '下载为 CSV',
                    df.to_csv(index=False).encode('utf-8'),
                    file_name=file_choice,
                    mime='text/csv'
                )

            # ═══════════════════════════════════════════════
            # GeoJSON / JSON 处理
            # ═══════════════════════════════════════════════
            elif ext in ('json', 'geojson'):
                with open(file_path, encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict) and data.get('type') == 'FeatureCollection':
                    _show_geojson_map(data)
                else:
                    st.json(data)

            # ═══════════════════════════════════════════════
            # 其他文件类型：纯文本展示
            # ═══════════════════════════════════════════════
            else:
                with open(file_path, encoding='utf-8', errors='replace') as f:
                    text = f.read()
                st.text_area('文件内容', text, height=400)

        except Exception as e:
            import traceback
            st.error(f'读取文件时出错: {e}')
            st.text(traceback.format_exc())

st.markdown('---')
st.caption('通过侧边栏选择文件夹和文件。支持 CSV/TSV/GeoJSON/JSON。'
           '带有坐标列的 CSV 也会自动生成地图视图。')


# run streamlit：streamlit run streamlit_app.py
