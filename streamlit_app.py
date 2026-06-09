import os
import json

import pandas as pd
import streamlit as st


st.set_page_config(page_title='Emotion Map Viewer')
st.title('Emotion Map Viewer')

BASE_DIRS = {
    'processed': 'data/processed',
}

folder_key = st.sidebar.selectbox('选择数据文件夹', list(BASE_DIRS.keys()))
folder_path = BASE_DIRS[folder_key]

if not os.path.exists(folder_path):
    st.warning(f'文件夹不存在: {folder_path}')
else:
    files = sorted([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
    if not files:
        st.info('所选文件夹中没有文件。')
    else:
        file_choice = st.sidebar.selectbox('选择文件', files)
        file_path = os.path.join(folder_path, file_choice)
        st.write('**文件路径:**', file_path)

        ext = file_choice.lower().split('.')[-1]
        try:
            if ext in ('csv', 'tsv'):
                sep = chr(9) if ext == 'tsv' else ','
                df = pd.read_csv(file_path, sep=sep)
                st.dataframe(df)
                st.download_button('下载为 CSV', df.to_csv(index=False).encode('utf-8'), file_name=file_choice, mime='text/csv')
            elif ext in ('json', 'geojson'):
                with open(file_path, encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict) and data.get('type') == 'FeatureCollection':
                    st.subheader('\U0001f5fa 地图可视化')
                    try:
                        import folium
                        from streamlit_folium import st_folium
                        import geopandas as gpd

                        # 移除 CRS 字段（部分 GeoJSON 的 CRS 可能导致兼容问题）
                        data_copy = {k: v for k, v in data.items() if k != 'crs'}

                        gdf = gpd.GeoDataFrame.from_features(data_copy['features'])

                        center_lat = gdf.geometry.y.mean()
                        center_lon = gdf.geometry.x.mean()

                        # ───── 底图配置 ─────
                        # 获取 Key：https://console.tianditu.gov.cn → 创建应用 → 应用类型选"浏览器端"
                        TIANDITU_KEY = '4d4dc85287c003c8a18d5520b8920796'

                        # Streamlit 侧边栏开关：控制中文注记显示
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

                        # 天地图中文注记（由侧边栏开关控制）
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
                        # 使用基于 id_e 的固定种子，保证每次渲染偏移一致
                        for feature in data['features']:
                            props = feature['properties']
                            coords = feature['geometry']['coordinates']
                            polarity = props.get('polarity', 'Neutral')
                            color = color_map.get(polarity, 'blue')

                            # 同坐标点添加微小随机偏移（约 ±30m），避免完全重叠
                            seed = hash(props.get('id_e', '')) % 10000
                            rng = random.Random(seed)
                            lat = coords[1] + rng.uniform(-0.0003, 0.0003)
                            lon = coords[0] + rng.uniform(-0.0003, 0.0003)

                            tooltip_html = (
                                f"<b>ID:</b> {props.get('id_e', '')}<br>"
                                f"<b>POI:</b> {props.get('poi', '')}<br>"
                                f"<b>评论:</b> {props.get('comments', '')}<br>"
                                f"<b>得分:</b> {props.get('score', '')}<br>"
                                f"<b>极性:</b> {polarity}"
                            )

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

                        st_folium(m, width=800, height=500, key='emotion_map')

                        st.subheader('\U0001f4cb 数据表格')
                        st.dataframe(gdf.drop(columns=['geometry']))

                    except Exception as map_err:
                        import traceback
                        st.warning(f'地图加载失败: {map_err}')
                        st.text(traceback.format_exc())
                        st.json(data)
                else:
                    st.json(data)
            else:
                with open(file_path, encoding='utf-8', errors='replace') as f:
                    text = f.read()
                st.text_area('文件内容', text, height=400)
        except Exception as e:
            st.error(f'读取文件时出错: {e}')

st.markdown('---')
st.caption('通过侧边栏选择文件夹并打开文件。支持 CSV/TSV/JSON/纯文本。')

