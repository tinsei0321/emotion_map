#!/usr/bin/env py
# -*- coding: utf-8 -*-
"""
POI / zone 审计 — 梳理所有 zone 归类错误 + seed 坐标偏移 + 落水清单。
只读分析，不改数据。产出 docs/poi-zone-audit.md 供用户审阅。

用法：PYTHONUTF8=1 py SCRIPT/poi_data/audit_poi_zones.py
"""
import os
import sys
import json
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.place_layer import get_place_layer, _haversine_m  # noqa

REPORT = os.path.join(_ROOT, 'docs', 'poi-zone-audit.md')


def _c(p):
    return (p['lng'], p['lat'])


def _centroid(points):
    if not points:
        return None
    n = len(points)
    return (sum(p['lng'] for p in points) / n, sum(p['lat'] for p in points) / n)


def main():
    pl = get_place_layer()
    seed = pl.seed_pois
    amap = pl.amap_pois
    allp = pl.all_pois
    out = []

    def w(s=''):
        out.append(s)

    w('# POI / Zone 审计报告')
    w('')
    w('> 只读分析。seed={} amap={} total={}。用户审阅后定修法（清洗 seed 坐标 / 删落水 / 修 zone 边界）。'.format(
        len(seed), len(amap), len(allp)))
    w('')

    # ── 1. 各 zone 成分 ──
    w('## 1. 各 zone 成分（按 classify_point 归区）')
    w('')
    by_zone = defaultdict(list)
    for p in allp:
        zid = pl.classify_point(p['lng'], p['lat'])
        by_zone[zid].append(p)
    w('| zone | 总数 | seed | amap | 主要类别（top3） |')
    w('|------|------|------|------|----------------|')
    for zid in sorted(by_zone):
        ps = by_zone[zid]
        cats = Counter(p.get('baidu_level1') or p.get('category') or '?' for p in ps)
        cat_str = ', '.join('{}={}'.format(k, v) for k, v in cats.most_common(3))
        n_seed = sum(1 for p in ps if (p.get('source') or 'seed') == 'seed')
        w('| {} | {} | {} | {} | {} |'.format(
            zid, len(ps), n_seed, len(ps) - n_seed, cat_str))
    w('')

    # ── 2. zone 内语义分簇（找"焊在一起"的多个商圈）──
    w('## 2. zone 内语义分簇（识别"焊在一起"的多个商圈）')
    w('')
    w('按名称关键词分簇，看每个 zone 是否包含多个独立商圈/片区（如「万达-国贸」= 万达 + 国贸）。')
    w('')
    KEYWORDS = {
        'wanda_cbd': ['万达', '国贸', '夷陵广场', '铁路坝', '兴发', '卓悦', '大洋', '水悦城', '太古里'],
        'ermalu_oldstreet': ['二马路', '解放路', '大南门', '滨江'],
    }
    for zid, kws in KEYWORDS.items():
        ps = by_zone.get(zid, [])
        w('### {}（{} POI）'.format(zid, len(ps)))
        w('')
        clusters = {kw: [] for kw in kws}
        other = []
        for p in ps:
            name = p.get('name') or ''
            matched = False
            for kw in kws:
                if kw in name:
                    clusters[kw].append(p)
                    matched = True
                    break
            if not matched:
                other.append(p)
        for kw in kws:
            ps_kw = clusters[kw]
            if not ps_kw:
                continue
            c = _centroid(ps_kw)
            w('- **{}**：{} 个，质心 ({:.4f}, {:.4f})'.format(kw, len(ps_kw), c[0], c[1]))
            for p in ps_kw[:6]:
                w('  - {} | {} | ({:.4f}, {:.4f}) | src={}'.format(
                    p.get('name'), p.get('baidu_level1') or p.get('category'), p['lng'], p['lat'],
                    p.get('source') or 'seed'))
            if len(ps_kw) > 6:
                w('  - … 余 {} 个'.format(len(ps_kw) - 6))
        w('- **其他**：{} 个（不含上述关键词）'.format(len(other)))
        # 簇间距离（万达 vs 国贸 例）
        if '万达' in clusters and '国贸' in clusters and clusters['万达'] and clusters['国贸']:
            c1 = _centroid(clusters['万达'])
            c2 = _centroid(clusters['国贸'])
            d = _haversine_m(c1[0], c1[1], c2[0], c2[1])
            w('')
            w('> **万达簇 ↔ 国贸簇 质心距离 ≈ {}m** — 若 >300m 说明是两个独立商圈被焊进一个 zone。'.format(round(d)))
        w('')

    # ── 3. seed 坐标偏移审计（与 amap 同名 POI 对照）──
    w('## 3. seed 坐标偏移审计（与 amap 同名 POI 对照）')
    w('')
    w('seed 手标坐标粗糙；用 amap 同名 POI 的坐标校正。下表列出 seed 中能在 amap 找到同名（或包含关系）且偏移 >100m 的条目。')
    w('')
    # amap 名字索引
    amap_by_name = defaultdict(list)
    for p in amap:
        if p.get('name'):
            amap_by_name[p['name']].append(p)
    w('| seed 名 | seed 坐标 | amap 同名坐标 | 偏移(m) | 说明 |')
    w('|---------|----------|--------------|---------|------|')
    flagged = []
    for s in seed:
        sname = s.get('name') or ''
        # 精确同名
        cands = amap_by_name.get(sname, [])
        # 退化：seed 名是 amap 名的子串
        if not cands:
            for ap in amap:
                an = ap.get('name') or ''
                if sname and sname in an and len(sname) >= 3:
                    cands.append(ap)
                    break
        if not cands:
            continue
        # 取最近的 amap 候选
        best = min(cands, key=lambda ap: _haversine_m(s['lng'], s['lat'], ap['lng'], ap['lat']))
        d = _haversine_m(s['lng'], s['lat'], best['lng'], best['lat'])
        if d > 100:
            flagged.append((d, s, best))
    flagged.sort(key=lambda t: -t[0])
    for d, s, best in flagged:
        note = '同名' if (s.get('name') == best.get('name')) else '子串匹配({})'.format(best.get('name'))
        w('| {} | ({:.4f}, {:.4f}) | ({:.4f}, {:.4f}) | {} | {} |'.format(
            s.get('name'), s['lng'], s['lat'], best['lng'], best['lat'], round(d), note))
    w('')
    w('> 共 {} 个 seed 偏移 >100m（可被 amap 校正）。'.format(len(flagged)))
    w('')

    # ── 4. 落水清单 ──
    w('## 4. 落水 POI 清单（28，已标 in_water；用户已选"删除"）')
    w('')
    water = [p for p in allp if p.get('_in_water')]
    w('| 名 | 坐标 | src | 类别 |')
    w('|----|------|-----|------|')
    for p in water:
        w('| {} | ({:.4f}, {:.4f}) | {} | {} |'.format(
            p.get('name'), p['lng'], p['lat'], p.get('source') or 'seed',
            p.get('baidu_level1') or p.get('category') or ''))
    w('')

    # ── 写盘 ──
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print('[OK] report ->', REPORT)
    print('[STAT] zones={} | seed_offset>100m={} | water={}'.format(
        len(by_zone), len(flagged), len(water)))


if __name__ == '__main__':
    main()
