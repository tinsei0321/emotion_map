"""
test_scripts_heatmap.py
══════════════════════════════════════════════════════════════
独立热点图测试脚本 — 不依赖 streamlit_app_v2，纯净测试环境。
"""
import json
import os
import re
import numpy as np
import pandas as pd
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

st.set_page_config(page_title='热点图测试', layout='wide')

# 工作目录
try:
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
except Exception:
    pass  # streamlit 环境下 __file__ 可能不可用

TIANDITU_KEY = '4d4dc85287c003c8a18d5520b8920796'

# ═══════════════════════════════════════════════════════════
# 数据加载
# ═══════════════════════════════════════════════════════════
st.sidebar.header('📂 数据源')
folder = st.sidebar.selectbox('文件夹', ['data/processed', 'data/raw'])
folder_path = folder
files = sorted([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
file_choice = st.sidebar.selectbox('文件', files)
file_path = os.path.join(folder_path, file_choice)

st.sidebar.divider()

# ═══════════════════════════════════════════════════════════
# 参数设置
# ═══════════════════════════════════════════════════════════
st.sidebar.header('🔥 热点图参数')

mode = st.sidebar.radio('模式', ['冷热分布 (Hot/Cold)', '极性分布 (Polarity)'])

st.sidebar.subheader('核心参数')
radius = st.sidebar.slider('搜索半径 (radius)', 3, 50, 15, 1,
                           help='每个点的影响范围（像素），越大越平滑')
blur = st.sidebar.slider('模糊度 (blur)', 1, 50, 10, 1,
                         help='边缘模糊程度，越大越柔和')
min_opacity = st.sidebar.slider('最小透明度 (min_opacity)', 0.0, 1.0, 0.4, 0.05,
                                help='低密度区域可见度')
max_zoom_val = st.sidebar.slider('最大渲染级别 (max_zoom)', 1, 20, 18, 1,
                                 help='超过此级别不再细化')

st.sidebar.subheader('冷热分布配色')
col_cold = st.sidebar.color_picker('冷点色', '#0000ff')
col_mid1 = st.sidebar.color_picker('过渡色1', '#00ffff')
col_mid2 = st.sidebar.color_picker('过渡色2', '#00ff00')
col_mid3 = st.sidebar.color_picker('过渡色3', '#ffff00')
col_hot = st.sidebar.color_picker('热点色', '#ff0000')

st.sidebar.subheader('极性分布配色')
col_pos_low = st.sidebar.color_picker('正面-低', '#a5d6a7')
col_pos_mid = st.sidebar.color_picker('正面-中', '#4caf50')
col_pos_high = st.sidebar.color_picker('正面-高', '#1b5e20')
col_neg_low = st.sidebar.color_picker('负面-低', '#ef9a9a')
col_neg_mid = st.sidebar.color_picker('负面-中', '#f44336')
col_neg_high = st.sidebar.color_picker('负面-高', '#b71c1c')

st.sidebar.subheader('显示选项')
show_labels = st.sidebar.checkbox('中文注记', True)
show_points = st.sidebar.checkbox('叠加原始点位', False,
                                  help='在热力图下方叠加半透明点标记')

# ═══════════════════════════════════════════════════════════
# 数据提取
# ═══════════════════════════════════════════════════════════
ext = file_choice.lower().split('.')[-1]
lats, lons, scores, props_list = [], [], [], []

if ext in ('csv', 'tsv'):
    df = pd.read_csv(file_path, sep='\t' if ext == 'tsv' else ',')
    lon_c = next((c for c in ['lon', 'longitude', 'lng'] if c in df.columns), None)
    lat_c = next((c for c in ['lat', 'latitude'] if c in df.columns), None)
    if lon_c and lat_c:
        lats = df[lat_c].astype(float).tolist()
        lons = df[lon_c].astype(float).tolist()
        scores = df['score'].astype(float).tolist() if 'score' in df.columns else [0.5]*len(df)
        props_list = df.to_dict('records')
    elif 'coordinate' in df.columns:
        # 解析 "(lon, lat)" 元组格式
        import re
        for _, row in df.iterrows():
            m = re.findall(r'[\d.]+', str(row['coordinate']))
            if len(m) >= 2:
                lons.append(float(m[0]))
                lats.append(float(m[1]))
            scores.append(float(row.get('score', 0.5)))
            props_list.append(row.to_dict())
elif ext in ('json', 'geojson'):
    with open(file_path, encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict) and data.get('type') == 'FeatureCollection':
        for feat in data['features']:
            c = feat['geometry']['coordinates']
            lons.append(c[0])
            lats.append(c[1])
            scores.append(float(feat['properties'].get('score', 0.5)))
            props_list.append(feat['properties'])

# ═══════════════════════════════════════════════════════════
# 地图渲染
# ═══════════════════════════════════════════════════════════
st.title('🔥 情绪热点图测试')
st.caption(f'数据: `{file_choice}` | 共 **{len(lats)}** 个点')

if not lats:
    st.error('无法提取坐标数据')
    st.stop()

center = [float(np.mean(lats)), float(np.mean(lons))]

# 创建地图
m = folium.Map(location=center, zoom_start=13, tiles=None, control_scale=True)

# 天地图底图
folium.TileLayer(
    tiles=f'https://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile'
          f'&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w'
          f'&FORMAT=tiles&TILEMATRIX={{z}}&TILEROW={{y}}&TILECOL={{x}}&tk={TIANDITU_KEY}',
    attr='天地图', name='天地图影像', max_zoom=18, overlay=False,
).add_to(m)

if show_labels:
    folium.TileLayer(
        tiles=f'https://t0.tianditu.gov.cn/cva_w/wmts?SERVICE=WMTS&REQUEST=GetTile'
              f'&VERSION=1.0.0&LAYER=cva&STYLE=default&TILEMATRIXSET=w'
              f'&FORMAT=tiles&TILEMATRIX={{z}}&TILEROW={{y}}&TILECOL={{x}}&tk={TIANDITU_KEY}',
        attr='天地图注记', name='天地图注记', max_zoom=18,
    ).add_to(m)

# 根据模式渲染
if '冷热' in mode:
    # 冷热分布
    heat_data = [[lat, lon, s] for lat, lon, s in zip(lats, lons, scores)]
    gradient = {0.0: col_cold, 0.25: col_mid1, 0.5: col_mid2, 0.75: col_mid3, 1.0: col_hot}
    HeatMap(heat_data, name='情绪热度', radius=radius, blur=blur,
            min_opacity=min_opacity, max_zoom=max_zoom_val,
            gradient=gradient).add_to(m)

    # 图例
    st.markdown(f"""
    <div style="position:fixed;bottom:28px;right:14px;z-index:9999;pointer-events:none;
    background:rgba(0,0,0,0.6);padding:10px 14px;border-radius:8px;">
    <b style="color:#fff;">🔥 冷热分布</b><br>
    <span style="display:inline-block;width:100px;height:10px;border-radius:5px;
    background:linear-gradient(90deg,{col_cold},{col_mid1},{col_mid2},{col_mid3},{col_hot});"></span><br>
    <span style="font-size:0.7rem;color:#aaa;">冷</span>
    <span style="font-size:0.7rem;color:#aaa;float:right;">热</span>
    </div>
    """, unsafe_allow_html=True)
else:
    # 极性分布
    pos_data = [[lat, lon, s] for lat, lon, s in zip(lats, lons, scores) if s >= 0.7]
    neg_data = [[lat, lon, 1 - s] for lat, lon, s in zip(lats, lons, scores) if s <= 0.3]
    if pos_data:
        HeatMap(pos_data, name='正面聚集', radius=radius, blur=blur,
                min_opacity=min_opacity, max_zoom=max_zoom_val,
                gradient={0.4: col_pos_low, 0.7: col_pos_mid, 1.0: col_pos_high}).add_to(m)
    if neg_data:
        HeatMap(neg_data, name='负面聚集', radius=radius, blur=blur,
                min_opacity=min_opacity, max_zoom=max_zoom_val,
                gradient={0.4: col_neg_low, 0.7: col_neg_mid, 1.0: col_neg_high}).add_to(m)

    st.markdown(f"""
    <div style="position:fixed;bottom:28px;right:14px;z-index:9999;pointer-events:none;
    background:rgba(0,0,0,0.6);padding:10px 14px;border-radius:8px;">
    <b style="color:#fff;">😊😞 极性分布</b><br>
    <span style="color:{col_pos_mid};">■</span><span style="font-size:0.75rem;color:#ccc;"> 正面聚集 ({len(pos_data)}点)</span><br>
    <span style="color:{col_neg_mid};">■</span><span style="font-size:0.75rem;color:#ccc;"> 负面聚集 ({len(neg_data)}点)</span>
    </div>
    """, unsafe_allow_html=True)

if show_points:
    for lat, lon, s in zip(lats, lons, scores):
        c = '#4caf50' if s >= 0.7 else ('#f44336' if s <= 0.3 else '#9e9e9e')
        folium.CircleMarker([lat, lon], radius=3, color=c, fill=True,
                           fill_opacity=0.5, weight=0.5).add_to(m)

# ── 渲染：用 st.components.v1.html 替代 st_folium，替换 CDN ──
html = m.get_root().render()
# 替换 jsdelivr CDN 为 unpkg（国内可访问）
html = html.replace('https://cdn.jsdelivr.net/npm/leaflet', 'https://unpkg.com/leaflet')
html = html.replace('https://cdn.jsdelivr.net/gh/python-visualization/folium@main/folium/templates/leaflet_heat.min.js',
                    'https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js')
html = html.replace('https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css',
                    'https://unpkg.com/leaflet@1.9.3/dist/leaflet.css')
st.components.v1.html(html, height=700)

# 数据统计
with st.expander('📊 数据统计'):
    c1, c2, c3 = st.columns(3)
    c1.metric('总点数', len(lats))
    c2.metric('正面(≥0.7)', sum(1 for s in scores if s >= 0.7))
    c3.metric('负面(≤0.3)', sum(1 for s in scores if s <= 0.3))
    st.write(f'得分均值: **{np.mean(scores):.2f}** | 中位数: **{np.median(scores):.2f}**')
