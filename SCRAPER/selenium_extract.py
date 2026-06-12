"""
Selenium 数据提取 — 小红书搜索页动态渲染抓取
==============================================
用于绕过 JS 动态加载限制，直接渲染页面提取笔记数据。
输出: data/raw/xiaohongshu_{YYYYMMDD}_xiling_raw.csv

运行方式:
    python SCRAPER/selenium_extract.py
"""

import csv
import os
import sys
import time
import re
from datetime import datetime

# ── 确保项目根目录在 sys.path 中 ──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
from webdriver_manager.chrome import ChromeDriverManager


# =====================================================================
# 安全打印 (兼容 Windows GBK 控制台)
# =====================================================================

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


# =====================================================================
# 配置
# =====================================================================

CHROME_BINARY_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SEARCH_URL = "https://www.xiaohongshu.com/search_result?keyword=西陵区"
SCROLL_COUNT = 3
SCROLL_PAUSE = 2.0          # 每次滚动后等待秒数
PAGE_LOAD_WAIT = 5          # 初始加载等待秒数
ELEMENT_WAIT_TIMEOUT = 10   # WebDriverWait 超时秒数

# 输出路径 (相对于项目根目录)
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "data", "raw")
SCREENSHOT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "screenshot.png"
)
PAGE_SOURCE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "page_source.html"
)


# =====================================================================
# Chrome 驱动初始化
# =====================================================================

def build_chrome_options():
    """构建 Chrome 选项，尽可能隐藏自动化特征。"""
    opts = Options()

    # 使用系统安装的 Chrome
    opts.binary_location = CHROME_BINARY_PATH

    # 基础反检测参数
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")

    # 窗口大小（模拟正常浏览器）
    opts.add_argument("--window-size=1920,1080")

    # 隐藏 "Chrome 正受到自动测试软件的控制" 提示
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    # User-Agent（使用较新版本 Chrome）
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )

    # 禁用图片加载（加速抓取，若需截图则注释此行）
    # prefs = {"profile.managed_default_content_settings.images": 2}
    # opts.add_experimental_option("prefs", prefs)

    return opts


def create_driver():
    """创建并返回配置好的 Chrome WebDriver 实例。"""
    _safe_print("[LOAD] Setting up ChromeDriver via webdriver-manager ...")
    service = Service(ChromeDriverManager().install())
    opts = build_chrome_options()
    driver = webdriver.Chrome(service=service, options=opts)

    # 进一步隐藏 webdriver 属性
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    _safe_print("[OK] ChromeDriver initialized")
    return driver


# =====================================================================
# 页面操作
# =====================================================================

def load_search_page(driver, url, wait_seconds=PAGE_LOAD_WAIT):
    """打开搜索页并等待基础渲染完成。"""
    _safe_print(f"[LOAD] Opening: {url}")
    driver.get(url)

    # 等待页面基础加载
    time.sleep(wait_seconds)

    # 检测是否被拦截
    page_text = driver.page_source.lower()

    if "login" in driver.current_url or "登录" in driver.page_source[:2000]:
        _safe_print("[WARN] Login required — page redirected to login")
        return False

    if "验证" in driver.page_source[:5000] or "captcha" in driver.page_source[:5000]:
        _safe_print("[WARN] Captcha detected, manual intervention needed")
        save_debug_artifacts(driver)
        return False

    return True


def scroll_to_load(driver, count=SCROLL_COUNT, pause=SCROLL_PAUSE):
    """滚动页面多次以触发更多内容加载。"""
    _safe_print(f"[LOAD] Scrolling page {count} times to load more notes ...")
    for i in range(count):
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )
        time.sleep(pause)
        _safe_print(f"  Scroll {i + 1}/{count} done")
    _safe_print("[OK] Scroll complete")


# =====================================================================
# 数据提取
# =====================================================================

# 多套 CSS 选择器（按尝试优先级排列），适配不同版本的小红书前端
NOTE_CARD_SELECTORS = [
    # 通用卡片容器
    "section.note-item",
    "div.note-item",
    "div[class*='note-item']",
    "section[class*='note-item']",
    "div.feeds-page div[class*='note']",
    # 搜索结果容器内的卡片
    "div.search-result-container section",
    "div.search-result-container div[class*='note']",
    # 通栏卡片
    "a[href*='/explore/']",
    # 更宽泛的选择
    "div[class*='card']",
]

TITLE_SELECTORS = [
    ".title",
    ".note-title",
    "span.title",
    "a.title",
    "a[class*='title']",
    "span[class*='title']",
    "div[class*='title']",
]

DESC_SELECTORS = [
    ".desc",
    ".note-desc",
    ".description",
    "span.desc",
    "p.desc",
    "div[class*='desc']",
    "span[class*='desc']",
    "div[class*='description']",
]

LIKE_SELECTORS = [
    ".like-count",
    ".count",
    "span.count",
    "span[class*='like']",
    "span[class*='count']",
    "div[class*='like'] span",
]

LINK_SELECTORS = [
    "a[href*='/explore/']",
    "a[href*='/discovery/item/']",
    "a[href*='/search_result/']",
]


def _try_selectors(element, selectors):
    """对给定的 WebElement 尝试多套 CSS 选择器，返回第一个匹配文本。"""
    for sel in selectors:
        try:
            found = element.find_element(By.CSS_SELECTOR, sel)
            text = found.text.strip()
            if text:
                return text
        except NoSuchElementException:
            continue
    return ""


def _try_selectors_all(driver, selectors):
    """在全页面范围尝试多套 CSS 选择器，返回所有匹配元素列表。"""
    for sel in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, sel)
        if elements:
            _safe_print(f"  Matched selector: {sel} -> {len(elements)} elements")
            return elements
    return []


def extract_notes(driver):
    """
    从已渲染的页面中提取笔记数据。

    Returns:
        list[dict]: 笔记数据列表，每项包含 title, text, like_count, url
    """
    _safe_print("[LOAD] Extracting notes from rendered page ...")

    # 先尝试用卡片级选择器找到每张卡片
    cards = _try_selectors_all(driver, NOTE_CARD_SELECTORS)

    if not cards:
        _safe_print("[WARN] No note cards found with any CSS selector")
        save_debug_artifacts(driver)
        # 尝试从页面 JSON 中提取（__INITIAL_STATE__）
        notes = _extract_from_initial_state(driver.page_source)
        if notes:
            _safe_print(f"[OK] Extracted {len(notes)} notes from __INITIAL_STATE__")
        return notes

    notes = []
    seen_urls = set()

    for card in cards:
        try:
            title = _try_selectors(card, TITLE_SELECTORS)
            desc = _try_selectors(card, DESC_SELECTORS)
            like_text = _try_selectors(card, LIKE_SELECTORS)
            link = _try_selectors(card, LINK_SELECTORS)

            # link 可能是 href 属性而非文本
            if not link:
                try:
                    a_tag = card.find_element(By.CSS_SELECTOR, "a[href*='/explore/']")
                    link = a_tag.get_attribute("href")
                except NoSuchElementException:
                    pass

            # 如果没有 title，用 desc 的前 50 字作为标题
            if not title and desc:
                title = desc[:50]

            # 解析点赞数
            like_count = _parse_like_count(like_text)

            # 跳过空内容和重复 URL
            if not title and not desc:
                continue
            if link and link in seen_urls:
                continue

            seen_urls.add(link)

            notes.append({
                "title": title,
                "text": desc,
                "like_count": like_count,
                "url": link or "",
            })
        except Exception:
            # 单个卡片解析失败不影响整体
            continue

    _safe_print(f"[OK] Extracted {len(notes)} notes from CSS selectors")
    return notes


def _extract_from_initial_state(html):
    """
    从页面 HTML 的 window.__INITIAL_STATE__ 中提取笔记数据（备用方案）。

    Returns:
        list[dict]: 笔记数据列表
    """
    match = re.search(
        r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>',
        html, re.DOTALL
    )
    if not match:
        return []

    try:
        import json
        raw = match.group(1)
        raw = re.sub(r':\s*undefined', ': null', raw)
        data = json.loads(raw)

        notes = []
        # 尝试多种 JSON 路径
        search = data.get("search", {})
        note_list = (
            search.get("notes", [])
            or search.get("noteList", [])
            or search.get("feeds", [])
        )

        for item in note_list:
            note_card = item.get("noteCard", item)
            notes.append({
                "title": note_card.get("displayTitle", note_card.get("title", "")),
                "text": note_card.get("desc", note_card.get("description", "")),
                "like_count": int(note_card.get("likedCount", 0)),
                "url": f"https://www.xiaohongshu.com/explore/{note_card.get('noteId', '')}",
            })
        return notes
    except Exception:
        return []


def _parse_like_count(text):
    """解析点赞数字符串为整数。支持 '1.2万' 等中文数字格式。"""
    if not text:
        return 0
    text = text.strip()
    try:
        if "万" in text:
            num = float(text.replace("万", "").strip())
            return int(num * 10000)
        return int(re.sub(r"[^0-9]", "", text) or 0)
    except (ValueError, TypeError):
        return 0


# =====================================================================
# 调试辅助
# =====================================================================

def save_debug_artifacts(driver):
    """保存截图和完整 HTML 源码到文件，便于人工诊断。"""
    try:
        driver.save_screenshot(SCREENSHOT_PATH)
        _safe_print(f"[WARN] Screenshot saved to: {SCREENSHOT_PATH}")
    except Exception as e:
        _safe_print(f"[ERR] Failed to save screenshot: {e}")

    try:
        with open(PAGE_SOURCE_PATH, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        _safe_print(f"[WARN] Page source saved to: {PAGE_SOURCE_PATH}")
    except Exception as e:
        _safe_print(f"[ERR] Failed to save page source: {e}")


# =====================================================================
# CSV 输出
# =====================================================================

def save_to_csv(notes, output_path):
    """
    保存笔记数据为 CSV 文件。

    输出字段与 EmotionItem 对齐:
        source, url, crawl_time, title, text, like_count
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    crawl_time = datetime.now().isoformat()

    fieldnames = ["source", "url", "crawl_time", "title", "text", "like_count"]

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for note in notes:
            writer.writerow({
                "source": "xiaohongshu",
                "url": note.get("url", ""),
                "crawl_time": crawl_time,
                "title": note.get("title", ""),
                "text": note.get("text", ""),
                "like_count": note.get("like_count", 0),
            })

    _safe_print(f"[OK] CSV saved: {output_path}")


# =====================================================================
# 主流程
# =====================================================================

def run():
    """主入口：执行完整的 Selenium 搜索 + 提取 + 保存流程。"""
    _safe_print("=" * 60)
    _safe_print("  Selenium Xiaohongshu Search Extractor")
    _safe_print(f"  Target: {SEARCH_URL}")
    _safe_print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    _safe_print("=" * 60)

    driver = None
    try:
        driver = create_driver()

        # ── 1. 打开搜索页 ──
        if not load_search_page(driver, SEARCH_URL):
            _safe_print("[ERR] Page load failed — aborting")
            return

        # ── 2. 滚动加载更多内容 ──
        scroll_to_load(driver)

        # ── 3. 提取笔记数据 ──
        notes = extract_notes(driver)

        if not notes:
            _safe_print("[WARN] No notes extracted — saving debug artifacts")
            save_debug_artifacts(driver)
            return

        # ── 4. 保存 CSV ──
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"xiaohongshu_{date_str}_xiling_raw.csv"
        output_path = os.path.join(OUTPUT_DIR, filename)
        save_to_csv(notes, output_path)

        # ── 5. 打印统计 ──
        total_likes = sum(n.get("like_count", 0) for n in notes)
        titles_with_content = sum(1 for n in notes if n.get("title") and n.get("text"))
        _safe_print("-" * 60)
        _safe_print(f"  [OK] Extracted {len(notes)} notes from xiaohongshu")
        _safe_print(f"  Total likes: {total_likes}")
        _safe_print(f"  Notes with full content: {titles_with_content}/{len(notes)}")
        _safe_print("-" * 60)

    except WebDriverException as e:
        _safe_print(f"[ERR] WebDriver error: {e}")
        _safe_print("[WARN] Check if Chrome is installed at: " + CHROME_BINARY_PATH)
        _safe_print("[WARN] Check if webdriver-manager can download ChromeDriver")
    except Exception as e:
        _safe_print(f"[ERR] Unexpected error: {e}")
        if driver:
            save_debug_artifacts(driver)
        raise
    finally:
        if driver:
            _safe_print("[LOAD] Closing browser ...")
            driver.quit()
            _safe_print("[OK] Browser closed")


# =====================================================================
# CLI 入口
# =====================================================================

if __name__ == "__main__":
    run()
