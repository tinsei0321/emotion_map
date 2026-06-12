"""
空间分析引擎 — 底图渲染 / 点状标记 / 热点分析 / 空间聚合 + CDN 替换
══════════════════════════════════════════════════════════════
为情绪地图提供空间可视化与空间分析能力（MVP：热点分析 / 缓冲区分析 / 行政单元聚合）。
"""
import folium
import numpy as np

from .config import (
    TIANDITU_IMG_URL, TIANDITU_CVA_URL, DEFAULT_CENTER, DEFAULT_ZOOM,
    FOLIUM_COLOR_MAP, SCORE_POSITIVE, SCORE_NEGATIVE,
    HEATMAP_DEFAULTS, GRADIENT_HOTCOLD, GRADIENT_POSITIVE, GRADIENT_NEGATIVE,
    CDN_REPLACEMENTS,
)


def create_base_map(lats=None, lons=None, show_labels=True,
                    center=None, zoom_start=None) -> folium.Map:
    """
    创建带天地图底图的基础地图。

    参数:
        lats, lons: 坐标列表（用于自动计算中心点）
        show_labels: 是否叠加中文注记
        center: 手动指定中心 [lat, lon]
        zoom_start: 手动指定缩放级别
    """
    if center is None:
        if lats and lons:
            center = [float(np.mean(lats)), float(np.mean(lons))]
        else:
            center = DEFAULT_CENTER

    m = folium.Map(
        location=center,
        zoom_start=zoom_start or DEFAULT_ZOOM,
        tiles=None,
        control_scale=True,
    )

    folium.TileLayer(
        tiles=TIANDITU_IMG_URL,
        attr='天地图', name='天地图影像', max_zoom=18,
    ).add_to(m)

    if show_labels:
        folium.TileLayer(
            tiles=TIANDITU_CVA_URL,
            attr='天地图注记', name='天地图注记',
            overlay=True, show=True, max_zoom=18,
        ).add_to(m)

    return m


def add_point_layer(m: folium.Map, lats, lons, scores,
                    props_list=None, jitter=True):
    """
    添加点状情绪标记层（支持五级极性自动识别）。

    props_list 支持两种格式:
      1. dict 列表: [{'id_e':..., 'comments':..., 'polarity':...}, ...]
      2. GeoJSON feature 列表: [{'properties':{...}}, ...]

    极性获取优先级: props 中的 polarity 列 > 根据 score 计算（向后兼容）
    """
    import random
    for i, (lat, lon, s) in enumerate(zip(lats, lons, scores)):
        # 优先从 props 读取 polarity，否则从 score 计算
        polarity = None
        if props_list and i < len(props_list):
            p = props_list[i]
            props = p.get('properties', p)  # 兼容 GeoJSON feature
            polarity = props.get('polarity')

        if polarity is None:
            # 向后兼容：从 score 计算五级极性
            if s >= 0.80:
                polarity = 'Very Positive'
            elif s >= 0.60:
                polarity = 'Positive'
            elif s >= 0.40:
                polarity = 'Neutral'
            elif s >= 0.20:
                polarity = 'Negative'
            else:
                polarity = 'Very Negative'

        color = FOLIUM_COLOR_MAP.get(polarity, 'blue')

        if jitter and props_list:
            id_str = str(i)
            if i < len(props_list):
                p = props_list[i]
                props = p.get('properties', p)
                id_str = str(props.get('id_e', props.get('id', i)))
            seed = hash(id_str) % 10000
            rng = random.Random(seed)
            lat += rng.uniform(-0.0003, 0.0003)
            lon += rng.uniform(-0.0003, 0.0003)

        tooltip_parts = []
        if props_list and i < len(props_list):
            p = props_list[i]
            props = p.get('properties', p)
            for key in ['id_e', 'poi', 'comments', 'score', 'polarity',
                        'category', 'target_type', 'target_detail']:
                if key in props and props[key]:
                    tooltip_parts.append(f"<b>{key}:</b> {props[key]}")
        tooltip_html = '<br>'.join(tooltip_parts) if tooltip_parts else f'点 {i}'

        folium.CircleMarker(
            location=[lat, lon], radius=8,
            fill=True, fill_color=color, fill_opacity=0.7,
            color=color, weight=2,
            tooltip=folium.Tooltip(tooltip_html, max_width=300),
        ).add_to(m)


def add_heatmap_layer(m: folium.Map, lats, lons, scores,
                      mode='hotcold', radius=None, blur=None,
                      min_opacity=None, pos_opacity=0.6, neg_opacity=0.6,
                      show_pos=True, show_neg=True):
    """
    添加热点图层。

    参数:
        m: folium 地图对象
        mode: 'hotcold' 冷热分布 / 'polarity' 极性分布
        radius, blur, min_opacity: 热力图参数
        pos_opacity, neg_opacity: 极性模式下正/负面透明度
        show_pos, show_neg: 极性模式下各图层开关
    """
    from folium.plugins import HeatMap

    radius = radius or HEATMAP_DEFAULTS['radius']
    blur = blur or HEATMAP_DEFAULTS['blur']
    min_opacity = min_opacity or HEATMAP_DEFAULTS['min_opacity']

    if mode == 'hotcold':
        # 所有点等权重 → 纯密度分布
        heat_data = [[lat, lon, 1.0] for lat, lon in zip(lats, lons)]
        HeatMap(heat_data, radius=radius, blur=blur,
                min_opacity=min_opacity, gradient=GRADIENT_HOTCOLD,
                name='冷热分布').add_to(m)

    else:  # polarity
        if show_pos:
            pos_data = [[lat, lon, s] for lat, lon, s in zip(lats, lons, scores)
                        if s >= SCORE_POSITIVE]
            if pos_data:
                HeatMap(pos_data, radius=radius, blur=blur,
                        min_opacity=pos_opacity, gradient=GRADIENT_POSITIVE,
                        name='正面聚集').add_to(m)
        if show_neg:
            neg_data = [[lat, lon, 1 - s] for lat, lon, s in zip(lats, lons, scores)
                        if s <= SCORE_NEGATIVE]
            if neg_data:
                HeatMap(neg_data, radius=radius, blur=blur,
                        min_opacity=neg_opacity, gradient=GRADIENT_NEGATIVE,
                        name='负面聚集').add_to(m)


def render_html(folium_map: folium.Map) -> str:
    """渲染 Folium 地图为 HTML，并替换 CDN 为国内镜像"""
    html = folium_map.get_root().render()
    for old, new in CDN_REPLACEMENTS.items():
        html = html.replace(old, new)
    return html
