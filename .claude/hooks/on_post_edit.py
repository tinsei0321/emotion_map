"""
PostToolUse 钩子 — 编辑 .py 后自动清理过期 .pyc
======================================================================
触发: Edit / Write / MultiEdit 作用于 *.py 文件后（由 settings.json 的
      PostToolUse 注册，本脚本对其它工具/非 .py 文件直接 return）。
行为: 仅删除被编辑模块在所在目录 __pycache__ 中的过期 .pyc/.pyo，
      不递归全项目、不重启 Streamlit、不跑 pytest（后两者耗时且打断会话）。

设计约束（与 CLAUDE.md「开发工作流」一致）:
  - 永不阻断工具调用 → 退出码恒为 0
  - 仅作用于被编辑文件的模块缓存，最小副作用
  - Windows GBK 安全：输出仅 ASCII 标记

输入 (stdin JSON, Claude Code PostToolUse 协议):
  {"session_id":..., "tool_name":"Edit",
   "tool_input":{"file_path":"..."}, "tool_response":{...}}

用法（手动模拟测试）:
  echo '{"tool_name":"Edit","tool_input":{"file_path":"core/config.py"}}' \
    | py .claude/hooks/on_post_edit.py
"""
import json
import os
import sys
from datetime import datetime


# 仅这些工具 + .py 文件触发清理
_TRIGGER_TOOLS = ('Edit', 'Write', 'MultiEdit')


def _read_event() -> tuple:
    """从 stdin 读取 PostToolUse 事件 JSON，返回 (tool_name, file_path)。"""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return None, None
        event = json.loads(raw)
    except Exception:
        return None, None
    tool_name = event.get('tool_name', '')
    file_path = (event.get('tool_input') or {}).get('file_path', '')
    return tool_name, file_path


def main() -> None:
    tool_name, file_path = _read_event()

    # 非目标工具 / 非 .py 文件 → 静默退出
    if tool_name not in _TRIGGER_TOOLS:
        return
    if not file_path or not file_path.lower().endswith('.py'):
        return

    abs_path = os.path.abspath(file_path)
    pkg_dir = os.path.dirname(abs_path)
    module_stem = os.path.splitext(os.path.basename(abs_path))[0]
    cache_dir = os.path.join(pkg_dir, '__pycache__')

    if not os.path.isdir(cache_dir):
        return

    # 仅删除该模块的缓存文件（如 ui_components.cpython-313.pyc）
    removed = 0
    try:
        for name in os.listdir(cache_dir):
            if name.startswith(module_stem + '.') and name.endswith(('.pyc', '.pyo')):
                try:
                    os.remove(os.path.join(cache_dir, name))
                    removed += 1
                except OSError:
                    pass
    except OSError:
        return

    if removed:
        ts = datetime.now().strftime('%H:%M:%S')
        rel = os.path.relpath(abs_path)
        print(f'[HOOK] PostEdit [{ts}] cleaned {removed} stale .pyc '
              f'for {module_stem} (edited: {rel})')


if __name__ == '__main__':
    main()
