"""
空间分析引擎 — 热点分析 + 空间自相关 + 行政单元聚合

基于 PySAL 和 GeoPandas，提供城市治理视角的空间统计方法：
  - Getis-Ord Gi* 热点分析: 识别情绪冷热点空间聚类
  - Moran's I 空间自相关: 检测情绪是否在空间上显著聚集
  - 行政单元聚合: 按街道/社区/格网统计情绪指标

使用方式:
    from core.spatial_analysis import (
        hot_spot_analysis,
        moran_i_test,
        aggregate_by_polygons,
        create_hex_grid,
    )
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from typing import Optional, Tuple

from core.tracker import track, TrackContext, register_track_id


# ═══════════════════════════════════════════════════════════
# 热点分析 — Getis-Ord Gi*
# ═══════════════════════════════════════════════════════════

@track("MOD_SPATIAL.F_001", track_args=False)
def hot_spot_analysis(
    gdf: gpd.GeoDataFrame,
    value_col: str = 'score',
    invert: bool = True,
) -> gpd.GeoDataFrame:
    """
    Getis-Ord Gi* 热点分析 — 识别情绪冷热点空间聚类。

    参数:
        gdf: 含 Point geometry 和 value_col 的 GeoDataFrame
        value_col: 要分析的数值列（如 'score' 情绪得分）
        invert: True=负面情绪为"热点"（score 越低越热），
                False=正面情绪为"热点"

    返回:
        含 Gi* Z-score 和 P-value 列的 GeoDataFrame
        - Gi_Z > 1.96: 显著热点（p < 0.05）
        - Gi_Z < -1.96: 显著冷点（p < 0.05）

    参考:
        Getis, A., & Ord, J. K. (1992).
        "The analysis of spatial association by use of distance statistics."
    """
    try:
        from libpysal.weights import DistanceBand
        from esda.getisord import G_Local
    except ImportError:
        raise ImportError(
            'PySAL 未安装。运行: pip install libpysal esda\n'
            'PySAL 是空间统计的标准开源库，不需要自己实现 Gi* 算法。'
        )

    if len(gdf) < 3:
        raise ValueError(f'热点分析需要至少 3 个点，当前 {len(gdf)} 个')

    # 确保是 Point geometry
    if not all(gdf.geometry.type == 'Point'):
        raise ValueError('热点分析需要 Point geometry')

    # 提取坐标
    coords = np.column_stack([gdf.geometry.x, gdf.geometry.y])

    # 自适应带宽：基于 KNN（默认 8 个邻居）
    k = min(8, len(gdf) - 1)
    with TrackContext("MOD_SPATIAL.D_001", n_points=len(gdf), k=k):
        w = DistanceBand.from_array(coords, threshold=0, binary=True, silence_warnings=True)
        # 确保每个点至少有 k 个邻居
        if w.neighbors.get(0, []) is None:
            from libpysal.weights import KNN
            w = KNN.from_array(coords, k=k)

    # 计算 Gi*
    values = gdf[value_col].values.astype(float)

    if invert:
        # 负面情绪热点：score 低 = 热点
        values = 1.0 - values

    gi = G_Local(values, w, transform='R')

    # 合并结果
    gdf = gdf.copy()
    gdf['Gi_Z'] = gi.Zs
    gdf['Gi_P'] = gi.p_sim
    gdf['hotspot'] = gdf['Gi_Z'].apply(_classify_hotspot)

    with TrackContext("MOD_SPATIAL.D_002",
                      n_hot=int((gdf['hotspot'] == 'hot').sum()),
                      n_cold=int((gdf['hotspot'] == 'cold').sum()),
                      n_ns=int((gdf['hotspot'] == 'ns').sum())):
        pass

    return gdf


def _classify_hotspot(z_score: float) -> str:
    """将 Gi* Z-score 分类为 hot/cold/ns。"""
    if z_score > 1.96:
        return 'hot'
    elif z_score < -1.96:
        return 'cold'
    return 'ns'


# ═══════════════════════════════════════════════════════════
# 空间自相关 — Moran's I
# ═══════════════════════════════════════════════════════════

@track("MOD_SPATIAL.F_002", track_args=False)
def moran_i_test(
    gdf: gpd.GeoDataFrame,
    value_col: str = 'score',
) -> dict:
    """
    Moran's I 空间自相关检验 — 检测情绪是否在空间上显著聚集。

    返回:
        {
            'I': float,          # Moran's I 值 (-1 ~ 1)
            'p_value': float,    # P 值
            'significant': bool, # p < 0.05
            'interpretation': str, # 解释文字
        }

    解读:
        I > 0: 空间正相关（相似情绪聚集在一起）
        I ≈ 0: 随机分布（情绪无空间模式）
        I < 0: 空间负相关（不同情绪交替分布）
    """
    try:
        from libpysal.weights import DistanceBand
        from esda.moran import Moran
    except ImportError:
        raise ImportError(
            'PySAL 未安装。运行: pip install libpysal esda'
        )

    if len(gdf) < 3:
        return {'I': 0, 'p_value': 1.0, 'significant': False,
                'interpretation': '数据点不足（需要 ≥3 个点）'}

    coords = np.column_stack([gdf.geometry.x, gdf.geometry.y])
    k = min(8, len(gdf) - 1)

    try:
        from libpysal.weights import KNN
        w = KNN.from_array(coords, k=k)
    except Exception:
        w = DistanceBand.from_array(coords, threshold=0, binary=True,
                                   silence_warnings=True)

    values = gdf[value_col].values.astype(float)
    mi = Moran(values, w)

    result = {
        'I': round(float(mi.I), 4),
        'p_value': round(float(mi.p_sim), 4),
        'significant': mi.p_sim < 0.05,
        'interpretation': '',
        'ei': round(float(mi.EI), 4),  # 期望值
    }

    if not result['significant']:
        result['interpretation'] = (
            f"Moran's I = {result['I']:.3f}, p = {result['p_value']:.3f}: "
            '情绪空间分布无显著聚集，呈随机分布。'
        )
    elif result['I'] > 0:
        result['interpretation'] = (
            f"Moran's I = {result['I']:.3f}, p = {result['p_value']:.3f}: "
            '情绪存在显著正向空间自相关——相似情绪在地理上聚集。'
        )
    else:
        result['interpretation'] = (
            f"Moran's I = {result['I']:.3f}, p = {result['p_value']:.3f}: "
            '情绪存在显著负向空间自相关——正面/负面情绪交替分布。'
        )

    return result


# ═══════════════════════════════════════════════════════════
# 行政单元聚合统计
# ═══════════════════════════════════════════════════════════

@track("MOD_SPATIAL.F_003", track_args=False)
def aggregate_by_polygons(
    points_gdf: gpd.GeoDataFrame,
    polygons_gdf: gpd.GeoDataFrame,
    agg_cols: Optional[list] = None,
    polygon_name_col: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """
    按行政/规划边界聚合点数据的情绪统计指标。

    参数:
        points_gdf: 情绪点 GeoDataFrame（需含 score/polarity 列）
        polygons_gdf: 面域 GeoDataFrame（如街道/社区/更新单元边界）
        agg_cols: 要统计的数值列，默认 ['score']
        polygon_name_col: 面域名称列（输出中保留）

    返回:
        含聚合统计的面域 GeoDataFrame，新增列:
          - point_count: 面域内点数
          - score_mean: 平均情绪得分
          - score_std: 情绪得分标准差
          - n_very_negative ~ n_very_positive: 五级极性计数
          - polarity_index: 综合情绪指数（-1~1，正值=偏正面）
    """
    if agg_cols is None:
        agg_cols = ['score']

    # 空间连接
    joined = gpd.sjoin(points_gdf, polygons_gdf, how='inner',
                       predicate='within')

    if len(joined) == 0:
        raise ValueError('空间连接结果为空——点不在任何面域内，请检查坐标系是否一致')

    # 按面域索引分组聚合
    grouped = joined.groupby('index_right')

    agg_stats = pd.DataFrame({'point_count': grouped.size()})

    for col in agg_cols:
        if col in joined.columns:
            agg_stats[f'{col}_mean'] = grouped[col].mean().round(3)
            agg_stats[f'{col}_std'] = grouped[col].std().round(3)

    # 五级极性统计
    if 'polarity' in joined.columns:
        for pol in ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']:
            col_name = f'n_{pol.lower().replace(" ", "_")}'
            agg_stats[col_name] = grouped['polarity'].apply(
                lambda x: (x == pol).sum()
            )

        # 综合情绪指数 (Polarity Index)
        agg_stats['polarity_index'] = (
            (agg_stats['n_very_positive'] * 2 +
             agg_stats['n_positive'] * 1 +
             agg_stats['n_negative'] * -1 +
             agg_stats['n_very_negative'] * -2) /
            agg_stats['point_count'].clip(lower=1)
        ).round(3)

    # 合并回面域 GeoDataFrame
    result = polygons_gdf.copy()
    result.index.name = 'polygon_id'

    # 重置索引以匹配
    merged = result.merge(agg_stats, left_index=True, right_index=True, how='left')
    merged = gpd.GeoDataFrame(merged, geometry='geometry', crs=polygons_gdf.crs)

    # 填充无数据的区域
    for col in agg_stats.columns:
        if col in merged.columns:
            if 'count' in col:
                merged[col] = merged[col].fillna(0).astype(int)
            else:
                merged[col] = merged[col].fillna(0)

    return merged


# ═══════════════════════════════════════════════════════════
# 六边形网格
# ═══════════════════════════════════════════════════════════

@track("MOD_SPATIAL.F_004", track_args=False)
def create_hex_grid(
    gdf: gpd.GeoDataFrame,
    resolution: int = 8,
) -> gpd.GeoDataFrame:
    """
    创建覆盖数据范围的 H3 六边形网格并进行聚合统计。

    参数:
        gdf: 情绪点 GeoDataFrame
        resolution: H3 分辨率 (0-15)，默认 8（约 0.7km² 每格）

    返回:
        含聚合统计的六边形 GeoDataFrame

    说明:
        H3 是 Uber 开源的地理索引系统，六边形格网比正方形格网
        更适合空间分析（等面积、相邻格网距离一致）。
        参见: https://h3geo.org
    """
    try:
        import h3
    except ImportError:
        raise ImportError(
            'h3 未安装。运行: pip install h3\n'
            'H3 是 Uber 开源的六边形地理索引系统。'
        )

    # 为每个点分配 H3 索引
    h3_indices = []
    for _, row in gdf.iterrows():
        h3_idx = h3.geo_to_h3(row.geometry.y, row.geometry.x, resolution)
        h3_indices.append(h3_idx)

    gdf = gdf.copy()
    gdf['h3_idx'] = h3_indices

    # 按 H3 格网聚合
    grouped = gdf.groupby('h3_idx')

    stats = pd.DataFrame({
        'point_count': grouped.size(),
        'score_mean': grouped['score'].mean().round(3),
    })

    if 'polarity' in gdf.columns:
        for pol in ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']:
            col_name = f'n_{pol.lower().replace(" ", "_")}'
            stats[col_name] = grouped['polarity'].apply(
                lambda x: (x == pol).sum()
            )

    # 生成六边形 geometry
    hex_geoms = []
    for h3_idx in stats.index:
        boundary = h3.h3_to_geo_boundary(h3_idx, geo_json=True)
        hex_geoms.append(Polygon(boundary))

    hex_gdf = gpd.GeoDataFrame(stats, geometry=hex_geoms, crs='EPSG:4326')
    hex_gdf['h3_idx'] = stats.index

    return hex_gdf


# ── 追踪 ID 注册表 ──
register_track_id("MOD_SPATIAL.F_001", "Getis-Ord Gi* 热点分析")
register_track_id("MOD_SPATIAL.F_002", "Moran's I 空间自相关检验")
register_track_id("MOD_SPATIAL.F_003", "行政单元聚合统计")
register_track_id("MOD_SPATIAL.F_004", "H3 六边形网格聚合")
register_track_id("MOD_SPATIAL.D_001", "热点分析：自适应空间权重矩阵构建")
register_track_id("MOD_SPATIAL.D_002", "热点分析：分类结果统计（hot/cold/ns）")
