#!/usr/bin/env python3
"""一次性补丁：为 ermawu_l3l4 CSV 补 lon/lat 坐标列（坐标只存在于同名 geojson）。

根因（生成器 `SCRIPT/sim_ermawu_l3l4.py` 缺陷）：
- 生成器写 CSV 时只写 properties 列（33 列），**未含坐标**；坐标只在同名 geojson 的 geometry。
- `core/geo_registry.get_layer_points` 读 CSV 需要 lon/lat 列 → 缺列 raise KeyError → EMC 无法加载大南门数据。

本脚本为一次性补丁（CB-16 大南门数据专题·两组预检确认）：
- 从同名 geojson 按 feature 顺序取 coordinates + id_e → 与 CSV id_e 断言一致 → 追加 lon/lat 到**末尾**。
- 跑前备份原 CSV（.bak）；保留 utf-8-sig BOM；幂等（已含 lon/lat 则跳过）。
- 不动生成器、不重新模拟（保 T1/T2/T3 已有数据不变·seed 2606 确定性）。

TODO（生成器修复·下次重跑前）：
- `SCRIPT/sim_ermawu_l3l4.py` 的 CSV 写出段应补 lon/lat 列（同 geojson 坐标），消除一次性补丁依赖。
- 跑法：py SCRIPT/backfill_ermawu_coords.py（当前文件在 DATA/performance/ 与 SCRIPT/ 间相对定位）。
"""
import csv
import json
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_HERE, os.pardir, 'DATA', 'performance')

# 层 → (csv 文件名, geojson 文件名)
LAYERS = {
    'T1': ('ermawu_l3l4_T1_result_csv.csv', 'ermawu_l3l4_T1_result_geojson.geojson'),
    'T2': ('ermawu_l3l4_T2_result_csv.csv', 'ermawu_l3l4_T2_result_geojson.geojson'),
    'T3': ('ermawu_l3l4_T3_result_csv.csv', 'ermawu_l3l4_T3_result_geojson.geojson'),
}


def backfill(t: str) -> int:
    csv_name, gj_name = LAYERS[t]
    csv_path = os.path.join(_DATA_DIR, csv_name)
    gj_path = os.path.join(_DATA_DIR, gj_name)
    if not os.path.isfile(csv_path) or not os.path.isfile(gj_path):
        raise FileNotFoundError(f'{t}: 缺文件 {csv_path} 或 {gj_path}')

    # 读 geojson 坐标 + id_e（按 feature 顺序）
    with open(gj_path, encoding='utf-8') as f:
        gj = json.load(f)
    coords = []
    for ft in gj.get('features', []):
        eid = (ft.get('properties') or {}).get('id_e', '')
        c = (ft.get('geometry') or {}).get('coordinates')
        if c is None or len(c) < 2:
            raise ValueError(f'{t}: feature 缺坐标 {eid}')
        coords.append((eid, c[0], c[1]))

    # 读 CSV（utf-8-sig·保 BOM 语义）
    with open(csv_path, encoding='utf-8-sig', newline='') as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    # 幂等：已含 lon/lat 则跳过
    if 'lon' in fieldnames and 'lat' in fieldnames:
        print(f'[SKIP] {t}: 已含 lon/lat（{len(rows)} 行）')
        return 0

    # ★ 关键断言：id_e 序完全一致（防行序错配静默污染·两组预检要求）
    csv_ids = [r.get('id_e', '') for r in rows]
    gj_ids = [c[0] for c in coords]
    if csv_ids != gj_ids:
        raise AssertionError(f'{t}: id_e 序不一致（CSV {len(csv_ids)} vs geojson {len(gj_ids)}）·backfill 中止')

    # 备份
    shutil.copy(csv_path, csv_path + '.bak')

    # 追加 lon/lat 到末尾
    fieldnames += ['lon', 'lat']
    for r, (eid, lon, lat) in zip(rows, coords):
        r['lon'], r['lat'] = lon, lat

    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f'[OK] {t}: {len(rows)} 行补坐标（追加 lon/lat 末尾·备份 .bak）')
    return len(rows)


if __name__ == '__main__':
    total = 0
    for t in ('T1', 'T2', 'T3'):
        total += backfill(t)
    print(f'═══ done：补坐标 {total} 行 ═══')
