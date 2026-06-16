"""
pytest 全局配置 — fixtures 和测试数据生成
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np

# 确保项目根在 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_texts():
    """标准测试文本集 — 覆盖五级极性。"""
    return [
        ("这个公园太美了，每天来散步心情都很好", "Very Positive"),
        ("小区环境不错，物业管理也到位", "Positive"),
        ("今天天气还行，没什么特别的", "Neutral"),
        ("楼下施工噪音太大了，严重影响休息", "Negative"),
        ("垃圾堆积一周没人清理，臭气熏天，投诉也没人管", "Very Negative"),
        ("", "Neutral"),  # 空文本
    ]


@pytest.fixture
def sample_l1_df():
    """生成最小 L1 DataFrame（仅测试所需列）。"""
    np.random.seed(42)
    n = 20
    texts = [
        "公园环境优美，适合散步",
        "施工噪音扰民，投诉无门",
        "今天天气不错",
        "商场服务态度很好",
        "路边垃圾成堆，臭味难闻",
        "社区文化活动丰富",
        "停车位严重不足",
        "绿化带被破坏",
        "公交站太远了",
        "小区保安很负责",
    ] * 2
    df = pd.DataFrame({
        'text': texts,
        'comments': [''] * n,
        'lat': np.random.uniform(30.6, 30.8, n),
        'lon': np.random.uniform(111.2, 111.4, n),
        'source': ['test'] * n,
    })
    return df


@pytest.fixture
def sample_coords():
    """标准坐标测试对 — GCJ-02 和对应 WGS84。"""
    return {
        'gcj02_lon': 111.3,
        'gcj02_lat': 30.7,
        # WGS84 预期值（近似，实际偏移约 100-700m）
        'wgs84_lon_approx': 111.295,
        'wgs84_lat_approx': 30.698,
    }
