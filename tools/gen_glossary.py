#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PT-CB18(W1-3) · 术语表生成器（非 MCP 正式工具·零追踪 ID·同 gen_progress 先例）。

治「裸编号看不懂」的病：从仓内权威源抽「内部编号 → 业务名」对照，产出仓根 GLOSSARY.md。
三个抽取源：
1. R 规则号 ← docs/debug-memory.md 标题行 `## R{n} — 名称`；
2. F_/D_ 工具号 ← 全仓 `register_track_id("MOD_X.F_NNN", "描述")` 注册表；
3. 批次号 ← docs/catch-ball/discuss/** 文件名标题段（含 archive 卷宗）。
确定性纪律：同一仓状态 → 逐字节同一产物（无时间戳·判新旧看首行 HEAD）。
产物硬预算 ≤100 行：F/D 号按模块紧凑串接；配对失败（裸编号无业务名）记「未配对清单」落盘。
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

GLOSSARY_PATH = os.path.join(REPO, 'GLOSSARY.md')
UNPAIRED_PATH = os.path.join(REPO, 'docs', 'catch-ball', 'glossary-unpaired.md')
MAX_LINES = 100
SKIP_DIRS = {'node_modules', '.git', 'DATA', '_tmp', 'vendor', '.dsh-meow',
             '__pycache__', '.pytest_cache'}


def _safe_print(msg, file=None):
    try:
        print(msg, file=file)
    except UnicodeEncodeError:
        print(msg.encode('gbk', 'replace').decode('gbk'), file=file)


def _head_short() -> str:
    try:
        out = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=REPO, capture_output=True, text=True, timeout=5, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return ''


def _clip(name: str, limit: int = 40) -> str:
    """规则名截断保预算（完整内容在 docs/debug-memory.md 原文）。"""
    name = name.strip()
    return name if len(name) <= limit else name[:limit] + '…'


def _collect_r_rules(unpaired: list) -> list:
    """R 规则号 ← debug-memory 标题行（含 R7.3/R8.1 派生号；分隔符实测为 ·/—/-）。"""
    path = os.path.join(REPO, 'docs', 'debug-memory.md')
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            m = re.match(r'^##\s+(R\d+(?:\.\d+)?)\s*[·—–-]+\s*(.+?)\s*$', line)
            if not m:
                continue
            rid, name = m.group(1), m.group(2).strip()
            if name and not re.fullmatch(r'R\d+(?:\.\d+)?', name):
                rows.append((rid, name))
            else:
                unpaired.append((rid, 'docs/debug-memory.md'))
    rows.sort(key=lambda r: [int(x) for x in r[0][1:].split('.')])
    return rows


def _collect_track_ids(unpaired: list) -> dict:
    """F_/D_ 号 ← 全仓 register_track_id 注册（首处注册为准·按模块聚簇）。"""
    pat = re.compile(
        r'register_track_id\(\s*["\'](MOD_[A-Z]+)\.([FD]_\d+)["\'],\s*["\']([^"\']+)')
    by_mod = {}
    for dp, dns, fs in os.walk(REPO):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for f in fs:
            if not f.endswith('.py'):
                continue
            try:
                with open(os.path.join(dp, f), encoding='utf-8', errors='ignore') as fh:
                    text = fh.read()
            except OSError:
                continue
            for m in pat.finditer(text):
                mod, fid, desc = m.group(1), m.group(2), m.group(3).strip()
                key = f'{mod}.{fid}'
                if desc and not re.fullmatch(r'(MOD_[A-Z]+\.)?[FD]_\d+', desc):
                    by_mod.setdefault(mod, {})[key] = desc
                else:
                    unpaired.append((key, os.path.relpath(os.path.join(dp, f), REPO)))
    return by_mod


def _collect_batches(unpaired: list) -> list:
    """批次号 ← discuss/** 文件名标题段（标题本身裸编号的回读文内首行）。"""
    base = os.path.join(REPO, 'docs', 'catch-ball', 'discuss')
    names = {}
    for dp, dns, fs in os.walk(base):
        dns[:] = [d for d in dns if d != '_prompts']
        for f in fs:
            if not f.endswith('.md'):
                continue
            m = re.match(r'^(PT-)?(CB\d+)(?:[x×](CB\d+))?-(.+?)_[^_]+-\d{4}-\d{2}-\d{2}', f)
            if not m:
                continue
            bid = f'{m.group(1) or ""}{m.group(2)}'
            title = m.group(4).strip()
            if re.fullmatch(r'v?\d+(?:\.\d+)?', title):  # 标题裸版本号 → 回读首行
                title = _first_heading(os.path.join(dp, f)) or ''
            if title and not re.fullmatch(r'(PT-)?CB\d+', title):
                prev = names.get(bid, '')
                if len(title) > len(prev):  # 取信息量最大的标题
                    names[bid] = title
            else:
                unpaired.append((bid, os.path.relpath(os.path.join(dp, f), REPO)))
    return sorted(names.items(), key=lambda kv: (len(kv[0]), kv[0]))


def _first_heading(path: str) -> str:
    try:
        with open(path, encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if line.startswith('#'):
                    return line.lstrip('#').strip()
    except OSError:
        pass
    return ''


def main() -> int:
    unpaired = []
    r_rows = _collect_r_rules(unpaired)
    by_mod = _collect_track_ids(unpaired)
    b_rows = _collect_batches(unpaired)

    head = _head_short()
    src = f'generated from {head}' if head else 'generated from (git 不可用)'
    lines = ['# EMC 术语表（内部编号 → 业务名）', '']
    lines += [f'> 数据源=仓内权威注册点·确定性生成（`py tools/gen_glossary.py`）·{src}。'
              '禁裸用编号（用户沟通纪律 2）——查不到编号含义先跑本生成器。', '']

    lines += ['## R 规则号（全局调试记忆·细则见 docs/debug-memory.md）', '']
    if r_rows:
        lines.append('；'.join(f'**{rid}** {_clip(name)}' for rid, name in r_rows))
    lines.append('')

    lines += ['## F_/D_ 工具号（register_track_id 注册表·按模块聚簇）', '']
    for mod in sorted(by_mod):
        ids = by_mod[mod]
        f_n = sum(1 for k in ids if '.F_' in k)
        d_n = sum(1 for k in ids if '.D_' in k)
        lines.append(f'- **{mod}**（{f_n}F/{d_n}D）：'
                     + '；'.join(f'{k.split(".")[1]}={v}' for k, v in sorted(ids.items())))
    lines.append('')

    lines += ['## 批次号（CB 讨论档案）', '']
    for bid, title in b_rows:
        lines.append(f'- **{bid}** {title}')
    lines.append('')

    text = '\n'.join(lines)
    n_lines = len(lines)
    with open(GLOSSARY_PATH, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)

    # 未配对清单 + 覆盖率落盘（验收件·独立文件不吃 100 行预算）
    total = len(r_rows) + sum(len(v) for v in by_mod.values()) + len(b_rows) + len(unpaired)
    cov = 100.0 * (total - len(unpaired)) / total if total else 0.0
    up = ['# 术语表未配对裸编号清单（PT-CB18 W1-3）', '',
          f'> 覆盖率 = 已配对/全部编号 = {total - len(unpaired)}/{total} = {cov:.1f}%'
          f'（验收线 ≥80%）。以下编号在权威源中未抽到业务名，补名后重跑生成器。', '']
    if unpaired:
        up += ['| 编号 | 发现位置 |', '|---|---|']
        up += [f'| {k} | {p} |' for k, p in sorted(set(unpaired))]
    else:
        up.append('（无未配对编号）')
    with open(UNPAIRED_PATH, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(up) + '\n')

    _safe_print(f'[OK] GLOSSARY.md generated: {GLOSSARY_PATH} ({n_lines} lines, budget {MAX_LINES})')
    _safe_print(f'[OK] coverage={cov:.1f}% unpaired={len(unpaired)} -> {UNPAIRED_PATH}')
    if n_lines > MAX_LINES:
        _safe_print(f'[WARN] 产物 {n_lines} 行超预算 {MAX_LINES}——检查紧凑格式')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
