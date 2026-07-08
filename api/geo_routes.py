"""GIS 工具箱路由 /api/v1/geo/*（挂载到 api/main.py，prefix=/api/v1）。

AI 问答内由模型经 ReAct 自动选用的 GIS 原子操作（用户铁律：几何剪裁/合并、用地字段筛选、
面积统计等必备，且 AI 自动调用，用户不手动点）。复用 core/spatial_analysis + core/range_selector
+ core/geo_registry，GeoPandas/Shapely 实现，不造轮子。

设计要点（避免大数据往返）：
- 分析类端点（zonal_stats/rank/hotspot）接受复合入参 layer + range + pre_filter，一次调用完成
  "范围内·某属性切片·聚合排序"，无需 AI 中转中间结果。
- 形态类端点（clip/filter_attr/merge/area_stats/buffer/overlay/nearest）返回 GeoJSON（结果）。
- 点层引用：layer 为 registry id（如 'yichang_l2_t1'）或 GeoJSON（send-in 用户上传层）。
- 边界引用：range/boundary 为 preset_id（如 'renewal_unit'）或 GeoJSON。

挂载：api/main.py `app.include_router(geo_router, prefix='/api/v1')` → 总路径 /api/v1/geo/*。
"""
import json
from typing import Any, Optional, Union

import geopandas as gpd
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.geo_registry import (
    list_point_layers, list_boundaries, resolve_points, resolve_boundary,
)
from core.spatial_analysis import aggregate_by_polygons, hot_spot_analysis

geo_router = APIRouter()

# 返回 GeoJSON feature 数硬上限（防 17k 点直出撑爆响应；分析类用 top_n 单独控制）
_MAX_RETURN_FEATS = 4000
_PROJECT_CRS = 'EPSG:4546'   # 宜昌米制投影（面积/缓冲精确）


# ── 共享入参模型 ──
class _GeoBase(BaseModel):
    layer: Optional[Any] = None       # layer_id(str) | GeoJSON(dict) | None=默认 L2
    range: Optional[Any] = None       # preset_id(str) | GeoJSON(dict)
    pre_filter: Optional[dict] = None  # {field, op(eq|in|gt|lt|gte|lte|ne), value}


# ════════════ 能力发现 ════════════
@geo_router.get('/geo/catalog')
async def geo_catalog():
    """列出可用点层、边界 preset、GIS 工具——供 AI/前端知道能调什么。"""
    from ai_qa.paradigm import GEO_TOOL_CATALOG
    return {
        'point_layers': list_point_layers(),
        'boundaries': list_boundaries(),
        'tools': [{'name': t['name'], 'when': t['when'], 'params': t['params']}
                  for t in GEO_TOOL_CATALOG],
    }


# ════════════ 共享预处理：解析 layer → 点 GeoDataFrame，应用 range clip + attr filter ════════════
def _prepare_points(layer, rng, pre_filter) -> gpd.GeoDataFrame:
    """解析点层 → 范围裁剪 → 属性过滤。"""
    pts = resolve_points(layer)   # KeyError/FileNotFoundError 向上抛 → 调用方包 400/500
    if rng is not None:
        polys = resolve_boundary(rng)
        pts = gpd.clip(pts, polys)
    if pre_filter:
        pts = _apply_attr_filter(pts, pre_filter)
    if len(pts) == 0:
        raise ValueError('范围内/过滤后无点——检查 range/pre_filter 与坐标系是否一致')
    return pts


def _apply_attr_filter(gdf: gpd.GeoDataFrame, f: dict) -> gpd.GeoDataFrame:
    """{field, op, value} → 布尔掩码过滤。op: eq|ne|in|gt|lt|gte|lte|contains。"""
    field = f.get('field')
    op = (f.get('op') or 'eq').lower()
    value = f.get('value')
    if not field or field not in gdf.columns:
        raise ValueError(f'过滤字段不存在: {field}（可用: {list(gdf.columns)[:20]}…）')
    col = gdf[field]
    if op == 'eq':
        mask = col == value
    elif op == 'ne':
        mask = col != value
    elif op == 'in':
        vals = value if isinstance(value, list) else [value]
        mask = col.isin(vals)
    elif op in ('gt', 'lt', 'gte', 'lte'):
        col = pd.to_numeric(col, errors='coerce')
        if op == 'gt':
            mask = col > value
        elif op == 'lt':
            mask = col < value
        elif op == 'gte':
            mask = col >= value
        else:
            mask = col <= value
    elif op == 'contains':
        mask = col.astype(str).str.contains(str(value), case=False, na=False)
    else:
        raise ValueError(f'未知 op: {op}')
    return gdf[mask]


def _norm_where(w):
    """where 容错：dict 原样回；字符串 'field/op/value'（/ 或 | 分隔）→ {field,op,value}。

    供 extract_feature 的按属性抽面（如 'MC/eq/西陵区'）。value 含分隔符时以首个为界、其余并入 value。
    """
    if w is None:
        return None
    if isinstance(w, dict):
        return w
    if isinstance(w, str):
        parts = [s.strip() for s in w.replace('|', '/').split('/') if s.strip()]
        if len(parts) < 3:
            raise ValueError(f'where 需 field/op/value（如 MC/eq/西陵区），收到: {w}')
        return {'field': parts[0], 'op': parts[1], 'value': '/'.join(parts[2:])}
    raise ValueError(f'where 需 dict 或 "field/op/value" 字符串，收到 {type(w)}')


def _to_geojson(gdf: gpd.GeoDataFrame, max_feats: int = _MAX_RETURN_FEATS) -> dict:
    """GeoDataFrame → GeoJSON dict（4326，截断超量 feature）。"""
    gdf = gdf.dropna(subset=['geometry'])
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs('EPSG:4326')
    total = len(gdf)
    truncated = total > max_feats
    if truncated:
        gdf = gdf.head(max_feats)
    fc = json.loads(gdf.to_json())
    fc['_total'] = total
    fc['_truncated'] = truncated
    return fc


def _props_df(gdf: gpd.GeoDataFrame, cols: list) -> pd.DataFrame:
    """提取属性列（含 name），用于排序输出（不带 geometry，轻量）。"""
    keep = [c for c in cols if c in gdf.columns]
    return gdf[keep].copy()


# ════════════ 1. filter_attr · 按字段筛选 ════════════
class FilterAttrRequest(_GeoBase):
    pass


@geo_router.post('/geo/filter_attr')
async def filter_attr(req: FilterAttrRequest):
    """按属性筛（用地/极性/domain/element/时点）。返回筛选后点 GeoJSON（截断+总数）。"""
    try:
        if not req.pre_filter:
            raise ValueError('filter_attr 需 pre_filter {field, op, value}')
        pts = resolve_points(req.layer)
        if req.range is not None:
            pts = gpd.clip(pts, resolve_boundary(req.range))
        pts = _apply_attr_filter(pts, req.pre_filter)
        fc = _to_geojson(pts)
    except (KeyError, FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'filter_attr 失败: {e}')
    return {'success': True, 'geojson': fc, 'count': fc['_total'],
            'truncated': fc['_truncated']}


# ════════════ 2. clip · 几何裁剪 ════════════
class ClipRequest(_GeoBase):
    pass


@geo_router.post('/geo/clip')
async def clip(req: ClipRequest):
    """按几何裁剪：range 范围内的点/聚合。返回子集 GeoJSON。"""
    if req.range is None:
        raise HTTPException(status_code=400, detail='clip 需 range(preset_id|geojson)')
    try:
        pts = resolve_points(req.layer)
        pts = gpd.clip(pts, resolve_boundary(req.range))
        if req.pre_filter:
            pts = _apply_attr_filter(pts, req.pre_filter)
        fc = _to_geojson(pts)
    except (KeyError, FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'clip 失败: {e}')
    return {'success': True, 'geojson': fc, 'count': fc['_total'],
            'truncated': fc['_truncated']}


# ════════════ 2b. extract_feature · 面层按属性抽取（裁出某区/某单元为独立面图层）════════════
class ExtractFeatureRequest(BaseModel):
    layer: Optional[Any] = None     # preset_id(如 admin_district) | GeoJSON（面边界）
    where: Optional[Any] = None     # {field,op,value} 或 "field/op/value"（如 MC/eq/西陵区）


@geo_router.post('/geo/extract_feature')
async def extract_feature(req: ExtractFeatureRequest):
    """从面边界按属性抽单要素（或子集）为独立面图层——纯 GIS 操作，结果落地图。

    典型：extract_feature(layer="admin_district", where="MC/eq/西陵区") → 西陵区单面。
    与 clip 的区别：clip 用面去切点（输出点子集）；extract_feature 从面层抽面（输出面子集）。"""
    if req.layer is None:
        raise HTTPException(status_code=400, detail='extract_feature 需 layer(preset_id|geojson)')
    try:
        polys = resolve_boundary(req.layer)
        if req.where:
            pf = _norm_where(req.where)
            # resolve_boundary 把 preset 的 nameField 规范化为 'name' 列；用户传原始 name_field（如 MC）时兜底映射
            if pf.get('field') and pf['field'] not in polys.columns and 'name' in polys.columns:
                pf = {**pf, 'field': 'name'}
            polys = _apply_attr_filter(polys, pf)
        if len(polys) == 0:
            raise ValueError('属性抽取无命中——检查 where 的 field/op/value（field 见 catalog name_field）')
        fc = _to_geojson(polys, max_feats=1000)
    except (KeyError, FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'extract_feature 失败: {e}')
    return {'success': True, 'geojson': fc, 'count': fc['_total'],
            'truncated': fc['_truncated'], 'name_field': 'name'}


# ════════════ 3. merge · 合并/dissolve ════════════
class MergeRequest(BaseModel):
    boundary: Optional[Any] = None   # preset_id | GeoJSON（要合并的面域）
    by: Optional[str] = None          # 按字段 dissolve；空=全部 unary_union


@geo_router.post('/geo/merge')
async def merge(req: MergeRequest):
    """合并/dissolve 面域：把多街道合成一片区，或同类用地合并。返回合并后面域 GeoJSON。"""
    if req.boundary is None:
        raise HTTPException(status_code=400, detail='merge 需 boundary(preset_id|geojson)')
    try:
        polys = resolve_boundary(req.boundary)
        if req.by:
            if req.by not in polys.columns:
                raise ValueError(f'dissolve 字段不存在: {req.by}')
            merged = polys.dissolve(by=req.by, as_index=False)
        else:
            merged = gpd.GeoDataFrame(
                {'name': ['合并区']}, geometry=[polys.geometry.unary_union], crs=polys.crs
            )
        # 算合并后面积
        merged_proj = merged.to_crs(_PROJECT_CRS)
        merged = merged.copy()
        merged['area_km2'] = (merged_proj.geometry.area / 1e6).round(3)
        fc = _to_geojson(merged)
    except (KeyError, FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'merge 失败: {e}')
    return {'success': True, 'geojson': fc, 'count': fc['_total']}


# ════════════ 4. area_stats · 面积统计 ════════════
class AreaStatsRequest(BaseModel):
    boundary: Optional[Any] = None
    group_by: Optional[str] = None    # 按字段分组统计面积占比


@geo_router.post('/geo/area_stats')
async def area_stats(req: AreaStatsRequest):
    """面积统计：各面域/各类用地的面积与占比。返回 [{name/group, area_km2, share}]。"""
    if req.boundary is None:
        raise HTTPException(status_code=400, detail='area_stats 需 boundary')
    try:
        polys = resolve_boundary(req.boundary)
        proj = polys.to_crs(_PROJECT_CRS)
        df = polys.drop(columns='geometry').copy() if hasattr(polys, 'drop') else pd.DataFrame()
        df['area_km2'] = (proj.geometry.area / 1e6).round(4)
        if req.group_by and req.group_by in polys.columns:
            grp = df.groupby(req.group_by)['area_km2'].sum().reset_index()
            grp.columns = [req.group_by, 'area_km2']
            total = grp['area_km2'].sum() or 1
            grp['share'] = (grp['area_km2'] / total).round(4)
            rows = grp.to_dict('records')
        else:
            total = df['area_km2'].sum() or 1
            df['share'] = (df['area_km2'] / total).round(4)
            rows = df.to_dict('records')
    except (KeyError, FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'area_stats 失败: {e}')
    return {'success': True, 'total_area_km2': round(sum(r.get('area_km2', 0) for r in rows), 3),
            'rows': rows}


# ════════════ 5. zonal_stats · 面域聚合统计（宏观/中观结论主干）════════════
class ZonalStatsRequest(_GeoBase):
    boundary: Any = None              # preset_id | GeoJSON（聚合面域，必填）
    agg_cols: Optional[list] = None   # 聚合数值列（默认 ['score']）
    top_n: Optional[int] = None       # 只返回前 N（按 |polarity_index| 降序）；空=全返


@geo_router.post('/geo/zonal_stats')
async def zonal_stats(req: ZonalStatsRequest):
    """按边界把点聚合成单元指标（point_count/极性/4×5 归因）+ 排序。宏观/中观结论核心。

    复用 spatial_analysis.aggregate_by_polygons；range=额外裁剪范围，pre_filter=属性切片。
    """
    if req.boundary is None:
        raise HTTPException(status_code=400, detail='zonal_stats 需 boundary(preset_id|geojson)')
    try:
        pts = _prepare_points(req.layer, req.range, req.pre_filter)
        polys = resolve_boundary(req.boundary)
        agg_cols = req.agg_cols or (['score'] if 'score' in pts.columns else [])
        merged = aggregate_by_polygons(pts, polys, agg_cols=agg_cols,
                                       polygon_name_col='name')
        # 排序：按 |polarity_index| 降序（张力大的在前）；无则按 point_count
        sort_col = 'polarity_index' if 'polarity_index' in merged.columns else 'point_count'
        merged = merged.sort_values(
            by=sort_col, key=lambda s: s.abs() if sort_col == 'polarity_index' else s,
            ascending=False, kind='stable')
        if req.top_n:
            merged = merged.head(int(req.top_n))
        # 属性表输出（轻量；含 name/极性/4×5/issue）—— AI 友好的"单元排行"
        prop_cols = ['name', 'point_count', 'polarity_index', 'score_mean',
                     'domain_top', 'element_top', 'issue_label', 'attribution', 'suggestion']
        rows = _props_df(merged, prop_cols)
        # 补 n_dom_*/n_elem_* 占比（如存在）
        for c in list(rows.columns):
            if c.startswith('n_dom_') or c.startswith('n_elem_'):
                prop_cols.append(c)
        rows = _props_df(merged, prop_cols)
        rows = rows.where(pd.notna(rows), '').to_dict('records')
    except (KeyError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'zonal_stats 失败: {e}')
    return {'success': True, 'count': len(rows), 'rows': rows,
            'sort_by': sort_col, 'message': f'已聚合 {len(rows)} 个单元（按 |{sort_col}| 降序）'}


# ════════════ 6. rank · 排序找 Top N ════════════
class RankRequest(_GeoBase):
    boundary: Optional[Any] = None    # 给定则先 zonal 聚合再排；空则需 layer 为已聚合 geojson
    by: Optional[str] = None          # worst|best|domain:X|element:X（默认 worst）
    top_n: int = 5


@geo_router.post('/geo/rank')
async def rank(req: RankRequest):
    """按极性/4×5 找 Top N 单元。boundary 给定→点聚合后排序；空→对已聚合 layer 直接排序。"""
    try:
        if req.boundary is not None:
            pts = _prepare_points(req.layer, req.range, req.pre_filter)
            polys = resolve_boundary(req.boundary)
            agg_cols = ['score'] if 'score' in pts.columns else []
            gdf = aggregate_by_polygons(pts, polys, agg_cols=agg_cols,
                                        polygon_name_col='name')
        else:
            # layer 须为已聚合 GeoJSON（含 polarity_index）
            src = resolve_points(req.layer)
            gdf = src
        if 'polarity_index' not in gdf.columns:
            raise ValueError('rank 需 layer 含 polarity_index（先 zonal_stats 或传聚合 GeoJSON）')
        by = (req.by or 'worst').lower()
        ascending = True   # worst=polarity_index 升序（最负在前）
        if by == 'best':
            ascending = False
        elif by.startswith('domain:') or by.startswith('element:'):
            # 按某 domain/element 点数占比排（n_dom_*/n_elem_*）
            pass
        # domain:X / element:X 排序键：对应 n_dom_X / n_elem_X 占比降序
        if by.startswith('domain:') or by.startswith('element:'):
            tag = by.split(':', 1)[1]
            key_col = None
            for c in gdf.columns:
                if c.endswith(f'_{tag}') and (c.startswith('n_dom_') or c.startswith('n_elem_')):
                    key_col = c
                    break
            if not key_col:
                raise ValueError(f'rank by {by}：未找到对应计列 {tag}')
            gdf = gdf.assign(_share=gdf[key_col] / gdf['point_count'].clip(lower=1)) \
                     .sort_values('_share', ascending=False, kind='stable')
        else:
            gdf = gdf.sort_values('polarity_index', ascending=ascending, kind='stable')
        gdf = gdf.head(int(req.top_n))
        prop_cols = ['name', 'point_count', 'polarity_index', 'score_mean',
                     'domain_top', 'element_top', 'issue_label']
        rows = _props_df(gdf, prop_cols).where(pd.notna(_props_df(gdf, prop_cols)), '') \
                                          .to_dict('records')
    except (KeyError, FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'rank 失败: {e}')
    return {'success': True, 'by': by, 'rows': rows}


# ════════════ 7. buffer · 缓冲区 ════════════
class BufferRequest(BaseModel):
    center: Any                       # preset_id | GeoJSON（缓冲中心面/点）
    radius_m: float = 500.0


@geo_router.post('/geo/buffer')
async def buffer(req: BufferRequest):
    """生成中心要素的缓冲区（米制精确）。返回缓冲面域 GeoJSON + 面积。"""
    try:
        center = resolve_boundary(req.center)
        proj = center.to_crs(_PROJECT_CRS)
        buf = proj.geometry.buffer(float(req.radius_m))
        names = center['name'].tolist() if 'name' in center.columns else ['缓冲区'] * len(center)
        buf_gdf = gpd.GeoDataFrame({'name': names},
                                   geometry=buf.values, crs=_PROJECT_CRS).to_crs('EPSG:4326')
        buf_gdf['area_km2'] = (buf.area / 1e6).round(3)
        fc = _to_geojson(buf_gdf)
    except (KeyError, FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'buffer 失败: {e}')
    return {'success': True, 'geojson': fc, 'radius_m': float(req.radius_m)}


# ════════════ 8. overlay · 叠置分析 ════════════
class OverlayRequest(BaseModel):
    layer_a: Any                      # preset_id | GeoJSON
    layer_b: Any                      # preset_id | GeoJSON
    how: str = 'intersection'         # intersection|union|difference|symmetric_difference


@geo_router.post('/geo/overlay')
async def overlay(req: OverlayRequest):
    """两个面域图层的叠置（交/并/差/对称差）。返回结果面域 GeoJSON + 面积。"""
    try:
        a = resolve_boundary(req.layer_a)
        b = resolve_boundary(req.layer_b)
        if req.how not in ('intersection', 'union', 'difference', 'symmetric_difference'):
            raise ValueError(f'未知 how: {req.how}')
        res = gpd.overlay(a, b, how=req.how)
        if len(res) == 0:
            return {'success': True, 'geojson': {'type': 'FeatureCollection', 'features': []},
                    'count': 0, 'message': f'{req.how} 结果为空'}
        res_proj = res.to_crs(_PROJECT_CRS)
        res = res.copy()
        res['area_km2'] = (res_proj.geometry.area / 1e6).round(4)
        fc = _to_geojson(res)
    except (KeyError, FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'overlay 失败: {e}')
    return {'success': True, 'geojson': fc, 'count': fc['_total'], 'how': req.how}


# ════════════ 9. nearest · 最近邻 ════════════
class NearestRequest(BaseModel):
    layer: Any                        # 点层（layer_id | GeoJSON）
    target: Any                       # 目标点（preset_id | GeoJSON）
    k: int = 1


@geo_router.post('/geo/nearest')
async def nearest(req: NearestRequest):
    """对每个 target 点，找 layer 中最近的 k 个点 + 距离（米）。返回配对表。"""
    try:
        pts = resolve_points(req.layer)
        target = resolve_boundary(req.target)
        # 仅保留 Point 几何
        pts = pts[pts.geometry.geom_type == 'Point']
        target = target[target.geometry.geom_type == 'Point']
        if len(pts) == 0 or len(target) == 0:
            raise ValueError('layer/target 需为点要素')
        pts_proj = pts.to_crs(_PROJECT_CRS)
        tgt_proj = target.to_crs(_PROJECT_CRS)
        joined = gpd.sjoin_nearest(tgt_proj, pts_proj, max_distance=float('inf'),
                                   return_geometry=False)
        # 距离列
        dist_col = 'distance' if 'distance' not in joined.columns else 'distance'
        if 'distance' not in joined.columns:
            joined[dist_col] = 0.0
        joined[dist_col] = (joined[dist_col]).round(1)
        rows = joined.where(pd.notna(joined), '').to_dict('records')
        rows = rows[: max(1, int(req.k)) * len(target)]   # 每 target 至多 k 个
    except (KeyError, FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'nearest 失败: {e}')
    return {'success': True, 'rows': rows, 'count': len(rows)}


# ════════════ 10. hotspot · Gi* 热点（接线已实现的 hot_spot_analysis）════════════
class HotspotRequest(_GeoBase):
    value_col: str = 'score'
    invert: bool = True               # True=负面为热（score 低为热）


@geo_router.post('/geo/hotspot')
async def hotspot(req: HotspotRequest):
    """Gi* 热点分析：识别情绪冷热点空间聚类。返回点 + Gi_Z/hotspot 分类（截断）。"""
    try:
        pts = _prepare_points(req.layer, req.range, req.pre_filter)
        if req.value_col not in pts.columns:
            raise ValueError(f'value_col {req.value_col} 不存在（可用 {list(pts.columns)[:20]}…）')
        pts = pts[pts.geometry.geom_type == 'Point'].copy()
        res = hot_spot_analysis(pts, value_col=req.value_col, invert=req.invert)
        fc = _to_geojson(res)
    except (KeyError, FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f'依赖缺失: {e}（Gi* 需 pip install libpysal esda）')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'hotspot 失败: {e}')
    return {'success': True, 'geojson': fc, 'count': fc['_total'],
            'truncated': fc['_truncated'],
            'legend': {'hot': '显著热点', 'cold': '显著冷点', 'ns': '不显著'}}
