# 事件钩子 (Event Hooks)
#
# 在此目录下放置可执行脚本，在 settings.json 的 hooks 字段中注册。
# Claude Code 支持在特定事件前后自动触发脚本。
#
# 事件类型:
#   - SessionStart: 会话开始时触发
#   - SessionEnd:   会话结束时触发
#   - PreToolUse:   工具调用前触发
#   - PostToolUse:  工具调用后触发
#   - Notification: 后台任务完成时触发
#
# 示例 settings.json 配置:
# "hooks": {
#   "SessionStart": [
#     { "command": "python .claude/hooks/on_start.py" }
#   ]
# }
#
# 详见: https://docs.anthropic.com/claude-code/hooks
