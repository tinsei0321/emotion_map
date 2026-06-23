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


# ── 图层导出（API 下载用）：GeoJSON FeatureCollection → geojson / csv / shp.zip ──
# 格式取舍（业界 + RFC 7946）：
#   • GeoJSON — 固定 WGS84（RFC 7946 强制），crs 参数对其无效。
#   • Shapefile — 支持 WGS84(4326) / CGCS2000 3度带 CM111E(4546)，规划交付常需后者。
#   • CSV — 隐含 WGS84；几何表示 = WKT 列 / 经纬度列(仅点) / 仅属性。
SENSITIVE_FIELDS = {
    'username', 'user_id', 'userid', 'user', 'author', 'nickname', '昵称', '作者',
    'phone', 'mobile', 'tel', '手机', '手机号', '电话',
    'email', '邮箱', 'id_card', '身份证',
}


def _safe_name(name):
    import re
    s = re.sub(r'[^\w一-龥.\-]', '_', str(name or 'export')).strip('_.')
    return s[:60] or 'export'


def _coerce_scalar(gdf):
    """shapefile/csv 不能存 list/dict 列 → 整列转字符串（防 to_file 报错）。"""
    for c in list(gdf.columns):
        if c == 'geometry':
            continue
        try:
            if gdf[c].apply(lambda v: isinstance(v, (list, dict))).any():
                gdf[c] = gdf[c].astype(str)
        except Exception:
            pass
    return gdf


def _csv_bytes(gdf, geom_csv):
    import io
    buf = io.StringIO()
    if geom_csv == 'none':
        gdf.drop(columns='geometry', errors='ignore').to_csv(buf, index=False)
    elif geom_csv == 'lonlat' and (gdf.geom_type == 'Point').all():
        df = gdf.drop(columns='geometry', errors='ignore').copy()
        df['lon'] = gdf.geometry.x.values
        df['lat'] = gdf.geometry.y.values
        df.to_csv(buf, index=False)
    else:  # wkt（lonlat 遇非点也回退 WKT）
        df = gdf.drop(columns='geometry', errors='ignore').copy()
        df['geometry'] = gdf.geometry.to_wkt()
        df.to_csv(buf, index=False)
    return buf.getvalue().encode('utf-8-sig')   # BOM — Excel 兼容（core/CLAUDE.md 导出规范）


def _shp_zip_bytes(gdf, base):
    """shapefile 单几何类型 → 按 geom_type 分组，每组一个 .shp，统一打进一个 zip。
    单类型（如绘制的多边形）= 一个 shp；混合类型（全部图层合并）= 多个 shp 同包。"""
    import io, tempfile, zipfile, shutil
    tmpdir = tempfile.mkdtemp(prefix='em_export_')
    try:
        groups = {}
        try:
            for gt, sub in gdf.groupby(gdf.geom_type):
                groups[gt] = sub
        except Exception:
            groups = {'geom': gdf}
        if not groups:
            groups = {'geom': gdf}
        multi = len(groups) > 1
        written_bases = []
        for gt, sub in groups.items():
            tag = '_' + ''.join(ch for ch in str(gt).lower() if ch.isalnum()) if multi else ''
            sub_base = base + tag
            sub.to_file(os.path.join(tmpdir, sub_base + '.shp'),
                        driver='ESRI Shapefile', encoding='utf-8')
            written_bases.append(sub_base)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in os.listdir(tmpdir):
                if any(f.startswith(b + '.') for b in written_bases):
                    zf.write(os.path.join(tmpdir, f), f)
        return buf.getvalue()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@track("MOD_EXPORT.F_005", track_args=False)
def export_layer(geojson_fc, fmt='geojson', crs='wgs84', geom_csv='wkt', desensitize=True, filename='export'):
    """GeoJSON FeatureCollection → 指定格式字节流（供 API 下载）。

    参数:
        geojson_fc: dict — GeoJSON FeatureCollection（WGS84，前端 layer.fc）
        fmt: 'geojson' | 'csv' | 'shp'
        crs: 'wgs84' | 'cgcs2000'（仅 shp 生效；geojson/csv 固定 WGS84）
        geom_csv: 'wkt' | 'lonlat' | 'none'（仅 csv 生效）
        desensitize: bool — 剥 SENSITIVE_FIELDS 列（铁律 7）
        filename: 输出文件名（不含扩展名）

    返回: (bytes, filename_with_ext, media_type)
    """
    feats = geojson_fc.get('features', []) if isinstance(geojson_fc, dict) else []
    if not feats:
        raise ValueError('输入图层为空或无 features')

    gdf = gpd.GeoDataFrame.from_features(feats, crs='EPSG:4326')
    if desensitize:
        drop = [c for c in gdf.columns if str(c).lower() in SENSITIVE_FIELDS]
        if drop:
            gdf = gdf.drop(columns=drop)
    gdf = _coerce_scalar(gdf)

    fmt = (fmt or 'geojson').lower()
    safe = _safe_name(filename)

    if fmt == 'geojson':
        data = gdf.to_json().encode('utf-8')          # 固定 WGS84
        return data, f'{safe}.geojson', 'application/geo+json'
    if fmt == 'csv':
        return _csv_bytes(gdf, geom_csv), f'{safe}.csv', 'text/csv; charset=utf-8'
    if fmt == 'shp':
        if crs == 'cgcs2000':
            gdf = gdf.to_crs(epsg=4546)
        return _shp_zip_bytes(gdf, safe), f'{safe}.zip', 'application/zip'
    raise ValueError(f'不支持的导出格式: {fmt}')


register_track_id("MOD_EXPORT.F_005", "图层导出（geojson/csv/shp.zip，含 CRS + 脱敏）")
