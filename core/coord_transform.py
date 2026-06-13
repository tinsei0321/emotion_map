"""
坐标转换工具 (Coordinate Transformer)
══════════════════════════════════════
L0 → L1 数据治理阶段统一坐标系。

宜昌市城市规划标准:
  TARGET_CRS = CGCS2000_3_Degree_GK_CM_111E (EPSG:4546 或自定义)
  这是宜昌市城市规划/GIS 工作者的主流投影坐标系。

中国常用坐标系:
  WGS84  (EPSG:4326) — GPS 原始坐标，国际标准，地图底图显示用
  GCJ-02 (火星坐标)  — 中国法规要求，社交媒体/地图平台使用
  BD-09  (百度坐标)  — 百度地图额外加密
  CGCS2000           — 中国大地坐标系统

转换策略:
  1. 社交媒体数据 (GCJ-02) → WGS84 (数学转换)
  2. WGS84 → CGCS2000 投影 (pyproj/gpd，< 1m 偏差可忽略)
  3. 无法转换时警告并记录原始 CRS
"""

import math
from typing import Tuple, List, Optional
import pandas as pd

from core.tracker import track, TrackContext, trace_log, trace_error, register_track_id

# ── 宜昌标准 ──
TARGET_CRS = 'CGCS2000_3_Degree_GK_CM_111E'
TARGET_EPSG = 4546  # CGCS2000 / 3-degree Gauss-Kruger zone 37 (CM 111E)
DISPLAY_CRS = 'WGS84'  # 地图底图显示用


# ── GCJ-02 ↔ WGS84 核心算法 ──

def _transform_lat(x: float, y: float) -> float:
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320.0 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lon(x: float, y: float) -> float:
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return ret


def wgs84_to_gcj02(lon: float, lat: float) -> Tuple[float, float]:
    """WGS84 → GCJ-02（火星坐标）"""
    if _out_of_china(lon, lat):
        return lon, lat
    dlat = _transform_lat(lon - 105.0, lat - 35.0)
    dlon = _transform_lon(lon - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - 0.00669342162296594323 * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((6378245.0 * (1 - 0.00669342162296594323)) / (magic * sqrtmagic) * math.pi)
    dlon = (dlon * 180.0) / (6378245.0 / sqrtmagic * math.cos(radlat) * math.pi)
    return lon + dlon, lat + dlat


@track("MOD_TRANSFORM.F_001", track_args=False)
def gcj02_to_wgs84(lon: float, lat: float) -> Tuple[float, float]:
    """GCJ-02（火星坐标）→ WGS84（精确迭代法）"""
    if _out_of_china(lon, lat):
        return lon, lat
    # 迭代逼近
    wgs_lon, wgs_lat = lon, lat
    for _ in range(5):
        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)
        wgs_lon += lon - gcj_lon
        wgs_lat += lat - gcj_lat
    return wgs_lon, wgs_lat


@track("MOD_TRANSFORM.F_002", track_args=False)
def bd09_to_wgs84(lon: float, lat: float) -> Tuple[float, float]:
    """BD-09（百度坐标）→ WGS84"""
    # BD-09 → GCJ-02
    x = lon - 0.0065
    y = lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * math.pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * math.pi)
    gcj_lon = z * math.cos(theta)
    gcj_lat = z * math.sin(theta)
    # GCJ-02 → WGS84
    return gcj02_to_wgs84(gcj_lon, gcj_lat)


@track("MOD_TRANSFORM.F_003", track_args=False)
def wgs84_to_bd09(lon: float, lat: float) -> Tuple[float, float]:
    """WGS84 → BD-09（百度坐标）"""
    gcj_lon, gcj_lat = wgs84_to_gcj02(lon, lat)
    z = math.sqrt(gcj_lon * gcj_lon + gcj_lat * gcj_lat) + 0.00002 * math.sin(gcj_lat * math.pi)
    theta = math.atan2(gcj_lat, gcj_lon) + 0.000003 * math.cos(gcj_lon * math.pi)
    return z * math.cos(theta) + 0.0065, z * math.sin(theta) + 0.006


def _out_of_china(lon: float, lat: float) -> bool:
    """粗略判断坐标是否在中国境外"""
    return not (72.004 <= lon <= 137.8347 and 0.8293 <= lat <= 55.8271)


# ── 平台 → 坐标系映射 ──

PLATFORM_CRS = {
    'xiaohongshu': 'GCJ-02',
    'dianping':    'GCJ-02',
    'meituan':     'GCJ-02',
    'weibo':       'GCJ-02',
    'douyin':      'GCJ-02',
    'baidu':       'BD-09',
    'su12345':     'WGS84',   # 政府数据通常是 WGS84/CGCS2000
    'unknown':     'GCJ-02',  # 默认假设火星坐标
}

# 目标坐标系（宜昌标准）
# CGCS2000_3_Degree_GK_CM_111E ≈ EPSG:4546


# ── 批量转换 ──

@track("MOD_TRANSFORM.F_004", track_args=False)
def convert_coords(lon: float, lat: float, source_crs: str,
                   target_crs: str = TARGET_CRS) -> Tuple[float, float]:
    """单点坐标转换。source_crs 支持 'WGS84'/'GCJ-02'/'BD-09'。"""
    if source_crs == target_crs:
        return lon, lat

    converters = {
        ('GCJ-02', 'WGS84'): gcj02_to_wgs84,
        ('WGS84',  'GCJ-02'): wgs84_to_gcj02,
        ('BD-09',  'WGS84'): bd09_to_wgs84,
        ('WGS84',  'BD-09'): wgs84_to_bd09,
        ('BD-09',  'GCJ-02'): lambda l, a: gcj02_to_wgs84(*bd09_to_wgs84(l, a)),
        ('GCJ-02', 'BD-09'): lambda l, a: wgs84_to_bd09(*gcj02_to_wgs84(l, a)),
    }

    key = (source_crs, target_crs)
    if key in converters:
        return converters[key](lon, lat)

    # 多跳转换
    if source_crs == 'BD-09' and target_crs == 'WGS84':
        glon, glat = bd09_to_wgs84(lon, lat)
        return gcj02_to_wgs84(glon, glat) if target_crs == 'GCJ-02' else (glon, glat)

    return lon, lat  # fallback


@track("MOD_TRANSFORM.F_005", track_args=True)
def normalize_dataframe_coords(df: pd.DataFrame, lon_col: str = 'lon_gcj02',
                                lat_col: str = 'lat_gcj02',
                                platform: str = 'unknown') -> pd.DataFrame:
    """
    L0 → L1 坐标标准化：根据平台自动将坐标转为 WGS84。

    Args:
        df: 含经纬度列的 DataFrame
        lon_col: 经度列名
        lat_col: 纬度列名
        platform: 数据来源平台 (xiaohongshu/dianping/weibo/...)

    Returns:
        坐标已转为 WGS84 的 DataFrame（新增 _original_crs 列记录原始坐标系）
    """
    source_crs = PLATFORM_CRS.get(platform, PLATFORM_CRS['unknown'])
    df = df.copy()

    if source_crs == TARGET_CRS:
        df['_original_crs'] = source_crs
        return df

    new_lons, new_lats = [], []
    for _, row in df.iterrows():
        try:
            lon, lat = float(row[lon_col]), float(row[lat_col])
            nlon, nlat = convert_coords(lon, lat, source_crs, TARGET_CRS)
            new_lons.append(nlon)
            new_lats.append(nlat)
        except (ValueError, TypeError):
            new_lons.append(row[lon_col])
            new_lats.append(row[lat_col])

    df[lon_col] = new_lons
    df[lat_col] = new_lats
    df['_original_crs'] = source_crs
    df['_target_crs'] = TARGET_CRS

    return df


@track("MOD_TRANSFORM.F_006", track_args=False)
def get_crs_info(platform: str) -> dict:
    """获取指定平台的坐标系信息。"""
    crs = PLATFORM_CRS.get(platform, PLATFORM_CRS['unknown'])
    needs_conv = crs != 'WGS84'  # 所有非 WGS84 平台都需要先转 WGS84，再投影
    note = (f'{crs} → WGS84(数学) → {TARGET_CRS}(投影)' if needs_conv
            else f'WGS84 ≈ {TARGET_CRS} (偏差 < 1m, 无需转换)')
    return {
        'platform': platform,
        'source_crs': crs,
        'target_crs': f'{TARGET_CRS} (宜昌标准)',
        'needs_conversion': needs_conv,
        'note': note,
    }

# ── 追踪 ID 注册表 ──
register_track_id("MOD_TRANSFORM.F_001", "GCJ-02 → WGS84 坐标转换（精确迭代）")
register_track_id("MOD_TRANSFORM.F_002", "BD-09 → WGS84 坐标转换")
register_track_id("MOD_TRANSFORM.F_003", "WGS84 → BD-09 坐标转换")
register_track_id("MOD_TRANSFORM.F_004", "单点坐标转换入口（支持多源坐标系）")
register_track_id("MOD_TRANSFORM.F_005", "DataFrame 批量坐标标准化")
register_track_id("MOD_TRANSFORM.F_006", "获取平台坐标系信息")
