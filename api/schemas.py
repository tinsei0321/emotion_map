"""
API 数据模型 — Pydantic schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """情绪分析请求。"""
    file_path: str = Field(..., description="L1 数据文件路径")
    engine_type: str = Field(
        default="snownlp",
        description="分析引擎: snownlp | llm | corpus"
    )
    output_name: Optional[str] = Field(
        default=None,
        description="输出文件名（不含扩展名），默认从 file_path 推断"
    )
    api_key: str = Field(default="", description="LLM API Key（L3/L4 需要）")
    enable_keywords: bool = Field(default=True, description="是否提取关键词")
    full_pipeline: bool = Field(default=False, description="是否运行全管道 L2→L3→L4")
    multimodal: bool = Field(default=False, description="是否启用多模态视觉分析")


class PolarityStats(BaseModel):
    """五级极性统计。"""
    very_positive: int = Field(default=0, alias="Very Positive")
    positive: int = Field(default=0, alias="Positive")
    neutral: int = Field(default=0, alias="Neutral")
    negative: int = Field(default=0, alias="Negative")
    very_negative: int = Field(default=0, alias="Very Negative")

    model_config = {"populate_by_name": True}


class AnalysisResponse(BaseModel):
    """分析结果响应。"""
    success: bool
    n_points: int = 0
    csv_path: str = ""
    geojson_path: str = ""
    message: str = ""
    polarity_stats: PolarityStats = Field(default_factory=PolarityStats)
    score_mean: float = 0.0


class HealthResponse(BaseModel):
    """健康检查响应。"""
    status: str = "ok"
    version: str = "1.0.0"
    engines: List[str] = ["snownlp", "llm", "corpus"]


class DataListResponse(BaseModel):
    """数据文件列表。"""
    raw_files: List[str] = Field(default_factory=list)
    processed_files: List[str] = Field(default_factory=list)


class GovernanceRequest(BaseModel):
    """数据治理请求。"""
    file_path: str = Field(..., description="L0 原始数据文件路径")
    output_name: Optional[str] = Field(default=None, description="输出文件名（不含扩展名）")
    boundary_path: Optional[str] = Field(default=None, description="边界文件路径")
