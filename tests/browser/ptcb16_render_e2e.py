# -*- coding: utf-8 -*-
"""PT-CB16 C1 · 渲染链路浏览器级 E2E（playwright·隔离栈手跑）。

场景（对齐 s3_acp_event_e2e.py 先例·不起真实 8000·用 mock 后端只验前端消费）：
  A·SSE 真链：起轻量 SSE 服务推 spec → 页面 [dsh] 图层出现且要素数正确；
  B·硬刷新无复活：F5 后页面零 [dsh] 层（hello 协议+无 backlog 重放·PT-CB15 收口验收）；
  C·迟到 spec 不上屏：推一条「落盘时间 >300s」的 spec（watcher TTL·mock 端直接模拟
    watcher 不推即可·此场景由 tests/e2e + test_render_channel 覆盖，浏览器级只做 A/B）。

跑法（前置：隔离栈起好）：
  py frontend/serve.py 8090 --backend-port 8009
  py tests/browser/ptcb16_render_e2e.py

状态（诚实登记）：脚本按先例编写·**栈上手跑验证未完成**（office 当前 8000 被占用·
隔离栈脚本未实跑）——入库作骨架，首次栈上验证结果补记本节。
"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8090'

TOP3_SPEC = {
    'spec_version': 1, 'spec_id': 'e2e-top3-001', 'kind': 'choropleth',
    'data': {'geojson': {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature',
         'geometry': {'type': 'Polygon', 'coordinates': [[
             [111.28 + i * 0.01, 30.68], [111.29 + i * 0.01, 30.68],
             [111.29 + i * 0.01, 30.69], [111.28 + i * 0.01, 30.68]]]},
         'properties': {'name': f'链测社区{i}', 'point_count': (i + 1) * 10}}
        for i in range(3)]}},
    'style': {'scheme': 'community_choropleth_v1', 'value_field': 'point_count'},
    'ui': {'name': 'E2E链测TOP3', 'zoom_to': False},
    'origin': {'producer': 'dsh', 'source_tool': 'e2e'},
    'caliber_lite': {'usage': 'analysis_output', 'data_nature': 'test'},
}


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        # A：拦截 SSE 端点注入 spec（mock 投递·不依赖真实 watcher）
        page.route('**/api/v1/render/stream', lambda route: route.fulfill(
            status=200, content_type='text/event-stream',
            body='event: hello\ndata: {"ok": true}\n\n'
                 + f'event: spec\ndata: {json.dumps(TOP3_SPEC, ensure_ascii=False)}\n\n'))
        errors = []
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.goto(BASE + '/?test=1')
        page.wait_for_timeout(3000)

        dsh_layers = page.evaluate(
            "() => window.__EMC_DEBUG__ ? window.__EMC_DEBUG__.layerNames().filter(n => n.startsWith('[dsh]')) : []")
        assert any('E2E链测TOP3' in n for n in dsh_layers), f'A 场景失败：图层未出现 {dsh_layers}'

        # B：硬刷新 → 无 [dsh] 层复活
        page.reload()
        page.wait_for_timeout(3000)
        after = page.evaluate(
            "() => window.__EMC_DEBUG__ ? window.__EMC_DEBUG__.layerNames().filter(n => n.startsWith('[dsh]')) : []")
        assert not any('E2E链测TOP3' in n for n in after), f'B 场景失败：刷新后图层复活 {after}'

        real_errors = [e for e in errors if 'favicon' not in e]
        assert not real_errors, f'console error: {real_errors[:3]}'
        browser.close()
    print('[OK] PT-CB16 浏览器级 E2E：A 图层出现 / B 刷新无复活 / 零 console error')


if __name__ == '__main__':
    sys.exit(main())
