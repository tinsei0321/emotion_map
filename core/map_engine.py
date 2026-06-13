"""
空间分析引擎 — pydeck GPU 渲染地图
"""
import pydeck as pdk
import numpy as np
import pandas as pd
import random

from .config import (
    DEFAULT_CENTER, DEFAULT_ZOOM,
    SCORE_POSITIVE, SCORE_NEGATIVE,
    POLARITY_RGBA, MAX_DISPLAY_POINTS,
)
from core.tracker import track, TrackContext, trace_log, register_track_id


# ── 底图样式 ──
# CartoDB basemaps（免费无需 API Key，数据源 OpenStreetMap）
# Tianditu（天地图，需 API Key，运行时动态生成 MapLibre 样式）
MAP_STYLES = {
    'carto_dark':    'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
    'carto_light':   'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
    'carto_voyager': 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
}

MAP_STYLE_LABELS = {
    'carto_dark':        'CartoDB 深色',
    'carto_light':       'CartoDB 浅色',
    'carto_voyager':     'CartoDB 标准',
    'tianditu_nolabel':  '天地图 无注记 (预览)',
    'tianditu_label':    '天地图 有注记 (预览)',
}

# 底图预览色（用于对话框缩略图示意）
MAP_STYLE_PREVIEW_COLORS = {
    'carto_dark':        '#1a1a2e',
    'carto_light':       '#f0f0f0',
    'carto_voyager':     '#e8e0d8',
    'tianditu_nolabel':  '#e8f0e8',
    'tianditu_label':    '#f0f4e8',
}


@track("MOD_MAP.F_001", track_args=False)
def create_base_map(lats=None, lons=None, show_labels=True,
                    center=None, zoom_start=None, map_style='carto_dark'):
    """创建 pydeck 基础地图。

    参数:
        map_style: carto_dark | carto_light | carto_voyager
                   tianditu_nolabel | tianditu_label (预览，暂不可用)
    """
    if center is None:
        if lats and lons:
            center = [float(np.mean(lats)), float(np.mean(lons))]
        else:
            center = DEFAULT_CENTER

    view_state = pdk.ViewState(
        latitude=center[0],
        longitude=center[1],
        zoom=zoom_start or DEFAULT_ZOOM,
        pitch=0,
    )

    # 天地图暂不可用，优雅降级为 CartoDB 浅色
    if map_style in ('tianditu_nolabel', 'tianditu_label'):
        style_url = MAP_STYLES['carto_light']
    else:
        style_url = MAP_STYLES.get(map_style, MAP_STYLES['carto_dark'])

    return pdk.Deck(
        initial_view_state=view_state,
        map_provider='mapbox',
        map_style=style_url,
        layers=[],
    )


@track("MOD_MAP.F_002", track_args=False)
def add_point_layer(deck, lats, lons, scores, props_list=None,
                    jitter=True, max_points=None):
    """添加情绪点图层（pydeck ScatterplotLayer）。

    props_list 支持两种格式:
      1. dict 列表: [{'id_e':..., 'comments':..., 'polarity':...}, ...]
      2. GeoJSON feature 列表: [{'properties':{...}}, ...]

    极性获取优先级: props 中的 polarity 列 > 根据 score 计算（向后兼容）

    大数据优化: 点数 > max_points 时随机采样（seed=42，保证同数据多次渲染一致）
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

    # ── 构建 DataFrame（pydeck 需要）──
    records = []
    for i, (lat, lon, s) in enumerate(zip(lats, lons, scores)):
        polarity = _get_polarity(props_list, i, s)
        color = POLARITY_RGBA.get(polarity, [0, 230, 118, 230])

        # Jitter：减少同坐标点完全重叠
        if jitter and props_list and i < len(props_list):
            p = props_list[i]
            props = p.get('properties', p)
            id_str = str(props.get('id_e', props.get('id', i)))
            seed_val = hash(id_str) % 10000
            rng = random.Random(seed_val)
            lat += rng.uniform(-0.0003, 0.0003)
            lon += rng.uniform(-0.0003, 0.0003)

        # Tooltip 信息
        tooltip_text = ''
        if props_list and i < len(props_list):
            p = props_list[i]
            props = p.get('properties', p)
            parts = []
            for key in ['id_e', 'polarity', 'score', 'relevance_category',
                        'primary_emotion', 'location_mentioned', 'ai_summary']:
                val = props.get(key, '')
                if val:
                    parts.append(f'{key}: {val}')
            tooltip_text = '\n'.join(parts)

        records.append({
            'lat': lat, 'lon': lon,
            'polarity': polarity,
            'color_r': color[0], 'color_g': color[1], 'color_b': color[2],
            'radius': 80,
            'tooltip': tooltip_text or f'点 {i}',
        })

    df = pd.DataFrame(records)

    layer = pdk.Layer(
        'ScatterplotLayer',
        data=df,
        get_position=['lon', 'lat'],
        get_fill_color=['color_r', 'color_g', 'color_b', 230],
        get_radius='radius',
        radius_scale=1,
        radius_min_pixels=4,
        radius_max_pixels=12,
        pickable=True,
        auto_highlight=True,
    )

    deck.layers.append(layer)
    return deck


def _hex_to_rgb(hex_color):
    """#RRGGBB -> [R, G, B]"""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]


@track("MOD_MAP.F_003", track_args=False)
def add_boundary_layer(deck, geojson_path=None, geojson_data=None,
                     name='分析范围', color='#1DBAD4', weight=4):
    """添加边界图层（pydeck GeoJsonLayer）。

    参数:
        deck: pydeck Deck 对象
        geojson_path: GeoJSON 文件路径
        geojson_data: GeoJSON dict（与 geojson_path 二选一）
        name: 图层名称
        color: 边界颜色 (hex 格式 #RRGGBB)
        weight: 内层线宽（像素），外发光层使用 2x 宽度
    """
    if geojson_data:
        data = geojson_data
    elif geojson_path:
        import json
        with open(geojson_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        return deck

    rgb = _hex_to_rgb(color)

    # ── 发光描边层（外层，更宽更透明）──
    glow_layer = pdk.Layer(
        'GeoJsonLayer',
        data=data,
        get_line_color=rgb + [60],
        get_line_width=weight * 2,
        get_fill_color=rgb + [10],
        pickable=False,
    )
    deck.layers.append(glow_layer)

    # ── 主边界层（内层，较细较实）──
    layer = pdk.Layer(
        'GeoJsonLayer',
        data=data,
        get_line_color=rgb + [220],
        get_line_width=weight,
        get_fill_color=rgb + [40],
        pickable=False,
    )

    deck.layers.append(layer)
    return deck


@track("MOD_MAP.F_004", track_args=False)
def add_heatmap_layer(deck, lats, lons, scores=None, radius=30, intensity=0.5,
                      threshold=0.05, opacity=0.7, max_points=None):
    """添加热力图图层（pydeck HeatmapLayer）。

    参数:
        deck: pydeck Deck 对象
        lats, lons: 坐标列表
        scores: 权重列表（None 则等权），值越大 = 越"热"
        radius: 热力半径（像素）
        intensity: 热力强度倍数
        threshold: 低于此权重的点不参与热力计算
        opacity: 图层不透明度
        max_points: 最大采样点数
    """
    n = len(lats)
    if n == 0:
        return deck

    # 采样
    if max_points and n > max_points:
        indices = random.Random(42).sample(range(n), max_points)
        lats = [lats[i] for i in indices]
        lons = [lons[i] for i in indices]
        if scores:
            scores = [scores[i] for i in indices]

    if scores is None:
        scores = [1.0] * len(lats)

    records = [{'lat': la, 'lon': lo, 'weight': float(w)}
               for la, lo, w in zip(lats, lons, scores)]

    layer = pdk.Layer(
        'HeatmapLayer',
        data=records,
        get_position=['lon', 'lat'],
        get_weight='weight',
        radius_pixels=radius,
        intensity=intensity,
        threshold=threshold,
        opacity=opacity,
    )

    deck.layers.append(layer)
    return deck


def _get_polarity(props_list, i, score):
    """获取极性：优先 props，否则从 score 计算（向后兼容）"""
    polarity = None
    if props_list and i < len(props_list):
        p = props_list[i]
        props = p.get('properties', p)
        polarity = props.get('polarity')
    if polarity is None:
        if score >= 0.80:
            polarity = 'Very Positive'
        elif score >= 0.60:
            polarity = 'Positive'
        elif score >= 0.40:
            polarity = 'Neutral'
        elif score >= 0.20:
            polarity = 'Negative'
        else:
            polarity = 'Very Negative'
    return polarity


# ── 追踪 ID 注册表 ──
register_track_id("MOD_MAP.F_001", "创建 pydeck 基础地图（支持暗色/亮色/卫星三档底图切换）")
register_track_id("MOD_MAP.F_002", "添加情绪点标记层（pydeck ScatterplotLayer + 五级极性）")
register_track_id("MOD_MAP.F_003", "添加行政区划边界叠加层（pydeck GeoJsonLayer）")
register_track_id("MOD_MAP.F_004", "添加热力图图层（pydeck HeatmapLayer）")

