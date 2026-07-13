"""GIS 数据注册表 · AI 问答 geo 工具箱的数据后端。

lazy-load + 内存缓存（GeoDataFrame），按稳定 id 引用——避免大数据（L1 30MB / 社区 87MB）
每次问答往返。被 api/geo_routes.py 的 /api/v1/geo/* 端点调用，供 AI 经 ReAct 自动选用。

数据资产：
- 点层：L1（治理点）/ L2（情绪点，含 score+polarity）× T1/T2/T3，读 DATA/performance/
- 边界 preset：行政区/街道/社区/更新单元/用地，复用 core/range_selector 的 manifest 机制
- CRS 统一 EPSG:4326（地图渲染基准；面积/缓冲在 spatial_analysis 内投影 EPSG:4546）

用户临时上传层不走注册表（保留 send-in 模式，由调用方直接传 GeoJSON）。
"""
import json
import os
from typing import Optional

import geopandas as gpd
import pandas as pd

from core.config import PERFORMANCE_DIR
from core.range_selector import list_presets, load_preset, _PRESETS_DIR
from core.field_dictionary import resolve_role, find_boundary_name_column   # P1 字段语义层

# 模块级缓存：layer_id/boundary_id → GeoDataFrame。lazy load，不启动全量加载。
_CACHE: dict = {}

# ── 点层 id → (文件名, 标签, 层级) ──
# L2 含 score/polarity（情绪主用）；L1 含 domain/element/topic（治理要素，无 score）。
_POINT_LAYERS = {
    'yichang_l2_t1': ('yichang_L2_T1_L2_result_csv.csv', '宜昌 L2 · T1（中心城区情绪·初）', 'L2'),
    'yichang_l2_t2': ('yichang_L2_T2_L2_result_csv.csv', '宜昌 L2 · T2（中心城区情绪·中）', 'L2'),
    'yichang_l2_t3': ('yichang_L2_T3_L2_result_csv.csv', '宜昌 L2 · T3（中心城区情绪·末）', 'L2'),
    'yichang_l1_t1': ('yichang_L1_T1_result_csv.csv', '宜昌 L1 · T1（全域治理点·初）', 'L1'),
    'yichang_l1_t2': ('yichang_L1_T2_result_csv.csv', '宜昌 L1 · T2（全域治理点·中）', 'L1'),
    'yichang_l1_t3': ('yichang_L1_T3_result_csv.csv', '宜昌 L1 · T3（全域治理点·末）', 'L1'),
}


_FIELD_CACHE: dict = {}   # fname → {fields, samples, dtypes}（catalog 暴露给 AI，避免瞎猜列名/取值）
# P1: 删 _KEY_FIELDS 硬编码，改用 field_dictionary.resolve_role 判定哪些字段优先给样例值（帮 LLM 构造 pre_filter）


def _point_layer_overview(fname: str) -> dict:
    """读 CSV 表头 + 首行（缓存），返 {fields, samples, dtypes}。供 catalog 暴露字段名 + 取值样例 + 类型。"""
    if fname in _FIELD_CACHE:
        return _FIELD_CACHE[fname]
    path = os.path.join(PERFORMANCE_DIR, fname)
    ov = {'fields': [], 'samples': {}, 'dtypes': {}}
    if os.path.isfile(path):
        try:
            df = pd.read_csv(path, nrows=2)
            fields = list(df.columns)
            # 优先给有 canonical role 的字段样例值（resolve_role 命中=polarity/score/text/name/...）
            key = [c for c in fields if resolve_role(c)] or fields[:8]
            row0 = df.iloc[0] if len(df) else None
            ov = {
                'fields': fields,
                'samples': {c: (str(row0[c])[:24] if row0 is not None and c in row0 else '') for c in key},
                'dtypes': {c: str(df[c].dtype) for c in key},
            }
        except Exception:
            pass
    _FIELD_CACHE[fname] = ov
    return ov


def list_point_layers() -> list:
    """列出可用的点层（标注 available + 字段/样例/类型/CRS）。L2 优先（含 score/polarity）。"""
    out = []
    for lid, (fname, label, level) in _POINT_LAYERS.items():
        available = os.path.isfile(os.path.join(PERFORMANCE_DIR, fname))
        ov = _point_layer_overview(fname) if available else {'fields': [], 'samples': {}, 'dtypes': {}}
        out.append({
            'id': lid,
            'label': label,
            'level': level,
            'available': available,
            'fields': ov['fields'],
            'samples': ov['samples'],
            'dtypes': ov['dtypes'],
            'crs': 'EPSG:4326',
        })
    return out


def list_boundaries() -> list:
    """列出可用的边界 preset（展平 list_presets 的 group→items，标注 available + name_field）。"""
    flat = []
    for g in list_presets() or []:
        for it in g.get('items', []):
            flat.append({
                'id': it.get('id'),
                'label': it.get('label'),
                'group': g.get('group'),
                'available': bool(it.get('available')),
                # 暴露名称字段：AI 据此构造 where（如 admin_district 的 MC、renewal_unit 的编号）
                'name_field': it.get('nameField'),
            })
    return flat


def get_layer_points(layer_id: str) -> gpd.GeoDataFrame:
    """按 id 取点层 GeoDataFrame（EPSG:4326，lon/lat → Point）。lazy 缓存。

    需要 lon/lat 列；score/polarity/domain/element/topic 等按文件原样保留（缺失则下游聚合跳过）。
    """
    if layer_id in _CACHE:
        return _CACHE[layer_id]
    if layer_id not in _POINT_LAYERS:
        raise KeyError(f'未知点层 id: {layer_id}（可用：{list(_POINT_LAYERS)}）')
    fname, _, _ = _POINT_LAYERS[layer_id]
    path = os.path.join(PERFORMANCE_DIR, fname)
    if not os.path.isfile(path):
        raise FileNotFoundError(f'点层文件缺失: {path}')

    df = pd.read_csv(path)
    # 坐标列兼容（L1/L2 均含 lon/lat；缺失则报错）
    lon_col = 'lon' if 'lon' in df.columns else ('longitude' if 'longitude' in df.columns else None)
    lat_col = 'lat' if 'lat' in df.columns else ('latitude' if 'latitude' in df.columns else None)
    if not lon_col or not lat_col:
        raise KeyError(f'{layer_id} 缺 lon/lat 列')

    df = df.dropna(subset=[lon_col, lat_col]).copy()
    # 数值列容错（聚合前 to_numeric；防 csv str 化崩 mean）
    for c in ('score', 'l1_confidence', 'emotion_intensity'):
        if c in df.columns:
            df[c] = pd.to_numeric(df.get(c), errors='coerce')
    # 极性规范化列名（聚合函数读 'polarity'）
    if 'polarity' not in df.columns and 'polarity_hint' in df.columns:
        # L1 用 polarity_hint（弱极性），映射到 polarity 列名供下游统一处理
        df = df.rename(columns={'polarity_hint': 'polarity'})

    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]), crs='EPSG:4326'
    )
    _CACHE[layer_id] = gdf
    return gdf


def resolve_boundary(boundary) -> gpd.GeoDataFrame:
    """把边界规格解析为面域 GeoDataFrame（EPSG:4326）。

    boundary可为：
    - str：preset_id（如 'renewal_unit'）→ load_preset 读 manifest 对应文件
    - dict：GeoJSON FeatureCollection（用户临时上传，send-in 模式）
    """
    if isinstance(boundary, str):
        loaded = load_preset(boundary)
        if not loaded.get('available'):
            avail = [b['id'] for b in list_boundaries() if b.get('available')]
            raise FileNotFoundError(f'边界 preset 不可用: {boundary}（文件未上传）。可用 preset: {avail}')
        gj = loaded.get('geojson') or {}
        feats = gj.get('features') if isinstance(gj, dict) else None
        if not feats:
            raise ValueError(f'边界 preset {boundary} 无 features')
        polys = gpd.GeoDataFrame.from_features(feats, crs='EPSG:4326')
        # 规范名称列（manifest nameField → name），供 zonal_stats 输出可读单元名
        nf = loaded.get('nameField')
        if nf and nf in polys.columns and 'name' not in polys.columns:
            polys = polys.rename(columns={nf: 'name'})
        return polys
    if isinstance(boundary, dict):
        feats = boundary.get('features') if isinstance(boundary, dict) else None
        if not feats:
            raise ValueError('boundary GeoJSON 无 features')
        polys = gpd.GeoDataFrame.from_features(feats, crs='EPSG:4326')
        # P1 send-in GeoJSON nameField 推断：find_boundary_name_column 找名称列→重命名 name（与 preset 路径一致）
        if 'name' not in polys.columns:
            nf = find_boundary_name_column(polys.columns)
            if nf:
                polys = polys.rename(columns={nf: 'name'})
        return polys
    raise TypeError(f'boundary 需为 preset_id(str) 或 GeoJSON(dict)，收到 {type(boundary)}')


def resolve_points(layer) -> Optional[gpd.GeoDataFrame]:
    """把点层规格解析为点 GeoDataFrame。

    layer可为：
    - str：注册表 layer_id（如 'yichang_l2_t1'）
    - dict：GeoJSON FeatureCollection（send-in，前端已加载的聚合层/上传点）
    - None：取默认情绪层（首个可用的 L2）
    """
    if layer is None:
        for lid in _POINT_LAYERS:   # L2 优先（_POINT_LAYERS 已按 L2 在前排序）
            try:
                return get_layer_points(lid)
            except Exception:
                continue
        raise FileNotFoundError('无可用点层')
    if isinstance(layer, str):
        return get_layer_points(layer)
    if isinstance(layer, dict):
        feats = layer.get('features') if isinstance(layer, dict) else None
        if not feats:
            raise ValueError('layer GeoJSON 无 features')
        return gpd.GeoDataFrame.from_features(feats, crs='EPSG:4326')
    raise TypeError(f'layer 需为 layer_id(str) / GeoJSON(dict) / None，收到 {type(layer)}')


def clear_cache():
    """清空注册表缓存（数据文件更新后调用）。"""
    _CACHE.clear()
