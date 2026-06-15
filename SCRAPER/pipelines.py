"""
Scrapy 数据管道 — 清洗 → 去重 → 导出 CSV
==========================================
处理流程:
  1. 去重：基于 url 字段去重
  2. 清洗：去除空文本、纯表情、过短文本（<5 字）
  3. 导出：自动输出到 data/raw/{source}_{date}_{area}_raw.csv
  4. 日志：每处理 10 条输出一次进度
"""

import csv
import os
import re
from datetime import datetime

from scrapy.exceptions import DropItem
from core.utils import safe_print

# ── 项目根目录（SCRAPER/ 的父目录）──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAW_DIR = os.path.join(_PROJECT_ROOT, 'data', 'raw')


# ── 安全打印（兼容 Windows GBK 控制台）──

class EmotionDataPipeline:
    """
    情绪数据清洗管道。

    功能:
    - 基于 url 去重（内存集合）
    - 过滤空文本 / 纯表情 / 短文本
    - 自动导出 CSV 到 data/raw/
    - 进度日志（每 10 条）
    """

    def __init__(self):
        self._seen_urls = set()
        self._count_total = 0
        self._count_passed = 0
        # 用于按 source 分组写 CSV
        self._csv_writers = {}  # key: source → csv.DictWriter
        self._csv_files = {}    # key: source → file handle

    def open_spider(self, spider):
        safe_print(f'[LOAD] Pipeline opened for spider: {spider.name}')
        os.makedirs(_RAW_DIR, exist_ok=True)

    def _get_csv_writer(self, source, area):
        """为指定 source+area 获取或创建 CSV writer。"""
        key = f'{source}_{area}'
        if key not in self._csv_writers:
            today = datetime.now().strftime('%Y%m%d')
            filename = f'{source}_{today}_{area}_raw.csv'
            filepath = os.path.join(_RAW_DIR, filename)
            is_new = not os.path.exists(filepath)

            f = open(filepath, 'a', newline='', encoding='utf-8')
            fieldnames = [
                'source', 'url', 'crawl_time', 'title', 'text',
                'lon', 'lat', 'area', 'tags', 'like_count',
                'comment_count', 'publish_time',
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if is_new:
                writer.writeheader()

            self._csv_writers[key] = writer
            self._csv_files[key] = f
            safe_print(f'[OK] Output file created: {filepath}')

        return self._csv_writers[key]

    def process_item(self, item, spider):
        self._count_total += 1

        # ── 1. 去重 ──
        url = item.get('url', '')
        if url and url in self._seen_urls:
            raise DropItem(f'Duplicate URL: {url}')
        if url:
            self._seen_urls.add(url)

        # ── 2. 清洗文本 ──
        text = (item.get('text') or '').strip()
        # 移除纯表情/特殊符号（保留中英文、数字、常用标点）
        cleaned_text = re.sub(r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffefa-zA-Z0-9\s.,!?;:()（）【】《》""''、。，！？；：]', '', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        if len(cleaned_text) < 5:
            raise DropItem(f'Text too short ({len(cleaned_text)} chars)')

        item['text'] = cleaned_text

        # ── 3. 设置爬取时间 ──
        if not item.get('crawl_time'):
            item['crawl_time'] = datetime.now().isoformat()

        # ── 4. 写 CSV ──
        source = item.get('source', 'unknown')
        area = item.get('area', 'unknown')
        writer = self._get_csv_writer(source, area)

        row = dict(item)
        # 将 list 字段序列化为字符串
        if isinstance(row.get('tags'), list):
            row['tags'] = '|'.join(str(t) for t in row['tags'])

        writer.writerow(row)

        self._count_passed += 1

        # ── 5. 进度日志 ──
        if self._count_passed % 10 == 0:
            safe_print(
                f'[OK] processed {self._count_passed} items '
                f'(total seen: {self._count_total})'
            )

        return item

    def close_spider(self, spider):
        # 关闭所有文件
        for f in self._csv_files.values():
            f.close()
        safe_print(
            f'[OK] Pipeline closed: {self._count_passed}/'
            f'{self._count_total} items passed.'
        )
