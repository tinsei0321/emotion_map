"""
Scrapy 数据模型 — 统一情绪数据 Item
=====================================
所有 Spider 输出统一的 EmotionItem，便于管道统一处理。
"""

import scrapy


class EmotionItem(scrapy.Item):
    """城市情绪数据条目 — 多源统一结构"""

    # ── 元信息 ──
    source = scrapy.Field()
    """数据来源: xiaohongshu / dianping / meituan / weibo / 12345"""

    url = scrapy.Field()
    """来源链接（用于去重和溯源）"""

    crawl_time = scrapy.Field()
    """爬取时间 (ISO 8601 字符串)"""

    # ── 文本内容 ──
    title = scrapy.Field()
    """标题（如有）"""

    text = scrapy.Field()
    """评论文本 / 笔记正文（核心分析字段）"""

    # ── 空间信息 ──
    lon = scrapy.Field()
    """经度 (float, 可选)"""

    lat = scrapy.Field()
    """纬度 (float, 可选)"""

    area = scrapy.Field()
    """区域标签，如 '西陵区'"""

    # ── 扩展字段 ──
    tags = scrapy.Field()
    """标签/话题列表 (list[str], 可选)"""

    like_count = scrapy.Field()
    """点赞数 (int, 可选)"""

    comment_count = scrapy.Field()
    """评论数 (int, 可选)"""

    publish_time = scrapy.Field()
    """发布时间（原始平台时间字符串）"""
