"""
Scrapy 中间件 — UA 轮换 / 延迟 / 反爬应对
============================================
"""

import random

from scrapy import signals


class EmotionMapDownloaderMiddleware:
    """
    通用下载中间件。

    功能:
    - 请求前：随机设置 User-Agent
    - 响应后：记录异常状态码
    - 异常处理：捕获并记录下载异常
    """

    USER_AGENTS = [
        # Chrome on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        # Firefox on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
        # Edge on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
        # Safari on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
    ]

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(
            middleware.spider_opened, signal=signals.spider_opened
        )
        return middleware

    def spider_opened(self, spider):
        spider.logger.info(f'[LOAD] Middleware activated for spider: {spider.name}')

    def process_request(self, request, spider):
        # 随机 UA 轮换
        request.headers.setdefault('User-Agent', random.choice(self.USER_AGENTS))

    def process_response(self, request, response, spider):
        # 记录非正常状态码
        if response.status >= 400:
            spider.logger.warning(
                f'[WARN] HTTP {response.status} for {request.url}'
            )
        return response

    def process_exception(self, request, exception, spider):
        spider.logger.error(
            f'[ERR] Download exception for {request.url}: {exception}'
        )
