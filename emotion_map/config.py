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
    '📂 processed（处理结果）': PROCESSED_DIR,
    '📂 raw（原始数据）': RAW_DIR,
}

# ── 情绪颜色映射 ──
COLOR_MAP = {
    'Positive': '#28a745',
    'Neutral': '#6c757d',
    'Negative': '#dc3545',
}

FOLIUM_COLOR_MAP = {
    'Positive': 'green',
    'Neutral': 'gray',
    'Negative': 'red',
}

# ── 情绪阈值 ──
SCORE_POSITIVE = 0.7   # ≥ 此值 = 正面
SCORE_NEGATIVE = 0.3   # ≤ 此值 = 负面

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
