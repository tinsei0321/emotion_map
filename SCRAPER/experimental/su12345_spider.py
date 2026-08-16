"""
12345 热线数据 Spider — 城市政务投诉数据采集

数据源: 各地 12345 政务服务便民热线公开数据
采集策略（按数据来源分）:
  1. 政府开放数据平台 (data.xx.gov.cn) — CSV/API
  2. 政务公开 — 12345 月度/季度报告 PDF
  3. 地方领导留言板 (liuyan.people.com.cn) — 公开投诉/建议

字段映射 (12345 → L0 标准格式):
  投诉内容/诉求 → comments
  投诉时间 → publish_time
  投诉地点/地址 → location_name
  处理状态 → process_status
  承办单位 → department
  投诉类别(市容/噪音/物业等) → category (预处理)

注意事项:
  - 12345 数据通常为 CSV/Excel 导出，不需要爬取网页
  - 地方政府开放数据平台需要注意 API Key 申请流程
  - 宜昌数据: 可通过宜昌市政务服务和大数据管理局获取
  - 部分数据含个人隐私（电话/姓名），L1 治理必须脱敏
"""
import os
import csv
import json
import scrapy
from datetime import datetime


class Su12345Spider(scrapy.Spider):
    name = 'su12345'
    allowed_domains = ['data.xx.gov.cn', 'liuyan.people.com.cn']

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 2,
        'ROBOTSTXT_OBEY': True,
    }

    def __init__(self, csv_path=None, api_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.csv_path = csv_path
        self.api_url = api_url

    def start_requests(self):
        # 策略1: 从本地 CSV 导入（最常见场景）
        if self.csv_path and os.path.exists(self.csv_path):
            yield from self._read_csv(self.csv_path)
            return

        # 策略2: 地方领导留言板 API
        if self.api_url:
            yield scrapy.Request(
                self.api_url,
                callback=self.parse_api,
                headers={'Accept': 'application/json'},
            )
            return

        # 策略3: 人民网地方领导留言板（默认）
        yield scrapy.Request(
            'https://liuyan.people.com.cn/threads/list?fid=42',
            callback=self.parse_liuyan,
        )

    def _read_csv(self, csv_path: str):
        """从本地 12345 CSV 导出文件中逐行读取并转换为 L0 格式。

        支持的列名（自动检测）:
          诉求内容/投诉内容/问题描述/留言内容 → comments
          诉求时间/投诉时间/提交时间 → publish_time
          地址/地点/区域 → location_name
          经度/纬度 → lon/lat
        """
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    yield self._csv_row_to_item(row)
        except Exception as e:
            self.logger.error(f'CSV 读取失败: {csv_path} — {e}')

    def _csv_row_to_item(self, row: dict) -> dict:
        """将 12345 CSV 行映射为 L0 标准格式。"""
        # 列名自动检测（常见变体）
        text_cols = ['诉求内容', '投诉内容', '问题描述', '留言内容',
                     'content', 'text', 'description', 'comments']
        time_cols = ['诉求时间', '投诉时间', '提交时间', 'create_time', 'time']
        loc_cols = ['地址', '地点', '区域', 'location', 'address', 'area']
        lon_cols = ['经度', 'lon', 'longitude', 'lng']
        lat_cols = ['纬度', 'lat', 'latitude']

        def _first_match(cols):
            for c in cols:
                if c in row and row[c]:
                    return str(row[c]).strip()
            return ''

        text = _first_match(text_cols)
        pub_time = _first_match(time_cols)
        location = _first_match(loc_cols)
        lon_str = _first_match(lon_cols)
        lat_str = _first_match(lat_cols)

        # 坐标转换
        lon = None
        lat = None
        try:
            if lon_str:
                lon = float(lon_str)
            if lat_str:
                lat = float(lat_str)
        except (ValueError, TypeError):
            pass

        return {
            'source': '12345',
            'source_url': row.get('url', row.get('link', '')),
            'comments': text,
            'publish_time': pub_time,
            'lon': lon,
            'lat': lat,
            'location_name': location,
            'category': row.get('category', row.get('类别', '')),
            'department': row.get('department', row.get('承办单位', '')),
            'status': row.get('status', row.get('处理状态', '')),
            'crawled_at': datetime.now().isoformat(),
        }

    def parse_api(self, response):
        """解析 API JSON 响应。"""
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f'API JSON 解析失败: {response.url}')
            return

        items = data.get('data', data.get('items', data.get('list', [])))
        for item in items:
            yield self._api_item_to_l0(item)

    def _api_item_to_l0(self, item: dict) -> dict:
        """API 返回的 dict → L0 标准格式。"""
        return {
            'source': '12345',
            'source_url': item.get('url', ''),
            'comments': item.get('content', item.get('text', '')),
            'publish_time': item.get('create_time', item.get('time', '')),
            'lon': item.get('lon', item.get('longitude')),
            'lat': item.get('lat', item.get('latitude')),
            'location_name': item.get('address', item.get('location', '')),
            'category': item.get('category', ''),
            'department': item.get('department', ''),
            'crawled_at': datetime.now().isoformat(),
        }

    def parse_liuyan(self, response):
        """解析人民网地方领导留言板列表页。"""
        threads = response.css('.thread-item, .message-item, li.item')
        for thread in threads:
            title = thread.css('a::text').get('')
            link = thread.css('a::attr(href)').get('')
            if link:
                yield response.follow(
                    link,
                    callback=self.parse_liuyan_detail,
                    meta={'title': title},
                )

    def parse_liuyan_detail(self, response):
        """解析留言详情页。"""
        title = response.meta.get('title', '')
        content = response.css('.content, .message-content, .detail-content::text').get('')
        location = response.css('.location, .address::text').get('')
        pub_time = response.css('.time, .date, .publish-time::text').get('')

        yield {
            'source': '12345-people',
            'source_url': response.url,
            'comments': f'{title}\n{content}' if title else content,
            'publish_time': pub_time,
            'location_name': location,
            'crawled_at': datetime.now().isoformat(),
        }
