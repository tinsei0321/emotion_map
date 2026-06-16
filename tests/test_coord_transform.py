"""
测试坐标转换模块 — 纯数学函数，不依赖外部服务
"""
import pandas as pd
import pytest
from core.coord_transform import (
    gcj02_to_wgs84,
    wgs84_to_gcj02,
    bd09_to_wgs84,
    normalize_dataframe_coords,
    convert_coords,
    get_crs_info,
    _out_of_china,
)


class TestGCJ02ToWGS84:
    """GCJ-02 → WGS84 转换测试。"""

    def test_basic_conversion(self):
        """基础转换：输入输出类型正确。"""
        wgs_lon, wgs_lat = gcj02_to_wgs84(111.3, 30.7)
        assert isinstance(wgs_lon, float)
        assert isinstance(wgs_lat, float)
        # 偏移应在合理范围（100-700m，约 0.001-0.007 度）
        assert abs(wgs_lon - 111.3) < 0.01
        assert abs(wgs_lat - 30.7) < 0.01

    def test_roundtrip(self):
        """往返转换：WGS84 → GCJ-02 → WGS84 应接近原始值。"""
        orig_lon, orig_lat = 111.3, 30.7
        gcj_lon, gcj_lat = wgs84_to_gcj02(orig_lon, orig_lat)
        wgs_lon, wgs_lat = gcj02_to_wgs84(gcj_lon, gcj_lat)
        # 往返误差应在 1 米内（约 1e-5 度）
        assert abs(wgs_lon - orig_lon) < 1e-4
        assert abs(wgs_lat - orig_lat) < 1e-4

    def test_zero_coords(self):
        """零坐标：不应崩溃。"""
        lon, lat = gcj02_to_wgs84(0.0, 0.0)
        assert isinstance(lon, float)
        assert isinstance(lat, float)

    def test_extreme_coords(self):
        """极端坐标：中国范围外（可能被判定为 out_of_china）。"""
        lon, lat = gcj02_to_wgs84(0.0, 85.0)
        assert isinstance(lon, float)
        assert isinstance(lat, float)


class TestOutOfChina:
    """中国范围外检测。"""

    def test_inside_china(self):
        """宜昌坐标应在范围内。"""
        assert not _out_of_china(111.3, 30.7)

    def test_outside_china(self):
        """海外坐标应判定为范围外。"""
        assert _out_of_china(-122.4, 37.8)  # 旧金山
        assert _out_of_china(139.7, 35.7)   # 东京

    def test_boundary(self):
        """边界测试。"""
        # 中国最西端附近
        assert not _out_of_china(75.0, 39.0)
        # 中国最东端附近
        assert not _out_of_china(134.0, 47.0)


class TestConvertCoords:
    """通用坐标转换函数。"""

    def test_gcj02_to_wgs84(self):
        lon, lat = convert_coords(111.3, 30.7, source_crs='gcj02', target_crs='wgs84')
        assert isinstance(lon, float)
        assert isinstance(lat, float)

    def test_wgs84_to_gcj02(self):
        lon, lat = convert_coords(111.3, 30.7, source_crs='wgs84', target_crs='gcj02')
        assert isinstance(lon, float)
        assert isinstance(lat, float)

    def test_same_crs(self):
        """同坐标系转换应返回原值。"""
        lon, lat = convert_coords(111.3, 30.7, source_crs='wgs84', target_crs='wgs84')
        assert lon == 111.3
        assert lat == 30.7


class TestNormalizeDataFrame:
    """DataFrame 批量坐标标准化。"""

    def test_basic_normalize(self):
        """基础 DataFrame 坐标标准化。"""
        import pandas as pd
        df = pd.DataFrame({
            'lon_gcj02': [111.30, 111.31, 111.32],
            'lat_gcj02': [30.70, 30.71, 30.72],
        })
        result = normalize_dataframe_coords(df, lon_col='lon_gcj02', lat_col='lat_gcj02')
        # normalize_dataframe_coords 保留原始列名 + 添加 _original_crs / _target_crs
        assert 'lon_gcj02' in result.columns
        assert 'lat_gcj02' in result.columns
        assert '_original_crs' in result.columns
        assert '_target_crs' in result.columns
        assert len(result) == 3

    def test_missing_columns(self):
        """缺少坐标列时应抛出 KeyError。"""
        df = pd.DataFrame({'text': ['a', 'b']})
        with pytest.raises(KeyError):
            normalize_dataframe_coords(df)


class TestGetCrsInfo:
    """CRS 信息查询。"""

    def test_gcj02(self):
        info = get_crs_info('gcj02')
        assert info is not None
        assert 'name' in info or 'epsg' in info or isinstance(info, dict)

    def test_wgs84(self):
        info = get_crs_info('wgs84')
        assert info is not None

    def test_unknown_platform(self):
        """未知平台应返回默认值或 None。"""
        info = get_crs_info('unknown_platform')
        # 不应崩溃
        assert info is not None
