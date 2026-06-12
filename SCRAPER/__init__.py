"""
数据采集层 — 多源数据爬取引擎 (Scrapy)
=========================================
负责从多平台采集城市情绪相关文本数据，输出到 data/raw/。

数据源:
  - 大众点评 (POI 评价)
  - 美团 (商户评论)
  - 小红书 (城市体验笔记)
  - 微博 (签到/话题)
  - 12345 热线 (投诉工单)

技术选型: Scrapy 2.x (开源爬虫框架)
备用方案: 购买数据

快速启动:
  cd SCRAPER
  scrapy crawl xiaohongshu              # 运行小红书爬虫
  scrapy crawl xiaohongshu -a keyword=西陵区 -a max_pages=5  # 自定义参数
"""

# ── 统一入口 ──
from .data_scraper import (
    EmotionScraper,
    run_scraper,
    scrape_xiaohongshu,
)

# ── Scrapy 核心组件 ──
from .items import EmotionItem
from .pipelines import EmotionDataPipeline

__all__ = [
    'EmotionScraper',
    'run_scraper',
    'scrape_xiaohongshu',
    'EmotionItem',
    'EmotionDataPipeline',
]
