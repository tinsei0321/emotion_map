#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PT-CB18(W1-1) · 单一交接文档生成器（非 MCP 正式工具·零追踪 ID·同 gen_progress 先例）。

数据源=_board.yaml + git → 产出 STATE.md（仓根·在途状态唯一落点）。
骨架五栏：当前分支 / 在途批次（每批一行）/ 待拍板项（消费决策区）/ 门禁基线 / 最近 5 提交。
确定性纪律：机器骨架部分同一 _board.yaml + 同一 HEAD → 逐字节同一产物；
仅首行允许携带「生成时间 + HEAD 短哈希」（人判新旧用·契约用例比对时豁免首行）。
手写段（阶段交接·八字段模板见 docs/state-handoff-template.md）位于产物末尾
「## 手写区」之内——生成器逐字节保留手写区内容，只刷新机器骨架。
纯只读生成：不改 _board.yaml。
"""
from __future__ import annotations

import datetime
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

STATE_PATH = os.path.join(REPO, 'STATE.md')
HANDWRITE_MARK = '## 手写区'


def _safe_print(msg, file=None):
    try:
        print(msg, file=file)
    except UnicodeEncodeError:
        print(msg.encode('gbk', 'replace').decode('gbk'), file=file)


def _git(*args: str) -> str:
    """git 子进程只读取数（失败降级空串·生成器不因 git 环境缺失而崩）。

    encoding 显式 utf-8：git 输出恒 UTF-8，Windows text=True 默认走 GBK 会解不开中文提交题。
    """
    try:
        out = subprocess.run(
            ['git', *args], cwd=REPO, capture_output=True, text=True,
            encoding='utf-8', errors='replace',
            timeout=10, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return ''


_STATUS_LABEL = {
    'done': '完成',
    'in_progress': '进行中',
    'in_review': '待回收',
    'in_lanes': '泳道中',
    'partial': '部分完成',
    'pending': '待启动',
    'awaiting': '待拍板',
    'decided': '已拍板',
    'dropped': '已放弃',
}


def _read_handwrite() -> str:
    """读回既有产物「## 手写区」之后全文（含标记行）；无则返回默认占位。"""
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding='utf-8') as fh:
            text = fh.read()
        idx = text.find(HANDWRITE_MARK)
        if idx >= 0:
            return text[idx:]
    return (
        HANDWRITE_MARK + '（里程碑级阶段结束时按 docs/state-handoff-template.md 八字段手写·'
        '小批只跑生成器刷机器骨架·禁写密码密钥）\n'
    )


def _render(now: str, head: str, branch: str, board: dict, log5: str) -> str:
    lines = [f'<!-- generated {now} from {head or "(git 不可用)"} -->', '']
    lines += ['# EMC 当前状态（单一交接文档）', '']
    src = f'数据源 `_board.yaml` + git·`py tools/gen_state.py` 生成·HEAD `{head}`' if head else '数据源 `_board.yaml`（git 不可用）'
    lines += [f'> {src}。在途状态以本文为唯一落点；历史进度看 `docs/progress.md`。', '']

    lines += ['## 当前分支', '', f'`{branch or "(git 不可用)"}`', '']

    lines += ['## 在途批次（每批一行）', '']
    active = [s for s in board.get('stages') or []
              if str(s.get('status', '')) not in ('done',)]
    if active:
        for st in active:
            label = _STATUS_LABEL.get(str(st.get('status', '')), str(st.get('status', '')))
            lines.append(f'- {st.get("batch", "")}（{label}）：{st.get("summary", "")}（{st.get("docs", "")}）')
    else:
        lines.append('（当前无在途批次）')
    lines.append('')

    lines += ['## 待拍板项（消费 _board.yaml decisions 区）', '']
    pending = [d for d in board.get('decisions') or []
               if str(d.get('status', '')) in ('awaiting', '')]
    if pending:
        for d in pending:
            lines.append(f'- {d.get("id", "")} {d.get("item", "")}｜候选：{d.get("candidates", "")}')
    else:
        lines.append('（当前无待拍板项）')
    lines.append('')

    lines += ['## 门禁基线', '']
    gb = board.get('gate_baseline') or {}
    if gb:
        lines.append(f'- pytest：{gb.get("pytest", "")}（{gb.get("updated", "")}·commit `{gb.get("commit", "")}`）')
    else:
        lines.append('（gate_baseline 未登记）')
    lines += ['- 全量跑法：`py -m pytest tests/ -q`（判新旧以本文首行生成时间 + HEAD 为准）', '']

    lines += ['## 最近 5 提交', '']
    if log5:
        for row in log5.splitlines():
            lines.append(f'- `{row}`')
    else:
        lines.append('（git 不可用）')
    lines.append('')
    return '\n'.join(lines)


def main() -> int:
    import yaml

    board_path = os.path.join(REPO, '_board.yaml')
    with open(board_path, encoding='utf-8') as fh:
        board = yaml.safe_load(fh) or {}
    head = _git('rev-parse', '--short', 'HEAD')
    branch = _git('rev-parse', '--abbrev-ref', 'HEAD')
    log5 = _git('log', '--oneline', '-5')
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    text = _render(now, head, branch, board, log5) + _read_handwrite()
    with open(STATE_PATH, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    _safe_print(f'[OK] STATE.md generated: {STATE_PATH}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
