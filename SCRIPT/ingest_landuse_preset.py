#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ingest_landuse_preset.py — 把大块三调用地 GeoJSON 按 DLMC 拆成 preset 矢量。

服务端处理（绕开浏览器上传 80/200MB 限制与代理 OOM）。两种用法：

  1) 列用地类型 + 给映射建议（不写盘，供你确认）：
       py SCRIPT/ingest_landuse_preset.py --inspect DATA/raw/landuse/landuse.geojson

  2) 按确认的映射拆分 + 简化 + 落盘 + 更新 manifest：
       py SCRIPT/ingest_landuse_preset.py --split DATA/raw/landuse/landuse.geojson \\
         --map SCRIPT/poi_data/landuse_map.json
       （landuse_map.json 形如 {"商业": ["零售商业用地", ...], "公园广场": ["公园绿地", ...], ...}）
       注：DATA/raw/landuse/ 已 gitignore（源矢量私有/超大，不入库）。

产出：DATA/boundaries/presets/用地_<类>.geojson（每类 unary_union dissolve + Douglas-Peucker
简化 ~10m，EPSG:4546 量米制；输出 WGS84）。每类一个 MultiPolygon = 演示用「用地筛选」面域。
"""
# 辅助文件（非生产管道，可跳过 SOP）。修改不涉及 L0→L4 主链。
import argparse
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PRESETS_DIR = os.path.join(_ROOT, 'DATA', 'boundaries', 'presets')
_MANIFEST = os.path.join(_PRESETS_DIR, 'manifest.json')

# 流式读大 GeoJSON：优先 ijson（常驻内存 O(1)），不可用退 json.load（全量入内存，400MB 级需 ~2GB）。
try:
    import ijson  # type: ignore
    _HAS_IJSON = True
except Exception:
    _HAS_IJSON = False


def _safe_print(msg):
    """Windows GBK 兼容打印（中文/生僻字 fallback）。"""
    try:
        print(msg)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((str(msg) + '\n').encode('utf-8', 'replace'))


def _iter_features(path):
    """yield 每个 feature 的 (properties, geometry)。ijson 流式 / json 全量两种。"""
    if _HAS_IJSON:
        with open(path, 'rb') as fh:
            for f in ijson.items(fh, 'features.item'):
                yield f.get('properties') or {}, f.get('geometry')
        return
    with open(path, 'r', encoding='utf-8') as fh:
        fc = json.load(fh)
    for f in fc.get('features', []):
        yield f.get('properties') or {}, f.get('geometry')


def _detect_geographic(path):
    """看首个坐标量级判断是否经纬度（GeoJSON 标准=WGS84，但三调可能存投影坐标）。"""
    for _i, (_p, g) in enumerate(_iter_features(path)):
        try:
            c = g['coordinates']
            x = c[0] if g['type'] == 'Point' else c[0][0]
            return abs(x) < 360   # 经度 < 360 → 地理坐标；否则投影（按 EPSG:4546 处理）
        except Exception:
            return True
        # 只看首个
    return True


# ── inspect：列 DLMC + 计数 + 映射建议 ──

def cmd_inspect(path):
    if not os.path.exists(path):
        _safe_print('[ERR] 文件不存在: %s' % path); sys.exit(2)
    from collections import Counter
    cnt = Counter()
    n_total = 0
    for props, _g in _iter_features(path):
        n_total += 1
        v = props.get('DLMC')
        if v is None:                      # DLMC 缺，提示可能的同义字段
            keys = [k for k in props.keys() if '地' in k or 'DL' in k or '类' in k]
            if n_total == 1:
                _safe_print('[WARN] 无 DLMC 字段。props keys=%s' % list(props.keys()))
                if keys:
                    _safe_print('[HINT] 疑似同类字段: %s — 可改脚本 _DLMC_FIELD 或映射用该字段' % keys)
            v = '(空)'
        cnt[str(v)] += 1
    geo = _detect_geographic(path)
    _safe_print('[LOAD] features=%d  DLMC 类型数=%d  坐标=%s' % (n_total, len(cnt), '地理(WGS84)' if geo else '投影(疑 EPSG:4546)'))
    _safe_print('\n%-30s %s' % ('DLMC', 'feature 数'))
    _safe_print('%-30s %s' % ('-' * 30, '-' * 10))
    for k, n in cnt.most_common():
        _safe_print('%-30s %d' % (k, n))
    _safe_print('\n[建议映射 landuse_map.json]（按关键词，按需手动调整）：')
    _safe_print(json.dumps(_suggest_mapping(cnt.keys()), ensure_ascii=False, indent=2))


# 关键词 → 演示类别（商业/公园广场/居住；其余忽略）
_KW = [
    ('商业',   ['商', '餐饮', '旅馆', '住宿', '商务', '金融', '娱乐', '零售', '市场']),
    ('公园广场', ['公园', '广场', '绿地', '风景', '游憩', '体育', '休闲']),
    ('居住',   ['住宅', '居住']),
]


def _suggest_mapping(dlmc_values):
    m = {'商业': [], '公园广场': [], '居住': []}
    for v in dlmc_values:
        for cat, kws in _KW:
            if any(k in v for k in kws):
                m[cat].append(v)
                break
    return {k: v for k, v in m.items() if v}


# ── split：按映射拆 + dissolve + 简化 + 落盘 + 更新 manifest ──

def cmd_split(path, map_path, tol):
    from shapely.geometry import shape, mapping
    from shapely.ops import unary_union, transform as shp_transform
    from pyproj import Transformer

    if not os.path.exists(path):
        _safe_print('[ERR] 文件不存在: %s' % path); sys.exit(2)
    if not os.path.exists(map_path):
        _safe_print('[ERR] 映射不存在: %s（先跑 --inspect 生成建议）' % map_path); sys.exit(2)
    mapping_cfg = json.load(open(map_path, encoding='utf-8'))
    # 反查：DLMC → 类别
    dlmc_to_cat = {}
    for cat, vals in mapping_cfg.items():
        for v in vals:
            dlmc_to_cat[str(v)] = cat

    geo = _detect_geographic(path)
    src_crs = 'EPSG:4326' if geo else 'EPSG:4546'
    to_m = Transformer.from_crs(src_crs, 'EPSG:4546', always_xy=True).transform
    to_ll = Transformer.from_crs('EPSG:4546', 'EPSG:4326', always_xy=True).transform

    buckets = {}   # cat -> list of shapely (in 4546, 米制)
    n_total = n_used = 0
    for props, g in _iter_features(path):
        n_total += 1
        cat = dlmc_to_cat.get(str(props.get('DLMC')))
        if not cat or not g:
            continue
        try:
            geom_m = shp_transform(to_m, shape(g))
            if not geom_m.is_valid:
                geom_m = geom_m.buffer(0)
            buckets.setdefault(cat, []).append(geom_m)
            n_used += 1
        except Exception as e:
            _safe_print('[WARN] geometry 解析失败 @feature %d: %s' % (n_total, e))

    if not buckets:
        _safe_print('[ERR] 无 feature 命中映射（检查 DLMC 值/字段名）'); sys.exit(3)

    os.makedirs(_PRESETS_DIR, exist_ok=True)
    written = []
    for cat, geoms in buckets.items():
        union = unary_union(geoms)
        simplified = union.simplify(tolerance=tol, preserve_topology=True)
        out_ll = shp_transform(to_ll, simplified)   # 回 WGS84
        fc = {'type': 'FeatureCollection', 'features': [{
            'type': 'Feature', 'properties': {'DLMC': cat}, 'geometry': mapping(out_ll),
        }]}
        out_path = os.path.join(_PRESETS_DIR, '用地_%s.geojson' % cat)
        with open(out_path, 'w', encoding='utf-8') as fh:
            json.dump(fc, fh, ensure_ascii=False)
        size_mb = os.path.getsize(out_path) / 1024 / 1024
        written.append((cat, out_path, size_mb))
        _safe_print('[OK] %s → %s (%.1f MB, dissolve %d 块 → simplify %dm)' % (cat, os.path.basename(out_path), size_mb, len(geoms), tol))

    _update_manifest(list(buckets.keys()))
    _safe_print('\n[完成] 命中 %d/%d feature；产出 %d 个 preset（Range tab → 用地筛选 可用）。'
                % (n_used, n_total, len(written)))


def _update_manifest(categories):
    """确保 manifest「用地筛选（三调）」组含本批类别（id land_<cat>，file 用地_<cat>.geojson，nameField DLMC）。幂等。"""
    if not os.path.exists(_MANIFEST):
        _safe_print('[WARN] manifest 不存在，跳过更新（%s）' % _MANIFEST); return
    groups = json.load(open(_MANIFEST, encoding='utf-8'))
    for g in groups:
        if '用地' in g.get('group', ''):
            existing = {it['id']: it for it in g.get('items', [])}
            for cat in categories:
                cid = 'land_' + {'商业': 'commercial', '公园广场': 'park', '居住': 'residential'}.get(cat, cat)
                existing[cid] = {
                    'id': cid, 'label': cat,
                    'file': '用地_%s.geojson' % cat, 'nameField': 'DLMC',
                }
            g['items'] = list(existing.values())
            break
    json.dump(groups, open(_MANIFEST, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    _safe_print('[OK] manifest 已更新（用地筛选 组）')


def main():
    ap = argparse.ArgumentParser(description='三调用地 GeoJSON → preset 拆分（服务端，绕开浏览器上传限制）')
    ap.add_argument('path', help='源 GeoJSON 路径（如 DATA/raw/landuse.geojson）')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--inspect', action='store_true', help='列 DLMC + 计数 + 映射建议（不写盘）')
    g.add_argument('--split', action='store_true', help='按 --map 拆分 + 简化 + 落盘 + 更新 manifest')
    ap.add_argument('--map', help='split 用：类别→DLMC 列表 的 JSON（先 inspect 生成建议）')
    ap.add_argument('--tol', type=float, default=10.0, help='Douglas-Peucker 简化容差（米，默认 10）')
    args = ap.parse_args()

    if not _HAS_IJSON:
        _safe_print('[WARN] 未装 ijson，回退 json.load（400MB 级需 ~2GB 内存）。pip install ijson 可流式。')

    if args.inspect:
        cmd_inspect(args.path)
    else:
        if not args.map:
            ap.error('--split 需配合 --map <json>')
        cmd_split(args.path, args.map, args.tol)


if __name__ == '__main__':
    main()
