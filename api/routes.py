"""
API 路由 — 分析 / 治理 / 数据查询
"""
import os
import sys
from fastapi import APIRouter, HTTPException, Query, Response

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.schemas import (
    AnalysisRequest, AnalysisResponse, PolarityStats,
    HealthResponse, DataListResponse, GovernanceRequest,
    BufferRequest, ExportRequest,
    SpatialAggregateRequest, SpatialGridRequest, SpatialTerrainRequest,
    PlaceHit, PlaceSearchResponse, GeocodeResult, ReverseGeocodeResult,
)
from core.config import RAW_DIR, PROCESSED_DIR, BOUNDARY_SHP
from core.geocode import search_place, geocode_address, reverse_geocode

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """服务健康检查。"""
    return HealthResponse()


@router.get("/data", response_model=DataListResponse)
async def list_data():
    """列出可用数据文件。"""
    raw_files = []
    if os.path.exists(RAW_DIR):
        raw_files = sorted([
            f for f in os.listdir(RAW_DIR)
            if f.endswith('.csv') and '_result_' not in f.lower()
        ])

    processed_files = []
    if os.path.exists(PROCESSED_DIR):
        processed_files = sorted([
            f for f in os.listdir(PROCESSED_DIR)
            if f.endswith('.csv')
        ])

    return DataListResponse(
        raw_files=raw_files,
        processed_files=processed_files,
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def run_analysis(req: AnalysisRequest):
    """运行情绪分析任务。

    支持 L2 SnowNLP / L3 LLM / L4 Corpus 三档引擎，
    以及 L2→L3→L4 全管道模式。
    """
    if not os.path.exists(req.file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {req.file_path}")

    from SCRIPT.emotion_analysis_v1 import run_analysis_task

    output_name = req.output_name or os.path.splitext(
        os.path.basename(req.file_path)
    )[0].replace('_raw', '').replace('_RAW', '')

    result = run_analysis_task(
        file_path=req.file_path,
        engine_type=req.engine_type,
        output_name=output_name,
        api_key=req.api_key,
        enable_keywords=req.enable_keywords,
        full_pipeline=req.full_pipeline,
        multimodal=req.multimodal,
    )

    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('message', '分析失败'))

    stats = result.get('polarity_stats', {})
    return AnalysisResponse(
        success=True,
        n_points=result['n_points'],
        csv_path=result['csv_path'],
        geojson_path=result.get('geojson_path', ''),
        message=result['message'],
        polarity_stats=PolarityStats(
            very_positive=stats.get('Very Positive', 0),
            positive=stats.get('Positive', 0),
            neutral=stats.get('Neutral', 0),
            negative=stats.get('Negative', 0),
            very_negative=stats.get('Very Negative', 0),
        ),
        score_mean=result.get('score_mean', 0.0),
    )


@router.post("/governance")
async def run_governance(req: GovernanceRequest):
    """运行 L0→L1 数据治理管道（复用 run_governance_pipeline，含 LLM 相关性漏斗）。

    步骤: 坐标转换 → (可选)空间范围过滤 → DeepSeek LLM 相关性分类 →
          筛 relevant+has_location → 脱敏 → 导出 L1。

    需要 DEEPSEEK_API_KEY 环境变量；缺失或 LLM 失败时返回明确错误，
    **不静默降级为 keyword-only 假 L1**（与 CLI/Streamlit 走同一管道）。
    """
    if not os.path.exists(req.file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {req.file_path}")

    from SCRIPT.data_governance import run_governance_pipeline
    from core.range_selector import get_active_boundary_path

    # 输出命名（保持向后兼容的 _规划范围 后缀）
    output_name = req.output_name or os.path.splitext(
        os.path.basename(req.file_path)
    )[0].replace('_raw', '').replace('_RAW', '')
    output_name = f'{output_name}_规划范围'

    # 边界解析优先级: 显式传参 > 激活态范围 > 默认规划范围 Shapefile
    boundary_path = req.boundary_path or get_active_boundary_path()
    if not boundary_path and os.path.exists(BOUNDARY_SHP):
        boundary_path = BOUNDARY_SHP

    result = run_governance_pipeline(
        csv_path=req.file_path,
        output_name=output_name,
        boundary_path=boundary_path,
        run_l2=False,
    )

    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('message', '治理失败'))

    return {
        'success': True,
        'input_n': result['input_n'],
        'spatial_n': result['spatial_n'],
        'relevant_n': result['relevant_n'],
        'output_n': result['output_n'],
        'l1_path': result['l1_path'],
        'message': result['message'],
    }


@router.post("/spatial/buffer")
async def create_buffer_route(req: BufferRequest):
    """缓冲区分析（覆盖范围）：对输入图层做 N 米缓冲，返回缓冲区 GeoJSON。

    内部重投影到 EPSG:4546（CGCS2000 CM 111E，米制）保证米级精度；
    适配两类数据源（投影 shp / 地理坐标）——输入统一为 WGS84 GeoJSON，
    源 CRS 在前端导入时已消解。用 shapely+pyproj（非 geopandas），3.14 友好。
    """
    from core.buffer_analysis import create_buffer

    fc = req.geojson or {}
    feats = fc.get('features') if isinstance(fc, dict) else None
    if not feats:
        raise HTTPException(status_code=400, detail="输入图层为空或非 GeoJSON")

    distance_m = req.distance * (1000.0 if req.unit == 'km' else 1.0)
    try:
        out_fc, total_area = create_buffer(fc, distance_m=distance_m, dissolve=req.dissolve)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"缓冲分析失败: {e}")

    return {
        'success': True,
        'buffer_geojson': out_fc,
        'covered_area_km2': total_area,
        'feature_count': len(out_fc['features']),
        'message': f'已生成 {len(out_fc["features"])} 个缓冲区，总覆盖 {total_area} km²',
    }


@router.post("/spatial/aggregate")
async def aggregate_route(req: SpatialAggregateRequest):
    """空间聚合 - 指定单元：情绪点按面域聚合（行政区/城市更新单元/控规单元/用地分类）。

    输入均 WGS84 GeoJSON；aggregate_by_polygons 直接 sjoin（面域尺度 within 可接受，
    亚米级精度需求留待后续内投影）。返回每面域带 point_count/score_mean/五级极性计数/
    polarity_index 的 GeoJSON。
    """
    import json
    import geopandas as gpd
    from core.spatial_analysis import aggregate_by_polygons

    pf = (req.points_geojson or {}).get('features') if isinstance(req.points_geojson, dict) else None
    gf = (req.polygons_geojson or {}).get('features') if isinstance(req.polygons_geojson, dict) else None
    if not pf or not gf:
        raise HTTPException(status_code=400, detail="points_geojson / polygons_geojson 需为非空 GeoJSON")

    try:
        pts = gpd.GeoDataFrame.from_features(pf, crs='EPSG:4326')
        polys = gpd.GeoDataFrame.from_features(gf, crs='EPSG:4326')
        merged = aggregate_by_polygons(
            pts, polys, agg_cols=req.agg_cols, polygon_name_col=req.name_col,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"空间聚合失败: {e}")

    fc = json.loads(merged.to_json())
    n = len(fc.get('features', []))
    return {
        'success': True,
        'geojson': fc,
        'feature_count': n,
        'message': f'已聚合 {n} 个面域',
    }


@router.post("/spatial/grid")
async def grid_route(req: SpatialGridRequest):
    """空间聚合 - 标准网格(方格) / 核密度 H3：点→网格聚合统一入口。

    grid_type='square'→create_square_grid(cell_size, unit)（EPSG:4546 量米制方格）；
    grid_type='hex'   →create_hex_grid(resolution)（H3，需 pip install h3）。
    返回带 point_count/score_mean/五级极性/polarity_index 的网格 GeoJSON。
    """
    import json
    import geopandas as gpd
    from core.spatial_analysis import create_square_grid

    feats = (req.geojson or {}).get('features') if isinstance(req.geojson, dict) else None
    if not feats:
        raise HTTPException(status_code=400, detail="geojson 需为非空点 GeoJSON")
    if req.grid_type not in ('hex', 'square'):
        raise HTTPException(status_code=400, detail="grid_type 必须 hex | square")

    try:
        pts = gpd.GeoDataFrame.from_features(feats, crs='EPSG:4326')
        if req.grid_type == 'hex':
            from core.spatial_analysis import create_hex_grid
            grid = create_hex_grid(pts, resolution=req.resolution)
            label = f'H3 res={req.resolution}'
        else:
            grid = create_square_grid(pts, cell_size=req.cell_size, unit=req.unit)
            label = f'方格 {req.cell_size}{req.unit}'
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"依赖缺失: {e}（hex 需 pip install h3）")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"网格聚合失败: {e}")

    fc = json.loads(grid.to_json())
    n = len(fc.get('features', []))
    return {
        'success': True,
        'geojson': fc,
        'feature_count': n,
        'message': f'已生成 {n} 个{label}格',
    }


@router.post("/spatial/terrain")
async def terrain_route(req: SpatialTerrainRequest):
    """情绪地形 - KDE 等值面 mesh：密度×强度 → 分层 fill-extrusion 曲面（无边界分析）。

    综合：高度=密度×强度(_level)，颜色=区域内 polarity_index(_norm, terrain-9)。
    极性（积极/消极/中性）：先过滤点，高度=密度×强度，颜色=该极性密度(green-3/red-3/blue-3)。
    返回等值面 GeoJSON（features 按 _level 升序，低环先画、高压顶）。
    """
    import json
    import geopandas as gpd
    from core.spatial_analysis import create_terrain_mesh

    feats = (req.geojson or {}).get('features') if isinstance(req.geojson, dict) else None
    if not feats:
        raise HTTPException(status_code=400, detail="geojson 需为非空点 GeoJSON")
    if req.polarity not in ('overall', 'positive', 'negative', 'neutral'):
        raise HTTPException(status_code=400, detail="polarity 必须 overall | positive | negative | neutral")

    try:
        pts = gpd.GeoDataFrame.from_features(feats, crs='EPSG:4326')
        mesh = create_terrain_mesh(
            pts, polarity=req.polarity, bandwidth_m=req.bandwidth_m,
            cell_m=req.cell_m, n_levels=req.levels,
        )
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"依赖缺失: {e}（需 pip install matplotlib）")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"情绪地形生成失败: {e}")

    fc = json.loads(mesh.to_json())
    n = len(fc.get('features', []))
    pol_label = {'overall': '综合', 'positive': '积极', 'negative': '消极', 'neutral': '中性'}[req.polarity]
    return {
        'success': True,
        'geojson': fc,
        'feature_count': n,
        'message': f'已生成 {pol_label}情绪地形 · {n} 层等值面',
    }


@router.post("/export")
async def export_route(req: ExportRequest):
    """图层导出：GeoJSON FeatureCollection → geojson / csv / shp(.zip) 下载流。

    geopandas 后端（core/export.export_layer）—— shp.zip 含 .shp/.dbf/.shx/.prj/.cpg，
    CRS 可选 WGS84 / CGCS2000(4546)；geojson 固定 WGS84（RFC 7946）；脱敏剥 PII。
    """
    from core.export import export_layer

    fc = req.geojson or {}
    feats = fc.get('features') if isinstance(fc, dict) else None
    if not feats:
        raise HTTPException(status_code=400, detail="输入图层为空或非 GeoJSON")

    try:
        data, fname, media = export_layer(
            fc, fmt=req.format, crs=req.crs, geom_csv=req.geom_csv,
            desensitize=req.desensitize, filename=req.filename or 'export',
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {e}")

    # Content-Disposition 头强制 latin-1,CJK 文件名会 UnicodeEncodeError → 未捕获 500。
    # 用 RFC 6266 双声明:filename= ASCII 兜底 + filename*=UTF-8 百分号编码
    #（浏览器优先 filename*，保留中文文件名；修手画层「绘制多边形」导出 500）。
    from urllib.parse import quote
    try:
        fname.encode('ascii')
        ascii_fb = fname                  # 本身 ASCII,直接作 filename=
    except UnicodeEncodeError:
        ext = fname.rsplit('.', 1)[-1] if '.' in fname else ''
        ascii_fb = f'export.{ext}' if ext else 'export'   # CJK → ASCII 兜底
    cd = f"attachment; filename=\"{ascii_fb}\"; filename*=UTF-8''{quote(fname)}"
    return Response(
        content=data, media_type=media,
        headers={'Content-Disposition': cd},
    )


# ── 地点搜索 / 地理编码（Phase 2）──────────────────────────────────
# 红线：AMAP_KEY 只在服务端 core/geocode.py 读 .env，绝不进前端；
#       高德返回 GCJ-02，core/geocode.py 已统一 gcj02_to_wgs84（坐标一律 WGS84 出）。
# 前端同源 fetch：GET /api/v1/place/search | /geocode | /reverse-geocode（serve.py 反代 :8000）。

@router.get("/place/search", response_model=PlaceSearchResponse)
async def place_search_route(
    q: str = Query(..., min_length=1, description="搜索关键词（地名/POI/类别）"),
    limit: int = Query(10, ge=1, le=30, description="返回条数上限"),
):
    """地点搜索：本地 1270 POI 即时（rapidfuzz）+ 高德 place/text 兜底。坐标 WGS84。"""
    try:
        hits = search_place(q, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"地点搜索失败: {e}")
    local_n = sum(1 for h in hits if h.get('source') == 'local')
    if not hits:
        source = ""
    elif local_n == len(hits):
        source = "local"
    elif local_n == 0:
        source = "amap"
    else:
        source = "mixed"
    return PlaceSearchResponse(success=True, query=q, hits=hits, source=source)


@router.get("/geocode", response_model=GeocodeResult)
async def geocode_route(
    q: str = Query(..., min_length=1, description="地址字符串"),
):
    """正向地理编码：地址 → 坐标（WGS84）。高德 geo 正向（GCJ-02→WGS84）。"""
    try:
        res = geocode_address(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"地理编码失败: {e}")
    if not res:
        return GeocodeResult(success=False, query=q)
    return GeocodeResult(
        success=True, query=q,
        lng=res['lng'], lat=res['lat'],
        formatted_address=res.get('formatted_address', ''),
        source=res.get('source', 'amap'),
    )


@router.get("/reverse-geocode", response_model=ReverseGeocodeResult)
async def reverse_geocode_route(
    lng: float = Query(..., description="经度（WGS84）"),
    lat: float = Query(..., description="纬度（WGS84）"),
):
    """逆地理编码：坐标(WGS84) → 所在区 + 最近 POI + 街道地址 + 行政区划(区/街道/路)。

    本地 place_layer.reverse 主（瞬时）；高德可用 → always regeo(extensions=all)
    补街道地址 + 区/街道/路（lru_cache 摊销重复坐标延迟）。
    """
    try:
        res = reverse_geocode(lng, lat)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"逆地理编码失败: {e}")
    return ReverseGeocodeResult(
        success=True, lng=lng, lat=lat,
        zone_id=res.get('zone_id', ''),
        zone_name=res.get('zone_name', ''),
        nearest_poi=res.get('nearest_poi'),
        formatted_address=res.get('formatted_address', ''),
        district=res.get('district', ''),
        township=res.get('township', ''),
        street=res.get('street', ''),
        source=res.get('source', 'local'),
    )
