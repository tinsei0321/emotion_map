"""
微博 Spider — 基于搜索 API 的城市情绪数据采集

数据源: https://m.weibo.cn/
采集策略:
  1. 位置搜索 API: /api/container/getIndex?containerid=100101{geohash}
  2. 关键词搜索: /api/container/getIndex?containerid=100103type=1&q={keyword}
  3. 需要登录 Cookie（SUB=...; SUP=...）才能获取完整数据

字段映射 (微博 → L0 标准格式):
  微博正文 text → comments
  发布时间 created_at → publish_time
  发布位置 region_name → location_name
  微博 URL scheme → source_url
  图片 pic_ids → image_urls
  转发/评论/点赞数 → engagement metrics

注意事项:
  - 微博 API 有严格的频率限制（约 150 次/小时，非认证开发者）
  - 位置搜索需要 geohash 编码（可通过 nominatim 或高德 API 获取）
  - 移动端 API (m.weibo.cn) 比 PC 端更容易解析
  - 请在 Scrapy settings.py 中配置 ROTATING_USER_AGENT 和 DOWNLOAD_DELAY >= 3
"""
import json
import scrapy
from datetime import datetime


class WeiboSpider(scrapy.Spider):
    name = 'weibo'
    allowed_domains = ['m.weibo.cn', 'weibo.com']

    # 宜昌西陵区 geohash（约 100km 范围）
    # 可通过 nominatim API 获取精确 geohash
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 1,
        'ROBOTSTXT_OBEY': False,
    }

    def __init__(self, keywords=None, geohash=None, max_pages=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keywords = keywords or '宜昌,西陵,城市规划,环境,噪音,绿化'
        self.geohash = geohash
        self.max_pages = max_pages
        self.page = 1

    def start_requests(self):
        # 策略1: 位置搜索（不需要关键词，按地理位置）
        if self.geohash:
            location_url = (
                f'https://m.weibo.cn/api/container/getIndex'
                f'?containerid=100101{self.geohash}'
            )
            yield scrapy.Request(location_url, callback=self.parse_location)

        # 策略2: 关键词搜索
        for kw in self.keywords.split(','):
            kw = kw.strip()
            if not kw:
                continue
            search_url = (
                f'https://m.weibo.cn/api/container/getIndex'
                f'?containerid=100103type%3D1%26q%3D{kw}'
                f'&page={self.page}'
            )
            yield scrapy.Request(
                search_url,
                callback=self.parse_search,
                meta={'keyword': kw, 'page': 1},
            )

    def parse_location(self, response):
        """解析位置搜索 API 响应（SSR JSON）。"""
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f'位置搜索 JSON 解析失败: {response.url}')
            return

        cards = data.get('data', {}).get('cards', [])
        for card in cards:
            if card.get('card_type') != 9:
                continue
            mblog = card.get('mblog', {})
            if mblog:
                yield self._extract_item(mblog)

    def parse_search(self, response):
        """解析关键词搜索 API 响应，递归翻页。"""
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f'搜索 JSON 解析失败: {response.url}')
            return

        cards = data.get('data', {}).get('cards', [])
        for card in cards:
            if card.get('card_type') != 9:
                continue
            mblog = card.get('mblog', {})
            if mblog:
                yield self._extract_item(mblog)

        # 翻页
        page = response.meta.get('page', 1)
        if page < self.max_pages:
            kw = response.meta.get('keyword', '')
            next_page = page + 1
            next_url = (
                f'https://m.weibo.cn/api/container/getIndex'
                f'?containerid=100103type%3D1%26q%3D{kw}'
                f'&page={next_page}'
            )
            yield scrapy.Request(
                next_url,
                callback=self.parse_search,
                meta={'keyword': kw, 'page': next_page},
            )

    def _extract_item(self, mblog: dict) -> dict:
        """提取单条微博为 L0 标准格式。"""
        created_at = mblog.get('created_at', '')
        text = mblog.get('text_raw', mblog.get('text', ''))
        # 清理 HTML 标签
        import re
        text = re.sub(r'<[^>]+>', '', text)

        # 坐标（如果有签到/位置信息）
        geo = None
        if 'geo' in mblog and mblog['geo']:
            geo = mblog['geo'].get('coordinates', [None, None])

        # 图片
        pics = mblog.get('pics', [])
        image_urls = [p.get('url', '') for p in pics]

        return {
            'source': 'weibo',
            'source_url': f"https://m.weibo.cn/detail/{mblog.get('id', '')}",
            'comments': text,
            'publish_time': created_at,
            'lon': geo[1] if geo else None,
            'lat': geo[0] if geo else None,
            'image_urls': json.dumps(image_urls, ensure_ascii=False),
            'likes': mblog.get('attitudes_count', 0),
            'reposts': mblog.get('reposts_count', 0),
            'comments_count': mblog.get('comments_count', 0),
            'user_name': mblog.get('user', {}).get('screen_name', ''),
            'location_name': mblog.get('region_name', ''),
            'crawled_at': datetime.now().isoformat(),
        }
