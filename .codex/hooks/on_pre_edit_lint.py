"""
PreToolUse 钩子 — 拦截 .py 代码中的 emoji（CLAUDE.md 规则 1：代码只允许 ASCII 标记）
======================================================================
触发: Edit / Write / MultiEdit 作用于 *.py 文件前（settings.json PreToolUse 注册）。
行为: 扫描待写入内容中的补充平面 emoji（U+1F000–U+1FAFF，如 🛠🔍🧪🎉🛰），
      命中则 exit 2 阻断工具调用并报告位置与码点。

设计（防误伤）:
  - 仅拦 U+1F000–U+1FAFF 补充平面 emoji（agent 风格表情符号，覆盖 mahjong/
    emoticons/transport/flags/supplemental/symbols-ext 等连续块）。
  - 不拦 中文 CJK、不拦箭头 ←→↓↑（U+2190–21FF）、不拦 BMP 符号 ☀⚠（U+2600–27BF），
    因为 .py 的 docstring/注释中这些可能合法出现。
  - 仅 .py；.md/.json 等不拦（文档允许 emoji）。
  - 阻断 = exit 2（PreToolUse 协议），stderr 回显给用户。

输入 (stdin JSON, Claude Code PreToolUse 协议):
  {"tool_name":"Edit","tool_input":{"file_path":"...","new_string":"..."}}
  {"tool_name":"Write","tool_input":{"file_path":"...","content":"..."}}
  {"tool_name":"MultiEdit","tool_input":{"file_path":"...","edits":[{"new_string":"..."}]}}

手动测试:
  echo '{"tool_name":"Write","tool_input":{"file_path":"x.py","content":"# 🎉"}}' \
    | py .claude/hooks/on_pre_edit_lint.py ; echo "exit=$?"
"""
import json
import re
import sys

_TRIGGER_TOOLS = ('Edit', 'Write', 'MultiEdit')
# 补充平面 emoji：mahjong / emoticons / transport / flags / supplemental / symbols-ext 等连续块
_EMOJI_RE = re.compile(r'[\U0001F000-\U0001FAFF]')


def _read_event():
    """从 stdin 读取 PreToolUse 事件，返回 (tool_name, file_path, tool_input)。"""
    try:
        # 显式 UTF-8 解码：Claude Code 经 stdin 传 UTF-8 JSON，Windows 默认 locale
        # (cp936) 会把 emoji 字节读坏致 JSON 解析失败、被 except 吞掉静默放行。
        raw = sys.stdin.buffer.read().decode('utf-8')
        if not raw.strip():
            return None, None, {}
        event = json.loads(raw)
    except Exception:
        return None, None, {}
    ti = event.get('tool_input') or {}
    return event.get('tool_name', ''), ti.get('file_path', ''), ti


def _scan(text, label):
    """返回首个命中 (char, context) 或 None。"""
    if not text:
        return None
    m = _EMOJI_RE.search(text)
    if not m:
        return None
    ch = m.group()
    start = max(0, m.start() - 30)
    ctx = text[start:m.end() + 30].replace('\n', '\\n')
    return ch, f"{label} near: ...{ctx}..."


def main():
    tool_name, file_path, tool_input = _read_event()
    if tool_name not in _TRIGGER_TOOLS:
        return
    if not file_path or not file_path.lower().endswith('.py'):
        return

    candidates = []
    if tool_name == 'Write':
        candidates.append((tool_input.get('content', ''), 'content'))
    elif tool_name == 'Edit':
        candidates.append((tool_input.get('new_string', ''), 'new_string'))
    elif tool_name == 'MultiEdit':
        for i, ed in enumerate(tool_input.get('edits', [])):
            candidates.append((ed.get('new_string', ''), f'edits[{i}].new_string'))

    for text, label in candidates:
        hit = _scan(text, label)
        if hit:
            ch, ctx = hit
            sys.stderr.write(
                "[HOOK][BLOCK] emoji in .py rejected "
                "(CLAUDE.md rule 1, ASCII-only markers)\n"
                f"  file: {file_path}\n"
                f"  char: {ch!r} (U+{ord(ch):04X})\n"
                f"  {ctx}\n"
                "  -> replace with ASCII marker [OK]/[WARN]/[LOAD]/[ERR], "
                "or move content to a .md doc.\n"
            )
            sys.exit(2)  # PreToolUse: exit 2 = block the tool call


if __name__ == '__main__':
    main()
