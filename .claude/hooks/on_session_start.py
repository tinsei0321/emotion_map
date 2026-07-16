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

    # 5. 上下文树阈值提醒（/garden 除草触发线；零 LLM 调用，超阈值才提示）
    try:
        import re
        slug = re.sub(r'[^A-Za-z0-9]', '-', os.path.abspath(PROJECT_ROOT))
        mem_dir = os.path.join(os.path.expanduser('~'), '.claude', 'projects', slug, 'memory')
        mem_count = len([f for f in os.listdir(mem_dir)
                        if f.endswith('.md') and f != 'MEMORY.md']) if os.path.isdir(mem_dir) else 0
        rl_path = os.path.join(PROJECT_ROOT, 'docs', 'revision-log.md')
        rl_kb = os.path.getsize(rl_path) // 1024 if os.path.exists(rl_path) else 0
        flags = []
        if mem_count > 50:
            flags.append(f"memory={mem_count} 条")
        if rl_kb > 500:
            flags.append(f"revision-log={rl_kb}KB")
        if flags:
            print(f"  [GARDEN] {' / '.join(flags)} 超阈值 — 考虑 /garden 除草")
    except Exception:
        pass

    print(f"[HOOK] SessionStart 完成\n")

if __name__ == "__main__":
    main()
