"""
导出工具 — DataFrame → CSV / GeoJSON
══════════════════════════════════════════════════════════════
"""
import os
import builtins as _bi
import pandas as pd
import geopandas as gpd


# 安全 print — 防止 Windows GBK 控制台崩溃
_real_print = _bi.print

def _safe_print(*args, **kwargs):
    try:
        _real_print(*args, **kwargs)
    except UnicodeEncodeError:
        _real_print(*(str(a).encode('ascii', errors='replace').decode('ascii') for a in args), **kwargs)


def export_to_csv(df: pd.DataFrame, output_path: str):
    """DataFrame → CSV"""
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8')
    _safe_print(f'[OK] CSV 已保存: {output_path} ({len(df)} 行)')
    return output_path


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
    _safe_print(f'[OK] GeoJSON 已保存: {output_path} ({len(df)} 条)')
    return output_path
