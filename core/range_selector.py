"""
范围选择引擎 (Range Selector)
==============================
管理分析范围：加载用户上传的 GIS 矢量文件（GeoJSON / SHP），
支持点坐标筛选。默认范围：宜昌市中心城区 (1623 km²)。
"""
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from core.tracker import track, TrackContext, trace_log, trace_error, register_track_id


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BOUNDARIES_DIR = os.path.join(_PROJECT_ROOT, 'data', 'boundaries')
os.makedirs(_BOUNDARIES_DIR, exist_ok=True)

DEFAULT_RANGE = {
    'name': '宜昌市中心城区（默认 1623 km2）',
    'area_km2': 1623,
    'center': [111.29, 30.70],
}


@dataclass
class RangeConfig:
    name: str
    center: List[float]
    area_km2: float
    geometry: object


def _find_shp_in_dir(dir_path: str) -> Optional[str]:
    """在目录中查找 .shp 或 .geojson 文件。"""
    for f in sorted(os.listdir(dir_path)):
        low = f.lower()
        if low.endswith(('.shp', '.geojson', '.json', '.gpkg')):
            return os.path.join(dir_path, f)
    return None


@track("MOD_RANGE.F_001", track_args=False)
def list_boundary_files() -> List[str]:
    """列出 data/boundaries/ 下所有可用的矢量数据集。"""
    if not os.path.exists(_BOUNDARIES_DIR):
        return []
    datasets = set()
    for item in os.listdir(_BOUNDARIES_DIR):
        item_path = os.path.join(_BOUNDARIES_DIR, item)
        if os.path.isdir(item_path):
            # 子目录中有 .shp/.geojson/.gpkg 任一即视为有效数据集
            for f in os.listdir(item_path):
                if f.lower().endswith(('.shp', '.geojson', '.json', '.gpkg')):
                    datasets.add(item)
                    break
        elif item.lower().endswith(('.geojson', '.json', '.gpkg')):
            datasets.add(item)
    return sorted(datasets)


@track("MOD_RANGE.F_002", track_args=False)
def get_active_boundary_path() -> Optional[str]:
    """获取当前激活的边界数据集路径。"""
    files = list_boundary_files()
    if not files:
        return None
    first = files[0]
    full = os.path.join(_BOUNDARIES_DIR, first)
    if os.path.isdir(full):
        return _find_shp_in_dir(full)
    return full


@track("MOD_RANGE.F_003", track_args=True)
def load_boundaries(file_path: str) -> Dict[str, RangeConfig]:
    """加载矢量文件所有 feature → {name: RangeConfig}。"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'边界文件不存在: {file_path}')

    # Shapefile 单文件修复：自动检测并提示
    if file_path.lower().endswith('.shp'):
        base = file_path[:-4]
        shx_path = base + '.shx'
        if not os.path.exists(shx_path):
            raise FileNotFoundError(
                f'Shapefile 缺少 .shx 索引文件。'
                f'请将 .shp / .shx / .dbf 三个文件打包为 .zip 后重新上传。'
                f'\n当前文件: {file_path}'
                f'\n缺少文件: {shx_path}'
            )

    try:
        gdf = gpd.read_file(file_path)
    except Exception as e:
        msg = str(e)
        if 'SHAPE_RESTORE_SHX' in msg or '.shx' in msg:
            raise FileNotFoundError(
                f'Shapefile 不完整: 缺少必需的 .shx / .dbf 伴生文件。'
                f'\n请将 .shp / .shx / .dbf 打包为 .zip 后上传。'
            )
        raise

    # 面积计算（在原始投影下算，更准确）
    orig_crs = gdf.crs
    area_map = {}
    if orig_crs and not gdf.geometry.is_empty.all():
        try:
            gdf_proj = gdf.to_crs('EPSG:3857')
            for i, geom in enumerate(gdf_proj.geometry):
                if geom.geom_type in ('Polygon', 'MultiPolygon'):
                    area_map[i] = round(geom.area / 1e6, 2)
        except Exception:
            pass

    # 转为 WGS84 用于地图显示
    if orig_crs and not (hasattr(orig_crs, 'is_geographic') and orig_crs.is_geographic):
        gdf = gdf.to_crs('EPSG:4326')

    # 名称检测：尝试多种常见字段名
    name_candidates = ['name', 'NAME', 'Name', '区域名称', '县名', '市名',
                       'Layer', 'LAYER', 'FID_规划', 'FID']
    ranges = {}
    for i, row in gdf.iterrows():
        name = None
        for nc in name_candidates:
            val = row.get(nc)
            if val is not None and str(val).strip() not in ('', '0', 'None'):
                name = str(val).strip()
                break
        if name is None:
            name = f'区域_{len(ranges) + 1}'

        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        centroid = geom.centroid
        area = area_map.get(i, 0.0)

        ranges[name] = RangeConfig(
            name=name,
            center=[centroid.x, centroid.y],
            area_km2=area,
            geometry=geom,
        )
    return ranges


@track("MOD_RANGE.F_004", track_args=True)
def save_uploaded_file(uploaded_files) -> list:
    """保存上传的矢量文件到 data/boundaries/ 子文件夹，返回路径列表。"""
    if not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]

    # 如果有 .shp 文件，用其名称作为文件夹名
    folder_name = None
    for f in uploaded_files:
        if f.name.lower().endswith('.shp'):
            folder_name = os.path.splitext(f.name)[0]
            break
    if folder_name is None:
        folder_name = os.path.splitext(uploaded_files[0].name)[0]

    folder_path = os.path.join(_BOUNDARIES_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    saved = []
    for f in uploaded_files:
        filepath = os.path.join(folder_path, f.name)
        with open(filepath, 'wb') as fh:
            fh.write(f.getbuffer())
        saved.append(filepath)

    return saved


@track("MOD_RANGE.F_005", track_args=False)
def point_in_range(lon: float, lat: float, ranges: Dict[str, RangeConfig]) -> List[str]:
    """判断点属于哪些范围。"""
    point = Point(lon, lat)
    return [name for name, rc in ranges.items()
            if rc.geometry and rc.geometry.contains(point)]


@track("MOD_RANGE.F_006", track_args=True)
def filter_by_range(df: pd.DataFrame, lon_col: str, lat_col: str,
                    ranges: Dict[str, RangeConfig],
                    selected_names: Optional[List[str]] = None) -> gpd.GeoDataFrame:
    """按范围筛选 DataFrame。"""
    selected = {k: v for k, v in ranges.items() if k in selected_names} \
        if selected_names else ranges
    if not selected:
        return gpd.GeoDataFrame()

    rows = []
    for _, row in df.iterrows():
        lon, lat = row.get(lon_col), row.get(lat_col)
        if not (isinstance(lon, (int, float)) and isinstance(lat, (int, float))):
            continue
        if pd.isna(lon) or pd.isna(lat):
            continue
        pt = Point(lon, lat)
        for name, rc in selected.items():
            if rc.geometry and rc.geometry.contains(pt):
                d = row.to_dict()
                d['matched_range'] = name
                rows.append(d)
                break
    return gpd.GeoDataFrame(rows) if rows else gpd.GeoDataFrame()


@track("MOD_RANGE.F_007", track_args=False)
def get_available_ranges() -> List[Dict]:
    """获取可用范围列表（供 UI）。"""
    path = get_active_boundary_path()
    if not path:
        return [{'name': DEFAULT_RANGE['name'], 'center': DEFAULT_RANGE['center'],
                 'area_km2': DEFAULT_RANGE['area_km2']}]
    try:
        ranges = load_boundaries(path)
        return [{'name': rc.name, 'center': rc.center, 'area_km2': rc.area_km2}
                for rc in ranges.values()]
    except Exception:
        return [{'name': DEFAULT_RANGE['name'], 'center': DEFAULT_RANGE['center'],
                 'area_km2': DEFAULT_RANGE['area_km2']}]


@track("MOD_RANGE.F_008", track_args=False)
def get_boundary_crs_info() -> Optional[Dict[str, str]]:
    """返回当前边界文件的 CRS 信息 {original, display, note}。"""
    path = get_active_boundary_path()
    if not path:
        return None
    try:
        gdf = gpd.read_file(path)
        crs = gdf.crs
        if crs is None:
            return {'original': '未知', 'display': 'WGS84 (EPSG:4326), assumed',
                    'note': '文件未定义 CRS，假设为地理坐标'}
        crs_name = str(crs.name) if hasattr(crs, 'name') else str(crs)
        epsg = crs.to_epsg()
        is_geo = hasattr(crs, 'is_geographic') and crs.is_geographic
        epsg_str = f' (EPSG:{epsg})' if epsg else ''
        geo_str = ', geographic' if is_geo else ', projected'
        note = ('[OK] 与地图底图一致，无需转换' if epsg == 4326
                else f'[OK] 已自动转换至 EPSG:4326 (底图: WGS84)')
        return {
            'original': f'{crs_name}{epsg_str}{geo_str}',
            'display': 'WGS84 (EPSG:4326)',
            'note': note,
        }
    except Exception:
        return None


@track("MOD_RANGE.F_009", track_args=False)
def get_boundary_geojson() -> Optional[dict]:
    """返回当前边界文件的 GeoJSON dict（地图叠加用），自动转为 WGS84。"""
    path = get_active_boundary_path()
    if not path:
        return None
    try:
        gdf = gpd.read_file(path)
        if gdf.crs and not (hasattr(gdf.crs, 'is_geographic') and gdf.crs.is_geographic):
            gdf = gdf.to_crs('EPSG:4326')
        # 只保留 geometry 和 name 字段用于地图叠加
        if 'name' not in gdf.columns:
            gdf['name'] = gdf.get('Layer', gdf.get('FID_规划', '边界'))
        return json.loads(gdf[['name', 'geometry']].to_json())
    except Exception:
        return None

# ── 追踪 ID 注册表 ──
register_track_id("MOD_RANGE.F_001", "列出可用矢量数据集")
register_track_id("MOD_RANGE.F_002", "获取当前激活的边界路径")
register_track_id("MOD_RANGE.F_003", "加载矢量文件 → {name: RangeConfig}")
register_track_id("MOD_RANGE.F_004", "保存上传的矢量文件到 data/boundaries/")
register_track_id("MOD_RANGE.F_005", "判断点属于哪些范围")
register_track_id("MOD_RANGE.F_006", "按范围筛选 DataFrame")
register_track_id("MOD_RANGE.F_007", "获取可用范围列表（供 UI）")
register_track_id("MOD_RANGE.F_008", "获取边界文件 CRS 信息")
register_track_id("MOD_RANGE.F_009", "获取边界 GeoJSON（地图叠加用）")
