# 自定义命令 (Custom Slash Commands)
#
# 在此目录下创建 .md 文件，自动注册为 /<filename> 命令。
# 例如: .claude/commands/commit.md → 输入 /commit 即可触发。
#
# 命令文件格式（Markdown + YAML frontmatter）:
# ---
# description: "提交当前变更并生成规范的 commit message"
# ---
# # /commit — 智能提交
# 
# 1. 检查 git status
# 2. 生成符合 Conventional Commits 的 commit message
# 3. 执行 git add + commit
#
# 使用: 在对话中输入 /commit
#
# 详见: https://docs.anthropic.com/claude-code/slash-commands
