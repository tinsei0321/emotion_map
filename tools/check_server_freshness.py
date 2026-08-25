#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""服务新旧核查工具（R7 预防）。

用途：检查当前 8000/8080 端口服务进程是否晚于最新代码提交。
若服务早于最新提交，提示“载旧码风险”，建议重启（R7）。

PT-CB15 K8（R2-6）：新增 RAG 索引新鲜度段——索引构建时间 vs 知识源最新改动，
陈旧即告警（治「DATA 整理了但索引没重建·AI 读旧知识」类事故）。

纯报告型：不杀进程、不重启、不修改任何文件。
铁律：ASCII 标记 [OK]/[WARN]；所有 print 走 _safe_print。
"""

import datetime
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PORTS = (8000, 8080, 8600)   # PT-CB17：8600=MCP 工具插座（工具代码由它供·漏检=修复不生效复发案根因）
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


def check_rag_index_freshness(repo=REPO):
    """RAG 索引新鲜度（PT-CB15 K8 + PT-CB16 S2 共用 _index_freshness）。"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from rag_index import _index_freshness
    _safe_print("=== RAG 索引新鲜度 ===")
    idx_m, _srcs, newest = _index_freshness(repo)
    if idx_m is None:
        _safe_print("[WARN] 索引不存在（跑 py tools/rag_index.py --build）")
        return 1
    idx_s = datetime.datetime.fromtimestamp(idx_m).isoformat(timespec="seconds")
    _safe_print(f"索引构建时间: {idx_s}")
    if not newest:
        _safe_print("[WARN] 知识源扫描为空（目录结构变了？）")
        return 1
    newest_src, newest_t = newest
    src_s = datetime.datetime.fromtimestamp(newest_t).isoformat(timespec="seconds")
    if newest_t > idx_m:
        hours = int((newest_t - idx_m) // 3600)
        _safe_print(f"[WARN] 知识源比索引新 {hours} 小时——最新改动: {newest_src}（{src_s}）"
                    "·建议 py tools/rag_index.py --rebuild")
        return 1
    _safe_print(f"[OK] 索引新于全部知识源（最新源: {os.path.basename(newest_src)} {src_s}）")
    return 0


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
    rag_rc = check_rag_index_freshness()
    return rag_rc


if __name__ == "__main__":
    sys.exit(main())

# 本机演示输出（2026-08-19 · PT-CB4 dsh 批二）
# === 服务新旧核查 ===
# 最新提交时间: 2026-08-19T14:47:05
# PID 5548: 启动时间 2026-08-19T14:30:31
# [WARN] 服务早于最新提交 16 分钟——载旧码风险，建议重启（R7）（PID 5548）
# PID 25696: 启动时间 2026-08-19T14:30:31
# [WARN] 服务早于最新提交 16 分钟——载旧码风险，建议重启（R7）（PID 25696）
