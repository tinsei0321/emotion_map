"""
API 路由 — 分析 / 治理 / 数据查询
"""
import os
import sys
from fastapi import APIRouter, HTTPException, Response

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.schemas import (
    AnalysisRequest, AnalysisResponse, PolarityStats,
    HealthResponse, DataListResponse, GovernanceRequest,
    BufferRequest, ExportRequest,
)
from core.config import RAW_DIR, PROCESSED_DIR, BOUNDARY_SHP

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
