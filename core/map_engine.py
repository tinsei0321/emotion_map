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


@track("MOD_MAP.F_001", track_args=False)
def create_base_map(lats=None, lons=None, show_labels=True,
                    center=None, zoom_start=None):
    """创建 pydeck 基础地图（OpenStreetMap 底图）。

    参数:
        lats, lons: 坐标列表（用于自动计算中心点）
        center: 手动指定中心 [lat, lon]
        zoom_start: 手动指定缩放级别
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

    return pdk.Deck(
        initial_view_state=view_state,
        map_provider='mapbox',
        map_style='https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
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

