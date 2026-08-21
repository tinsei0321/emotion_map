# -*- coding: utf-8 -*-
"""PT-CB11 Kimi 任务A 四口径自测（headless playwright·视觉验收证据）。

口径：①色带图例(B3-3) ②悬停显数值(B3-4) ③面板不误导(B3-5) ④控制台全零告警(B3-6)。
前置：8080 服务在跑 + 已投递 point_count 内联 choropleth spec（最新 backlog）。
产出：_tmp/kimi_b3_*.png 三张 + 控制台 [dsh] 日志摘要（stdout）。
"""
import json
import subprocess
import sys

from playwright.sync_api import sync_playwright

REPO = 'D:/Github/emotion_map'
OUT = REPO + '/_tmp'

ZERO_SPEC_CODE = (
    "import sys, json; sys.path.insert(0,'tools'); sys.path.insert(0,'.');"
    "import mcp_server_emc as m;"
    "feats=[{'type':'Feature','geometry':{'type':'Polygon','coordinates':["
    "[[111.2+i*0.06,30.6],[111.26+i*0.06,30.6],[111.26+i*0.06,30.65],"
    "[111.2+i*0.06,30.65],[111.2+i*0.06,30.6]]]},"
    "'properties':{'name':'zero'+str(i),'point_count':0}} for i in range(1,6)];"
    "r=m.render_spec(kind='choropleth', name='Kimi selftest zero',"
    " value_field='point_count', geojson={'type':'FeatureCollection','features':feats});"
    "print(json.dumps({'ok':r.get('ok'),'spec_id':r.get('spec_id')}))"
)


def main():
    logs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1400, 'height': 900})
        page.on('console', lambda m: logs.append({'type': m.type, 'text': m.text}))
        page.goto('http://127.0.0.1:8080', wait_until='domcontentloaded')
        # 底图+SSE backlog 推送+渲染：给足预热时间
        page.wait_for_timeout(15000)

        # 口径①③前置确认：图层行存在
        row = page.locator('text=Kimi selftest').first
        row_ok = row.count() > 0
        page.screenshot(path=f'{OUT}/kimi_b3_1_map_legend.png', full_page=False)

        # 口径②悬停 tip：视口中心（fit 后落在中间格 point_count=30）
        page.mouse.move(700, 450)
        page.wait_for_timeout(1200)
        page.mouse.move(702, 451)   # 微移触发 mousemove
        page.wait_for_timeout(1000)
        tip = page.locator('#tip-popup')
        tip_visible = tip.is_visible() if tip.count() else False
        tip_text = tip.inner_text() if tip_visible else ''
        page.screenshot(path=f'{OUT}/kimi_b3_2_tip.png', full_page=False)

        # 口径③参数面板：点该层要素按钮（精确行选择器：layer-row 内含同名 layer-name）
        panel_note = ''
        if row_ok:
            btn = page.locator(
                'div.layer-row:has(span.layer-name[title*="Kimi selftest"]) button[data-feat]').first
            try:
                btn.click(timeout=5000)
            except Exception:
                btn.dispatch_event('click')   # 行在折叠卡组内时 JS 直派
            page.wait_for_timeout(1200)
            body = page.locator('.set-body').first
            if body.count() and body.is_visible():
                panel_note = body.inner_text()
            page.screenshot(path=f'{OUT}/kimi_b3_3_panel.png', full_page=False)

        # 口径④全零告警：投递全零 spec → SSE 推到本页 → render_client console.warn
        r = subprocess.run(['py', '-c', ZERO_SPEC_CODE], cwd=REPO,
                           capture_output=True, text=True, timeout=60)
        page.wait_for_timeout(5000)
        page.screenshot(path=f'{OUT}/kimi_b3_4_zero.png', full_page=False)
        browser.close()

    warns = [l['text'] for l in logs if 'warn' in l['type'] and '[dsh]' in l['text']]
    errs = [l['text'] for l in logs if l['type'] == 'error']
    print(json.dumps({
        'row_found': row_ok,
        'tip_visible': tip_visible,
        'tip_text': tip_text[:200],
        'panel_note': panel_note[:300],
        'zero_post': (r.stdout or '').strip().splitlines()[-1] if r.stdout else r.stderr[:200],
        'dsh_warns': warns[-5:],
        'js_errors': errs[:10],
    }, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    sys.exit(main())
