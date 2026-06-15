"""
会话结束钩子 (SessionEnd Hook)
在 Claude Code 会话结束时自动执行。
提醒更新交接卡和提交代码。
"""
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

    print(f"[HOOK] SessionEnd 完成\n")

if __name__ == "__main__":
    main()
