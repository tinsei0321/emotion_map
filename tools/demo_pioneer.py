#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PT-CB6 P+ · demo_pioneer.py —— v2 场景本机版（无 dsh 验砖）。

三步演示（按任务书 §七 同款语义）：
  1. zonal_stats(12345 真实点层 × 174 社区面, layer_output=True)
  2. render_spec(community_choropleth_v1·value_field=point_count·inline 路)
  3. 安全/民生社区点层各一张同法（经 manifest 现路径读 GeoJSON 直传
     zonal_stats 的 layer 位——这两个点层 preset 不在 geo_registry 点层注册表，
     故走 resolve_points 的 dict send-in 路径，能力本体不变）。

产物：DATA/exports/render_inbox 落三张 spec；前端 8080 EventSource 自动消费。
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, 'tools'))

import mcp_server_emc as mcp


def _safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('gbk', 'replace').decode('gbk'))


def _find_174_preset():
    data = mcp.list_data()
    presets = data.get('presets', [])
    for p in presets:
        if p.get('id') == 'checkup_cfg_community':
            return p
    for p in presets:
        label = str(p.get('label', ''))
        if '174' in label and '社区' in label:
            return p
    return None


def _load_preset_fc(preset_id):
    with open(mcp.MANIFEST, 'r', encoding='utf-8') as fh:
        groups = json.load(fh)
    for group in groups:
        for it in group.get('items', []):
            if it.get('id') == preset_id:
                rel = it.get('file', '')
                path = os.path.normpath(os.path.join(os.path.dirname(mcp.MANIFEST), rel))
                with open(path, 'r', encoding='utf-8') as f2:
                    return json.load(f2)
    return None


def _zonal_and_render(boundary, layer, name, fc_loader=None):
    pts = fc_loader() if fc_loader else layer
    z = mcp.zonal_stats(boundary=boundary, layer=pts, top_n=10, layer_output=True,
                        sort_by='point_count')
    if not z.get('geojson'):
        _safe_print(f'[ERR] zonal_stats 失败（{name}）: {z.get("hint")}')
        return False
    r = mcp.render_spec(kind='choropleth', scheme='community_choropleth_v1',
                        value_field='point_count', name=name, geojson=z['geojson'],
                        data_nature='real', community_caliber=174, source_tool='zonal_stats')
    if r.get('ok'):
        _safe_print(f'[OK] {name}: spec_id={r["spec_id"]} inbox={r["inbox_path"]}')
        return True
    _safe_print(f'[ERR] render_spec 失败（{name}）: {r.get("hint")}')
    return False


def main():
    preset = _find_174_preset()
    if preset is None:
        _safe_print('[ERR] 174 社区面 preset 未找到（list_data 实查无果）·停手待主手裁决')
        return 2
    boundary = preset['id']
    _safe_print(f'[OK] 174 社区面 preset id = {boundary}（{preset.get("label")}）')

    ok = 0
    ok += _zonal_and_render(boundary, 'checkup_12345_2024',
                            '12345热线诉求最密集社区(真实)')
    ok += _zonal_and_render(boundary, 'subj_12345_safety_community_point',
                            '12345安全韧性最密集社区(真实)',
                            fc_loader=lambda: _load_preset_fc('subj_12345_safety_community_point'))
    ok += _zonal_and_render(boundary, 'subj_12345_livelihood_community_point',
                            '12345民生基础最密集社区(真实)',
                            fc_loader=lambda: _load_preset_fc('subj_12345_livelihood_community_point'))

    _safe_print(f'[OK] 演示完成：{ok}/3 张 spec 已落 render_inbox')
    _safe_print('提示：起 serve 后开 8080·EventSource 自动消费（py frontend/serve.py 8080）')
    return 0 if ok == 3 else 1


if __name__ == '__main__':
    sys.exit(main())
