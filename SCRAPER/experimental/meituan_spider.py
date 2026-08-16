"""
美团/大众点评 Spider — 城市商业情绪数据采集

数据源: 美团 (meituan.com) / 大众点评 (dianping.com)
采集策略:
  1. 商户评论 API（需分析 JS bundle 或使用 Selenium）
  2. 美团开放平台 API（需商家授权，适用于合作场景）
  3. 大众点评搜索页 + 点评详情页

字段映射 (点评 → L0 标准格式):
  点评内容/评论 → comments
  评分 → score (1-5 星级，映射到 0-1)
  发布时间 → publish_time
  商户名称 → poi_name
  商户地址 → location_name

注意事项:
  - 大众点评反爬非常严格（字体加密 CSS、滑块验证码、IP 封禁）
  - 美团相对宽松但页面结构频繁变动
  - 建议优先使用美团开放平台 API（有官方 SDK）
  - 如果必须爬取网页，强烈建议使用 Selenium + stealth.js
  - 字体加密破解: https://github.com/flyyuan/dianping-font-decoder
  - 本项目优先使用搜索页 SSR 数据（类似小红书策略），避免直接爬详情页
"""
import json
import scrapy
from datetime import datetime


class MeituanSpider(scrapy.Spider):
    name = 'meituan'
    allowed_domains = ['meituan.com', 'dianping.com']

    custom_settings = {
        'DOWNLOAD_DELAY': 5,
        'CONCURRENT_REQUESTS': 1,
        'ROBOTSTXT_OBEY': False,
        'DOWNLOADER_MIDDLEWARES': {
            'SCRAPER.middlewares.RotatingUserAgentMiddleware': 543,
        },
    }

    def __init__(self, keywords=None, city='宜昌', max_pages=5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keywords = keywords or '公园,商圈,美食,环境,服务'
        self.city = city
        self.max_pages = max_pages

    def start_requests(self):
        """
        策略: 大众点评搜索页（优先 SSR，类似小红书策略）

        搜索 URL 模式:
          https://www.dianping.com/search/keyword/{keyword}/0_0

        注意:
          - 搜索页返回 HTML 含 __INITIAL_STATE__ 或 __NEXT_DATA__ SSR JSON
          - 详情页有 CSS 字体加密，优先从搜索页提取信息
          - 首次访问需要处理验证码（手动 Cookie 或验证码识别服务）
        """
        for kw in self.keywords.split(','):
            kw = kw.strip()
            if not kw:
                continue

            # 搜索页
            search_url = (
                f'https://www.dianping.com/search/keyword/7/0_{kw}'
            )
            yield scrapy.Request(
                search_url,
                callback=self.parse_search,
                meta={'keyword': kw, 'page': 0},
                dont_filter=True,
            )

    def parse_search(self, response):
        """解析大众点评搜索页 — 提取 SSR 数据和点评摘要。"""
        keyword = response.meta.get('keyword', '')
        page = response.meta.get('page', 0)

        # 尝试从 __NEXT_DATA__ / __INITIAL_STATE__ 提取 JSON
        ssr_data = None
        for script in response.css('script::text').getall():
            if '__NEXT_DATA__' in script or '__INITIAL_STATE__' in script:
                try:
                    # 提取 JSON 部分
                    import re
                    match = re.search(r'window\.__\w+__\s*=\s*({.*?});', script, re.DOTALL)
                    if match:
                        ssr_data = json.loads(match.group(1))
                except (json.JSONDecodeError, AttributeError):
                    pass

        if ssr_data:
            # 从 SSR 数据中提取商户列表（字段名需根据实际页面调整）
            shops = (
                ssr_data.get('props', {})
                .get('initialState', {})
                .get('search', {})
                .get('list', [])
            )
            for shop in shops:
                yield self._extract_shop_item(shop, keyword)

        # 翻页
        if page < self.max_pages:
            next_page = page + 1
            next_url = (
                f'https://www.dianping.com/search/keyword/7/'
                f'{next_page}_{keyword}'
            )
            yield scrapy.Request(
                next_url,
                callback=self.parse_search,
                meta={'keyword': keyword, 'page': next_page},
            )

    def _extract_shop_item(self, shop: dict, keyword: str) -> dict:
        """从搜索列表的单个商户中提取 L0 标准字段。"""
        # 摘要评论（搜索页通常显示 1-2 条精选评论）
        reviews = shop.get('reviews', shop.get('reviewList', []))
        if isinstance(reviews, list) and reviews:
            review_text = reviews[0].get('text', reviews[0].get('content', ''))
        else:
            review_text = shop.get('abstract', '')

        return {
            'source': 'meituan-dianping',
            'source_url': shop.get('url', shop.get('shopUrl', '')),
            'poi_name': shop.get('name', shop.get('shopName', '')),
            'poi_type': shop.get('categoryName', shop.get('category', '')),
            'comments': review_text,
            'score': float(shop.get('avgScore', shop.get('star', 3.5))) / 5.0,
            'lon': shop.get('lng', shop.get('longitude')),
            'lat': shop.get('lat', shop.get('latitude')),
            'location_name': shop.get('address', shop.get('region', '')),
            'avg_price': shop.get('avgPrice', shop.get('avg_price')),
            'search_keyword': keyword,
            'crawled_at': datetime.now().isoformat(),
        }
