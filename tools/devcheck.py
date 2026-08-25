#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EMC 开测前自检（devcheck）——说人话版。

面向非技术用户：只回答两个问题——「现在能不能开始测试？」「不能的话点哪里？」
不输出 PID/提交哈希行话（必要信息用大白话表达）。

用法：py tools/devcheck.py（或双击 devcheck.bat）
铁律：ASCII 标记 [OK]/[WARN]；print 走 _safe_print；纯只读不改任何东西。
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

REPO = r"D:\Github\emotion_map"
# 三个服务的角色说明（大白话）：
SERVICES = [
    (8000, '后端服务（管数据和出图通道）'),
    (8080, '地图网页（你看到的页面）'),
    (8600, '工具插座（AI 干活用的全部工具）'),
]


def _safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        encoded = [str(a).encode("utf-8", errors="replace").decode("utf-8", errors="replace") for a in args]
        print(*encoded, **kwargs)


def _run(cmd, timeout=15):
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout, check=False)
        return proc.stdout or ""
    except Exception:
        return ""


def _latest_commit():
    out = _run(["git", "-C", REPO, "log", "-1", "--format=%cI|%s"]).strip()
    if "|" not in out:
        return None, ""
    ts, msg = out.split("|", 1)
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().replace(tzinfo=None)
        return dt, msg.strip()
    except ValueError:
        return None, msg.strip()


def _listening_pids(port):
    out = _run(["netstat", "-ano"])
    pids = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0] == "TCP" and parts[3].upper() == "LISTENING":
            try:
                if int(parts[1].rsplit(":", 1)[-1]) == port and parts[-1].isdigit():
                    pids.append(int(parts[-1]))
            except ValueError:
                continue
    return pids


def _proc_start(pid):
    out = _run(["wmic", "process", "where", f"ProcessId={pid}", "get", "CreationDate", "/value"])
    m = re.search(r"CreationDate=(\d{14})", out)
    if not m:
        return None
    try:
        return datetime.datetime.strptime(m.group(1), "%Y%m%d%H%M%S")
    except ValueError:
        return None


def _how_old(delta):
    """时间差说人话。"""
    mins = int(delta.total_seconds() // 60)
    if mins < 1:
        return "刚刚"
    if mins < 60:
        return f"{mins} 分钟前"
    hours = mins // 60
    if hours < 24:
        return f"{hours} 小时前"
    return f"{hours // 24} 天前"


def _rag_index_age():
    idx = os.path.join(REPO, "DATA", "RAG", "rag_index", "vectors.npy")
    if not os.path.isfile(idx):
        return None, 0.0
    idx_t = os.path.getmtime(idx)
    newest = 0.0
    for rel, pat in (("docs/urban-renewal-plan", ".md"), ("DATA/THEME", ".md"),
                     ("ai_qa/outlet_kb", ".py"), ("DATA", "README.md")):
        root = os.path.join(REPO, rel)
        for dirpath, _dirs, files in os.walk(root):
            if "_Retired" in dirpath or "_retired" in dirpath:
                continue
            for fn in files:
                if not fn.endswith(pat):
                    continue
                try:
                    newest = max(newest, os.path.getmtime(os.path.join(dirpath, fn)))
                except OSError:
                    continue
    return idx_t, newest


def main():
    problems = []
    _safe_print("=" * 56)
    _safe_print("  EMC 开测前自检（只读检查·不改任何东西）")
    _safe_print("=" * 56)

    commit_dt, commit_msg = _latest_commit()
    if commit_dt:
        _safe_print(f"\n[信息] 最新代码是 {_how_old(datetime.datetime.now() - commit_dt)}改的"
                    + (f"（{commit_msg[:28]}…）" if commit_msg else ""))
    else:
        _safe_print("\n[WARN] 读不到代码版本信息（git 异常）——建议联系开发组")
        problems.append("git")

    _safe_print("\n[检查 1/2] 三个服务是不是都在跑最新代码：")
    for port, label in SERVICES:
        pids = _listening_pids(port)
        if not pids:
            _safe_print(f"  [WARN] {label}：没在运行——请双击 start.bat 启动")
            problems.append(port)
            continue
        started = _proc_start(pids[0])
        if started is None:
            _safe_print(f"  [WARN] {label}：在运行，但查不到启动时间——建议双击 start.bat 重置")
            problems.append(port)
            continue
        if commit_dt and commit_dt > started:
            _safe_print(f"  [WARN] {label}：跑的是旧代码"
                        f"（服务 {_how_old(commit_dt - started)}前启动，之后代码又改过）"
                        "——请双击 start.bat 重置")
            problems.append(port)
        else:
            _safe_print(f"  [OK]   {label}：正常（最新代码）")

    _safe_print("\n[检查 2/2] AI 的知识索引新不新鲜：")
    idx_t, src_t = _rag_index_age()
    if not idx_t:
        _safe_print("  [WARN] 知识索引不存在——告诉开发组重建（py tools/rag_index.py --rebuild）")
        problems.append("rag")
    elif src_t > idx_t:
        _safe_print("  [WARN] 资料比索引新（你最近改过资料但索引没重建）"
                    "——告诉开发组跑一句：py tools/rag_index.py --rebuild")
        problems.append("rag")
    else:
        _safe_print("  [OK]   知识索引是最新的")

    _safe_print("\n" + "-" * 56)
    if problems:
        _safe_print("结论：现在先别测——有旧代码/旧索引，测了也是白测。")
        _safe_print("怎么办：双击 start.bat（一键全部重置），看到网页打开后再测。")
        return 1
    _safe_print("结论：全部正常，可以放心开始测试。")
    _safe_print("提示：测试中觉得哪里不对劲，随时再双击 devcheck.bat 复查。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
