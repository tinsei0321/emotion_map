# -*- coding: utf-8 -*-
"""CB-39 A5：《紧急任务数据总账》生成器（一次性运维脚本·私有函数免追踪号）。

用法：py SCRIPT/_ops_gen_ledger_cb39.py  →  覆写 DATA/analysis/_总账.md
复跑场景：R1 收尾终对账（总账/retired/presets manifest 三方一致性）。
规则：git ls-files 全量 + git log --follow --diff-filter=A 取来源 commit + 目录/文件名规则定数据族/去留/去向。
"""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'DATA' / 'analysis' / '_总账.md'


def _git(args):
    # core.quotepath=false：中文路径原样输出（默认八进制转义会废掉族判定与 --follow 追溯）
    r = subprocess.run(['git', '-C', str(ROOT), '-c', 'core.quotepath=false'] + args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.stdout.strip()


def _files():
    out = _git(['ls-files', '--', 'DATA/analysis'])
    return sorted(p for p in out.splitlines() if p.strip())


def _origin_commit(rel):
    h = _git(['log', '--follow', '--diff-filter=A', '--format=%h', '-1', '--', rel])
    return h or '?'


def _family(rel):
    name = rel.replace('\\', '/')
    if '_retired/' in name:
        return 'page7 中间产物（归档）'
    if name.startswith('DATA/analysis/12345'):
        return '主观轨（12345）'
    if name.startswith('DATA/analysis/77'):
        return '体检专题（量化）'
    if name.startswith(('DATA/analysis/安全韧性', 'DATA/analysis/民生基础')):
        return '体检专题（板块分析）'
    if name.startswith('DATA/analysis/page7'):
        return 'page7 产物'
    if name.startswith('DATA/analysis/汇总'):
        return '成文分析'
    return '空间底座（根）'


def _disposition(rel):
    if '_retired/' in rel:
        return '归档（_retired）'
    return '留'


def _caliber(rel):
    n = rel.replace('\\', '/')
    base = os.path.basename(n)
    if '_最终' in base:
        return 'current（最终版·唯一引用基准）'
    if 'README' in base or base == '_总账.md':
        return '-'
    if _family(n).startswith('成文分析'):
        return 'current（v6 去村·08-13/14 版）'
    return 'current（B2 对账后复核）'


def _dest(rel):
    n = rel.replace('\\', '/')
    base = os.path.basename(n)
    fam = _family(n)
    if fam.startswith('空间底座'):
        return '图层（presets 注册·B1 补「城市体检底座」group）'
    if n.endswith('.geojson'):
        return '图层（点层 presets 补注册·B1）'
    if n.endswith('.md') and fam.startswith('成文分析'):
        return 'RAG note+fact（C2 拷贝 00-宜昌专项 + 蒸馏）'
    if n.endswith('.csv'):
        return '口径素材→fact（C2 蒸馏·禁原文入 RAG）'
    if n.endswith('.xlsx'):
        return '交付归档（不进 RAG·口径卡指向为基准）'
    if n.endswith('.png'):
        return '-（已退役归档）'
    if n.endswith('.py'):
        return '-（过程脚本·随归档）'
    return '-'


def _main():
    rows = []
    for rel in _files():
        if rel.replace('\\', '/').endswith('_总账.md'):
            continue
        rows.append((rel.replace('\\', '/'), _family(rel), _origin_commit(rel), _disposition(rel), _caliber(rel), _dest(rel)))
    lines = [
        '# 紧急任务数据总账（CB-39 A5·生成于 git 实测）',
        '',
        '> 每文件一行：`路径 | 数据族 | 来源 commit | 去留 | 口径版本 | 沉淀去向`。',
        '> 生成器：`SCRIPT/_ops_gen_ledger_cb39.py`（可复跑·R1 终对账用）。台账本身不进 RAG（加载器只扫 docs/urban-renewal-plan）。',
        f'> 文件数：{len(rows)}（git ls-files DATA/analysis 实测）。三方一致性：retired.md（page7 归档）/ presets manifest（图层注册）随 B1/B2 批交叉登记。',
        '',
        '| 路径 | 数据族 | 来源 commit | 去留 | 口径版本 | 沉淀去向 |',
        '|---|---|---|---|---|---|',
    ]
    for r in rows:
        lines.append('| ' + ' | '.join(r) + ' |')
    lines += [
        '',
        '## 挂起区（B2 对账前暂留 DATA/performance/ 的同名三对）',
        '',
        '| 文件 | 状态 |',
        '|---|---|',
        '| ~~DATA/performance/77项_社区占比表.csv~~ | 已裁决归档 _retired/（PT-CB4 T1·2026-08-19·analysis 137 社区超集胜出） |',
        '| ~~DATA/performance/77项_社区11类占比矩阵.csv~~ | 已裁决归档 _retired/（193 含村旧口径负于 analysis 137 城市社区） |',
        '| ~~DATA/performance/12345_事件类型.csv~~ | 已裁决归档 _retired/（与 analysis 版仅差 BOM·冗余） |',
        '',
        '## 备注',
        '',
        '- 2026-08-16（A2/A3/A4）迁移与归位记录见 DATA/README.md 与 retired.md；page7 中间版 9 件归档不删（裁定）。',
        '- 来源 commit 经 `git log --follow` 追溯（跨 rename 取最初入库点）。',
    ]
    OUT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'[OK] {OUT.relative_to(ROOT)} rows={len(rows)}')


if __name__ == '__main__':
    _main()
