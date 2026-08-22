#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PT-CB13 · 进度契约确定性生成器（非 MCP 正式工具·零追踪 ID·同 grid_export 先例）。

数据源=_board.yaml（进度契约·手改唯一入口）→ 产出 docs/progress.md（人读版）。
确定性纪律：同一 _board.yaml + 同一 HEAD → 逐字节同一产物（无时间戳·禁 datetime.now）。
产物头部注 generated from <HEAD short hash>（git rev-parse 失败降级空·不阻塞）。
纯只读生成：不改 _board.yaml·awaiting_user 置顶（待拍板清单是用户唯一要盯的）。
"""
from __future__ import annotations

import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)


def _safe_print(msg, file=None):
    try:
        print(msg, file=file)
    except UnicodeEncodeError:
        print(msg.encode('gbk', 'replace').decode('gbk'), file=file)


def _head_short() -> str:
    """当前 HEAD short hash（失败降级空串·生成器不因 git 环境缺失而崩）。"""
    try:
        out = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=REPO, capture_output=True, text=True, timeout=5, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return ''


_STATUS_LABEL = {
    'done': '完成',
    'in_progress': '进行中',
    'in_review': '待回收',
    'partial': '部分完成',
    'pending': '待启动',
}


def _render(head: str, board: dict) -> str:
    lines = ['# EMC 进度（人读版）', '']
    src = f'generated from {head}' if head else 'generated from (git 不可用)'
    lines += [f'> 数据源 `_board.yaml`·确定性生成（`py tools/gen_progress.py`）·{src}。', '']

    awaiting = board.get('awaiting_user') or []
    lines += ['## 待用户（唯一要盯的）', '']
    if awaiting:
        for i, it in enumerate(awaiting, 1):
            refs = it.get('refs') or ''
            tail = f'（{refs}）' if refs else ''
            lines.append(f'{i}. {it.get("item", "")}{tail}')
    else:
        lines.append('（当前无待用户项）')
    lines.append('')

    lines += ['## 阶段进度', '']
    lines.append('| 批次 | 状态 | 结论 | 文档 |')
    lines.append('|---|---|---|---|')
    for st in board.get('stages') or []:
        label = _STATUS_LABEL.get(str(st.get('status', '')), str(st.get('status', '')))
        lines.append(
            f'| {st.get("batch", "")} | {label} | {st.get("summary", "")} | {st.get("docs", "")} |'
        )
    lines.append('')

    lines += ['## 小目标', '']
    lines.append('| 目标 | 状态 | 说明 |')
    lines.append('|---|---|---|')
    for g in board.get('goals') or []:
        label = _STATUS_LABEL.get(str(g.get('status', '')), str(g.get('status', '')))
        lines.append(f'| {g.get("title", "")} | {label} | {g.get("note", "")} |')
    lines.append('')
    return '\n'.join(lines)


def main() -> int:
    import yaml

    board_path = os.path.join(REPO, '_board.yaml')
    with open(board_path, encoding='utf-8') as fh:
        board = yaml.safe_load(fh) or {}
    text = _render(_head_short(), board)
    out_path = os.path.join(REPO, 'docs', 'progress.md')
    with open(out_path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    _safe_print(f'[OK] progress.md generated: {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
