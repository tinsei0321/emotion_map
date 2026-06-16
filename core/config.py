"""
全局配置 — 消除散布各文件的魔法字符串
══════════════════════════════════════════════════════════════
"""

# ── 天地图 Key（保留，向后兼容）──
TIANDITU_KEY = '4d4dc85287c003c8a18d5520b8920796'

# ── 数据路径（绝对路径，跨平台一致）──
import os as _os
_PROJECT_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
RAW_DIR = _os.path.join(_PROJECT_ROOT, 'DATA', 'raw')
PROCESSED_DIR = _os.path.join(_PROJECT_ROOT, 'DATA', 'processed')

# ── 边界文件路径（规划范围 Shapefile）──
BOUNDARY_SHP = _os.path.join(_PROJECT_ROOT, 'DATA', 'boundaries', '规划范围', '规划范围.shp')

# ── 文件夹选项 ──
FOLDER_OPTIONS = {
    '[DATA] raw（原始数据）': RAW_DIR,
    '[DATA] processed（处理结果）': PROCESSED_DIR,
}

# ── 情绪极性阈值（五级制，为城市更新/治理/运营优化）──
# 设计思路：
#   - 三级制（正面/中性/负面）太粗糙，无法区分"严重问题"和"一般不满"
#   - 五级制让决策者更精确地定位问题等级和资源投入优先级
#   - 区间划分参考 SnowNLP 实际分布特征（中部集中、两端稀疏）
POLARITY_THRESHOLDS = {
    'Very Negative':   (0.00, 0.20),   # 严重不满 → 需紧急干预
    'Negative':        (0.20, 0.40),   # 一般负面 → 需关注改善
    'Neutral':         (0.40, 0.60),   # 中性/无明显情绪
    'Positive':        (0.60, 0.80),   # 一般正面 → 维持即可
    'Very Positive':   (0.80, 1.00),   # 非常满意 → 可作为标杆
}

# ── 三级极性（保持向后兼容）──
SCORE_POSITIVE = 0.7   # ≥ 此值 = 正面
SCORE_NEGATIVE = 0.3   # ≤ 此值 = 负面

# ── 情绪颜色映射（五级制）──
# 设计原则：蓝绿→蓝→白→橙黄→红，低饱和适中明度
# 在天地图卫星影像（深色底图）上清晰可辨
# 颜色渐变：蓝绿(清新) → 蓝(平静) → 浅灰(中性) → 琥珀橙(紧张) → 珊瑚红(紧迫)
COLOR_MAP = {
    'Very Positive': '#48C9B0',   # 蓝绿 — 清新活泼
    'Positive':      '#5DADE2',   # 蓝 — 平静正面
    'Neutral':       '#C0C0C0',   # 浅灰 — 中性
    'Negative':      '#F0A050',   # 琥珀橙 — 紧张感
    'Very Negative': '#E06050',   # 珊瑚红 — 紧迫感
}

# Folium 渲染专用色映射（与 COLOR_MAP 保持一致）
FOLIUM_COLOR_MAP = {
    'Very Positive': '#48C9B0',
    'Positive':      '#5DADE2',
    'Neutral':       '#C0C0C0',
    'Negative':      '#F0A050',
    'Very Negative': '#E06050',
}

# ── L2 情绪关键词提取配置 ──
KEYWORD_MIN_LEN = 2        # 关键词最小长度
KEYWORD_TOP_N = 5          # 每条文本提取关键词数

# ── pydeck 极性颜色映射（RGBA 格式：[R, G, B, A] 0-255）──
# 蓝绿 → 蓝 → 浅灰 → 琥珀橙 → 珊瑚红
POLARITY_RGBA = {
    'Very Positive': [120, 220, 50, 230],   # #78DC32 黄绿
    'Positive':      [93, 173, 226, 230],   # #5DADE2 蓝
    'Neutral':       [192, 192, 192, 230],  # #C0C0C0 浅灰
    'Negative':      [196, 149, 106, 230],  # #C4956A 茶色
    'Very Negative': [185, 45, 45, 230],    # #B92D2D 深红色
}

# ── 地图渲染安全阈值 ──
MAX_TABLE_ROWS = 2000          # 数据表格最大行数
LARGE_FILE_WARN_MB = 50        # 文件大小警告阈值 (MB)

# ── 分级渲染策略 (Tiered Rendering) ──
# 根据数据量自动调整点样式，确保 10~100k+ 数据流畅渲染。
# 参考: Kepler.gl LOD、Mapbox cluster、Deck.gl radiusScale
RENDER_TIERS = [
    # (max_points, label,   radius_m, opacity, stroke_w,  description)
    (5000,    'S·标准',      100,      0.85,    1.0,       '所有点完整显示，情绪颜色清晰可辨'),
    (20000,   'M·密集',       60,      0.75,    0.5,       '点半径缩小、半透明描边，减少重叠遮挡'),
    (50000,   'L·紧凑',       30,      0.65,    0.0,       '无描边微点，适合宏观分布观察'),
    (100000,  'XL·热力',      None,    None,    None,      '自动切换热力图模式 (可手动切回散点)'),
    (float('inf'), 'XXL·抽样', None,  None,    None,      '分层抽样保留情绪分布 + 热力图叠加'),
]
# 向后兼容
MAX_DISPLAY_POINTS = RENDER_TIERS[-2][0]  # 100k — 超出任何一级即触发最后一层

# ── 矢量文件上载安全阈值 ──
UPLOAD_MAX_FILE_SIZE_MB = 100        # 单文件最大大小 (MB)
UPLOAD_MAX_GEOJSON_VERTICES = 50000  # GeoJSON 顶点总数上限，超出自动简化
UPLOAD_MAX_SHAPEFILE_FEATURES = 20000 # Shapefile 要素数上限，超出自动简化
UPLOAD_SIMPLIFY_TOLERANCE = 0.0001   # 道格拉斯-普克简化容差（约10m@赤道）
UPLOAD_PARSE_TIMEOUT_SEC = 30        # 文件解析超时 (秒)

# ── 矢量图层默认样式 ──
# 多图层自动差异化配色方案（HSL 色相均匀分布，支持无限数量图层）
DEFAULT_BOUNDARY_STYLE = {
    "line_color": [255, 140, 0],     # 橙色 RGB
    "line_width": 20,                 # 线宽 px
    "fill": False,                    # 默认不填充面
    "fill_color": [255, 140, 0, 80], # 面颜色 RGBA
    "fill_opacity": 0.3,             # 面不透明度
}
# 自动差异化色板（前8个图层的默认颜色，超出则HSL计算）
LAYER_PALETTE = [
    [255, 140, 0],     # 橙色
    [0, 200, 255],     # 青色
    [255, 80, 80],     # 红色
    [80, 255, 120],    # 绿色
    [255, 220, 0],     # 黄色
    [180, 130, 255],   # 紫色
    [255, 160, 180],   # 粉色
    [100, 220, 200],   # 蓝绿
]

# ── 初始默认坐标（宜昌）──
DEFAULT_CENTER = [30.708, 111.286]
DEFAULT_ZOOM = 12

# ── 多模态 API 端点（L3 Vision + OCR + Audio）──
# 火山引擎 Ark Vision (Chat Completions API)
VOLCENGINE_VISION_URL = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
# 火山引擎 Ark 多模态 Embedding
VOLCENGINE_EMBED_URL = 'https://ark.cn-beijing.volces.com/api/v3/embeddings/multimodal'
# 讯飞 OCR API
IFLYTEK_OCR_URL = 'https://api.xf-yun.com/v1/ocr'

# ── 多模态分析阈值 ──
VISION_CONFIDENCE_THRESHOLD = 0.6     # 视觉分析最低置信度（低于此值结果标记为低置信）
VISION_MAX_IMAGES_PER_POST = 9        # 单条数据最多分析图片数（小红书最多9图）
VISION_REQUEST_TIMEOUT = 120          # Vision API 单次请求超时（秒）
OCR_REQUEST_TIMEOUT = 60              # OCR API 单次请求超时（秒）
AUDIO_REQUEST_TIMEOUT = 300           # ASR API 单次请求超时（秒）
