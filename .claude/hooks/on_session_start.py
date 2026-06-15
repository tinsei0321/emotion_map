"""
会话启动钩子 (SessionStart Hook)
在每次 Claude Code 会话启动时自动执行。
"""
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print(f"[HOOK] SessionStart — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 1. 检查 Python 环境
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"  Python: {py_ver}")

    # 2. 检查 API Key
    env_file = os.path.join(PROJECT_ROOT, ".env")
    keys = {"DEEPSEEK_API_KEY": False, "IFLYTEK_API_KEY": False, "VOLCENGINE_API_KEY": False}
    if os.path.exists(env_file):
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                for k in keys:
                    if line.startswith(f"{k}=") and len(line.strip().split("=", 1)[1]) > 3:
                        keys[k] = True

    missing = [k for k, v in keys.items() if not v]
    if missing:
        print(f"  [WARN] API Key 缺失: {', '.join(missing)}")
    else:
        print(f"  [OK] API Key: 3/3 已配置")

    # 3. 检查 TODO 状态
    todo_path = os.path.join(PROJECT_ROOT, "docs", "todo.md")
    if os.path.exists(todo_path):
        with open(todo_path, encoding='utf-8') as f:
            content = f.read()
        # 统计任务状态
        pending = content.count("| ⬜ |")
        in_progress = content.count("| 🔄 |")
        done = content.count("| ✅ |")
        print(f"  TODO: {done} done / {in_progress} in-progress / {pending} pending")

    # 4. 检查 Git 状态
    import subprocess
    try:
        result = subprocess.run(
            ["git", "status", "--short"], capture_output=True, text=True,
            cwd=PROJECT_ROOT, timeout=10
        )
        dirty = len([l for l in result.stdout.splitlines() if l.strip()])
        if dirty:
            print(f"  Git: {dirty} 个未提交文件")
        else:
            print(f"  Git: 工作区干净")
    except Exception:
        print(f"  Git: 检查失败")

    print(f"[HOOK] SessionStart 完成\n")

if __name__ == "__main__":
    main()
