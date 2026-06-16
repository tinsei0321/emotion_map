"""最小化 pydeck tooltip 测试"""
import streamlit as st
import pydeck as pdk
import pandas as pd

st.set_page_config(page_title="Tooltip Test", layout="wide")

# 创建测试数据
df = pd.DataFrame({
    'lat': [30.7, 30.71, 30.69],
    'lon': [111.3, 111.31, 111.29],
    'name': ['点A-测试', '点B-解放路', '点C-天桥'],
    'value': [100, 200, 150],
    'desc': ['描述A：路灯问题', '描述B：噪音投诉', '描述C：交通拥堵'],
})

layer = pdk.Layer(
    'ScatterplotLayer',
    data=df,
    get_position=['lon', 'lat'],
    get_fill_color=[255, 100, 100, 200],
    get_radius=200,
    pickable=True,
    auto_highlight=True,
)

view_state = pdk.ViewState(latitude=30.7, longitude=111.3, zoom=12)
deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style='https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
)

# 设置 tooltip
deck.tooltip = {
    'html': '<b>{name}</b><br>Value: {value}<br><i>{desc}</i>',
    'style': {
        'backgroundColor': 'rgba(20,22,32,0.95)',
        'color': '#e0e0e0',
        'borderRadius': '6px',
        'padding': '8px 12px',
        'fontSize': '13px',
    },
}

st.title('Pydeck Tooltip 最小测试')
st.caption('悬停红点上应该看到 tooltip：ID + value + desc')

# 也显示原始 deck JSON 中的 tooltip
import json
j = json.loads(deck.to_json())
st.json({'tooltip_in_json': j.get('tooltip'), 'layer_data_keys': list(j['layers'][0]['data'][0].keys()) if j.get('layers') else 'N/A'})

st.pydeck_chart(deck, use_container_width=True)
