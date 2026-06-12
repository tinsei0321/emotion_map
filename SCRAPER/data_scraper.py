"""
数据爬取引擎 — 多源数据采集器 (统一入口)
==========================================
基于 Scrapy 2.x，提供多平台数据采集的统一 Python API。

支持的平台:
  - xiaohongshu  小红书（城市体验笔记）
  - dianping     大众点评（POI 评价）[待实现]
  - meituan      美团（商户评论）[待实现]
  - weibo        微博（签到/话题）[待实现]
  - su12345      12345 热线（投诉工单）[待实现]

使用方式:
  # 方式1: 命令行
  cd SCRAPER && scrapy crawl xiaohongshu -a area=西陵区

  # 方式2: Python API
  from SCRAPER.data_scraper import run_scraper
  run_scraper('xiaohongshu', area='西陵区', max_pages=3)

  # 方式3: 单独调用
  from SCRAPER.data_scraper import scrape_xiaohongshu
  scrape_xiaohongshu(area='西陵区', max_pages=3)

输出格式: {source}_{date}_{area}_raw.csv → data/raw/
"""

import os
import sys
import subprocess
from datetime import datetime

# ── 确保 SCRAPER/ 目录可被 Python 导入 ──
_SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRAPER_DIR not in sys.path:
    sys.path.insert(0, _SCRAPER_DIR)


def _safe_print(*args, **kwargs):
    """安全打印，兼容 Windows GBK 控制台编码。"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = tuple(
            str(a).encode('ascii', errors='replace').decode('ascii')
            for a in args
        )
        print(*safe_args, **kwargs)


class EmotionScraper:
    """
    多源数据采集器 — 统一管理所有平台爬虫。

    属性:
        available_spiders: 已注册的爬虫名称列表
    """

    available_spiders = ['xiaohongshu']

    def __init__(self):
        self._spiders_dir = os.path.join(_SCRAPER_DIR, 'spiders')

    def list_spiders(self):
        """列出所有可用爬虫。"""
        return self.available_spiders

    def run(self, spider_name, **kwargs):
        """
        运行指定爬虫。

        Args:
            spider_name: 爬虫名称 (xiaohongshu / dianping / ...)
            **kwargs: 传递给爬虫的参数 (area, keyword, max_pages 等)

        Returns:
            int: 进程退出码 (0=成功)
        """
        if spider_name not in self.available_spiders:
            _safe_print(f'[WARN] Unknown spider: {spider_name}')
            _safe_print(f'[LOAD] Available spiders: {self.available_spiders}')
            return 1

        cmd = ['scrapy', 'crawl', spider_name]

        for key, value in kwargs.items():
            cmd.extend(['-a', f'{key}={value}'])

        _safe_print(f'[LOAD] Running: {" ".join(cmd)}')
        result = subprocess.run(
            cmd,
            cwd=_SCRAPER_DIR,
        )
        return result.returncode


def run_scraper(spider_name='xiaohongshu', **kwargs):
    """
    快捷函数：运行指定爬虫。

    Args:
        spider_name: 爬虫名称
        **kwargs: 爬虫参数 (area, keyword, max_pages 等)
    """
    scraper = EmotionScraper()
    exit_code = scraper.run(spider_name, **kwargs)
    if exit_code == 0:
        _safe_print(f'[OK] Spider "{spider_name}" completed successfully.')
    else:
        _safe_print(f'[ERR] Spider "{spider_name}" exited with code {exit_code}.')
    return exit_code


# ── 平台专用快捷函数 ──

def scrape_xiaohongshu(area='西陵区', keyword=None, max_pages=3):
    """
    爬取小红书搜索笔记。

    Args:
        area: 区域标签，默认 '西陵区'
        keyword: 搜索关键词，默认与 area 相同
        max_pages: 最大翻页数，默认 3

    Returns:
        int: 退出码
    """
    if keyword is None:
        keyword = area
    _safe_print(
        f'[LOAD] Starting xiaohongshu scraper: '
        f'area={area}, keyword={keyword}, max_pages={max_pages}'
    )
    return run_scraper(
        'xiaohongshu',
        area=area,
        keyword=keyword,
        max_pages=max_pages,
    )


def scrape_dianping(area='西陵区', keyword=None, max_pages=3):
    """爬取大众点评 POI 评价。[待实现]"""
    _safe_print('[WARN] dianping spider not yet implemented.')
    return 1


def scrape_meituan(area='西陵区', keyword=None, max_pages=3):
    """爬取美团商户评论。[待实现]"""
    _safe_print('[WARN] meituan spider not yet implemented.')
    return 1


def scrape_weibo(area='西陵区', keyword=None, max_pages=3):
    """爬取微博签到/话题。[待实现]"""
    _safe_print('[WARN] weibo spider not yet implemented.')
    return 1


def scrape_su12345(area='西陵区', keyword=None, max_pages=3):
    """爬取 12345 热线投诉工单。[待实现]"""
    _safe_print('[WARN] su12345 spider not yet implemented.')
    return 1


# ── 直接运行入口 ──
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Emotion Map — Multi-source Data Scraper'
    )
    parser.add_argument(
        'spider', nargs='?', default='xiaohongshu',
        choices=['xiaohongshu', 'list'],
        help='Spider name to run (default: xiaohongshu)'
    )
    parser.add_argument(
        '--area', default='西陵区',
        help='Target area label (default: 西陵区)'
    )
    parser.add_argument(
        '--keyword', default=None,
        help='Search keyword (default: same as area)'
    )
    parser.add_argument(
        '--max-pages', type=int, default=3,
        help='Maximum pages to scrape (default: 3)'
    )

    args = parser.parse_args()

    if args.spider == 'list':
        scraper = EmotionScraper()
        _safe_print(f'Available spiders: {scraper.list_spiders()}')
    else:
        run_scraper(
            args.spider,
            area=args.area,
            keyword=args.keyword or args.area,
            max_pages=args.max_pages,
        )
