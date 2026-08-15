#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AutoMemory 蒸馏层同步（Gitee 末日保险·三层记忆保护伞第3层）

镜像 ~/.claude/projects/d--Github-emotion-map/memory/ <-> repo memories/auto/
全量对话 context 不上云（密钥/体积），只同步蒸馏记忆（memory/*.md·KB级）。

用法:
  py tools/memory_sync.py push        # memory/ -> memories/auto/ + commit + push (gitee+github)
  py tools/memory_sync.py pull        # memories/auto/ -> memory/（恢复/迁移·带确认）
  py tools/memory_sync.py push --dry  # 只列镜像清单不落盘
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = Path.home() / ".claude" / "projects" / "d--Github-emotion-map" / "memory"
DST = REPO / "memories" / "auto"
REMOTES = ("origin", "github")


def _safe_print(text):
    """GBK 兼容打印（Windows 规范）"""
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((str(text) + "\n").encode("gbk", "replace"))
        sys.stdout.buffer.flush()


def _robocopy(src, dst, dry=False):
    cmd = ["robocopy", str(src), str(dst), "/MIR", "/R:1", "/W:1",
           "/NFL", "/NDL", "/NP"]
    if dry:
        cmd.append("/L")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode >= 8:
        _safe_print("[ERR] robocopy 失败 code=%d  %s -> %s" % (r.returncode, src, dst))
        sys.exit(1)
    return r.returncode


def _git(*args, check=True):
    r = subprocess.run(["git", "-C", str(REPO)] + list(args),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        _safe_print("[ERR] git %s -> %s" % (" ".join(args), (r.stderr or r.stdout).strip()))
    return r


def push(dry=False):
    if not SRC.is_dir():
        _safe_print("[ERR] 源不存在: %s （本机无 AutoMemory？）" % SRC)
        sys.exit(1)
    code = _robocopy(SRC, DST, dry=dry)
    _safe_print("[OK] 镜像完成 memory/ -> memories/auto/ (robocopy=%d%s)"
                % (code, " · dry-run" if dry else ""))
    if dry:
        return
    st = _git("status", "--porcelain", "--", "memories/auto")
    if not st.stdout.strip():
        _safe_print("[OK] 无变化，跳过提交")
        return
    branch = _git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    _git("add", "memories/auto")
    _git("commit", "-m", "chore: sync AutoMemory snapshot [memory-sync]")
    _git("pull", "--rebase", "origin", branch, check=False)
    for remote in REMOTES:
        r = _git("push", remote, branch, check=False)
        if r.returncode == 0:
            _safe_print("[OK] push %s %s" % (remote, branch))
        else:
            _safe_print("[WARN] push %s 失败（离盘/断网？）下次再推" % remote)


def pull():
    if not DST.is_dir() or not any(DST.iterdir()):
        _safe_print("[ERR] repo 内无 memories/auto/ 快照")
        sys.exit(1)
    confirm = input("pull 将用 repo memories/auto/ 覆盖本机 %s 确认? y/N " % SRC)
    if confirm.strip().lower() != "y":
        _safe_print("[OK] 已取消")
        return
    SRC.parent.mkdir(parents=True, exist_ok=True)
    code = _robocopy(DST, SRC)
    _safe_print("[OK] 恢复完成 memories/auto/ -> memory/ (robocopy=%d)" % code)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "push"
    if mode == "push":
        push(dry="--dry" in sys.argv)
    elif mode == "pull":
        pull()
    else:
        _safe_print("[ERR] 未知模式: %s （push | pull）" % mode)
        sys.exit(1)
