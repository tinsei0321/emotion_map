"""
情绪热点图 — 完整版
══════════════════════════════════════════════════════════════
1. 侧边栏加载文件（CSV / GeoJSON）
2. 可调参数生成热点图层
3. 天地图影像底图 + bootcdn CDN
"""
import json, os, re
import numpy as np
import pandas as pd
import streamlit as st
import folium
from folium.plugins import HeatMap
"""
情绪热点图 — 完整版
1. 侧边栏加载文件  2. 可调参数生成热点图层  3. 天地图底图 + bootcdn
"""
import json, os, re
import numpy as np; import pandas as pd; import streamlit as st
import folium; from folium.plugins import HeatMap

st.set_page_config(page_title='情绪热点图', layout='wide')
TIANDITU_KEY = '4d4dc85287c003c8a18d5520b8920796'

# ── 侧边栏：文件选择 ──
st.sidebar.header('📂 数据源')
folder = st.sidebar.selectbox('文件夹', ['data/processed', 'data/raw'])
if not os.path.exists(folder): st.sidebar.warning('文件夹不存在'); st.stop()
files = sorted([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])
if not files: st.sidebar.info('文件夹为空'); st.stop()
file_choice = st.sidebar.selectbox('文件', files)
file_path = os.path.join(folder, file_choice)

# ── 侧边栏：热点图参数 ──
st.sidebar.divider(); st.sidebar.header('🔥 参数')
mode = st.sidebar.radio('模式', ['冷热分布', '极性分布'])
radius = st.sidebar.slider('搜索半径', 3, 50, 15, 1)
blur = st.sidebar.slider('模糊度', 1, 50, 10, 1)
min_op = st.sidebar.slider('最小透明度', 0.0, 1.0, 0.4, 0.05)
show_labels = st.sidebar.checkbox('中文注记', True)
show_pts = st.sidebar.checkbox('叠加原点', False)

# 极性分布专用控制
if mode == '极性分布':
    st.sidebar.subheader('正面图层')
    show_pos = st.sidebar.checkbox('显示正面聚集', True)
    pos_op = st.sidebar.slider('正面透明度', 0.1, 1.0, 0.6, 0.05)
    st.sidebar.subheader('负面图层')
    show_neg = st.sidebar.checkbox('显示负面聚集', True)
    neg_op = st.sidebar.slider('负面透明度', 0.1, 1.0, 0.6, 0.05)

# ── 数据加载 ──
ext = file_choice.lower().split('.')[-1]; lats, lons, scores = [], [], []
if ext in ('csv','tsv'):
    df = pd.read_csv(file_path, sep='\t' if ext=='tsv' else ',')
    lc = next((c for c in ['lon','longitude','lng'] if c in df.columns), None)
    pc = next((c for c in ['lat','latitude'] if c in df.columns), None)
    if lc and pc:
        lats=df[pc].astype(float).tolist(); lons=df[lc].astype(float).tolist()
    elif 'coordinate' in df.columns:
        for _,r in df.iterrows():
            m=re.findall(r'[\d.]+',str(r['coordinate']))
            if len(m)>=2: lons.append(float(m[0])); lats.append(float(m[1]))
    scores=df['score'].astype(float).tolist() if 'score' in df.columns else [0.5]*len(lats)
elif ext in ('json','geojson'):
    with open(file_path,encoding='utf-8') as f: data=json.load(f)
    if isinstance(data,dict) and data.get('type')=='FeatureCollection':
        for f in data['features']:
            c=f['geometry']['coordinates']; lons.append(c[0]); lats.append(c[1])
            scores.append(float(f['properties'].get('score',0.5)))

st.title('🔥 情绪热点图')
st.caption(f'`{file_choice}` — {len(lats)} 点')
if not lats: st.error('无法提取坐标'); st.stop()

# ── 地图 ──
m=folium.Map(location=[float(np.mean(lats)),float(np.mean(lons))],zoom_start=13,
             tiles=None,control_scale=True)
folium.TileLayer(tiles=f'https://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&'
    f'REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&'
    f'FORMAT=tiles&TILEMATRIX={{z}}&TILEROW={{y}}&TILECOL={{x}}&tk={TIANDITU_KEY}',
    attr='天地图',name='天地图影像',max_zoom=18).add_to(m)
if show_labels:
    folium.TileLayer(tiles=f'https://t0.tianditu.gov.cn/cva_w/wmts?SERVICE=WMTS&'
        f'REQUEST=GetTile&VERSION=1.0.0&LAYER=cva&STYLE=default&TILEMATRIXSET=w&'
        f'FORMAT=tiles&TILEMATRIX={{z}}&TILEROW={{y}}&TILECOL={{x}}&tk={TIANDITU_KEY}',
        attr='天地图注记',name='天地图注记',max_zoom=18).add_to(m)

# ── 热点图层 ──
if mode == '冷热分布':
    # 所有点等权重，只反映密度（与情绪得分无关）
    heat_data = [[lat, lon, 1.0] for lat, lon in zip(lats, lons)]
    HeatMap(heat_data, radius=radius, blur=blur, min_opacity=min_op,
            gradient={0.0: '#cce5ff', 0.3: '#ffffb2', 0.6: '#fdae61',
                      0.8: '#f46d43', 1.0: '#a50026'}).add_to(m)
    st.markdown('<div style="position:fixed;bottom:28px;right:14px;z-index:9999;'
        'pointer-events:none;background:rgba(0,0,0,.6);padding:10px 14px;border-radius:8px;">'
        '<b style="color:#fff;">📊 冷热分布</b><br>'
        '<span style="display:inline-block;width:120px;height:10px;border-radius:5px;'
        'background:linear-gradient(90deg,#cce5ff,#ffffb2,#fdae61,#f46d43,#a50026);"></span><br>'
        '<span style="font-size:.7rem;color:#aaa;">冷(稀疏)</span>'
        '<span style="font-size:.7rem;color:#aaa;float:right;">热(密集)</span></div>',
        unsafe_allow_html=True)
else:
    # 正面图层：仅正面点，权重=score，翠绿→黄
    pos_data = [[lat, lon, s] for lat, lon, s in zip(lats, lons, scores) if s >= 0.7]
    if show_pos and pos_data:
        HeatMap(pos_data, radius=radius, blur=blur, min_opacity=pos_op,
                gradient={0.0: '#004529', 0.3: '#238b45', 0.6: '#74c476',
                          0.85: '#c7e9c0', 1.0: '#ffffcc'},
                name='正面聚集').add_to(m)
    # 负面图层：仅负面点，权重=(1-score)，灰→黄
    neg_data = [[lat, lon, 1 - s] for lat, lon, s in zip(lats, lons, scores) if s <= 0.3]
    if show_neg and neg_data:
        HeatMap(neg_data, radius=radius, blur=blur, min_opacity=neg_op,
                gradient={0.0: '#252525', 0.3: '#636363', 0.6: '#bdbdbd',
                          0.85: '#f0f0f0', 1.0: '#ffffcc'},
                name='负面聚集').add_to(m)
    # 图例
    leg_parts = []
    if show_pos:
        leg_parts.append(f'<span style="color:#238b45;">■</span>'
                        f'<span style="font-size:.75rem;color:#ccc;"> 正面({len(pos_data)})</span><br>')
    if show_neg:
        leg_parts.append(f'<span style="color:#636363;">■</span>'
                        f'<span style="font-size:.75rem;color:#ccc;"> 负面({len(neg_data)})</span><br>')
    if leg_parts:
        st.markdown('<div style="position:fixed;bottom:28px;right:14px;z-index:9999;'
            'pointer-events:none;background:rgba(0,0,0,.6);padding:10px 14px;border-radius:8px;">'
            f'<b style="color:#fff;">😊😞 极性分布</b><br>{"".join(leg_parts)}</div>',
            unsafe_allow_html=True)

if show_pts:
    for lat,lon,s in zip(lats,lons,scores):
        c='#4caf50' if s>=.7 else ('#f44336' if s<=.3 else '#9e9e9e')
        folium.CircleMarker([lat,lon],radius=3,color=c,fill=True,fill_opacity=.4,weight=.5).add_to(m)

# ── 渲染（替换 CDN）──
html=m.get_root().render()
html=html.replace('cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js',
                  'cdn.bootcdn.net/ajax/libs/leaflet/1.9.3/leaflet.js')
html=html.replace('cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css',
                  'cdn.bootcdn.net/ajax/libs/leaflet/1.9.3/leaflet.css')
html=html.replace('cdn.jsdelivr.net/gh/python-visualization/folium@main/folium/templates/leaflet_heat.min.js',
                  'cdn.bootcdn.net/ajax/libs/leaflet.heat/0.2.0/leaflet-heat.js')
st.components.v1.html(html, height=700)

with st.expander('📊 统计'):
    c1,c2,c3=st.columns(3)
    c1.metric('总数',len(lats)); c2.metric('正面≥.7',sum(1 for s in scores if s>=.7)); c3.metric('负面≤.3',sum(1 for s in scores if s<=.3))
