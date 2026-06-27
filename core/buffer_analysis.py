"""
缓冲区分析（覆盖范围）— geopandas + shapely 实现

对一类设施（点/线/面）做 N 米缓冲，看服务覆盖范围与盲区。
在投影面坐标（默认 CGCS2000 EPSG:4546，CM 111E，米制）下 buffer，保证米级精度。

buffer 逻辑独立成模块（而非留在 spatial_analysis.py），便于前端缓冲工具按需引用；
复杂空间统计（Gi*/Moran/聚合）仍在 spatial_analysis.py。
"""
import json
import geopandas as gpd
from shapely.ops import unary_union

from core.tracker import track, register_track_id


@track("MOD_SPATIAL.F_005", track_args=False)
def create_buffer(
    geojson_fc: dict,
    distance_m: float,
    dissolve: bool = False,
    target_crs: str = 'EPSG:4546',
):
    """
    缓冲区分析：GeoJSON FeatureCollection → 投影 4546 → 米制 buffer → 回 WGS84。

    参数:
        geojson_fc: 输入 GeoJSON FeatureCollection（WGS84，features 含 geometry）
        distance_m: 缓冲距离（米）
        dissolve: True=unary_union 合并为单一覆盖区；False=保留每要素缓冲
        target_crs: 缓冲运算用投影 CRS（宜昌标准 EPSG:4546，平面米制）

    返回:
        (buffer_fc, total_area_km2)
        buffer_fc: 缓冲区面 GeoJSON FeatureCollection（EPSG:4326），每要素含 buffer_area_km2
        total_area_km2: 总覆盖面积（km²，按投影平面米计）
    """
    feats = (geojson_fc or {}).get('features') if isinstance(geojson_fc, dict) else None
    if not feats:
        raise ValueError('输入图层为空，无法缓冲')
    gdf = gpd.GeoDataFrame.from_features(feats, crs='EPSG:4326')
    gdf = gdf[~gdf.geometry.isna()]            # 剔除无几何行
    if len(gdf) == 0:
        raise ValueError('输入图层无有效几何')

    projected = gdf.to_crs(target_crs)
    buffered = projected.geometry.buffer(distance_m)

    if dissolve:
        merged = unary_union([g for g in buffered if g is not None])
        buf = gpd.GeoDataFrame(
            {'buffer_area_km2': [round(merged.area / 1e6, 4)]},
            geometry=[merged], crs=target_crs,
        )
    else:
        bufs = [g for g in buffered if g is not None]
        buf = gpd.GeoDataFrame(
            {'buffer_area_km2': (buffered.area / 1e6).round(4).values},
            geometry=bufs, crs=target_crs,
        )

    total = round(float(buf['buffer_area_km2'].sum()), 4)
    fc = json.loads(buf.to_crs('EPSG:4326').to_json())   # 回 WGS84 供前端渲染
    return fc, total


# ── 追踪 ID 注册表（rule 10：@track 用到的 ID 必注册）──
register_track_id("MOD_SPATIAL.F_005", "缓冲区分析(覆盖范围)")
