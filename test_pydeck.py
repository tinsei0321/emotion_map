"""pydeck 最小测试 — 验证底图能否渲染"""
import streamlit as st
import pydeck as pdk

st.set_page_config(page_title='pydeck test')
st.write('测试 pydeck 地图渲染...')

view = pdk.ViewState(latitude=30.71, longitude=111.29, zoom=12)

deck = pdk.Deck(
    initial_view_state=view,
    map_provider='mapbox',
    map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=[{'lat': 30.71, 'lon': 111.29}],
            get_position=['lon', 'lat'],
            get_fill_color=[29, 186, 212, 255],
            get_radius=200,
            pickable=True,
        )
    ],
)

st.pydeck_chart(deck, use_container_width=True, height=600)
st.caption('如果看到宜昌地图+一个青蓝色圆点，pydeck 正常')
