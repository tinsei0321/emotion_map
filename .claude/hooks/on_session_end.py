"""
会话结束钩子 (SessionEnd Hook)
在 Claude Code 会话结束时自动执行。
提醒更新交接卡和提交代码。
"""
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _append_trace_digest():
    """闭环补强 Wave4：把本次会话新增的 trace ERR/WARN 摘要沉淀到 docs/trace-digest.md。

    用 .claude/.trace-digest-cursor 记录已消化的日志行数，避免每次会话重复追加。
    全程 try/except 包裹——digest 永不阻断 SessionEnd 主流程。
    """
    log_file = os.environ.get("EMOTION_TRACE_LOG") or os.path.join(PROJECT_ROOT, ".trace", "trace.log")
    if not log_file or not os.path.exists(log_file):
        return
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
    except Exception:
        return

    cursor_file = os.path.join(PROJECT_ROOT, ".claude", ".trace-digest-cursor")
    cursor = 0
    try:
        if os.path.exists(cursor_file):
            with open(cursor_file, "r", encoding="utf-8") as f:
                cursor = int((f.read().strip() or "0"))
    except Exception:
        cursor = 0

    new_lines = all_lines[cursor:]
    errs = [ln.rstrip("\n") for ln in new_lines if "[ERR]" in ln or "[WARN]" in ln]

    # 无论是否命中都推进游标，避免下次重复消化旧行
    try:
        with open(cursor_file, "w", encoding="utf-8") as f:
            f.write(str(len(all_lines)))
    except Exception:
        pass

    if not errs:
        return

    digest_path = os.path.join(PROJECT_ROOT, "docs", "trace-digest.md")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    block = []
    if not os.path.exists(digest_path):
        block.append("# Trace 错误摘要 (Error Digest)\n\n")
        block.append("> 闭环补强 Wave4：SessionEnd 自动从 `.trace/trace.log` 摘取**新增** ERR/WARN 沉淀于此。\n")
        block.append("> 让 debug 史不再蒸发——可检索、可回灌。游标 `.claude/.trace-digest-cursor` 防重复（gitignored）。\n\n---\n\n")
    block.append(f"## {ts}（{len(errs)} 条新增 ERR/WARN）\n\n")
    block.append("```\n")
    block.extend(e + "\n" for e in errs[-50:])
    block.append("```\n\n")
    try:
        with open(digest_path, "a", encoding="utf-8") as f:
            f.writelines(block)
        print(f"  [DIGEST] {len(errs)} 条 trace ERR/WARN 已沉淀到 docs/trace-digest.md")
    except Exception:
        pass


def main():
    print(f"[HOOK] SessionEnd — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 1. 提醒更新会话交接卡
    handoff_path = os.path.join(PROJECT_ROOT, "memories", "repo", "session-handoff.md")
    if os.path.exists(handoff_path):
        print(f"  [REMIND] 记得更新会话交接卡: memories/repo/session-handoff.md")

    # 2. 检查 Git 未提交变更
    import subprocess
    try:
        result = subprocess.run(
            ["git", "status", "--short"], capture_output=True, text=True,
            cwd=PROJECT_ROOT, timeout=10
        )
        dirty = len([l for l in result.stdout.splitlines() if l.strip()])

        # 检查 ahead
        result2 = subprocess.run(
            ["git", "status"], capture_output=True, text=True,
            cwd=PROJECT_ROOT, timeout=10
        )
        if dirty > 0:
            print(f"  [REMIND] {dirty} 个未提交文件，别忘了 git commit")
        if "ahead of" in result2.stdout:
            print(f"  [REMIND] 本地领先远程，需要 git push")
    except Exception:
        pass

    # 3. 记录时间戳
    timestamp_file = os.path.join(PROJECT_ROOT, ".claude", ".last-session")
    try:
        os.makedirs(os.path.dirname(timestamp_file), exist_ok=True)
        with open(timestamp_file, 'w') as f:
            f.write(datetime.now().isoformat())
    except Exception:
        pass

    # 4. trace 错误摘要回灌（闭环补强 Wave4）
    try:
        _append_trace_digest()
    except Exception:
        pass

    print(f"[HOOK] SessionEnd 完成\n")

if __name__ == "__main__":
    main()
