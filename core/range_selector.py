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

from core.tracker import track, TrackContext, trace_log, trace_error, trace_warn, register_track_id
from core.field_dictionary import find_boundary_name_column   # P1 字段语义层·名称列推断


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BOUNDARIES_DIR = os.path.join(_PROJECT_ROOT, 'DATA', 'boundaries')
os.makedirs(_BOUNDARIES_DIR, exist_ok=True)
# 预设范围库（行政区/街道/社区/更新单元/用地等）：manifest 声明 button→file 映射，用户上传文件到此目录即激活
_PRESETS_DIR = os.path.join(_BOUNDARIES_DIR, 'presets')
_PRESETS_MANIFEST = os.path.join(_PRESETS_DIR, 'manifest.json')
os.makedirs(_PRESETS_DIR, exist_ok=True)

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
    """列出 DATA/boundaries/ 下所有可用的矢量数据集。"""
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

    # P1 名称检测：用字段语义层 find_boundary_name_column 找名称列（替代硬编码候选名）
    name_col = find_boundary_name_column(gdf.columns)
    ranges = {}
    for i, row in gdf.iterrows():
        name = None
        if name_col:
            val = row.get(name_col)
            if val is not None and str(val).strip() not in ('', '0', 'None'):
                name = str(val).strip()
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


# ── 预设范围库（行政区/街道/社区/更新单元/用地筛选）──
# manifest.json 声明 button→file 映射；用户把矢量文件按 file 名上传到 _PRESETS_DIR 即激活对应按钮。
@track("MOD_RANGE.F_013", track_args=False)
def list_presets() -> List[Dict]:
    """读取预设范围 manifest，每项标注 available（文件是否已上传）。

    返回 manifest 原结构（[{"group","items":[{id,label,file,nameField,available}]}]）；
    manifest 不存在 → 返回空列表（前端渲染为「暂无预设」）。"""
    if not os.path.exists(_PRESETS_MANIFEST):
        return []
    try:
        with open(_PRESETS_MANIFEST, 'r', encoding='utf-8') as fh:
            groups = json.load(fh)
    except Exception:
        return []
    for g in groups:
        for item in g.get('items', []):
            item['available'] = os.path.exists(os.path.join(_PRESETS_DIR, item.get('file', '')))
    return groups


@track("MOD_RANGE.F_014", track_args=True)
def load_preset(preset_id: str) -> Optional[Dict]:
    """按 id 加载预设范围 → {available, geojson, nameField}。

    文件缺失 → {available:False}；存在 → 读为 WGS84 GeoJSON（同 get_boundary_geojson 语义）。
    名称字段 nameField 从 manifest 取，供前端 grid-tool name_col 默认值。"""
    if not os.path.exists(_PRESETS_MANIFEST):
        return {'available': False}
    try:
        with open(_PRESETS_MANIFEST, 'r', encoding='utf-8') as fh:
            groups = json.load(fh)
    except Exception:
        return {'available': False}

    item = None
    for g in groups:
        for it in g.get('items', []):
            if it.get('id') == preset_id:
                item = it
                break
        if item:
            break
    if not item:
        return {'available': False}

    file_path = os.path.join(_PRESETS_DIR, item.get('file', ''))
    if not os.path.exists(file_path):
        return {'available': False, 'nameField': item.get('nameField')}

    try:
        gdf = gpd.read_file(file_path)
        if gdf.crs and not (hasattr(gdf.crs, 'is_geographic') and gdf.crs.is_geographic):
            gdf = gdf.to_crs('EPSG:4326')
        # 编号注入：manifest nameField='编号' 时（如更新单元无原生名称字段），
        # 按文件 feature 序自动编号「{label}-01…NN」注入 properties（不改原文件，加载期生成）。
        nf = item.get('nameField')
        if nf == '编号' and nf not in gdf.columns:
            label = item.get('label', '单元')
            width = max(2, len(str(len(gdf))))
            gdf[nf] = [u'{}-{:0{w}d}'.format(label, i + 1, w=width) for i in range(len(gdf))]
        return {
            'available': True,
            'geojson': json.loads(gdf.to_json()),
            'nameField': item.get('nameField'),
        }
    except Exception:
        return {'available': False, 'nameField': item.get('nameField')}


@track("MOD_RANGE.F_015", track_args=True)
def save_preset_geojson(preset_id: str, geojson: dict) -> Dict:
    """把前端解析好的 WGS84 GeoJSON 存为 manifest[id].file（激活预设按钮）。

    前端把 shp/kml/geojson 统一解析为 WGS84 GeoJSON 后 POST 到此；后端按 manifest
    声明的 file 名落盘（强制 .geojson 规范化存储）。返回 {success, file, message}。
    """
    if not os.path.exists(_PRESETS_MANIFEST):
        return {'success': False, 'message': 'manifest.json 不存在'}
    try:
        with open(_PRESETS_MANIFEST, 'r', encoding='utf-8') as fh:
            groups = json.load(fh)
    except Exception as e:
        return {'success': False, 'message': f'manifest 读取失败: {e}'}

    item = None
    for g in groups:
        for it in g.get('items', []):
            if it.get('id') == preset_id:
                item = it
                break
        if item:
            break
    if not item:
        return {'success': False, 'message': f'预设 id 不存在: {preset_id}'}

    file_name = item.get('file') or f'{preset_id}.geojson'
    if not file_name.lower().endswith(('.geojson', '.json')):
        file_name = file_name.rsplit('.', 1)[0] + '.geojson'   # 强制 geojson 规范化存储

    out_path = os.path.join(_PRESETS_DIR, file_name)
    try:
        with open(out_path, 'w', encoding='utf-8') as fh:
            json.dump(geojson, fh, ensure_ascii=False)
    except Exception as e:
        return {'success': False, 'message': f'写入失败: {e}'}
    return {'success': True, 'file': file_name,
            'message': f'已保存为 {file_name}，预设「{item.get("label", preset_id)}」已激活'}


def _count_features(geojson: dict) -> int:
    """统计 GeoJSON 中的 feature 数量。"""
    geojson_type = geojson.get("type", "")
    if geojson_type == "FeatureCollection":
        return len(geojson.get("features", []))
    elif geojson_type == "Feature":
        return 1
    return 0


def _extract_features(geojson: dict) -> list:
    """从 GeoJSON 中提取 feature 列表。"""
    geojson_type = geojson.get("type", "")
    if geojson_type == "FeatureCollection":
        return geojson.get("features", [])
    elif geojson_type == "Feature":
        return [geojson]
    return []


def _flatten_coords(geometry: dict) -> list:
    """从几何对象中提取所有坐标点，返回 [(lon, lat), ...]"""
    coords = []
    geom_type = geometry.get("type", "")

    if geom_type == "Polygon":
        for ring in geometry.get("coordinates", []):
            coords.extend([(pt[0], pt[1]) for pt in ring])
    elif geom_type == "MultiPolygon":
        for polygon in geometry.get("coordinates", []):
            for ring in polygon:
                coords.extend([(pt[0], pt[1]) for pt in ring])

    return coords


# ── 安全阈值与简化 ──
@track("MOD_RANGE.F_010", track_args=True)
def count_vertices(geojson: dict) -> int:
    """统计 GeoJSON 中所有几何的顶点总数。

    用于判断是否需要道格拉斯-普克简化。
    """
    total = 0
    try:
        features = _extract_features(geojson)
        for feat in features:
            geom = feat.get("geometry", {})
            coords = _flatten_coords(geom)
            total += len(coords)
    except Exception:
        return 999999  # 解析失败视为超大，触发简化
    return total


@track("MOD_RANGE.F_011", track_args=True)
def simplify_geojson(geojson: dict, tolerance: float = 0.0001) -> dict:
    """对 GeoJSON 执行道格拉斯-普克几何简化。

    Args:
        geojson: 原始 GeoJSON 字典
        tolerance: 简化容差（度），默认 0.0001 ≈ 10m @ 赤道

    Returns:
        简化后的 GeoJSON 深拷贝
    """
    import copy
    from shapely.geometry import shape

    simplified = copy.deepcopy(geojson)
    features = _extract_features(simplified)

    for feat in features:
        geom = feat.get("geometry", {})
        try:
            shp = shape(geom)
            simplified_shp = shp.simplify(tolerance, preserve_topology=True)
            feat["geometry"] = simplified_shp.__geo_interface__
        except Exception:
            trace_warn("MOD_RANGE.F_011", f"简化失败，保留原始几何: {feat.get('id', '?')}")
            continue

    # 更新顶层结构
    geojson_type = simplified.get("type", "")
    if geojson_type == "FeatureCollection":
        simplified["features"] = features
    elif geojson_type == "Feature":
        if features:
            simplified["geometry"] = features[0].get("geometry", simplified.get("geometry", {}))
    return simplified


@track("MOD_RANGE.F_012", track_args=True)
def validate_upload_safety(
    geojson: dict,
    file_size_mb: float = 0,
    max_vertices: int = 50000,
    max_features: int = 20000,
    max_file_mb: int = 100,
    simplify_tolerance: float = 0.0001,
) -> dict:
    """校验上传矢量文件的安全性，必要时自动简化。

    Returns:
        {"safe": True/False, "geojson": 处理后的GeoJSON,
         "warnings": [...], "simplified": bool, "error": str|None}
    """
    result = {"safe": True, "geojson": geojson, "warnings": [], "simplified": False, "error": None}

    # 1. 文件大小检查
    if file_size_mb > max_file_mb:
        result["safe"] = False
        result["error"] = f"[ERR] 文件过大 ({file_size_mb:.1f} MB > {max_file_mb} MB 上限)，请简化数据后重新上传"
        return result
    if file_size_mb > max_file_mb * 0.5:
        result["warnings"].append(f"[WARN] 文件较大 ({file_size_mb:.1f} MB)，加载可能较慢")

    # 2. 要素数检查
    feature_count = _count_features(geojson)
    if feature_count > max_features:
        result["safe"] = False
        result["error"] = f"[ERR] 要素数过多 ({feature_count} > {max_features})"
        return result
    if feature_count > max_features * 0.5:
        result["warnings"].append(f"[WARN] 要素数较多 ({feature_count})，可能影响渲染性能")

    # 3. 顶点数检查 + 自动简化
    vertex_count = count_vertices(geojson)
    if vertex_count > max_vertices:
        with TrackContext("MOD_RANGE.D_010", action="auto_simplify",
                           vertex_count=vertex_count, tolerance=simplify_tolerance):
            geojson = simplify_geojson(geojson, tolerance=simplify_tolerance)
            new_count = count_vertices(geojson)
            result["geojson"] = geojson
            result["simplified"] = True
            result["warnings"].append(
                f"[WARN] 顶点过多 ({vertex_count})，已自动简化为 {new_count} 顶点 "
                f"(容差={simplify_tolerance}度 ~10m)"
            )

    return result


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
register_track_id("MOD_RANGE.F_010", "统计 GeoJSON 顶点总数")
register_track_id("MOD_RANGE.F_011", "道格拉斯-普克几何简化")
register_track_id("MOD_RANGE.F_012", "矢量文件安全阈值校验 + 自动简化")
register_track_id("MOD_RANGE.F_013", "读取预设范围 manifest（标注 available）")
register_track_id("MOD_RANGE.F_014", "按 id 加载预设范围 → GeoJSON")
register_track_id("MOD_RANGE.F_015", "保存上传 GeoJSON 为预设文件（激活按钮）")
register_track_id("MOD_RANGE.D_010", "顶点数超限 → 自动简化")
