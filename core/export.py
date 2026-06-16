"""
导出工具 — DataFrame → CSV / GeoJSON
══════════════════════════════════════════════════════════════
"""
import os
import builtins as _bi
import pandas as pd
import geopandas as gpd

from core.tracker import track, TrackContext, trace_log, trace_error, register_track_id
from core.utils import safe_print


# 安全 print — 防止 Windows GBK 控制台崩溃
_real_print = _bi.print


@track("MOD_EXPORT.F_001", track_args=True)
def export_to_csv(df: pd.DataFrame, output_path: str):
    """DataFrame → CSV"""
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8')
    safe_print(f'[OK] CSV 已保存: {output_path} ({len(df)} 行)')
    return output_path


@track("MOD_EXPORT.F_002", track_args=True)
def export_to_geojson(df: pd.DataFrame, output_path: str,
                      lon_col='lon', lat_col='lat'):
    """DataFrame → GeoJSON（需含 lon/lat 列）"""
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs="EPSG:4326",
    )

    cols_to_drop = [c for c in [lon_col, lat_col] if c in gdf.columns]
    gdf.drop(columns=cols_to_drop, inplace=True)

    gdf.to_file(output_path, driver='GeoJSON', encoding='utf-8')
    safe_print(f'[OK] GeoJSON 已保存: {output_path} ({len(df)} 条)')
    return output_path

@track("MOD_EXPORT.F_003", track_args=False)
def export_boundaries_geojson(polygon_layers: list) -> bytes:
    """合并多个边界图层为单个 GeoJSON FeatureCollection。

    参数:
        polygon_layers: [{'name': str, 'geojson': dict, 'visible': bool, ...}, ...]

    返回:
        UTF-8 编码的 GeoJSON 字节流（可直接用于 st.download_button）
    """
    import json

    features = []
    for layer in polygon_layers:
        geojson = layer.get('geojson')
        if not geojson:
            continue
        # 支持 FeatureCollection 和单个 Feature
        if geojson.get('type') == 'FeatureCollection':
            for feat in geojson.get('features', []):
                # 注入图层名到 properties
                if 'properties' not in feat or feat['properties'] is None:
                    feat['properties'] = {}
                feat['properties']['_layer_name'] = layer.get('name', '')
                features.append(feat)
        elif geojson.get('type') == 'Feature':
            feat = dict(geojson)
            if 'properties' not in feat or feat['properties'] is None:
                feat['properties'] = {}
            feat['properties']['_layer_name'] = layer.get('name', '')
            features.append(feat)

    collection = {
        'type': 'FeatureCollection',
        'features': features,
    }
    return json.dumps(collection, ensure_ascii=False, indent=2).encode('utf-8')


def get_export_preview(df, polygon_layers):
    """返回导出预览信息 dict。

    返回:
        {'n_points': int, 'n_layers': int, 'n_features': int, 'est_csv_kb': float}
    """
    preview = {
        'n_points': len(df) if df is not None else 0,
        'n_layers': len(polygon_layers) if polygon_layers else 0,
        'n_features': 0,
        'est_csv_kb': 0,
    }
    if df is not None and not df.empty:
        # 估算 CSV 大小：行数 * 列数 * 平均字段长度 / 1024
        est_bytes = len(df) * len(df.columns) * 30  # ~30 bytes per cell avg
        preview['est_csv_kb'] = round(est_bytes / 1024, 1)

    for layer in (polygon_layers or []):
        geojson = layer.get('geojson', {})
        if geojson.get('type') == 'FeatureCollection':
            preview['n_features'] += len(geojson.get('features', []))
        elif geojson.get('type') == 'Feature':
            preview['n_features'] += 1

    return preview


# ── 追踪 ID 注册表 ──
register_track_id("MOD_EXPORT.F_001", "DataFrame → CSV 导出")
register_track_id("MOD_EXPORT.F_002", "DataFrame → GeoJSON 导出（含 geometry 构建）")
register_track_id("MOD_EXPORT.F_003", "边界图层合并导出为 GeoJSON FeatureCollection")
register_track_id("MOD_EXPORT.F_004", "导出对话框预览（数据+边界统计）")
