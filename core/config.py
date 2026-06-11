"""
全局配置 — 消除散布各文件的魔法字符串
══════════════════════════════════════════════════════════════
"""

# ── 天地图 Key ──
# 获取：https://console.tianditu.gov.cn → 创建应用 → 浏览器端
TIANDITU_KEY = '4d4dc85287c003c8a18d5520b8920796'

# ── 天地图瓦片 URL 模板 ──
TIANDITU_IMG_URL = (
    'https://t0.tianditu.gov.cn/img_w/wmts?'
    'SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0'
    '&LAYER=img&STYLE=default&TILEMATRIXSET=w'
    '&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}'
    f'&tk={TIANDITU_KEY}'
)

TIANDITU_CVA_URL = (
    'https://t0.tianditu.gov.cn/cva_w/wmts?'
    'SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0'
    '&LAYER=cva&STYLE=default&TILEMATRIXSET=w'
    '&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}'
    f'&tk={TIANDITU_KEY}'
)

# ── 数据路径 ──
RAW_DIR = 'data/raw'
PROCESSED_DIR = 'data/processed'

# ── 文件夹选项 ──
FOLDER_OPTIONS = {
    '[DATA] processed（处理结果）': PROCESSED_DIR,
    '[DATA] raw（原始数据）': RAW_DIR,
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
COLOR_MAP = {
    'Very Positive': '#1a7a1a',
    'Positive':      '#28a745',
    'Neutral':       '#6c757d',
    'Negative':      '#e8590c',
    'Very Negative': '#dc3545',
}

FOLIUM_COLOR_MAP = {
    'Very Positive': 'darkgreen',
    'Positive':      'green',
    'Neutral':       'gray',
    'Negative':      'orange',
    'Very Negative': 'red',
}

# ── L2 情绪关键词提取配置 ──
KEYWORD_MIN_LEN = 2        # 关键词最小长度
KEYWORD_TOP_N = 5          # 每条文本提取关键词数

# ── 热点图默认参数 ──
HEATMAP_DEFAULTS = {
    'radius': 15,
    'blur': 10,
    'min_opacity': 0.4,
    'max_zoom': 18,
}

# ── 冷热分布渐变色带 ──
GRADIENT_HOTCOLD = {
    0.0: '#cce5ff',   # 冷（稀疏）- 浅蓝
    0.3: '#ffffb2',   # 过渡 - 浅黄
    0.6: '#fdae61',   # 中密度 - 橙
    0.8: '#f46d43',   # 高密度 - 橙红
    1.0: '#a50026',   # 热（密集）- 深红
}

# ── 极性分布渐变色带 ──
GRADIENT_POSITIVE = {
    0.0: '#004529',   # 深绿
    0.3: '#238b45',   # 翠绿
    0.6: '#74c476',   # 浅绿
    0.85: '#c7e9c0',  # 淡绿
    1.0: '#ffffcc',   # 黄
}

GRADIENT_NEGATIVE = {
    0.0: '#252525',   # 深灰
    0.3: '#636363',   # 中灰
    0.6: '#bdbdbd',   # 浅灰
    0.85: '#f0f0f0',  # 极浅灰
    1.0: '#ffffcc',   # 黄
}

# ── CDN 替换（国内镜像）──
CDN_REPLACEMENTS = {
    'cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js':
        'cdn.bootcdn.net/ajax/libs/leaflet/1.9.3/leaflet.js',
    'cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css':
        'cdn.bootcdn.net/ajax/libs/leaflet/1.9.3/leaflet.css',
    'cdn.jsdelivr.net/gh/python-visualization/folium@main/folium/templates/leaflet_heat.min.js':
        'cdn.bootcdn.net/ajax/libs/leaflet.heat/0.2.0/leaflet-heat.js',
}

# ── 初始默认坐标（宜昌）──
DEFAULT_CENTER = [30.708, 111.286]
DEFAULT_ZOOM = 12
