"""
空间分析引擎 — 底图渲染 / 点状标记 / 热点分析 / 空间聚合 + CDN 替换
══════════════════════════════════════════════════════════════
为情绪地图提供空间可视化与空间分析能力（MVP：热点分析 / 缓冲区分析 / 行政单元聚合）。
"""
import folium
import folium.plugins
import numpy as np
import random

from .config import (
    TIANDITU_IMG_URL, TIANDITU_CVA_URL, DEFAULT_CENTER, DEFAULT_ZOOM,
    FOLIUM_COLOR_MAP, SCORE_POSITIVE, SCORE_NEGATIVE,
    HEATMAP_DEFAULTS, GRADIENT_HOTCOLD, GRADIENT_POSITIVE, GRADIENT_NEGATIVE,
    CDN_REPLACEMENTS, MAX_DISPLAY_POINTS,
)
from core.tracker import track, TrackContext, trace_log, trace_error, register_track_id


@track("MOD_MAP.F_001", track_args=False)
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


@track("MOD_MAP.F_002", track_args=False)
def add_point_layer(m: folium.Map, lats, lons, scores,
                    props_list=None, jitter=True, max_points=None):
    """
    添加点状情绪标记层（支持五级极性自动识别）。

    props_list 支持两种格式:
      1. dict 列表: [{'id_e':..., 'comments':..., 'polarity':...}, ...]
      2. GeoJSON feature 列表: [{'properties':{...}}, ...]

    极性获取优先级: props 中的 polarity 列 > 根据 score 计算（向后兼容）

    大数据优化:
      - 点数 > max_points 时随机采样（seed=42，保证同数据多次渲染一致）
      - 点数 > 1000 时使用 MarkerCluster 替代逐点 CircleMarker
    """
    max_points = max_points or MAX_DISPLAY_POINTS
    n = len(lats)

    # ── 大数据采样（固定种子 seed=42，保证同数据多次渲染一致）──
    if n > max_points:
        indices = random.Random(42).sample(range(n), max_points)
        lats = [lats[i] for i in indices]
        lons = [lons[i] for i in indices]
        scores = [scores[i] for i in indices]
        if props_list:
            props_list = [props_list[i] for i in indices]

    n_render = len(lats)

    # ── 大数据使用 MarkerCluster 提升渲染性能 ──
    if n_render > 1000:
        cluster = folium.plugins.MarkerCluster(name='数据点').add_to(m)
        target = cluster
    else:
        target = m

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

        color = FOLIUM_COLOR_MAP.get(polarity, '#00e676')

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

        tooltip = folium.Tooltip(tooltip_html, max_width=300)

        # 外层光晕：大半径 + 低透明度 = 柔和扩散光，提升深色底图上的可见性
        folium.CircleMarker(
            location=[lat, lon], radius=13,
            fill=True, fill_color=color, fill_opacity=0.12,
            color='transparent', weight=0,
            tooltip=tooltip,
        ).add_to(target)

        # 内层实心点：白色描边 + 高填充透明度 = 清晰边界，与底图分离
        folium.CircleMarker(
            location=[lat, lon], radius=7,
            fill=True, fill_color=color, fill_opacity=0.92,
            color='#ffffff', weight=2,
            tooltip=tooltip,
        ).add_to(target)


@track("MOD_MAP.F_003", track_args=False)
def add_boundary_layer(m: folium.Map, geojson_path: str = None,
                     geojson_data: dict = None, name: str = '分析范围',
                     color: str = '#ff6b35', weight: int = 2,
                     fill_opacity: float = 0.08):
    """
    在地图上叠加行政区划边界图层。

    参数:
        m: folium 地图对象
        geojson_path: GeoJSON 文件路径
        geojson_data: GeoJSON dict（与 geojson_path 二选一）
        name: 图层名称
        color: 边界颜色
        weight: 线宽
        fill_opacity: 填充透明度
    """
    if geojson_data:
        data = geojson_data
    elif geojson_path:
        import json
        with open(geojson_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        return

    folium.GeoJson(
        data,
        name=name,
        style_function=lambda x: {
            'fillColor': color,
            'color': color,
            'weight': weight,
            'fillOpacity': fill_opacity,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['name'],
            aliases=['区域: '],
            localize=True,
        ),
    ).add_to(m)


@track("MOD_MAP.F_004", track_args=False)
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


@track("MOD_MAP.F_005", track_args=False)
def render_html(folium_map: folium.Map) -> str:
    """渲染 Folium 地图为 HTML，并替换 CDN 为国内镜像"""
    html = folium_map.get_root().render()
    for old, new in CDN_REPLACEMENTS.items():
        html = html.replace(old, new)
    return html

# ── 追踪 ID 注册表 ──
register_track_id("MOD_MAP.F_001", "创建天地图底图")
register_track_id("MOD_MAP.F_002", "添加情绪点标记层（五级极性 + 双层光晕）")
register_track_id("MOD_MAP.F_003", "添加行政区划边界叠加层")
register_track_id("MOD_MAP.F_004", "添加热点图层（冷热分布/极性分布）")
register_track_id("MOD_MAP.F_005", "渲染 Folium 地图为 HTML（CDN 替换）")
