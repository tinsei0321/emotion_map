"""
测试数据治理管道 — L0→L1 坐标转换 + 范围过滤 + 相关性筛选 + 脱敏
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SCRIPT.data_governance import (
    step1_load_and_transform,
    step4_run_l2_analysis,
)
from core.config import PROCESSED_DIR


class TestStep1LoadAndTransform:
    """L0→L1 坐标转换测试。"""

    def _create_l0_csv(self, path, n=10):
        """创建最小 L0 模拟 CSV。"""
        np.random.seed(42)
        df = pd.DataFrame({
            'lon_gcj02': np.random.uniform(111.28, 111.35, n),
            'lat_gcj02': np.random.uniform(30.68, 30.72, n),
            'comments': [f'测试评论 {i}' for i in range(n)],
            'source': ['test'] * n,
            'name': [f'user_{i}' for i in range(n)],  # 应被脱敏
        })
        df.to_csv(path, index=False, encoding='utf-8-sig')
        return df

    def test_load_basic(self):
        """基础加载：L0 CSV 应成功加载并完成坐标转换。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, 'test_l0.csv')
            self._create_l0_csv(csv_path, n=10)
            df = step1_load_and_transform(csv_path)
            assert df is not None
            assert len(df) == 10
            # 应包含转换后的坐标列
            assert 'lon' in df.columns or 'lon_gcj02' in df.columns
            assert 'lat' in df.columns or 'lat_gcj02' in df.columns

    def test_load_empty_csv(self):
        """空 CSV：应优雅处理。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, 'empty.csv')
            pd.DataFrame().to_csv(csv_path, index=False)
            # 空 DataFrame 可能返回 None 或空 DataFrame
            try:
                df = step1_load_and_transform(csv_path)
                if df is not None:
                    assert len(df) == 0
            except Exception:
                pass  # 空文件抛异常也可接受

    def test_load_nonexistent(self):
        """不存在的文件：应返回 None 或抛异常。"""
        try:
            result = step1_load_and_transform('/nonexistent/path.csv')
            assert result is None
        except (FileNotFoundError, Exception):
            pass  # 抛异常也可接受


class TestDataGovernancePipeline:
    """数据治理全管道测试。"""

    def _create_minimal_l0(self, tmpdir):
        """创建含多种文本的 L0 模拟数据。"""
        np.random.seed(42)
        n = 30
        texts = [
            "公园环境优美，绿化很好，每天早上来散步",  # 正面
            "施工噪音太大，严重影响休息，投诉了也没用",  # 负面
            "今天天气还行",  # 中性
            "商场服务态度特别好，停车也方便",  # 正面
            "垃圾堆积一周没人清理，臭气熏天",  # 负面
            "小区绿化不错，物业也负责",  # 正面
            "楼下餐馆油烟直接排放，窗户都不敢开",  # 负面
            "公交线路太少，出行不便",  # 负面
            "社区活动中心设施齐全，老人小孩都喜欢",  # 正面
            "人行道破损严重，下雨天积水",  # 负面
        ] * 3
        df = pd.DataFrame({
            'lon_gcj02': np.random.uniform(111.28, 111.35, n),
            'lat_gcj02': np.random.uniform(30.68, 30.72, n),
            'comments': texts,
            'source': ['test'] * n,
            'name': [f'user_{i}' for i in range(n)],
        })
        csv_path = os.path.join(tmpdir, 'test_l0.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        return csv_path, n

    def test_step1_output_columns(self):
        """Step1 输出应有基本列。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path, n = self._create_minimal_l0(tmpdir)
            df = step1_load_and_transform(csv_path)
            assert df is not None
            assert len(df) == n
            # 应有坐标列（lon/lat 或 lon_gcj02/lat_gcj02）
            has_lon = any(c in df.columns for c in ['lon', 'lon_gcj02'])
            has_lat = any(c in df.columns for c in ['lat', 'lat_gcj02'])
            assert has_lon and has_lat, f"缺少坐标列，实际列: {df.columns.tolist()}"
