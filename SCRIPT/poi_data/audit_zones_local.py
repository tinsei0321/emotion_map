#!/usr/bin/env py
# -*- coding: utf-8 -*-
"""
zone/POI 再审计（基于用户本地知识）—— 宜昌商圈正确清单 + seed 伪造排查。

宜昌商圈（用户提供）：
  1. 夷陵广场CBD（大洋百货、CBD）—— 西陵区老城中心
  2. 水悦城
  3. 中南路（兴发广场、环球港）
  4. 五一广场（福久源商圈）
  5. 九码头 / 万达国际广场
  6. 吾悦广场
  7. 华翔CAZ
  8. 江南URD
  9. 夷陵万达商圈（夷陵区，≠ 夷陵广场）
关键纠正：万达=万达广场（唯一），无"万达簇"；宜昌无太古里（伪造）；CBD 专指夷陵广场。

只读分析。产出 docs/poi-zone-audit-v2.md。
用法：PYTHONUTF8=1 py SCRIPT/poi_data/audit_zones_local.py
"""
import os
import sys
import json
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.place_layer import get_place_layer, _haversine_m  # noqa

REPORT = os.path.join(_ROOT, 'docs', 'poi-zone-audit-v2.md')

# 用户给的宜昌商圈清单 + 关键地标关键词
DISTRICTS = [
    ('夷陵广场CBD', ['夷陵广场', '大洋百货', 'CBD', '国贸', '铁路坝', '卓悦']),
    ('水悦城', ['水悦城']),
    ('中南路', ['兴发', '环球港', '中南路']),
    ('五一广场/福久源', ['五一广场', '福久源']),
    ('九码头/万达国际广场', ['万达广场', '万达国际', '九码头', 'CBD 万达']),
    ('吾悦广场', ['吾悦']),
    ('华翔CAZ', ['华翔', 'CAZ']),
    ('江南URD', ['江南', 'URD']),
    ('夷陵万达（夷陵区）', ['夷陵万达']),
]
# 已知伪造/可疑（无 amap 对照 或 用户点名）
SUSPECT = ['太古里', '兴发广场 ']  # 太古里=用户点名伪造


def _find_all(pois, kws):
    """名称含任一关键词的 POI。"""
    out = []
    for p in pois:
        n = p.get('name') or ''
        if any(kw in n for kw in kws):
            out.append(p)
    return out


def main():
    pl = get_place_layer()
    seed = pl.seed_pois
    amap = pl.amap_pois
    allp = pl.all_pois
    out = []
    def w(s=''): out.append(s)

    w('# POI / Zone 再审计（本地知识校准）')
    w('')
    w('> 基于用户提供的宜昌商圈正确清单 + 本地化纠正（万达=万达广场唯一；CBD 专指夷陵广场；宜昌无太古里）。'
      'seed={} amap={} total={}。'.format(len(seed), len(amap), len(allp)))
    w('')

    # ── 1. 9 商圈在数据里的分布 ──
    w('## 1. 宜昌 9 商圈在 POI 数据里的命中情况')
    w('')
    w('每个商圈按关键词匹配，列出命中的 POI（名称/坐标/src/现 zone）。看坐标是否落在该商圈实际位置。')
    w('')
    for name, kws in DISTRICTS:
        hits = _find_all(allp, kws)
        w('### {}（关键词：{}）— {} 命中'.format(name, '/'.join(kws), len(hits)))
        w('')
        if not hits:
            w('> ⚠ 数据中无匹配 POI —— 可能数据缺失，或关键词需调整。')
            w('')
            continue
        for p in hits[:12]:
            zid = pl.classify_point(p['lng'], p['lat'])
            w('- {} | ({:.4f}, {:.4f}) | src={} | 现 zone={}'.format(
                p.get('name'), p['lng'], p['lat'], p.get('source') or 'seed', zid))
        if len(hits) > 12:
            w('- … 余 {} 个'.format(len(hits) - 12))
        # 质心 + 跨度
        if hits:
            lngs = [p['lng'] for p in hits]; lats = [p['lat'] for p in hits]
            w('')
            w('> 质心 ({:.4f}, {:.4f})；跨度 {}m × {}m。'.format(
                sum(lngs)/len(lngs), sum(lats)/len(lats),
                round((_haversine_m(min(lngs), 0, max(lngs), 0))),
                round(_haversine_m(0, min(lats), 0, max(lats)))))
        w('')

    # ── 2. seed 伪造排查（无 amap 对照）──
    w('## 2. seed 伪造排查（在 amap 找不到任何同名/含名对照）')
    w('')
    w('seed 手标，可能含凭空捏造的地点（如太古里——宜昌没有，成都才有）。'
      '下表列出 seed 中在 amap 1270 条里**完全找不到名称对照**的条目（既无同名也无含名）。')
    w('')
    amap_names = [p.get('name') or '' for p in amap]
    w('| seed 名 | seed 坐标 | 现 zone | 备注 |')
    w('|---------|----------|---------|------|')
    no_match = []
    for s in seed:
        sn = (s.get('name') or '').strip()
        if not sn:
            continue
        # amap 中是否有同名 或 双向含名
        has = any(sn == an or (len(sn) >= 3 and (sn in an or an in sn)) for an in amap_names)
        if not has:
            no_match.append(s)
    for s in no_match:
        zid = pl.classify_point(s['lng'], s['lat'])
        note = '⚠ 用户点名伪造' if '太古里' in (s.get('name') or '') else 'amap 无对照（可能伪造/可能 amap 缺）'
        w('| {} | ({:.4f}, {:.4f}) | {} | {} |'.format(
            s.get('name'), s['lng'], s['lat'], zid, note))
    w('')
    w('> 共 {} 个 seed 在 amap 无任何名称对照（需用户判定真伪）。'.format(len(no_match)))
    w('')

    # ── 3. 现 zone 与真实商圈的错位 ──
    w('## 3. 现 zone 与真实商圈错位总结')
    w('')
    w('- **wanda_cbd zone** 名字与内容均错：'
      '把夷陵广场CBD（大洋/国贸/卓悦）、中南路（兴发——seed 坐标错标到此）、'
      '水悦城、万达广场 等多个独立商圈焊成一个。且 seed 坐标偏移致兴发等错位。')
    w('- **万达 ≠ 万达簇**：数据中名称含「万达」的仅万达广场/万达影城/万达瑞华等万达品牌店，'
      '集中在 (111.31~111.32, 30.70~30.71)，= 万达国际广场商圈。')
    w('- **太古里（西陵）是伪造**（宜昌无），应删。')
    w('- 兴发广场 seed 坐标 (111.298, 30.697) 错——实际在中南路（amap 同名 111.3253, 30.6819，偏 3100m）。')
    w('')
    w('### 建议的新 zone 结构（待用户确认）')
    w('')
    w('把 wanda_cbd 拆成多个真实商圈 zone，general 保留兜底：')
    w('')
    w('| zone_id | name_zh | 含 |')
    w('|---------|---------|-----|')
    for name, kws in DISTRICTS:
        zonename = name
        zid = name.split('/')[0].split('（')[0]
        w('| {} | {} | {} |'.format(zid, zonename, '/'.join(kws)))
    w('')
    w('> 注：是否每个商圈都独立成 zone（9→可能 7~9 zone），还是合并几个，由用户定。'
      '情绪叙事（6 zone）已搁置，本次只动 POI 分类层。')
    w('')

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print('[OK] report ->', REPORT)
    print('[STAT] no-amap-match seed =', len(no_match))


if __name__ == '__main__':
    main()
