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
from shapely.geometry import Point, Polygon, box
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

    # 数值列强制 numeric（容错 str 化，同 F_006；agg_cols 默认 ['score']）
    for _c in agg_cols:
        if _c in joined.columns:
            joined[_c] = pd.to_numeric(joined[_c], errors='coerce')

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

    # domain/element 4×5 聚合 + DEMO 规则归因（与 create_square_grid 同源 helper）
    _attach_4x5_attrs(joined, grouped, agg_stats)

    # 合并回面域 GeoDataFrame
    result = polygons_gdf.copy()
    result.index.name = 'polygon_id'

    # 重置索引以匹配
    merged = result.merge(agg_stats, left_index=True, right_index=True, how='left')
    merged = gpd.GeoDataFrame(merged, geometry='geometry', crs=polygons_gdf.crs)

    # 填充无数据的区域（数值列填 0；字符串归因列 domain_top/issue_label 等填空串）
    for col in agg_stats.columns:
        if col not in merged.columns:
            continue
        if pd.api.types.is_numeric_dtype(agg_stats[col]):
            if 'count' in col:
                merged[col] = merged[col].fillna(0).astype(int)
            else:
                merged[col] = merged[col].fillna(0)
        else:
            merged[col] = merged[col].fillna('')

    # polygon_name_col 落地为规范 name 字段（popup/Table/AI digest 读稳定字段；原为 dead param）
    if polygon_name_col and polygon_name_col in merged.columns:
        merged['name'] = merged[polygon_name_col]
    elif 'name' not in merged.columns:
        merged['name'] = [f'区域_{i + 1}' for i in range(len(merged))]

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
    # h3 v4 API: latlng_to_cell(lat, lng, res)（v3 为 geo_to_h3）
    h3_indices = []
    for _, row in gdf.iterrows():
        h3_idx = h3.latlng_to_cell(row.geometry.y, row.geometry.x, resolution)
        h3_indices.append(h3_idx)

    gdf = gdf.copy()
    gdf['h3_idx'] = h3_indices

    # 数值列强制 numeric（容错 str 化，同 F_006；score 列 str 化时 mean 崩）
    if 'score' in gdf.columns:
        gdf['score'] = pd.to_numeric(gdf['score'], errors='coerce')

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
    # h3 v4 API: cell_to_boundary(cell) 返回 (lat, lng) 对，
    # Polygon 需 (lng, lat) 顺序，故逐对反转。
    hex_geoms = []
    for h3_idx in stats.index:
        boundary = h3.cell_to_boundary(h3_idx)
        hex_geoms.append(Polygon([(lng, lat) for lat, lng in boundary]))

    hex_gdf = gpd.GeoDataFrame(stats, geometry=hex_geoms, crs='EPSG:4326')
    hex_gdf['h3_idx'] = stats.index

    return hex_gdf


# ═══════════════════════════════════════════════════════════
# 4×5 情绪归因规则（DEMO 临时：L3/L4 LLM 归因上线后删除/替换）
# ═══════════════════════════════════════════════════════════
# 演示链"识别具体城建/更新问题"环：在聚合层按格的 (domain_top, element_top, polarity)
# 查表生成归因，让 popup 直接讲"此格=治理×设施=交通拥堵"。L3/L4 上线后改由 LLM 产出、本表移除。
# key = (domain, element, sign)，sign ∈ {'pos','neg'}（|polarity_index|>0.15）；未命中或中性 → 兜底。
_ATTRIBUTION_RULES = {
    # governance × facility（交通/市政设施）
    ('urban_governance', 'facility', 'neg'): (
        '交通拥堵/设施陈旧',
        '消极情绪集中在【城市治理×设施】，反映交通拥堵、停车难或市政设施老化',
        '优先评估交通承载力与市政设施更新时序'),
    ('urban_governance', 'facility', 'pos'): (
        '交通便利/设施完善',
        '正面评价集中在【城市治理×设施】，交通出行与市政设施体验改善',
        '巩固设施维护，推广经验至相邻片区'),
    # governance × service（政务/医疗）
    ('urban_governance', 'service', 'neg'): (
        '政务服务/就医体验',
        '消极情绪集中在【城市治理×服务】，反映政务办事效率、服务态度或就医体验问题',
        '优化政务服务流程与公共医疗资源配置'),
    ('urban_governance', 'service', 'pos'): (
        '公共服务获认可',
        '正面评价集中在【城市治理×服务】，政务/医疗服务满意度较高',
        '维持服务水准，持续监测满意度'),
    # operation × service（商业/餐饮/购物）
    ('urban_operation', 'service', 'neg'): (
        '商业服务体验差',
        '消极情绪集中在【城市运营×服务】，反映商家服务、价格或售后问题',
        '加强商业服务监管与消费者权益保障'),
    ('urban_operation', 'service', 'pos'): (
        '商业服务繁荣',
        '正面评价集中在【城市运营×服务】，餐饮/购物/生活服务满意度高',
        '保持商业活力，引导业态升级'),
    # operation × event（休闲/夜经济/节庆）
    ('urban_operation', 'event', 'neg'): (
        '活动组织/秩序问题',
        '消极情绪集中在【城市运营×事件】，反映活动拥挤、秩序或噪音问题',
        '提升大型活动组织与秩序管理'),
    ('urban_operation', 'event', 'pos'): (
        '夜经济/节庆活力',
        '正面评价集中在【城市运营×事件】，夜经济、节庆与休闲活动吸引力强',
        '培育夜经济品牌，扩大活动影响力'),
    # operation × culture（文旅/文化）
    ('urban_operation', 'culture', 'neg'): (
        '文旅体验不足',
        '消极情绪集中在【城市运营×文化】，文旅产品或文化设施体验不佳',
        '丰富文旅产品供给，提升文化设施品质'),
    ('urban_operation', 'culture', 'pos'): (
        '文旅活力突出',
        '正面评价集中在【城市运营×文化】，文旅打卡、文化设施吸引力强',
        '强化文旅 IP，打造文化消费场景'),
    # operation × environment（公园/绿地/滨水）
    ('urban_operation', 'environment', 'neg'): (
        '环境品质不佳',
        '消极情绪集中在【城市运营×环境】，公园绿地或滨水空间品质不足',
        '提升绿化与滨水空间环境品质'),
    ('urban_operation', 'environment', 'pos'): (
        '环境品质优良',
        '正面评价集中在【城市运营×环境】，公园绿地与滨水环境获好评',
        '维护环境品质，拓展公共休闲空间'),
    # renewal × service（住宅/更新片区）
    ('urban_renewal', 'service', 'neg'): (
        '老旧小区/物业问题',
        '消极情绪集中在【城市更新×服务】，反映老旧小区物业服务、配套或居住问题',
        '推进老旧小区改造与物业服务提升'),
    ('urban_renewal', 'service', 'pos'): (
        '更新成效显现',
        '正面评价集中在【城市更新×服务】，更新片区居住与配套改善获认可',
        '持续推进更新，总结可复制经验'),
}
_ATTR_DEFAULT = (
    '情绪聚集区',
    '该单元情绪显著聚集，建议结合 domain×element 进一步研判具体问题',
    '深入现场调研，结合 L3/L4 语义归因细化问题与对策',
)


def lookup_attribution(domain_top, element_top, polarity_index):
    """DEMO 临时：4×5 规则归因（L3/L4 LLM 归因上线后替换）。
    返回 {issue_label, attribution, suggestion}；polarity_index 中性或 key 未命中 → 兜底。"""
    sign = 'pos' if (polarity_index is not None and polarity_index > 0.15) else \
           ('neg' if (polarity_index is not None and polarity_index < -0.15) else None)
    label, attr, sug = _ATTRIBUTION_RULES.get((domain_top, element_top, sign), _ATTR_DEFAULT) \
        if sign else _ATTR_DEFAULT
    return {'issue_label': label, 'attribution': attr, 'suggestion': sug}


def _attach_4x5_attrs(joined, grouped, stats):
    """4×5 domain/element 聚合 + DEMO 规则归因（in-place 写入 stats）。

    create_square_grid / aggregate_by_polygons 共用（DRY：原两处内联重复）。
    joined = sjoin 结果（含点侧 domain/element 列）；grouped = joined.groupby('index_right')；
    stats = 按 index_right 索引的聚合 DataFrame（已含 polarity_index）。
    L3/L4 LLM 归因上线后本函数整体替换为 LLM 产出。"""
    for _c in ('domain', 'element', 'spatial_hotspot', 'area_seed'):
        if _c in joined.columns:
            joined[_c] = joined[_c].fillna('').astype(str)
    if 'domain' in joined.columns:
        stats['domain_top'] = grouped['domain'].agg(
            lambda x: x.mode().iloc[0] if not x.mode().empty else '')
        for _d in ('urban_operation', 'urban_governance', 'urban_renewal', 'urban_planning'):
            stats[f'n_dom_{_d}'] = grouped['domain'].apply(lambda x: int((x == _d).sum())).astype(int)
    if 'element' in joined.columns:
        stats['element_top'] = grouped['element'].agg(
            lambda x: x.mode().iloc[0] if not x.mode().empty else '')
        for _e in ('facility', 'environment', 'service', 'culture', 'event'):
            stats[f'n_elem_{_e}'] = grouped['element'].apply(lambda x: int((x == _e).sum())).astype(int)
    # place_name：格内代表地名（点侧 spatial_hotspot 多数；空则 area_seed 多数兜底）。
    # 供单极性 Overview 关键词「地点 Top5」（item 5）—— 让"地点-4×5-判断"三点一致有具体地名。
    if 'spatial_hotspot' in joined.columns or 'area_seed' in joined.columns:
        def _place_mode(g):
            for fld in ('spatial_hotspot', 'area_seed'):
                if fld in g.columns:
                    vals = g[fld][g[fld].astype(str) != '']
                    if not vals.empty:
                        m = vals.mode()
                        if not m.empty:
                            return str(m.iloc[0])
            return ''
        stats['place_name'] = grouped.apply(_place_mode)
    if 'domain_top' in stats.columns and 'polarity_index' in stats.columns:
        _attrs = stats.apply(lambda _r: lookup_attribution(
            _r.get('domain_top', ''), _r.get('element_top', ''), _r.get('polarity_index')), axis=1)
        stats['issue_label'] = _attrs.apply(lambda _d: _d['issue_label'])
        stats['attribution'] = _attrs.apply(lambda _d: _d['attribution'])
        stats['suggestion'] = _attrs.apply(lambda _d: _d['suggestion'])


# ═══════════════════════════════════════════════════════════
# 固定方格网格（标准网格）
# ═══════════════════════════════════════════════════════════

@track("MOD_SPATIAL.F_006", track_args=False)
def create_square_grid(
    gdf: gpd.GeoDataFrame,
    cell_size: float = 200.0,
    unit: str = 'm',
    target_crs: str = 'EPSG:4546',
) -> gpd.GeoDataFrame:
    """
    固定方格网格聚合（标准网格）—— 按指定边长方格统计情绪指标。

    参数:
        gdf: 情绪点 GeoDataFrame（WGS84 或任意 CRS；内部投影到 target_crs 量米制）
        cell_size: 方格边长（按 unit）；常用 50/200/400/1000
        unit: 'm' | 'km'（'km' 时 cell_size ×1000）
        target_crs: 量度投影 CRS（宜昌标准 EPSG:4546，CM 111E，米制，保证 cell_size 精确）

    返回:
        含聚合统计的方格 GeoDataFrame（EPSG:4326，仅含有点落入的格），列：
          - point_count: 格内点数
          - score_mean: 平均情绪得分
          - n_very_negative ~ n_very_positive: 五级极性计数
          - polarity_index: 综合情绪指数（-1~1，正值=偏正面）

    说明:
        snap-to-grid —— 仅对有点落入的格建 Polygon，避免稀疏点生成巨量空格
        （与 create_hex_grid "仅有点的格" 行为一致）。方格在 EPSG:4546 量度，
        保证 50/200/400/1000m 边长精确，结果回投影 EPSG:4326 供前端渲染。
    """
    pts = gdf.copy()
    if pts.crs is None:
        pts = pts.set_crs('EPSG:4326')
    pts = pts.to_crs(target_crs)

    cs = cell_size * (1000.0 if unit == 'km' else 1.0)
    if cs <= 0:
        raise ValueError('cell_size 必须为正')

    xs = pts.geometry.x.values
    ys = pts.geometry.y.values
    # snap 每点到其格原点（左下角），去重 → 仅建有点的格
    origins = {(float(np.floor(x / cs) * cs), float(np.floor(y / cs) * cs))
               for x, y in zip(xs, ys)}

    cells = [box(ox, oy, ox + cs, oy + cs) for ox, oy in origins]
    cells_gdf = gpd.GeoDataFrame(geometry=cells, crs=target_crs).reset_index(drop=True)

    # 空间连接：点 → 格（within）
    joined = gpd.sjoin(pts, cells_gdf, how='inner', predicate='within')
    if len(joined) == 0:
        raise ValueError('方格空间连接为空——点未落入任何格，检查坐标系/几何')

    # 数值列强制 numeric（容错：GeoJSON 经文本中转会把 score/置信度/强度序列化成 str，
    # 直接 mean() 抛 "dtype 'str' does not support operation 'mean'"）
    for _c in ('score', 'l1_confidence', 'emotion_intensity'):
        if _c in joined.columns:
            joined[_c] = pd.to_numeric(joined[_c], errors='coerce')

    grouped = joined.groupby('index_right')
    stats = pd.DataFrame({'point_count': grouped.size()})

    if 'score' in joined.columns:
        stats['score_mean'] = grouped['score'].mean().round(3)

    # L1 舆论热度辅助字段（置信度/强度均值，供前端算"密度×置信度"热度）
    if 'l1_confidence' in joined.columns:
        stats['l1_confidence_mean'] = grouped['l1_confidence'].mean().round(3)
    if 'emotion_intensity' in joined.columns:
        stats['emotion_intensity_mean'] = grouped['emotion_intensity'].mean().round(3)

    # 五级极性统计 + 综合情绪指数（公式同 aggregate_by_polygons）
    if 'polarity' in joined.columns:
        for pol in ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']:
            col_name = f'n_{pol.lower().replace(" ", "_")}'
            stats[col_name] = grouped['polarity'].apply(lambda x: (x == pol).sum())
        stats['polarity_index'] = (
            (stats['n_very_positive'] * 2 +
             stats['n_positive'] * 1 +
             stats['n_negative'] * -1 +
             stats['n_very_negative'] * -2) /
            stats['point_count'].clip(lower=1)
        ).round(3)

    # domain/element 4×5 聚合 + DEMO 规则归因（共享 helper，与 aggregate_by_polygons 同源）
    _attach_4x5_attrs(joined, grouped, stats)

    # 合并统计回方格（inner：仅保留有点的格）→ 回 WGS84
    result = cells_gdf.merge(stats, left_index=True, right_index=True, how='inner')
    result = gpd.GeoDataFrame(result, geometry='geometry', crs=target_crs)
    return result.to_crs('EPSG:4326')


# ═══════════════════════════════════════════════════════════
# 情绪地形 — KDE 等值面 mesh（密度×强度 → 分层 fill-extrusion 曲面）
# ═══════════════════════════════════════════════════════════

def _gaussian_kernel1d(sigma):
    """1D 高斯核（截断 ±3sigma），sigma<0.5 退化为单位核。纯 numpy（不引 scipy）。"""
    if sigma < 0.5:
        return np.array([1.0])
    r = int(max(1, round(3 * sigma)))
    k = np.arange(-r, r + 1, dtype=float)
    g = np.exp(-0.5 * (k / sigma) ** 2)
    return g / g.sum()


def _convolve_separable(H, sigma):
    """2D 栅格可分离高斯卷积（先轴0再轴1），'same' 模式。纯 numpy。"""
    g = _gaussian_kernel1d(sigma)
    H1 = np.apply_along_axis(lambda col: np.convolve(col, g, 'same'), 0, H)
    return np.apply_along_axis(lambda row: np.convolve(row, g, 'same'), 1, H1)


@track("MOD_SPATIAL.F_007", track_args=False)
def create_terrain_mesh(
    points_gdf: gpd.GeoDataFrame,
    polarity: str = 'overall',
    bandwidth_m: float = 250.0,
    cell_m: float = 60.0,
    n_levels: int = 7,
    target_crs: str = 'EPSG:4546',
) -> gpd.GeoDataFrame:
    """情绪地形等值面 mesh —— KDE(密度×强度) 等值线 → 分层 fill-extrusion 曲面。

    业界做法（kepler hexbin 同源）：高度=核密度（此处加权 emotion_intensity），
    颜色=区域内极性均值（综合）/ 密度（极性）。

    流程：
      点(WGS84) → 投影 4546(米) → 加权 histogram2d(权重=强度)
              → 可分离高斯卷积(KDE 曲面) → 分位 levels → contourpy 等值线环
              → 每环 Polygon(4546) → 点-环 sjoin 算 polarity_index/score/点数
              → 回 WGS84，按 level 升序（fill-extrusion 低先画、高压顶，免 z-fighting）

    参数:
      points_gdf: 情绪点 GeoDataFrame（WGS84，含 emotion_intensity/score/polarity）
      polarity: 'overall'(综合,全部点) | 'positive'/'negative'/'neutral'(先按极性过滤)
      bandwidth_m: KDE 高斯带宽（米），控制曲面平滑度（主城 200–300m）
      cell_m: 栅格边长（米），越小越细但越慢（默认 60）
      n_levels: 等值面层数（默认 7）

    返回:
      等值面 GeoDataFrame（EPSG:4326），每 feature（环多边形）属性：
        - _level: 高度 0~1（密度分位归一化，前端 fill-extrusion-height 用）
        - _norm: polarity_index 归一化 0~1（综合着色用，(-2..2)→(0..1)）
        - point_count / score_mean / polarity_index / emotion_intensity_mean
        - level_raw: 原始密度级（调试用）
      features 按 _level 升序（低环先 → 渲染压顶正确）。

    依赖: contourpy（matplotlib 自带）。依赖缺失抛 ImportError + 安装提示。
    """
    try:
        import contourpy as cpy
    except ImportError:
        raise ImportError(
            'contourpy 未安装（matplotlib 自带）。运行: pip install matplotlib\n'
            'contourpy 用于从 KDE 栅格提取等值线，是 matplotlib 的成熟等值面后端。'
        )

    pts = points_gdf.copy()
    if pts.crs is None:
        pts = pts.set_crs('EPSG:4326')
    # 极性过滤（单极性地形：只看某极性的密度峰）
    if polarity in ('positive', 'negative', 'neutral') and 'polarity' in pts.columns:
        polmap = {
            'positive': ['Very Positive', 'Positive'],
            'negative': ['Very Negative', 'Negative'],
            'neutral': ['Neutral'],
        }
        pts = pts[pts['polarity'].isin(polmap[polarity])].copy()
    if len(pts) < 3:
        raise ValueError(
            f'地形分析需要至少 3 个点（极性={polarity} 过滤后剩 {len(pts)}）'
        )

    # 数值列 coerce（容错 str 化，同 F_006）
    for _c in ('emotion_intensity', 'score'):
        if _c in pts.columns:
            pts[_c] = pd.to_numeric(pts[_c], errors='coerce')
    if 'emotion_intensity' in pts.columns:
        # 1~5 等级 → 0~1（模拟数据）/ 已 0~1（SnowNLP）；权重下限 0.05 防零权重消失
        ei = pts['emotion_intensity'].fillna(0.5)
        ei = np.where(ei > 1, ei / 5.0, ei)
        pts['_w'] = np.clip(ei, 0.05, 1.0)
    else:
        pts['_w'] = 1.0

    pts = pts.to_crs(target_crs)
    xs = pts.geometry.x.values
    ys = pts.geometry.y.values
    w = pts['_w'].values.astype(float)

    xmin, ymin, xmax, ymax = (float(v) for v in pts.total_bounds)
    pad = bandwidth_m  # 边界 pad：防卷积截断
    xmin -= pad; ymin -= pad; xmax += pad; ymax += pad
    nx = max(24, int(np.ceil((xmax - xmin) / cell_m)))
    ny = max(24, int(np.ceil((ymax - ymin) / cell_m)))

    with TrackContext("MOD_SPATIAL.D_003", n_points=len(pts), grid=f'{nx}x{ny}',
                      bandwidth_m=bandwidth_m, polarity=polarity):
        # 加权 KDE 栅格：H[i,j] = x-bin i, y-bin j 的强度权和
        H, xe, ye = np.histogram2d(
            xs, ys, bins=[nx, ny],
            range=[[xmin, xmax], [ymin, ymax]], weights=w,
        )
        sigma_cell = bandwidth_m / cell_m
        Hs = np.clip(_convolve_separable(H, sigma_cell), 0.0, None)

        nz = Hs[Hs > 0]
        if len(nz) < nx + ny:
            raise ValueError('KDE 曲面有效格不足（点过于稀疏或带宽过小）')
        # 分位 levels：从 25% 起，避开全域平底；末段加密突出峰
        qs = np.quantile(nz, [0.25, 0.40, 0.55, 0.68, 0.80, 0.90, 0.97])[:max(3, n_levels)]
        levels = sorted(set(round(float(q), 8) for q in qs if q > 0))
        if len(levels) < 3:
            levels = list(np.linspace(float(nz.min()), float(nz.max()), 6)[1:-1])
        # _level 按 level 范围归一化到 0~1（非 L/zmax——quantile 远小于峰值，否则高度被压扁）：
        # 最低环=贴地基底，最高环=1，层级差等距 → 视觉张力（山底平地 / 山顶高耸）。
        Lmin, Lmax = float(levels[0]), float(levels[-1])
        Lspan = (Lmax - Lmin) or 1.0

        # contourpy 等值线：z[j,i] @ (xc[i], yc[j]) → H.T（ny,nx）
        xc = (xe[:-1] + xe[1:]) / 2.0
        yc = (ye[:-1] + ye[1:]) / 2.0
        cg = cpy.contour_generator(x=xc, y=yc, z=Hs.T, line_type=cpy.LineType.Separate)

        rings = []  # [(level_raw, level_norm, Polygon(4546))]
        for L in levels:
            for r in cg.lines(float(L)):
                arr = np.asarray(r)
                if arr.ndim != 2 or arr.shape[0] < 4 or np.isnan(arr[:, 0]).any():
                    continue
                poly = Polygon(arr)
                if not poly.is_valid:
                    poly = poly.buffer(0)
                if poly.is_empty or poly.area < 1.0:   # <1m² 噪声环跳过
                    continue
                rings.append((float(L), (float(L) - Lmin) / Lspan, poly))

    if not rings:
        raise ValueError('等值面提取为空（KDE 曲面过平？增大 bandwidth_m 或点数）')

    # 点-环 sjoin 算每环极性/分数/强度统计（4546 米制 within）
    ring_gdf = gpd.GeoDataFrame(
        {'level_raw': [r[0] for r in rings], '_level': [r[1] for r in rings]},
        geometry=[r[2] for r in rings], crs=target_crs,
    ).reset_index(drop=True)
    join_cols = [c for c in ('score', 'polarity', 'emotion_intensity', 'domain', 'element') if c in pts.columns]
    joined = gpd.sjoin(pts[join_cols + ['geometry']], ring_gdf, how='inner', predicate='within') \
        if join_cols else gpd.sjoin(pts[['geometry']], ring_gdf, how='inner', predicate='within')

    grouped = joined.groupby('index_right')
    feats = []
    for idx, row in ring_gdf.iterrows():
        props = {
            '_level': round(float(row['_level']), 4),
            'level_raw': round(float(row['level_raw']), 6),
            'point_count': 0,
        }
        sub = grouped.get_group(idx) if idx in grouped.groups else joined.iloc[0:0]
        if len(sub):
            props['point_count'] = int(len(sub))
            if 'score' in sub.columns:
                props['score_mean'] = round(float(sub['score'].mean()), 3)
            if 'emotion_intensity' in sub.columns:
                props['emotion_intensity_mean'] = round(float(sub['emotion_intensity'].mean()), 3)
            # domain/element 4×5 众数（供 popup 识别治理要素）
            for _c in ('domain', 'element'):
                if _c in sub.columns:
                    _m = sub[_c].dropna().mode()
                    props[f'{_c}_top'] = _m.iloc[0] if not _m.empty else ''
            if 'polarity' in sub.columns:
                for pol in ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']:
                    props[f'n_{pol.lower().replace(" ", "_")}'] = int((sub['polarity'] == pol).sum())
                pc = props['point_count']
                pi = (
                    props.get('n_very_positive', 0) * 2 + props.get('n_positive', 0) * 1
                    + props.get('n_negative', 0) * -1 + props.get('n_very_negative', 0) * -2
                ) / max(1, pc)
                props['polarity_index'] = round(float(pi), 3)
                # 4×5 情绪归因（DEMO 规则，L3/L4 接管后移除）；_norm 对称拉伸移至循环后
                props.update(lookup_attribution(props.get('domain_top', ''), props.get('element_top', ''), pi))
                props['_norm'] = round((float(pi) + 2) / 4, 4)   # 占位，循环后覆盖为对称拉伸
            else:
                props['_norm'] = props['_level']
        else:
            props['_norm'] = props['_level']   # 无点落入（理论不应）→ 退密度
        feats.append({'geometry': row.geometry, **props})

    # _norm 固定分段映射 _pi_to_norm（与 grid-tool piToNorm 同步：对齐 valenceOf 5 级阈值）；
    # 替 p95 拉伸——后者数据相关致色带边界无法对齐判断阈值（颜色不准根因）。
    def _pi_to_norm(pi):
        if pi <= -1.0:
            return 0.0
        if pi <= -0.15:
            return 0.4 * (pi + 1.0) / 0.85
        if pi < 0.15:
            return 0.4 + 0.2 * (pi + 0.15) / 0.30
        if pi < 1.0:
            return 0.6 + 0.4 * (pi - 0.15) / 0.85
        return 1.0
    for f in feats:
        _pi = f.get('polarity_index')
        if _pi is not None:
            f['_norm'] = round(_pi_to_norm(float(_pi)), 4)

    out = gpd.GeoDataFrame(feats, geometry='geometry', crs=target_crs)
    out = out.sort_values('_level', ascending=True, kind='stable').reset_index(drop=True)
    return out.to_crs('EPSG:4326')


# ── 追踪 ID 注册表 ──
register_track_id("MOD_SPATIAL.F_001", "Getis-Ord Gi* 热点分析")
register_track_id("MOD_SPATIAL.F_002", "Moran's I 空间自相关检验")
register_track_id("MOD_SPATIAL.F_003", "行政单元聚合统计")
register_track_id("MOD_SPATIAL.F_004", "H3 六边形网格聚合")
register_track_id("MOD_SPATIAL.F_006", "固定方格网格聚合(标准网格)")
register_track_id("MOD_SPATIAL.F_007", "情绪地形 KDE 等值面 mesh")
register_track_id("MOD_SPATIAL.D_001", "热点分析：自适应空间权重矩阵构建")
register_track_id("MOD_SPATIAL.D_002", "热点分析：分类结果统计（hot/cold/ns）")
register_track_id("MOD_SPATIAL.D_003", "地形：KDE 曲面 + 等值面提取参数")
