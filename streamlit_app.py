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

                        gdf = gpd.GeoDataFrame.from_features(data['features'])

                        center_lat = gdf.geometry.y.mean()
                        center_lon = gdf.geometry.x.mean()

                        # 使用高德地图底图（适合中国大陆，无需token）
                        m = folium.Map(
                            location=[center_lat, center_lon],
                            zoom_start=12,
                            control_scale=True,
                        )
                        m.tiles = None

                        # 高德矢量图
                        folium.TileLayer(
                            tiles='https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
                            attr='高德地图',
                            name='高德矢量',
                            max_zoom=18,
                        ).add_to(m)

                        # 高德影像图
                        folium.TileLayer(
                            tiles='https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',
                            attr='高德地图',
                            name='高德影像',
                            max_zoom=18,
                        ).add_to(m)

                        folium.LayerControl().add_to(m)

                        color_map = {'Positive': 'green', 'Neutral': 'gray', 'Negative': 'red'}

                        # 直接用 folium.GeoJson 加载全部点
                        def style_function(feature):
                            polarity = feature['properties'].get('polarity', 'Neutral')
                            color = color_map.get(polarity, 'blue')
                            return {
                                'fillColor': color,
                                'color': color,
                                'fillOpacity': 0.7,
                                'weight': 2,
                                'radius': 8,
                            }

                        folium.GeoJson(
                            data,
                            name='情绪点',
                            style_function=style_function,
                            tooltip=folium.GeoJsonTooltip(
                                fields=['id_e', 'comments', 'score', 'polarity'],
                                aliases=['ID', '评论', '得分', '极性'],
                                max_width=300,
                            ),
                        ).add_to(m)

                        st_folium(m, width=800, height=500)

                        st.subheader('\U0001f4cb 数据表格')
                        st.dataframe(gdf.drop(columns=['geometry']))

                    except Exception as map_err:
                        st.warning(f'地图加载失败，显示JSON格式: {map_err}')
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

