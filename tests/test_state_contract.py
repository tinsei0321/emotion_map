"""PT-CB18(W1-1) · STATE.md 单一交接文档契约门禁（照 test_progress_contract.py 先例）。

断言：①骨架五栏齐 ②重生成机器骨架 diff=0（豁免首行生成时间）③分支/最近提交与 git 一致
④决策区至少 1 条 awaiting 驱动「待拍板」栏非空 ⑤手写区重生成后逐字节保留。
"""
import os
import re
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join(ROOT, '_board.yaml')
STATE = os.path.join(ROOT, 'STATE.md')

SECTIONS = ('## 当前分支', '## 在途批次', '## 待拍板项', '## 门禁基线', '## 最近 5 提交')


def _git(*args):
    # encoding 显式 utf-8：git 输出恒 UTF-8，Windows text=True 默认 GBK 解不开中文提交题
    return subprocess.run(
        ['git', *args], cwd=ROOT, capture_output=True, text=True,
        encoding='utf-8', errors='replace', timeout=10, check=True,
    ).stdout.strip()


def _strip_volatile(text: str) -> str:
    # 豁免随 HEAD 变的行（多会话仓并发提交常见·同 gen_progress 先例）：
    # 首行生成时间+HEAD、> 数据源行（含 HEAD）、最近提交子弹行（与 git 一致性由专项用例验）
    return '\n'.join(l for l in text.splitlines()
                     if not (l.startswith('<!-- generated ')
                             or l.startswith('> 数据源')
                             or l.startswith('- `')))


def test_state_skeleton_five_sections():
    with open(STATE, encoding='utf-8') as fh:
        text = fh.read()
    for sec in SECTIONS:
        assert sec in text, f'STATE.md 缺骨架栏: {sec}'
    first = text.splitlines()[0]
    assert re.match(r'<!-- generated \d{4}-\d{2}-\d{2} \d{2}:\d{2} from \w+', first), \
        '首行必须 = 生成时间 + HEAD 短哈希'


def test_state_regenerate_deterministic():
    with open(STATE, encoding='utf-8') as fh:
        before = fh.read()
    subprocess.run(
        [sys.executable, os.path.join('tools', 'gen_state.py')],
        cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace',
        timeout=60, check=True,
    )
    with open(STATE, encoding='utf-8') as fh:
        after = fh.read()
    assert _strip_volatile(before) == _strip_volatile(after), \
        'STATE.md 重生成 diff!=0——产物与 _board.yaml/git 漂移（跑 py tools/gen_state.py 再提交）'


def test_state_branch_and_head_match_git():
    with open(STATE, encoding='utf-8') as fh:
        text = fh.read()
    branch = _git('rev-parse', '--abbrev-ref', 'HEAD')
    assert f'`{branch}`' in text, f'STATE.md 分支栏与 git 不一致（应为 {branch}）'
    head = _git('rev-parse', '--short', 'HEAD')
    assert head in text, 'STATE.md 未携带当前 HEAD 短哈希'
    latest = _git('log', '--oneline', '-1')
    assert latest in text, f'STATE.md「最近 5 提交」未含最新提交 {latest}'


def test_decisions_zone_drives_pending():
    with open(BOARD, encoding='utf-8') as fh:
        board = yaml.safe_load(fh) or {}
    awaiting = [d for d in board.get('decisions') or [] if d.get('status') == 'awaiting']
    assert awaiting, '_board.yaml decisions 区无 awaiting 记录——待拍板清单不许悄悄消失'
    with open(STATE, encoding='utf-8') as fh:
        text = fh.read()
    for d in awaiting:
        assert d['id'] in text, f'决策区 {d["id"]} 未出现在 STATE.md 待拍板栏'


def test_handwrite_section_preserved():
    with open(STATE, encoding='utf-8') as fh:
        before = fh.read()
    idx = before.find('## 手写区')
    assert idx >= 0, 'STATE.md 缺「## 手写区」标记（阶段交接八字段落点）'
    subprocess.run(
        [sys.executable, os.path.join('tools', 'gen_state.py')],
        cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace',
        timeout=60, check=True,
    )
    with open(STATE, encoding='utf-8') as fh:
        after = fh.read()
    assert after[after.find('## 手写区'):] == before[idx:], '手写区被生成器覆写——手写交接段丢失'
