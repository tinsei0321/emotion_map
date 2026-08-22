"""PT-CB13 · 进度契约门禁（_board.yaml + gen_progress.py 确定性）。

四断言：①三段齐 ②awaiting_user 非空 ③重生成 diff=0 ④产物无时间戳。
"""
import os
import re
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join(ROOT, '_board.yaml')
PROGRESS = os.path.join(ROOT, 'docs', 'progress.md')


def test_board_three_sections_present():
    with open(BOARD, encoding='utf-8') as fh:
        board = yaml.safe_load(fh) or {}
    for key in ('stages', 'goals', 'awaiting_user'):
        assert isinstance(board.get(key), list), f'_board.yaml 缺三段之一: {key}'
    assert board['stages'], 'stages 不应为空'
    assert board['goals'], 'goals 不应为空'


def test_awaiting_user_not_empty():
    with open(BOARD, encoding='utf-8') as fh:
        board = yaml.safe_load(fh) or {}
    assert board.get('awaiting_user'), 'awaiting_user 为空——待拍板清单不许悄悄消失'


def test_regenerate_deterministic():
    with open(PROGRESS, encoding='utf-8') as fh:
        before = fh.read()
    subprocess.run(
        [sys.executable, os.path.join('tools', 'gen_progress.py')],
        cwd=ROOT, capture_output=True, text=True, timeout=60, check=True,
    )
    with open(PROGRESS, encoding='utf-8') as fh:
        after = fh.read()
    # 忽略 generated from <hash> 行（每次 commit 后 HEAD 变·产物 hash 过一期=结构性行为·非漂移）
    strip = lambda t: '\n'.join(l for l in t.splitlines() if not l.startswith('> 数据源'))
    assert strip(before) == strip(after), '重生成 diff!=0——产物与 _board.yaml 漂移（跑 py tools/gen_progress.py 再提交）'


def test_progress_has_no_timestamp():
    with open(PROGRESS, encoding='utf-8') as fh:
        text = fh.read()
    assert not re.search(r'\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}', text), '产物含时间戳——违反确定性纪律'
