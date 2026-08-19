#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""服务新旧核查工具（R7 预防）。

用途：检查当前 8000/8080 端口服务进程是否晚于最新代码提交。
若服务早于最新提交，提示“载旧码风险”，建议重启（R7）。

纯报告型：不杀进程、不重启、不修改任何文件。
铁律：ASCII 标记 [OK]/[WARN]；所有 print 走 _safe_print。
"""

import datetime
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PORTS = (8000, 8080)
REPO = r"D:\Github\emotion_map"


def _safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        encoded = [str(a).encode("utf-8", errors="replace").decode("utf-8", errors="replace") for a in args]
        print(*encoded, **kwargs)


def _run(cmd):
    """运行命令并返回 stdout 文本；失败返回空字符串。"""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
        return proc.stdout or ""
    except Exception:
        return ""


def _get_listening_pids():
    """通过 netstat 找出监听 PORTS 的 PID 集合。"""
    out = _run(["netstat", "-ano"])
    pids = set()
    for line in out.splitlines():
        # 示例:  TCP    0.0.0.0:8000    0.0.0.0:0    LISTENING    12345
        parts = line.split()
        if len(parts) < 5:
            continue
        if parts[0] != "TCP":
            continue
        local = parts[1]
        state = parts[3] if len(parts) > 3 else ""
        pid = parts[-1]
        if state.upper() != "LISTENING":
            continue
        try:
            port = int(local.rsplit(":", 1)[-1])
        except ValueError:
            continue
        if port in PORTS and pid.isdigit():
            pids.add(int(pid))
    return pids


def _get_process_start_time(pid):
    """通过 wmic 获取进程创建时间；返回 datetime 或 None。"""
    out = _run(["wmic", "process", "where", f"ProcessId={pid}", "get", "CreationDate", "/value"])
    m = re.search(r"CreationDate=(\d{14})", out)
    if not m:
        return None
    try:
        return datetime.datetime.strptime(m.group(1), "%Y%m%d%H%M%S")
    except ValueError:
        return None


def _get_latest_commit_time():
    """获取仓库最新提交时间（ISO 8601）；返回 datetime 或 None。"""
    out = _run(["git", "-C", REPO, "log", "-1", "--format=%cI"])
    out = out.strip()
    if not out:
        return None
    try:
        dt = datetime.datetime.fromisoformat(out.replace("Z", "+00:00"))
        # 统一为本地无时区 datetime，避免与 wmic 的 naive 时间相减出错
        return dt.astimezone().replace(tzinfo=None)
    except ValueError:
        return None


def main():
    _safe_print("=== 服务新旧核查 ===")
    pids = _get_listening_pids()
    commit_time = _get_latest_commit_time()
    if commit_time is None:
        _safe_print("[WARN] 无法获取最新提交时间")
        return 1

    _safe_print(f"最新提交时间: {commit_time.isoformat()}")

    if not pids:
        _safe_print("[OK] 无服务运行（8000/8080 无 LISTENING 进程）")
        return 0

    for pid in sorted(pids):
        start_time = _get_process_start_time(pid)
        if start_time is None:
            _safe_print(f"[WARN] PID {pid}: 无法获取进程启动时间")
            continue
        delta = commit_time - start_time
        _safe_print(f"PID {pid}: 启动时间 {start_time.isoformat()}")
        if delta.total_seconds() <= 0:
            _safe_print(f"[OK] 服务晚于最新提交（PID {pid}）")
        else:
            minutes = int(delta.total_seconds() // 60)
            _safe_print(
                f"[WARN] 服务早于最新提交 {minutes} 分钟——载旧码风险，建议重启（R7）（PID {pid}）"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())

# 本机演示输出（2026-08-19 · PT-CB4 dsh 批二）
# === 服务新旧核查 ===
# 最新提交时间: 2026-08-19T14:47:05
# PID 5548: 启动时间 2026-08-19T14:30:31
# [WARN] 服务早于最新提交 16 分钟——载旧码风险，建议重启（R7）（PID 5548）
# PID 25696: 启动时间 2026-08-19T14:30:31
# [WARN] 服务早于最新提交 16 分钟——载旧码风险，建议重启（R7）（PID 25696）

