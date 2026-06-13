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
MAX_DISPLAY_POINTS = 5000      # 地图最大显示点数，超出自动采样
MAX_TABLE_ROWS = 2000          # 数据表格最大行数
LARGE_FILE_WARN_MB = 50        # 文件大小警告阈值 (MB)

# ── 初始默认坐标（宜昌）──
DEFAULT_CENTER = [30.708, 111.286]
DEFAULT_ZOOM = 12
