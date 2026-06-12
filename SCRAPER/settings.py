"""
Scrapy 全局设置 — emotion_map 数据采集系统
============================================
所有 Spider 共享的下载器、管道、编码等配置。
"""

# ── 爬虫名称 ──
BOT_NAME = 'emotion_map_scraper'

# ── 模块路径 ──
SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

# ── 遵守 robots.txt ──
# 设为 False：小红书/大众点评等平台的 robots.txt 通常会禁止搜索页
# 初期研究用途，需控制频率和并发，避免对目标服务器造成压力
ROBOTSTXT_OBEY = False

# ── 下载延迟（礼貌爬取，1~3 秒随机）──
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True

# ── 并发请求数（初期保守）──
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# ── User-Agent ──
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/125.0.0.0 Safari/537.36'
)

# ── 默认请求头 ──
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# ── 启用 Pipeline ──
ITEM_PIPELINES = {
    'pipelines.EmotionDataPipeline': 300,
}

# ── 输出编码 ──
FEED_EXPORT_ENCODING = 'utf-8'

# ── 日志级别 ──
LOG_LEVEL = 'INFO'

# ── 重试设置 ──
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# ── 下载超时 ──
DOWNLOAD_TIMEOUT = 30

# ── 自动限速（AutoThrottle，替代固定延迟时可启用）──
AUTOTHROTTLE_ENABLED = False

# ── Cookies 默认禁用（各 Spider 按需开启）──
COOKIES_ENABLED = False

# ── Telnet 控制台（调试用）──
TELNETCONSOLE_ENABLED = False
