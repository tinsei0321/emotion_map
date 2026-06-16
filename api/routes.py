"""
API 路由 — 分析 / 治理 / 数据查询
"""
import os
import sys
from fastapi import APIRouter, HTTPException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.schemas import (
    AnalysisRequest, AnalysisResponse, PolarityStats,
    HealthResponse, DataListResponse, GovernanceRequest,
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
    """运行 L0→L1 数据治理管道。

    步骤: 坐标转换 → 范围过滤 → 相关性筛选 → 脱敏 → 导出 L1
    """
    if not os.path.exists(req.file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {req.file_path}")

    from SCRIPT.data_governance import step1_load_and_transform
    from core.range_selector import load_boundaries, filter_by_range, get_active_boundary_path
    from core.export import export_to_csv

    # Step 1: 坐标转换
    df = step1_load_and_transform(req.file_path)
    input_n = len(df)

    # Step 2: 范围过滤
    boundary_path = req.boundary_path or get_active_boundary_path()
    if not boundary_path and os.path.exists(BOUNDARY_SHP):
        boundary_path = BOUNDARY_SHP

    if boundary_path and os.path.exists(boundary_path):
        import pandas as pd
        ranges = load_boundaries(boundary_path)
        df_filtered = filter_by_range(df, 'lon', 'lat', ranges, None)
        df = pd.DataFrame(df_filtered)
    else:
        import pandas as pd
        df = pd.DataFrame(df)

    # Step 3: 关键词粗筛
    from SCRIPT.relevance_filter import keyword_prefilter, _build_text_for_classification
    df['_kw_pass'] = df.apply(
        lambda row: keyword_prefilter(_build_text_for_classification(row)) == 'pass',
        axis=1
    )
    df = df[df['_kw_pass']].copy()
    df['relevance'] = 'relevant'
    df['filter_layer'] = 'keyword'
    df.drop(columns=['_kw_pass'], inplace=True, errors='ignore')

    # Step 4: 脱敏 + 导出
    if 'comments' in df.columns:
        df['comments'] = ''

    output_name = req.output_name or os.path.splitext(
        os.path.basename(req.file_path)
    )[0].replace('_raw', '').replace('_RAW', '')
    output_name = f'{output_name}_规划范围'
    l1_path = os.path.join(PROCESSED_DIR, f'{output_name}_L1_result_csv.csv')
    export_to_csv(df, l1_path)

    return {
        'success': True,
        'input_n': input_n,
        'output_n': len(df),
        'l1_path': l1_path,
        'message': f'L1 治理完成: {input_n} → {len(df)} 条',
    }
