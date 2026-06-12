"""
小红书爬虫 — 城市情绪数据采集
================================
爬虫名: xiaohongshu
目标: 搜索"西陵区"相关笔记，提取标题 + 正文
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

    # ── 搜索配置 ──
    search_keyword = '\u897f\u9675\u533a'   # 西陵区（宜昌市）
    target_area = '\u897f\u9675\u533a'       # 西陵区

    def __init__(self, keyword=None, area=None, max_pages=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if keyword:
            self.search_keyword = keyword
        if area:
            self.target_area = area
        self.max_pages = int(max_pages)
        self.page_count = 0

    def start_requests(self):
        """
        入口：构建搜索 URL 并发送请求。

        小红书 web 版搜索 URL 格式（供参考，实际可能变动）:
          https://www.xiaohongshu.com/search_result?keyword={keyword}
        """
        # ── 方案 C: web 版搜索页（无需登录的基础抓取）──
        search_url = (
            'https://www.xiaohongshu.com/search_result'
            f'?keyword={self.search_keyword}&source=web_search_result_notes'
        )
        yield Request(
            url=search_url,
            callback=self.parse_search_results,
            headers={
                'Referer': 'https://www.xiaohongshu.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            },
            meta={'page': 1},
        )

        # ── 快速验证: 用 requests 尝试直接请求 ──
        self._quick_verify(search_url)

    def parse_search_results(self, response):
        """
        解析搜索结果页。

        web 版搜索结果页结构（供参考）:
          - 笔记卡片: div.note-item 或 section.note-item
          - 标题: a.title 或 span.title
          - 链接: a[href] 指向 /explore/{note_id}
          - 点赞数: span.like-count

        注意: 小红书 web 版大量使用 JS 渲染，直接 HTML 解析
        可能拿不到数据。实际对接时需用 Selenium/Playwright 预渲染。
        """
        self.page_count += 1
        current_page = response.meta.get('page', 1)

        self.logger.info(
            f'[LOAD] Parsing page {current_page}/{self.max_pages}: {response.url}'
        )

        # ── 尝试从 HTML 中提取笔记信息 ──
        # 小红书 web 版会在 <script> 中嵌入初始数据 (SSR)
        # 格式: window.__INITIAL_STATE__ = {...}
        script_data = self._extract_initial_state(response.text)
        if script_data:
            # 从 JSON 中提取笔记列表
            notes = self._parse_notes_from_json(script_data)
            for note in notes:
                yield self._build_item(note)
        else:
            # 退而求其次: HTML 解析
            notes = response.css('div.note-item, section.note-item')
            self.logger.info(
                f'[LOAD] Found {len(notes)} note cards via CSS selector'
            )
            for note in notes:
                yield self._build_item_from_html(note, response)

        # ── 翻页 ──
        if self.page_count < self.max_pages:
            # 小红书搜索翻页参数: ?keyword=xxx&page=N
            next_page = current_page + 1
            next_url = (
                'https://www.xiaohongshu.com/search_result'
                f'?keyword={self.search_keyword}'
                f'&page={next_page}'
                f'&source=web_search_result_notes'
            )
            yield Request(
                url=next_url,
                callback=self.parse_search_results,
                headers={'Referer': response.url},
                meta={'page': next_page},
            )

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
        """从 __INITIAL_STATE__ JSON 中提取笔记列表。"""
        notes = []
        try:
            # 路径依赖小红书实际数据结构，以下为参考
            search_data = data.get('search', {})
            note_list = search_data.get('notes', [])
            for item in note_list:
                note_card = item.get('noteCard', item)
                notes.append(note_card)
        except Exception as e:
            self.logger.warning(f'[WARN] JSON note extraction error: {e}')
        return notes

    def _build_item(self, note_data):
        """从 JSON note 数据构建 EmotionItem。"""
        item = EmotionItem()
        item['source'] = 'xiaohongshu'
        item['title'] = note_data.get('displayTitle', note_data.get('title', ''))
        item['text'] = note_data.get('desc', '')
        item['url'] = (
            f'https://www.xiaohongshu.com/explore/'
            f'{note_data.get("noteId", note_data.get("id", ""))}'
        )
        item['area'] = self.target_area
        item['tags'] = note_data.get('tagList', [])
        item['like_count'] = int(note_data.get('likedCount', 0) or 0)
        item['comment_count'] = int(note_data.get('commentsCount', 0) or 0)
        item['publish_time'] = note_data.get('time', '')
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
