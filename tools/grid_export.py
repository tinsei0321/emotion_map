#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""grid_export.py — 固定方格网格聚合 → render_inbox spec（choropleth 计数）。

把 core.spatial_analysis.create_square_grid 包装为命令行出图工具：
点层 → 方格聚合（EPSG:4546 量度·snap-to-grid 仅有点的格）→
按 render_spec v1 契约落 DATA/exports/render_inbox（前端 SSE 自动消费·[dsh] 前缀）。

用法:
  py tools/grid_export.py --layer checkup_12345_2024 --cell 400 --name "12345热线400m网格分布"

注: 非 MCP 正式工具（grid 能力尚未入 EMC 插座·F_029 待立项）；
    输出契约与 mcp_server_emc.render_spec 逐字段对齐（kind/data/style/ui/origin/caliber_lite）。
"""
import argparse
import json
import os
import random
import sys
import time


def _safe_print(msg, file=None):
    try:
        print(msg, file=file)
    except UnicodeEncodeError:
        print(msg.encode('gbk', 'replace').decode('gbk'), file=file)


def main():
    ap = argparse.ArgumentParser(description='网格聚合出图（→ render_inbox）')
    ap.add_argument('--layer', required=True, help='点层 id（list_data 可查）')
    ap.add_argument('--cell', type=float, default=400.0, help='方格边长米（默认 400）')
    ap.add_argument('--name', required=True, help='图层名（现实内容·前端加 [dsh] 前缀）')
    ap.add_argument('--value-field', default='point_count', help='choropleth 取值字段（默认 point_count）')
    ap.add_argument('--data-nature', default='real', choices=('real', 'demo'))
    args = ap.parse_args()

    REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, REPO)

    from core.geo_registry import resolve_points
    from core.spatial_analysis import create_square_grid

    points = resolve_points(args.layer)
    if points is None or len(points) == 0:
        _safe_print(json.dumps({'ok': False, 'hint': f'点层为空/未知: {args.layer}'}, ensure_ascii=False))
        return 1

    grid = create_square_grid(points, cell_size=float(args.cell), unit='m')
    fc = json.loads(grid.to_json())

    spec_id = f'{int(time.time() * 1000)}-{random.randint(1000, 9999)}'
    spec = {
        'spec_version': 1,
        'spec_id': spec_id,
        'kind': 'choropleth',
        'data': {'geojson': fc},
        'style': {'scheme': 'community_choropleth_v1', 'value_field': args.value_field},
        'ui': {'name': args.name, 'zoom_to': True},
        'origin': {'producer': 'dsh', 'source_tool': 'grid_export'},
        'caliber_lite': {
            'usage': 'input',
            'data_nature': args.data_nature,
            'note': f'{args.cell:.0f}m 方格网格聚合（create_square_grid·仅有点的格）',
        },
    }
    inbox = os.path.join(REPO, 'DATA', 'exports', 'render_inbox')
    os.makedirs(inbox, exist_ok=True)
    inbox_path = os.path.join(inbox, f'{spec_id}.json')
    with open(inbox_path, 'w', encoding='utf-8', newline='') as fh:
        json.dump(spec, fh, ensure_ascii=False)

    _safe_print(json.dumps({
        'ok': True,
        'spec_id': spec_id,
        'inbox_path': inbox_path,
        'layer': args.layer,
        'cell_m': float(args.cell),
        'grid_count': int(len(grid)),
        'total_points': int(grid['point_count'].sum()),
        'max_count': int(grid['point_count'].max()),
        'features': len(fc.get('features', [])),
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
