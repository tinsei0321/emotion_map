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


class BufferRequest(BaseModel):
    """缓冲分析请求（覆盖范围）。"""
    geojson: dict = Field(..., description="输入图层 GeoJSON FeatureCollection")
    distance: float = Field(..., gt=0, description="缓冲距离（数值）")
    unit: str = Field(default="m", description="距离单位: m | km")
    dissolve: bool = Field(default=False, description="True=合并所有缓冲为单一覆盖区")


class ExportRequest(BaseModel):
    """图层导出请求。"""
    geojson: dict = Field(..., description="待导出图层 GeoJSON FeatureCollection（WGS84）")
    format: str = Field(default="geojson", description="格式: geojson | csv | shp")
    crs: str = Field(default="wgs84", description="坐标系: wgs84 | cgcs2000（仅 shp 生效；geojson 固定 WGS84）")
    geom_csv: str = Field(default="wkt", description="CSV 几何表示: wkt | lonlat | none（仅 csv 生效）")
    desensitize: bool = Field(default=True, description="脱敏：剥用户名/ID/手机等 PII 字段（铁律 7）")
    filename: str = Field(default="export", description="输出文件名（不含扩展名）")


# ── 地点搜索 / 地理编码（Phase 2）──

class PlaceHit(BaseModel):
    """单条地点搜索命中。坐标一律 WGS84。"""
    name: str
    lng: float
    lat: float
    category: str = Field(default="", description="类别（本地 baidu_level / 高德 type）")
    baidu_level1: str = Field(default="", description="高德一级类别（审计用）")
    baidu_level2: str = Field(default="", description="高德二级类别（审计用）")
    area: str = Field(default="", description="片区（area 字段，审计用）")
    zone_id: str = Field(default="", description="所在叙事区 ID（本地命中时填）")
    zone_name: str = Field(default="", description="所在区中文名（本地命中时填）")
    address: str = Field(default="", description="街道地址（高德命中时填）")
    score: float = Field(default=0.0, description="匹配分（本地模糊分；高德=0）")
    source: str = Field(default="local", description="local | amap")
    data_source: str = Field(default="", description="数据源审计：amap(高德库) | seed(手标) | amap-api(补全)")


class PlaceSearchResponse(BaseModel):
    """地点搜索响应。"""
    success: bool = True
    query: str = ""
    hits: List[PlaceHit] = Field(default_factory=list)
    source: str = Field(default="", description="主力源：local | amap | mixed")


class GeocodeResult(BaseModel):
    """正向地理编码（地址→坐标）。坐标 WGS84。"""
    success: bool
    query: str = ""
    lng: float = 0.0
    lat: float = 0.0
    formatted_address: str = ""
    source: str = ""


class ReverseGeocodeResult(BaseModel):
    """逆地理编码（坐标→地名）。输入输出坐标均为 WGS84。"""
    success: bool = True
    lng: float
    lat: float
    zone_id: str = ""
    zone_name: str = ""
    nearest_poi: Optional[dict] = None
    formatted_address: str = Field(default="", description="街道地址（高德 regeo 命中时填）")
    source: str = ""
