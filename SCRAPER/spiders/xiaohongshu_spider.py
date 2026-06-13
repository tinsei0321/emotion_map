"""
小红书爬虫 — 城市情绪数据采集
================================
爬虫名: xiaohongshu
目标: 搜索"规划范围"相关笔记，提取标题 + 正文
输出: EmotionItem → EmotionalDataPipeline → data/raw/

=== 小红书反爬注意事项（实际对接时务必处理）===
1. Cookie / 登录态 — 小红书大部分接口需要登录，需在请求中携带
   Cookie（从浏览器手动导出或通过 Selenium 登录获取）。
2. 验证码 — 高频访问会触发滑块验证码，需接入打码平台或手动处理。
3. API 签名 — 小红书 API 有 x-s / x-t 等签名参数，需逆向 JS 或
   使用 playwright/selenium 绕过。
4. 内容加密 — 部分接口返回的文本是加密的，需解密。
5. 频率限制 — 短时间内请求过多会被封 IP。

=== 推荐实际对接方案 ===
- 方案 A: Selenium / Playwright 模拟浏览器 + 手动扫码登录
- 方案 B: 使用第三方小红书 API（如 xsph_api）→ 需付费
- 方案 C: 抓取 web 版搜索结果页（限制较多，但无需登录）
- 方案 D: 购买数据（稳定但成本高）

当前实现为方案 C 的骨架版本 + requests 快速验证，
实际生产需切换到方案 A 或 B。
"""

import json
import re
from datetime import datetime

import scrapy
from scrapy.http import Request

from items import EmotionItem


class XiaohongshuSpider(scrapy.Spider):
    name = 'xiaohongshu'
    allowed_domains = ['xiaohongshu.com', 'xhslink.com']
    start_urls = ['https://www.xiaohongshu.com/explore']

    # ── 搜索配置 ──
    search_keyword = '\u89c4\u5212\u8303\u56f4'   # 规划范围
    target_area = '\u89c4\u5212\u8303\u56f4'       # 规划范围

    def __init__(self, keyword=None, area=None, max_pages=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if keyword:
            self.search_keyword = keyword
        if area:
            self.target_area = area
        self.max_pages = int(max_pages)
        self.page_count = 0

    def parse(self, response):
        """解析探索页：从 __INITIAL_STATE__ 的 feed.feeds 提取 noteCard 列表。"""
        self.page_count += 1
        current_page = response.meta.get('page', 1)

        self.logger.info(
            f'[LOAD] Parsing explore page {current_page}: {response.url}'
        )

        script_data = self._extract_initial_state(response.text)
        if not script_data:
            self.logger.warning('[WARN] No __INITIAL_STATE__ found')
            return

        # 从 feed.feeds 提取笔记
        feed_data = script_data.get('feed', {})
        feeds = feed_data.get('feeds', [])
        self.logger.info(f'[LOAD] Found {len(feeds)} feed items')

        note_count = 0
        for feed_item in feeds:
            note_card = feed_item.get('noteCard', {})
            if not note_card:
                continue
            note_count += 1
            yield self._build_item_from_note_card(feed_item.get('id', ''), note_card)

        self.logger.info(f'[OK] Scraped {note_count} notes from page {current_page}')

    def _extract_initial_state(self, html):
        """从 HTML 中提取 window.__INITIAL_STATE__ JSON 数据。"""
        match = re.search(
            r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>',
            html, re.DOTALL
        )
        if match:
            try:
                # 替换 undefined → null 以便 JSON 解析
                raw = match.group(1)
                raw = re.sub(r':\s*undefined', ': null', raw)
                return json.loads(raw)
            except json.JSONDecodeError:
                self.logger.warning('[WARN] Failed to parse __INITIAL_STATE__ JSON')
        return None

    def _parse_notes_from_json(self, data):
        """从 __INITIAL_STATE__ JSON 中提取笔记列表（兼容 explore 页 feed 结构）。"""
        feed_data = data.get('feed', {})
        feeds = feed_data.get('feeds', [])
        notes = []
        for feed_item in feeds:
            note_card = feed_item.get('noteCard', {})
            if note_card:
                note_card['_feed_id'] = feed_item.get('id', '')
                notes.append(note_card)
        return notes

    @staticmethod
    def _parse_count(value):
        """解析小红书计数格式: '5.7万' -> 57000, '8800' -> 8800, '' -> 0"""
        if not value:
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        value = str(value).strip()
        if not value:
            return 0
        if '万' in value:
            try:
                return int(float(value.replace('万', '')) * 10000)
            except ValueError:
                return 0
        try:
            return int(value.replace(',', ''))
        except ValueError:
            return 0

    def _build_item_from_note_card(self, feed_id, note_card):
        """从 noteCard 构建 EmotionItem（explore 页格式）。"""
        item = EmotionItem()
        item['source'] = 'xiaohongshu'
        title = note_card.get('displayTitle', note_card.get('title', ''))
        desc = note_card.get('desc', '')
        item['title'] = title
        # 探索页通常只有标题，desc 可能为空，合并 title 作为正文
        item['text'] = desc if desc and len(desc.strip()) >= 5 else title
        item['url'] = f'https://www.xiaohongshu.com/explore/{feed_id}'
        item['area'] = self.target_area
        item['tags'] = [
            t.get('name', str(t)) for t in note_card.get('tagList', [])
            if isinstance(t, dict)
        ]
        interact = note_card.get('interactInfo', {})
        item['like_count'] = self._parse_count(interact.get('likedCount', 0))
        item['comment_count'] = self._parse_count(interact.get('commentCount', 0))
        item['publish_time'] = note_card.get('time', '')
        item['crawl_time'] = datetime.now().isoformat()
        return item

    def _build_item_from_html(self, note_sel, response):
        """从 HTML 选择器构建 EmotionItem（备用方案）。"""
        item = EmotionItem()
        item['source'] = 'xiaohongshu'

        title_sel = note_sel.css('a.title::text, span.title::text').get()
        item['title'] = title_sel.strip() if title_sel else ''

        desc_sel = note_sel.css('div.desc::text, p.desc::text, a.sub-title::text').get()
        item['text'] = desc_sel.strip() if desc_sel else ''

        href = note_sel.css('a::attr(href)').get()
        if href:
            item['url'] = response.urljoin(href)
        else:
            item['url'] = response.url

        item['area'] = self.target_area
        item['tags'] = note_sel.css('span.tag::text').getall()
        item['crawl_time'] = datetime.now().isoformat()
        return item

    def _quick_verify(self, url):
        """
        快速验证：用 requests 尝试直接请求，确认网络可达性。
        此方法不参与 Scrapy 数据流，仅作诊断输出。
        """
        try:
            import requests
            resp = requests.get(
                url,
                headers={
                    'User-Agent': (
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/125.0.0.0 Safari/537.36'
                    ),
                },
                timeout=15,
                allow_redirects=True,
            )
            _safe_print(
                f'[QUICK-VERIFY] {url[:80]}... '
                f'status={resp.status_code}, '
                f'len={len(resp.text)} chars'
            )
            # 检查是否被重定向到登录页
            if 'login' in resp.url.lower() or '验证' in resp.text[:2000]:
                _safe_print(
                    '[WARN] xiaohongshu likely requires login/verification. '
                    'Consider Selenium/Playwright approach.'
                )
        except Exception as e:
            _safe_print(f'[QUICK-VERIFY] Failed: {e}')


# ── 安全打印（兼容 Windows GBK 控制台）──
def _safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = tuple(
            str(a).encode('ascii', errors='replace').decode('ascii')
            for a in args
        )
        print(*safe_args, **kwargs)


# ── 独立运行入口（快速测试）──
if __name__ == '__main__':
    from scrapy import cmdline
    cmdline.execute(
        ['scrapy', 'runspider', __file__, '-a', 'max_pages=1']
    )
