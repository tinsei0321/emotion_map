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
import math
from typing import Any, Optional, Union

import geopandas as gpd
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.geo_registry import (
    list_point_layers, list_boundaries, resolve_points, resolve_boundary,
)
from core.spatial_analysis import aggregate_by_polygons, hot_spot_analysis
from core.field_dictionary import resolve_field_alias, resolve_role   # P1 字段语义层·alias 解析
from core.field_dictionary import validate_input_usage   # PT-CB2 T2·铁律7 守卫（结论层拒绝作空间操作输入）
from shapely.geometry import Point as _Point, box as _box   # CB-16 Wave 2：grid_pois 格几何重建

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
def _guard_usage_refs(*refs):
    """PT-CB2 T2·铁律7 闸门：扫描入参中的图层引用（str preset_id / list[str]），结论层（usage=analysis_output）
    → raise UsageGuardError（ValueError 子类·三段式文案），被各端点 except ValueError 分支转 400。
    GeoJSON dict / 非 manifest 字符串（点层 id、控制参数）→ 静默放行（多步链 $n 产物与用户上传不受限）。"""
    for r in refs:
        vals = r if isinstance(r, list) else [r]
        for v in vals:
            if isinstance(v, str):
                validate_input_usage(v)



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
    # P1 字段语义层·alias 解析：用户传'情绪'/'sentiment'/'区域名称'等别名→解析到实际列（物理列名不改）
    actual = resolve_field_alias(field, gdf.columns) if field else None
    # CB-05+ 字段自纠正：LLM 常猜 MC（训练数据）但实际列是 name 等 → 遍历列找含该值的字段
    if not actual and field and value is not None:
        _strval = str(value)
        for _col in gdf.columns:
            if _col == 'geometry':
                continue
            try:
                if _strval in gdf[_col].astype(str).values:
                    actual = _col
                    break
            except Exception:
                continue
    if not actual:
        avail = [(c, resolve_role(c) or '?') for c in list(gdf.columns)[:20]]
        raise ValueError(f'过滤字段不存在: {field}（可用: {avail}…）')
    col = gdf[actual]
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
        out = {'field': parts[0], 'op': parts[1], 'value': '/'.join(parts[2:])}
        # Hotfix R3 M1：op='in' + value 含逗号 → 拆 list（支持 "MC/in/西陵区,伍家岗区" 多要素一次提取）
        if out['op'] == 'in' and isinstance(out['value'], str) and ',' in out['value']:
            out['value'] = [v.strip() for v in out['value'].split(',') if v.strip()]
        return out
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
        _guard_usage_refs(req.layer, req.range)
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
        _guard_usage_refs(req.layer, req.range)
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
        _guard_usage_refs(req.layer)
        polys = resolve_boundary(req.layer)
        if req.where:
            pf = _norm_where(req.where)
            polys = _apply_attr_filter(polys, pf)   # alias 解析在 _apply_attr_filter 内（resolve_field_alias），不再硬编码 name 兜底
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
    boundary: Optional[Any] = None   # preset_id | GeoJSON（合并单图层·dissolve）
    layers: Optional[list] = None   # CB-11：多图层合并（concat·保留各要素分类字段）·boundary 单层模式二选一·每项 preset_id|GeoJSON
    by: Optional[str] = None          # 按字段 dissolve；空=全部 unary_union（单层）


@geo_router.post('/geo/merge')
async def merge(req: MergeRequest):
    """合并/dissolve 面域：把多街道合成一片区，或同类用地合并。返回合并后面域 GeoJSON。

    CB-11（Codex+glm组 方案 A）：支持 layers 多图层 concat——合并多个独立图层（保留 DLMC 分类·
    无字段后缀·区别于 overlay union 的空间并集）。boundary 单层路径完全保留（纯增量）。"""
    if req.boundary is None and req.layers is None:
        raise HTTPException(status_code=400, detail='merge 需 boundary 或 layers（二选一）')
    try:
        _guard_usage_refs(req.boundary, req.layers)
        if req.layers:
            # CB-11 P6（Codex）：layers 字符串→数组防御（LLM 单字符串 422）
            if isinstance(req.layers, str):
                req.layers = [req.layers]
            # 多图层 concat：逐项 resolve_boundary → CRS 统一 → pd.concat → _source_layer 标记 → 可选 dissolve
            gdfs = []
            for i, ly in enumerate(req.layers):
                g = resolve_boundary(ly)
                if not g.crs:
                    g = g.set_crs('EPSG:4326')
                g = g.to_crs('EPSG:4326')
                g = g.copy()
                # CB-11 P5（Codex）：_source_layer 携带原始引用（preset_id/层名/GeoJSON 摘要）·非序号（换序即变·无法回指）
                if isinstance(ly, str):
                    g['_source_layer'] = ly
                else:
                    g['_source_layer'] = f"geojson#{i}"
                gdfs.append(g)
            polys = pd.concat(gdfs, ignore_index=True)
            if req.by:
                if req.by not in polys.columns:
                    raise ValueError(f'dissolve 字段不存在: {req.by}')
                merged = polys.dissolve(by=req.by, as_index=False)
            else:
                merged = polys   # concat 直接保留各要素（含 DLMC 分类）
        else:
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
        _guard_usage_refs(req.boundary)
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
    top_n: Optional[int] = None       # 只返回前 N（按排序列降序）；空=全返
    sort_by: Optional[str] = None     # CB-23 A5：显式排序列（如 停车泊_sum/停车泊_mean）·空则 fallback 链


@geo_router.post('/geo/zonal_stats')
async def zonal_stats(req: ZonalStatsRequest):
    """按边界把点聚合成单元指标（point_count/极性/4×5 归因）+ 排序。宏观/中观结论核心。

    复用 spatial_analysis.aggregate_by_polygons；range=额外裁剪范围，pre_filter=属性切片。
    """
    if req.boundary is None:
        raise HTTPException(status_code=400, detail='zonal_stats 需 boundary(preset_id|geojson)')
    try:
        _guard_usage_refs(req.layer, req.range, req.boundary)
        pts = _prepare_points(req.layer, req.range, req.pre_filter)
        polys = resolve_boundary(req.boundary)
        # CB-12 P1'（glm组）：zonal_stats 诊断日志（PRM-07 夷陵 0 层定位）——boundary geometry/点数/overlap
        _poly_n = 0
        try:
            _poly_n = len(polys) if hasattr(polys, '__len__') else 0
        except Exception:
            _poly_n = -1
        import logging as _lg
        _lg.getLogger('uvicorn.error').warning(
            f'[zonal] boundary={str(req.boundary)[:80]} polys={_poly_n} pts={len(pts)}'
            f' crs_pts={getattr(pts.crs, "name", "?")} crs_poly={getattr(getattr(polys, "crs", None), "name", "?")}')
        agg_cols = req.agg_cols or (['score'] if 'score' in pts.columns else [])
        merged = aggregate_by_polygons(pts, polys, agg_cols=agg_cols,
                                       polygon_name_col='name')
        # CB-23 A5 排序 fallback 链：显式 sort_by → polarity_index(情绪轨) → 首 agg_col 聚合列(总量 sum) → point_count
        #   体检轨无 polarity_index → 退化按 point_count 会恒西陵第一（点数多）·改按 agg_col sum（总量口径·对齐 CHK-I05）
        if req.sort_by and req.sort_by in merged.columns:
            sort_col = req.sort_by
            _sort_semantic = 'sum' if sort_col.endswith('_sum') else ('mean' if sort_col.endswith('_mean') else 'attr')
        elif 'polarity_index' in merged.columns:
            sort_col = 'polarity_index'
            _sort_semantic = 'polarity'
        elif agg_cols:
            _cand = [f'{c}_sum' for c in agg_cols if f'{c}_sum' in merged.columns]
            sort_col = _cand[0] if _cand else 'point_count'
            _sort_semantic = 'sum' if _cand else 'count'
        else:
            sort_col = 'point_count'
            _sort_semantic = 'count'
        merged = merged.sort_values(
            by=sort_col, key=lambda s: s.abs() if sort_col == 'polarity_index' else s,
            ascending=False, kind='stable')
        if req.top_n:
            merged = merged.head(int(req.top_n))
        # 属性表输出（轻量；含 name/极性/4×5/issue/地点）—— AI 友好的"单元排行"
        # P3-4（CB-19）：加 place_name/place_name_source/poi_names/poi_count——后端已算好却被裁剪掉
        #   → rows 带地点 → harness _lastToolRows → 出口卡需求位置 + 结论段 + 地图图层自动受益（Gap B 核心杠杆）
        prop_cols = ['name', 'point_count', 'polarity_index', 'score_mean',
                     'domain_top', 'element_top', 'issue_label', 'attribution', 'suggestion',
                     'place_name', 'place_name_source', 'poi_names', 'poi_count']
        # CB-23 审计 P1-1（Codex）：agg_cols 非空时动态补 {c}_sum——排序用了 sum 但输出拿不到总量·
        #   阶段 3' 统计表/观点卡（harness _lastToolRows → 出口卡）需总量数值
        if agg_cols:
            prop_cols += [f'{c}_sum' for c in agg_cols if f'{c}_sum' in merged.columns]
        # [CB-1] 原为 discover-then-refetch：遍历 rows.columns 找 n_dom_*/n_elem_* 想补，
        # 但 _props_df 只返请求列 → 永不含 n_dom_ → 循环空转、二次 _props_df 冗余。
        # 清为单次调用（零行为变化）。补充虽从未生效，但深挖确认**无活消费方**：
        # rank 直读 gdf.columns（不经 _props_df）/ panel.js 矩阵读地图图层 feature.properties
        # （图层含完整 stats 列）—— 均不经此 trimmed 响应。修复=向无人读的响应加列=死重 → wontfix。
        rows = _props_df(merged, prop_cols)
        rows = rows.where(pd.notna(rows), '').to_dict('records')
    except (KeyError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'zonal_stats 失败: {e}')
    return {'success': True, 'count': len(rows), 'rows': rows,
            'sort_by': sort_col, 'sort_semantic': _sort_semantic,
            'message': f'已聚合 {len(rows)} 个单元（按 {sort_col} 降序·{_sort_semantic} 口径）'}


# ════════════ 6. rank · 排序找 Top N ════════════
class RankRequest(_GeoBase):
    boundary: Optional[Any] = None    # 给定则先 zonal 聚合再排；空则需 layer 为已聚合 geojson
    by: Optional[str] = None          # worst|best|domain:X|element:X（默认 worst）
    top_n: int = 5


# ════════════ 6.5 grid_pois · 格内 POI 清单（CB-16 Wave 2 / CB-15 P0）════════════
class GridPoisRequest(_GeoBase):
    """格内 POI 详查（下钻链最小闭环·按需重查·对齐悬停试探/点击锁定双层范式）。

    cell_id 或质心坐标（cell_lng/cell_lat + cell_size）二选一——cell_id 解析失败时质心兜底。
    返回格内 POI 清单（名称/类别/domain/element/坐标）+ 与格的距离。
    """
    cell_id: Optional[str] = None             # 确定性格 id（grid_{cell_size}_{row}_{col}·可选）
    cell_lng: Optional[float] = None          # 质心坐标 WGS84·与 cell_lat + cell_size 重建格
    cell_lat: Optional[float] = None
    cell_size: Optional[float] = None         # 格边长（米·重建格几何用）


@geo_router.post('/geo/grid_pois')
async def grid_pois(req: GridPoisRequest):
    """返回格内 POI 清单（place_layer.all_pois·含 CB-16 Wave 2 接入的 3220·共 4310 条）。

    cell_id（grid_{size}_{row}_{col}·4546 米制）或质心坐标 + cell_size 重建格几何 → sjoin 格内 POI。
    """
    if req.cell_id is None and (req.cell_lng is None or req.cell_lat is None or req.cell_size is None):
        raise HTTPException(status_code=400, detail='grid_pois 需 cell_id 或 (cell_lng,cell_lat,cell_size)')
    try:
        from core.place_layer import get_place_layer
        _pl = get_place_layer() if get_place_layer else None
        _pois = _pl.all_pois if _pl else []
        if not _pois:
            return {'success': True, 'cell_id': req.cell_id, 'pois': [], 'count': 0, 'message': 'POI 未加载'}

        # 解析格几何（cell_id 优先·质心坐标兜底）→ 统一 EPSG:4546 米制
        _crs = _PROJECT_CRS
        if req.cell_id:
            # grid_{cell_size}_{row}_{col}（4546 米制 origin）
            _parts = req.cell_id.split('_')
            if len(_parts) == 4 and _parts[0] == 'grid':
                _size = float(_parts[1]); _row = float(_parts[2]); _col = float(_parts[3])
                _ox, _oy = _col * _size, _row * _size
                _cell = gpd.GeoDataFrame(geometry=[_box(_ox, _oy, _ox + _size, _oy + _size)], crs=_crs)
                _cell_4326 = _cell.to_crs('EPSG:4326').geometry.iloc[0]
            else:
                raise HTTPException(status_code=400, detail=f'cell_id 格式错误: {req.cell_id}（期望 grid_{"{size}"}_{"{row}"}_{"{col}"}）')
        else:
            # 质心 + cell_size → 4546 建格（格原点 = floor(质心/cs)*cs·行/列号回算）
            _cell_size = float(req.cell_size)
            _src = gpd.GeoDataFrame(geometry=[_Point(req.cell_lng, req.cell_lat)], crs='EPSG:4326')
            _p = _src.to_crs(_crs).geometry.iloc[0]
            _row = int(math.floor(_p.y / _cell_size))
            _col = int(math.floor(_p.x / _cell_size))
            _ox, _oy = _col * _cell_size, _row * _cell_size
            _cell = gpd.GeoDataFrame(geometry=[_box(_ox, _oy, _ox + _cell_size, _oy + _cell_size)], crs=_crs)
            _cell_4326 = _cell.to_crs('EPSG:4326').geometry.iloc[0]

        # POI 点（WGS84）→ sjoin 格内（iterrows 保留 shapely geometry·to_dict 会丢 geometry 类型）
        _poi_gdf = gpd.GeoDataFrame(
            _pois, geometry=[_Point(_p.get('lng', 0), _p.get('lat', 0)) for _p in _pois], crs='EPSG:4326')
        _in = _poi_gdf[_poi_gdf.intersects(_cell_4326)]
        _out = []
        for _idx, _r in _in.iterrows():
            _out.append({
                'name': str(_r.get('name', '')),
                'category': str(_r.get('baidu_level1', _r.get('category', ''))),
                'domain': str(_r.get('domain', '')),
                'element': str(_r.get('element', '')),
                'lng': round(float(_r.geometry.x), 6),
                'lat': round(float(_r.geometry.y), 6),
            })
        _cell_id = req.cell_id or f'grid_{int(_cell_size)}_{int(_row)}_{int(_col)}'
        return {'success': True, 'cell_id': _cell_id, 'pois': _out, 'count': len(_out),
                'message': f'格内 {len(_out)} 处 POI（含 3220 接入）'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'grid_pois 失败: {e}')


@geo_router.post('/geo/rank')
async def rank(req: RankRequest):
    """按极性/4×5 找 Top N 单元。boundary 给定→点聚合后排序；空→对已聚合 layer 直接排序。"""
    try:
        _guard_usage_refs(req.layer, req.range, req.boundary)
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
        # P3-4（CB-19）：加地点字段（同 zonal）——rank rows 也带 place_name/place_name_source/poi_names/poi_count
        prop_cols = ['name', 'point_count', 'polarity_index', 'score_mean',
                     'domain_top', 'element_top', 'issue_label',
                     'place_name', 'place_name_source', 'poi_names', 'poi_count']
        _props = _props_df(gdf, prop_cols)
        rows = _props.where(pd.notna(_props), '').to_dict('records')
    except (KeyError, FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'rank 失败: {e}')
    return {'success': True, 'by': by, 'rows': rows}


# ════════════ 7. buffer · 缓冲区 ════════════
class BufferRequest(_GeoBase):
    center: Any                       # preset_id | GeoJSON（缓冲中心面/点）
    radius_m: float = 500.0
    agg_cols: Optional[list] = None   # 可选聚合列（如 ['score']）；与 layer 同传时焊圈内点情绪统计


@geo_router.post('/geo/buffer')
async def buffer(req: BufferRequest):
    """生成中心要素的缓冲区（米制精确）。返回缓冲面域 GeoJSON + 面积；传 layer 时焊上圈内点聚合
   （point_count/polarity_index/domain_top/...，消除 buffer→zonal 断点）。省略 layer → 逐字节同原（向后兼容）。"""
    try:
        _guard_usage_refs(req.center, req.layer, req.range)
        center = resolve_boundary(req.center)
    except (FileNotFoundError, ValueError):
        # CB-15 P1（A）：str center 非 preset → 尝试中文名 search_place 取坐标（AI/前端共用一处）
        #   边界：只对 str center（GeoJSON dict 已是坐标）·top-1 命中·无命中诚实 400（禁编造坐标）·search_place 返回 WGS84
        if isinstance(req.center, str) and req.center.strip():
            from core.geocode import search_place
            _hits = search_place(req.center.strip(), limit=1)
            if not _hits:
                raise HTTPException(status_code=400,
                                    detail=f'center 无法解析：{req.center}（非 preset_id/GeoJSON/POI 名·请改用已加载范围或上传）')
            _h = _hits[0]
            center = gpd.GeoDataFrame({'name': [_h['name']]},
                                      geometry=[_Point(_h['lng'], _h['lat'])], crs='EPSG:4326')
        else:
            raise
    try:
        proj = center.to_crs(_PROJECT_CRS)
        buf = proj.geometry.buffer(float(req.radius_m))
        names = center['name'].tolist() if 'name' in center.columns else ['缓冲区'] * len(center)
        buf_gdf = gpd.GeoDataFrame({'name': names},
                                   geometry=buf.values, crs=_PROJECT_CRS).to_crs('EPSG:4326')
        buf_gdf['area_km2'] = (buf.area / 1e6).round(3)
        # 可选聚合：传 layer → 焊圈内点情绪统计到 buf_gdf（buf_gdf 已 4326，pts 默认 4326，sjoin within 对齐）；
        # 空 sjoin/无点 → ValueError 降级纯几何（buf_gdf 不变）。省略 layer → 不进此分支，buf_gdf 逐字节同原。
        if req.layer is not None:
            try:
                pts = _prepare_points(req.layer, req.range, req.pre_filter)
                agg_cols = req.agg_cols or (['score'] if 'score' in pts.columns else [])
                buf_gdf = aggregate_by_polygons(pts, buf_gdf, agg_cols=agg_cols, polygon_name_col='name')
            except ValueError:
                pass
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
        _guard_usage_refs(req.layer_a, req.layer_b)
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
        _guard_usage_refs(req.layer, req.target)
        pts = resolve_points(req.layer)
        target = resolve_boundary(req.target)
        # layer 必须为点；target 可为点（点-点最近邻）或面（每个面找最近点，如"每个行政区离最近的负面点"）
        pts = pts[pts.geometry.geom_type == 'Point']
        if len(pts) == 0:
            raise ValueError('layer 需为点要素')
        if len(target) == 0:
            raise ValueError('target 无要素')
        pts_proj = pts.to_crs(_PROJECT_CRS)
        tgt_proj = target.to_crs(_PROJECT_CRS)
        # distance_col：取真实最近距离（修复 distance 恒 0.0——此前未传 distance_col，fallback 全 0，演示数据失真）
        joined = gpd.sjoin_nearest(tgt_proj, pts_proj, distance_col='distance')
        joined['distance'] = joined['distance'].round(1)
        # A1 连线坐标（前端连线层用·additive 列，不改配对逻辑/核心算法）：
        # target 代表点 + 最近点，均转 WGS84；.loc 按标签对齐（唯一 index），to_numpy 保查询序。
        tgt_rp = gpd.GeoSeries(tgt_proj.geometry.representative_point(), crs=_PROJECT_CRS).to_crs('EPSG:4326')
        tgt_rp = tgt_rp.loc[joined.index]
        right_geom = gpd.GeoSeries(
            pts_proj.geometry.loc[joined['index_right'].to_numpy()].to_numpy(), crs=_PROJECT_CRS
        ).to_crs('EPSG:4326')
        joined['tgt_lon'] = tgt_rp.x.to_numpy().round(6)
        joined['tgt_lat'] = tgt_rp.y.to_numpy().round(6)
        joined['pt_lon'] = right_geom.x.to_numpy().round(6)
        joined['pt_lat'] = right_geom.y.to_numpy().round(6)
        joined = joined.drop(columns='geometry', errors='ignore')
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
    # P1 软分级透传（W2 审计）：threshold/soft_threshold——默认 1.96/1.0（前端可不传）
    threshold: float = 1.96
    soft_threshold: float = 1.0


@geo_router.post('/geo/hotspot')
async def hotspot(req: HotspotRequest):
    """Gi* 热点分析：识别情绪冷热点空间聚类。返回点 + Gi_Z/hotspot 五档分类（截断）。"""
    try:
        _guard_usage_refs(req.layer, req.range)   # 复审修复 H2：首轮漏挂（Codex 审计·实测 200 反例）
        pts = _prepare_points(req.layer, req.range, req.pre_filter)
        if req.value_col not in pts.columns:
            raise ValueError(f'value_col {req.value_col} 不存在（可用 {list(pts.columns)[:20]}…）')
        pts = pts[pts.geometry.geom_type == 'Point'].copy()
        # P1 软分级（W2 审计）：透传 threshold/soft_threshold（五档·诚实标倾向聚集）
        res = hot_spot_analysis(pts, value_col=req.value_col, invert=req.invert,
                                threshold=req.threshold, soft_threshold=req.soft_threshold)
        fc = _to_geojson(res)
    except (KeyError, FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f'依赖缺失: {e}（Gi* 需 pip install libpysal esda）')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'hotspot 失败: {e}')
    return {'success': True, 'geojson': fc, 'count': fc['_total'],
            'truncated': fc['_truncated'],
            # W3 审计：legend 五档（显著 95%/倾向 84% 对称·诚实标注非"显著热点"）
            'legend': {'hot': '显著聚集(95%)', 'tend_hot': '倾向聚集(84%)', 'ns': '不显著',
                       'tend_cold': '倾向冷区(84%)', 'cold': '显著冷区(95%)'}}
