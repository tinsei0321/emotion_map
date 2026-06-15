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
                    jitter=True, n_total=None, return_meta=False):
    """添加情绪点图层（pydeck ScatterplotLayer）— 支持分级渲染。

    根据数据总量自动切换渲染策略 (参考 Kepler.gl LOD / Mapbox cluster):
      S  (<5k):  标准点 radius=100m, opacity=0.85, 描边
      M  (5-20k): 密集点 radius=60m, opacity=0.75, 半描边
      L  (20-50k): 紧凑点 radius=30m, opacity=0.65, 无描边
      XL (50-100k): 无点, 建议切热力图

    Args:
        n_total: 数据总量（用于分级，默认=len(lats)）
        return_meta: 是否返回渲染元信息

    Returns:
        deck (始终), 若 return_meta=True 则附加 (tier_label, tier_index, sampled)
    """
    total = n_total or len(lats)

    # ── 分级检测 ──
    tier_idx = 0
    tier_label = 'S·标准'
    for i, (max_n, label, *_rest) in enumerate(RENDER_TIERS):
        if total <= max_n:
            tier_idx = i; tier_label = label; break

    radius, opacity, stroke_w = RENDER_TIERS[tier_idx][2:5]

    # ── XL 及以上：不渲染点（应使用热力图）──
    if radius is None:  # XL / XXL tier — only heatmap
        if return_meta:
            return deck, (tier_label, tier_idx, 0)
        return deck

    max_points = MAX_DISPLAY_POINTS
    n = len(lats)
    sampled = 0

    # ── 大数据采样（固定种子 seed=42，保证同数据多次渲染一致）──
    if n > max_points:
        sampled = n - max_points
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
                        'primary_emotion', 'location_mentioned', 'ai_summary',
                        'comments', 'poi']:
                val = props.get(key, '')
                if val:
                    parts.append(f'{key}: {val}')
            tooltip_text = '\n'.join(parts)

        records.append({
            'lat': lat, 'lon': lon,
            'polarity': polarity,
            'color_r': color[0], 'color_g': color[1], 'color_b': color[2],
            'radius': radius,
            'tooltip': tooltip_text or f'点 {i}',
        })

    df = pd.DataFrame(records)

    # ── 分级像素控制 ──
    # 数据量大时用更小的像素约束，减少视觉过载
    px_min = {0: 5, 1: 3, 2: 2, 3: 1, 4: 1}.get(tier_idx, 4)
    px_max = {0: 14, 1: 10, 2: 6, 3: 4, 4: 3}.get(tier_idx, 12)

    layer = pdk.Layer(
        'ScatterplotLayer',
        data=df,
        get_position=['lon', 'lat'],
        get_fill_color=['color_r', 'color_g', 'color_b', int(opacity * 255)],
        get_radius='radius',
        radius_scale=1,
        radius_min_pixels=px_min,
        radius_max_pixels=px_max,
        pickable=True,
        auto_highlight=True,
    )

    # 无描边模式 (L tier)
    if stroke_w > 0:
        layer.get_line_color = [255, 255, 255, int(opacity * 200)]
        layer.get_line_width = stroke_w
        layer.line_width_units = 'meters'
        layer.stroked = True

    deck.layers.append(layer)
    if return_meta:
        return deck, (tier_label, tier_idx, sampled)
    return deck


def _hex_to_rgb(hex_color):
    """#RRGGBB -> [R, G, B]"""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]


@track("MOD_MAP.F_003", track_args=False)
def add_boundary_layer(deck, geojson_path=None, geojson_data=None,
                     name='分析范围', color='#1DBAD4', weight=4,
                     fill=False, fill_color=None, fill_opacity=0.3):
    """添加边界图层（pydeck GeoJsonLayer）。

    参数:
        deck: pydeck Deck 对象
        geojson_path: GeoJSON 文件路径
        geojson_data: GeoJSON dict（与 geojson_path 二选一）
        name: 图层名称
        color: 边界颜色 (hex 格式 #RRGGBB 或 [R,G,B] 列表)
        weight: 内层线宽（像素），外发光层使用 2x 宽度
        fill: 是否填充面域
        fill_color: 面填充颜色 ([R,G,B,A] 或 hex)
        fill_opacity: 面不透明度 (0.0-1.0)
    """
    if geojson_data:
        data = geojson_data
    elif geojson_path:
        import json
        with open(geojson_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        return deck

    # 支持两种颜色格式：hex 字符串 或 [R,G,B] 列表
    if isinstance(color, str):
        rgb = _hex_to_rgb(color)
    else:
        rgb = list(color[:3])

    # ── 发光描边层（外层，更宽更透明）──
    glow_layer = pdk.Layer(
        'GeoJsonLayer',
        data=data,
        get_line_color=rgb + [60],
        get_line_width=weight * 2,
        get_fill_color=[0, 0, 0, 0],
        pickable=False,
    )
    deck.layers.append(glow_layer)

    # ── 填充颜色处理 ──
    if fill and fill_color:
        if isinstance(fill_color, str):
            frgb = _hex_to_rgb(fill_color) + [int(255 * fill_opacity)]
        elif len(fill_color) == 4:
            frgb = list(fill_color)
        else:
            frgb = list(fill_color[:3]) + [int(255 * fill_opacity)]
    else:
        frgb = [0, 0, 0, 0]

    # ── 主边界层（内层，较细较实）──
    layer = pdk.Layer(
        'GeoJsonLayer',
        data=data,
        get_line_color=rgb + [220],
        get_line_width=weight,
        get_fill_color=frgb if fill else [0, 0, 0, 0],
        stroked=True,
        filled=fill,
        extruded=False,
        pickable=False,
    )

    deck.layers.append(layer)
    return deck


@track("MOD_MAP.F_005", track_args=False)
def add_multiple_boundary_layers(deck, polygon_layers: list) -> None:
    """添加多个矢量范围图层到地图（每个图层独立样式）。

    参数:
        deck: pydeck Deck 对象
        polygon_layers: [{name, geojson, visible, style}, ...]
            style = {line_color: [R,G,B], line_width: int,
                     fill: bool, fill_color: [R,G,B,A], fill_opacity: float}
    """
    for layer_info in polygon_layers:
        if not layer_info.get("visible", True):
            continue
        geojson = layer_info.get("geojson")
        if geojson is None:
            continue
        style = layer_info.get("style", {})
        color = style.get("line_color", [255, 140, 0])
        weight = style.get("line_width", 20)
        fill = style.get("fill", False)
        fill_color = style.get("fill_color", [255, 140, 0, 120])
        fill_opacity = style.get("fill_opacity", 0.5)

        # 发光层
        rgb = list(color[:3]) if isinstance(color, (list, tuple)) else _hex_to_rgb(str(color))
        glow = pdk.Layer(
            "GeoJsonLayer",
            data=geojson,
            get_line_color=rgb + [60],
            get_line_width=weight * 2,
            get_fill_color=[0, 0, 0, 0],
            pickable=False,
        )
        deck.layers.append(glow)

        # 填充色：使用显式 RGBA 数组
        if fill:
            if isinstance(fill_color, (list, tuple)) and len(fill_color) >= 3:
                a = int(fill_color[3]) if len(fill_color) >= 4 else int(fill_opacity * 255)
                frgb = [int(fill_color[0]), int(fill_color[1]), int(fill_color[2]), a]
            else:
                frgb = _hex_to_rgb(str(fill_color)) + [int(fill_opacity * 255)]
        else:
            frgb = [0, 0, 0, 0]

        # 主线层
        main = pdk.Layer(
            "GeoJsonLayer",
            data=geojson,
            get_line_color=rgb + [220],
            get_line_width=weight,
            line_width_min_pixels=1,
            get_fill_color=frgb,
            stroked=True,
            filled=fill,
            extruded=False,
            pickable=False,
        )
        deck.layers.append(main)


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


@track("MOD_MAP.F_006", track_args=False)
def add_selection_marker(deck, lat, lon, radius=150, color=None):
    """添加选中点的高亮轮廓圆环（半透明金色圆环 + 中心实心点）。

    参数:
        deck: pydeck Deck 对象
        lat, lon: 选中点坐标
        radius: 圆环半径（像素），默认 150
        color: 轮廓颜色 [R,G,B]，默认金色 [255, 215, 0]
    """
    if lat is None or lon is None:
        return deck

    if color is None:
        color = [255, 215, 0]  # 金色

    records = [{
        'lat': lat, 'lon': lon,
        'color_r': color[0], 'color_g': color[1], 'color_b': color[2],
        'radius': radius,
    }]

    # ── 外层发光圆环（大半径，低不透明度）──
    glow = pdk.Layer(
        'ScatterplotLayer',
        data=records,
        get_position=['lon', 'lat'],
        get_fill_color=['color_r', 'color_g', 'color_b', 80],
        get_radius='radius',
        radius_scale=1,
        radius_min_pixels=radius,
        radius_max_pixels=radius,
        pickable=False,
    )
    deck.layers.append(glow)

    # ── 内层实心微点（标记精确位置）──
    inner = pdk.Layer(
        'ScatterplotLayer',
        data=records,
        get_position=['lon', 'lat'],
        get_fill_color=['color_r', 'color_g', 'color_b', 220],
        get_radius=20,
        radius_scale=1,
        radius_min_pixels=10,
        radius_max_pixels=10,
        pickable=False,
    )
    deck.layers.append(inner)
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
register_track_id("MOD_MAP.F_003", "添加行政区划边界叠加层（pydeck GeoJsonLayer），支持独立填充/线宽/颜色")
register_track_id("MOD_MAP.F_004", "添加热力图图层（pydeck HeatmapLayer）")
register_track_id("MOD_MAP.F_005", "添加多个矢量范围图层（每图层独立样式）")
register_track_id("MOD_MAP.F_006", "添加选中点高亮轮廓圆环（金色半透明圆环 + 中心微点）")

