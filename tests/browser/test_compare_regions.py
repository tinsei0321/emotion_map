"""用例 1（C6 运行时盲区）· compare 中文地名↔preset_id 错配（5.115 happy path）。

场景：欢迎胶囊"对比西陵区和伍家岗区的情绪与归因" → harness 路由 compare → compare_regions
调 2× /geo/zonal_stats。

修复前：LLM 把"西陵区"中文名当 preset_id 传 → 后端 load_preset 按 id 查无 → 400 →
       compare 落"区域对比仅 0/2 区" → 硬断言红。
修复后：boundary-resolve.js 把中文名解析成 admin_district 内 feature 的 GeoJSON dict →
       2× 200 + rows → 硬断言绿。

运行（自管 serve.py：起 :8080 + 自起后端 :8000，跑完同停）：
    py tests/browser/test_compare_regions.py

前置：.env 配 DEEPSEEK_API_KEY（chat 链路需 LLM）；playwright 已装（py -m playwright --version）。
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from playwright.sync_api import sync_playwright

from emc_helpers import GeoCapture, inject_points, open_emc, send_prompt, wait_answer_done

PROMPT = '对比西陵区和伍家岗区的情绪与归因'
ZONAL = 'zonal_stats'
PORT = 8080
FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'compare_points.geojson')
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _wait_ready(timeout=90):
    """等 serve.py + 后端就绪（/api/v1/health 通）。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{PORT}/api/v1/health', timeout=2).read()
            return True
        except Exception:
            time.sleep(1)
    return False


def main() -> int:
    with open(FIXTURE, encoding='utf-8') as fh:
        fc = json.load(fh)
    serve = subprocess.Popen(['py', 'frontend/serve.py', str(PORT)], cwd=REPO)
    try:
        if not _wait_ready():
            print('[ERR] serve.py 后端未就绪（查 DEEPSEEK_API_KEY / uvicorn 启动）')
            return 1
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            cap = GeoCapture(page)
            open_emc(page)
            inject_points(page, fc)   # 地图空启动，经 ?e2e=1 seam 注入点层（落西陵/伍家岗区内）供 zonal_stats 聚合
            send_prompt(page, PROMPT)

            # 硬断言：恰好 2× POST /geo/zonal_stats 且均读到响应
            calls = cap.wait_calls(ZONAL, expected=2, timeout_ms=90000)
            assert len(calls) == 2, f'期望 2× zonal_stats，收到 {len(calls)}'

            statuses = [c['status'] for c in calls]
            assert all(s == 200 for s in statuses), f'zonal_stats 非全 200：{statuses}（中文名→preset_id 解析未生效？）'

            names = []
            for c in calls:
                rows = (c['body'] or {}).get('rows') or []
                assert rows, f"zonal_stats 200 但 rows 空：{c['body']}"
                names.append(str(rows[0].get('name', '')))
            joined = ''.join(names)
            assert '西陵' in joined and '伍家岗' in joined, f'聚合单元名缺两区：{names}'

            # 软断言：回答散文含两区（LLM 文本，warning 不 fail）
            answer = wait_answer_done(page, timeout_ms=60000)
            if '西陵' not in answer or '伍家岗' not in answer:
                print(f'[WARN] 回答未含两区名（软断言，LLM 保守措辞）：{answer[:200]}')
            else:
                print('[OK] 回答含两区')

            print(f'[OK] PASS — 2× zonal_stats 200, units={names}')
            browser.close()
            return 0
    finally:
        serve.terminate()
        try:
            serve.wait(timeout=10)
        except Exception:
            serve.kill()


if __name__ == '__main__':
    sys.exit(main())
