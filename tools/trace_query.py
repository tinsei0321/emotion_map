"""trace.log 查询工具（CB-12·业界结构化日志查询·根因分析第一动作）。

用法：
  py tools/trace_query.py --stats                     # 各 ID 计数（F_002/F_003/F_005 交叉·一眼看 while-loop/finalStep/FC）
  py tools/trace_query.py --id MOD_AIQA.F_002         # 按 ID 过滤
  py tools/trace_query.py --time 21:14-21:50          # 按时间窗（HH:MM-HH:MM）
  py tools/trace_query.py --level ERR|WARN            # 按级别
  py tools/trace_query.py --session <sid>             # 按 session（各组跑测试带 EMOTION_TRACE_SESSION 隔离）
  py tools/trace_query.py --case <kw>                 # 按 detail 关键词（如 B3）
  py tools/trace_query.py --tail 100                  # 最近 N 行
  py tools/trace_query.py --id F_002 --stats          # 组合（先看该 ID 分布再细看）
  py tools/trace_query.py --file <path>               # 指定日志文件（默认 .trace/trace.log）

纯函数·无依赖·不调 LLM。输出 ASCII 标记（[OK]/[ERR]·禁 emoji）。
"""
import argparse
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_LOG = REPO / '.trace' / 'trace.log'

_ID_RE = re.compile(r'\|\s*(MOD_\w+\.\w+)\s*\|?')
_STATUS_RE = re.compile(r'\|\s*\[(ERR|WARN|ok|enter|exit|INFO|DEBUG|ERROR)\]\s*\|?')


def _iter_lines(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            yield line


def _fields(line):
    """解析 [TRACE] 行 → {ts, id, status, elapsed, detail}（宽松·不依赖严格格式）。"""
    if '[TRACE]' not in line:
        return None
    m = re.match(r'^\s*\[TRACE\]\s+(\S+)', line)
    ts = m.group(1) if m else ''
    parts = line.split('|')
    f = {'raw': line.strip(), 'ts': ts, 'id': '', 'status': '', 'elapsed': 0.0, 'detail': ''}
    for p in parts[1:]:
        p = p.strip()
        if not p:
            continue
        if not f['id'] and (m2 := _ID_RE.match('| ' + p + ' |')):
            f['id'] = m2.group(1)
            continue
        if not f['status'] and (m3 := _STATUS_RE.match('| ' + p + ' |')):
            f['status'] = m3.group(1)
            continue
        if re.match(r'^\d+(\.\d+)?ms$', p):
            f['elapsed'] = float(p[:-2])
            continue
        f['detail'] = p
    return f


def _match(f, args):
    if args.id and args.id not in f['id']:
        return False
    if args.level and args.level.upper() != f['status'].upper():
        return False
    if args.session and args.session not in f['raw']:
        return False
    if args.case and args.case not in f['raw']:
        return False
    if args.time:
        t0, _, t1 = args.time.partition('-')
        if t0 and f['ts'] < t0:
            return False
        if t1 and f['ts'] > t1:
            return False
    return True


def main():
    ap = argparse.ArgumentParser(description='trace.log 查询工具')
    ap.add_argument('--file', default=str(DEFAULT_LOG))
    ap.add_argument('--stats', action='store_true', help='各 ID 计数（根因分析第一动作）')
    ap.add_argument('--id', default='')
    ap.add_argument('--time', default='', help='时间窗 HH:MM-HH:MM')
    ap.add_argument('--level', default='', help='ERR|WARN|ok')
    ap.add_argument('--session', default='')
    ap.add_argument('--case', default='')
    ap.add_argument('--tail', type=int, default=0, help='最近 N 行')
    ap.add_argument('--raw', action='store_true', help='输出原始行')
    a = ap.parse_args()

    if not Path(a.file).exists():
        print(f'[ERR] 日志不存在: {a.file}')
        sys.exit(1)

    matched = []
    for line in _iter_lines(a.file):
        f = _fields(line)
        if not f:
            continue
        if _match(f, a):
            matched.append(f)

    if a.stats:
        # 各 ID 计数（含 status 分桶·while-loop 看 F_002）
        from collections import Counter
        c = Counter(m['id'] for m in matched)
        print(f'== 各 ID 计数（{len(matched)} 行）==')
        for tid, n in c.most_common():
            errs = sum(1 for m in matched if m['id'] == tid and m['status'] in ('ERR', 'ERROR'))
            print(f'  {tid}: {n}{"  [ERR " + str(errs) + "]" if errs else ""}')
        return 0

    if a.tail:
        matched = matched[-a.tail:]
    for f in matched:
        print(f['raw'] if a.raw else f"{f['ts']} | {f['id']} | {f['status']} | {f['elapsed']:.1f}ms | {f['detail'][:120]}")
    print(f'== {len(matched)} 行 ==')
    return 0


if __name__ == '__main__':
    sys.exit(main())
