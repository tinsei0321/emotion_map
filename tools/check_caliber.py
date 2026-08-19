#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PT-CB4 T3 · 口径复核工具（口径注册表 X-01 作废数字卡的机械执行）。

用途：
  读 `docs/urban-renewal-plan/00-宜昌专项/_口径注册表.md` 的 X-01 作废值表，
  解析出作废值清单（含书写变体：千分位 5,615 与 5615、87.9% 与 87.9、
  全角数字 ８７．９ 与全角逗号千分位 ５，６１５ 等），
  扫描待蒸馏素材（默认 DATA/analysis + docs/urban-renewal-plan），
  命中即输出 文件/行号/命中值/所属卡 ID 并 exit 1；干净则 exit 0。

用法：
  py tools/check_caliber.py                        # 默认白名单两个前缀
  py tools/check_caliber.py DATA/analysis 汇总     # 显式指定目标（文件或目录）
  py tools/check_caliber.py --registry 路径        # 覆盖默认注册表路径

纪律：
  - 排除 _retired/ 目录与注册表自身；
  - 只扫文本类扩展名（md/csv/txt/geojson/json/py），跳过 xlsx/png/pdf 等二进制；
  - 追踪：MOD_AIQA.F_020（主手预留号·本模块 import 时注册）；
  - 所有 print 走 _safe_print，ASCII 标记 [OK]/[ERR]/[WARN]。
"""
import argparse
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from core.tracker import register_track_id, track

register_track_id('MOD_AIQA.F_020', '口径复核：读注册表作废值→扫素材→命中即fail清单')

DEFAULT_REGISTRY = os.path.join(REPO, 'docs', 'urban-renewal-plan', '00-宜昌专项', '_口径注册表.md')
DEFAULT_TARGETS = [
    os.path.join(REPO, 'DATA', 'analysis'),
    os.path.join(REPO, 'docs', 'urban-renewal-plan'),
]
TEXT_EXTS = {'.md', '.csv', '.txt', '.geojson', '.json', '.py'}
CARD_ID = 'X-01'

# 全角数字/标点 → 半角（v2：８７．９％ / ５，６１５ 与半角写法同义）
_FULLWIDTH_MAP = str.maketrans({
    '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
    '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
    '，': ',', '．': '.', '％': '%',
})


def _normalize_width(text):
    return text.translate(_FULLWIDTH_MAP)


def _safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('gbk', 'replace').decode('gbk'))


def _parse_x01_values(registry_path):
    """解析注册表 X-01 节表格第一列（作废值·去掉 ** 加粗标记）。"""
    values = []
    in_section = False
    with open(registry_path, 'r', encoding='utf-8') as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if line.startswith('### ') and 'X-01' in line and '作废' in line:
                in_section = True
                continue
            if not in_section:
                continue
            # 下一节标题即本表结束
            if line.startswith('## ') or (line.startswith('### ') and 'X-01' not in line):
                break
            if not line.startswith('|'):
                continue
            cells = [c.strip() for c in line.strip('|').split('|')]
            if not cells:
                continue
            value = cells[0].replace('**', '').strip()
            # 跳过表头与分隔行
            if not value or value == '作废值' or set(value) <= {'-', ':', ' '}:
                continue
            values.append(value)
    return values


def _variants_for(raw):
    """为一个作废值生成匹配变体（千分位/百分比/全角/空格/斜杠复合写法）。"""
    v = _normalize_width(raw.strip())
    out = {v}
    no_comma = re.sub(r'(?<=\d),(?=\d)', '', v)
    out.add(no_comma)
    if '%' in v:
        out.add(v.replace('%', ''))
        out.add(no_comma.replace('%', ''))
    # 去空格紧凑形（覆盖「港务 1,153」vs「港务1,153」类差异）
    for base in (v, no_comma):
        out.add(re.sub(r'\s+', '', base))

    # 斜杠复合值（如 双高 16/32/3/26、194 行矩阵 / 675 行占比表）
    if '/' in v:
        parts = [p.strip() for p in v.split('/')]
        prefix = ''
        first_match = re.match(r'^([^\d]*?)\s*(\d)', parts[0])
        if first_match:
            prefix = first_match.group(1).strip()
        for part in parts:
            if not re.search(r'\d', part):
                continue
            part_nc = re.sub(r'(?<=\d),(?=\d)', '', part)
            part_compact = re.sub(r'\s+', '', part_nc)
            # 去掉括号注记（如 26（各代））后判断是否纯数字；纯数字不单独作变体（防“3”全域误报）
            core_part = re.sub(r'[（(].*?[)）]', '', part).strip()
            has_text = bool(re.search(r'[^\d\s,\.%]', core_part))
            if has_text:
                out.add(part)
                out.add(part_nc)
                out.add(part_compact)
            if prefix:
                nums = re.findall(r'\d[\d,]*(?:\.\d+)?', part)
                for num in nums:
                    num_nc = num.replace(',', '')
                    out.add(f'{prefix}{num}')
                    out.add(f'{prefix} {num}')
                    out.add(f'{prefix}{num_nc}')
                    out.add(f'{prefix} {num_nc}')
    return {x for x in out if x}


def _variant_pattern(variant):
    """数字段加前后边界（防 5615 命中 15615/56150）；文字段原样。"""
    parts = re.split(r'(\d[\d,]*(?:\.\d+)?%?)', variant)
    pattern = ''
    for part in parts:
        if part and part[0].isdigit():
            pattern += r'(?<![0-9])' + re.escape(part) + r'(?![0-9])'
        else:
            pattern += re.escape(part)
    return pattern


def _build_variant_groups(raw_values):
    """每个作废值一组变体；组内按长度降序，取最长命中避免同值重复报。"""
    groups = []
    for raw in raw_values:
        variants = sorted(_variants_for(raw), key=len, reverse=True)
        patterns = [(v, re.compile(_variant_pattern(v))) for v in variants]
        groups.append({'raw': raw, 'patterns': patterns})
    return groups


def _should_scan(path, registry_abs):
    if os.path.abspath(path) == registry_abs:
        return False
    if '_retired' in path.split(os.sep):
        return False
    return os.path.splitext(path)[1].lower() in TEXT_EXTS


def _iter_files(targets, registry_path):
    registry_abs = os.path.abspath(registry_path)
    for target in targets:
        abs_target = os.path.abspath(target)
        if os.path.isfile(abs_target):
            if _should_scan(abs_target, registry_abs):
                yield abs_target
        elif os.path.isdir(abs_target):
            for root, dirs, files in os.walk(abs_target):
                dirs[:] = [d for d in dirs if d != '_retired']
                for name in files:
                    path = os.path.join(root, name)
                    if _should_scan(path, registry_abs):
                        yield path
        else:
            _safe_print(f'[WARN] 扫描目标不存在: {target}')


def _scan_file(path, groups):
    hits = []
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            for lineno, line in enumerate(fh, 1):
                line = _normalize_width(line)
                for group in groups:
                    matched = None
                    for variant, pattern in group['patterns']:
                        if pattern.search(line):
                            matched = variant
                            break
                    if matched:
                        try:
                            rel = os.path.relpath(path, REPO)
                        except ValueError:
                            rel = path
                        hits.append((rel, lineno, matched, group['raw']))
    except OSError as exc:
        _safe_print(f'[WARN] 无法读取 {path}: {exc}')
    return hits


@track('MOD_AIQA.F_020', track_args=False)
def main(argv=None):
    parser = argparse.ArgumentParser(description='口径复核：注册表 X-01 作废值 vs 待蒸馏素材')
    parser.add_argument('targets', nargs='*', help='扫描目标文件或目录（缺省=DATA/analysis 与 docs/urban-renewal-plan）')
    parser.add_argument('--registry', default=DEFAULT_REGISTRY, help='口径注册表路径（缺省=00-宜昌专项/_口径注册表.md）')
    args = parser.parse_args(argv)

    if not os.path.isfile(args.registry):
        _safe_print(f'[ERR] 注册表不存在: {args.registry}')
        return 2

    raw_values = _parse_x01_values(args.registry)
    if not raw_values:
        _safe_print('[ERR] 注册表 X-01 节未解析到任何作废值')
        return 2
    _safe_print(f'[OK] 注册表解析: {len(raw_values)} 个作废值（卡 {CARD_ID}）')

    groups = _build_variant_groups(raw_values)
    targets = args.targets if args.targets else DEFAULT_TARGETS

    hits = []
    scanned = 0
    for path in _iter_files(targets, args.registry):
        scanned += 1
        hits.extend(_scan_file(path, groups))

    for rel, lineno, matched, raw in hits:
        _safe_print(f'[ERR] {rel}:{lineno} 命中作废值「{matched}」（原始登记「{raw}」·卡 {CARD_ID}）')

    if hits:
        _safe_print(f'[ERR] 口径复核未通过: {len(hits)} 处命中（卡 {CARD_ID}）')
        return 1
    _safe_print(f'[OK] 口径复核通过: 扫描 {scanned} 个文件·0 命中（卡 {CARD_ID}）')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
