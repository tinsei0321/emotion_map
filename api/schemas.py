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


class SpatialAggregateRequest(BaseModel):
    """空间聚合 - 指定单元：情绪点按面域聚合（行政区/更新单元/控规/用地等）。"""
    points_geojson: dict = Field(..., description="情绪点 GeoJSON FeatureCollection (WGS84)")
    polygons_geojson: dict = Field(..., description="聚合面域 GeoJSON FeatureCollection (WGS84)")
    agg_cols: Optional[List[str]] = Field(default=None, description="数值统计列，默认 ['score']")
    name_col: Optional[str] = Field(default=None, description="面域名称列（输出保留）")


class SpatialGridRequest(BaseModel):
    """空间聚合 - 标准网格(方格) / 核密度 H3：点→网格聚合统一入口。"""
    geojson: dict = Field(..., description="情绪点 GeoJSON FeatureCollection (WGS84)")
    grid_type: str = Field(default="square", description="hex | square")
    resolution: int = Field(default=8, ge=0, le=15, description="H3 分辨率（grid_type=hex 时）")
    cell_size: float = Field(default=200, gt=0, description="方格边长（grid_type=square 时）")
    unit: str = Field(default="m", description="cell_size 单位: m | km")


class SpatialTerrainRequest(BaseModel):
    """情绪地形 - KDE 等值面 mesh：密度×强度 → 分层 fill-extrusion 曲面。"""
    geojson: dict = Field(..., description="情绪点 GeoJSON FeatureCollection (WGS84)")
    polarity: str = Field(default="overall", description="overall | positive | negative | neutral")
    bandwidth_m: float = Field(default=250, gt=0, description="KDE 高斯带宽（米），控制曲面平滑度")
    cell_m: float = Field(default=60, gt=0, description="KDE 栅格边长（米），越小越细越慢")
    levels: int = Field(default=7, ge=3, le=15, description="等值面层数")


class RangePresetItem(BaseModel):
    """预设范围条目（一个按钮 = 一个矢量文件）。"""
    id: str = Field(..., description="预设 id（前端 loadPresetRange 用）")
    label: str = Field(..., description="按钮显示名（行政区/街道/社区/更新单元/商业区…）")
    file: str = Field(..., description="DATA/boundaries/presets/ 下的文件名")
    nameField: Optional[str] = Field(default=None, description="名称字段（grid-tool name_col 默认）")
    available: bool = Field(default=False, description="文件是否已上传")


class RangePresetGroup(BaseModel):
    """预设范围分组（行政区划/城市更新单元/用地筛选）。"""
    group: str = Field(..., description="分组名")
    items: List[RangePresetItem] = Field(default_factory=list)


class RangePresetUploadRequest(BaseModel):
    """预设范围上传（前端解析好的 WGS84 GeoJSON）。"""
    id: str = Field(..., description="预设 id（manifest 中的 item.id）")
    geojson: dict = Field(..., description="WGS84 GeoJSON FeatureCollection")


class ChatRequest(BaseModel):
    """AI 问答请求（provider-agnostic，默认 DeepSeek）。"""
    messages: List[dict] = Field(..., description="OpenAI 兼容消息数组 [{role,content}]")
    context: Optional[str] = Field(default=None, description="前端计算的数据摘要（grounding）")
    model: Optional[str] = Field(default=None, description="模型：留空=默认Flash；deepseek-reasoner=深度思考(Pro，带思考链)")
    context_tokens: Optional[List[dict]] = Field(default=None, description="用户@关联对象(feature/range/layer/pin)，注入 grounding")


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
    zone_color: str = Field(default="", description="zone 颜色 hex（前端色点用）")
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
    district: str = Field(default="", description="行政区划·区（高德 regeo）")
    township: str = Field(default="", description="街道/乡镇（高德 regeo）")
    street: str = Field(default="", description="道路名（高德 regeo）")
    source: str = ""
